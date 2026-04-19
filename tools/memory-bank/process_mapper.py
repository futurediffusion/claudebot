import os
import time

class ProcessMapper:
    def __init__(self):
        # Ruta corregida hacia la carpeta de memoria
        self.map_path = os.path.join("memory", "memory_bank", "progress_map.md")

    def update_map(self, current_step, next_steps=None, completed_steps=None):
        """Genera un diagrama Mermaid visual del progreso actual"""
        next_steps = next_steps or []
        completed_steps = completed_steps or []
        
        mermaid_content = "```mermaid\ngraph TD\n"
        
        # Añadir pasos completados
        for step in completed_steps:
            mermaid_content += f"    {step.replace(' ', '_')}[{step}] -->\n"
            mermaid_content += f"    style {step.replace(' ', '_')} fill:#9f9,stroke:#333,stroke-width:2px\n"
            
        # Añadir paso actual
        mermaid_content += f"    {current_step.replace(' ', '_')}(({current_step}))\n"
        mermaid_content += f"    style {current_step.replace(' ', '_')} fill:#f96,stroke:#333,stroke-width:4px\n"
        
        # Añadir pasos futuros
        for step in next_steps:
            mermaid_content += f"    {current_step.replace(' ', '_')} -.-> {step.replace(' ', '_')}[{step}]\n"
            mermaid_content += f"    style {step.replace(' ', '_')} fill:#eee,stroke:#999,stroke-dasharray: 5 5\n"
            
        mermaid_content += "```"
        
        # Asegurar que el directorio existe antes de escribir
        os.makedirs(os.path.dirname(self.map_path), exist_ok=True)
        
        with open(self.map_path, 'w', encoding='utf-8') as f:
            f.write(f"# Progress Map\n\nActualizado el: {time.ctime()}\n\n{mermaid_content}\n")
            
        print(f"🗺️ Memory Bank: Mapa de procesos actualizado en {self.map_path}")

# Singleton para acceso global
mapper = ProcessMapper()
