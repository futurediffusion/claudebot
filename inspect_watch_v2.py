import asyncio
import sys
from bleak import BleakClient

# MAC de tu reloj
ADDRESS = "04:DA:28:A1:9F:17"

async def main():
    print(f"Intentando conectar a {ADDRESS}...")
    
    try:
        async with BleakClient(ADDRESS, timeout=20.0) as client:
            if not client.is_connected:
                print("Error: No se pudo conectar.")
                return
                
            print(f"¡Conectado! Nombre: {client.address}")
            print("\nLISTADO DE SERVICIOS Y CARACTERÍSTICAS:\n")
            
            for service in client.services:
                print(f"SERVICIOS: {service.uuid} ({service.description})")
                for char in service.characteristics:
                    props = ", ".join(char.properties)
                    print(f"  └─ CARACT: {char.uuid} | Props: [{props}]")
                    
                    # Intentar leer el valor si es posible
                    if "read" in char.properties:
                        try:
                            value = await client.read_gatt_char(char.uuid)
                            print(f"     Val: {value.hex()}")
                        except Exception:
                            print(f"     Val: <No se pudo leer>")
                print("-" * 50)
                
    except Exception as e:
        print(f"Error crítico: {e}")

if __name__ == "__main__":
    # Forzar salida UTF-8 para consola Windows
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        
    asyncio.run(main())
