import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

from logger_pro import setup_logger

SCOPES = [
    'https://www.googleapis.com/auth/fitness.activity.read',
    'https://www.googleapis.com/auth/fitness.heart_rate.read',
    'https://www.googleapis.com/auth/fitness.sleep.read',
]


class GoogleFitSync:
    """Sincronizador de datos de Google Fit API."""

    def __init__(self, credentials_path: str = 'life_logs/credentials.json'):
        self.credentials_path = credentials_path
        self.token_path = 'life_logs/token.json'
        self.logger = setup_logger('google_fit_sync')
        self.creds: Optional[Credentials] = None

    def authenticate(self) -> Credentials:
        """Autentica con Google Fit API usando OAuth."""
        self.logger.info("Iniciando autenticación con Google Fit...")

        if not os.path.exists(self.credentials_path):
            self.logger.error(f"Archivo {self.credentials_path} no encontrado")
            raise FileNotFoundError(
                f"credentials.json no encontrado en {self.credentials_path}. "
                "Descárgalo desde Google Cloud Console."
            )

        if os.path.exists(self.token_path):
            self.creds = Credentials.from_authorized_user_info(
                json.load(open(self.token_path)),
                SCOPES
            )
            self.logger.info("Token cargado desde archivo existente")
            if self.creds.expired:
                self.logger.info("Token expirado, renovando...")
                self.creds = self._refresh_token()
        else:
            self.creds = self._run_oauth_flow()

        self._save_token()
        return self.creds

    def _run_oauth_flow(self) -> Credentials:
        """Ejecuta el flujo OAuth de Google."""
        flow = InstalledAppFlow.from_client_secrets_file(
            self.credentials_path,
            SCOPES,
            redirect_uri='http://localhost'
        )
        self.logger.info("Abriendo navegador para autorización...")
        creds = flow.run_local_server(port=0)
        self.logger.info("Autenticación completada")
        return creds

    def _refresh_token(self) -> Credentials:
        """Renueva el token expirado."""
        try:
            creds = self.creds
            creds.refresh()
            self.logger.info("Token renovado exitosamente")
            return creds
        except Exception as e:
            self.logger.warning(f"Error renovando token: {e}. Ejecutando OAuth flow...")
            return self._run_oauth_flow()

    def _save_token(self):
        """Guarda el token en archivo JSON."""
        os.makedirs(os.path.dirname(self.token_path), exist_ok=True)
        with open(self.token_path, 'w') as f:
            json.dump(json.loads(self.creds.to_json()), f)
        self.logger.info(f"Token guardado en {self.token_path}")

    def list_data_sources(self):
        """Lista todas las fuentes de datos disponibles (para debug)."""
        headers = {'Authorization': f'Bearer {self.creds.token}'}
        try:
            resp = requests.get('https://www.googleapis.com/fitness/v1/users/me/dataSources', headers=headers)
            sources = resp.json().get('dataSource', [])
            for s in sources:
                print(f"ID: {s['dataStreamId']} (Type: {s['dataType']['name']})")
        except Exception as e:
            print(f"Error listando fuentes: {e}")

    def get_health_data(self, date: Optional[datetime] = None) -> dict:
        """Obtiene pasos y pulsaciones del día."""
        if date is None:
            date = datetime.now(timezone.utc)

        start_time = datetime(date.year, date.month, date.day, tzinfo=timezone.utc)
        end_time = start_time + timedelta(days=1)

        start_ms = int(start_time.timestamp() * 1000)
        end_ms = int(end_time.timestamp() * 1000)

        headers = {
            'Authorization': f'Bearer {self.creds.token}',
            'Content-Type': 'application/json',
        }

        data = {
            'steps': 0,
            'heart_rate_avg': 0,
            'heart_rate_min': 0,
            'heart_rate_max': 0,
            'date': date.strftime('%Y-%m-%d'),
        }

        body = {
            "aggregateBy": [
                {"dataTypeName": "com.google.step_count.delta"},
                {"dataTypeName": "com.google.heart_rate.bpm"}
            ],
            "bucketByTime": {"durationMillis": 86400000},
            "startTimeMillis": start_ms,
            "endTimeMillis": end_ms
        }

        self.logger.debug(f"Obteniendo datos para {start_time.date()}...")

        try:
            response = requests.post(
                'https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate',
                headers=headers,
                json=body,
                timeout=30
            )

            if response.status_code != 200:
                self.logger.error(f"API response: {response.status_code} - {response.text}")
                return data

            results = response.json().get('bucket', [])

            for bucket in results:
                dataset = bucket.get('dataset', [])
                for ds in dataset:
                    points = ds.get('point', [])

                    if ds.get('dataSourceId') == 'derived:com.google.step_count.delta:Google:Fit':
                        steps = sum(p.get('value', [{}])[0].get('intVal', 0) for p in points)
                        data['steps'] = steps
                        self.logger.debug(f"Pasos: {steps}")

                    elif ds.get('dataSourceId') == 'derived:com.google.heart_rate.bpm:Google:Fit':
                        hr_values = [p.get('value', [{}])[0].get('fpVal', 0) for p in points]
                        if hr_values:
                            data['heart_rate_avg'] = round(sum(hr_values) / len(hr_values), 1)
                            data['heart_rate_min'] = min(hr_values)
                            data['heart_rate_max'] = max(hr_values)
                            self.logger.debug(f"HR: avg={data['heart_rate_avg']}, min={data['heart_rate_min']}, max={data['heart_rate_max']}")

        except requests.RequestException as e:
            self.logger.error(f"Error en requête: {e}")

        self.logger.info(
            f"Datos ({data['date']}): pasos={data['steps']}, "
            f"HR avg={data['heart_rate_avg']} bpm"
        )
        return data


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--refresh':
        if os.path.exists('life_logs/token.json'):
            os.remove('life_logs/token.json')
            print("Token eliminado. Ejecuta de nuevo para autenticar.")

    sync = GoogleFitSync()
    sync.authenticate()
    health_data = sync.get_health_data()

    print(f"\n[FECHA]: {health_data['date']}")
    print(f"[PASOS]: {health_data['steps']:,}")
    print(f"[PULSACIONES]: {health_data['heart_rate_min']}-{health_data['heart_rate_max']} bpm (avg: {health_data['heart_rate_avg']})")