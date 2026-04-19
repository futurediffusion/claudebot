from google_fit_sync import GoogleFitSync
from datetime import datetime, timedelta

sync = GoogleFitSync()
sync.authenticate()

# Consultamos los últimos 3 días para estar seguros
for i in range(1, 4):
    target_date = datetime.now() - timedelta(days=i)
    data = sync.get_health_data(target_date)
    print(f"\n📅 Fecha: {data['date']}")
    print(f"👟 Pasos: {data['steps']:,}")
    print(f"❤️ Pulsaciones (avg): {data['heart_rate_avg']} bpm")
    print("-" * 30)
