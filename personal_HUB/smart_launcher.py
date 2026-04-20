import socket
import subprocess
import sys
import os
from pathlib import Path

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def launch_app(app_name, path):
    # Intentar puerto 3000, luego 3001, 3002...
    port = 3000
    while is_port_in_use(port):
        print(f" Port {port} is busy. Trying next...")
        port += 1
    
    print(f"--- Starting {app_name} on port {port} ---")
    
    # Cambiar al directorio de la app
    os.chdir(path)
    
    # En Next.js se puede pasar el puerto con -p
    cmd = f"npm run dev -- -p {port}"
    
    # Ejecutar
    try:
        # Usamos shell=True para Windows y subprocess.Popen para no bloquear
        subprocess.Popen(cmd, shell=True)
        print(f" SUCCESS: {app_name} is launching at http://localhost:{port}")
    except Exception as e:
        print(f" ERROR launching {app_name}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python smart_launcher.py <app_name> <relative_path>")
        sys.exit(1)
    
    app_name = sys.argv[1]
    # El path es relativo a la raíz del proyecto
    app_path = Path(sys.argv[2]).resolve()
    launch_app(app_name, app_path)
