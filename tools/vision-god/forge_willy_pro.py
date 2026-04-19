import json
import base64
import time
import urllib.request
import urllib.error

url = "http://127.0.0.1:7861/sdapi/v1/txt2img"

# Base de Willy Prompt Master + PONY BASIC Style
# Fusión de calidad de score + realismo fotográfico
prompt = (
    "score_9, score_8_up, score_7_up, masterpiece, best quality, ultra-detailed, realistic skin, "
    "1girl, solo, beautiful face, soft features, long flowing hair, looking at viewer, "
    "detailed skin texture, skin pores, subtle freckles, cinematic lighting, softbox lighting, "
    "shot on Sony A7R IV, 85mm f/1.4, sharp focus, shallow depth of field, creamy bokeh, "
    "clean stark bright white background, minimalist composition."
)

# Negative Prompt de PONY BASIC + REALIL
negative_prompt = (
    "watermark, signature, artist name, twitter username, 3d, score_6, score_5, score_4, "
    "ugly face, mutated hands, low res, blurry face, monochrome, furry, bad eyes, dot eyes, "
    "bad anatomy, deformed, extra fingers, cartoon, anime, low quality, worst quality, "
    "jpeg artifacts, signature, simple background, bad hands, dark background, harsh shadows."
)

payload = {
    "prompt": prompt,
    "negative_prompt": negative_prompt,
    "steps": 28,
    "cfg_scale": 7,
    "sampler_name": "Euler",
    "scheduler": "Karras",
    "width": 768,
    "height": 1080,
    "override_settings": {
        "sd_model_checkpoint": "Illustrious-XL-v2.0"
    }
}

headers = {"Content-Type": "application/json"}

print("Starting Forge API for High Quality Render...")
# No hace falta esperar, ya debería estar listo si lo lanzamos ahora
# Pero el script tiene el check de seguridad

def check_api():
    try:
        req = urllib.request.Request("http://127.0.0.1:7861/sdapi/v1/memory", method="GET")
        with urllib.request.urlopen(req) as response:
            return response.status == 200
    except:
        return False

# Re-lanzar Forge si no está activo
import subprocess
import os

if not check_api():
    print("API not found. Restarting Forge...")
    # Matar procesos colgados
    subprocess.run(["powershell", "Stop-Process -Name python -Force -ErrorAction SilentlyContinue"])
    # Lanzar de nuevo
    cmd = 'cd /d D:\\IA\\FORGE && call environment.bat && cd webui && webui.bat --api --nowebui'
    subprocess.Popen(cmd, shell=True)
    
    # Esperar a que cargue
    for i in range(120):
        if check_api():
            print("API is ready!")
            break
        time.sleep(2)
        if i % 5 == 0: print(f"Loading models... {i*2}s")

# Enviar generación
data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(url, data=data, headers=headers, method="POST")

try:
    print("Generating High Quality Image (768x1080)...")
    with urllib.request.urlopen(req, timeout=600) as response:
        r = json.loads(response.read().decode('utf-8'))
        image_b64 = r['images'][0]
        
        output_path = "output_willy_pro.png"
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(image_b64))
        print(f"Success! Image saved to {output_path}")
except Exception as e:
    print(f"Error: {e}")
