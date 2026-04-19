import asyncio
import sys
from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic

HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
HEART_RATE_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
TARGET_DEVICE_ADDRESS = "04:DA:28:A1:9F:17"


def heart_rate_callback(characteristic: BleakGATTCharacteristic, data: bytearray):
    if len(data) >= 2:
        flags = data[0]
        hr_format_uint16 = flags & 0x01
        if hr_format_uint16:
            heart_rate = int.from_bytes(data[1:3], byteorder="little")
        else:
            heart_rate = data[1]
        print(f"❤️ Pulsaciones: {heart_rate} BPM")
    else:
        print(f"Datos recibidos (hex): {data.hex()}")


async def main():
    print(f"Conectando a {TARGET_DEVICE_ADDRESS}...")
    
    try:
        async with BleakClient(TARGET_DEVICE_ADDRESS) as client:
            print(f"Conectado: {client.is_connected}")
            
            services = client.services
            print("Servicios disponibles:")
            for service in services:
                print(f"  - {service.uuid}")
            
            hr_service = services.get_service(HEART_RATE_SERVICE_UUID)
            if hr_service is None:
                print("❌ Servicio de Heart Rate no encontrado")
                return
            
            print(f"✅ Servicio de Heart Rate encontrado: {hr_service.uuid}")
            
            hr_char = hr_service.get_characteristic(HEART_RATE_MEASUREMENT_UUID)
            if hr_char is None:
                print("❌ Característica de Heart Rate Measurement no encontrada")
                return
            
            print(f"✅ Característica encontrada: {hr_char.uuid}")
            print("📡 Esperando notificaciones de pulsaciones... (Ctrl+C para salir)")
            
            await client.start_notify(hr_char, heart_rate_callback)
            
            while client.is_connected:
                await asyncio.sleep(1)
                
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Desconectado")
