# Traceability Spec

Status: active

## Objetivo

Definir un formato mínimo y homogéneo de trazabilidad por ejecución para correlacionar decisiones y resultados entre:

- self-model
- episodic memory
- world model
- wrappers CLI (`run_browser.py`, `run_windows.py`, `run_worker.py`)
- orquestador

## Alcance

Este spec aplica a:

- ejecuciones de routing lógico (modelo/herramienta)
- ejecuciones de automatización (`browser`, `windows`, `worker`)
- eventos de fallback
- eventos de mouse/visión cuando se usan como ruta extrema

No reemplaza los logs técnicos de bajo nivel; complementa la capa operacional para auditoría y aprendizaje.

## Campos mínimos por ejecución

Cada ejecución debe registrar, como mínimo:

1. `intention`
   - Qué se intenta lograr (objetivo del usuario/tarea).
2. `route_selected`
   - Ruta final elegida (por ejemplo: `model:qwen3-coder-next`, `worker-core:browser`, `fallback:mouse_vision`).
3. `route_reason`
   - Motivo explícito y breve de la selección de ruta.
4. `tools_used`
   - Lista de herramientas invocadas durante la ejecución.
5. `result`
   - Resultado operativo (`success`, `partial`, `failure`) y resumen corto.
6. `fallback_applied`
   - Si se aplicó fallback; incluir tipo y razón. Si no aplica, registrar `none`.

## Formato recomendado (JSONL)

Formato recomendado: **JSONL**, un evento por línea, apto para agregación incremental.

### Esquema lógico recomendado

```json
{
  "trace_id": "uuid-v4",
  "timestamp": "2026-04-18T00:00:00Z",
  "agent": "shared_cli",
  "layer": "wrapper|orchestrator|self_model|episodic_memory|world_model",
  "event": "execution_start|route_decision|tool_call|execution_result|fallback_applied|mouse_vision_event",
  "intention": "string",
  "route_selected": "string",
  "route_reason": "string",
  "tools_used": ["string"],
  "result": {
    "status": "success|partial|failure",
    "summary": "string"
  },
  "fallback_applied": {
    "type": "none|model_switch|tool_switch|mouse_vision",
    "reason": "string"
  },
  "correlation": {
    "self_model_key": "string|null",
    "episodic_episode_id": "string|null",
    "world_state_id": "string|null"
  },
  "metadata": {
    "task_type": "string",
    "source": "string"
  }
}
```

### Reglas de correlación

- `trace_id` debe mantenerse estable para todos los eventos de una ejecución.
- `correlation.self_model_key` debe apuntar a la entrada de conocimiento/ruteo usada o actualizada.
- `correlation.episodic_episode_id` debe apuntar al episodio creado o reutilizado.
- `correlation.world_state_id` debe identificar el snapshot o actualización de estado relevante.
- `event` permite reconstruir la secuencia sin acoplarse al formato interno de cada motor.

## Eventos obligatorios para mouse/visión

Cuando se use mouse/visión, registrar obligatoriamente:

1. `mouse_vision_requested`
   - Quién solicitó el uso y con qué intención.
2. `mouse_vision_preconditions`
   - Evidencia de por qué no bastó CLI/API/ruta primaria.
3. `mouse_vision_action`
   - Acción ejecutada (click, move, scroll, screenshot, OCR/visión, etc.).
4. `mouse_vision_result`
   - Resultado de la acción y evidencia mínima.
5. `mouse_vision_fallback_reason`
   - Motivo concreto del fallback extremo (bloqueo UI, falta de selector, anti-bot, etc.).
6. `mouse_vision_exit`
   - Criterio de salida (vuelta a ruta normal o finalización).

### Regla crítica

Si hay fallback a mouse/visión, **siempre** registrar el motivo explícito (`mouse_vision_fallback_reason`) incluso si la ejecución termina en éxito.

## Ejemplo JSONL mínimo por ejecución

```json
{"trace_id":"9ef6...","timestamp":"2026-04-18T10:00:00Z","event":"route_decision","intention":"Abrir sitio y extraer título","route_selected":"worker-core:browser","route_reason":"Tarea web con navegación","tools_used":["browser"],"result":{"status":"partial","summary":"Ruta seleccionada"},"fallback_applied":{"type":"none","reason":""}}
{"trace_id":"9ef6...","timestamp":"2026-04-18T10:00:08Z","event":"execution_result","intention":"Abrir sitio y extraer título","route_selected":"worker-core:browser","route_reason":"Tarea web con navegación","tools_used":["browser"],"result":{"status":"success","summary":"Título extraído"},"fallback_applied":{"type":"none","reason":""}}
```

## Integración sugerida

- Wrappers: incluir referencia visible a este spec en ayuda/epílogo.
- Orquestador: enlazar este spec desde `README` y docs de memoria/estado para trazabilidad transversal.
- Motores de estado: mapear IDs de correlación sin romper formatos existentes.
