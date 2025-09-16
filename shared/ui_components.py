"""
Shared UI Components
Reusable UI components used across multiple tabs
"""

import tkinter as tk
import ttkbootstrap as ttk

class CardFrame:
    """Reusable card-style frame component"""
    
    def __init__(self, parent, title, subtitle=None, padding=25):
        self.parent = parent
        self.title = title
        self.subtitle = subtitle
        self.padding = padding
        self.frame = None
        self.create_card()
    
    def create_card(self):
        """Create a card-style frame with header"""
        # Main card frame
        self.frame = ttk.Frame(self.parent, style="Card.TFrame")
        self.frame.pack(fill="x", padx=5)
        
        # Card header
        header = ttk.Frame(self.frame)
        header.pack(fill="x", padx=self.padding, pady=(20, 15))
        
        # Title
        title_label = ttk.Label(
            header,
            text=self.title,
            font=("Segoe UI", 16, "bold")
        )
        title_label.pack(anchor="w")
        
        # Subtitle (optional)
        if self.subtitle:
            subtitle_label = ttk.Label(
                header,
                text=self.subtitle,
                font=("Segoe UI", 10),
                foreground="gray"
            )
            subtitle_label.pack(anchor="w", pady=(2, 0))
        
        # Content area
        self.content = ttk.Frame(self.frame)
        self.content.pack(fill="x", padx=self.padding, pady=(0, 20))
    
    def get_content_frame(self):
        """Get the content frame for adding widgets"""
        return self.content

class FormField:
    """Reusable form field component"""
    
    def __init__(self, parent, label, field_type="entry", values=None, width=None, height=None, **kwargs):
        self.parent = parent
        self.label_text = label
        self.field_type = field_type
        self.values = values or []
        self.width = width
        self.height = height
        self.kwargs = kwargs
        
        self.frame = None
        self.label = None
        self.field = None
        self.var = None
        
        self.create_field()
    
    def create_field(self):
        """Create the form field"""
        # Field container
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill="x", pady=8)
        
        # Label
        self.label = ttk.Label(
            self.frame,
            text=self.label_text,
            font=("Segoe UI", 11, "bold")
        )
        self.label.pack(anchor="w", pady=(0, 5))
        
        # Field
        if self.field_type == "entry":
            self.var = tk.StringVar()
            self.field = ttk.Entry(
                self.frame,
                textvariable=self.var,
                font=("Segoe UI", 11),
                width=self.width,
                **self.kwargs
            )
        elif self.field_type == "combobox":
            self.var = tk.StringVar()
            self.field = ttk.Combobox(
                self.frame,
                textvariable=self.var,
                values=self.values,
                font=("Segoe UI", 11),
                width=self.width,
                height=self.height or 8,
                **self.kwargs
            )
        elif self.field_type == "checkbox":
            self.var = tk.BooleanVar()
            self.field = ttk.Checkbutton(
                self.frame,
                text=self.label_text,
                variable=self.var,
                **self.kwargs
            )
            # Remove label since checkbox has its own
            self.label.destroy()
            self.label = None
        
        self.field.pack(fill="x", pady=(0, 5))
    
    def get_var(self):
        """Get the field's variable"""
        return self.var
    
    def get_field(self):
        """Get the field widget"""
        return self.field
    
    def get_value(self):
        """Get the current value"""
        if self.field_type == "checkbox":
            return self.var.get()
        else:
            return self.var.get().strip()
    
    def set_value(self, value):
        """Set the field value"""
        self.var.set(value)
    
    def clear(self):
        """Clear the field"""
        if self.field_type == "checkbox":
            self.var.set(False)
        else:
            self.var.set("")

class ActionButtons:
    """Reusable action buttons component"""
    
    def __init__(self, parent, buttons_config):
        """
        buttons_config: list of dicts with keys:
        - text: button text
        - command: button command
        - style: button style (optional)
        - width: button width (optional)
        """
        self.parent = parent
        self.buttons_config = buttons_config
        self.buttons = {}
        
        self.create_buttons()
    
    def create_buttons(self):
        """Create the action buttons"""
        # Container frame
        container = ttk.Frame(self.parent)
        container.pack(fill="x", pady=(0, 25))
        
        # Buttons frame
        buttons_frame = ttk.Frame(container)
        buttons_frame.pack(anchor="w")
        
        # Create buttons
        for i, config in enumerate(self.buttons_config):
            btn = ttk.Button(
                buttons_frame,
                text=config["text"],
                command=config["command"],
                bootstyle=config.get("style", "primary"),
                width=config.get("width", 15)
            )
            
            # Pack with appropriate spacing
            if i == 0:
                btn.pack(side="left", padx=(0, 10))
            else:
                btn.pack(side="left", padx=10)
            
            self.buttons[config["text"]] = btn
    
    def get_button(self, text):
        """Get a specific button by text"""
        return self.buttons.get(text)
    
    def disable_all(self):
        """Disable all buttons"""
        for btn in self.buttons.values():
            btn.config(state="disabled")
    
    def enable_all(self):
        """Enable all buttons"""
        for btn in self.buttons.values():
            btn.config(state="normal")

class StatusDisplay:
    """Reusable status display component"""
    
    def __init__(self, parent, initial_text="Ready"):
        self.parent = parent
        self.initial_text = initial_text
        
        self.status_var = tk.StringVar(value=initial_text)
        self.result_label = None
        
        self.create_display()
    
    def create_display(self):
        """Create the status display"""
        # Status label
        self.status_label = ttk.Label(
            self.parent,
            textvariable=self.status_var,
            font=("Segoe UI", 11, "italic")
        )
        self.status_label.pack(pady=10)
        
        # Result label
        self.result_label = ttk.Label(
            self.parent,
            text="",
            wraplength=700,
            font=("Segoe UI", 11)
        )
        self.result_label.pack(pady=10, fill="both", expand=True)
    
    def set_status(self, text):
        """Set status text"""
        self.status_var.set(text)
    
    def set_result(self, text):
        """Set result text"""
        self.result_label.config(text=text)
    
    def clear(self):
        """Clear both status and result"""
        self.status_var.set(self.initial_text)
        self.result_label.config(text="")

class LoadingIndicator:
    """Reusable loading indicator"""
    
    def __init__(self, parent, text="Loading..."):
        self.parent = parent
        self.text = text
        self.is_loading = False
        
        self.loading_var = tk.StringVar()
        self.loading_label = None
        
        self.create_indicator()
    
    def create_indicator(self):
        """Create the loading indicator"""
        self.loading_label = ttk.Label(
            self.parent,
            textvariable=self.loading_var,
            font=("Segoe UI", 11, "bold")
        )
        self.loading_label.pack(pady=10)
    
    def start_loading(self, text=None):
        """Start loading indicator"""
        self.is_loading = True
        self.loading_var.set(text or self.text)
    
    def stop_loading(self):
        """Stop loading indicator"""
        self.is_loading = False
        self.loading_var.set("")
    
    def set_text(self, text):
        """Set loading text"""
        self.loading_var.set(text)

class TwoColumnLayout:
    """Reusable two-column layout component"""
    
    def __init__(self, parent):
        self.parent = parent
        
        self.left_column = ttk.Frame(parent)
        self.left_column.pack(side="left", fill="x", expand=True, padx=(0, 15))
        
        self.right_column = ttk.Frame(parent)
        self.right_column.pack(side="right", fill="x", expand=True, padx=(15, 0))
    
    def get_left_column(self):
        """Get the left column frame"""
        return self.left_column
    
    def get_right_column(self):
        """Get the right column frame"""
        return self.right_column 