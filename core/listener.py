import time
import threading
from pynput import keyboard

class KeystrokeListener:
    def __init__(self):
        """Initializes the keystroke listener with thread-safe data structures."""
        self.timestamps = []
        self.lock = threading.Lock()
        self.listener = None
        self.active = False

    def _on_press(self, key):
        """Internal callback invoked on every keypress."""
        if not self.active:
            return
        
        now = time.time()
        with self.lock:
            self.timestamps.append(now)

    def start(self):
        """Starts the global keyboard hook listener in a background daemon thread."""
        with self.lock:
            if not self.active:
                self.active = True
                self.timestamps = []
                self.listener = keyboard.Listener(on_press=self._on_press)
                self.listener.daemon = True
                self.listener.start()

    def stop(self):
        """Stops the global keyboard hook listener cleanly."""
        with self.lock:
            self.active = False
            if self.listener is not None:
                try:
                    self.listener.stop()
                except Exception:
                    pass
                self.listener = None

    def get_kpm(self):
        """
        Calculates and returns the current Keystrokes Per Minute (KPM)
        based on a rolling 60-second sliding window.
        
        Also performs clean up of older timestamps to prevent memory growth.
        """
        now = time.time()
        cutoff = now - 60.0
        
        with self.lock:
            # Keep only timestamps within the last 60 seconds
            self.timestamps = [t for t in self.timestamps if t >= cutoff]
            kpm = len(self.timestamps)
            
        return kpm

    def clear(self):
        """Clears the tracked history."""
        with self.lock:
            self.timestamps = []
