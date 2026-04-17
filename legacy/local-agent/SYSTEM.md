# SYSTEM.md - Especificación del Sistema Local Agent

## Propósito
Extender las capacidades de Claude Code con un sistema de agent local que puede:
1. Capturar y analizar información visual
2. Ejecutar herramientas del sistema
3. Mantener memoria persistente entre sesiones
4. Registrar fracasos para no repetirlos

## Arquitectura

```
User ──► Claude Code ──► Skill/Tool ──► Resultado
                    ▲
                    │
              MEMORY/ (persistente)
```

## Componentes

### SKILLS/
Skills son unidades de trabajo completas: script + metadata + descripción.
Cada skill vive en su propia carpeta y es autocontenida.

### TOOLS/
Herramientas utilitarias simples. Scripts independientes que pueden
ser llamados directamente. No tienen metadata复杂的.

### MEMORY/
Sistema de memoria persistente. Se actualiza después de cada operación
importante para mantener contexto entre sesiones.

## Flujo de Ejecución

1. User invoca skill via Skill tool
2. Skill ejecuta su script principal
3. Resultado se registra en LOGS/
4. Si hay aprendizaje nuevo, se actualiza MEMORY/
5. Resultado se devuelve al user

## Principios de Diseño

- **Fallo rápido**: Si algo falla, registrar en failures.md inmediatamente
- **Transparencia**: Todo se loggea, nada se oculta
- **Auto-mejora**: MEMORY/ se actualiza proactivamente
- **Simplicidad**: Cada skill hace una cosa bien hecha