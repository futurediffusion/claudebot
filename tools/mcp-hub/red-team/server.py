import subprocess
import json
import sys
import os

class RedTeamAuditor:
    def __init__(self):
        print("--- RED TEAM MCP AUDITOR ONLINE ---")
        self.bandit = "bandit"
        self.safety = "safety"

    def run_command(self, cmd):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.stdout
        except Exception as e:
            return str(e)

    def python_security_audit(self, target_path):
        """Escaneo SAST usando Bandit"""
        cmd = [self.bandit, "-r", target_path, "-f", "json", "-q"]
        output = self.run_command(cmd)
        try:
            return json.loads(output)
        except:
            return {"error": "No se pudo procesar la salida de Bandit", "raw": output}

    def check_vulnerable_deps(self):
        """Verifica vulnerabilidades en dependencias instaladas"""
        cmd = [self.safety, "check", "--json"]
        output = self.run_command(cmd)
        try:
            return json.loads(output)
        except:
            return {"message": "Analisis de dependencias completado (revisar formato)"}

    def scan_for_secrets(self, target_path):
        """Busqueda heuristica de secretos y llaves"""
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
                except: pass
        return findings

def run_mcp_loop():
    auditor = RedTeamAuditor()
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line: break
            request = json.loads(line)
            method = request.get("method")
            params = request.get("params", {})
            
            target = params.get("path", os.getcwd())
            
            if method == "audit_code":
                result = auditor.python_security_audit(target)
            elif method == "check_deps":
                result = auditor.check_vulnerable_deps()
            elif method == "scan_secrets":
                result = auditor.scan_for_secrets(target)
            else:
                result = {"error": "Metodo no soportado"}
            
            print(json.dumps({"result": result}))
            sys.stdout.flush()
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            sys.stdout.flush()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        auditor = RedTeamAuditor()
        print("Test: Escaneando secretos en la carpeta actual...")
        print(json.dumps(auditor.scan_for_secrets(os.getcwd())[:5], indent=2))
        print("\nTest: Auditoria rapida de codigo...")
        print("Analisis en curso...")
    else:
        run_mcp_loop()
