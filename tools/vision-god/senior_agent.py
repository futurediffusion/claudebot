import asyncio
from playwright.async_api import async_playwright
import time
import requests
import pyautogui
import io
import sys
import os

# Importar herramientas Senior
sys.path.append(os.path.join(os.getcwd(), 'tools', 'senior-coder'))
from fast_mouse import mouse
sys.path.append(os.path.join(os.getcwd(), 'tools', 'self-corrector'))
from action_auditor import auditor

VISION_URL = "http://127.0.0.1:8000/analyze"

class SeniorVisionAgent:
    """Agente de Vision de Nivel Senior (Karpathy-Style)"""
    
    def __init__(self):
        self.state = "INIT"
        self.browser = None
        self.page = None
        self.last_view = None

    async def observe(self):
        """Metodo central de percepcion: mira y analiza"""
        screenshot = pyautogui.screenshot()
        img_bytes = io.BytesIO()
        screenshot.save(img_bytes, format='PNG')
        
        try:
            r = requests.post(VISION_URL, files={'file': ('s.png', img_bytes.getvalue(), 'image/png')}, timeout=10)
            self.last_view = r.json()
            return True
        except Exception as e:
            print(f"Error de percepcion: {e}")
            return False

    def get_target(self, query, element_type=None):
        """Busqueda robusta de objetivos interactuables"""
        if not self.last_view: return None
        
        for i, el in enumerate(self.last_view['elements']):
            content = el.get('content', '')
            if not content: continue
            
            if query.lower() in content.lower():
                if element_type and el['type'] != element_type: continue
                box = self.last_view['coordinates'].get(str(i))
                if box:
                    return box[0] + (box[2]/2), box[1] + (box[3]/2)
        return None

    async def safe_action(self, target_query, action_func, *args, **kwargs):
        """Ejecuta una accion solo si el objetivo es verificado visualmente"""
        print(f"--- ACCION: {target_query} ---")
        if not await self.observe(): return False
        
        target = self.get_target(target_query)
        if target:
            # Usamos el auditor para verificar que la pantalla cambie
            return auditor.execute_with_verify(action_func, target[0], target[1], *args, **kwargs)
        
        print(f"❌ Error: Objetivo '{target_query}' no hallado visualmente.")
        return False

    async def run(self, search_term="gatos"):
        print("--- DESPLEGANDO AGENTE SENIOR (Speedrun Mode) ---")
        
        async with async_playwright() as p:
            self.browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
            self.context = await self.browser.new_context(no_viewport=True)
            self.page = await self.context.new_page()
            
            # Navegar
            await self.page.goto("https://duckduckgo.com")
            await asyncio.sleep(2)

            # 1. Buscar
            if await self.safe_action("search", mouse.click):
                pyautogui.write(search_term, interval=0.01)
                pyautogui.press('enter')
                await asyncio.sleep(3)
            
            # 2. Ir a Imagenes
            if await self.safe_action("imágenes", mouse.click):
                await asyncio.sleep(3)

            # 3. Seleccionar Gato (Vision Interactiva)
            await self.observe()
            cat_pos = None
            for i, el in enumerate(self.last_view['elements']):
                if el['type'] == 'icon':
                    box = self.last_view['coordinates'].get(str(i))
                    if box and 300 < box[0] < 1200 and 200 < box[1] < 700:
                        cat_pos = (box[0] + box[2]/2, box[1] + box[3]/2)
                        break
            
            if cat_pos:
                if auditor.execute_with_verify(mouse.click, cat_pos[0], cat_pos[1], button='right'):
                    await asyncio.sleep(1)
                    pyautogui.press('v')
                    await asyncio.sleep(2)
                    pyautogui.write(f"SENIOR_GATO_{int(time.time())}", interval=0.05)
                    pyautogui.press('enter')
                    print("🏁 MISION COMPLETADA CON ÉXITO")
            
            await asyncio.sleep(4)
            await self.browser.close()

if __name__ == "__main__":
    agent = SeniorVisionAgent()
    asyncio.run(agent.run("gatos graciosos"))
