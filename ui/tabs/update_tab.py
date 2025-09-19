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

class UpdateTab:
    def __init__(self, parent, history_manager, theme_manager):
        self.parent = parent
        self.history_manager = history_manager
        self.theme_manager = theme_manager
        # Initialize optimized API client
        self.api_client = get_client()
        self.setup_ui()

    def setup_ui(self):
        """Sets up the UI for the 'Update Feature Flag' tab with a modern card-based layout."""
        # --- Main container with enhanced spacing ---
        main_container = ttk.Frame(self.parent, padding=25)
        main_container.pack(fill="both", expand=True)

        # --- Enhanced Header Section ---
        header_container = ttk.Frame(main_container)
        header_container.pack(fill="x", pady=(0, 25))
        
        # Title card with modern styling
        title_card = ttk.Frame(header_container, style="Card.TFrame", padding=20)
        title_card.pack(fill="x", pady=(0, 10))
        
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
        config_card = ttk.Frame(content_container, style="Card.TFrame", padding=25)
        config_card.pack(fill="x", pady=(0, 20))
        
        # Configuration header with modern styling
        config_header = ttk.Frame(config_card)
        config_header.pack(fill="x", pady=(0, 20))
        
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
        left_header.pack(anchor="w", pady=(0, 15))
        
        # Feature Flag Key with enhanced styling
        key_container = ttk.Frame(left_column, style="Card.TFrame", padding=15)
        key_container.pack(fill="x", pady=(0, 15))
        
        key_label = ttk.Label(
            key_container, 
            text="🔑 Feature Flag Key", 
            font=("Segoe UI", 12, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        key_label.pack(anchor="w", pady=(0, 8))
        
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
        env_container = ttk.Frame(left_column, style="Card.TFrame", padding=15)
        env_container.pack(fill="x", pady=(0, 10))
        
        env_label = ttk.Label(
            env_container, 
            text="🌍 Environment", 
            font=("Segoe UI", 12, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        env_label.pack(anchor="w", pady=(0, 8))
        
        self.environment_entry = ttk.Combobox(
            env_container, 
            values=UPDATE_ENVIRONMENT_OPTIONS, 
            font=("Segoe UI", 11),
            state="readonly",
            height=8
        )
        self.environment_entry.set("DEV")
        self.environment_entry.pack(fill="x", pady=(0, 8))
        
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
        right_header.pack(anchor="w", pady=(0, 15))
        
        # PMC ID field with enhanced styling
        pmcid_container = ttk.Frame(right_column, style="Card.TFrame", padding=15)
        pmcid_container.pack(fill="x", pady=(0, 15))
        
        pmcid_label = ttk.Label(
            pmcid_container, 
            text="🏢 PMC ID (Optional)", 
            font=("Segoe UI", 12, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        pmcid_label.pack(anchor="w", pady=(0, 8))
        
        self.pmcid_var = tk.StringVar()
        self.pmcid_entry = ttk.Entry(
            pmcid_container, 
            textvariable=self.pmcid_var, 
            font=("Segoe UI", 11)
        )
        self.pmcid_entry.pack(fill="x", pady=(0, 8))
        
        # Enhanced helper text for PMCID
        pmcid_help = ttk.Label(
            pmcid_container,
            text="📊 For intelligent targeting and context",
            font=("Segoe UI", 10),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        pmcid_help.pack(anchor="w")

        # Site ID field with enhanced styling
        siteid_container = ttk.Frame(right_column, style="Card.TFrame", padding=15)
        siteid_container.pack(fill="x", pady=(0, 10))
        
        siteid_label = ttk.Label(
            siteid_container, 
            text="🌍 Site ID (Optional)", 
            font=("Segoe UI", 12, "bold"),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        siteid_label.pack(anchor="w", pady=(0, 8))
        
        self.siteid_var = tk.StringVar()
        self.siteid_entry = ttk.Entry(
            siteid_container, 
            textvariable=self.siteid_var, 
            font=("Segoe UI", 11)
        )
        self.siteid_entry.pack(fill="x", pady=(0, 8))
        
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
        action_container.pack(fill="x", pady=(25, 0))
        
        # Action buttons with enhanced modern styling
        action_frame = ttk.Frame(action_container, style="Card.TFrame", padding=15)
        action_frame.pack(fill="x")
        
        # Centered button layout
        button_container = ttk.Frame(action_frame)
        button_container.pack(expand=True)
        
        self.update_on_button = ttk.Button(
            button_container, 
            text="🟢 Turn ON", 
            bootstyle="success", 
            width=18,
            command=lambda: self.toggle_feature_flag(True)
        )
        self.update_on_button.pack(side="left", padx=(0, 15))

        self.update_off_button = ttk.Button(
            button_container, 
            text="🔴 Turn OFF", 
            bootstyle="danger", 
            width=18,
            command=lambda: self.toggle_feature_flag(False)
        )
        self.update_off_button.pack(side="left", padx=(0, 15))

        reset_button = ttk.Button(
            button_container, 
            text="🔄 Reset", 
            bootstyle="secondary", 
            width=15,
            command=self.reset_update_fields
        )
        reset_button.pack(side="left")

        # === TWO-COLUMN LAYOUT: STATUS & API RESPONSE ===
        columns_container = ttk.Frame(content_container)
        columns_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # === LEFT COLUMN: UPDATE STATUS ===
        left_column = ttk.Frame(columns_container, style="Card.TFrame", padding=20)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Status header with modern styling
        status_header = ttk.Frame(left_column)
        status_header.pack(fill="x", pady=(0, 20))
        
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
        self.loading_frame.pack(pady=10)
        
        self.loading_spinner = ttk.Label(
            self.loading_frame,
            text="⏳",
            font=("Segoe UI", 16),
            foreground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        self.loading_spinner.pack(side="left", padx=(0, 10))
        
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
        self.update_result_label.pack(pady=10, anchor="w")

        # === RIGHT COLUMN: API RESPONSE DETAILS ===
        right_column = ttk.Frame(columns_container, style="Card.TFrame", padding=20)
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
            bg=self.theme_manager.get_theme_config()["colors"]["surface"],
            fg=self.theme_manager.get_theme_config()["colors"]["text"],
            selectbackground=self.theme_manager.get_theme_config()["colors"]["primary"],
            insertbackground=self.theme_manager.get_theme_config()["colors"]["text"]
        )
        
        # Enhanced scrollbar setup
        response_scrollbar = ttk.Scrollbar(text_container, orient="vertical", command=self.response_text.yview)
        self.response_text.configure(yscrollcommand=response_scrollbar.set)
        
        # Pack text widget and scrollbar properly
        self.response_text.pack(side="left", fill="both", expand=True)
        response_scrollbar.pack(side="right", fill="y")



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

        print(f"DEBUG: UPDATE Tab - Feature Key: {feature_key}")
        print(f"DEBUG: UPDATE Tab - Environment: {environment}")
        print(f"DEBUG: UPDATE Tab - Action: {'Enable' if enable else 'Disable'}")
        print(f"DEBUG: UPDATE Tab - PMC ID: {pmcid}")
        print(f"DEBUG: UPDATE Tab - Site ID: {siteid}")

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
                print(f"DEBUG: PMC ID provided, using intelligent targeting...")
                success, message, api_responses = self.update_flag_with_pmcid_targeting(feature_key, environment, pmcid, siteid, enable)
                response_data["api_responses"] = api_responses
            else:
                # Use standard flag toggle
                print(f"DEBUG: No PMC ID provided, using standard flag toggle...")
                success = update_flag(environment, feature_key, enable)
                message = f"Flag '{feature_key}' {'enabled' if enable else 'disabled'} globally in {environment}"
                response_data["api_responses"] = [{"operation": "standard_toggle", "success": success, "message": message}]
            
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
                
                print(f"DEBUG: SUCCESS - {success_message}{context_display}")
                print(f"DEBUG: Details - {message}")
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
                
                print(f"DEBUG: FAILURE - {error_message}: {message}")
                
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
            
            print(f"DEBUG: EXCEPTION - {error_message}")
            logging.error(f"Error updating feature flag: {str(e)}")
        
        # Hide loading indicator and re-enable buttons
        self.loading_frame.pack_forget()
        self.update_on_button.config(state="normal")
        self.update_off_button.config(state="normal")

    def update_flag_with_pmcid_targeting(self, feature_key, environment, pmcid, siteid, enable):
        """Update flag with intelligent PMC ID targeting"""
        print(f"DEBUG: Starting intelligent targeting for PMC ID: {pmcid}")
        
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
            
            print(f"DEBUG: Current environment data retrieved for {actual_env}")
            
            # Check for existing PMC ID rules
            rules = env_data.get("rules", [])
            pmcid_int = None
            try:
                pmcid_int = int(pmcid)
            except:
                pmcid_int = pmcid  # Keep as string if conversion fails
            
            print(f"DEBUG: === TWO-RULE SYSTEM ===")
            print(f"DEBUG: Checking {len(rules)} existing rules for PMC ID: {pmcid_int}")
            
            # Debug: List all existing rules
            for i, rule in enumerate(rules):
                rule_desc = rule.get("description", "No description")
                rule_var = rule.get("variation", "Unknown")
                print(f"DEBUG: Rule {i}: '{rule_desc}' (variation: {rule_var})")
            
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
            print(f"DEBUG: Target variation determined: {target_variation} ({'enable' if enable else 'disable'})")
            print(f"DEBUG: Enable variation: {enable_variation}, Disable variation: {disable_variation}")
            
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
                            print(f"DEBUG: Found PMCs Enabled Rule at index {i} (description: '{rule.get('description', '')}')")
                    elif "pmcs disabled rule" in rule_description or rule_variation == disable_variation:
                        if disabled_rule_index == -1:  # Only take the first one we find
                            disabled_rule_index = i
                            print(f"DEBUG: Found PMCs Disabled Rule at index {i} (description: '{rule.get('description', '')}')")
                
                # Check if this PMC ID is in any rule
                for clause in clauses:
                    if clause.get("attribute") == "PmcId":
                        clause_values = clause.get("values", [])
                        if pmcid_int in clause_values or str(pmcid_int) in clause_values:
                            current_pmcid_rule_index = i
                            print(f"DEBUG: Found PMC ID {pmcid_int} in rule at index {i} (variation {rule_variation})")
                            break
                
                if current_pmcid_rule_index >= 0:
                    continue  # Keep looking for standard rules even if we found the PMC
            
            # Determine what action to take with the two-rule system
            target_rule_index = enabled_rule_index if enable else disabled_rule_index
            source_rule_index = disabled_rule_index if enable else enabled_rule_index
            
            print(f"DEBUG: Target rule index: {target_rule_index}, Source rule index: {source_rule_index}")
            
            # Check if PMC is already in the correct rule
            if current_pmcid_rule_index == target_rule_index and target_rule_index >= 0:
                print(f"DEBUG: PMC ID {pmcid_int} already in correct rule")
                action_description = f"PMC ID {pmcid_int} already {'enabled' if enable else 'disabled'} - no changes needed"
                success = True
                rule_to_apply = None
                rule_index_to_update = -1
            elif current_pmcid_rule_index == -1 and target_rule_index == -1:
                # No PMC rules exist yet - create the first standard rule
                print(f"DEBUG: No PMC targeting rules exist yet, creating first standard rule")
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
                    print(f"DEBUG: Removing PMC ID {pmcid_int} from rule at index {current_pmcid_rule_index}")
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
                    
                    # SMART RULING: Delete empty rule instead of keeping it
                    if not remaining_pmcs:
                        print(f"DEBUG: SMART RULING - Source rule will be empty, deleting entire rule at index {current_pmcid_rule_index}")
                        # Get the actual rule ID (UUID) from the rule
                        source_rule_id = source_rule.get("_id")
                        # Use JSON Patch to remove the rule by index
                        patches_needed.append({
                            "op": "remove",
                            "path": f"/environments/{actual_env}/rules/{current_pmcid_rule_index}"
                        })
                        print(f"DEBUG: Will remove rule at index: {current_pmcid_rule_index}")
                        rule_deleted = True
                        
                        # Adjust target rule index if it comes after the deleted rule
                        if target_rule_index > current_pmcid_rule_index:
                            adjusted_target_rule_index = target_rule_index - 1
                            print(f"DEBUG: Adjusted target rule index from {target_rule_index} to {adjusted_target_rule_index}")
                    else:
                        print(f"DEBUG: Source rule still has {len(remaining_pmcs)} PMC(s), updating rule")
                        # Get the actual rule ID (UUID) from the rule
                        source_rule_id = source_rule.get("_id")
                        # Use JSON Patch to replace the rule at the specific index
                        patches_needed.append({
                            "op": "replace",
                            "path": f"/environments/{actual_env}/rules/{current_pmcid_rule_index}",
                            "value": source_rule
                        })
                        print(f"DEBUG: Will update rule at index: {current_pmcid_rule_index}")
                
                # Step 2: Add to or create target rule
                if adjusted_target_rule_index >= 0:
                    # Add to existing target rule
                    print(f"DEBUG: Adding PMC ID {pmcid_int} to existing {'enabled' if enable else 'disabled'} rule at index {adjusted_target_rule_index}")
                    target_rule = rules[adjusted_target_rule_index].copy()
                    
                    # Add PMC ID to the target rule
                    for clause in target_rule["clauses"]:
                        if clause.get("attribute") == "PmcId":
                            if pmcid_int not in clause["values"]:
                                clause["values"].append(pmcid_int)
                            break
                    
                    rule_to_apply = target_rule
                    rule_index_to_update = adjusted_target_rule_index
                    
                    if rule_deleted:
                        action_description = f"SMART RULING: Deleted empty rule and moved PMC {pmcid_int} to {'enabled' if enable else 'disabled'} rule"
                    else:
                        action_description = f"Moved PMC {pmcid_int} to {'enabled' if enable else 'disabled'} rule"
                else:
                    # Create new standard rule
                    print(f"DEBUG: Creating new standard {'enabled' if enable else 'disabled'} rule")
                    rule_to_apply = self.create_standard_pmc_rule(pmcid_int, target_variation, enable)
                    rule_index_to_update = -1
                    action_description = f"Created new {'enabled' if enable else 'disabled'} rule with PMC {pmcid_int}"
                
                additional_ops = patches_needed
            
            # Apply the changes via API using JSON Patch operations with user attribution
            if rule_to_apply:
                # Check if we have additional operations (for moving between rules)
                additional_ops = locals().get('additional_ops', None)
                success = self.update_flag_configuration(feature_key, flag_data, environment, rule_index_to_update, rule_to_apply, additional_ops)
                api_responses.append({
                    "operation": "update_flag_config", 
                    "success": success, 
                    "rule_applied": rule_to_apply,
                    "rule_index": rule_index_to_update,
                    "additional_operations": additional_ops
                })
            else:
                success = True  # No changes needed case
                api_responses.append({"operation": "no_changes_needed", "success": True, "message": "PMC ID already in correct state"})
            
            if success:
                print(f"DEBUG: Successfully applied targeting rule changes")
                self.reset_update_fields()
                return True, action_description, api_responses
            else:
                api_responses.append({"operation": "final_result", "success": False, "error": "Failed to apply targeting rule changes"})
                return False, "Failed to apply targeting rule changes", api_responses
                
        except Exception as e:
            print(f"DEBUG: Exception in intelligent targeting: {str(e)}")
            api_responses.append({"operation": "exception", "success": False, "error": str(e)})
            return False, f"Error in intelligent targeting: {str(e)}", api_responses

    def create_standard_pmc_rule(self, pmcid_int, target_variation, enable):
        """Create a standard PMC targeting rule (either enabled or disabled)"""
        rule_type = "enabled" if enable else "disabled"
        description = f"PMCs {rule_type.title()} Rule"
        
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
        
        print(f"DEBUG: Created standard rule: {description} with PMC {pmcid_int}")
        return new_rule

    def get_flag_configuration(self, feature_key):
        """Get current flag configuration from LaunchDarkly"""
        try:
            url = URLBuilder.build_flag_url(PROJECT_KEY, feature_key)
            headers = APIHeaders.get_launchdarkly_headers(LAUNCHDARKLY_API_KEY)
            
            print(f"DEBUG: Fetching flag configuration from: {url}")
            
            response = requests.get(url, headers=headers, timeout=APIConfig.DEFAULT_TIMEOUT)
            
            if response.status_code == 200:
                flag_data = response.json()
                print(f"DEBUG: Successfully retrieved flag configuration")
                return flag_data
            else:
                print(f"DEBUG: Failed to get flag configuration: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"DEBUG: Exception getting flag configuration: {str(e)}")
            return None

    def update_flag_configuration(self, feature_key, flag_data, environment, rule_index_to_update=-1, rule_to_apply=None, additional_operations=None):
        """Update flag configuration in LaunchDarkly using JSON Patch operations with user attribution"""
        from shared.user_session import get_api_comment
        
        try:
            url = URLBuilder.build_flag_url(PROJECT_KEY, feature_key)
            headers = APIHeaders.get_launchdarkly_headers(LAUNCHDARKLY_API_KEY)
            
            actual_env = ENVIRONMENT_MAPPINGS.get(environment, environment)
            
            # Build JSON Patch operations (like the working checkpoint version)
            patch_operations = []
            
            # Ensure flag is turned ON
            patch_operations.append({
                "op": "replace",
                "path": f"/environments/{actual_env}/on",
                "value": True
            })
            
            # Add any additional operations first (like removing from old rules)
            if additional_operations:
                patch_operations.extend(additional_operations)
            
            if rule_index_to_update >= 0 and rule_to_apply:
                # Update existing rule
                print(f"DEBUG: Creating patch to update existing rule at index {rule_index_to_update}")
                patch_operations.append({
                    "op": "replace",
                    "path": f"/environments/{actual_env}/rules/{rule_index_to_update}",
                    "value": rule_to_apply
                })
            elif rule_to_apply:
                # Add new rule
                print(f"DEBUG: Creating patch to add new rule")
                patch_operations.append({
                    "op": "add",
                    "path": f"/environments/{actual_env}/rules/-",
                    "value": rule_to_apply
                })
            
            print(f"DEBUG: Updating flag configuration at: {url}")
            print(f"DEBUG: JSON Patch operations: {json.dumps(patch_operations, indent=2)}")
            
            # Add user attribution comment to the patch
            patch_operations.append({
                "op": "replace", 
                "path": f"/environments/{actual_env}/comment",
                "value": get_api_comment(f"Flag configuration update for {feature_key}")
            })
            
            response = requests.patch(url, headers=headers, json=patch_operations, timeout=APIConfig.DEFAULT_TIMEOUT)
            
            if response.status_code in [200, 204]:
                print(f"DEBUG: Successfully updated flag configuration")
                self.reset_update_fields()
                return True
            else:
                print(f"DEBUG: Failed to update flag configuration: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"DEBUG: Exception updating flag configuration: {str(e)}")
            return False

    def reset_update_fields(self):
        """Reset update form fields"""
        self.update_key_var.set("")
        self.environment_entry.set("DEV")
        self.pmcid_var.set("")
        self.siteid_var.set("")
        self.update_result_label.config(text="")
        self.update_response_box(None)
        self.reset_log()

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

    def reset_log(self):
        """Reset loading text"""
        self.update_loading_var.set("")
        self.loading_frame.pack_forget()

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