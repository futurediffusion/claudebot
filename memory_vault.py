import json
import os
import numpy as np
import requests
from datetime import datetime

class MemoryVault:
    def __init__(self, vault_path='life_logs/vector_vault.json'):
        self.vault_path = vault_path
        self.embeddings_model = "nomic-embed-text" # Modelo ligero de embeddings
        self.vault = self._load_vault()

    def _load_vault(self):
        if os.path.exists(self.vault_path):
            with open(self.vault_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _get_embedding(self, text):
        try:
            response = requests.post('http://127.0.0.1:11434/api/embeddings', 
                                   json={"model": self.embeddings_model, "prompt": text})
            return response.json()['embedding']
        except Exception as e:
            print(f"Error generando embedding: {e}")
            return None

    def add_memory(self, entry_id, text, metadata):
        embedding = self._get_embedding(text)
        if embedding:
            self.vault.append({
                "id": entry_id,
                "text": text,
                "vector": embedding,
                "metadata": metadata
            })
            with open(self.vault_path, 'w', encoding='utf-8') as f:
                json.dump(self.vault, f)
            return True
        return False

    def search_similar(self, query_text, top_k=2):
        query_vec = self._get_embedding(query_text)
        if not query_vec or not self.vault:
            return []

        def cosine_similarity(v1, v2):
            return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

        similarities = []
        for memory in self.vault:
            sim = cosine_similarity(query_vec, memory['vector'])
            similarities.append((sim, memory))

        # Ordenar por similitud
        similarities.sort(key=lambda x: x[0], reverse=True)
        return similarities[:top_k]

if __name__ == "__main__":
    import sys
    vault = MemoryVault()
    
    if len(sys.argv) < 3:
        sys.exit(0)

    action = sys.argv[1]
    
    if action == "add":
        # python memory_vault.py add "id" "texto" "metadata_json"
        entry_id = sys.argv[2]
        text = sys.argv[3]
        metadata = json.loads(sys.argv[4])
        vault.add_memory(entry_id, text, metadata)
        print("Memoria indexada.")
        
    elif action == "search":
        # python memory_vault.py search "texto a buscar"
        query = sys.argv[2]
        results = vault.search_similar(query)
        # Devolver solo el texto y la fecha para el prompt
        output = [{"text": r[1]['text'], "date": r[1]['metadata'].get('date')} for r in results]
        print(json.dumps(output))
