import asyncio
import sys
import os
import random
import subprocess
import json
import time
import uuid
from datetime import datetime
from functools import wraps
from pathlib import Path
from playwright.async_api import async_playwright

# --- CONFIGURACION ---
EDGE_PORT = 9222
RULE_ENGINE_FILE = Path("self_model/rule_engine.json")
TASK_LOG_FILE = "self_model/task_history.jsonl"
STEP_LOG_FILE = "self_model/internal_steps.jsonl"

class TaskRecorder:
    def __init__(self, task_name):
        self.task_id = str(uuid.uuid4())[:8]
        self.task_name = task_name
        self.start_time = datetime.now()
        self._log_task("started")

    def _log_task(self, status, result=None):
        entry = {"task_id": self.task_id, "timestamp": datetime.now().isoformat(), "task": self.task_name, "status": status, "result": result}
        os.makedirs("self_model", exist_ok=True)
        with open(TASK_LOG_FILE, "a", encoding="utf-8") as f: f.write(json.dumps(entry) + "\n")

    def complete(self, result="success"):
        duration = (datetime.now() - self.start_time).total_seconds()
        self._log_task("completed", {"duration_sec": duration, "final_res": result})
        print(f"🏁 [TASK] {self.task_name} completada en {duration}s.")

    def log_step(self, step_name, status, metadata=None):
        entry = {"task_id": self.task_id, "timestamp": datetime.now().isoformat(), "step": step_name, "status": status, "metadata": metadata or {}}
        with open(STEP_LOG_FILE, "a", encoding="utf-8") as f: f.write(json.dumps(entry) + "\n")
        print(f"🧱 [STEP] {step_name}: {status}")

class RuleHandler:
    """Interceptor de fallos basado en reglas de auto-reparación"""
    def __init__(self, toolbox):
        self.toolbox = toolbox
        self.rules = self._load_rules()

    def _load_rules(self):
        if RULE_ENGINE_FILE.exists():
            data = json.loads(RULE_ENGINE_FILE.read_text(encoding="utf-8"))
            # Normalizar formato de chatgpt o el nuestro
            return data.get("rules", data.get("rules_active", []))
        return []

    def reload(self): self.rules = self._load_rules()

    def classify(self, exc: Exception) -> str:
        msg = str(exc).lower()
        if "timeout" in msg: return "timeout"
        if "context or browser has been closed" in msg: return "edge_context_closed"
        if "connect_over_cdp" in msg: return "cdp_connect_failed"
        if "selector" in msg: return "selector_not_found"
        return "unknown_failure"

    def match(self, fn_name, signature):
        for rule in self.rules:
            methods = rule.get("methods", rule.get("scope", {}).get("tool_ids", ["*"]))
            # Manejo de firmas (signatures o pattern/error_types)
            signatures = rule.get("signatures", rule.get("pattern", {}).get("error_types", []))
            if (fn_name in methods or "*" in methods) and signature in signatures:
                return rule
        return None

    async def apply_async(self, rule, recorder):
        # Mapeo de acciones del esquema de ChatGPT
        actions = rule.get("actions", [])
        if not actions and "action" in rule: actions = [rule["action"]]
        
        for action in actions:
            kind = action.get("type", action.get("handler_id"))
            if kind == "ensure_edge" or kind == "kill_and_retry_edge":
                self.toolbox._ensure_edge_is_running(recorder)
            elif kind == "sleep":
                await asyncio.sleep(action.get("seconds", 2))
            elif kind == "reload_rules":
                self.reload()

    def guard(self, fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            recorder = kwargs.get("recorder") or TaskRecorder(fn.__name__)
            kwargs["recorder"] = recorder
            attempt = 0
            max_attempts = 3
            while attempt < max_attempts:
                try:
                    return await fn(*args, **kwargs)
                except Exception as exc:
                    attempt += 1
                    signature = self.classify(exc)
                    recorder.log_step("rule_intercept", "matched", {"method": fn.__name__, "sig": signature, "attempt": attempt})
                    rule = self.match(fn.__name__, signature)
                    if not rule or attempt >= max_attempts: raise
                    await self.apply_async(rule, recorder)
                    recorder.log_step("reparing", "retry_triggered")
        return wrapper

class GeminiToolbox:
    def __init__(self):
        self.rule_handler = RuleHandler(self)
        self.chatgpt = self.rule_handler.guard(self._chatgpt_impl)
        self.download_image = self.rule_handler.guard(self._download_image_impl)

    def _ensure_edge_is_running(self, recorder):
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', EDGE_PORT))
        sock.close()
        if result != 0:
            recorder.log_step("edge_launch", "starting")
            subprocess.run(["taskkill", "/F", "/IM", "msedge.exe", "/T"], capture_output=True)
            time.sleep(1)
            subprocess.Popen(f'start msedge.exe --remote-debugging-port={EDGE_PORT} --start-maximized "https://chatgpt.com"', shell=True)
            time.sleep(5)

    async def _chatgpt_impl(self, message, recorder=None):
        self._ensure_edge_is_running(recorder)
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(f"http://localhost:{EDGE_PORT}")
            page = next((p for ctx in browser.contexts for p in ctx.pages if "chatgpt.com" in p.url), None)
            if not page: page = await browser.contexts[0].new_page(); await page.goto("https://chatgpt.com")
            await page.bring_to_front()
            input_sel = '#prompt-textarea'
            await page.wait_for_selector(input_sel, timeout=20000)
            await page.click(input_sel)
            await page.type(input_sel, message, delay=random.randint(50, 100))
            await page.keyboard.press("Enter")
            # Espera estabilidad
            last_text, stable = "", 0
            while stable < 4:
                msgs = page.locator('div[data-message-author-role="assistant"]')
                if await msgs.count() > 0:
                    txt = await msgs.last.inner_text()
                    if txt == last_text and txt != "": stable += 1
                    else: last_text, stable = txt, 0
                await asyncio.sleep(1)
            recorder.complete("success")
            print(f"\n🤖 RESPUESTA: {last_text}\n")
            return last_text

    async def _download_image_impl(self, query, recorder=None):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            page = await context.new_page()
            await page.goto("https://duckduckgo.com")
            await page.type('input[name="q"]', query, delay=100)
            await page.keyboard.press("Enter")
            await page.get_by_role("link", name="Imágenes").first.click()
            await asyncio.sleep(3)
            await page.evaluate("""() => {
                const img = Array.from(document.querySelectorAll('img')).find(i => i.width > 100 && !i.src.includes('logo'));
                if (img) img.click();
            }""")
            await asyncio.sleep(3)
            url = await page.evaluate("Array.from(document.querySelectorAll('img')).find(i => i.width > 400).src")
            if url:
                res = await page.request.get(url)
                filename = f"descarga_{query}_{recorder.task_id}.jpg"
                with open(filename, "wb") as f: f.write(await res.body())
                recorder.complete("success")
            await browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(1)
    tool = GeminiToolbox()
    if sys.argv[1] == "chat": asyncio.run(tool.chatgpt(sys.argv[2]))
    elif sys.argv[1] == "image": asyncio.run(tool.download_image(sys.argv[2]))
