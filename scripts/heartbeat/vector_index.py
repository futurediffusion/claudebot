import sys
import os

# Añadir la raíz al path para importar knowledge_oracle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from knowledge_oracle import index_project
    print("Iniciando re-indexación vectorial...")
    index_project()
    print("Oráculo actualizado con éxito.")
except Exception as e:
    print(f"Error en indexación: {e}")
    sys.exit(1)
