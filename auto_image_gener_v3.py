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

def click_center(label_id, data):
    coords = data['coordinates']
    if str(label_id) in coords:
        box = coords[str(label_id)]
        cx = box[0] + (box[2] / 2)
        cy = box[1] + (box[3] / 2)
        print(f"Haciendo clic en el AREA DE TEXTO real (ID {label_id}) en ({cx}, {cy})")
        pyautogui.moveTo(cx, cy, duration=0.5)
        pyautogui.click()
        return True
    return False

# 1. PASO 1: Pestaña (Si ya estamos ahi, el servidor lo detectara rapido)
print("Verificando interfaz...")
data = get_vision_data()
if not data: sys.exit(1)

# 2. PASO 2: Buscar "describe" (el input real)
input_id = -1
for i, el in enumerate(data['elements']):
    if not el.get('content'): continue
    text = el['content'].lower()
    if "describe" in text or "images" in text:
        input_id = i
        break

if input_id != -1:
    click_center(input_id, data)
    time.sleep(0.5)
    # Limpiar y asegurar foco
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('backspace')
    time.sleep(0.2)
else:
    print("No halle 'describe', intentando clic por posicion relativa al toggle...")
    # Si no lo veo, suelo estar justo debajo del toggle que detecte antes
    pyautogui.click(600, 400) 

print("Inyectando Prompt Maestro...")
pyautogui.write("score_9, masterpiece, 1girl, solo, looking at viewer, detailed eyes, soft lighting, high quality anime style, white background", interval=0.01)
time.sleep(0.5)

# 3. PASO 3: Generar con el atajo Pro
print("Disparando Generacion (Ctrl + Enter)...")
pyautogui.hotkey('ctrl', 'enter')

print("--- MISION CUMPLIDA: IMAGEN EN PROCESO ---")
