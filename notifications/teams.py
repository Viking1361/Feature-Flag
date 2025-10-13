"""
Microsoft Teams notifications via Microsoft Graph
"""
from __future__ import annotations

import requests
import logging
import json
from datetime import datetime
from typing import Optional
from shared.config_loader import (
    TEAMS_ENABLED,
    GRAPH_TENANT_ID,
    GRAPH_CLIENT_ID,
    GRAPH_CLIENT_SECRET,
    TEAMS_TEAM_ID,
    TEAMS_CHANNEL_ID,
    TEAMS_DRY_RUN,
    TEAMS_DRY_RUN_WEBHOOK,
    TEAMS_DRY_RUN_FILE,
    AUDIT_FILE,
)

logger = logging.getLogger(__name__)

def _append_history(payload: dict) -> None:
    """Append a single JSON line to the unified audit history file (ASCII-safe)."""
    try:
        # Ensure minimal types and avoid non-serializable objects
        safe = {
            k: (str(v) if not isinstance(v, (str, int, float, bool, type(None), list, dict)) else v)
            for k, v in payload.items()
        }
        with open(AUDIT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(safe) + "\n")
    except Exception as e:
        logger.debug(f"append_history failed: {e}")

TOKEN_URL_TMPL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
GRAPH_SCOPE = "https://graph.microsoft.com/.default"


def _get_graph_token() -> Optional[str]:
    """Client credentials OAuth2 flow for Microsoft Graph."""
    try:
        if not (GRAPH_TENANT_ID and GRAPH_CLIENT_ID and GRAPH_CLIENT_SECRET):
            logger.info("Teams notify disabled: missing Graph credentials")
            return None
        data = {
            "client_id": GRAPH_CLIENT_ID,
            "client_secret": GRAPH_CLIENT_SECRET,
            "scope": GRAPH_SCOPE,
            "grant_type": "client_credentials",
        }
        url = TOKEN_URL_TMPL.format(tenant=GRAPH_TENANT_ID)
        resp = requests.post(url, data=data, timeout=15)
        if resp.status_code != 200:
            logger.error(f"Graph token error: {resp.status_code}")
            return None
        return resp.json().get("access_token")
    except Exception as e:
        logger.error(f"Graph token exception: {e}")
        return None


def _post_channel_message_html(token: str, team_id: str, channel_id: str, html: str) -> bool:
    try:
        url = f"https://graph.microsoft.com/v1.0/teams/{team_id}/channels/{channel_id}/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        body = {
            "body": {
                "contentType": "html",
                "content": html,
            }
        }
        r = requests.post(url, headers=headers, json=body, timeout=15)
        ok = 200 <= r.status_code < 300
        if not ok:
            logger.error(f"Teams notify failed: {r.status_code} {r.text[:200]}")
        else:
            logger.info("Teams notify sent")
        return ok
    except Exception as e:
        logger.error(f"Teams notify exception: {e}")
        return False


def build_flag_change_html(
    feature_key: str,
    environment: str,
    enabled: bool,
    user: str,
    ticket: Optional[str] = None,
    comment: Optional[str] = None,
    ld_url: Optional[str] = None,
) -> str:
    status_text = "ON" if enabled else "OFF"
    html_lines = [
        "<b>Feature Flag Change</b>",
        f"<div>Flag: <code>{feature_key}</code></div>",
        f"<div>Env: <code>{environment}</code></div>",
        f"<div>Status: <b>{status_text}</b></div>",
        f"<div>User: {user}</div>",
    ]
    if ticket:
        html_lines.append(f"<div>Ticket: {ticket}</div>")
    if comment:
        html_lines.append(f"<div>Comment: {comment}</div>")
    if ld_url:
        html_lines.append(f"<div><a href='{ld_url}'>Open in LaunchDarkly</a></div>")
    return "".join(html_lines)


def notify_flag_change(
    feature_key: str,
    environment: str,
    enabled: bool,
    user: str,
    ticket: Optional[str] = None,
    comment: Optional[str] = None,
    ld_url: Optional[str] = None,
    dry_run_override: Optional[bool] = None,
) -> bool:
    """Post a concise message about a flag change to a Teams channel.
    Returns True if sent, False otherwise.
    """
    try:
        # Build message HTML (ASCII-only content)
        html = build_flag_change_html(
            feature_key=feature_key,
            environment=environment,
            enabled=enabled,
            user=user,
            ticket=ticket,
            comment=comment,
            ld_url=ld_url,
        )

        # Dry-run path: allow validation without Graph credentials
        use_dry_run = TEAMS_DRY_RUN if dry_run_override is None else bool(dry_run_override)
        if use_dry_run:
            payload = {
                "ts": datetime.utcnow().isoformat() + "Z",
                "type": "feature_flag_change",
                "feature_key": feature_key,
                "environment": environment,
                "enabled": bool(enabled),
                "user": user,
                "ticket": ticket or "",
                "comment": comment or "",
                "ld_url": ld_url or "",
                "html": html,
                "transport": "dry_run",
            }
            try:
                if TEAMS_DRY_RUN_WEBHOOK:
                    # Post JSON to a local/dev webhook for inspection
                    r = requests.post(TEAMS_DRY_RUN_WEBHOOK, json=payload, timeout=10)
                    ok = 200 <= r.status_code < 300
                    # Always append to history as well
                    payload_hist = dict(payload)
                    payload_hist["ok"] = bool(ok)
                    payload_hist["webhook_status"] = r.status_code
                    _append_history(payload_hist)
                    if ok:
                        logger.info("Teams dry-run webhook ok")
                        return True
                    logger.error(f"Teams dry-run webhook failed: {r.status_code} {r.text[:200]}")
                    return False
            except Exception as e:
                logger.error(f"Teams dry-run webhook exception: {e}")
                # fall through to file sink
            try:
                with open(TEAMS_DRY_RUN_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(payload) + "\n")
                logger.info(f"Teams dry-run wrote to {TEAMS_DRY_RUN_FILE}")
                # Also append to unified audit file
                try:
                    payload_hist = dict(payload)
                    payload_hist["ok"] = True
                    _append_history(payload_hist)
                except Exception:
                    pass
                return True
            except Exception as e:
                logger.error(f"Teams dry-run file write failed: {e}")
                return False

        # Real send path
        if not TEAMS_ENABLED:
            return False
        if not (TEAMS_TEAM_ID and TEAMS_CHANNEL_ID):
            logger.info("Teams notify disabled: team/channel not configured")
            return False

        token = _get_graph_token()
        if not token:
            return False

        ok = _post_channel_message_html(token, TEAMS_TEAM_ID, TEAMS_CHANNEL_ID, html)
        # Append to history for visibility in Notifications tab
        try:
            payload_hist = {
                "ts": datetime.utcnow().isoformat() + "Z",
                "type": "feature_flag_change",
                "feature_key": feature_key,
                "environment": environment,
                "enabled": bool(enabled),
                "user": user,
                "ticket": ticket or "",
                "comment": comment or "",
                "ld_url": ld_url or "",
                "html": html,
                "transport": "graph",
                "ok": bool(ok),
            }
            _append_history(payload_hist)
        except Exception:
            pass
        return ok
    except Exception as e:
        logger.error(f"notify_flag_change exception: {e}")
        return False
