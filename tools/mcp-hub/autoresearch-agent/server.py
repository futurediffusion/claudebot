import re
import requests
from urllib.parse import quote
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("autoresearch")

HEADERS = {"User-Agent": "claudebot/2.0"}


def _search_github(query):
    url = f"https://api.github.com/search/repositories?q={quote(query)}&sort=stars&order=desc"
    try:
        r = requests.get(url, timeout=10, headers=HEADERS)
        items = r.json().get('items', [])
        return {"status": "success", "results": [
            {"full_name": i['full_name'], "description": i['description'],
             "stars": i['stargazers_count'], "url": i['html_url']} for i in items[:5]
        ]}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def search_github(query: str) -> dict:
    """Busca repositorios en GitHub por relevancia y estrellas. Devuelve top 5."""
    return _search_github(query)


@mcp.tool()
def web_search(query: str, max_results: int = 5) -> dict:
    """Búsqueda web real via DuckDuckGo Instant Answer API. Devuelve títulos y URLs."""
    url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json&no_redirect=1&no_html=1"
    try:
        r = requests.get(url, timeout=10, headers=HEADERS)
        data = r.json()
        results = []
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if "Text" in topic and "FirstURL" in topic:
                results.append({"title": topic["Text"][:120], "url": topic["FirstURL"]})
        abstract = data.get("AbstractText", "")
        if abstract:
            results.insert(0, {"title": abstract[:200], "url": data.get("AbstractURL", "")})
        return {"status": "success", "query": query, "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def fetch_page(url: str) -> dict:
    """Descarga contenido de una URL pública (GitHub READMEs, HuggingFace cards, docs). Retorna texto limpio."""
    try:
        r = requests.get(url, timeout=15, headers=HEADERS)
        text = re.sub(r'<[^>]+>', ' ', r.text)
        text = re.sub(r'\s+', ' ', text).strip()[:4000]
        return {"status": "success", "url": url, "content": text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    mcp.run()
