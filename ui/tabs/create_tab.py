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
from shared.constants import UPDATE_ENVIRONMENT_OPTIONS

# Configure logging for create tab
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class CreateTab:
    def __init__(self, parent, history_manager, theme_manager):
        self.parent = parent
        self.history_manager = history_manager
        self.theme_manager = theme_manager
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
        
        key_label = ttk.Label(
            key_frame, 
            text="🔑 Flag Key", 
            font=("Segoe UI", 11, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        key_label.pack(anchor="w", pady=(0, 5))
        
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
        
        name_label = ttk.Label(
            name_frame, 
            text="📋 Flag Name", 
            font=("Segoe UI", 11, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        name_label.pack(anchor="w", pady=(0, 5))
        
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
        
        desc_label = ttk.Label(
            desc_frame, 
            text="📄 Description", 
            font=("Segoe UI", 11, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        desc_label.pack(anchor="w", pady=(0, 5))
        
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
        
        tags_label = ttk.Label(
            tags_frame, 
            text="🏷️ Tags", 
            font=("Segoe UI", 11, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        tags_label.pack(anchor="w", pady=(0, 5))
        
        self.create_tags_var = tk.StringVar()
        self.create_tags_entry = ttk.Entry(
            tags_frame, 
            textvariable=self.create_tags_var, 
            font=("Segoe UI", 11)
        )
        self.create_tags_entry.pack(fill="x", pady=(0, 5))

        # --- Configuration Section ---
        config_container = ttk.Frame(create_frame)
        config_container.pack(fill="x", pady=(0, 12))
        
        # Configuration card
        config_frame = ttk.Frame(config_container, style="Content.TFrame")
        config_frame.pack(fill="x", padx=5)
        
        # Card header
        config_header = ttk.Frame(config_frame)
        config_header.pack(fill="x", padx=16, pady=(10, 8))
        
        config_title = ttk.Label(
            config_header,
            text="⚙️ Configuration",
            font=("Segoe UI", 16, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        config_title.pack(anchor="w")

        # Configuration form
        config_form = ttk.Frame(config_frame)
        config_form.pack(fill="x", padx=16, pady=(0, 12))
        
        # Environment selection
        env_frame = ttk.Frame(config_form)
        env_frame.pack(fill="x", pady=6)
        
        env_label = ttk.Label(
            env_frame, 
            text="🌍 Environment (Production excluded for safety)", 
            font=("Segoe UI", 11, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        env_label.pack(anchor="w", pady=(0, 5))
        
        self.create_env_var = tk.StringVar(value="DEV")
        env_combo = ttk.Combobox(
            env_frame, 
            textvariable=self.create_env_var,
            values=UPDATE_ENVIRONMENT_OPTIONS,
            font=("Segoe UI", 11),
            state="readonly"
        )
        env_combo.pack(fill="x", pady=(0, 5))

        # Removed 'Default Value' toggle per request. The flag will be created OFF by default for safety.

        # Fallthrough / offVariation selection
        fallthrough_frame = ttk.Frame(config_form)
        fallthrough_frame.pack(fill="x", pady=6)
        ttk.Label(
            fallthrough_frame,
            text="Default rule (fallthrough):",
            font=("Segoe UI", 11, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        ).pack(anchor="w", pady=(0, 5))
        self.create_fallthrough_var = tk.StringVar(value="True")
        self.create_fallthrough_combo = ttk.Combobox(
            fallthrough_frame,
            textvariable=self.create_fallthrough_var,
            values=["True", "False"],
            state="readonly",
            font=("Segoe UI", 11)
        )
        self.create_fallthrough_combo.pack(anchor="w")

        # --- Action Buttons ---
        buttons_container = ttk.Frame(create_frame)
        buttons_container.pack(fill="x", pady=(0, 12))
        
        buttons_frame = ttk.Frame(buttons_container)
        buttons_frame.pack(anchor="w")
        
        self.create_button = ttk.Button(
            buttons_frame, 
            text="🚀 Create Flag", 
            bootstyle="success", 
            width=15, 
            command=self.create_feature_flag
        )
        self.create_button.pack(side="left", padx=(0, 10))

        reset_create_button = ttk.Button(
            buttons_frame, 
            text="🔄 Reset Form", 
            bootstyle="secondary", 
            width=15, 
            command=self.reset_create_fields
        )
        reset_create_button.pack(side="left", padx=10)

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
        environment = self.create_env_var.get()

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
            # Create the feature flag using LaunchDarkly API
            logger.info("Calling create_flag_in_launchdarkly method")

            success, response_data = self.create_flag_in_launchdarkly(
                flag_key, flag_name, description, tags, environment
            )

            logger.info(f"create_flag_in_launchdarkly returned: success={success}")

            if success:
                success_msg = f"Feature flag '{flag_key}' created successfully!"
                detail_msg = f"Flag '{flag_key}' has been created in the {environment} environment."

                logger.info(f"Feature flag created successfully: {flag_key} in {environment}")

                # Update UI
                self.create_status_var.set(success_msg)
                self.create_result_label.config(text=detail_msg)

                # Confirmation messagebox
                messagebox.showinfo(
                    "Success!", 
                    f"Feature flag '{flag_key}' has been successfully created!\n\n"
                    f"Environment: {environment}\n"
                    f"Description: {description or 'No description provided'}\n"
                    f"Tags: {tags or 'No tags provided'}"
                )

                self.reset_create_fields()
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

        # Hide loading indicator and re-enable button
        logger.info("Cleaning up UI after flag creation attempt")
        self.loading_frame.pack_forget()
        self.create_button.config(state="normal")

    def create_flag_in_launchdarkly(self, flag_key, flag_name, description, tags, environment):
        """Create a feature flag in LaunchDarkly using the API"""
        logger.info("Entering create_flag_in_launchdarkly method")

        api_key = LAUNCHDARKLY_API_KEY
        project_key = PROJECT_KEY

        logger.debug(f"API Key present: {'Yes' if api_key else 'No'}, Project Key: {project_key}")

        url = FeatureFlagEndpoints.CREATE_FLAG + f"/{project_key}"
        headers = APIHeaders.get_launchdarkly_headers(api_key)

        logger.debug(f"API URL: {url}")

        # Prepare the flag data
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
                # Will be set to the selected fallthrough variation below
                "onVariation": 0,
                "offVariation": 1
            },
            "environments": {
                environment: {
                    # Create flags OFF by default for safety
                    "on": False,
                    "archived": False,
                    "salt": f"{flag_key}-{environment}",
                    "prerequisites": [],
                    "targets": [],
                    "rules": [],
                    "fallthrough": {
                        # Will be set to the selected fallthrough variation below
                        "variation": 0
                    }
                }
            }
        }

        # Apply selected fallthrough/offVariation to payload
        try:
            variations = flag_data.get("variations", [])
            true_index = 0
            false_index = 1
            for i, v in enumerate(variations):
                if v.get("value") is True:
                    true_index = i
                elif v.get("value") is False:
                    false_index = i
            desired = (self.create_fallthrough_var.get() or "True").strip().lower()
            desired_index = true_index if desired == "true" else false_index
            # Set environment fallthrough to selected variation
            flag_data["environments"][environment]["fallthrough"] = {"variation": desired_index}
            # Set defaults on/off variation and env offVariation to selected variation
            flag_data["defaults"]["onVariation"] = desired_index
            flag_data["defaults"]["offVariation"] = desired_index
            flag_data["environments"][environment]["offVariation"] = desired_index
            logger.debug(f"Create: fallthrough set to {desired} (index {desired_index}); offVariation set to index {desired_index}")
        except Exception as e:
            logger.debug(f"Create: skipped applying fallthrough/offVariation selection due to: {e}")

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
        self.create_env_var.set("DEV")
        # Removed: self.create_default_var (Default Value toggle)
        self.create_status_var.set("")
        self.create_result_label.config(text="")
        self.loading_frame.pack_forget()
 