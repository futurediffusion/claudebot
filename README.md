# Claudebot Workspace

Workspace reorganized to keep the active system separate from older experiments.

## What To Use

- [orchestrator/README.md](D:/IA/CODE/claudebot/orchestrator/README.md): active multimodel orchestrator.
- [tools/](D:/IA/CODE/claudebot/tools): external tooling and support repos.
- [.claude/](D:/IA/CODE/claudebot/.claude): local editor and agent config.
- [run_browser.py](D:/IA/CODE/claudebot/run_browser.py): direct browser automation wrapper.
- [run_windows.py](D:/IA/CODE/claudebot/run_windows.py): direct Windows automation wrapper.
- [run_worker.py](D:/IA/CODE/claudebot/run_worker.py): full `worker-core` wrapper.
- [self_model/README.md](D:/IA/CODE/claudebot/self_model/README.md): shared self-model used by Claude, Gemini, Codex, and wrappers.
- [self_model_cli.py](D:/IA/CODE/claudebot/self_model_cli.py): inspect or simulate the shared self-model from the repo root.

## Archived

- [legacy/](D:/IA/CODE/claudebot/legacy): previous prototypes not used by the current flow.

## Minimal Structure

```text
claudebot/
|-- orchestrator/   active project
|-- tools/          external utilities and helper repos
|-- legacy/         archived prototypes
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

You can still call the wrappers directly if you want explicit control:

```bash
python run_browser.py "Abre https://example.com y extrae el titulo"
python run_windows.py "Abre Notepad y escribe hola mundo"
python run_worker.py "Abre https://example.com y guarda un resumen en tasks/output/resumen.txt"
```

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
