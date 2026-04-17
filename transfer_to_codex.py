import win32com.client
import time
import sys
import os

# Añadimos el path para usar el World Model
sys.path.append(os.getcwd())
from orchestrator.core.world_model import WorldModelEngine

def transfer_instruction():
    world = WorldModelEngine(agent_name="gemini_transfer")
    shell = win32com.client.Dispatch("WScript.Shell")
    
    print("🌍 [WORLD] Observando el escritorio...")
    state = world.observe_desktop()
    
    # 1. Localizar Notepad y Codex
    notepad = next((app for app in state["desktop"]["open_apps"] if "notepad" in app["process_name"].lower() or "bloc de notas" in app["title"].lower()), None)
    codex = next((app for app in state["desktop"]["open_apps"] if "codex" in app["process_name"].lower() or "codex" in app["title"].lower()), None)
    
    if not notepad:
        print("❌ Error: No encontré el Bloc de Notas abierto.")
        return
    if not codex:
        print("❌ Error: No encontré la ventana de Codex abierta.")
        return

    print(f"📍 Notepad detectado: {notepad['title']}")
    print(f"📍 Codex detectado: {codex['title']}")

    # 2. PROCESO DE COPIA (Notepad)
    print("\n📝 [FASE 1] Copiando instrucción de Notepad...")
    if shell.AppActivate(notepad["pid"]):
        time.sleep(1)
        shell.SendKeys("^a") # Seleccionar todo
        time.sleep(0.3)
        shell.SendKeys("^c") # Copiar
        print("✅ Texto copiado al portapapeles.")
    else:
        print("❌ Falló el foco en Notepad.")
        return

    # 3. PROCESO DE PEGADO (Codex)
    print("\n🤖 [FASE 2] Entregando instrucción a Codex...")
    if shell.AppActivate(codex["pid"]):
        time.sleep(1)
        shell.SendKeys("^v") # Pegar
        time.sleep(0.5)
        shell.SendKeys("{ENTER}") # Enviar
        print("✅ Instrucción pegada y enviada a Codex.")
    else:
        # Reintento por título si el PID falla
        if shell.AppActivate("Codex"):
            time.sleep(1)
            shell.SendKeys("^v")
            time.sleep(0.5)
            shell.SendKeys("{ENTER}")
            print("✅ Enviado a Codex (vía título).")
        else:
            print("❌ Falló el foco en Codex.")

if __name__ == "__main__":
    transfer_instruction()
