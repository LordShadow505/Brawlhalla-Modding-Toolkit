"""
Color Converter Module
Convierte entre diferentes formatos de color: HEX, RGB, HSL, HSV, INT
Con selector visual de colores y presets
"""

import customtkinter as ctk
from .ToolModuleBase import ToolModule
import colorsys
import re
from src.utils.ThemeManager import BMTTheme, ACCENTS


class ColorConverterModule(ToolModule):
    """Módulo de Color Converter con conversiones múltiples"""
    
    def __init__(self, parent, game_path, mods_path, icons=None):
        super().__init__(parent, game_path, mods_path, icons=icons)
        self.current_color = "#FF0000"
        self.updating = False  # Flag para evitar loops infinitos
        
    def get_tool_name(self):
        return "Color Converter"
    
    def get_tool_icon(self):
        return ""
    
    def create_ui(self):
        """Crea la interfaz del Color Converter"""
        self.container = ctk.CTkFrame(self.parent, fg_color=BMTTheme.BG_DARK)
        
        # Frame principal
        main_frame = ctk.CTkFrame(self.container, fg_color=BMTTheme.BG_DARK)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
        # Título
        title_frame = ctk.CTkFrame(main_frame, fg_color="#171717", corner_radius=10)
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        title = ctk.CTkLabel(
            title_frame,
            text="Color Converter",
            font=BMTTheme.get_font(24, "bold"),
        )
        BMTTheme.style_title(title, color=ACCENTS["Color Converter"])
        title.pack(pady=15)
        
        # Panel izquierdo - Vista previa
        left_panel = ctk.CTkFrame(main_frame, fg_color="#171717", corner_radius=10)
        left_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        
        preview_label = ctk.CTkLabel(
            left_panel,
            text="Color Preview",
            font=BMTTheme.get_font(16, "bold"),
            text_color="#FFFFFF"
        )
        preview_label.pack(pady=(20, 10))
        
        # Cuadro de color grande
        self.color_preview = ctk.CTkFrame(
            left_panel,
            width=300,
            height=200,
            corner_radius=15,
            fg_color=self.current_color
        )
        self.color_preview.pack(pady=20, padx=20)
        self.color_preview.pack_propagate(False)
        
        # Texto del color actual
        self.color_text = ctk.CTkLabel(
            self.color_preview,
            text=self.current_color,
            font=BMTTheme.get_font(20, "bold"),
            text_color="#FFFFFF",
            fg_color=("gray10", "gray90"),
            corner_radius=8
        )
        self.color_text.place(relx=0.5, rely=0.5, anchor="center")
        
        # Sliders RGB
        sliders_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        sliders_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            sliders_frame,
            text="RGB Sliders:",
            font=BMTTheme.get_font(14, "bold"),
            text_color="#9E9E9E"
        ).pack(anchor="w", pady=(0, 10))
        
        # Red slider
        red_frame = ctk.CTkFrame(sliders_frame, fg_color="transparent")
        red_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            red_frame,
            text="R:",
            width=30,
            font=BMTTheme.get_font(12),
            text_color="#F44336"
        ).pack(side="left")
        
        self.red_slider = ctk.CTkSlider(
            red_frame,
            from_=0,
            to=255,
            number_of_steps=255,
            command=self.on_slider_change,
            button_color="#F44336",
            button_hover_color="#D32F2F"
        )
        self.red_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.red_slider.set(255)
        
        self.red_value = ctk.CTkLabel(
            red_frame,
            text="255",
            width=40,
            font=BMTTheme.get_font(12),
            text_color="#FFFFFF"
        )
        self.red_value.pack(side="left")
        
        # Green slider
        green_frame = ctk.CTkFrame(sliders_frame, fg_color="transparent")
        green_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            green_frame,
            text="G:",
            width=30,
            font=BMTTheme.get_font(12),
            text_color="#4CAF50"
        ).pack(side="left")
        
        self.green_slider = ctk.CTkSlider(
            green_frame,
            from_=0,
            to=255,
            number_of_steps=255,
            command=self.on_slider_change,
            button_color="#4CAF50",
            button_hover_color="#388E3C"
        )
        self.green_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.green_slider.set(0)
        
        self.green_value = ctk.CTkLabel(
            green_frame,
            text="0",
            width=40,
            font=BMTTheme.get_font(12),
            text_color="#FFFFFF"
        )
        self.green_value.pack(side="left")
        
        # Blue slider
        blue_frame = ctk.CTkFrame(sliders_frame, fg_color="transparent")
        blue_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            blue_frame,
            text="B:",
            width=30,
            font=BMTTheme.get_font(12),
            text_color="#2196F3"
        ).pack(side="left")
        
        self.blue_slider = ctk.CTkSlider(
            blue_frame,
            from_=0,
            to=255,
            number_of_steps=255,
            command=self.on_slider_change,
            button_color="#2196F3",
            button_hover_color="#1976D2"
        )
        self.blue_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.blue_slider.set(0)
        
        self.blue_value = ctk.CTkLabel(
            blue_frame,
            text="0",
            width=40,
            font=BMTTheme.get_font(12),
            text_color="#FFFFFF"
        )
        self.blue_value.pack(side="left")
        
        # Panel derecho - Conversiones
        right_panel = ctk.CTkFrame(main_frame, fg_color="#171717", corner_radius=10)
        right_panel.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        
        conversions_label = ctk.CTkLabel(
            right_panel,
            text="Color Formats",
            font=BMTTheme.get_font(16, "bold"),
            text_color="#FFFFFF"
        )
        conversions_label.pack(pady=(20, 10))
        
        # Scrollable frame para las conversiones
        scroll_frame = ctk.CTkScrollableFrame(
            right_panel,
            fg_color="transparent",
            height=400
        )
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # HEX
        self.create_format_field(scroll_frame, "HEX", "#FF0000", "hex")
        
        # RGB
        self.create_format_field(scroll_frame, "RGB", "rgb(255, 0, 0)", "rgb")
        
        # INT
        self.create_format_field(scroll_frame, "INT (Decimal)", "16711680", "int")
        
        # HSL
        self.create_format_field(scroll_frame, "HSL", "hsl(0, 100%, 50%)", "hsl")
        
        # HSV
        self.create_format_field(scroll_frame, "HSV", "hsv(0, 100%, 100%)", "hsv")
        
        # CMYK
        self.create_format_field(scroll_frame, "CMYK", "cmyk(0%, 100%, 100%, 0%)", "cmyk", readonly=True)
        
        # Presets de colores
        presets_frame = ctk.CTkFrame(scroll_frame, fg_color="#2C2C2C", corner_radius=8)
        presets_frame.pack(fill="x", pady=(20, 0))
        
        ctk.CTkLabel(
            presets_frame,
            text="Color Presets",
            font=BMTTheme.get_font(14, "bold"),
            text_color="#9E9E9E"
        ).pack(pady=(10, 5))
        
        # Grid de presets
        presets_grid = ctk.CTkFrame(presets_frame, fg_color="transparent")
        presets_grid.pack(fill="x", padx=10, pady=(0, 10))
        
        colors = [
            ("#FF0000", "Red"), ("#00FF00", "Green"), ("#0000FF", "Blue"),
            ("#FFFF00", "Yellow"), ("#FF00FF", "Magenta"), ("#00FFFF", "Cyan"),
            ("#FFFFFF", "White"), ("#000000", "Black"), ("#808080", "Gray"),
            ("#FFA500", "Orange"), ("#800080", "Purple"), ("#FFC0CB", "Pink")
        ]
        
        for i, (color, name) in enumerate(colors):
            row = i // 3
            col = i % 3
            
            btn = ctk.CTkButton(
                presets_grid,
                text=name,
                width=90,
                height=35,
                fg_color=color,
                hover_color=self.adjust_brightness(color, -20),
                text_color="#FFFFFF" if self.is_dark(color) else "#000000",
                font=BMTTheme.get_font(11),
                command=lambda c=color: self.set_color_from_hex(c)
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            presets_grid.grid_columnconfigure(col, weight=1)
        
        return self.container
    
    def create_format_field(self, parent, label, initial_value, format_type, readonly=False):
        """Crea un campo de formato de color"""
        frame = ctk.CTkFrame(parent, fg_color="#2C2C2C", corner_radius=8)
        frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            frame,
            text=label,
            font=BMTTheme.get_font(12, "bold"),
            text_color="#9E9E9E",
            width=120,
            anchor="w"
        ).pack(side="left", padx=(10, 5), pady=10)
        
        entry = ctk.CTkEntry(
            frame,
            font=BMTTheme.get_font(12),
            fg_color="#0D0D0D",
            border_width=0,
            height=35
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 5), pady=5)
        entry.insert(0, initial_value)
        
        if readonly:
            entry.configure(state="disabled")
        else:
            entry.bind("<KeyRelease>", lambda e: self.on_entry_change(format_type, entry.get()))
        
        # Botón copiar
        copy_btn = ctk.CTkButton(
            frame,
            text="Copy",
            width=50,
            height=35,
        )
        BMTTheme.style_primary_button(copy_btn, color=ACCENTS["Color Converter"])
        copy_btn.configure(command=lambda: self.copy_to_clipboard(entry.get()))
        copy_btn.pack(side="left", padx=(0, 5))
        
        # Guardar referencia
        setattr(self, f"{format_type}_entry", entry)
    
    def on_slider_change(self, value):
        """Callback cuando cambian los sliders RGB"""
        if self.updating:
            return
        
        r = int(self.red_slider.get())
        g = int(self.green_slider.get())
        b = int(self.blue_slider.get())
        
        self.red_value.configure(text=str(r))
        self.green_value.configure(text=str(g))
        self.blue_value.configure(text=str(b))
        
        self.current_color = f"#{r:02x}{g:02x}{b:02x}".upper()
        self.update_all_formats()
    
    def on_entry_change(self, format_type, value):
        """Callback cuando cambia un campo de entrada"""
        if self.updating:
            return
        
        try:
            if format_type == "hex":
                self.set_color_from_hex(value)
            elif format_type == "rgb":
                self.set_color_from_rgb(value)
            elif format_type == "int":
                self.set_color_from_int(value)
            elif format_type == "hsl":
                self.set_color_from_hsl(value)
            elif format_type == "hsv":
                self.set_color_from_hsv(value)
        except:
            pass  # Valor inválido, ignorar
    
    def set_color_from_hex(self, hex_value):
        """Establece el color desde HEX"""
        hex_value = hex_value.strip()
        if not hex_value.startswith('#'):
            hex_value = '#' + hex_value
        
        # Validar formato HEX
        if re.match(r'^#[0-9A-Fa-f]{6}$', hex_value):
            self.current_color = hex_value.upper()
            self.update_all_formats()
    
    def set_color_from_rgb(self, rgb_value):
        """Establece el color desde RGB"""
        match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', rgb_value.strip())
        if match:
            r, g, b = map(int, match.groups())
            if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                self.current_color = f"#{r:02x}{g:02x}{b:02x}".upper()
                self.update_all_formats()
    
    def set_color_from_int(self, int_value):
        """Establece el color desde INT"""
        try:
            color_int = int(int_value.strip())
            if 0 <= color_int <= 16777215:
                self.current_color = f"#{color_int:06x}".upper()
                self.update_all_formats()
        except ValueError:
            pass
    
    def set_color_from_hsl(self, hsl_value):
        """Establece el color desde HSL"""
        match = re.match(r'hsl\((\d+),\s*(\d+)%,\s*(\d+)%\)', hsl_value.strip())
        if match:
            h, s, l = map(int, match.groups())
            if 0 <= h <= 360 and 0 <= s <= 100 and 0 <= l <= 100:
                r, g, b = self.hsl_to_rgb(h/360, s/100, l/100)
                self.current_color = f"#{r:02x}{g:02x}{b:02x}".upper()
                self.update_all_formats()
    
    def set_color_from_hsv(self, hsv_value):
        """Establece el color desde HSV"""
        match = re.match(r'hsv\((\d+),\s*(\d+)%,\s*(\d+)%\)', hsv_value.strip())
        if match:
            h, s, v = map(int, match.groups())
            if 0 <= h <= 360 and 0 <= s <= 100 and 0 <= v <= 100:
                r, g, b = colorsys.hsv_to_rgb(h/360, s/100, v/100)
                r, g, b = int(r*255), int(g*255), int(b*255)
                self.current_color = f"#{r:02x}{g:02x}{b:02x}".upper()
                self.update_all_formats()
    
    def update_all_formats(self):
        """Actualiza todos los campos de formato"""
        self.updating = True
        
        # Extraer RGB del color actual
        r = int(self.current_color[1:3], 16)
        g = int(self.current_color[3:5], 16)
        b = int(self.current_color[5:7], 16)
        
        # Actualizar preview
        self.color_preview.configure(fg_color=self.current_color)
        self.color_text.configure(text=self.current_color)
        
        # Determinar color del texto
        text_color = "#FFFFFF" if self.is_dark(self.current_color) else "#000000"
        self.color_text.configure(text_color=text_color)
        
        # Actualizar sliders
        self.red_slider.set(r)
        self.green_slider.set(g)
        self.blue_slider.set(b)
        self.red_value.configure(text=str(r))
        self.green_value.configure(text=str(g))
        self.blue_value.configure(text=str(b))
        
        # Actualizar campos de texto
        self.hex_entry.delete(0, "end")
        self.hex_entry.insert(0, self.current_color)
        
        self.rgb_entry.delete(0, "end")
        self.rgb_entry.insert(0, f"rgb({r}, {g}, {b})")
        
        color_int = (r << 16) + (g << 8) + b
        self.int_entry.delete(0, "end")
        self.int_entry.insert(0, str(color_int))
        
        # HSL
        h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
        self.hsl_entry.delete(0, "end")
        self.hsl_entry.insert(0, f"hsl({int(h*360)}, {int(s*100)}%, {int(l*100)}%)")
        
        # HSV
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        self.hsv_entry.delete(0, "end")
        self.hsv_entry.insert(0, f"hsv({int(h*360)}, {int(s*100)}%, {int(v*100)}%)")
        
        # CMYK
        c, m, y, k = self.rgb_to_cmyk(r, g, b)
        self.cmyk_entry.configure(state="normal")
        self.cmyk_entry.delete(0, "end")
        self.cmyk_entry.insert(0, f"cmyk({c}%, {m}%, {y}%, {k}%)")
        self.cmyk_entry.configure(state="disabled")
        
        self.updating = False
    
    def hsl_to_rgb(self, h, s, l):
        """Convierte HSL a RGB"""
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return int(r*255), int(g*255), int(b*255)
    
    def rgb_to_cmyk(self, r, g, b):
        """Convierte RGB a CMYK"""
        if (r, g, b) == (0, 0, 0):
            return 0, 0, 0, 100
        
        c = 1 - r/255
        m = 1 - g/255
        y = 1 - b/255
        k = min(c, m, y)
        
        c = int((c - k) / (1 - k) * 100) if k != 1 else 0
        m = int((m - k) / (1 - k) * 100) if k != 1 else 0
        y = int((y - k) / (1 - k) * 100) if k != 1 else 0
        k = int(k * 100)
        
        return c, m, y, k
    
    def is_dark(self, hex_color):
        """Determina si un color es oscuro"""
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return brightness < 128
    
    def adjust_brightness(self, hex_color, amount):
        """Ajusta el brillo de un color"""
        r = max(0, min(255, int(hex_color[1:3], 16) + amount))
        g = max(0, min(255, int(hex_color[3:5], 16) + amount))
        b = max(0, min(255, int(hex_color[5:7], 16) + amount))
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def copy_to_clipboard(self, text):
        """Copia texto al portapapeles"""
        self.container.clipboard_clear()
        self.container.clipboard_append(text)
        # Feedback visual temporal (opcional)
