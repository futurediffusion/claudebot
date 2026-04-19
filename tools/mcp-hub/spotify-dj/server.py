import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("spotify-dj")

_current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_current_dir, ".env"))

_dj = None  # lazy init — evita crash si credenciales no están configuradas


def _get_dj():
    global _dj
    if _dj is None:
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
        scope = "user-modify-playback-state user-read-playback-state user-read-currently-playing"
        _dj = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=os.getenv("CLIENT_ID"),
            client_secret=os.getenv("CLIENT_SECRET"),
            redirect_uri=os.getenv("REDIRECT_URI"),
            scope=scope,
            cache_path=os.path.join(_current_dir, ".cache"),
        ))
    return _dj


@mcp.tool()
def get_spotify_status() -> dict:
    """Devuelve la canción actual, artista, estado (playing/paused) y volumen."""
    try:
        current = _get_dj().current_playback()
        if not current:
            return {"status": "off", "message": "Spotify no está abierto o no hay reproducción activa."}
        return {
            "status": "playing" if current['is_playing'] else "paused",
            "track": current['item']['name'],
            "artist": current['item']['artists'][0]['name'],
            "volume": current['device']['volume_percent'],
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def search_track(query: str) -> dict:
    """Busca canciones en Spotify. Funciona con cuentas gratuitas. Devuelve top 5."""
    try:
        results = _get_dj().search(q=query, limit=5, type='track')
        tracks = []
        for item in results['tracks']['items']:
            tracks.append({
                "name": item['name'],
                "artist": item['artists'][0]['name'],
                "album": item['album']['name'],
                "url": item['external_urls']['spotify'],
            })
        return {"status": "success", "results": tracks}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def toggle_play_pause() -> dict:
    """Alterna play/pause en Spotify. Requiere cuenta Premium para control de reproducción."""
    try:
        current = _get_dj().current_playback()
        if current['is_playing']:
            _get_dj().pause_playback()
            return {"message": "Música pausada"}
        else:
            _get_dj().start_playback()
            return {"message": "Reproducción reanudada"}
    except Exception as e:
        if "Active premium subscription required" in str(e):
            return {"error": "Esta acción requiere Spotify Premium"}
        return {"error": str(e)}


if __name__ == "__main__":
    mcp.run()
