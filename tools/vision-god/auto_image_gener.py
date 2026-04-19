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

def click_element(label_id, coordinates):
    # El ID en coordinates suele ser un string como "0", "1", etc.
    if str(label_id) in coordinates:
        # Las coordenadas de OmniParser suelen ser [cx, cy, w, h] o [xmin, ymin, xmax, ymax]
        # Aqui asumimos que son coordenadas de centro [x, y] segun el BoxAnnotator
        coord = coordinates[str(label_id)]
        print(f"Haciendo clic en el ID {label_id} en posicion {coord}")
        pyautogui.moveTo(coord[0], coord[1], duration=0.5)
        pyautogui.click()
        return True
    return False

# 1. PASO 1: Localizar Pestaña "image gener"
print("Escaneando pantalla para localizar la pestaña...")
data = get_vision_data()
if not data: sys.exit(1)

target_id = -1
for i, el in enumerate(data['elements']):
    text = el['content'].lower()
    if "image" in text or "gener" in text:
        print(f"Pestaña detectada! ID: {i} -> {el['content']}")
        target_id = i
        break

if target_id != -1:
    click_element(target_id, data['coordinates'])
    time.sleep(2) # Esperar a que cambie la pestaña
else:
    print("No encontre la pestaña 'image gener'. Intentare un clic en la zona superior.")
    pyautogui.click(600, 20) # Clic ciego en zona de pestañas
    time.sleep(2)

# 2. PASO 2: Buscar Prompt y Generar
print("Escaneando nueva interfaz para hallar el Prompt...")
data = get_vision_data()
if not data: sys.exit(1)

# Buscamos el boton de Generate primero para tener referencia
gen_id = -1
prompt_id = -1

for i, el in enumerate(data['elements']):
    if not el.get('content'): continue
    text = el['content'].lower()
    if "generate" in text:
        gen_id = i
    if "prompt" in text and el['type'] == 'text':
        prompt_id = i

if prompt_id != -1:
    click_element(prompt_id, data['coordinates'])
    # Moverse un poco hacia abajo del texto "Prompt" para caer en la celda
    pyautogui.moveRel(0, 50)
    pyautogui.click()
else:
    # Si no lo encuentra, suele ser la primera caja grande en Stable Diffusion
    pyautogui.click(400, 300) 

pyautogui.write("masterpiece, best quality, 1girl, solo, looking at viewer, cinematic lighting, ultra detailed skin, beautiful eyes, white background", interval=0.01)
time.sleep(1)

if gen_id != -1:
    click_element(gen_id, data['coordinates'])
else:
    print("No veo el boton Generate, pulsando F5 o Enter...")
    pyautogui.press('enter')

print("--- OPERACION FINALIZADA ---")
