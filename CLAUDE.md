# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Bootstrap / Identidad (IMPORTANTE)

Para activar el traje de **Claude Bot**, el agente DEBE ejecutar el siguiente comando al inicio de la sesión o cuando se le pida `/conocete`:

```bash
python claudebot_identity.py
```

Este comando sincroniza al agente con la **Constitución**, el **Self-Model** y el estado del hardware.

## Atajos de Personal HUB

Cuando el usuario pida abrir estas herramientas, usar `run_shell_command` con `is_background=true`:

- **Hub de Gastos**: `personal_HUB/run_expense_tracker.bat`
- **Journey**: `personal_HUB/run_journey.bat`

## Sistema
... (resto del archivo)
**Claudebot** es una estación de comando autónoma personal. Arquitectura: 8 MCPs especializados (registrados en `.claude/settings.json`) + servidor Vision-God (FastAPI en puerto 8000) + self-model compartido + memoria episódica.

Python runtime: `C:\Users\walva\AppData\Local\Programs\Python\Python310\python.exe`

## MCPs Disponibles (activos via Claude Code)

Todos usan `FastMCP`. Cada servidor vive en `tools/mcp-hub/<nombre>/server.py`.

| MCP | Herramientas |
|-----|-------------|
| `windows-expert` | `list_processes`, `kill_process`, `get_system_stats` |
| `file-oracle` | `search_files`, `grep_content`, `get_tree` |
| `gpu-monitor` | `get_gpu_stats` (NVIDIA NVML — RTX 4060) |
| `media-surgical` | `extract_audio`, `trim_media`, `gpu_upscale` (h264_nvenc) |
| `autoresearch` | `search_github`, `web_search`, `fetch_page` |
| `rag-architect` | `index_directory`, `semantic_search` (FAISS + MiniLM) |
| `red-team` | `python_security_audit`, `check_vulnerable_deps`, `scan_for_secrets` |
| `spotify-dj` | `get_spotify_status`, `search_track`, `toggle_play_pause` |

Para reiniciar un MCP individualmente: `python tools/mcp-hub/<nombre>/server.py`

## Herramientas Nativas de Claude Code

`WebSearch` — búsqueda web en tiempo real. Usar para información post-2024, docs actualizadas, modelos recientes.  
`WebFetch` — descarga cualquier URL pública. Ideal para READMEs de GitHub, model cards de HuggingFace, documentación.  
Ambas son "deferred tools": cargarlas con `ToolSearch` antes de usarlas si no están en el contexto activo.

## Vision-God (Percepción Visual)

Servidor: `tools/vision-god/server.py` — FastAPI + OmniParser V2.0 en GPU (CUDA 12.1).  
Arrancar: ejecutar `START_VISION_SERVER.bat` o `uvicorn server:app --host 0.0.0.0 --port 8000` dentro del venv `venv_vision`.  
Cliente: `tools/vision-god/client.py` — captura pantalla → POST a `http://127.0.0.1:8000/analyze` → retorna elementos con coordenadas.  
Protocolo completo: `docs/FREEPIK_VISION_PROTOCOL.md`

## Shared Skill Bridge

Bridge local compartido para descubrir y reutilizar skills entre `gemini_skills/`, `skills/`, `skills/.codex/skills/`, `legacy/local-agent/SKILLS/` y skills empacadas.  
Entrypoint: `python skills_bridge.py list gemini`  
Sugerencia contextual: `python skills_bridge.py suggest "Necesito automatizar browser y extraer datos"`  
Gemini tambiÃ©n expone esta capa vÃ­a `python gemini_bridge.py skills` y `python gemini_bridge.py skill-run <skill_id>`.

## Self-Model (Mandatos Obligatorios)

Leer `self_model/rule_engine.json` antes de actuar en sesiones complejas:
- **KNOWLEDGE_PRESERVATION (BLOCKER)**: Nunca sobrescribir archivos en `self_model/` sin leer y mergear el JSON existente.
- **KARPATHY_DISCIPLINE (CRITICAL)**: Pensar → Simplicidad → Cambio quirúrgico → Verificar resultado.
- **AGGRESSIVE_SELF_IMPROVEMENT (CRITICAL)**: Ante fallo o corrección del usuario, registrar en `self_model/failure_patterns.json`.

Routing de modelos/tareas: `self_model/routing_knowledge.json`  
Debilidades conocidas: `self_model/weaknesses.json`

## Memoria y Evolución

- Registrar habilidades nuevas: `memory/memos_kernel/memos_core.py` → `register_skill(name, description, procedure, examples)`
- Progreso visual: `memory/memory_bank/progress_map.md` (gráfico Mermaid)
- Logs de sesión: `memory/logs/tasks_YYYY-MM-DD.jsonl`

## Protocolos de Imagen

- **Stable Diffusion Forge** (Illustrious-XL-v2.0): `docs/ILLUSTRIOUS_FORGE_PROTOCOL.md` — API headless en puerto 7860, steps=28, Euler a/Karras, CFG=4
- **Generación visual web**: `docs/FREEPIK_VISION_PROTOCOL.md`

## AutoHotkey — Enviar Teclas desde Claude (OBLIGATORIO)

El usuario usa AHK v1 intensivamente. Script principal: `misscripts.ahk` en Startup (recarga con F12).

**NUNCA usar PowerShell SendKeys ni scripts AHK inline para hotkeys.** Usar siempre:

```bash
"C:/Program Files/AutoHotkey/v1.1.37.01/AutoHotkeyU64.exe" "C:/Windows/Temp/claude_sendkey.ahk" "TECLAS" DELAY_MS
```

Ejemplos:
```bash
# Recargar misscripts.ahk
"C:/Program Files/AutoHotkey/v1.1.37.01/AutoHotkeyU64.exe" "C:/Windows/Temp/claude_sendkey.ahk" "{F12}" 400

# Abrir nota con timestamp
"C:/Program Files/AutoHotkey/v1.1.37.01/AutoHotkeyU64.exe" "C:/Windows/Temp/claude_sendkey.ahk" "^!n" 400

# Abrir VS Code
"C:/Program Files/AutoHotkey/v1.1.37.01/AutoHotkeyU64.exe" "C:/Windows/Temp/claude_sendkey.ahk" "^#v" 400
```

Sintaxis AHK para teclas: `^`=Ctrl, `!`=Alt, `#`=Win, `+`=Shift, `{F12}`=F12, `{Enter}`=Enter.  
El archivo `claude_sendkey.ahk` acepta: `"KEYS" [delay_ms] [window_title]`

Shortcuts activos del usuario en `misscripts.ahk`:
- `F12` → Reload (usar después de editar el .ahk)
- `^#c/b/o` → Chrome / Brave / Opera GX
- `^#a` → Ableton 11 | `^#v` → VS Code | `^#d` → Discord | `^#z` → claudebot en VS Code
- `^!n` → Notepad con timestamp | `^!b` → Google Search de texto seleccionado
- `#!Left/Right` → Snap mitad izquierda/derecha

## Hardware

RTX 4060 — VRAM 8GB. Verificar estado: `mcp__gpu-monitor__get_gpu_stats()`.  
CUDA 12.1 activo en `venv_vision`. PyTorch 2.5.1+cu121.
