"""
Version management for Feature Flag Manager
"""
__version__ = "1.0.25"
__build_date__ = "2025-10-27"   
__author__ = "Feature Flag Team"

# Update configuration - REPLACE WITH YOUR GITHUB REPOSITORY
GITHUB_OWNER = "Viking1361"  # Replace with your GitHub username/organization
GITHUB_REPO = "Feature-Flag"  # Replace with your repository name

UPDATE_CHECK_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
UPDATE_DOWNLOAD_URL = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest/download/"
UPDATE_CHECK_INTERVAL = 24 * 60 * 60  # 24 hours in seconds

def get_version():
    """Get current version string"""
    return __version__

def get_version_info():
    """Get detailed version information"""
    return {
        "version": __version__,
        "build_date": __build_date__,
        "author": __author__
    }
