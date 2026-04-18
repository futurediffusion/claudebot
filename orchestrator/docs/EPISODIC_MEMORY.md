# Episodic Memory

## Purpose

Episodic memory stores concrete operational episodes across agents.

It is not the self-model.

- The self-model is abstract knowledge about strengths, weaknesses, and routing.
- Episodic memory is a history of specific attempts in specific contexts.
- The world model is the current state of windows, tabs, files, downloads, and objectives.


Para formato de correlación con self-model/world-model y eventos obligatorios de fallback mouse/visión, ver [../docs/TRACEABILITY_SPEC.md](D:/IA/CODE/claudebot/docs/TRACEABILITY_SPEC.md).

## Location

Episodes are stored under [D:/IA/CODE/claudebot/episodic_memory](D:/IA/CODE/claudebot/episodic_memory) so Claude, Gemini, Codex, and wrapper CLIs all use the same local memory.

## What An Episode Contains

Each episode can capture:

- attempted task
- task type
- selected model or automation route
- steps executed
- app context
- web context
- screen or UI context
- exact failure signature
- working fix or successful path

## Current Flow

```text
input
  -> classify or detect automation route
  -> retrieve similar episodes
  -> inject compact memory brief into execution context
  -> execute
  -> record a new episode with failure/fix context
```

## Retrieval

Episodes are matched by:

- task type
- automation route
- app overlap
- shared domains or URLs
- keyword overlap in task, failure, and resolution

This is intentionally simple and local.
It is meant to be reliable and debuggable, not magical.

## Entrypoints

- [orchestrator/core/episodic_memory.py](D:/IA/CODE/claudebot/orchestrator/core/episodic_memory.py)
- [orchestrator/core/orchestrator.py](D:/IA/CODE/claudebot/orchestrator/core/orchestrator.py)
- [gemini_bridge.py](D:/IA/CODE/claudebot/gemini_bridge.py)
- [run_browser.py](D:/IA/CODE/claudebot/run_browser.py)
- [run_windows.py](D:/IA/CODE/claudebot/run_windows.py)
- [run_worker.py](D:/IA/CODE/claudebot/run_worker.py)
- [episodic_memory_cli.py](D:/IA/CODE/claudebot/episodic_memory_cli.py)

## Examples

```bash
python D:/IA/CODE/claudebot/episodic_memory_cli.py summary
python D:/IA/CODE/claudebot/episodic_memory_cli.py find "Abre Chrome y ve a https://example.com y revisa el login" --task-type browser_automation
```
