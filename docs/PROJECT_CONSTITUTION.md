# Constitución del Proyecto

> Documento normativo primario para el workspace `claudebot` y su núcleo `orchestrator`.

## 1) Identidad oficial

- **Nombre oficial**: **Sistema local CLI-first para automatización personal en PC**.
- **Misión**: resolver trabajo cotidiano de forma directa, repetible y verificable, priorizando operación local y resultados útiles por encima de complejidad teórica.
- **Naturaleza del sistema**:
  - No es AGI.
  - No es mouse-first (estado: `deprecated` como estrategia por defecto).
  - No es multimodelo por defecto (estado: `discouraged` como supuesto base).

## 2) Principios de diseño

1. **Utilidad práctica primero**
   - Toda decisión debe justificar cómo reduce trabajo manual real (limpieza, organización, instalación, reparación, automatización web).
2. **Local-first por defecto**
   - Se privilegia ejecución local y controlable antes que dependencias externas innecesarias.
3. **CLI-first como interfaz primaria**
   - El camino principal de operación es por comandos, scripts y wrappers reproducibles.
4. **Routing pragmático, no dogmático**
   - El enrutamiento se define por costo/beneficio y tasa de éxito observada, no por preferencias estéticas de stack.
5. **Trazabilidad mínima obligatoria**
   - Toda ejecución relevante debe permitir reconstruir intención, ruta, motivo, resultado y fallback.
6. **Fallback explícito y acotado**
   - Mouse/visión se permite sólo cuando las rutas superiores no son viables.
7. **Compatibilidad operativa entre agentes**
   - El comportamiento debe mantenerse consistente entre orchestrator y wrappers raíz.

## 3) Prioridades

Prioridad descendente de objetivos del proyecto:

1. **Confiabilidad operativa diaria**.
2. **Reproducibilidad de flujos (CLI/scripts)**.
3. **Observabilidad y trazabilidad de decisiones**.
4. **Cobertura de tareas frecuentes de productividad personal**.
5. **Extensibilidad controlada (nuevas rutas/modelos) sin degradar lo anterior**.

## 4) No-objetivos

Este proyecto **no** persigue como objetivo primario:

- demostrar capacidades de AGI;
- maximizar complejidad arquitectónica por sí misma;
- convertir mouse/visión en ruta predeterminada;
- adoptar múltiples proveedores/modelos como requisito base;
- optimizar benchmarks desconectados del uso diario real.

## 5) Jerarquía de ejecución (normativa)

Orden oficial de resolución por capas:

1. **Flujo CLI-first / wrappers directos**.
2. **Routing de orchestrator para tareas de código/planificación**.
3. **Rutas de automatización browser/windows por worker-core cuando aplica**.
4. **Fallback extremo mouse/visión sólo bajo bloqueo real de rutas superiores**.

Reglas:

- Saltar a una capa inferior requiere justificación observable (limitación técnica, incapacidad de herramienta o restricción del entorno).
- Toda degradación de ruta debe registrarse como evento de fallback trazable.

## 6) Política de routing (resumen vinculante)

- Se debe aplicar intención de usuario + tipo de tarea + restricciones del entorno.
- Para automatización natural (browser/windows), priorizar delegación operacional antes de forzar rutas de generación de código.
- Para tareas de código/arquitectura, usar router de modelos del orchestrator conforme política vigente.
- El routing debe ser **explicable**: cada decisión debe tener motivo legible.

> Implementación detallada: ver documentación operativa específica de routing y jerarquía.

## 7) Política de deprecaciones

Estados oficiales permitidos:

- `active`
- `discouraged`
- `deprecated`
- `archived`

Normas:

- Ningún cambio puede promover una capacidad `deprecated` a comportamiento por defecto sin aprobación explícita.
- Las rutas `discouraged` requieren justificación breve cuando se usen como principal.
- Toda migración debe incluir impacto, plan de transición y criterio de salida verificable.

## 8) Decisiones irreversibles

Las siguientes decisiones se consideran **irreversibles** salvo cambio constitucional explícito:

1. **CLI-first** como interfaz operativa primaria del sistema.
2. **Mouse fallback** (mouse/visión) sólo como último recurso y nunca como default.
3. **Local-first** como postura base de ejecución.
4. **Pragmatismo orientado a utilidad diaria** como criterio rector frente a experimentación.

## 9) Proceso corto de cambios constitucionales (anti-deriva)

Para modificar esta constitución, se exige el siguiente proceso mínimo:

1. **Quién propone**
   - Owner del área afectada (o mantenedor principal del repositorio).
2. **Qué archivo(s) tocar**
   - Primario: `docs/PROJECT_CONSTITUTION.md`.
   - Referencias obligatorias: `README.md` y `orchestrator/README.md` si cambia semántica pública.
3. **Criterios de aceptación**
   - Coherencia con identidad oficial y principios de diseño.
   - No contradicción con jerarquía de ejecución ni política de deprecaciones.
   - Impacto descrito en lenguaje operativo (qué cambia en ejecución real).
   - Diff pequeño, explícito y revisable.

Sin cumplir estos tres puntos, el cambio se considera inválido por gobernanza.

## 10) Relación con documentos operativos

Esta constitución define el marco normativo de alto nivel.
Los documentos operativos detallan implementación y procedimientos:

- `orchestrator/docs/ROUTING_POLICY.md`
- `orchestrator/docs/EXECUTION_HIERARCHY.md`
- `docs/DEPRECATION_POLICY.md`
- `docs/TRACEABILITY_SPEC.md`

En caso de conflicto, prevalece esta constitución para decisiones de dirección del proyecto.
