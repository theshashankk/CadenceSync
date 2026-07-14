import time
from config.settings import Settings

class StateMapper:
    def __init__(self):
        """Initializes the tempo state mapper."""
        self.current_state = "Calm"
        self.pending_state = "Calm"
        self.pending_state_since = None

    def update(self, kpm):
        """
        Evaluates the KPM against speed brackets and applies debouncing.
        
        Args:
            kpm (int): Keystrokes Per Minute.
            
        Returns:
            str or None: The new state name ("Calm", "Flow", "Sprint") only when 
                         a transition completes (debounced), otherwise None.
        """
        # Determine the target state based on KPM
        if kpm < Settings.KPM_CALM_LIMIT:
            target_state = "Calm"
        elif kpm <= Settings.KPM_FLOW_LIMIT:
            target_state = "Flow"
        else:
            target_state = "Sprint"

        # If the KPM target state is the same as our active current state,
        # reset any pending state transition timer.
        if target_state == self.current_state:
            self.pending_state = self.current_state
            self.pending_state_since = None
            return None

        # If the target state changed from the pending state, start/reset the debounce timer.
        if target_state != self.pending_state:
            self.pending_state = target_state
            self.pending_state_since = time.time()
            return None

        # If target_state == pending_state and target_state != current_state,
        # check if we have held this pending state for the required debounce duration.
        elapsed = time.time() - self.pending_state_since
        if elapsed >= Settings.DEBOUNCE_SECONDS:
            old_state = self.current_state
            self.current_state = self.pending_state
            self.pending_state_since = None
            return self.current_state

        return None

    def force_state(self, state):
        """Forces the current state to a specific value immediately, bypassing debounce."""
        if state in ["Calm", "Flow", "Sprint"]:
            self.current_state = state
            self.pending_state = state
            self.pending_state_since = None
