import os
import torch
from PIL import Image
import sys
import base64
import io
from fastapi import FastAPI, UploadFile, File
import uvicorn
from typing import List

# Añadir el path de OmniParser relativo a esta carpeta
current_dir = os.path.dirname(os.path.abspath(__file__))
omniparser_path = os.path.join(current_dir, 'OmniParser')
sys.path.append(omniparser_path)

from OmniParser.util.utils import check_ocr_box, get_yolo_model, get_som_labeled_img

app = FastAPI(title="Vision God Core Server")

# Global variables for models
yolo_model = None
device = 'cuda' if torch.cuda.is_available() else 'cpu'
weights_path = os.path.join(omniparser_path, 'weights')

@app.on_event("startup")
async def load_models():
    global yolo_model
    print(f"--- INICIALIZANDO SERVIDOR DE VISIÓN (OmniParser V2.0) en {device} ---")
    print(f"Buscando pesos en: {weights_path}")
    yolo_model = get_yolo_model(model_path=os.path.join(weights_path, 'icon_detect', 'model.pt'))
    print("¡Sistemas Visuales CALIENTES y Listos!")

@app.post("/analyze")
async def analyze_screen(file: UploadFile = File(...)):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    temp_path = os.path.join(current_dir, "temp_server_image.png")
    image.save(temp_path)

    (text, boxes), _ = check_ocr_box(temp_path, display_img=False, output_bb_format='xyxy')
    
    if text is None: text = []
    if boxes is None: boxes = []

    dino_labled_img, label_coordinates, parsed_content_list = get_som_labeled_img(
        temp_path, 
        yolo_model, 
        BOX_TRESHOLD=0.05, 
        output_coord_in_ratio=False, 
        ocr_bbox=boxes, 
        caption_model_processor=None, 
        ocr_text=text,
        use_local_semantics=False, 
        iou_threshold=0.1,
        imgsz=640
    )

    serializable_coords = {}
    for k, v in label_coordinates.items():
        if hasattr(v, 'tolist'):
            coords = v.tolist()
        else:
            coords = list(v)
        serializable_coords[k] = [float(x) for x in coords]

    return {
        "status": "success",
        "objects_count": len(parsed_content_list),
        "elements": parsed_content_list,
        "coordinates": serializable_coords, 
        "image_b64": dino_labled_img
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
