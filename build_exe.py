"""
Build script for creating executable with PyInstaller
Includes auto-update functionality and proper resource bundling
"""

import PyInstaller.__main__
import os
import sys
from pathlib import Path

def build_executable():
    """Build the executable using PyInstaller"""
    
    # Get the current directory
    current_dir = Path(__file__).parent
    
    # Define paths
    main_script = current_dir / "main.py"
    icon_path = current_dir / "assets" / "icon.ico"  # Add your icon file
    
    # PyInstaller arguments
    args = [
        str(main_script),
        '--name=FeatureFlagManager',
        '--onefile',
        '--windowed',
        '--clean',
        f'--distpath={current_dir / "dist"}',
        f'--workpath={current_dir / "build"}',
        f'--specpath={current_dir}',
        
        # Include version information
        '--add-data=version.py;.',
        '--add-data=utils/auto_updater.py;utils',
        
        # Include all necessary modules
        '--hidden-import=requests',
        '--hidden-import=tkinter',
        '--hidden-import=ttkbootstrap',
        '--hidden-import=PIL',
        '--hidden-import=configparser',
        '--hidden-import=json',
        '--hidden-import=threading',
        '--hidden-import=subprocess',
        '--hidden-import=tempfile',
        '--hidden-import=pathlib',
        
        # Include data files
        '--add-data=ui;ui',
        '--add-data=utils;utils',
        '--add-data=api_client;api_client',
        '--add-data=api_config;api_config',
        '--add-data=shared;shared',
        '--add-data=constants;constants',
        
        # Version info for Windows
        '--version-file=version_info.txt',
    ]
    
    # Add icon if it exists
    if icon_path.exists():
        args.append(f'--icon={icon_path}')
    
    # Add console for debugging (remove for production)
    # args.append('--console')
    
    print("Building executable with auto-update support...")
    print(f"Main script: {main_script}")
    print(f"Output directory: {current_dir / 'dist'}")
    
    # Run PyInstaller
    PyInstaller.__main__.run(args)
    
    print("\n✅ Build completed!")
    print(f"Executable location: {current_dir / 'dist' / 'FeatureFlagManager.exe'}")
    print("\nAuto-update features included:")
    print("• Automatic version checking on startup")
    print("• Manual update check via Help menu")
    print("• Background download and installation")
    print("• Version skipping and reminder options")

def create_version_info():
    """Create version info file for Windows executable"""
    from version import __version__, __build_date__, __author__
    
    version_parts = __version__.split('.')
    while len(version_parts) < 4:
        version_parts.append('0')
    
    version_info_content = f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({','.join(version_parts)}),
    prodvers=({','.join(version_parts)}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'{__author__}'),
        StringStruct(u'FileDescription', u'Feature Flag Management System'),
        StringStruct(u'FileVersion', u'{__version__}'),
        StringStruct(u'InternalName', u'FeatureFlagManager'),
        StringStruct(u'LegalCopyright', u'© 2024 Feature Flag Management System'),
        StringStruct(u'OriginalFilename', u'FeatureFlagManager.exe'),
        StringStruct(u'ProductName', u'Feature Flag Manager'),
        StringStruct(u'ProductVersion', u'{__version__}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)"""
    
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info_content)
    
    print("Created version_info.txt")

if __name__ == "__main__":
    # Create version info file
    create_version_info()
    
    # Build executable
    build_executable()
    
    # Cleanup
    try:
        os.remove('version_info.txt')
    except:
        pass
