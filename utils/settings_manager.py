"""
Settings Manager for Feature Flag Application
Handles saving and loading user preferences
"""

import json
import os
from typing import Dict, Any

class SettingsManager:
    def __init__(self, settings_file: str = "app_settings.json"):
        self.settings_file = settings_file
        self.default_settings = {
            "view_options": {
                "row_height": 30,
                "color_theme": "Enhanced (Current)",
                "auto_refresh_enabled": True,
                "auto_refresh_interval": 30
            },
            "window": {
                "last_tab": "view",
                "window_size": "1200x800"
            },
            "filters": {
                "default_environment": "All",
                "default_status": "All",
                "default_health": "All"
            }
        }
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file or return defaults"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return self._merge_settings(self.default_settings, loaded_settings)
            else:
                print(f"Settings file {self.settings_file} not found, using defaults")
                return self.default_settings.copy()
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self.default_settings.copy()
    
    def save_settings(self) -> bool:
        """Save current settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            print(f"Settings saved to {self.settings_file}")
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get(self, section: str, key: str = None) -> Any:
        """Get a setting value"""
        try:
            if key is None:
                return self.settings.get(section, {})
            return self.settings.get(section, {}).get(key)
        except Exception:
            return None
    
    def set(self, section: str, key: str, value: Any) -> bool:
        """Set a setting value"""
        try:
            if section not in self.settings:
                self.settings[section] = {}
            self.settings[section][key] = value
            return True
        except Exception as e:
            print(f"Error setting {section}.{key}: {e}")
            return False
    
    def update_view_options(self, row_height: int, theme: str, auto_refresh_enabled: bool, auto_refresh_interval: int):
        """Update view options settings"""
        self.set("view_options", "row_height", row_height)
        self.set("view_options", "color_theme", theme)
        self.set("view_options", "auto_refresh_enabled", auto_refresh_enabled)
        self.set("view_options", "auto_refresh_interval", auto_refresh_interval)
        return self.save_settings()
    
    def get_view_options(self) -> Dict[str, Any]:
        """Get all view options"""
        return self.get("view_options")
    
    def _merge_settings(self, defaults: Dict, loaded: Dict) -> Dict:
        """Recursively merge loaded settings with defaults"""
        result = defaults.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_settings(result[key], value)
            else:
                result[key] = value
        return result
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.settings = self.default_settings.copy()
        return self.save_settings()
