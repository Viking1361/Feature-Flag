"""
API Endpoints Configuration
Centralized configuration for all API endpoints and service URLs
"""

# Base URLs
LAUNCHDARKLY_BASE_URL = "https://app.launchdarkly.com/api/v2"

# Feature Flag Endpoints
class FeatureFlagEndpoints:
    """Feature flag related API endpoints"""
    
    # Get all flags
    GET_ALL_FLAGS = f"{LAUNCHDARKLY_BASE_URL}/flags"
    
    # Get specific flag
    GET_FLAG = f"{LAUNCHDARKLY_BASE_URL}/flags"
    
    # Create new flag
    CREATE_FLAG = f"{LAUNCHDARKLY_BASE_URL}/flags"
    
    # Update flag
    UPDATE_FLAG = f"{LAUNCHDARKLY_BASE_URL}/flags"
    
    # Delete flag
    DELETE_FLAG = f"{LAUNCHDARKLY_BASE_URL}/flags"

# Legacy API Endpoints (for backward compatibility)
class LegacyEndpoints:
    """Legacy API endpoints for older functionality"""
    
    # Legacy feature flag status endpoint
    LEGACY_FLAG_STATUS = "https://api.example.com/legacy/flag-status"
    
    # Legacy PMC/Site context endpoint
    LEGACY_CONTEXT = "https://api.example.com/legacy/context"

# Authentication Endpoints
class AuthEndpoints:
    """Authentication related endpoints"""
    
    # Token validation
    VALIDATE_TOKEN = f"{LAUNCHDARKLY_BASE_URL}/auth/token"
    
    # User info
    USER_INFO = f"{LAUNCHDARKLY_BASE_URL}/auth/user"

# Project Endpoints
class ProjectEndpoints:
    """Project related endpoints"""
    
    # Get project info
    GET_PROJECT = f"{LAUNCHDARKLY_BASE_URL}/projects"
    
    # List environments
    GET_ENVIRONMENTS = f"{LAUNCHDARKLY_BASE_URL}/environments"

# Environment Endpoints
class EnvironmentEndpoints:
    """Environment related endpoints"""
    
    # Get environment info
    GET_ENVIRONMENT = f"{LAUNCHDARKLY_BASE_URL}/environments"
    
    # Update environment
    UPDATE_ENVIRONMENT = f"{LAUNCHDARKLY_BASE_URL}/environments"

# Custom Service URLs (for specific business logic)
class CustomServiceURLs:
    """Custom service URLs for specific business requirements"""
    
    # PMC/Site context service
    PMC_SITE_CONTEXT = "https://api.example.com/pmc-site-context"
    
    # Feature flag analytics
    FLAG_ANALYTICS = "https://api.example.com/analytics/flags"
    
    # User management
    USER_MANAGEMENT = "https://api.example.com/users"
    
    # Audit logs
    AUDIT_LOGS = "https://api.example.com/audit"

# API Headers Configuration
class APIHeaders:
    """Standard API headers configuration"""
    
    @staticmethod
    def get_launchdarkly_headers(api_key):
        """Get LaunchDarkly API headers"""
        return {
            "Authorization": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    @staticmethod
    def get_legacy_headers(token):
        """Get legacy API headers"""
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    @staticmethod
    def get_custom_headers(api_key, additional_headers=None):
        """Get custom API headers"""
        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if additional_headers:
            headers.update(additional_headers)
        
        return headers

# URL Builder Functions
class URLBuilder:
    """Helper functions for building API URLs"""
    
    @staticmethod
    def build_flag_url(project_key, flag_key=None):
        """Build feature flag URL"""
        base_url = f"{LAUNCHDARKLY_BASE_URL}/flags/{project_key}"
        if flag_key:
            return f"{base_url}/{flag_key}"
        return base_url
    
    @staticmethod
    def build_environment_url(project_key, environment_key=None):
        """Build environment URL"""
        base_url = f"{LAUNCHDARKLY_BASE_URL}/environments/{project_key}"
        if environment_key:
            return f"{base_url}/{environment_key}"
        return base_url
    
    @staticmethod
    def build_project_url(project_key):
        """Build project URL"""
        return f"{LAUNCHDARKLY_BASE_URL}/projects/{project_key}"
    
    @staticmethod
    def build_legacy_url(endpoint, params=None):
        """Build legacy API URL with parameters"""
        url = endpoint
        if params:
            param_strings = [f"{k}={v}" for k, v in params.items()]
            url += "?" + "&".join(param_strings)
        return url

# API Configuration
class APIConfig:
    """API configuration settings"""
    
    # Timeout settings
    DEFAULT_TIMEOUT = 30  # seconds
    SHORT_TIMEOUT = 10    # seconds
    LONG_TIMEOUT = 60     # seconds
    
    # Retry settings
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    
    # Rate limiting
    REQUESTS_PER_MINUTE = 60
    REQUESTS_PER_HOUR = 1000
    
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100

# Environment-specific URLs
class EnvironmentURLs:
    """Environment-specific URL configurations"""
    
    # Development environment
    DEV = {
        "launchdarkly": "https://app.launchdarkly.com/api/v2",
        "legacy": "https://dev-api.example.com",
        "custom": "https://dev-custom.example.com"
    }
    
    # Staging environment
    STAGING = {
        "launchdarkly": "https://app.launchdarkly.com/api/v2",
        "legacy": "https://staging-api.example.com",
        "custom": "https://staging-custom.example.com"
    }
    
    # Production environment
    PRODUCTION = {
        "launchdarkly": "https://app.launchdarkly.com/api/v2",
        "legacy": "https://api.example.com",
        "custom": "https://custom.example.com"
    }

# URL Validation Patterns
class URLPatterns:
    """URL validation patterns"""
    
    # LaunchDarkly URL pattern
    LAUNCHDARKLY_PATTERN = r"^https://app\.launchdarkly\.com/api/v2/.*"
    
    # Legacy API pattern
    LEGACY_PATTERN = r"^https://.*\.example\.com/.*"
    
    # Custom service pattern
    CUSTOM_PATTERN = r"^https://.*\.example\.com/.*"
    
    # General HTTPS pattern
    HTTPS_PATTERN = r"^https://.*"

# Error Messages for API Endpoints
class APIErrorMessages:
    """Error messages specific to API endpoints"""
    
    INVALID_URL = "Invalid API endpoint URL"
    CONNECTION_FAILED = "Failed to connect to API endpoint"
    TIMEOUT_ERROR = "API request timed out"
    AUTHENTICATION_FAILED = "Authentication failed for API endpoint"
    RATE_LIMIT_EXCEEDED = "Rate limit exceeded for API endpoint"
    INVALID_RESPONSE = "Invalid response from API endpoint"
    ENDPOINT_NOT_FOUND = "API endpoint not found"

# Success Messages for API Endpoints
class APISuccessMessages:
    """Success messages specific to API endpoints"""
    
    CONNECTION_SUCCESS = "Successfully connected to API endpoint"
    DATA_RETRIEVED = "Data retrieved successfully from API"
    DATA_UPDATED = "Data updated successfully via API"
    DATA_CREATED = "Data created successfully via API"
    DATA_DELETED = "Data deleted successfully via API" 