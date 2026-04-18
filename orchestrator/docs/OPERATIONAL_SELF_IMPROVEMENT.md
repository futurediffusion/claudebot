# Operational Self-Improvement (OSI)

## Objetivo

Definir un marco de **mejora operativa acotada** para el orquestador.

Este documento regula qué puede aprender el sistema después de ejecutar tareas, cómo medir ese aprendizaje y cómo persistirlo en:

- `self_model/` (conocimiento abstracto y reusable)
- `episodic_memory/` (historial concreto de ejecuciones)

La mejora se limita a optimizar rendimiento en tareas concretas, routing y uso de herramientas.

---

## Alcance permitido de aprendizaje

El aprendizaje automático/local está permitido únicamente en las siguientes categorías:

1. **Selección de skill**
   - Qué skill funcionó mejor para cada `task_type` y contexto.
   - Cuándo evitar una skill por baja tasa de éxito reciente.

2. **Comandos efectivos**
   - Comandos que resolvieron tareas con menor error y menor latencia.
   - Variantes de comandos que deben evitarse por fallos repetidos.

3. **Rutas rápidas (fast paths)**
   - Secuencias cortas de pasos con alta confiabilidad.
   - Atajos válidos por tipo de tarea (ej. build/test/fix loops).

4. **Patrones de fallo/fix**
   - Firmas de fallo recurrentes.
   - Fixes que demostraron resolver dichos fallos de forma estable.

> Regla base: cualquier aprendizaje debe estar respaldado por evidencia repetida (no por una sola ejecución aislada).

---

## Exclusiones explícitas (no objetivo)

Este sistema **no** persigue ni habilita:

- objetivos AGI
- auto-preservación
- auto-replicación
- expansión de objetivos no solicitados
- autonomía irrestricta

La auto-mejora es exclusivamente **operacional, local, acotada y auditable**.

---

## Métricas obligatorias

Para cada `task_type` se deben mantener, como mínimo, estas métricas:

1. **Tasa de éxito por tipo de tarea**
   - Definición: `success_count / total_count`
   - Ventana sugerida: rolling (ej. últimas 50 ejecuciones del tipo)

2. **Tiempo medio por tarea**
   - Definición: promedio de `duration_ms` en ejecuciones finalizadas
   - Recomendación: registrar también p50/p95 cuando haya suficiente volumen

3. **Retries evitados**
   - Definición operativa:
     - `retry_count` real por episodio
     - estimación de `retries_avoided` al usar fast paths o fixes ya conocidos
   - Objetivo: reducir retrabajo y ciclos redundantes

---

## Convenciones de integración con `self_model/`

Persistir señales agregadas (no logs crudos) en archivos de `self_model/` con estas convenciones.

### 1) `self_model/routing_knowledge.json`

Añadir/actualizar por `task_type`:

- `observed_stats.success_rate`
- `observed_stats.avg_duration_ms`
- `observed_stats.retry_rate`
- `observed_stats.retries_avoided_estimate`
- `preferred_skills` (ordenado por evidencia reciente)
- `fast_paths` (lista de secuencias recomendadas)

### 2) `self_model/tool_map.json`

Añadir/actualizar por comando/herramienta:

- `effectiveness.success_count`
- `effectiveness.failure_count`
- `effectiveness.avg_duration_ms`
- `effectiveness.last_seen_at`
- `avoid_when` (condiciones en las que conviene no usarlo)

### 3) `self_model/failure_patterns.json`

Añadir/actualizar patrones:

- `signature`
- `task_types`
- `effective_fixes`
- `fix_success_rate`
- `last_confirmed_at`

---

## Convenciones de integración con `episodic_memory/`

Cada episodio debe incluir campos mínimos para poder calcular las métricas anteriores y vincular evidencia con decisiones:

- `task_id`
- `task_type`
- `skill_selected`
- `commands_executed` (lista ordenada)
- `status` (`success` / `failure`)
- `duration_ms`
- `retry_count`
- `failure_signature` (si aplica)
- `fix_applied` (si aplica)
- `used_fast_path` (bool)
- `timestamp`

### Convención de trazabilidad

Cuando un episodio influya una decisión del self-model, registrar referencias cruzadas:

- en episodio: `promoted_to_self_model: true|false`
- en self-model: `evidence_episode_ids: []`

Esto permite auditoría y rollback de conocimiento degradado.

---

## Reglas de actualización

1. **Promoción por evidencia**
   - No promover skill/comando/fast-path hasta observar éxito repetido.

2. **Degradación por deriva**
   - Si cae la tasa de éxito o sube el tiempo medio de forma sostenida, bajar prioridad.

3. **Evitar sobreajuste**
   - No generalizar un fix específico a todos los contextos sin validación cruzada.

4. **Auditable by design**
   - Toda preferencia relevante debe poder rastrearse a episodios concretos.

---

## Criterio de éxito del OSI

Se considera que el sistema mejora operativamente cuando, para un mismo `task_type`, se observa de forma sostenida:

- mayor tasa de éxito,
- menor tiempo medio,
- menor número de retries,
- mayor reutilización de fixes efectivos.
