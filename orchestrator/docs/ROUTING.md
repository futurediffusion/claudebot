# Routing Logic

## Decision Flow

```text
Task input
  -> detect_automation_route()
    -> browser/windows/worker-core when the task is desktop automation
  -> classify_task()
  -> self_model simulate_routing()
    -> compare registry default vs learned strengths/weaknesses/failure patterns
  -> get_model_by_task()
  -> validate_task_model_match()
  -> execute with adapter
  -> optional Groq follow-up for validation/formatting
  -> record outcome back into self_model/
```

## Core Rules

- Planning and architecture go to `minimax-m2.7:cloud`.
- Heavy refactors and multi-file fixes go to `qwen3-coder:480b-cloud`.
- Quick coding tasks go to `qwen3-coder-next:cloud`.
- Vision tasks go to `qwen3-vl:latest`.
- Simple generic checks stay on `gemma4:latest`.
- Groq is only used for parsing, validation, formatting, classification, and JSON work.
- Architecture and coding tasks must not be routed to Groq.
- Browser and Windows automation are exposed as tool bridges through `worker-core`, not as primary models.
- Natural-language automation is intercepted before LLM model routing.
- A shared self-model can override the registry default when repeated evidence says it should.

## Self-Model Layer

The self-model lives at [self_model/](D:/IA/CODE/claudebot/self_model) in the repo root.

It stores:

- capabilities
- weaknesses
- routing knowledge
- tool map
- failure patterns

The router uses that layer to simulate options before committing to a model.
This gives the system a compact internal critic:

- "what is the default choice?"
- "what has worked before?"
- "what should be avoided for this task shape?"
- "is there a cheaper or safer option?"

## Natural Language Automation Rules

These inputs do not need `browser:`, `windows:`, or `worker:` prefixes anymore:

```text
Abre Chrome y ve a https://example.com
Abre Notepad y escribe hola mundo
Abre https://example.com y guarda un resumen en tasks/output/resumen.txt
```

Routing:

- browser navigation or page interaction -> `worker-core:browser`
- desktop app control -> `worker-core:windows`
- browser/desktop tasks with save/export/summary orchestration -> `worker-core:orchestrator`

The detector explicitly avoids routing coding, architecture, and codebase tasks into these automation bridges.

## Groq Routing Rules

| Task Type | Model |
|-----------|-------|
| `log_analysis` | `groq_qwen_32b` |
| `parsing` | `groq_qwen_32b` |
| `validation` | `groq_qwen_32b` |
| `formatting` | `groq_gpt_oss_20b` |
| `classification` | `groq_gpt_oss_20b` |
| `json` | `groq_gpt_oss_20b` |

## Example: Groq Routing Decision

Input:

```text
Format this response as JSON and classify the error type
```

Decision:

1. The task matches formatting/JSON/classification keywords.
2. It is a transform task, not a planning or coding task.
3. The router selects `groq_gpt_oss_20b`.

## Example: Heavy Model -> Groq Validation

Input:

```text
Create the API response object and validate the JSON schema
```

Expected pipeline:

1. `qwen3-coder-next:cloud` or `qwen3-coder:480b-cloud` handles implementation.
2. `groq_qwen_32b` runs the lightweight validation step.

This keeps Groq in the fast-processing layer instead of using it for design or coding.

## Tool Bridge Commands

If a model response contains one of these lines, the orchestrator delegates to `worker-core`:

```text
browser: Open https://example.com and extract the page title
windows: Open Notepad and type hello world
worker: Open a site and save a summary into tasks/output/summary.txt
```

That bridge makes `browser-use` and `windows-use` callable from the main orchestrator without embedding those large projects into the core package.
