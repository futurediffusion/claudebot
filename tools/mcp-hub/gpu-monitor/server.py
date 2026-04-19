import pynvml
import json
import sys
import time

class GPUMonitor:
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
            "memory_utilization_percent": util.memory
        }

monitor = GPUMonitor()

def run_mcp_loop():
    print("--- GPU MONITOR MCP SERVER ONLINE ---")
    print(f"Monitoreando: {monitor.name if monitor.enabled else 'ERROR'}")
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line: break
            request = json.loads(line)
            method = request.get("method")
            
            if method == "get_gpu_stats":
                result = monitor.get_stats()
            else:
                result = {"error": "Metodo no soportado"}
            
            print(json.dumps({"result": result}))
            sys.stdout.flush()
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            sys.stdout.flush()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print(json.dumps(monitor.get_stats(), indent=2))
    else:
        run_mcp_loop()
