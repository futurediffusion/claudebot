# Local Agent - Claude Code Enhancement

Sistema de agentes locales para extender las capacidades de Claude Code.

## Estructura

```
local-agent/
├── SKILLS/        ← Habilidades ejecutables (scripts + descripciones)
├── TOOLS/         ← Herramientas utilitarias independientes
├── MEMORY/        ← Sistema de memoria persistente
├── WORKSPACE/     ← Espacio de trabajo temporal
├── LOGS/          ← Logs de ejecución
├── SYSTEM.md      ← Especificación del sistema
└── RULES.md       ← Reglas de operación
```

## Skills Disponibles

- `screenshot` - Captura y descripción de pantalla
- `filesystem` - Análisis de carpetas y archivos
- `vision` - Inspección de imágenes
- `testing` - Ejecución de pruebas
- `webgrab` - Obtención de páginas web

## Uso

Cada skill se invoca via Skill tool. Ver `SKILLS/<skill>/skill.md` para documentación específica.

## Sistema de Memoria

El agent mantiene memoria persistente en `MEMORY/`:
- `identity.md` - Quién soy y cómo opero
- `learnings.md` - Conocimientos adquiridos
- `failures.md` - Registro de intentos fallidos
- `todos.md` - Estado de tareas en curso