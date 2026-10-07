"""
Auxiliary Utilities for Brawlhalla Modding Toolkit
===================================================
Common helper functions used across all modules.
"""

import os
import sys
import json
import threading
import time
import traceback
from pathlib import Path
from functools import wraps

# (Moved ThemeManager import to bottom to prevent circular import)

# ============================================================
# THREAD UTILITIES
# ============================================================

def run_in_thread(func):
    """Decorator to run a function in a daemon thread."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        t = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
        t.start()
        return t
    return wrapper


def debounce(wait_ms):
    """Decorator that debounces a function call (tkinter-safe)."""
    def decorator(func):
        @wraps(func)
        def wrapper(self_or_widget, *args, **kwargs):
            attr_name = f"_debounce_id_{func.__name__}"
            widget = self_or_widget
            if hasattr(widget, 'container') and widget.container:
                after_widget = widget.container
            elif hasattr(widget, 'after'):
                after_widget = widget
            else:
                return func(self_or_widget, *args, **kwargs)
            
            prev_id = getattr(self_or_widget, attr_name, None)
            if prev_id is not None:
                try:
                    after_widget.after_cancel(prev_id)
                except Exception:
                    pass
            
            new_id = after_widget.after(
                wait_ms,
                lambda: func(self_or_widget, *args, **kwargs)
            )
            setattr(self_or_widget, attr_name, new_id)
        return wrapper
    return decorator


# ============================================================
# SAFE UI OPERATIONS
# ============================================================

def safe_widget_op(func):
    """Decorator that catches errors from widget operations on destroyed widgets."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            pass
    return wrapper


def widget_exists(widget):
    """Check if a tkinter/ctk widget still exists and is valid."""
    if widget is None:
        return False
    try:
        return widget.winfo_exists()
    except Exception:
        return False


def safe_after(widget, ms, callback, *args):
    """Schedule a callback only if the widget is still alive."""
    if not widget_exists(widget):
        return None
    try:
        return widget.after(ms, callback, *args)
    except Exception:
        return None


def safe_configure(widget, **kwargs):
    """Configure a widget only if it's still alive."""
    if widget_exists(widget):
        try:
            widget.configure(**kwargs)
        except Exception:
            pass


# ============================================================
# CONFIG HELPERS
# ============================================================

def get_app_config_dir():
    """Returns the app config directory in APPDATA (creates if needed)."""
    app_folder = os.path.join(os.getenv("APPDATA", ""), "Brawlhalla Modding Toolkit")
    os.makedirs(app_folder, exist_ok=True)
    return app_folder


def load_json_config(filename):
    """Load a JSON config file from the app config directory."""
    filepath = os.path.join(get_app_config_dir(), filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARNING] Failed to load config {filename}: {e}")
    return {}


def save_json_config(filename, data):
    """Save a dict as JSON config file in the app config directory."""
    filepath = os.path.join(get_app_config_dir(), filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[WARNING] Failed to save config {filename}: {e}")
        return False


# ============================================================
# PATH HELPERS
# ============================================================

def get_project_root():
    """Returns the project root directory (works both in dev and compiled exe)."""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller
        return Path(sys._MEIPASS)
    else:
        # Development & Nuitka (Nuitka preserves __file__ to point to the unpacked temp directory)
        return Path(__file__).parent.parent.parent


def get_assets_path():
    """Returns the path to resources/assets/frame0."""
    return get_project_root() / "resources" / "assets" / "frame0"


def get_resources_path():
    """Returns the path to resources/."""
    return get_project_root() / "resources"


# ============================================================
# LOGGING
# ============================

class SimpleLogger:
    """Simple thread-safe logger that can write to a CTkTextbox widget."""
    def __init__(self, textbox_widget=None):
        self._textbox = textbox_widget
        self._lock = threading.Lock()
    
    def set_textbox(self, textbox_widget):
        self._textbox = textbox_widget
    
    def log(self, message, level="INFO"):
        formatted = f"[{level}] {message}"
        print(formatted)
        if self._textbox and widget_exists(self._textbox):
            try:
                self._textbox.after(0, lambda: self._append_to_textbox(formatted))
            except Exception:
                pass
    
    def _append_to_textbox(self, text):
        if self._textbox and widget_exists(self._textbox):
            try:
                self._textbox.insert("end", text + "\n")
                self._textbox.see("end")
            except Exception:
                pass
    
    def info(self, message): self.log(message, "INFO")
    def warning(self, message): self.log(message, "WARNING")
    def error(self, message): self.log(message, "ERROR")
    def ok(self, message): self.log(message, "OK")


# ============================================================
# IMAGE HELPERS
# ============================================================

def create_placeholder_image(size, color="#2C2C2C"):
    """Create a solid-color placeholder PIL Image."""
    try:
        from PIL import Image
        return Image.new("RGBA", size, color)
    except ImportError:
        return None


def load_and_fit_image(path, target_size, background_color=(0, 0, 0, 0)):
    """Load an image, resize to fit within target_size keeping aspect ratio."""
    try:
        from PIL import Image
        img = Image.open(path).convert("RGBA")
        img.thumbnail(target_size, Image.LANCZOS)
        bg = Image.new("RGBA", target_size, background_color)
        paste_x = (target_size[0] - img.width) // 2
        paste_y = (target_size[1] - img.height) // 2
        bg.paste(img, (paste_x, paste_y), img)
        return bg
    except Exception:
        return create_placeholder_image(target_size)


# ============================================================
# LAZY LOADER FOR EXTERNAL MODULES
# ============================================================

class LazyModuleLoader:
    """Loads Python modules from external .pyc/.pyd files at runtime."""
    def __init__(self, modules_dir):
        self.modules_dir = Path(modules_dir)
    
    def load(self, module_name):
        import importlib.util
        extensions = [".pyd", ".pyc", ".py"]
        for ext in extensions:
            module_path = self.modules_dir / f"{module_name}{ext}"
            if module_path.exists():
                try:
                    spec = importlib.util.spec_from_file_location(module_name, str(module_path))
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        return module
                except Exception as e:
                    print(f"[ERROR] Failed to load {module_name}: {e}")
        return None

# Export BMTTheme and ACCENTS from here for convenience
from .ThemeManager import BMTTheme, ACCENTS
