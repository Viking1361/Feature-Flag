# Settings System Guide

## How to Save Your View Options

Your Feature Flag app now has a persistent settings system that saves your preferences between sessions.

### 🎨 View Options Dialog

1. **Open Settings**: Click the "👀 View Options" button in the View Tab
2. **Adjust Settings**:
   - **📏 Row Height**: 20-100px slider with smart font scaling (default: 30px)
     - 20px → 8pt fonts (compact)
     - 30px → 10pt fonts (balanced) 
     - 50px → 12pt fonts (comfortable)
     - 100px → 16pt fonts (large)
   - **🎨 Color Theme**: Choose from 5 themes (default: Enhanced)
   - **🔄 Auto-refresh**: Set interval or disable (default: 30s)

3. **Save Settings**: Click "✅ Apply Changes" to save permanently
4. **Reset**: Click "🔄 Reset Defaults" to restore original settings

### 💾 Settings File

- **Location**: `app_settings.json` in your app directory
- **Format**: JSON with sections for different preferences
- **Automatic**: Settings are loaded when you start the app

### 📋 Available Settings

```json
{
  "view_options": {
    "row_height": 30,
    "color_theme": "Enhanced (Current)",
    "auto_refresh_enabled": true,
    "auto_refresh_interval": 30
  },
  "window": {
    "last_tab": "view",
    "window_size": "1200x800"
  },
  "filters": {
    "default_environment": "All",
    "default_status": "All", 
    "default_health": "All"
  }
}
```

### 🔧 Features

- **Smart Font Scaling**: Fonts automatically adjust with row height (8pt-16pt range)
- **Compact to Large Views**: Support for 20px (ultra-compact) to 100px (extra large) rows  
- **Persistent**: Settings survive app restarts
- **Automatic Loading**: Your preferences are applied on startup
- **Visual Feedback**: Toast notifications confirm saves
- **Error Handling**: Falls back to defaults if settings file is corrupted
- **Easy Reset**: One-click restore to defaults

### 🐛 Troubleshooting

- **Settings not saving**: Check file permissions in app directory
- **Settings not loading**: Delete `app_settings.json` to reset
- **Unexpected behavior**: Use "Reset Defaults" button

### 🆕 What's New

- Row height changes are immediately visible
- Auto-refresh settings control background updates
- Theme settings prepared for future visual themes
- All settings persist between app sessions

Your customizations are now saved automatically! 🎉
