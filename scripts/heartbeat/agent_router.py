import os
import subprocess
import sys
import requests
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID")

def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_USER_ID:
        print("Telegram no configurado. Solo salida por consola.")
        print(text)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # Recortar texto si es muy largo para Telegram
    if len(text) > 3900:
        text = text[:3900] + "\n...[Recortado]"
        
    payload = {"chat_id": TELEGRAM_USER_ID, "text": text}
    requests.post(url, json=payload)

def run_cmd(cmd):
    try:
        # Se usa shell=True para ejecutar comandos del sistema
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Timeout"

def execute_with_fallback(prompt):
    print("Iniciando Enrutador de Agentes (Agent Router)...")
    
    # 1. Gemini Models (Rotación por cuota)
    gemini_models = ["gemini-2.0-flash", "gemini-3.1-pro-preview", "gemini-1.5-pro"]
    for model in gemini_models:
        print(f"-> Intentando con Gemini CLI ({model})...")
        safe_prompt = prompt.replace('"', '\\"')
        cmd = f'gemini -m {model} -y -p "{safe_prompt}"'
        code, out, err = run_cmd(cmd)
        
        # Validar si falló por cuota ("quota", "exhausted", "429")
        out_lower = (out + err).lower()
        if code == 0 and "quota" not in out_lower and "exhausted" not in out_lower and "429" not in out_lower:
            return f"🌟 *Vía Gemini ({model})*\n\n{out}"
        else:
            print(f"   [X] Gemini {model} falló o sin tokens. Saltando...")

    # 2. Minimax (OpenCode)
    print("-> Intentando con Minimax (OpenCode CLI)...")
    cmd = f'opencode run "{safe_prompt}" -m opencode/minimax-m2.5-free --pure'
    code, out, err = run_cmd(cmd)
    out_lower = (out + err).lower()
    if code == 0 and "error" not in out_lower and "rate limit" not in out_lower:
        return f"☁️ *Vía Minimax (Nube Gratis)*\n\n{out}"
    else:
        print("   [X] Minimax falló.")

    # 3. Claude Code
    print("-> Intentando con Claude Code...")
    cmd = f'claude -p "{safe_prompt}"'
    code, out, err = run_cmd(cmd)
    if code == 0 and "error" not in (out + err).lower():
        return f"🧠 *Vía Claude Code*\n\n{out}"
    else:
        print("   [X] Claude Code falló.")

    # 4. Local Ollama (Qwen 3b)
    print("-> Todos los servicios cloud fallaron. Usando Local Ollama...")
    try:
        payload = {"model": "qwen2.5-coder:3b", "prompt": prompt, "stream": False}
        resp = requests.post("http://localhost:11434/api/generate", json=payload, timeout=60)
        answer = resp.json().get('response', '')
        if answer:
            return f"🖥️ *Vía Local Qwen 3b (Offline)*\n\n{answer}"
    except Exception as e:
        print(f"   [X] Ollama falló: {e}")

    return "❌ *Fallo Total del Enjambre*\nNingún agente pudo completar la tarea."

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # El prompt se pasa como argumento al script
        prompt = " ".join(sys.argv[1:])
        resultado = execute_with_fallback(prompt)
        send_telegram(resultado)
    else:
        print("Uso: python agent_router.py \"Tu prompt aquí\"")
