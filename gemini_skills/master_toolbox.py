import asyncio
import sys
import os
import random
import subprocess
import json
import time
import uuid
from datetime import datetime
from playwright.async_api import async_playwright

# --- CONFIGURACION ---
EDGE_PORT = 9222
TASK_LOG_FILE = "self_model/task_history.jsonl"
STEP_LOG_FILE = "self_model/internal_steps.jsonl"

class TaskRecorder:
    """Auto Task Recorder: Capa estratégica de registro"""
    def __init__(self, task_name):
        self.task_id = str(uuid.uuid4())[:8]
        self.task_name = task_name
        self.start_time = datetime.now()
        self._log_task("started")

    def _log_task(self, status, result=None):
        entry = {
            "task_id": self.task_id,
            "timestamp": datetime.now().isoformat(),
            "task": self.task_name,
            "status": status,
            "result": result
        }
        with open(TASK_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def complete(self, result="success"):
        duration = (datetime.now() - self.start_time).total_seconds()
        self._log_task("completed", {"duration_sec": duration, "final_res": result})
        print(f"🏁 [TASK] {self.task_name} completada en {duration}s.")

    def log_step(self, step_name, status, metadata=None):
        """Log Internal Step: Capa granular de registro"""
        entry = {
            "task_id": self.task_id,
            "timestamp": datetime.now().isoformat(),
            "step": step_name,
            "status": status,
            "metadata": metadata or {}
        }
        with open(STEP_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        print(f"🧱 [STEP] {step_name}: {status}")

class GeminiToolbox:
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
            cmd = f'start msedge.exe --remote-debugging-port={EDGE_PORT} --start-maximized "https://chatgpt.com"'
            subprocess.Popen(cmd, shell=True)
            time.sleep(5)
            recorder.log_step("edge_launch", "success")

    async def chatgpt(self, message):
        recorder = TaskRecorder("chatgpt_interaction")
        async with async_playwright() as p:
            try:
                self._ensure_edge_is_running(recorder)
                recorder.log_step("cdp_connect", "attempting")
                browser = await p.chromium.connect_over_cdp(f"http://localhost:{EDGE_PORT}")
                
                page = None
                for ctx in browser.contexts:
                    for pge in ctx.pages:
                        if "chatgpt.com" in pge.url:
                            page = pge; break
                    if page: break
                
                if not page:
                    recorder.log_step("tab_open", "navigating")
                    page = await browser.contexts[0].new_page()
                    await page.goto("https://chatgpt.com")
                
                await page.bring_to_front()
                input_selector = '#prompt-textarea'
                await page.wait_for_selector(input_selector, timeout=20000)
                
                recorder.log_step("typing", "executing")
                await page.click(input_selector)
                await page.type(input_selector, message, delay=random.randint(50, 100))
                await page.keyboard.press("Enter")
                
                recorder.log_step("response_wait", "monitoring")
                await asyncio.sleep(4)
                
                # Sistema de espera por estabilidad de texto
                last_text = ""
                stable_count = 0
                while stable_count < 4:
                    msgs = page.locator('div[data-message-author-role="assistant"]')
                    count = await msgs.count()
                    if count > 0:
                        txt = await msgs.last.inner_text()
                        if txt == last_text and txt != "": stable_count += 1
                        else: last_text = txt; stable_count = 0
                    await asyncio.sleep(1)
                
                recorder.complete("success")
                print(f"\n🤖 RESPUESTA: {last_text}\n")
                return last_text
            except Exception as e:
                recorder.log_step("error", "failed", {"msg": str(e)})
                recorder.complete("failed")

    async def download_image(self, query):
        recorder = TaskRecorder("image_download")
        async with async_playwright() as p:
            try:
                recorder.log_step("browser_launch", "executing")
                browser = await p.chromium.launch(headless=False)
                context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                page = await context.new_page()
                
                recorder.log_step("navigating_ddg", "executing")
                await page.goto("https://duckduckgo.com")
                await page.type('input[name="q"]', query, delay=100)
                await page.keyboard.press("Enter")
                
                recorder.log_step("click_images", "executing")
                await page.get_by_role("link", name="Imágenes").first.click()
                await asyncio.sleep(3)
                
                recorder.log_step("js_extract", "finding_image")
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
                    recorder.log_step("save_file", "success", {"file": filename})
                    recorder.complete("success")
                else:
                    recorder.complete("failed_no_url")
                await browser.close()
            except Exception as e:
                recorder.log_step("error", "failed", {"msg": str(e)})
                recorder.complete("failed")

    def git_sync(self, commit_message):
        """Micro-acción: Sincronizar código con GitHub (Add, Commit, Push)"""
        print(f"📦 Iniciando Sincronización Git: '{commit_message}'")
        try:
            # 1. Git Add
            print("  [1/3] Añadiendo archivos (git add .)...")
            subprocess.run(["git", "add", "."], check=True)
            
            # 2. Git Commit
            print("  [2/3] Creando commit...")
            commit_res = subprocess.run(["git", "commit", "-m", commit_message], capture_output=True, text=True)
            
            if "nothing to commit" in commit_res.stdout or "nothing added to commit" in commit_res.stdout:
                print("🤷‍♂️ No hay cambios nuevos para subir al repositorio.")
                return
            
            print(f"✅ Commit creado con éxito.")
            
            # 3. Git Push
            print("  [3/3] Subiendo cambios a GitHub (git push -u origin main)...")
            push_res = subprocess.run(["git", "push", "-u", "origin", "main"], capture_output=True, text=True)
            
            if push_res.returncode == 0:
                print("🎉 ¡Sincronización completada con éxito!")
            else:
                print(f"❌ Error en Git Push: {push_res.stderr}")
                
        except Exception as e:
            print(f"❌ Error crítico en Git Sync: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(1)
    tool = GeminiToolbox()
    if sys.argv[1] == "chat": asyncio.run(tool.chatgpt(sys.argv[2]))
    elif sys.argv[1] == "image": asyncio.run(tool.download_image(sys.argv[2]))
    elif sys.argv[1] == "git": tool.git_sync(sys.argv[2])
