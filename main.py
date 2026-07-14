import os
import sys
import time
import logging
import threading
from PIL import Image

import pystray
from pystray import MenuItem as item

from config.settings import Settings
from core.listener import KeystrokeListener
from core.spotify_client import SpotifyClient
from core.mapper import StateMapper

# Resolve the application paths
if getattr(sys, 'frozen', False):
    BASE_PATH = os.path.dirname(sys.executable)
    RESOURCE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_PATH = BASE_PATH

# Configure local logging
try:
    log_file = os.path.join(BASE_PATH, 'cadence_sync.log')
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
except Exception:
    # Fallback to console logging if log file is not writable
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
logging.info("Starting CadenceSync application...")

# Load application icon asset with safe fallback
icon_path = os.path.join(RESOURCE_PATH, 'assets', 'icon.png')
try:
    if os.path.exists(icon_path):
        icon_image = Image.open(icon_path)
    else:
        # Fallback to dynamic image if file is missing
        icon_image = Image.new('RGB', (64, 64), '#1F2937')
        from PIL import ImageDraw
        draw = ImageDraw.Draw(icon_image)
        # Draw a simple cyan music/keyboard wave box
        draw.rectangle((16, 16, 48, 48), fill='#06B6D4')
        draw.line((24, 32, 40, 32), fill='#FFFFFF', width=2)
        draw.line((28, 26, 36, 26), fill='#FFFFFF', width=2)
        draw.line((20, 38, 44, 38), fill='#FFFFFF', width=2)
except Exception as e:
    logging.error(f"Failed to load/create icon image: {e}")
    icon_image = Image.new('RGB', (64, 64), '#1F2937')

class CadenceSyncApp:
    def __init__(self):
        self.listener = KeystrokeListener()
        self.spotify = SpotifyClient()
        self.mapper = StateMapper()

        self.tracking_active = True
        self.app_running = True
        
        self.current_kpm = 0
        self.current_mode = "Calm"
        self.last_played_playlist = None
        
        self.current_track = "None"
        self.current_device = "None"
        self.spotify_status = "Initializing..."
        
        self.icon = None
        self.lock = threading.Lock()

    def get_status_header(self):
        """Generates dynamic status string for the menu header."""
        with self.lock:
            if not self.tracking_active:
                return f"Status: Paused ({self.current_kpm} KPM)"
            return f"Status: {self.current_mode} Mode ({self.current_kpm} KPM)"

    def on_toggle_tracker(self, icon, item):
        """Toggles the keystroke tracking state."""
        with self.lock:
            self.tracking_active = not self.tracking_active
            active = self.tracking_active
            
        if active:
            logging.info("Keystroke tracker resumed.")
            self.listener.start()
        else:
            logging.info("Keystroke tracker paused.")
            self.listener.clear()
            self.mapper.force_state("Calm")
            self.last_played_playlist = None

    def on_refresh_spotify(self, icon, item):
        """Triggers manual re-authentication / settings reload in a background thread."""
        def worker():
            logging.info("Manual token refresh triggered.")
            with self.lock:
                self.spotify_status = "Authorizing..."
            
            success = self.spotify.refresh_token()
            
            with self.lock:
                if success:
                    self.spotify_status = "Connected to Spotify"
                    # Reset last played playlist context to force update on resume
                    self.last_played_playlist = None
                    logging.info("Spotify token successfully refreshed.")
                else:
                    self.spotify_status = self.spotify.status_message
                    logging.warning(f"Spotify authentication failed: {self.spotify_status}")
                    
        threading.Thread(target=worker, daemon=True).start()

    def on_exit(self, icon, item):
        """Shuts down all resources and terminates the application cleanly."""
        logging.info("Exiting application...")
        self.app_running = False
        self.listener.stop()
        if self.icon:
            self.icon.stop()

    def create_menu(self):
        """Builds and returns the system tray popup menu structure."""
        return pystray.Menu(
            item(
                lambda text: self.get_status_header(),
                action=lambda icon, item: None,
                enabled=False
            ),
            pystray.Menu.SEPARATOR,
            item(
                lambda text: "Pause Tracker" if self.tracking_active else "Resume Tracker",
                action=self.on_toggle_tracker,
                checked=lambda item: self.tracking_active
            ),
            item(
                "Force Refresh Spotify Token",
                action=self.on_refresh_spotify
            ),
            pystray.Menu.SEPARATOR,
            item(
                "Exit",
                action=self.on_exit
            )
        )

    def run_coordinator(self):
        """Background loop that evaluates typing pace and coordinates Spotify playback."""
        # Initial silent authentication attempt on start
        self.spotify.authenticate(force_interactive=False)

        while self.app_running:
            try:
                # 1. Retrieve KPM from keyboard listener
                kpm = self.listener.get_kpm()
                
                with self.lock:
                    self.current_kpm = kpm
                    active = self.tracking_active

                # 2. Feed KPM to state mapper & trigger playlist updates if needed
                if active:
                    new_mode = self.mapper.update(kpm)
                    with self.lock:
                        self.current_mode = self.mapper.current_state
                        current_mode = self.current_mode
                    
                    if new_mode:
                        playlist_uri = None
                        if new_mode == "Calm":
                            playlist_uri = Settings.SPOTIFY_PLAYLIST_CALM
                        elif new_mode == "Flow":
                            playlist_uri = Settings.SPOTIFY_PLAYLIST_FLOW
                        elif new_mode == "Sprint":
                            playlist_uri = Settings.SPOTIFY_PLAYLIST_SPRINT
                        
                        if playlist_uri and playlist_uri != self.last_played_playlist:
                            logging.info(f"Transitioning to {new_mode} state. Playing playlist: {playlist_uri}")
                            success = self.spotify.play_playlist(playlist_uri)
                            if success:
                                self.last_played_playlist = playlist_uri
                                logging.info(f"Successfully playing {new_mode} playlist.")
                            else:
                                logging.error(f"Playback transition failed: {self.spotify.status_message}")
                else:
                    with self.lock:
                        self.current_mode = "Paused"

                # 3. Update playback information
                is_playing, track, device, status = self.spotify.get_playback_status()
                with self.lock:
                    self.current_track = track
                    self.current_device = device
                    self.spotify_status = status

                # 4. Formulate localized, character-limited tray icon tooltip (Max 128 chars)
                tooltip_parts = [
                    f"CadenceSync ({self.current_mode})",
                    f"KPM: {self.current_kpm} | Dev: {self.current_device[:15]}",
                    f"Track: {self.current_track[:30]}",
                    f"Status: {self.spotify_status[:35]}"
                ]
                tooltip_text = "\n".join(tooltip_parts)[:127]
                
                if self.icon:
                    self.icon.title = tooltip_text
                    self.icon.update_menu()

            except Exception as e:
                logging.error(f"Exception in coordinator loop: {e}", exc_info=True)

            time.sleep(1.0)

    def run(self):
        """Starts the application hooks and boots the main system tray interface."""
        print("===================================================")
        print("           CadenceSync is now running!")
        print("===================================================")
        print(" -> Check your Windows System Tray (bottom-right taskbar).")
        print(" -> Note: It might be hidden inside the '^' overflow arrow.")
        print(" -> To interact: Right-click the icon in the system tray.")
        print(" -> To exit: Select 'Exit' from the tray menu or press Ctrl+C here.")
        print("===================================================\n")
        print("Listening for keystrokes globally...")
        sys.stdout.flush()
        logging.info("Starting listener thread...")
        self.listener.start()

        logging.info("Starting coordinator daemon thread...")
        coord_thread = threading.Thread(target=self.run_coordinator, daemon=True)
        coord_thread.start()

        logging.info("Launching System Tray Icon...")
        self.icon = pystray.Icon(
            "CadenceSync",
            icon=icon_image,
            menu=self.create_menu()
        )
        self.icon.run()

if __name__ == '__main__':
    # Force single-instance check if needed, or simply run the app
    app = CadenceSyncApp()
    app.run()
