from __future__ import annotations

import json
import os
import getpass
from datetime import datetime
import logging

from shared.config_loader import AUDIT_FILE

logger = logging.getLogger(__name__)


def _ensure_dir(path: str) -> None:
    try:
        d = os.path.dirname(os.path.abspath(path))
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
    except Exception as e:
        logger.debug(f"audit ensure_dir failed: {e}")


def _current_user() -> str:
    try:
        # Prefer app user session if available
        try:
            from shared.user_session import user_session  # type: ignore
            if getattr(user_session, "is_logged_in", False):
                return str(getattr(user_session, "username", "")) or getpass.getuser()
        except Exception:
            pass
        return getpass.getuser()
    except Exception:
        return "unknown"


def audit_event(event_type: str, details: dict | None = None, ok: bool | None = None) -> None:
    """Append a single audit event to the JSONL audit file.

    Schema (stable, additive):
    - ts: ISO UTC timestamp
    - type: event type (e.g., get_flag, update_flag, create_flag, notify_flag)
    - user: username (from session if present, else OS user)
    - ok: optional boolean outcome
    - ...details: flattened event data (feature_key, environment, enabled, message, etc.)
    """
    try:
        payload = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "type": str(event_type),
            "user": _current_user(),
        }
        if ok is not None:
            payload["ok"] = bool(ok)
        if details:
            for k, v in details.items():
                try:
                    # Basic sanitation for JSON serializable content
                    if isinstance(v, (str, int, float, bool)) or v is None:
                        payload[k] = v
                    else:
                        payload[k] = json.loads(json.dumps(v))
                except Exception:
                    payload[k] = str(v)
        _ensure_dir(AUDIT_FILE)
        with open(AUDIT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception as e:
        logger.debug(f"audit_event failed: {e}")
