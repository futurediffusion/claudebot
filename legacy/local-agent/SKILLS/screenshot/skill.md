# Screenshot Skill

## Propósito
Captura la pantalla actual y opcionalmente describe su contenido usando visión.

## Archivos
- `take_screenshot.py` - Script principal de captura
- `describe_last_image.py` - Script para describir la última captura

## Uso

### take_screenshot.py
```bash
python SKILLS/screenshot/take_screenshot.py [output_path]
```
- Sin argumentos: guarda en `WORKSPACE/screenshot_<timestamp>.png`
- Con path: guarda en el path especificado
- Retorna: path donde se guardó la imagen

### describe_last_image.py
```bash
python SKILLS/screenshot/describe_last_image.py
```
- Lee la última imagen capturada
- Usa describe_image para analizarla
- Retorna: descripción en texto

## Dependencias
- PIL / Pillow (para captura)
- mss (alternativa cross-platform)
- anthropic SDK (para describe_image)

## Ejemplo de output
```
OK: screenshot_20260415_143022.png
```

## Notas
- Compatible con Windows (usando PIL/Pillow con MSS)
- La imagen queda disponible para vision skill