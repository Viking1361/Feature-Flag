HELP_CONTENT = {
    "get.flag_key": {
        "title": "Feature Flag Key",
        "about": "The unique key of a LaunchDarkly feature flag.",
        "examples": [
            "checkout-new-ui",
            "pricing-v2",
        ],
    },
    "get.environment": {
        "title": "Environment",
        "about": "The LaunchDarkly environment to read from.",
        "examples": [
            "DEV",
            "OCRT",
            "SAT",
            "PROD",
        ],
    },
    "get.pmc_id": {
        "title": "PMC ID",
        "about": "Optional: PMC identifier used in some targeting rules.",
        "examples": [
            "4341841",
        ],
    },
    "get.site_id": {
        "title": "Site ID",
        "about": "Optional: Site ID used in some targeting rules.",
        "examples": [
            "4341842",
        ],
    },
    "get.get_button": {
        "title": "Get Flag Status",
        "about": "Fetches flag details and status from LaunchDarkly for the selected environment.",
        "examples": [
            "Enter flag key, choose environment, click Get Flag Status.",
        ],
    },
    "get.reset_button": {
        "title": "Reset",
        "about": "Clears inputs and results.",
        "examples": [
            "Click Reset to clear all fields.",
        ],
    },
    # Update tab
    "update.flag_key": {
        "title": "Feature Flag Key",
        "about": "Key of the flag you want to update.",
        "examples": ["checkout-new-ui"],
    },
    "update.environment": {
        "title": "Environment",
        "about": "Target environment to apply the change.",
        "examples": ["DEV", "OCRT", "SAT"],
    },
    "update.pmc_id": {
        "title": "PMC ID",
        "about": "Optional PMC identifier for targeted updates.",
        "examples": ["4341841"],
    },
    "update.site_id": {
        "title": "Site ID",
        "about": "Optional Site identifier for targeted updates.",
        "examples": ["4341842"],
    },
    "update.turn_on": {
        "title": "Turn ON",
        "about": "Enable the flag globally or for targeted PMC/Site if provided.",
        "examples": ["Click to set the flag ON"],
    },
    "update.turn_off": {
        "title": "Turn OFF",
        "about": "Disable the flag globally or for targeted PMC/Site if provided.",
        "examples": ["Click to set the flag OFF"],
    },
    "update.apply_default": {
        "title": "Apply Default Rule",
        "about": "Set the fallthrough (default) variation without toggling ON/OFF.",
        "examples": ["Choose True/False and click Apply"],
    },
    "update.reset": {
        "title": "Reset",
        "about": "Clears update inputs and results.",
        "examples": ["Click Reset to clear all fields."],
    },
    # Create tab
    "create.flag_key": {
        "title": "Flag Key",
        "about": "Unique key for the new flag.",
        "examples": ["new-experiment"],
    },
    "create.flag_name": {
        "title": "Flag Name",
        "about": "Human-friendly name for the flag.",
        "examples": ["New Experiment"]
    },
    "create.description": {
        "title": "Description",
        "about": "Optional description for context.",
        "examples": ["Controls rollout of new experiment"]
    },
    "create.tags": {
        "title": "Tags",
        "about": "Comma-separated tags to categorize the flag.",
        "examples": ["frontend, experiment"],
    },
    "create.create_button": {
        "title": "Create Flag",
        "about": "Creates the flag in LaunchDarkly.",
        "examples": ["Provide key and name, then click Create"],
    },
    "create.reset": {
        "title": "Reset Form",
        "about": "Clears the creation form.",
        "examples": ["Click Reset Form to clear all fields"],
    },
    # History tab
    "history.flag_key": {
        "title": "Flag Key",
        "about": "Key of the flag to filter audit entries.",
        "examples": ["checkout-new-ui"],
    },
    "history.environment": {
        "title": "Environment",
        "about": "Environment to filter audit entries.",
        "examples": ["DEV", "OCRT", "SAT", "PROD"],
    },
    "history.refresh": {
        "title": "Refresh",
        "about": "Fetches audit entries for the selected flag and environment.",
        "examples": ["Enter key, select environment, click Refresh"],
    },
    "history.clear": {
        "title": "Clear",
        "about": "Clears filters and results.",
        "examples": ["Click Clear to reset inputs"],
    },
    # Notifications tab
    "notifications.filters.key": {
        "title": "Filter by Key",
        "about": "Filter history/items by feature key substring.",
        "examples": ["checkout"]
    },
    "notifications.filters.env": {
        "title": "Filter by Environment",
        "about": "Limit entries to a specific environment.",
        "examples": ["DEV", "PROD"]
    },
    "notifications.filters.transport": {
        "title": "Transport",
        "about": "Filter by transport/mode (dry_run, graph).",
        "examples": ["dry_run"]
    },
    "notifications.filters.type": {
        "title": "Type",
        "about": "Filter by entry type.",
        "examples": ["update_flag", "create_flag"]
    },
    "notifications.filters.ok_only": {
        "title": "OK Only",
        "about": "Show only successful entries.",
        "examples": ["Enable to hide failed entries"]
    },
    "notifications.refresh": {
        "title": "Refresh",
        "about": "Load entries from the audit file using current filters.",
        "examples": ["Click Refresh after adjusting filters"],
    },
    "notifications.clear": {
        "title": "Clear Filters",
        "about": "Reset all filters to defaults.",
        "examples": ["Click Clear Filters"],
    },
    "notifications.copy_html": {
        "title": "Copy HTML",
        "about": "Copy HTML payload for a notification entry.",
        "examples": ["Select an entry, click Copy HTML"],
    },
    "notifications.copy_json": {
        "title": "Copy JSON",
        "about": "Copy JSON payload for a selected entry.",
        "examples": ["Select an entry, click Copy JSON"],
    },
    "notifications.copy_flag_name": {
        "title": "Copy Flag Name",
        "about": "Copy the feature key of the selected entry.",
        "examples": ["Select, then click Copy Flag Name"],
    },
    # Log tab
    "log.refresh": {
        "title": "Refresh Logs",
        "about": "Reload and filter the log file.",
        "examples": ["Click Refresh Logs"],
    },
    "log.clear": {
        "title": "Clear Logs",
        "about": "Clear the current log file contents.",
        "examples": ["Click Clear Logs"],
    },
    "log.export": {
        "title": "Export Logs",
        "about": "Export logs to a chosen file path.",
        "examples": ["Export to desktop as logs.txt"],
    },
    "log.filter": {
        "title": "Filter",
        "about": "Select a filter preset to limit visible log lines.",
        "examples": ["Errors Only"],
    },
    "log.search": {
        "title": "Search",
        "about": "Type text to filter displayed log lines.",
        "examples": ["timeout", "ERROR"],
    },
}
