from orchestrator.core.world_model import WorldModelEngine
import json

def test_world_awareness():
    # 1. Inicializar el motor del mundo
    print("🌍 Inicializando WorldModelEngine...")
    world = WorldModelEngine(agent_name="gemini_situational")
    
    # 2. Observar el escritorio real (vía PowerShell)
    print("👀 Observando tu escritorio en vivo...")
    state = world.observe_desktop()
    
    # 3. Obtener resumen estructurado
    summary = world.get_summary()
    
    print("\n" + "="*40)
    print("📊 REPORTE DE CONSCIENCIA SITUACIONAL")
    print("="*40)
    print(f"🪟 VENTANA ACTIVA: {summary['active_window'].get('title', 'N/A')}")
    print(f"⚙️ PROCESO ACTIVO: {summary['active_window'].get('process_name', 'N/A')}")
    print(f"📱 APPS ABIERTAS: {summary['open_app_count']}")
    
    print("\n📂 ÚLTIMAS APPS DETECTADAS:")
    for app in state['desktop'].get('open_apps', [])[:5]:
        print(f"   - {app['process_name']} ({app['title']})")
        
    print(f"\n📥 DESCARGAS ACTIVAS: {len(summary['downloads_in_progress'])}")
    for dl in summary['downloads_in_progress']:
        print(f"   - {dl['name']} ({dl['size_bytes']} bytes)")

    print("="*40)

if __name__ == "__main__":
    test_world_awareness()
