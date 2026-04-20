import json
import os
import requests
from datetime import datetime, timedelta

class SelfModelEvolver:
    def __init__(self, workspace_root='D:\\IA\\CODE\\claudebot'):
        self.root = workspace_root
        self.vault_path = os.path.join(self.root, 'life_logs', 'vector_vault.json')
        self.finance_path = os.path.join(self.root, 'personal_HUB', 'expense_tracker', 'data', 'finance.json')
        self.rule_engine_path = os.path.join(self.root, 'self_model', 'rule_engine.json')

    def _get_historical_summary(self):
        """Resume los últimos 30 días de vida."""
        summary = []
        journal_dir = os.path.join(self.root, 'life_logs', 'journal')
        if os.path.exists(journal_dir):
            files = sorted(os.listdir(journal_dir), reverse=True)[:30]
            for f in files:
                if f.endsWith('.json'):
                    with open(os.path.join(journal_dir, f), 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        summary.append({
                            "date": data['date'],
                            "readiness": (data.get('insight', {}).get('scores', {}).get('deep_work', 0)),
                            "entry": data.get('entry', '')[:200],
                            "tags": data.get('insight', {}).get('tags', [])
                        })
        return summary

    def evolve(self):
        history = self._get_historical_summary()
        
        prompt = f"""
        Eres el "Estratega de Evolución Aether". Tu misión es analizar el historial del usuario y extraer LEYES DE RENDIMIENTO.
        REGLA CRÍTICA: Nunca prohíbas nada. Tus consejos deben ser técnicos, basados en datos y sugerir "Costos de Oportunidad".
        
        HISTORIAL RECIENTE:
        {json.dumps(history, indent=2)}
        
        TAREA:
        1. Identifica qué condiciones (sueño, hora, proyectos) generan más dinero o código limpio.
        2. Crea 3 "Protocolos de Riesgo" (ej: "Protocolo de Latencia Alta: Si Readiness < 30%, el costo de debugging aumenta 2x").
        
        FORMATO JSON PURO PARA 'rule_engine.json':
        {{
          "version": "1.1",
          "last_evolution": "{datetime.now().isoformat()}",
          "active_protocols": [
            {{ "name": "Nombre", "condition": "Si X...", "advice": "Cuidado con...", "emoji": "⚠️" }}
          ]
        }}
        """

        try:
            response = requests.post('http://127.0.0.1:11434/api/generate', 
                                   json={
                                       "model": "qwen2.5-coder:3b",
                                       "system": "Eres un analista de datos y rendimiento humano.",
                                       "prompt": prompt,
                                       "stream": false,
                                       "format": "json"
                                   })
            new_rules = json.loads(response.json()['response'])
            
            with open(self.rule_engine_path, 'w', encoding='utf-8') as f:
                json.dump(new_rules, f, indent=2)
            
            print("Self-Model Evolucionado: Nuevos protocolos cargados.")
        except Exception as e:
            print(f"Error en evolución: {e}")

if __name__ == "__main__":
    evolver = SelfModelEvolver()
    evolver.evolve()
