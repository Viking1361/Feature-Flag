# Role-Based Access Control (RBAC)

## Overview

The Feature Flag application now implements **Role-Based Access Control** with two distinct access levels:

### 👤 **User Access** (Limited)
- **Authentication**: Windows credentials (`vanasuri` + Windows password)
- **Available Tabs**: Get, Update, Create, Log
- **Permissions**: Basic flag operations
- **Use Case**: Day-to-day flag management by developers

### 👑 **Admin Access** (Full)
- **Authentication**: Admin credentials (`ia` / `ia1`)
- **Available Tabs**: Get, Update, Create, **View**, Log
- **Permissions**: All operations + advanced features
- **Use Case**: Administrative oversight and bulk operations

## Login Options

### 🔒 **User Login (Windows Authentication)**
```
Username: vanasuri (auto-detected)
Password: [Your Windows password]
Result: User role with basic access
```

### 👑 **Admin Login (Admin Credentials)**
```
Username: ia
Password: ia1
Result: Admin role with full access including View tab
```

## Feature Comparison

| Feature | User Access | Admin Access |
|---------|-------------|--------------|
| Get Flag Status | ✅ | ✅ |
| Update Flags | ✅ | ✅ |
| Create Flags | ✅ | ✅ |
| View All Flags | ❌ | ✅ |
| Export Functions | ❌ | ✅ |
| Orphaned Flags | ❌ | ✅ |
| Bulk Operations | ❌ | ✅ |
| Log Viewer | ✅ | ✅ |

## Security Benefits

### 🛡️ **Enhanced Security**
- **Segregation of Duties**: Regular users can't access sensitive View tab
- **Windows Integration**: Uses existing corporate credentials
- **Audit Trails**: All operations attributed to actual user
- **Admin Controls**: Sensitive features restricted to admin users

### 🔐 **Authentication Methods**
- **Windows Authentication**: Leverages OS-level security
- **Admin Credentials**: Separate admin access control
- **Session Management**: Role-aware session tracking
- **Fallback Support**: Development mode for testing

## UI Indicators

### **Window Title**
- User: `Feature Flag v3.0 - vanasuri (User)`
- Admin: `Feature Flag v3.0 - admin (Admin)`

### **Session Display**
- User: `👤 vanasuri (User) | ⏱️ 01:23`
- Admin: `👑 admin (Admin) | ⏱️ 01:23`

### **Tab Labels**
- Admin tabs show `🔒` prefix and `(Admin)` suffix
- Restricted tabs are hidden from non-admin users

## Implementation Details

### **Permission System**
```python
admin_permissions = ["view_all_flags", "export_flags", "manage_settings"]
user_permissions = ["get_flag", "update_flag", "create_flag"]
```

### **Role Assignment**
- `ia` / `ia1` credentials → `admin` role
- Windows authentication → `user` role
- Automatic tab filtering based on permissions

### **API Attribution**
All operations include user context:
```json
{
  "comment": "Flag enabled by vanasuri via Feature Flag App at 2024-01-15 14:30:25"
}
```

## Migration Impact

### **Existing Users**
- No change to existing functionality
- Enhanced security with proper attribution
- Clear distinction between user and admin functions

### **New Security Model**
- View tab now restricted to admins only
- Windows authentication for regular users
- Admin credentials for privileged access

## Best Practices

### 🎯 **For Users**
- Use Windows credentials for daily flag operations
- Request admin access only when needed
- Understand permission limitations

### 🎯 **For Admins**
- Use admin credentials (`ia`/`ia1`) for bulk operations
- Monitor View tab for flag hygiene
- Utilize export features for compliance reporting

This RBAC implementation provides enterprise-grade security while maintaining usability for different user types.
