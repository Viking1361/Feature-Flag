# Security Features

## Windows Authentication

The application now uses **Windows Authentication** for enhanced security:

### How It Works:
1. **System Username Detection** - Automatically detects your Windows username (`vanasuri`)
2. **Windows Password Verification** - Uses Windows LogonUser API to verify your actual system password
3. **Domain Support** - Supports both local accounts and domain accounts
4. **Fallback Mode** - Development fallback using `ia`/`ia1` for testing

### Security Benefits:
- ✅ **No Static Passwords** - No hardcoded passwords in the application
- ✅ **Real Authentication** - Uses your actual Windows credentials
- ✅ **Domain Integration** - Works with corporate Active Directory
- ✅ **Audit Trail** - All API operations are attributed to your Windows username
- ✅ **Session Management** - Proper login/logout with session tracking

### Login Methods:

#### Primary (Windows Auth):
- **Username**: `vanasuri` (auto-detected)
- **Password**: Your Windows password
- **Security**: Verified against Windows authentication

#### Fallback (Development):
- **Username**: `ia`
- **Password**: `ia1`
- **Usage**: Development/testing only

### Technical Implementation:
- Uses Windows `LogonUser` API via `ctypes`
- Supports interactive logon type
- Handles both local machine and domain authentication
- Graceful fallback for non-Windows systems

### API Attribution:
All LaunchDarkly API operations now include user attribution:
```json
{
  "comment": "Flag enabled by vanasuri via Feature Flag App at 2024-01-15 14:30:25"
}
```

This provides full audit trails for compliance and debugging.
