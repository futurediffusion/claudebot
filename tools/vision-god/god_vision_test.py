
import cv2
from ultralytics import YOLO
import torch

# 1. Cargar modelo YOLOv11n (el más rápido y moderno)
# Se descargará automáticamente en el primer uso
try:
    print("Cargando modelo YOLOv11...")
    model = YOLO('yolo11n.pt') 

    # 2. Realizar inferencia en la imagen de Willy
    source = 'output_willy_pro.png'
    print(f"Analizando imagen: {source}")
    
    results = model.predict(source, save=True, imgsz=1024, conf=0.25)

    # 3. Procesar resultados
    print("\n--- RESULTADOS DE VISIÓN NIVEL DIOS ---")
    for result in results:
        boxes = result.boxes
        print(f"Objetos detectados: {len(boxes)}")
        for box in boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            name = model.names[cls]
            print(f"- [ {name} ] con {conf*100:.1f}% de confianza")

    print("\nImagen analizada guardada en la carpeta 'runs/detect/predict/'")
    
except Exception as e:
    print(f"Error durante el análisis visual: {e}")
