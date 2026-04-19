import json
import sys
import os
import requests
from urllib.parse import quote

class AutoResearchAgent:
    def __init__(self):
        print("--- AUTORESEARCH MCP AGENT ONLINE ---")

    def search_github(self, query):
        """Busca repositorios en GitHub por relevancia"""
        url = f"https://api.github.com/search/repositories?q={quote(query)}&sort=stars&order=desc"
        try:
            r = requests.get(url, timeout=10)
            items = r.json().get('items', [])
            results = []
            for item in items[:5]:
                results.append({
                    "full_name": item['full_name'],
                    "description": item['description'],
                    "stars": item['stargazers_count'],
                    "url": item['html_url']
                })
            return {"status": "success", "results": results}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def analyze_tech(self, topic):
        """Busca informacion tecnica general sobre un tema"""
        # Mock de busqueda profunda (en una implementacion real usaria un motor de busqueda)
        print(f"🕵️‍♂️ Investigando: {topic}...")
        return {
            "status": "success",
            "topic": topic,
            "summary": f"Resumen tecnico generado sobre {topic}...",
            "links": [f"https://github.com/search?q={quote(topic)}"]
        }

def run_mcp_loop():
    agent = AutoResearchAgent()
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line: break
            request = json.loads(line)
            method = request.get("method")
            params = request.get("params", {})
            
            if method == "search_github":
                result = agent.search_github(params.get("query", ""))
            elif method == "research":
                result = agent.analyze_tech(params.get("topic", ""))
            else:
                result = {"error": "Metodo no soportado"}
            
            print(json.dumps({"result": result}))
            sys.stdout.flush()
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            sys.stdout.flush()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        agent = AutoResearchAgent()
        print("Test: Buscando repositorios de Persistent AI Memory...")
        print(json.dumps(agent.search_github("persistent AI memory"), indent=2))
    else:
        run_mcp_loop()
