import requests
import pyautogui
import time
from PIL import ImageGrab
import io
import base64

def get_god_vision():
    url = "http://127.0.0.1:8000/analyze"
    
    # 1. Tomar captura instantanea
    screenshot = ImageGrab.grab()
    img_byte_arr = io.BytesIO()
    screenshot.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    # 2. Enviar al servidor
    files = {'file': ('screen.png', img_byte_arr, 'image/png')}
    
    start_time = time.time()
    try:
        response = requests.post(url, files=files)
        data = response.json()
        end_time = time.time()
        
        print(f"--- VISIÓN RELÁMPAGO COMPLETADA ({end_time - start_time:.2f}s) ---")
        print(f"Objetos detectados: {data['objects_count']}")
        
        # Guardar feedback visual si es necesario
        with open("vision_feedback.png", "wb") as f:
            f.write(base64.b64decode(data['image_b64']))
            
        return data['elements']
    except Exception as e:
        print(f"El servidor de vision no responde: {e}")
        return None

if __name__ == "__main__":
    elements = get_god_vision()
    if elements:
        print("Top 5 elementos detectados:")
        for e in elements[:5]:
            print(f"- {e['type']}: {e['content']}")
