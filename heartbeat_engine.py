import asyncio
import json
import os
import requests
from datetime import datetime, timedelta
from logger_pro import setup_logger

# Configuración
STATE_FILE = "heartbeat_state.json"
CHECK_INTERVAL = 900 
OLLAMA_URL = "http://localhost:11434/api/generate"

log = setup_logger('heartbeat_engine')

class HeartbeatEngine:
    def __init__(self):
        self.state = self.load_state()
        self.tasks = [
            {"id": "system_health", "command": "python skills/system-medic/scripts/medic.py status", "interval": 4},
            {"id": "health_sync", "command": "python google_fit_sync.py", "interval": 1},
            {"id": "git_backup", "command": "python scripts/heartbeat/git_backup.py", "interval": 12},
            {"id": "vector_index", "command": "python scripts/heartbeat/vector_index.py", "interval": 24},
            {"id": "market_scout", "command": "python scripts/heartbeat/market_scout.py", "interval": 48},
            {"id": "system_pruning", "command": "python scripts/heartbeat/system_pruning.py", "interval": 168}
        ]

    def load_state(self):
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f: return json.load(f)
        return {}

    def save_state(self):
        with open(STATE_FILE, 'w') as f: json.dump(self.state, f, indent=4)

    async def ask_ollama_for_fix(self, task_id, error_msg):
        """Consulta a Ollama local para obtener una solución rápida."""
        prompt = f"""
        ERROR EN CLAUDEBOT HEARTBEAT:
        Tarea: {task_id}
        Error: {error_msg}
        
        Eres el Ingeniero de Guardia de Claudebot. El comando de arriba ha fallado.
        Dame un comando de terminal UNICO para intentar solucionar este problema.
        Responde SOLO con el comando dentro de etiquetas <FIX>comando</FIX>.
        Si no sabes qué hacer, responde <FIX>None</FIX>.
        """
        log.info(f"Consultando a Ollama por solución para {task_id}...")
        try:
            payload = {"model": "qwen2.5-coder:3b", "prompt": prompt, "stream": False}
            resp = requests.post(OLLAMA_URL, json=payload, timeout=10)
            text = resp.json().get('response', '')
            if "<FIX>" in text:
                return text.split("<FIX>")[1].split("</FIX>")[0].strip()
        except Exception as e:
            log.error(f"Ollama no disponible: {e}")
        return None

    async def run_task(self, task, retry=True):
        log.info(f"Iniciando: {task['id']}")
        process = await asyncio.create_subprocess_shell(
            task['command'],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            log.info(f"Éxito: {task['id']}")
            self.state[task['id']] = datetime.now().isoformat()
            self.save_state()
        else:
            err_msg = stderr.decode(errors='replace')
            log.error(f"Fallo en {task['id']}: {err_msg}")
            
            if retry:
                fix_command = await self.ask_ollama_for_fix(task['id'], err_msg)
                if fix_command and fix_command != "None":
                    log.warning(f"Intentando Auto-Reparación con: {fix_command}")
                    repair_proc = await asyncio.create_subprocess_shell(fix_command)
                    await repair_proc.wait()
                    # Re-intentar la tarea original una vez
                    await self.run_task(task, retry=False)

    async def start(self):
        log.info("--- MOTOR PROACTIVO V2 (SELF-HEALING) INICIADO ---")
        while True:
            now = datetime.now()
            for task in self.tasks:
                last_run_str = self.state.get(task['id'])
                if not last_run_str or (now - datetime.fromisoformat(last_run_str) >= timedelta(hours=task['interval'])):
                    await self.run_task(task)
            await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    engine = HeartbeatEngine()
    asyncio.run(engine.start())
