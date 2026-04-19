import json
import base64
import time
import urllib.request
import urllib.error

url = "http://127.0.0.1:7861/sdapi/v1/txt2img"

prompt = "Extreme macro closeup portrait of a beautiful young woman, ultra-tight crop. Extraordinarily fine even skin micro-texture, raw unretouched natural skin, visible pores and fine peach-fuzz hairs, subtle natural body-temperature warmth sheen catching light, faint natural skin creases, intricate eye details with sharp catchlights. Soft even flat diffused studio lighting, flat light with no harsh shadows, minimal shadow gradient. Clean stark bright white background. Hasselblad macro 8K, shallow depth of field, photorealistic, raw editorial beauty photography style."
negative_prompt = "airbrushed, smooth skin, plastic skin, CGI, painted, illustration, dramatic shadows, dark background, wet skin, heavy sweat droplets, 3D render, retouching, low resolution, soft focus."

payload = {
    "prompt": prompt,
    "negative_prompt": negative_prompt,
    "steps": 28,
    "cfg_scale": 7,
    "sampler_name": "Euler",
    "scheduler": "Karras",
    "width": 1024,
    "height": 1024,
    "override_settings": {
        "sd_model_checkpoint": "Illustrious-XL-v2.0"
    }
}

headers = {"Content-Type": "application/json"}

# Wait for API to be ready
print("Waiting for Forge API to be ready on port 7861...")
for _ in range(60):
    try:
        req = urllib.request.Request("http://127.0.0.1:7861/sdapi/v1/memory", method="GET")
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print("API is ready! Sending generation request...")
                break
    except Exception:
        pass
    time.sleep(2)
else:
    print("API did not start in time.")
    exit(1)

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(url, data=data, headers=headers, method="POST")

try:
    with urllib.request.urlopen(req, timeout=300) as response:
        r = json.loads(response.read().decode('utf-8'))
        image_b64 = r['images'][0]
        
        with open("output_illustrious.png", "wb") as f:
            f.write(base64.b64decode(image_b64))
        print("Image successfully generated and saved to output_illustrious.png")
except urllib.error.URLError as e:
    print(f"Failed to connect: {e}")
except Exception as e:
    print(f"Error during generation: {e}")
