# 🚀 Feature Flag Management System

A professional, modular Python application for managing LaunchDarkly feature flags with a modern GUI built using `ttkbootstrap`.

## 📁 Project Structure

```
FeatureFlag/
├── main.py                    # 🎯 Main application entry point
├── shared/config_loader.py    # ⚙️ Centralized configuration loader (env vars, optional config.json)
├── config.example.json        # 🧩 Example JSON config (copy to config.json and fill in values)
├── app_logic.py              # 🔧 Business logic functions
├── ui/                       # 🎨 User Interface Package
│   ├── __init__.py
│   ├── main_app.py           # 🏠 Main application class
│   ├── login_window.py       # 🔐 Login window
│   └── tabs/                 # 📑 Tab Modules
│       ├── __init__.py
│       ├── get_tab.py        # 📋 Get Feature Flag tab
│       ├── update_tab.py     # ⚙️ Update Feature Flag tab
│       ├── create_tab.py     # ➕ Create Feature Flag tab
│       ├── enhanced_view_tab.py  # 📊 Feature Flags List (Enhanced View) tab
│       └── log_tab.py        # 📝 Log Viewer tab
├── api_config/               # ⚙️ API Configuration Package
│   ├── __init__.py
│   └── api_endpoints.py      # 🌐 API endpoints and URLs
├── shared/                   # 🔄 Shared Components Package
│   ├── __init__.py
│   ├── ui_components.py      # 🎨 Reusable UI components
│   ├── utils.py              # 🛠️ Shared utility functions
│   └── constants.py          # 📋 Shared constants
├── utils/                    # 🛠️ Utility Package
│   ├── __init__.py
│   ├── theme_manager.py      # 🎨 Theme management
│   └── history_manager.py    # 📚 History management
└── constants/                # 📋 Constants Package
    ├── __init__.py
    └── themes.py             # 🎨 Theme configurations
```

## ✨ Features

### 🎨 **Modern UI Design**
- **Vertical Tab Navigation**: Professional sidebar navigation
- **Theme Support**: Light and Dark themes with smooth transitions
- **Card-based Layout**: Modern card design for better organization
- **Responsive Design**: Adapts to different screen sizes

### 📋 **Feature Flag Operations**
- **Get Feature Flag**: Retrieve flag status with PMC/Site context
- **Update Feature Flag**: Toggle flags on/off across environments
- **Create Feature Flag**: Create new flags with full configuration
- **View Flags List**: Browse all flags with search and pagination
- **Log Viewer**: Monitor application logs with export functionality

### 🔧 **Advanced Features**
- **API Integration**: Full LaunchDarkly API support
- **History Management**: Autocomplete for frequently used values
- **Error Handling**: Comprehensive error handling and user feedback
- **Threading**: Background operations for better UX
- **Logging**: Detailed application logging

## 🚀 Getting Started

### Prerequisites
```bash
pip install ttkbootstrap requests
```

### Configuration
You can configure credentials via environment variables or an optional `config.json` file.

- Environment variables (recommended):
  - `LAUNCHDARKLY_API_KEY`
  - `PROJECT_KEY`
  - `LOG_FILE` (optional, default: `feature_flag.log`)
  - `HISTORY_FILE` (optional, default: `autocomplete_history.json`)
  - `GITHUB_TOKEN` (optional, only needed if your GitHub repo is private for updates)

- Optional `config.json` (placed next to the EXE, current working directory, or project root):
  ```json
  {
    "LAUNCHDARKLY_API_KEY": "your-api-key",
    "PROJECT_KEY": "your-project-key",
    "LOG_FILE": "feature_flag.log",
    "HISTORY_FILE": "autocomplete_history.json",
    "GITHUB_TOKEN": "your-github-token-if-using-private-releases"
  }
  ```

Configuration loading is centralized in `shared/config_loader.py` with the following precedence:
1) Environment variables
2) Optional `config.py` if present (not required)
3) `config.json` found next to the EXE, in the CWD, or project root
4) Sensible defaults

### Running the Application
```bash
python main.py
```

## 🎯 Module Overview

### **Main Application (`main.py`)**
- Clean entry point for the modular application
- Initializes the login window

### **UI Package (`ui/`)**
- **`main_app.py`**: Main application class that orchestrates all components
- **`login_window.py`**: Authentication interface
- **`tabs/`**: Individual tab modules for each functionality

### **Utils Package (`utils/`)**
- **`theme_manager.py`**: Handles theme switching and persistence
- **`history_manager.py`**: Manages autocomplete history

### **Constants Package (`constants/`)**
- **`themes.py`**: Theme configurations and color palettes

### **API Config Package (`api_config/`)**
- **`api_endpoints.py`**: Centralized API endpoints, URLs, and service configurations

### **Shared Package (`shared/`)**
- **`ui_components.py`**: Reusable UI components (CardFrame, FormField, ActionButtons, etc.)
- **`utils.py`**: Shared utility functions (validation, file operations, API helpers)
- **`constants.py`**: Shared constants (UI constants, validation rules, messages)

## 🔧 Tab Modules

### **Get Tab (`get_tab.py`)**
- Retrieve feature flag status
- Support for both legacy and new API endpoints
- PMC/Site context integration
- Real-time validation

### **Update Tab (`update_tab.py`)**
- Toggle feature flags on/off
- Environment selection (DEV, OCRT, SAT)
- Real-time status updates
- Error handling and user feedback

### **Create Tab (`create_tab.py`)**
- Create new feature flags
- Full configuration options
- Environment and default value settings
- API integration with LaunchDarkly

### **View Tab (`enhanced_view_tab.py`)**
- Browse all feature flags
- Search and filtering capabilities
- Pagination for large datasets
- Real-time data fetching

### **Log Tab (`log_tab.py`)**
- View application logs
- Export functionality
- Clear logs option
- Real-time log monitoring

## 🎨 Theme System

### **Light Theme**
- Clean, professional appearance
- High contrast for readability
- Suitable for daytime use

### **Dark Theme**
- Modern dark interface
- Reduced eye strain
- Professional dark aesthetics

## 🔧 Configuration

### **API Configuration**
```python
# config.json (optional)
{
  "LAUNCHDARKLY_API_KEY": "your-api-key",
  "PROJECT_KEY": "your-project-key"
}
```

### **Theme Configuration**
```python
# constants/themes.py
THEMES = {
    "light": {
        "name": "Light",
        "theme": "flatly",
        "colors": { ... }
    },
    "dark": {
        "name": "Dark", 
        "theme": "darkly",
        "colors": { ... }
    }
}
```

## 🛠️ Development

### **Adding New Tabs**
1. Create a new tab module in `ui/tabs/`
2. Inherit from base tab structure
3. Add to `main_app.py` tab instances
4. Update tab configuration

### **Adding New Themes**
1. Add theme configuration to `constants/themes.py`
2. Update theme selector in `main_app.py`
3. Test theme switching functionality

### **Adding New Features**
1. Create utility functions in `utils/`
2. Update relevant tab modules
3. Add error handling and logging
4. Test thoroughly

## 📊 Benefits of Modular Structure

### **🔧 Maintainability**
- **Separation of Concerns**: Each module has a specific responsibility
- **Easy Debugging**: Issues are isolated to specific modules
- **Clean Code**: Smaller, focused files are easier to understand

### **🔄 Code Reusability**
- **Shared Components**: Common UI components used across tabs
- **DRY Principle**: No code duplication between modules
- **Consistent Design**: Unified look and feel across all tabs
- **Easy Updates**: Change once, affects everywhere

### **🚀 Scalability**
- **Parallel Development**: Multiple developers can work on different modules
- **Easy Extension**: New features can be added without affecting existing code
- **Reusable Components**: Common functionality can be shared

### **🎯 Professional Standards**
- **Industry Best Practices**: Follows Python package conventions
- **Documentation**: Each module is self-documenting
- **Testing**: Each module can be tested independently

## 🔍 Usage Examples

### **Getting a Feature Flag**
1. Navigate to "Get Feature Flag" tab
2. Enter URL and feature flag key
3. Add PMC ID and Site ID (optional)
4. Click "Submit Query"
5. View results in the response area

### **Updating a Feature Flag**
1. Navigate to "Update Feature Flag" tab
2. Enter the feature flag key
3. Select environment (DEV, OCRT, SAT)
4. Click "Turn ON" or "Turn OFF"
5. Monitor status updates

### **Creating a New Feature Flag**
1. Navigate to "Create Feature Flag" tab
2. Fill in basic information (key, name, description)
3. Configure environment and default value
4. Click "Create Flag"
5. Monitor creation status

### **Browsing Feature Flags**
1. Navigate to "Feature Flags List" tab
2. Use search to filter flags
3. Navigate through pages
4. Click "Refresh" to update data

## 🐛 Troubleshooting

### **Common Issues**
- **API Connection**: Check your LaunchDarkly API key
- **Theme Issues**: Verify theme configuration in `constants/themes.py`
- **Import Errors**: Ensure all modules are in the correct directories

### **Logging**
- Check `feature_flag.log` for detailed error information
- Use the Log Viewer tab to monitor application activity

## 📝 License

 2024 Feature Flag Management System

## 🤝 Contributing

1. Follow the modular structure
2. Add appropriate error handling
3. Update documentation
4. Test thoroughly before submitting

---

**🎉 Enjoy using your modular Feature Flag Management System!** 

# Feature Flag Management System

A comprehensive desktop application for managing LaunchDarkly feature flags with advanced targeting capabilities and automatic updates.

## 🚀 Features

- **Feature Flag Management**: Create, update, and view LaunchDarkly feature flags
- **PMC-based Targeting**: Advanced targeting rules with PMC ID support
- **Real-time Data**: Auto-refresh functionality with caching
- **User Authentication**: Role-based access control (Admin/User)
- **Export/Import**: CSV export and data management capabilities
- **Auto-Updates**: Automatic version checking and seamless updates
- **Modern UI**: Clean, responsive interface with theme support

## 📋 Requirements

- Python 3.12+
- LaunchDarkly API access
- Windows OS (for executable builds)

## 🛠️ Installation

### For Development
```bash
git clone https://github.com/Viking1361/Feature-Flag.git
cd Feature-Flag
pip install -r requirements.txt
python main.py
```

### For End Users
Download the latest executable from [Releases](https://github.com/Viking1361/Feature-Flag/releases)

## 🔧 Configuration

1. **Update GitHub Repository URLs** in `version.py`:
   ```python
   GITHUB_OWNER = "your-username"  # Your GitHub username
   GITHUB_REPO = "feature-flag-manager"  # Your repository name
   ```

2. **Configure LaunchDarkly credentials** via environment variables or `config.json`:
   - Environment variables:
     - `LAUNCHDARKLY_API_KEY`, `PROJECT_KEY`
   - Or create `config.json` (copy `config.example.json` and fill values):
     ```json
     {
       "LAUNCHDARKLY_API_KEY": "your-api-key",
       "PROJECT_KEY": "your-project-key"
     }
     ```

## 🚀 GitHub Integration Setup

### Step 1: Create GitHub Repository
1. Create a new repository on GitHub
2. Clone this project to your repository
3. Update the URLs in `version.py`

### Step 2: Enable GitHub Actions
The project includes an automated Windows build workflow (`.github/workflows/release.yml`):
- **Automatic builds** on version tags (v1.0.0, v1.0.1, etc.)
- **Executable creation** using PyInstaller
- **Release publishing** with auto-generated release notes

### Step 3: Create Your First Release
```bash
# Update version in version.py
# Commit your changes
git add .
git commit -m "Release v1.0.0"
git tag v1.0.0
git push origin main --tags
```

The GitHub Action will automatically:
- Build the Windows executable
- Create a GitHub release
- Upload the EXE file
- Generate release notes

## 🔄 Auto-Update System

The application includes a sophisticated auto-update system:

### For Users
- **Automatic checks** on startup (every 24 hours)
- **Manual checks** via Help → Check for Updates
- **Smart notifications** with release notes
- **One-click installation** with progress tracking
- **Version control** (skip versions, remind later)

### For Developers
- **GitHub Releases integration** for version distribution
- **Semantic versioning** support (1.0.0 → 1.0.1)
- **Background downloads** with progress tracking
- **Seamless installation** process

### Private GitHub Releases
If your repository is private, the updater needs a token to check and download releases:

- Set `GITHUB_TOKEN` via environment variable or include it in `config.json` (do not commit this file):
  - PowerShell (current session):
    ```powershell
    $env:GITHUB_TOKEN = "<your-token-with-repo-read>"
    ```
  - Or `config.json`:
    ```json
    { "GITHUB_TOKEN": "<your-token-with-repo-read>" }
    ```
- Token scopes:
  - Classic token: `repo` scope
  - Fine-grained: grant read access to the target repository (including Releases/assets)

The app will add `Authorization: token <GITHUB_TOKEN>` to GitHub API calls and use the asset API URL with `Accept: application/octet-stream` for downloads.

## 📁 Project Structure

```
feature-flag-manager/
├── ui/                     # User interface modules
│   ├── tabs/              # Tab implementations
│   ├── login_window.py    # Authentication
│   └── main_app.py        # Main application
├── utils/                 # Utility modules
│   ├── auto_updater.py    # Auto-update system
│   ├── settings_manager.py # Settings management
│   └── history_manager.py # History tracking
├── api_client/            # LaunchDarkly API client
├── shared/                # Shared components
├── .github/workflows/     # GitHub Actions
├── version.py             # Version management
├── build_exe.py          # Build script
└── requirements.txt      # Dependencies
```

## 🏗️ Building Executable

```bash
python build_exe.py
```

This creates a standalone Windows executable in the `dist/` folder with:
- Auto-update functionality
- All dependencies bundled
- Windows version information
- Professional appearance

## 🔐 Security Features

- **Secure API handling** with proper authentication
- **HTTPS downloads** for updates
- **Version validation** and integrity checks
- **User session management** with timeouts

## 📊 Usage

1. **Login** with your credentials
2. **Select tab** based on your needs:
   - **Get**: Retrieve flag information
   - **Update**: Modify flag settings with PMC targeting
   - **Create**: Create new feature flags
   - **View**: Browse all flags with filtering
   - **Log**: View operation history

3. **Auto-updates** will notify you of new versions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details

## 🆘 Support

- **Issues**: Report bugs via GitHub Issues
- **Documentation**: Check the wiki for detailed guides
- **Updates**: Enable auto-updates for the latest features

---

**Version**: 1.0.0 | **Build Date**: 2025-01-15 | **Author**: Feature Flag Team