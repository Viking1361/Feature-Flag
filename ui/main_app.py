import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox
import os
import webbrowser
import logging
import json
from datetime import datetime, timezone, timedelta

from version import get_version_info, GITHUB_OWNER, GITHUB_REPO
from utils.auto_updater import get_updater
from shared.config_loader import (
    LOG_FILE,
    AUDIT_FILE,
    DAILY_SUMMARY_ENABLED,
    DAILY_SUMMARY_EVENT_TYPES,
    DAILY_SUMMARY_OK_ONLY,
    WHATS_NEW_ON_UPDATE_ENABLED,
)

# Import utility managers
from utils.theme_manager import ThemeManager
from utils.history_manager import HistoryManager
from utils.settings_manager import SettingsManager

# Import tab modules
from ui.tabs.get_tab import GetTab
from ui.tabs.update_tab import UpdateTab
from ui.tabs.create_tab import CreateTab
from ui.tabs.enhanced_view_tab import EnhancedViewTab as ViewTab
from ui.tabs.notifications_tab import NotificationsTab
from ui.tabs.log_tab import LogTab
from ui.tabs.history_tab import HistoryTab

# Module logger for this UI module
logger = logging.getLogger(__name__)

class FeatureFlagApp:
    def __init__(self, root):
        self.root = root
        # Guard to prevent duplicate daily summary popups
        self._daily_summary_shown = False
        # Guard to prevent duplicate What's New popups
        self._whats_new_shown = False
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
        self.settings_manager = SettingsManager()
        
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
        help_menu.add_command(label="Show Today's Summary", command=self.show_summary_for_today)
        help_menu.add_command(label="View What's New for Current Version", command=self.show_whats_new_current)
        help_menu.add_command(label="Documentation", command=self.open_documentation)
        help_menu.add_separator()
        try:
            initial_show = bool(self.settings_manager.get("help", "show_help_icons"))
        except Exception:
            initial_show = True
        self.help_icons_var = tk.BooleanVar(value=initial_show)
        help_menu.add_checkbutton(label="Show Help Icons", variable=self.help_icons_var, command=self.on_toggle_help_icons)
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
            text=" 2024 Feature Flag Management System", 
            font=("Segoe UI", 9),
            foreground=self.theme_manager.get_theme_config()["colors"]["text_secondary"]
        )
        copyright_label.pack(side="right")
        
        # End of UI setup
        # Show a daily summary popup the first time the app is used today (if enabled)
        try:
            if DAILY_SUMMARY_ENABLED:
                # Slight delay so the main window is drawn first
                self.root.after(800, self.maybe_show_daily_summary)
        except Exception:
            pass
        # Show What's New after update (first launch on new version)
        try:
            if WHATS_NEW_ON_UPDATE_ENABLED:
                self.root.after(1200, self.maybe_show_whats_new)
        except Exception:
            pass

    def create_vertical_tabs(self, parent):
        """Create vertical tab layout"""
        # Create main container with vertical layout
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True)

        # Left panel for tab buttons
        self.tab_buttons_frame = ttk.Frame(container, width=220, style="Sidebar.TFrame")
        self.tab_buttons_frame.pack(side="left", fill="y", padx=(0, 15))
        self.tab_buttons_frame.pack_propagate(False)  # Maintain fixed width

        # Right panel for tab content (scrollable)
        # Outer container holds the canvas + scrollbar
        self.content_frame_container = ttk.Frame(container, style="Content.TFrame")
        self.content_frame_container.pack(side="right", fill="both", expand=True)

        # Canvas for scrolling and a vertical scrollbar
        colors = self.theme_manager.get_theme_config()["colors"]
        self.content_canvas = tk.Canvas(
            self.content_frame_container,
            highlightthickness=0,
            bd=0,
            bg=colors.get("background", "white"),
        )
        self.content_vscroll = ttk.Scrollbar(
            self.content_frame_container, orient="vertical", command=self.content_canvas.yview
        )
        self.content_canvas.configure(yscrollcommand=self.content_vscroll.set)
        self.content_canvas.pack(side="left", fill="both", expand=True)
        self.content_vscroll.pack(side="right", fill="y")

        # Inner frame that actually holds tab content frames
        self.content_frame = ttk.Frame(self.content_canvas, style="Content.TFrame")
        self._canvas_window = self.content_canvas.create_window((0, 0), window=self.content_frame, anchor="nw")

        # Keep scrollregion and width in sync
        def _on_inner_configure(event=None):
            try:
                self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all"))
            except Exception:
                pass

        def _on_canvas_configure(event):
            try:
                # Make the inner frame width match the visible canvas width
                self.content_canvas.itemconfig(self._canvas_window, width=event.width)
            except Exception:
                pass

        self.content_frame.bind("<Configure>", _on_inner_configure)
        self.content_canvas.bind("<Configure>", _on_canvas_configure)

        # Mouse wheel support (Windows)
        def _on_mousewheel(event):
            try:
                # If hovering a widget that handles its own vertical scroll, let it handle it
                cls = str(getattr(event.widget, 'winfo_class', lambda: '')())
                if cls in ("Text", "Treeview", "Listbox"):
                    return
                self.content_canvas.yview_scroll(-int(event.delta/120), "units")
            except Exception:
                pass

        def _bind_wheel(_event=None):
            try:
                self.content_canvas.bind_all("<MouseWheel>", _on_mousewheel)
            except Exception:
                pass

        def _unbind_wheel(_event=None):
            try:
                self.content_canvas.unbind_all("<MouseWheel>")
            except Exception:
                pass

        self.content_frame.bind("<Enter>", _bind_wheel)
        self.content_frame.bind("<Leave>", _unbind_wheel)

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
            ("history", "Flag History", "🕘", "get_flag"),
            ("notifications", "Notifications", "🔔", "get_flag"),
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
        if "notifications" in available_tab_ids:
            self.tab_instances["notifications"] = NotificationsTab(self.tab_frames["notifications"], self.history_manager, self.theme_manager)
        if "history" in available_tab_ids:
            self.tab_instances["history"] = HistoryTab(self.tab_frames["history"], self.history_manager, self.theme_manager)

        # Apply initial help icon visibility after tabs are created
        try:
            self.update_help_icons_visibility()
        except Exception:
            pass

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

        # Reset scroll to top when switching tabs
        try:
            if hasattr(self, "content_canvas"):
                self.content_canvas.yview_moveto(0)
                # Ensure scrollregion is up-to-date
                self.content_canvas.update_idletasks()
                self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all"))
        except Exception:
            pass

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
        # Update scrollable content canvas bg
        try:
            if hasattr(self, 'content_canvas') and self.content_canvas:
                self.content_canvas.configure(bg=colors.get("background", "white"))
        except Exception:
            pass
        
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

    def on_toggle_help_icons(self):
        try:
            val = bool(self.help_icons_var.get())
        except Exception:
            val = True
        try:
            self.settings_manager.set("help", "show_help_icons", val)
            self.settings_manager.save_settings()
        except Exception:
            pass
        try:
            self.update_help_icons_visibility()
        except Exception:
            pass

    def update_help_icons_visibility(self):
        try:
            val = bool(self.help_icons_var.get())
        except Exception:
            val = True
        try:
            for tab in (self.tab_instances or {}).values():
                if hasattr(tab, "set_help_icons_visible"):
                    tab.set_help_icons_visible(val)
        except Exception:
            pass

    # --- Daily summary (first run of the day) ---
    def maybe_show_daily_summary(self):
        """If this is the first app use today, show a popup summarizing today's changes
        based on the audit/notifications JSONL file.
        """
        try:
            # Instance-level guard: if already shown in this process, skip
            if getattr(self, "_daily_summary_shown", False):
                return
            self._daily_summary_shown = True
            # Determine sentinel path next to the audit file
            base_dir = os.path.dirname(os.path.abspath(AUDIT_FILE)) if AUDIT_FILE else os.getcwd()
            sentinel = os.path.join(base_dir, "last_summary_date.txt")

            today_local = datetime.now().date().isoformat()
            # If already shown today, skip
            try:
                if os.path.exists(sentinel):
                    with open(sentinel, "r", encoding="utf-8") as f:
                        last = (f.read() or "").strip()
                    if last == today_local:
                        return
            except Exception:
                pass

            # Build summary for yesterday's audit entries (show on first open today)
            target_date = datetime.now().date() - timedelta(days=1)
            summary_text, found_count = self._build_summary_for_date(target_date)
            if summary_text is None:
                # No audit file or no entries; still write sentinel to avoid repeated popups
                try:
                    with open(sentinel, "w", encoding="utf-8") as f:
                        f.write(today_local)
                except Exception:
                    pass
                return

            # To avoid race where two after-calls run before sentinel is written,
            # write the sentinel BEFORE showing the messagebox.
            try:
                with open(sentinel, "w", encoding="utf-8") as f:
                    f.write(today_local)
            except Exception:
                pass

            # Show popup only if we have relevant info (or always show with "No changes")
            try:
                messagebox.showinfo(
                    "Daily Summary",
                    summary_text,
                    parent=self.root,
                )
            finally:
                # Write sentinel so we don't show again today
                try:
                    with open(sentinel, "w", encoding="utf-8") as f:
                        f.write(today_local)
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"daily summary failed: {e}")

    # --- What's New (first run after update) ---
    def maybe_show_whats_new(self):
        try:
            if getattr(self, "_whats_new_shown", False):
                return
            self._whats_new_shown = True

            if not WHATS_NEW_ON_UPDATE_ENABLED:
                return

            info = get_version_info()
            current_ver = str(info.get("version", "")).strip()
            if not current_ver:
                return

            updater = get_updater(self.root)
            last_seen = (getattr(updater, "settings", {}) or {}).get("last_seen_version")
            if last_seen == current_ver:
                return

            # Persist last seen before showing to avoid duplicate popups
            try:
                updater.settings["last_seen_version"] = current_ver
                updater.save_settings()
            except Exception:
                pass

            # Fetch release notes for current version
            rn = None
            try:
                rn = updater.get_release_notes_for_version(current_ver)
            except Exception:
                rn = None

            notes = (rn.get("body") if rn else "") or "No release notes available."
            self._open_whats_new_dialog(current_ver, notes)

        except Exception as e:
            try:
                logger.debug(f"whats new failed: {e}")
            except Exception:
                pass

    def _open_whats_new_dialog(self, version: str, notes: str):
        """Reusable dialog to show What's New for the given version."""
        url = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/tag/v{version}"

        dialog = tk.Toplevel(self.root)
        dialog.title(f"What's New - v{version}")
        dialog.geometry("560x420")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        try:
            dialog.grab_set()
        except Exception:
            pass
        # Center dialog
        try:
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (560 // 2)
            y = (dialog.winfo_screenheight() // 2) - (420 // 2)
            dialog.geometry(f"560x420+{x}+{y}")
        except Exception:
            pass

        main = tk.Frame(dialog, padx=16, pady=16)
        main.pack(fill="both", expand=True)

        title = tk.Label(main, text=f"What's New in v{version}", font=("Segoe UI", 14, "bold"))
        title.pack(anchor="w", pady=(0, 8))

        notes_frame = tk.Frame(main)
        notes_frame.pack(fill="both", expand=True)
        txt = tk.Text(notes_frame, wrap="word", font=("Segoe UI", 10))
        sb = tk.Scrollbar(notes_frame, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        txt.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        try:
            txt.insert("1.0", notes)
            txt.config(state="disabled")
        except Exception:
            pass

        btns = tk.Frame(main)
        btns.pack(fill="x", pady=(10, 0))

        def open_release():
            try:
                webbrowser.open(url)
            except Exception:
                pass

        link_btn = tk.Button(btns, text="Open Release Notes", command=open_release)
        link_btn.pack(side="right", padx=(8, 0))
        ok_btn = tk.Button(btns, text="OK", command=dialog.destroy)
        ok_btn.pack(side="right")

    def show_whats_new_current(self):
        """Help menu action: View What's New for the current version on demand."""
        try:
            info = get_version_info()
            current_ver = str(info.get("version", "")).strip()
            if not current_ver:
                return
            updater = get_updater(self.root)
            rn = updater.get_release_notes_for_version(current_ver)
            notes = (rn.get("body") if rn else "") or "No release notes available."
            self._open_whats_new_dialog(current_ver, notes)
        except Exception as e:
            try:
                messagebox.showinfo("What's New", f"Unable to load release notes: {e}", parent=self.root)
            except Exception:
                pass

    def _build_today_summary_text(self):
        """Read AUDIT_FILE and build a human-friendly summary for today's changes.
        Returns (text, count) or (None, 0) if not available.
        """
        try:
            path = AUDIT_FILE
            if not path or not os.path.exists(path):
                return None, 0

            # Load entries
            entries = []
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = (line or "").strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        entries.append(obj)
                    except Exception:
                        continue

            if not entries:
                return None, 0

            # Filter today's entries in local time
            def _parse_ts(ts: str):
                try:
                    s = str(ts or "")
                    if not s:
                        return None
                    if s.endswith("Z"):
                        return datetime.fromisoformat(s.replace("Z", "+00:00"))
                    return datetime.fromisoformat(s)
                except Exception:
                    return None

            today_date = datetime.now().date()
            today_entries = []
            for e in entries:
                dt = _parse_ts(e.get("ts"))
                if not dt:
                    continue
                try:
                    local_dt = dt.astimezone()
                except Exception:
                    # dt may be naive; treat as UTC
                    local_dt = dt.replace(tzinfo=timezone.utc).astimezone()
                if local_dt.date() == today_date:
                    today_entries.append((local_dt, e))

            # Build counts and recent list
            if not today_entries:
                text = (
                    f"No changes recorded today (as of {datetime.now().strftime('%H:%M')}).\n\n"
                    f"Audit file: {os.path.abspath(path)}"
                )
                return text, 0

            # Keep updates only (exclude read-only events)
            exclude_types = {"get_flag"}
            updates = [(dt, e) for dt, e in today_entries if str(e.get("type", "")) not in exclude_types]
            # Apply configured event type filter, if set
            try:
                allowed = {t.strip() for t in str(DAILY_SUMMARY_EVENT_TYPES or "").split(",") if t.strip()}
            except Exception:
                allowed = set()
            if allowed:
                updates = [(dt, e) for dt, e in updates if str(e.get("type", "")) in allowed]
            # Apply ok-only filter if enabled
            if DAILY_SUMMARY_OK_ONLY:
                updates = [(dt, e) for dt, e in updates if bool(e.get("ok", True))]

            # Counts by type
            counts = {}
            for _, e in updates:
                t = str(e.get("type", ""))
                counts[t] = counts.get(t, 0) + 1

            # Sort descending by time and take last 10
            updates.sort(key=lambda x: x[0], reverse=True)
            recent = updates[:10]

            # Build lines
            lines = []
            for dt, e in recent:
                hhmm = dt.strftime("%H:%M")
                key = e.get("feature_key") or e.get("key") or ""
                env = e.get("environment", "")
                summary = self._summary_line(e)
                if not summary:
                    summary = str(e.get("summary", "")).strip()
                if not summary:
                    # fallback generic
                    enabled = e.get("enabled")
                    summary = f"{e.get('type','')} enabled={'True' if enabled else 'False'}"
                lines.append(f"[{hhmm}] {key} {('@'+env) if env else ''} - {summary}")

            # Counts lines
            count_lines = [f"- {k}: {v}" for k, v in sorted(counts.items())]
            total = sum(counts.values())
            header = f"Daily changes summary for {today_date.isoformat()}\n\n"
            body_counts = "Total updates: " + str(total) + ("\n" + "\n".join(count_lines) if count_lines else "")
            body_recent = "\n\nRecent changes (latest 10):\n" + ("\n".join(lines) if lines else "- None")
            footer = f"\n\nAudit file: {os.path.abspath(path)}"
            return header + body_counts + body_recent + footer, total
        except Exception as e:
            logger.debug(f"build_today_summary_text failed: {e}")
            return None, 0

    def _build_summary_for_date(self, target_date):
        """Build a human-friendly summary for the given local date (yyyy-mm-dd)."""
        try:
            path = AUDIT_FILE
            if not path or not os.path.exists(path):
                return None, 0

            # Load entries
            entries = []
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = (line or "").strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        entries.append(obj)
                    except Exception:
                        continue

            if not entries:
                return None, 0

            def _parse_ts(ts: str):
                try:
                    s = str(ts or "")
                    if not s:
                        return None
                    if s.endswith("Z"):
                        return datetime.fromisoformat(s.replace("Z", "+00:00"))
                    return datetime.fromisoformat(s)
                except Exception:
                    return None

            # Filter entries matching target_date in local time
            selected = []
            for e in entries:
                dt = _parse_ts(e.get("ts"))
                if not dt:
                    continue
                try:
                    local_dt = dt.astimezone()
                except Exception:
                    local_dt = dt.replace(tzinfo=timezone.utc).astimezone()
                if local_dt.date() == target_date:
                    selected.append((local_dt, e))

            if not selected:
                text = (
                    f"No changes recorded on {target_date.isoformat()} as of {datetime.now().strftime('%H:%M')}\n\n"
                    f"Audit file: {os.path.abspath(path)}"
                )
                return text, 0

            # Exclude read-only event types
            exclude_types = {"get_flag"}
            updates = [(dt, e) for dt, e in selected if str(e.get("type", "")) not in exclude_types]
            # Apply configured event type filter, if set
            try:
                allowed = {t.strip() for t in str(DAILY_SUMMARY_EVENT_TYPES or "").split(",") if t.strip()}
            except Exception:
                allowed = set()
            if allowed:
                updates = [(dt, e) for dt, e in updates if str(e.get("type", "")) in allowed]
            # Apply ok-only filter if enabled
            if DAILY_SUMMARY_OK_ONLY:
                updates = [(dt, e) for dt, e in updates if bool(e.get("ok", True))]

            counts = {}
            for _, e in updates:
                t = str(e.get("type", ""))
                counts[t] = counts.get(t, 0) + 1

            updates.sort(key=lambda x: x[0], reverse=True)
            recent = updates[:10]

            lines = []
            for dt, e in recent:
                hhmm = dt.strftime("%H:%M")
                key = e.get("feature_key") or e.get("key") or ""
                env = e.get("environment", "")
                summary = self._summary_line(e) or str(e.get("summary", "")).strip()
                if not summary:
                    enabled = e.get("enabled")
                    summary = f"{e.get('type','')} enabled={'True' if enabled else 'False'}"
                lines.append(f"[{hhmm}] {key} {('@'+env) if env else ''} - {summary}")

            count_lines = [f"- {k}: {v}" for k, v in sorted(counts.items())]
            total = sum(counts.values())
            header = f"Daily changes summary for {target_date.isoformat()}\n\n"
            body_counts = "Total updates: " + str(total) + ("\n" + "\n".join(count_lines) if count_lines else "")
            body_recent = "\n\nRecent changes (latest 10):\n" + ("\n".join(lines) if lines else "- None")
            footer = f"\n\nAudit file: {os.path.abspath(path)}"
            return header + body_counts + body_recent + footer, total
        except Exception as e:
            logger.debug(f"build_summary_for_date failed: {e}")
            return None, 0

    def _summary_line(self, e: dict) -> str:
        """Return a one-line summary for a single audit event (shared logic)."""
        try:
            etype = str(e.get("type", "")).strip()
            enabled_val = e.get("enabled")
            key = e.get("feature_key") or e.get("key") or ""
            env = e.get("environment", "")
            if etype == "pmc_targeting_update":
                pmc = str(e.get("pmc_id", "")).strip()
                action = "enabled" if enabled_val else "disabled"
                return f"PMC {pmc} {action}"
            if etype == "default_rule_update":
                if enabled_val is True:
                    return "Default rule set to True"
                if enabled_val is False:
                    return "Default rule set to False"
                return "Default rule updated"
            if etype == "feature_flag_change":
                return f"Toggled {'ON' if enabled_val else 'OFF'}"
            if etype == "update_flag":
                return f"Update flag enabled={'True' if enabled_val else 'False'}"
            if etype == "create_flag":
                return "Created flag"
            return ""
        except Exception:
            return ""

    # --- Menu handler: Show Today's Summary ---
    def show_summary_for_today(self):
        try:
            text, count = self._build_summary_for_date(datetime.now().date())
            if not text:
                text = "No changes recorded today."
            messagebox.showinfo("Today's Summary", text, parent=self.root)
        except Exception as e:
            try:
                messagebox.showinfo("Today's Summary", f"Unable to build summary: {e}", parent=self.root)
            except Exception:
                pass

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