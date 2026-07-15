from src.utils import get_project_root
import os
import json
import tempfile
import threading
import re
import math
import time
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import vtracer
from pathlib import Path

from src.modules.ToolModuleBase import ToolModule
from src.utils.ThemeManager import BMTTheme, BMTToolTip

try:
    import skia
    HAS_SKIA = True
except ImportError:
    HAS_SKIA = False

try:
    from src.utils.vcp_wrapper import ask_color
    HAS_VCP = True
except ImportError:
    HAS_VCP = False
    
# Resolve paths
ASSETS_PATH = get_project_root() / "resources" / "assets"
EDIT_ICON_PATH = ASSETS_PATH / "IconsNew" / "edit_24dp_E3E3E3_FILL0_wght500_GRAD0_opsz24.png"

class SVGMakerModule(ToolModule):
    TOOL_NAME = "SVG Maker"
    ICON_KEY = "svg_maker"

    def __init__(self, parent, game_path, mods_path, icons=None):
        super().__init__(parent, game_path, mods_path, icons)
        self.current_color = BMTTheme.LIME
        self.icons = icons or {}
        
        self.input_path = None
        self.input_posterized_temp = os.path.join(tempfile.gettempdir(), "bmt_posterized.png")
        self.output_temp = os.path.join(tempfile.gettempdir(), "bmt_vtracer_out.svg")
        self.output_post_temp = os.path.join(tempfile.gettempdir(), "bmt_vtracer_post.svg")
        
        self.original_img = None
        self.preview_img = None
        self.is_processing = False
        
        self.slider_ratio = 0.5
        self.is_dragging = False
        
        self._cached_w = 0
        self._cached_h = 0
        self.current_swf_file = None
        self.current_swf_shape = None
        
        self.history_undo = []
        self.history_redo = []
        
        self._resized_orig = None
        self._resized_prev = None
        
        # Post-Processing
        self.dominant_colors = []
        self.current_palette = []
        self.color_overrides = {}
        self.color_swap_status = {}
        self.palette_timer = None
        self._anim_frame = 0
        
        self.settings = {}
        self.slider_labels = {}
        self.palette_bboxes = []
        
        try:
            self.edit_icon_img = ImageTk.PhotoImage(Image.open(EDIT_ICON_PATH).resize((20, 20)))
        except Exception:
            self.edit_icon_img = None
            
        self.load_presets()

    def get_tool_name(self): 
        return self.TOOL_NAME

    def get_tool_icon(self):  
        return self.icons.get(self.ICON_KEY)
        
    def load_presets(self):
        self.presets_file = os.path.join(self.mods_path, "svg_presets.json") if self.mods_path else "svg_presets.json"
        self.presets = {
            "Brawlhalla Perfect": {
                "colormode": "color",
                "mode": "spline",
                "hierarchical": True,
                "filter_speckle": 10,
                "corner_threshold": 60,
                "length_threshold": 30,
                "splice_threshold": 45,
                "path_precision": 8,
                "max_iterations": 16,
                "color_precision": 16,
                "layer_difference": 6,
                "spatial_radius": 3,
                "merge_threshold": 30,
                "target_quality": 90,
                "auto_max_iters": 4
            }
        }
        if os.path.exists(self.presets_file):
            try:
                with open(self.presets_file, "r") as f:
                    user_presets = json.load(f)
                    self.presets.update(user_presets)
            except Exception: pass
            
    def save_presets(self):
        try:
            with open(self.presets_file, "w") as f:
                user_presets = {k: v for k,v in self.presets.items() if k != "Brawlhalla Perfect"}
                json.dump(user_presets, f, indent=4)
        except Exception as e:
            print(f"[SVG Maker] Failed to save presets: {e}")

    def create_ui(self):
        self.container = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(1, weight=1)
        self.container.grid_columnconfigure(0, weight=3) # 3/4 Preview
        self.container.grid_columnconfigure(1, weight=1) # 1/4 Settings
        
        # Header
        header = ctk.CTkFrame(self.container, fg_color="#171717", corner_radius=10)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        
        title = ctk.CTkLabel(
            header, 
            text="SVG Maker", 
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="white"
        )
        title.pack(side="left", padx=20, pady=15)
        
        button_font = ctk.CTkFont(family="Roboto", size=14, weight="bold")
        
        self.btn_export = ctk.CTkButton(
            header,
            text="Export SVG",
            command=self.export_svg,
            font=button_font,
            text_color="white",
            fg_color=self.current_color,
            hover_color="#3B0764",
            state="disabled"
        )
        self.btn_export.pack(side="right", padx=20)
        
        self.btn_import = ctk.CTkButton(
            header,
            text="Import Image",
            command=self.import_image,
            font=button_font,
            text_color="white",
            fg_color="#2C2C2C",
            hover_color="#404040"
        )
        self.btn_import.pack(side="right", padx=10)
        
        self.btn_redo = ctk.CTkButton(header, text="", image=BMTTheme.get_icon('redo'), width=30, fg_color="#2A2A2A", hover_color="#383838", command=self._redo)
        self.btn_redo.pack(side="right", padx=(2, 0))
        self.btn_undo = ctk.CTkButton(header, text="", image=BMTTheme.get_icon('undo'), width=30, fg_color="#2A2A2A", hover_color="#383838", command=self._undo)
        self.btn_undo.pack(side="right", padx=(2, 0))
        
        # Left Panel (Preview)
        preview_panel = ctk.CTkFrame(self.container, fg_color="#171717", corner_radius=10)
        preview_panel.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=10)
        preview_panel.grid_rowconfigure(1, weight=1)
        preview_panel.grid_columnconfigure(0, weight=1)
        
        lbl_container = ctk.CTkFrame(preview_panel, fg_color="transparent")
        lbl_container.grid(row=0, column=0, pady=(10, 0))
        ctk.CTkLabel(lbl_container, text="SVG Vector Comparison", font=ctk.CTkFont(family="Roboto", size=14, weight="bold")).pack()
        self.lbl_svg_info = ctk.CTkLabel(
            lbl_container, 
            text="Total Paths: 0 | Total Nodes: 0 | Colors: 0", 
            font=ctk.CTkFont(family="Roboto", size=11),
            text_color="white"
        )
        self.lbl_svg_info.pack()
        
        self.canvas_preview = tk.Canvas(preview_panel, bg="#0E0E0E", highlightthickness=0, cursor="sb_h_double_arrow")
        self.canvas_preview.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        self.canvas_preview.bind("<Configure>", self.on_resize)
        self.canvas_preview.bind("<Button-1>", self.on_mouse_down)
        self.canvas_preview.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas_preview.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        # Right Panel Container (Fixed Button at Bottom)
        right_container = ctk.CTkFrame(self.container, fg_color="#171717", corner_radius=10)
        right_container.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=10)
        right_container.grid_rowconfigure(1, weight=1)
        right_container.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(right_container, text="Settings & Tuning", font=ctk.CTkFont(size=16, weight="bold"), text_color="white").grid(row=0, column=0, sticky="w", padx=20, pady=(15, 5))
        
        settings_panel = ctk.CTkScrollableFrame(right_container, fg_color="transparent")
        settings_panel.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(right_container, fg_color="#2C2C2C", progress_color=BMTTheme.LIME)
        self.progress_bar.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 0))
        self.progress_bar.set(0)
        self.progress_bar.grid_remove()
        
        self.btn_process = ctk.CTkButton(
            right_container,
            text="Generate!",
            command=self.process_preview,
            font=button_font,
            text_color="white",
            fg_color="#2C2C2C",
            hover_color="#404040",
            state="disabled",
            height=40
        )
        self.btn_process.grid(row=3, column=0, sticky="ew", padx=20, pady=(10, 20))
        
        # Presets Section
        preset_frame = self.create_section(settings_panel, "Presets")
        self.preset_var = ctk.StringVar(value="Brawlhalla Perfect")
        self.preset_menu = ctk.CTkOptionMenu(
            preset_frame, variable=self.preset_var, values=list(self.presets.keys()), command=self.apply_preset,
            fg_color=BMTTheme.LIME, button_color=BMTTheme.ACID_GREEN, button_hover_color=BMTTheme.ACID_GREEN,
            text_color="black", font=("Roboto", 11, "bold")
        )
        self.preset_menu.pack(fill="x", padx=10, pady=5)
        
        preset_btns = ctk.CTkFrame(preset_frame, fg_color="transparent")
        preset_btns.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(preset_btns, text="Save", command=self.save_current_preset, width=60, fg_color="#303030", hover_color="#404040").pack(side="left", padx=2)
        ctk.CTkButton(preset_btns, text="Delete", command=self.delete_preset, width=60, fg_color="#602020", hover_color="#802020").pack(side="left", padx=2)
        ctk.CTkButton(preset_btns, text="Reset", command=lambda: self.apply_preset("Brawlhalla Perfect"), width=60, fg_color="#303030", hover_color="#404040").pack(side="right", padx=2)
        
        # Basic Section (Not collapsible)
        basic_frame = self.create_section(settings_panel, "Basic Settings", collapsible=False)
        
        self.create_optionmenu(basic_frame, "Color Mode", "colormode", ["color", "binary"], "Color mode (color or black and white).")
        self.create_optionmenu(basic_frame, "Trace Mode", "mode", ["spline", "polygon", "none"], "Defines how lines will be traced.")
        self.create_checkbox(basic_frame, "Hierarchical (Stacked)", "hierarchical", True, "If checked, layers are stacked. Otherwise, it cuts holes.")
        
        # Auto Optimization
        self.auto_opt_var = tk.BooleanVar(value=False)
        self.chk_auto = ctk.CTkCheckBox(
            basic_frame, text="Enable Auto Optimization", variable=self.auto_opt_var, 
            command=self._toggle_auto_opt, font=("Roboto", 12, "bold"),
            fg_color=BMTTheme.LIME, hover_color=BMTTheme.ACID_GREEN
        )
        self.chk_auto.pack(pady=5, padx=10, anchor="w")
        self.auto_sliders_frame = ctk.CTkFrame(basic_frame, fg_color="transparent")
        self.create_slider(self.auto_sliders_frame, "Target Color Quality", "target_quality", 50, 99, 90, "Target color similarity score (50-99%) (Lower reduces quality target, higher requires better quality).")
        self.create_slider(self.auto_sliders_frame, "Max Iterations", "auto_max_iters", 1, 10, 4, "Maximum self-verification retries (Lower retries less, higher retries more).")
        
        # Color Post-Processing
        color_frame = self.create_section(settings_panel, "Color Quantization")
        self.create_slider(color_frame, "Color precision", "color_precision", 1, 32, 16, "Internal VTracer precision (Lower uses more colors, higher uses fewer colors).")
        self.create_slider(color_frame, "Layer Difference", "layer_difference", 1, 12, 6, "Threshold for merging similar layers (Lower merges fewer layers, higher merges more layers).")
        
        self.create_slider(color_frame, "Color Spatial Radius", "spatial_radius", 1, 8, 3, "Analyzes NxN blocks to find regional colors (Lower analyzes smaller blocks, higher analyzes larger blocks).")
        self.create_slider(color_frame, "Color Merge Threshold", "merge_threshold", 0, 200, 30, "Similarity threshold for merging colors (Lower merges only very similar colors, higher merges more distinct colors).")
        
        self.color_slider, self.color_slider_lbl = self.create_dynamic_slider(
            color_frame, "Max Palette Colors", "max_palette_colors", 2, 256, 32, 
            "Limits the final SVG colors. Post-process real-time (Lower uses fewer colors, higher allows more colors).", self.on_palette_slider_change)
            
        # Path Optimization
        path_frame = self.create_section(settings_panel, "Path Optimization")
        
        self.simplify_paths_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(path_frame, text="Post-Simplify Paths", variable=self.simplify_paths_var, font=("Roboto", 12), fg_color=BMTTheme.LIME, hover_color=BMTTheme.ACID_GREEN).pack(pady=5, padx=10, anchor="w")
        
        self.create_slider(path_frame, "Filter Speckle (Noise)", "filter_speckle", 0, 16, 10, "Removes small specks or noise from the image (Lower keeps more noise, higher removes more noise).")
        self.create_slider(path_frame, "Corner Threshold", "corner_threshold", 1, 100, 60, "Angle threshold for detecting sharp corners (Lower detects sharper corners, higher allows smoother corners).")
        self.create_slider(path_frame, "Length Threshold", "length_threshold", 1, 100, 30, "Minimum length for merging short segments (Lower keeps shorter segments, higher merges longer segments).")
        self.create_slider(path_frame, "Splice Threshold", "splice_threshold", 1, 100, 45, "Threshold for splicing nearby paths (Lower splices closer paths, higher splices further paths).")
        self.create_slider(path_frame, "Path Precision", "path_precision", 1, 10, 8, "Overall precision when processing vector paths (Lower uses fewer points, higher uses more points).")
        self.create_slider(path_frame, "Max Iterations", "max_iterations", 1, 30, 16, "Maximum iterations of the curve optimizer (Lower is faster but less optimized, higher optimizes more).")
        
        # Post Optimizer
        self.post_opt_frame = self.create_section(settings_panel, "Post Optimizer", collapsible=True)
        self.post_btns = []
        
        def create_post_btn(text, color, tooltip, cmd):
            btn = ctk.CTkButton(
                self.post_opt_frame, text=text, fg_color="#2A2A2A", border_color=color, border_width=2,
                text_color="white", hover_color="#383838", state="disabled", font=("Roboto", 11, "bold"),
                command=cmd
            )
            btn.pack(fill="x", padx=10, pady=2)
            BMTToolTip(btn, tooltip)
            self.post_btns.append(btn)
            
        create_post_btn("Node Optimizer", "#00FFFF", "Rounds coordinates to nearest integer to drastically reduce file size and simplify curves.", self.opt_node_optimizer)
        create_post_btn("Precision Deflator", "#FFFF00", "Applies a self-colored 0.5px stroke to eliminate garbage lines/artifacts between overlapping edges.", self.opt_precision_deflator)
        
        # Palette UI
        palette_header = ctk.CTkFrame(color_frame, fg_color="transparent")
        palette_header.pack(fill="x", padx=10, pady=(10, 0))
        ctk.CTkLabel(palette_header, text="Final Color Palette", text_color="white", font=ctk.CTkFont(weight="bold")).pack(side="left")
        
        self.container.winfo_toplevel().bind("<Control-z>", self._undo)
        self.container.winfo_toplevel().bind("<Control-y>", self._redo)
        
        # Check Compatibility Checkbox
        self.check_compat_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(color_frame, text="Check Compatibility (Color Map)", variable=self.check_compat_var, 
                        font=("Roboto", 11, "bold"), fg_color=BMTTheme.LIME, hover_color=BMTTheme.ACID_GREEN, 
                        command=self.apply_post_processing).pack(anchor="w", padx=10, pady=(0, 5))
        
        # Legend (Wrap-friendly)
        legend_frame = ctk.CTkFrame(color_frame, fg_color="transparent")
        legend_frame.pack(fill="x", padx=10, pady=(0, 5))
        ctk.CTkLabel(legend_frame, text="Color Swap:", font=("Roboto", 10, "bold"), text_color="#A0A0A0").pack(side="left", padx=(0,5))
        
        def create_status_legend(parent, text, color):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.pack(side="left", padx=2)
            c = tk.Canvas(f, width=12, height=12, bg="#2B2B2B", highlightthickness=0)
            c.pack(side="left", pady=2)
            c.create_oval(1, 1, 11, 11, fill=color, outline="")
            ctk.CTkLabel(f, text=text, font=("Roboto", 9)).pack(side="left", padx=2)
            
        create_status_legend(legend_frame, "Unknown", "#FFFFFF")
        create_status_legend(legend_frame, "Match", "#32CD32")
        create_status_legend(legend_frame, "Failed", "#FF3333")
        
        # Import Options
        import_opt_frame = ctk.CTkFrame(color_frame, fg_color="transparent")
        import_opt_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        self.import_threshold_var = tk.DoubleVar(value=25.0)
        ctk.CTkLabel(import_opt_frame, text="Tolerance:", font=("Roboto", 10)).pack(side="left")
        
        self.lbl_import_thresh = ctk.CTkEntry(import_opt_frame, width=45, height=20, font=("Roboto", 10, "bold"), justify="right")
        self.lbl_import_thresh.pack(side="right", padx=(5, 10))
        self.lbl_import_thresh.insert(0, "25.0%")
        
        def _update_import_lbl(val):
            if self.lbl_import_thresh.focus_get() != self.lbl_import_thresh:
                self.lbl_import_thresh.delete(0, tk.END)
                self.lbl_import_thresh.insert(0, f"{float(val):.1f}%")
            
        def _on_import_entry(event):
            try:
                val = float(self.lbl_import_thresh.get().replace('%', ''))
                val = max(0.0, min(100.0, val))
                self.import_threshold_var.set(val)
                self.lbl_import_thresh.delete(0, tk.END)
                self.lbl_import_thresh.insert(0, f"{val:.1f}%")
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid number.")
                self.lbl_import_thresh.delete(0, tk.END)
                self.lbl_import_thresh.insert(0, f"{self.import_threshold_var.get():.1f}%")
                
        self.lbl_import_thresh.bind("<Return>", _on_import_entry)
        self.lbl_import_thresh.bind("<FocusOut>", _on_import_entry)
        
        sl_thresh = ctk.CTkSlider(
            import_opt_frame, variable=self.import_threshold_var, from_=0.0, to=100.0, number_of_steps=1000, 
            command=_update_import_lbl, button_color=self.current_color, button_hover_color=self.current_color
        )
        sl_thresh.pack(fill="x", expand=True, padx=5, pady=2)
        
        # Import ComboBox
        import_frame = ctk.CTkFrame(color_frame, fg_color="transparent")
        import_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        self.import_mode_var = ctk.StringVar(value="Import Palette From...")
        modes = ["Import Palette From...", "Shapes (.svg)", "Text File (.txt)", "Scripts (.as)", "Manual Entry"]
        
        def on_import_select(val):
            if val == "Shapes (.svg)": self.import_palette_shapes()
            elif val == "Text File (.txt)": self.import_palette_txt()
            elif val == "Scripts (.as)": self.import_palette_as()
            elif val == "Manual Entry": self.import_palette_manual()
            self.import_mode_var.set("Import Palette From...")
            
        import_combo = ctk.CTkOptionMenu(
            import_frame, variable=self.import_mode_var, values=modes, command=on_import_select, 
            fg_color=BMTTheme.LIME, button_color=BMTTheme.ACID_GREEN, button_hover_color=BMTTheme.ACID_GREEN, 
            text_color="black", font=("Roboto", 11, "bold")
        )
        import_combo.pack(side="left", fill="x", expand=True)
        
        btn_reset = ctk.CTkButton(
            import_frame, text="↺ Reset", width=40, font=("Roboto", 11, "bold"),
            fg_color="#802020", hover_color="#C03030", command=self._reset_swap
        )
        btn_reset.pack(side="left", padx=(5, 0))
        
        self.palette_colors_frame = ctk.CTkFrame(color_frame, fg_color="transparent")
        self.palette_colors_frame.pack(fill="x", padx=10, pady=5)
        
        self.palette_canvas = tk.Canvas(self.palette_colors_frame, bg="#171717", highlightthickness=0, height=100)
        self.palette_canvas.pack(fill="both", expand=True)
        self.palette_canvas.bind("<Configure>", lambda e: self.update_palette_ui())
        self.palette_canvas.bind("<Motion>", self.on_palette_hover)
        self.palette_canvas.bind("<Button-1>", self.on_palette_click)
        self.palette_canvas.bind("<Button-3>", self.on_palette_right_click)
        
        # Load default preset on startup
        self.apply_preset("Brawlhalla Perfect")

    def create_section(self, parent, title, collapsible=True):
        frame = ctk.CTkFrame(parent, fg_color="#242424", corner_radius=8)
        frame.pack(fill="x", padx=10, pady=5)
        
        inner_frame = ctk.CTkFrame(frame, fg_color="transparent")
        
        if collapsible:
            def toggle():
                if inner_frame.winfo_ismapped():
                    inner_frame.pack_forget()
                    btn.configure(text="▶ " + title)
                else:
                    inner_frame.pack(fill="x", padx=5, pady=(0, 5))
                    btn.configure(text="▼ " + title)
                    
            btn = ctk.CTkButton(frame, text="▼ " + title, anchor="w", fg_color="transparent", text_color="white", 
                                font=ctk.CTkFont(weight="bold", size=13), hover_color="#333333", command=toggle)
            btn.pack(fill="x", padx=2, pady=2)
            inner_frame.pack(fill="x", padx=5, pady=(0, 5))
            return inner_frame
        else:
            lbl = ctk.CTkLabel(frame, text=title, text_color="white", font=ctk.CTkFont(weight="bold", size=13))
            lbl.pack(anchor="w", padx=10, pady=5)
            inner_frame.pack(fill="x", padx=5, pady=(0, 5))
            return inner_frame
        
    def create_optionmenu(self, parent, label, key, values, tooltip_text):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=5)
        lbl = ctk.CTkLabel(frame, text=label, text_color="#A0A0A0")
        lbl.pack(side="left")
        BMTToolTip(lbl, tooltip_text)
        
        var = ctk.StringVar(value=values[0])
        self.settings[key] = var
        menu = ctk.CTkOptionMenu(frame, variable=var, values=values, fg_color="#2C2C2C", button_color="#2C2C2C", button_hover_color="#404040")
        menu.pack(side="right")
        
    def create_checkbox(self, parent, label, key, default, tooltip_text):
        var = ctk.BooleanVar(value=default)
        self.settings[key] = var
        cb = ctk.CTkCheckBox(parent, text=label, variable=var, fg_color=BMTTheme.LIME, hover_color=BMTTheme.ACID_GREEN)
        cb.pack(fill="x", padx=10, pady=5)
        BMTToolTip(cb, tooltip_text)
        
    def create_slider(self, parent, label, key, min_val, max_val, default, tooltip_text, command=None):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=5)
        
        lbl_frame = ctk.CTkFrame(frame, fg_color="transparent")
        lbl_frame.pack(fill="x")
        lbl = ctk.CTkLabel(lbl_frame, text=label, text_color="#A0A0A0")
        lbl.pack(side="left")
        BMTToolTip(lbl, tooltip_text)
        
        var = ctk.DoubleVar(value=default)
        self.settings[key] = var
        
        val_entry = ctk.CTkEntry(lbl_frame, width=40, height=20, font=ctk.CTkFont(weight="bold"), justify="right")
        val_entry.pack(side="right")
        val_entry.insert(0, str(default))
        self.slider_labels[key] = val_entry
        
        def _on_manual_entry(event):
            try:
                val = float(val_entry.get())
                if val < min_val:
                    val = min_val
                elif val > max_val:
                    val = max_val
                var.set(val)
                val_entry.delete(0, tk.END)
                val_entry.insert(0, str(int(val)))
                if command: command(int(val))
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid number.")
                val_entry.delete(0, tk.END)
                val_entry.insert(0, str(int(var.get())))
                
        val_entry.bind("<Return>", _on_manual_entry)
        val_entry.bind("<FocusOut>", _on_manual_entry)
        
        def on_change(val):
            if val_entry.focus_get() != val_entry:
                val_entry.delete(0, tk.END)
                val_entry.insert(0, str(int(val)))
            if command:
                command(int(val))
            
        slider = ctk.CTkSlider(frame, variable=var, from_=min_val, to=max_val, number_of_steps=int(max_val-min_val), 
                               button_color=self.current_color, button_hover_color=self.current_color, command=on_change)
        slider.pack(fill="x", pady=(5, 0))
        return slider
        
    def create_dynamic_slider(self, parent, label, key, min_val, max_val, default, tooltip_text, command=None):
        slider = self.create_slider(parent, label, key, min_val, max_val, default, tooltip_text, command)
        return slider, self.slider_labels[key]

    def _toggle_auto_opt(self):
        if self.auto_opt_var.get():
            self.auto_sliders_frame.pack(fill="x", expand=True)
        else:
            self.auto_sliders_frame.pack_forget()

    def apply_preset(self, preset_name):
        if preset_name not in self.presets: return
        p = self.presets[preset_name]
        for k, v in p.items():
            if k in self.settings:
                if isinstance(self.settings[k], ctk.BooleanVar):
                    self.settings[k].set(v)
                elif isinstance(self.settings[k], ctk.StringVar):
                    self.settings[k].set(v)
                elif isinstance(self.settings[k], ctk.DoubleVar):
                    self.settings[k].set(float(v))
                    if k in self.slider_labels:
                        self.slider_labels[k].delete(0, tk.END)
                        self.slider_labels[k].insert(0, str(int(v)))

    def save_current_preset(self):
        name = ctk.CTkInputDialog(text="Enter preset name:", title="Save Preset").get_input()
        if not name or name == "Brawlhalla Perfect": return
        p = {}
        for k, var in self.settings.items():
            if k in ["max_palette_colors", "target_quality", "auto_max_iters"]: continue 
            p[k] = var.get()
        self.presets[name] = p
        self.save_presets()
        self.preset_menu.configure(values=list(self.presets.keys()))
        self.preset_var.set(name)
        
    def delete_preset(self):
        name = self.preset_var.get()
        if name == "Brawlhalla Perfect": return
        if name in self.presets:
            del self.presets[name]
            self.save_presets()
            self.preset_menu.configure(values=list(self.presets.keys()))
            self.apply_preset("Brawlhalla Perfect")
            self.preset_var.set("Brawlhalla Perfect")

    def on_palette_slider_change(self, val):
        if not self.preview_img or not self.dominant_colors: return
        if self.palette_timer:
            self.container.after_cancel(self.palette_timer)
        self.palette_timer = self.container.after(300, self.apply_post_processing)
        
    def import_image(self):
        path = filedialog.askopenfilename(
            title="Select Image to Vectorize",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        if not path: return
        
        self.input_path = path
        self.original_img = Image.open(path).convert("RGBA")
        self.preview_img = None
        self._resized_orig = None
        self._resized_prev = None
        self.slider_ratio = 1.0
        self.dominant_colors = []
        self.current_palette = []
        self.color_overrides = {}
        
        self.btn_process.configure(state="normal")
        self.btn_export.configure(state="disabled")
        
        self._update_canvases()
        
    def on_resize(self, event):
        if self.original_img:
            self._update_canvases()

    def on_mouse_down(self, event):
        if not self.original_img: return
        self.is_dragging = True
        self.on_mouse_drag(event)

    def on_mouse_drag(self, event):
        if not self.is_dragging or not self.original_img: return
        cw = self.canvas_preview.winfo_width()
        if cw <= 0: return
        
        self.slider_ratio = max(0.0, min(1.0, event.x / cw))
        self._draw_slider_view()

    def on_mouse_up(self, event):
        self.is_dragging = False

    def _update_canvases(self):
        if not self.original_img: return
        
        cw = self.canvas_preview.winfo_width()
        ch = self.canvas_preview.winfo_height()
        if cw < 10 or ch < 10: return
        
        if cw != self._cached_w or ch != self._cached_h or self._resized_orig is None:
            img_w, img_h = self.original_img.size
            ratio = min(cw/img_w, ch/img_h)
            nw, nh = int(img_w * ratio), int(img_h * ratio)
            
            bg = Image.new("RGBA", (cw, ch), (26, 26, 26, 255))
            draw = ImageDraw.Draw(bg)
            sq = 20
            for y in range(0, ch, sq):
                for x in range(0, cw, sq):
                    if (x // sq + y // sq) % 2 == 0:
                        draw.rectangle([x, y, x+sq, y+sq], fill=(38, 38, 38, 255))
            
            res_o = self.original_img.resize((nw, nh), Image.LANCZOS)
            final_o = bg.copy()
            final_o.paste(res_o, ((cw - nw) // 2, (ch - nh) // 2), res_o)
            self._resized_orig = final_o
            
            if self.preview_img:
                res_p = self.preview_img.resize((nw, nh), Image.LANCZOS)
                final_p = bg.copy()
                final_p.paste(res_p, ((cw - nw) // 2, (ch - nh) // 2), res_p)
                self._resized_prev = final_p
            else:
                self._resized_prev = None
                
            self._cached_w = cw
            self._cached_h = ch

        self._draw_slider_view()
        
    def _draw_slider_view(self):
        cw = self._cached_w
        ch = self._cached_h
        if cw <= 0 or ch <= 0: return
        
        self.canvas_preview.delete("all")
        
        if not self.preview_img:
            if self._resized_orig:
                self.tk_orig = ImageTk.PhotoImage(self._resized_orig)
                self.canvas_preview.create_image(0, 0, image=self.tk_orig, anchor="nw")
            self.canvas_preview.create_text(cw//2, ch-30, text="Click 'Generate!'", fill="#A0A0A0", font=("Roboto", 14))
            return
            
        split_x = int(cw * self.slider_ratio)
        
        if self._resized_prev and split_x > 0:
            cropped_prev = self._resized_prev.crop((0, 0, split_x, ch))
            self.tk_prev = ImageTk.PhotoImage(cropped_prev)
            self.canvas_preview.create_image(0, 0, image=self.tk_prev, anchor="nw")
            
        if self._resized_orig and split_x < cw:
            cropped_orig = self._resized_orig.crop((split_x, 0, cw, ch))
            self.tk_orig = ImageTk.PhotoImage(cropped_orig)
            self.canvas_preview.create_image(split_x, 0, image=self.tk_orig, anchor="nw")
            
        self.canvas_preview.create_line(split_x, 0, split_x, ch, fill=self.current_color, width=3)
        self.canvas_preview.create_oval(split_x-5, ch//2-5, split_x+5, ch//2+5, fill=self.current_color, outline="")
        
        self.canvas_preview.create_rectangle(5, 5, 80, 35, fill="#171717", outline="")
        self.canvas_preview.create_text(15, 20, text="Vector", fill="white", anchor="w", font=("Roboto", 14, "bold"))
        
        self.canvas_preview.create_rectangle(cw-90, 5, cw-5, 35, fill="#171717", outline="")
        self.canvas_preview.create_text(cw-15, 20, text="Original", fill="white", anchor="e", font=("Roboto", 14, "bold"))

    def extract_dominant_colors(self, img):
        if not img: return
        
        radius = int(self.settings["spatial_radius"].get())
        
        w, h = img.size
        pixels = img.load()
        
        local_modes = {}
        
        for y in range(0, h, radius):
            time.sleep(0.001) # Yield GIL to prevent full freeze
            for x in range(0, w, radius):
                block_counts = {}
                for by in range(y, min(y + radius, h)):
                    for bx in range(x, min(x + radius, w)):
                        rgba = pixels[bx, by]
                        if len(rgba) == 4 and rgba[3] < 128: continue
                        rgb = rgba[:3]
                        block_counts[rgb] = block_counts.get(rgb, 0) + 1
                        
                if block_counts:
                    mode_color = max(block_counts.items(), key=lambda item: item[1])[0]
                    local_modes[mode_color] = local_modes.get(mode_color, 0) + 1
                    
        valid_colors = sorted(local_modes.items(), key=lambda item: item[1], reverse=True)
        
        dom_colors = []
        min_dist_sq = int(self.settings["merge_threshold"].get()) 
        
        for rgb, count in valid_colors:
            is_unique = True
            for i, (dom, dcount) in enumerate(dom_colors):
                dist = (rgb[0]-dom[0])**2 + (rgb[1]-dom[1])**2 + (rgb[2]-dom[2])**2
                if dist < min_dist_sq:
                    is_unique = False
                    dom_colors[i] = (dom, dcount + count)
                    break
            if is_unique:
                dom_colors.append((rgb, count))
                
        dom_colors.sort(key=lambda x: x[1], reverse=True)
        self.dominant_colors = [rgb for rgb, count in dom_colors]
        
        # Auto-calculate recommended palette size to ignore trailing junk colors
        total_blocks = sum(count for _, count in dom_colors)
        cumulative = 0
        recommended = len(self.dominant_colors)
        for i, (rgb, count) in enumerate(dom_colors):
            cumulative += count
            if cumulative / total_blocks > 0.98: # Covers 98% of the image structure
                recommended = max(4, i + 1)
                break
                
        # Add generous margin for small details (eyes, tiny fx)
        self.recommended_colors = min(256, int(recommended * 1.1) + 12)

    def opt_node_optimizer(self): self._run_opt_task("Optimizing Nodes...", self._do_node_optimizer)
    def opt_precision_deflator(self): self._run_opt_task("Deflating Precision...", self._do_precision_deflator)

    def _run_opt_task(self, msg, func):
        self.btn_process.configure(text=msg)
        self.container.update()
        
        def worker():
            try:
                if os.path.exists(self.output_temp):
                    with open(self.output_temp, "r", encoding="utf-8") as f:
                        svg_data = f.read()
                        
                    import copy
                    state = (svg_data, copy.deepcopy(self.dominant_colors))
                    
                    new_svg = func(svg_data)
                    if new_svg:
                        with open(self.output_temp, "w", encoding="utf-8") as f:
                            f.write(new_svg)
                            
                        def add_undo():
                            self.history_undo.append(state)
                            if len(self.history_undo) > 10: self.history_undo.pop(0)
                            self.history_redo.clear()
                        self.container.after(0, add_undo)
            except Exception as e:
                print(f"[SVG Maker] Optimizer Error: {e}")
                
            self.container.after(0, lambda: self.btn_process.configure(text="Generate!"))
            self.container.after(0, self.apply_post_processing)
            
        import threading
        threading.Thread(target=worker, daemon=True).start()

    def _save_history_state(self):
        if not os.path.exists(self.output_temp): return
        with open(self.output_temp, "r", encoding="utf-8") as f:
            svg = f.read()
        import copy
        self.history_undo.append((svg, copy.deepcopy(self.dominant_colors)))
        if len(self.history_undo) > 10: self.history_undo.pop(0)
        self.history_redo.clear()

    def _undo(self, event=None):
        if not self.history_undo: return
        with open(self.output_temp, "r", encoding="utf-8") as f:
            current_svg = f.read()
        import copy
        self.history_redo.append((current_svg, copy.deepcopy(self.dominant_colors)))
        if len(self.history_redo) > 10: self.history_redo.pop(0)
        
        state = self.history_undo.pop()
        with open(self.output_temp, "w", encoding="utf-8") as f:
            f.write(state[0])
        self.dominant_colors = copy.deepcopy(state[1])
        self.update_palette_ui()
        self.apply_post_processing()
        
    def _redo(self, event=None):
        if not self.history_redo: return
        with open(self.output_temp, "r", encoding="utf-8") as f:
            current_svg = f.read()
        import copy
        self.history_undo.append((current_svg, copy.deepcopy(self.dominant_colors)))
        
        state = self.history_redo.pop()
        with open(self.output_temp, "w", encoding="utf-8") as f:
            f.write(state[0])
        self.dominant_colors = copy.deepcopy(state[1])
        self.update_palette_ui()
        self.apply_post_processing()

    def _do_node_optimizer(self, svg_data):
        def optimize_d(match):
            d = match.group(1)
            tokens = re.findall(r'[a-zA-Z]|[-+]?\d*\.?\d+', d)
            commands = []
            i = 0
            curr_cmd = 'M'
            while i < len(tokens):
                tk = tokens[i]
                if tk.isalpha():
                    curr_cmd = tk
                    i += 1
                if curr_cmd.upper() == 'Z':
                    commands.append(('Z', []))
                    continue
                coords = []
                while i < len(tokens) and not tokens[i].isalpha():
                    coords.append(float(tokens[i]))
                    i += 1
                if coords:
                    commands.append((curr_cmd, coords))
            
            curr_x, curr_y, path_start_x, path_start_y = 0.0, 0.0, 0.0, 0.0
            abs_commands = []
            for cmd, coords in commands:
                upper = cmd.upper()
                is_rel = cmd.islower()
                j = 0
                while j < len(coords):
                    if upper == 'M':
                        x, y = coords[j:j+2]
                        if is_rel: x += curr_x; y += curr_y
                        curr_x, curr_y, path_start_x, path_start_y = x, y, x, y
                        abs_commands.append(('M', [x, y]))
                        j += 2
                        is_rel = False
                        upper = 'L' 
                    elif upper == 'L':
                        x, y = coords[j:j+2]
                        if is_rel: x += curr_x; y += curr_y
                        curr_x, curr_y = x, y
                        abs_commands.append(('L', [x, y]))
                        j += 2
                    elif upper == 'C':
                        if j + 5 < len(coords):
                            x1, y1, x2, y2, x3, y3 = coords[j:j+6]
                            if is_rel: x1+=curr_x; y1+=curr_y; x2+=curr_x; y2+=curr_y; x3+=curr_x; y3+=curr_y
                            curr_x, curr_y = x3, y3
                            abs_commands.append(('C', [x1,y1,x2,y2,x3,y3]))
                            j += 6
                        else: break
                    elif upper == 'Z':
                        curr_x, curr_y = path_start_x, path_start_y
                        abs_commands.append(('Z', []))
                        break
                    else: j += 1 

            filtered = []
            last_x, last_y = None, None
            for cmd, coords in abs_commands:
                if cmd == 'Z': filtered.append((cmd, coords))
                elif cmd == 'M':
                    last_x, last_y = coords[0], coords[1]
                    filtered.append((cmd, coords))
                elif cmd == 'L':
                    x, y = coords[0], coords[1]
                    if last_x is None or abs(x - last_x) > 3.0 or abs(y - last_y) > 3.0:
                        filtered.append((cmd, coords))
                        last_x, last_y = x, y
                elif cmd == 'C':
                    x3, y3 = coords[4], coords[5]
                    if last_x is None or abs(x3 - last_x) > 3.0 or abs(y3 - last_y) > 3.0:
                        filtered.append((cmd, coords))
                        last_x, last_y = x3, y3
                        
            res = []
            for cmd, coords in filtered:
                res.append(cmd)
                res.extend([str(round(c, 1)) for c in coords])
            return f'd="{" ".join(res)}"'
        return re.sub(r'd="([^"]+)"', optimize_d, svg_data)


    def _do_precision_deflator(self, svg_data):
        def add_stroke(match):
            tag = match.group(0)
            f_match = re.search(r'fill="#([0-9a-fA-F]+)"', tag)
            if f_match and 'stroke=' not in tag:
                fill = f_match.group(1)
                return tag.replace('/>', f' stroke="#{fill}" stroke-width="0.5"/>')
            return tag
        return re.sub(r'<path[^>]+>', add_stroke, svg_data)


    def apply_post_processing(self):
        if not os.path.exists(self.output_temp) or not self.dominant_colors: return
        
        max_cols = int(self.settings["max_palette_colors"].get())
        palette = self.dominant_colors[:max_cols]
        
        try:
            with open(self.output_temp, "r") as f:
                svg_data = f.read()
                
            def map_color(match):
                color = match.group(1).lower()
                if len(color) == 3:
                    r, g, b = int(color[0]*2, 16), int(color[1]*2, 16), int(color[2]*2, 16)
                elif len(color) == 6:
                    r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
                else:
                    return match.group(0)
                    
                closest = min(palette, key=lambda c: (c[0]-r)**2 + (c[1]-g)**2 + (c[2]-b)**2)
                
                if getattr(self, 'check_compat_var', None) and self.check_compat_var.get():
                    status = self.color_swap_status.get(closest, 'unknown')
                    if status == 'compatible': return '#32cd32'
                    elif status == 'incompatible': return '#ff3333'
                    else: return '#ffffff'
                    
                final_color = self.color_overrides.get(closest, closest)
                return f'#{final_color[0]:02x}{final_color[1]:02x}{final_color[2]:02x}'
                
            new_svg = re.sub(r'#([0-9a-fA-F]{3,6})\b', map_color, svg_data)
            
            with open(self.output_post_temp, "w") as f:
                f.write(new_svg)
                
            self.current_palette = palette
            self.update_palette_ui()
            
            if hasattr(self, 'lbl_svg_info'):
                try:
                    paths = svg_data.count('<path')
                    nodes = sum(svg_data.count(char) for char in 'CcLlMmZz')
                    self.lbl_svg_info.configure(text=f"Total Paths: {paths} | Total Nodes: {nodes} | Colors: {len(palette)}")
                except:
                    pass
            
            self._render_skia_preview(self.output_post_temp)
            self._cached_w = 0 
            self._update_canvases()
        except Exception as e:
            print(f"[SVG Maker] Post-processing error: {e}")

    def update_palette_ui(self):
        self.palette_canvas.delete("all")
        self.palette_bboxes = []
        if not self.current_palette: return
        
        cw = self.palette_canvas.winfo_width()
        if cw <= 10: return
        
        num_colors = len(self.current_palette)
        margin = 15
        max_cols = 6
        cols = min(num_colors, max_cols)
        rows = math.ceil(num_colors / cols)
        
        available_width = cw - (cols + 1) * margin
        circle_size = min(60, available_width // cols)
        if circle_size < 10: circle_size = 10
        
        required_height = rows * (circle_size + margin) + margin
        self.palette_canvas.configure(height=required_height)
        
        for i, orig_rgb in enumerate(self.current_palette):
            current_rgb = self.color_overrides.get(orig_rgb, orig_rgb)
            orig_hex = f'#{orig_rgb[0]:02x}{orig_rgb[1]:02x}{orig_rgb[2]:02x}'
            curr_hex = f'#{current_rgb[0]:02x}{current_rgb[1]:02x}{current_rgb[2]:02x}'
            
            c = i % cols
            r = i // cols
            
            x0 = margin + c * (circle_size + margin)
            y0 = margin + r * (circle_size + margin)
            x1 = x0 + circle_size
            y1 = y0 + circle_size
            
            self.palette_bboxes.append((x0, y0, x1, y1, orig_rgb, curr_hex))
            
            status = self.color_swap_status.get(orig_rgb, 'unknown')
            outline_color = "#FFFFFF" if status == 'unknown' else "#32CD32" if status == 'compatible' else "#FF3333"
            self.palette_canvas.create_oval(x0-3, y0-3, x1+3, y1+3, fill=outline_color, outline="")
            
            if orig_hex != curr_hex:
                self.palette_canvas.create_arc(x0, y0, x1, y1, start=90, extent=180, fill=orig_hex, outline="")
                self.palette_canvas.create_arc(x0, y0, x1, y1, start=270, extent=180, fill=curr_hex, outline="")
                self.palette_canvas.create_line(x0 + circle_size//2, y0, x0 + circle_size//2, y1, fill="#FFFFFF")
            else:
                self.palette_canvas.create_oval(x0, y0, x1, y1, fill=curr_hex, outline="")

    def get_hovered_palette(self, x, y):
        for i, (x0, y0, x1, y1, orig, curr) in enumerate(self.palette_bboxes):
            if x0 <= x <= x1 and y0 <= y <= y1:
                return i, x0, y0, x1, y1, orig, curr
        return None
        
    def on_palette_hover(self, event):
        self.palette_canvas.delete("edit_icon")
        self.palette_canvas.config(cursor="arrow")
        hit = self.get_hovered_palette(event.x, event.y)
        if hit:
            i, x0, y0, x1, y1, orig, curr = hit
            self.palette_canvas.config(cursor="hand2")
            cx, cy = (x0+x1)//2, (y0+y1)//2
            if getattr(self, 'edit_icon_img', None):
                self.palette_canvas.create_image(cx, cy, image=self.edit_icon_img, tags="edit_icon")
            else:
                self.palette_canvas.create_text(cx, cy, text="✎", fill="white", tags="edit_icon", font=("Arial", 16))
                
    def _change_palette_color(self, idx, btn):
        if not self.dominant_colors: return
        from tkinter.colorchooser import askcolor
        new_color = askcolor(initialcolor=f'#{self.dominant_colors[idx][0]:02x}{self.dominant_colors[idx][1]:02x}{self.dominant_colors[idx][2]:02x}')[1]
        if new_color:
            self._save_history_state()
            h = new_color.lstrip('#')
            rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
            orig = self.dominant_colors[idx]
            self.color_overrides[orig] = rgb
            self.apply_post_processing()

    def on_palette_click(self, event):
        hit = self.get_hovered_palette(event.x, event.y)
        if hit and HAS_VCP:
            i, x0, y0, x1, y1, orig, curr = hit
            new_color = ask_color(self.container, initial_hex=curr)
            if new_color:
                self._save_history_state()
                h = new_color.lstrip('#')
                self.color_overrides[orig] = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
                self.color_swap_status[orig] = 'compatible'
                self.apply_post_processing()

    def on_palette_right_click(self, event):
        hit = self.get_hovered_palette(event.x, event.y)
        if hit:
            i, x0, y0, x1, y1, orig, curr = hit
            if orig in self.color_overrides:
                del self.color_overrides[orig]
            self.color_swap_status[orig] = 'unknown'
            self.apply_post_processing()

    def _render_skia_preview(self, svg_path):
        if not HAS_SKIA: return
        try:
            stream = skia.Stream.MakeFromFile(svg_path)
            svg_dom = skia.SVGDOM.MakeFromStream(stream)
            if svg_dom:
                w, h = self.original_img.size
                surface = skia.Surface(w, h)
                canvas = surface.getCanvas()
                canvas.clear(skia.ColorTRANSPARENT)
                
                cw, ch = svg_dom.containerSize().width(), svg_dom.containerSize().height()
                if cw > 0 and ch > 0:
                    canvas.scale(w / cw, h / ch)
                
                svg_dom.render(canvas)
                image = surface.makeImageSnapshot()
                self.preview_img = Image.fromarray(image.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType), 'RGBA')
        except Exception as e:
            print(f"[SVG Maker] Skia render error: {e}")
            
    def calculate_similarity(self, img1, img2):
        if not img1 or not img2: return 0.0, 0.0
        i1 = img1.resize((64, 64), Image.BILINEAR).convert("RGB")
        i2 = img2.resize((64, 64), Image.BILINEAR).convert("RGB")
        d1 = list(i1.getdata())
        d2 = list(i2.getdata())
        
        diff_struct = 0
        diff_color = 0
        for (r1,g1,b1), (r2,g2,b2) in zip(d1, d2):
            lum1 = r1*0.299 + g1*0.587 + b1*0.114
            lum2 = r2*0.299 + g2*0.587 + b2*0.114
            diff_struct += (lum1 - lum2)**2
            diff_color += (r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2
            
        max_struct = 64 * 64 * (255**2)
        max_color = 64 * 64 * 3 * (255**2)
        
        struct_score = 1.0 - (diff_struct / max_struct)
        color_score = 1.0 - (diff_color / max_color)
        return struct_score, color_score
        
    # --- Palette Import Methods ---
    def _int_to_hex(self, val):
        try:
            val = int(val)
            return '#{:06x}'.format(val).upper()
        except:
            return None

    def _hex_to_rgb(self, h):
        h = h.lstrip('#')
        if len(h) != 6: return None
        try:
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        except:
            return None

    def import_palette_shapes(self):
        paths = tk.filedialog.askopenfilenames(title="Select Shapes", filetypes=[("SVG files", "*.svg")])
        if not paths: return
        imported = set()
        import re
        for p in paths:
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    fills = re.findall(r'fill="#([0-9a-fA-F]{6})"', f.read())
                    for hx in fills: imported.add(self._hex_to_rgb('#'+hx))
            except Exception as e: print(f"Error reading shape: {e}")
        self._remap_palette_to_imported(list(filter(None, imported)))

    def import_palette_txt(self):
        p = tk.filedialog.askopenfilename(title="Select Text File", filetypes=[("Text files", "*.txt")])
        if not p: return
        imported = set()
        import re
        try:
            with open(p, 'r', encoding='utf-8') as f:
                data = f.read()
                for h in re.findall(r'#([0-9a-fA-F]{6})', data): imported.add(self._hex_to_rgb('#'+h))
                for i in re.findall(r'\b(\d{5,8})\b', data):
                    hx = self._int_to_hex(i)
                    if hx: imported.add(self._hex_to_rgb(hx))
        except Exception as e: print(f"Error reading txt: {e}")
        self._remap_palette_to_imported(list(filter(None, imported)))

    def import_palette_as(self):
        paths = tk.filedialog.askopenfilenames(title="Select AS Scripts", filetypes=[("ActionScript", "*.as")])
        if not paths: return
        imported = set()
        import re
        for p in paths:
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    match = re.search(r'this\.a\s*=\s*\[(.*?)\]', f.read())
                    if match:
                        for n in match.group(1).split(','):
                            hx = self._int_to_hex(n.strip())
                            if hx: imported.add(self._hex_to_rgb(hx))
            except Exception as e: print(f"Error reading AS: {e}")
        self._remap_palette_to_imported(list(filter(None, imported)))
        
    def import_palette_manual(self):
        dialog = ctk.CTkInputDialog(text="Enter comma-separated Hex or Int colors:\nExample: #FF0000, 16711680, #A2F3D1", title="Manual Input")
        val = dialog.get_input()
        if not val: return
        imported = set()
        import re
        for h in re.findall(r'#([0-9a-fA-F]{6})', val): imported.add(self._hex_to_rgb('#'+h))
        for i in re.findall(r'\b(\d{5,8})\b', val):
            hx = self._int_to_hex(i)
            if hx: imported.add(self._hex_to_rgb(hx))
        self._remap_palette_to_imported(list(filter(None, imported)))
        
    def _reset_swap(self):
        self.color_overrides.clear()
        self.color_swap_status.clear()
        self.apply_post_processing()
        self.update_palette_ui()

    def _remap_palette_to_imported(self, imported_colors):
        if not imported_colors:
            messagebox.showinfo("Import", "No colors found.")
            return
            
        self.color_swap_status = {}
        import math
        
        # Escala exponencial: (x/100)^3 para que valores bajos sean muy estrictos
        pct = (self.import_threshold_var.get() / 100.0) ** 3
        tolerance = pct * 442.0  # Max Euclidean RGB distance is ~441.67
        
        for c in self.current_palette:
            # Ignore black / pure lineart (Distance to 0,0,0 <= 13)
            if math.sqrt(c[0]**2 + c[1]**2 + c[2]**2) <= 13.0:
                self.color_swap_status[c] = 'unknown'
                continue
                
            closest = min(imported_colors, key=lambda tc: sum((c[i]-tc[i])**2 for i in range(3)))
            dist = math.sqrt(sum((c[i]-closest[i])**2 for i in range(3)))
            
            if dist <= tolerance:
                self.color_overrides[c] = closest
                self.color_swap_status[closest] = 'compatible'
                self.color_swap_status[c] = 'compatible'
            else:
                self.color_swap_status[c] = 'incompatible'
                
        self.apply_post_processing()
        self.update_palette_ui()
            
    def _play_flash_animation(self, callback):
        if not self._resized_orig:
            callback()
            return
            
        w, h = self._resized_orig.size
        pixels = self._resized_orig.load()
        visited = bytearray(w * h)
        pieces = []
        
        # Fast BFS to find contiguous non-transparent pieces
        # We treat dark lineart (RGB < 40) as boundaries to successfully split interior colors into distinct pieces!
        for y in range(h):
            for x in range(w):
                idx = y * w + x
                r, g, b, a = pixels[x, y]
                is_lineart = (r < 40 and g < 40 and b < 40)
                
                if not visited[idx] and a > 0 and not is_lineart:
                    piece_pixels = []
                    queue = [(x, y)]
                    visited[idx] = 1
                    
                    head = 0
                    while head < len(queue):
                        cx, cy = queue[head]
                        head += 1
                        piece_pixels.append((cx, cy))
                        
                        for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                            nx, ny = cx + dx, cy + dy
                            if 0 <= nx < w and 0 <= ny < h:
                                nidx = ny * w + nx
                                if not visited[nidx]:
                                    r2, g2, b2, a2 = pixels[nx, ny]
                                    is_lineart2 = (r2 < 40 and g2 < 40 and b2 < 40)
                                    if a2 > 0 and not is_lineart2:
                                        visited[nidx] = 1
                                        queue.append((nx, ny))
                                        
                    if len(piece_pixels) > 10:
                        pieces.append(piece_pixels)
                else:
                    visited[idx] = 1
                    
        if not pieces:
            callback()
            return
            
        import random
        flash_img = self._resized_orig.copy()
        flash_pixels = flash_img.load()
        self.btn_process.configure(text="Scanning structural areas...")
        
        # Sort pieces from Left to Right by centroid X
        def get_centroid_x(piece):
            return sum(px for px, py in piece) / len(piece)
            
        pieces.sort(key=get_centroid_x)
        
        def animate_piece(index):
            if index >= len(pieces):
                self.container.after(600, callback)
                return
                
            # Flash multiple pieces at once if there are too many
            pieces_per_frame = max(1, len(pieces) // 10)
            
            for _ in range(pieces_per_frame):
                if index >= len(pieces): break
                neon = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255), 255)
                current_piece = pieces[index]
                
                original_colors = [(px, py, flash_pixels[px, py]) for px, py in current_piece]
                
                for px, py in current_piece:
                    flash_pixels[px, py] = neon
                    
                def revert_func(colors=original_colors):
                    for px, py, orig in colors:
                        flash_pixels[px, py] = orig
                    self.tk_prev = ImageTk.PhotoImage(flash_img)
                    self.canvas_preview.create_image(0, 0, image=self.tk_prev, anchor="nw")
                    
                self.container.after(500, revert_func)
                index += 1
                
            self.tk_prev = ImageTk.PhotoImage(flash_img)
            self.canvas_preview.create_image(0, 0, image=self.tk_prev, anchor="nw")
            
            self.container.after(80, lambda: animate_piece(index))
            
        # Start piece-by-piece animation loop
        animate_piece(0)

    def process_preview(self):
        if not self.input_path or self.is_processing: return
        
        self.is_processing = True
        self.color_overrides = {}
        self.btn_process.configure(state="disabled", fg_color="#1E1E1E", text_color="#A0A0A0")
        
        self.progress_bar.grid()
        self.progress_bar.set(0)
        self.progress_bar.start()
        
        def worker():
            try:
                # 1. Structural Scan & Noise Reduction
                self.container.after(0, lambda: self.btn_process.configure(text="Applying structural filters..."))
                img = self.original_img.copy()
                img = img.filter(ImageFilter.MedianFilter(size=3))
                
                # 2. Extract Colors
                self.container.after(0, lambda: self.btn_process.configure(text="Extracting dominant colors..."))
                self.extract_dominant_colors(img)
                
                # 3. Posterize (Flatten Colors) to remove Anti-aliasing
                self.container.after(0, lambda: self.btn_process.configure(text="Flattening color areas..."))
                cache = {}
                pixels = img.load()
                w, h = img.size
                for y in range(h):
                    if y % 50 == 0: time.sleep(0.001) # Yield GIL
                    for x in range(w):
                        r, g, b, a = pixels[x, y]
                        if a < 128:
                            pixels[x, y] = (0, 0, 0, 0)
                            continue
                        
                        rgb = (r, g, b)
                        if rgb in cache:
                            best = cache[rgb]
                        else:
                            best = min(self.dominant_colors, key=lambda c: (c[0]-r)**2 + (c[1]-g)**2 + (c[2]-b)**2)
                            cache[rgb] = best
                        pixels[x, y] = (best[0], best[1], best[2], 255)
                        
                img.save(self.input_posterized_temp)
                
                # 4. VTracer Vectorization & Auto-Optimization Loop
                self.container.after(0, lambda: self.btn_process.configure(text="Running VTracer engine..."))
                
                colormode = self.settings["colormode"].get()
                hierarchical = "stacked" if self.settings["hierarchical"].get() else "cutout"
                mode = self.settings["mode"].get()
                filter_speckle = int(self.settings["filter_speckle"].get())
                color_precision = int(self.settings["color_precision"].get())
                layer_difference = int(self.settings["layer_difference"].get())
                corner_threshold = int(self.settings["corner_threshold"].get())
                length_threshold = float(self.settings["length_threshold"].get())
                max_iterations = int(self.settings["max_iterations"].get())
                base_splice = int(self.settings["splice_threshold"].get())
                base_path = int(self.settings["path_precision"].get())
                
                is_auto = self.auto_opt_var.get()
                max_auto_iters = int(self.settings["auto_max_iters"].get()) if is_auto else 1
                target_q = float(self.settings["target_quality"].get()) / 100.0 if is_auto else 0.0
                
                best_score = -1.0
                best_svg = ""
                
                for attempt in range(max_auto_iters):
                    if is_auto:
                        self.container.after(0, lambda a=attempt+1: self.btn_process.configure(text=f"Optimization Attempt {a}/{max_auto_iters}..."))
                        
                    current_splice = max(0, base_splice - (attempt * 10))
                    current_path = min(10, base_path + attempt)
                    
                    vtracer.convert_image_to_svg_py(
                        self.input_posterized_temp,
                        self.output_temp,
                        colormode=colormode,
                        hierarchical=hierarchical,
                        mode=mode,
                        filter_speckle=filter_speckle,
                        color_precision=color_precision,
                        layer_difference=layer_difference,
                        corner_threshold=corner_threshold,
                        length_threshold=length_threshold,
                        max_iterations=max_iterations,
                        splice_threshold=current_splice,
                        path_precision=current_path
                    )
                    
                    with open(self.output_temp, "r") as f:
                        svg_data = f.read()
                        
                    if not is_auto:
                        best_svg = svg_data
                        break
                        
                    # Re-rasterize and verify
                    self._render_skia_preview(self.output_temp)
                    struct_score, color_score = self.calculate_similarity(img, self.preview_img)
                    
                    if struct_score > best_score:
                        best_score = struct_score
                        best_svg = svg_data
                        
                    if struct_score >= 0.85:
                        if color_score < target_q:
                            self.container.after(0, lambda s=struct_score, c=color_score: self.btn_process.configure(text=f"Refining colors (Path:{s*100:.1f}%, Color:{c*100:.1f}%)..."))
                            
                            # Fetch original PNG dominant colors to replace bad SVG colors
                            cur_max = int(self.settings["max_palette_colors"].get())
                            dom_colors = self.extract_dominant_colors(img, max_colors=cur_max)
                            
                            def hex_to_rgb(h): return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
                            def rgb_to_hex(rgb): return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])
                            
                            import re
                            fills = set(re.findall(r'fill="#([0-9a-fA-F]{6})"', best_svg))
                            remapped_svg = best_svg
                            
                            for hx in fills:
                                rgb = hex_to_rgb(hx)
                                closest = min(dom_colors, key=lambda tc: sum((rgb[i]-tc[i])**2 for i in range(3)))
                                new_hex = rgb_to_hex(closest)
                                if '#' + hx.lower() != new_hex:
                                    remapped_svg = re.sub(f'fill="#{hx}"', f'fill="{new_hex}"', remapped_svg, flags=re.IGNORECASE)
                            
                            with open(self.output_temp, "w") as f:
                                f.write(remapped_svg)
                                
                            self._render_skia_preview(self.output_temp)
                            new_struct, new_color = self.calculate_similarity(img, self.preview_img)
                            
                            if new_color > color_score:
                                best_svg = remapped_svg
                                color_score = new_color
                                
                            if color_score >= target_q:
                                self.container.after(0, lambda s=struct_score, c=color_score: self.btn_process.configure(text=f"Target met! Path:{s*100:.1f}%, Color:{c*100:.1f}%"))
                                break
                        else:
                            self.container.after(0, lambda s=struct_score, c=color_score: self.btn_process.configure(text=f"Target met! Path:{s*100:.1f}%, Color:{c*100:.1f}%"))
                            break
                        
                # Write best result back to temp for post-processing
                with open(self.output_temp, "w") as f:
                    f.write(best_svg)
                
                self.container.after(0, self._on_process_complete, True)
            except Exception as e:
                print(f"[SVG Maker] Trace error: {e}")
                self.container.after(0, self._on_process_complete, False)

        
        def start_worker():
            threading.Thread(target=worker, daemon=True).start()
            
        self._play_flash_animation(start_worker)
        
    def _on_process_complete(self, success):
        self.is_processing = False
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        
        if success:
            self.btn_process.configure(text="Post-processing colors...")
            self.container.update()
            
            if self.dominant_colors:
                det = len(self.dominant_colors)
                slider_max = max(2, min(det, 256))
                rec = min(slider_max, getattr(self, 'recommended_colors', slider_max))
                
                self.color_slider.configure(to=slider_max, number_of_steps=slider_max-1)
                
                self.settings["max_palette_colors"].set(rec)
                if "max_palette_colors" in self.slider_labels:
                    self.slider_labels["max_palette_colors"].delete(0, tk.END)
                    self.slider_labels["max_palette_colors"].insert(0, str(rec))
                
            self.apply_post_processing()
            
            self.btn_process.configure(state="normal", text="Generate!", fg_color=BMTTheme.LIME, text_color="white")
            self.btn_export.configure(state="normal")
            
            for btn in getattr(self, 'post_btns', []):
                btn.configure(state="normal")
                
            self.slider_ratio = 1.0
            self._animate_reveal()
        else:
            self.btn_process.configure(state="normal", text="Generate!", fg_color="#2C2C2C", text_color="white")
            
    def _animate_reveal(self):
        if self.slider_ratio > 0.5:
            self.slider_ratio -= 0.05
            self._draw_slider_view()
            self.container.after(16, self._animate_reveal)
            
    def export_svg(self):
        target_export = self.output_post_temp if os.path.exists(self.output_post_temp) else self.output_temp
        if not os.path.exists(target_export): return
        
        import datetime
        default_name = "Export"
        if self.input_path:
            base = os.path.basename(self.input_path)
            name_part = os.path.splitext(base)[0]
            timestamp = datetime.datetime.now().strftime("%d%m%Y%H%M")
            default_name = f"{name_part}-{timestamp}"
        
        out_path = filedialog.asksaveasfilename(
            initialfile=f"{default_name}.svg",
            defaultextension=".svg",
            filetypes=[("SVG Vector Image", "*.svg")],
            title="Save SVG As"
        )
        if out_path:
            import shutil
            shutil.copy2(target_export, out_path)
