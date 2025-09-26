import json
import os
import ttkbootstrap as ttk
from constants.themes import THEMES

class ThemeManager:
    def __init__(self):
        self.current_theme = "light"
        self.theme_config = THEMES[self.current_theme]
    
    def load_theme_preference(self):
        """Load user's theme preference"""
        try:
            if os.path.exists('theme_preference.json'):
                with open('theme_preference.json', 'r') as f:
                    data = json.load(f)
                    return data.get('theme', 'light')
        except:
            pass
        return 'light'

    def save_theme_preference(self, theme_name):
        """Save user's theme preference"""
        try:
            with open('theme_preference.json', 'w') as f:
                json.dump({'theme': theme_name}, f)
        except:
            pass

    def apply_theme(self, theme_name, root):
        """Apply the specified theme to the application"""
        if theme_name not in THEMES:
            return
            
        self.current_theme = theme_name
        self.theme_config = THEMES[theme_name]
        
        # Apply ttkbootstrap theme
        style = ttk.Style()
        style.theme_use(self.theme_config["theme"])
        
        # Configure custom styles
        self.configure_custom_styles()
        
        # Update window background
        root.configure(bg=self.theme_config["colors"]["background"])

    def configure_custom_styles(self):
        """Configure custom styles for the current theme"""
        style = ttk.Style()
        colors = self.theme_config["colors"]
        
        # Configure frame styles first
        style.configure(
            "Sidebar.TFrame",
            background=colors["sidebar"]
        )
        
        style.configure(
            "Content.TFrame",
            background=colors["background"]
        )
        
        # Set defaults so any unspecified frames/labels inherit our theme bg/fg
        style.configure("TFrame", background=colors["background"]) 
        style.configure("TLabel", background=colors["background"], foreground=colors["text"]) 
        style.configure("TNotebook", background=colors["background"]) 
        # Avoid overriding TSeparator to prevent ttkbootstrap from recreating the element and
        # throwing 'Duplicate element Horizontal.Separator.separator' on theme re-apply.
        style.configure("TMenubutton", background=colors["surface"], foreground=colors["text"]) 
        
        # Configure title label style
        style.configure(
            "Title.TLabel",
            font=("Segoe UI", 22, "bold"),
            foreground=colors["text"],
            background=colors["background"]
        )
        
        # Configure section label style
        style.configure(
            "Section.TLabel",
            font=("Segoe UI", 14, "bold"),
            foreground=colors["text"],
            background=colors["background"]
        )
        
        # Configure info label style
        style.configure(
            "Info.TLabel",
            font=("Segoe UI", 10),
            foreground=colors["text_secondary"],
            background=colors["background"]
        )
        
        # Configure card frame style
        style.configure(
            "Card.TFrame",
            background=colors["surface"],
            relief="flat",
            borderwidth=0,
            bordercolor=colors.get("border", colors["surface"])  # ttkbootstrap supports bordercolor
        )

        # Also flatten Labelframes that some cards may use internally
        style.configure(
            "TLabelframe",
            background=colors["background"],
            borderwidth=0
        )
        style.configure(
            "Card.TLabelframe",
            background=colors["background"],
            borderwidth=0,
            bordercolor=colors.get("border", colors["surface"]) 
        )
        style.configure(
            "TLabelframe.Label",
            background=colors["background"],
            foreground=colors["text"]
        )

        # Improve input visibility (Entry, Combobox)
        # Entry fields
        style.configure(
            "TEntry",
            fieldbackground=colors.get("input_bg", colors["surface"]),
            foreground=colors.get("input_fg", colors["text"]),
            background=colors["surface"],
            bordercolor=colors.get("border", colors["surface"])  # ttkbootstrap option
        )
        style.map(
            "TEntry",
            fieldbackground=[
                ("disabled", colors["surface"]),
                ("readonly", colors.get("input_bg", colors["surface"]))
            ],
            foreground=[
                ("disabled", colors["text_secondary"]),
                ("readonly", colors.get("input_fg", colors["text"]))
            ]
        )

        # Combobox fields
        style.configure(
            "TCombobox",
            fieldbackground=colors.get("input_bg", colors["surface"]),
            foreground=colors.get("input_fg", colors["text"]),
            background=colors["surface"],
            bordercolor=colors.get("border", colors["surface"])  # ttkbootstrap option
        )
        style.map(
            "TCombobox",
            fieldbackground=[
                ("readonly", colors.get("input_bg", colors["surface"]))
            ],
            foreground=[
                ("disabled", colors["text_secondary"]),
                ("readonly", colors.get("input_fg", colors["text"]))
            ]
        )

    def get_current_theme(self):
        """Get current theme name"""
        return self.current_theme

    def get_theme_config(self):
        """Get current theme configuration"""
        return self.theme_config 