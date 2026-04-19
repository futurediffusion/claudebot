import os
import torch
from PIL import Image, ImageGrab
import sys
import base64

# Añadir el path de OmniParser para importar sus módulos
sys.path.append(os.getcwd())

from util.utils import check_ocr_box, get_yolo_model, get_som_labeled_img

# Configuración de rutas
device = 'cuda' if torch.cuda.is_available() else 'cpu'
weights_path = 'weights'

print(f"--- CAPTURANDO REALIDAD (OmniParser V2.0 Windows) en {device} ---")

try:
    # 1. Cargar el detector de iconos (YOLOv8)
    print("Cargando detector de iconos...")
    yolo_model = get_yolo_model(model_path=os.path.join(weights_path, 'icon_detect', 'model.pt'))
    
    # 2. Tomar pantallazo real de Windows
    print("Tomando captura de pantalla...")
    screenshot = ImageGrab.grab()
    image_path = 'current_desktop.png'
    screenshot.save(image_path)
    print(f"Pantallazo guardado en {image_path} ({screenshot.size[0]}x{screenshot.size[1]})")

    print(f"Analizando entorno Windows...")
    
    # Ejecutar el parsing de la pantalla (OCR)
    (text, boxes), goal_filtering = check_ocr_box(image_path, display_img=False, output_bb_format='xyxy')
    
    if text is None: text = []
    if boxes is None: boxes = []

    # Etiquetar la imagen (Som = Set of Marks)
    # USAMOS CONFIGURACIÓN POR DEFECTO PARA EVITAR ERRORES DE ARGUMENTOS
    dino_labled_img, label_coordinates, parsed_content_list = get_som_labeled_img(
        image_path, 
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

    print("\n--- OBJETOS INTERACTUABLES DETECTADOS ---")
    for i, content in enumerate(parsed_content_list):
        c_type = content.get('type', 'desconocido')
        c_val = content.get('content', 'Icono')
        print(f"[{i}] {c_type}: {c_val}")

    # Guardar el resultado visual
    output_img_path = 'windows_vision_analysis.png'
    with open(output_img_path, 'wb') as f:
        f.write(base64.b64decode(dino_labled_img))
    
    print(f"\n¡ÉXITO! Análisis guardado en {output_img_path}.")

except Exception as e:
    import traceback
    print(f"Error en la visión: {e}")
    traceback.print_exc()
