# Self Model

Shared self-model state for the whole local ecosystem.

These files are not just logs. They are the explicit working model of how the
system understands itself.

Files:

- `capabilities.json`: what each model, agent, and tool is good at.
- `weaknesses.json`: where each model or agent should be avoided.
- `routing_knowledge.json`: preferred strategies, observed stats, and recent routing decisions.
- `tool_map.json`: which execution tools are best for which kind of task.
- `failure_patterns.json`: compact learned failure signatures.

Design rules:

- The directory lives at the repo root so Claude, Gemini, Codex, and wrapper scripts can share it.
- Updates are controlled and incremental. The engine only auto-adds preferences after repeated success, and avoid-rules after repeated failure.
- The goal is coherence, not magic. The self-model informs routing, self-critique, and post-task learning.

The execution pyramid and escalation jump conditions are documented in [orchestrator/docs/EXECUTION_HIERARCHY.md](D:/IA/CODE/claudebot/orchestrator/docs/EXECUTION_HIERARCHY.md).
