import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox
import logging
import requests
import webbrowser
from shared.config_loader import LAUNCHDARKLY_API_KEY, PROJECT_KEY, LOG_FILE
from api_config.api_endpoints import LAUNCHDARKLY_BASE_URL
from shared.constants import ENVIRONMENT_MAPPINGS
try:
    from shared.constants import READ_ENVIRONMENT_OPTIONS
except ImportError:
    # Failsafe - define READ_ENVIRONMENT_OPTIONS locally if import fails
    READ_ENVIRONMENT_OPTIONS = ["DEV", "OCRT", "SAT", "PROD"]
from api_client import get_client
import json
import time
from shared.audit import audit_event

# Module logger for this UI module
logger = logging.getLogger(__name__)

class GetTab:
    def __init__(self, parent, history_manager, theme_manager):
        self.parent = parent
        self.history_manager = history_manager
        self.theme_manager = theme_manager
        # Initialize optimized API client
        self.api_client = get_client()
        # Keep last result for summary banner
        self.last_flag_data = None
        # Track running animation jobs per canvas to allow cancellation
        self._anim_jobs = {}
        self.setup_ui()

    def setup_ui(self):
        """Sets up the UI for the 'Get Feature Flag' tab with a professional layout."""
        # --- Main container frame ---
        get_frame = ttk.Frame(self.parent, padding=30)
        get_frame.pack(fill="both", expand=True)

        # --- Header Section ---
        header_frame = ttk.Frame(get_frame)
        header_frame.pack(fill="x", pady=(0, 30))
        
        # Title with icon
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(anchor="w")
        
        title_label = ttk.Label(
            title_frame, 
            text="📋 Get Feature Flag Status", 
            font=("Segoe UI", 24, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        title_label.pack(anchor="w")
        
        subtitle_label = ttk.Label(
            title_frame,
            text="Retrieve feature flag information from LaunchDarkly API",
            font=("Segoe UI", 12),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        subtitle_label.pack(anchor="w", pady=(5, 0))

        # --- Input Fields Section ---
        self.input_container = ttk.Frame(get_frame)
        self.input_container.pack(fill="x", pady=(0, 25))
        
        # Create a modern card-like frame
        input_frame = ttk.Frame(self.input_container, style="Content.TFrame")
        input_frame.pack(fill="x", padx=5)
        
        # Card header
        self.card_header = ttk.Frame(input_frame)
        self.card_header.pack(fill="x", padx=25, pady=(20, 15))
        
        card_title = ttk.Label(
            self.card_header,
            text="🔧 Configuration",
            font=("Segoe UI", 16, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        card_title.pack(side="left", anchor="w")
        # Collapse/Expand button for input card
        self.input_collapsed = False
        def _toggle_input():
            try:
                if self.input_collapsed:
                    # Smooth expand
                    self._expand_input(animated=True)
                else:
                    # Smooth collapse
                    self._collapse_input(animated=True)
            except Exception as e:
                logger.debug(f"toggle_input error: {e}")
        self.collapse_btn = ttk.Button(self.card_header, text="Collapse", width=10, command=_toggle_input)
        self.collapse_btn.pack(side="right")

        # Animated container for input content (form + actions)
        # This enables smooth collapse/expand of the top card contents
        self.input_anim_canvas = tk.Canvas(
            input_frame,
            height=1,
            highlightthickness=0,
            bg=self.theme_manager.get_theme_config()["colors"]["background"],
            borderwidth=0,
        )
        # Inner content frame that holds the form and action sections
        self.input_content = ttk.Frame(self.input_anim_canvas)
        self._input_anim_id = self.input_anim_canvas.create_window((0, 0), window=self.input_content, anchor="nw")
        self.input_anim_canvas.pack(fill="x")
        # Keep canvas width synced with parent
        def _on_input_canvas_cfg(event):
            try:
                self.input_anim_canvas.itemconfigure(self._input_anim_id, width=event.width)
            except Exception:
                pass
        self.input_anim_canvas.bind("<Configure>", _on_input_canvas_cfg)

        # Form fields with better layout
        self.form_frame = ttk.Frame(self.input_content)
        self.form_frame.pack(fill="x", padx=25, pady=(0, 25))
        
        # Two-column layout for better organization
        left_column = ttk.Frame(self.form_frame)
        left_column.pack(side="left", fill="x", expand=True, padx=(0, 15))
        
        right_column = ttk.Frame(self.form_frame)
        right_column.pack(side="right", fill="x", expand=True, padx=(15, 0))

        # Left column fields
        # Feature Flag Key
        key_frame = ttk.Frame(left_column)
        key_frame.pack(fill="x", pady=8)
        
        key_label = ttk.Label(
            key_frame, 
            text="🔑 Feature Flag Key", 
            font=("Segoe UI", 11, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        key_label.pack(anchor="w", pady=(0, 5))
        
        self.key_var = tk.StringVar()
        self.key_var.trace_add("write", self.on_input_data_change)
        
        key_combobox = ttk.Combobox(
            key_frame, 
            textvariable=self.key_var, 
            values=self.history_manager.get_history().get("get_keys", []),
            font=("Segoe UI", 11)
        )
        key_combobox.pack(fill="x", pady=(0, 5))

        # Environment
        env_frame = ttk.Frame(left_column)
        env_frame.pack(fill="x", pady=8)
        
        env_label = ttk.Label(
            env_frame, 
            text="🌍 Environment", 
            font=("Segoe UI", 11, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        env_label.pack(anchor="w", pady=(0, 5))
        
        self.env_var = tk.StringVar(value="DEV")
        self.env_entry = ttk.Combobox(
            env_frame, 
            textvariable=self.env_var,
            values=READ_ENVIRONMENT_OPTIONS, 
            font=("Segoe UI", 11),
            state="readonly",
            height=8
        )
        self.env_entry.pack(fill="x", pady=(0, 5))

        # Right column fields
        # PMC ID field
        pmcid_frame = ttk.Frame(right_column)
        pmcid_frame.pack(fill="x", pady=8)
        
        pmcid_label = ttk.Label(
            pmcid_frame, 
            text="🏢 PMC ID (Optional)", 
            font=("Segoe UI", 11, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        pmcid_label.pack(anchor="w", pady=(0, 5))
        
        self.pmcid_var = tk.StringVar()
        self.pmcid_entry = ttk.Entry(
            pmcid_frame, 
            textvariable=self.pmcid_var, 
            font=("Segoe UI", 11)
        )
        self.pmcid_entry.pack(fill="x", pady=(0, 2))
        
        # Helper text for PMCID
        pmcid_help = ttk.Label(
            pmcid_frame,
            text="Project Management Center identifier",
            font=("Segoe UI", 9),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        pmcid_help.pack(anchor="w")

        # Site ID field  
        siteid_frame = ttk.Frame(right_column)
        siteid_frame.pack(fill="x", pady=8)
        
        siteid_label = ttk.Label(
            siteid_frame, 
            text="🌍 Site ID (Optional)", 
            font=("Segoe UI", 11, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        siteid_label.pack(anchor="w", pady=(0, 5))
        
        self.siteid_var = tk.StringVar()
        self.siteid_entry = ttk.Entry(
            siteid_frame, 
            textvariable=self.siteid_var, 
            font=("Segoe UI", 11)
        )
        self.siteid_entry.pack(fill="x", pady=(0, 2))
        
        # Helper text for Site ID
        siteid_help = ttk.Label(
            siteid_frame,
            text="Site or location identifier",
            font=("Segoe UI", 9),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        siteid_help.pack(anchor="w")

        # === ACTION BUTTONS SECTION ===
        self.action_container = ttk.Frame(self.input_content)
        self.action_container.pack(fill="x", pady=(10, 0))
        
        # Action buttons with enhanced modern styling
        action_frame = ttk.Frame(self.action_container, style="Content.TFrame", padding=10)
        action_frame.pack(fill="x", padx=10)
        
        # Centered button layout
        button_container = ttk.Frame(action_frame)
        button_container.pack(expand=True)
        
        self.submit_button = ttk.Button(
            button_container, 
            text="🔍 Get Flag Status", 
            bootstyle="primary", 
            width=20,
            command=self.on_submit
        )
        self.submit_button.pack(side="left", padx=(0, 15))

        reset_button = ttk.Button(
            button_container, 
            text="🔄 Reset", 
            bootstyle="secondary", 
            width=15,
            command=self.reset_get_fields
        )
        reset_button.pack(side="left", padx=(0, 15))


        # Make sure input canvas starts at natural height (expanded)
        try:
            self.parent.after(0, self._sync_input_canvas_height_initial)
        except Exception:
            pass

        # === TWO-COLUMN LAYOUT: FLAG STATUS & API RESPONSE ===
        # Quick summary banner (shown when input is collapsed)
        self.quick_summary_bar = ttk.Frame(get_frame, style="Content.TFrame", padding=(12,6))
        self.quick_summary_label = ttk.Label(
            self.quick_summary_bar,
            text="",
            font=("Segoe UI", 10),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"],
        )
        self.quick_summary_label.pack(anchor="w")
        # Hidden by default
        self.quick_summary_bar.pack_forget()

        self.columns_container = ttk.Frame(get_frame)
        self.columns_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # === LEFT COLUMN: FLAG STATUS ===
        left_column = ttk.Frame(self.columns_container, style="Content.TFrame", padding=20)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Flag status header with modern styling
        status_header = ttk.Frame(left_column)
        status_header.pack(fill="x", pady=(0, 20))
        
        status_title = ttk.Label(
            status_header,
            text="📊 Flag Status",
            font=("Segoe UI", 16, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        status_title.pack(anchor="w")

        # Status content area
        status_content = ttk.Frame(left_column)
        status_content.pack(fill="both", expand=True)

        # Loading indicator with spinner
        self.loading_frame = ttk.Frame(status_content)
        self.loading_frame.pack(pady=10)
        
        self.loading_spinner = ttk.Label(
            self.loading_frame,
            text="⏳",
            font=("Segoe UI", 16),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        self.loading_spinner.pack(side="left", padx=(0, 10))
        
        self.loading_var = tk.StringVar()
        self.loading_label = ttk.Label(
            self.loading_frame, 
            textvariable=self.loading_var, 
            font=("Segoe UI", 11, "italic"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        self.loading_label.pack(side="left")
        
        # Hide loading frame initially
        self.loading_frame.pack_forget()

        # Flag status result area
        self.status_var = tk.StringVar(value="Not checked")
        self.status_display = ttk.Label(
            status_content,
            textvariable=self.status_var,
            wraplength=400,  # Reduced wraplength for left column
            font=("Segoe UI", 11),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"],
            justify="left"
        )
        self.status_display.pack(pady=10, anchor="w")

        # === RIGHT COLUMN: VISUAL / JSON TABS ===
        right_column = ttk.Frame(self.columns_container, style="Content.TFrame", padding=20)
        right_column.pack(side="right", fill="both", expand=True, padx=(5, 0))

        tabs_header = ttk.Frame(right_column)
        tabs_header.pack(fill="x", pady=(0, 10))
        tabs_title = ttk.Label(
            tabs_header,
            text="Flag Details",
            font=("Segoe UI", 16, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        tabs_title.pack(anchor="w")

        # Notebook with Visual and JSON views
        self.view_tabs = ttk.Notebook(right_column)
        self.view_tabs.pack(fill="both", expand=True)

        self.visual_frame = ttk.Frame(self.view_tabs)
        self.summary_frame = ttk.Frame(self.view_tabs)
        self.json_frame = ttk.Frame(self.view_tabs)

        # Order: Visual (default), Summary, JSON
        self.view_tabs.add(self.visual_frame, text="Visual")
        self.view_tabs.add(self.summary_frame, text="Summary")
        self.view_tabs.add(self.json_frame, text="JSON")

        # Visual tab content: scrollable area (Canvas + inner frame + scrollbar)
        self.visual_container = ttk.Frame(self.visual_frame)
        self.visual_container.pack(fill="both", expand=True)

        # Canvas background matches theme background
        bg_color = self.theme_manager.get_theme_config()["colors"]["background"]
        self.visual_canvas = tk.Canvas(
            self.visual_container,
            highlightthickness=0,
            bg=bg_color,
            borderwidth=0,
        )
        self.visual_vscroll = ttk.Scrollbar(
            self.visual_container, orient="vertical", command=self.visual_canvas.yview
        )
        self.visual_canvas.configure(yscrollcommand=self.visual_vscroll.set)

        # Inner frame that will hold all visual widgets
        self.visual_inner = ttk.Frame(self.visual_canvas)
        self.visual_inner_id = self.visual_canvas.create_window(
            (0, 0), window=self.visual_inner, anchor="nw"
        )

        self.visual_canvas.pack(side="left", fill="both", expand=True)
        self.visual_vscroll.pack(side="right", fill="y")

        # Keep scrollregion in sync with inner frame size and width with canvas width
        def _on_inner_configure(event):
            try:
                self.visual_canvas.configure(scrollregion=self.visual_canvas.bbox("all"))
            except Exception:
                pass

        def _on_canvas_configure(event):
            try:
                self.visual_canvas.itemconfigure(self.visual_inner_id, width=event.width)
            except Exception:
                pass

        self.visual_inner.bind("<Configure>", _on_inner_configure)
        self.visual_canvas.bind("<Configure>", _on_canvas_configure)

        # Mouse wheel scrolling (Windows)
        def _on_mousewheel(event):
            try:
                self.visual_canvas.yview_scroll(-int(event.delta / 120), "units")
            except Exception:
                pass

        def _bind_wheel(_):
            self.visual_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_wheel(_):
            self.visual_canvas.unbind_all("<MouseWheel>")

        self.visual_canvas.bind("<Enter>", _bind_wheel)
        self.visual_canvas.bind("<Leave>", _unbind_wheel)

        # Summary tab content (text-only)
        summary_container = ttk.Frame(self.summary_frame)
        summary_container.pack(fill="both", expand=True)

        self.summary_text = tk.Text(
            summary_container,
            height=25,
            width=50,
            font=("Consolas", 10),
            wrap="word",
            state="disabled",
            bg=self.theme_manager.get_theme_config()["colors"]["background"],
            fg=self.theme_manager.get_theme_config()["colors"]["text"],
            selectbackground=self.theme_manager.get_theme_config()["colors"]["primary"],
            insertbackground=self.theme_manager.get_theme_config()["colors"]["text"],
            bd=0,
            highlightthickness=0,
            relief="flat"
        )
        summary_scrollbar = ttk.Scrollbar(summary_container, orient="vertical", command=self.summary_text.yview)
        self.summary_text.configure(yscrollcommand=summary_scrollbar.set)
        self.summary_text.pack(side="left", fill="both", expand=True)
        summary_scrollbar.pack(side="right", fill="y")

        # JSON tab content
        json_container = ttk.Frame(self.json_frame)
        json_container.pack(fill="both", expand=True)

        self.response_text = tk.Text(
            json_container,
            height=25,
            width=50,
            font=("Consolas", 9),
            wrap="none",
            state="disabled",
            bg=self.theme_manager.get_theme_config()["colors"]["background"],
            fg=self.theme_manager.get_theme_config()["colors"]["text"],
            selectbackground=self.theme_manager.get_theme_config()["colors"]["primary"],
            insertbackground=self.theme_manager.get_theme_config()["colors"]["text"],
            bd=0,
            highlightthickness=0,
            relief="flat"
        )

        json_scrollbar = ttk.Scrollbar(json_container, orient="vertical", command=self.response_text.yview)
        self.response_text.configure(yscrollcommand=json_scrollbar.set)

        self.response_text.pack(side="left", fill="both", expand=True)
        json_scrollbar.pack(side="right", fill="y")

        # Hide the left "Flag Status" column; we now merge summary into Visual view
        try:
            # columns_container has two children: left_column and right_column
            # left_column is the first one we created; pack_forget will remove it from layout
            left_column.pack_forget()
        except Exception:
            pass



    # --- Event Handlers ---
    def on_input_data_change(self, *args):
        """Reset response when input changes"""
        self.reset_response_fields()

    def on_submit(self):
        """Submit the feature flag status request"""
        
        feature_key = self.key_var.get().strip()
        environment = self.env_var.get()
        pmcid = self.pmcid_var.get().strip()
        siteid = self.siteid_var.get().strip()

        if not feature_key:
            messagebox.showwarning("Warning", "Please enter a feature flag key.")
            return

        # Build user context from PMCID and SITE ID
        user_context = self.build_user_context(pmcid, siteid)
        # Show loading indicator
        try:
            self.loading_frame.pack(pady=10)
            self.loading_var.set("Fetching flag status...")
            self.submit_button.config(state="disabled")
            self.history_manager.add_get_key(feature_key)
            
            # Start spinner animation
            self.animate_spinner()
            
            # Force UI update to show loading indicators immediately
            self.parent.update_idletasks()
        except Exception as e:
            logger.debug(f"Error setting up loading indicators: {str(e)}")

        try:
            # Get flag status using LaunchDarkly API
            flag_data = self.get_feature_flag_status(feature_key, environment, user_context)
            
            if flag_data:
                self.display_flag_status(flag_data)
                # Ensure logging is configured (fallback to file if no handlers)
                if not logging.getLogger().handlers:
                    try:
                        logging.basicConfig(
                            filename=LOG_FILE,
                            level=logging.INFO,
                            format='%(asctime)s:%(levelname)s:%(message)s',
                            encoding='utf-8'
                        )
                    except Exception:
                        pass
                # Minimal ASCII-only success audit log (no sensitive data)
                enabled_val = bool(flag_data.get("enabled", False))
                actual_env = flag_data.get("actual_environment", environment)
                logging.info(f"Get success: key={feature_key} env={actual_env} enabled={enabled_val}")
                try:
                    audit_event(
                        "get_flag",
                        {
                            "feature_key": feature_key,
                            "environment": actual_env,
                            "enabled": enabled_val,
                        },
                        ok=True,
                    )
                except Exception:
                    pass
            else:
                self.status_var.set("❌ Failed to retrieve flag status")
                self.response_text.config(state="normal")
                self.response_text.delete(1.0, tk.END)
                self.response_text.insert(1.0, "Failed to retrieve feature flag status. Please check the flag key and try again.")
                try:
                    audit_event(
                        "get_flag",
                        {
                            "feature_key": feature_key,
                            "environment": environment,
                        },
                        ok=False,
                    )
                except Exception:
                    pass
                
        except Exception as e:
            self.status_var.set("❌ Error occurred")
            self.response_text.config(state="normal")
            self.response_text.delete(1.0, tk.END)
            self.response_text.insert(1.0, f"Error: {str(e)}")
            logging.error(f"Error getting feature flag status: {str(e)}")
            try:
                audit_event(
                    "get_flag",
                    {
                        "feature_key": feature_key,
                        "environment": environment,
                        "error": str(e),
                    },
                    ok=False,
                )
            except Exception:
                pass

        # Hide loading indicator
        self.loading_frame.pack_forget()
        self.loading_var.set("")
        self.submit_button.config(state="normal")


    def build_user_context(self, pmcid, siteid):
        """Build user context JSON from PMCID and SITE ID"""
        # If no context fields provided, return empty
        if not pmcid and not siteid:
            return ""
        
        context = {}
        
        # Add PMC ID if provided (try to convert to int if it's numeric)
        if pmcid:
            try:
                context["PmcId"] = int(pmcid)  # LaunchDarkly rules often expect numeric PMC IDs
            except ValueError:
                context["PmcId"] = pmcid  # Keep as string if not numeric
                
        # Add Site ID if provided
        if siteid:
            context["SiteId"] = siteid
            
        # Auto-generate user key based on provided context
        if pmcid and siteid:
            context["key"] = f"user-pmc{pmcid}-site{siteid}"
        elif pmcid:
            context["key"] = f"user-pmc{pmcid}"
        elif siteid:
            context["key"] = f"user-site{siteid}"
            
        return json.dumps(context)

    def get_feature_flag_status(self, feature_key, environment, user_context=None):
        """Get feature flag status using LaunchDarkly API with user context evaluation"""
        # Environment mapping
        actual_env = ENVIRONMENT_MAPPINGS.get(environment, environment)
        
        # Validate configuration before constructing URL
        if not PROJECT_KEY or not LAUNCHDARKLY_API_KEY:
            logging.error("Missing LaunchDarkly configuration (PROJECT_KEY or API key). Cannot get feature flag status.")
            return None

        # Build the API URL
        url = f"{LAUNCHDARKLY_BASE_URL}/flags/{PROJECT_KEY}/{feature_key}"
        
        headers = {
            "Authorization": LAUNCHDARKLY_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                flag_data = response.json()
                
                # Extract environment-specific data
                environments = flag_data.get("environments", {})
                env_data = environments.get(actual_env, {})
                
                # Process user context if provided
                context_info = self.process_user_context(user_context, flag_data, actual_env)
                
                links = flag_data.get("_links", {}) if isinstance(flag_data, dict) else {}
                app_url = ""
                try:
                    app_url = links.get("site", {}).get("href") or ""
                except Exception:
                    app_url = ""
                return {
                    "key": feature_key,
                    "name": flag_data.get("name", ""),
                    "description": flag_data.get("description", ""),
                    "environment": environment,
                    "actual_environment": actual_env,
                    "status": "Active" if not flag_data.get("archived", False) else "Archived",
                    "enabled": env_data.get("on", False),
                    "variations": flag_data.get("variations", []),
                    "defaults": flag_data.get("defaults", {}),
                    "user_context": context_info,
                    "full_data": flag_data,
                    "api_url": url,
                    "app_url": app_url,
                }
            else:
                logging.error(f"API Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            return None

    def process_user_context(self, user_context, flag_data, environment):
        """Process user context and determine flag variation"""
        if not user_context or not user_context.strip():
            return {
                "provided": False,
                "message": "No user context provided - showing default flag status"
            }
        
        try:
            # Try to parse as JSON first
            context_data = json.loads(user_context)
            context_type = "JSON"
        except:
            # If not JSON, treat as simple string
            context_data = {"key": user_context.strip()}
            context_type = "Simple"
        
        # Get environment data
        environments = flag_data.get("environments", {})
        env_data = environments.get(environment, {})
        
        # Determine variation based on context
        variation_result = self.determine_variation(context_data, env_data, flag_data)
        
        return {
            "provided": True,
            "type": context_type,
            "context": context_data,
            "variation": variation_result,
            "message": f"User context evaluated: {variation_result['message']}"
        }

    def determine_variation(self, context_data, env_data, flag_data):
        """Determine flag variation based on user context"""
        # Debug: Environment and context details
        logger.debug(f"Environment data: {json.dumps(env_data, indent=2)}")
        logger.debug(f"User context: {json.dumps(context_data, indent=2)}")
        
        # Check if flag is enabled
        if not env_data.get("on", False):
            return {
                "variation": "OFF",
                "value": False,
                "message": "Flag is disabled in this environment"
            }
        
        # Get rules and targets
        rules = env_data.get("rules", [])
        targets = env_data.get("targets", [])
        
        logger.debug(f"Found {len(rules)} rules and {len(targets)} targets")
        
        # Check if user matches any targets
        user_key = context_data.get("key", "")
        for t_idx, target in enumerate(targets):
            if user_key in target.get("values", []):
                variation = target.get("variation", 0)
                return {
                    "variation": f"Target Match (Variation {variation})",
                    "value": self.get_variation_value(variation, flag_data),
                    "message": f"User '{user_key}' matches target rule",
                    "match": {"type": "target", "index": t_idx}
                }
        
        # Check if user matches any rules
        for i, rule in enumerate(rules):
            logger.debug(f"Evaluating rule {i}: {json.dumps(rule, indent=2)}")
            if self.evaluate_rule(context_data, rule):
                variation = rule.get("variation", 0)
                return {
                    "variation": f"Rule Match (Variation {variation})",
                    "message": f"User context matches rule: {rule.get('description', 'Custom rule')}",
                    "value": self.get_variation_value(variation, flag_data),
                    "match": {"type": "rule", "index": i, "description": rule.get("description")}
                }
        
        # Default to fallthrough
        fallthrough = env_data.get("fallthrough", {})
        variation = fallthrough.get("variation", 0)
        logger.debug(f"Using fallthrough variation {variation}")
        return {
            "variation": f"Fallthrough (Variation {variation})",
            "value": self.get_variation_value(variation, flag_data),
            "message": "User context matches fallthrough (default) behavior",
            "match": {"type": "fallthrough"}
        }

    def evaluate_rule(self, context_data, rule):
        """Evaluate if user context matches a rule"""
        clauses = rule.get("clauses", [])
        
        logger.debug(f"Evaluating rule with {len(clauses)} clauses")
        logger.debug(f"Context data: {context_data}")
        
        for clause in clauses:
            attribute = clause.get("attribute", "")
            op = clause.get("op", "")
            values = clause.get("values", [])
            
            # Get user attribute value
            user_value = context_data.get(attribute, "")
            
            # Handle type conversion for numeric values
            if attribute in ["PmcId", "pmcId"] and user_value:
                try:
                    user_value = int(user_value)
                except (ValueError, TypeError):
                    pass  # Keep as string if conversion fails
                    
            # Handle SiteId comparison
            if attribute in ["SiteId", "siteId"] and user_value:
                # SiteId is typically a string, no conversion needed
                pass
            
            # Debug logging
            logger.debug(f"Evaluating clause - attribute='{attribute}', op='{op}', user_value='{user_value}' (type: {type(user_value)}), values={values}")
            
            # Simple evaluation (can be enhanced)
            if op == "in" and user_value in values:
                logger.debug(f"Rule matched: {user_value} in {values}")
                return True
            elif op == "is" and user_value in values:
                logger.debug(f"Rule matched: {user_value} is in {values}")
                return True
            elif op == "matches" and str(user_value) in [str(v) for v in values]:
                logger.debug(f"Rule matched (string comparison): {user_value} matches {values}")
                return True
        
        logger.debug("No rule match found")
        return False

    def get_variation_value(self, variation_index, flag_data):
        """Return the variation value for the given index from the flag data.
        Safely handles out-of-range indexes and missing fields.
        """
        try:
            variations = flag_data.get("variations", [])
            if isinstance(variation_index, int) and 0 <= variation_index < len(variations):
                return variations[variation_index].get("value")
            # Unknown index
            return None
        except Exception as e:
            # Debug-only to avoid noisy UI; keep ASCII-only
            logger.debug(f"get_variation_value error: {e}")
            return None

    def display_flag_status(self, flag_data):
        """Display flag status in a simple, clean format"""
        # Keep the last result for quick summary banner
        self.last_flag_data = flag_data
        key = flag_data.get("key", "")
        name = flag_data.get("name", "")
        env = flag_data.get("environment", "")
        actual_env = flag_data.get("actual_environment", "")
        enabled = flag_data.get("enabled", False)
        user_context = flag_data.get("user_context", {})
        full_data = flag_data.get("full_data", {})
        
        # Extract context data
        pmc_id = None
        site_id = None
        user_key = None
        
        if user_context.get("provided") and "context" in user_context:
            context_data = user_context["context"]
            # Support both key casings just in case
            pmc_id = context_data.get("PmcId")
            if pmc_id is None:
                pmc_id = context_data.get("pmcId")
            site_id = context_data.get("SiteId")
            user_key = context_data.get("key", "")

        # Get environment-specific data
        environments = full_data.get("environments", {})
        env_data = environments.get(actual_env, {})
        
        # Determine flag status (On/Off in environment)
        flag_status = "🟢 On" if enabled else "🔴 Off"
        
        # Get default serve value - depends on flag on/off state
        variations = full_data.get("variations", [])
        default_serve_value = "Unknown"
        
        if enabled:
            # Flag is ON - use fallthrough variation
            fallthrough = env_data.get("fallthrough", {})
            fallthrough_variation = fallthrough.get("variation", 0)
            if 0 <= fallthrough_variation < len(variations):
                default_value = variations[fallthrough_variation].get("value", False)
                default_serve_value = "🟢 Enabled" if default_value else "🔴 Disabled"
        else:
            # Flag is OFF - use off variation
            off_variation = env_data.get("offVariation", 1)  # Default to second variation (usually false)
            if 0 <= off_variation < len(variations):
                off_value = variations[off_variation].get("value", False)
                default_serve_value = "🟢 Enabled" if off_value else "🔴 Disabled"
        
        # Get user-specific result
        user_result = "Default rule applied"
        user_result_value = default_serve_value
        
        if user_context.get("provided") and "variation" in user_context:
            variation_data = user_context["variation"]
            variation_value = variation_data.get("value", None)
            
            if variation_value is True:
                user_result_value = "🟢 Enabled"
            elif variation_value is False:
                user_result_value = "🔴 Disabled"
            else:
                user_result_value = default_serve_value
            
            user_result = variation_data.get("message", "Rule matched")
        else:
            # No specific user targeting, use flag state
            if enabled:
                user_result = "Fallthrough rule applied"
            else:
                user_result = "Flag is off - serving off variation"

        # Build simple summary for FLAG STATUS section
        summary_lines = [
            f"🚩 Flag: {key}",
            f"📝 Name: {name}",
            f"🌐 Environment: {env}",
            f"📊 Status: {flag_status}",
            f"🎯 Default: {default_serve_value}",
            f"👤 Your Result: {user_result_value}",
        ]
        
        if pmc_id:
            summary_lines.append(f"🏢 PMC ID: {pmc_id}")
        if site_id:
            summary_lines.append(f"🌍 Site ID: {site_id}")
        if user_key:
            summary_lines.append(f"🔑 User Key: {user_key}")

        # Show in FLAG STATUS section
        self.status_var.set("\n".join(summary_lines))

        # Render Visual tab (LD-like view)
        try:
            self.render_visual_view(flag_data)
        except Exception as e:
            logger.debug(f"render_visual_view error: {e}")

        # Render Summary tab (concise, text-only)
        try:
            self.render_summary_view(flag_data)
        except Exception as e:
            logger.debug(f"render_summary_view error: {e}")

        # Show clean API response in JSON tab
        self.response_text.config(state="normal")
        self.response_text.delete(1.0, tk.END)
        self.response_text.insert(1.0, json.dumps(full_data, indent=2))
        self.response_text.config(state="disabled")

        # Default to Visual tab
        try:
            self.view_tabs.select(self.visual_frame)
        except Exception:
            pass

        # Auto-collapse the input area to maximize vertical space (animated)
        try:
            if hasattr(self, 'input_collapsed') and not self.input_collapsed:
                self._collapse_input(animated=True)
        except Exception as e:
            logger.debug(f"auto-collapse error: {e}")

        # Update quick summary banner after results
        try:
            self.refresh_quick_summary(show=True)
        except Exception as e:
            logger.debug(f"quick_summary refresh error: {e}")

        # Persist a compact snapshot for Notifications tab autofill
        try:
            hist = self.history_manager.get_history()
            hist["last_flag"] = {
                "key": key,
                "name": name,
                "environment": env,
                "actual_environment": actual_env,
                "enabled": bool(enabled),
                "app_url": flag_data.get("app_url") or "",
            }
            self.history_manager.save_history()
        except Exception as e:
            logger.debug(f"save last_flag history error: {e}")

    def render_summary_view(self, flag_data):
        """Render a concise text-only summary of the flag and evaluation."""
        full = flag_data.get("full_data", {})
        actual_env = flag_data.get("actual_environment", "")
        enabled = bool(flag_data.get("enabled", False))
        key = flag_data.get("key", "")
        name = flag_data.get("name", "")

        envs = full.get("environments", {})
        env_data = envs.get(actual_env, {})

        # Default serve value based on on/off state
        if enabled:
            fallthrough = env_data.get("fallthrough", {})
            def_idx = fallthrough.get("variation", 0)
        else:
            def_idx = env_data.get("offVariation", 1)
        def_val_raw = self.get_variation_value(def_idx, full)
        def_val = "Enabled" if def_val_raw is True else ("Disabled" if def_val_raw is False else def_val_raw)

        # Evaluation result for provided context
        uc = flag_data.get("user_context", {}) or {}
        var = uc.get("variation", {}) if isinstance(uc, dict) else {}
        eval_val_raw = var.get("value")
        eval_val = "Enabled" if eval_val_raw is True else ("Disabled" if eval_val_raw is False else eval_val_raw)
        eval_msg = var.get("message") or ""
        match = var.get("match") if isinstance(var, dict) else None

        # Optional context fields
        ctx = uc.get("context", {}) if uc.get("provided") else {}
        user_key = ctx.get("key") if isinstance(ctx, dict) else None
        pmc = ctx.get("PmcId") if isinstance(ctx, dict) else None
        if pmc is None and isinstance(ctx, dict):
            pmc = ctx.get("pmcId")
        site = ctx.get("SiteId") if isinstance(ctx, dict) else None

        # Compose summary lines
        lines = []
        lines.append(f"Flag: {key}")
        if name:
            lines.append(f"Name: {name}")
        lines.append(f"Environment: {actual_env}")
        lines.append(f"Status: {'On' if enabled else 'Off'}")
        lines.append(f"Default serve: {def_val}")
        if eval_val is not None:
            lines.append(f"Your result: {eval_val}")
        if eval_msg:
            lines.append(f"Reason: {eval_msg}")
        if match:
            try:
                if match.get('type') == 'rule':
                    desc = match.get('description') or f"Rule {match.get('index', 0)+1}"
                    lines.append(f"Matched: {desc}")
                elif match.get('type') == 'target':
                    lines.append("Matched: Target list")
                else:
                    lines.append("Matched: Default rule (fallthrough)")
            except Exception:
                pass
        # Context line
        ctx_parts = []
        if user_key:
            ctx_parts.append(f"key={user_key}")
        if pmc is not None:
            ctx_parts.append(f"PmcId={pmc}")
        if site:
            ctx_parts.append(f"SiteId={site}")
        if ctx_parts:
            lines.append("Context: " + ", ".join(ctx_parts))

        # Push to widget
        text = "\n".join(lines)
        self.summary_text.config(state="normal")
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(1.0, text)
        self.summary_text.config(state="disabled")

    def refresh_quick_summary(self, show: bool = True):
        """Update the quick summary banner content and visibility.
        Shows key details: flag key/name, environment, status, result, and PmcId if provided.
        """
        try:
            if not self.last_flag_data:
                self.quick_summary_bar.pack_forget()
                return

            fd = self.last_flag_data
            key = fd.get("key", "")
            name = fd.get("name") or ""
            actual_env = fd.get("actual_environment", fd.get("environment", ""))
            enabled = bool(fd.get("enabled", False))
            status_txt = "On" if enabled else "Off"

            full = fd.get("full_data", {}) or {}
            envs = full.get("environments", {})
            env_data = envs.get(actual_env, {})
            if enabled:
                fallthrough = env_data.get("fallthrough", {})
                def_idx = fallthrough.get("variation", 0)
            else:
                def_idx = env_data.get("offVariation", 1)
            def_val_raw = self.get_variation_value(def_idx, full)
            def_val = "Enabled" if def_val_raw is True else ("Disabled" if def_val_raw is False else def_val_raw)

            uc = fd.get("user_context", {}) or {}
            var = uc.get("variation", {}) if isinstance(uc, dict) else {}
            eval_val_raw = var.get("value")
            eval_val = "Enabled" if eval_val_raw is True else ("Disabled" if eval_val_raw is False else eval_val_raw)
            ctx = uc.get("context", {}) if uc.get("provided") else {}
            pmc = None
            site = None
            if isinstance(ctx, dict):
                pmc = ctx.get("PmcId") if ctx.get("PmcId") is not None else ctx.get("pmcId")
                site = ctx.get("SiteId")

            parts = []
            parts.append(f"Flag: {key}")
            if name:
                parts.append(f"Name: {name}")
            if actual_env:
                parts.append(f"Env: {actual_env}")
            try:
                env_type = fd.get("environment", "")
                if env_type and env_type != actual_env:
                    parts.append(f"Type: {env_type}")
            except Exception:
                pass
            parts.append(f"Status: {status_txt}")
            parts.append(f"Default: {def_val}")
            if eval_val is not None:
                parts.append(f"Result: {eval_val}")
            if pmc is not None:
                parts.append(f"PmcId: {pmc}")
            if site:
                parts.append(f"SiteId: {site}")

            self.quick_summary_label.configure(text=" | ".join(parts))

            if show:
                try:
                    # Place banner just above the response columns
                    if hasattr(self, 'columns_container') and self.columns_container.winfo_manager():
                        self.quick_summary_bar.pack(fill="x", pady=(6, 6), before=self.columns_container)
                    else:
                        self.quick_summary_bar.pack(fill="x", pady=(6, 6))
                except Exception:
                    self.quick_summary_bar.pack(fill="x", pady=(6, 6))
            else:
                self.quick_summary_bar.pack_forget()
        except Exception as e:
            logger.debug(f"refresh_quick_summary error: {e}")

    # --- Animation helpers for smoother transitions ---
    def _sync_input_canvas_height_initial(self):
        try:
            self.input_content.update_idletasks()
            h = self.input_content.winfo_reqheight()
            self.input_anim_canvas.configure(height=max(1, h))
        except Exception as e:
            logger.debug(f"sync_input_canvas error: {e}")

    def _ease_cubic_in_out(self, p: float) -> float:
        # Faster ease-in-out compared to smoothstep
        try:
            if p < 0.5:
                return 4 * p * p * p
            q = 2 * p - 2
            return 1 + (q * q * q) / 2
        except Exception:
            return p

    def _animate_canvas_height(self, canvas: tk.Canvas, target_h: int, duration_ms: int = 280, easing: str = "cubic", mode: str = "open", on_done=None):
        """Animate a canvas height with easing.
        - Cancels any prior animation on the same canvas for smoothness.
        - Calls on_done when the animation completes.
        - mode can be 'open' or 'close' to bias easing.
        """
        try:
            # Cancel any existing scheduled frame for this canvas
            try:
                job = self._anim_jobs.pop(canvas, None)
                if job is not None:
                    canvas.after_cancel(job)
            except Exception:
                pass

            start = time.perf_counter()
            start_h = int(canvas.winfo_height())
            delta = int(target_h) - start_h
            # Compute duration with distance-based scaling
            px = abs(delta)
            base = duration_ms
            # target speed about ~1.0 px/ms, clamp total duration
            duration = max(160, min(420, int(base + px * 0.9)))

            def ease_val(p):
                # Blend ease based on mode
                if easing == "cubic":
                    if mode == "open":
                        # easeOutCubic
                        return 1 - pow(1 - p, 3)
                    elif mode == "close":
                        # easeInCubic
                        return p * p * p
                # Fallback linear
                return p

            def frame():
                try:
                    now = time.perf_counter()
                    t = (now - start) * 1000.0
                    p = 1.0 if duration == 0 else max(0.0, min(1.0, t / float(duration)))
                    ep = ease_val(p)
                    nh = int(start_h + delta * ep)
                    canvas.configure(height=max(0, nh))
                    if p < 1.0:
                        job_id = canvas.after(12, frame)
                        self._anim_jobs[canvas] = job_id
                    else:
                        canvas.configure(height=max(0, target_h))
                        # Clear job and fire callback
                        try:
                            self._anim_jobs.pop(canvas, None)
                        except Exception:
                            pass
                        if on_done:
                            try:
                                on_done()
                            except Exception:
                                pass
                except Exception:
                    try:
                        canvas.configure(height=max(0, target_h))
                        self._anim_jobs.pop(canvas, None)
                    except Exception:
                        pass
                    if on_done:
                        try:
                            on_done()
                        except Exception:
                            pass
            # Kick off first frame
            frame()
        except Exception as e:
            logger.debug(f"animate_canvas_height error: {e}")

    def _collapse_input(self, animated: bool = True):
        try:
            self.input_content.update_idletasks()
            if animated:
                self._animate_canvas_height(self.input_anim_canvas, 0)
            else:
                self.input_anim_canvas.configure(height=0)
            if hasattr(self, 'collapse_btn'):
                self.collapse_btn.configure(text="Expand")
            self.input_collapsed = True
            # Tighten spacing under header to reclaim vertical space
            try:
                self.input_container.pack_configure(pady=(0, 6))
            except Exception:
                pass
            # Show quick summary banner if we have results
            try:
                self.refresh_quick_summary(show=True)
            except Exception:
                pass
        except Exception as e:
            logger.debug(f"collapse_input error: {e}")

    def _expand_input(self, animated: bool = True):
        try:
            self.input_content.update_idletasks()
            target_h = self.input_content.winfo_reqheight()
            if animated:
                self._animate_canvas_height(self.input_anim_canvas, max(1, target_h))
            else:
                self.input_anim_canvas.configure(height=max(1, target_h))
            if hasattr(self, 'collapse_btn'):
                self.collapse_btn.configure(text="Collapse")
            self.input_collapsed = False
            # Restore spacing under header
            try:
                self.input_container.pack_configure(pady=(0, 25))
            except Exception:
                pass
            # Hide quick summary banner
            try:
                self.quick_summary_bar.pack_forget()
            except Exception:
                pass
        except Exception as e:
            logger.debug(f"expand_input error: {e}")

    def render_visual_view(self, flag_data):
        """Render a LaunchDarkly-like targeting view in the Visual tab."""
        # Clear previous visual contents
        for child in self.visual_inner.winfo_children():
            child.destroy()

        full_data = flag_data.get("full_data", {})
        actual_env = flag_data.get("actual_environment", "")
        enabled = bool(flag_data.get("enabled", False))
        text_fg = self.theme_manager.get_theme_config()["colors"]["text"]

        environments = full_data.get("environments", {})
        env_data = environments.get(actual_env, {})
        variations = full_data.get("variations", [])

        # Actions bar (Copy/Open)
        actions = ttk.Frame(self.visual_inner)
        actions.pack(fill="x", pady=(0, 6))

        def _copy_json():
            try:
                data = json.dumps(full_data, indent=2)
                self.parent.clipboard_clear()
                self.parent.clipboard_append(data)
            except Exception as e:
                logger.debug(f"copy_json error: {e}")

        def _copy_api_url():
            try:
                api_url = flag_data.get("api_url", "")
                if api_url:
                    self.parent.clipboard_clear()
                    self.parent.clipboard_append(api_url)
            except Exception as e:
                logger.debug(f"copy_api_url error: {e}")

        def _open_api_url():
            try:
                api_url = flag_data.get("api_url", "")
                if api_url:
                    webbrowser.open(api_url)
            except Exception as e:
                logger.debug(f"open_api_url error: {e}")

        def _open_app_url():
            try:
                app_url = flag_data.get("app_url", "")
                if app_url:
                    webbrowser.open(app_url)
            except Exception as e:
                logger.debug(f"open_app_url error: {e}")

        ttk.Button(actions, text="Copy JSON", bootstyle="secondary", width=14, command=_copy_json).pack(side="left", padx=(0,6))
        ttk.Button(actions, text="Copy API URL", bootstyle="secondary", width=14, command=_copy_api_url).pack(side="left", padx=(0,6))
        ttk.Button(actions, text="Open API URL", bootstyle="info", width=14, command=_open_api_url).pack(side="left", padx=(0,6))
        ttk.Button(actions, text="Open in LaunchDarkly", bootstyle="primary", width=22, command=_open_app_url).pack(side="left")

        # Evaluation banner (top)
        uc = flag_data.get("user_context", {}) or {}
        ctx = uc.get("context", {}) if uc.get("provided") else {}
        user_key = ctx.get("key") if isinstance(ctx, dict) else None
        eval_text = "Default behavior"
        detail_text = ""
        bootstyle = None
        try:
            var = uc.get("variation", {}) if isinstance(uc, dict) else {}
            val = var.get("value", None)
            msg = var.get("message") or ""
            match = var.get("match") if isinstance(var, dict) else None
            if isinstance(val, bool):
                eval_text = "Enabled" if val else "Disabled"
                bootstyle = "success" if val else "danger"
            elif val is not None:
                eval_text = f"Variation: {val}"
                bootstyle = "info"
            else:
                eval_text = "No specific match — default behavior"
                bootstyle = "secondary"
            detail_text = msg
        except Exception:
            bootstyle = "secondary"

        banner = ttk.Frame(self.visual_inner, padding=10, style="Content.TFrame")
        banner.pack(fill="x", pady=(0, 10))
        title_lbl = ttk.Label(
            banner,
            text=eval_text,
            font=("Segoe UI", 12, "bold"),
            foreground=text_fg,
        )
        # Try to color the title using ttkbootstrap bootstyle (non-fatal if unsupported)
        try:
            if bootstyle:
                title_lbl.configure(bootstyle=bootstyle)
        except Exception:
            pass
        title_lbl.pack(anchor="w")

        # Context line (chips)
        ctx_row = ttk.Frame(banner)
        ctx_row.pack(anchor="w", pady=(2,0))
        if user_key:
            ttk.Label(ctx_row, text="User:", font=("Segoe UI", 9, "bold"), foreground=text_fg).pack(side="left")
            ttk.Label(ctx_row, text=user_key, font=("Segoe UI", 9), foreground=text_fg).pack(side="left", padx=(4,8))
        try:
            pmc = ctx.get("PmcId") if isinstance(ctx, dict) else None
            if pmc is None and isinstance(ctx, dict):
                pmc = ctx.get("pmcId")
            if pmc is not None:
                ttk.Label(ctx_row, text="PmcId:", font=("Segoe UI", 9, "bold"), foreground=text_fg).pack(side="left")
                ttk.Label(ctx_row, text=str(pmc), font=("Segoe UI", 9), foreground=text_fg).pack(side="left", padx=(4,8))
        except Exception:
            pass
        try:
            site = ctx.get("SiteId")
            if site:
                ttk.Label(ctx_row, text="SiteId:", font=("Segoe UI", 9, "bold"), foreground=text_fg).pack(side="left")
                ttk.Label(ctx_row, text=str(site), font=("Segoe UI", 9), foreground=text_fg).pack(side="left", padx=(4,8))
        except Exception:
            pass
        # Plain-text context summary for maximum contrast
        try:
            parts = []
            if isinstance(ctx, dict):
                if user_key:
                    parts.append(f"key={user_key}")
                pmc_dbg = ctx.get("PmcId") if ctx.get("PmcId") is not None else ctx.get("pmcId")
                if pmc_dbg is not None:
                    parts.append(f"PmcId={pmc_dbg}")
                if ctx.get("SiteId"):
                    parts.append(f"SiteId={ctx.get('SiteId')}")
            if parts:
                ttk.Label(banner, text="Context: " + ", ".join(str(p) for p in parts), font=("Segoe UI", 9), foreground=text_fg).pack(anchor="w", pady=(2,0))
        except Exception:
            pass

        if detail_text:
            ttk.Label(banner, text=detail_text, font=("Segoe UI", 10), foreground=text_fg).pack(anchor="w")

        # Environment header (pill)
        env_header = ttk.Frame(self.visual_inner)
        env_header.pack(fill="x", pady=(0, 10))
        env_title = ttk.Label(env_header, text=f"Targeting configuration for {actual_env}", font=("Segoe UI", 12, "bold"), foreground=text_fg)
        env_title.pack(anchor="w")

        # Top bar: Flag is On/Off ...
        top_bar = ttk.Frame(self.visual_inner, style="Content.TFrame")
        top_bar.pack(fill="x", pady=(5, 10))
        status_text = "On" if enabled else "Off"
        serve_text = "serving variations based on rules" if enabled else "serving off variation"
        ttk.Label(top_bar, text=f"Flag is {status_text} — {serve_text}", font=("Segoe UI", 11, "bold"), foreground=text_fg).pack(anchor="w", padx=8, pady=8)

        # Accordion helper (only one open at a time) with simple height animation
        accordion_sections = []
        def make_section(parent, title_text, collapsible: bool = True, start_open: bool = False):
            header = ttk.Frame(parent)
            header.pack(fill="x", pady=(0,2))
            # Chevron indicator + clickable title (avoid right-side toggle buttons)
            chevron = ttk.Label(header, text=("v" if start_open else ">"), font=("Segoe UI", 11, "bold"), foreground=text_fg)
            chevron.pack(side="left", padx=(8,4))
            title = ttk.Label(header, text=title_text, font=("Segoe UI", 11, "bold"), foreground=text_fg)
            title.pack(side="left")
            # Animated container (canvas) with an inner frame
            container = tk.Canvas(parent, height=0, highlightthickness=0, bg=self.theme_manager.get_theme_config()["colors"]["background"], borderwidth=0)
            content = ttk.Frame(container, style="Content.TFrame")
            inner_id = container.create_window((0, 0), window=content, anchor="nw")
            # Set initial visibility
            state = {"visible": bool(start_open), "animating": False}
            if start_open:
                try:
                    container.pack(fill="x")
                    content.update_idletasks()
                    container.configure(height=max(1, content.winfo_reqheight() + 4))
                except Exception:
                    pass
            # Keep container width synced
            def _on_container_configure(event):
                try:
                    container.itemconfigure(inner_id, width=event.width)
                except Exception:
                    pass
            container.bind("<Configure>", _on_container_configure)

            def _animate_height(target_h: int, duration_ms: int = 280):
                # Delegate to centralized time-based easing for consistency
                try:
                    self._animate_canvas_height(container, target_h, duration_ms, easing="cubic")
                except Exception:
                    try:
                        container.configure(height=target_h)
                    except Exception:
                        pass

            def accordion_open_me():
                # For collapsible sections, close others first; for non-collapsible, don't affect others
                if collapsible:
                    for sec in accordion_sections:
                        if sec["state"]["visible"] and sec["content"] is not content:
                            try:
                                if sec["state"].get("animating"):
                                    continue
                                sec["state"]["animating"] = True
                                self._animate_canvas_height(
                                    sec["container"],
                                    0,
                                    260,
                                    easing="cubic",
                                    mode="close",
                                    on_done=lambda s=sec: (s["container"].pack_forget(), s["chevron"].configure(text=">"), s["state"].update({"visible": False, "animating": False}))
                                )
                                sec["chevron"].configure(text=">")
                            except Exception:
                                pass
                # Open/resize this section
                try:
                    container.pack(fill="x")
                    content.update_idletasks()
                    target_h = content.winfo_reqheight() + 4
                    state["animating"] = True
                    self._animate_canvas_height(
                        container,
                        target_h,
                        300,
                        easing="cubic",
                        mode="open",
                        on_done=lambda: state.update({"animating": False})
                    )
                    chevron.configure(text="v")
                    state["visible"] = True
                except Exception:
                    pass
            def on_toggle():
                if not collapsible:
                    return
                if state.get("animating"):
                    return
                if state["visible"]:
                    try:
                        # Animate close to zero height then hide
                        state["animating"] = True
                        def _done_close():
                            try:
                                container.pack_forget()
                            except Exception:
                                pass
                            chevron.configure(text=">")
                            state.update({"visible": False, "animating": False})
                        self._animate_canvas_height(container, 0, 280, easing="cubic", mode="close", on_done=_done_close)
                        chevron.configure(text=">")
                    except Exception:
                        pass
                else:
                    accordion_open_me()
            # Make header clickable (title/chevron) only if collapsible
            if collapsible:
                for w in (header, title, chevron):
                    try:
                        w.bind("<Button-1>", lambda e: on_toggle())
                        w.configure(cursor="hand2")
                    except Exception:
                        pass
                accordion_sections.append({"header": header, "content": content, "container": container, "chevron": chevron, "state": state, "title": title_text})
            return content, state, accordion_open_me

        # Default rule (always open, non-collapsible) — show this first
        def_frame, def_state, def_open = make_section(self.visual_inner, "Default rule", collapsible=False, start_open=True)
        if enabled:
            fallthrough = env_data.get("fallthrough", {})
            v_idx = fallthrough.get("variation", 0)
        else:
            v_idx = env_data.get("offVariation", 1)
        v_val = self.get_variation_value(v_idx, full_data)
        ttk.Label(def_frame, text=f"Serve: {v_val}", font=("Segoe UI", 10), foreground=text_fg).pack(anchor="w", padx=12)
        # Ensure the non-collapsible section resizes to fit its content
        try:
            def_open()
        except Exception:
            pass

        # Targets and Rules sections
        open_done = False
        targets = env_data.get("targets", []) or []
        if targets:
            tgt_frame, tgt_state, tgt_open = make_section(self.visual_inner, "Targets")
            for idx, t in enumerate(targets):
                var_idx = t.get("variation", 0)
                val = self.get_variation_value(var_idx, full_data)
                vals = t.get("values", [])
                row = ttk.Frame(tgt_frame)
                row.pack(fill="x", pady=2, padx=12)
                ttk.Label(row, text=f"Serve: {val}", font=("Segoe UI", 10, "bold"), foreground=text_fg).pack(side="left")
                ttk.Label(row, text=f"for {len(vals)} user keys", font=("Segoe UI", 10), foreground=text_fg).pack(side="left", padx=(6,0))
                # Matched tag
                try:
                    if match and match.get("type") == "target" and match.get("index") == idx:
                        ttk.Label(row, text="Matched", bootstyle="success", font=("Segoe UI", 9, "bold")).pack(side="right")
                except Exception:
                    pass

        # Rules section
        rules = env_data.get("rules", []) or []
        if rules:
            rules_frame, rules_state, rules_open = make_section(self.visual_inner, "Rules")
            for i, rule in enumerate(rules, start=1):
                rf = ttk.Frame(rules_frame)
                rf.pack(fill="x", pady=6, padx=8)
                desc = rule.get("description") or f"Rule {i}"
                var_idx = rule.get("variation", 0)
                var_val = self.get_variation_value(var_idx, full_data)
                header_row = ttk.Frame(rf)
                header_row.pack(fill="x")
                ttk.Label(header_row, text=desc, font=("Segoe UI", 10, "bold"), foreground=text_fg).pack(side="left")
                # Matched tag
                try:
                    if match and match.get("type") == "rule" and match.get("index") == (i-1):
                        ttk.Label(header_row, text="Matched", bootstyle="success", font=("Segoe UI", 9, "bold")).pack(side="right")
                except Exception:
                    pass
                # Clauses summary
                clauses = rule.get("clauses", [])
                for cl in clauses:
                    attr = cl.get("attribute", "attribute")
                    op = cl.get("op", "in")
                    values = cl.get("values", [])
                    try:
                        shown = ", ".join([str(v) for v in values[:5]]) + (" ..." if len(values) > 5 else "")
                    except Exception:
                        shown = str(values)
                    # Readable inline clause line (high contrast)
                    clause_line = ttk.Frame(rf)
                    clause_line.pack(anchor="w", padx=12)
                    ttk.Label(clause_line, text="If ", font=("Segoe UI", 10), foreground=text_fg).pack(side="left")
                    ttk.Label(clause_line, text=str(attr), font=("Segoe UI", 10, "bold"), foreground=text_fg).pack(side="left")
                    ttk.Label(clause_line, text=f" {op} ", font=("Segoe UI", 10), foreground=text_fg).pack(side="left")
                    ttk.Label(clause_line, text=f"[ {shown} ]", font=("Segoe UI", 10), foreground=text_fg).pack(side="left")
                ttk.Label(rf, text=f"Serve: {var_val}", font=("Segoe UI", 10, "bold"), foreground=text_fg).pack(anchor="w", padx=12, pady=(0,2))
            # Open rules now so content appears right after the header
            try:
                rules_open()
                open_done = True
            except Exception:
                pass

        


    def animate_spinner(self):
        """Animate the loading spinner"""
        spinner_chars = ["⏳", "⌛", "⏳", "⌛"]
        if hasattr(self, 'spinner_index'):
            self.spinner_index = (self.spinner_index + 1) % len(spinner_chars)
        else:
            self.spinner_index = 0
        
        self.loading_spinner.config(text=spinner_chars[self.spinner_index])
        
        # Continue animation if loading frame is visible
        if self.loading_frame.winfo_viewable():
            self.parent.after(500, self.animate_spinner)

    def reset_response_fields(self):
        """Reset response fields"""
        self.status_var.set("Not checked")
        self.response_text.config(state="normal")
        self.response_text.delete(1.0, tk.END)
        self.response_text.config(state="disabled")
        self.loading_var.set("")
        self.loading_frame.pack_forget()

    def reset_get_fields(self):
        """Reset all form fields in GET Tab"""
        self.key_var.set("")
        self.env_var.set("DEV")
        self.pmcid_var.set("")
        self.siteid_var.set("")
        self.reset_response_fields() 

 