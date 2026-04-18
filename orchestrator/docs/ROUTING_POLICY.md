# Routing Policy

## Objetivo

Definir una política de enrutamiento estable para tareas de orquestación local, con escalado explícito por complejidad, riesgo, costo esperado e impacto del error.

## Orden de decisión base

1. **Gemini (default)**
   - Primera opción para la mayoría de tareas generales, rápidas o de bajo/medio riesgo.
2. **Claude / MiniMax (secundario)**
   - Segunda línea para tareas donde Gemini no sea ideal (por tipo de instrucción, estabilidad, o calidad de salida esperada).
3. **Codex / Claude premium (heavy/critical)**
   - Escalado para tareas pesadas o críticas que exijan mayor precisión, razonamiento profundo o cambios amplios.
4. **Ollama (opcional si disponible) — Status: deprecated como base**
   - Ruta alternativa local cuando haya modelos adecuados instalados y el caso lo permita.

## Criterios de escalado explícitos

Escalar de nivel cuando aumente uno o más factores:

- **Complejidad**
  - Multiarchivo, arquitectura, dependencias cruzadas, o necesidad de planificación extensa.
- **Riesgo**
  - Posibilidad alta de romper funcionalidades, dañar estado del sistema, o introducir regresiones.
- **Costo esperado**
  - Si el costo de reintentos, validación o correcciones supera el costo de usar un modelo más fuerte desde el inicio.
- **Impacto del error**
  - Errores con consecuencias importantes en producción, datos, seguridad o confianza operativa.

Regla práctica:

- Bajo impacto + baja complejidad -> mantener ruta base (Gemini).
- Medio riesgo/costo -> subir a Claude o MiniMax.
- Alto riesgo, alta complejidad o alto impacto de error -> escalar a Codex o Claude premium.

## Proveedores opt-in por caso

- **Groq y otros proveedores** se consideran **opt-in por caso**. **Status: deprecated como base**
- No forman parte de la **base del sistema** por defecto.
- Deben activarse explícitamente cuando el caso de uso lo justifique (p. ej., validación específica, parsing rápido, costo puntual).

## Notas de gobernanza

- Esta política prioriza consistencia operativa sobre experimentación continua.
- Cambios en el orden base o en reglas de escalado deben documentarse antes de aplicarse.
