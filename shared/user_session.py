"""
User Session Management
Handles user authentication state and context for API operations
"""

import threading
from datetime import datetime
from typing import Optional, Dict, Any

class UserSession:
    """Singleton class to manage user session across the application"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(UserSession, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not getattr(self, '_initialized', False):
            self._username = None
            self._login_time = None
            self._session_data = {}
            self._role = "user"
            self._initialized = True
    
    def login(self, username: str, additional_data: Dict[str, Any] = None, role: str = "user"):
        """Set user login information with role-based access"""
        self._username = username
        self._login_time = datetime.now()
        self._session_data = additional_data or {}
        self._role = role
        print(f"🔒 User session started: {username} ({role}) at {self._login_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def logout(self):
        """Clear user session"""
        if self._username:
            print(f"🔓 User session ended: {self._username}")
        self._username = None
        self._login_time = None
        self._session_data = {}
        self._role = "user"
    
    @property
    def username(self) -> Optional[str]:
        """Get current logged-in username"""
        return self._username
    
    @property
    def is_logged_in(self) -> bool:
        """Check if user is logged in"""
        return self._username is not None
    
    @property
    def login_time(self) -> Optional[datetime]:
        """Get login timestamp"""
        return self._login_time
    
    @property
    def session_duration(self) -> Optional[str]:
        """Get formatted session duration"""
        if self._login_time:
            duration = datetime.now() - self._login_time
            hours, remainder = divmod(int(duration.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return None
    
    @property
    def role(self) -> str:
        """Get current user role"""
        return getattr(self, '_role', 'user')
    
    @property
    def is_admin(self) -> bool:
        """Check if current user is admin"""
        return self.role == "admin"
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        admin_permissions = ["view_all_flags", "export_flags", "manage_settings"]
        user_permissions = ["get_flag", "update_flag", "create_flag"]
        
        if self.is_admin:
            return permission in admin_permissions + user_permissions
        else:
            return permission in user_permissions
    
    def get_session_data(self, key: str, default=None):
        """Get session data by key"""
        return self._session_data.get(key, default)
    
    def set_session_data(self, key: str, value: Any):
        """Set session data by key"""
        self._session_data[key] = value
    
    def get_api_comment(self, operation: str = "operation") -> str:
        """Generate API comment with user attribution"""
        if self._username:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return f"{operation} by {self._username} via Feature Flag App at {timestamp}"
        else:
            return f"{operation} via Feature Flag App"
    
    def get_user_context(self) -> Dict[str, Any]:
        """Get user context for API operations"""
        return {
            "username": self._username,
            "login_time": self._login_time.isoformat() if self._login_time else None,
            "session_duration": self.session_duration,
            "timestamp": datetime.now().isoformat()
        }

# Global instance
user_session = UserSession()

def get_current_user() -> str:
    """Helper function to get current username"""
    return user_session.username or "anonymous"

def get_api_comment(operation: str = "Flag operation") -> str:
    """Helper function to get API comment with user attribution"""
    return user_session.get_api_comment(operation)

def is_user_logged_in() -> bool:
    """Helper function to check if user is logged in"""
    return user_session.is_logged_in
