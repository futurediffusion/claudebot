import asyncio
from playwright.async_api import async_playwright
import os
import requests
import io
import base64
import time
import pyautogui
import sys

# Motor de vision acelerado
VISION_URL = "http://127.0.0.1:8000/analyze"

def get_vision_target(query_text, filter_type=None):
    # Captura absoluta para punteria 1:1
    screenshot = pyautogui.screenshot()
    img_byte_arr = io.BytesIO()
    screenshot.save(img_byte_arr, format='PNG')
    
    files = {'file': ('screen.png', img_byte_arr.getvalue(), 'image/png')}
    try:
        response = requests.post(VISION_URL, files=files)
        data = response.json()
        
        for i, el in enumerate(data['elements']):
            content = el.get('content', '')
            if not content: continue
            if query_text.lower() in content.lower():
                if filter_type and el['type'] != filter_type: continue
                box = data['coordinates'][str(i)]
                # Centro exacto del ID
                return box[0] + (box[2] / 2), box[1] + (box[3] / 2)
    except:
        pass
    return None

async def speedrun():
    print("--- INICIANDO SPEEDRUN VISUAL (DuckDuckGo) ---")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()
        
        # 1. Navegar
        await page.goto("https://duckduckgo.com")
        await asyncio.sleep(1) # Solo 1s para render inicial

        # 2. Buscar Barra y Escribir (Inmediato)
        print("⚡️ Localizando barra...")
        target = get_vision_target("search")
        if not target: target = (960, 400) # Fallback centro
        pyautogui.click(target)
        pyautogui.write("gatos bonitos", interval=0.01)
        pyautogui.press('enter')
        
        # 3. Ir a Imagenes
        print("⚡️ Saltando a Imagenes...")
        await asyncio.sleep(2)
        target = get_vision_target("imágenes")
        if not target: target = (250, 160)
        pyautogui.click(target)
        
        # 4. Seleccionar Gato (Vision GPU)
        print("⚡️ Eligiendo el gato mas rapido...")
        await asyncio.sleep(2)
        # Tomamos captura para buscar un icono de imagen grande
        screenshot = pyautogui.screenshot()
        img_byte_arr = io.BytesIO()
        screenshot.save(img_byte_arr, format='PNG')
        files = {'file': ('cats.png', img_byte_arr.getvalue(), 'image/png')}
        response = requests.post(VISION_URL, files=files).json()
        
        cat_coords = (600, 450) # Default
        for i, el in enumerate(response['elements']):
            box = response['coordinates'].get(str(i))
            if box and el['type'] == 'icon' and 400 < box[0] < 1000 and 300 < box[1] < 700:
                cat_coords = (box[0] + box[2]/2, box[1] + box[3]/2)
                break
        
        # 5. Clic Derecho y Guardar
        print("⚡️ Clic Derecho y Guardado Express...")
        pyautogui.rightClick(cat_coords)
        await asyncio.sleep(0.5)
        pyautogui.press('v') # Atajo de guardado
        
        await asyncio.sleep(1.5)
        pyautogui.write("SPEEDRUN_CAT_GOD", interval=0.01)
        pyautogui.press('enter')
        
        print("--- SPEEDRUN FINALIZADO CON ÉXITO ---")
        await asyncio.sleep(2)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(speedrun())
