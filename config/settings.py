import os
import sys
from dotenv import load_dotenv

# Resolve the application directory containing the script/executable
if getattr(sys, 'frozen', False):
    # Running as a compiled PyInstaller executable
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running from Python source code
    # __file__ is e:\vc\cadence-sync\config\settings.py, so parent of config is root.
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from the .env file in the base directory
env_path = os.path.join(BASE_DIR, '.env')
load_dotenv(env_path)

class Settings:
    # Spotify Developer Credentials
    SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', '')
    SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', '')
    SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8080')

    # Path to local token cache
    CACHE_PATH = os.path.join(BASE_DIR, '.cache')

    # Playlist Mappings (Spotify URIs or IDs)
    # Defaulting to some popular public playlists, but users should override these in .env
    SPOTIFY_PLAYLIST_CALM = os.getenv('SPOTIFY_PLAYLIST_CALM', 'spotify:playlist:37i9dQZF1DWWQRwui0ExPn')   # Lofi Beats
    SPOTIFY_PLAYLIST_FLOW = os.getenv('SPOTIFY_PLAYLIST_FLOW', 'spotify:playlist:37i9dQZF1DX8Uebhpia6b0')   # Chill Lofi Study Beats
    SPOTIFY_PLAYLIST_SPRINT = os.getenv('SPOTIFY_PLAYLIST_SPRINT', 'spotify:playlist:37i9dQZF1DX8T6tZ55487w') # Synthwave / Retrowave

    # Keyboard KPM Thresholds
    KPM_CALM_LIMIT = int(os.getenv('KPM_CALM_LIMIT', '80'))     # < 80 KPM = Calm
    KPM_FLOW_LIMIT = int(os.getenv('KPM_FLOW_LIMIT', '180'))    # 80 <= KPM <= 180 = Flow, > 180 = Sprint

    # Debounce parameter (seconds)
    DEBOUNCE_SECONDS = float(os.getenv('DEBOUNCE_SECONDS', '15.0'))

    @classmethod
    def reload(cls):
        """Reload settings from .env file (useful for dynamic updates)."""
        load_dotenv(env_path, override=True)
        cls.SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', '')
        cls.SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', '')
        cls.SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8080')
        cls.SPOTIFY_PLAYLIST_CALM = os.getenv('SPOTIFY_PLAYLIST_CALM', 'spotify:playlist:37i9dQZF1DWWQRwui0ExPn')
        cls.SPOTIFY_PLAYLIST_FLOW = os.getenv('SPOTIFY_PLAYLIST_FLOW', 'spotify:playlist:37i9dQZF1DX8Uebhpia6b0')
        cls.SPOTIFY_PLAYLIST_SPRINT = os.getenv('SPOTIFY_PLAYLIST_SPRINT', 'spotify:playlist:37i9dQZF1DX8T6tZ55487w')
        cls.KPM_CALM_LIMIT = int(os.getenv('KPM_CALM_LIMIT', '80'))
        cls.KPM_FLOW_LIMIT = int(os.getenv('KPM_FLOW_LIMIT', '180'))
        cls.DEBOUNCE_SECONDS = float(os.getenv('DEBOUNCE_SECONDS', '15.0'))

    @classmethod
    def is_credentials_set(cls):
        """Check if required Spotify developer credentials are configured."""
        return bool(cls.SPOTIFY_CLIENT_ID and cls.SPOTIFY_CLIENT_SECRET)
