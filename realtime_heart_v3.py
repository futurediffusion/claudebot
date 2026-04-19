import asyncio
import sys
import logging
from bleak import BleakClient
from Crypto.Cipher import AES
from logger_pro import setup_logger

# CONFIGURACIÓN DISPOSITIVO
DEVICE_ADDRESS = "04:DA:28:A1:9F:17"
TOKEN_HEX = "b626bc015ecb484bf3e1b2737213d11a"

# NUEVOS UUIDS PARA REDMI WATCH 5 (HyperOS/Modern Xiaomi)
AUTH_CHAR_UUID = "0000005e-0000-1000-8000-00805f9b34fb" # Reemplaza al viejo fee1/0009
HR_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
HR_CONTROL_POINT_UUID = "00002a39-0000-1000-8000-00805f9b34fb"

class RedmiWatchRealtime:
    def __init__(self, address, token_hex):
        self.address = address
        self.token = bytes.fromhex(token_hex)
        self.log = setup_logger('watch_realtime')
        self.authenticated = False
        self.client = None

    def encrypt_challenge(self, random_nr):
        """Encriptación AES-128-ECB con el Bindkey."""
        aes = AES.new(self.token, AES.MODE_ECB)
        return aes.encrypt(random_nr)

    async def auth_handler(self, sender, data):
        self.log.debug(f"Xiaomi Auth Data: {data.hex()}")
        
        # Flujo de Auth Xiaomi: 10 01 01 <Random_Number>
        if data.startswith(b'\x10\x01\x01'):
            random_nr = data[3:]
            self.log.info("Desafío recibido. Autenticando...")
            encrypted = self.encrypt_challenge(random_nr)
            # Respuesta: 03 00 <Encrypted_Random_Number>
            await self.client.write_gatt_char(AUTH_CHAR_UUID, b'\x03\x00' + encrypted)
            
        elif data.startswith(b'\x10\x03\x01'):
            self.log.info("--- AUTENTICACIÓN EXITOSA ---")
            self.authenticated = True
        
        elif data.startswith(b'\x10\x01\x04'):
            self.log.error("Fallo de autenticación (Token Inválido)")

    def hr_handler(self, sender, data):
        if len(data) >= 2:
            bpm = data[1]
            self.log.info(f"❤️ LATIDO: {bpm} BPM")

    async def run(self):
        self.log.info(f"Conectando a {self.address}...")
        
        async with BleakClient(self.address, timeout=15.0) as client:
            self.client = client
            self.log.info("Conexión física OK. Iniciando Handshake...")
            
            # 1. Escuchar Auth
            await client.start_notify(AUTH_CHAR_UUID, self.auth_handler)
            
            # 2. Pedir Desafío
            await client.write_gatt_char(AUTH_CHAR_UUID, b'\x01\x00')
            
            # Esperar Auth
            for _ in range(10):
                if self.authenticated: break
                await asyncio.sleep(1)
            
            if not self.authenticated:
                self.log.error("No se pudo completar la autenticación Xiaomi.")
                return

            # 3. Activar Sensor HR (Forzado)
            try:
                await client.write_gatt_char(HR_CONTROL_POINT_UUID, b'\x15\x01\x01')
                self.log.info("Sensor de pulsaciones despertado.")
            except Exception as e:
                self.log.debug(f"Control Point Error (ignorando): {e}")

            # 4. Suscribirse
            await client.start_notify(HR_MEASUREMENT_UUID, self.hr_handler)
            self.log.info("!!! SISTEMA EN VIVO: ESCUCHANDO CORAZÓN !!!")
            
            while True:
                await asyncio.sleep(1)

if __name__ == "__main__":
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    monitor = RedmiWatchRealtime(DEVICE_ADDRESS, TOKEN_HEX)
    try:
        asyncio.run(monitor.run())
    except KeyboardInterrupt:
        print("\nSincronización detenida.")
    except Exception as e:
        print(f"Error: {e}")
