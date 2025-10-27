import os
import json
import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox
import logging
from datetime import datetime

from shared.config_loader import AUDIT_FILE, PROJECT_KEY
try:
    from shared.constants import READ_ENVIRONMENT_OPTIONS, ENVIRONMENT_MAPPINGS
except Exception:
    READ_ENVIRONMENT_OPTIONS = ["DEV", "OCRT", "SAT", "PROD"]
    ENVIRONMENT_MAPPINGS = {"DEV": "dev", "OCRT": "ocrt", "SAT": "sat", "PROD": "prod"}
from api_client import get_client
from ui.widgets.help_icon import HelpIcon
from utils.settings_manager import SettingsManager


logger = logging.getLogger(__name__)


class HistoryTab:
    def __init__(self, parent, history_manager, theme_manager):
        self.parent = parent
        self.history_manager = history_manager
        self.theme_manager = theme_manager
        self.api_client = get_client()
        self._history_cache = []
        self._sort_key = "ts"
        self._sort_reverse = True
        # Dialogs should only appear when user explicitly clicks Refresh
        self._user_trigger = False
        self._help_icons = []
        self.setup_ui()

    def setup_ui(self):
        colors = self.theme_manager.get_theme_config()["colors"]
        root = ttk.Frame(self.parent, padding=30)
        root.pack(fill="both", expand=True)

        # Title
        title = ttk.Label(
            root,
            text="Flag History",
            font=("Segoe UI", 24, "bold"),
            foreground=colors["text"],
        )
        title.pack(anchor="w")

        subtitle = ttk.Label(
            root,
            text="View audit events for a specific flag, filtered by environment",
            font=("Segoe UI", 12),
            foreground=colors["text"],
        )
        subtitle.pack(anchor="w", pady=(4, 12))

        # Status card
        status = ttk.Frame(root, style="Content.TFrame", padding=12)
        status.pack(fill="x", pady=(0, 10))
        ttk.Label(status, text="Source: LaunchDarkly Audit Log API (/auditlog)", font=("Segoe UI", 10), foreground=colors["text"]).pack(anchor="w")

        # Filters card
        filters_card = ttk.Frame(root, style="Content.TFrame", padding=10)
        filters_card.pack(fill="x", pady=(6, 10))

        filters_row = ttk.Frame(filters_card)
        filters_row.pack(fill="x")

        ttk.Label(filters_row, text="Flag Key:", font=("Segoe UI", 10), foreground=colors["text"]).pack(side="left")
        _hh1 = HelpIcon(filters_row, "history.flag_key")
        _hh1.pack(side="left", padx=(2,0))
        self._help_icons.append((_hh1, {"side": "left", "padx": (2,0)}))
        self.key_var = tk.StringVar()
        # Suggest keys from history (union of get/update)
        try:
            hist = self.history_manager.get_history() if hasattr(self, "history_manager") else {}
            keys = list(dict.fromkeys((hist.get("get_keys", []) or []) + (hist.get("update_keys", []) or [])))
        except Exception:
            keys = []
        self.key_entry = ttk.Combobox(filters_row, textvariable=self.key_var, values=keys, width=34)
        self.key_entry.pack(side="left", padx=(6, 12))

        ttk.Label(filters_row, text="Environment:", font=("Segoe UI", 10), foreground=colors["text"]).pack(side="left")
        _hh2 = HelpIcon(filters_row, "history.environment")
        _hh2.pack(side="left", padx=(2,0))
        self._help_icons.append((_hh2, {"side": "left", "padx": (2,0)}))
        self.env_var = tk.StringVar(value="Any")
        env_opts = ["Any"] + READ_ENVIRONMENT_OPTIONS
        self.env_entry = ttk.Combobox(filters_row, textvariable=self.env_var, values=env_opts, state="readonly", width=12)
        self.env_entry.pack(side="left", padx=(6, 12))

        refresh_group = ttk.Frame(filters_row)
        refresh_group.pack(side="left")
        ttk.Button(refresh_group, text="Refresh", width=10, command=self.on_user_refresh).pack(side="left")
        _hh3 = HelpIcon(refresh_group, "history.refresh")
        _hh3.pack(side="left", padx=(2,0))
        self._help_icons.append((_hh3, {"side": "left", "padx": (2,0)}))

        clear_group = ttk.Frame(filters_row)
        clear_group.pack(side="left", padx=(8, 0))
        ttk.Button(clear_group, text="Clear", width=10, command=self.on_clear).pack(side="left")
        _hh4 = HelpIcon(clear_group, "history.clear")
        _hh4.pack(side="left", padx=(2,0))
        self._help_icons.append((_hh4, {"side": "left", "padx": (2,0)}))

        # Results card
        results_card = ttk.Frame(root, style="Content.TFrame", padding=10)
        results_card.pack(fill="both", expand=True)
        ttk.Label(results_card, text="Results", font=("Segoe UI", 10, "bold"), foreground=colors["text"]).pack(anchor="w")

        tree_frame = ttk.Frame(results_card)
        tree_frame.pack(fill="both", expand=True)
        cols = ("ts", "type", "environment", "enabled", "user", "summary")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=12)
        col_defs = (
            ("ts", "Time", 170),
            ("type", "Type", 150),
            ("environment", "Env", 80),
            ("enabled", "Enabled", 70),
            ("user", "User", 120),
            ("summary", "Summary", 420),
        )
        self._col_labels = {c: t for c, t, _ in col_defs}
        for c, text, w in col_defs:
            self.tree.heading(c, text=text, command=lambda col=c: self._on_sort(col))
            self.tree.column(c, width=w, anchor="w")
        yscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # Actions row
        actions = ttk.Frame(results_card)
        actions.pack(fill="x", pady=(6, 0))
        ttk.Button(actions, text="Copy JSON", width=12, command=self.on_copy_json).pack(side="left")
        ttk.Button(actions, text="Copy Flag Key", width=14, command=self.on_copy_key).pack(side="left", padx=(8, 0))

        # Preview card
        preview = ttk.Frame(root, style="Content.TFrame", padding=10)
        preview.pack(fill="both", expand=True, pady=(8, 0))
        ttk.Label(preview, text="Preview", font=("Segoe UI", 10, "bold"), foreground=colors["text"]).pack(anchor="w")
        self.preview_text = tk.Text(
            preview,
            height=10,
            font=("Consolas", 10),
            wrap="word",
            state="disabled",
            bg=colors["background"],
            fg=colors["text"],
            bd=0,
            highlightthickness=0,
            relief="flat",
        )
        self.preview_text.pack(fill="both", expand=True)

        # Initial load
        try:
            self.on_refresh()
        except Exception:
            pass
        # Apply initial help icon visibility
        try:
            show = bool(SettingsManager().get("help", "show_help_icons"))
        except Exception:
            show = True
        if not show:
            self.set_help_icons_visible(False)

    # Data helpers
    def _load_events(self):
        """Fetch deep history from LaunchDarkly Audit Log API filtered by project/env/flag."""
        keyf = (self.key_var.get() or "").strip()
        env_display = (self.env_var.get() or "Any").strip()

        user_trigger = bool(getattr(self, "_user_trigger", False))
        if not keyf:
            if user_trigger:
                messagebox.showinfo("Flag History", "Please enter a flag key to query LaunchDarkly history.")
            return []
        if not env_display or env_display == "Any":
            if user_trigger:
                messagebox.showinfo("Flag History", "Please select an environment to query LaunchDarkly history.")
            return []
        if not PROJECT_KEY:
            if user_trigger:
                messagebox.showerror("Flag History", "PROJECT_KEY is not configured.")
            return []

        # Map display env (e.g., DEV) to LaunchDarkly environment key
        actual_env_key = ENVIRONMENT_MAPPINGS.get(env_display, env_display)

        specs = [
            f"proj/{PROJECT_KEY}:env/{actual_env_key}:flag/{keyf}",
            f"proj/{PROJECT_KEY}:flag/{keyf}:env/{actual_env_key}",
            f"{PROJECT_KEY}:env/{actual_env_key}:flag/{keyf}",
        ]
        last_err = None
        items = []
        for s in specs:
            try:
                items = self.api_client.get_audit_log_entries(
                    project_key=PROJECT_KEY,
                    env_key=actual_env_key,
                    limit=100,
                    spec=s,
                ) or []
                last_err = None
                break
            except Exception as e:
                last_err = e
                continue
        if last_err is not None:
            try:
                import requests
                if user_trigger:
                    if isinstance(last_err, requests.exceptions.HTTPError) and getattr(last_err, "response", None) is not None:
                        detail = last_err.response.text
                        messagebox.showerror("Flag History", f"AuditLog request failed. Spec variants tried: {len(specs)}. Details: {detail}")
                    else:
                        messagebox.showerror("Flag History", f"Failed to fetch history from LaunchDarkly: {last_err}")
            except Exception:
                if user_trigger:
                    messagebox.showerror("Flag History", f"Failed to fetch history from LaunchDarkly: {last_err}")
            return []

        entries = []
        for it in items:
            try:
                # Convert epoch millis to ISO time
                ts_val = it.get("date")
                if isinstance(ts_val, (int, float)):
                    ts_iso = datetime.fromtimestamp(ts_val / 1000).isoformat(timespec="seconds")
                else:
                    ts_iso = str(ts_val or "")

                # Determine user/member
                user_val = ""
                try:
                    m = it.get("member") or {}
                    if m.get("email"):
                        user_val = m.get("email")
                    else:
                        fn = (m.get("firstName") or "").strip()
                        ln = (m.get("lastName") or "").strip()
                        user_val = (fn + " " + ln).strip()
                except Exception:
                    user_val = ""
                if not user_val:
                    tkn = it.get("token") or {}
                    user_val = tkn.get("name", "") or ""

                # Enabled heuristic from titleVerb
                enabled_val = None
                try:
                    verb = (it.get("titleVerb") or "").lower()
                    if "turned on" in verb or "enabled" in verb:
                        enabled_val = True
                    elif "turned off" in verb or "disabled" in verb:
                        enabled_val = False
                except Exception:
                    enabled_val = None

                summary = (
                    (it.get("shortDescription") or "").strip()
                    or (it.get("description") or "").strip()
                    or (it.get("title") or "").strip()
                    or (it.get("name") or "").strip()
                )

                norm = {
                    "ts": ts_iso,
                    "type": it.get("titleVerb") or it.get("kind") or it.get("title") or "",
                    "feature_key": keyf,
                    "environment": env_display,
                    "enabled": enabled_val,
                    "user": user_val,
                    "summary": summary,
                    "raw": it,
                }
                entries.append(norm)
            except Exception:
                continue
        return entries

    def _apply_filters(self, entries):
        keyf = (self.key_var.get() or "").strip().lower()
        envf = (self.env_var.get() or "Any").strip()
        out = []
        for e in entries:
            if keyf and keyf not in str(e.get("feature_key", "")).lower():
                continue
            if envf and envf != "Any" and e.get("environment") != envf:
                continue
            out.append(e)
        # Sort
        key = self._sort_key or "ts"
        rev = bool(self._sort_reverse)
        try:
            if key in ("enabled",):
                out.sort(key=lambda x: bool(x.get(key, False)), reverse=rev)
            else:
                out.sort(key=lambda x: str(x.get(key, "")), reverse=rev)
        except Exception:
            out.sort(key=lambda x: x.get("ts", ""), reverse=True)
        return out

    def _render(self, entries):
        try:
            for iid in self.tree.get_children():
                self.tree.delete(iid)
            for idx, e in enumerate(entries):
                summary = self._summary(e)
                values = (
                    e.get("ts", ""),
                    e.get("type", ""),
                    e.get("environment", ""),
                    "True" if e.get("enabled") else "False",
                    e.get("user", ""),
                    summary,
                )
                self.tree.insert("", "end", iid=str(idx), values=values)
            self._history_cache = entries
        except Exception:
            pass

    def _summary(self, e: dict) -> str:
        try:
            s = str(e.get("summary", "")).strip()
            if s:
                return s
            etype = str(e.get("type", "")).strip()
            enabled_val = e.get("enabled")
            if etype == "pmc_targeting_update":
                pmc = str(e.get("pmc_id", "")).strip()
                action = "enabled" if enabled_val else "disabled"
                return f"PMC {pmc} {action}"
            if etype == "default_rule_update":
                if enabled_val is True:
                    return "Default rule set to True"
                if enabled_val is False:
                    return "Default rule set to False"
                return "Default rule updated"
            if etype == "feature_flag_change":
                return f"Toggled {'ON' if enabled_val else 'OFF'}"
            if etype == "update_flag":
                return f"Update flag enabled={'True' if enabled_val else 'False'}"
            return ""
        except Exception:
            return ""

    # Events
    def on_refresh(self, *_):
        entries = self._load_events()
        entries = self._apply_filters(entries)
        self._render(entries)

    def on_user_refresh(self):
        """Refresh initiated by user action (enables dialogs)."""
        try:
            self._user_trigger = True
            self.on_refresh()
        finally:
            self._user_trigger = False

    def set_help_icons_visible(self, show: bool):
        try:
            for icon, kwargs in getattr(self, "_help_icons", []):
                if show:
                    if not icon.winfo_ismapped():
                        icon.pack(**kwargs)
                else:
                    icon.pack_forget()
        except Exception:
            pass

    def on_clear(self):
        try:
            self.key_var.set("")
            self.env_var.set("Any")
            self.on_refresh()
        except Exception:
            pass

    def on_select(self, event=None):
        try:
            sel = self.tree.selection()
            if not sel:
                return
            idx = int(sel[0])
            e = self._history_cache[idx] if idx < len(self._history_cache) else None
            if not e:
                return
            self.preview_text.config(state="normal")
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, json.dumps(e, indent=2))
            self.preview_text.config(state="disabled")
        except Exception:
            pass

    def on_copy_json(self):
        try:
            sel = self.tree.selection()
            if not sel:
                messagebox.showinfo("History", "Select an entry first.")
                return
            idx = int(sel[0])
            e = self._history_cache[idx]
            data = json.dumps(e, indent=2)
            self.parent.clipboard_clear()
            self.parent.clipboard_append(data)
            messagebox.showinfo("History", "JSON copied to clipboard.")
        except Exception:
            pass

    def on_copy_key(self):
        try:
            key = (self.key_var.get() or "").strip()
            if not key:
                messagebox.showinfo("History", "No flag key to copy.")
                return
            self.parent.clipboard_clear()
            self.parent.clipboard_append(key)
            messagebox.showinfo("History", "Flag key copied to clipboard.")
        except Exception:
            pass

    def _on_sort(self, column):
        try:
            if self._sort_key == column:
                self._sort_reverse = not self._sort_reverse
            else:
                self._sort_key = column
                self._sort_reverse = True if column == "ts" else False
            # Update headings label with indicator
            for c, base in self._col_labels.items():
                indicator = ""
                if c == self._sort_key:
                    indicator = " ▼" if self._sort_reverse else " ▲"
                try:
                    self.tree.heading(c, text=base + indicator, command=lambda col=c: self._on_sort(col))
                except Exception:
                    pass
            self.on_refresh()
        except Exception:
            pass
