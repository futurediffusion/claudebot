import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import os
import requests
import io
import base64
import time
from PIL import Image

# Importar el humanizador de mouse
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from mouse_humanizer import click_human, move_human

class GhostBrowser:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.vision_url = "http://127.0.0.1:8000/analyze"

    async def start(self, url="https://www.google.com"):
        print(f"--- INICIANDO NAVEGADOR FANTASMA (Stealth Mode) ---")
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False) # Visible para que veas la magia
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        self.page = await self.context.new_page()
        
        # Aplicar sigilo
        await stealth_async(self.page)
        
        print(f"Navegando a {url}...")
        await self.page.goto(url)
        await asyncio.sleep(2) # Esperar renderizado inicial

    async def see_and_click(self, query_text):
        print(f"Buscando '{query_text}' visualmente...")
        
        # 1. Tomar captura de la pagina
        screenshot_bytes = await self.page.screenshot()
        
        # 2. Enviar al servidor de vision
        files = {'file': ('page.png', screenshot_bytes, 'image/png')}
        try:
            response = requests.post(self.vision_url, files=files)
            data = response.json()
            
            # 3. Buscar el elemento
            target_id = -1
            for i, el in enumerate(data['elements']):
                if el.get('content') and query_text.lower() in el['content'].lower():
                    target_id = i
                    break
            
            if target_id != -1:
                box = data['coordinates'][str(target_id)]
                # Las coordenadas de la captura de pantalla pueden necesitar ajuste al viewport
                # OmniParser detecta sobre la imagen enviada (1280x720)
                cx = box[0] + (box[2] / 2)
                cy = box[1] + (box[3] / 2)
                
                # Obtener posicion de la ventana del navegador en el escritorio (simplificado para test)
                # Para precision total usaremos pygetwindow, pero por ahora asumimos pantalla completa o fija
                print(f"Elemento hallado! Realizando clic humano en ({cx}, {cy})")
                click_human(cx, cy + 80) # +80 por la barra de herramientas del navegador
                return True
            else:
                print(f"No encontre '{query_text}' en la pantalla.")
                return False
                
        except Exception as e:
            print(f"Error de vision: {e}")
            return False

    async def close(self):
        await self.browser.close()

async def main():
    ghost = GhostBrowser()
    await ghost.start("https://www.freepik.com")
    # Ejemplo: buscar visualmente el boton de login o un input
    # await ghost.see_and_click("search")
    print("Navegador listo. Esperando ordenes visuales...")
    await asyncio.sleep(10) # Mantener abierto para ver
    await ghost.close()

if __name__ == "__main__":
    asyncio.run(main())
