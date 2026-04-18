# SKILLS Catalog

Catálogo operativo de skills para el workspace `claudebot`.

## Objetivo

Estandarizar **cuándo**, **cómo** y **con qué costo/riesgo** se usa cada skill antes de ejecutar tareas en browser, sistema, archivos o repositorios.

## Esquema de definición por skill

Cada skill se documenta con los campos:

- **Nombre**
- **Dominio**
- **Entradas esperadas**
- **Salidas esperadas**
- **Costo** (tiempo, complejidad, riesgo)
- **Fallbacks**
- **Owner**

---

## Categoría: Web research

### Skill: `web-research`
- **Dominio**: investigación web, verificación de fuentes, extracción de hechos.
- **Entradas esperadas**:
  - pregunta/hipótesis,
  - alcance temporal (ej. “últimos 30 días”),
  - nivel de rigor (rápido vs validado).
- **Salidas esperadas**:
  - resumen de hallazgos,
  - lista de fuentes,
  - notas de confianza e incertidumbre.
- **Costo**:
  - tiempo: medio,
  - complejidad: baja-media,
  - riesgo: medio (fuentes desactualizadas o sesgadas).
- **Fallbacks**:
  1. refinar query y repetir,
  2. limitar a fuentes primarias,
  3. marcar explícitamente “no concluyente”.
- **Owner**: Orchestrator / Knowledge workflows.

---

## Categoría: Downloads / install

### Skill: `downloads-install`
- **Dominio**: descarga de artefactos y preparación/instalación de herramientas.
- **Entradas esperadas**:
  - nombre y versión objetivo,
  - plataforma destino,
  - restricciones (offline, permisos, checksum).
- **Salidas esperadas**:
  - artefacto descargado o tool instalada,
  - ruta final,
  - validación básica (versión o checksum).
- **Costo**:
  - tiempo: medio-alto,
  - complejidad: media,
  - riesgo: alto (supply chain / incompatibilidades).
- **Fallbacks**:
  1. usar mirror o release alternativo,
  2. fijar versión anterior estable,
  3. abortar con diagnóstico reproducible.
- **Owner**: Platform / Environment maintainers.

---

## Categoría: Cleanup

### Skill: `cleanup`
- **Dominio**: limpieza de artefactos temporales, residuos de ejecución, cachés controladas.
- **Entradas esperadas**:
  - alcance de limpieza (carpetas, patrones, antigüedad),
  - política de borrado (soft/hard),
  - exclusiones obligatorias.
- **Salidas esperadas**:
  - reporte de elementos eliminados o archivados,
  - ahorro estimado de espacio,
  - lista de exclusiones respetadas.
- **Costo**:
  - tiempo: bajo,
  - complejidad: baja,
  - riesgo: medio-alto (borrado accidental).
- **Fallbacks**:
  1. dry-run,
  2. mover a cuarentena,
  3. restaurar desde backup.
- **Owner**: Ops / Workspace hygiene.

---

## Categoría: File organization

### Skill: `file-organization`
- **Dominio**: clasificación, renombrado y reubicación de archivos por reglas.
- **Entradas esperadas**:
  - directorio origen,
  - reglas de organización,
  - conflictos esperados (nombres duplicados, colisiones).
- **Salidas esperadas**:
  - estructura objetivo aplicada,
  - mapping origen→destino,
  - errores/conflictos pendientes.
- **Costo**:
  - tiempo: bajo-medio,
  - complejidad: media,
  - riesgo: medio (desorden o sobrescrituras).
- **Fallbacks**:
  1. simulación previa (plan-only),
  2. prefijos/sufijos anti-colisión,
  3. rollback por manifest.
- **Owner**: Ops / Personal workflow owners.

---

## Categoría: Browser tasks

### Skill: `browser-automation`
- **Dominio**: navegación automatizada, extracción, formularios, validación de UI.
- **Entradas esperadas**:
  - objetivo funcional,
  - URL inicial,
  - credenciales/secrets si aplica,
  - criterio de éxito observable.
- **Salidas esperadas**:
  - resultado de la tarea (extracto, estado, captura),
  - logs de pasos,
  - errores accionables si falla.
- **Costo**:
  - tiempo: medio,
  - complejidad: media-alta,
  - riesgo: medio (flakiness UI, cambios DOM, anti-bot).
- **Fallbacks**:
  1. retry con waits selectivos,
  2. degradar a extracción parcial,
  3. escalar a control manual asistido.
- **Owner**: Browser automation maintainers.

---

## Categoría: Setup / repos

### Skill: `setup-repos`
- **Dominio**: bootstrap de repos, dependencias, configuración local y validación inicial.
- **Entradas esperadas**:
  - URL/ruta de repo,
  - runtime requerido,
  - comandos de setup/test.
- **Salidas esperadas**:
  - entorno listo,
  - dependencias instaladas,
  - checks mínimos en verde (o diagnóstico).
- **Costo**:
  - tiempo: medio,
  - complejidad: media,
  - riesgo: medio-alto (drift de entorno).
- **Fallbacks**:
  1. usar lockfiles,
  2. aislar en entorno limpio,
  3. documentar fix-forward exacto.
- **Owner**: Repo maintainers / DevEx.

---

## Cuándo usar skill vs código directo vs shell

### Usar **skill** cuando
- la tarea es recurrente y ya tiene flujo conocido,
- hay riesgo operativo que exige validaciones/fallbacks,
- se necesita consistencia de entradas/salidas y trazabilidad.

### Usar **código directo** cuando
- hace falta lógica nueva no cubierta por skills existentes,
- hay que incorporar pruebas, tipado o refactors sostenibles,
- la solución debe vivir en el repo como capacidad estable.

### Usar **shell** cuando
- la acción es simple, atómica y de bajo riesgo,
- se requiere diagnóstico rápido (inspección, diff, estado),
- no compensa crear/ajustar una skill ni modificar código.

### Regla práctica de decisión
1. Si existe skill adecuada y el trabajo encaja en su contrato, **usar skill**.
2. Si no existe contrato claro pero la necesidad es duradera, **crear/ajustar código** (y luego skill si aplica).
3. Si es puntual y reversible, **shell** con logging mínimo.
