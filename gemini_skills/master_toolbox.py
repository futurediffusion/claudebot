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

# Importar el motor de memoria episódica de Codex y el World Model
try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from orchestrator.core.episodic_memory import EpisodicMemoryEngine
    from orchestrator.core.world_model import WorldModelEngine
except ImportError:
    from orchestrator.core.episodic_memory import EpisodicMemoryEngine
    from orchestrator.core.world_model import WorldModelEngine

# --- CONFIGURACION ---
EDGE_PORT = 9222
RULE_ENGINE_FILE = Path("self_model/rule_engine.json")
TASK_LOG_FILE = "self_model/task_history.jsonl"
STEP_LOG_FILE = "self_model/internal_steps.jsonl"

class TaskRecorder:
    def __init__(self, task_name, memory_engine=None, world_model=None):
        self.task_id = str(uuid.uuid4())[:8]
        self.task_name = task_name
        self.start_time = datetime.now()
        self.memory_engine = memory_engine
        self.world_model = world_model
        self.steps = []
        self._log_task("started")
        
        # REGISTRO EN EL WORLD MODEL AL INICIO
        if self.world_model:
            self.world_model.record_task_start(task_name, "generic")

    def _log_task(self, status, result=None):
        entry = {"task_id": self.task_id, "timestamp": datetime.now().isoformat(), "task": self.task_name, "status": status, "result": result}
        os.makedirs("self_model", exist_ok=True)
        with open(TASK_LOG_FILE, "a", encoding="utf-8") as f: f.write(json.dumps(entry) + "\n")

    def log_step(self, step_name, status, metadata=None):
        step_entry = {"stage": step_name, "status": status, "metadata": metadata or {}}
        self.steps.append(step_entry)
        entry = {"task_id": self.task_id, "timestamp": datetime.now().isoformat(), "step": step_name, "status": status, "metadata": metadata or {}}
        with open(STEP_LOG_FILE, "a", encoding="utf-8") as f: f.write(json.dumps(entry) + "\n")
        print(f"🧱 [STEP] {step_name}: {status}")

    def complete(self, success=True, response=None, error=None, task_type="generic", tools=None, metadata=None):
        duration = int((datetime.now() - self.start_time).total_seconds() * 1000)
        self._log_task("completed", {"duration_ms": duration, "success": success})
        
        # SINCRONIZACION CON MEMORIA EPISODICA
        if self.memory_engine:
            self.memory_engine.record_episode(
                task=self.task_name, task_type=task_type, success=success,
                execution_time_ms=duration, episode_type="production",
                model_name="gemini-2.0-flash", tools_used=tools or [],
                steps=self.steps, response=response, error=error, metadata=metadata
            )
            
        # SINCRONIZACION CON EL WORLD MODEL AL FINAL
        if self.world_model:
            self.world_model.record_execution(
                task=self.task_name, task_type=task_type, success=success,
                model_name="gemini-2.0-flash", tools_used=tools or [],
                response=response, error=error
            )
        print(f"🏁 [TASK] {self.task_name} finalizada ({'ÉXITO' if success else 'FALLO'}) en {duration/1000}s.")

class RuleHandler:
    def __init__(self, toolbox):
        self.toolbox = toolbox
        self.rules = self._load_rules()

    def _load_rules(self):
        if RULE_ENGINE_FILE.exists():
            data = json.loads(RULE_ENGINE_FILE.read_text(encoding="utf-8"))
            return data.get("rules", data.get("rules_active", []))
        return []

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
            signatures = rule.get("signatures", rule.get("pattern", {}).get("error_types", []))
            if (fn_name in methods or "*" in methods) and signature in signatures: return rule
        return None

    async def apply_async(self, rule, recorder):
        actions = rule.get("actions", [])
        if not actions and "action" in rule: actions = [rule["action"]]
        for action in actions:
            kind = action.get("type", action.get("handler_id"))
            if kind in ["ensure_edge", "kill_and_retry_edge"]: self.toolbox._ensure_edge_is_running(recorder)
            elif kind == "sleep": await asyncio.sleep(action.get("seconds", 2))

    def guard(self, fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            # Inyectar recorder con acceso a memoria y mundo
            recorder = kwargs.get("recorder") or TaskRecorder(
                kwargs.get("message", kwargs.get("query", fn.__name__)), 
                memory_engine=self.toolbox.memory,
                world_model=self.toolbox.world
            )
            kwargs["recorder"] = recorder
            attempt = 0
            max_attempts = 3
            while attempt < max_attempts:
                try:
                    return await fn(*args, **kwargs)
                except Exception as exc:
                    attempt += 1
                    signature = self.classify(exc)
                    recorder.log_step("rule_intercept", "matched", {"sig": signature, "attempt": attempt})
                    rule = self.match(fn.__name__, signature)
                    if not rule or attempt >= max_attempts: 
                        recorder.complete(success=False, error=str(exc))
                        raise
                    await self.apply_async(rule, recorder)
                    recorder.log_step("reparing", "retry_triggered")
        return wrapper

class GeminiToolbox:
    def __init__(self):
        self.memory = EpisodicMemoryEngine(agent_name="gemini_cli")
        self.world = WorldModelEngine(agent_name="gemini_cli")
        self.rule_handler = RuleHandler(self)
        self.chatgpt = self.rule_handler.guard(self._chatgpt_impl)
        self.download_image = self.rule_handler.guard(self._download_image_impl)

    def _ensure_edge_is_running(self, recorder):
        # USAR WORLD MODEL PARA VER SI EDGE YA ESTA
        state = self.world.observe_desktop()
        edge_open = any("msedge" in app["process_name"].lower() for app in state["desktop"]["open_apps"])
        
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM); sock.settimeout(1)
        port_open = sock.connect_ex(('127.0.0.1', EDGE_PORT)) == 0
        sock.close()

        if not port_open:
            recorder.log_step("edge_launch", "starting")
            if edge_open: 
                print("🛑 Matando Edge para forzar modo debug...")
                subprocess.run(["taskkill", "/F", "/IM", "msedge.exe", "/T"], capture_output=True)
            time.sleep(1)
            subprocess.Popen(f'start msedge.exe --remote-debugging-port={EDGE_PORT} --start-maximized "https://chatgpt.com"', shell=True)
            time.sleep(5)
        else:
            recorder.log_step("edge_check", "already_running_on_port")

    async def _chatgpt_impl(self, message, recorder=None):
        # CONSULTA A MEMORIA Y WORLD MODEL
        relevant = self.memory.find_relevant_episodes(task=message)
        if relevant: print(f"💡 [MEMORIA] Recordando episodio similar: {relevant[0]['task']}")
        
        state = self.world.get_state()
        print(f"🌍 [WORLD] Ventana activa detectada: {state['desktop']['active_window'].get('title')}")

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
            
            last_text, stable = "", 0
            while stable < 4:
                msgs = page.locator('div[data-message-author-role="assistant"]')
                if await msgs.count() > 0:
                    txt = await msgs.last.inner_text()
                    if txt == last_text and txt != "": stable += 1
                    else: last_text, stable = txt, 0
                await asyncio.sleep(1)
            
            recorder.complete(success=True, response=last_text, task_type="chat_interaction", tools=["playwright", "edge_cdp"])
            print(f"\n🤖 RESPUESTA: {last_text}\n")
            return last_text

    async def _download_image_impl(self, query, recorder=None):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            page = await context.new_page()
            await page.goto("https://duckduckgo.com")
            await page.type('input[name="q"]', query, delay=100); await page.keyboard.press("Enter")
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
                recorder.complete(success=True, task_type="image_download", tools=["playwright"])
            else:
                recorder.complete(success=False, error="no_image_url_found")
            await browser.close()

    def vision_world(self):
        """Skill de ConscienciaSituacional: Captura + Procesos + Ventanas"""
        recorder = TaskRecorder("vision_world_snapshot", memory_engine=self.memory, world_model=self.world)
        recorder.log_step("snapshot", "starting")
        subprocess.run(["powershell", "-File", "capture_pro.ps1"], capture_output=True)
        state = self.world.observe_desktop()
        summary = self.world.get_summary()
        recorder.complete(success=True, task_type="situational_awareness", metadata=summary)
        print(f"\n🌍 [SITUACION] Ventana activa: {summary['active_window'].get('title')}")
        print(f"📱 Apps: {summary['open_app_count']} | Descargas: {len(summary['downloads_in_progress'])}")

    def interact_with_claude(self, message):
        """Interacción nativa con la ventana de Claude"""
        recorder = TaskRecorder("claude_interaction", memory_engine=self.memory, world_model=self.world)
        self.world.observe_desktop()
        state = self.world.get_state()
        claude_app = next((app for app in state["desktop"]["open_apps"] if "claude" in app["title"].lower() or "claude" in app["process_name"].lower()), None)
        if claude_app:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            if shell.AppActivate(claude_app["pid"]):
                time.sleep(0.5); shell.SendKeys(message + "{ENTER}")
                recorder.complete(success=True, tools=["win32_keyboard"])
                print(f"✅ Mensaje enviado a Claude ({claude_app['title']})")
            else: recorder.complete(success=False, error="activation_failed")
        else:
            print("❌ Claude no encontrado."); recorder.complete(success=False, error="not_found")

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(1)
    tool = GeminiToolbox()
    if sys.argv[1] == "chat": asyncio.run(tool.chatgpt(message=sys.argv[2]))
    elif sys.argv[1] == "image": asyncio.run(tool.download_image(query=sys.argv[2]))
    elif sys.argv[1] == "vision_world": tool.vision_world()
    elif sys.argv[1] == "claude": tool.interact_with_claude(sys.argv[2])
    elif sys.argv[1] == "git": tool.git_sync(sys.argv[2])
