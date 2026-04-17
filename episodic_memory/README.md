# Episodic Memory

This directory stores shared operational episodes for the local agent ecosystem.

It is separate from the self-model.

- `self_model/` is the system's theory of itself.
- `episodic_memory/` is the record of concrete attempts, contexts, failures, and fixes.

Each episode is meant to answer:

- what task was attempted
- what steps were executed
- what app, web, or screen context existed
- what failed exactly
- what workaround or fix actually worked

The runtime episode stream is written to `episodes.jsonl`.
That file is intentionally ignored by Git so Claude, Gemini, Codex, and wrapper scripts can learn locally without polluting commits.
