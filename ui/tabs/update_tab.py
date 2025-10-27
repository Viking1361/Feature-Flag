import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox
import logging
import requests
import json
from datetime import datetime
from app_logic import update_flag
from shared.config_loader import LOG_FILE, LAUNCHDARKLY_API_KEY, PROJECT_KEY
from api_config.api_endpoints import FeatureFlagEndpoints, APIHeaders, APIConfig, URLBuilder
from shared.constants import UPDATE_ENVIRONMENT_OPTIONS, ENVIRONMENT_MAPPINGS
from api_client import get_client
from shared.audit import audit_event
from ui.widgets.help_icon import HelpIcon
from utils.settings_manager import SettingsManager

# Module logger for this UI module
logger = logging.getLogger(__name__)

class UpdateTab:
    def __init__(self, parent, history_manager, theme_manager):
        self.parent = parent
        self.history_manager = history_manager
        self.theme_manager = theme_manager
        # Initialize optimized API client
        self.api_client = get_client()
        self._help_icons = []
        self.setup_ui()

    def setup_ui(self):
        """Sets up the UI for the 'Update Feature Flag' tab with a modern card-based layout."""
        # --- Main container with enhanced spacing ---
        main_container = ttk.Frame(self.parent, padding=16)
        main_container.pack(fill="both", expand=True)

        # --- Enhanced Header Section ---
        header_container = ttk.Frame(main_container)
        header_container.pack(fill="x", pady=(0, 12))
        
        # Title card with modern styling
        title_card = ttk.Frame(header_container, style="Content.TFrame", padding=12)
        title_card.pack(fill="x", pady=(0, 6))
        
        title_label = ttk.Label(
            title_card, 
            text="⚙️ Update Feature Flag", 
            font=("Segoe UI", 22, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        title_label.pack(anchor="w")
        
        subtitle_label = ttk.Label(
            title_card,
            text="Modify feature flag settings across environments",
            font=("Segoe UI", 11),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        subtitle_label.pack(anchor="w", pady=(3, 0))

        # --- Main Content Area with Card Layout ---
        content_container = ttk.Frame(main_container)
        content_container.pack(fill="both", expand=True)
        
        # Enhanced Configuration Card
        config_card = ttk.Frame(content_container, style="Content.TFrame", padding=16)
        config_card.pack(fill="x", pady=(0, 12))
        
        # Configuration header with modern styling
        config_header = ttk.Frame(config_card)
        config_header.pack(fill="x", pady=(0, 10))
        
        config_title = ttk.Label(
            config_header,
            text="🔧 Configuration",
            font=("Segoe UI", 18, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        config_title.pack(anchor="w")

        # Enhanced form layout with better column organization
        form_container = ttk.Frame(config_card)
        form_container.pack(fill="x")
        
        # Left column - Primary configuration
        left_column = ttk.Frame(form_container)
        left_column.pack(side="left", fill="x", expand=True, padx=(0, 25))
        
        # Right column - Context configuration  
        right_column = ttk.Frame(form_container)
        right_column.pack(side="right", fill="x", expand=True, padx=(25, 0))

        # === LEFT COLUMN: Primary Configuration ===
        left_header = ttk.Label(
            left_column,
            text="Primary Settings",
            font=("Segoe UI", 14, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        left_header.pack(anchor="w", pady=(0, 8))
        
        # Feature Flag Key with enhanced styling
        key_container = ttk.Frame(left_column, style="Content.TFrame", padding=10)
        key_container.pack(fill="x", pady=(0, 8))
        
        key_hdr = ttk.Frame(key_container)
        key_hdr.pack(fill="x")
        key_label = ttk.Label(
            key_hdr, 
            text="🔑 Feature Flag Key", 
            font=("Segoe UI", 12, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        key_label.pack(side="left", pady=(0, 5))
        _uh1 = HelpIcon(key_hdr, "update.flag_key")
        _uh1.pack(side="left", padx=(2,0))
        self._help_icons.append((_uh1, {"side": "left", "padx": (2,0)}))
        
        self.update_key_var = tk.StringVar()
        self.update_key_var.trace_add("write", lambda *args: self.reset_log())
        self.update_key_entry = ttk.Combobox(
            key_container, 
            textvariable=self.update_key_var, 
            values=self.history_manager.get_history().get("update_keys", []), 
            font=("Segoe UI", 11),
            height=8
        )
        self.update_key_entry.pack(fill="x")

        # Environment with enhanced styling
        env_container = ttk.Frame(left_column, style="Content.TFrame", padding=10)
        env_container.pack(fill="x", pady=(0, 6))
        
        env_hdr = ttk.Frame(env_container)
        env_hdr.pack(fill="x")
        env_label = ttk.Label(
            env_hdr, 
            text="🌍 Environment", 
            font=("Segoe UI", 12, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        env_label.pack(side="left", pady=(0, 5))
        _uh2 = HelpIcon(env_hdr, "update.environment")
        _uh2.pack(side="left", padx=(2,0))
        self._help_icons.append((_uh2, {"side": "left", "padx": (2,0)}))
        
        self.environment_entry = ttk.Combobox(
            env_container, 
            values=UPDATE_ENVIRONMENT_OPTIONS, 
            font=("Segoe UI", 11),
            state="readonly",
            height=8
        )
        self.environment_entry.set("DEV")
        self.environment_entry.pack(fill="x", pady=(0, 5))
        
        # Enhanced helper text
        env_help = ttk.Label(
            env_container,
            text="⚠️ Production excluded for safety",
            font=("Segoe UI", 10),
            foreground="orange"
        )
        env_help.pack(anchor="w")

        # === RIGHT COLUMN: Context Configuration ===
        right_header = ttk.Label(
            right_column,
            text="Context Settings",
            font=("Segoe UI", 14, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        right_header.pack(anchor="w", pady=(0, 8))
        
        # PMC ID field with enhanced styling
        pmcid_container = ttk.Frame(right_column, style="Content.TFrame", padding=10)
        pmcid_container.pack(fill="x", pady=(0, 8))
        
        pmcid_hdr = ttk.Frame(pmcid_container)
        pmcid_hdr.pack(fill="x")
        pmcid_label = ttk.Label(
            pmcid_hdr, 
            text="🏢 PMC ID (Optional)", 
            font=("Segoe UI", 12, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        pmcid_label.pack(side="left", pady=(0, 5))
        _uh3 = HelpIcon(pmcid_hdr, "update.pmc_id")
        _uh3.pack(side="left", padx=(2,0))
        self._help_icons.append((_uh3, {"side": "left", "padx": (2,0)}))
        
        self.pmcid_var = tk.StringVar()
        self.pmcid_entry = ttk.Entry(
            pmcid_container, 
            textvariable=self.pmcid_var, 
            font=("Segoe UI", 11)
        )
        self.pmcid_entry.pack(fill="x", pady=(0, 5))
        
        # Enhanced helper text for PMCID
        pmcid_help = ttk.Label(
            pmcid_container,
            text="📊 For intelligent targeting and context",
            font=("Segoe UI", 10),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        pmcid_help.pack(anchor="w")

        # Site ID field with enhanced styling
        siteid_container = ttk.Frame(right_column, style="Content.TFrame", padding=10)
        siteid_container.pack(fill="x", pady=(0, 6))
        
        siteid_hdr = ttk.Frame(siteid_container)
        siteid_hdr.pack(fill="x")
        siteid_label = ttk.Label(
            siteid_hdr, 
            text="🌍 Site ID (Optional)", 
            font=("Segoe UI", 12, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        siteid_label.pack(side="left", pady=(0, 5))
        _uh4 = HelpIcon(siteid_hdr, "update.site_id")
        _uh4.pack(side="left", padx=(2,0))
        self._help_icons.append((_uh4, {"side": "left", "padx": (2,0)}))
        
        self.siteid_var = tk.StringVar()
        self.siteid_entry = ttk.Entry(
            siteid_container, 
            textvariable=self.siteid_var, 
            font=("Segoe UI", 11)
        )
        self.siteid_entry.pack(fill="x", pady=(0, 5))
        
        # Enhanced helper text for Site ID
        siteid_help = ttk.Label(
            siteid_container,
            text="🗺️ Site or location identifier",
            font=("Segoe UI", 10),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        siteid_help.pack(anchor="w")

        # === ACTION BUTTONS SECTION ===
        action_container = ttk.Frame(config_card)
        action_container.pack(fill="x", pady=(12, 0))
        
        # Action buttons with enhanced modern styling
        action_frame = ttk.Frame(action_container, style="Content.TFrame", padding=12)
        action_frame.pack(fill="x")
        
        # Optional settings controls
        options_container = ttk.Frame(action_frame)
        options_container.pack(fill="x", pady=(0, 6))
        ttk.Label(options_container, text="Default rule (fallthrough):").pack(anchor="w")
        self.fallthrough_option_var = tk.StringVar(value="No value")
        self.fallthrough_option_combo = ttk.Combobox(
            options_container,
            textvariable=self.fallthrough_option_var,
            values=["No value", "True", "False"],
            state="readonly"
        )
        self.fallthrough_option_combo.pack(anchor="w")

        # New: Allow applying default rule independently of ON/OFF
        apply_group = ttk.Frame(options_container)
        apply_group.pack(anchor="w", pady=(6, 0))
        self.apply_fallthrough_button = ttk.Button(
            apply_group,
            text="Apply Default Rule",
            bootstyle="info",
            width=20,
            command=self.apply_default_rule
        )
        self.apply_fallthrough_button.pack(side="left")
        _uh5 = HelpIcon(apply_group, "update.apply_default")
        _uh5.pack(side="left", padx=(2,0))
        self._help_icons.append((_uh5, {"side": "left", "padx": (2,0)}))

        # Centered button layout
        button_container = ttk.Frame(action_frame)
        button_container.pack(expand=True)

        on_group = ttk.Frame(button_container)
        on_group.pack(side="left", padx=(0, 15))
        self.update_on_button = ttk.Button(
            on_group, 
            text="🟢 Turn ON", 
            bootstyle="success", 
            width=18,
            command=lambda: self.toggle_feature_flag(True)
        )
        self.update_on_button.pack(side="left")
        _uh6 = HelpIcon(on_group, "update.turn_on")
        _uh6.pack(side="left", padx=(2,0))
        self._help_icons.append((_uh6, {"side": "left", "padx": (2,0)}))

        off_group = ttk.Frame(button_container)
        off_group.pack(side="left", padx=(0, 15))
        self.update_off_button = ttk.Button(
            off_group, 
            text="🔴 Turn OFF", 
            bootstyle="danger", 
            width=18,
            command=lambda: self.toggle_feature_flag(False)
        )
        self.update_off_button.pack(side="left")
        _uh7 = HelpIcon(off_group, "update.turn_off")
        _uh7.pack(side="left", padx=(2,0))
        self._help_icons.append((_uh7, {"side": "left", "padx": (2,0)}))

        reset_group = ttk.Frame(button_container)
        reset_group.pack(side="left")
        reset_button = ttk.Button(
            reset_group, 
            text="🔄 Reset", 
            bootstyle="secondary", 
            width=15,
            command=self.reset_update_fields
        )
        reset_button.pack(side="left")
        _uh8 = HelpIcon(reset_group, "update.reset")
        _uh8.pack(side="left", padx=(2,0))
        self._help_icons.append((_uh8, {"side": "left", "padx": (2,0)}))

        # === TWO-COLUMN LAYOUT: STATUS & API RESPONSE ===
        columns_container = ttk.Frame(content_container)
        columns_container.pack(fill="both", expand=True, padx=8, pady=6)
        
        # === LEFT COLUMN: UPDATE STATUS ===
        left_column = ttk.Frame(columns_container, style="Content.TFrame", padding=12)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Status header with modern styling
        status_header = ttk.Frame(left_column)
        status_header.pack(fill="x", pady=(0, 10))
        
        status_title = ttk.Label(
            status_header,
            text="📊 Update Status",
            font=("Segoe UI", 16, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        status_title.pack(anchor="w")

        # Status content area
        status_content = ttk.Frame(left_column)
        status_content.pack(fill="both", expand=True)

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
        
        self.update_loading_var = tk.StringVar()
        self.loading_label = ttk.Label(
            self.loading_frame, 
            textvariable=self.update_loading_var, 
            font=("Segoe UI", 11, "italic"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        self.loading_label.pack(side="left")
        
        # Hide loading frame initially
        self.loading_frame.pack_forget()

        # Status result area
        self.update_result_label = ttk.Label(
            status_content, 
            text="", 
            wraplength=400,  # Reduced wraplength for left column
            font=("Segoe UI", 11),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        self.update_result_label.pack(pady=6, anchor="w")

        # === RIGHT COLUMN: API RESPONSE DETAILS ===
        right_column = ttk.Frame(columns_container, style="Content.TFrame", padding=12)
        right_column.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # API Response header
        response_header = ttk.Frame(right_column)
        response_header.pack(fill="x", pady=(0, 10))
        
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

        # Apply initial help icon visibility
        try:
            show = bool(SettingsManager().get("help", "show_help_icons"))
        except Exception:
            show = True
        if not show:
            self.set_help_icons_visible(False)

    # --- Event Handlers ---
    def toggle_feature_flag(self, enable):
        """Toggle feature flag on/off with intelligent PMC ID targeting"""
        feature_key = self.update_key_var.get().strip()
        environment = self.environment_entry.get()
        pmcid = self.pmcid_var.get().strip()
        siteid = self.siteid_var.get().strip()

        if not feature_key:
            messagebox.showwarning("Warning", "Please enter a feature flag key.")
            return

        logger.debug(f"UPDATE Tab - Feature Key: {feature_key}")
        logger.debug(f"UPDATE Tab - Environment: {environment}")
        logger.debug(f"UPDATE Tab - Action: {'Enable' if enable else 'Disable'}")
        logger.debug(f"UPDATE Tab - PMC ID: {pmcid}")
        logger.debug(f"UPDATE Tab - Site ID: {siteid}")

        # Show loading indicator
        self.loading_frame.pack(pady=10)
        self.update_loading_var.set(f"Updating {feature_key} to {'ON' if enable else 'OFF'} in {environment}...")
        
        # Disable buttons during update
        self.update_on_button.config(state="disabled")
        self.update_off_button.config(state="disabled")
        
        self.history_manager.add_update_key(feature_key)
        
        # Start spinner animation
        self.animate_spinner()
        
        # Force UI update to show loading indicators immediately
        self.parent.update_idletasks()

        try:
            # Clear previous response
            self.update_response_box(None)
            
            # Prepare response data collection
            response_data = {
                "operation": "feature_flag_update",
                "timestamp": datetime.now().isoformat(),
                "request": {
                    "feature_key": feature_key,
                    "environment": environment,
                    "action": "enable" if enable else "disable",
                    "pmc_id": pmcid if pmcid else None,
                    "site_id": siteid if siteid else None
                },
                "api_responses": []
            }
            
            # If PMC ID is provided, use intelligent targeting
            if pmcid:
                logger.debug("PMC ID provided, using intelligent targeting...")
                success, message, api_responses = self.update_flag_with_pmcid_targeting(feature_key, environment, pmcid, siteid, enable)
                response_data["api_responses"] = api_responses
            else:
                # Use standard flag toggle
                logger.debug("No PMC ID provided, using standard flag toggle...")
                success = update_flag(environment, feature_key, enable)
                message = f"Flag '{feature_key}' {'enabled' if enable else 'disabled'} globally in {environment}"
                response_data["api_responses"] = [{"operation": "standard_toggle", "success": success, "message": message}]
            
            # If user requested to set default rule (fallthrough) to True/False and we are enabling,
            # apply a follow-up JSON Patch to set fallthrough even on the standard path and audit it.
            try:
                desired = ""
                if getattr(self, 'fallthrough_option_var', None):
                    desired = (self.fallthrough_option_var.get() or "").strip().lower()
                if success and enable and desired in ("true", "false"):
                    logger.debug("Applying fallthrough update after standard toggle (no PMC ID)...")
                    flag_data_std = self.get_flag_configuration(feature_key)
                    if flag_data_std:
                        ft_success = self.update_flag_configuration(feature_key, flag_data_std, environment)
                        response_data["api_responses"].append({
                            "operation": "fallthrough_update",
                            "success": ft_success
                        })
                        # Audit default rule update for Notifications tab
                        try:
                            actual_env = ENVIRONMENT_MAPPINGS.get(environment, environment)
                            audit_event(
                                "default_rule_update",
                                {
                                    "feature_key": feature_key,
                                    "environment": actual_env,
                                    "enabled": True if desired == "true" else False,
                                    "note": "fallthrough/offVariation updated after toggle",
                                },
                                ok=bool(ft_success),
                            )
                        except Exception:
                            pass
                        if not ft_success:
                            logger.error("Failed to update fallthrough variation after standard toggle")
            except Exception as e:
                logger.exception(f"Exception applying fallthrough update after standard toggle: {str(e)}")
            
            # Update response data with results
            response_data["success"] = success
            response_data["result_message"] = message
            
            if success:
                success_message = f"✅ Successfully updated {feature_key} in {environment}"
                
                # Build context information for display
                context_info = []
                if pmcid:
                    context_info.append(f"PMC ID: {pmcid}")
                if siteid:
                    context_info.append(f"Site ID: {siteid}")
                
                context_display = f" | {' | '.join(context_info)}" if context_info else ""
                response_data["context"] = context_info
                
                self.update_loading_var.set(success_message)
                self.update_result_label.config(text=f"{message}{context_display}")
                
                # Update response box with detailed API data
                self.update_response_box(response_data)
                
                logger.info(f"Update success for {feature_key} in {environment}{context_display}")
                logger.debug(f"Details - {message}")
                # Minimal ASCII-only success audit log (no sensitive data)
                try:
                    action = "on" if enable else "off"
                    safe_pmc = pmcid if pmcid else "-"
                    safe_site = siteid if siteid else "-"
                    logging.info(f"Update success: key={feature_key} env={environment} action={action} pmc={safe_pmc} site={safe_site}")
                except Exception:
                    pass
                
            else:
                error_message = f"❌ Failed to update {feature_key}"
                response_data["error"] = error_message
                
                self.update_loading_var.set(error_message)
                self.update_result_label.config(text=f"Failed to update feature flag '{feature_key}' in {environment} environment. {message}")
                
                # Update response box with error details
                self.update_response_box(response_data)
                
                logger.error(f"Update failed for {feature_key} in {environment}: {message}")
                
        except Exception as e:
            error_message = f"❌ Error: {str(e)}"
            error_response = {
                "operation": "feature_flag_update",
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": error_message,
                "exception_details": str(e),
                "request": {
                    "feature_key": feature_key,
                    "environment": environment,
                    "action": "enable" if enable else "disable",
                    "pmc_id": pmcid if pmcid else None,
                    "site_id": siteid if siteid else None
                }
            }
            
            self.update_loading_var.set(error_message)
            self.update_result_label.config(text=f"Error: {str(e)}")
            
            # Update response box with exception details
            self.update_response_box(error_response)
            
            logger.exception(f"Exception updating feature flag: {str(e)}")
        
        # Hide loading indicator and re-enable buttons
        self.loading_frame.pack_forget()
        self.update_on_button.config(state="normal")
        self.update_off_button.config(state="normal")

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

    def apply_default_rule(self):
        """Apply only the default rule (fallthrough/offVariation) without toggling ON/OFF."""
        feature_key = self.update_key_var.get().strip()
        environment = self.environment_entry.get()
        desired_raw = (self.fallthrough_option_var.get() or "").strip().lower()

        if not feature_key:
            messagebox.showwarning("Warning", "Please enter a feature flag key.")
            return

        if desired_raw not in ("true", "false"):
            messagebox.showwarning("Warning", "Choose True or False under 'Default rule (fallthrough)'.")
            return

        # Show loading indicator
        self.loading_frame.pack(pady=10)
        self.update_loading_var.set(f"Applying default rule for {feature_key} in {environment}...")
        self.parent.update_idletasks()

        try:
            # Clear previous response
            self.update_response_box(None)

            response_data = {
                "operation": "fallthrough_update_only",
                "timestamp": datetime.now().isoformat(),
                "request": {
                    "feature_key": feature_key,
                    "environment": environment,
                    "action": "fallthrough_update",
                    "pmc_id": None,
                    "site_id": None
                },
                "api_responses": []
            }

            flag_data = self.get_flag_configuration(feature_key)
            if not flag_data:
                self.update_loading_var.set("Error retrieving flag configuration")
                self.update_result_label.config(text="Could not retrieve flag configuration.")
                response_data["success"] = False
                response_data["error"] = "Could not retrieve flag configuration"
                self.update_response_box(response_data)
                return

            # Apply configuration update without forcing the flag ON and without resetting inputs
            success = self.update_flag_configuration(
                feature_key,
                flag_data,
                environment,
                ensure_on=False,
                reset_fields=False
            )

            response_data["success"] = success
            response_data["result_message"] = "Default rule updated" if success else "Failed to update default rule"
            self.update_response_box(response_data)

            if success:
                self.update_loading_var.set(f"✅ Default rule updated for {feature_key}")
                self.update_result_label.config(text=f"Fallthrough/offVariation set in {environment}")
                logger.info(f"Default rule updated for key={feature_key} env={environment}")
                # Audit to Notifications tab
                try:
                    actual_env = ENVIRONMENT_MAPPINGS.get(environment, environment)
                    audit_event(
                        "default_rule_update",
                        {
                            "feature_key": feature_key,
                            "environment": actual_env,
                            "enabled": True if desired_raw == "true" else False,
                            "note": "fallthrough/offVariation updated via Apply Default Rule",
                        },
                        ok=True,
                    )
                except Exception:
                    pass
                # Reset the dropdown to 'No value' after success
                try:
                    if hasattr(self, 'fallthrough_option_var'):
                        self.fallthrough_option_var.set("No value")
                except Exception:
                    pass
            else:
                self.update_loading_var.set("❌ Failed to update default rule")
                self.update_result_label.config(text=f"Failed to update default rule for '{feature_key}' in {environment}")
                logger.error(f"Failed to update default rule for key={feature_key} env={environment}")
                # Audit failure
                try:
                    actual_env = ENVIRONMENT_MAPPINGS.get(environment, environment)
                    audit_event(
                        "default_rule_update",
                        {
                            "feature_key": feature_key,
                            "environment": actual_env,
                            "enabled": True if desired_raw == "true" else False,
                            "note": "fallthrough/offVariation update failed",
                        },
                        ok=False,
                    )
                except Exception:
                    pass

        except Exception as e:
            self.update_loading_var.set(f"❌ Error: {str(e)}")
            self.update_result_label.config(text=str(e))
            logger.exception(f"Exception applying default rule: {str(e)}")
        finally:
            self.loading_frame.pack_forget()

    def update_flag_with_pmcid_targeting(self, feature_key, environment, pmcid, siteid, enable):
        """Update flag with intelligent PMC ID targeting"""
        logger.debug(f"Starting intelligent targeting for PMC ID: {pmcid}")
        
        api_responses = []
        
        try:
            # First, get the current flag configuration
            flag_data = self.get_flag_configuration(feature_key)
            if not flag_data:
                api_responses.append({"operation": "get_flag_config", "success": False, "error": "Could not retrieve flag configuration"})
                return False, "Could not retrieve flag configuration", api_responses
            
            api_responses.append({"operation": "get_flag_config", "success": True, "data": flag_data})
            
            actual_env = ENVIRONMENT_MAPPINGS.get(environment, environment)
            environments = flag_data.get("environments", {})
            env_data = environments.get(actual_env, {})
            
            if not env_data:
                api_responses.append({"operation": "environment_check", "success": False, "error": f"Environment '{actual_env}' not found in flag configuration"})
                return False, f"Environment '{actual_env}' not found in flag configuration", api_responses
            
            logger.debug(f"Current environment data retrieved for {actual_env}")
            
            # Check for existing PMC ID rules
            rules = env_data.get("rules", [])
            pmcid_int = None
            try:
                pmcid_int = int(pmcid)
            except:
                pmcid_int = pmcid  # Keep as string if conversion fails
            
            logger.debug("=== TWO-RULE SYSTEM ===")
            logger.debug(f"Checking {len(rules)} existing rules for PMC ID: {pmcid_int}")
            
            # Debug: List all existing rules
            for i, rule in enumerate(rules):
                rule_desc = rule.get("description", "No description")
                rule_var = rule.get("variation", "Unknown")
                logger.debug(f"Rule {i}: '{rule_desc}' (variation: {rule_var})")
            
            # Determine the variation index for enable/disable FIRST
            variations = flag_data.get("variations", [])
            enable_variation = 0  # Assume first variation is "true/enabled"
            disable_variation = 1  # Assume second variation is "false/disabled"
            
            # Try to determine correct variations based on values
            for i, variation in enumerate(variations):
                if variation.get("value") == True:
                    enable_variation = i
                elif variation.get("value") == False:
                    disable_variation = i
            
            target_variation = enable_variation if enable else disable_variation
            logger.debug(f"Target variation determined: {target_variation} ({'enable' if enable else 'disable'})")
            logger.debug(f"Enable variation: {enable_variation}, Disable variation: {disable_variation}")
            
            # Look for the two standard PMC rules: enabled and disabled
            enabled_rule_index = -1
            disabled_rule_index = -1
            current_pmcid_rule_index = -1
            
            for i, rule in enumerate(rules):
                rule_description = rule.get("description", "").lower()
                rule_variation = rule.get("variation", -1)
                clauses = rule.get("clauses", [])
                
                # Check if this is one of our standard PMC rules
                has_pmcid_clause = any(c.get("attribute") == "PmcId" for c in clauses)
                
                if has_pmcid_clause:
                    if "pmcs enabled rule" in rule_description or rule_variation == enable_variation:
                        if enabled_rule_index == -1:  # Only take the first one we find
                            enabled_rule_index = i
                            logger.debug(f"Found PMCs Enabled Rule at index {i} (description: '{rule.get('description', '')}')")
                    elif "pmcs disabled rule" in rule_description or rule_variation == disable_variation:
                        if disabled_rule_index == -1:  # Only take the first one we find
                            disabled_rule_index = i
                            logger.debug(f"Found PMCs Disabled Rule at index {i} (description: '{rule.get('description', '')}')")
                
                # Check if this PMC ID is in any rule
                for clause in clauses:
                    if clause.get("attribute") == "PmcId":
                        clause_values = clause.get("values", [])
                        if pmcid_int in clause_values or str(pmcid_int) in clause_values:
                            current_pmcid_rule_index = i
                            logger.debug(f"Found PMC ID {pmcid_int} in rule at index {i} (variation {rule_variation})")
                            break
                
                if current_pmcid_rule_index >= 0:
                    continue  # Keep looking for standard rules even if we found the PMC
            
            # Determine what action to take with the two-rule system
            target_rule_index = enabled_rule_index if enable else disabled_rule_index
            source_rule_index = disabled_rule_index if enable else enabled_rule_index
            
            logger.debug(f"Target rule index: {target_rule_index}, Source rule index: {source_rule_index}")
            
            # Check if PMC is already in the correct rule
            if current_pmcid_rule_index == target_rule_index and target_rule_index >= 0:
                logger.debug(f"PMC ID {pmcid_int} already in correct rule")
                action_description = f"PMC ID {pmcid_int} already {'enabled' if enable else 'disabled'} - no changes needed"
                success = True
                rule_to_apply = None
                rule_index_to_update = -1
                # DEDUPE: ensure PMC is not present in the opposite rule
                try:
                    patches_needed = []
                    if source_rule_index >= 0:
                        src_rule = rules[source_rule_index].copy()
                        for clause in src_rule.get("clauses", []):
                            if clause.get("attribute") == "PmcId":
                                vals = clause.get("values", [])
                                new_vals = [v for v in vals if v != pmcid_int and v != str(pmcid_int)]
                                if len(new_vals) != len(vals):
                                    clause["values"] = new_vals
                                    if not new_vals:
                                        # Remove empty rule entirely
                                        patches_needed.append({
                                            "op": "remove",
                                            "path": f"/environments/{actual_env}/rules/{source_rule_index}"
                                        })
                                    else:
                                        # Replace the opposite rule with the updated values
                                        patches_needed.append({
                                            "op": "replace",
                                            "path": f"/environments/{actual_env}/rules/{source_rule_index}",
                                            "value": src_rule
                                        })
                                break
                    if patches_needed:
                        dedupe_ok = self.update_flag_configuration(
                            feature_key,
                            flag_data,
                            environment,
                            rule_index_to_update=-1,
                            rule_to_apply=None,
                            additional_operations=patches_needed
                        )
                        api_responses.append({
                            "operation": "dedupe_source_rule",
                            "success": bool(dedupe_ok),
                            "message": "Removed PMC from opposite rule to avoid duplication"
                        })
                        if dedupe_ok:
                            action_description += " | deduped in opposite rule"
                except Exception as _e:
                    logger.debug(f"Dedupe check error: {_e}")
            elif current_pmcid_rule_index == -1 and target_rule_index == -1:
                # No PMC rules exist yet - create the first standard rule
                logger.debug("No PMC targeting rules exist yet, creating first standard rule")
                rule_to_apply = self.create_standard_pmc_rule(pmcid_int, target_variation, enable)
                rule_index_to_update = -1
                action_description = f"Created first PMC targeting rule: {'enabled' if enable else 'disabled'} with PMC {pmcid_int}"
                additional_ops = []
            else:
                # Need to move PMC between rules or add to target rule
                patches_needed = []
                
                # Step 1: Remove from source rule (if exists)
                rule_deleted = False
                adjusted_target_rule_index = target_rule_index
                
                if current_pmcid_rule_index >= 0 and current_pmcid_rule_index != target_rule_index:
                    logger.debug(f"Removing PMC ID {pmcid_int} from rule at index {current_pmcid_rule_index}")
                    source_rule = rules[current_pmcid_rule_index].copy()
                    
                    # Remove PMC ID from the source rule
                    remaining_pmcs = []
                    for clause in source_rule["clauses"]:
                        if clause.get("attribute") == "PmcId":
                            clause_values = clause.get("values", [])
                            new_values = [v for v in clause_values if v != pmcid_int and v != str(pmcid_int)]
                            clause["values"] = new_values
                            remaining_pmcs = new_values
                            break
                    
                    # SMART RULING: Delete empty rule instead of keeping it; otherwise, replace the rule without the PMC
                    if not remaining_pmcs:
                        logger.debug(f"SMART RULING - Source rule will be empty, deleting entire rule at index {current_pmcid_rule_index}")
                        # Get the actual rule ID (UUID) from the rule
                        source_rule_id = source_rule.get("_id")
                        # Use JSON Patch to remove the rule by index
                        patches_needed.append({
                            "op": "remove",
                            "path": f"/environments/{actual_env}/rules/{current_pmcid_rule_index}"
                        })
                        logger.debug(f"Will remove rule at index: {current_pmcid_rule_index}")
                        rule_deleted = True
                        
                        # Adjust target rule index if it comes after the deleted rule
                        if target_rule_index > current_pmcid_rule_index:
                            adjusted_target_rule_index = target_rule_index - 1
                            logger.debug(f"Adjusted target rule index from {target_rule_index} to {adjusted_target_rule_index}")
                    else:
                        logger.debug("Updating source rule to remove PMC without deleting entire rule")
                        patches_needed.append({
                            "op": "replace",
                            "path": f"/environments/{actual_env}/rules/{current_pmcid_rule_index}",
                            "value": source_rule
                        })
                # Step 2: Add to or create target rule
                if adjusted_target_rule_index >= 0:
                    # Add to existing target rule
                    logger.debug(f"Adding PMC ID {pmcid_int} to existing {'enabled' if enable else 'disabled'} rule at index {adjusted_target_rule_index}")
                    target_rule = rules[adjusted_target_rule_index].copy()

                    # Add PMC ID to the target rule
                    for clause in target_rule.get("clauses", []):
                        if clause.get("attribute") == "PmcId":
                            if pmcid_int not in clause.get("values", []):
                                clause["values"].append(pmcid_int)
                            break

                    rule_to_apply = target_rule
                    rule_index_to_update = adjusted_target_rule_index

                    if rule_deleted:
                        action_description = f"Deleted empty rule and moved PMC {pmcid_int} to {'enabled' if enable else 'disabled'} rule"
                    else:
                        action_description = f"Moved PMC {pmcid_int} to {'enabled' if enable else 'disabled'} rule"
                else:
                    # Create new standard rule
                    logger.debug(f"Creating new standard {'enabled' if enable else 'disabled'} rule")
                    rule_to_apply = self.create_standard_pmc_rule(pmcid_int, target_variation, enable)
                    rule_index_to_update = -1
                    action_description = f"Created new {'enabled' if enable else 'disabled'} rule with PMC {pmcid_int}"

                additional_ops = patches_needed

            # Apply the changes via API using JSON Patch operations
            if rule_to_apply:
                success = self.update_flag_configuration(
                    feature_key,
                    flag_data,
                    environment,
                    rule_index_to_update,
                    rule_to_apply,
                    additional_ops
                )
                api_responses.append({
                    "operation": "update_flag_config",
                    "success": success,
                    "rule_index": rule_index_to_update,
                    "additional_operations": additional_ops
                })
            else:
                success = True
                api_responses.append({
                    "operation": "no_changes_needed",
                    "success": True,
                    "message": "PMC ID already in correct state"
                })

                # If user requested to set default rule (fallthrough) to True/False and we are enabling,
                # apply a follow-up JSON Patch to set fallthrough even when no rule changes are needed and audit it.
                try:
                    desired = ""
                    if getattr(self, 'fallthrough_option_var', None):
                        desired = (self.fallthrough_option_var.get() or "").strip().lower()
                    if enable and desired in ("true", "false"):
                        logger.debug("Applying fallthrough update in intelligent path (no changes needed case)...")
                        ft_success = self.update_flag_configuration(feature_key, flag_data, environment)
                        api_responses.append({
                            "operation": "fallthrough_update",
                            "success": ft_success
                        })
                        # Audit default rule update for Notifications tab
                        try:
                            actual_env = ENVIRONMENT_MAPPINGS.get(environment, environment)
                            audit_event(
                                "default_rule_update",
                                {
                                    "feature_key": feature_key,
                                    "environment": actual_env,
                                    "enabled": True if desired == "true" else False,
                                    "note": "fallthrough/offVariation updated in intelligent path",
                                },
                                ok=bool(ft_success),
                            )
                        except Exception:
                            pass
                        if not ft_success:
                            logger.error("Failed to update fallthrough variation in intelligent path (no changes needed)")
                except Exception as e:
                    logger.exception(f"Exception applying fallthrough update in intelligent path: {str(e)}")

            if success:
                # Audit concise summary for Notifications tab
                try:
                    audit_event(
                        "pmc_targeting_update",
                        {
                            "feature_key": feature_key,
                            "environment": actual_env,
                            "enabled": bool(enable),
                            "pmc_id": str(pmcid_int),
                            "site_id": str(siteid) if siteid else "",
                            "summary": action_description,
                        },
                        ok=True,
                    )
                except Exception:
                    pass
                return True, action_description, api_responses
            else:
                api_responses.append({"operation": "final_result", "success": False, "error": "Failed to apply targeting rule changes"})
                try:
                    audit_event(
                        "pmc_targeting_update",
                        {
                            "feature_key": feature_key,
                            "environment": actual_env,
                            "enabled": bool(enable),
                            "pmc_id": str(pmcid_int),
                            "site_id": str(siteid) if siteid else "",
                            "summary": "Failed to apply targeting rule changes",
                        },
                        ok=False,
                    )
                except Exception:
                    pass
                return False, "Failed to apply targeting rule changes", api_responses
                
        except Exception as e:
            logger.exception(f"Exception in intelligent targeting: {str(e)}")
            api_responses.append({"operation": "exception", "success": False, "error": str(e)})
            return False, f"Error in intelligent targeting: {str(e)}", api_responses

    def create_standard_pmc_rule(self, pmcid_int, target_variation, enable):
        """Create a standard PMC rule dict for enabled/disabled state."""
        description = "PMCs Enabled Rule" if enable else "PMCs Disabled Rule"
        new_rule = {
            "variation": target_variation,
            "description": description,
            "clauses": [
                {
                    "attribute": "PmcId",
                    "op": "in",
                    "values": [pmcid_int],
                    "negate": False
                }
            ],
            "trackEvents": True
        }
        logger.debug(f"Created standard rule: {description} with PMC {pmcid_int}")
        return new_rule

    def get_flag_configuration(self, feature_key):
        """Get current flag configuration from LaunchDarkly"""
        try:
            # Validate configuration before constructing URL
            if not PROJECT_KEY or not LAUNCHDARKLY_API_KEY:
                logger.error("Missing LaunchDarkly configuration (PROJECT_KEY or API key). Cannot fetch flag configuration.")
                return None
            url = URLBuilder.build_flag_url(PROJECT_KEY, feature_key)
            headers = APIHeaders.get_launchdarkly_headers(LAUNCHDARKLY_API_KEY)
            logger.debug(f"Fetching flag configuration from: {url}")
            
            response = requests.get(url, headers=headers, timeout=APIConfig.DEFAULT_TIMEOUT)
            
            if response.status_code == 200:
                flag_data = response.json()
                logger.info("Successfully retrieved flag configuration")
                return flag_data
            else:
                logger.error(f"Failed to get flag configuration: {response.status_code}")
                return None
                
        except Exception as e:
            logger.exception(f"Exception getting flag configuration: {str(e)}")
            return None

    def update_flag_configuration(self, feature_key, flag_data, environment, rule_index_to_update=-1, rule_to_apply=None, additional_operations=None, ensure_on=True, reset_fields=True):
        """Update flag configuration in LaunchDarkly using JSON Patch operations with user attribution.

        Parameters:
        - ensure_on: If True, force the flag's 'on' state to True. If False, do not modify the 'on' state.
        - reset_fields: If True, reset the Update tab fields after success. Useful to keep context when only editing fallthrough.
        """
        from shared.user_session import get_api_comment
        try:
            url = URLBuilder.build_flag_url(PROJECT_KEY, feature_key)
            headers = APIHeaders.get_launchdarkly_headers(LAUNCHDARKLY_API_KEY)
            # Validate configuration before making request
            if not PROJECT_KEY or not LAUNCHDARKLY_API_KEY:
                logger.error("Missing LaunchDarkly configuration (PROJECT_KEY or API key). Cannot update flag configuration.")
                return False
            actual_env = ENVIRONMENT_MAPPINGS.get(environment, environment)

            # Build JSON Patch operations
            patch_operations = []

            # Determine boolean variation indices for default rule (fallthrough)
            true_index = 0
            false_index = 1
            try:
                variations = flag_data.get("variations", [])
                for i, v in enumerate(variations):
                    if v.get("value") is True:
                        true_index = i
                    elif v.get("value") is False:
                        false_index = i
            except Exception:
                # Fallback to defaults if variations are unexpected
                pass

            # Optionally ensure flag is turned ON
            if ensure_on:
                patch_operations.append({
                    "op": "replace",
                    "path": f"/environments/{actual_env}/on",
                    "value": True
                })

            # Optionally set default rule (fallthrough) to True/False based on UI selection
            try:
                desired = ""
                if getattr(self, 'fallthrough_option_var', None):
                    desired = (self.fallthrough_option_var.get() or "").strip().lower()
                if desired in ("true", "false"):
                    desired_index = true_index if desired == "true" else false_index
                    envs = flag_data.get("environments", {})
                    env_obj = envs.get(actual_env, {}) if isinstance(envs, dict) else {}
                    fallthrough_obj = env_obj.get("fallthrough", {}) if isinstance(env_obj, dict) else {}
                    if isinstance(fallthrough_obj, dict) and "variation" in fallthrough_obj:
                        logger.debug(f"Fallthrough uses 'variation' - patching /fallthrough/variation to {desired}")
                        patch_operations.append({
                            "op": "replace",
                            "path": f"/environments/{actual_env}/fallthrough/variation",
                            "value": desired_index
                        })
                    else:
                        # Some flags (e.g., migration) use 'rollout' in fallthrough. Replace entire fallthrough with a rollout
                        # that serves 100% of the selected variation.
                        logger.debug(f"Fallthrough not in 'variation' form - replacing entire fallthrough with rollout 100% {desired}")
                        patch_operations.append({
                            "op": "replace",
                            "path": f"/environments/{actual_env}/fallthrough",
                            "value": {
                                "rollout": {
                                    "variations": [
                                        {"variation": desired_index, "weight": 100000}
                                    ],
                                    "contextKind": "user"
                                }
                            }
                        })
                    # Also set offVariation so that when the flag is OFF, it serves the selected variation
                    logger.debug(f"Patching /offVariation to index {desired_index} ({desired})")
                    patch_operations.append({
                        "op": "replace",
                        "path": f"/environments/{actual_env}/offVariation",
                        "value": desired_index
                    })
            except Exception as e:
                # If UI var not present or structure unexpected, skip this optional change
                logger.debug(f"Skipping optional fallthrough update due to: {e}")

            # Add any additional operations first (like removing from old rules)
            if additional_operations:
                patch_operations.extend(additional_operations)

            # Update existing rule or add a new one
            if rule_to_apply is not None and rule_index_to_update >= 0:
                logger.debug(f"Creating patch to update existing rule at index {rule_index_to_update}")
                patch_operations.append({
                    "op": "replace",
                    "path": f"/environments/{actual_env}/rules/{rule_index_to_update}",
                    "value": rule_to_apply
                })
            elif rule_to_apply is not None:
                logger.debug("Creating patch to add new rule")
                patch_operations.append({
                    "op": "add",
                    "path": f"/environments/{actual_env}/rules/-",
                    "value": rule_to_apply
                })

            # Prepare payload with comment per LaunchDarkly docs (Updates with comments)
            payload = {
                "comment": get_api_comment(f"Flag configuration update for {feature_key}"),
                "patch": patch_operations
            }

            logger.debug(f"Updating flag configuration at: {url}")
            logger.debug(f"JSON Patch payload: {json.dumps(payload, indent=2)}")

            response = requests.patch(url, headers=headers, json=payload, timeout=APIConfig.DEFAULT_TIMEOUT)

            if response.status_code in [200, 204]:
                logger.info("Successfully updated flag configuration")
                if reset_fields:
                    self.reset_update_fields()
                return True
            else:
                try:
                    resp_text = response.text
                except Exception:
                    resp_text = ""
                # Sanitize response text to ASCII-only for CI compatibility
                try:
                    resp_text_ascii = resp_text.encode("ascii", "ignore").decode("ascii")
                except Exception:
                    resp_text_ascii = ""
                logger.error(f"Failed to update flag configuration: {response.status_code} - {resp_text_ascii}")
                return False

        except Exception as e:
            logger.exception(f"Exception updating flag configuration: {str(e)}")
            return False

    def reset_log(self):
        """Reset loading text"""
        self.update_loading_var.set("")
        self.loading_frame.pack_forget()
    
    def reset_update_fields(self):
        """Reset input fields and UI state for the Update tab."""
        try:
            # Reset input fields
            self.update_key_var.set("")
            self.environment_entry.set("DEV")
            self.pmcid_var.set("")
            self.siteid_var.set("")
            # Reset fallthrough selection to 'No value'
            try:
                if hasattr(self, 'fallthrough_option_var'):
                    self.fallthrough_option_var.set("No value")
            except Exception:
                pass

            # Reset status labels and loading UI
            self.update_result_label.config(text="")
            self.update_loading_var.set("")
            self.loading_frame.pack_forget()

            # Clear API response box
            self.update_response_box(None)

            # Re-enable action buttons
            self.update_on_button.config(state="normal")
            self.update_off_button.config(state="normal")

            logger.debug("Update tab fields reset")
        except Exception as e:
            logger.exception(f"Error resetting update fields: {e}")

    def animate_spinner(self):
        """Animate the loading spinner while the loading frame is visible."""
        try:
            # Initialize spinner state
            if not hasattr(self, "_spinner_index"):
                self._spinner_index = 0
            spinner_chars = "|/-\\"

            # Only animate if loading frame is visible
            if self.loading_frame.winfo_ismapped():
                char = spinner_chars[self._spinner_index % len(spinner_chars)]
                self.loading_spinner.config(text=char)
                self._spinner_index += 1
                self.parent.after(100, self.animate_spinner)
            else:
                # Reset icon when not animating
                self.loading_spinner.config(text="⏳")
        except Exception as e:
            logger.debug(f"Spinner animation stopped: {e}")

    def update_response_box(self, response_data):
        """Update the response text box with formatted API response data (summary + raw)"""
        self.response_text.config(state="normal")
        self.response_text.delete(1.0, tk.END)
        
        if not response_data:
            self.response_text.config(state="disabled")
            return
            
        try:
            # Parse the response data if it's a JSON string
            if isinstance(response_data, str):
                data = json.loads(response_data)
            else:
                data = response_data
                
            # Build formatted content with summary and raw sections
            content_lines = []
            
            # === SUMMARY SECTION ===
            content_lines.append("=" * 50)
            content_lines.append("OPERATION SUMMARY")
            content_lines.append("=" * 50)
            
            # Basic operation info
            operation = data.get("operation", "Unknown")
            timestamp = data.get("timestamp", "")
            success = data.get("success", False)
            
            content_lines.append(f"🔧 Operation: {operation}")
            content_lines.append(f"⏰ Timestamp: {timestamp}")
            content_lines.append(f"✅ Status: {'Success' if success else 'Failed'}")
            
            # Request details
            request_info = data.get("request", {})
            if request_info:
                content_lines.append("")
                content_lines.append("📝 Request Details:")
                content_lines.append(f"   🚩 Feature Key: {request_info.get('feature_key', 'N/A')}")
                content_lines.append(f"   🌐 Environment: {request_info.get('environment', 'N/A')}")
                content_lines.append(f"   ⚡ Action: {request_info.get('action', 'N/A')}")
                if request_info.get('pmc_id'):
                    content_lines.append(f"   🏢 PMC ID: {request_info.get('pmc_id')}")
                if request_info.get('site_id'):
                    content_lines.append(f"   🌍 Site ID: {request_info.get('site_id')}")
            
            # Result message
            result_message = data.get("result_message", "")
            if result_message:
                content_lines.append("")
                content_lines.append(f"💬 Result: {result_message}")
            
            # API responses summary
            api_responses = data.get("api_responses", [])
            if api_responses:
                content_lines.append("")
                content_lines.append(f"📡 API Calls Made: {len(api_responses)}")
                for i, api_call in enumerate(api_responses, 1):
                    operation_type = api_call.get("operation", "Unknown")
                    call_success = api_call.get("success", False)
                    status_icon = "✅" if call_success else "❌"
                    content_lines.append(f"   {i}. {status_icon} {operation_type}")
            
            # Context information
            context = data.get("context", [])
            if context:
                content_lines.append("")
                content_lines.append(f"🎯 Context: {', '.join(context)}")
            
            # Error details if any
            error = data.get("error")
            if error:
                content_lines.append("")
                content_lines.append(f"❌ Error: {error}")
                
            exception_details = data.get("exception_details")
            if exception_details:
                content_lines.append(f"🔍 Details: {exception_details}")
            
            # === STRUCTURED DATA SECTION ===
            content_lines.append("")
            content_lines.append("=" * 50)
            content_lines.append("STRUCTURED DATA")
            content_lines.append("=" * 50)
            
            # Create a clean structured summary
            structured_summary = {
                "OPERATION_SUMMARY": {
                    "operation_type": operation,
                    "timestamp": timestamp,
                    "success": success,
                    "feature_key": request_info.get("feature_key") if request_info else None,
                    "environment": request_info.get("environment") if request_info else None,
                    "action": request_info.get("action") if request_info else None,
                    "result_message": result_message,
                    "total_api_calls": len(api_responses)
                }
            }
            
            if request_info:
                structured_summary["REQUEST_CONTEXT"] = {
                    "pmc_id": request_info.get("pmc_id"),
                    "site_id": request_info.get("site_id"),
                    "targeting_applied": bool(request_info.get("pmc_id") or request_info.get("site_id"))
                }
            
            if api_responses:
                structured_summary["API_CALLS_SUMMARY"] = []
                for api_call in api_responses:
                    call_summary = {
                        "operation": api_call.get("operation", "Unknown"),
                        "success": api_call.get("success", False),
                        "message": api_call.get("message", ""),
                        "method": api_call.get("method", ""),
                        "url": api_call.get("url", "")
                    }
                    structured_summary["API_CALLS_SUMMARY"].append(call_summary)
            
            content_lines.append(json.dumps(structured_summary, indent=2))
            
            # === RAW API RESPONSES SECTION ===
            content_lines.append("")
            content_lines.append("=" * 50)
            content_lines.append("RAW API RESPONSES")
            content_lines.append("=" * 50)
            content_lines.append(json.dumps(data, indent=2))
            
            # Display the formatted content
            final_content = "\n".join(content_lines)
            self.response_text.insert(1.0, final_content)
            
        except Exception as e:
            # Fallback to raw JSON if formatting fails
            error_content = f"Error formatting response data: {str(e)}\n\n=== RAW DATA ===\n"
            if isinstance(response_data, str):
                error_content += response_data
            else:
                error_content += json.dumps(response_data, indent=2)
            self.response_text.insert(1.0, error_content)
        
        self.response_text.config(state="disabled") 