# World Model

This directory stores the shared desktop world model for the local agent ecosystem.

It is different from the other two layers:

- `self_model/` answers: what is this system generally good or bad at?
- `episodic_memory/` answers: what happened in similar past runs?
- `world_model/` answers: what is the desktop world state right now?

The world model is meant to track things like:

- which apps are open
- which window is active
- which files were created or touched
- which downloads are in progress
- which browser tabs correspond to which tasks
- which objectives are still pending

Runtime state is written to `state.json`.
That file is intentionally ignored by Git so the model can stay live without polluting commits.
