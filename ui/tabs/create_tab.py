import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox
import requests
import json
import logging
import traceback
from datetime import datetime
from shared.config_loader import LAUNCHDARKLY_API_KEY, PROJECT_KEY
from api_config.api_endpoints import FeatureFlagEndpoints, APIHeaders, APIConfig
from shared.audit import audit_event
from ui.widgets.help_icon import HelpIcon
from utils.settings_manager import SettingsManager

# Configure logging for create tab
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class CreateTab:
    def __init__(self, parent, history_manager, theme_manager):
        self.parent = parent
        self.history_manager = history_manager
        self.theme_manager = theme_manager
        self._help_icons = []
        self.setup_ui()

    def setup_ui(self):
        """Sets up the UI for the 'Create Feature Flag' tab with a professional layout."""
        # --- Main container frame ---
        create_frame = ttk.Frame(self.parent, padding=16)
        create_frame.pack(fill="both", expand=True)

        # --- Header Section ---
        header_frame = ttk.Frame(create_frame)
        header_frame.pack(fill="x", pady=(0, 12))
        
        # Title with icon
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(anchor="w")
        
        title_label = ttk.Label(
            title_frame, 
            text="➕ Create Feature Flag", 
            font=("Segoe UI", 24, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        title_label.pack(anchor="w")
        
        subtitle_label = ttk.Label(
            title_frame,
            text="Create new feature flags in LaunchDarkly",
            font=("Segoe UI", 12),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        subtitle_label.pack(anchor="w", pady=(5, 0))

        # --- Basic Information Section ---
        basic_container = ttk.Frame(create_frame)
        basic_container.pack(fill="x", pady=(0, 12))
        
        # Basic info card
        basic_frame = ttk.Frame(basic_container, style="Content.TFrame")
        basic_frame.pack(fill="x", padx=5)
        
        # Card header
        basic_header = ttk.Frame(basic_frame)
        basic_header.pack(fill="x", padx=16, pady=(10, 8))
        
        basic_title = ttk.Label(
            basic_header,
            text="📝 Basic Information",
            font=("Segoe UI", 16, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        basic_title.pack(anchor="w")

        # Form fields
        basic_form = ttk.Frame(basic_frame)
        basic_form.pack(fill="x", padx=16, pady=(0, 12))
        
        # Two-column layout
        left_column = ttk.Frame(basic_form)
        left_column.pack(side="left", fill="x", expand=True, padx=(0, 15))
        
        right_column = ttk.Frame(basic_form)
        right_column.pack(side="right", fill="x", expand=True, padx=(15, 0))

        # Left column fields
        # Flag Key
        key_frame = ttk.Frame(left_column)
        key_frame.pack(fill="x", pady=6)
        
        key_hdr = ttk.Frame(key_frame)
        key_hdr.pack(fill="x")
        key_label = ttk.Label(
            key_hdr, 
            text="🔑 Flag Key", 
            font=("Segoe UI", 11, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        key_label.pack(side="left", pady=(0, 5))
        _ch1 = HelpIcon(key_hdr, "create.flag_key")
        _ch1.pack(side="left", padx=(2,0))
        self._help_icons.append((_ch1, {"side": "left", "padx": (2,0)}))
        
        self.create_key_var = tk.StringVar()
        self.create_key_entry = ttk.Entry(
            key_frame, 
            textvariable=self.create_key_var, 
            font=("Segoe UI", 11)
        )
        self.create_key_entry.pack(fill="x", pady=(0, 5))

        # Flag Name
        name_frame = ttk.Frame(left_column)
        name_frame.pack(fill="x", pady=6)
        
        name_hdr = ttk.Frame(name_frame)
        name_hdr.pack(fill="x")
        name_label = ttk.Label(
            name_hdr, 
            text="📋 Flag Name", 
            font=("Segoe UI", 11, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        name_label.pack(side="left", pady=(0, 5))
        _ch2 = HelpIcon(name_hdr, "create.flag_name")
        _ch2.pack(side="left", padx=(2,0))
        self._help_icons.append((_ch2, {"side": "left", "padx": (2,0)}))
        
        self.create_name_var = tk.StringVar()
        self.create_name_entry = ttk.Entry(
            name_frame, 
            textvariable=self.create_name_var, 
            font=("Segoe UI", 11)
        )
        self.create_name_entry.pack(fill="x", pady=(0, 5))

        # Right column fields
        # Description
        desc_frame = ttk.Frame(right_column)
        desc_frame.pack(fill="x", pady=6)
        
        desc_hdr = ttk.Frame(desc_frame)
        desc_hdr.pack(fill="x")
        desc_label = ttk.Label(
            desc_hdr, 
            text="📄 Description", 
            font=("Segoe UI", 11, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        desc_label.pack(side="left", pady=(0, 5))
        _ch3 = HelpIcon(desc_hdr, "create.description")
        _ch3.pack(side="left", padx=(2,0))
        self._help_icons.append((_ch3, {"side": "left", "padx": (2,0)}))
        
        self.create_desc_var = tk.StringVar()
        self.create_desc_entry = ttk.Entry(
            desc_frame, 
            textvariable=self.create_desc_var, 
            font=("Segoe UI", 11)
        )
        self.create_desc_entry.pack(fill="x", pady=(0, 5))

        # Tags
        tags_frame = ttk.Frame(right_column)
        tags_frame.pack(fill="x", pady=6)
        
        tags_hdr = ttk.Frame(tags_frame)
        tags_hdr.pack(fill="x")
        tags_label = ttk.Label(
            tags_hdr, 
            text="🏷️ Tags", 
            font=("Segoe UI", 11, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        tags_label.pack(side="left", pady=(0, 5))
        _ch4 = HelpIcon(tags_hdr, "create.tags")
        _ch4.pack(side="left", padx=(2,0))
        self._help_icons.append((_ch4, {"side": "left", "padx": (2,0)}))
        
        self.create_tags_var = tk.StringVar()
        self.create_tags_entry = ttk.Entry(
            tags_frame, 
            textvariable=self.create_tags_var, 
            font=("Segoe UI", 11)
        )
        self.create_tags_entry.pack(fill="x", pady=(0, 5))

        # Note: Removed Configuration section (environment and fallthrough). We now default to
        # environment = DEV and default fallthrough = False for safety.

        # --- Action Buttons ---
        buttons_container = ttk.Frame(create_frame)
        buttons_container.pack(fill="x", pady=(0, 12))
        
        buttons_frame = ttk.Frame(buttons_container)
        buttons_frame.pack(anchor="w")
        
        create_group = ttk.Frame(buttons_frame)
        create_group.pack(side="left", padx=(0, 10))
        self.create_button = ttk.Button(
            create_group, 
            text="🚀 Create Flag", 
            bootstyle="success", 
            width=15, 
            command=self.create_feature_flag
        )
        self.create_button.pack(side="left")
        _ch5 = HelpIcon(create_group, "create.create_button")
        _ch5.pack(side="left", padx=(2,0))
        self._help_icons.append((_ch5, {"side": "left", "padx": (2,0)}))

        reset_group = ttk.Frame(buttons_frame)
        reset_group.pack(side="left")
        reset_create_button = ttk.Button(
            reset_group, 
            text="🔄 Reset Form", 
            bootstyle="secondary", 
            width=15, 
            command=self.reset_create_fields
        )
        reset_create_button.pack(side="left")
        _ch6 = HelpIcon(reset_group, "create.reset")
        _ch6.pack(side="left", padx=(2,0))
        self._help_icons.append((_ch6, {"side": "left", "padx": (2,0)}))

        # --- Status Section ---
        status_container = ttk.Frame(create_frame)
        status_container.pack(fill="both", expand=True)
        
        # Status card
        status_frame = ttk.Frame(status_container, style="Content.TFrame")
        status_frame.pack(fill="both", expand=True, padx=5)
        
        # Status header
        status_header = ttk.Frame(status_frame)
        status_header.pack(fill="x", padx=16, pady=(10, 8))
        
        status_title = ttk.Label(
            status_header,
            text="📊 Creation Status",
            font=("Segoe UI", 16, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        status_title.pack(anchor="w")

        # Status content
        status_content = ttk.Frame(status_frame)
        status_content.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        # Loading indicator with spinner
        self.loading_frame = ttk.Frame(status_content)
        self.loading_frame.pack(pady=6)
        
        self.loading_spinner = ttk.Label(
            self.loading_frame,
            text="⏳",
            font=("Segoe UI", 16),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        self.loading_spinner.pack(side="left", padx=(0, 6))
        
        self.create_status_var = tk.StringVar()
        self.loading_label = ttk.Label(
            self.loading_frame, 
            textvariable=self.create_status_var, 
            font=("Segoe UI", 11, "italic"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        self.loading_label.pack(side="left")
        
        # Hide loading frame initially
        self.loading_frame.pack_forget()
        self.create_result_label = ttk.Label(
            status_content, 
            text="", 
            wraplength=700, 
            font=("Segoe UI", 11),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        self.create_result_label.pack(pady=6, fill="both", expand=True)
        # Apply initial help icon visibility
        try:
            show = bool(SettingsManager().get("help", "show_help_icons"))
        except Exception:
            show = True
        if not show:
            self.set_help_icons_visible(False)

    # --- Event Handlers ---
    def create_feature_flag(self):
        """Create a new feature flag in LaunchDarkly"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Starting feature flag creation at {timestamp}")

        # Show loading indicator
        self.loading_frame.pack(pady=10)
        self.create_status_var.set("Creating feature flag...")
        self.create_button.config(state="disabled")

        # Start spinner animation
        self.animate_spinner()

        # Force UI update to show loading indicators immediately
        self.parent.update_idletasks()

        # Get form data
        flag_key = self.create_key_var.get().strip()
        flag_name = self.create_name_var.get().strip()
        description = self.create_desc_var.get().strip()
        tags = self.create_tags_var.get().strip()
        # No environment specified during creation; exclude env-specific config from payload
        environment = ""

        # Debug: Log all form data
        form_data = {
            "flag_key": flag_key,
            "flag_name": flag_name,
            "description": description,
            "tags": tags,
            "environment": environment
        }
        logger.debug(f"Form data collected: {form_data}")

        # Validate required fields
        if not flag_key or not flag_name:
            error_msg = "Flag Key and Flag Name are required fields."
            logger.warning(f"Validation error: {error_msg}")
            messagebox.showwarning("Validation Error", error_msg)
            self.create_status_var.set("")
            self.create_button.config(state="normal")
            self.loading_frame.pack_forget()
            return

        logger.info("Validation passed, proceeding with flag creation")

        try:
            logger.info("Calling create_flag_in_launchdarkly method")

            success, response_data = self.create_flag_in_launchdarkly(
                flag_key, flag_name, description, tags, environment
            )

            logger.info(f"create_flag_in_launchdarkly returned: success={success}")

            if success:
                success_msg = f"Feature flag '{flag_key}' created successfully!"
                detail_msg = f"Flag '{flag_key}' has been created."

                logger.info(f"Feature flag created successfully: {flag_key}")

                # Update UI
                self.create_status_var.set(success_msg)
                self.create_result_label.config(text=detail_msg)

                # Confirmation messagebox
                messagebox.showinfo(
                    "Success!", 
                    f"Feature flag '{flag_key}' has been successfully created!\n\n"
                    f"Description: {description or 'No description provided'}\n"
                    f"Tags: {tags or 'No tags provided'}"
                )

                self.reset_create_fields()
                # Audit success
                try:
                    audit_event(
                        "create_flag",
                        {
                            "feature_key": flag_key,
                            "environment": environment,
                            "name": flag_name,
                            "tags": tags,
                        },
                        ok=True,
                    )
                except Exception:
                    pass
            else:
                error_msg = "Failed to create feature flag"
                detail_msg = f"An error occurred while creating the feature flag. Response: {response_data}"
                logger.error(f"Failed to create feature flag: {response_data}")

                self.create_status_var.set(error_msg)
                self.create_result_label.config(text=detail_msg)

                # Error messagebox
                messagebox.showerror(
                    "Creation Failed", 
                    f"Failed to create feature flag '{flag_key}'.\n\n"
                    f"Please check the details in the status area below and try again."
                )
                # Audit failure
                try:
                    audit_event(
                        "create_flag",
                        {
                            "feature_key": flag_key,
                            "environment": environment,
                            "name": flag_name,
                            "error": str(response_data),
                        },
                        ok=False,
                    )
                except Exception:
                    pass

        except Exception as e:
            error_msg = f"Exception occurred: {str(e)}"
            logger.error(f"Exception during flag creation: {str(e)}", exc_info=True)

            self.create_status_var.set("Error occurred")
            self.create_result_label.config(text=error_msg)

            # Exception messagebox
            messagebox.showerror(
                "Unexpected Error", 
                f"An unexpected error occurred:\n\n{str(e)}\n\n"
                f"Please check the console/logs for more details."
            )
            # Audit exception
            try:
                audit_event(
                    "create_flag",
                    {
                        "feature_key": flag_key,
                        "environment": environment,
                        "name": flag_name,
                        "error": str(e),
                    },
                    ok=False,
                )
            except Exception:
                pass

        # Hide loading indicator and re-enable button
        logger.info("Cleaning up UI after flag creation attempt")
        self.loading_frame.pack_forget()
        self.create_button.config(state="normal")

    def set_help_icons_visible(self, show: bool):
        try:
            for icon, kwargs in getattr(self, "_help_icons", []):
                if show:
                    if not icon.winfo_ismapped():
                        icon.pack(**kwargs)
                else:
                    icon.pack_forget()
        except Exception:
            pass

    def create_flag_in_launchdarkly(self, flag_key, flag_name, description, tags, environment):
        """Create a feature flag in LaunchDarkly using the API"""
        logger.info("Entering create_flag_in_launchdarkly method")

        api_key = LAUNCHDARKLY_API_KEY
        project_key = PROJECT_KEY

        logger.debug(f"API Key present: {'Yes' if api_key else 'No'}, Project Key: {project_key}")

        url = FeatureFlagEndpoints.CREATE_FLAG + f"/{project_key}"
        headers = APIHeaders.get_launchdarkly_headers(api_key)

        logger.debug(f"API URL: {url}")

        # Prepare the flag data WITHOUT any environment-specific configuration
        flag_data = {
            "key": flag_key,
            "name": flag_name,
            "description": description,
            "temporary": False,
            "variations": [
                {"value": True},
                {"value": False}
            ],
            "defaults": {
                # Will be set to the desired fallthrough variation below
                "onVariation": 0,
                "offVariation": 1
            }
        }

        # Apply default fallthrough/offVariation to payload (Default Disabled = False)
        try:
            variations = flag_data.get("variations", [])
            true_index = 0
            false_index = 1
            for i, v in enumerate(variations):
                if v.get("value") is True:
                    true_index = i
                elif v.get("value") is False:
                    false_index = i
            desired_index = false_index  # Default to Disabled for safety
            # Set project-level defaults only (no environment payload)
            flag_data["defaults"]["onVariation"] = desired_index
            flag_data["defaults"]["offVariation"] = desired_index
            logger.debug(f"Create: defaults set to Disabled (index {desired_index})")
        except Exception as e:
            logger.debug(f"Create: skipped applying default fallthrough/offVariation due to: {e}")

        # Add tags if provided
        if tags:
            flag_data["tags"] = [tag.strip() for tag in tags.split(",")]
            logger.debug(f"Tags added: {flag_data['tags']}")

        logger.debug(f"Flag data prepared: {json.dumps(flag_data, indent=2)}")

        try:
            response = requests.post(
                url,
                headers=headers,
                json=flag_data,
                timeout=APIConfig.DEFAULT_TIMEOUT
            )

            try:
                response_json = response.json()
                logger.debug(f"API Response: Status {response.status_code}, Body: {json.dumps(response_json, indent=2)}")
            except json.JSONDecodeError:
                response_text = response.text
                logger.debug(f"API Response: Status {response.status_code}, Text: {response_text}")
                response_json = {"error": "Invalid JSON response", "text": response_text}

            success = response.status_code == 201
            logger.info(f"API request completed: success={success}, status_code={response.status_code}")

            return success, response_json

        except requests.exceptions.Timeout:
            error_msg = "API request timed out"
            logger.error(error_msg)
            return False, {"error": "timeout", "message": error_msg}

        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(f"Connection error: {str(e)}")
            return False, {"error": "connection_error", "message": error_msg}

        except requests.exceptions.RequestException as e:
            error_msg = f"Request exception: {str(e)}"
            logger.error(f"Request exception: {str(e)}")
            return False, {"error": "request_exception", "message": error_msg}

        except Exception as e:
            error_msg = f"Unexpected error in API call: {str(e)}"
            logger.error(f"Unexpected error in API call: {str(e)}", exc_info=True)
            return False, {"error": "unexpected_error", "message": error_msg}

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

    def reset_create_fields(self):
        """Reset create form fields"""
        self.create_key_var.set("")
        self.create_name_var.set("")
        self.create_desc_var.set("")
        self.create_tags_var.set("")
        # Removed: self.create_default_var (Default Value toggle)
        self.create_status_var.set("")
        self.create_result_label.config(text="")
        self.loading_frame.pack_forget()
 