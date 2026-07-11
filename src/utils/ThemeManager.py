from src.utils import get_project_root
import tkinter as tk
import customtkinter as ctk
from pathlib import Path
from PIL import Image

class BMTTheme:
    _icons_cache = {}
    
    # --- Color Palette (Provided by User) ---
    BLACK = "#000000"
    WHITE = "#ffffff"
    GREEN = "#32c12c"
    TEAL = "#009888"
    INDIGO = "#3e49bb"
    BLUE = "#526eff"
    PURPLE = "#7f4fc9"
    LIME = "#87c735"
    ACID_GREEN = "#cde000"
    SKY_BLUE = "#00a5f9"
    CYAN = "#00bcd9"
    DEEP_PURPLE = "#682cbf"
    YELLOW = "#ffef00"
    ORANGE = "#ff9a00"
    DEEP_ORANGE = "#e34c22"
    BROWN = "#7c5547"
    BLUE_GREY = "#5f7d8e"
    GOLDEN_YELLOW = "#ffcd00"
    BRIGHT_ORANGE = "#ff5500"
    RED = "#d40c00"
    DARK_BROWN = "#50342c"
    GREY = "#9e9e9e"

    # --- UI Backgrounds (Keeping user's dark theme) ---
    BG_DARK = "#0E0E0E"
    BG_PANEL = "#171717"
    BG_SUBPANEL = "#2C2C2C"
    
    # --- Component Constants ---
    CORNER_RADIUS = 8
    BORDER_WIDTH = 1

    # --- Font Helper ---
    @staticmethod
    def get_font(size=12, weight="normal"):
        return ctk.CTkFont(family="Roboto", size=size, weight=weight)
        
    @classmethod
    def get_icon(cls, name, size=24):
        """Loads and caches an icon from resources/assets/IconsNew. 
           Name should match the prefix of the filename (e.g. 'add' for 'add_24dp_...').
           If size is an integer, it creates a square (size, size).
        """
        if isinstance(size, int):
            size = (size, size)
        cache_key = f"{name}_{size[0]}x{size[1]}"
        if cache_key in cls._icons_cache:
            return cls._icons_cache[cache_key]

        icons_dir = get_project_root() / "resources" / "assets" / "IconsNew"
        
        # Find file matching prefix (e.g., 'add' matches 'add_*.png')
        try:
            matched_file = next(icons_dir.glob(f"{name}_*.png"))
        except StopIteration:
            print(f"[ThemeManager] Warning: Icon '{name}' not found in IconsNew.")
            return None
            
        try:
            img = Image.open(matched_file).convert("RGBA")
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
            cls._icons_cache[cache_key] = ctk_img
            return ctk_img
        except Exception as e:
            print(f"[ThemeManager] Error loading icon '{name}': {e}")
            return None

    # --- Styling Helpers ---
    @staticmethod
    def style_primary_button(button, color=BLUE_GREY):
        button.configure(
            fg_color=color,
            hover_color=BMTTheme.adjust_brightness(color, -0.2),
            text_color=BMTTheme.WHITE,
            corner_radius=BMTTheme.CORNER_RADIUS,
            font=BMTTheme.get_font(13, "bold")
        )

    @staticmethod
    def style_secondary_button(button):
        button.configure(
            fg_color="transparent",
            border_width=1,
            border_color=BMTTheme.GREY,
            hover_color=BMTTheme.BG_SUBPANEL,
            text_color=BMTTheme.WHITE,
            corner_radius=BMTTheme.CORNER_RADIUS,
            font=BMTTheme.get_font(13)
        )

    @staticmethod
    def style_title(label, color=WHITE):
        label.configure(
            font=BMTTheme.get_font(24, "bold"),
            text_color=color
        )

    @staticmethod
    def style_subtitle(label, color=GREY):
        label.configure(
            font=BMTTheme.get_font(14, "bold"),
            text_color=color
        )

    @staticmethod
    def style_log_text(textbox):
        textbox.configure(
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=BMTTheme.BLACK,
            text_color=BMTTheme.WHITE,
            border_width=1,
            border_color=BMTTheme.BG_SUBPANEL
        )

    @staticmethod
    def adjust_brightness(hex_color, factor):
        """Simple helper to darken/lighten colors for hover effects."""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        new_rgb = [max(0, min(255, int(c * (1 + factor)))) for c in rgb]
        return '#{:02x}{:02x}{:02x}'.format(*new_rgb)

# --- Module Accent Mapping ---
ACCENTS = {
    "Skin Editor": BMTTheme.GOLDEN_YELLOW,
    "Reference Loader": BMTTheme.DEEP_PURPLE,
    "Sprite Exporter": BMTTheme.SKY_BLUE,
    "Color Swapper": BMTTheme.INDIGO,
    "Skin Changer": BMTTheme.DEEP_ORANGE,
    "Skin Changer Pro": BMTTheme.RED,
    "Color Converter": BMTTheme.TEAL,
    "Fast Shape Replacer": BMTTheme.DEEP_ORANGE,
    "Mod Source Manager": BMTTheme.BLUE_GREY,
    "Lang Editor": BMTTheme.GREEN,
    "SVG Maker": BMTTheme.LIME,
}

# ═══════════════════════════════════════════════════════════════════════
#  CUSTOM TOOLTIP WITH ACCENT BAR
# ═══════════════════════════════════════════════════════════════════════
class BMTToolTip:
    def __init__(self, widget, text, accent_color=BMTTheme.BLUE_GREY, warning=None):
        self.widget = widget
        self.text = text
        self.accent_color = accent_color
        self.warning = warning
        self.tip_window = None
        
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
            
        # Get coordinates to place the tooltip to the RIGHT of the widget
        try:
            x = self.widget.winfo_rootx() + self.widget.winfo_width() + 10
            y = self.widget.winfo_rooty() + (self.widget.winfo_height() // 2) - 20
        except Exception:
            return # Widget might have been destroyed
        
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)
        
        # Main frame with accent border
        bg_color = "#1A1A1A"
        main_frame = tk.Frame(tw, bg="#333333", padx=1, pady=1) # Dark grey border
        main_frame.pack()
        
        content_frame = tk.Frame(main_frame, bg=bg_color)
        content_frame.pack()
        
        # Left Accent bar
        tk.Frame(content_frame, bg=self.accent_color, width=4).pack(side="left", fill="y")
        
        # Text container
        text_frame = tk.Frame(content_frame, bg=bg_color, padx=12, pady=10)
        text_frame.pack(side="left", fill="both", expand=True)
        
        # Description
        tk.Label(
            text_frame, text=self.text, justify="left",
            font=("Roboto", 10), fg="#DDDDDD", bg=bg_color,
            wraplength=280
        ).pack(anchor="w")
        
        # Warning if present
        if self.warning:
            tk.Label(
                text_frame, text=f"⚠ {self.warning}", justify="left",
                font=("Roboto", 9, "bold"), fg="#FFB300", bg=bg_color,
                wraplength=280
            ).pack(anchor="w", pady=(8, 0))

        # Ensure the tooltip doesn't steal focus or capture mouse
        tw.bind("<Enter>", lambda e: self.hide_tip()) # Hide if cursor somehow enters tooltip

    def hide_tip(self, event=None):
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except Exception:
                pass
            self.tip_window = None
