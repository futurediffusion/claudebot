"""
Quality Gate — hook PreToolUse para Bash.
Claude Code envía JSON por stdin: {"tool_name": "Bash", "tool_input": {"command": "..."}}
Si el comando es un git commit con mensaje demasiado corto, lo bloquea (exit 2).
Exit 0 = permitir. Exit 2 = bloquear (Claude Code muestra el stderr al usuario).
"""
import json
import re
import sys


def check_commit_message(command: str):
    # detectar git commit -m "msg" o git commit -m 'msg'
    match = re.search(r'git\s+commit\b.*?-m\s+["\'](.+?)["\']', command, re.DOTALL)
    if not match:
        # formato heredoc o sin -m → dejar pasar
        return None
    msg = match.group(1).strip()
    if len(msg) < 15:
        return f"Mensaje de commit demasiado corto ({len(msg)} chars). Describe el WHY, no el WHAT."
    return None


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)
        data = json.loads(raw)
    except Exception:
        sys.exit(0)

    tool = data.get("tool_name", "")
    if tool != "Bash":
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "")

    if "git commit" in command:
        error = check_commit_message(command)
        if error:
            print(f"[quality_gate] BLOQUEADO: {error}", file=sys.stderr)
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
