"""
Centralized configuration loader for the Feature Flag app.

Order of precedence (highest to lowest):
1) Environment variables
2) Optional root-level config.py (if present on the system)
3) config.json placed next to the EXE or in the working directory
4) Sensible defaults

This design avoids bundling secrets and works in PyInstaller builds.
"""

from __future__ import annotations

import os
import sys
import json
import importlib
import importlib.util
import importlib.machinery
from pathlib import Path

# Defaults (can be overridden by env/config)
LOG_FILE = os.environ.get("LOG_FILE", "feature_flag.log")
HISTORY_FILE = os.environ.get("HISTORY_FILE", "autocomplete_history.json")
LAUNCHDARKLY_API_KEY = os.environ.get("LAUNCHDARKLY_API_KEY", "")
PROJECT_KEY = os.environ.get("PROJECT_KEY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "Admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ia1")

# 2) Try to load optional root-level config.py without creating a hard import dependency
try:
    spec = importlib.util.find_spec("config")
    if spec is not None:
        cfg = importlib.import_module("config")
        LAUNCHDARKLY_API_KEY = getattr(cfg, "LAUNCHDARKLY_API_KEY", LAUNCHDARKLY_API_KEY)
        PROJECT_KEY = getattr(cfg, "PROJECT_KEY", PROJECT_KEY)
        LOG_FILE = getattr(cfg, "LOG_FILE", LOG_FILE)
        HISTORY_FILE = getattr(cfg, "HISTORY_FILE", HISTORY_FILE)
        GITHUB_TOKEN = getattr(cfg, "GITHUB_TOKEN", GITHUB_TOKEN)
        ADMIN_USERNAME = getattr(cfg, "ADMIN_USERNAME", ADMIN_USERNAME)
        ADMIN_PASSWORD = getattr(cfg, "ADMIN_PASSWORD", ADMIN_PASSWORD)
except Exception:
    # Safe fallback if config.py isn't available
    pass

# 3) Try to load a plain config.py file by path (next to EXE, CWD, or project root)
try:
    # Determine common locations
    exe_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else None
    cwd = Path.cwd()
    project_root = Path(__file__).resolve().parent.parent

    candidate_dirs: list[Path] = []
    if exe_dir:
        candidate_dirs.append(exe_dir)
    candidate_dirs.append(cwd)
    candidate_dirs.append(project_root)

    for d in candidate_dirs:
        try:
            cfg_path = d / "config.py"
            if cfg_path.exists():
                loader = importlib.machinery.SourceFileLoader("config_local", str(cfg_path))
                spec_local = importlib.util.spec_from_loader("config_local", loader)
                if spec_local is not None:
                    cfg_local = importlib.util.module_from_spec(spec_local)
                    loader.exec_module(cfg_local)
                    LAUNCHDARKLY_API_KEY = getattr(cfg_local, "LAUNCHDARKLY_API_KEY", LAUNCHDARKLY_API_KEY)
                    PROJECT_KEY = getattr(cfg_local, "PROJECT_KEY", PROJECT_KEY)
                    LOG_FILE = getattr(cfg_local, "LOG_FILE", LOG_FILE)
                    HISTORY_FILE = getattr(cfg_local, "HISTORY_FILE", HISTORY_FILE)
                    GITHUB_TOKEN = getattr(cfg_local, "GITHUB_TOKEN", GITHUB_TOKEN)
                    ADMIN_USERNAME = getattr(cfg_local, "ADMIN_USERNAME", ADMIN_USERNAME)
                    ADMIN_PASSWORD = getattr(cfg_local, "ADMIN_PASSWORD", ADMIN_PASSWORD)
                    break
        except Exception:
            continue
except Exception:
    pass

# 4) If still missing, try to load config.json placed next to the EXE or in CWD
try:
    # Where to look for a JSON config
    candidates: list[Path] = []

    # If frozen by PyInstaller, sys.executable points to the EXE
    try:
        exe_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else None
        if exe_dir:
            candidates.append(exe_dir / "config.json")
            candidates.append(exe_dir / "feature_flag_config.json")
    except Exception:
        pass

    # Current working directory
    try:
        cwd = Path.cwd()
        candidates.append(cwd / "config.json")
        candidates.append(cwd / "feature_flag_config.json")
    except Exception:
        pass

    # Project root (two levels up from this file: shared/config_loader.py)
    try:
        project_root = Path(__file__).resolve().parent.parent
        candidates.append(project_root / "config.json")
        candidates.append(project_root / "feature_flag_config.json")
    except Exception:
        pass

    for path in candidates:
        try:
            if path and path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Only override if keys provided
                LAUNCHDARKLY_API_KEY = data.get("LAUNCHDARKLY_API_KEY", LAUNCHDARKLY_API_KEY)
                PROJECT_KEY = data.get("PROJECT_KEY", PROJECT_KEY)
                LOG_FILE = data.get("LOG_FILE", LOG_FILE)
                HISTORY_FILE = data.get("HISTORY_FILE", HISTORY_FILE)
                GITHUB_TOKEN = data.get("GITHUB_TOKEN", GITHUB_TOKEN)
                ADMIN_USERNAME = data.get("ADMIN_USERNAME", ADMIN_USERNAME)
                ADMIN_PASSWORD = data.get("ADMIN_PASSWORD", ADMIN_PASSWORD)
                break
        except Exception:
            # Ignore JSON errors and try the next candidate
            continue
except Exception:
    pass

# 5) Ensure default paths are writable on Windows
try:
    is_windows = os.name == "nt"
    # If running as a frozen EXE or using default relative names, prefer LocalAppData
    prefer_appdata = getattr(sys, "frozen", False)

    if is_windows:
        local = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        app_dir = Path(local) / "FeatureFlag"
        try:
            app_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            # If unable to create, fallback to CWD for relative paths
            app_dir = Path.cwd()

        def _resolve_path(p: str, default_names: tuple[str, ...]) -> str:
            try:
                if not p:
                    return p
                p_path = Path(str(p))
                # Keep absolute or network paths as-is
                if p_path.is_absolute():
                    return str(p_path)
                base = p_path.name
                # If running frozen, redirect any relative path to app_dir
                if prefer_appdata:
                    return str(app_dir / base)
                # If not frozen, only redirect known default filenames
                if base.lower() in default_names:
                    return str(app_dir / base)
                return str(p_path)
            except Exception:
                return p

        LOG_FILE = _resolve_path(LOG_FILE, ("feature_flag.log",))
        HISTORY_FILE = _resolve_path(HISTORY_FILE, ("autocomplete_history.json",))
except Exception:
    pass

# Final sanity: keep types consistent
LAUNCHDARKLY_API_KEY = str(LAUNCHDARKLY_API_KEY) if LAUNCHDARKLY_API_KEY is not None else ""
PROJECT_KEY = str(PROJECT_KEY) if PROJECT_KEY is not None else ""
LOG_FILE = str(LOG_FILE) if LOG_FILE is not None else "feature_flag.log"
HISTORY_FILE = str(HISTORY_FILE) if HISTORY_FILE is not None else "autocomplete_history.json"
GITHUB_TOKEN = str(GITHUB_TOKEN) if GITHUB_TOKEN is not None else ""
ADMIN_USERNAME = str(ADMIN_USERNAME) if ADMIN_USERNAME is not None else "Admin"
ADMIN_PASSWORD = str(ADMIN_PASSWORD) if ADMIN_PASSWORD is not None else "ia1"
