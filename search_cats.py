import pyautogui
import time

# 1. Asegurar que estamos en el campo de busqueda (ya detectado por vision)
pyautogui.write("edge", interval=0.1)
time.sleep(1)
pyautogui.press("enter")
print("Microsoft Edge abierto mediante busqueda.")

# 2. Esperar a que el navegador cargue la pagina de inicio
time.sleep(4)

# 3. Ir a buscar gatos (suponiendo que el foco cae en la barra de direcciones o buscador)
# Usaremos un atajo universal (Ctrl+L) para ir a la barra de direcciones
pyautogui.hotkey('ctrl', 'l')
time.sleep(0.5)
pyautogui.write("https://www.google.com/search?q=gatos&tbm=isch", interval=0.05)
pyautogui.press("enter")
print("Navegando a busqueda de imagenes de gatos...")
