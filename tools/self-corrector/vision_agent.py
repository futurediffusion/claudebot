import asyncio
from playwright.async_api import async_playwright
import time
import requests
import pyautogui
from PIL import Image
import io
import os
import sys
import random

# Rutas y Configuración
VISION_URL = "http://127.0.0.1:8000/analyze"

class GodEyeAgent:
    def __init__(self):
        print("--- AGENTE VISUAL NIVEL DIOS (Auto-Browser Edition) ---")
        self.state = "START"
        self.last_elements = []
        self.last_coords = {}
        self.browser = None
        self.page = None

    async def look(self):
        """Toma una captura real del escritorio (incluyendo el navegador)"""
        # Usamos pyautogui.screenshot para capturar todo el contexto de Windows
        screenshot = pyautogui.screenshot()
        img_byte_arr = io.BytesIO()
        screenshot.save(img_byte_arr, format='PNG')
        
        try:
            response = requests.post(VISION_URL, files={'file': ('screen.png', img_byte_arr.getvalue(), 'image/png')})
            data = response.json()
            self.last_elements = data['elements']
            self.last_coords = data['coordinates']
            return True
        except Exception as e:
            print(f"Error de vision: {e}")
            return False

    def find(self, text_query):
        """Busca un objeto por texto y devuelve su centro"""
        for i, el in enumerate(self.last_elements):
            content = el.get('content', '')
            if content and text_query.lower() in content.lower():
                box = self.last_coords.get(str(i))
                if box:
                    return box[0] + (box[2]/2), box[1] + (box[3]/2)
        return None

    def find_cat_image(self):
        """Busca una imagen grande en el area central"""
        for i, el in enumerate(self.last_elements):
            if el['type'] == 'icon':
                box = self.last_coords.get(str(i))
                if box and 300 < box[0] < 1200 and 300 < box[1] < 800:
                    return box[0] + (box[2]/2), box[1] + (box[3]/2)
        return None

    async def run(self):
        async with async_playwright() as p:
            # 1. Abrir Navegador
            print("Paso 0: Materializando navegador...")
            self.browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
            context = await self.browser.new_context(no_viewport=True)
            self.page = await context.new_page()
            
            # Aplicar sigilo si es posible
            try:
                from playwright_stealth import stealth_async
                await stealth_async(self.page)
            except: pass

            await self.page.goto("https://duckduckgo.com")
            await asyncio.sleep(3)

            # Bucle de Decision Visual
            while self.state != "FINISHED":
                print(f"\n[CEREBRO]: Evaluando estado {self.state}...")
                if not await self.look(): break
                
                # LOGICA DE ESTADOS
                if self.state == "START":
                    # Buscar barra o simplemente escribir si DDG ya tiene el foco
                    print("Buscando barra de busqueda...")
                    target = self.find("search") or self.find("buscar")
                    if target:
                        pyautogui.click(target)
                    else:
                        pyautogui.click(600, 400) # Clic de seguridad al centro
                    
                    pyautogui.write("gatos tiernos", interval=0.02)
                    pyautogui.press('enter')
                    self.state = "WAITING_RESULTS"
                    await asyncio.sleep(4)
                    continue

                if self.state == "WAITING_RESULTS":
                    print("Buscando pestaña 'Imágenes'...")
                    target = self.find("imágenes") or self.find("images")
                    if target:
                        pyautogui.click(target)
                        self.state = "CHOOSING_CAT"
                        await asyncio.sleep(4)
                    else:
                        print("No veo la pestaña, esperando un poco mas...")
                        await asyncio.sleep(2)
                    continue

                if self.state == "CHOOSING_CAT":
                    print("Eligiendo el gato mas bonito...")
                    cat_pos = self.find_cat_image()
                    if cat_pos:
                        print(f"¡Gato fijado en {cat_pos}! Clic derecho...")
                        pyautogui.rightClick(cat_pos)
                        self.state = "SAVING"
                        await asyncio.sleep(1.5)
                    else:
                        print("No veo gatos claros, haciendo scroll...")
                        pyautogui.scroll(-500)
                        await asyncio.sleep(1)
                    continue

                if self.state == "SAVING":
                    print("Guardando imagen...")
                    pyautogui.press('v') # Atajo 'Guardar como'
                    await asyncio.sleep(2.5)
                    pyautogui.write("GATO_VISION_GOD_FINAL", interval=0.05)
                    pyautogui.press('enter')
                    print("--- MISION CUMPLIDA ---")
                    self.state = "FINISHED"

            await asyncio.sleep(5)
            await self.browser.close()

if __name__ == "__main__":
    agent = GodEyeAgent()
    asyncio.run(agent.run())
