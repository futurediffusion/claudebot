import cv2
from ultralytics import YOLO
import os

def audit_image(image_path):
    print(f"--- AUDITORÍA ANATÓMICA NIVEL DIOS: {image_path} ---")
    
    models = {
        "Rostro": "models_vision/face_yolov8m.pt",
        "Ojos": "models_vision/Eyes.pt",
        "Manos": "models_vision/hand_yolov8s.pt"
    }
    
    summary = {}

    for label, model_path in models.items():
        if not os.path.exists(model_path):
            print(f"Error: Modelo {model_path} no encontrado.")
            continue
            
        model = YOLO(model_path)
        results = model.predict(image_path, conf=0.4, verbose=False)
        
        count = 0
        for result in results:
            count += len(result.boxes)
            
        summary[label] = count
        print(f"- {label} detectados: {count}")

    # Análisis de integridad
    print("\n--- INFORME DEL DIRECTOR ---")
    status = "✅ CALIDAD APROBADA"
    alerts = []

    if summary.get("Rostro", 0) != 1:
        alerts.append(f"⚠️ ¡OJO! Se detectan {summary.get('Rostro')} rostros (esperado: 1)")
        status = "❌ FALLO ANATÓMICO"
        
    if summary.get("Ojos", 0) < 2:
         alerts.append(f"⚠️ ¡OJO! Solo se detectan {summary.get('Ojos')} ojos. Posible error de composición.")
         status = "❌ FALLO ANATÓMICO"
    elif summary.get("Ojos", 0) > 2:
         alerts.append(f"⚠️ ¡ALERTA! {summary.get('Ojos')} ojos detectados. Mutación de IA.")
         status = "❌ MUTACIÓN DETECTADA"

    if len(alerts) == 0:
        print("Estructura facial estándar detectada. Proporciones correctas.")
    else:
        for alert in alerts:
            print(alert)
            
    print(f"\nESTADO FINAL: {status}")

if __name__ == "__main__":
    audit_image("output_willy_pro.png")
