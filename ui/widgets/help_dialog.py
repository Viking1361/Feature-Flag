import tkinter as tk
import ttkbootstrap as ttk

class HelpDialog(tk.Toplevel):
    def __init__(self, parent, title: str, about: str, examples: list[str] | None = None, anchor_widget=None):
        super().__init__(parent)
        self.title(f"Help - {title}")
        self.transient(parent)
        self.resizable(True, True)
        # Set initial size and center on parent/screen
        width, height = 520, 360
        try:
            self.update_idletasks()
            if anchor_widget is not None:
                ax = anchor_widget.winfo_rootx()
                ay = anchor_widget.winfo_rooty()
                ah = anchor_widget.winfo_height()
                x = ax
                y = ay + ah + 8
            else:
                px = parent.winfo_rootx()
                py = parent.winfo_rooty()
                pw = parent.winfo_width()
                ph = parent.winfo_height()
                if pw <= 1 or ph <= 1:
                    raise Exception("parent size not ready")
                x = px + (pw - width) // 2
                y = py + (ph - height) // 2
        except Exception:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            x = (sw - width) // 2
            y = (sh - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.configure(bg=parent.cget("bg") if hasattr(parent, 'cget') else None)
        try:
            self.grab_set()
        except Exception:
            pass

        container = ttk.Frame(self, padding=14)
        container.pack(fill="both", expand=True)

        header = ttk.Label(container, text=title, font=("Segoe UI", 14, "bold"))
        header.pack(anchor="w")

        notebook = ttk.Notebook(container)
        notebook.pack(fill="both", expand=True, pady=(8, 10))

        about_frame = ttk.Frame(notebook)
        notebook.add(about_frame, text="About")
        about_txt = tk.Text(
            about_frame,
            wrap="word",
            height=8,
            font=("Segoe UI", 10),
            state="normal",
            bd=0,
            relief="flat",
        )
        about_txt.insert("1.0", about or "")
        about_txt.config(state="disabled")
        about_txt.pack(fill="both", expand=True, padx=6, pady=6)

        examples_frame = ttk.Frame(notebook)
        notebook.add(examples_frame, text="Examples")
        examples_txt = tk.Text(
            examples_frame,
            wrap="word",
            height=8,
            font=("Consolas", 10),
            state="normal",
            bd=0,
            relief="flat",
        )
        if examples:
            content = "\n".join(f"- {ex}" for ex in examples)
        else:
            content = "No examples available."
        examples_txt.insert("1.0", content)
        examples_txt.config(state="disabled")
        examples_txt.pack(fill="both", expand=True, padx=6, pady=6)

        btns = ttk.Frame(container)
        btns.pack(fill="x")
        close_btn = ttk.Button(btns, text="Close", width=12, command=self.destroy)
        close_btn.pack(side="right")

        # ESC to close
        self.bind("<Escape>", lambda e: self.destroy())
