import requests
import pyautogui
import time
from PIL import ImageGrab
import io
import sys

def get_vision_data():
    url = "http://127.0.0.1:8000/analyze"
    screenshot = ImageGrab.grab()
    img_byte_arr = io.BytesIO()
    screenshot.save(img_byte_arr, format='PNG')
    files = {'file': ('screen.png', img_byte_arr.getvalue(), 'image/png')}
    try:
        response = requests.post(url, files=files)
        return response.json()
    except Exception as e:
        print(f"Error conectando al servidor visual: {e}")
        return None

def click_center(label_id, data, offset_y=0):
    coords = data['coordinates']
    if str(label_id) in coords:
        box = coords[str(label_id)]
        cx = box[0] + (box[2] / 2)
        cy = box[1] + (box[3] / 2) + offset_y
        print(f"Haciendo clic en ID {label_id} -> ({cx}, {cy})")
        pyautogui.moveTo(cx, cy, duration=0.3)
        pyautogui.click()
        return True
    return False

# 1. PASO 1: Saltar a la pestaña "Image Gener"
print("Paso 1: Localizando pestaña...")
data = get_vision_data()
if not data: sys.exit(1)

tab_id = -1
for i, el in enumerate(data['elements']):
    if not el.get('content'): continue
    text = el['content'].lower()
    # Buscamos la pestaña en la parte superior (cy < 100)
    box = data['coordinates'][str(i)]
    if ("image" in text or "gener" in text) and box[1] < 150:
        tab_id = i
        break

if tab_id != -1:
    click_center(tab_id, data)
    time.sleep(1.5)
else:
    print("No veo la pestaña arriba, intentando clic por posicion fija de pestaña...")
    pyautogui.click(900, 70)
    time.sleep(1.5)

# 2. PASO 2: Buscar el input "describe your images"
print("Paso 2: Buscando el area de texto...")
# Tomamos una nueva captura de la nueva interfaz
data = get_vision_data()
if not data: sys.exit(1)

input_id = -1
for i, el in enumerate(data['elements']):
    if not el.get('content'): continue
    text = el['content'].lower()
    # Buscamos especificamente el placeholder "describe" 
    # Y que no sea nuestro propio log (ignoramos zona del CLI)
    box = data['coordinates'][str(i)]
    if ("describe" in text or "images" in text) and box[1] > 150:
        input_id = i
        break

if input_id != -1:
    # Hacemos clic un poco mas arriba del texto si es un placeholder inferior
    click_center(input_id, data)
    time.sleep(0.5)
    # Limpiar y escribir
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('backspace')
    time.sleep(0.2)
    print("Escribiendo prompt...")
    pyautogui.write("score_9, masterpiece, 1girl, solo, looking at viewer, detailed eyes, soft lighting, anime style, white background", interval=0.01)
    time.sleep(0.5)
    print("Disparando con Ctrl+Enter...")
    pyautogui.hotkey('ctrl', 'enter')
else:
    print("No halle el input. Intentando clic de emergencia en el centro de la pantalla...")
    pyautogui.click(960, 540)
    pyautogui.hotkey('ctrl', 'enter')

print("--- MISION FINALIZADA ---")
