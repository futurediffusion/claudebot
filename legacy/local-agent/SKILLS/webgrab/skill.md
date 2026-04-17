# Webgrab Skill

## Propósito
Obtener páginas web para análisis offline. Soporta HTML plano,
extracción de links, y descarga de recursos estáticos.

## Archivos
- `fetch_page.py` - Script principal de obtención

## Uso

### fetch_page.py
```bash
python SKILLS/webgrab/fetch_page.py <url> [--output <path>] [--links|--text]
```
- `<url>`: URL a obtener (required)
- `--output <path>`: Guardar contenido en archivo
- `--links`: Extraer solo links
- `--text`: Extraer solo texto (strip HTML)

## Output ejemplo
```
URL: https://example.com
STATUS: 200
SIZE: 15,234 bytes
OUTPUT: /path/to/saved/page.html
LINKS: 47 found
```

## Dependencias
- requests (HTTP library)
- beautifulsoup4 (para parsing HTML, opcional)

## Limitaciones
- No ejecuta JavaScript (server-side rendering only)
- No sigue redirects automáticamente
- Timeout de 30 segundos por defecto

## Loggers
- Los URLs visitados se registran en `LOGS/webgrab_<timestamp>.log`