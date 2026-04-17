# Legacy

Aquí quedaron archivados los intentos previos y prototipos que ya no son la entrada principal del workspace.

## Contenido

- [cli-gemma-prototype/](D:/IA/CODE/claudebot/legacy/cli-gemma-prototype): experimento inicial con `run_gemma.py`, `run_shell.py`, prompts y skills simples.
- [local-agent/](D:/IA/CODE/claudebot/legacy/local-agent): sistema alterno de agente local con memoria, skills, logs y workspace propio.

## Criterio

Nada de esto se eliminó.

Se movió fuera del root porque:
- no participa en el flujo actual del `orchestrator`
- duplicaba nombres como `skills`, `workspace` y `agent`
- hacía más confuso distinguir qué código está vivo

Si luego quieres rescatar algo de aquí, se puede mover de vuelta de forma selectiva.
