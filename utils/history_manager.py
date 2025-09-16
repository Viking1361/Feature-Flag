import json
import os
from config import HISTORY_FILE

class HistoryManager:
    def __init__(self):
        self.history = self.load_history()

    def load_history(self):
        """Load history from file"""
        default_history = {"urls": [], "keys": [], "pmcs": [], "sites": [], "update_keys": [], "get_keys": []}
        
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r') as f:
                    loaded_history = json.load(f)
                    # Ensure all required keys exist
                    for key in default_history:
                        if key not in loaded_history:
                            loaded_history[key] = []
                    return loaded_history
            except:
                return default_history
        return default_history

    def save_history(self):
        """Save history to file"""
        with open(HISTORY_FILE, 'w') as f:
            json.dump(self.history, f)

    def update_history(self, url, key, pmc, site):
        """Update history with new values"""
        if url and url not in self.history['urls']:
            self.history['urls'].append(url)
        if key and key not in self.history['keys']:
            self.history['keys'].append(key)
        if pmc and pmc not in self.history['pmcs']:
            self.history['pmcs'].append(pmc)
        if site and site not in self.history['sites']:
            self.history['sites'].append(site)
        self.save_history()

    def add_update_key(self, key):
        """Add a key to update history"""
        if key and key not in self.history['update_keys']:
            self.history['update_keys'].append(key)
            self.save_history()

    def add_get_key(self, key):
        """Add a key to get history"""
        # Ensure get_keys exists
        if 'get_keys' not in self.history:
            self.history['get_keys'] = []
            
        if key and key not in self.history['get_keys']:
            self.history['get_keys'].append(key)
            self.save_history()

    def get_history(self):
        """Get current history"""
        return self.history 