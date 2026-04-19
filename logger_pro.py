import logging
import os
from logging.handlers import RotatingFileHandler

# Configuración de colores ANSI
COLORS = {
    'DEBUG': '\033[36m',     # Cyan
    'INFO': '\033[32m',      # Green
    'WARNING': '\033[33m',   # Yellow
    'ERROR': '\033[31m',     # Red
    'CRITICAL': '\033[35m',  # Magenta
    'RESET': '\033[0m',
}

class ColoredConsoleHandler(logging.StreamHandler):
    """Handler personalizado para imprimir logs con colores en la consola."""
    def emit(self, record):
        try:
            level = record.levelname
            color = COLORS.get(level, COLORS['RESET'])
            # Guardamos el nivel original para no afectar otros handlers
            original_level = record.levelname
            record.levelname = f"{color}{level}{COLORS['RESET']}"
            msg = self.format(record)
            self.stream.write(msg + self.terminator)
            self.flush()
            record.levelname = original_level # Restauramos
        except Exception:
            self.handleError(record)

class ModuleFilter(logging.Filter):
    """Filtro para permitir logs solo de módulos específicos o silenciar otros."""
    def __init__(self, allowed_module=None):
        super().__init__()
        self.allowed_module = allowed_module

    def filter(self, record):
        if self.allowed_module is None:
            return True
        return record.name.startswith(self.allowed_module)

def setup_logger(name: str, log_dir: str = 'logs', level=logging.DEBUG) -> logging.Logger:
    """Configura un logger profesional con rotación de archivos y consola a color."""
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Evitar duplicar handlers si el logger ya existe
    if logger.handlers:
        return logger

    formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # Handler de Archivo (Rotativo)
    file_path = os.path.join(log_dir, f"{name}.log")
    file_handler = RotatingFileHandler(file_path, maxBytes=5*1024*1024, backupCount=3)
    file_handler.setFormatter(formatter)
    
    # Handler de Consola (Color)
    console_handler = ColoredConsoleHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

if __name__ == '__main__':
    # Prueba del sistema
    log = setup_logger('claudebot_main')
    log.info("Sistema de logging iniciado correctamente.")
    log.debug("Este es un mensaje de depuración.")
    log.warning("Advertencia: El sistema está en modo test.")
    log.error("Error simulado para verificar el color rojo.")
    log.critical("¡Fallo crítico! (Color Magenta)")
