"""
Shared Constants
Common constants used across multiple tabs
"""

# UI Constants
UI_TITLE = "Feature Flag Management"
UI_WIDTH = 1200
UI_HEIGHT = 800

# Field Types
FIELD_TYPES = {
    "text": "text",
    "number": "number",
    "email": "email",
    "url": "url"
}

# Validation Rules
VALIDATION_RULES = {
    "required": "This field is required",
    "email": "Please enter a valid email address",
    "url": "Please enter a valid URL",
    "number": "Please enter a valid number"
}

# Error Messages
ERROR_MESSAGES = {
    "api_error": "API request failed",
    "network_error": "Network connection error",
    "validation_error": "Validation error",
    "timeout_error": "Request timed out"
}

# Success Messages
SUCCESS_MESSAGES = {
    "flag_updated": "Feature flag updated successfully",
    "flag_created": "Feature flag created successfully",
    "flag_retrieved": "Feature flag retrieved successfully"
}

# Icons
ICONS = {
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
    "loading": "⏳"
}

# Tab Configurations
TAB_CONFIGS = {
    "get": {
        "title": "Get Feature Flag",
        "icon": "🔍",
        "description": "Retrieve feature flag status"
    },
    "update": {
        "title": "Update Feature Flag",
        "icon": "✏️",
        "description": "Update existing feature flags"
    },
    "create": {
        "title": "Create Feature Flag",
        "icon": "➕",
        "description": "Create new feature flags"
    },
    "view": {
        "title": "Feature Flags List",
        "icon": "📋",
        "description": "View all feature flags"
    },
    "log": {
        "title": "Log Viewer",
        "icon": "📊",
        "description": "View application logs"
    }
}

# Environment Mappings
ENVIRONMENT_MAPPINGS = {
    "DEV": "onesite-general-dev",
    "OCRT": "onesite-general-ocrt",
    "SAT": "onesite-general-sat",
    "PROD": "onesite-general-prod-us"
}

# Environment Display Names
ENVIRONMENT_DISPLAY_NAMES = {
    "DEV": "Development",
    "OCRT": "OCR Testing",
    "SAT": "Saturation",
    "PROD": "Production"
}

# Environment Options for UI
ENVIRONMENT_OPTIONS = ["DEV", "OCRT", "SAT", "PROD"]

# Environment Options for Update Operations (excluding PROD for safety)
UPDATE_ENVIRONMENT_OPTIONS = ["DEV", "OCRT", "SAT"]

# Environment Options for Read Operations (including PROD)
READ_ENVIRONMENT_OPTIONS = ["DEV", "OCRT", "SAT", "PROD"] 