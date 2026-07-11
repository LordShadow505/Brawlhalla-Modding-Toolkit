"""
Color picker wrapper — usa ctk_color_picker (CTkToplevel modal nativo).
Interfaz única para todo el programa: ask_color(parent, initial_hex) -> "#rrggbb" | None
"""
from src.utils import get_project_root
import sys
from pathlib import Path

# Añadir el path del ctk_color_picker al sys.path una sola vez
_CTK_PICKER_PATH = get_project_root() / "resources" / "tools"
if str(_CTK_PICKER_PATH) not in sys.path:
    sys.path.insert(0, str(_CTK_PICKER_PATH))

try:
    from ctk_color_picker import askcolor as _ctk_askcolor
    _HAS_CTK_PICKER = True
except ImportError as e:
    print(f"[ColorPicker] ctk_color_picker not available: {e}")
    _HAS_CTK_PICKER = False


def _resolve_parent(obj):
    """
    Devuelve un widget Tk/Toplevel válido a partir de cualquier objeto.

    Estrategia:
      1. Si el objeto YA tiene winfo_toplevel (es un widget Tk), usarlo.
      2. Si tiene .parent (ToolModule / patrón delegado), intentar con ese.
      3. Si tiene .container, intentar con ese.
      4. Como último recurso, buscar la ventana CTk raíz activa.
    """
    # Paso 1 — el objeto mismo es un widget
    if hasattr(obj, "winfo_toplevel"):
        try:
            top = obj.winfo_toplevel()
            # winfo_toplevel devuelve el objeto mismo si no está en jerarquía
            # aún así vale como master para CTkToplevel
            return top
        except Exception:
            pass

    # Paso 2 — ToolModule u objetos con .parent
    parent_attr = getattr(obj, "parent", None)
    if parent_attr is not None and hasattr(parent_attr, "winfo_toplevel"):
        try:
            return parent_attr.winfo_toplevel()
        except Exception:
            pass

    # Paso 3 — objetos con .container
    container_attr = getattr(obj, "container", None)
    if container_attr is not None and hasattr(container_attr, "winfo_toplevel"):
        try:
            return container_attr.winfo_toplevel()
        except Exception:
            pass

    # Paso 4 — encontrar cualquier ventana CTk/Tk viva
    try:
        import customtkinter as ctk
        for win in ctk.CTk._CTk__default_color_theme_light:  # no funciona
            pass
    except Exception:
        pass

    try:
        import tkinter as tk
        # Buscar entre todas las ventanas Tk registradas
        for name, win in tk._default_root.children.items() if tk._default_root else []:
            return tk._default_root
        if tk._default_root:
            return tk._default_root
    except Exception:
        pass

    # Si todo falla, devolver el objeto original y que CTkToplevel gestione el error
    return obj


def ask_color(parent, initial_hex: str = "#ffffff") -> str | None:
    """
    Abre el color picker modal centrado sobre 'parent'.
    Devuelve el hex seleccionado (ej: '#ff5733') o None si se canceló.
    """
    master = _resolve_parent(parent)

    if _HAS_CTK_PICKER:
        try:
            return _ctk_askcolor(master=master, initial=initial_hex)
        except Exception as e:
            print(f"[ColorPicker] Error: {e}")
            # Fallback con un None master
            try:
                return _ctk_askcolor(master=None, initial=initial_hex)
            except Exception:
                pass

    # Fallback mínimo con tkinter colorchooser
    try:
        from tkinter import colorchooser
        result = colorchooser.askcolor(color=initial_hex, title="Color")
        if result and result[1]:
            return result[1]
    except Exception:
        pass
    return None


def ask_color_from_rgb(parent, r: int, g: int, b: int) -> tuple[int, int, int] | None:
    """
    Versión que acepta y devuelve tuplas RGB (0-255).
    """
    initial_hex = f"#{r:02x}{g:02x}{b:02x}"
    result = ask_color(parent, initial_hex)
    if result:
        h = result.lstrip("#")
        if len(h) == 6:
            return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return None
