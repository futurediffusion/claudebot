import asyncio
from playwright.async_api import async_playwright
import os
import requests
import io
import base64
import time
import pyautogui
import sys
import json

# Importar el Auditor y el Servidor de Vision
sys.path.append(os.path.join(os.getcwd(), 'tools', 'self-corrector'))
from action_auditor import auditor

VISION_URL = "http://127.0.0.1:8000/analyze"

def get_interactable_target(query_text, filter_type=None):
    """Usa la capa de interactividad de OmniParser para hallar coordenadas exactas"""
    print(f"🔍 Escaneando interactividad para: '{query_text}'...")
    screenshot = pyautogui.screenshot()
    img_byte_arr = io.BytesIO()
    screenshot.save(img_byte_arr, format='PNG')
    files = {'file': ('screen.png', img_byte_arr.getvalue(), 'image/png')}
    
    try:
        response = requests.post(VISION_URL, files=files)
        data = response.json()
        
        # Recorrer todos los objetos detectados por OmniParser
        for i, el in enumerate(data['elements']):
            content = el.get('content', '')
            if not content: continue
            
            if query_text.lower() in content.lower():
                if filter_type and el['type'] != filter_type: continue
                
                # Obtener coordenadas del Bounding Box [x, y, w, h]
                box = data['coordinates'].get(str(i))
                if box:
                    # Calcular el centro exacto del objeto interactuable
                    cx = box[0] + (box[2] / 2)
                    cy = box[1] + (box[3] / 2)
                    print(f"🎯 Blanco fijado: ID {i} ({el['type']}) en ({cx}, {cy})")
                    return cx, cy
    except Exception as e:
        print(f"Error en capa de vision: {e}")
    return None

async def run_mission():
    print("--- INICIALIZANDO MISION OMNI-AUDITED V3.0 ---")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()
        
        # 1. Navegar
        await page.goto("https://duckduckgo.com")
        await asyncio.sleep(2)

        # 2. Clic en Barra (Interactividad Real)
        print("Paso 1: Buscando barra de busqueda interactuable...")
        target = get_interactable_target("search")
        if not target: 
            print("⚠️ No detecte objeto interactuable 'search', usando vision de respaldo...")
            target = (960, 450)
        
        # Ejecutar con verificacion de cambio visual
        auditor.execute_with_verify(pyautogui.click, target[0], target[1])
        pyautogui.write("gatos bonitos", interval=0.01)
        pyautogui.press('enter')
        await asyncio.sleep(3)

        # 3. Pestaña Imagenes (Interactividad Real)
        print("Paso 2: Buscando pestaña de imágenes...")
        target = get_interactable_target("imágenes")
        if target:
            auditor.execute_with_verify(pyautogui.click, target[0], target[1])
        else:
            print("⚠️ Fallo al localizar pestaña 'Imágenes'.")
        await asyncio.sleep(3)

        # 4. Seleccion de Gato (Interactividad Real)
        print("Paso 3: Localizando el icono del gato...")
        # Buscamos el primer objeto tipo 'icon' en el area central
        screenshot = pyautogui.screenshot()
        img_byte_arr = io.BytesIO()
        screenshot.save(img_byte_arr, format='PNG')
        files = {'file': ('screen.png', img_byte_arr.getvalue(), 'image/png')}
        data = requests.post(VISION_URL, files=files).json()
        
        cat_coords = None
        for i, el in enumerate(data['elements']):
            box = data['coordinates'].get(str(i))
            # Filtrar por zona central y tipo icono/imagen
            if box and 300 < box[0] < 1200 and 300 < box[1] < 800:
                cat_coords = (box[0] + box[2]/2, box[1] + box[3]/2)
                print(f"🎯 Gato interactuable hallado en ID {i}")
                break
        
        if cat_coords:
            auditor.execute_with_verify(pyautogui.rightClick, cat_coords[0], cat_coords[1])
        else:
            print("⚠️ No encontre ningun gato interactuable.")
            cat_coords = (600, 500)
            pyautogui.rightClick(cat_coords)

        # 5. Guardado
        await asyncio.sleep(1)
        print("Paso 4: Comando de guardado...")
        pyautogui.press('v')
        await asyncio.sleep(2)
        pyautogui.write("GATO_OMNI_AUDITED", interval=0.1)
        pyautogui.press('enter')
        
        print("\n--- RESUMEN FINAL ---")
        if os.path.exists(auditor.patterns_file):
            with open(auditor.patterns_file, 'r') as f:
                logs = json.load(f)
                print(f"Total de fallos auditados: {len(logs)}")
        
        await asyncio.sleep(5)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_mission())
