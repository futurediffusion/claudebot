import asyncio
from bleak import BleakScanner

async def run():
    print("Buscando todos los dispositivos Bluetooth cercanos (10 segundos)...")
    print("Presiona Ctrl+C para detener\n")
    
    # discover() devuelve una lista de objetos BLEDevice que tienen RSSI en metadata
    devices = await BleakScanner.discover(timeout=10.0, return_adv=True)
    
    print(f"Encontrados {len(devices)} dispositivos\n")
    print(f"{'Nombre':<30} {'MAC':<18} {'RSSI':<8}")
    print("-" * 60)
    
    # devices es un dict: {address: (device, advertisement_data)}
    for address, (device, adv_data) in devices.items():
        name = device.name if device.name else "Desconocido"
        rssi = adv_data.rssi
        print(f"{name:<30} {address:<18} {rssi:<8} dBm")

if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nEscaneo detenido por el usuario.")
    except Exception as e:
        print(f"\nError: {e}")
