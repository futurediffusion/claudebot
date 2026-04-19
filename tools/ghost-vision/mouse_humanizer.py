import pyautogui
import random
import time
import numpy as np
from scipy import interpolate

def move_human(x2, y2):
    # Obtener posicion actual
    x1, y1 = pyautogui.position()
    
    # Crear puntos de control para una curva Bezier (2-3 puntos intermedios aleatorios)
    cp = random.randint(2, 4)
    x = np.linspace(x1, x2, num=cp + 2)
    y = np.linspace(y1, y2, num=cp + 2)
    
    # Añadir aleatoriedad a los puntos intermedios para la curva
    for i in range(1, cp + 1):
        x[i] += random.randint(-100, 100)
        y[i] += random.randint(-100, 100)
        
    # Interpolar para suavizar
    t = np.linspace(0, 1, num=max(int(np.linalg.norm([x2-x1, y2-y1])/5), 20))
    tck, u = interpolate.splprep([x, y], s=0)
    out = interpolate.splev(t, tck)
    
    # Mover el mouse por los puntos de la curva con pausas naturales
    for px, py in zip(out[0], out[1]):
        pyautogui.moveTo(px, py)
        if random.random() > 0.95: # Pausa humana aleatoria
            time.sleep(random.uniform(0.01, 0.03))
            
    # Micro-ajuste final
    pyautogui.moveTo(x2, y2, duration=random.uniform(0.1, 0.2))
    time.sleep(random.uniform(0.1, 0.3))

def click_human(x, y, button='left'):
    move_human(x, y)
    # Temblor previo al clic
    pyautogui.moveRel(random.randint(-1, 1), random.randint(-1, 1))
    pyautogui.click(button=button)
    print(f"Clic humano realizado en ({x}, {y})")

if __name__ == "__main__":
    # Test rápido: mover al centro y click
    click_human(960, 540)
