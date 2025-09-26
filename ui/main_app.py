import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox
import os
import webbrowser
import logging

from version import get_version_info, GITHUB_OWNER, GITHUB_REPO
from utils.auto_updater import get_updater
from shared.config_loader import LOG_FILE

# Import utility managers
from utils.theme_manager import ThemeManager
from utils.history_manager import HistoryManager

# Import tab modules
from ui.tabs.get_tab import GetTab
from ui.tabs.update_tab import UpdateTab
from ui.tabs.create_tab import CreateTab
from ui.tabs.enhanced_view_tab import EnhancedViewTab as ViewTab
from ui.tabs.log_tab import LogTab

# Module logger for this UI module
logger = logging.getLogger(__name__)

class FeatureFlagApp:
    def __init__(self, root):
        self.root = root
        # Ensure logging is configured early so logs always show in Log Viewer
        try:
            if not logging.getLogger().handlers:
                logging.basicConfig(
                    filename=LOG_FILE,
                    level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s',
                    encoding='utf-8'
                )
                # ASCII-only startup log
                info = get_version_info()
                logging.info(
                    f"App start: version={info.get('version','')} build_date={info.get('build_date','')} log_file={os.path.abspath(LOG_FILE)}"
                )
        except Exception as e:
            # Fallback to console if file logging fails (ASCII-only)
            print(f"DEBUG: Logging initialization failed: {e}")
        
        # Set window title with current user and role
        from shared.user_session import user_session
        username = user_session.username or "Unknown User"
        role_display = f" ({user_session.role.title()})" if user_session.is_logged_in else ""
        self.root.title(f"Feature Flag v3.0 - {username}{role_display}")
        self.root.geometry("1500x850")

        # Initialize managers
        self.theme_manager = ThemeManager()
        self.history_manager = HistoryManager()
        
        # Initialize theme
        self.current_theme = self.theme_manager.load_theme_preference()
        self.theme_manager.apply_theme(self.current_theme, self.root)
        
        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        """Setup the main application UI"""
        # Top frame for controls
        top_frame = ttk.Frame(self.root)
        top_frame.pack(side="top", fill="x", padx=10, pady=5)
        
        # Theme selector on the left
        theme_frame = ttk.Frame(top_frame)
        theme_frame.pack(side="left")
        
        ttk.Label(theme_frame, text="Theme:", font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        self.theme_var = tk.StringVar(value=self.current_theme)
        theme_combo = ttk.Combobox(
            theme_frame, 
            textvariable=self.theme_var,
            values=["light", "dark"],
            state="readonly",
            width=10,
            font=("Segoe UI", 10)
        )
        theme_combo.pack(side="left", padx=5)
        theme_combo.bind("<<ComboboxSelected>>", self.on_theme_change)
        
        # User session info in the middle
        session_frame = ttk.Frame(top_frame)
        session_frame.pack(side="left", expand=True)
        
        # Center the session info
        session_info_frame = ttk.Frame(session_frame)
        session_info_frame.pack(anchor="center")
        
        # User info with role
        from shared.user_session import user_session
        if user_session.is_logged_in:
            session_duration = user_session.session_duration or "00:00"
            role_icon = "👑" if user_session.is_admin else "👤"
            role_text = user_session.role.title()
            user_info_text = f"{role_icon} {user_session.username} ({role_text}) | ⏱️ {session_duration}"
            color = "purple" if user_session.is_admin else "darkgreen"
            
            self.user_info_label = ttk.Label(
                session_info_frame, 
                text=user_info_text, 
                font=("Segoe UI", 10, "bold"),
                foreground=color
            )
            self.user_info_label.pack(side="left", padx=20)
            
            # Update session info every minute - with safety check
            if self.user_info_label and self.user_info_label.winfo_exists():
                self.update_session_info()
            else:
                logger.debug("Session info label not ready, skipping periodic updates")
        
        # Logout button on the right
        logout_button = ttk.Button(top_frame, text="Logout", command=self.logout, bootstyle="danger")
        logout_button.pack(side="right")

        # Help menu (to the left of Logout)
        help_btn = ttk.Menubutton(top_frame, text="Help", bootstyle="secondary")
        help_menu = tk.Menu(help_btn, tearoff=0)
        help_menu.add_command(label="Check for Updates", command=lambda: get_updater(self.root).manual_check_for_updates())
        help_menu.add_command(label="Documentation", command=self.open_documentation)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about_dialog)
        help_btn["menu"] = help_menu
        help_btn.pack(side="right", padx=(0, 10))

        # Main container frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(pady=10, expand=True, fill="both", padx=10)

        # Create vertical tab layout
        self.create_vertical_tabs(main_frame)

        # Bottom frame for copyright
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(side="bottom", fill="x", padx=10, pady=5)
        
        copyright_label = ttk.Label(
            bottom_frame, 
            text="© 2024 Feature Flag Management System", 
            font=("Segoe UI", 9),
            foreground=self.theme_manager.get_theme_config()["colors"]["text_secondary"]
        )
        copyright_label.pack(side="right")

    def create_vertical_tabs(self, parent):
        """Create vertical tab layout"""
        # Create main container with vertical layout
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True)

        # Left panel for tab buttons
        self.tab_buttons_frame = ttk.Frame(container, width=220, style="Sidebar.TFrame")
        self.tab_buttons_frame.pack(side="left", fill="y", padx=(0, 15))
        self.tab_buttons_frame.pack_propagate(False)  # Maintain fixed width

        # Right panel for tab content
        self.content_frame = ttk.Frame(container, style="Content.TFrame")
        self.content_frame.pack(side="right", fill="both", expand=True)

        # Create tab buttons and content frames
        self.tab_buttons = {}
        self.tab_frames = {}
        
        # Add sidebar title
        title_frame = ttk.Frame(self.tab_buttons_frame)
        title_frame.pack(fill="x", pady=(15, 20))
        
        self.sidebar_title = ttk.Label(
            title_frame, 
            text="Feature Flags", 
            font=("Segoe UI", 16, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"],
            background=self.theme_manager.get_theme_config()["colors"]["sidebar"]
        )
        self.sidebar_title.pack(pady=5)
        
        # Add separator
        separator = ttk.Separator(self.tab_buttons_frame, orient="horizontal")
        separator.pack(fill="x", padx=10, pady=10)
        
        # Role-based tab configurations
        from shared.user_session import user_session
        
        all_tabs_config = [
            ("get", "Get Feature Flag", "📋", "get_flag"),
            ("update", "Update Feature Flag", "⚙️", "update_flag"),
            ("create", "Create Feature Flag", "➕", "create_flag"),
            ("view", "🔒 Feature Flags List", "📊", "view_all_flags"),  # Admin only
            ("log", "Log Viewer", "📝", "get_flag")  # Available to all
        ]
        
        # Filter tabs based on user permissions
        tabs_config = []
        for tab_id, tab_text, icon, permission in all_tabs_config:
            if user_session.has_permission(permission):
                # Add role indicator for admin-only tabs
                if permission == "view_all_flags" and user_session.is_admin:
                    display_text = f"{icon} {tab_text} (Admin)"
                else:
                    display_text = f"{icon} {tab_text}"
                tabs_config.append((tab_id, display_text, icon))
        
        logger.debug(
            f"Tabs available for {user_session.username} ({user_session.role}): {[t[0] for t in tabs_config]}"
        )

        # Create tab buttons
        for i, (tab_id, tab_text, icon) in enumerate(tabs_config):
            # Create button frame
            button_frame = ttk.Frame(self.tab_buttons_frame)
            button_frame.pack(fill="x", pady=1)

            # Create tab button
            btn = ttk.Button(
                button_frame,
                text=tab_text,
                command=lambda tid=tab_id: self.show_tab(tid),
                bootstyle="outline-toolbutton",
                width=28
            )
            btn.pack(fill="x", padx=8, pady=3)
            
            # Store button reference
            self.tab_buttons[tab_id] = btn

            # Create content frame
            content_frame = ttk.Frame(self.content_frame)
            self.tab_frames[tab_id] = content_frame

        # Initialize tab instances only for accessible tabs
        self.tab_instances = {}
        available_tab_ids = [tab_id for tab_id, _, _ in tabs_config]
        
        if "get" in available_tab_ids:
            self.tab_instances["get"] = GetTab(self.tab_frames["get"], self.history_manager, self.theme_manager)
        if "update" in available_tab_ids:
            self.tab_instances["update"] = UpdateTab(self.tab_frames["update"], self.history_manager, self.theme_manager)
        if "create" in available_tab_ids:
            self.tab_instances["create"] = CreateTab(self.tab_frames["create"], self.history_manager, self.theme_manager)
        if "view" in available_tab_ids:
            self.tab_instances["view"] = ViewTab(self.tab_frames["view"], self.history_manager, self.theme_manager)
        if "log" in available_tab_ids:
            self.tab_instances["log"] = LogTab(self.tab_frames["log"], self.history_manager, self.theme_manager)

        # Show default tab (first available tab)
        default_tab = available_tab_ids[0] if available_tab_ids else "get"
        self.show_tab(default_tab)

        # Auto-check for updates on startup (asynchronous; logs will show the request)
        try:
            get_updater(self.root).auto_check_on_startup()
        except Exception as e:
            # Log at debug level (ASCII-only message)
            logger.debug(f"Auto update check init failed: {e}")

    def show_tab(self, tab_id):
        """Show the specified tab"""
        # Hide all content frames
        for frame in self.tab_frames.values():
            frame.pack_forget()

        # Reset all button styles
        for btn in self.tab_buttons.values():
            btn.configure(bootstyle="outline-toolbutton")

        # Show selected content frame
        self.tab_frames[tab_id].pack(fill="both", expand=True)

        # Highlight selected button
        self.tab_buttons[tab_id].configure(bootstyle="primary")

    def on_theme_change(self, event=None):
        """Handle theme change event"""
        new_theme = self.theme_var.get()
        if new_theme != self.current_theme:
            self.theme_manager.apply_theme(new_theme, self.root)
            self.theme_manager.save_theme_preference(new_theme)
            self.current_theme = new_theme
            self.update_widget_colors()

    def update_widget_colors(self):
        """Update colors of existing widgets"""
        colors = self.theme_manager.get_theme_config()["colors"]
        
        # Update sidebar background
        if hasattr(self, 'tab_buttons_frame'):
            self.tab_buttons_frame.configure(style="Sidebar.TFrame")
        
        # Update tab buttons
        current_tab = self.get_current_tab()
        for tab_id, button in self.tab_buttons.items():
            if tab_id == current_tab:
                button.configure(bootstyle="primary")
            else:
                button.configure(bootstyle="outline-toolbutton")
        
        # Update treeview colors if it exists
        if hasattr(self.tab_instances, 'view') and hasattr(self.tab_instances['view'], 'update_treeview_colors'):
            self.tab_instances['view'].update_treeview_colors()
        
        # Update text colors if log tab exists
        if hasattr(self.tab_instances, 'log') and hasattr(self.tab_instances['log'], 'update_text_colors'):
            self.tab_instances['log'].update_text_colors()
        
        # Update sidebar title if it exists
        if hasattr(self, 'sidebar_title'):
            self.update_sidebar_title()

    def update_sidebar_title(self):
        """Update sidebar title colors for current theme"""
        colors = self.theme_manager.get_theme_config()["colors"]
        self.sidebar_title.configure(
            foreground=colors["text"],
            background=colors["sidebar"]
        )

    def get_current_tab(self):
        """Get the currently active tab"""
        for tab_id, frame in self.tab_frames.items():
            if frame.winfo_ismapped():
                return tab_id
        return "get"  # default

    def update_session_info(self):
        """Update session info display every minute"""
        try:
            from shared.user_session import user_session
            
            # Check if session is still valid and widget exists
            if (user_session.is_logged_in and 
                hasattr(self, 'user_info_label') and 
                self.user_info_label and
                self.user_info_label.winfo_exists()):
                
                session_duration = user_session.session_duration or "00:00"
                role_icon = "👑" if user_session.is_admin else "👤"
                role_text = user_session.role.title()
                user_info_text = f"{role_icon} {user_session.username} ({role_text}) | ⏱️ {session_duration}"
                color = "purple" if user_session.is_admin else "darkgreen"
                
                # Safely update the label
                self.user_info_label.config(text=user_info_text, foreground=color)
                
                # Schedule next update in 60 seconds
                self.root.after(60000, self.update_session_info)
            else:
                # Session ended or widget destroyed, stop updating
                logger.debug("Session ended or widget destroyed, stopping session updates")
                
        except tk.TclError as e:
            # Widget has been destroyed
            logger.debug(f"Widget destroyed during session update: {e}")
        except Exception as e:
            logger.debug(f"Error updating session info: {e}")
    
    # --- Help menu handlers ---
    def open_documentation(self):
        """Open project documentation (README) in the default browser"""
        try:
            url = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}#readme"
            webbrowser.open(url)
        except Exception as e:
            messagebox.showinfo("Help", f"Open documentation at: https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}\nError: {e}")

    def show_about_dialog(self):
        """Show About dialog with version details"""
        try:
            info = get_version_info()
            msg = (
                "Feature Flag Manager\n"
                f"Version: {info.get('version', '')}\n"
                f"Build Date: {info.get('build_date', '')}\n"
                f"Author: {info.get('author', '')}"
            )
            messagebox.showinfo("About", msg)
        except Exception as e:
            messagebox.showerror("About", f"Unable to load version info: {e}")
    
    def logout(self):
        """Logout and return to login screen with session cleanup"""
        from shared.user_session import user_session
        
        # Stop any scheduled session updates by clearing reference
        try:
            if hasattr(self, 'user_info_label'):
                self.user_info_label = None
                logger.debug("Cleared user_info_label reference during logout")
        except Exception as e:
            logger.debug(f"Error during logout cleanup: {e}")
        
        # Clear user session
        user_session.logout()
        
        # Destroy all widgets in the main window
        for widget in self.root.winfo_children():
            widget.destroy()

        # Change theme back to superhero for login
        style = ttk.Style()
        style.theme_use("superhero")

        # Re-initialize the LoginWindow
        from ui.login_window import LoginWindow
        LoginWindow(self.root) 