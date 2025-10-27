import tkinter as tk
import ttkbootstrap as ttk
from ui.widgets.help_dialog import HelpDialog
from ui.help.help_content import HELP_CONTENT
from ui.widgets.tooltip import Tooltip
from utils.settings_manager import SettingsManager

_settings_mgr = None
def _get_help_settings():
    global _settings_mgr
    if _settings_mgr is None:
        try:
            _settings_mgr = SettingsManager()
        except Exception:
            # Fallback defaults if settings manager not available
            class _Tmp:
                def get(self, section, key=None):
                    return {
                        "show_help_icons": True,
                        "help_anchor_mode": "center",
                        "tooltip_enabled": True,
                    } if key is None else {
                        "show_help_icons": True,
                        "help_anchor_mode": "center",
                        "tooltip_enabled": True,
                    }.get(key)
            _settings_mgr = _Tmp()
    return _settings_mgr.get("help") or {"show_help_icons": True, "help_anchor_mode": "center", "tooltip_enabled": True}

class HelpIcon(ttk.Button):
    def __init__(self, parent, help_id: str, *args, **kwargs):
        # Use link style and bracketed text for compact inline placement
        super().__init__(parent, text="(?)", bootstyle="link", *args, **kwargs)
        self.help_id = help_id
        try:
            self.configure(padding=0, cursor="hand2", takefocus=0)
        except Exception:
            pass
        self.configure(command=self._on_click)
        # Optional tooltip
        try:
            settings = _get_help_settings()
            if settings.get("tooltip_enabled", True):
                about = (HELP_CONTENT.get(self.help_id, {}) or {}).get("about", "")
                if about:
                    Tooltip(self, about)
        except Exception:
            pass

    def _on_click(self):
        data = HELP_CONTENT.get(self.help_id, {})
        title = data.get("title", self.help_id)
        about = data.get("about", "")
        examples = data.get("examples", [])
        # Anchor behavior based on settings
        anchor_widget = None
        try:
            settings = _get_help_settings()
            if (settings.get("help_anchor_mode") or "center").lower() == "attach":
                anchor_widget = self
        except Exception:
            anchor_widget = None
        HelpDialog(self.winfo_toplevel(), title, about, examples, anchor_widget=anchor_widget)
