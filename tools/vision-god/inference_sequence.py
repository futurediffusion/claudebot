import json
import base64
import urllib.request

url = "http://127.0.0.1:7860/sdapi/v1/txt2img"

def generate(prompt, neg, filename):
    payload = {
        "prompt": prompt,
        "negative_prompt": neg,
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
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=600) as response:
        r = json.loads(response.read().decode('utf-8'))
        with open(filename, "wb") as f:
            f.write(base64.b64decode(r['images'][0]))
    print(f"Generated: {filename}")

# PROMPT 1: ANIME PURO
p1 = "score_9, score_8_up, score_7_up, masterpiece, best quality, 1girl, solo, looking at viewer, anime style, flat color, cel shading, vibrant colors, clean lineart, simple white background, highres, absurdres."
n1 = "photorealistic, 3d, realistic, realism, textured skin, score_6, score_5, score_4, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry."

print("Starting Inference 1: Anime Style...")
generate(p1, n1, "output_anime_pure.png")
