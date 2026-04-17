# RULES.md - Reglas de Operación

## Reglas Fundamentales

### 1. Antes de ejecutar cualquier skill
- Verificar que el script existe y es ejecutable
- Revisar `MEMORY/failures.md` para evitar repetir fracasos
- Confirmar con el usuario si la acción es destructiva

### 2. Después de ejecutar cualquier skill
- Loggear el resultado en `LOGS/<skill>_<timestamp>.log`
- Si falló, registrar en `MEMORY/failures.md` con:
  - Qué se intentó
  - Qué salió mal
  - Qué hacer en su lugar
- Si succeeded, considerar si hay aprendizaje para `MEMORY/learnings.md`

### 3. Sistema de memoria
- **Jamás inventar información** - Solo registrar lo que realmente ocurrió
- **Cada sesión nueva** - Leer MEMORY/ antes de empezar a trabajar
- **Actualizar proactivamente** - No esperar a que el usuario pida

### 4. Reglas de seguridad
- **Nunca ejecutar comandos destructivos** sin confirmación explícita
- **Nunca guardar secretos** en archivos del proyecto
- **Siempre verificar paths** antes de escribir/leer

### 5. Reglas de comunicación
- Hablar en cristiano (español claro)
- Respuetas cortas y directas
- No repetir lo que ya está en MEMORY/
- Si no sé algo, decirlo - no inventar

## Formato de Logs

```
[TIMESTAMP] SKILL: <nombre>
COMMAND: <comando ejecutado>
RESULT: SUCCESS|FAILURE
STDOUT: <output relevante>
STDERR: <errores si hay>
LEARNED: <insight si hay>
```

## Formato de Failures

```
## [TIMESTAMP] <descripción corta>

**Qué se intentó:** <lo que we attempted>
**Qué salió mal:** <what went wrong>
**Qué hacer en su lugar:** <alternative approach>
**Status:** OPEN|RESOLVED
```