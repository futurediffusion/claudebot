---
name: learnings
description: Conocimientos adquiridos por el agent
type: learnings
---

# Learnings - Lo Que He Aprendido

## Propósito
Registrar insights, patrones descubiertos, y conocimientos gained
through experience que me hacen más efectivo.

---

## [YYYY-MM-DD] <Insight>

**Contexto:** <situación en la que lo aprendí>
**Aprendizaje:** <lo que descubrí>
**Cómo aplicarlo:** <cómo usar este conocimiento>

---

## Template para nuevos learnings

```markdown
## [YYYY-MM-DD] <título del insight>

**Contexto:** <qué estaba pasando>
**Aprendizaje:** <qué aprendí>
**Cómo aplicarlo:** <para qué sirve esto>
```

---

## Learnings Importantes

_(Agregar aquí conforme se descubran)_

### Ejemplo:
## [2026-04-15] Estructura de skills

**Contexto:** Necesitaba organizar skills de forma autocontenida
**Aprendizaje:** Cada skill vive en su propia carpeta con: skill.md (docs), script.py (código), y opcionalmente archivos de soporte
**Cómo aplicarlo:** Cuando cree una nueva skill, seguir la estructura: SKILLS/<nombre>/{skill.md, script.py}

### [2026-04-15] UTF-8 en Windows

**Contexto:** Ejecuté summarize_folder.py en Windows y falló con UnicodeEncodeError
**Aprendizaje:** En Windows, Python usa cp1252 por defecto para stdout. Caracteres como ├──, └──, │ fallan. Solución: `sys.stdout.reconfigure(encoding='utf-8')` al inicio del script.
**Cómo aplicarlo:** Todo script que imprima caracteres no-ASCII debe incluir `sys.stdout.reconfigure(encoding='utf-8')` al inicio de main() para funcionar en Windows.

### [2026-04-15] Vision con Ollama - gemma4 NO tiene soporte visual

**Contexto:** Intenté usar gemma4:latest de Ollama para analizar imágenes. Falló con timeout.
**Aprendizaje:** gemma4 en Ollama NO soporta imágenes aunque Google lo diga. Para visión hay que usar llava:7b-v1.6-vicuna-q2_K que SÍ es multimodal.
**Cómo aplicarlo:** En SKILLS/vision/analyze_screen.py usar `llava:7b-v1.6-vicuna-q2_K` como model, no gemma4.

### [2026-04-15] Visión práctica funcionando

**Contexto:** Ejecuté analyze_screen.py y pude ver lo que había en mi pantalla
**Aprendizaje:** Puedo tomar screenshots y enviarlo a Ollama para análisis. El modelo vio: Chrome con tabs, Claude Code con la conversación, file manager, etc.
**Cómo aplicarlo:** Usar `python SKILLS/vision/analyze_screen.py` cuando necesite "ver" qué está pasando en el escritorio del usuario.