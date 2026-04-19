import pyautogui
import time

# Coordenadas aproximadas para una de las primeras imagenes de gato (Icono [45])
# En una pantalla 1920x1080 con Google Imagenes, esto suele estar en el tercio superior izquierdo.
# Basandonos en el analisis visual de OmniParser:
x, y = 400, 450 

print(f"Haciendo clic derecho en el gato en ({x}, {y})...")
pyautogui.moveTo(x, y, duration=0.5)
pyautogui.rightClick()

# Esperar a que aparezca el menu contextual
time.sleep(1.5)

# En Edge, la tecla 'v' suele ser el acceso directo para 'Guardar imagen como...'
# Vamos a intentar usarla directamente para mayor velocidad, 
# pero si fallara, tendriamos que buscar el texto con vision.
print("Enviando comando de guardado...")
pyautogui.press('v')

# Esperar a que se abra la ventana de guardado de Windows
time.sleep(2)

# Escribir el nombre del archivo
pyautogui.write("gato_capturado_por_dios", interval=0.1)
pyautogui.press('enter')

print("¡Mision cumplida! El gato deberia estar guardandose.")
