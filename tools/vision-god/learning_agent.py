import asyncio
from playwright.async_api import async_playwright
import time
import requests
import pyautogui
import io
import sys
import os
import json
import hashlib

# Herramientas Core
sys.path.append(os.path.join(os.getcwd(), 'tools', 'senior-coder'))
from fast_mouse import mouse
sys.path.append(os.path.join(os.getcwd(), 'tools', 'self-corrector'))
from action_auditor import auditor

VISION_URL = "http://127.0.0.1:8000/analyze"
MEMORY_FILE = os.path.join("tools", "self-corrector", "patterns", "senior_memory.json")

class SeniorLearningAgent:
    def __init__(self, target_file="GATO_SENIOR_FINAL.png"):
        self.target_file = target_file
        self.last_view = None
        self.memory = self.load_memory()
        print(f"--- CEREBRO SENIOR ACTIVADO ({len(self.memory)} experiencias) ---")

    def load_memory(self):
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r') as f: return json.load(f)
        return {}

    def save_memory(self):
        with open(MEMORY_FILE, 'w') as f: json.dump(self.memory, f, indent=2)

    async def get_view(self):
        try:
            screenshot = pyautogui.screenshot()
            img_bytes = io.BytesIO()
            screenshot.save(img_bytes, format='PNG')
            r = requests.post(VISION_URL, files={'file': ('s.png', img_bytes.getvalue(), 'image/png')}, timeout=15)
            self.last_view = r.json()
            # Generar un hash unico de la interfaz
            elements_str = "".join([f"{el['type']}{el.get('content','')}" for el in self.last_view['elements'][:10]])
            return hashlib.md5(elements_str.encode()).hexdigest()
        except: return "unknown"

    def find_best_target(self, query, state_hash, forbidden_ids):
        """Busca el mejor objetivo ignorando los que ya fallaron"""
        if not self.last_view: return None
        for i, el in enumerate(self.last_view['elements']):
            if i in forbidden_ids: continue
            content = el.get('content', '')
            if content and query.lower() in content.lower():
                box = self.last_view['coordinates'].get(str(i))
                if box: return i, (box[0] + box[2]/2, box[1] + box[3]/2)
        return None, None

    async def run(self):
        print(f"--- MISION: OBTENER {self.target_file} ---")
        if os.path.exists(self.target_file): os.remove(self.target_file)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
            page = await browser.new_page()
            
            forbidden_actions = {} # state_hash -> list of failed element IDs

            while not os.path.exists(self.target_file):
                # 1. Asegurar HOME
                if page.url == "about:blank":
                    await page.goto("https://duckduckgo.com")
                    await asyncio.sleep(2)

                current_url = page.url
                state_hash = await self.get_view()
                if state_hash not in forbidden_actions: forbidden_actions[state_hash] = []

                print(f"\n[SITUACION]: {state_hash} | URL: {current_url}")

                # FASE A: BUSQUEDA (Si estamos en el home)
                if "duckduckgo.com" in current_url and "/?q=" not in current_url:
                    target_id, pos = self.find_best_target("search", state_hash, forbidden_actions[state_hash])
                    if pos:
                        print(f"Probando objetivo ID {target_id} en {pos}...")
                        mouse.click(pos[0], pos[1])
                        pyautogui.write("gatos graciosos", interval=0.01)
                        pyautogui.press('enter')
                        await asyncio.sleep(4)
                        
                        # VALIDACION CRITICA: ¿Cambio la URL?
                        if page.url == current_url:
                            print(f"❌ FALLO DE PROGRESO: La URL no cambio. ID {target_id} vetado.")
                            forbidden_actions[state_hash].append(target_id)
                            # Táctica B: Enter directo
                            pyautogui.press('enter')
                        continue
                    else:
                        print("No veo objetivos nuevos. Usando Enter de emergencia...")
                        pyautogui.press('enter')
                        await asyncio.sleep(2)

                # FASE B: IMAGENES
                if "/?q=" in page.url and "&ia=images" not in page.url:
                    target_id, pos = self.find_best_target("imágenes", state_hash, forbidden_actions[state_hash])
                    if pos:
                        mouse.click(pos[0], pos[1])
                        await asyncio.sleep(4)
                        if page.url == current_url:
                            print(f"❌ FALLO: No saltamos a imagenes. ID {target_id} vetado.")
                            forbidden_actions[state_hash].append(target_id)
                        continue

                # FASE C: CAPTURA
                if "&ia=images" in page.url:
                    cat_candidates = [i for i, el in enumerate(self.last_view['elements']) if el['type'] == 'icon']
                    if cat_candidates:
                        target_id = cat_candidates[min(len(cat_candidates)-1, 5)]
                        box = self.last_view['coordinates'][str(target_id)]
                        cx, cy = box[0] + box[2]/2, box[1] + box[3]/2
                        print(f"Intentando capturar gato ID {target_id}...")
                        mouse.click(cx, cy, button='right')
                        await asyncio.sleep(1.5)
                        pyautogui.press('v')
                        await asyncio.sleep(2)
                        pyautogui.write(self.target_file.split('.')[0], interval=0.05)
                        pyautogui.press('enter')
                        
                        for _ in range(5):
                            if os.path.exists(self.target_file):
                                print("🏁 ¡LOGRADO CON CEREBRO SENIOR!")
                                return
                            time.sleep(1)
                
                print("Esperando re-evaluacion...")
                await asyncio.sleep(1)

            await browser.close()

if __name__ == "__main__":
    agent = SeniorLearningAgent("GATO_FINAL_SENIOR.png")
    asyncio.run(agent.run())
