# World Model

## Purpose

The world model stores the current operational state of the local desktop ecosystem.

It is not the self-model.
It is not episodic memory.

- The self-model is the system's theory about itself.
- Episodic memory is the record of past attempts and fixes.
- The world model is the current state of windows, tabs, files, downloads, and objectives.

## Location

The shared state lives in [D:/IA/CODE/claudebot/world_model](D:/IA/CODE/claudebot/world_model) so Claude, Gemini, Codex, and wrapper CLIs use the same live state.

## What It Tracks

- open apps
- active window
- tracked browser tabs
- files created or touched
- downloads in progress
- active task
- pending objectives

## Current Flow

```text
input
  -> refresh desktop observation
  -> retrieve task-relevant world-state brief
  -> inject brief into context
  -> execute
  -> update files, tabs, objectives, and task state
```

## Execution Hierarchy Alignment

El world model sirve como evidencia operacional para decidir si un salto de nivel fue necesario o prematuro según [EXECUTION_HIERARCHY.md](D:/IA/CODE/claudebot/orchestrator/docs/EXECUTION_HIERARCHY.md).

Cuando se escale a browser automation, herramientas OS o mouse/visión, el estado del mundo (apps activas, foco, tabs, archivos, objetivos) debe respaldar esa decisión.

## Data Sources

The current implementation combines:

- live PowerShell observation for active window, open apps, and partial downloads
- task parsing for URLs, file paths, and objective clauses
- worker-core playbooks for concrete subtasks and file outputs
- automation results from browser/windows/worker wrappers

## Entrypoints

- [orchestrator/core/world_model.py](D:/IA/CODE/claudebot/orchestrator/core/world_model.py)
- [orchestrator/core/orchestrator.py](D:/IA/CODE/claudebot/orchestrator/core/orchestrator.py)
- [gemini_bridge.py](D:/IA/CODE/claudebot/gemini_bridge.py)
- [run_browser.py](D:/IA/CODE/claudebot/run_browser.py)
- [run_windows.py](D:/IA/CODE/claudebot/run_windows.py)
- [run_worker.py](D:/IA/CODE/claudebot/run_worker.py)
- [world_model_cli.py](D:/IA/CODE/claudebot/world_model_cli.py)

## Examples

```bash
python D:/IA/CODE/claudebot/world_model_cli.py summary --refresh
python D:/IA/CODE/claudebot/world_model_cli.py focus "Abre Chrome y ve a https://example.com y guarda un resumen"
python D:/IA/CODE/claudebot/world_model_cli.py observe
```
