"""
Enhanced View Tab with comprehensive flag management features
Includes data insights, advanced filtering, responsive layout, and real-time updates
"""

import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox
import threading
import queue
import time
import json
import webbrowser
from datetime import datetime, timedelta
from api_client import get_client
from config import PROJECT_KEY
from utils.settings_manager import SettingsManager

class ToastNotification:
    """Toast notification system for user feedback"""
    
    def __init__(self, parent):
        self.parent = parent
        self.active_toasts = []
    
    def show_success(self, message: str, duration: int = 3000):
        self._show_toast(message, "success", duration)
    
    def show_error(self, message: str, duration: int = 5000):
        self._show_toast(message, "danger", duration)
    
    def show_info(self, message: str, duration: int = 3000):
        self._show_toast(message, "info", duration)
    
    def _show_toast(self, message: str, style: str, duration: int):
        """Create and display toast notification"""
        toast = tk.Toplevel(self.parent)
        toast.withdraw()
        toast.overrideredirect(True)
        toast.attributes('-topmost', True)
        
        # Create toast frame with proper styling
        if style == "success":
            bg_color = "#10b981"  # Green
            text_color = "#ffffff"
            icon = "✅"
        elif style == "danger":
            bg_color = "#ef4444"  # Red
            text_color = "#ffffff" 
            icon = "❌"
        else:  # info
            bg_color = "#3b82f6"  # Blue
            text_color = "#ffffff"
            icon = "ℹ️"
        
        toast_frame = tk.Frame(
            toast, 
            bg=bg_color,
            relief="solid",
            borderwidth=1,
            padx=20,
            pady=15
        )
        toast_frame.pack(fill="both", expand=True)
        
        # Message label with explicit styling
        message_label = tk.Label(
            toast_frame,
            text=f"{icon} {message}",
            font=("Segoe UI", 11, "bold"),
            fg=text_color,
            bg=bg_color,
            wraplength=300
        )
        message_label.pack()
        
        # Position toast
        toast.update_idletasks()
        width = toast.winfo_reqwidth()
        height = toast.winfo_reqheight()
        
        # Position in top-right corner
        try:
            main_window = self.parent.winfo_toplevel()
            x = main_window.winfo_x() + main_window.winfo_width() - width - 20
            y = main_window.winfo_y() + 40 + len(self.active_toasts) * (height + 10)
        except:
            # Fallback positioning
            x = 1200
            y = 100 + len(self.active_toasts) * (height + 10)
        
        toast.geometry(f"{width}x{height}+{x}+{y}")
        toast.deiconify()
        
        # Add to active toasts
        self.active_toasts.append(toast)
        
        # Auto-dismiss after duration
        def dismiss():
            try:
                if toast in self.active_toasts:
                    self.active_toasts.remove(toast)
                toast.destroy()
                # Reposition remaining toasts
                self._reposition_toasts()
            except:
                pass
        
        self.parent.after(duration, dismiss)
    
    def _reposition_toasts(self):
        """Reposition remaining toasts"""
        for i, toast in enumerate(self.active_toasts):
            try:
                width = toast.winfo_reqwidth()
                height = toast.winfo_reqheight()
                
                try:
                    main_window = self.parent.winfo_toplevel()
                    x = main_window.winfo_x() + main_window.winfo_width() - width - 20
                    y = main_window.winfo_y() + 40 + i * (height + 10)
                except:
                    x = 1200
                    y = 100 + i * (height + 10)
                
                toast.geometry(f"{width}x{height}+{x}+{y}")
            except:
                pass

class LoadingSpinner:
    """Animated loading spinner"""
    
    def __init__(self, parent, text="Loading..."):
        self.parent = parent
        self.text = text
        self.is_spinning = False
        self.spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        self.current_char = 0
        
        # Create spinner frame
        self.frame = ttk.Frame(parent, padding=10)
        self.label = ttk.Label(
            self.frame,
            text=f"{self.spinner_chars[0]} {self.text}",
            font=("Segoe UI", 10)
        )
        self.label.pack()
    
    def start(self):
        """Start the spinning animation"""
        self.is_spinning = True
        self._animate()
    
    def stop(self):
        """Stop the spinning animation"""
        self.is_spinning = False
    
    def _animate(self):
        """Animate the spinner"""
        if self.is_spinning:
            try:
                char = self.spinner_chars[self.current_char]
                self.label.config(text=f"{char} {self.text}")
                self.current_char = (self.current_char + 1) % len(self.spinner_chars)
                self.parent.after(100, self._animate)
            except:
                pass
    
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
    
    def pack_forget(self):
        self.frame.pack_forget()

class EnhancedViewTab:
    """Enhanced View Tab with comprehensive flag management features"""
    
    def __init__(self, parent, history_manager, theme_manager):
        self.parent = parent
        self.history_manager = history_manager
        self.theme_manager = theme_manager
        
        # Initialize settings manager
        self.settings_manager = SettingsManager()
        
        # Load saved settings
        self.load_saved_settings()
        
        # Initialize API client
        self.api_client = get_client()
        
        # Data storage
        self.all_flags = []
        self.displayed_flags = []
        self.flag_statistics = {}
        
        # Pagination
        self.page_number = 1
        self.page_size = 20
        self.total_pages = 1
        
        # Filtering
        self.filter_query = None
        self.status_filter = "All"
        self.env_filter = "All"
        self.health_filter = "All"
        self.sidebar_collapsed = False
        
        # Auto-refresh
        self.auto_refresh_enabled = False
        self.auto_refresh_interval = 30  # seconds
        self.auto_refresh_job = None
        
        # UI Components
        self.toast = ToastNotification(parent)
        self.loading_spinner = None
        
        # Queue for threaded operations
        self.operation_queue = queue.Queue()
        
        self.setup_ui()
        self.setup_keyboard_shortcuts()
        
        # Start with initial data load
        self.refresh_data()
        
        # Show welcome toast notification about dramatic improvements
        self.parent.after(1000, lambda: self.toast.show_success("🎨 UI UPGRADE! Smart scaling: 20-100px rows, 8-16pt fonts! Customize in View Options! 🎉"))
    
    def load_saved_settings(self):
        """Load and apply saved user settings"""
        try:
            print("DEBUG: Loading saved settings...")
            view_options = self.settings_manager.get_view_options()
            
            # Apply auto-refresh settings
            self.auto_refresh_enabled = view_options.get("auto_refresh_enabled", True)
            self.auto_refresh_interval = view_options.get("auto_refresh_interval", 30)
            
            print(f"DEBUG: Loaded settings - Auto-refresh: {self.auto_refresh_enabled}, Interval: {self.auto_refresh_interval}s")
            
            # Note: Row height will be applied when UI is created
            
        except Exception as e:
            print(f"DEBUG: Error loading settings: {e}")
            # Use defaults if loading fails
            self.auto_refresh_enabled = True
            self.auto_refresh_interval = 30
    
    def apply_saved_row_height(self):
        """Apply saved row height with dynamic font scaling after UI is created"""
        try:
            view_options = self.settings_manager.get_view_options()
            saved_height = view_options.get("row_height", 30)
            
            if hasattr(self, 'tree'):
                self.configure_dramatic_styling(row_height=saved_height)
                print(f"DEBUG: Applied saved row height with scaled fonts: {saved_height}px")
                
        except Exception as e:
            print(f"DEBUG: Error applying saved row height: {e}")
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Bind to parent window
        def bind_key(key, func):
            self.parent.bind_all(key, lambda e: func())
        
        bind_key("<F5>", self.refresh_data)
        bind_key("<Control-f>", self.focus_search)
        bind_key("<Control-r>", self.toggle_auto_refresh)
        bind_key("<Control-h>", self.toggle_sidebar)
    
    def focus_search(self):
        """Focus on search entry"""
        self.search_entry.focus_set()
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh functionality"""
        self.auto_refresh_enabled = not self.auto_refresh_enabled
        if self.auto_refresh_enabled:
            self.start_auto_refresh()
            self.toast.show_info(f"Auto-refresh enabled ({self.auto_refresh_interval}s)")
        else:
            self.stop_auto_refresh()
            self.toast.show_info("Auto-refresh disabled")
    
    def toggle_sidebar(self):
        """Toggle sidebar visibility"""
        try:
            print("DEBUG: Toggle sidebar clicked!")
            print(f"DEBUG: Current sidebar_collapsed state: {self.sidebar_collapsed}")
            print(f"DEBUG: Sidebar frame exists: {hasattr(self, 'sidebar_frame')}")
            
            if not hasattr(self, 'sidebar_frame'):
                print("DEBUG: ERROR - sidebar_frame does not exist!")
                return
                
            self.sidebar_collapsed = not self.sidebar_collapsed
            print(f"DEBUG: New sidebar_collapsed state: {self.sidebar_collapsed}")
            
            if self.sidebar_collapsed:
                print("DEBUG: Hiding sidebar...")
                self.sidebar_frame.pack_forget()
                self.toggle_sidebar_btn.config(text="🔍 Show Filters")
                print("DEBUG: Sidebar hidden, button text updated")
                self.toast.show_info("🔍 Filters hidden")
            else:
                print("DEBUG: Showing sidebar...")
                # Re-pack the sidebar with the original settings
                self.sidebar_frame.pack(side="left", fill="y", padx=(0, 10), before=self.sidebar_frame.master.winfo_children()[1] if len(self.sidebar_frame.master.winfo_children()) > 1 else None)
                self.toggle_sidebar_btn.config(text="🔍 Hide Filters")
                print("DEBUG: Sidebar shown, button text updated")
                self.toast.show_info("🔍 Filters shown")
                
        except Exception as e:
            print(f"DEBUG: Error in toggle_sidebar: {e}")
            import traceback
            traceback.print_exc()
            self.toast.show_error(f"Error toggling filters: {str(e)}")
    
    def setup_ui(self):
        """Setup the enhanced UI"""
        # Main container
        main_container = ttk.Frame(self.parent, padding=20)
        main_container.pack(fill="both", expand=True)
        
        # Header Section
        self.setup_header(main_container)
        
        # Quick Stats Bar
        self.setup_stats_bar(main_container)
        
        # Content Area (Sidebar + Main Content)
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill="both", expand=True, pady=(20, 0))
        
        # Sidebar for filters and insights
        self.setup_sidebar(content_frame)
        
        # Main content area
        self.setup_main_content(content_frame)
        
        # Ensure button state matches initial sidebar state
        if hasattr(self, 'toggle_sidebar_btn'):
            if self.sidebar_collapsed:
                self.toggle_sidebar_btn.config(text="🔍 Show Filters")
            else:
                self.toggle_sidebar_btn.config(text="🔍 Hide Filters")
            print(f"DEBUG: Button text set to match sidebar state: collapsed={self.sidebar_collapsed}")
        
        # Status bar
        self.setup_status_bar(main_container)
    
    def setup_header(self, parent):
        """Setup header with title and controls"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Left side - Title
        left_frame = ttk.Frame(header_frame)
        left_frame.pack(side="left", fill="x", expand=True)
        
        title_label = ttk.Label(
            left_frame,
            text="🚩 Feature Flags Management",
            font=("Segoe UI", 24, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        title_label.pack(anchor="w")
        
        subtitle_label = ttk.Label(
            left_frame,
            text="Comprehensive flag management with real-time insights",
            font=("Segoe UI", 12),
            foreground=self.theme_manager.get_theme_config()["colors"]["text_secondary"]
        )
        subtitle_label.pack(anchor="w", pady=(5, 0))
        
        # Right side - Controls
        controls_frame = ttk.Frame(header_frame)
        controls_frame.pack(side="right")
        
        # Toggle sidebar button
        self.toggle_sidebar_btn = ttk.Button(
            controls_frame,
            text="🔍 Hide Filters"
        )
        self.toggle_sidebar_btn.pack(side="left", padx=(0, 10))
        
        # Bind the command after creation to ensure it works
        self.toggle_sidebar_btn.config(command=lambda: self.toggle_sidebar())
        print("DEBUG: Toggle sidebar button created and command bound successfully")
        
        # Auto-refresh toggle
        self.auto_refresh_btn = ttk.Button(
            controls_frame,
            text="🔄 Auto-refresh",
            bootstyle="info",
            command=self.toggle_auto_refresh
        )
        self.auto_refresh_btn.pack(side="left", padx=(0, 10))
        
        # Manual refresh
        refresh_btn = ttk.Button(
            controls_frame,
            text="↻ Refresh",
            bootstyle="primary",
            command=self.refresh_data
        )
        refresh_btn.pack(side="left")
    
    def setup_stats_bar(self, parent):
        """Setup quick statistics bar"""
        self.stats_frame = ttk.Frame(parent, style="Card.TFrame")
        self.stats_frame.pack(fill="x", pady=(0, 20))
        
        stats_content = ttk.Frame(self.stats_frame)
        stats_content.pack(fill="x", padx=20, pady=15)
        
        # Statistics will be populated by update_stats_bar()
        self.stats_labels = {}
        
        # Initialize with placeholders
        stats = [
            ("total", "📊 Total Flags", "0"),
            ("active", "🟢 Active", "0"),
            ("archived", "🔴 Archived", "0"),
            ("orphaned", "⚠️ Orphaned", "0"),
            ("health", "❤️ Avg Health", "0%")
        ]
        
        for i, (key, label, value) in enumerate(stats):
            stat_frame = ttk.Frame(stats_content)
            stat_frame.pack(side="left", padx=20 if i > 0 else 0)
            
            ttk.Label(
                stat_frame,
                text=label,
                font=("Segoe UI", 10),
                foreground=self.theme_manager.get_theme_config()["colors"]["text_secondary"]
            ).pack()
            
            self.stats_labels[key] = ttk.Label(
                stat_frame,
                text=value,
                font=("Segoe UI", 16, "bold"),
                foreground=self.theme_manager.get_theme_config()["colors"]["text"]
            )
            self.stats_labels[key].pack()
    
    def setup_sidebar(self, parent):
        """Setup collapsible sidebar with filters and insights"""
        print("DEBUG: Setting up sidebar...")
        self.sidebar_frame = ttk.Frame(parent, style="Card.TFrame")
        self.sidebar_frame.pack(side="left", fill="y", padx=(0, 10))
        print("DEBUG: Sidebar frame created and packed")
        
        sidebar_content = ttk.Frame(self.sidebar_frame)
        sidebar_content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Search Section
        search_section = ttk.LabelFrame(sidebar_content, text="🔍 Search & Filters", padding=15)
        search_section.pack(fill="x", pady=(0, 15))
        
        # Search entry
        ttk.Label(search_section, text="Search:").pack(anchor="w")
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            search_section,
            textvariable=self.search_var,
            font=("Segoe UI", 11)
        )
        self.search_entry.pack(fill="x", pady=(5, 10))
        self.search_entry.bind("<KeyRelease>", self.on_search_change)
        
        # Clear search button
        ttk.Button(
            search_section,
            text="✕ Clear",
            bootstyle="secondary",
            command=self.clear_search
        ).pack(fill="x", pady=(0, 10))
        
        # Status filter
        ttk.Label(search_section, text="Status:").pack(anchor="w")
        self.status_filter_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(
            search_section,
            textvariable=self.status_filter_var,
            values=["All", "Active", "Archived"],
            state="readonly"
        )
        status_combo.pack(fill="x", pady=(5, 10))
        status_combo.bind("<<ComboboxSelected>>", self.on_filter_change)
        
        # Environment filter
        ttk.Label(search_section, text="Environment:").pack(anchor="w")
        self.env_filter_var = tk.StringVar(value="All")
        self.env_combo = ttk.Combobox(
            search_section,
            textvariable=self.env_filter_var,
            values=["All"],
            state="readonly"
        )
        self.env_combo.pack(fill="x", pady=(5, 10))
        self.env_combo.bind("<<ComboboxSelected>>", self.on_filter_change)
        
        # Health filter
        ttk.Label(search_section, text="Health:").pack(anchor="w")
        self.health_filter_var = tk.StringVar(value="All")
        health_combo = ttk.Combobox(
            search_section,
            textvariable=self.health_filter_var,
            values=["All", "Healthy (40%+)", "Warning (50-79%)", "Critical (<50%)"],
            state="readonly"
        )
        health_combo.pack(fill="x", pady=(5, 0))
        health_combo.bind("<<ComboboxSelected>>", self.on_filter_change)
        
        # Data Insights Section
        insights_section = ttk.LabelFrame(sidebar_content, text="📊 Data Insights", padding=15)
        insights_section.pack(fill="x", pady=(0, 15))
        
        # Recently Modified section
        self.recent_frame = ttk.Frame(insights_section)
        self.recent_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(
            self.recent_frame,
            text="🕐 Recently Modified (7 days)",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")
        
        self.recent_listbox = tk.Listbox(
            self.recent_frame,
            height=4,
            font=("Segoe UI", 9)
        )
        self.recent_listbox.pack(fill="x", pady=(5, 0))
        self.recent_listbox.bind("<Double-Button-1>", self.on_recent_flag_select)
        
        # Orphaned Flags section
        self.orphaned_frame = ttk.Frame(insights_section)
        self.orphaned_frame.pack(fill="x")
        
        ttk.Label(
            self.orphaned_frame,
            text="⚠️ Orphaned Flags",
            font=("Segoe UI", 10, "bold"),
            foreground="#dc2626"
        ).pack(anchor="w")
        
        self.orphaned_listbox = tk.Listbox(
            self.orphaned_frame,
            height=4,
            font=("Segoe UI", 9)
        )
        self.orphaned_listbox.pack(fill="x", pady=(5, 0))
        self.orphaned_listbox.bind("<Double-Button-1>", self.on_orphaned_flag_select)
        
        # Performance Section
        perf_section = ttk.LabelFrame(sidebar_content, text="⚡ Performance", padding=15)
        perf_section.pack(fill="x")
        
        self.perf_labels = {}
        perf_stats = [
            ("cache_hit_rate", "Cache Hit Rate"),
            ("requests_made", "API Requests"),
            ("cached_items", "Cached Items")
        ]
        
        for key, label in perf_stats:
            stat_frame = ttk.Frame(perf_section)
            stat_frame.pack(fill="x", pady=2)
            
            ttk.Label(
                stat_frame,
                text=f"{label}:",
                font=("Segoe UI", 9)
            ).pack(side="left")
            
            self.perf_labels[key] = ttk.Label(
                stat_frame,
                text="0",
                font=("Segoe UI", 9, "bold")
            )
            self.perf_labels[key].pack(side="right")
    
    def setup_main_content(self, parent):
        """Setup main content area with enhanced treeview"""
        main_frame = ttk.Frame(parent, style="Card.TFrame")
        main_frame.pack(side="right", fill="both", expand=True)
        
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Content header with enhanced toolbar
        content_header = ttk.Frame(content_frame)
        content_header.pack(fill="x", pady=(0, 15))
        
        # Left side - Title and results
        header_left = ttk.Frame(content_header)
        header_left.pack(side="left", fill="x", expand=True)
        
        ttk.Label(
            header_left,
            text="📋 Feature Flags",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left")
        
        # Results info with enhanced styling
        self.results_info_var = tk.StringVar(value="")
        results_label = ttk.Label(
            header_left,
            textvariable=self.results_info_var,
            font=("Segoe UI", 11),
            foreground="#6b7240"
        )
        results_label.pack(side="left", padx=(20, 0))
        
        # Right side - Quick actions toolbar
        toolbar = ttk.Frame(content_header)
        toolbar.pack(side="right")
        
        # Export button
        export_btn = ttk.Button(
            toolbar,
            text="💾 Export",
            bootstyle="outline-secondary",
            command=self.export_flags
        )
        export_btn.pack(side="left", padx=(0, 5))
        
        # Export Orphaned Flags button
        orphaned_export_btn = ttk.Button(
            toolbar,
            text="⚠️ Export Orphaned",
            bootstyle="outline-warning",
            command=self.export_orphaned_flags_bg
        )
        orphaned_export_btn.pack(side="left", padx=(0, 5))
        
        # View options button
        view_btn = ttk.Button(
            toolbar,
            text="👀 View Options",
            command=self.show_view_options
        )
        view_btn.pack(side="left", padx=(0, 5))
        
        # Sort dropdown
        sort_frame = ttk.Frame(toolbar)
        sort_frame.pack(side="left", padx=(0, 10))
        
        ttk.Label(sort_frame, text="Sort by:", font=("Segoe UI", 9)).pack(side="left")
        self.sort_var = tk.StringVar(value="Modified ↓")
        self.sort_combo = ttk.Combobox(
            sort_frame,
            textvariable=self.sort_var,
            values=["Modified ↓", "Created ↓", "Name ↑", "Key ↑", "Health ↓", "Status"],
            state="readonly",
            width=12,
            font=("Segoe UI", 9)
        )
        self.sort_combo.pack(side="left", padx=(5, 0))
        self.sort_combo.bind("<<ComboboxSelected>>", self.on_sort_change)
        
        # Copy selected button
        self.copy_btn = ttk.Button(
            toolbar,
            text="📋 Copy Selected",
            bootstyle="outline-primary",
            command=self.copy_selected_flags,
            state="disabled"
        )
        self.copy_btn.pack(side="left")
        
        # Create container for tree and pagination with proper space distribution
        main_container = ttk.Frame(content_frame)
        main_container.pack(fill="both", expand=True)
        
        # Pagination controls - PACK FIRST to reserve space at bottom
        self.setup_pagination(main_container)
        
        # Treeview container - takes remaining space AFTER pagination
        tree_container = ttk.Frame(main_container)
        tree_container.pack(fill="both", expand=True)
        
        print("DEBUG: Tree container packed AFTER pagination")
        
        # Treeview with scrollbars in a modern card layout
        tree_frame = ttk.Frame(tree_container, style="Card.TFrame")
        tree_frame.pack(fill="both", expand=True, pady=(0, 5))
        
        # Loading frame (only shown when loading) 
        self.loading_frame = ttk.Frame(main_container)
        # Don't pack it initially - only pack when showing loading
        
        # Add some padding inside the card
        tree_content = ttk.Frame(tree_frame)
        tree_content.pack(fill="both", expand=True, padx=15, pady=(15, 5))
        
        # Enhanced treeview with more columns
        self.setup_enhanced_treeview(tree_content)
        
        # Apply saved row height after tree creation
        self.apply_saved_row_height()
        
        print("DEBUG: Layout setup completed - pagination packed first, tree second")
        
        # Force layout update to ensure pagination shows
        main_container.update_idletasks()
    
    def configure_dramatic_styling(self, row_height=None):
        """Configure dramatic visual styling for treeview with dynamic font scaling"""
        style = ttk.Style()
        try:
            colors = self.theme_manager.get_theme_config()["colors"]
        except:
            # Fallback colors if theme config fails
            colors = {
                "background": "#ffffff",
                "surface": "#f8fafc",
                "text": "#1e293b",
                "text_secondary": "#64748b"
            }
        
        # Get row height from settings if not provided
        if row_height is None:
            view_options = self.settings_manager.get_view_options()
            row_height = view_options.get("row_height", 30)
        
        # Calculate font sizes based on row height (scale between 8pt-16pt)
        # Row height 20px -> 8pt font, Row height 100px -> 16pt font
        content_font_size = max(8, min(16, int(8 + (row_height - 20) * 8 / 80)))
        header_font_size = content_font_size + 1
        
        print(f"DEBUG: Row height: {row_height}px, Content font: {content_font_size}pt, Header font: {header_font_size}pt")
        
        # Dynamic row height and modern styling with scaled fonts
        style.configure("Enhanced.Treeview",
                       rowheight=row_height,
                       font=("Segoe UI", content_font_size),
                       fieldbackground="#ffffff",
                       borderwidth=2,
                       relief="solid",
                       background="#ffffff")
        
        # Enhanced header styling with scaled fonts and padding
        header_padding_x = max(10, row_height // 3)
        header_padding_y = max(6, row_height // 5)
        style.configure("Enhanced.Treeview.Heading",
                       font=("Segoe UI", header_font_size, "bold"),
                       relief="flat",
                       borderwidth=2,
                       background="#e2e8f0",
                       foreground="#1e293b",
                       padding=(header_padding_x, header_padding_y))
    
    def configure_row_tags(self):
        """Configure row tags for color coding after treeview creation"""
        # DRAMATIC color-coded health styling with BIGGER fonts
        self.tree.tag_configure("healthy", 
                               foreground="#065f46",  # Dark green
                               background="#d1fae5",   # Light green background
                               font=("Segoe UI", 14, "bold"))
        self.tree.tag_configure("warning", 
                               foreground="#92400e",  # Dark orange
                               background="#fef3c7",   # Light orange background
                               font=("Segoe UI", 14, "bold"))
        self.tree.tag_configure("critical", 
                               foreground="#991b1b",  # Dark red
                               background="#fee2e2",   # Light red background
                               font=("Segoe UI", 14, "bold"))
        
        # STRIKING row alternation with clear distinction and BIGGER fonts
        self.tree.tag_configure("evenrow", 
                               background="#f1f5f9",  # Slightly darker blue-gray
                               font=("Segoe UI", 14))
        self.tree.tag_configure("oddrow", 
                               background="#ffffff",  # Pure white
                               font=("Segoe UI", 14))
        
        # DRAMATIC flag type backgrounds with consistent fonts
        self.tree.tag_configure("active_flag",
                               background="#ecfdf5",    # Light green tint
                               foreground="#065f46",
                               font=("Segoe UI", 14))
        self.tree.tag_configure("archived_flag",
                               background="#fef2f2",    # Light red tint
                               foreground="#991b1b",
                               font=("Segoe UI", 14))
        self.tree.tag_configure("orphaned_flag",
                               background="#fffbeb",    # Light yellow tint
                               foreground="#92400e",
                               font=("Segoe UI", 14))
        
        # STRIKING hover effect
        self.tree.tag_configure("hover",
                               background="#dbeafe",    # Blue hover
                               foreground="#1d4ed8",
                               font=("Segoe UI", 14, "bold"))
        
        # HIGH-PRIORITY flag highlighting
        self.tree.tag_configure("high_priority",
                               background="#fef2f2",
                               foreground="#991b1b",
                               font=("Segoe UI", 14, "bold"))
        
        # RECENTLY MODIFIED highlighting  
        self.tree.tag_configure("recent",
                               background="#f0f9ff",
                               foreground="#1e40af",
                               font=("Segoe UI", 14, "italic"))
    
    def setup_enhanced_treeview(self, parent):
        """Setup enhanced treeview with environment status columns"""
        
        # FIRST: Configure the dramatic visual styling BEFORE creating treeview
        self.configure_dramatic_styling()
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(parent, orient="vertical")
        v_scroll.pack(side="right", fill="y")
        
        h_scroll = ttk.Scrollbar(parent, orient="horizontal")
        h_scroll.pack(side="bottom", fill="x")
        
        # Enhanced columns with better organization (removed environment columns since API doesn't support them)
        columns = (
            "key", "name", "status", "health", "description", 
            "created", "modified", "tags"
        )
        
        self.tree = ttk.Treeview(
            parent,
            columns=columns,
            show="headings",
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set,
            style="Enhanced.Treeview"
        )
        
        # Configure scrollbars
        v_scroll.config(command=self.tree.yview)
        h_scroll.config(command=self.tree.xview)
        
        # MASSIVE column configuration for 14pt fonts and 40px rows (removed environment columns)
        column_config = {
            "key": ("🔑 Flag Key", 400, True, "w"),
            "name": ("📝 Name", 320, True, "w"),
            "status": ("📊 Status", 140, False, "center"),
            "health": ("❤️ Health", 140, False, "center"),
            "description": ("📋 Description", 500, True, "w"),
            "created": ("📅 Created", 150, False, "center"),
            "modified": ("🕐 Modified", 150, False, "center"),
            "tags": ("🏷️ Tags", 240, False, "w")
        }
        
        for col, (heading, width, stretch, anchor) in column_config.items():
            self.tree.heading(col, text=heading, anchor="w")
            self.tree.column(col, width=width, minwidth=width//2, stretch=stretch, anchor=anchor)
        
        # Apply row tags for color coding (done after treeview creation)
        self.configure_row_tags()
        
        # Force style update to ensure dramatic styling takes effect
        self.tree.update_idletasks()
        
        # Pack with additional padding for dramatic spacing
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Event bindings
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.on_right_click)
        self.tree.bind("<<TreeviewSelect>>", self.on_selection_change)
        self.tree.bind("<Motion>", self.on_mouse_motion)
        self.tree.bind("<Leave>", self.on_mouse_leave)
        
        # Track hover state
        self.hovered_item = None
        
        # Context menu
        self.setup_context_menu()
    
    def setup_context_menu(self):
        """Setup right-click context menu"""
        self.context_menu = tk.Menu(self.parent, tearoff=0)
        self.context_menu.add_command(label="📋 Copy Flag Key", command=self.copy_flag_key)
        self.context_menu.add_command(label="📋 Copy Flag Name", command=self.copy_flag_name)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🌐 Open in LaunchDarkly", command=self.open_in_launchdarkly)
        self.context_menu.add_command(label="📄 Show Details", command=self.show_flag_details)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🔄 Refresh", command=self.refresh_data)
    
    def setup_pagination(self, parent):
        """Setup enhanced pagination controls"""
        print("DEBUG: Setting up pagination controls...")  # Debug
        
        print("DEBUG: Creating pagination at bottom of parent frame")
        
        # Create a SUPER PROMINENT pagination card that RESERVES space
        pagination_card = tk.Frame(parent, relief="solid", borderwidth=3, bg="#e2e8f0")
        pagination_card.pack(side="bottom", fill="x", pady=(15, 5), padx=10)  # Pack at BOTTOM first
        
        print("DEBUG: Pagination card created and packed at bottom")
        
        # Add highly visible background color 
        pagination_frame = tk.Frame(pagination_card, bg="#f1f5f9", relief="flat", bd=0, height=40)
        pagination_frame.pack(fill="x", padx=25, pady=25)
        pagination_frame.pack_propagate(False)  # Don't shrink below height=40
        
        print("DEBUG: Pagination frame created with fixed height")
        
        # Page size selector (left side)
        size_frame = tk.Frame(pagination_frame, bg="#f8fafc")
        size_frame.pack(side="left")
        
        tk.Label(size_frame, text="📊 Items per page:", font=("Segoe UI", 11), bg="#f8fafc").pack(side="left")
        
        self.page_size_var = tk.StringVar(value="20")
        page_size_combo = ttk.Combobox(
            size_frame,
            textvariable=self.page_size_var,
            values=["10", "20", "50", "100"],
            state="readonly",
            width=8,
            font=("Segoe UI", 11)
        )
        page_size_combo.pack(side="left", padx=(8, 0))
        page_size_combo.bind("<<ComboboxSelected>>", self.on_page_size_change)
        
        print("DEBUG: Page size selector created")  # Debug
        
        # Pagination controls (centered)
        page_controls = tk.Frame(pagination_frame, bg="#f8fafc")
        page_controls.pack(expand=True)
        
        print("DEBUG: Page controls frame created")  # Debug
        
        self.prev_btn = ttk.Button(
            page_controls,
            text="◀ Previous",
            command=self.previous_page,
            width=12
        )
        self.prev_btn.pack(side="left", padx=8)
        
        print("DEBUG: Previous button created")  # Debug
        
        # Initialize page info variable
        if not hasattr(self, 'page_info_var'):
            self.page_info_var = tk.StringVar(value="Page 1 of 1")
        
        page_info_label = tk.Label(
            page_controls,
            textvariable=self.page_info_var,
            font=("Segoe UI", 12, "bold"),
            fg="#2563eb",
            bg="#f8fafc"
        )
        page_info_label.pack(side="left", padx=25)
        
        print("DEBUG: Page info label created")  # Debug
        
        self.next_btn = ttk.Button(
            page_controls,
            text="Next ▶",
            command=self.next_page,
            width=12
        )
        self.next_btn.pack(side="left", padx=8)
        
        print("DEBUG: Next button created")  # Debug
        
        # Quick stats on the right
        stats_frame = tk.Frame(pagination_frame, bg="#f8fafc")
        stats_frame.pack(side="right")
        
        # Add total items counter
        if not hasattr(self, 'total_items_var'):
            self.total_items_var = tk.StringVar(value="📋 Total: 0 flags")
        
        total_label = tk.Label(
            stats_frame,
            textvariable=self.total_items_var,
            font=("Segoe UI", 11),
            fg="#64748b",
            bg="#f8fafc"
        )
        total_label.pack(side="right")
        
        print("DEBUG: Pagination setup completed successfully!")  # Debug
    
    def setup_status_bar(self, parent):
        """Setup status bar"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill="x", pady=(20, 0))
        
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 10)
        ).pack(side="left")
        
        # Performance indicator
        self.performance_var = tk.StringVar(value="")
        ttk.Label(
            status_frame,
            textvariable=self.performance_var,
            font=("Segoe UI", 9)
        ).pack(side="right")
    
    # Event Handlers
    def on_search_change(self, event=None):
        """Handle search input changes"""
        self.filter_query = self.search_var.get().strip().lower()
        self.page_number = 1
        self.apply_filters_and_pagination()
    
    def clear_search(self):
        """Clear search field"""
        self.search_var.set("")
        self.filter_query = None
        self.page_number = 1
        self.apply_filters_and_pagination()
    
    def on_filter_change(self, event=None):
        """Handle filter changes"""
        self.status_filter = self.status_filter_var.get()
        self.env_filter = self.env_filter_var.get()
        self.health_filter = self.health_filter_var.get()
        self.page_number = 1
        self.apply_filters_and_pagination()
    
    def on_sort_change(self, event=None):
        """Handle sort option changes"""
        sort_option = self.sort_var.get()
        
        # Map UI sort options to API sort parameters
        sort_mapping = {
            "Modified ↓": "modified",
            "Created ↓": "created", 
            "Name ↑": "name",
            "Key ↑": "key",
            "Health ↓": "health",
            "Status": "status"
        }
        
        sort_by = sort_mapping.get(sort_option, "modified")
        
        # Re-fetch data with new sorting
        self.show_loading(f"Sorting by {sort_option.replace(' ↓', '').replace(' ↑', '')}...")
        
        def fetch_sorted_data():
            try:
                # Clear cache and fetch with new sorting
                self.api_client.clear_cache()
                flags = self.api_client.get_all_flags(sort_by=sort_by)
                stats = self.api_client.get_flag_statistics()
                perf_stats = self.api_client.get_performance_stats()
                
                self.operation_queue.put({
                    "type": "refresh_complete",
                    "flags": flags,
                    "stats": stats,
                    "performance": perf_stats
                })
            except Exception as e:
                self.operation_queue.put({
                    "type": "error",
                    "message": f"Failed to sort data: {str(e)}"
                })
        
        thread = threading.Thread(target=fetch_sorted_data, daemon=True)
        thread.start()
        self.check_operation_queue()
    
    def on_page_size_change(self, event=None):
        """Handle page size change"""
        self.page_size = int(self.page_size_var.get())
        self.page_number = 1
        self.apply_filters_and_pagination()
    
    def on_double_click(self, event):
        """Handle double-click on tree item"""
        self.copy_flag_key()
    
    def on_right_click(self, event):
        """Handle right-click on tree item"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()
    
    def on_selection_change(self, event):
        """Handle tree selection changes"""
        selected = self.tree.selection()
        if len(selected) == 1:
            item = selected[0]
            flag_key = self.tree.item(item)["values"][0]
            # Remove indicators from flag key for display
            clean_key = flag_key.replace("⏰ ", "").replace("⚠️ ", "")
            self.results_info_var.set(f"Selected: {clean_key}")
            self.copy_btn.config(state="normal")
        elif len(selected) > 1:
            self.results_info_var.set(f"{len(selected)} flags selected")
            self.copy_btn.config(state="normal")
        else:
            self.update_results_info()
            self.copy_btn.config(state="disabled")
    
    def on_recent_flag_select(self, event):
        """Handle selection of recent flag"""
        selection = self.recent_listbox.curselection()
        if selection:
            flag_key = self.recent_listbox.get(selection[0])
            self.search_var.set(flag_key)
            self.on_search_change()
    
    def on_orphaned_flag_select(self, event):
        """Handle selection of orphaned flag"""
        selection = self.orphaned_listbox.curselection()
        if selection:
            flag_key = self.orphaned_listbox.get(selection[0])
            self.search_var.set(flag_key)
            self.on_search_change()
    
    def on_mouse_motion(self, event):
        """Handle mouse motion for hover effects"""
        item = self.tree.identify_row(event.y)
        
        # Remove previous hover effect with error handling
        if self.hovered_item and self.hovered_item != item:
            try:
                current_tags = list(self.tree.item(self.hovered_item, "tags"))
                if "hover" in current_tags:
                    current_tags.remove("hover")
                    self.tree.item(self.hovered_item, tags=current_tags)
            except tk.TclError:
                # Item no longer exists (tree was refreshed)
                pass
        
        # Add hover effect to current item with error handling
        if item and item != self.hovered_item:
            try:
                current_tags = list(self.tree.item(item, "tags"))
                if "hover" not in current_tags:
                    current_tags.append("hover")
                    self.tree.item(item, tags=current_tags)
                
                self.hovered_item = item
            except tk.TclError:
                # Item no longer exists (tree was refreshed)
                self.hovered_item = None
    
    def on_mouse_leave(self, event):
        """Handle mouse leaving the treeview"""
        if self.hovered_item:
            try:
                current_tags = list(self.tree.item(self.hovered_item, "tags"))
                if "hover" in current_tags:
                    current_tags.remove("hover")
                    self.tree.item(self.hovered_item, tags=current_tags)
            except tk.TclError:
                # Item no longer exists (tree was refreshed)
                pass
            self.hovered_item = None
    
    # Data Operations
    def refresh_data(self):
        """Refresh all data from API"""
        self.show_loading("Refreshing flag data...")
        
        def fetch_data():
            try:
                # Clear cache to get fresh data
                self.api_client.clear_cache()
                
                # Get current sort preference
                sort_option = getattr(self, 'sort_var', None)
                if sort_option:
                    sort_mapping = {
                        "Modified ↓": "modified",
                        "Created ↓": "created", 
                        "Name ↑": "name",
                        "Key ↑": "key",
                        "Health ↓": "health",
                        "Status": "status"
                    }
                    sort_by = sort_mapping.get(sort_option.get(), "modified")
                else:
                    sort_by = "modified"
                
                # Fetch flags and statistics with sorting
                flags = self.api_client.get_all_flags(sort_by=sort_by)
                stats = self.api_client.get_flag_statistics()
                perf_stats = self.api_client.get_performance_stats()
                
                self.operation_queue.put({
                    "type": "refresh_complete",
                    "flags": flags,
                    "stats": stats,
                    "performance": perf_stats
                })
            except Exception as e:
                self.operation_queue.put({
                    "type": "error",
                    "message": f"Failed to refresh data: {str(e)}"
                })
        
        thread = threading.Thread(target=fetch_data, daemon=True)
        thread.start()
        
        # Check for results
        self.check_operation_queue()
    
    def check_operation_queue(self):
        """Check for completed operations"""
        try:
            result = self.operation_queue.get_nowait()
            
            if result["type"] == "refresh_complete":
                self.all_flags = result["flags"]
                self.flag_statistics = result["stats"]
                self.performance_stats = result["performance"]
                
                self.update_ui_after_refresh()
                self.hide_loading()
                self.toast.show_success(f"Refreshed {len(self.all_flags)} flags")
                
            elif result["type"] == "error":
                self.hide_loading()
                self.toast.show_error(result["message"])
                
        except queue.Empty:
            # Check again in 100ms
            self.parent.after(100, self.check_operation_queue)
    
    def update_ui_after_refresh(self):
        """Update UI components after data refresh"""
        # Update stats bar
        self.update_stats_bar()
        
        # Update environment filter
        self.update_environment_filter()
        
        # Update sidebar insights
        self.update_sidebar_insights()
        
        # Update performance stats
        self.update_performance_display()
        
        # Apply filters and update display
        self.apply_filters_and_pagination()
        
        # Update status
        self.status_var.set(f"Loaded {len(self.all_flags)} flags")
    
    def update_stats_bar(self):
        """Update the quick statistics bar"""
        stats = self.flag_statistics
        
        self.stats_labels["total"].config(text=str(stats.get("total_flags", 0)))
        self.stats_labels["active"].config(text=str(stats.get("active_flags", 0)))
        self.stats_labels["archived"].config(text=str(stats.get("archived_flags", 0)))
        self.stats_labels["orphaned"].config(text=str(stats.get("orphaned_flags", 0)))
        self.stats_labels["health"].config(text=f"{stats.get('health_score_avg', 0):.0f}%")
    
    def update_environment_filter(self):
        """Update environment filter dropdown"""
        environments = set()
        for flag in self.all_flags:
            env_status = flag.get("environmentStatus", {})
            environments.update(env_status.keys())
        
        env_values = ["All"] + sorted(environments)
        self.env_combo.config(values=env_values)
    
    def update_sidebar_insights(self):
        """Update sidebar insights sections"""
        # Recently modified flags
        recent_flags = [
            f for f in self.all_flags
            if f.get("lastModifiedDateTime") and
            (datetime.now() - f["lastModifiedDateTime"]).days <= 7
        ]
        recent_flags.sort(key=lambda x: x.get("lastModifiedDateTime", datetime.min), reverse=True)
        
        self.recent_listbox.delete(0, tk.END)
        for flag in recent_flags[:10]:  # Top 10 recent
            self.recent_listbox.insert(tk.END, flag["key"])
        
        # Orphaned flags
        orphaned_flags = [f for f in self.all_flags if f.get("isOrphaned", False)]
        
        self.orphaned_listbox.delete(0, tk.END)
        for flag in orphaned_flags[:10]:  # Top 10 orphaned
            self.orphaned_listbox.insert(tk.END, flag["key"])
    
    def update_performance_display(self):
        """Update performance statistics display"""
        perf = getattr(self, 'performance_stats', {})
        
        for key in self.perf_labels:
            if key == "cache_hit_rate":
                value = f"{perf.get(key, 0)}%"
            else:
                value = str(perf.get(key, 0))
            self.perf_labels[key].config(text=value)
        
        # Update status bar performance indicator
        requests = perf.get("requests_made", 0)
        cache_rate = perf.get("cache_hit_rate", 0)
        self.performance_var.set(f"API Requests: {requests} | Cache Hit Rate: {cache_rate}%")
    
    def apply_filters_and_pagination(self):
        """Apply all filters and update display"""
        filtered_flags = self.all_flags.copy()
        
        # Text search filter
        if self.filter_query:
            filtered_flags = [
                f for f in filtered_flags
                if (self.filter_query in f.get("key", "").lower() or
                    self.filter_query in f.get("name", "").lower() or
                    self.filter_query in f.get("description", "").lower() or
                    any(self.filter_query in tag.lower() for tag in f.get("tags", [])))
            ]
        
        # Status filter
        if self.status_filter != "All":
            if self.status_filter == "Active":
                filtered_flags = [f for f in filtered_flags if f.get("status") == "Active"]
            elif self.status_filter == "Archived":
                filtered_flags = [f for f in filtered_flags if f.get("status") == "Archived"]
        
        # Environment filter
        if self.env_filter != "All":
            filtered_flags = [
                f for f in filtered_flags
                if self.env_filter in f.get("environmentStatus", {})
            ]
        
        # Health filter
        if self.health_filter != "All":
            if "Healthy" in self.health_filter:
                filtered_flags = [f for f in filtered_flags if f.get("healthScore", 0) >= 40]
            elif "Warning" in self.health_filter:
                filtered_flags = [f for f in filtered_flags if 50 <= f.get("healthScore", 0) < 40]
            elif "Critical" in self.health_filter:
                filtered_flags = [f for f in filtered_flags if f.get("healthScore", 0) < 50]
        
        self.displayed_flags = filtered_flags
        
        # Update pagination
        self.total_pages = max(1, (len(self.displayed_flags) + self.page_size - 1) // self.page_size)
        self.page_number = min(self.page_number, self.total_pages)
        
        # Update display
        self.update_treeview()
        self.update_pagination_controls()
        self.update_results_info()
    

    def export_orphaned_flags_bg(self):
        """Start background orphaned flags export with progress notifications"""
        try:
            # Confirm with user
            from tkinter import messagebox
            result = messagebox.askyesno(
                "Export Orphaned Flags", 
                "This will analyze all 811 flags to find orphaned ones.\n\n"
                "The process will run in the background and you'll get\n"
                "progress notifications. Continue?",
                icon="question"
            )
            
            if not result:
                return
            
            # Show initial notification
            self.toast.show_info("🔍 Starting orphaned flags analysis in background...")
            
            # Track progress
            self.export_progress = {
                'current': 0,
                'total': 0,
                'last_toast': 0
            }
            
            # Get API client
            from api_client import get_client
            client = get_client()
            
            # Progress callback (called for each flag)
            def on_progress(current, total, flag_key):
                self.export_progress['current'] = current
                self.export_progress['total'] = total
                
                # Show toast every 50 flags
                if current % 50 == 0 or current == 1:
                    percentage = int((current / total) * 100)
                    self.parent.after(0, lambda: self.toast.show_info(
                        f"🔍 Analyzing flags... {current}/{total} ({percentage}%)"
                    ))
            
            # Completion callback
            def on_completion(orphaned_flags, filename, error=None):
                if error:
                    self.parent.after(0, lambda: self.toast.show_error(f"❌ Export failed: {error}"))
                    return
                
                if orphaned_flags is None:
                    self.parent.after(0, lambda: self.toast.show_error("❌ Export failed: Unknown error"))
                    return
                
                count = len(orphaned_flags) if orphaned_flags else 0
                
                if count > 0:
                    self.parent.after(0, lambda: self._show_export_completion(count, filename, orphaned_flags))
                else:
                    self.parent.after(0, lambda: self.toast.show_success(
                        f"✅ Analysis complete! No orphaned flags found. Report saved: {filename}"
                    ))
            
            # Start background processing
            def run_export():
                try:
                    client.export_orphaned_flags_bg(
                        progress_callback=on_progress,
                        completion_callback=on_completion
                    )
                except Exception as e:
                    self.parent.after(0, lambda: self.toast.show_error(f"❌ Export error: {str(e)}"))
            
            # Run in background thread
            import threading
            thread = threading.Thread(target=run_export, daemon=True)
            thread.start()
            
        except Exception as e:
            self.toast.show_error(f"❌ Failed to start export: {str(e)}")
    
    def _show_export_completion(self, count, filename, orphaned_flags):
        """Show completion dialog with options to view report"""
        from tkinter import messagebox
        import os
        import subprocess
        import sys
        
        # Show completion message
        message = f"⚠️ Found {count} orphaned flags!\n\nReport saved to: {filename}\n\nWould you like to open the report?"
        
        result = messagebox.askyesnocancel(
            "Orphaned Flags Export Complete",
            message,
            icon="warning"
        )
        
        if result is True:  # Yes - open file
            try:
                if sys.platform == "win32":
                    os.startfile(filename)
                elif sys.platform == "darwin":
                    subprocess.run(["open", filename])
                else:
                    subprocess.run(["xdg-open", filename])
                
                self.toast.show_success(f"📁 Opened report: {filename}")
            except Exception as e:
                self.toast.show_error(f"❌ Could not open file: {str(e)}")
        elif result is False:  # No - just show success
            self.toast.show_success(f"✅ Export complete! {count} orphaned flags found. Report: {filename}")
        # None/Cancel - do nothing
    
    def update_treeview(self):
        """Update treeview with current page data"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Calculate page range
        start_idx = (self.page_number - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_flags = self.displayed_flags[start_idx:end_idx]
        
        # Add items to treeview
        for i, flag in enumerate(page_flags):
            self.insert_flag_row(flag, i)
    
    def insert_flag_row(self, flag: dict, index: int):
        """Insert a flag row into the treeview with enhanced formatting"""
        # Determine base row tags
        row_tag = "evenrow" if index % 2 == 0 else "oddrow"
        
        # Health-based styling
        health_score = flag.get("healthScore", 0)
        if health_score >= 40:
            health_tag = "healthy"
        elif health_score >= 50:
            health_tag = "warning"
        else:
            health_tag = "critical"
        
        # Flag type specific styling
        status = flag.get("status", "Unknown")
        if status == "Active":
            type_tag = "active_flag"
        elif status == "Archived":
            type_tag = "archived_flag"
        else:
            type_tag = "active_flag"
        
        # Add orphaned flag styling
        if flag.get("isOrphaned", False):
            type_tag = "orphaned_flag"
        
        # Add special styling for recently modified flags
        recent_tag = None
        modified_date = flag.get("lastModifiedDateTime")
        if modified_date and (datetime.now() - modified_date).days <= 3:
            recent_tag = "recent"
        
        # Add high priority styling for critical health
        priority_tag = None
        if health_score < 30:
            priority_tag = "high_priority"
        
        # Combine all tags
        tags = [row_tag, health_tag, type_tag]
        if recent_tag:
            tags.append(recent_tag)
        if priority_tag:
            tags.append(priority_tag)
        
        tags = tuple(tag for tag in tags if tag)
        
        # Enhanced environment status with better indicators
        env_status = flag.get("environmentStatus", {})
        
        # Debug: Print available environment names for the first few flags
        if hasattr(self, '_debug_env_count') and self._debug_env_count < 3:
            print(f"DEBUG: Available environments for flag {flag.get('key', 'unknown')}: {list(env_status.keys())}")
            self._debug_env_count = getattr(self, '_debug_env_count', 0) + 1
        elif not hasattr(self, '_debug_env_count'):
            self._debug_env_count = 1
            print(f"DEBUG: Available environments for flag {flag.get('key', 'unknown')}: {list(env_status.keys())}")
        
        def format_env_status(env_names):
            """Try multiple environment name variations"""
            for env_name in env_names:
                env_data = env_status.get(env_name, {})
                if env_data:
                    if env_data.get("enabled", False):
                        return "🟢"  # Enabled
                    else:
                        return "🔴"  # Disabled
            return "➖"  # No data available
        
        # Environment columns removed since API doesn't provide environment data
        # dev_status = format_env_status(["DEV", "Development", "dev"])
        # sat_status = format_env_status(["SAT", "Saturation", "sat"]) 
        # prod_status = format_env_status(["PROD", "Production", "prod"])
        
        # Enhanced date formatting
        created_date = flag.get("creationDateTime")
        if created_date:
            created_str = created_date.strftime("%m/%d/%y")
        else:
            created_str = "Unknown"
        
        modified_date = flag.get("lastModifiedDateTime")
        if modified_date:
            # Show relative time for recent modifications
            days_ago = (datetime.now() - modified_date).days
            if days_ago == 0:
                modified_str = "Today"
            elif days_ago == 1:
                modified_str = "Yesterday"
            elif days_ago < 7:
                modified_str = f"{days_ago}d ago"
            else:
                modified_str = modified_date.strftime("%m/%d/%y")
        else:
            modified_str = "Unknown"
        
        # Enhanced tags formatting with color coding
        tags_list = flag.get("tags", [])
        if not tags_list:
            tags_str = "📝 No tags"
        else:
            # Show first 2 tags with visual indicators
            formatted_tags = []
            for tag in tags_list[:2]:
                if "api" in tag.lower():
                    formatted_tags.append(f"🔌 {tag}")
                elif "feature" in tag.lower():
                    formatted_tags.append(f"⭐ {tag}")
                elif "test" in tag.lower():
                    formatted_tags.append(f"🧪 {tag}")
                else:
                    formatted_tags.append(f"🏷️ {tag}")
            
            tags_str = ", ".join(formatted_tags)
            if len(tags_list) > 2:
                tags_str += f" (+{len(tags_list) - 2} more)"
        
        # Enhanced status display with better visuals
        if status == "Active":
            status_display = "🟢 Active"
        elif status == "Archived": 
            status_display = "🔴 Archived"
        else:
            status_display = "❓ Unknown"
        
        # Enhanced health score with visual indicators
        if health_score >= 40:
            health_display = f"💚 {health_score}%"
        elif health_score >= 50:
            health_display = f"🟡 {health_score}%"
        else:
            health_display = f"🔴 {health_score}%"
        
        # Smarter description truncation
        description = flag.get("description", "")
        if len(description) > 60:
            # Try to truncate at word boundary
            truncated = description[:60].rsplit(' ', 1)[0] + "..."
        else:
            truncated = description if description else "📝 No description"
        
        # Enhanced flag key display
        flag_key = flag.get("key", "")
        if flag.get("temporary", False):
            flag_key = f"⏰ {flag_key}"
        elif flag.get("isOrphaned", False):
            flag_key = f"⚠️ {flag_key}"
        
        # Insert row with reordered columns (status and health more prominent, environment columns removed)
        values = (
            flag_key,                    # Key with indicators
            flag.get("name", ""),        # Name
            status_display,              # Status (moved up)
            health_display,              # Health (moved up)
            truncated,                   # Description (moved down)
            # Removed environment columns: dev_status, sat_status, prod_status
            created_str,                 # Created date
            modified_str,                # Modified date (relative)
            tags_str                     # Tags with icons
        )
        
        self.tree.insert("", "end", values=values, tags=tags)
    
    def update_pagination_controls(self):
        """Update pagination controls with enhanced info"""
        self.page_info_var.set(f"Page {self.page_number} of {self.total_pages}")
        
        # Update total items counter
        if hasattr(self, 'total_items_var'):
            total_displayed = len(self.displayed_flags) if hasattr(self, 'displayed_flags') else 0
            total_all = len(self.all_flags) if hasattr(self, 'all_flags') else 0
            
            if total_displayed == total_all:
                self.total_items_var.set(f"📋 Total: {total_all} flags")
            else:
                self.total_items_var.set(f"📋 Showing: {total_displayed} of {total_all}")
        
        # Update button states
        self.prev_btn.config(state="normal" if self.page_number > 1 else "disabled")
        self.next_btn.config(state="normal" if self.page_number < self.total_pages else "disabled")
    
    def update_results_info(self):
        """Update results information"""
        total = len(self.all_flags)
        filtered = len(self.displayed_flags)
        
        if filtered == total:
            self.results_info_var.set(f"Showing {total} flags")
        else:
            self.results_info_var.set(f"Showing {filtered} of {total} flags")
    
    # Pagination
    def previous_page(self):
        """Go to previous page"""
        if self.page_number > 1:
            self.page_number -= 1
            self.update_treeview()
            self.update_pagination_controls()
    
    def next_page(self):
        """Go to next page"""
        if self.page_number < self.total_pages:
            self.page_number += 1
            self.update_treeview()
            self.update_pagination_controls()
    
    # Interactive Actions
    def copy_flag_key(self):
        """Copy selected flag key to clipboard"""
        selected = self.tree.selection()
        if selected:
            flag_key = self.tree.item(selected[0])["values"][0]
            self.parent.clipboard_clear()
            self.parent.clipboard_append(flag_key)
            self.toast.show_success(f"Copied: {flag_key}")
    
    def copy_flag_name(self):
        """Copy selected flag name to clipboard"""
        selected = self.tree.selection()
        if selected:
            flag_name = self.tree.item(selected[0])["values"][1]
            self.parent.clipboard_clear()
            self.parent.clipboard_append(flag_name)
            self.toast.show_success(f"Copied: {flag_name}")
    
    def open_in_launchdarkly(self):
        """Open selected flag in LaunchDarkly"""
        selected = self.tree.selection()
        if selected:
            flag_key = self.tree.item(selected[0])["values"][0]
            url = f"https://app.launchdarkly.com/{PROJECT_KEY}/features/{flag_key}"
            webbrowser.open(url)
            self.toast.show_info(f"Opened {flag_key} in browser")
    
    def show_flag_details(self):
        """Show detailed flag information"""
        selected = self.tree.selection()
        if not selected:
            return
        
        flag_key = self.tree.item(selected[0])["values"][0]
        flag_data = next((f for f in self.all_flags if f["key"] == flag_key), None)
        
        if not flag_data:
            self.toast.show_error("Flag data not found")
            return
        
        # Create details window
        details_window = tk.Toplevel(self.parent)
        details_window.title(f"Flag Details - {flag_key}")
        details_window.geometry("700x600")
        details_window.resizable(True, True)
        
        # Main frame
        main_frame = ttk.Frame(details_window, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text=f"🚩 {flag_key}",
            font=("Segoe UI", 18, "bold")
        )
        title_label.pack(anchor="w", pady=(0, 20))
        
        # Details text widget with scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill="both", expand=True)
        
        text_widget = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            state="normal"
        )
        
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Format and insert details
        details_text = self.format_flag_details(flag_data)
        text_widget.insert("1.0", details_text)
        text_widget.config(state="disabled")
        
        # Close button
        ttk.Button(
            main_frame,
            text="Close",
            bootstyle="secondary",
            command=details_window.destroy
        ).pack(pady=(20, 0))
    
    def format_flag_details(self, flag: dict) -> str:
        """Format flag details for display"""
        details = f"""FLAG INFORMATION
================

Key: {flag.get('key', 'N/A')}
Name: {flag.get('name', 'N/A')}
Status: {flag.get('status', 'N/A')}
Health Score: {flag.get('healthScore', 0)}%
Orphaned: {'Yes' if flag.get('isOrphaned', False) else 'No'}
Temporary: {'Yes' if flag.get('temporary', False) else 'No'}

Description: {flag.get('description', 'No description')}

DATES
=====
Created: {flag.get('creationDateTime', 'N/A')}
Last Modified: {flag.get('lastModifiedDateTime', 'N/A')}

ENVIRONMENTS
============
"""
        
        env_status = flag.get("environmentStatus", {})
        for env_name, status in env_status.items():
            enabled = "✅ Enabled" if status["enabled"] else "❌ Disabled"
            rules = "📋 Has Rules" if status["has_rules"] else "📋 No Rules"
            targeting = "🎯 Has Targeting" if status["has_targeting"] else "🎯 No Targeting"
            
            details += f"\n{env_name}: {enabled} | {rules} | {targeting}"
        
        details += f"""

TAGS
====
{', '.join(flag.get('tags', ['None']))}

VARIATIONS
==========
"""
        
        variations = flag.get("variations", [])
        for i, variation in enumerate(variations):
            details += f"\n{i}: {json.dumps(variation.get('value', 'N/A'), indent=2)}"
        
        details += f"""

LINKS
=====
LaunchDarkly URL: https://app.launchdarkly.com/{PROJECT_KEY}/features/{flag.get('key', '')}
"""
        
        return details
    
    # Auto-refresh functionality
    def start_auto_refresh(self):
        """Start auto-refresh timer"""
        if self.auto_refresh_job:
            self.parent.after_cancel(self.auto_refresh_job)
        
        self.auto_refresh_job = self.parent.after(
            self.auto_refresh_interval * 1000,
            self._auto_refresh_callback
        )
    
    def stop_auto_refresh(self):
        """Stop auto-refresh timer"""
        if self.auto_refresh_job:
            self.parent.after_cancel(self.auto_refresh_job)
            self.auto_refresh_job = None
    
    def _auto_refresh_callback(self):
        """Auto-refresh callback"""
        if self.auto_refresh_enabled:
            self.refresh_data()
            self.start_auto_refresh()  # Schedule next refresh
    
    # Loading state management
    def show_loading(self, message="Loading..."):
        """Show loading spinner overlaying the content"""
        if self.loading_spinner:
            self.hide_loading()
        
        # Place loading frame OVER the tree frame, not replacing it
        self.loading_frame.place(relx=0.5, rely=0.4, anchor="center")
        self.loading_spinner = LoadingSpinner(self.loading_frame, message)
        self.loading_spinner.pack(expand=True, padx=20, pady=20)
        self.loading_spinner.start()
    
    def hide_loading(self):
        """Hide loading spinner and restore normal view"""
        if self.loading_spinner:
            self.loading_spinner.stop()
            self.loading_spinner.pack_forget()
            self.loading_frame.place_forget()  # Use place_forget instead of pack_forget
            self.loading_spinner = None
    

    
    def export_flags(self):
        """Export current filtered flags to CSV"""
        try:
            import csv
            from tkinter import filedialog
            
            if not self.displayed_flags:
                self.toast.show_error("No flags to export")
                return
            
            # Ask user for file location
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Feature Flags"
            )
            
            if not filename:
                return
            
            # Export data
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Headers (removed environment columns since API doesn't support them)
                headers = [
                    "Flag Key", "Name", "Status", "Health Score", "Description",
                    "Created", "Modified", "Tags", "Orphaned", "Temporary"
                ]
                writer.writerow(headers)
                
                # Data rows (removed environment status since API doesn't support them)
                for flag in self.displayed_flags:
                    row = [
                        flag.get("key", ""),
                        flag.get("name", ""),
                        flag.get("status", ""),
                        flag.get("healthScore", 0),
                        flag.get("description", ""),
                        # Removed environment status: DEV, SAT, PROD
                        flag.get("creationDateTime", "").strftime("%Y-%m-%d") if flag.get("creationDateTime") else "",
                        flag.get("lastModifiedDateTime", "").strftime("%Y-%m-%d") if flag.get("lastModifiedDateTime") else "",
                        ", ".join(flag.get("tags", [])),
                        "Yes" if flag.get("isOrphaned", False) else "No",
                        "Yes" if flag.get("temporary", False) else "No"
                    ]
                    writer.writerow(row)
            
            self.toast.show_success(f"Exported {len(self.displayed_flags)} flags to {filename}")
            
        except Exception as e:
            self.toast.show_error(f"Export failed: {str(e)}")
    
    def show_view_options(self):
        """Show enhanced view customization options"""
        try:
            print("DEBUG: Opening View Options dialog...")
            
            # Get the main window for proper parenting
            main_window = self.parent.winfo_toplevel()
            options_window = tk.Toplevel(main_window)
            options_window.title("🎨 View Options")
            options_window.geometry("500x700")  # Even larger for big buttons
            options_window.resizable(False, False)
            
            print("DEBUG: View Options window created")
            
            # Make it modal and center it
            options_window.transient(main_window)
            options_window.grab_set()
            
            # Center the window properly
            options_window.update_idletasks()
            x = (options_window.winfo_screenwidth() // 2) - (500 // 2)
            y = (options_window.winfo_screenheight() // 2) - (700 // 2)
            options_window.geometry(f"500x700+{x}+{y}")
            
            print("DEBUG: View Options dialog positioned and made modal")
        
            main_frame = ttk.Frame(options_window, padding=25)
            main_frame.pack(fill="both", expand=True)
            
            print("DEBUG: Main frame created")
            
            # Enhanced title with icon
            title_frame = ttk.Frame(main_frame)
            title_frame.pack(fill="x", pady=(0, 25))
            
            title_label = ttk.Label(
                title_frame,
                text="🎨 Customize View",
                font=("Segoe UI", 16, "bold")
            )
            title_label.pack()
            
            subtitle_label = ttk.Label(
                title_frame,
                text="Adjust table appearance and behavior",
                font=("Segoe UI", 10),
                foreground="#64748b"
            )
            subtitle_label.pack()
            
            # Settings info
            settings_info = ttk.Label(
                title_frame,
                text="💾 Settings will be saved to app_settings.json",
                font=("Segoe UI", 9),
                foreground="#6b7240"
            )
            settings_info.pack(pady=(5, 0))
            
            print("DEBUG: Title section created")
        
            # Row height option with current value display
            height_frame = ttk.LabelFrame(main_frame, text="📏 Row Height", padding=15)
            height_frame.pack(fill="x", pady=(0, 15))
            
            # Load current settings
            view_options = self.settings_manager.get_view_options()
            
            height_var = tk.StringVar(value=str(view_options.get("row_height", 30)))
            ttk.Label(height_frame, text="Adjust row height (fonts scale automatically):").pack(anchor="w")
            ttk.Label(height_frame, text="20px = 8pt fonts • 30px = 10pt fonts • 50px = 12pt fonts • 100px = 16pt fonts", 
                     font=("Segoe UI", 8), foreground="#6b7280").pack(anchor="w", pady=(2, 5))
            
            height_scale = ttk.Scale(
                height_frame,
                from_=20,
                to=100,
                variable=height_var,
                orient="horizontal"
            )
            height_scale.pack(fill="x", pady=(8, 5))
            
            current_height = view_options.get("row_height", 30)
            height_value_label = ttk.Label(height_frame, text=f"Current: {current_height}px", font=("Segoe UI", 9))
            height_value_label.pack()
            
            def update_height_display(val):
                try:
                    height_value_label.config(text=f"Current: {int(float(val))}px")
                except:
                    pass
            
            height_scale.config(command=update_height_display)
            
            print("DEBUG: Row height section created")
        
            # Color theme option
            theme_frame = ttk.LabelFrame(main_frame, text="🎨 Color Theme", padding=15)
            theme_frame.pack(fill="x", pady=(0, 15))
            
            ttk.Label(theme_frame, text="Choose visual appearance:").pack(anchor="w")
            theme_var = tk.StringVar(value=view_options.get("color_theme", "Enhanced (Current)"))
            theme_combo = ttk.Combobox(
                theme_frame,
                textvariable=theme_var,
                values=["Enhanced (Current)", "High Contrast", "Colorful", "Minimal", "Dark Mode"],
                state="readonly",
                font=("Segoe UI", 10)
            )
            theme_combo.pack(fill="x", pady=(8, 0))
            
            print("DEBUG: Color theme section created")
            
            # Auto-refresh interval
            refresh_frame = ttk.LabelFrame(main_frame, text="🔄 Auto-refresh", padding=15)
            refresh_frame.pack(fill="x", pady=(0, 20))
            
            ttk.Label(refresh_frame, text="Automatic data refresh interval:").pack(anchor="w")
            
            # Set interval based on settings
            current_interval = view_options.get("auto_refresh_interval", 30)
            auto_refresh_enabled = view_options.get("auto_refresh_enabled", True)
            
            if auto_refresh_enabled:
                interval_value = str(current_interval)
            else:
                interval_value = "Disabled"
                
            interval_var = tk.StringVar(value=interval_value)
            interval_combo = ttk.Combobox(
                refresh_frame,
                textvariable=interval_var,
                values=["Disabled", "15", "30", "60", "120", "300"],
                state="readonly",
                font=("Segoe UI", 10)
            )
            interval_combo.pack(fill="x", pady=(8, 0))
            
            print("DEBUG: Auto-refresh section created")
        
            # Separator line before buttons
            separator = ttk.Separator(main_frame, orient="horizontal")
            separator.pack(fill="x", pady=(20, 15))
            
            # Enhanced buttons with better layout and visibility
            button_frame = tk.Frame(main_frame, bg="#f8fafc", relief="solid", borderwidth=1, height=80)
            button_frame.pack(fill="x", pady=(15, 25), padx=5)
            button_frame.pack_propagate(False)  # Don't shrink below height=80
            
            print("DEBUG: Button frame created and packed with visible background and fixed height")
            
            def apply_options():
                try:
                    print("DEBUG: Applying view options...")
                    
                    # Get values from form
                    new_height = int(float(height_var.get()))
                    new_theme = theme_var.get()
                    interval_val = interval_var.get()
                    
                    # Determine auto-refresh settings
                    if interval_val == "Disabled":
                        auto_refresh_enabled = False
                        auto_refresh_interval = 30  # Default for when re-enabled
                    else:
                        auto_refresh_enabled = True
                        auto_refresh_interval = int(interval_val)
                    
                    # Save settings to file
                    settings_saved = self.settings_manager.update_view_options(
                        row_height=new_height,
                        theme=new_theme, 
                        auto_refresh_enabled=auto_refresh_enabled,
                        auto_refresh_interval=auto_refresh_interval
                    )
                    
                    if settings_saved:
                        print("DEBUG: Settings saved successfully")
                    else:
                        print("DEBUG: Warning - settings may not have saved properly")
                    
                    # Apply settings to current UI with dynamic font scaling
                    self.configure_dramatic_styling(row_height=new_height)
                    
                    print(f"DEBUG: Row height and fonts updated to {new_height}px")
                    
                    # Apply auto-refresh settings to current instance
                    self.auto_refresh_enabled = auto_refresh_enabled
                    self.auto_refresh_interval = auto_refresh_interval
                    
                    if auto_refresh_enabled:
                        print(f"DEBUG: Auto-refresh enabled: {auto_refresh_interval}s")
                    else:
                        print("DEBUG: Auto-refresh disabled")
                    
                    # Force tree update
                    if hasattr(self, 'tree'):
                        self.tree.update_idletasks()
                    
                    # Show success message
                    if settings_saved:
                        self.toast.show_success(f"✅ Settings saved! Row height: {new_height}px, Theme: {new_theme}, Refresh: {interval_val}")
                    else:
                        self.toast.show_success(f"✅ View updated temporarily! Row height: {new_height}px, Refresh: {interval_val}")
                    
                    options_window.destroy()
                    print("DEBUG: View options applied successfully")
                    
                except Exception as e:
                    print(f"DEBUG: Error applying options: {e}")
                    self.toast.show_error(f"❌ Failed to apply: {str(e)}")
            
            def reset_defaults():
                try:
                    print("DEBUG: Resetting to defaults...")
                    
                    # Reset form values
                    height_var.set("30")
                    theme_var.set("Enhanced (Current)")
                    interval_var.set("30")
                    update_height_display("30")
                    
                    # Reset settings file to defaults
                    self.settings_manager.reset_to_defaults()
                    
                    print("DEBUG: Defaults reset and saved")
                    self.toast.show_info("🔄 Settings reset to defaults")
                    
                except Exception as e:
                    print(f"DEBUG: Error resetting defaults: {e}")
                    self.toast.show_error(f"❌ Failed to reset: {str(e)}")
            
            print("DEBUG: Creating buttons...")
            
            # Button layout with LARGER buttons for better visibility and usability
            reset_btn = tk.Button(
                button_frame,
                text="🔄 Reset Defaults",
                command=reset_defaults,
                bg="#e5e7eb",
                fg="#374151",
                font=("Segoe UI", 11, "bold"),
                relief="raised",
                borderwidth=3,
                padx=20,
                pady=12,
                cursor="hand2"
            )
            reset_btn.pack(side="left", padx=15, pady=15)
            print("DEBUG: Reset button created and packed")
            
            # Spacer to push Apply and Cancel to the right
            spacer = tk.Frame(button_frame, bg="#f8fafc")
            spacer.pack(side="left", fill="x", expand=True)
            
            apply_btn = tk.Button(
                button_frame,
                text="✅ Apply Changes",
                command=apply_options,
                bg="#10b981", 
                fg="white",
                font=("Segoe UI", 11, "bold"),
                relief="raised",
                borderwidth=3,
                padx=25,
                pady=12,
                cursor="hand2"
            )
            apply_btn.pack(side="right", padx=(15, 10), pady=15)
            print("DEBUG: Apply button created and packed")
            
            cancel_btn = tk.Button(
                button_frame,
                text="❌ Cancel", 
                command=options_window.destroy,
                bg="#ef4444",
                fg="white",
                font=("Segoe UI", 11, "bold"),
                relief="raised",
                borderwidth=3,
                padx=20,
                pady=12,
                cursor="hand2"
            )
            cancel_btn.pack(side="right", padx=(10, 15), pady=15)
            print("DEBUG: Cancel button created and packed")
            
            print("DEBUG: All buttons created and packed successfully!")
            
            # Force layout update and show dimensions for debugging
            options_window.update_idletasks()
            button_frame.update_idletasks()
            
            print(f"DEBUG: Dialog size: {options_window.winfo_width()}x{options_window.winfo_height()}")
            print(f"DEBUG: Expected button frame should be larger and more prominent now")
            print(f"DEBUG: Button frame size: {button_frame.winfo_width()}x{button_frame.winfo_height()}")
            print(f"DEBUG: Button frame position: x={button_frame.winfo_x()}, y={button_frame.winfo_y()}")
            
            print("DEBUG: View Options dialog fully created and ready")
            
            # Focus on the dialog
            options_window.focus_set()
            
        except Exception as e:
            print(f"DEBUG: Error creating View Options dialog: {e}")
            self.toast.show_error(f"Failed to open View Options: {str(e)}")
    
    def copy_selected_flags(self):
        """Copy selected flag keys to clipboard"""
        selected = self.tree.selection()
        if not selected:
            self.toast.show_error("No flags selected")
            return
        
        try:
            flag_keys = []
            for item in selected:
                flag_key = self.tree.item(item)["values"][0]
                # Remove indicators from flag key
                clean_key = flag_key.replace("⏰ ", "").replace("⚠️ ", "")
                flag_keys.append(clean_key)
            
            # Copy to clipboard
            clipboard_text = "\n".join(flag_keys)
            self.parent.clipboard_clear()
            self.parent.clipboard_append(clipboard_text)
            
            if len(flag_keys) == 1:
                self.toast.show_success(f"Copied: {flag_keys[0]}")
            else:
                self.toast.show_success(f"Copied {len(flag_keys)} flag keys")
                
        except Exception as e:
            self.toast.show_error(f"Copy failed: {str(e)}")
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_auto_refresh()
        if hasattr(self.api_client, 'session'):
            self.api_client.session.close()

# Backward compatibility alias
ViewTab = EnhancedViewTab
