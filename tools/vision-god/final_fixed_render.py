import json
import base64
import urllib.request

url = "http://127.0.0.1:7860/sdapi/v1/txt2img"

# Strings del Estilo IL de Forge
style_il_pos = "masterpiece, best quality, amazing quality, very aesthetic, absurdres, newest, "
style_il_neg = "lowres,worst quality,bad quality,bad anatomy,sketch,jpeg artifacts,signature,watermark,old,oldest,censored,bar_censor,simple background,bad hands,nsfw, "

def generate(prompt, neg, filename):
    print(f"Generating with Euler a + Karras + CFG 4: {filename}...")
    
    # Fusionamos el Estilo IL con el prompt
    full_prompt = style_il_pos + prompt
    full_neg = style_il_neg + neg
    
    payload = {
        "prompt": full_prompt,
        "negative_prompt": full_neg,
        "steps": 28,
        "cfg_scale": 4, # Ajustado a 4 según instrucción
        "sampler_name": "Euler a", # Cambiado a Euler a
        "scheduler": "Karras",
        "width": 768,
        "height": 1080,
        "override_settings": {
            "sd_model_checkpoint": "Illustrious-XL-v2.0"
        }
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=600) as response:
            r = json.loads(response.read().decode('utf-8'))
            with open(filename, "wb") as f:
                f.write(base64.b64decode(r['images'][0]))
        print(f"Success: {filename}")
    except Exception as e:
        print(f"Error in {filename}: {e}")

# PROMPT 1: ANIME PURO (Corregido)
p1 = "score_9, score_8_up, score_7_up, 1girl, solo, looking at viewer, anime style, clean lineart, vibrant colors, white background."
n1 = "realistic, 3d, photorealistic, score_6, score_5, score_4."

# PROMPT 2: SEMI-REALISMO (Corregido)
p2 = "score_9, score_8_up, score_7_up, 1girl, solo, looking at viewer, high-end stylized render, soft subsurface scattering, detailed eyes, white background."
n2 = "lineart, score_6, score_5, score_4."

# Ejecutar secuencia
generate(p1, n1, "output_1_anime_FIXED.png")
generate(p2, n2, "output_2_stylized_FIXED.png")
