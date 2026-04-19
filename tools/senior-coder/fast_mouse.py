import pyautogui
import random
import time
import numpy as np
from scipy import interpolate

class FastHumanMouse:
    @staticmethod
    def move(x2, y2, speed_factor=1.0):
        """Mueve el raton de forma humana pero VELOZ"""
        x1, y1 = pyautogui.position()
        distance = np.sqrt((x2-x1)**2 + (y2-y1)**2)
        
        # Si la distancia es muy corta, movimiento directo para evitar errores de spline
        if distance < 30:
            pyautogui.moveTo(x2, y2, duration=random.uniform(0.05, 0.1))
            return

        # Puntos de control (solo 1 o 2 para velocidad)
        cp_count = 1 if distance < 300 else 2
        x = np.linspace(x1, x2, num=cp_count + 2)
        y = np.linspace(y1, y2, num=cp_count + 2)
        
        # Desviacion minima para no ser tortuga
        for i in range(1, cp_count + 1):
            x[i] += random.randint(-20, 20)
            y[i] += random.randint(-20, 20)
            
        # Suavizado rapido (con blindaje matematico)
        try:
            steps = max(int(distance / (15 * speed_factor)), 5)
            t = np.linspace(0, 1, num=steps)
            tck, u = interpolate.splprep([x, y], s=0)
            out = interpolate.splev(t, tck)
            
            # Ejecucion de alta frecuencia
            for px, py in zip(out[0], out[1]):
                pyautogui.moveTo(px, py)
                if random.random() > 0.98:
                    time.sleep(0.001)
        except Exception:
            # Fallback a movimiento directo si la matematica de splines falla
            pyautogui.moveTo(x2, y2, duration=random.uniform(0.1, 0.2))
                
        # Ajuste final instantaneo
        pyautogui.moveTo(x2, y2)

    @staticmethod
    def click(x, y, button='left', double=False):
        FastHumanMouse.move(x, y, speed_factor=1.5)
        time.sleep(random.uniform(0.05, 0.15)) # Pausa de decision humana corta
        if double:
            pyautogui.doubleClick(button=button)
        else:
            pyautogui.click(button=button)
        print(f"🎯 Click {button} en ({x:.0f}, {y:.0f})")

# Singleton para acceso rapido
mouse = FastHumanMouse()
