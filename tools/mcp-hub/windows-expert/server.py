import psutil
import json
import sys
import os

def list_processes(name_filter=None):
    """Lista procesos activos con filtro opcional"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_info']):
        try:
            info = proc.info
            if name_filter:
                if name_filter.lower() in info['name'].lower():
                    processes.append(info)
            else:
                processes.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    # Devolver top 15 por CPU si no hay filtro
    if not name_filter:
        processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:15]
    return processes

def kill_process(pid):
    """Mata un proceso por su PID"""
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        return {"status": "success", "message": f"Proceso {pid} finalizado."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_system_stats():
    """Obtiene estadisticas vitales del sistema"""
    return {
        "cpu_usage": psutil.cpu_percent(interval=1),
        "memory": psutil.virtual_memory()._asdict(),
        "disk": psutil.disk_usage('/')._asdict()
    }

# Mock de la interfaz MCP para validacion de fabrica
# En una implementacion real, esto usaria mcp-python-sdk
def run_mcp_loop():
    print("--- WINDOWS EXPERT MCP SERVER ONLINE ---")
    print("Esperando comandos JSON via STDIN...")
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line: break
            request = json.loads(line)
            method = request.get("method")
            params = request.get("params", {})
            
            if method == "list_processes":
                result = list_processes(params.get("filter"))
            elif method == "kill_process":
                result = kill_process(params.get("pid"))
            elif method == "get_stats":
                result = get_system_stats()
            else:
                result = {"error": "Metodo no soportado"}
            
            print(json.dumps({"result": result}))
            sys.stdout.flush()
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            sys.stdout.flush()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Test de diagnostico:")
        print(json.dumps(get_system_stats(), indent=2))
    else:
        run_mcp_loop()
