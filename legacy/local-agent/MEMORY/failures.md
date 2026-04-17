---
name: failures
description: Registro de intentos fallidos
type: failures
---

# Failures - Lo Que No Funcionó

## Propósito
Documentar fracasos para:
1. No repetirlos
2. Entender qué falló
3. Tener alternativas claras

---

## Template

```markdown
## [TIMESTAMP] <título>

**Qué se intentó:** <comando/acción>
**Qué salió mal:** <error específico>
**Qué hacer en su lugar:** <alternativa>
**Status:** OPEN|RESOLVED
```

---

## Fracasos Registrados

## [2026-04-15] summarize_folder.py - UnicodeEncodeError en Windows

**Qué se intentó:** `python SKILLS/filesystem/summarize_folder.py "D:/IA/CODE/claudebot/local-agent" 2`
**Qué salió mal:** `UnicodeEncodeError: 'charmap' codec can't encode characters` — los caracteres tree (├──, └──, │) no son compatibles con cp1252 en Windows
**Qué hacer en su lugar:** Agregar `PYTHONIOENCODING=utf-8` al comando, o fixear el script para usar `sys.stdout.reconfigure(encoding='utf-8')`
**Status:** RESOLVED

---

## Regla importante
**Cada fracaso debe incluir qué hacer en su lugar.**
Si no tienes una alternativa, el fracaso no está completamente documentado.