import os
import json
import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox
import logging

from shared.config_loader import (
    AUDIT_FILE,
)
try:
    from shared.constants import READ_ENVIRONMENT_OPTIONS
except Exception:
    READ_ENVIRONMENT_OPTIONS = ["DEV", "OCRT", "SAT", "PROD"]
 

logger = logging.getLogger(__name__)


class NotificationsTab:
    def __init__(self, parent, history_manager, theme_manager):
        self.parent = parent
        self.history_manager = history_manager
        self.theme_manager = theme_manager
        self.last_payload = None
        # Default sort: newest first by timestamp
        self._sort_key = "ts"
        self._sort_reverse = True
        self.setup_ui()

    def setup_ui(self):
        colors = self.theme_manager.get_theme_config()["colors"]
        root = ttk.Frame(self.parent, padding=30)
        root.pack(fill="both", expand=True)

        # Title
        title = ttk.Label(
            root,
            text="Notifications",
            font=("Segoe UI", 24, "bold"),
            foreground=colors["text"],
        )
        title.pack(anchor="w")

        subtitle = ttk.Label(
            root,
            text="Browse audit history of all actions (Get, Update, Create, Notifications)",
            font=("Segoe UI", 12),
            foreground=colors["text"],
        )
        subtitle.pack(anchor="w", pady=(4, 12))

        # Status panel
        status_card = ttk.Frame(root, style="Content.TFrame", padding=14)
        status_card.pack(fill="x", pady=(0, 14))
        ttk.Label(
            status_card,
            text=f"Audit file: {AUDIT_FILE}",
            font=("Segoe UI", 10),
            foreground=colors["text"],
        ).pack(anchor="w")

        # Selection/result line
        self.result_var = tk.StringVar(value="")
        ttk.Label(root, textvariable=self.result_var, font=("Segoe UI", 10), foreground=colors["text"]).pack(anchor="w", pady=(6, 0))

        # (Dry-run testing UI removed)

        # History panel
        history_card = ttk.Frame(root, style="Content.TFrame", padding=10)
        history_card.pack(fill="both", expand=True, pady=(8, 0))
        ttk.Label(history_card, text="History (Most recent first)", font=("Segoe UI", 10, "bold"), foreground=colors["text"]).pack(anchor="w")

        # Filters row
        filters = ttk.Frame(history_card)
        filters.pack(fill="x", pady=(6, 6))
        ttk.Label(filters, text="Key:", font=("Segoe UI", 10), foreground=colors["text"]).pack(side="left")
        self.filter_key_var = tk.StringVar()
        ttk.Entry(filters, textvariable=self.filter_key_var, width=24).pack(side="left", padx=(6, 12))
        ttk.Label(filters, text="Env:", font=("Segoe UI", 10), foreground=colors["text"]).pack(side="left")
        self.filter_env_var = tk.StringVar(value="Any")
        env_opts = ["Any"] + READ_ENVIRONMENT_OPTIONS
        ttk.Combobox(filters, textvariable=self.filter_env_var, values=env_opts, state="readonly", width=10).pack(side="left", padx=(6, 12))
        ttk.Label(filters, text="Transport:", font=("Segoe UI", 10), foreground=colors["text"]).pack(side="left")
        self.filter_transport_var = tk.StringVar(value="Any")
        ttk.Combobox(filters, textvariable=self.filter_transport_var, values=["Any", "dry_run", "graph"], state="readonly", width=10).pack(side="left", padx=(6, 12))
        self.filter_ok_only = tk.BooleanVar(value=False)
        ttk.Checkbutton(filters, text="OK only", variable=self.filter_ok_only, bootstyle="round-toggle").pack(side="left", padx=(4, 12))
        ttk.Label(filters, text="Type:", font=("Segoe UI", 10), foreground=colors["text"]).pack(side="left", padx=(12, 0))
        self.filter_type_var = tk.StringVar(value="Any")
        ttk.Combobox(filters, textvariable=self.filter_type_var, values=["Any", "feature_flag_change", "get_flag", "update_flag", "create_flag"], state="readonly", width=14).pack(side="left", padx=(6, 12))
        ttk.Button(filters, text="Refresh", width=10, command=self.on_refresh_history).pack(side="left")
        ttk.Button(filters, text="Clear Filters", width=12, command=self.on_clear_filters).pack(side="left", padx=(8, 0))

        # Treeview for history
        tree_frame = ttk.Frame(history_card)
        tree_frame.pack(fill="both", expand=True)
        cols = ("ts", "type", "feature_key", "environment", "enabled", "transport", "ok", "user", "ticket")
        self.history_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=12)
        col_defs = (
            ("ts", "Time", 180),
            ("type", "Type", 110),
            ("feature_key", "Key", 180),
            ("environment", "Env", 80),
            ("enabled", "Enabled", 70),
            ("transport", "Mode", 90),
            ("ok", "OK", 50),
            ("user", "User", 120),
            ("ticket", "Ticket", 140),
        )
        # Store base labels for sort indicator toggling
        self._col_labels = {c: t for c, t, _ in col_defs}
        for c, text, w in col_defs:
            self.history_tree.heading(c, text=text, command=lambda col=c: self._on_sort(col))
            self.history_tree.column(c, width=w, anchor="w")
        yscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=yscroll.set)
        self.history_tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")
        self.history_tree.bind("<<TreeviewSelect>>", self.on_history_select)

        # Copy actions
        copy_row = ttk.Frame(history_card)
        copy_row.pack(fill="x", pady=(6, 0))
        ttk.Button(copy_row, text="Copy HTML", width=14, command=self.on_copy_html).pack(side="left")
        ttk.Button(copy_row, text="Copy JSON", width=14, command=self.on_copy_json).pack(side="left", padx=(8, 0))

        # Preview area (read-only)
        preview_card = ttk.Frame(root, style="Content.TFrame", padding=10)
        preview_card.pack(fill="both", expand=True, pady=(8, 0))
        ttk.Label(preview_card, text="Preview", font=("Segoe UI", 10, "bold"), foreground=colors["text"]).pack(anchor="w")
        # Preview toolbar actions
        preview_toolbar = ttk.Frame(preview_card)
        preview_toolbar.pack(anchor="w", pady=(4, 6))
        ttk.Button(preview_toolbar, text="Copy Flag Name", width=16, command=self.on_copy_flag_name).pack(side="left")
        self.preview_text = tk.Text(
            preview_card,
            height=12,
            font=("Consolas", 10),
            wrap="word",
            state="disabled",
            bg=self.theme_manager.get_theme_config()["colors"]["background"],
            fg=self.theme_manager.get_theme_config()["colors"]["text"],
            bd=0,
            highlightthickness=0,
            relief="flat",
        )
        self.preview_text.pack(fill="both", expand=True)

        # Initial load
        try:
            self.on_refresh_history()
        except Exception:
            pass

    def _update_preview(self, content: str):
        try:
            self.preview_text.config(state="normal")
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, content)
            self.preview_text.config(state="disabled")
        except Exception:
            pass

    # --- History helpers ---
    def _load_history(self):
        entries = []
        try:
            path = AUDIT_FILE
            if not path or not os.path.exists(path):
                return []
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        # Normalize keys
                        obj.setdefault("type", obj.get("type", ""))
                        obj.setdefault("feature_key", obj.get("feature_key", obj.get("key", "")))
                        obj.setdefault("environment", obj.get("environment", ""))
                        obj.setdefault("enabled", obj.get("enabled", None))
                        # Some entries may not be notifications; default transport to "-"
                        obj.setdefault("transport", obj.get("transport", "-"))
                        obj.setdefault("ok", obj.get("ok", True))
                        obj.setdefault("ticket", obj.get("ticket", ""))
                        obj.setdefault("user", obj.get("user", ""))
                        entries.append(obj)
                    except Exception:
                        continue
        except Exception:
            return entries
        return entries

    def _apply_filters(self, entries):
        keyf = (self.filter_key_var.get() or "").strip().lower()
        envf = self.filter_env_var.get()
        transf = self.filter_transport_var.get()
        typef = self.filter_type_var.get()
        ok_only = bool(self.filter_ok_only.get())
        out = []
        for e in entries:
            if keyf and keyf not in str(e.get("feature_key", "")).lower():
                continue
            if envf and envf != "Any" and e.get("environment") != envf:
                continue
            if transf and transf != "Any" and e.get("transport") != transf:
                continue
            if typef and typef != "Any" and e.get("type") != typef:
                continue
            if ok_only and not bool(e.get("ok", True)):
                continue
            out.append(e)
        # Sort by chosen column
        key = self._sort_key or "ts"
        rev = bool(self._sort_reverse)
        try:
            if key in ("enabled", "ok"):
                out.sort(key=lambda x: bool(x.get(key, False)), reverse=rev)
            else:
                out.sort(key=lambda x: str(x.get(key, "")), reverse=rev)
        except Exception:
            # Fallback sort by ts desc
            out.sort(key=lambda x: x.get("ts", ""), reverse=True)
        return out

    def _on_sort(self, column):
        try:
            # Toggle sort order if the same column, else set new col with default desc for ts, asc otherwise
            if self._sort_key == column:
                self._sort_reverse = not self._sort_reverse
            else:
                self._sort_key = column
                self._sort_reverse = True if column == "ts" else False
            # Update headings to show sort indicator
            for c, base in self._col_labels.items():
                indicator = ""
                if c == self._sort_key:
                    indicator = " ▼" if self._sort_reverse else " ▲"
                try:
                    self.history_tree.heading(c, text=base + indicator, command=lambda col=c: self._on_sort(col))
                except Exception:
                    pass
            # Re-render with new sort
            self.on_refresh_history()
        except Exception:
            pass

    def _render_history(self, entries):
        try:
            # Clear existing
            for iid in self.history_tree.get_children():
                self.history_tree.delete(iid)
            # Populate
            for idx, e in enumerate(entries):
                values = (
                    e.get("ts", ""),
                    e.get("type", ""),
                    e.get("feature_key", ""),
                    e.get("environment", ""),
                    "True" if e.get("enabled") else "False",
                    e.get("transport", ""),
                    "True" if e.get("ok", True) else "False",
                    e.get("user", ""),
                    e.get("ticket", ""),
                )
                self.history_tree.insert("", "end", iid=str(idx), values=values)
            # Store for selection lookup
            self._history_cache = entries
        except Exception:
            pass

    def on_refresh_history(self, *_):
        entries = self._load_history()
        entries = self._apply_filters(entries)
        self._render_history(entries)

    def on_clear_filters(self):
        try:
            self.filter_key_var.set("")
            self.filter_env_var.set("Any")
            self.filter_transport_var.set("Any")
            self.filter_ok_only.set(False)
            self.filter_type_var.set("Any")
            self.on_refresh_history()
        except Exception:
            pass

    def on_history_select(self, event=None):
        try:
            sel = self.history_tree.selection()
            if not sel:
                return
            idx = int(sel[0])
            e = self._history_cache[idx] if hasattr(self, "_history_cache") and idx < len(self._history_cache) else None
            if not e:
                return
            if e.get("html"):
                self._update_preview(e.get("html", ""))
            else:
                # Show JSON pretty for non-notify events
                try:
                    self.preview_text.config(state="normal")
                    self.preview_text.delete(1.0, tk.END)
                    self.preview_text.insert(1.0, json.dumps(e, indent=2))
                    self.preview_text.config(state="disabled")
                except Exception:
                    pass
            self.result_var.set(f"Selected: {e.get('type','')} {e.get('feature_key','')} @ {e.get('ts','')}")
        except Exception:
            pass

    def on_copy_html(self):
        try:
            sel = self.history_tree.selection()
            if not sel:
                messagebox.showinfo("Notifications", "Select an entry first.")
                return
            idx = int(sel[0])
            e = self._history_cache[idx]
            html = e.get("html") or ""
            if not html:
                messagebox.showinfo("Notifications", "Selected entry has no HTML content.")
                return
            self.parent.clipboard_clear()
            self.parent.clipboard_append(html)
            messagebox.showinfo("Notifications", "HTML copied to clipboard.")
        except Exception:
            pass

    def on_copy_json(self):
        try:
            sel = self.history_tree.selection()
            if not sel:
                messagebox.showinfo("Notifications", "Select an entry first.")
                return
            idx = int(sel[0])
            e = self._history_cache[idx]
            data = json.dumps(e, indent=2)
            self.parent.clipboard_clear()
            self.parent.clipboard_append(data)
            messagebox.showinfo("Notifications", "JSON copied to clipboard.")
        except Exception:
            pass

    def on_copy_flag_name(self):
        try:
            sel = self.history_tree.selection()
            if not sel:
                messagebox.showinfo("Notifications", "Select an entry first.")
                return
            idx = int(sel[0])
            e = self._history_cache[idx]
            key = e.get("feature_key") or ""
            if not key:
                messagebox.showinfo("Notifications", "Selected entry has no feature key.")
                return
            self.parent.clipboard_clear()
            self.parent.clipboard_append(key)
            messagebox.showinfo("Notifications", "Feature key copied to clipboard.")
        except Exception:
            pass
