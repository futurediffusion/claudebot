import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path

MODEL_NAME = "all-MiniLM-L6-v2"
INDEX_FILE = "knowledge_base.index"
METADATA_FILE = "metadata.json"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

embedding_model = None
faiss_index = None
documents_metadata = []


def get_embedding_model():
    global embedding_model
    if embedding_model is None:
        print(f"Cargando modelo: {MODEL_NAME}")
        embedding_model = SentenceTransformer(MODEL_NAME)
    return embedding_model


def load_file_content(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    if ext in [".md", ".txt", ".py", ".json", ".yaml", ".yml", ".toml", ".sql"]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except (UnicodeDecodeError, IOError):
            pass
    return ""


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    if len(text) <= chunk_size:
        return [text] if text.strip() else []
    
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        
        if end < text_len:
            last_newline = chunk.rfind("\n")
            last_space = chunk.rfind(" ")
            if last_newline > chunk_size // 2:
                end = start + last_newline
            elif last_space > chunk_size // 2:
                end = start + last_space
        
        chunks.append(chunk.strip())
        start = end - overlap if end < text_len else text_len
    
    return [c for c in chunks if c]


def should_ignore(path: str) -> bool:
    ignore_dirs = {".venv", ".git", "node_modules", "__pycache__", ".venv_vision", "venv", "venv_vision"}
    parts = Path(path).parts
    for part in parts:
        if part in ignore_dirs or part.startswith("."):
            return True
    return False


def collect_files(base_dirs: list[str]) -> list[str]:
    files = []
    for base_dir in base_dirs:
        base_path = Path(base_dir)
        if not base_path.exists():
            continue
        for root, dirs, filenames in os.walk(base_path):
            if should_ignore(root):
                dirs.clear()
                continue
            for fname in filenames:
                fpath = os.path.join(root, fname)
                if not should_ignore(fpath):
                    files.append(fpath)
    return files


def index_project(base_dirs: list[str] = None):
    global faiss_index, documents_metadata
    
    if base_dirs is None:
        base_dirs = ["skills", "memory", "docs"]
    
    print(f"Recolectando archivos de: {base_dirs}")
    files = collect_files(base_dirs)
    print(f"Archivos encontrados: {len(files)}")
    
    model = get_embedding_model()
    all_chunks = []
    all_metadata = []
    
    for fpath in files:
        content = load_file_content(fpath)
        if not content:
            continue
        
        chunks = chunk_text(content)
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadata.append({
                "file": fpath,
                "chunk_id": i,
                "total_chunks": len(chunks)
            })
    
    print(f"Chunks generados: {len(all_chunks)}")
    
    if not all_chunks:
        print("No hay contenido para indexar")
        return
    
    print("Generando embeddings...")
    embeddings = model.encode(all_chunks, show_progress_bar=True)
    embeddings = np.array(embeddings).astype("float32")
    
    print("Construyendo índice faiss...")
    dimension = embeddings.shape[1]
    faiss_index = faiss.IndexFlatL2(dimension)
    faiss_index.add(embeddings)
    
    documents_metadata = all_metadata
    
    print(f"Índice creado con {faiss_index.ntotal} vectores")
    
    save_index()


def save_index():
    global faiss_index, documents_metadata
    
    if faiss_index is not None:
        faiss.write_index(faiss_index, INDEX_FILE)
        print(f"Índice guardado: {INDEX_FILE}")
    
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(documents_metadata, f, indent=2)
        print(f"Metadatos guardados: {METADATA_FILE}")


def load_index():
    global faiss_index, documents_metadata
    
    if os.path.exists(INDEX_FILE):
        faiss_index = faiss.read_index(INDEX_FILE)
        print(f"Índice cargado: {faiss_index.ntotal} vectores")
    else:
        print("Índice no encontrado")
        return False
    
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            documents_metadata = json.load(f)
        print(f"Metadatos cargados: {len(documents_metadata)} entradas")
    else:
        print("Metadatos no encontrados")
        documents_metadata = []
    
    get_embedding_model()
    return True


def query_oracle(question: str, top_k: int = 3) -> list[dict]:
    global faiss_index, documents_metadata
    
    if faiss_index is None:
        if not load_index():
            print("Indexando proyecto primero...")
            index_project()
    
    model = get_embedding_model()
    query_embedding = model.encode([question]).astype("float32")
    
    search_k = min(top_k * 2, faiss_index.ntotal)
    distances, indices = faiss_index.search(query_embedding, search_k)
    
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < len(documents_metadata):
            meta = documents_metadata[idx]
            results.append({
                "file": meta["file"],
                "chunk_id": meta["chunk_id"],
                "distance": float(dist),
                "text": ""
            })
    
    unique_files = {}
    for r in results:
        key = (r["file"], r["chunk_id"])
        if key not in unique_files:
            unique_files[key] = r
    
    final_results = []
    for r in list(unique_files.values())[:top_k]:
        try:
            idx = documents_metadata.index(
                next(m for m in documents_metadata 
                if m["file"] == r["file"] and m["chunk_id"] == r["chunk_id"])
            )
            content = load_file_content(r["file"])
            chunks = chunk_text(content)
            if r["chunk_id"] < len(chunks):
                r["text"] = chunks[r["chunk_id"]][:800]
        except:
            pass
        final_results.append(r)
    
    return final_results


def query(question: str, top_k: int = 3) -> list[dict]:
    return query_oracle(question, top_k)


if __name__ == "__main__":
    print("=== Knowledge Oracle ===")
    print("1. Indexar proyecto")
    print("2. Consultar")
    print("3. Cargar índice existente")
    
    choice = input("Opción: ").strip()
    
    if choice == "1":
        index_project()
    elif choice == "2":
        if not load_index():
            index_project()
        while True:
            q = input("\nPregunta (enter para salir): ").strip()
            if not q:
                break
            results = query_oracle(q)
            for i, r in enumerate(results):
                print(f"\n--- Resultado {i+1} ---")
                print(f"Archivo: {r['file']}")
                print(f"Distancia: {r['distance']:.2f}")
                print(f"Contenido: {r['text'][:300]}...")
    elif choice == "3":
        load_index()
