import os
import json
import sys
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

class RAGArchitect:
    def __init__(self):
        print("--- RAG ARCHITECT MCP SERVER ONLINE ---")
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_db = None
        self.db_path = os.path.join(os.path.dirname(__file__), "vector_store")

    def index_directory(self, root_dir, extension="*.py"):
        """Indexa archivos de un directorio por su contenido semantico"""
        documents = []
        for root, _, filenames in os.walk(root_dir):
            if any(x in root for x in ['.git', '__pycache__', 'venv', 'node_modules']):
                continue
            for filename in filenames:
                if filename.endswith(extension.replace('*','')):
                    file_path = os.path.join(root, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            documents.append(Document(page_content=content, metadata={"source": file_path}))
                    except: pass
        
        # Splitter para fragmentar el codigo en trozos manejables
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = text_splitter.split_documents(documents)
        
        print(f"📦 Indexando {len(docs)} fragmentos de {len(documents)} archivos...")
        self.vector_db = FAISS.from_documents(docs, self.embeddings)
        self.vector_db.save_local(self.db_path)
        return {"status": "success", "indexed_files": len(documents), "chunks": len(docs)}

    def semantic_search(self, query):
        """Busca por sentido semantico en la base de datos cargada"""
        if not self.vector_db:
            if os.path.exists(self.db_path):
                self.vector_db = FAISS.load_local(self.db_path, self.embeddings, allow_dangerous_deserialization=True)
            else:
                return {"error": "Base de datos no indexada. Usa index_directory primero."}
        
        results = self.vector_db.similarity_search(query, k=5)
        formatted_results = []
        for doc in results:
            formatted_results.append({
                "source": doc.metadata["source"],
                "content": doc.page_content[:300] + "..."
            })
        return {"status": "success", "results": formatted_results}

def run_mcp_loop():
    rag = RAGArchitect()
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line: break
            request = json.loads(line)
            method = request.get("method")
            params = request.get("params", {})
            
            if method == "index":
                result = rag.index_directory(params.get("path", os.getcwd()), params.get("ext", ".py"))
            elif method == "search":
                result = rag.semantic_search(params.get("query", ""))
            else:
                result = {"error": "Metodo no soportado"}
            
            print(json.dumps({"result": result}))
            sys.stdout.flush()
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            sys.stdout.flush()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        rag = RAGArchitect()
        print("Test: Indexando herramientas actuales...")
        print(json.dumps(rag.index_directory(os.path.join(os.getcwd(), "tools")), indent=2))
        print("\nTest: Busqueda semantica 'mouse movement'...")
        print(json.dumps(rag.semantic_search("mouse movement"), indent=2))
    else:
        run_mcp_loop()
