import os
import json
import sys
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Cargar credenciales del .env local
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, ".env"))

class SpotifyDJ:
    def __init__(self):
        scope = "user-modify-playback-state user-read-playback-state user-read-currently-playing"
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=os.getenv("CLIENT_ID"),
            client_secret=os.getenv("CLIENT_SECRET"),
            redirect_uri=os.getenv("REDIRECT_URI"),
            scope=scope,
            cache_path=os.path.join(current_dir, ".cache")
        ))

    def get_status(self):
        try:
            current = self.sp.current_playback()
            if not current: return {"status": "off", "message": "Spotify no esta abierto o no hay reproduccion activa."}
            return {
                "status": "playing" if current['is_playing'] else "paused",
                "track": current['item']['name'],
                "artist": current['item']['artists'][0]['name'],
                "volume": current['device']['volume_percent']
            }
        except Exception as e:
            if "Active premium subscription required" in str(e):
                return {"status": "restricted", "message": "Control de reproduccion bloqueado (Requiere cuenta Premium)"}
            return {"error": str(e)}

    def search_track(self, query):
        """Busqueda de canciones (Funciona para cuentas Gratuitas)"""
        try:
            results = self.sp.search(q=query, limit=5, type='track')
            tracks = []
            for item in results['tracks']['items']:
                tracks.append({
                    "name": item['name'],
                    "artist": item['artists'][0]['name'],
                    "album": item['album']['name'],
                    "url": item['external_urls']['spotify']
                })
            return {"status": "success", "results": tracks}
        except Exception as e:
            return {"error": str(e)}

    def play_pause(self):
        try:
            current = self.sp.current_playback()
            if current['is_playing']:
                self.sp.pause_playback()
                return {"message": "Musica pausada"}
            else:
                self.sp.start_playback()
                return {"message": "Reproduccion reanudada"}
        except Exception as e:
            if "Active premium subscription required" in str(e):
                return {"error": "Esta accion requiere Spotify Premium"}
            return {"error": str(e)}

def run_mcp_loop():
    dj = SpotifyDJ()
    print("--- SPOTIFY DJ MCP SERVER ONLINE (Non-Premium Ready) ---")
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line: break
            request = json.loads(line)
            method = request.get("method")
            params = request.get("params", {})
            
            if method == "status":
                result = dj.get_status()
            elif method == "search":
                result = dj.search_track(params.get("query", ""))
            elif method == "toggle":
                result = dj.play_pause()
            else:
                result = {"error": "Metodo no soportado o requiere Premium"}
            
            print(json.dumps({"result": result}))
            sys.stdout.flush()
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            sys.stdout.flush()

if __name__ == "__main__":
    dj = SpotifyDJ()
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Test de busqueda (Validando conexion API):")
        print(json.dumps(dj.search_track("gatos"), indent=2))
    else:
        run_mcp_loop()
