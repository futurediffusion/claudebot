import sys
import os
import faiss

# Añadir la raíz al path para importar knowledge_oracle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

INDEX_FILE = "knowledge_base.index"

def run():
    if os.path.exists(INDEX_FILE):
        index = faiss.read_index(INDEX_FILE)
        if index.ntotal > 10000:
            print(f"Index existente detectado con {index.ntotal} vectores. Saltando re-indexación pesada.")
            return

    try:
        from knowledge_oracle import index_project
        print("Iniciando indexación inicial (esta vez será la única larga)...")
        index_project()
        print("Oráculo inicializado con éxito.")
    except Exception as e:
        print(f"Error en indexación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
