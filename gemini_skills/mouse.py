import ctypes
import sys
import time

# Constantes de eventos del mouse en Windows
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010

def move_mouse(x, y):
    # Mover el cursor a la posición exacta
    ctypes.windll.user32.SetCursorPos(int(x), int(y))

def perform_click(button='left'):
    # Hacer clic (presionar y soltar muy rápido)
    if button == 'left':
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    elif button == 'right':
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Error. Uso: python mouse.py <X> <Y> [accion]")
        print("Acciones: move, click, right_click, double_click")
        sys.exit(1)
    
    x = sys.argv[1]
    y = sys.argv[2]
    action = sys.argv[3] if len(sys.argv) > 3 else "move"
    
    # 1. Siempre nos movemos a la coordenada primero
    move_mouse(x, y)
    print(f"ACCION: Ratón movido a ({x}, {y})")
    
    time.sleep(0.1) # Pequeña pausa humana
    
    # 2. Ejecutamos la acción si la hay
    if action == 'click':
        perform_click('left')
        print("ACCION: Clic izquierdo realizado.")
    elif action == 'right_click':
        perform_click('right')
        print("ACCION: Clic derecho realizado.")
    elif action == 'double_click':
        perform_click('left')
        time.sleep(0.05)
        perform_click('left')
        print("ACCION: Doble clic izquierdo realizado.")
    elif action == 'move':
        pass # Solo mover
    else:
        print(f"ERROR: Acción desconocida '{action}'. Me he equivocado.")
