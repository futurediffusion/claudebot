import json
import os
import sys
from pathlib import Path

# Configuración de rutas
ROOT = Path(__file__).resolve().parent
SELF_MODEL_DIR = ROOT / "self_model"

def get_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return {}

def check_vision_god():
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('127.0.0.1', 8000))
    sock.close()
    return "ACTIVO (Puerto 8000)" if result == 0 else "INACTIVO"

def check_hub_ports():
    import socket
    active = []
    for port in range(3000, 3005):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.1)
            if s.connect_ex(('localhost', port)) == 0:
                active.append(str(port))
    return ", ".join(active) if active else "Ninguno"

def main():
    print("="*60)
    print(" CLAUDE BOT IDENTITY ORACLE - ACTIVANDO PROTOCOLO ")
    print("="*60)

    # 1. IDENTIDAD Y FILOSOFÍA
    print("\n[IDENTIDAD]")
    print(f"Misión: Sistema CLI-first para automatización personal.")
    print(f"Filosofía: Chromatic Systems (Precisión, Intuición Estructurada).")
    
    # 2. CAPACIDADES
    capabilities = get_json(SELF_MODEL_DIR / "capabilities.json")
    
    print("\n[DOMINIOS MAESTROS]")
    domains = capabilities.get("mastered_domains", [])
    for d in domains[:4]:
        name = d.get("domain", "Unknown")
        features = d.get("features", [])
        feat_str = f" ({', '.join(features[:2])})" if features else ""
        print(f" - {name}{feat_str}")

    # 3. DEBILIDADES (Estructura corregida)
    weaknesses = get_json(SELF_MODEL_DIR / "weaknesses.json")
    print("\n[RIESGOS Y DEBILIDADES]")
    models_w = weaknesses.get("models", {})
    for m_name, data in list(models_w.items())[:3]:
        w = data.get("weaknesses", [])
        if w:
            print(f" ! {m_name}: {', '.join(w[:2])}")
    
    agents_w = weaknesses.get("agents", {})
    for a_name, data in list(agents_w.items())[:2]:
        w = data.get("weaknesses", [])
        if w:
            print(f" ! Agent {a_name}: {', '.join(w[:2])}")

    # 4. ESTADO DEL SISTEMA
    print("\n[ESTADO DEL ENTORNO]")
    print(f"Vision-God: {check_vision_god()}")
    print(f"Puertos HUB activos: {check_hub_ports()}")
    print(f"OS: {sys.platform} | GPU: RTX 4060 (8GB)")

    # 5. REGLAS DE ORO
    print("\n[MANDATOS OBLIGATORIOS]")
    print(" 1. KNOWLEDGE_PRESERVATION: Leer y mergear self_model/, NUNCA sobrescribir.")
    print(" 2. KARPATHY_DISCIPLINE: Pensar -> Simplicidad -> Quirúrgico -> Verificar.")
    print(" 3. CLI-FIRST: El ratón/visión son fallbacks de ÚLTIMA instancia.")

    # 6. ATAJOS PERSONAL HUB
    print("\n[ATAJOS PERSONAL HUB]")
    print(" - 'abre hub de gastos' -> Ejecuta personal_HUB/run_expense_tracker.bat")
    print(" - 'abre journey'       -> Ejecuta personal_HUB/run_journey.bat")

    print("\n" + "="*60)
    print(" CLAUDE BOT ESTÁ LISTO. PROCEDE CON PRECISIÓN. ")
    print("="*60)

if __name__ == "__main__":
    main()
