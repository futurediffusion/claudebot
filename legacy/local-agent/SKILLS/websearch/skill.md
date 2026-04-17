# Web Search Skill

## Propósito
Buscar información actualizada en internet. Nunca depender solo del
conocimiento entrenado (que tiene cutoff). Usar Playwright para páginas
que requieren JavaScript, con fallback a requests para páginas estáticas.

## Archivo principal
- `fetch_info.py` - Script principal de fetching y búsqueda

## Uso

### Fetch simple
```bash
python SKILLS/websearch/fetch_info.py <url>
```
- Descarga el contenido de la URL
- Usa Playwright (JS) con fallback a requests
- Guarda en WORKSPACE/fetched_*.txt y LOGS/webfetch_*.log

### Fetch solo texto
```bash
python SKILLS/websearch/fetch_info.py <url> --text
```
- Lo mismo pero imprime solo el texto (sin HTML)

### Buscar en Bing
```bash
python SKILLS/websearch/fetch_info.py search <query>
```
- Busca en Bing y devuelve los top 5 resultados con títulos y URLs

## Dependencias
- playwright (`pip install playwright && playwright install chromium`)
- requests (`pip install requests`)
- beautifulsoup4 (`pip install beautifulsoup4`)

## Ejemplo output
```
Searching Bing for: python playwright tutorial
--------------------------------------------------

Top 5 results:

  1. Playwright Python Tutorial
     https://playwright.dev/python/docs/intro

  2. Scraping with Playwright and Python - Article
     https://example.com/article
...
```

## Integración
- Cuando necesites info actualizada (versiones, docs, noticias)
- Cuando问我 algo que sabe a "actualizado" y no estoy seguro de mi cutoff
- Primero busca, luego me muestras el resultado o me dices que lo analice