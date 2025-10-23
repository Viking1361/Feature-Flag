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
AUDIT_FILE = os.environ.get("AUDIT_FILE", "audit_events.jsonl")
LAUNCHDARKLY_API_KEY = os.environ.get("LAUNCHDARKLY_API_KEY", "")
PROJECT_KEY = os.environ.get("PROJECT_KEY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "Admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ia1")
# Teams/Graph notifications (optional)
TEAMS_ENABLED = os.environ.get("TEAMS_ENABLED", "false")
GRAPH_TENANT_ID = os.environ.get("GRAPH_TENANT_ID", "")
GRAPH_CLIENT_ID = os.environ.get("GRAPH_CLIENT_ID", "")
GRAPH_CLIENT_SECRET = os.environ.get("GRAPH_CLIENT_SECRET", "")
TEAMS_TEAM_ID = os.environ.get("TEAMS_TEAM_ID", "")
TEAMS_CHANNEL_ID = os.environ.get("TEAMS_CHANNEL_ID", "")
TEAMS_CHANNEL_EMAIL = os.environ.get("TEAMS_CHANNEL_EMAIL", "")
# Teams dry-run testing (no Graph keys needed)
TEAMS_DRY_RUN = os.environ.get("TEAMS_DRY_RUN", "false")
TEAMS_DRY_RUN_WEBHOOK = os.environ.get("TEAMS_DRY_RUN_WEBHOOK", "")
TEAMS_DRY_RUN_FILE = os.environ.get("TEAMS_DRY_RUN_FILE", "teams_dry_run.jsonl")
# Daily summary popup configuration
DAILY_SUMMARY_ENABLED = os.environ.get("DAILY_SUMMARY_ENABLED", "true")
# Comma-separated list of event types to include (e.g., "update_flag,pmc_targeting_update"). Empty = include all (except reads)
DAILY_SUMMARY_EVENT_TYPES = os.environ.get("DAILY_SUMMARY_EVENT_TYPES", "")
# If true, include only ok==True entries
DAILY_SUMMARY_OK_ONLY = os.environ.get("DAILY_SUMMARY_OK_ONLY", "false")

# 2) Try to load optional root-level config.py without creating a hard import dependency
try:
    spec = importlib.util.find_spec("config")
    if spec is not None:
        cfg = importlib.import_module("config")
        LAUNCHDARKLY_API_KEY = getattr(cfg, "LAUNCHDARKLY_API_KEY", LAUNCHDARKLY_API_KEY)
        PROJECT_KEY = getattr(cfg, "PROJECT_KEY", PROJECT_KEY)
        LOG_FILE = getattr(cfg, "LOG_FILE", LOG_FILE)
        HISTORY_FILE = getattr(cfg, "HISTORY_FILE", HISTORY_FILE)
        AUDIT_FILE = getattr(cfg, "AUDIT_FILE", AUDIT_FILE)
        GITHUB_TOKEN = getattr(cfg, "GITHUB_TOKEN", GITHUB_TOKEN)
        ADMIN_USERNAME = getattr(cfg, "ADMIN_USERNAME", ADMIN_USERNAME)
        ADMIN_PASSWORD = getattr(cfg, "ADMIN_PASSWORD", ADMIN_PASSWORD)
        TEAMS_ENABLED = getattr(cfg, "TEAMS_ENABLED", TEAMS_ENABLED)
        GRAPH_TENANT_ID = getattr(cfg, "GRAPH_TENANT_ID", GRAPH_TENANT_ID)
        GRAPH_CLIENT_ID = getattr(cfg, "GRAPH_CLIENT_ID", GRAPH_CLIENT_ID)
        GRAPH_CLIENT_SECRET = getattr(cfg, "GRAPH_CLIENT_SECRET", GRAPH_CLIENT_SECRET)
        TEAMS_TEAM_ID = getattr(cfg, "TEAMS_TEAM_ID", TEAMS_TEAM_ID)
        TEAMS_CHANNEL_ID = getattr(cfg, "TEAMS_CHANNEL_ID", TEAMS_CHANNEL_ID)
        TEAMS_CHANNEL_EMAIL = getattr(cfg, "TEAMS_CHANNEL_EMAIL", TEAMS_CHANNEL_EMAIL)
        TEAMS_DRY_RUN = getattr(cfg, "TEAMS_DRY_RUN", TEAMS_DRY_RUN)
        TEAMS_DRY_RUN_WEBHOOK = getattr(cfg, "TEAMS_DRY_RUN_WEBHOOK", TEAMS_DRY_RUN_WEBHOOK)
        TEAMS_DRY_RUN_FILE = getattr(cfg, "TEAMS_DRY_RUN_FILE", TEAMS_DRY_RUN_FILE)
        DAILY_SUMMARY_ENABLED = getattr(cfg, "DAILY_SUMMARY_ENABLED", DAILY_SUMMARY_ENABLED)
        DAILY_SUMMARY_EVENT_TYPES = getattr(cfg, "DAILY_SUMMARY_EVENT_TYPES", DAILY_SUMMARY_EVENT_TYPES)
        DAILY_SUMMARY_OK_ONLY = getattr(cfg, "DAILY_SUMMARY_OK_ONLY", DAILY_SUMMARY_OK_ONLY)
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
                    AUDIT_FILE = getattr(cfg_local, "AUDIT_FILE", AUDIT_FILE)
                    GITHUB_TOKEN = getattr(cfg_local, "GITHUB_TOKEN", GITHUB_TOKEN)
                    ADMIN_USERNAME = getattr(cfg_local, "ADMIN_USERNAME", ADMIN_USERNAME)
                    ADMIN_PASSWORD = getattr(cfg_local, "ADMIN_PASSWORD", ADMIN_PASSWORD)
                    TEAMS_ENABLED = getattr(cfg_local, "TEAMS_ENABLED", TEAMS_ENABLED)
                    GRAPH_TENANT_ID = getattr(cfg_local, "GRAPH_TENANT_ID", GRAPH_TENANT_ID)
                    GRAPH_CLIENT_ID = getattr(cfg_local, "GRAPH_CLIENT_ID", GRAPH_CLIENT_ID)
                    GRAPH_CLIENT_SECRET = getattr(cfg_local, "GRAPH_CLIENT_SECRET", GRAPH_CLIENT_SECRET)
                    TEAMS_TEAM_ID = getattr(cfg_local, "TEAMS_TEAM_ID", TEAMS_TEAM_ID)
                    TEAMS_CHANNEL_ID = getattr(cfg_local, "TEAMS_CHANNEL_ID", TEAMS_CHANNEL_ID)
                    TEAMS_CHANNEL_EMAIL = getattr(cfg_local, "TEAMS_CHANNEL_EMAIL", TEAMS_CHANNEL_EMAIL)
                    TEAMS_DRY_RUN = getattr(cfg_local, "TEAMS_DRY_RUN", TEAMS_DRY_RUN)
                    TEAMS_DRY_RUN_WEBHOOK = getattr(cfg_local, "TEAMS_DRY_RUN_WEBHOOK", TEAMS_DRY_RUN_WEBHOOK)
                    TEAMS_DRY_RUN_FILE = getattr(cfg_local, "TEAMS_DRY_RUN_FILE", TEAMS_DRY_RUN_FILE)
                    DAILY_SUMMARY_ENABLED = getattr(cfg_local, "DAILY_SUMMARY_ENABLED", DAILY_SUMMARY_ENABLED)
                    DAILY_SUMMARY_EVENT_TYPES = getattr(cfg_local, "DAILY_SUMMARY_EVENT_TYPES", DAILY_SUMMARY_EVENT_TYPES)
                    DAILY_SUMMARY_OK_ONLY = getattr(cfg_local, "DAILY_SUMMARY_OK_ONLY", DAILY_SUMMARY_OK_ONLY)
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
                AUDIT_FILE = data.get("AUDIT_FILE", AUDIT_FILE)
                GITHUB_TOKEN = data.get("GITHUB_TOKEN", GITHUB_TOKEN)
                ADMIN_USERNAME = data.get("ADMIN_USERNAME", ADMIN_USERNAME)
                ADMIN_PASSWORD = data.get("ADMIN_PASSWORD", ADMIN_PASSWORD)
                TEAMS_ENABLED = data.get("TEAMS_ENABLED", TEAMS_ENABLED)
                GRAPH_TENANT_ID = data.get("GRAPH_TENANT_ID", GRAPH_TENANT_ID)
                GRAPH_CLIENT_ID = data.get("GRAPH_CLIENT_ID", GRAPH_CLIENT_ID)
                GRAPH_CLIENT_SECRET = data.get("GRAPH_CLIENT_SECRET", GRAPH_CLIENT_SECRET)
                TEAMS_TEAM_ID = data.get("TEAMS_TEAM_ID", TEAMS_TEAM_ID)
                TEAMS_CHANNEL_ID = data.get("TEAMS_CHANNEL_ID", TEAMS_CHANNEL_ID)
                TEAMS_CHANNEL_EMAIL = data.get("TEAMS_CHANNEL_EMAIL", TEAMS_CHANNEL_EMAIL)
                TEAMS_DRY_RUN = data.get("TEAMS_DRY_RUN", TEAMS_DRY_RUN)
                TEAMS_DRY_RUN_WEBHOOK = data.get("TEAMS_DRY_RUN_WEBHOOK", TEAMS_DRY_RUN_WEBHOOK)
                TEAMS_DRY_RUN_FILE = data.get("TEAMS_DRY_RUN_FILE", TEAMS_DRY_RUN_FILE)
                DAILY_SUMMARY_ENABLED = data.get("DAILY_SUMMARY_ENABLED", DAILY_SUMMARY_ENABLED)
                DAILY_SUMMARY_EVENT_TYPES = data.get("DAILY_SUMMARY_EVENT_TYPES", DAILY_SUMMARY_EVENT_TYPES)
                DAILY_SUMMARY_OK_ONLY = data.get("DAILY_SUMMARY_OK_ONLY", DAILY_SUMMARY_OK_ONLY)
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

        # Expand placeholders and environment variables in path-like settings
        def _expand_path_tokens(p: str) -> str:
            try:
                if not p:
                    return p
                # Expand environment variables like %USERPROFILE% or %LOCALAPPDATA%
                p = os.path.expandvars(str(p))
                # Token substitution
                exe_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
                tokens = {
                    "{EXE_DIR}": str(exe_dir),
                    "{CWD}": str(Path.cwd()),
                    "{APPDATA_DIR}": str(app_dir),
                }
                for k, v in tokens.items():
                    p = p.replace(k, v)
                return p
            except Exception:
                return p

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

        # First expand tokens, then resolve relative paths
        LOG_FILE = _resolve_path(_expand_path_tokens(LOG_FILE), ("feature_flag.log",))
        HISTORY_FILE = _resolve_path(_expand_path_tokens(HISTORY_FILE), ("autocomplete_history.json",))
        TEAMS_DRY_RUN_FILE = _resolve_path(_expand_path_tokens(TEAMS_DRY_RUN_FILE), ("teams_dry_run.jsonl",))
        AUDIT_FILE = _resolve_path(_expand_path_tokens(AUDIT_FILE), ("audit_events.jsonl",))
except Exception:
    pass

# Final sanity: keep types consistent
LAUNCHDARKLY_API_KEY = str(LAUNCHDARKLY_API_KEY) if LAUNCHDARKLY_API_KEY is not None else ""
PROJECT_KEY = str(PROJECT_KEY) if PROJECT_KEY is not None else ""
LOG_FILE = str(LOG_FILE) if LOG_FILE is not None else "feature_flag.log"
HISTORY_FILE = str(HISTORY_FILE) if HISTORY_FILE is not None else "autocomplete_history.json"
AUDIT_FILE = str(AUDIT_FILE) if AUDIT_FILE is not None else "audit_events.jsonl"
GITHUB_TOKEN = str(GITHUB_TOKEN) if GITHUB_TOKEN is not None else ""
ADMIN_USERNAME = str(ADMIN_USERNAME) if ADMIN_USERNAME is not None else "Admin"
ADMIN_PASSWORD = str(ADMIN_PASSWORD) if ADMIN_PASSWORD is not None else "ia1"

# Normalize booleans and ensure strings for Teams/Graph
try:
    TEAMS_ENABLED = str(TEAMS_ENABLED).strip().lower() in ("1", "true", "yes", "on")
except Exception:
    TEAMS_ENABLED = False

try:
    TEAMS_DRY_RUN = str(TEAMS_DRY_RUN).strip().lower() in ("1", "true", "yes", "on")
except Exception:
    TEAMS_DRY_RUN = False

try:
    DAILY_SUMMARY_ENABLED = str(DAILY_SUMMARY_ENABLED).strip().lower() in ("1", "true", "yes", "on")
except Exception:
    DAILY_SUMMARY_ENABLED = True

try:
    DAILY_SUMMARY_OK_ONLY = str(DAILY_SUMMARY_OK_ONLY).strip().lower() in ("1", "true", "yes", "on")
except Exception:
    DAILY_SUMMARY_OK_ONLY = False

GRAPH_TENANT_ID = str(GRAPH_TENANT_ID) if 'GRAPH_TENANT_ID' in globals() and GRAPH_TENANT_ID is not None else ""
GRAPH_CLIENT_ID = str(GRAPH_CLIENT_ID) if 'GRAPH_CLIENT_ID' in globals() and GRAPH_CLIENT_ID is not None else ""
GRAPH_CLIENT_SECRET = str(GRAPH_CLIENT_SECRET) if 'GRAPH_CLIENT_SECRET' in globals() and GRAPH_CLIENT_SECRET is not None else ""
TEAMS_TEAM_ID = str(TEAMS_TEAM_ID) if 'TEAMS_TEAM_ID' in globals() and TEAMS_TEAM_ID is not None else ""
TEAMS_CHANNEL_ID = str(TEAMS_CHANNEL_ID) if 'TEAMS_CHANNEL_ID' in globals() and TEAMS_CHANNEL_ID is not None else ""
TEAMS_CHANNEL_EMAIL = str(TEAMS_CHANNEL_EMAIL) if 'TEAMS_CHANNEL_EMAIL' in globals() and TEAMS_CHANNEL_EMAIL is not None else ""
TEAMS_DRY_RUN_WEBHOOK = str(TEAMS_DRY_RUN_WEBHOOK) if 'TEAMS_DRY_RUN_WEBHOOK' in globals() and TEAMS_DRY_RUN_WEBHOOK is not None else ""
TEAMS_DRY_RUN_FILE = str(TEAMS_DRY_RUN_FILE) if 'TEAMS_DRY_RUN_FILE' in globals() and TEAMS_DRY_RUN_FILE is not None else "teams_dry_run.jsonl"
AUDIT_FILE = str(AUDIT_FILE) if 'AUDIT_FILE' in globals() and AUDIT_FILE is not None else "audit_events.jsonl"
DAILY_SUMMARY_EVENT_TYPES = str(DAILY_SUMMARY_EVENT_TYPES) if 'DAILY_SUMMARY_EVENT_TYPES' in globals() and DAILY_SUMMARY_EVENT_TYPES is not None else ""
