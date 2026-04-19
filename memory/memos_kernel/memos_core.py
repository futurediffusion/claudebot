import json
import os
import time
import hashlib

class MemOSKernel:
    def __init__(self):
        self.vault_path = os.path.join("memory", "memos_kernel", "skills_vault")
        self.log_path = os.path.join("memory", "memos_kernel", "evolution_logs")

    def register_skill(self, name, description, procedure, examples=None):
        """Registra o actualiza una habilidad en la boveda"""
        skill_file = os.path.join(self.vault_path, f"{name.lower()}.json")
        
        current_data = {}
        if os.path.exists(skill_file):
            with open(skill_file, 'r') as f:
                current_data = json.load(f)

        version = current_data.get("version", 0) + 1
        
        skill_data = {
            "name": name,
            "version": version,
            "last_updated": time.ctime(),
            "description": description,
            "procedure": procedure,
            "examples": examples or [],
            "success_rate": current_data.get("success_rate", 1.0)
        }

        with open(skill_file, 'w') as f:
            json.dump(skill_data, f, indent=2)
            
        print(f"🧬 MemOS: Habilidad '{name}' evolucionada a v{version}.")
        self._log_evolution(name, version, "Habilidad actualizada/creada")

    def _log_evolution(self, skill_name, version, message):
        log_file = os.path.join(self.log_path, "evolution.log")
        with open(log_file, 'a') as f:
            f.write(f"[{time.ctime()}] {skill_name} v{version}: {message}\n")

    def get_skill(self, name):
        skill_file = os.path.join(self.vault_path, f"{name.lower()}.json")
        if os.path.exists(skill_file):
            with open(skill_file, 'r') as f:
                return json.load(f)
        return None

# Singleton del Kernel
memos = MemOSKernel()
