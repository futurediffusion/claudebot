# Vision Skill

## Propósito
Capturar la pantalla y analizar lo que hay usando Ollama con un modelo
multimodal (gemma4). Compensa la "ceguera" operativa de los modelos.

## Archivo principal
- `analyze_screen.py` - Toma screenshot y analiza con Ollama

## Uso

### analyze_screen.py
```bash
python SKILLS/vision/analyze_screen.py
```
- Toma screenshot automáticamente
- Lo envía a gemma4 via Ollama
- Imprime el análisis en español
- Guarda log en LOGS/

## Dependencias
- Pillow (para captura de pantalla)
- Ollama corriendo con gemma4:latest
- urllib (stdlib)

## Output típico
```
VISION ANALYSIS
==================================================

[1] Tomando screenshot...
SCREENSHOT: D:\...\WORKSPACE\screenshot_20260415_...

[2] Analizando con gemma4 via Ollama...

ANÁLISIS:
--------------------------------------------------
La imagen muestra una terminal de Windows con...
...
--------------------------------------------------

LOG: D:\...\LOGS\vision_20260415_...
```

## Integración
- Se invoca cuando necesito "ver" qué está pasando en pantalla
- Útil después de ejecutar comandos para verificar resultados
- Reemplaza mi incapacidad de ver el terminal