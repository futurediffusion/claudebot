import time
import requests
import pyautogui
from PIL import Image, ImageChops
import io
import json
import os

class ActionAuditor:
    def __init__(self):
        self.vision_url = "http://127.0.0.1:8000/analyze"
        self.patterns_file = os.path.join("tools", "self-corrector", "patterns", "failures.json")
        if not os.path.exists(self.patterns_file):
            with open(self.patterns_file, 'w') as f:
                json.dump([], f)

    def get_screen_hash(self):
        # Captura rapida para comparar cambios
        screenshot = pyautogui.screenshot()
        # Reducimos tamaño para que la comparacion sea mas veloz
        screenshot = screenshot.resize((128, 72))
        return screenshot

    def log_failure(self, action_type, target, reason):
        print(f"❌ FALLO DETECTADO en {action_type} sobre {target}: {reason}")
        with open(self.patterns_file, 'r+') as f:
            data = json.load(f)
            data.append({
                "timestamp": time.time(),
                "action": action_type,
                "target": target,
                "reason": reason
            })
            f.seek(0)
            json.dump(data, f, indent=2)

    def execute_with_verify(self, func, *args, **kwargs):
        """Ejecuta una funcion de pyautogui y verifica si la pantalla cambio"""
        pre_screen = self.get_screen_hash()
        
        # Ejecutar accion
        print(f"Ejecutando accion: {func.__name__} {args}")
        func(*args, **kwargs)
        
        # Esperar cambio visual
        time.sleep(1.5)
        post_screen = self.get_screen_hash()
        
        # Comparar (Diferencia de pixeles)
        diff = ImageChops.difference(pre_screen, post_screen)
        if not diff.getbbox():
            self.log_failure(func.__name__, str(args), "Pantalla estatica tras la accion")
            return False
        
        print("✅ Accion verificada: Cambio visual detectado.")
        return True

# Singleton para uso global
auditor = ActionAuditor()

if __name__ == "__main__":
    # Test: intentar un clic donde no hay nada
    auditor.execute_with_verify(pyautogui.click, 10, 10)
