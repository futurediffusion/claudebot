# Execution Hierarchy

## Propósito

Definir un orden operativo explícito para ejecutar tareas con el menor costo, riesgo y fragilidad posibles.

La regla general es: **si un nivel resuelve el objetivo de forma confiable, no se salta al siguiente**.

## Pirámide de ejecución (de menor a mayor costo/riesgo)

1. **Planear**
2. **Código**
3. **Shell**
4. **Archivos**
5. **Browser automation**
6. **Herramientas OS**
7. **Mouse/visión**

## Nivel 1 — Planear

Objetivo:

- comprender la intención
- descomponer subtareas
- identificar dependencias y criterios de éxito
- seleccionar el nivel inicial más bajo viable

Salida esperada:

- plan breve con pasos ejecutables
- criterio de validación por paso
- riesgos conocidos

### Condiciones de salto a Código

Subir a **Código** cuando al menos una de estas condiciones sea verdadera:

- la tarea requiere crear o modificar lógica
- se necesita automatizar pasos repetibles en scripts
- el resultado objetivo es un artefacto de software

## Nivel 2 — Código

Objetivo:

- implementar lógica determinística y reutilizable
- resolver en texto estructurado antes de operar interfaces

Salida esperada:

- cambios concretos en código o configuración
- validación local (tests, lint o checks equivalentes)

### Condiciones de salto a Shell

Subir a **Shell** cuando:

- se necesita ejecutar comandos para compilar, probar, inspeccionar o transformar
- el flujo depende de herramientas CLI del sistema o del proyecto
- el estado real solo puede confirmarse ejecutando comandos

## Nivel 3 — Shell

Objetivo:

- usar comandos para inspección, ejecución y validación operativa

Salida esperada:

- comandos reproducibles
- evidencia de salida/estado (logs, exit codes, artefactos)

### Condiciones de salto a Archivos

Subir a **Archivos** cuando:

- se requiere lectura/escritura directa de contenidos
- hay que crear, mover o versionar artefactos específicos
- la manipulación de archivos no se resuelve de forma suficiente con un único comando

## Nivel 4 — Archivos

Objetivo:

- materializar entregables y estado persistente en el filesystem

Salida esperada:

- archivos creados/actualizados con estructura clara
- integridad mínima verificada (existencia, formato, referencias)

### Condiciones de salto a Browser automation

Subir a **Browser automation** cuando:

- el objetivo depende de interacción web real (navegación, formularios, extracción dinámica)
- la información/acción requerida solo está disponible en una sesión de navegador
- la evidencia debe venir de ejecución en contexto web activo

## Nivel 5 — Browser automation

Objetivo:

- operar sitios y flujos web de forma programática y reproducible

Salida esperada:

- acciones web trazables
- resultados capturados (datos, screenshots, archivos descargados)

### Condiciones de salto a Herramientas OS

Subir a **Herramientas OS** cuando:

- la tarea involucra aplicaciones de escritorio fuera del navegador
- se necesitan APIs/capacidades del sistema operativo (ventanas, procesos, foco)
- la coordinación entre apps locales es requisito del objetivo

## Nivel 6 — Herramientas OS

Objetivo:

- controlar entorno de escritorio con primitivas del sistema (apps, ventanas, procesos)

Salida esperada:

- operaciones de escritorio verificables
- estado del sistema actualizado en world model/episodic logs

### Condiciones de salto a Mouse/visión

Subir a **Mouse/visión** solo si todas las alternativas previas fallaron o no son viables, por ejemplo:

- UI sin accesibilidad o sin selectores confiables
- controles no expuestos por APIs ni automatización estándar
- bloqueo por renderizado dinámico/canvas donde no hay mejor interfaz

## Nivel 7 — Mouse/visión (fallback extremo)

**Definición:** capa de interacción por coordenadas/píxeles y percepción visual, usada únicamente como último recurso.

**Política:**

- no es estrategia por defecto
- requiere justificación explícita
- debe registrar evidencia suficiente para auditoría y aprendizaje

### Justificación obligatoria en logs

Cada uso de mouse/visión debe dejar una entrada estructurada con:

- `reason_for_escalation`: por qué fallaron/no aplican niveles 1–6
- `alternatives_attempted`: qué se intentó antes
- `risk_assessment`: riesgos (fragilidad, falsos clicks, drift de UI)
- `verification_method`: cómo se verificó resultado (screen diff, estado app, archivo)
- `rollback_or_recovery`: cómo revertir o recuperar en caso de error

## Reglas transversales

- **Minimizar escalado:** iniciar en el nivel más bajo viable.
- **Escalar por evidencia:** subir de nivel solo con condición de salto explícita.
- **Registrar decisiones:** cada salto debe quedar trazado en logs.
- **Desescalar cuando sea posible:** si aparece una vía más robusta en niveles inferiores, volver.

## Relación con el sistema

- Esta jerarquía complementa la política de routing y no la reemplaza.
- El self-model puede aprender patrones de cuándo un salto fue correcto o prematuro.
- El world model aporta el estado operativo para validar si realmente se necesitaba escalar.
