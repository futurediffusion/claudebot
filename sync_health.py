import json
import os
import glob
from datetime import datetime
from typing import Optional

import pandas as pd

from logger_pro import setup_logger


class StravaSync:
    """Sincronizador de actividades desde Strava API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.logger = setup_logger('strava_sync')

    def fetch_activities(self):
        """Obtiene actividades desde Strava API.

        TODO: Implementar cuando el usuario proporcione su API key de Strava.
        La API requiere autenticación OAuth. Voir:
        https://developers.strava.com/docs/getting-started/
        """
        self.logger.warning("fetch_activities() no implementado - API key requerida")
        raise NotImplementedError(
            "Se necesita API key de Strava para realizar fetching. "
            "Obtén una en: https://www.strava.com/settings/api"
        )


def find_fitness_data() -> list[str]:
    """Encuentra archivos CSV de fitness_data en life_logs/."""
    pattern = os.path.join('life_logs', 'aggregated_fitness_data*.csv')
    files = glob.glob(pattern)
    return sorted(files)


def extract_health_metrics(csv_path: str) -> dict:
    """Extrae métricas de heart_rate y sleep de un CSV."""
    df = pd.read_csv(csv_path)

    metrics = {}

    if 'heart_rate' in df.columns:
        metrics['heart_rate_avg'] = float(df['heart_rate'].mean())
        metrics['heart_rate_min'] = float(df['heart_rate'].min())
        metrics['heart_rate_max'] = float(df['heart_rate'].max())

    if 'sleep' in df.columns:
        metrics['sleep_avg_hours'] = float(df['sleep'].mean())
        metrics['sleep_min'] = float(df['sleep'].min())
        metrics['sleep_max'] = float(df['sleep'].max())

    return metrics


def generate_daily_summary() -> dict:
    """Genera resumen diario depuis CSV encontrados."""
    files = find_fitness_data()

    if not files:
        return {
            'date': datetime.now().isoformat(),
            'files_found': 0,
            'status': 'no_data'
        }

    all_metrics = []
    for f in files:
        metrics = extract_health_metrics(f)
        all_metrics.append(metrics)

    summary = {
        'date': datetime.now().isoformat(),
        'files_found': len(files),
        'files': [os.path.basename(f) for f in files],
        'heart_rate_avg': sum(m.get('heart_rate_avg', 0) for m in all_metrics) / len(all_metrics),
        'sleep_avg_hours': sum(m.get('sleep_avg_hours', 0) for m in all_metrics) / len(all_metrics),
        'metrics': all_metrics
    }

    return summary


def save_daily_summary(summary: dict):
    """Guarda resumen en daily_summary.json."""
    output_path = os.path.join('life_logs', 'daily_summary.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)


def main():
    logger = setup_logger('sync_health')
    logger.info("Iniciando sync_health.py")

    files = find_fitness_data()
    logger.info(f"Archivos encontrados: {len(files)}")

    summary = generate_daily_summary()
    logger.info(f"Resumen generado: {summary.get('status', 'ok')}")

    save_daily_summary(summary)
    logger.info("Resumen guardado en life_logs/daily_summary.json")

    return summary


if __name__ == '__main__':
    main()