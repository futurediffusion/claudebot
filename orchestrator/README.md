# Multi-Model Orchestrator

Multi-model orchestration system for Claude Code using Ollama plus Groq as a fast processing layer.

## Quick Use

```bash
run_orchestrator.bat "Create a Python function to add two numbers"
run_orchestrator.bat "Design an API, create files, and validate the JSON schema"
run_orchestrator.bat "Abre Chrome y ve a https://example.com"
run_orchestrator.bat "Abre Notepad y escribe hola mundo"
run_orchestrator.bat "Abre https://example.com y guarda un resumen en tasks/output/resumen.txt"
python ../run_browser.py "Open https://example.com and extract the title"
python ../run_windows.py "Open Notepad and type hello world"
python ../run_worker.py "Open a website and save a summary to tasks/output/summary.txt"
```

## Python Use

```python
from core.task_decomposer import MultiModelOrchestrator

orchestrator = MultiModelOrchestrator()
result = orchestrator.execute_complex_task("Your task here")
```

## Self-Model Engine

The orchestrator now consults a shared self-model before routing.
That state lives in [self_model/](D:/IA/CODE/claudebot/self_model) at the repo root so Claude, Gemini, Codex, and wrapper CLIs can all read and update the same knowledge.

Key pieces:

- [self_model/capabilities.json](D:/IA/CODE/claudebot/self_model/capabilities.json)
- [self_model/weaknesses.json](D:/IA/CODE/claudebot/self_model/weaknesses.json)
- [self_model/routing_knowledge.json](D:/IA/CODE/claudebot/self_model/routing_knowledge.json)
- [self_model/tool_map.json](D:/IA/CODE/claudebot/self_model/tool_map.json)
- [self_model/failure_patterns.json](D:/IA/CODE/claudebot/self_model/failure_patterns.json)
- [docs/SELF_MODEL.md](D:/IA/CODE/claudebot/orchestrator/docs/SELF_MODEL.md)

You can inspect it from the repo root:

```bash
python ../self_model_cli.py summary
python ../self_model_cli.py plan "Fix this broken project and validate the output"
```

## Models

| Model | Role | Typical Use |
|-------|------|-------------|
| `minimax-m2.7:cloud` | Planner | Architecture, planning, strategy |
| `qwen3-coder:480b-cloud` | Heavy Code | Complex refactors, multi-file fixes |
| `qwen3-coder-next:cloud` | Fast Code | Quick implementation and edits |
| `qwen3-vl:latest` | Vision | Screenshots and UI analysis |
| `gemma4:latest` | Lightweight | Simple verification |
| `groq_qwen_32b` | Fast Brain | Parsing, validation, log analysis |
| `groq_gpt_oss_20b` | Ultra Cheap Worker | Formatting, classification, JSON |

## Groq Setup

Use `GROQ_API_KEY`.

- Do not store API keys in code.
- Do not print or log API keys.
- If you want local file-based setup, create `.env` yourself from `.env.example`.

Example:

```env
GROQ_API_KEY=YOUR_KEY_HERE
```

## Routing Summary

- Planning and architecture -> MiniMax
- Complex coding -> Qwen 480B
- Quick coding -> Qwen Next
- Vision -> Qwen VL
- Simple checks -> Gemma
- Parsing and validation -> Groq Qwen
- Formatting, classification, JSON -> Groq GPT-OSS

## Browser/Windows Bridge

`browser-use` and `windows-use` are connected through `tools/worker-core` and exposed in two ways:

1. Direct CLI wrappers at the repo root:
   `python D:/IA/CODE/claudebot/run_browser.py "..."`
   `python D:/IA/CODE/claudebot/run_windows.py "..."`
   `python D:/IA/CODE/claudebot/run_worker.py "..."`
2. Tool bridge inside the orchestrator:
   if a model emits `browser: ...`, `windows: ...`, or `worker: ...`, the orchestrator now delegates the task to worker-core.

This makes the browser/desktop automation reachable from Claude-style agents and any other CLI agent that can execute Python commands.

## Natural Language Auto-Routing

The orchestrator now detects simple user intent before model routing.
That means inputs like these no longer need tool prefixes:

```text
Abre Chrome y ve a https://example.com
Abre Notepad y escribe hola mundo
Abre https://example.com y guarda un resumen en tasks/output/resumen.txt
```

Routing behavior:

- browser/site navigation -> `worker-core:browser`
- Windows desktop app control -> `worker-core:windows`
- multi-step automation with save/export/summary steps -> `worker-core:orchestrator`

Coding and architecture requests still go through the normal model router. Groq is not used for this automation path.

## Gemini And Other Agents

The shared self-model is not exclusive to the orchestrator.

- `gemini_bridge.py auto "<task>"` now chooses browser/windows/worker using the same self-model.
- `run_browser.py`, `run_windows.py`, and `run_worker.py` now record outcomes back into the same shared state.
- External agents can pass `--agent claude_code`, `--agent gemini_cli`, or `--agent codex_cli` to the wrappers when they want attribution.

## Example Groq Routing

```text
"Validate this JSON and extract the error messages"
-> groq_qwen_32b
```

## Example Pipeline

```text
qwen3-coder -> groq validation
```

Example:

1. `qwen3-coder-next:cloud` creates the response object.
2. `groq_qwen_32b` validates the JSON/schema output.
