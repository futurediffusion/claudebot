import asyncio
import logging
import sys
from bleak import BleakClient, BleakScanner
from Crypto.Cipher import AES
from logger_pro import setup_logger

# CONFIGURACIÓN TÉCNICA
DEVICE_ADDRESS = "04:DA:28:A1:9F:17"
TOKEN_HEX = "b626bc015ecb484bf3e1b2737213d11a"

# UUIDS PROTOCOLO XIAOMI/REDMI
AUTH_SERVICE_UUID = "0000fee1-0000-1000-8000-00805f9b34fb"
AUTH_CHARACTERISTIC_UUID = "00000009-0000-3512-2118-0009af100700"

# UUIDS ESTÁNDAR HEART RATE
HR_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
HR_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
HR_CONTROL_POINT_UUID = "00002a39-0000-1000-8000-00805f9b34fb"

class ClaudebotWatchHeart:
    def __init__(self, address, token_hex):
        self.address = address
        self.token = bytes.fromhex(token_hex)
        self.log = setup_logger('watch_heart')
        self.authenticated = False
        self.client = None

    def encrypt_challenge(self, random_nr):
        """Encripta el desafío de Xiaomi usando AES-128-ECB."""
        aes = AES.new(self.token, AES.MODE_ECB)
        return aes.encrypt(random_nr)

    async def auth_handler(self, sender, data):
        """Manejador del handshake de autenticación."""
        self.log.debug(f"Auth Response: {data.hex()}")
        
        # Paso 1: Recibimos el número aleatorio (Challenge)
        if data.startswith(b'\x10\x01\x01'):
            random_nr = data[3:]
            self.log.info("Desafío recibido. Encriptando...")
            encrypted = self.encrypt_challenge(random_nr)
            # Paso 2: Enviamos la respuesta encriptada
            await self.client.write_gatt_char(AUTH_CHARACTERISTIC_UUID, b'\x03\x00' + encrypted)
            
        # Paso 3: Confirmación de éxito
        elif data.startswith(b'\x10\x03\x01'):
            self.log.info("Autenticación Xiaomi EXITOSA")
            self.authenticated = True
        
        elif data.startswith(b'\x10\x01\x04'):
            self.log.error("Fallo de autenticación: Token incorrecto o dispositivo bloqueado")

    def hr_handler(self, sender, data):
        """Manejador de datos de pulsaciones."""
        if len(data) >= 2:
            bpm = data[1]
            self.log.info(f"CORAZÓN: {bpm} BPM")

    async def run(self):
        self.log.info(f"Conectando a Redmi Watch 5 ({self.address})...")
        
        async with BleakClient(self.address) as client:
            self.client = client
            if not client.is_connected:
                self.log.error("No se pudo conectar al reloj")
                return

            self.log.info("Conectado. Iniciando protocolo de seguridad...")
            
            # 1. Suscribirse a notificaciones de Auth
            await client.start_notify(AUTH_CHARACTERISTIC_UUID, self.auth_handler)
            
            # 2. Solicitar número aleatorio (Request Challenge)
            await client.write_gatt_char(AUTH_CHARACTERISTIC_UUID, b'\x01\x00')
            
            # 3. Esperar a que la autenticación termine
            timeout = 10
            while not self.authenticated and timeout > 0:
                await asyncio.sleep(1)
                timeout -= 1
            
            if not self.authenticated:
                self.log.error("Timeout de autenticación")
                return

            # 4. Forzar encendido del sensor si es necesario
            try:
                await client.write_gatt_char(HR_CONTROL_POINT_UUID, b'\x15\x01\x01')
                self.log.info("Sensor de pulsaciones activado")
            except:
                self.log.debug("Control Point no disponible, ignorando...")

            # 5. Suscribirse a las pulsaciones
            await client.start_notify(HR_MEASUREMENT_UUID, self.hr_handler)
            self.log.info("ESCUCHANDO PULSACIONES EN TIEMPO REAL...")
            
            while True:
                await asyncio.sleep(1)

if __name__ == "__main__":
    # Fix para error de encoding en consola Windows
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')

    monitor = ClaudebotWatchHeart(DEVICE_ADDRESS, TOKEN_HEX)
    try:
        asyncio.run(monitor.run())
    except KeyboardInterrupt:
        print("\nDetenido por el usuario.")
    except Exception as e:
        print(f"\nError crítico: {e}")
