import os

def setup_canva_premium():
    print("="*50)
    print("   CANVA PREMIUM ACTIVATION FOR CLAUDE SKILLS")
    print("="*50)
    
    client_id = input("Introduce tu Canva Client ID: ")
    client_secret = input("Introduce tu Canva Client Secret: ")
    
    env_content = f"""
# Canva Premium Credentials
CANVA_CLIENT_ID={client_id}
CANVA_CLIENT_SECRET={client_secret}
CANVA_PREMIUM_ACCESS=true
"""
    
    with open(".env", "a") as f:
        f.write(env_content)
    
    print("\n✅ ¡Configuración guardada en .env!")
    print("Ahora el skill 'canva-official' usará tu cuenta Premium para:")
    print("- Acceso a templates y elementos Pro.")
    print("- Uso de tus Brand Kits oficiales.")
    print("- Exportación en alta resolución sin marcas de agua.")

if __name__ == "__main__":
    # Nota: Este script es para que el usuario lo ejecute localmente si desea
    # Por ahora, solo lo dejamos como referencia de cómo integramos la info.
    pass
