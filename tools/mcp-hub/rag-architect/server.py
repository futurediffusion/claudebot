import os
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("rag-architect")

_DB_PATH = os.path.join(os.path.dirname(__file__), "vector_store")
_rag = None  # lazy init para evitar carga de FAISS en startup


def _get_rag():
    global _rag
    if _rag is None:
        from langchain_community.vectorstores import FAISS
        from langchain_huggingface import HuggingFaceEmbeddings
        _rag = {"embeddings": HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2"), "db": None}
        if os.path.exists(_DB_PATH):
            _rag["db"] = FAISS.load_local(_DB_PATH, _rag["embeddings"], allow_dangerous_deserialization=True)
    return _rag


@mcp.tool()
def index_directory(path: str, extension: str = ".py") -> dict:
    """Indexa semánticamente los archivos de un directorio usando FAISS + MiniLM."""
    from langchain_community.vectorstores import FAISS
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document

    r = _get_rag()
    documents = []
    for root, _, filenames in os.walk(path):
        if any(x in root for x in ['.git', '__pycache__', 'venv', 'node_modules']):
            continue
        for filename in filenames:
            if filename.endswith(extension):
                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        documents.append(Document(page_content=f.read(), metadata={"source": file_path}))
                except Exception:
                    pass

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = splitter.split_documents(documents)
    r["db"] = FAISS.from_documents(docs, r["embeddings"])
    r["db"].save_local(_DB_PATH)
    return {"status": "success", "indexed_files": len(documents), "chunks": len(docs)}


@mcp.tool()
def semantic_search(query: str) -> dict:
    """Busca por significado semántico en el índice FAISS. Requiere haber indexado primero."""
    r = _get_rag()
    if r["db"] is None:
        return {"error": "Base de datos no indexada. Usa index_directory primero."}
    results = r["db"].similarity_search(query, k=5)
    return {
        "status": "success",
        "results": [{"source": d.metadata["source"], "content": d.page_content[:300] + "..."} for d in results],
    }


if __name__ == "__main__":
    mcp.run()
