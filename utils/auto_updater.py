"""
Auto-updater module for Feature Flag Manager executable
Handles version checking, downloading, and installing updates
"""

import os
import sys
import json
import time
import requests
import threading
import subprocess
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import logging

from version import __version__, UPDATE_CHECK_URL, UPDATE_DOWNLOAD_URL, UPDATE_CHECK_INTERVAL
from shared.config_loader import GITHUB_TOKEN

logger = logging.getLogger(__name__)

def _log_token_status():
    """Log whether a GitHub token is present (do not print the token)."""
    try:
        present = bool(GITHUB_TOKEN)
        length = len(GITHUB_TOKEN) if present else 0
        logger.info(f"Updater: token_present={present} token_length={length}")
    except Exception:
        logger.info("Updater: token_present=unknown")

class AutoUpdater:
    """Handles automatic updates for the executable version"""
    
    def __init__(self, parent_window=None):
        self.parent_window = parent_window
        self.current_version = __version__
        self.settings_file = Path("update_settings.json")
        self.update_available = False
        self.latest_version = None
        self.download_url = None
        
        # Load update settings
        self.load_settings()
        # Log token status once on init for diagnostics
        _log_token_status()
    
    def load_settings(self):
        """Load update settings from file"""
        default_settings = {
            "auto_check_enabled": True,
            "last_check": None,
            "skip_version": None,
            "check_interval": UPDATE_CHECK_INTERVAL
        }
        
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
                # Merge with defaults for new keys
                for key, value in default_settings.items():
                    if key not in self.settings:
                        self.settings[key] = value
            except Exception as e:
                logger.error(f"Error loading update settings: {e}")
                self.settings = default_settings
        else:
            self.settings = default_settings
    
    def save_settings(self):
        """Save update settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving update settings: {e}")
    
    def should_check_for_updates(self):
        """Check if it's time to check for updates"""
        if not self.settings.get("auto_check_enabled", True):
            return False
        
        last_check = self.settings.get("last_check")
        if not last_check:
            return True
        
        try:
            last_check_time = datetime.fromisoformat(last_check)
            time_since_check = datetime.now() - last_check_time
            return time_since_check.total_seconds() > self.settings.get("check_interval", UPDATE_CHECK_INTERVAL)
        except:
            return True
    
    def check_for_updates_async(self, callback=None):
        """Check for updates in background thread"""
        def check_updates():
            try:
                has_update, version_info = self.check_for_updates()
                if callback:
                    # Schedule callback on main thread
                    if self.parent_window:
                        self.parent_window.after(0, lambda: callback(has_update, version_info))
            except Exception as e:
                logger.error(f"Error checking for updates: {e}")
                if callback:
                    if self.parent_window:
                        self.parent_window.after(0, lambda: callback(False, None))
        
        thread = threading.Thread(target=check_updates, daemon=True)
        thread.start()
    
    def check_for_updates(self):
        """Check for available updates"""
        try:
            logger.info("Checking for updates...")
            
            # Update last check time
            self.settings["last_check"] = datetime.now().isoformat()
            self.save_settings()
            
            # Make API request to check latest version
            headers = {"Accept": "application/vnd.github+json"}
            use_auth = bool(GITHUB_TOKEN)
            if use_auth:
                headers["Authorization"] = f"token {GITHUB_TOKEN}"
            logger.info(f"Updater: GET {UPDATE_CHECK_URL} auth={use_auth}")
            response = requests.get(UPDATE_CHECK_URL, headers=headers, timeout=10)
            response.raise_for_status()
            
            release_data = response.json()
            latest_version = release_data.get("tag_name", "").lstrip("v")
            
            if not latest_version:
                logger.warning("Could not determine latest version")
                return False, None
            
            # Compare versions
            if self.is_newer_version(latest_version, self.current_version):
                # Check if user chose to skip this version
                if latest_version == self.settings.get("skip_version"):
                    logger.info(f"Skipping version {latest_version} as requested by user")
                    return False, None
                
                # Find download URL for Windows executable
                download_url = None
                selected_asset = None
                for asset in release_data.get("assets", []):
                    if asset.get("name", "").endswith(".exe"):
                        selected_asset = asset
                        # For private repos, use the API asset URL with auth
                        if use_auth:
                            download_url = asset.get("url")  # API URL for asset
                        else:
                            download_url = asset.get("browser_download_url")
                        logger.info(f"Updater: selected asset name={asset.get('name','')} use_api_asset={use_auth}")
                        break
                
                if not download_url:
                    logger.warning("No Windows executable found in latest release")
                    return False, None
                
                version_info = {
                    "version": latest_version,
                    "download_url": download_url,
                    "release_notes": release_data.get("body", ""),
                    "published_at": release_data.get("published_at", ""),
                    "size": (selected_asset.get("size", 0) if selected_asset else 0),
                    # When using a private repo with token, we download via the API asset URL
                    "use_api_asset": use_auth
                }
                
                self.update_available = True
                self.latest_version = latest_version
                self.download_url = download_url
                
                logger.info(f"Update available: {latest_version}")
                return True, version_info
            
            logger.info("No updates available")
            return False, None
            
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return False, None
    
    def is_newer_version(self, version1, version2):
        """Compare version strings (semantic versioning)"""
        try:
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
            
            # Pad shorter version with zeros
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            return v1_parts > v2_parts
        except:
            return version1 > version2
    
    def show_update_dialog(self, version_info):
        """Show update available dialog"""
        if not self.parent_window:
            return
        
        dialog = tk.Toplevel(self.parent_window)
        dialog.title("Update Available")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        dialog.transient(self.parent_window)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (400 // 2)
        dialog.geometry(f"500x400+{x}+{y}")
        
        main_frame = tk.Frame(dialog, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="🚀 Update Available!",
            font=("Segoe UI", 16, "bold"),
            fg="#2563eb"
        )
        title_label.pack(pady=(0, 10))
        
        # Version info
        version_frame = tk.Frame(main_frame)
        version_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            version_frame,
            text=f"Current Version: {self.current_version}",
            font=("Segoe UI", 10)
        ).pack(anchor="w")
        
        tk.Label(
            version_frame,
            text=f"Latest Version: {version_info['version']}",
            font=("Segoe UI", 10, "bold"),
            fg="#059669"
        ).pack(anchor="w")
        
        # Release notes
        notes_label = tk.Label(
            main_frame,
            text="Release Notes:",
            font=("Segoe UI", 10, "bold")
        )
        notes_label.pack(anchor="w", pady=(10, 5))
        
        notes_frame = tk.Frame(main_frame)
        notes_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        notes_text = tk.Text(
            notes_frame,
            wrap="word",
            height=8,
            font=("Segoe UI", 9)
        )
        notes_scrollbar = tk.Scrollbar(notes_frame, orient="vertical", command=notes_text.yview)
        notes_text.configure(yscrollcommand=notes_scrollbar.set)
        
        notes_text.pack(side="left", fill="both", expand=True)
        notes_scrollbar.pack(side="right", fill="y")
        
        # Insert release notes
        notes_text.insert("1.0", version_info.get("release_notes", "No release notes available."))
        notes_text.config(state="disabled")
        
        # Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(15, 0))
        
        def download_update():
            dialog.destroy()
            self.download_and_install_update(version_info)
        
        def skip_version():
            self.settings["skip_version"] = version_info["version"]
            self.save_settings()
            dialog.destroy()
        
        def remind_later():
            dialog.destroy()
        
        # Download button
        download_btn = tk.Button(
            button_frame,
            text="📥 Download & Install",
            command=download_update,
            bg="#059669",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=20,
            pady=8
        )
        download_btn.pack(side="right", padx=(10, 0))
        
        # Skip version button
        skip_btn = tk.Button(
            button_frame,
            text="⏭️ Skip This Version",
            command=skip_version,
            bg="#6b7280",
            fg="white",
            font=("Segoe UI", 10),
            padx=15,
            pady=8
        )
        skip_btn.pack(side="right", padx=(10, 0))
        
        # Remind later button
        later_btn = tk.Button(
            button_frame,
            text="🕐 Remind Later",
            command=remind_later,
            bg="#e5e7eb",
            fg="#374151",
            font=("Segoe UI", 10),
            padx=15,
            pady=8
        )
        later_btn.pack(side="right")
    
    def download_and_install_update(self, version_info):
        """Download and install update"""
        def download_progress():
            try:
                # Create progress dialog
                progress_dialog = tk.Toplevel(self.parent_window)
                progress_dialog.title("Downloading Update")
                progress_dialog.geometry("400x150")
                progress_dialog.resizable(False, False)
                progress_dialog.transient(self.parent_window)
                progress_dialog.grab_set()
                
                # Center dialog
                progress_dialog.update_idletasks()
                x = (progress_dialog.winfo_screenwidth() // 2) - (400 // 2)
                y = (progress_dialog.winfo_screenheight() // 2) - (150 // 2)
                progress_dialog.geometry(f"400x150+{x}+{y}")
                
                frame = tk.Frame(progress_dialog, padx=20, pady=20)
                frame.pack(fill="both", expand=True)
                
                status_label = tk.Label(
                    frame,
                    text="Downloading update...",
                    font=("Segoe UI", 10)
                )
                status_label.pack(pady=(0, 10))
                
                progress_var = tk.StringVar(value="0%")
                progress_label = tk.Label(
                    frame,
                    textvariable=progress_var,
                    font=("Segoe UI", 9)
                )
                progress_label.pack()
                
                # Download file
                req_headers = {}
                if version_info.get("use_api_asset"):
                    # GitHub API asset download for private repos
                    req_headers["Accept"] = "application/octet-stream"
                    if GITHUB_TOKEN:
                        req_headers["Authorization"] = f"token {GITHUB_TOKEN}"
                response = requests.get(version_info["download_url"], stream=True, headers=req_headers)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".exe") as temp_file:
                    temp_path = temp_file.name
                    downloaded = 0
                    
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            temp_file.write(chunk)
                            downloaded += len(chunk)
                            
                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                progress_var.set(f"{percent:.1f}%")
                                progress_dialog.update_idletasks()
                
                progress_dialog.destroy()
                
                # Offer install options
                install_now = messagebox.askyesno(
                    "Install Update",
                    "Update downloaded successfully.\n\n"
                    "Do you want to install it now?",
                    icon="question"
                )

                if install_now:
                    try:
                        # Offer in-place replace if running as packaged EXE on Windows
                        can_replace = (os.name == "nt" and getattr(sys, "frozen", False))
                        replace_in_place = False
                        if can_replace:
                            replace_in_place = messagebox.askyesno(
                                "Installation Option",
                                "Replace the current EXE in place and restart now?\n\n"
                                "Yes = Safely replace FeatureFlagManager.exe and relaunch.\n"
                                "No  = Choose another install option.",
                                icon="question"
                            )

                        if replace_in_place and can_replace:
                            try:
                                target_exe = Path(sys.executable)
                                dest_dir = target_exe.parent
                                stem = target_exe.stem
                                suffix = target_exe.suffix or ".exe"
                                new_exe = dest_dir / f"{stem}-new{suffix}"
                                backup_exe = dest_dir / f"{stem}-backup{suffix}"

                                # Copy downloaded file to -new next to current EXE
                                try:
                                    shutil.copy2(temp_path, new_exe)
                                    logger.info(f"Updater: prepared new EXE at {new_exe}")
                                except Exception as copy_err:
                                    logger.error(f"Updater: failed to stage new EXE: {copy_err}")
                                    # Fallback to running from temp
                                    subprocess.Popen([temp_path])
                                    sys.exit(0)

                                # Create swap script in destination directory
                                script_name = f"ffm_swap_{int(time.time())}.cmd"
                                script_path = dest_dir / script_name
                                bat = (
                                    "@echo off\r\n"
                                    "setlocal\r\n"
                                    f"set \"TARGET={str(target_exe)}\"\r\n"
                                    f"set \"NEW={str(new_exe)}\"\r\n"
                                    f"set \"BACKUP={str(backup_exe)}\"\r\n"
                                    ":wait\r\n"
                                    "move /y \"%TARGET%\" \"%BACKUP%\" >nul 2>&1\r\n"
                                    "if errorlevel 1 (\r\n"
                                    "  timeout /t 1 /nobreak >nul\r\n"
                                    "  goto wait\r\n"
                                    ")\r\n"
                                    "move /y \"%NEW%\" \"%TARGET%\" >nul 2>&1\r\n"
                                    "start \"\" \"%TARGET%\"\r\n"
                                    "del /f /q \"%BACKUP%\" >nul 2>&1\r\n"
                                    "del /f /q \"%~f0\" >nul 2>&1\r\n"
                                    "endlocal\r\n"
                                )
                                try:
                                    with open(script_path, "w", encoding="utf-8") as f:
                                        f.write(bat)
                                    logger.info(f"Updater: wrote swap script {script_path}")
                                except Exception as werr:
                                    logger.error(f"Updater: failed to write swap script: {werr}")
                                    subprocess.Popen([temp_path])
                                    sys.exit(0)

                                # Inform user and launch swap script
                                messagebox.showinfo(
                                    "Installing Update",
                                    "The application will close and restart with the new version."
                                )
                                try:
                                    subprocess.Popen(["cmd.exe", "/c", str(script_path)])
                                except Exception as perr:
                                    logger.error(f"Updater: failed to start swap script: {perr}")
                                    # Fallback to temp
                                    subprocess.Popen([temp_path])
                                finally:
                                    # Exit current app so the script can replace the EXE
                                    try:
                                        os.unlink(temp_path)
                                    except Exception:
                                        pass
                                    sys.exit(0)

                            except Exception as repl_err:
                                logger.error(f"Updater: in-place replace error: {repl_err}")
                                # Fallback to side-by-side/temporary path below

                        # If not replacing in place, ask whether to save side-by-side with version suffix (recommended)
                        side_by_side = messagebox.askyesno(
                            "Installation Option",
                            "Save the new EXE next to your current one with a versioned name?\n\n"
                            "Yes = Save as FeatureFlagManager-v<version>.exe and launch it.\n"
                            "No  = Just run the downloaded EXE from the temporary folder.",
                            icon="question"
                        )

                        if side_by_side:
                            # Determine destination directory (next to current EXE if frozen)
                            try:
                                if getattr(sys, "frozen", False):
                                    dest_dir = Path(sys.executable).parent
                                else:
                                    dest_dir = Path.cwd()
                            except Exception:
                                dest_dir = Path.cwd()

                            version_str = str(version_info.get("version", "")) or "unknown"
                            dest_name = f"FeatureFlagManager-v{version_str}.exe"
                            dest_path = dest_dir / dest_name

                            # Copy downloaded EXE next to current application
                            try:
                                shutil.copy2(temp_path, dest_path)
                                logger.info(f"Updater: saved new EXE to {dest_path}")
                            except Exception as copy_err:
                                logger.error(f"Updater: failed to save EXE to {dest_path}: {copy_err}")
                                # Fallback to running from temp
                                subprocess.Popen([temp_path])
                                sys.exit(0)

                            # Ask to launch the new side-by-side EXE
                            launch_new = messagebox.askyesno(
                                "Launch New Version",
                                f"Saved: {dest_path}\n\nLaunch the new version now?",
                                icon="question"
                            )
                            if launch_new:
                                try:
                                    subprocess.Popen([str(dest_path)])
                                except Exception as e:
                                    logger.error(f"Updater: failed to launch new EXE: {e}")
                                finally:
                                    # Exit current app regardless if launch attempted
                                    sys.exit(0)
                            else:
                                # Keep current app running; remove temp file
                                try:
                                    os.unlink(temp_path)
                                except Exception:
                                    pass
                                messagebox.showinfo("Update Saved", f"New version saved to:\n{dest_path}")
                        else:
                            # Run from temp as a one-off
                            subprocess.Popen([temp_path])
                            sys.exit(0)
                    except Exception as install_err:
                        logger.error(f"Updater: install flow error: {install_err}")
                        # Fallback to running from temp
                        try:
                            subprocess.Popen([temp_path])
                        except Exception:
                            pass
                        sys.exit(0)
                else:
                    # Clean up temp file if user declined
                    try:
                        os.unlink(temp_path)
                    except Exception:
                        pass
                
            except Exception as e:
                logger.error(f"Error downloading update: {e}")
                messagebox.showerror(
                    "Download Error",
                    f"Failed to download update:\n{str(e)}"
                )
        
        # Run download in background thread
        thread = threading.Thread(target=download_progress, daemon=True)
        thread.start()
    
    def auto_check_on_startup(self):
        """Perform automatic update check on startup"""
        if not self.should_check_for_updates():
            return
        
        def update_callback(has_update, version_info):
            if has_update and version_info:
                self.show_update_dialog(version_info)
        
        # Check for updates in background
        self.check_for_updates_async(update_callback)
    
    def manual_check_for_updates(self):
        """Manually check for updates (called from menu)"""
        def update_callback(has_update, version_info):
            if has_update and version_info:
                self.show_update_dialog(version_info)
            else:
                messagebox.showinfo(
                    "No Updates",
                    f"You are running the latest version ({self.current_version})."
                )
        
        self.check_for_updates_async(update_callback)

# Global updater instance
_updater_instance = None

def get_updater(parent_window=None):
    """Get global updater instance"""
    global _updater_instance
    if _updater_instance is None:
        _updater_instance = AutoUpdater(parent_window)
    elif parent_window and not _updater_instance.parent_window:
        _updater_instance.parent_window = parent_window
    return _updater_instance
