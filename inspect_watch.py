"""
Xiaomi Watch Service Inspector
Conecta al reloj y lista TODOS los servicios y caracteristicas con sus propiedades.
"""
import asyncio
import sys
from bleak import BleakScanner, BleakClient


PROPERTIES = {
    0x01: "Read",
    0x02: "Write",
    0x04: "Write Without Response",
    0x08: "Notify",
    0x10: "Indicate",
    0x20: "Authenticated Signed Writes",
    0x40: "Extended Properties",
}

TARGET_MAC = "04:DA:28:A1:9F:17"


def parse_properties(props: int) -> list[str]:
    result = []
    for flag, name in PROPERTIES.items():
        if props & flag:
            result.append(name)
    return result if result else ["None"]


def safe_str(val: str) -> str:
    if not val:
        return "N/A"
    try:
        return val.encode('utf-8', errors='replace').decode('utf-8')
    except:
        return "N/A"


async def find_device(timeout: float = 10.0) -> str | None:
    target_clean = TARGET_MAC.replace("-", "").replace(":", "").upper()
    print(f"Buscando {TARGET_MAC}...")
    
    for attempt in range(5):
        devices = await BleakScanner.discover(timeout=timeout, return_adv=True)
        
        for addr, (dev, adv) in devices.items():
            addr_clean = addr.replace("-", "").replace(":", "").upper()
            if addr_clean == target_clean:
                rssi = adv.rssi
                name = dev.name or "Desconocido"
                print(f"  >> Encontrado: {name} ({rssi} dBm)")
                return addr
        
        if attempt < 4:
            await asyncio.sleep(2)
    
    return None


async def inspect_services(address: str):
    print(f"\nConectando a {address}...")
    
    try:
        async with BleakClient(address, timeout=20.0) as client:
            print(f" >> Conectado!\n")
            print(f"=" * 70)
            print(f"DISPOSITIVO: {client.name or 'Desconocido'}")
            print(f"MAC: {address}")
            print(f"=" * 70)
            
            services = client.services
            print(f"\nServicios encontrados: {len(services.services)}\n")
            
            for handle, service in services.services.items():
                print(f"\n{'─' * 70}")
                print(f"SERVICE UUID: {service.uuid}")
                print(f"Descripcion: {safe_str(service.description)}")
                print(f"Handle: {handle}")
                print(f"\nCaracteristicas:")
                
                for char in service.characteristics:
                    props = parse_properties(char.properties)
                    props_str = ", ".join(props)
                    
                    print(f"  |")
                    print(f"  |-- {char.uuid}")
                    print(f"  |   Desc: {safe_str(char.description)}")
                    print(f"  |   Props: [{props_str}]")
                    print(f"  |   Handle: {char.handle}")
                    
                    if char.descriptors:
                        print(f"  |   Descriptors:")
                        for desc in char.descriptors:
                            print(f"  |   | {desc.uuid} - {safe_str(desc.description)}")
                    
                    try:
                        if 0x01 & char.properties:
                            value = await client.read_gatt_char(char.uuid)
                            hex_val = bytes(value).hex()
                            if len(hex_val) < 100:
                                try:
                                    utf_val = value.decode('utf-8')
                                except:
                                    utf_val = "<binary>"
                                print(f"  |   Value(hex): {hex_val}")
                                print(f"  |   Value(utf8): {utf_val}")
                            else:
                                print(f"  |   Value(hex): {hex_val[:96]}...")
                    except Exception:
                        pass
                
                print(f"  |")
            
            print(f"\n{'=' * 70}")
            print("Inspeccion completada.")
            
    except Exception as e:
        print(f"Error: {e}")


async def main():
    target_mac = TARGET_MAC.replace("-", ":")
    
    print(f"Buscando {TARGET_MAC}...")
    print("Asegurate de que el reloj este discoverable/cerca\n")
    
    addr = await find_device(timeout=10.0)
    
    if not addr:
        print("\n[!] No se encontro el reloj.")
        print("El reloj debe estar discoverable (no asociado al telefono)")
        print("Intenta: mostrar reloj cerca del PC")
        sys.exit(1)
    
    await inspect_services(addr)


if __name__ == "__main__":
    asyncio.run(main())