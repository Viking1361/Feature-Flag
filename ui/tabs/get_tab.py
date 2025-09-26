import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox
import logging
import requests
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

# Module logger for this UI module
logger = logging.getLogger(__name__)

class GetTab:
    def __init__(self, parent, history_manager, theme_manager):
        self.parent = parent
        self.history_manager = history_manager
        self.theme_manager = theme_manager
        # Initialize optimized API client
        self.api_client = get_client()
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
        input_container = ttk.Frame(get_frame)
        input_container.pack(fill="x", pady=(0, 25))
        
        # Create a modern card-like frame
        input_frame = ttk.Frame(input_container, style="Content.TFrame")
        input_frame.pack(fill="x", padx=5)
        
        # Card header
        card_header = ttk.Frame(input_frame)
        card_header.pack(fill="x", padx=25, pady=(20, 15))
        
        card_title = ttk.Label(
            card_header,
            text="🔧 Configuration",
            font=("Segoe UI", 16, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        card_title.pack(anchor="w")

        # Form fields with better layout
        form_frame = ttk.Frame(input_frame)
        form_frame.pack(fill="x", padx=25, pady=(0, 25))
        
        # Two-column layout for better organization
        left_column = ttk.Frame(form_frame)
        left_column.pack(side="left", fill="x", expand=True, padx=(0, 15))
        
        right_column = ttk.Frame(form_frame)
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
        action_container = ttk.Frame(input_frame)
        action_container.pack(fill="x", pady=(10, 0))
        
        # Action buttons with enhanced modern styling
        action_frame = ttk.Frame(action_container, style="Content.TFrame", padding=10)
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
        reset_button.pack(side="left")

        # === TWO-COLUMN LAYOUT: FLAG STATUS & API RESPONSE ===
        columns_container = ttk.Frame(get_frame)
        columns_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # === LEFT COLUMN: FLAG STATUS ===
        left_column = ttk.Frame(columns_container, style="Content.TFrame", padding=20)
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

        # === RIGHT COLUMN: API RESPONSE DETAILS ===
        right_column = ttk.Frame(columns_container, style="Content.TFrame", padding=20)
        right_column.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # API Response header
        response_header = ttk.Frame(right_column)
        response_header.pack(fill="x", pady=(0, 20))
        
        response_title = ttk.Label(
            response_header,
            text="📋 API Response Details",
            font=("Segoe UI", 16, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        response_title.pack(anchor="w")
        
        # Response content area
        response_content = ttk.Frame(right_column)
        response_content.pack(fill="both", expand=True)
        
        # Create text container for better layout
        text_container = ttk.Frame(response_content)
        text_container.pack(fill="both", expand=True)
        
        # Enhanced API response text widget optimized for column layout
        self.response_text = tk.Text(
            text_container,
            height=25,  # Taller for column layout
            width=50,   # Adjusted width for right column
            font=("Consolas", 9),  # Slightly smaller font to fit more content
            wrap="none",  # No wrapping for better JSON formatting
            state="disabled",
            bg=self.theme_manager.get_theme_config()["colors"]["background"],
            fg=self.theme_manager.get_theme_config()["colors"]["text"],
            selectbackground=self.theme_manager.get_theme_config()["colors"]["primary"],
            insertbackground=self.theme_manager.get_theme_config()["colors"]["text"],
            bd=0,
            highlightthickness=0,
            relief="flat"
        )
        
        # Enhanced scrollbar setup
        response_scrollbar = ttk.Scrollbar(text_container, orient="vertical", command=self.response_text.yview)
        self.response_text.configure(yscrollcommand=response_scrollbar.set)
        
        # Pack text widget and scrollbar properly
        self.response_text.pack(side="left", fill="both", expand=True)
        response_scrollbar.pack(side="right", fill="y")



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
            else:
                self.status_var.set("❌ Failed to retrieve flag status")
                self.response_text.config(state="normal")
                self.response_text.delete(1.0, tk.END)
                self.response_text.insert(1.0, "Failed to retrieve feature flag status. Please check the flag key and try again.")
                
        except Exception as e:
            self.status_var.set("❌ Error occurred")
            self.response_text.config(state="normal")
            self.response_text.delete(1.0, tk.END)
            self.response_text.insert(1.0, f"Error: {str(e)}")
            logging.error(f"Error getting feature flag status: {str(e)}")

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
                    "full_data": flag_data
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
        for target in targets:
            if user_key in target.get("values", []):
                variation = target.get("variation", 0)
                return {
                    "variation": f"Target Match (Variation {variation})",
                    "value": self.get_variation_value(variation, flag_data),
                    "message": f"User '{user_key}' matches target rule"
                }
        
        # Check if user matches any rules
        for i, rule in enumerate(rules):
            logger.debug(f"Evaluating rule {i}: {json.dumps(rule, indent=2)}")
            if self.evaluate_rule(context_data, rule):
                variation = rule.get("variation", 0)
                return {
                    "variation": f"Rule Match (Variation {variation})",
                    "message": f"User context matches rule: {rule.get('description', 'Custom rule')}",
                    "value": self.get_variation_value(variation, flag_data)
                }
        
        # Default to fallthrough
        fallthrough = env_data.get("fallthrough", {})
        variation = fallthrough.get("variation", 0)
        logger.debug(f"Using fallthrough variation {variation}")
        return {
            "variation": f"Fallthrough (Variation {variation})",
            "value": self.get_variation_value(variation, flag_data),
            "message": "User context matches fallthrough (default) behavior"
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

    def display_flag_status(self, flag_data):
        """Display flag status in a simple, clean format"""
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
            pmc_id = context_data.get("PmcId")
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

        # Show clean API response in response text widget
        self.response_text.config(state="normal")
        self.response_text.delete(1.0, tk.END)
        self.response_text.insert(1.0, json.dumps(full_data, indent=2))
        self.response_text.config(state="disabled")

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

 