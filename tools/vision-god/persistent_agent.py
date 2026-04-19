import asyncio
from playwright.async_api import async_playwright
import time
import requests
import pyautogui
import io
import sys
import os
import json

# Herramientas Core
sys.path.append(os.path.join(os.getcwd(), 'tools', 'senior-coder'))
from fast_mouse import mouse
sys.path.append(os.path.join(os.getcwd(), 'tools', 'self-corrector'))
from action_auditor import auditor

VISION_URL = "http://127.0.0.1:8000/analyze"

class SeniorPersistentAgent:
    def __init__(self, target_file="GATO_VERIFICADO.png"):
        self.target_file = target_file
        self.last_view = None
        self.history = [] # Para detectar bucles
        self.attempt_count = 0

    async def observe(self):
        try:
            screenshot = pyautogui.screenshot()
            img_bytes = io.BytesIO()
            screenshot.save(img_bytes, format='PNG')
            r = requests.post(VISION_URL, files={'file': ('s.png', img_bytes.getvalue(), 'image/png')}, timeout=10)
            self.last_view = r.json()
            return True
        except: return False

    def find(self, query):
        if not self.last_view: return None
        for i, el in enumerate(self.last_view['elements']):
            if el.get('content') and query.lower() in el['content'].lower():
                box = self.last_view['coordinates'].get(str(i))
                if box: return box[0] + box[2]/2, box[1] + box[3]/2
        return None

    def is_stuck(self, current_state):
        self.history.append(current_state)
        if len(self.history) > 3:
            self.history.pop(0)
            if len(set(self.history)) == 1: # Los últimos 3 estados son iguales
                return True
        return False

    async def run(self):
        print(f"--- MISION SENIOR: {self.target_file} ---")
        if os.path.exists(self.target_file): os.remove(self.target_file)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
            context = await browser.new_context(no_viewport=True)
            page = await context.new_page()
            
            state = "HOME"
            
            while not os.path.exists(self.target_file):
                print(f"\n[ESTADO]: {state}")
                if self.is_stuck(state):
                    print("🚨 ¡BUCLE DETECTADO! Cambiando estrategia...")
                    await page.goto("https://duckduckgo.com")
                    state = "HOME"
                    self.history = []
                    await asyncio.sleep(2)
                    continue

                if not await self.observe(): continue

                # 1. ESTADO HOME: Buscar
                if state == "HOME":
                    search_pos = self.find("search") or self.find("buscar")
                    if search_pos:
                        mouse.click(search_pos[0], search_pos[1])
                        pyautogui.write("gatos tiernos", interval=0.02)
                        pyautogui.press('enter')
                        state = "WAITING_RESULTS"
                        await asyncio.sleep(3)
                    else:
                        print("No veo la barra, intentando clic central...")
                        pyautogui.click(600, 400)
                        pyautogui.write("gatos tiernos", interval=0.02)
                        pyautogui.press('enter')
                        state = "WAITING_RESULTS"
                    continue

                # 2. ESTADO WAITING: Ir a imagenes
                if state == "WAITING_RESULTS":
                    img_tab = self.find("imágenes") or self.find("images")
                    if img_tab:
                        mouse.click(img_tab[0], img_tab[1])
                        state = "RESULTS_GRID"
                        await asyncio.sleep(3)
                    else:
                        # DIAGNOSTICO: ¿Por que no veo la pestaña?
                        # Si veo el logo de DDG grande, es que la busqueda no se envio
                        if self.find("duckduckgo"):
                            print("Sigo en el home. Re-enviando busqueda...")
                            pyautogui.press('enter')
                        else:
                            print("Parece que estoy en resultados pero no veo la pestaña. Scroll suave...")
                            pyautogui.scroll(-200)
                    continue

                # 3. ESTADO GRID: Elegir gato
                if state == "RESULTS_GRID":
                    cat_candidates = [i for i, el in enumerate(self.last_view['elements']) if el['type'] == 'icon']
                    if cat_candidates:
                        # Elegir uno que este en el centro
                        target_id = cat_candidates[min(len(cat_candidates)-1, 5)]
                        box = self.last_view['coordinates'][str(target_id)]
                        cx, cy = box[0] + box[2]/2, box[1] + box[3]/2
                        print(f"Gato fijado en {cx, cy}. Clic derecho...")
                        mouse.click(cx, cy, button='right')
                        state = "SAVE_MENU"
                        await asyncio.sleep(2)
                    else:
                        print("No veo imagenes, bajando un poco...")
                        pyautogui.scroll(-500)
                    continue

                # 4. ESTADO SAVE: Guardar
                if state == "SAVE_MENU":
                    print("Enviando comando de guardado...")
                    pyautogui.press('v')
                    await asyncio.sleep(2)
                    pyautogui.write(self.target_file.split('.')[0], interval=0.05)
                    pyautogui.press('enter')
                    
                    # Verificacion fisica
                    print("Verificando disco...")
                    for _ in range(5):
                        if os.path.exists(self.target_file):
                            print("✅ ¡LOGRADO!")
                            state = "FINISHED"
                            break
                        time.sleep(1)
                    if state != "FINISHED":
                        print("El guardado fallo. Volviendo a la cuadricula...")
                        state = "RESULTS_GRID"

            await browser.close()

if __name__ == "__main__":
    agent = SeniorPersistentAgent("GATO_SENIOR.png")
    asyncio.run(agent.run())
