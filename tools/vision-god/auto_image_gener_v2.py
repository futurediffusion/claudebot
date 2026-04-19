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
        # Coordenadas OmniParser V2 en modo xywh (top-left, width, height)
        box = coords[str(label_id)]
        cx = box[0] + (box[2] / 2)
        cy = box[1] + (box[3] / 2)
        print(f"Haciendo clic en el CENTRO del ID {label_id} en ({cx}, {cy})")
        pyautogui.moveTo(cx, cy, duration=0.5)
        pyautogui.click()
        return True
    return False

# 1. PASO 1: Localizar y saltar a la Pestaña
print("Buscando pestaña 'image gener'...")
data = get_vision_data()
if not data: sys.exit(1)

target_id = -1
for i, el in enumerate(data['elements']):
    if not el.get('content'): continue
    text = el['content'].lower()
    if "image" in text or "gener" in text:
        target_id = i
        break

if target_id != -1:
    click_center(target_id, data)
    time.sleep(2)
else:
    print("Pestaña no detectada, pruebo clic en zona superior.")
    pyautogui.click(800, 60)
    time.sleep(2)

# 2. PASO 2: Localizar Prompt, Limpiar e Inyectar
print("Localizando campo de Prompt...")
data = get_vision_data()
if not data: sys.exit(1)

prompt_id = -1
gen_id = -1

for i, el in enumerate(data['elements']):
    if not el.get('content'): continue
    text = el['content'].lower()
    if "generate" in text:
        gen_id = i
    if ("prompt" in text or "positive" in text) and el['type'] == 'text':
        prompt_id = i

if prompt_id != -1:
    # Clic en el prompt
    click_center(prompt_id, data)
    time.sleep(1)
    # Limpiar campo por si acaso
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('backspace')
    time.sleep(0.5)
else:
    print("No halle el texto 'Prompt', clic en zona tipica (400, 300)...")
    pyautogui.click(400, 300)

print("Escribiendo prompt...")
pyautogui.write("score_9, masterpiece, 1girl, solo, looking at viewer, beautiful face, soft skin, white background, cinematic lighting", interval=0.02)
time.sleep(1)

# 3. PASO 3: Generar
if gen_id != -1:
    print("Pulsando GENERATE...")
    click_center(gen_id, data)
else:
    print("Boton no detectado, pulsando ENTER...")
    pyautogui.press('enter')

print("--- MISION COMPLETADA CON ÉXITO ---")
