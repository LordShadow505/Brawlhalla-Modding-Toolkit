"""
Brawlhalla Modding Toolkit - Dashboard Unificado
Integra todas las herramientas de modding en una sola interfaz intuitiva
"""

import json
import sys
import os
import io
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import font as tkfont
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw

# ── SVG renderer utility ─────────────────────────────────────────────
from src.svg_utils import render_svg, HAS_CAIROSVG, HAS_RESVG

# Build configuration - controls which tools appear
from build_config import ENABLED_TOOLS, APP_NAME, APP_VERSION, ALLOW_LIGHT_MODE
from src.utils import get_app_config_dir, load_json_config, save_json_config
from src.utils.ThemeManager import BMTTheme, ACCENTS, BMTToolTip
from src.svg_utils import render_svg

# ============================================================
# LAZY IMPORTS: Only import enabled modules to avoid loading
# unnecessary code and prevent decompilation of unused modules.
# Each module is imported directly from its own file.
# ============================================================
_module_classes = {}

if ENABLED_TOOLS.get("Sprite Exporter", False):
    from src.modules.SpriteExporterModule import SpriteExporterModule
    _module_classes["Sprite Exporter"] = SpriteExporterModule

if ENABLED_TOOLS.get("Mod Source Manager", False):
    from src.modules.ModSourceManagerModule import ModSourceManagerModule
    _module_classes["Mod Source Manager"] = ModSourceManagerModule

if ENABLED_TOOLS.get("Color Swapper", False):
    from src.modules.ColorSwapperModule import ColorSwapperModule
    _module_classes["Color Swapper"] = ColorSwapperModule

if ENABLED_TOOLS.get("Skin Changer", False):
    from src.modules.SkinChangerModule import SkinChangerModule
    _module_classes["Skin Changer"] = SkinChangerModule

if ENABLED_TOOLS.get("Skin Changer Pro", False):
    from src.modules.SkinChangerProModule import SkinChangerProModule
    _module_classes["Skin Changer Pro"] = SkinChangerProModule

if ENABLED_TOOLS.get("Reference Loader", False):
    from src.modules.ReferenceLoaderModule import ReferenceLoaderModule
    _module_classes["Reference Loader"] = ReferenceLoaderModule

if ENABLED_TOOLS.get("Color Converter", False):
    from src.modules.ColorConverterModule import ColorConverterModule
    _module_classes["Color Converter"] = ColorConverterModule

if ENABLED_TOOLS.get("Fast Shape Replacer", False):
    from src.modules.FastShapeReplacerModule import FastShapeReplacerModule
    _module_classes["Fast Shape Replacer"] = FastShapeReplacerModule

if ENABLED_TOOLS.get("Skin Editor", False):
    from src.modules.SkinEditorModule import SkinEditorModule
    _module_classes["Skin Editor"] = SkinEditorModule

if ENABLED_TOOLS.get("Lang Editor", False):
    from src.modules.LangEditorModule import LangEditorModule
    _module_classes["Lang Editor"] = LangEditorModule

if ENABLED_TOOLS.get("SVG Maker", False):
    from src.modules.SVGMakerModule import SVGMakerModule
    _module_classes["SVG Maker"] = SVGMakerModule




# ═══════════════════════════════════════════════════════════════════════
#  HOURGLASS ANIMATION HELPERS
# ═══════════════════════════════════════════════════════════════════════
def _load_spinner_frames(cursors_path, size=(48, 48)):
    """Load busy_circle_fade.svg and create 12 rotated frames."""
    svg_path = cursors_path / "busy_circle_fade.svg"
    frames = []
    base_img = None
    if svg_path.exists():
        try:
            svg_text = svg_path.read_text(encoding="utf-8")
            base_img = render_svg(svg_text, size)
        except Exception:
            pass
            
    if base_img is None:
        # fallback
        w, h = size
        base_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(base_img)
        d.arc([4, 4, w-4, h-4], 0, 270, fill=(200, 200, 200, 255), width=4)
        
    for i in range(12):
        angle = i * -30  # rotate clockwise
        rotated = base_img.rotate(angle, resample=Image.BICUBIC)
        frames.append(rotated)
    return frames


class BrawlhallaModdingToolkit(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Hide main window during splash loading
        self.withdraw()
        
        # Performance/HighDPI Best Practices (Context7)
        if sys.platform.startswith("win"):
            ctk.deactivate_automatic_dpi_awareness()
            
        ctk.set_appearance_mode("Dark")
        self.title(APP_NAME)
        
        # Variables globales
        self.gamePathString = ""
        self.modsPathString = ""
        self.current_tool = None
        self.current_module = None
        self._module_cache = {}  # {tool_name: module_instance} para persistir sesión
        self._loading_overlay = None
        
        # Colores unificados desde ThemeManager
        self.tool_colors = ACCENTS
        
        # Color actual por defecto
        self.current_color = BMTTheme.BLUE_GREY
        
        # Rutas de assets y fonts
        self.assets_path = Path(__file__).parent / "resources" / "assets" / "frame0"
        self.fonts_path = Path(__file__).parent / "resources" / "fonts"
        
        # Show splash and schedule deferred loading
        self._create_splash()
        self.logo_image = None
        self.logo_path = Path(__file__).parent / "resources" / "icons" / "Icon.svg"
        self._after_tasks = [] # Track scheduled tasks to cancel on exit
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(200, self._load_step_fonts)
    
    def on_close(self):
        """Cleanup before closing."""
        print("[INFO] Closing application...")
        self.cancel_all_tasks()
        self.destroy()
        sys.exit(0)
    
    def load_custom_fonts(self):
        """Carga las fuentes personalizadas Roboto"""
        try:
            # Registrar fuentes en tkinter
            roboto_regular = str(self.fonts_path / "Roboto-Regular.ttf")
            roboto_medium = str(self.fonts_path / "Roboto-Medium.ttf")
            roboto_light = str(self.fonts_path / "Roboto-Light.ttf")
            roboto_black = str(self.fonts_path / "Roboto-Black.ttf")
            
            # Crear fuentes customtkinter con Roboto
            self.font_title = ctk.CTkFont(family="Roboto", size=24, weight="bold")
            self.font_subtitle = ctk.CTkFont(family="Roboto", size=16, weight="bold")
            self.font_button = ctk.CTkFont(family="Roboto", size=14, weight="normal")
            self.font_normal = ctk.CTkFont(family="Roboto", size=12, weight="normal")
            self.font_small = ctk.CTkFont(family="Roboto", size=10, weight="normal")
            
            print("[OK] Custom fonts loaded")
        except Exception as e:
            print(f"[WARNING] Could not load custom fonts: {e}")
            # Usar fuentes por defecto
            self.font_title = ctk.CTkFont(size=24, weight="bold")
            self.font_subtitle = ctk.CTkFont(size=16, weight="bold")
            self.font_button = ctk.CTkFont(size=14, weight="normal")
            self.font_normal = ctk.CTkFont(size=12, weight="normal")
            self.font_small = ctk.CTkFont(size=10, weight="normal")
    
    def load_icons(self):
        """Carga los iconos desde assets"""
        self.icons = {}
        self.icons_big = {}

        tool_icons_path = Path(__file__).parent / "resources" / "assets" / "Tool Icons"

        try:
            # Iconos de herramientas desde la carpeta Tool Icons
            tool_icon_mappings = {
                "mod_source_manager": "Mod_Source_Manager_Icon.png",
                "sprite_exporter":    "Sprite_Exporter_Icon.png",
                "color_swapper":      "Color_Swapper_Icon.png",
                "skin_changer":       "Skin_Replacer_Icon.png",
                "skin_changer_pro":   "Skin_Replacer_Icon.png",
                "color_converter":    "Color_Converter_Icon.png",
                "reference_loader":   "Reference_Loader_icon.png",
                "fast_shape_replacer":"Fast_Shape_Replacer.png",
                "skin_editor":        "Skin_Editor_Icon.png",
                "lang_editor":        "Languaje_Editor.png",
                "svg_maker":          "SVG_Maker.png",
            }

            for key, filename in tool_icon_mappings.items():
                icon_path = tool_icons_path / filename
                if icon_path.exists():
                    img = Image.open(icon_path)
                    self.icons[key]     = ctk.CTkImage(img, size=(24, 24))
                    self.icons_big[key] = ctk.CTkImage(img, size=(64, 64))
                else:
                    print(f"[WARNING] Tool icon not found: {filename}")
                    self.icons[key]     = None
                    self.icons_big[key] = None



            # Iconos de UI desde frame0
            ui_icon_mappings = {
                "folder":  "Folder.png",
                "save":    "SaveButtonImage.png",
                "search":  "SearchIcon.png",
                "reload":  "ReloadIcon.png",
                "settings":"Settings.png",
                "home":    "Home.png",
                "sort":    "SortButtonImage.png",
                "add":     "Add.png",
            }

            for key, filename in ui_icon_mappings.items():
                icon_path = self.assets_path / filename
                if icon_path.exists():
                    img = Image.open(icon_path)
                    self.icons[key] = ctk.CTkImage(img, size=(24, 24))
                else:
                    print(f"[WARNING] UI icon not found: {filename}")
                    self.icons[key] = None

            print(f"[OK] Loaded {len(self.icons)} icons")
        except Exception as e:
            print(f"[ERROR] Failed to load icons: {e}")
            self.icons = {}
            self.icons_big = {}

        # Load hourglass frames for tool loading overlay
        try:
            cursors_path = Path(__file__).parent / "resources" / "assets" / "cursors"
            hg_frames = _load_spinner_frames(cursors_path, size=(48, 48))
            self._hourglass_ctk = [
                ctk.CTkImage(light_image=f, dark_image=f, size=(48, 48))
                for f in hg_frames
            ]
        except Exception:
            self._hourglass_ctk = []

    # ═══════════════════════════════════════════════════════════════════
    #  SPLASH SCREEN
    # ═══════════════════════════════════════════════════════════════════
    def _create_splash(self):
        """Create startup splash screen using custom image."""
        self.update_idletasks() # Ensure accurate screen dimensions
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        sp_w, sp_h = int(669 * 1.3), int(450 * 1.3)
        x = (sw - sp_w) // 2
        y = (sh - sp_h) // 2

        self._splash = tk.Toplevel(self)
        self._splash.overrideredirect(True)
        self._splash.geometry(f"{sp_w}x{sp_h}+{x}+{y}")
        
        # Transparent background trick for Windows
        trans_color = "#000001"
        self._splash.configure(bg=trans_color)
        self._splash.attributes("-transparentcolor", trans_color)
        self._splash.attributes("-topmost", True)
        self._splash.protocol("WM_DELETE_WINDOW", lambda: None)

        self._splash_cv = tk.Canvas(self._splash, width=sp_w, height=sp_h, highlightthickness=0, bd=0, bg=trans_color)
        self._splash_cv.pack(fill="both", expand=True)

        self._splash_bg_ref = None
        try:
            splash_path = Path(__file__).parent / "resources" / "assets" / "frame0" / "splash.png"
            if splash_path.exists():
                bg_img = Image.open(splash_path).resize((sp_w, sp_h), Image.LANCZOS)
                self._splash_bg_ref = ImageTk.PhotoImage(bg_img)
                self._splash_cv.create_image(0, 0, image=self._splash_bg_ref, anchor="nw")
        except Exception as e:
            print(f"[Splash] Failed to load background: {e}")

        # Loading area bounds scaled by 1.3
        box_x = int(35 * 1.3)
        box_y = int(240 * 1.3)
        box_w = int((270 - 35) * 1.3)
        box_h = int((350 - 240) * 1.3)

        # Progress bar
        bar_x = box_x
        bar_y = box_y + (box_h // 2) - 10
        bar_w = box_w
        bar_h = 4
        self._splash_cv.create_rectangle(bar_x, bar_y, bar_x + bar_w, bar_y + bar_h, fill="#27272A", outline="")
        self._prog_rect = self._splash_cv.create_rectangle(bar_x, bar_y, bar_x, bar_y + bar_h, fill="#f03043", outline="")
        self._prog_max_w = bar_w
        self._prog_x = bar_x
        self._prog_y = bar_y
        self._prog_h = bar_h

        # Status text below progress bar
        self._splash_status_text = self._splash_cv.create_text(
            bar_x, bar_y + bar_h + 8,
            text="Initializing...",
            font=("Roboto", 9), fill="#FFFFFF", anchor="nw"
        )

        self._splash_anim_on = True
        self._splash_anim_id = None
        
        self._splash_log_msg("[INFO] Starting Brawlhalla Modding Toolkit...")
        self._splash.update()

    def _splash_anim_tick(self):
        """No animation needed in new modern splash"""
        pass

    def _splash_log_msg(self, msg):
        """Update the status text elegantly."""
        try:
            clean = msg.replace("[INFO] ", "").replace("[OK] ", "").replace("[WARNING] ", "")
            if hasattr(self, "_splash_cv") and self._splash.winfo_exists():
                self._splash_cv.itemconfigure(self._splash_status_text, text=clean)
                self._splash.update_idletasks()
        except Exception:
            pass

    def _splash_progress(self, frac):
        """Update splash progress bar (0.0 -> 1.0)."""
        try:
            if hasattr(self, "_prog_rect") and self._splash.winfo_exists():
                w = int(self._prog_max_w * max(0.0, min(1.0, frac)))
                self._splash_cv.coords(
                    self._prog_rect,
                    self._prog_x, self._prog_y,
                    self._prog_x + w, self._prog_y + self._prog_h
                )
                self._splash.update_idletasks()
        except Exception:
            pass

    # ── Loading steps (executed sequentially via after()) ─────────────
    def _load_step_fonts(self):
        self._splash_log_msg("[INFO] Loading custom fonts...")
        self._splash_progress(0.10)
        self.load_custom_fonts()
        self._splash_log_msg("[OK] Custom fonts loaded")
        self._splash_progress(0.20)
        self.after(50, self._load_step_icons)

    def _load_step_icons(self):
        self._splash_log_msg("[INFO] Loading tool icons...")
        self._splash_progress(0.30)
        self.load_icons()
        self._splash_log_msg(f"[OK] Loaded {len(self.icons)} icons")
        self._splash_progress(0.45)
        self.after(50, self._load_step_app_icon)

    def _load_step_app_icon(self):
        self._splash_log_msg("[INFO] Setting application icon...")
        try:
            # Try to find the best icon available
            icon_candidates = ["Icon.ico", "Icon32.ico"]
            icon_path = None
            for icon_name in icon_candidates:
                temp_path = Path(__file__).parent / "resources" / "icons" / icon_name
                if temp_path.exists():
                    icon_path = temp_path
                    break
            
            if icon_path:
                self.wm_iconbitmap(str(icon_path))
                self._splash_log_msg(f"[OK] Icon set: {icon_path.name}")
            else:
                self._splash_log_msg("[WARNING] No icon file found (.ico)")
        except Exception:
            self._splash_log_msg("[WARNING] Could not set application icon")
        self._splash_progress(0.55)
        self.after(50, self._load_step_config)

    def _load_step_config(self):
        self._splash_log_msg("[INFO] Loading saved configuration...")
        self.load_configuration()
        if self.gamePathString:
            self._splash_log_msg(f"[OK] Game path loaded")
        if self.modsPathString:
            self._splash_log_msg(f"[OK] Mods path loaded")
        if not self.gamePathString and not self.modsPathString:
            self._splash_log_msg("[INFO] No saved configuration found")
        self._splash_progress(0.70)
        self.after(50, self._load_step_ui)

    def _load_step_ui(self):
        self._splash_log_msg("[INFO] Building user interface...")
        self._splash_progress(0.75)

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        # Use a reasonable default window size instead of forcing fullscreen.
        default_w = min(1400, screen_w - 100)
        default_h = min(850, screen_h - 100)
        x = (screen_w - default_w) // 2
        y = (screen_h - default_h) // 2

        self.geometry(f"{default_w}x{default_h}+{x}+{y}")
        self.minsize(900, 600)
        self.resizable(True, True)

        self._splash_log_msg("[INFO] Creating sidebar navigation...")
        self._splash_progress(0.80)
        self.create_ui()
        self._splash_log_msg("[OK] User interface ready")
        self._splash_progress(0.90)
        self.after(50, self._load_step_finish)

    def _load_step_finish(self):
        enabled = sum(1 for v in ENABLED_TOOLS.values() if v)
        self._splash_log_msg(f"[INFO] {enabled} tools registered")
        self._splash_log_msg("[OK] Brawlhalla Modding Toolkit is ready!")
        self._splash_progress(1.0)
        self.after(600, self._destroy_splash)

    def _destroy_splash(self):
        """Close splash and show main window."""
        self._splash_anim_on = False
        if self._splash_anim_id:
            try:
                self._splash.after_cancel(self._splash_anim_id)
            except Exception:
                pass
        try:
            self._splash.attributes("-topmost", False)
        except Exception:
            pass
        try:
            self._splash.destroy()
        except Exception:
            pass
        self._splash = None
        self.deiconify()
        try:
            self.attributes("-topmost", False)
        except Exception:
            pass
        try:
            self.lift()
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════════
    #  TOOL LOADING OVERLAY (animated hourglass inside main panel)
    # ═══════════════════════════════════════════════════════════════════
    def _show_loading_overlay(self, tool_name):
        """Show loading overlay with animated hourglass in tool_container."""
        overlay = ctk.CTkFrame(self.tool_container, fg_color="#0E0E0E")
        overlay.pack(fill="both", expand=True)

        center = ctk.CTkFrame(overlay, fg_color="transparent")
        center.pack(expand=True, anchor="center")

        # Hourglass animation
        if hasattr(self, '_hourglass_ctk') and self._hourglass_ctk:
            self._ov_hg_idx = 0
            self._ov_hg_label = ctk.CTkLabel(
                center, text="",
                image=self._hourglass_ctk[0]
            )
            self._ov_hg_label.pack(pady=(0, 20))
            self._ov_anim_on = True
            self._ov_anim_id = None
            self._ov_anim_tick()

        # Tool name
        ctk.CTkLabel(
            center, text=f"Loading {tool_name}...",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#FFFFFF"
        ).pack(pady=(0, 8))

        # Status text
        self._ov_status = ctk.CTkLabel(
            center, text="Initializing module...",
            font=ctk.CTkFont(size=12), text_color="#808080"
        )
        self._ov_status.pack()

        self._loading_overlay = overlay
        overlay.update()

    def _ov_anim_tick(self):
        """Cycle hourglass frames on the tool loading overlay."""
        if not getattr(self, '_ov_anim_on', False):
            return
        try:
            self._ov_hg_idx = (self._ov_hg_idx + 1) % len(self._hourglass_ctk)
            self._ov_hg_label.configure(image=self._hourglass_ctk[self._ov_hg_idx])
            self._ov_anim_id = self.after(400, self._ov_anim_tick)
        except Exception:
            pass

    def _stop_ov_anim(self):
        """Stop the overlay hourglass animation."""
        self._ov_anim_on = False
        if hasattr(self, '_ov_anim_id') and self._ov_anim_id:
            try:
                self.after_cancel(self._ov_anim_id)
            except Exception:
                pass

    def create_ui(self):
        """Crea la interfaz principal del dashboard"""
        
        # Frame principal con dos columnas
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar izquierdo
        self.create_sidebar()
        
        # Panel principal de contenido
        self.main_panel = ctk.CTkFrame(self, fg_color="#0E0E0E")
        self.main_panel.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_panel.grid_rowconfigure(1, weight=1)
        self.main_panel.grid_columnconfigure(0, weight=1)
        
        # Header con rutas
        self.create_header()
        
        # Contenedor de herramientas (se cambiará dinámicamente)
        self.tool_container = ctk.CTkFrame(self.main_panel, fg_color="#0E0E0E")
        self.tool_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 20))
        
        # Mostrar pantalla de bienvenida por defecto
        self.show_welcome_screen()
        
    def create_sidebar(self):
        """Crea el sidebar con los botones de navegación"""
        
        sidebar = ctk.CTkFrame(self, width=250, fg_color="#171717")
        sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        sidebar.grid_propagate(False)
        
        # Logo/Título
        title_frame = ctk.CTkFrame(sidebar, fg_color="#171717", height=160)
        title_frame.pack(fill="x", padx=15, pady=(20, 20))
        
        self.title_label = ctk.CTkLabel(
            title_frame,
            text="",
            image=None
        )
        self.title_label.pack(pady=(0, 5))
        
        # Initial logo render
        self._update_logo_color(self.current_color)
        
        version_label = ctk.CTkLabel(
            title_frame,
            text=f"Version {APP_VERSION}",
            font=BMTTheme.get_font(10),
            text_color=BMTTheme.GREY
        )
        version_label.pack()
        
        # Separador
        separator = ctk.CTkFrame(sidebar, height=2, fg_color="#2C2C2C")
        separator.pack(fill="x", padx=15, pady=(0, 20))
        
        # Botones de herramientas (solo las habilitadas en build_config)
        self.tool_buttons = {}
        
        all_tools = [
            ("Mod Source Manager",  "mod_source_manager",  self.show_skin_editor),
            ("Sprite Exporter",     "sprite_exporter",     self.show_sprite_exporter),
            ("Color Swapper",       "color_swapper",       self.show_color_swapper),
            ("Skin Changer",        "skin_changer",        self.show_skin_changer),
            ("Skin Changer Pro",    "skin_changer_pro",    self.show_skin_changer_pro),
            ("Reference Loader",    "reference_loader",    self.show_reference_loader),
            ("Color Converter",     "color_converter",     self.show_color_converter),
            ("Fast Shape Replacer", "fast_shape_replacer", self.show_fast_shape_replacer),
            ("Skin Editor",         "skin_editor",         self.show_skin_editor_module),
            ("Lang Editor",         "lang_editor",         self.show_lang_editor),
            ("SVG Maker",           "svg_maker",           self.show_svg_maker),
        ]
        
        # Filter to only enabled tools
        tools = [(n, i, c) for n, i, c in all_tools if ENABLED_TOOLS.get(n, False)]
        
        self.tool_tooltips = {
            "Skin Editor": ("Advanced skin editor for Brawlhalla. Export modifications directly to the game.", "Beta tool. Always keep backups to avoid file corruption."),
            "Reference Loader": ("Seamlessly inject reference sprites into your skin files for accurate scaling and positioning.", None),
            "Sprite Exporter": ("Extract all assets from a skin and export them into a standalone .swf file for external use.", None),
            "Color Swapper": ("Batch replace colors across multiple signatures, skins, and effects with high precision.", None),
            "Skin Changer": ("Manually swap skin files between characters.", "For advanced users only. Use Skin Changer Pro for a safer experience."),
            "Skin Changer Pro": ("Powerful porting tool. Import multiple .swf files and port their shapes and definitions to a target file automatically.", None),
            "Color Converter": ("Multi-format color conversion utility (HEX, INT, RGB, HSL). Essential for working with Brawlhalla's internal color systems.", None),
            "Fast Shape Replacer": ("Rapidly edit multiple SVG shapes using a single grid-template file. No need to open files individually.", None),
            "Mod Source Manager": ("Centralized project hub. View and manage all your modding projects. Requires a 16:9 'Render.png' for grid thumbnails.", None),
            "Lang Editor": ("Beta tool to edit languageX.bin files and export them for use with Brawlhalla Mod Creator/Loader.", "Make sure you have Mod Creator and Loader v0.3.1 or higher."),
            "SVG Maker": ("Convert raster images (PNG/JPG) to scalable vector graphics (SVG) with advanced tuning options.", None),
        }

        for name, icon_key, command in tools:
            # Obtener icono
            icon = self.icons.get(icon_key, None)
            
            accent = self.tool_colors.get(name, BMTTheme.BLUE_GREY)
            btn = ctk.CTkButton(
                sidebar,
                text=f"  {name}",
                image=icon,
                compound="left",
                command=command,
                font=BMTTheme.get_font(13, "bold"),
                fg_color="transparent",
                hover_color=accent,
                anchor="w",
                height=45,
                corner_radius=BMTTheme.CORNER_RADIUS,
                text_color=BMTTheme.WHITE
            )
            btn.pack(fill="x", padx=15, pady=4)
            self.tool_buttons[name] = btn
            
            # Attach Tooltip
            desc, warn = self.tool_tooltips.get(name, (None, None))
            if desc:
                BMTToolTip(btn, desc, accent_color=accent, warning=warn)
        
        # No activar ningún botón por defecto
        # self.set_active_button("Sprite Exporter")
        
        # Footer con configuración
        footer_frame = ctk.CTkFrame(sidebar, fg_color="#171717")
        footer_frame.pack(side="bottom", fill="x", padx=15, pady=20)
        
        # Use icon for settings if available, otherwise plain text
        settings_icon = self.icons.get('settings')
        settings_btn = ctk.CTkButton(
            footer_frame,
            text="Settings" if not settings_icon else f"  Settings",
            image=settings_icon,
            compound="left" if settings_icon else None,
            command=self.show_settings,
            font=self.font_normal,
            fg_color="#2C2C2C",
            hover_color="#404040",
            height=35
        )
        settings_btn.pack(fill="x", pady=(0, 10))

        credits_btn = ctk.CTkButton(
            footer_frame,
            text="Credits & Licenses",
            command=self.show_credits_screen,
            font=self.font_normal,
            fg_color="transparent",
            text_color=BMTTheme.GREY,
            hover_color="#2C2C2C",
            height=30
        )
        credits_btn.pack(fill="x")
        
    def create_header(self):
        """Crea el header con las rutas de configuración"""
        
        header = ctk.CTkFrame(self.main_panel, fg_color="#171717", height=80)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        header.grid_columnconfigure(1, weight=1)
        
        # Ruta de Brawlhalla
        brawl_label = ctk.CTkLabel(header, text="Brawlhalla Path:")
        BMTTheme.style_subtitle(brawl_label)
        brawl_label.grid(row=0, column=0, padx=(15, 5), pady=5, sticky="w")
        
        self.brawl_path_entry = ctk.CTkEntry(
            header, placeholder_text="Select Brawlhalla folder...",
            height=35, font=BMTTheme.get_font(12),
            fg_color=BMTTheme.BG_SUBPANEL, border_width=0
        )
        self.brawl_path_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        if self.gamePathString:
            self.brawl_path_entry.insert(0, self.gamePathString)
        
        folder_icon = self.icons.get('folder')
        self.brawl_btn = ctk.CTkButton(
            header, text="" if folder_icon else "...", image=folder_icon,
            command=self.select_brawlhalla_path, width=45, height=35
        )
        BMTTheme.style_primary_button(self.brawl_btn, color=self.current_color)
        self.brawl_btn.grid(row=0, column=2, padx=(5, 15), pady=5)
        
        # Ruta de Mods
        mods_label = ctk.CTkLabel(header, text="Mods Path:")
        BMTTheme.style_subtitle(mods_label)
        mods_label.grid(row=1, column=0, padx=(15, 5), pady=5, sticky="w")
        
        self.mods_path_entry = ctk.CTkEntry(
            header, placeholder_text="Select mods folder...",
            height=35, font=BMTTheme.get_font(12),
            fg_color=BMTTheme.BG_SUBPANEL, border_width=0
        )
        self.mods_path_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        if self.modsPathString:
            self.mods_path_entry.insert(0, self.modsPathString)
        
        self.mods_btn = ctk.CTkButton(
            header, text="" if folder_icon else "...", image=folder_icon,
            command=self.select_mods_path, width=45, height=35
        )
        BMTTheme.style_primary_button(self.mods_btn, color=self.current_color)
        self.mods_btn.grid(row=1, column=2, padx=(5, 15), pady=5)
    
    def show_welcome_screen(self):
        """Muestra la pantalla de bienvenida"""
        self.clear_tool_container()
        
        # Resetear color a azul grisáceo (base)
        self.current_color = BMTTheme.BLUE_GREY
        
        # Actualizar título
        if hasattr(self, 'title_label'):
            self.title_label.configure(text_color=self.current_color)
        
        # Resetear todos los botones
        for btn in self.tool_buttons.values():
            btn.configure(fg_color="#171717")
        
        # Contenedor principal
        welcome_frame = ctk.CTkFrame(self.tool_container, fg_color="#0E0E0E")
        welcome_frame.pack(fill="both", expand=True)
        
        # Centrar contenido de forma segura sin place
        center_frame = ctk.CTkFrame(welcome_frame, fg_color="transparent")
        center_frame.pack(expand=True, anchor="center")
        
        # Logo/Icono grande (si existe)
        try:
            logo_path = Path(__file__).parent / "Icon.png"
            if logo_path.exists():
                logo_img = Image.open(logo_path)
                logo_ctk = ctk.CTkImage(logo_img, size=(128, 128))
                logo_label = ctk.CTkLabel(center_frame, image=logo_ctk, text="")
                logo_label.pack(pady=(0, 20))
        except:
            pass
        
        # Título de bienvenida
        welcome_title = ctk.CTkLabel(
            center_frame,
            text="Welcome to\nBrawlhalla Modding Toolkit",
            font=ctk.CTkFont(family="Roboto", size=36, weight="bold"),
            text_color="#FFFFFF"
        )
        welcome_title.pack(pady=(0, 10))
        
        # Subtítulo
        subtitle = ctk.CTkLabel(
            center_frame,
            text="Select a tool to get started",
            font=ctk.CTkFont(family="Roboto", size=18, weight="normal"),
            text_color="#9E9E9E"
        )
        subtitle.pack(pady=(0, 40))
        
        # Grid de herramientas con iconos grandes
        tools_grid = ctk.CTkFrame(center_frame, fg_color="transparent")
        tools_grid.pack()
        
        all_tools_data = [
            ("Mod Source Manager",  "mod_source_manager",  self.show_skin_editor),
            ("Sprite Exporter",     "sprite_exporter",     self.show_sprite_exporter),
            ("Color Swapper",       "color_swapper",       self.show_color_swapper),
            ("Skin Changer",        "skin_changer",        self.show_skin_changer),
            ("Skin Changer Pro",    "skin_changer_pro",    self.show_skin_changer_pro),
            ("Reference Loader",    "reference_loader",    self.show_reference_loader),
            ("Color Converter",     "color_converter",     self.show_color_converter),
            ("Fast Shape Replacer", "fast_shape_replacer", self.show_fast_shape_replacer),
            ("Skin Editor",         "skin_editor",         self.show_skin_editor_module),
            ("Lang Editor",         "lang_editor",         self.show_lang_editor),
        ]
        
        # Filter to only enabled tools and compute grid positions
        tools_data = []
        idx = 0
        for name, icon_key, command in all_tools_data:
            if ENABLED_TOOLS.get(name, False):
                row = idx // 3
                col = idx % 3
                tools_data.append((name, icon_key, command, row, col))
                idx += 1
        
        for name, icon_key, command, row, col in tools_data:
            tool_btn_frame = ctk.CTkFrame(tools_grid, fg_color="#171717", corner_radius=12)
            tool_btn_frame.grid(row=row, column=col, padx=15, pady=15)
            
            # Botón con icono (tamaño grande para el dashboard)
            icon = self.icons_big.get(icon_key) or self.icons.get(icon_key, None)

            # Crear un botón más grande con icono
            big_btn = ctk.CTkButton(
                tool_btn_frame,
                text="",
                image=icon,
                command=command,
                width=100,
                height=100,
                fg_color="#2C2C2C",
                hover_color=self.tool_colors.get(name, "#404040"),
                corner_radius=10
            )
            big_btn.pack(padx=10, pady=(10, 5))
            
            # Nombre de la herramienta
            tool_name_label = ctk.CTkLabel(
                tool_btn_frame,
                text=name,
                font=self.font_normal,
                text_color="#FFFFFF"
            )
            tool_name_label.pack(pady=(0, 10))
        
        # Mensaje de configuración si faltan rutas
        if not self.gamePathString or not self.modsPathString:
            warning_frame = ctk.CTkFrame(welcome_frame, fg_color="#2C2C2C", corner_radius=8)
            warning_frame.pack(side="bottom", fill="x", padx=40, pady=20)
            
            warning_label = ctk.CTkLabel(
                warning_frame,
                text="Please configure Brawlhalla and Mods paths in the header above",
                font=self.font_normal,
                text_color="#FFA726"
            )
            warning_label.pack(pady=15)
        
    def safe_after(self, ms, callback, *args):
        """Schedules a task and tracks its ID for later cancellation."""
        task_id = self.after(ms, callback, *args)
        self._after_tasks.append(task_id)
        return task_id

    def cancel_all_tasks(self):
        """Cancels all pending after() tasks to prevent 'invalid command name' errors."""
        for task_id in self._after_tasks:
            try:
                self.after_cancel(task_id)
            except Exception:
                pass
        self._after_tasks = []

    def set_active_button(self, button_name):
        """Establece el botón activo en el sidebar"""
        # Actualizar color actual
        self.current_color = self.tool_colors.get(button_name, "#1976D2")
        
        # Actualizar logo con el nuevo color
        self._update_logo_color(self.current_color)
        
        # Actualizar botones del header
        if hasattr(self, 'brawl_btn'):
            self.brawl_btn.configure(hover_color=self.current_color)
        if hasattr(self, 'mods_btn'):
            self.mods_btn.configure(hover_color=self.current_color)
        
        # Actualizar botones
        for name, btn in self.tool_buttons.items():
            if name == button_name:
                btn.configure(fg_color=self.current_color)
            else:
                btn.configure(fg_color="#171717")
    
    def clear_tool_container(self):
        """Oculta el módulo actual sin destruirlo (persistencia de sesión).
        Solo se usa directamente para welcome/settings (sin módulos cacheados)."""
        if self.current_module:
            self.current_module.hide()
            self.current_module = None
        
        # Destruir widgets huérfanos (overlays, welcome screen, etc)
        for widget in self.tool_container.winfo_children():
            # No destruir frames de módulos cacheados
            is_cached = False
            for cached_mod in self._module_cache.values():
                if hasattr(cached_mod, 'container') and cached_mod.container is widget:
                    is_cached = True; break
                if hasattr(cached_mod, 'main_frame') and cached_mod.main_frame is widget:
                    is_cached = True; break
            if not is_cached:
                widget.destroy()
    
    def load_tool_module(self, module_class, tool_name="Tool"):
        """Carga un módulo con persistencia: si ya fue creado, lo muestra directamente."""
        # Ocultar módulo anterior
        if self.current_module:
            self.current_module.hide()
            self.current_module = None
        
        # Destruir widgets no-módulo (welcome, overlays, settings)
        for widget in self.tool_container.winfo_children():
            is_cached = False
            for cached_mod in self._module_cache.values():
                if hasattr(cached_mod, 'container') and cached_mod.container is widget:
                    is_cached = True; break
                if hasattr(cached_mod, 'main_frame') and cached_mod.main_frame is widget:
                    is_cached = True; break
            if not is_cached:
                widget.destroy()
        
        # Si el módulo ya está en caché, simplemente mostrarlo
        if tool_name in self._module_cache:
            self.current_module = self._module_cache[tool_name]
            self.current_module.show()
            return
        
        # Primera vez: crear con overlay de carga
        self._show_loading_overlay(tool_name)
        self.safe_after(150, lambda: self._do_load_tool(module_class, tool_name))

    def _do_load_tool(self, module_class, tool_name="Tool"):
        """Execute the actual tool module loading."""
        try:
            print(f"[DEBUG] Loading module {module_class.__name__}...")
            accent = self.tool_colors.get(tool_name, "#1976D2")
            self._update_logo_color(accent)
            
            print(f"[DEBUG] Instantiating module...")
            module = module_class(
                self.tool_container,
                self.gamePathString,
                self.modsPathString,
                icons=self.icons
            )
            print(f"[DEBUG] Building UI...")
            module.create_ui()
            print(f"[DEBUG] Module {tool_name} loaded successfully.")

            # Remove overlay
            self._stop_ov_anim()
            if self._loading_overlay:
                self._loading_overlay.destroy()
                self._loading_overlay = None

            # Guardar en caché y mostrar
            self._module_cache[tool_name] = module
            self.current_module = module
            module.show()
        except Exception as e:
            self._stop_ov_anim()
            if self._loading_overlay:
                self._loading_overlay.destroy()
                self._loading_overlay = None
            self.show_error_message(module_class.__name__, str(e))
    
    # Métodos para mostrar cada herramienta
    def _show_tool(self, tool_name):
        """Generic method to show a tool by name (only if enabled)."""
        module_class = _module_classes.get(tool_name)
        if module_class:
            self.set_active_button(tool_name)
            self.load_tool_module(module_class, tool_name)
        else:
            print(f"[WARNING] Tool '{tool_name}' is not enabled or not loaded.")
    
    def show_sprite_exporter(self):
        self._show_tool("Sprite Exporter")
    
    def show_color_swapper(self):
        self._show_tool("Color Swapper")
    
    def show_skin_editor(self):
        self._show_tool("Mod Source Manager")
    
    def show_skin_changer(self):
        self._show_tool("Skin Changer")

    def show_skin_changer_pro(self):
        self._show_tool("Skin Changer Pro")
    
    def show_reference_loader(self):
        self._show_tool("Reference Loader")
    
    def show_color_converter(self):
        self._show_tool("Color Converter")
    
    def show_fast_shape_replacer(self):
        self._show_tool("Fast Shape Replacer")

    def show_skin_editor_module(self):
        self._show_tool("Skin Editor")

    def show_lang_editor(self):
        self._show_tool("Lang Editor")

    def show_svg_maker(self):
        self._show_tool("SVG Maker")
    def show_settings(self):
        """Muestra el panel de configuración"""
        self.clear_tool_container()
        
        # Resetear color a un color neutral para Settings
        self.current_color = "#616161"  # Material Grey 700
        
        # Actualizar título
        if hasattr(self, 'title_label'):
            self.title_label.configure(text_color=self.current_color)
        
        # Resetear botones
        for btn in self.tool_buttons.values():
            btn.configure(fg_color="#171717")
        
        content = ctk.CTkFrame(self.tool_container, fg_color="#0E0E0E")
        content.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Settings title (no emoji)
        title = ctk.CTkLabel(
            content,
            text="Settings",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.current_color
        )
        title.pack(pady=(0, 30))
        
        # Opciones de configuración
        settings_frame = ctk.CTkFrame(content, fg_color="#171717", corner_radius=10)
        settings_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # ==========================================
        # Application Settings Section
        # ==========================================
        app_settings_lbl = ctk.CTkLabel(settings_frame, text="Application Settings", font=ctk.CTkFont(size=16, weight="bold"), text_color=BMTTheme.WHITE)
        app_settings_lbl.pack(anchor="w", padx=20, pady=(20, 10))

        # Switches
        self.hw_accel_var = ctk.BooleanVar(value=True)
        hw_accel_switch = ctk.CTkSwitch(settings_frame, text="Enable Hardware Acceleration (Skia OpenGL)", variable=self.hw_accel_var, progress_color="#6A1B9A", font=BMTTheme.get_font(13))
        hw_accel_switch.pack(anchor="w", padx=40, pady=10)



        self.advanced_log_var = ctk.BooleanVar(value=False)
        advanced_log_switch = ctk.CTkSwitch(settings_frame, text="Enable Verbose Debug Logging", variable=self.advanced_log_var, progress_color="#6A1B9A", font=BMTTheme.get_font(13))
        advanced_log_switch.pack(anchor="w", padx=40, pady=10)

        # Separator
        ctk.CTkFrame(settings_frame, height=2, fg_color="#2C2C2C").pack(fill="x", padx=20, pady=20)

        # ==========================================
        # Storage & Cache Section
        # ==========================================
        storage_lbl = ctk.CTkLabel(settings_frame, text="Storage & Cache", font=ctk.CTkFont(size=16, weight="bold"), text_color=BMTTheme.WHITE)
        storage_lbl.pack(anchor="w", padx=20, pady=(0, 10))
        
        # Botón para limpiar caché
        clear_cache_btn = ctk.CTkButton(
            settings_frame,
            text="Clear Thumbnails & Projects Cache",
            image=BMTTheme.get_icon("delete", size=18) if hasattr(BMTTheme, 'get_icon') else None,
            compound="left",
            command=self.clear_cache,
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            fg_color="#8E24AA",
            hover_color="#6A1B9A"
        )
        clear_cache_btn.pack(anchor="w", padx=40, pady=10)
        
        # Información de versión
        info_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        info_frame.pack(side="bottom", pady=20)
        
        version_info = ctk.CTkLabel(
            info_frame,
            text=f"{APP_NAME} v{APP_VERSION}\n© 2026 - All tools integrated",
            font=ctk.CTkFont(size=12),
            text_color="#616161"
        )
        version_info.pack()

    def show_credits_screen(self):
        """Displays the Credits and Licenses screen"""
        self.clear_tool_container()
        
        # Reset color to a neutral one for Credits
        self.current_color = "#4CAF50"  # Material Green
        
        # Actualizar título
        if hasattr(self, 'title_label'):
            self.title_label.configure(text_color=self.current_color)
            
        # Resetear botones
        for btn in self.tool_buttons.values():
            btn.configure(fg_color="#171717")
        
        container = ctk.CTkScrollableFrame(self.tool_container, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Título
        title = ctk.CTkLabel(
            container, 
            text="Brawlhalla Modding Toolkit", 
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="white"
        )
        title.pack(anchor="w")
        
        subtitle = ctk.CTkLabel(
            container,
            text=f"Version {APP_VERSION} - Developed by Lord Shadow",
            font=ctk.CTkFont(size=14),
            text_color=self.current_color
        )
        subtitle.pack(anchor="w", pady=(0, 30))
        
        def add_credit(title_text, desc_text, url_text):
            frame = ctk.CTkFrame(container, fg_color="#1A1A1A", corner_radius=8)
            frame.pack(fill="x", pady=8)
            
            lbl_title = ctk.CTkLabel(frame, text=title_text, font=ctk.CTkFont(size=15, weight="bold"), text_color="white")
            lbl_title.pack(anchor="w", padx=20, pady=(15, 5))
            
            lbl_desc = ctk.CTkLabel(frame, text=desc_text, font=ctk.CTkFont(size=13), text_color="#A0A0A0", justify="left", wraplength=700)
            lbl_desc.pack(anchor="w", padx=20, pady=(0, 5))
            
            if url_text:
                lbl_url = ctk.CTkLabel(frame, text=url_text, font=ctk.CTkFont(size=12), text_color=self.current_color, cursor="hand2")
                lbl_url.pack(anchor="w", padx=20, pady=(0, 15))
            else:
                ctk.CTkFrame(frame, height=15, fg_color="transparent").pack()
        
        add_credit("Skia Engine (skia-python)", "High-performance vector rendering engine used in the Skin Editor for infinite-quality SVGs and GPU caching.", "https://github.com/kyamagu/skia-python")
        add_credit("FFDEC (JPEXS Free Flash Decompiler)", "The core system that allows decompiling, extracting, and injecting sprites/shapes into Brawlhalla's SWF files.", "https://github.com/jindrapetrik/jpexs-decompiler")
        add_credit("CustomTkinter (CTK)", "Modern UI library for Python, bringing this beautiful and responsive design to life.", "https://github.com/TomSchimansky/CustomTkinter")
        add_credit("CTK Color Picker", "Advanced color selector (HEX, INT, RGB) seamlessly integrated with CustomTkinter for the Color Swapper.", "https://github.com/kandelucky/ctk-color-picker")
        add_credit("Brawlhalla Language Edit & Lang Reader", "Parsing and injection tools used to read and modify the game's text strings (XML/BIN).", "https://github.com/bucccket/BrawlhallaLanguageEdit | https://github.com/allhailcheese/BrawlhallaLangReader")
        add_credit("Cairo & Resvg", "Auxiliary libraries for 2D vector parsing and rendering.", "https://github.com/Kozea/cairosvg | https://github.com/linebender/resvg")
        add_credit("JPype1 & Py4J", "Communication bridges between the Python frontend and the FFDEC Java backend.", "https://github.com/jpype-project/jpype")
    
    def show_error_message(self, tool_name, error):
        """Muestra un mensaje de error en el contenedor"""
        content = ctk.CTkFrame(self.tool_container, fg_color="#0E0E0E")
        content.pack(fill="both", expand=True)
        
        label = ctk.CTkLabel(
            content,
            text=f"Error loading {tool_name}\n\n{error}",
            font=ctk.CTkFont(size=16),
            text_color="#FF5252"
        )
        label.pack(expand=True)
    
    def select_brawlhalla_path(self):
        """Selecciona la ruta de Brawlhalla"""
        path = filedialog.askdirectory(title="Select Brawlhalla Folder")
        if path:
            self.gamePathString = path
            self.brawl_path_entry.delete(0, tk.END)
            self.brawl_path_entry.insert(0, path)
            self.save_configuration()
            
            # Actualizar módulo actual si existe
            if self.current_module and hasattr(self.current_module, 'game_path'):
                self.current_module.game_path = path
                if hasattr(self.current_module, 'log'):
                    self.current_module.log(f"Game path updated: {path}")
    
    def select_mods_path(self):
        """Selecciona la ruta de Mods"""
        path = filedialog.askdirectory(title="Select Mods Folder")
        if path:
            self.modsPathString = path
            self.mods_path_entry.delete(0, tk.END)
            self.mods_path_entry.insert(0, path)
            self.save_configuration()
            
            # Actualizar módulo actual si existe
            if self.current_module and hasattr(self.current_module, 'mods_path'):
                self.current_module.mods_path = path
                if hasattr(self.current_module, 'log'):
                    self.current_module.log(f"Mods path updated: {path}")
    
    def change_appearance(self, mode):
        """Cambia el modo de apariencia"""
        if not ALLOW_LIGHT_MODE and mode != "Dark":
            ctk.set_appearance_mode("Dark")
            return
        ctk.set_appearance_mode(mode)
    
    def clear_cache(self):
        """Limpia el caché de la aplicación"""
        result = messagebox.askyesno(
            "Clear Cache",
            "Are you sure you want to clear the project and thumbnail cache?\nThis will force a full re-scan of your mod folders."
        )
        if result:
            try:
                cache_dir = os.path.join(os.getenv('APPDATA'), 'Brawlhalla Modding Toolkit', 'Cache')
                if os.path.exists(cache_dir):
                    import shutil
                    shutil.rmtree(cache_dir)
                    os.makedirs(cache_dir, exist_ok=True)
                
                # Clear memory cache if MSM is loaded
                if "Mod Source Manager" in self._module_cache:
                    msm = self._module_cache["Mod Source Manager"]
                    msm.projects = []
                    msm.image_cache = {}
                    msm.project_cache = {}
                
                messagebox.showinfo("Cache Cleared", "Cache has been cleared successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Could not clear cache: {e}")
    
    def save_configuration(self):
        """Guarda la configuración"""
        config_data = {
            "gamePathString": self.gamePathString,
            "modsPathString": self.modsPathString
        }
        
        app_folder_path = os.path.join(os.getenv("APPDATA"), "Brawlhalla Modding Toolkit")
        if not os.path.exists(app_folder_path):
            os.makedirs(app_folder_path)
        
        config_file_path = os.path.join(app_folder_path, "config.json")
        with open(config_file_path, "w") as config_file:
            json.dump(config_data, config_file, indent=4)
    
    def load_configuration(self):
        """Carga la configuración guardada"""
        config_file_path = os.path.join(
            os.getenv("APPDATA"),
            "Brawlhalla Modding Toolkit",
            "config.json"
        )
        
        if os.path.exists(config_file_path):
            try:
                with open(config_file_path, "r") as config_file:
                    config_data = json.load(config_file)
                
                self.gamePathString = config_data.get("gamePathString", "")
                self.modsPathString = config_data.get("modsPathString", "")
            except Exception as e:
                print(f"Error loading configuration: {e}")


    def _update_logo_color(self, hex_color: str):
        """Updates the sidebar logo with a new accent color."""
        if not hasattr(self, 'logo_path') or not self.logo_path.exists():
            return

        try:
            # Read SVG and replace the target color
            svg_text = self.logo_path.read_text(encoding="utf-8")
            # Replace both #ef273a and #ef273aff just in case
            svg_text = svg_text.replace("#ef273a", hex_color)
            svg_text = svg_text.replace("#ef273aff", hex_color)

            # Render SVG to PIL Image
            # Increased size to 90x90 for better visibility
            pil_img = render_svg(svg_text, (90, 90))
            if pil_img:
                self.logo_image = ctk.CTkImage(pil_img, size=(90, 90))
                if hasattr(self, 'title_label'):
                    self.title_label.configure(image=self.logo_image)
        except Exception as e:
            print(f"[ERROR] Could not update logo color: {e}")

import multiprocessing

if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = BrawlhallaModdingToolkit()
    app.mainloop()
