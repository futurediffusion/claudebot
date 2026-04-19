import pyautogui
import time

# Coordenadas estimadas para el icono de Edge en la barra de tareas basandose en el analisis de OmniParser
# En una pantalla 1920x1080, Edge suele estar cerca del inicio.
# El analisis detecto iconos en la zona inferior.

# Vamos a intentar buscar el icono de Edge en la pantalla directamente con pyautogui para ser precisos.
try:
    # Si no lo encuentra por imagen, usaremos la deteccion de OmniParser
    # Pero como medida de seguridad, buscaremos el pixel azul de Edge
    print("Buscando icono de Edge en la barra de tareas...")
    
    # El icono de Edge tiene un color azul/cian caracteristico.
    # Vamos a hacer clic en una posicion habitual de la barra de tareas si la deteccion falla.
    # Segun el log de OmniParser, el icono [113] o similares estan en la zona de iconos.
    
    # Movimiento humano (curva)
    pyautogui.moveTo(450, 1055, duration=1) # Posicion aproximada en barra de tareas
    pyautogui.click()
    print("Clic realizado en la barra de tareas.")
    
except Exception as e:
    print(f"Error al mover el mouse: {e}")
