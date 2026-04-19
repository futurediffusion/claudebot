import pynvml
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("gpu-monitor")


class _GPUMonitor:
    def __init__(self):
        try:
            pynvml.nvmlInit()
            self.handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            self.name = pynvml.nvmlDeviceGetName(self.handle)
            self.enabled = True
        except Exception as e:
            self.enabled = False
            self.error = str(e)

    def get_stats(self):
        if not self.enabled:
            return {"error": f"NVML no inicializado: {self.error}"}
        info = pynvml.nvmlDeviceGetMemoryInfo(self.handle)
        temp = pynvml.nvmlDeviceGetTemperature(self.handle, pynvml.NVML_TEMPERATURE_GPU)
        util = pynvml.nvmlDeviceGetUtilizationRates(self.handle)
        return {
            "gpu_name": self.name,
            "vram_total_mb": info.total / 1024**2,
            "vram_used_mb": info.used / 1024**2,
            "vram_free_mb": info.free / 1024**2,
            "vram_percent": (info.used / info.total) * 100,
            "temperature_c": temp,
            "gpu_utilization_percent": util.gpu,
            "memory_utilization_percent": util.memory,
        }


_monitor = _GPUMonitor()


@mcp.tool()
def get_gpu_stats() -> dict:
    """Devuelve temperatura, VRAM usada/libre y utilización de la RTX 4060."""
    return _monitor.get_stats()


if __name__ == "__main__":
    mcp.run()
