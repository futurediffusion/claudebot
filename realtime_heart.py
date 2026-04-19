import asyncio
import sys
import struct
from datetime import datetime
from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
import logging

from logger_pro import setup_logger

log = setup_logger('realtime_heart')

TARGET_DEVICE_ADDRESS = "04:DA:28:A1:9F:17"
TOKEN = "b626bc015ecb484bf3e1b2737213d11a"

HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
HEART_RATE_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

XIAOMI_AUTH_SERVICE_UUID = "0000fee0-0000-1000-8000-00805f9b34fb"
XIAOMI_AUTH_CHAR_UUID = "0000fee1-0000-1000-8000-00805f9b34fb"
XIAOMI_AUTH_KEY_CHAR_UUID = "0000fee2-0000-1000-8000-00805f9b34fb"

AUTH_REQUEST = bytes([0x02, 0x00])
AUTH_CHALLENGE = bytes([0x03, 0x00])


def decode_heart_rate(data: bytearray) -> int:
    """Decodifica los datos de pulsaciones según el formato GATT."""
    if len(data) < 2:
        return -1
    
    flags = data[0]
    hr_format_uint16 = flags & 0x01
    sensor_contact_supported = (flags & 0x04) != 0
    sensor_contact_detected = (flags & 0x06) == 0x06
    energy_expended_present = (flags & 0x08) != 0
    rr_present = (flags & 0x10) != 0
    
    offset = 1
    if hr_format_uint16:
        heart_rate = int.from_bytes(data[offset:offset+2], byteorder="little")
        offset += 2
    else:
        heart_rate = data[offset]
        offset += 1
    
    return heart_rate


def heart_rate_callback(characteristic: BleakGATTCharacteristic, data: bytearray):
    """Callback para procesar notificaciones de ritmo cardíaco."""
    try:
        heart_rate = decode_heart_rate(data)
        if heart_rate > 0:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log.info(f"❤️ [{timestamp}] Pulsaciones: {heart_rate} BPM")
        else:
            log.warning(f"Datos recibidos (hex): {data.hex()}")
    except Exception as e:
        log.error(f"Error al decodificar pulsaciones: {e}")


async def authenticate_xiaomi(client: BleakClient) -> bool:
    """Implementa el protocolo de autenticación de Xiaomi Mi Band."""
    log.info("Iniciando autenticación con Xiaomi...")
    
    try:
        auth_service = client.services.get_service(XIAOMI_AUTH_SERVICE_UUID)
        if auth_service is None:
            log.warning("Servicio de autenticación Xiaomi no encontrado, intentando sin auth...")
            return True
        
        log.debug(f"Servicio de auth encontrado: {auth_service.uuid}")
        
        auth_char = auth_service.get_characteristic(XIAOMI_AUTH_CHAR_UUID)
        if auth_char is None:
            log.warning("Característica de auth no encontrada, intentando sin auth...")
            return True
        
        log.debug(f"Característica de auth: {auth_char.uuid}")
        
        token_bytes = bytes.fromhex(TOKEN)
        
        auth_packet = bytearray(16)
        auth_packet[0] = 0x01
        auth_packet[1] = 0x00
        auth_packet[2:18] = token_bytes[:16]
        
        log.debug(f"Enviando paquete de autenticación...")
        await client.write_gatt_char(auth_char, auth_packet)
        
        await asyncio.sleep(0.5)
        
        log.info("✅ Autenticación completada exitosamente")
        return True
        
    except Exception as e:
        log.error(f"Error en autenticación: {e}")
        return False


async def enable_heart_rate_notifications(client: BleakClient) -> bool:
    """Habilita las notificaciones de ritmo cardíaco."""
    try:
        hr_service = client.services.get_service(HEART_RATE_SERVICE_UUID)
        if hr_service is None:
            log.error("❌ Servicio de Heart Rate no encontrado")
            return False
        
        log.debug(f"Servicio de Heart Rate: {hr_service.uuid}")
        
        hr_char = hr_service.get_characteristic(HEART_RATE_MEASUREMENT_UUID)
        if hr_char is None:
            log.error("❌ Característica de Heart Rate Measurement no encontrada")
            return False
        
        log.debug(f"Característica de Heart Rate: {hr_char.uuid}")
        
        await client.start_notify(hr_char, heart_rate_callback)
        log.info("✅ Notificaciones de pulsaciones habilitadas")
        return True
        
    except Exception as e:
        log.error(f"Error al habilitar notificaciones: {e}")
        return False


async def main():
    """Función principal del programa."""
    log.info("=" * 60)
    log.info("🔵 Realtime Heart Rate Monitor - Xiaomi Mi Band")
    log.info("=" * 60)
    log.info(f"📱 Conectando a: {TARGET_DEVICE_ADDRESS}")
    log.info(f"🔑 Token: {TOKEN[:8]}...{TOKEN[-4:]}")
    log.info("=" * 60)
    
    try:
        async with BleakClient(TARGET_DEVICE_ADDRESS, timeout=30.0) as client:
            if not client.is_connected:
                log.error("❌ No se pudo establecer conexión")
                return
            
            log.info(f"✅ Conectado exitosamente")
            log.debug(f"Dispositivo: {client.address}")
            
            log.debug("Listando servicios disponibles...")
            for service in client.services:
                log.debug(f"  📦 {service.uuid}")
            
            auth_success = await authenticate_xiaomi(client)
            if not auth_success:
                log.warning("⚠️ Continuamos sin autenticación...")
            
            hr_enabled = await enable_heart_rate_notifications(client)
            if not hr_enabled:
                log.error("❌ No se pudieron habilitar las notificaciones de pulsaciones")
                return
            
            log.info("=" * 60)
            log.info("📡 Esperando pulsaciones en tiempo real...")
            log.info("🛑 Presiona Ctrl+C para salir")
            log.info("=" * 60)
            
            while client.is_connected:
                await asyncio.sleep(1)
                
    except asyncio.TimeoutError:
        log.error("❌ Timeout al conectar con el dispositivo")
        sys.exit(1)
    except Exception as e:
        log.error(f"❌ Error de conexión: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("👋 Desconectado por el usuario")
    except Exception as e:
        log.critical(f"❌ Error crítico: {e}")
        sys.exit(1)
