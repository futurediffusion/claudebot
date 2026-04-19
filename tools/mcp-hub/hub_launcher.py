import subprocess
import os
import sys

class MCPHub:
    def __init__(self):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.servers = {
            "windows": "windows-expert/server.py",
            "gpu": "gpu-monitor/server.py",
            "oracle": "file-oracle/server.py",
            "media": "media-surgical/server.py"
        }

    def start_all(self):
        print("--- HUB DE PODER MCP (Clean Edition) ---")
        for name, path in self.servers.items():
            full_path = os.path.join(self.base_path, path)
            if os.path.exists(full_path):
                print(f"🚀 Motor {name} listo.")
            else:
                print(f"ℹ️ Motor {name} no configurado.")

if __name__ == "__main__":
    hub = MCPHub()
    hub.start_all()
