# Model Reference

## Ollama Models

| Model | Role | Use |
|-------|------|-----|
| `minimax-m2.7:cloud` | Planner / Strategist | Planning, architecture, ambiguity |
| `qwen3-coder:480b-cloud` | Heavy Code Specialist | Multi-file refactors, complex fixes |
| `qwen3-coder-next:cloud` | Fast Coding / Agentic | Quick edits, scaffolding, implementation |
| `qwen3-vl:latest` | Vision / UI | Screenshots, UI analysis |
| `gemma4:latest` | Lightweight Helper | Simple checks and summaries |

## Groq Models

Groq is the fast processing layer.

It is:
- not for thinking
- not for planning
- only for transformation, parsing, validation

| Alias | Provider Model | Role | Use For | Do Not Use For |
|-------|----------------|------|---------|----------------|
| `groq_qwen_32b` | `qwen/qwen3-32b` | `fast_brain` | parsing, validation, log analysis, simple intermediate decisions | architecture, complex reasoning, deep debugging |
| `groq_gpt_oss_20b` | `openai/gpt-oss-20b` | `ultra_cheap_worker` | formatting, classification, JSON generation, simple transforms | reasoning, planning |

## Concept Mapping

- Groq = CPU
- MiniMax = brain
- Qwen 480B = senior engineer
- Gemma = cheap assistant

## Example Routing Decision

Task:

```text
Validate this JSON response and extract the error fields
```

Routing result:

- task type: `validation`
- model: `groq_qwen_32b`
- reason: fast parsing and validation without spending a heavy model

## Example Pipeline

```text
qwen3-coder:480b-cloud -> groq_qwen_32b
```

Example flow:

1. `qwen3-coder:480b-cloud` implements API files.
2. `groq_qwen_32b` validates the generated JSON/schema output.

## Setup

Use the environment variable `GROQ_API_KEY`.

Do not put API keys in source code.
Do not print or log API keys.

Local setup example:

```env
GROQ_API_KEY=YOUR_KEY_HERE
```

The orchestrator reads the key from the environment, and also supports a local `.env` file if you create one manually.
