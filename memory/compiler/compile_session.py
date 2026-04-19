"""
Memory Compilation Loop — inspirado en claude-memory-compiler (Karpathy method).
Corre automáticamente via hook Stop al cerrar una sesión Claude Code.
Lee logs JSONL del día y compila un artículo de conocimiento en knowledge_base/.
"""
import json
import os
import sys
from datetime import date
from collections import Counter

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOGS_DIR = os.path.join(REPO_ROOT, "memory", "logs")
KB_DIR = os.path.join(REPO_ROOT, "memory", "knowledge_base", "sessions")
INDEX_FILE = os.path.join(REPO_ROOT, "memory", "knowledge_base", "index.md")


def load_today_log():
    today = date.today().isoformat()
    log_file = os.path.join(LOGS_DIR, f"tasks_{today}.jsonl")
    if not os.path.exists(log_file):
        return []
    entries = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


def compile_entries(entries):
    if not entries:
        return None

    successes, failures, task_types, models_used = [], [], [], []

    for e in entries:
        task = e.get("task", "")[:120]
        error = e.get("error", "")
        result = e.get("result", "")
        tt = e.get("task_type", "unknown")
        model = e.get("model", "unknown")
        ms = e.get("execution_time_ms", 0)

        task_types.append(tt)
        models_used.append(model)

        if error and not result:
            failures.append({"task": task, "error": error[:200], "type": tt})
        else:
            successes.append({"task": task, "time_ms": ms, "type": tt})

    type_counts = Counter(task_types)
    model_counts = Counter(models_used)
    avg_ms = int(sum(e.get("execution_time_ms", 0) for e in entries) / max(len(entries), 1))

    return {
        "date": date.today().isoformat(),
        "total": len(entries),
        "successes": successes,
        "failures": failures,
        "top_task_types": type_counts.most_common(5),
        "models_used": model_counts.most_common(5),
        "avg_ms": avg_ms,
    }


def write_session_article(data):
    os.makedirs(KB_DIR, exist_ok=True)
    out_file = os.path.join(KB_DIR, f"{data['date']}.md")

    lines = [
        f"# Sesión {data['date']}",
        f"\n**Total tareas:** {data['total']} | **Avg tiempo:** {data['avg_ms']}ms",
        "\n## Modelos usados",
    ]
    for model, count in data["models_used"]:
        lines.append(f"- `{model}`: {count}x")

    lines.append("\n## Tipos de tarea")
    for tt, count in data["top_task_types"]:
        lines.append(f"- `{tt}`: {count}x")

    if data["successes"]:
        lines.append(f"\n## Completadas ({len(data['successes'])})")
        for s in data["successes"][:10]:
            lines.append(f"- [{s['type']}] {s['task']} `{s['time_ms']}ms`")

    if data["failures"]:
        lines.append(f"\n## Fallos a revisar ({len(data['failures'])})")
        for f in data["failures"][:10]:
            lines.append(f"- [{f['type']}] **{f['task']}**")
            lines.append(f"  → `{f['error']}`")

    with open(out_file, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    return out_file


def update_index(data, session_file):
    rel_path = os.path.relpath(session_file, os.path.dirname(INDEX_FILE))
    entry = f"- [{data['date']}]({rel_path}) — {data['total']} tareas, {len(data['failures'])} fallos"

    os.makedirs(os.path.dirname(INDEX_FILE), exist_ok=True)
    if not os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            f.write("# Knowledge Base — Índice de Sesiones\n\n")

    # evitar duplicar la línea del día
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    if data["date"] not in content:
        with open(INDEX_FILE, "a", encoding="utf-8") as f:
            f.write(entry + "\n")


def main():
    entries = load_today_log()
    if not entries:
        print("compile_session: sin logs hoy, nada que compilar.")
        return

    data = compile_entries(entries)
    session_file = write_session_article(data)
    update_index(data, session_file)

    print(f"compile_session: {data['total']} tareas compiladas -> {session_file}")


if __name__ == "__main__":
    main()
