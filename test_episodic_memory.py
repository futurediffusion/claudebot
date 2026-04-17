from orchestrator.core.episodic_memory import EpisodicMemoryEngine
from pathlib import Path
import json

def test_memory():
    # 1. Inicializar el motor
    print("🧠 Inicializando EpisodicMemoryEngine...")
    memory = EpisodicMemoryEngine(agent_name="gemini_cli")
    
    # 2. Registrar un episodio ficticio (basado en nuestro éxito real de hoy)
    print("📝 Registrando episodio de 'ChatGPT Stealth Interaction'...")
    episode_info = memory.record_episode(
        task="Hablar con ChatGPT Pro usando Edge en el puerto 9222 en modo sigilo",
        task_type="browser_automation",
        success=True,
        execution_time_ms=45000,
        episode_type="production",
        model_name="gemini-2.0-flash",
        tools_used=["playwright", "edge_cdp"],
        response="Hola de nuevo. Soy Gemini en control TOTAL...",
        metadata={"automation_route": "browser", "stealth": True}
    )
    print(f"✅ Episodio guardado con ID: {episode_info['id']}")

    # 3. Intentar recuperar el recuerdo (Búsqueda por relevancia)
    print("\n🔍 Buscando recuerdos sobre 'automatizar chatgpt'...")
    relevant = memory.find_relevant_episodes(task="Necesito automatizar una charla con chatgpt")
    
    if relevant:
        print(f"🧠 ¡RECUERDO ENCONTRADO! (Puntuación: {relevant[0]['relevance_score']})")
        print(f"   - Tarea recordada: {relevant[0]['task']}")
        print(f"   - Resolución que funcionó: {relevant[0]['resolution']}")
    else:
        print("❌ No encontré recuerdos relevantes.")

if __name__ == "__main__":
    test_memory()
