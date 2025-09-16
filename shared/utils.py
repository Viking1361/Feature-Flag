"""
Shared Utilities
Common utility functions used across multiple tabs
"""

import base64
import json
import os
from urllib.parse import urlparse, parse_qs
from tkinter import messagebox

def convert_string_to_base64_string(input_string):
    """Convert string to base64 encoded string"""
    return base64.b64encode(input_string.encode()).decode()

def validate_numeric_input(widget, event):
    """Validate numeric input for a widget"""
    new_value = widget.get()
    if not new_value.isdigit():
        widget.set(''.join(filter(str.isdigit, new_value)))

def validate_required_fields(fields, field_names):
    """
    Validate that required fields are not empty
    
    Args:
        fields: dict of field values
        field_names: list of required field names
    
    Returns:
        tuple: (is_valid, missing_fields)
    """
    missing_fields = []
    for field_name in field_names:
        if not fields.get(field_name, "").strip():
            missing_fields.append(field_name)
    
    return len(missing_fields) == 0, missing_fields

def show_validation_error(missing_fields):
    """Show validation error message"""
    field_list = ", ".join(missing_fields)
    messagebox.showwarning(
        "Validation Error", 
        f"The following fields are required: {field_list}"
    )

def show_success_message(title, message):
    """Show success message"""
    messagebox.showinfo(title, message)

def show_error_message(title, message):
    """Show error message"""
    messagebox.showerror(title, message)

def show_warning_message(title, message):
    """Show warning message"""
    messagebox.showwarning(title, message)

def parse_url_parameters(url):
    """Parse URL and extract parameters"""
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        return parsed_url, query_params
    except Exception as e:
        return None, None

def create_app_context(pmc_id, site_id):
    """Create app context JSON and convert to base64"""
    context = {"pmcId": pmc_id, "siteId": site_id}
    context_json = json.dumps(context)
    return convert_string_to_base64_string(context_json)

def format_api_response(response_data):
    """Format API response for display"""
    if isinstance(response_data, dict):
        return json.dumps(response_data, indent=2)
    else:
        return str(response_data)

def safe_file_operation(operation, file_path, *args, **kwargs):
    """
    Safely perform file operations with error handling
    
    Args:
        operation: function to perform
        file_path: path to file
        *args, **kwargs: arguments for operation
    
    Returns:
        tuple: (success, result_or_error)
    """
    try:
        result = operation(file_path, *args, **kwargs)
        return True, result
    except Exception as e:
        return False, str(e)

def read_file_safe(file_path, encoding='utf-8'):
    """Safely read file content"""
    success, result = safe_file_operation(
        lambda path, enc: open(path, 'r', encoding=enc).read(),
        file_path, encoding
    )
    return success, result

def write_file_safe(file_path, content, encoding='utf-8'):
    """Safely write file content"""
    success, result = safe_file_operation(
        lambda path, cont, enc: open(path, 'w', encoding=enc).write(cont),
        file_path, content, encoding
    )
    return success, result

def file_exists_safe(file_path):
    """Safely check if file exists"""
    try:
        return os.path.exists(file_path)
    except Exception:
        return False

def get_file_size_safe(file_path):
    """Safely get file size"""
    try:
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        return 0
    except Exception:
        return 0

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def sanitize_filename(filename):
    """Sanitize filename for safe file operations"""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Ensure filename is not empty
    if not filename:
        filename = "untitled"
    
    return filename

def truncate_text(text, max_length=100):
    """Truncate text to specified length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def format_timestamp(timestamp):
    """Format timestamp for display"""
    try:
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(timestamp)

def create_unique_filename(base_path, filename):
    """Create unique filename to avoid conflicts"""
    if not os.path.exists(os.path.join(base_path, filename)):
        return filename
    
    name, ext = os.path.splitext(filename)
    counter = 1
    
    while True:
        new_filename = f"{name}_{counter}{ext}"
        if not os.path.exists(os.path.join(base_path, new_filename)):
            return new_filename
        counter += 1 