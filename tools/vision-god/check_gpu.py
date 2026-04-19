import torch
import sys

print("--- VERIFICADOR DE POTENCIA GRAFICA ---")
print(f"Version de Python: {sys.version}")
print(f"Version de PyTorch: {torch.__version__}")

cuda_available = torch.cuda.is_available()
print(f"¿CUDA Disponible?: {'SI' if cuda_available else 'NO'}")

if cuda_available:
    print(f"GPU Detectada: {torch.cuda.get_device_name(0)}")
    print(f"Capacidad de Computo: {torch.cuda.get_device_capability(0)}")
    print(f"Memoria Total: {torch.cuda.get_device_properties(0).total_memory / 1024**2:.0f} MB")
else:
    print("ERROR: No se detecto soporte para GPU. Revisa la instalacion de drivers.")
