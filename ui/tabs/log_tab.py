import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox
import os
from shared.config_loader import LOG_FILE

class LogTab:
    def __init__(self, parent, history_manager, theme_manager):
        self.parent = parent
        self.history_manager = history_manager
        self.theme_manager = theme_manager
        self.setup_ui()

    def setup_ui(self):
        """Sets up the UI for the 'Log Viewer' tab with a professional layout."""
        # --- Main container frame ---
        log_frame = ttk.Frame(self.parent, padding=30)
        log_frame.pack(fill="both", expand=True)

        # --- Header Section ---
        header_frame = ttk.Frame(log_frame)
        header_frame.pack(fill="x", pady=(0, 30))
        
        # Title with icon
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(anchor="w")
        
        title_label = ttk.Label(
            title_frame, 
            text="📝 Log Viewer", 
            font=("Segoe UI", 24, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        title_label.pack(anchor="w")
        
        subtitle_label = ttk.Label(
            title_frame,
            text="View application logs and system events",
            font=("Segoe UI", 12),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        subtitle_label.pack(anchor="w", pady=(5, 0))

        # --- Controls Section ---
        controls_container = ttk.Frame(log_frame)
        controls_container.pack(fill="x", pady=(0, 25))
        
        # Controls card
        controls_frame = ttk.Frame(controls_container, style="Card.TFrame")
        controls_frame.pack(fill="x", padx=5)
        
        # Controls header
        controls_header = ttk.Frame(controls_frame)
        controls_header.pack(fill="x", padx=25, pady=(20, 15))
        
        controls_title = ttk.Label(
            controls_header,
            text="🔧 Controls",
            font=("Segoe UI", 16, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        controls_title.pack(anchor="w")

        # Controls content
        controls_content = ttk.Frame(controls_frame)
        controls_content.pack(fill="x", padx=25, pady=(0, 20))
        
        # Control buttons row
        buttons_frame = ttk.Frame(controls_content)
        buttons_frame.pack(fill="x", pady=8)
        
        # Refresh button
        refresh_button = ttk.Button(
            buttons_frame, 
            text="🔄 Refresh Logs", 
            bootstyle="info", 
            width=15, 
            command=self.refresh_logs
        )
        refresh_button.pack(side="left", padx=(0, 10))
        
        # Clear logs button
        clear_button = ttk.Button(
            buttons_frame, 
            text="🗑️ Clear Logs", 
            bootstyle="danger", 
            width=15, 
            command=self.clear_logs
        )
        clear_button.pack(side="left", padx=10)
        
        # Export button
        export_button = ttk.Button(
            buttons_frame, 
            text="📤 Export Logs", 
            bootstyle="success", 
            width=15, 
            command=self.export_logs
        )
        export_button.pack(side="left", padx=10)

        # Filter controls row
        filter_frame = ttk.Frame(controls_content)
        filter_frame.pack(fill="x", pady=8)
        ttk.Label(filter_frame, text="Filter:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.filter_var,
            values=[
                "All",
                "Errors & Warnings",
                "Errors Only",
                "Info Only",
                "Debug Only",
            ],
            state="readonly",
            width=18
        )
        filter_combo.pack(side="left", padx=(10, 0))
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_logs())

        # Search row
        search_frame = ttk.Frame(controls_content)
        search_frame.pack(fill="x", pady=4)
        ttk.Label(search_frame, text="Search:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.search_var = tk.StringVar(value="")
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", padx=(10, 0))
        search_entry.bind("<KeyRelease>", lambda e: self.refresh_logs())
        ttk.Button(
            search_frame,
            text="✕ Clear",
            bootstyle="secondary",
            width=10,
            command=self._clear_search
        ).pack(side="left", padx=(10, 0))

        # --- Log Display Section ---
        log_display_container = ttk.Frame(log_frame)
        log_display_container.pack(fill="both", expand=True)
        
        # Log display card
        log_display_frame = ttk.Frame(log_display_container, style="Card.TFrame")
        log_display_frame.pack(fill="both", expand=True, padx=5)
        
        # Log display header
        log_display_header = ttk.Frame(log_display_frame)
        log_display_header.pack(fill="x", padx=25, pady=(20, 15))
        
        log_display_title = ttk.Label(
            log_display_header,
            text="📋 Application Logs",
            font=("Segoe UI", 16, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        log_display_title.pack(anchor="w")

        # Log display content
        log_display_content = ttk.Frame(log_display_frame)
        log_display_content.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        
        # Create text widget with scrollbars
        text_frame = ttk.Frame(log_display_content)
        text_frame.pack(fill="both", expand=True)
        
        # Scrollbars
        text_scroll_y = ttk.Scrollbar(text_frame, orient="vertical")
        text_scroll_y.pack(side="right", fill="y")
        
        text_scroll_x = ttk.Scrollbar(text_frame, orient="horizontal")
        text_scroll_x.pack(side="bottom", fill="x")
        
        # Text widget
        self.log_text = tk.Text(
            text_frame,
            wrap="word",
            font=("Consolas", 10),
            bg=self.theme_manager.get_theme_config()["colors"]["surface"],
            fg=self.theme_manager.get_theme_config()["colors"]["text"],
            insertbackground=self.theme_manager.get_theme_config()["colors"]["text"],
            selectbackground=self.theme_manager.get_theme_config()["colors"]["primary"],
            selectforeground=self.theme_manager.get_theme_config()["colors"]["sidebar_active_text"],
            yscrollcommand=text_scroll_y.set,
            xscrollcommand=text_scroll_x.set,
            state="disabled"
        )
        self.log_text.pack(fill="both", expand=True)
        
        # Configure scrollbars
        text_scroll_y.config(command=self.log_text.yview)
        text_scroll_x.config(command=self.log_text.xview)
        
        # Status label
        self.log_status_var = tk.StringVar(value="Ready to display logs")
        status_label = ttk.Label(
            log_display_content, 
            textvariable=self.log_status_var, 
            font=("Segoe UI", 10, "italic"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text_secondary"]
        )
        status_label.pack(pady=(10, 0))

        # Load initial logs
        self.refresh_logs()

    def _line_passes_filter(self, line: str) -> bool:
        """Return True if a log line matches the selected filter."""
        try:
            filt = (self.filter_var.get() if hasattr(self, 'filter_var') else 'All') or 'All'
        except Exception:
            filt = 'All'
        u = line.upper()
        is_debug = ":DEBUG:" in u
        is_info = ":INFO:" in u
        is_warn = ":WARNING:" in u
        is_error = ":ERROR:" in u or ":CRITICAL:" in u
        if filt == 'All':
            return True
        if filt == 'Errors & Warnings':
            return is_warn or is_error
        if filt == 'Errors Only':
            return is_error
        if filt == 'Info Only':
            return is_info
        if filt == 'Debug Only':
            return is_debug
        return True

    def _line_matches_search(self, line: str) -> bool:
        """Return True if the line matches the current search query (case-insensitive substring)."""
        try:
            q = (self.search_var.get() if hasattr(self, 'search_var') else "").strip()
        except Exception:
            q = ""
        if not q:
            return True
        try:
            return q.lower() in line.lower()
        except Exception:
            return True

    def _clear_search(self):
        """Clear the search query and refresh logs."""
        try:
            if hasattr(self, 'search_var'):
                self.search_var.set("")
        except Exception:
            pass
        self.refresh_logs()

    # --- Event Handlers ---
    def refresh_logs(self):
        """Refresh the log display"""
        self.log_status_var.set("Loading logs...")
        
        try:
            if os.path.exists(LOG_FILE):
                # Read with UTF-8 using replacement for any legacy non-UTF8 bytes
                with open(LOG_FILE, 'r', encoding='utf-8', errors='replace') as f:
                    full_content = f.read()
                # Apply filter
                try:
                    lines = full_content.split('\n')
                    filtered_lines = [ln for ln in lines if self._line_passes_filter(ln) and self._line_matches_search(ln)]
                    log_content = "\n".join(filtered_lines)
                    total_lines = len(lines)
                    shown_lines = len(filtered_lines)
                except Exception:
                    # Fallback to unfiltered if anything goes wrong
                    log_content = full_content
                    total_lines = len(full_content.split('\n'))
                    shown_lines = total_lines
                
                # Update text widget
                self.log_text.config(state="normal")
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(1.0, log_content)
                self.log_text.config(state="disabled")
                
                # Scroll to bottom
                self.log_text.see(tk.END)
                
                # Update status
                try:
                    current_filter = self.filter_var.get() if hasattr(self, 'filter_var') else 'All'
                except Exception:
                    current_filter = 'All'
                try:
                    q = (self.search_var.get() if hasattr(self, 'search_var') else '').strip()
                except Exception:
                    q = ''
                if q:
                    self.log_status_var.set(
                        f"Loaded {shown_lines}/{total_lines} log entries (filter: {current_filter}, search: \"{q}\")"
                    )
                else:
                    self.log_status_var.set(
                        f"Loaded {shown_lines}/{total_lines} log entries (filter: {current_filter})"
                    )
            else:
                self.log_text.config(state="normal")
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(1.0, "No log file found.")
                self.log_text.config(state="disabled")
                self.log_status_var.set("No log file available")
                
        except Exception as e:
            self.log_text.config(state="normal")
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(1.0, f"Error reading log file: {str(e)}")
            self.log_text.config(state="disabled")
            self.log_status_var.set("Error loading logs")

    def clear_logs(self):
        """Clear the log file"""
        try:
            if os.path.exists(LOG_FILE):
                # Clear the file
                with open(LOG_FILE, 'w', encoding='utf-8') as f:
                    f.write("")
                
                # Refresh display
                self.refresh_logs()
                messagebox.showinfo("Success", "Log file has been cleared.")
            else:
                messagebox.showinfo("Info", "No log file to clear.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear log file: {str(e)}")

    def export_logs(self):
        """Export logs to a file"""
        try:
            if os.path.exists(LOG_FILE):
                from tkinter import filedialog
                
                # Get save file path
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                    title="Export Logs"
                )
                
                if file_path:
                    # Copy log file to selected location
                    with open(LOG_FILE, 'r', encoding='utf-8') as source:
                        with open(file_path, 'w', encoding='utf-8') as target:
                            target.write(source.read())
                    
                    messagebox.showinfo("Success", f"Logs exported to: {file_path}")
            else:
                messagebox.showinfo("Info", "No log file to export.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export logs: {str(e)}")

    def update_text_colors(self):
        """Update text widget colors for current theme"""
        colors = self.theme_manager.get_theme_config()["colors"]
        
        self.log_text.config(
            bg=colors["surface"],
            fg=colors["text"],
            insertbackground=colors["text"],
            selectbackground=colors["primary"],
            selectforeground=colors["sidebar_active_text"]
        ) 