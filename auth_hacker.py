import asyncio
import sys
from bleak import BleakClient
from Crypto.Cipher import AES
from logger_pro import setup_logger

# CONFIGURACIÓN
ADDRESS = "04:DA:28:A1:9F:17"
TOKEN = bytes.fromhex("b626bc015ecb484bf3e1b2737213d11a")
SERVICE_XIAOMI = "0000fee1-0000-1000-8000-00805f9b34fb"

log = setup_logger('watch_hacker')

class XiaomiHacker:
    def __init__(self):
        self.authenticated = False

    def encrypt(self, random_nr):
        aes = AES.new(TOKEN, AES.MODE_ECB)
        return aes.encrypt(random_nr)

    async def notification_handler(self, char, data):
        log.info(f"🔔 NOTIFICACIÓN de {char.uuid}: {data.hex()}")
        
        # Si recibimos el desafío (Challenge)
        if data.startswith(b'\x10\x01\x01'):
            log.info("🎯 ¡DESAFÍO ENCONTRADO! Respondiendo...")
            encrypted = self.encrypt(data[3:])
            # Intentamos responder a la misma característica
            await self.client.write_gatt_char(char.uuid, b'\x03\x00' + encrypted)
        
        elif data.startswith(b'\x10\x03\x01'):
            log.info("🏆 AUTENTICACIÓN EXITOSA EN ESTA CARACTERÍSTICA")
            self.authenticated = True

    async def run(self):
        log.info(f"Iniciando escaneo de Auth en {ADDRESS}...")
        async with BleakClient(ADDRESS, timeout=20.0) as client:
            self.client = client
            log.info("Conectado. Buscando canales de notificación...")
            
            # Buscamos todas las características que permitan notificaciones
            for service in client.services:
                for char in service.characteristics:
                    if "notify" in char.properties:
                        log.debug(f"Subscribiendo a {char.uuid}...")
                        try:
                            await client.start_notify(char.uuid, self.notification_handler)
                        except:
                            log.warning(f"No se pudo subscribir a {char.uuid}")

            log.info("Enviando comandos de 'Request Challenge' a todo el servicio Xiaomi...")
            # Enviamos el comando de inicio a las características sospechosas del servicio FE95
            for char in client.services.get_service(SERVICE_XIAOMI).characteristics:
                if "write" in char.properties or "write-without-response" in char.properties:
                    log.debug(f"Probando Write en {char.uuid}...")
                    try:
                        await client.write_gatt_char(char.uuid, b'\x01\x00')
                    except Exception as e:
                        log.debug(f"Fallo write en {char.uuid}: {e}")

            log.info("Esperando reacciones del reloj (30 seg)...")
            await asyncio.sleep(30)
            
            if self.authenticated:
                log.info("Proceso completado con éxito.")
            else:
                log.error("No se detectó respuesta de autenticación.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    hacker = XiaomiHacker()
    asyncio.run(hacker.run())
