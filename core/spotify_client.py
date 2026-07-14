import logging
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config.settings import Settings

class SpotifyClient:
    def __init__(self):
        self.sp = None
        self.sp_oauth = None
        self.status_message = "Not Authenticated"
        self.last_error = None
        self.is_authenticating = False

    def is_configured(self):
        """Check if Spotify developer credentials are set in Settings."""
        return Settings.is_credentials_set()

    def initialize_oauth(self):
        """Initializes the SpotifyOAuth handler using current Settings."""
        if not self.is_configured():
            self.status_message = "Credentials missing in .env"
            return False
        
        try:
            self.sp_oauth = SpotifyOAuth(
                client_id=Settings.SPOTIFY_CLIENT_ID,
                client_secret=Settings.SPOTIFY_CLIENT_SECRET,
                redirect_uri=Settings.SPOTIFY_REDIRECT_URI,
                scope="user-modify-playback-state user-read-currently-playing user-read-playback-state",
                cache_path=Settings.CACHE_PATH,
                open_browser=True
            )
            return True
        except Exception as e:
            self.status_message = f"OAuth Init Error: {str(e)}"
            self.last_error = e
            return False

    def authenticate(self, force_interactive=False):
        """
        Attempts to authenticate with Spotify.
        If force_interactive is True and no cached token is found,
        it launches a web browser for authorization.
        """
        if self.is_authenticating:
            return False

        if not self.sp_oauth:
            if not self.initialize_oauth():
                return False

        self.is_authenticating = True
        try:
            # Check for cached token (validate_token refreshes automatically if expired)
            cached_token = self.sp_oauth.cache_handler.get_cached_token()
            token_info = self.sp_oauth.validate_token(cached_token)

            if not token_info:
                if force_interactive:
                    self.status_message = "Authorizing in browser..."
                    # get_access_token will open a browser window and start redirect server
                    token_info = self.sp_oauth.get_access_token(as_dict=True)
                else:
                    self.status_message = "Spotify login required (Click Refresh/Auth)"
                    self.sp = None
                    return False

            if token_info and 'access_token' in token_info:
                self.sp = spotipy.Spotify(auth=token_info['access_token'])
                self.status_message = "Connected to Spotify"
                return True
            else:
                self.status_message = "Auth failed: no token"
                self.sp = None
                return False
        except Exception as e:
            self.status_message = f"Auth Error: {str(e)}"
            self.last_error = e
            self.sp = None
            return False
        finally:
            self.is_authenticating = False

    def refresh_token(self):
        """Forces a refresh of the Spotify OAuth token and re-authenticates."""
        # Reload settings in case credentials changed in .env
        Settings.reload()
        # Reset OAuth client with fresh credentials
        if self.initialize_oauth():
            return self.authenticate(force_interactive=True)
        return False

    def get_active_device(self):
        """
        Finds the active player device. If none is active, attempts to locate
        any available device and transfer playback to it.
        Returns:
            device_id (str or None): ID of target device.
            device_name (str or None): Name of target device.
        """
        if not self.sp:
            return None, None

        try:
            devices_data = self.sp.devices()
            devices = devices_data.get('devices', [])

            if not devices:
                self.status_message = "No Spotify devices found. Open Spotify."
                return None, None

            # Look for an already active device
            for dev in devices:
                if dev.get('is_active'):
                    return dev.get('id'), dev.get('name')

            # Fallback: transfer to first available device
            first_dev = devices[0]
            dev_id = first_dev.get('id')
            dev_name = first_dev.get('name')
            
            try:
                self.sp.transfer_playback(device_id=dev_id, force_play=False)
                self.status_message = f"Transferred to {dev_name}"
            except Exception:
                # Swallowing transfer exception but still returning the device ID
                pass
            return dev_id, dev_name

        except Exception as e:
            self.status_message = f"Device lookup error: {str(e)}"
            self.last_error = e
            return None, None

    def play_playlist(self, playlist_uri):
        """
        Starts playback of the specified playlist on the active/available device.
        Handles API errors, offline states, and inactive devices.
        """
        if not self.sp:
            if not self.authenticate(force_interactive=False):
                return False

        try:
            device_id, device_name = self.get_active_device()
            if not device_id:
                return False

            # Start playback of the playlist context
            self.sp.start_playback(device_id=device_id, context_uri=playlist_uri)
            self.status_message = f"Playing playlist on {device_name}"
            return True
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 403:
                self.status_message = "Spotify Premium required for controls"
            elif e.http_status == 404:
                self.status_message = "Spotify Device not found or offline"
            else:
                self.status_message = f"Playback error: {e.msg}"
            self.last_error = e
            return False
        except Exception as e:
            self.status_message = f"Error: {str(e)}"
            self.last_error = e
            return False

    def get_playback_status(self):
        """
        Fetches the current playback status from Spotify.
        Returns:
            is_playing (bool)
            current_track (str)
            device_name (str)
            status_message (str)
        """
        if not self.sp:
            return False, "None", "None", self.status_message

        try:
            playback = self.sp.current_playback()
            if not playback:
                # Player is inactive/idle, check if devices exist
                devices_data = self.sp.devices()
                devices = devices_data.get('devices', [])
                if devices:
                    # Devices are online but nothing is active/playing
                    active_dev_name = next((d.get('name') for d in devices if d.get('is_active')), "None")
                    if active_dev_name == "None":
                        return False, "Not Playing", "None", "No active playback (open & play Spotify)"
                    return False, "Not Playing", active_dev_name, "Ready (Spotify paused)"
                else:
                    return False, "None", "None", "No Spotify devices found (open Spotify)"

            is_playing = playback.get('is_playing', False)
            device_name = playback.get('device', {}).get('name', 'Unknown')
            track_name = "Unknown"
            
            item = playback.get('item')
            if item:
                track_name = item.get('name', 'Unknown')
                artists = item.get('artists', [])
                if artists:
                    artist_names = ", ".join([art.get('name', '') for art in artists])
                    track_name = f"{track_name} - {artist_names}"

            return is_playing, track_name, device_name, "Spotify Active"
        except Exception as e:
            self.last_error = e
            return False, "Unknown", "Unknown", f"Status query error: {str(e)}"
