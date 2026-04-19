import asyncio
from playwright.async_api import async_playwright
import os
import requests
import io
import base64
import time
import pyautogui
import sys
import random

# Importar el humanizador de mouse
sys.path.append(os.path.join(os.getcwd(), 'tools', 'ghost-vision'))
from mouse_humanizer import click_human, move_human

async def human_type(text):
    for char in text:
        pyautogui.write(char)
        time.sleep(random.uniform(0.05, 0.2))

async def download_cat_stealth():
    url_home = "https://duckduckgo.com"
    vision_url = "http://127.0.0.1:8000/analyze"
    
    print("--- INICIALIZANDO PROTOCOLO PATO SILENCIOSO (DuckDuckGo) ---")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()
        
        # 1. Entrar a DuckDuckGo Home
        print("Paso 1: Entrando a DuckDuckGo...")
        await page.goto(url_home)
        await asyncio.sleep(2)

        # 2. Buscar barra de busqueda
        print("Buscando barra de busqueda visualmente...")
        screenshot_bytes = await page.screenshot()
        files = {'file': ('ddg_home.png', screenshot_bytes, 'image/png')}
        response = requests.post(vision_url, files=files)
        data = response.json()
        
        search_id = -1
        if 'elements' in data:
            for i, el in enumerate(data['elements']):
                if not el.get('content'): continue
                if any(word in el['content'].lower() for word in ["search", "buscar", "encontrar"]):
                    search_id = i
                    break
        
        if search_id != -1:
            box = data['coordinates'][str(search_id)]
            cx, cy = box[0] + (box[2]/2), box[1] + (box[3]/2)
            click_human(cx, cy + 90)
            print("Paso 2: Escribiendo 'gatos bonitos'...")
            await human_type("gatos bonitos")
            pyautogui.press('enter')
            await asyncio.sleep(4)
        else:
            print("No vi la barra, clic central y escribir...")
            pyautogui.click(600, 400)
            await human_type("gatos bonitos")
            pyautogui.press('enter')
            await asyncio.sleep(4)

        # 3. Ir a la pestaña "Imagenes"
        print("Paso 3: Localizando pestaña 'Imágenes' en DDG...")
        screenshot_bytes = await page.screenshot()
        files = {'file': ('ddg_results.png', screenshot_bytes, 'image/png')}
        response = requests.post(vision_url, files=files)
        data = response.json()
        
        img_tab_id = -1
        if 'elements' in data:
            for i, el in enumerate(data['elements']):
                if el.get('content') and "imágenes" in el['content'].lower():
                    img_tab_id = i
                    break
        
        if img_tab_id != -1:
            box = data['coordinates'][str(img_tab_id)]
            cx, cy = box[0] + (box[2]/2), box[1] + (box[3]/2)
            click_human(cx, cy + 90)
            await asyncio.sleep(3)
        else:
            print("No vi la pestaña 'Imágenes', probando clic en zona superior izquierda...")
            pyautogui.click(250, 160) # Posicion tipica en DDG
            await asyncio.sleep(3)

        # 4. Seleccionar Gato
        print("Paso 4: Seleccionando el gato más bonito...")
        screenshot_bytes = await page.screenshot()
        files = {'file': ('ddg_cats.png', screenshot_bytes, 'image/png')}
        response = requests.post(vision_url, files=files)
        data = response.json()
        
        target_coords = None
        if 'elements' in data:
            for i, el in enumerate(data['elements']):
                # Buscar un icono (imagen) que no sea texto pequeño
                if el['type'] == 'icon' or 'text' not in el['type']:
                    box = data['coordinates'].get(str(i))
                    if box and 300 < box[0] < 1000 and 300 < box[1] < 700:
                        target_coords = box
                        break
        
        cx, cy = (target_coords[0] + target_coords[2]/2, target_coords[1] + target_coords[3]/2) if target_coords else (600, 500)
        
        print(f"Haciendo clic derecho en el gato en ({cx}, {cy})...")
        click_human(cx, cy + 90, button='right')
        await asyncio.sleep(2)
        
        print("Guardando el botín (v)...")
        pyautogui.press('v')
        await asyncio.sleep(2.5)
        
        pyautogui.write("GATO_DUCK_STEALTH", interval=0.1)
        pyautogui.press('enter')
        print("--- OPERACIÓN DUCK COMPLETA: GATO EN EL REPO ---")
            
        await asyncio.sleep(5)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(download_cat_stealth())
