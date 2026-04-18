# Claudebot Workspace

Workspace reorganized to keep the active system separate from older experiments.

## What To Use

- **Nombre operativo**: **Sistema local CLI-first para automatización personal en PC**.
- **Prioridades**: operación local primero, CLI-first, routing pragmático.
- [orchestrator/README.md](D:/IA/CODE/claudebot/orchestrator/README.md): núcleo activo de operación local CLI-first con routing pragmático.
- [tools/](D:/IA/CODE/claudebot/tools): external tooling and support repos.
- [.claude/](D:/IA/CODE/claudebot/.claude): local editor and agent config.
- [run_browser.py](D:/IA/CODE/claudebot/run_browser.py): direct browser automation wrapper.
- [run_windows.py](D:/IA/CODE/claudebot/run_windows.py): direct Windows automation wrapper.
- [run_worker.py](D:/IA/CODE/claudebot/run_worker.py): full `worker-core` wrapper.
- [self_model/README.md](D:/IA/CODE/claudebot/self_model/README.md): shared self-model used by Claude, Gemini, Codex, and wrappers.
- [self_model_cli.py](D:/IA/CODE/claudebot/self_model_cli.py): inspect or simulate the shared self-model from the repo root.
- [episodic_memory/README.md](D:/IA/CODE/claudebot/episodic_memory/README.md): shared episodic memory for concrete attempts, failures, and fixes.
- [episodic_memory_cli.py](D:/IA/CODE/claudebot/episodic_memory_cli.py): inspect similar past episodes from the repo root.
- [world_model/README.md](D:/IA/CODE/claudebot/world_model/README.md): shared desktop world model for live environment state.
- [world_model_cli.py](D:/IA/CODE/claudebot/world_model_cli.py): inspect the current world-state slice from the repo root.
- [orchestrator/docs/CAPABILITIES_MATRIX.md](D:/IA/CODE/claudebot/orchestrator/docs/CAPABILITIES_MATRIX.md): matriz de capacidades reales vs experimentales del sistema.
- [orchestrator/docs/EXECUTION_HIERARCHY.md](D:/IA/CODE/claudebot/orchestrator/docs/EXECUTION_HIERARCHY.md): pirámide oficial de ejecución, escalado por niveles y fallback extremo mouse/visión.
- [docs/SKILLS_CATALOG.md](D:/IA/CODE/claudebot/docs/SKILLS_CATALOG.md): catálogo de skills operativas (dominio, IO, costo, fallbacks y owner).

## Qué NO es

- No es AGI.
- No es mouse-first.
- No es multimodelo por defecto.

## Archived

- [legacy/](D:/IA/CODE/claudebot/legacy): previous prototypes not used by the current flow.

## Minimal Structure

```text
claudebot/
|-- orchestrator/   active project
|-- tools/          external utilities and helper repos
|-- legacy/         archived prototypes
|-- self_model/     shared routing self-model
|-- episodic_memory/ shared execution episodes
|-- world_model/    shared desktop world state
`-- .claude/        local config
```

## Natural Language Automation

The main orchestrator now auto-routes plain language desktop and browser tasks.
You do not need to remember prefixes like `browser:` or `windows:`.

Examples:

```bash
cd D:/IA/CODE/claudebot/orchestrator
run_orchestrator.bat "Abre Chrome y ve a https://example.com"
run_orchestrator.bat "Abre Notepad y escribe hola mundo"
run_orchestrator.bat "Abre https://example.com y guarda un resumen en tasks/output/resumen.txt"
```

Behind the scenes:

- browser tasks go to `worker-core:browser`
- Windows desktop tasks go to `worker-core:windows`
- multi-step automation flows go to `worker-core:orchestrator`

The skills taxonomy used by these wrappers is documented in [docs/SKILLS_CATALOG.md](D:/IA/CODE/claudebot/docs/SKILLS_CATALOG.md).

You can still call the wrappers directly if you want explicit control:

```bash
python run_browser.py "Abre https://example.com y extrae el titulo"
python run_windows.py "Abre Notepad y escribe hola mundo"
python run_worker.py "Abre https://example.com y guarda un resumen en tasks/output/resumen.txt"
```

For direct coordinate-driven desktop control with calibration and verification:

```bash
python run_mouse.py 960 540 --action click --label "boton enviar" --verify cursor
python run_mouse.py 640 360 --action click --coordinate-space image --image-path screenshot.png --verify screen_change
python run_mouse.py --request-json "{\"x\":0.5,\"y\":0.8,\"coordinate_space\":\"normalized\",\"action\":\"move\"}"
```

`run_mouse.py` stores a learned calibration profile per app and resolution, retries around the predicted point, and records successes/failures into the shared self-model and episodic memory.

## Shared Self-Model

The repo now includes a live `self_model/` directory at the root.
This is the explicit model of how the system understands itself.

It is shared across:

- Claude-style orchestrator runs
- Gemini bridge runs
- Codex or other CLI agents using the root wrappers

Examples:

```bash
python self_model_cli.py summary
python self_model_cli.py plan "Fix this broken project and validate the output"
python gemini_bridge.py auto "Abre Chrome y ve a https://example.com"
python run_browser.py --agent codex_cli "Abre https://example.com y extrae el titulo"
```

The key point is that routing decisions and outcomes now update the same structured state instead of living only in ad-hoc logs.

## Episodic Memory

The repo now also includes a separate `episodic_memory/` layer.
This is not the self-model.

- `self_model/` answers "what am I generally good or bad at?"
- `episodic_memory/` answers "what happened last time in a similar task, app, page, or failure?"

Each episode can store:

- attempted task
- executed steps
- app, web, and screen context
- exact failure
- working fix or successful route

Examples:

```bash
python episodic_memory_cli.py summary
python episodic_memory_cli.py find "Abre Chrome y ve a https://example.com y revisa el login" --task-type browser_automation
```

Claude-style orchestrator runs, Gemini bridge runs, and the root wrappers all write into the same episodic layer.

## World Model

The repo now also includes a separate `world_model/` layer.

This is the live desktop/browser/filesystem state that agents can consult before acting.

It tracks things like:

- open apps
- active window
- files created or touched
- downloads in progress
- browser tabs associated with tasks
- pending objectives

Examples:

```bash
python world_model_cli.py summary --refresh
python world_model_cli.py focus "Abre Chrome y ve a https://example.com y guarda un resumen"
```

The main orchestrator, Gemini bridge, and root wrappers all update the same shared world state.
