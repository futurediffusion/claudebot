# Deprecation Policy

Esta política define cómo clasificamos componentes activos vs legado en la documentación del workspace.

## Estados oficiales

| Estado | Significado operativo | Acción esperada |
|---|---|---|
| `active` | Ruta recomendada y mantenida para uso diario. | Usar por defecto en guías, ejemplos y nuevas tareas. |
| `discouraged` | Aún funciona en casos puntuales, pero ya no es la ruta preferida. | Evitar en nuevos flujos; usar solo con justificación. |
| `deprecated` | Camino en retirada con reemplazo claro y fecha de salida por definir. | No usar en nuevos cambios; planificar migración inmediata. |
| `archived` | Fuera del flujo operativo actual. Solo referencia histórica. | No usar salvo análisis forense o recuperación puntual. |

## Qué se considera legado

Los siguientes enfoques pasan a estado de legado y deben etiquetarse explícitamente:

1. **Rutas multimodelo por defecto** → `discouraged`  
   El sistema operativo actual es CLI-first con routing pragmático, no multimodelo por defecto.
2. **Supuestos de Groq/Ollama como base obligatoria** → `deprecated`  
   Proveedores/modelos deben tratarse como opt-in según tarea y disponibilidad.
3. **Estrategia mouse-first** → `deprecated`  
   Mouse/visión permanece como fallback extremo, no como estrategia principal.

## Cómo etiquetar documentación

Cuando un componente entre en retirada, añadir etiqueta visible en el encabezado o tabla:

- `Status: active`
- `Status: discouraged`
- `Status: deprecated`
- `Status: archived`

Formato recomendado en Markdown:

```md
## Nombre del componente
Status: discouraged
```

## Checklist de migración (sin romper casos útiles)

- [ ] Identificar el flujo legado exacto y su uso real (qué problema sí resuelve hoy).
- [ ] Documentar reemplazo `active` equivalente (comando, ruta o componente).
- [ ] Mantener compatibilidad temporal mediante fallback explícito (sin promocionarlo como default).
- [ ] Añadir criterio de entrada/salida para fallback (cuándo aplica y cuándo no).
- [ ] Validar al menos un caso histórico útil con el nuevo camino.
- [ ] Confirmar que ejemplos nuevos no usen rutas `discouraged/deprecated`.
- [ ] Marcar en docs el estado final del componente migrado.
- [ ] Registrar riesgos conocidos y plan de rollback.

## Relación con `legacy/`

Todo lo que ya vive en `legacy/` se considera `archived` salvo indicación contraria explícita.
