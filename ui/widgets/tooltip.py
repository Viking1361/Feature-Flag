import tkinter as tk

class Tooltip:
    def __init__(self, widget, text: str, delay_ms: int = 350):
        self.widget = widget
        self.text = text or ""
        self.delay_ms = delay_ms
        self._after_id = None
        self._tip = None
        self.widget.bind("<Enter>", self._schedule)
        self.widget.bind("<Leave>", self._cancel)

    def _schedule(self, _):
        self._cancel(None)
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _cancel(self, _):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        self._hide()

    def _show(self):
        if not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + 12
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
            self._tip = tk.Toplevel(self.widget)
            self._tip.wm_overrideredirect(True)
            self._tip.wm_attributes("-topmost", True)
            self._tip.geometry(f"+{x}+{y}")
            label = tk.Label(
                self._tip,
                text=self.text,
                justify="left",
                background="#ffffe0",
                relief="solid",
                borderwidth=1,
                font=("Segoe UI", 9),
                padx=6,
                pady=3,
                wraplength=320,
            )
            label.pack()
        except Exception:
            self._hide()

    def _hide(self):
        if self._tip is not None:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None
