# Matriz de capacidades

Esta matriz separa claramente lo que el sistema puede hacer de forma **confiable en producción** de lo que existe solo como **capacidad experimental** para pruebas internas.

## Capacidad real (producción)

| Capacidad | Estado | Nivel de confianza | Costo | Latencia | Condición de uso |
|---|---|---|---|---|---|
| Shell | Disponible y estable | Alto | Bajo | Baja | Usar por defecto para automatización CLI, ejecución de comandos y validaciones reproducibles. |
| Filesystem | Disponible y estable | Alto | Bajo | Baja | Usar para lectura/escritura local dentro del repo y artefactos de ejecución. |
| Browser automation | Disponible vía worker-core/browser | Medio-Alto | Medio | Media | Usar cuando la tarea exige navegación web, extracción o flujos browser-first. |
| Repo management | Disponible y estable | Alto | Bajo | Baja | Usar para cambios en Git, commits, diffs, ramas y preparación de entregables. |
| Downloads/installs | Disponible con restricciones de entorno | Medio | Medio | Media-Alta | Usar solo cuando sea necesario para dependencias faltantes y con validación posterior. |

## Capacidad experimental (no gobernante)

| Capacidad | Estado | Nivel de confianza | Costo | Latencia | Condición de uso |
|---|---|---|---|---|---|
| Mouse/vision | Experimental | Bajo-Medio | Medio-Alto | Media-Alta | Usar solo como fallback cuando no exista ruta CLI/browser robusta. |
| Auto-mejora | Experimental | Bajo | Variable | Alta | Usar en iteraciones controladas, nunca como mecanismo autónomo gobernante. |
| Routing multimodel local | Experimental | Bajo-Medio | Medio | Media | Usar para pruebas de orquestación local; no reemplaza el routing pragmático principal. |
