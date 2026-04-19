import json
import os
import sys
import requests
from datetime import datetime

# Añadir la raíz al path para importar logger_pro
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from logger_pro import setup_logger

log = setup_logger('capability_evolver')

PATTERNS_FILE = "self_model/failure_patterns.json"
EVO_REPORT_FILE = "evolution_report.md"
OLLAMA_URL = "http://localhost:11434/api/generate"

class CapabilityEvolver:
    def __init__(self):
        self.patterns = self.load_patterns()

    def load_patterns(self):
        if os.path.exists(PATTERNS_FILE):
            with open(PATTERNS_FILE, 'r') as f:
                return json.load(f).get("patterns", [])
        return []

    async def ask_ollama_for_evolution(self):
        """Usa Ollama para analizar los fallos y proponer mejoras de código."""
        patterns_text = json.dumps(self.patterns, indent=2)
        prompt = f"""
        ERES EL ARQUITECTO DE EVOLUCION DE CLAUDEBOT.
        Analiza estos patrones de fallo recientes:
        {patterns_text}
        
        Tu tarea es generar un reporte de evolución (Markdown) que incluya:
        1. Análisis de causa raíz de cada patrón.
        2. Propuesta de mejora de código o instrucciones para las skills.
        3. Prioridad de la mutación (Baja, Media, Alta).
        
        Responde SOLO con el contenido del reporte en Markdown.
        """
        log.info("Consultando a Ollama (Arquitecto) para plan de evolución...")
        try:
            payload = {"model": "qwen2.5-coder:7b", "prompt": prompt, "stream": False}
            resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
            return resp.json().get('response', 'Fallo al generar reporte con Ollama.')
        except Exception as e:
            log.error(f"Ollama no disponible para evolución: {e}")
            return "Error: Ollama (Qwen 7b) no respondió. Revisa si el servicio está activo."

    async def run(self):
        if not self.patterns:
            log.info("No hay patrones de fallo para analizar. Evolución no necesaria.")
            return

        report_content = await self.ask_ollama_for_evolution()
        
        with open(EVO_REPORT_FILE, "w", encoding="utf-8") as f:
            f.write(f"# 🧬 CLAUDEBOT EVOLUTION REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write(report_content)
        
        log.info(f"¡Evolución completada! Reporte generado en: {EVO_REPORT_FILE}")

if __name__ == "__main__":
    import asyncio
    evolver = CapabilityEvolver()
    asyncio.run(evolver.run())
