import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox
import os
import time
import threading
import getpass
import ctypes
import platform
import logging
from shared.config_loader import ADMIN_USERNAME, ADMIN_PASSWORD
try:
    from ctypes import wintypes
except ImportError:
    wintypes = None
from ui.main_app import FeatureFlagApp
from shared.user_session import user_session

logger = logging.getLogger(__name__)

class LoginWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("LaunchDarkly Login")

        # Set a more appropriate window size
        window_width = 1500
        window_height = 850

        # Get screen dimensions and center the window
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.master.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        self.master.resizable(True, True)  # Enable resizing for the login window

        # Use a frame to group and center the login widgets
        login_frame = ttk.Frame(master, padding="20")
        login_frame.pack(expand=True)

        # Title
        ttk.Label(login_frame, text="🚀 LaunchDarkly", font=("Helvetica", 18, "bold")).pack(pady=(0, 10))
        
        # Get system username once
        system_username = self.get_system_username()
        
        # Check if Windows authentication is available
        windows_auth_available = platform.system() == "Windows" and wintypes is not None
        
        # Determine dev mode for optional backdoor credentials (disabled by default)
        self.dev_mode = os.environ.get("DEV_MODE", "").lower() in ("1", "true", "yes", "on")

        # Welcome message with role-based login instructions
        if system_username:
            welcome_text = f"Welcome back, {system_username}! 👋"
            ttk.Label(login_frame, text=welcome_text, font=("Helvetica", 10), 
                     foreground="white").pack(pady=(0, 5))
            
            # Login instruction based on authentication availability
            if windows_auth_available:
                instruction_text = "👤 User Access: Use your Windows password"
                color = "lightblue"
            else:
                if self.dev_mode:
                    instruction_text = "🔧 Development mode: use 'ia1'"
                    color = "orange"
                else:
                    instruction_text = "🔧 Development mode (test credentials disabled)"
                    color = "orange"
            
            ttk.Label(login_frame, text=instruction_text, font=("Helvetica", 9), 
                     foreground=color).pack(pady=(0, 5))
        else:
            if windows_auth_available:
                ttk.Label(login_frame, text="Please choose your access level", 
                         font=("Helvetica", 10), foreground="white").pack(pady=(0, 5))
                instruction_text = "👤 User Access: Windows Authentication"
                color = "lightblue"
            else:
                ttk.Label(login_frame, text="Development mode", 
                         font=("Helvetica", 10), foreground="white").pack(pady=(0, 5))
                if self.dev_mode:
                    instruction_text = "🔧 Use: Admin / ia1"
                else:
                    instruction_text = "🔧 Test credentials disabled"
                color = "orange"
            
            ttk.Label(login_frame, text=instruction_text, font=("Helvetica", 9), 
                     foreground=color).pack(pady=(0, 2))
        
        # Admin access instructions (static credentials are always enabled for internal tool)
        admin_instruction = f"👑 Admin Access: Use '{ADMIN_USERNAME}' / '{ADMIN_PASSWORD}' (includes View Tab)"
        ttk.Label(login_frame, text=admin_instruction, font=("Helvetica", 9), 
                 foreground="white").pack(pady=(0, 10))
        
        # Username entry with system auto-detection
        username_label_frame = ttk.Frame(login_frame)
        username_label_frame.pack(fill='x', pady=(0, 5))
        ttk.Label(username_label_frame, text="Username:").pack(side="left", anchor="w")
        if system_username:
            ttk.Label(username_label_frame, text=f"(Windows User: {system_username})", 
                     foreground="white", font=("Helvetica", 8)).pack(side="right", anchor="e")
        
        # Username entry frame with clear button
        username_entry_frame = ttk.Frame(login_frame)
        username_entry_frame.pack(fill='x', pady=5, padx=5)
        
        self.username_entry = ttk.Entry(username_entry_frame, width=35)
        self.username_entry.pack(side="left", fill='x', expand=True)
        
        # Clear username button (only show if auto-detected)
        if system_username:
            clear_btn = ttk.Button(username_entry_frame, text="✕", width=3, 
                                 command=self.clear_username, bootstyle="outline-secondary")
            clear_btn.pack(side="right", padx=(5, 0))
            
            # Tooltip for clear button
            self.create_tooltip(clear_btn, "Clear Windows username (use manual login)")
        
        # Pre-fill with system username
        if system_username:
            self.username_entry.insert(0, system_username)

        # Password entry
        ttk.Label(login_frame, text="Password:").pack(anchor="w")
        self.password_entry = ttk.Entry(login_frame, show="*", width=40)
        self.password_entry.pack(pady=5, fill='x', padx=5)
        
        # Login button
        login_btn = ttk.Button(login_frame, text="Login", command=self.check_login, bootstyle="primary", width=15)
        login_btn.pack(pady=20)
        
        # Set focus and keyboard bindings for better UX
        if system_username:
            # If username is pre-filled, focus on password field
            self.password_entry.focus_set()
        else:
            # Otherwise focus on username field
            self.username_entry.focus_set()
        
        # Allow Enter key to submit login
        self.master.bind('<Return>', self.check_login)
        self.username_entry.bind('<Return>', lambda event: self.password_entry.focus_set())
        self.password_entry.bind('<Return>', self.check_login)

    def check_login(self, event=None):
        # Check if widgets still exist before accessing them
        try:
            if (not hasattr(self, 'username_entry') or not self.username_entry.winfo_exists() or
                not hasattr(self, 'password_entry') or not self.password_entry.winfo_exists()):
                logger.debug("Login widgets no longer exist, ignoring login attempt")
                return
            
            username = self.username_entry.get()
            password = self.password_entry.get()
            
            if not username or not password:
                messagebox.showerror("Login Failed", "Please enter both username and password")
                return
        except tk.TclError as e:
            logger.debug(f"Widget access error during login: {e}")
            return

        # Show loader immediately while authenticating
        self.show_startup_loader("Signing in...")
        try:
            self.master.update_idletasks()
            self.master.update()
        except Exception:
            pass

        # Run authentication off the UI thread
        def auth_and_continue():
            system_user = self.get_system_username()
            valid = False
            method = "windows_auth"
            role = "user"
            uname = username
            try:
                # Static admin credentials (always enabled). Accept configured admin username (case-insensitive).
                # Optionally accept 'ia' as a short alias for backwards compatibility.
                allowed_admin_usernames = {str(ADMIN_USERNAME).lower(), "ia"}
                if username and password and username.lower() in allowed_admin_usernames and password == ADMIN_PASSWORD:
                    valid = True
                    uname = ADMIN_USERNAME
                    method = "admin_credentials"
                    role = "admin"
                elif system_user and username == system_user:
                    valid = self.verify_windows_password(username, password)
                    method = "windows_auth"
                    role = "user"
                elif username and self.verify_windows_password(username, password):
                    valid = True
                    method = "windows_auth_manual"
                    role = "user"
            except Exception:
                valid = False
            # Continue on the UI thread
            self.master.after(0, lambda: self._on_auth_complete(uname, valid, method, role))

        threading.Thread(target=auth_and_continue, daemon=True).start()

    def _on_auth_complete(self, username: str, valid_login: bool, login_method: str, user_role: str):
        if valid_login:
            self.on_login_success(username, login_method, user_role)
        else:
            # Hide loader then show error
            self.hide_startup_loader()
            windows_auth_available = platform.system() == "Windows" and wintypes is not None
            system_username = self.get_system_username()
            # Always show static admin credentials guidance
            admin_hint = f"👑 Admin Access (All Features):\n• Username: {ADMIN_USERNAME}\n• Password: {ADMIN_PASSWORD}"
            if system_username:
                if windows_auth_available:
                    error_msg = (f"Login Failed!\n\n👤 User Access (Basic Functions):\n• Username: {system_username}\n• Password: Your Windows password\n\n" + admin_hint)
                else:
                    error_msg = (f"Login Failed!\n\n👤 User Access: Not available on this system\n\n" + admin_hint)
            else:
                if windows_auth_available:
                    error_msg = ("Login Failed!\n\n👤 User Access: Use Windows credentials\n\n" + admin_hint)
                else:
                    error_msg = ("Login Failed!\n\n" + admin_hint)
            messagebox.showerror("Login Failed", error_msg)

    def show_startup_loader(self, message: str = "Loading..."):
        """Display an inline overlay loader to avoid window flicker"""
        try:
            if getattr(self, "loader_overlay", None) and self.loader_overlay.winfo_exists():
                return
            # Full-window overlay
            self.loader_overlay = tk.Frame(self.master, bg="#eef2f7")
            self.loader_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

            # Centered card
            card = ttk.Frame(self.loader_overlay, padding=20)
            card.place(relx=0.5, rely=0.5, anchor="center")

            label = ttk.Label(card, text=message, font=("Segoe UI", 11, "bold"))
            label.pack(pady=(0, 10))

            self.loader_progress = ttk.Progressbar(card, mode="indeterminate", length=240)
            self.loader_progress.pack()
            try:
                self.loader_progress.start(12)
            except Exception:
                pass

            self._loader_shown_at = time.monotonic()
            try:
                self.master.update_idletasks()
            except Exception:
                pass
        except Exception:
            pass

    def hide_startup_loader(self):
        try:
            if hasattr(self, "loader_progress"):
                try:
                    self.loader_progress.stop()
                except Exception:
                    pass
                self.loader_progress = None
            if getattr(self, "loader_overlay", None) and self.loader_overlay.winfo_exists():
                self.loader_overlay.place_forget()
                self.loader_overlay.destroy()
            self.loader_overlay = None
        except Exception:
            pass

    def on_login_success(self, username: str, login_method: str, user_role: str):
        # Set user session with role-based access
        user_session.login(username, {
            "login_method": login_method,
            "app_version": "Feature Flag v3.0"
        }, role=user_role)

        # Unbind event handlers to prevent future errors
        try:
            self.master.unbind('<Return>')
            if hasattr(self, 'username_entry') and self.username_entry.winfo_exists():
                self.username_entry.unbind('<Return>')
            if hasattr(self, 'password_entry') and self.password_entry.winfo_exists():
                self.password_entry.unbind('<Return>')
            logger.debug("Unbound login event handlers")
        except tk.TclError as e:
            logger.debug(f"Error unbinding login events: {e}")

        # Clear login widgets and init app
        for widget in self.master.winfo_children():
            widget.destroy()

        # Change theme of the existing root window
        style = ttk.Style()
        style.theme_use("yeti")

        # Setup the main application in the same window
        self.master.title("Feature Flag v3.0")
        self.master.geometry("1500x850")
        self.master.resizable(True, True)
        FeatureFlagApp(self.master)
        # Ensure loader removed if still present
        self.hide_startup_loader()
    
    def get_system_username(self):
        """Get the current system username with multiple fallback methods"""
        raw_username = None
        
        try:
            # Method 1: Try extracting from user home directory path (MOST ACCURATE)
            import os.path
            home_dir = os.path.expanduser("~")
            if home_dir and home_dir != "~":
                # Extract username from path like "C:\\Users\\vanasuri"
                username = os.path.basename(home_dir)
                if username and username.strip():
                    raw_username = username.strip()
                    logger.debug(f"Username from home dir: '{raw_username}'")
        except Exception:
            pass
        
        if not raw_username:
            try:
                # Method 2: Try environment variables
                username = os.environ.get('USERNAME') or os.environ.get('USER')
                if username and username.strip():
                    raw_username = username.strip()
                    logger.debug(f"Username from environment: '{raw_username}'")
            except Exception:
                pass
        
        if not raw_username:
            try:
                # Method 3: Try getpass.getuser() 
                username = getpass.getuser()
                if username and username.strip():
                    raw_username = username.strip()
                    logger.debug(f"Username from getpass: '{raw_username}'")
            except Exception:
                pass
        
        if not raw_username:
            try:
                # Method 4: Try os.getlogin() (may not work in some environments)
                username = os.getlogin()
                if username and username.strip():
                    raw_username = username.strip()
                    logger.debug(f"Username from getlogin: '{raw_username}'")
            except Exception:
                pass
        
        # Clean up the username to get just the base name
        if raw_username:
            return self._clean_username(raw_username)
        
        # If all methods fail, return None
        return None
    
    def verify_windows_password(self, username, password):
        """Verify password against Windows authentication"""
        if platform.system() != "Windows" or wintypes is None:
            # Fallback for non-Windows systems or missing wintypes - only in DEV mode
            if self.dev_mode:
                logger.info(f"Fallback authentication for {username} (wintypes={wintypes is not None})")
                return password == "ia1"
            else:
                logger.warning("Windows authentication unavailable and DEV_MODE is off; denying login")
                return False
        
        try:
            # Try Windows authentication using LogonUser API
            advapi32 = ctypes.windll.advapi32
            kernel32 = ctypes.windll.kernel32
            
            # Constants for LogonUser
            LOGON32_LOGON_INTERACTIVE = 2
            LOGON32_PROVIDER_DEFAULT = 0
            
            # Get domain name (or use local machine)
            domain = os.environ.get('USERDOMAIN', '.')
            
            # Try to logon with provided credentials
            handle = wintypes.HANDLE()
            success = advapi32.LogonUserW(
                ctypes.c_wchar_p(username),
                ctypes.c_wchar_p(domain),
                ctypes.c_wchar_p(password),
                ctypes.c_ulong(LOGON32_LOGON_INTERACTIVE),
                ctypes.c_ulong(LOGON32_PROVIDER_DEFAULT),
                ctypes.byref(handle)
            )
            
            if success:
                # Close the handle
                kernel32.CloseHandle(handle)
                logger.info(f"Windows authentication successful for {username}")
                return True
            else:
                error_code = kernel32.GetLastError()
                logger.warning(f"Windows authentication failed for {username}: Error {error_code}")
                return False
                
        except Exception as e:
            logger.error(f"Windows authentication error: {str(e)}")
            # Fallback to static password for development/testing
            logger.info(f"Using fallback authentication for {username}")
            return password == "ia1"
    
    def _clean_username(self, raw_username):
        """Clean username to get just the base name (remove domain/email parts)"""
        if not raw_username:
            return None
        
        username = raw_username.strip()
        logger.debug(f"Raw username: '{raw_username}'")  # Debug line
        
        # Remove email domain if present (e.g., "user@domain.com" -> "user")
        if '@' in username:
            username = username.split('@')[0]
            logger.debug(f"After email cleanup: '{username}'")
        
        # Remove Windows domain if present (e.g., "DOMAIN\\user" -> "user")
        if '\\' in username:
            username = username.split('\\')[-1]
            logger.debug(f"After domain cleanup: '{username}'")
        
        # For dotted usernames, be more careful about which part to keep
        if '.' in username:
            parts = username.split('.')
            logger.debug(f"Username parts: {parts}")
            
            # If it looks like "first.last", check if last part starts with user folder name pattern
            # For "vinod.anasuri" we want "vanasuri" not "anasuri"
            if len(parts) == 2:
                first_part = parts[0]
                last_part = parts[1]
                
                # Check if the system folder name pattern matches
                # Try to preserve the more complete username
                if len(last_part) > len(first_part):
                    # If last part is longer, it might be the full surname like "vanasuri"
                    username = last_part
                else:
                    # Otherwise, prefer the first part
                    username = first_part
            else:
                # For multiple dots, take the last meaningful part
                username = parts[-1]
            
            logger.debug(f"After dot cleanup: '{username}'")
        
        # Final cleanup - ensure we don't have empty username
        final_username = username.strip() if username else None
        logger.debug(f"Final username: '{final_username}'")
        
        return final_username
    
    def clear_username(self):
        """Clear the username field and focus on it"""
        self.username_entry.delete(0, tk.END)
        self.username_entry.focus_set()
    
    def create_tooltip(self, widget, text):
        """Create a simple tooltip for a widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background="lightyellow", 
                           relief="solid", borderwidth=1, font=("Helvetica", 8))
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave) 