import subprocess
import json
import os
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("red-team")

_BANDIT = "bandit"
_SAFETY = "safety"


def _run_cmd(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return str(e)


@mcp.tool()
def python_security_audit(target_path: str) -> dict:
    """Escaneo SAST con Bandit sobre un directorio Python. Devuelve hallazgos JSON."""
    cmd = [_BANDIT, "-r", target_path, "-f", "json", "-q"]
    output = _run_cmd(cmd)
    try:
        return json.loads(output)
    except Exception:
        return {"error": "No se pudo procesar la salida de Bandit", "raw": output[:500]}


@mcp.tool()
def check_vulnerable_deps() -> dict:
    """Verifica vulnerabilidades conocidas en las dependencias instaladas (safety)."""
    cmd = [_SAFETY, "check", "--json"]
    output = _run_cmd(cmd)
    try:
        return json.loads(output)
    except Exception:
        return {"message": "Análisis de dependencias completado (revisar formato)", "raw": output[:500]}


@mcp.tool()
def scan_for_secrets(target_path: str) -> list:
    """Búsqueda heurística de secretos y llaves API hardcodeados en el código fuente."""
    patterns = ["API_KEY", "SECRET", "PASSWORD", "TOKEN", "PRIVATE_KEY"]
    findings = []
    for root, _, filenames in os.walk(target_path):
        if any(x in root for x in ['.git', 'venv', 'node_modules', '__pycache__']):
            continue
        for filename in filenames:
            file_path = os.path.join(root, filename)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    for p in patterns:
                        if p in content.upper():
                            findings.append({"file": file_path, "pattern": p})
            except Exception:
                pass
    return findings


if __name__ == "__main__":
    mcp.run()
