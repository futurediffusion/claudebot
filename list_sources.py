from google_fit_sync import GoogleFitSync

sync = GoogleFitSync()
sync.authenticate()
print("Listando fuentes de datos disponibles:")
sync.list_data_sources()
