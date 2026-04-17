import pyautogui
import time
import subprocess

# 1. Abrir Notepad de forma limpia
subprocess.Popen('notepad.exe')
time.sleep(2)  # Esperar a que abra

# 2. Escribir el mensaje
pyautogui.write('HOLA. SOY EL GEMINI QUE TE ESTA HABLANDO.\n', interval=0.05)
pyautogui.write('NO NECESITO OTRAS APIS. YO TENGO EL CONTROL.\n', interval=0.05)
pyautogui.write('ESTO ES AUTOMATIZACION NATIVA.\n', interval=0.05)

print("Tarea completada con éxito.")
