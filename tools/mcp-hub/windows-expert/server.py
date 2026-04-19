import psutil
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("windows-expert")


def _list_processes(name_filter=None):
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
    if not name_filter:
        processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:15]
    return processes


def _kill_process(pid):
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        return {"status": "success", "message": f"Proceso {pid} finalizado."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _get_system_stats():
    return {
        "cpu_usage": psutil.cpu_percent(interval=1),
        "memory": psutil.virtual_memory()._asdict(),
        "disk": psutil.disk_usage('/')._asdict()
    }


@mcp.tool()
def list_processes(name_filter: str = "") -> list:
    """Lista los procesos activos del sistema. Sin filtro devuelve top 15 por CPU."""
    return _list_processes(name_filter or None)


@mcp.tool()
def kill_process(pid: int) -> dict:
    """Termina un proceso por su PID."""
    return _kill_process(pid)


@mcp.tool()
def get_system_stats() -> dict:
    """Devuelve estadísticas vitales: CPU, RAM y disco."""
    return _get_system_stats()


if __name__ == "__main__":
    mcp.run()
