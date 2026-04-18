# Self-Model Engine

## Purpose

The self-model is the shared structured representation of how this local ecosystem understands itself.

It is not the same thing as logs.
Logs are facts about what happened.
The self-model is the current theory of:

- what each model is good at
- where each model should be avoided
- which tools fit which tasks
- which failure patterns keep repeating

For concrete execution history, app/page context, and exact fixes, use [EPISODIC_MEMORY.md](D:/IA/CODE/claudebot/orchestrator/docs/EPISODIC_MEMORY.md).
For live desktop/browser/filesystem state, use [WORLD_MODEL.md](D:/IA/CODE/claudebot/orchestrator/docs/WORLD_MODEL.md).

## Location

The self-model lives at [D:/IA/CODE/claudebot/self_model](D:/IA/CODE/claudebot/self_model) so multiple agents can use the same source of truth:

- Claude-style orchestrator runs
- Gemini bridge runs
- Codex or other CLIs calling the root wrappers

## Files

- [capabilities.json](D:/IA/CODE/claudebot/self_model/capabilities.json): explicit strengths and preferred task classes.
- [weaknesses.json](D:/IA/CODE/claudebot/self_model/weaknesses.json): avoid rules and update thresholds.
- [routing_knowledge.json](D:/IA/CODE/claudebot/self_model/routing_knowledge.json): task preferences, meta-strategies, observed stats, recent decisions.
- [tool_map.json](D:/IA/CODE/claudebot/self_model/tool_map.json): tool suitability and per-agent tool availability.
- [failure_patterns.json](D:/IA/CODE/claudebot/self_model/failure_patterns.json): compact learned failure signatures.


La política oficial de orden de decisión y criterios de escalado está en [ROUTING_POLICY.md](D:/IA/CODE/claudebot/orchestrator/docs/ROUTING_POLICY.md).

## How It Works

1. Classify the task.
2. Simulate model or tool choices against the self-model.
3. Select a route.
4. Execute.
5. Record the outcome back into the self-model.

This gives you a real feedback loop instead of isolated per-task guesses.

## What Changes Automatically

The engine updates cautiously:

- repeated success can add a model to preferred choices for that task type
- repeated failure can add an avoid rule
- tool success/failure counters are tracked per agent
- compact failure signatures accumulate over time

It does not invent huge architectural changes by itself.
It only adjusts structured routing knowledge based on repeated evidence.

## Entrypoints

- [orchestrator/core/router.py](D:/IA/CODE/claudebot/orchestrator/core/router.py): simulates routing choices before execution.
- [orchestrator/core/orchestrator.py](D:/IA/CODE/claudebot/orchestrator/core/orchestrator.py): injects self-model context and records outcomes.
- [gemini_bridge.py](D:/IA/CODE/claudebot/gemini_bridge.py): uses the same self-model for Gemini automation decisions.
- [run_browser.py](D:/IA/CODE/claudebot/run_browser.py), [run_windows.py](D:/IA/CODE/claudebot/run_windows.py), [run_worker.py](D:/IA/CODE/claudebot/run_worker.py): update the shared state even when used directly.
- [self_model_cli.py](D:/IA/CODE/claudebot/self_model_cli.py): inspect or simulate the self-model from the root.

## Examples

```bash
python D:/IA/CODE/claudebot/self_model_cli.py summary
python D:/IA/CODE/claudebot/self_model_cli.py plan "Fix this broken project and validate the output"
python D:/IA/CODE/claudebot/gemini_bridge.py auto "Abre Chrome y ve a https://example.com"
python D:/IA/CODE/claudebot/run_worker.py --agent codex_cli "Abre https://example.com y guarda un resumen en tasks/output/resumen.txt"
```
