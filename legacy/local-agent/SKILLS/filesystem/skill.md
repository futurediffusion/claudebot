# Filesystem Skill

## Propósito
Analizar carpetas y archivos, resumir estructuras, y proporcionar
información contextual sobre el filesystem del proyecto.

## Archivos
- `summarize_folder.py` - Script principal de análisis

## Uso

### summarize_folder.py
```bash
python SKILLS/filesystem/summarize_folder.py <path> [depth]
```
- `<path>`: Carpeta a analizar (required)
- `[depth]`: Profundidad máxima de recursión (default: 2)
- Sin argumentos: usa el directorio actual

## Output ejemplo
```
SUMMARY: /path/to/folder
├── folder1/
│   ├── file1.txt
│   └── file2.txt
├── folder2/
│   └── (empty)
└── README.md

Stats:
- Total files: 47
- Total folders: 12
- Largest file: something.zip (15MB)
- Last modified: 2026-04-15
```

## Dependencias
- Python standard library (os, glob, pathlib)

## Integración
- Se usa antes de executar skills que necesitan conocer el proyecto
- Útil para el flujo "entrada en caliente" del agent