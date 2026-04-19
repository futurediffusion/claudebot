---
name: system-medic
description: Habilidad de infraestructura para el diagnóstico y reparación automática del entorno Claudebot (Ollama, Playwright, Venv, Python deps). Usa la episodic_memory para aprender de fallos pasado

. Automáticamente repara Ollama si está caído, instala chromium en Playwright si falta, y valida configuración .env.
---

# System Medic Skill

Diagnóstico y reparación automática del entorno Claudebot. Detecta problemas comunes y los resuelve autonomously, aprende de fallos pasados via episodic memory.

## When to Use This Skill

Trigger when user:
- Menciona "system medic", "diagnóstico", "reparar entorno", "check salud"
- Dice "ollama caído", "playwright no funciona", "faltan dependencias"
- Reporta errores de infraestructura: ConnectionError, ModuleNotFoundError, playwright not found
- Pide "diagnosticar", "repair", "fix environment", "health check"

## Core Workflow

### 1. Ollama Health Check & Restart

```bash
# Check if Ollama is running
python scripts/medic.py check ollama

# If not running, restart it
python scripts/medic.py fix ollama
```

**Detection Logic:**
- Try `curl http://localhost:11434/api/tags` 
- If fails → Ollama not responding
- Attempt restart via `ollama serve` or service restart

**Restart Method:**
```powershell
# Windows: Start Ollama service
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden

# Or via sc query (service mode)
sc query Ollama
```

### 2. Playwright Chromium Installation

```bash
# Check if chromium is installed
python scripts/medic.py check playwright

# If missing, install chromium
python scripts/medic.py fix playwright
```

**Detection Logic:**
```bash
# Try to launch browser
python -c "from playwright.sync_api import sync_playwright; p.sync_playwright().start().chromium.launch()"

# If fails → chromium not installed
```

**Fix:**
```bash
# Install chromium via patchright (recommended)
python -m patchright install chromium

# Or via playwright
python -m playwright install chromium
```

### 3. .env Configuration Validation

```bash
# Check if .env files are present
python scripts/medic.py check env

# If missing, report which env files are needed
python scripts/medic.py fix env
```

**Files to Check:**
- `.env` (root)
- `.env.local` (root)
- `credentials.json` (if required)

**Validation:**
```python
import os
from pathlib import Path

required_files = [
    ".env",
    "credentials.json"
]

missing = []
for f in required_files:
    if not Path(f).exists():
        missing.append(f)
```

## Script Reference

### Medic Script (`medic.py`)

```bash
# Run all health checks
python scripts/medic.py check all

# Check specific component
python scripts/medic.py check ollama
python scripts/medic.py check playwright
python scripts/medic.py check env

# Fix specific component
python scripts/medic.py fix ollama
python scripts/medic.py fix playwright
python scripts/medic.py fix env

# Auto-fix everything
python scripts/medic.py repair

# Show status report
python scripts/medic.py status
```

### Output Format

```json
{
  "ollama": {
    "status": "running|stopped|error",
    "version": "0.1.2",
    "last_check": "2026-04-19T12:00:00Z"
  },
  "playwright": {
    "chromium": "installed|missing",
    "last_install": "2026-04-18T10:00:00Z"
  },
  "env": {
    ".env": "present|missing",
    "credentials.json": "present|missing"
  }
}
```

## Decision Flow

```
User invokes System Medic
    ↓
Run medic.py check all
    ↓
┌─────────────────────────────────────────┐
│ Detect issues:                          │
│ - Ollama stopped → fix ollama            │
│ - Chromium missing → fix playwright     │
│ - .env missing → report missing files  │
└─────────────────────────────────────────┘
    ↓
Log findings to episodic_memory
    ↓
Report to user with status
    ↓
If user approves → auto-repair
```

## Learning from Failures

System Medic writes to episodic memory:
- `memory/logs/tasks_YYYY-MM-DD.jsonl`

**Logged Events:**
```json
{
  "timestamp": "2026-04-19T12:00:00Z",
  "event": "ollama_restart",
  "success": true,
  "attempt": 2,
  "method": "service_restart"
}
```

**Memory Pattern Recognition:**
- Track failures across sessions
- Use preferred fix method per component
- Wait longer before retry if multiple failures

## Troubleshooting

| Problem | Solution |
|--------|----------|
| Ollama not responding after restart | Kill old process, restart fresh |
| Chromium install fails | Try `python -m playwright install --force` |
| .env missing | Create from `.env.example` template |
| Permission denied | Run as admin or check file permissions |
| Version mismatch | Check Python/ollama versions |

## Best Practices

1. **Always check first** - `python scripts/medic.py check all`
2. **Log to memory** - Track all repair attempts
3. **One fix at a time** - Verify after each fix
4. **Report status** - Show before/after state
5. **Ask before repair** - Confirm before applying fixes

## Limitations

- Windows-only support (PowerShell commands)
- Assumes Ollama at `localhost:11434`
- No network diagnosis (internet connectivity)
- No database health checks
- No Git repository validation

## Resources

- `scripts/medic.py` - Main diagnostic script
- `memory/logs/` - Event logs for learning