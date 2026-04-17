from groq import Groq
import os

api_key = os.environ.get("GROQ_API_KEY", "YOUR_KEY_HERE")
client = Groq(api_key=api_key)

try:
    print("Listando modelos disponibles en tu cuenta de Groq...")
    models = client.models.list()
    for model in models.data:
        print(f"- {model.id}")
except Exception as e:
    print(f"Error al listar: {e}")
