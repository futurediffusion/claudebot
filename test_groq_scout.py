import base64
import os
import sys
from pathlib import Path

# Añadir el orquestador al path para poder importar los adaptadores
sys.path.append(os.getcwd())
from orchestrator.models.groq_adapter import GroqVisionScoutAdapter

def test_groq_vision():
    # 1. Sacar captura usando el script que ya tenemos
    print("📸 Sacando captura de pantalla...")
    os.system("powershell -ExecutionPolicy Bypass -File capture_pro.ps1")
    
    image_path = "menu_contextual.png" # Usamos el nombre que genera el script
    if not os.path.exists(image_path):
        # Si no existe, probamos con el otro nombre común
        image_path = "screenshot.png"
        
    with open(image_path, "rb") as f:
        img_data = f.read()
        img_b64 = base64.b64encode(img_data).decode('utf-8')

    # 2. Configurar el adaptador de Groq Scout
    print("🦅 Invocando a Groq Vision Scout (Llama 3.2 Vision)...")
    scout = GroqVisionScoutAdapter()
    
    context = {
        "image_base64": img_b64
    }
    
    task = "Analiza esta captura de pantalla de Windows. ¿Qué ventanas ves abiertas? ¿Qué iconos hay en la barra de tareas? Sé muy conciso."
    
    result = scout.generate_response(task, context)
    
    if result["success"]:
        print("\n--- [ RESPUESTA DE GROQ SCOUT ] ---")
        print(result["response"])
        print("----------------------------------")
        print(f"Modelo: {result['model']} | Tokens: {result.get('tokens', 'N/A')}")
    else:
        print(f"❌ Error en Groq: {result['error']}")

if __name__ == "__main__":
    test_groq_vision()
