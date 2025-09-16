#!/usr/bin/env python3
"""
Feature Flag Management Application
Main entry point for the modular application
"""

import ttkbootstrap as ttk
from ui.login_window import LoginWindow

def main():
    """Main application entry point"""
    # Use a themed window for a better look
    login_root = ttk.Window(themename="superhero")
    login_app = LoginWindow(login_root)
    login_root.mainloop()

if __name__ == "__main__":
    main() 