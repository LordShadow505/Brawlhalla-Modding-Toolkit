"""
Sprite Exporter Module - Integrado al Dashboard
Adaptado para funcionar dentro del Brawlhalla Modding Toolkit
Con sistema de caché optimizado y UI mejorada
Con integración de BrawlhallaLangReader para nombres reales
"""

import json
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image
from src.utils.ThemeManager import BMTTheme, ACCENTS
import os
import requests
from io import BytesIO
import sys
from pathlib import Path
LIB_PATH = Path(__file__).parent.parent.parent / "Lib"
if str(LIB_PATH) not in sys.path:
    sys.path.append(str(LIB_PATH))

# Variables globales para los módulos cargados
Methods = None
BrawlhallaLangReader = None
CTkToolTip = None

try:
    import importlib.util
    
    # Cargar Methods.py
    methods_path = LIB_PATH / "Methods.py"
    if methods_path.exists():
        print(f"[INFO] Loading Methods from: {methods_path}")
        spec = importlib.util.spec_from_file_location("Methods", str(methods_path))
        Methods = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(Methods)
        print("[OK] Methods loaded successfully")
        
        # Verificar que get_swf existe
        if hasattr(Methods, 'get_swf'):
            print("[OK] Methods.get_swf() is available")
        else:
            print("[WARNING] Methods.get_swf() NOT FOUND - FFDEC may not have initialized")
    else:
        print(f"[ERROR] Methods.py not found at: {methods_path}")
    
    # Cargar BrawlhallaLangReader.py
    langreader_path = LIB_PATH / "BrawlhallaLangReader.py"
    if langreader_path.exists():
        print(f"[INFO] Loading BrawlhallaLangReader from: {langreader_path}")
        spec = importlib.util.spec_from_file_location("BrawlhallaLangReader", str(langreader_path))
        BrawlhallaLangReader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(BrawlhallaLangReader)
        print("[OK] BrawlhallaLangReader loaded successfully")
    else:
        print(f"[WARNING] BrawlhallaLangReader.py not found at: {langreader_path}")
    
    # Cargar CTkToolTip
    try:
        from CTkToolTip import CTkToolTip
        print("[OK] CTkToolTip loaded successfully")
    except ImportError as e:
        print(f"[WARNING] CTkToolTip not available: {e}")
        
except ImportError as e:
    print(f"[ERROR] Failed to import libraries from Lib folder: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"[ERROR] Unexpected error loading Lib modules: {e}")
    import traceback
    traceback.print_exc()

import threading
import pickle
from datetime import datetime, timedelta
import shutil
import re


class SpriteExporterModule:
    """Módulo de Sprite Exporter integrado al Dashboard"""
    
    def __init__(self, parent, game_path, mods_path, icons=None):
        """
        Inicializa el módulo
        
        Args:
            parent: Widget padre donde se renderizará
            game_path: Ruta a la carpeta de Brawlhalla
            mods_path: Ruta a la carpeta de mods
        """
        print("="*60)
        print("[SpriteExporterModule] Initializing...")
        print(f"[SpriteExporterModule] game_path: {game_path}")
        print(f"[SpriteExporterModule] mods_path: {mods_path}")
        print(f"[SpriteExporterModule] Methods module: {Methods}")
        print(f"[SpriteExporterModule] BrawlhallaLangReader module: {BrawlhallaLangReader}")
        
        self.parent = parent
        self.game_path = game_path if game_path else ""
        self.mods_path = mods_path if mods_path else ""
        self.icons = icons if icons else {}
        
        # Mostrar warning si Methods no está disponible
        if Methods is None:
            print("[WARNING] Methods is None - SpriteExporter will NOT work!")
            print("[WARNING] Check console for errors during Methods.py loading")
        
        # Variables del módulo
        self.container = None
        self._is_destroying = False  # Flag para detener threads
        self.SpriteEM = "SWF"
        self.ExportScaleUsed = 1
        self.FilterList = ""
        self.extractorSelectedSwf = None
        self.swfName = ""
        self.all_names = []
        self.displayed_names = []
        self.legends_data = []
        self.legend_buttons = []
        self.sort_ascending = True
        self.filter_enabled = True  # Nuevo: controla si el filtrado está activo
        self.current_legend_name = None  # Guarda el nombre de la leyenda actual
        self.selected_skin_index = None  # Índice de la skin seleccionada
        self.skin_to_swf_map = {}  # Mapeo de skin -> (ruta_swf, objeto_swf)
        
        # Cache - usar carpeta assets/legends del programa
        program_dir = os.path.dirname(os.path.abspath(__file__))
        self.cache_dir = os.path.join(program_dir, "assets")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.legends_cache_file = os.path.join(self.cache_dir, "legends_data.pkl")
        self.images_cache_dir = os.path.join(self.cache_dir, "legends")
        os.makedirs(self.images_cache_dir, exist_ok=True)
        
        # Cache para imágenes de skins de la wiki
        self.skins_cache_dir = os.path.join(self.cache_dir, "skins_cache")
        os.makedirs(self.skins_cache_dir, exist_ok=True)
        
        # Limpiar caché de skins al iniciar
        self.clear_skins_cache()
        
        # Inicializar lector de idiomas
        try:
            languages_path = os.path.join(self.game_path, "languages")
            if os.path.exists(languages_path):
                self.lang_reader = BrawlhallaLangReader.BrawlhallaLangReader(languages_path)
                self.lang_reader.load_language(1)  # Cargar inglés por defecto
                print("[OK] Language reader initialized successfully")
            else:
                self.lang_reader = None
                print(f"[WARNING] Languages folder not found: {languages_path}")
        except Exception as e:
            self.lang_reader = None
            print(f"[WARNING] Could not initialize language reader: {e}")
        
        # Diccionario de archivos SWF adicionales para leyendas (excepciones)
        # Mapea legend_name -> [lista de archivos SWF adicionales]
        self.additional_swf_files = {
            "king_zuva": ["Gfx_AfricanKingArmor.swf", "Gfx_AfricanKingFancy.swf"],
            "artemis": ["Gfx_AnnivArtemis.swf"],
            "diana": ["Gfx_AnnivDiana.swf"],
            "munin": ["Gfx_BirdBardDeath.swf", "Gfx_MuninBeach.swf"],
            "azoth": ["Gfx_BP11Azoth01.swf", "Gfx_BP11Azoth02.swf", "Gfx_BP11Azoth03.swf"],
            "asuri": ["Gfx_CatBP11.swf"],
            "queen_nai": ["Gfx_CoralNai.swf"],
            "cassidy": ["Gfx_CowgirlFancy.swf"],
            "wu_shang": ["Gfx_CthulWu.swf", "Gfx_MonkGuardian01.swf", "Gfx_MonkGuardian02.swf", "Gfx_MonkGuardian03.swf"],
            "ragnir": ["Gfx_DragonSeahorse.swf"],
            "mirage": ["Gfx_EgyptianShoujo.swf", "Gfx_LibrarianMirage.swf"],
            "ember": ["Gfx_ElfAnni.swf"],
            "arcadia": ["Gfx_FairyDoll.swf"],
            "barraza": ["Gfx_FamineBarazza.swf"],
            "magyar": ["Gfx_GhostArmorMecha.swf", "Gfx_GhostArmorTreeGhost.swf"],
            "kor": ["Gfx_GolemBP11.swf"],
            "imugi": ["Gfx_ImugiBloomhalla.swf"],
            "loki": ["Gfx_LokiCoatl.swf", "Gfx_LokiBoss.swf", "Gfx_LokiHeatwave.swf", "Gfx_LokiRogue.swf", "Gfx_LokiScientist.swf"],
            "tezca": ["Gfx_LuchaPartnerAztec.swf", "Gfx_LuchaPartnerDruid.swf"],
            "mako": ["Gfx_MakoHeatWave.swf"],
            "nix": ["Gfx_MetadevNix.swf", "Gfx_MythicNix.swf"],
            "val": ["Gfx_MetadevVal.swf"],
            "teros": ["Gfx_MinotaurMagical01.swf", "Gfx_MinotaurMagical02.swf", "Gfx_MinotaurMagical03.swf"],
            "yumiko": ["Gfx_NinetailsEpic.swf"],
        }
        
        # Diccionario de leyendas a SWF principal
        self.diccionario_swf = {
            "bodvar": "Gfx_Viking.swf",
            "cassidy": "Gfx_Cowgirl.swf",
            "orion": "Gfx_Valkyrie.swf",
            "lord_vraxx": "Gfx_Alien.swf",
            "gnash": "Gfx_Caveman.swf",
            "queen_nai": "Gfx_Witch.swf",
            "lucien": "Gfx_Skins_02.swf",
            "hattori": "Gfx_Ninja.swf",
            "sir_roland": "Gfx_Knight.swf",
            "scarlet": "Gfx_Steampunk.swf",
            "thatch": "Gfx_Thatch.swf",
            "ada": "Gfx_Cyber.swf",
            "sentinel": "Gfx_Super.swf",
            "teros": "Gfx_Skins_02.swf",
            "redraptor": "Gfx_Sentai.swf",
            "ember": "Gfx_Skins_02.swf",
            "brynn": "Gfx_Skins_02.swf",
            "asuri": "Gfx_Skins_02.swf",
            "barraza": "Gfx_Skins_02.swf",
            "ulgrim": "Gfx_Dwarf.swf",
            "azoth": "Gfx_Skins_02.swf",
            "koji": "Gfx_Skins_02.swf",
            "diana": "Gfx_Marksman.swf",
            "jhala": "Gfx_Barbarian.swf",
            "loki": "Gfx_Loki.swf",
            "kor": "Gfx_Golem.swf",
            "wu_shang": "Gfx_Monk.swf",
            "val": "Gfx_TechnoNinja.swf",
            "ragnir": "Gfx_Dragon.swf",
            "cross": "Gfx_Mobster.swf",
            "mirage": "Gfx_Egyptian.swf",
            "nix": "Gfx_Reaper.swf",
            "mordex": "Gfx_Werewolf.swf",
            "yumiko": "Gfx_Ninetails.swf",
            "artemis": "Gfx_Spacehunter.swf",
            "caspian": "Gfx_Skins_04.swf",
            "sidra": "Gfx_Skins_04.swf",
            "xull": "Gfx_Skins_04.swf",
            "isaiah": "Gfx_Skins_04.swf",
            "kaya": "Gfx_Skins_04.swf",
            "jiro": "Gfx_Skins_04.swf",
            "lin_fei": "Gfx_Skins_04.swf",
            "zariel": "Gfx_Skins_04.swf",
            "rayman": "Gfx_Skins_04.swf",
            "dusk": "Gfx_Skins_04.swf",
            "fait": "Gfx_Skins_04.swf",
            "thor": "Gfx_Skins_04.swf",
            "petra": "Gfx_Skins_04.swf",
            "vector": "Gfx_Skins_04.swf",
            "volkov": "Gfx_Skins_04.swf",
            "onyx": "Gfx_Gargoyle.swf",
            "jaeyun": "Gfx_Sellsword.swf",
            "mako": "Gfx_ActualShark.swf",
            "magyar": "Gfx_GhostArmor.swf",
            "reno": "Gfx_BountyHunter.swf",
            "munin": "Gfx_BirdBard.swf",
            "arcadia": "Gfx_FairyQueen.swf",
            "ezio": "Gfx_Ezio.swf",
            "thea": "Gfx_Speedster.swf",
            "tezca": "Gfx_Luchador.swf",
            "seven": "Gfx_RoboEngineer.swf",
            "vivi": "Gfx_Assassin.swf",
            "imugi": "Gfx_Imugi.swf",
            "king_zuva": "Gfx_AfricanKing.swf",
            "priya": "Gfx_BladeDancer.swf",
            "ramson": "Gfx_CyberVirus.swf",
            "lady_vera": "Gfx_Cleric.swf",
            "rupture": "Gfx_DarkheartMonster.swf",
            "aurus": "Gfx_ActualGladiator.swf"
        }
    
    def create_ui(self):
        """Crea la interfaz del Sprite Exporter con diseño mejorado"""
        self.container = ctk.CTkFrame(self.parent, fg_color=BMTTheme.BG_DARK)
        
        # Mostrar ventana de carga
        self.show_loading_screen()
        
        # Cargar datos en segundo plano
        threading.Thread(target=self.load_data_async, daemon=True).start()
        
        return self.container
    
    def show_loading_screen(self):
        """Muestra pantalla de carga inicial"""
        self.loading_frame = ctk.CTkFrame(self.container, fg_color=BMTTheme.BG_DARK)
        self.loading_frame.pack(fill="both", expand=True)
        
        # Contenedor central
        center_frame = ctk.CTkFrame(self.loading_frame, fg_color="#171717", corner_radius=15)
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Título
        title = ctk.CTkLabel(
            center_frame,
            text="Loading Sprite Exporter",
            font=BMTTheme.get_font(24, "bold"),
        )
        BMTTheme.style_title(title, color=ACCENTS["Sprite Exporter"])
        title.pack(pady=(30, 20), padx=50)
        
        # Barra de progreso
        self.loading_progress = ctk.CTkProgressBar(center_frame, width=300, height=8)
        self.loading_progress.pack(pady=10, padx=50)
        self.loading_progress.set(0)
        
        # Label de estado
        self.loading_status = ctk.CTkLabel(
            center_frame,
            text="Initializing...",
            font=BMTTheme.get_font(12),
            text_color="#AAAAAA"
        )
        self.loading_status.pack(pady=(5, 30), padx=50)
    
    def update_loading(self, progress, status):
        """Actualiza el estado de carga"""
        # Verificar que los widgets existan antes de actualizar
        if not self.container or not hasattr(self, 'loading_progress'):
            return
        
        try:
            if self.loading_progress and self.loading_progress.winfo_exists():
                self.loading_progress.set(progress)
            if self.loading_status and self.loading_status.winfo_exists():
                self.loading_status.configure(text=status)
            if self.container and self.container.winfo_exists():
                self.container.update_idletasks()
        except:
            # Ignorar errores si los widgets ya fueron destruidos
            pass
    
    def load_data_async(self):
        """Carga los datos de forma asíncrona"""
        try:
            # Verificar que no estemos destruyendo el módulo
            if self._is_destroying or not self.container or not self.container.winfo_exists():
                return
            
            # Paso 1: Cargar caché
            self.update_loading(0.2, "Loading cache...")
            if self._is_destroying:
                return
            
            cached_data = self.load_from_cache()
            
            # Paso 2: Cargar desde API si es necesario
            if self._is_destroying:
                return
            
            if cached_data is None or self.is_cache_expired():
                self.update_loading(0.4, "Loading legends from API...")
                if self._is_destroying:
                    return
                self.legends_data = self.load_legends_from_api()
                self.save_to_cache(self.legends_data)
            else:
                self.legends_data = cached_data
            
            # Ensure ALL local dictionary legends are present (handles newly added legends)
            self._ensure_all_local_legends()
            
            # Paso 3: Cargar imágenes
            if self._is_destroying:
                return
            
            self.update_loading(0.6, "Loading images...")
            self.preload_images()
            
            # Paso 4: Construir UI (verificar de nuevo)
            if self._is_destroying:
                return
            
            if self.container and self.container.winfo_exists():
                self.update_loading(0.8, "Building interface...")
                self.container.after(0, self.build_main_ui)
                
                # Completado
                self.update_loading(1.0, "Ready!")
                self.container.after(500, self.hide_loading_screen)
            
        except Exception as e:
            # Verificar que el contenedor existe antes de mostrar error
            if not self._is_destroying and self.container and self.container.winfo_exists():
                try:
                    self.container.after(0, lambda: messagebox.showerror("Loading Error", f"Failed to load data:\n{str(e)}"))
                    self.container.after(0, self.build_main_ui)
                except:
                    pass
    
    def load_from_cache(self):
        """Carga datos desde el caché"""
        try:
            if os.path.exists(self.legends_cache_file):
                with open(self.legends_cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                    return cache_data.get('legends', None)
        except:
            pass
        return None
    
    def save_to_cache(self, data):
        """Guarda datos en caché"""
        try:
            cache_data = {
                'legends': data,
                'timestamp': datetime.now().isoformat()
            }
            with open(self.legends_cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
        except:
            pass
    
    def is_cache_expired(self):
        """Verifica si el caché ha expirado (7 días)"""
        try:
            if os.path.exists(self.legends_cache_file):
                with open(self.legends_cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                    timestamp = datetime.fromisoformat(cache_data.get('timestamp', ''))
                    return datetime.now() - timestamp > timedelta(days=7)
        except:
            pass
        return True
    
    def load_legends_from_api(self):
        """Carga leyendas desde la API con timeout corto, siempre incluye las locales"""
        api_data = []
        try:
            url = "https://bhapi.338.rocks/v2/legends/all"
            response = requests.get(url, timeout=3)
            response.raise_for_status()
            api_data = response.json().get("data", [])
        except Exception:
            pass
        
        # Build a set of API legend names (lowercased, underscored)
        api_names = set()
        for legend in api_data:
            key = legend.get("legend_name_key", "").lower().replace(" ", "_")
            api_names.add(key)
        
        # Ensure ALL local dictionary legends are included (handles new/missing legends)
        for local_name in self.diccionario_swf.keys():
            if local_name not in api_names:
                api_data.append({
                    "legend_name_key": local_name.replace("_", " ").title(),
                    "legend_id": hash(local_name) % 10000
                })
        
        if not api_data:
            return self.get_local_legends_data()
        
        return api_data
    
    def get_local_legends_data(self):
        """Obtiene datos de leyendas desde el diccionario local"""
        return [{"legend_name_key": name.replace("_", " ").title(), "legend_id": i} 
                for i, name in enumerate(self.diccionario_swf.keys())]
    
    def _ensure_all_local_legends(self):
        """Ensures all legends in diccionario_swf exist in legends_data.
        
        This handles the case where new legends are added manually to the
        dictionary but the cached API data doesn't include them yet.
        """
        existing_names = set()
        for legend in self.legends_data:
            key = legend.get("legend_name_key", "").lower().replace(" ", "_")
            existing_names.add(key)
        
        added = 0
        for local_name in self.diccionario_swf.keys():
            if local_name not in existing_names:
                self.legends_data.append({
                    "legend_name_key": local_name.replace("_", " ").title(),
                    "legend_id": hash(local_name) % 10000
                })
                added += 1
                print(f"[INFO] Added missing legend to data: {local_name}")
        
        if added > 0:
            # Update cache with the new data
            self.save_to_cache(self.legends_data)
    
    def preload_images(self):
        """Precarga las imágenes de leyendas"""
        for legend in self.legends_data:
            legend_name = legend.get("legend_name_key", "").lower().replace(" ", "_")
            image_path = os.path.join(self.images_cache_dir, f"{legend_name}.png")
            
            if not os.path.exists(image_path):
                thumbnail_url = legend.get("thumbnail", "")
                if thumbnail_url:
                    try:
                        img_response = requests.get(thumbnail_url, timeout=2)
                        image = Image.open(BytesIO(img_response.content))
                        image.save(image_path)
                    except:
                        pass
    
    def hide_loading_screen(self):
        """Oculta la pantalla de carga"""
        try:
            if hasattr(self, 'loading_frame') and self.loading_frame:
                if self.loading_frame.winfo_exists():
                    self.loading_frame.destroy()
        except:
            pass
    
    def build_main_ui(self):
        """Construye la interfaz principal"""
        # Frame principal
        main_frame = ctk.CTkFrame(self.container, fg_color="#0E0E0E")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configurar grid: 1/4 izquierda, 3/4 derecha
        main_frame.grid_columnconfigure(0, weight=1, minsize=500)  # Panel restablecido a 300px
        main_frame.grid_columnconfigure(1, weight=3)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # ===== PANEL IZQUIERDO (1/3) =====
        self.build_left_panel(main_frame)
        
        # ===== PANEL DERECHO (2/3) =====
        self.build_right_panel(main_frame)
    
    def build_left_panel(self, parent):
        """Construye el panel izquierdo con lista de skins"""
        left_panel = ctk.CTkFrame(parent, fg_color="#171717", corner_radius=8)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_panel.grid_rowconfigure(2, weight=1)  # Lista de skins expansible
        left_panel.grid_columnconfigure(0, weight=1)
        
        # Título
        title = ctk.CTkLabel(
            left_panel,
            text="Skins List",
            font=BMTTheme.get_font(16, "bold"),
            text_color="#175DDC"
        )
        title.grid(row=0, column=0, pady=(15, 10), padx=15, sticky="w")
        
        # Frame de búsqueda y ordenar
        controls_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        controls_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 10))
        controls_frame.grid_columnconfigure(0, weight=1)
        
        # Búsqueda
        search_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        search_frame.grid_columnconfigure(1, weight=1)
        
        search_icon = ctk.CTkLabel(search_frame, text="", image=BMTTheme.get_icon("search", size=16))
        search_icon.grid(row=0, column=0, padx=(0, 5))
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search skins...",
            height=32,
            font=BMTTheme.get_font(12)
        )
        self.search_entry.grid(row=0, column=1, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self.filter_names_list)
        
        # Botón de ordenar
        self.sort_button = ctk.CTkButton(
            controls_frame,
            text="Sort A-Z", image=BMTTheme.get_icon("sort_by_alpha", size=16),
            command=self.toggle_sort,
            height=32,
            fg_color="#2C2C2C",
            hover_color="#404040",
            font=BMTTheme.get_font(11)
        )
        self.sort_button.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        
        # Checkbox de filtrado (solo para archivos compartidos)
        self.filter_checkbox = ctk.CTkCheckBox(
            controls_frame,
            text="Filter by Legend",
            command=self.toggle_filter,
            font=BMTTheme.get_font(11),
            fg_color="#175DDC",
            hover_color="#1348A8",
            text_color="#CCCCCC",
            checkbox_width=18,
            checkbox_height=18
        )
        self.filter_checkbox.grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.filter_checkbox.select()  # Activado por defecto
        
        # Lista de skins con scrollbar
        list_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        list_frame.grid(row=2, column=0, sticky="nsew", padx=15, pady=(10, 10))
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Usar Text widget en lugar de Listbox para mejor formato
        self.namesList = tk.Text(
            list_frame,
            width=1,  # IMPORTANTE: width=1 permite que el panel se reduzca al minsize sin ser forzado por el texto
            bg="#0E0E0E",
            fg="#FFFFFF",
            font=("Roboto", 12),  # Fuente Roboto para mejor estética
            highlightthickness=0,
            borderwidth=0,
            cursor="hand2",
            wrap=tk.NONE,
            state=tk.DISABLED,
            tabs=("200",),  # Ajustado a 200px para encajar con los 300px de panel
            padx=15, pady=10  # Margen interno agregado sin alterar el tamaño del panel
        )
        self.namesList.grid(row=0, column=0, sticky="nsew")
        
        # Configurar tags para colores y estilos
        self.namesList.tag_config("header", foreground="#175DDC", font=("Roboto", 12, "bold"))  # Azul para encabezados
        self.namesList.tag_config("separator", foreground="#444444")  # Gris oscuro para separadores
        self.namesList.tag_config("technical", foreground="#888888", font=("Roboto", 11, "italic"))  # Gris para nombre técnico (File Name)
        self.namesList.tag_config("display", foreground="#FFFFFF", font=("Roboto", 12, "bold"))  # Blanco para nombre real (Skin Name)
        self.namesList.tag_config("selected", background="#175DDC", foreground="#FFFFFF")  # Selección
        
        # Tags para filas alternas y prioridad
        self.namesList.tag_config("row_alt", background="#151515")
        self.namesList.tag_config("row_normal", background="#0E0E0E")
        self.namesList.tag_raise("selected")  # Garantizar que el azul de selección se sobreponga al fondo
        
        # Vincular eventos de selección
        self.namesList.bind("<Button-1>", self.on_text_click)
        
        scrollbar = ctk.CTkScrollbar(list_frame)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.namesList.config(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.namesList.yview)
    
    def build_right_panel(self, parent):
        """Construye el panel derecho con leyendas, opciones, preview y log"""
        right_panel = ctk.CTkFrame(parent, fg_color="#0E0E0E")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        right_panel.grid_rowconfigure(3, weight=1)  # Only bottom section (preview/log) expands
        right_panel.grid_columnconfigure(0, weight=1)
        
        # ===== SELECTOR DE SWF MANUAL =====
        swf_frame = ctk.CTkFrame(right_panel, fg_color="#171717", corner_radius=8)
        swf_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        swf_frame.grid_columnconfigure(1, weight=1)
        
        swf_label = ctk.CTkLabel(
            swf_frame,
            text="SWF File:",
            font=BMTTheme.get_font(12, "bold")
        )
        swf_label.grid(row=0, column=0, padx=(15, 10), pady=10, sticky="w")
        
        self.swf_path_entry = ctk.CTkEntry(
            swf_frame,
            placeholder_text="Or browse for a SWF file...",
            height=32,
            font=BMTTheme.get_font(11),
            state="readonly"
        )
        self.swf_path_entry.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        
        folder_icon = BMTTheme.get_icon("file_open")
        browse_btn = ctk.CTkButton(
            swf_frame,
            text="" if folder_icon else "Browse",
            image=folder_icon,
            width=35 if folder_icon else 80,
            height=30,
            command=self.select_swf
        )
        BMTTheme.style_secondary_button(browse_btn)
        browse_btn.grid(row=0, column=2, padx=(5, 15), pady=10)
        
        # ===== PANEL DE LEYENDAS (FIXED HEIGHT) =====
        self.legends_container = ctk.CTkFrame(right_panel, fg_color="#171717", corner_radius=8)
        self.legends_container.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        self.legends_container.grid_rowconfigure(2, weight=1)
        self.legends_container.grid_columnconfigure(0, weight=1)
        # Prevent content from dictating container size
        self.legends_container.configure(height=300)  # Revertido un poco de altura
        self.legends_container.grid_propagate(False)
        
        # Título
        legends_title = ctk.CTkLabel(
            self.legends_container,
            text="Select Legend",
            font=BMTTheme.get_font(16, "bold"),
            text_color="#175DDC"
        )
        legends_title.grid(row=0, column=0, pady=(12, 0), padx=15, sticky="w")

        legends_subtitle = ctk.CTkLabel(
            self.legends_container,
            text="(These are preloaded files, if something doesn't work, load it manually)",
            font=BMTTheme.get_font(10),
            text_color="#666666"
        )
        legends_subtitle.grid(row=1, column=0, pady=(2, 8), padx=15, sticky="w")
        
        # Frame scrollable para leyendas
        self.legends_frame = ctk.CTkScrollableFrame(
            self.legends_container,
            fg_color="#0E0E0E",
            corner_radius=8,
            height=250,
            scrollbar_button_color="#175DDC",
            scrollbar_button_hover_color="#1A237E"
        )
        self.legends_frame.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 5))
        
        # Cargar leyendas (el bind se hace desde load_legends_grid tras renderizar)
        self.load_legends_grid()
        
        # ===== EXPORT OPTIONS =====
        export_frame = ctk.CTkFrame(right_panel, fg_color="#171717", corner_radius=8)
        export_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        
        export_title = ctk.CTkLabel(
            export_frame,
            text="Export Options",
            font=BMTTheme.get_font(14, "bold")
        )
        export_title.grid(row=0, column=0, columnspan=3, pady=(15, 10), padx=15, sticky="w")
        
        # Botones de exportación en fila
        export_shapes_btn = ctk.CTkButton(
            export_frame,
            text="Export Shapes",
            font=BMTTheme.get_font(12, "bold"),
            height=38,
            fg_color="#6A1B9A",
            hover_color="#3B0764",
            command=self.export_shapes
        )
        export_shapes_btn.grid(row=1, column=0, padx=(15, 5), pady=(0, 15), sticky="ew")
        
        export_sprites_btn = ctk.CTkButton(
            export_frame,
            text="Export Sprites",
            font=BMTTheme.get_font(12, "bold"),
            height=38,
            fg_color="#1565C0",
            hover_color="#1E3A8A",
            command=self.export_sprites
        )
        export_sprites_btn.grid(row=1, column=1, padx=5, pady=(0, 15), sticky="ew")
        
        export_swf_btn = ctk.CTkButton(
            export_frame,
            text="Export SWF",
            font=BMTTheme.get_font(12, "bold"),
            height=38,
            fg_color="#004D40",
            hover_color="#052E16",
            command=self.export_swf
        )
        export_swf_btn.grid(row=1, column=2, padx=(5, 15), pady=(0, 15), sticky="ew")
        
        # Configurar columnas del export frame
        export_frame.grid_columnconfigure(0, weight=1)
        export_frame.grid_columnconfigure(1, weight=1)
        export_frame.grid_columnconfigure(2, weight=1)
        
        # ===== PREVIEW Y LOG (DOS COLUMNAS) =====
        bottom_container = ctk.CTkFrame(right_panel, fg_color="transparent")
        bottom_container.grid(row=3, column=0, sticky="nsew")
        bottom_container.grid_rowconfigure(0, weight=1)
        bottom_container.grid_columnconfigure(0, weight=1)  # Preview
        bottom_container.grid_columnconfigure(1, weight=1)  # Log
        
        # ===== VISTA PREVIA DE SKIN (IZQUIERDA) =====
        preview_frame = ctk.CTkFrame(bottom_container, fg_color="#171717", corner_radius=8)
        preview_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        preview_frame.grid_rowconfigure(1, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)
        
        # Guardar referencia al frame
        self.preview_frame = preview_frame
        
        # Max preview image size (prevents the panel from growing)
        self.MAX_PREVIEW_W = 350
        self.MAX_PREVIEW_H = 300
        
        # Título de vista previa
        preview_title = ctk.CTkLabel(
            preview_frame,
            text="Skin Preview",
            font=BMTTheme.get_font(14, "bold")
        )
        preview_title.grid(row=0, column=0, pady=(15, 10), padx=15, sticky="w")
        
        # Wrapper that absorbs content size requests (prevents image from resizing panel)
        self._preview_wrapper = ctk.CTkFrame(preview_frame, fg_color="#0E0E0E", corner_radius=6)
        self._preview_wrapper.grid(row=1, column=0, pady=(0, 15), padx=15, sticky="nsew")
        self._preview_wrapper.grid_propagate(False)
        self._preview_wrapper.grid_rowconfigure(0, weight=1)
        self._preview_wrapper.grid_columnconfigure(0, weight=1)
        
        # Label para mostrar la imagen (inside non-propagating wrapper)
        self.skin_preview_label = ctk.CTkLabel(
            self._preview_wrapper,
            text="Select a skin to preview",
            font=BMTTheme.get_font(11),
            text_color="#666666",
            fg_color="transparent",
        )
        self.skin_preview_label.grid(row=0, column=0)
        
        # Variables para la imagen actual
        self.current_image_path = None
        self.current_pil_image = None
        
        # Bind para redimensionar la imagen cuando cambie el tamaño del frame
        preview_frame.bind("<Configure>", self.on_preview_resize)
        
        # ===== LOG (DERECHA) =====
        log_frame = ctk.CTkFrame(bottom_container, fg_color="#171717", corner_radius=8)
        log_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        log_title = ctk.CTkLabel(
            log_frame,
            text="Log",
            font=BMTTheme.get_font(14, "bold")
        )
        log_title.grid(row=0, column=0, pady=(15, 5), padx=15, sticky="w")
        
        self.log_text = ctk.CTkTextbox(
            log_frame,
            font=BMTTheme.get_font(11),
            fg_color="#0E0E0E",
            wrap="word"
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        
        # Log inicial
        # Mensaje de inicio
        self.log("[OK] Sprite Exporter ready!")
        self.log(f"Game Path: {self.game_path if self.game_path else 'Not set'}")
        self.log(f"Mods Path: {self.mods_path if self.mods_path else 'Not set'}")
        self.log("Select a legend or browse for a SWF file to start")
    
    def on_legends_container_resize(self, event=None):
        """Mantenido por compatibilidad - ahora el sistema usa el evento del canvas interno."""
        pass

    def _apply_legend_grid_columns(self, visible_width):
        """
        Reorganiza los botones del grid usando el ancho visible EXACTO del canvas.
        
        Args:
            visible_width: Ancho en pixeles del área visible del scrollable frame (de event.width)
        """
        if not self.legend_buttons:
            return

        # Tamaño real de cada celda: botón (57px) + padx (6px) = 63px
        button_total_width = 72

        # Columnas que caben en el espacio visible
        # Se restablece la restricción del margen de seguridad (-1) a petición del usuario
        new_columns = max(1, (visible_width // button_total_width) - 1)

        # Solo reorganizar si el número de columnas cambió
        if getattr(self, '_current_columns', -1) == new_columns:
            return

        self._current_columns = new_columns
        columns = new_columns

        for index, btn in enumerate(self.legend_buttons):
            row = index // columns
            col = index % columns
            btn.grid_forget()
            btn.grid(row=row, column=col, padx=3, pady=3)

    def _on_legends_canvas_configure(self, event):
        """
        Se llama cuando el canvas interno del CTkScrollableFrame cambia de tamaño.
        event.width es el ancho VISIBLE del viewport en ese instante exacto.
        """
        # Debounce: cancelar cualquier recalculo pendiente
        if hasattr(self, '_canvas_resize_after'):
            try:
                self.container.after_cancel(self._canvas_resize_after)
            except Exception:
                pass
        self._canvas_resize_after = self.container.after(
            80, lambda w=event.width: self._apply_legend_grid_columns(w)
        )

    def recalculate_legend_grid(self, event=None):
        """Fuerza un recálculo usando el ancho actual del canvas interno."""
        if not hasattr(self, 'legends_frame') or not self.legend_buttons:
            return
        try:
            canvas = self.legends_frame._parent_canvas
            canvas.update_idletasks()
            w = canvas.winfo_width()
            if w > 1:
                self._apply_legend_grid_columns(w)
        except Exception:
            pass
    
    def load_legends_grid(self):
        """Carga el grid de leyendas. El número de columnas se determina dinámicamente
        al bindear al evento <Configure> del canvas interno del CTkScrollableFrame."""
        if not self.legends_data:
            self.legends_data = self.get_local_legends_data()
        
        # Limpiar botones existentes
        for btn in self.legend_buttons:
            try:
                btn.destroy()
            except Exception:
                pass
        self.legend_buttons.clear()
        
        # Resetear columnas para forzar recálculo
        self._current_columns = -1
        
        # Fixed button size to prevent layout shifts (increased by 12px for better visibility)
        target_size = (64, 64)
        
        # Crear botones en grid adaptativo
        for index, legend in enumerate(self.legends_data):
            legend_name = legend.get("legend_name_key", "").lower().replace(" ", "_")
            
            # Intentar cargar imagen desde caché
            image_path = os.path.join(self.images_cache_dir, f"{legend_name}.png")
            
            # Load image with fixed size to avoid layout changes
            try:
                from src.utils import load_and_fit_image
                final_img = load_and_fit_image(image_path, target_size)
            except Exception:
                try:
                    img = Image.open(image_path).convert('RGBA')
                    img.thumbnail(target_size, Image.LANCZOS)
                    background = Image.new('RGBA', target_size, (0, 0, 0, 0))
                    paste_x = (target_size[0] - img.width) // 2
                    paste_y = (target_size[1] - img.height) // 2
                    background.paste(img, (paste_x, paste_y), img)
                    final_img = background
                except Exception:
                    final_img = Image.new('RGBA', target_size, '#2C2C2C')

            # Crear CTkImage con tamaño fijo
            thumbnail_image = ctk.CTkImage(final_img, size=target_size)
            
            button = ctk.CTkButton(
                self.legends_frame,
                image=thumbnail_image,
                text="",
                width=target_size[0],
                height=target_size[1],
                fg_color='#020617',
                hover_color='#175DDC',
                command=lambda ln=legend_name: self.select_legend(ln)
            )
            
            # Colocar inicialmente todos en columna 0, fila=index (se reorgamiza con el evento)
            button.grid(row=index, column=0, padx=3, pady=3)
            
            self.legend_buttons.append(button)
            
            # Tooltip
            tooltip_text = legend_name.replace("_", " ").title()
            if CTkToolTip:
                CTkToolTip(button, delay=0.01, message=tooltip_text, bg_color="#0E0E0E")
        
        # Enlazar el evento <Configure> del canvas VISIBLE interno.
        # Este evento nos da event.width = ancho EXACTO del viewport en cada resize.
        # Se hace aqui despues de que los botones ya existen.
        try:
            canvas = self.legends_frame._parent_canvas
            # Desenlazar binds previos para evitar duplicados
            canvas.unbind("<Configure>")
            canvas.bind("<Configure>", self._on_legends_canvas_configure)
        except Exception:
            pass
        
        # Dispara un recalculo inicial con un retardo para asegurarnos
        # de que el canvas ya tiene su tamaño definitivo
        self.container.after(300, self.recalculate_legend_grid)
    
    def select_legend(self, legend_name):
        """Maneja la selección de una leyenda y carga todos sus archivos SWF"""
        # Buscar el SWF principal
        main_swf_file = self.diccionario_swf.get(legend_name)
        
        if not main_swf_file:
            self.log(f"[WARNING] No SWF found for {legend_name}")
            return
        
        # Construir ruta completa al SWF principal
        if not self.game_path:
            messagebox.showwarning("Game Path Not Set", "Please set the Brawlhalla game path in the main dashboard settings.")
            self.log("ERROR: Game path not configured")
            return
        
        main_swf_path = os.path.join(self.game_path, main_swf_file)
        
        if not os.path.exists(main_swf_path):
            self.log(f"[WARNING] SWF file not found: {main_swf_file}")
            self.log(f"Looking in: {main_swf_path}")
            messagebox.showwarning("SWF Not Found", f"Could not find SWF file:\n{main_swf_path}")
            return
        
        # Obtener archivos SWF adicionales si existen
        additional_files = self.additional_swf_files.get(legend_name, [])
        additional_swf_paths = []
        
        for swf_file in additional_files:
            swf_path = os.path.join(self.game_path, swf_file)
            if os.path.exists(swf_path):
                additional_swf_paths.append(swf_path)
            else:
                self.log(f"[INFO] Optional SWF not found: {swf_file}")
        
        # Cargar el SWF principal y los adicionales
        self.load_swf_file_multi(main_swf_path, additional_swf_paths, legend_name)
    
    def select_swf(self):
        """Abre un diálogo para seleccionar un archivo SWF manualmente"""
        initial_dir = self.game_path if self.game_path else "/"
        
        swf_path = filedialog.askopenfilename(
            title="Select SWF File",
            initialdir=initial_dir,
            filetypes=[("SWF files", "*.swf"), ("All files", "*.*")]
        )
        
        if swf_path:
            # Extraer nombre del archivo sin extensión
            legend_name = os.path.splitext(os.path.basename(swf_path))[0]
            self.load_swf_file(swf_path, legend_name)
    
    def load_swf_file_multi(self, main_swf_path, additional_swf_paths, legend_name):
        """
        Carga múltiples archivos SWF para una leyenda y combina todas las skins
        
        Args:
            main_swf_path: Ruta al archivo SWF principal
            additional_swf_paths: Lista de rutas a archivos SWF adicionales
            legend_name: Nombre de la leyenda
        """
        try:
            self.log(f"Loading SWF: {os.path.basename(main_swf_path)}")
            
            # Verificar que Methods esté cargado
            if Methods is None:
                messagebox.showerror(
                    "Error - Methods Library Not Loaded",
                    "The FFDEC library (Methods.py) failed to load!\n\n"
                    "Required for loading legends and extracting sprites.\n\n"
                    "Please check:\n"
                    "1. Lib/Methods.py exists\n"
                    "2. Lib/ffdec/ folder with .jar files exists\n"
                    "3. JPype is installed: pip install jpype1\n"
                    "4. Java JDK is installed and in PATH"
                )
                self.log("ERROR: Methods library not available")
                return
            
            # Verificar que get_swf exista
            if not hasattr(Methods, 'get_swf'):
                messagebox.showerror(
                    "Error - Methods Incomplete",
                    "Methods.get_swf() function not found!\n\n"
                    "The FFDEC library may have failed to initialize.\n"
                    "Check the console/terminal for error messages."
                )
                self.log("ERROR: Methods.get_swf() not available")
                return
            
            # Cargar el SWF principal
            self.extractorSelectedSwf = Methods.get_swf(main_swf_path, False)
            self.swfName = os.path.basename(main_swf_path)
            
            if self.extractorSelectedSwf is None:
                messagebox.showinfo("Failed to load SWF", f"SWF failed to load. Path: {main_swf_path}")
                self.log("ERROR: SWF failed to load")
                return
            
            # Actualizar entry con la ruta
            if hasattr(self, 'swf_path_entry'):
                self.swf_path_entry.configure(state="normal")
                self.swf_path_entry.delete(0, tk.END)
                self.swf_path_entry.insert(0, main_swf_path)
                self.swf_path_entry.configure(state="readonly")
            
            # Extraer skins del SWF principal
            listNames = Methods.get_all_skin_names(self.extractorSelectedSwf, 0)
            names = list(listNames) if listNames else []
            all_skin_names = [name for name in names if name and not name[0].isdigit()]
            
            # Guardar mapeo de skin -> archivo SWF para exportación
            self.skin_to_swf_map = {}
            for skin in all_skin_names:
                self.skin_to_swf_map[skin] = (main_swf_path, self.extractorSelectedSwf)
            
            # Cargar skins adicionales de otros archivos
            for additional_path in additional_swf_paths:
                try:
                    self.log(f"Loading additional SWF: {os.path.basename(additional_path)}")
                    additional_swf = Methods.get_swf(additional_path, False)
                    
                    if additional_swf:
                        additional_names = Methods.get_all_skin_names(additional_swf, 0)
                        additional_names_list = list(additional_names) if additional_names else []
                        additional_skin_names = [name for name in additional_names_list if name and not name[0].isdigit()]
                        
                        # Agregar skins adicionales a la lista
                        for skin in additional_skin_names:
                            if skin not in all_skin_names:  # Evitar duplicados
                                all_skin_names.append(skin)
                                self.skin_to_swf_map[skin] = (additional_path, additional_swf)
                        
                        self.log(f"[OK] Added {len(additional_skin_names)} skins from {os.path.basename(additional_path)}")
                except Exception as e:
                    self.log(f"[WARNING] Could not load {os.path.basename(additional_path)}: {e}")
            
            # Guardar nombre de leyenda actual
            self.current_legend_name = legend_name
            
            # Determinar si es un archivo compartido
            is_shared_swf = self.swfName in ["Gfx_Skins_02.swf", "Gfx_Skins_04.swf"]
            
            # Filtrar skins por leyenda SOLO si es archivo compartido Y el filtro está activo
            if is_shared_swf and self.filter_enabled:
                self.all_names = self.filter_skins_by_legend(all_skin_names, legend_name)
            else:
                self.all_names = all_skin_names
            
            self.displayed_names = self.all_names.copy()
            # Actualizar la lista de skins
            self.update_skins_list()
            
            total_loaded = len(all_skin_names)
            total_shown = len(self.all_names)
            if len(additional_swf_paths) > 0:
                self.log(f"[OK] Loaded {total_shown}/{total_loaded} skins from {1 + len(additional_swf_paths)} files")
            else:
                self.log(f"[OK] Loaded {total_shown} skins from {os.path.basename(main_swf_path)}")
            
        except Exception as e:
            self.log(f"ERROR loading SWF: {str(e)}")
            messagebox.showerror("Load Error", f"Failed to load SWF file:\n{str(e)}")
    
    def load_swf_file(self, swf_path, legend_name):
        """Carga un archivo SWF individual (para selección manual)"""
        try:
            self.log(f"Loading SWF: {os.path.basename(swf_path)}")
            
            # Verificar que Methods esté cargado
            if Methods is None or not hasattr(Methods, 'get_swf'):
                messagebox.showerror(
                    "Error",
                    "Methods library not loaded!\n\n"
                    "Cannot load SWF files without FFDEC library.\n"
                    "See console for details."
                )
                self.log("ERROR: Methods library not available")
                return
            
            # Limpiar mapeo anterior para que la exportación use SIEMPRE
            # el archivo actualmente cargado (self.extractorSelectedSwf)
            self.skin_to_swf_map = {}
            
            # Cargar el SWF usando Methods.get_swf (igual que el original)
            self.extractorSelectedSwf = Methods.get_swf(swf_path, False)
            self.swfName = os.path.basename(swf_path)
            
            if self.extractorSelectedSwf is None:
                messagebox.showinfo("Failed to load SWF", f"SWF failed to load. Path: {swf_path}")
                self.log("ERROR: SWF failed to load")
                return
            
            # Actualizar entry con la ruta
            if hasattr(self, 'swf_path_entry'):
                self.swf_path_entry.configure(state="normal")
                self.swf_path_entry.delete(0, tk.END)
                self.swf_path_entry.insert(0, swf_path)
                self.swf_path_entry.configure(state="readonly")
            
            # Extraer lista de nombres de skins del SWF
            listNames = Methods.get_all_skin_names(self.extractorSelectedSwf, 0)
            names = list(listNames) if listNames else []
            all_skin_names = [name for name in names if name and not name[0].isdigit()]
            
            # Guardar nombre de leyenda actual
            self.current_legend_name = legend_name
            
            # Determinar si es un archivo compartido (Gfx_Skins_02 o Gfx_Skins_04)
            is_shared_swf = self.swfName in ["Gfx_Skins_02.swf", "Gfx_Skins_04.swf"]
            
            # Filtrar skins por leyenda SOLO si es archivo compartido Y el filtro está activo
            if is_shared_swf and self.filter_enabled:
                self.all_names = self.filter_skins_by_legend(all_skin_names, legend_name)
            else:
                self.all_names = all_skin_names
            
            self.displayed_names = self.all_names.copy()
            # Actualizar la lista de skins en el panel izquierdo con nombres reales
            self.update_skins_list()
            
            self.log(f"[OK] Loaded {len(self.all_names)} skins from {os.path.basename(swf_path)}")
            
        except Exception as e:
            self.log(f"ERROR loading SWF: {str(e)}")
            messagebox.showerror("Load Error", f"Failed to load SWF file:\n{str(e)}")
    
    def toggle_sort(self):
        """Alterna entre ordenar A-Z y Z-A"""
        self.sort_ascending = not self.sort_ascending
        
        if self.sort_ascending:
            self.sort_button.configure(text="Sort A-Z")
            self.all_names.sort()
        else:
            self.sort_button.configure(text="Sort Z-A")
            self.all_names.sort(reverse=True)
            
        self.filter_names_list()
        
        # Actualizar lista con nombres formateados
        self.update_skins_list()
        self.log(f"Sorted {'A-Z' if self.sort_ascending else 'Z-A'}")
    
    def toggle_filter(self):
        """Activa/desactiva el filtrado de skins por leyenda"""
        self.filter_enabled = not self.filter_enabled
        
        # Recargar la lista si hay un SWF cargado
        if self.extractorSelectedSwf and self.current_legend_name:
            # Re-extraer todas las skins
            listNames = Methods.get_all_skin_names(self.extractorSelectedSwf, 0)
            names = list(listNames) if listNames else []
            all_skin_names = [name for name in names if name and not name[0].isdigit()]
            
            # Aplicar filtro si está activo y es archivo compartido
            is_shared_swf = self.swfName in ["Gfx_Skins_02.swf", "Gfx_Skins_04.swf"]
            
            if is_shared_swf and self.filter_enabled:
                self.all_names = self.filter_skins_by_legend(all_skin_names, self.current_legend_name)
                self.log(f"[OK] Filter enabled - showing {len(self.all_names)} skins")
            else:
                self.all_names = all_skin_names
                self.log(f"[OK] Filter disabled - showing all {len(self.all_names)} skins")
            
            self.displayed_names = self.all_names.copy()
            self.update_skins_list()
    
    def update_skins_list(self):
        """Actualiza la lista de skins mostrando primero el nombre real y luego el file name"""
        if not hasattr(self, 'namesList'):
            return

        self.namesList.configure(state=tk.NORMAL)
        self.namesList.delete("1.0", tk.END)

        # Preparar lista de nombres reales (si existe lang_reader) para calcular anchos
        display_names = []
        for name in self.displayed_names:
            real_name = name
            if self.lang_reader:
                try:
                    translated = self.lang_reader.get_skin_name(name, 1)
                    if translated and translated != name:
                        real_name = translated
                except:
                    pass
            display_names.append(real_name)

        # Agregar encabezados de columnas (ahora Skin Name primero)
        header_skin = "Skin Name"
        header_file = "File Name"
        separator = "-" * 30 + "\t" + "-" * 20

        self.namesList.insert(tk.END, header_skin, "header")
        self.namesList.insert(tk.END, "\t", "header")
        self.namesList.insert(tk.END, header_file + "\n", "header")
        self.namesList.insert(tk.END, separator + "\n", "separator")

        # Agregar cada skin con formato (Skin Name primero, luego File Name)
        for idx, name in enumerate(self.displayed_names):
            real_name = display_names[idx] if idx < len(display_names) else name
            
            # Determinar fondo alterno por fila
            row_tag = "row_alt" if idx % 2 != 0 else "row_normal"

            # Columna 1: Nombre real (Skin Name) alineado a la izquierda
            self.namesList.insert(tk.END, real_name, ("display", row_tag))

            # Espaciador entre columnas (usamos tabulador)
            self.namesList.insert(tk.END, "\t", ("separator", row_tag))

            # Columna 2: Nombre técnico (File Name)
            tech_text = name + "\n"
            self.namesList.insert(tk.END, tech_text, ("technical", row_tag))
        
        self.namesList.configure(state=tk.DISABLED)
    
    def on_text_click(self, event):
        """Maneja clics en el widget de texto"""
        # Obtener la línea clickeada
        index = self.namesList.index(f"@{event.x},{event.y}")
        line_num = int(index.split('.')[0])
        
        # Ignorar clics en encabezado (líneas 1 y 2)
        if line_num <= 2:
            return
        
        # Calcular el índice real (línea 3 = índice 0)
        actual_index = line_num - 3
        
        # Verificar que el índice sea válido
        if actual_index < 0 or actual_index >= len(self.displayed_names):
            return
        
        # Remover selección anterior
        self.namesList.tag_remove("selected", "1.0", tk.END)
        
        # Seleccionar línea actual
        self.namesList.tag_add("selected", f"{line_num}.0", f"{line_num}.end")
        
        # Actualizar vista previa de la skin y guardar índice real para exportación
        selected_name = self.displayed_names[actual_index]
        self.selected_skin_index = self.all_names.index(selected_name) if selected_name in self.all_names else actual_index

        
        # Obtener solo el nombre real (sin el "TechnicalName -> ")
        real_name = selected_name  # Por defecto usar nombre técnico
        if self.lang_reader:
            translated_name = self.lang_reader.get_skin_name(selected_name, 1)
            if translated_name and translated_name != selected_name:
                real_name = translated_name
        
        legend_name = self.current_legend_name if self.current_legend_name else "Unknown"
        
        # Actualizar en un hilo separado para no bloquear la UI
        threading.Thread(
            target=self.update_skin_preview,
            args=(real_name, legend_name),
            daemon=True
        ).start()
    
    def filter_names_list(self, event=None):
        """Filtra la lista de nombres según búsqueda"""
        search_text = self.search_entry.get().lower()
        
        if not search_text.strip():
            self.displayed_names = self.all_names.copy()
            self.update_skins_list()
            return
        
        # Filtrar por nombre técnico O nombre real
        filtered_names = []
        for name in self.all_names:
            display_name = self.get_skin_display_name(name)
            if search_text in name.lower() or search_text in display_name.lower():
                filtered_names.append(name)
        
        self.displayed_names = filtered_names
        self.update_skins_list()
        
        self.log(f"Found {len(filtered_names)} skins matching '{search_text}'")
    
    def export_shapes(self):
        """Exporta shapes del SWF seleccionado"""
        if not self.extractorSelectedSwf:
            messagebox.showwarning("No SWF Loaded", "Please load a SWF file first")
            self.log("ERROR: No SWF loaded")
            return
            
        if self.selected_skin_index is None or self.selected_skin_index >= len(self.all_names):
            messagebox.showwarning("No Skin Selected", "Please select a skin from the list")
            self.log("ERROR: No skin selected")
            return
        
        try:
            selected_name = self.all_names[self.selected_skin_index]
            display_name = self.get_skin_display_name(selected_name)
            
            # Obtener el SWF correcto para esta skin
            swf_to_use = self.extractorSelectedSwf
            swf_name_to_use = self.swfName
            
            if selected_name in self.skin_to_swf_map:
                swf_path, swf_obj = self.skin_to_swf_map[selected_name]
                swf_to_use = swf_obj
                swf_name_to_use = os.path.basename(swf_path)
                self.log(f"Using SWF: {swf_name_to_use}")
                
            self.log(f"Filtering SWF for skin: {display_name}...")
            filtered_swf = Methods.export_mod(
                [],  # assets to extract
                swf_to_use,
                swf_name_to_use,
                selected_name
            )
            
            self.log("Exporting shapes as SVG...")
            
            # Exportar shapes (usando el SWF filtrado)
            Methods.extract_shapes(filtered_swf, "SVG", False)
            
            self.log("[OK] Shapes exported successfully!")
            messagebox.showinfo("Export Complete", "Shapes exported successfully!")
            
        except Exception as e:
            self.log(f"ERROR during export: {str(e)}")
            messagebox.showerror("Export Error", f"Failed to export shapes:\n{str(e)}")
    
    def export_sprites(self):
        """Exporta sprites del skin seleccionado"""
        if not self.extractorSelectedSwf:
            messagebox.showwarning("No SWF Loaded", "Please load a SWF file first")
            self.log("ERROR: No SWF loaded")
            return
        
        if self.selected_skin_index is None or self.selected_skin_index >= len(self.all_names):
            messagebox.showwarning("No Skin Selected", "Please select a skin from the list")
            self.log("ERROR: No skin selected")
            return
        
        if not self.mods_path:
            messagebox.showwarning("Mods Path Not Set", "Please set the Mods path in the main dashboard settings.")
            self.log("ERROR: Mods path not configured")
            return
        
        try:
            # Obtener nombre técnico desde all_names
            selected_name = self.all_names[self.selected_skin_index]
            display_name = self.get_skin_display_name(selected_name)
            
            # Obtener el SWF correcto para esta skin
            swf_to_use = self.extractorSelectedSwf
            swf_name_to_use = self.swfName
            
            if selected_name in self.skin_to_swf_map:
                swf_path, swf_obj = self.skin_to_swf_map[selected_name]
                swf_to_use = swf_obj
                swf_name_to_use = os.path.basename(swf_path)
                self.log(f"Using SWF: {swf_name_to_use}")
            
            self.log(f"Filtering SWF for skin: {display_name}...")
            filtered_swf = Methods.export_mod(
                [],  # assets to extract
                swf_to_use,
                swf_name_to_use,
                selected_name
            )
            
            self.log(f"Exporting sprites for: {display_name}")
            
            # Exportar sprites
            Methods.extract_sprites(
                selected_name,
                filtered_swf,
                "SVG",  # mode
                self.ExportScaleUsed,
                swf_name_to_use,
                False,  # is_swf
                False,  # export_folder
                self.mods_path,
                1  # filter_list_size
            )
            
            self.log(f"[OK] Sprites exported successfully for {display_name}!")
            messagebox.showinfo("Export Complete", f"Sprites exported successfully!\nSkin: {display_name}")
            
        except Exception as e:
            self.log(f"ERROR during export: {str(e)}")
            messagebox.showerror("Export Error", f"Failed to export sprites:\n{str(e)}")
    
    def export_swf(self):
        """Exporta un SWF mod"""
        if not self.extractorSelectedSwf:
            messagebox.showwarning("No SWF Loaded", "Please load a SWF file first")
            self.log("ERROR: No SWF loaded")
            return
        
        if self.selected_skin_index is None or self.selected_skin_index >= len(self.all_names):
            messagebox.showwarning("No Skin Selected", "Please select a skin from the list")
            self.log("ERROR: No skin selected")
            return
        
        if not self.mods_path:
            messagebox.showwarning("Mods Path Not Set", "Please set the Mods path in the main dashboard settings.")
            self.log("ERROR: Mods path not configured")
            return
        
        try:
            # Obtener nombre técnico desde all_names
            selected_name = self.all_names[self.selected_skin_index]
            display_name = self.get_skin_display_name(selected_name)
            
            # Obtener el SWF correcto para esta skin
            swf_to_use = self.extractorSelectedSwf
            swf_name_to_use = self.swfName
            
            if selected_name in self.skin_to_swf_map:
                swf_path, swf_obj = self.skin_to_swf_map[selected_name]
                swf_to_use = swf_obj
                swf_name_to_use = os.path.basename(swf_path)
                self.log(f"Using SWF: {swf_name_to_use}")
            
            self.log(f"Exporting SWF mod for: {display_name}")
            
            # Exportar SWF
            generated_swf = Methods.export_mod(
                [],  # assets to extract (vacío por ahora)
                swf_to_use,
                swf_name_to_use,
                selected_name
            )
            
            # Preguntar dónde guardar
            save_path = filedialog.asksaveasfilename(
                initialdir=self.mods_path,
                defaultextension=".swf",
                filetypes=[("SWF files", "*.swf")],
                initialfile=f"{selected_name}_mod.swf"
            )
            
            if save_path:
                if not save_path.endswith(".swf"):
                    save_path += ".swf"
                
                Methods.save_swf_to(generated_swf, save_path)
                
                self.log(f"[OK] SWF mod saved: {os.path.basename(save_path)}")
                messagebox.showinfo("Export Complete", f"SWF mod saved successfully!\n{save_path}")
                
                # Abrir carpeta
                os.startfile(os.path.dirname(save_path))
            
        except Exception as e:
            self.log(f"ERROR during export: {str(e)}")
            messagebox.showerror("Export Error", f"Failed to export SWF:\n{str(e)}")
    
    def filter_skins_by_legend(self, skin_names, legend_name):
        """
        Filtra las skins para mostrar solo las de la leyenda seleccionada.
        Maneja crossovers verificando si el código técnico contiene el nombre base de la leyenda.
        
        Args:
            skin_names: Lista de nombres técnicos de skins
            legend_name: Nombre de la leyenda (ej: "sidra", "caspian")
            
        Returns:
            Lista filtrada de skins
        """
        # Si no hay lector de idiomas, retornar todas las skins
        if not self.lang_reader:
            return skin_names
        
        # Obtener el nombre real de la leyenda
        legend_display_name = None
        
        # Intentar obtener desde legends_data si está disponible
        if self.legends_data:
            for legend in self.legends_data:
                if legend.get('legend_name_key', '').lower() == legend_name.lower():
                    legend_display_name = legend.get('bio_name')
                    break
        
        # Si no se encuentra, capitalizar el nombre
        if not legend_display_name:
            legend_display_name = legend_name.replace("_", " ").title()
        
        # Diccionario de mapeo para leyendas con nombres especiales
        legend_mapping = {
            "lord_vraxx": "Vraxx",
            "queen_nai": "Nai",
            "sir_roland": "Roland",
            "wu_shang": "WuShang",
            "lin_fei": "LinFei",
            "king_zuva": "Zuva"
        }
        
        # Obtener nombre base para búsqueda en códigos técnicos
        base_name = legend_mapping.get(legend_name.lower(), legend_name.replace("_", ""))
        
        filtered_skins = []
        
        for skin_code in skin_names:
            try:
                # Obtener el nombre real de la skin
                real_name = self.lang_reader.get_skin_name(skin_code, 1)
                
                # Método 1: Verificar si el nombre de la leyenda está en el nombre real
                # Esto maneja la mayoría de casos
                name_match = legend_display_name.lower() in real_name.lower()
                
                # Método 2: Verificar si el código técnico contiene el nombre base
                # Esto ayuda con crossovers (ej: "JakeFinn" contiene "Finn")
                code_match = base_name.lower() in skin_code.lower()
                
                # Método 3: Verificar si es la skin por defecto (nombre vacío o igual)
                is_default = skin_code == "" or skin_code.lower() == base_name.lower()
                
                # Método 4: Excluir crossovers que pertenecen a OTRA leyenda
                # Buscar si el código contiene nombres de OTRAS leyendas
                is_other_legend_crossover = False
                for other_legend in self.diccionario_swf.keys():
                    if other_legend != legend_name:
                        other_base = legend_mapping.get(other_legend, other_legend.replace("_", ""))
                        # Si el código contiene otra leyenda Y NO contiene la nuestra
                        if other_base.lower() in skin_code.lower() and base_name.lower() not in skin_code.lower():
                            is_other_legend_crossover = True
                            break
                
                # Incluir la skin si coincide Y no es crossover de otra leyenda
                if (name_match or code_match or is_default) and not is_other_legend_crossover:
                    filtered_skins.append(skin_code)
                    
            except Exception as e:
                # Si hay error, incluir la skin por defecto
                filtered_skins.append(skin_code)
        
        # Si no se encontraron skins filtradas, retornar todas (para evitar listas vacías)
        if not filtered_skins:
            self.log(f"[WARNING] No skins found for {legend_display_name}, showing all skins")
            return skin_names
        
        self.log(f"Filtered {len(filtered_skins)}/{len(skin_names)} skins for {legend_display_name}")
        return filtered_skins
    
    def get_skin_display_name(self, technical_name):
        """
        Obtiene el nombre formateado de una skin
        
        Args:
            technical_name: Nombre técnico (ej: "EpicOrion")
            
        Returns:
            Nombre formateado "TechnicalName -> Display Name" o solo technical_name
        """
        if not technical_name:
            return "Default"
        
        # Si no hay lector de idiomas, retornar el nombre técnico
        if not self.lang_reader:
            return technical_name
        
        try:
            # Obtener nombre real del archivo de idioma
            real_name = self.lang_reader.get_skin_name(technical_name, 1)
            
            # Si se encontró un nombre diferente, mostrarlo en el formato solicitado
            if real_name and real_name != technical_name:
                return f"{technical_name} -> {real_name}"
            else:
                return technical_name
                
        except Exception as e:
            print(f"Error getting skin name for {technical_name}: {e}")
            return technical_name
    
    def get_technical_name_from_display(self, display_name):
        """
        Extrae el nombre técnico de un nombre formateado
        
        Args:
            display_name: Nombre formateado "TechnicalName -> Display Name"
            
        Returns:
            Nombre técnico
        """
        if " -> " in display_name:
            return display_name.split(" -> ")[0]
        return display_name
    
    def log(self, message):
        """Añade un mensaje al log"""
        if hasattr(self, 'log_text'):
            self.log_text.insert("end", f"{message}\n")
            self.log_text.see("end")
    
    def clear_skins_cache(self):
        """Limpia el caché de imágenes de skins"""
        import shutil
        try:
            if os.path.exists(self.skins_cache_dir):
                shutil.rmtree(self.skins_cache_dir)
                os.makedirs(self.skins_cache_dir, exist_ok=True)
                print("[OK] Skins cache cleared")
        except Exception as e:
            print(f"[WARNING] Could not clear skins cache: {e}")
    
    def get_skin_image_from_wiki(self, skin_name, legend_name):
        """
        Descarga la imagen de una skin desde la wiki oficial de Brawlhalla
        
        Args:
            skin_name: Nombre de la skin (ej. "Orion Prime")
            legend_name: Nombre de la leyenda (ej. "Orion")
            
        Returns:
            Ruta al archivo de imagen descargado, o None si falla
        """
        try:
            # Normalizar nombres para el caché
            cache_filename = f"{skin_name.replace(' ', '_').replace('/', '_')}.png"
            cache_path = os.path.join(self.skins_cache_dir, cache_filename)
            
            # Si ya existe en caché, retornarla
            if os.path.exists(cache_path):
                return cache_path
            
            # Construir URL de la wiki usando el formato exacto
            # Formato: https://brawlhalla.wiki.gg/wiki/NOMBRE_SKIN#/media/File:NOMBRE_SKIN.png
            # Ejemplo: https://brawlhalla.wiki.gg/wiki/Alpine_Kaya#/media/File:Alpine_Kaya.png
            wiki_skin_name = skin_name.replace(" ", "_")
            wiki_url = f"https://brawlhalla.wiki.gg/wiki/{wiki_skin_name}#/media/File:{wiki_skin_name}.png"
            
            # Imprimir la URL para debug
            self.log(f"[DEBUG] Trying URL: {wiki_url}")
            
            # Hacer request a la página de la wiki
            response = requests.get(wiki_url, timeout=5)
            response.raise_for_status()
            
            # Buscar la URL real de la imagen en el HTML
            html = response.text
            
            # Buscar patrones de URL de imagen en la wiki (múltiples patrones)
            patterns = [
                # Patrón 1: URL en meta property og:image
                r'<meta\s+property="og:image"\s+content="([^"]*\.png[^"]*)"',
                # Patrón 2: URL directa en el atributo src de img
                r'<img[^>]*src="(https://static\.wikia\.nocookie\.net/brawlhalla[^"]*\.png[^"]*)"',
                # Patrón 3: URL en data-src
                r'data-src="(https://static\.wikia\.nocookie\.net/brawlhalla[^"]*\.png[^"]*)"',
                # Patrón 4: URL en href
                r'href="(https://static\.wikia\.nocookie\.net/brawlhalla[^"]*\.png[^"]*)"',
                # Patrón 5: Cualquier URL de imagen de Brawlhalla
                r'(https://static\.wikia\.nocookie\.net/brawlhalla_gamepedia/images/[^"\s]*\.png)',
                # Patrón 6: URL alternativa de wikia
                r'(https://static\.wikia\.nocookie\.net/brawlhalla/images/[^"\s]*\.png)',
            ]
            
            image_url = None
            for pattern in patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    image_url = match.group(1)
                    # Limpiar parámetros de escala
                    image_url = re.sub(r'/revision/.*', '', image_url)
                    image_url = re.sub(r'/scale-to-width.*', '', image_url)
                    image_url = re.sub(r'\?.*', '', image_url)  # Limpiar query params
                    self.log(f"[DEBUG] Found image URL: {image_url}")
                    break
            
            if not image_url:
                self.log(f"[WARNING] Could not find image URL for {skin_name}")
                self.log(f"[DEBUG] HTML snippet: {html[:500]}")  # Mostrar inicio del HTML para debug
                return None
            
            # Descargar la imagen
            img_response = requests.get(image_url, timeout=5)
            img_response.raise_for_status()
            
            # Guardar en caché
            with open(cache_path, 'wb') as f:
                f.write(img_response.content)
            
            self.log(f"[OK] Downloaded skin image: {skin_name}")
            return cache_path
            
        except Exception as e:
            self.log(f"[WARNING] Could not download image for {skin_name}: {e}")
            return None
    
    def on_preview_resize(self, event=None):
        """Redimensiona la imagen cuando cambia el tamaño del panel de preview"""
        if not hasattr(self, 'current_pil_image') or not self.current_pil_image:
            return
        
        if not hasattr(self, '_preview_wrapper') or not self._preview_wrapper:
            return
        
        try:
            # Use the wrapper size (it won't grow with the image)
            frame_width = self._preview_wrapper.winfo_width() - 10
            frame_height = self._preview_wrapper.winfo_height() - 10
            
            # Hard cap to max preview size
            frame_width = min(frame_width, self.MAX_PREVIEW_W)
            frame_height = min(frame_height, self.MAX_PREVIEW_H)
            
            if frame_width <= 0 or frame_height <= 0:
                return
            
            # Crear una copia de la imagen original
            pil_image = self.current_pil_image.copy()
            
            # Calcular ratio para mantener aspecto (nunca agrandar más que el original)
            img_width, img_height = pil_image.size
            width_ratio = frame_width / img_width
            height_ratio = frame_height / img_height
            ratio = min(width_ratio, height_ratio, 1.0)  # Clamp to 1.0 = never upscale
            
            # Calcular nuevo tamaño
            new_width = max(1, int(img_width * ratio))
            new_height = max(1, int(img_height * ratio))
            
            # Redimensionar
            pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convertir a CTkImage
            ctk_image = ctk.CTkImage(
                light_image=pil_image,
                dark_image=pil_image,
                size=(new_width, new_height)
            )
            
            # Actualizar label
            self.skin_preview_label.configure(image=ctk_image, text="")
            self.skin_preview_label.image = ctk_image  # Mantener referencia
            
        except Exception as e:
            pass  # Ignorar errores durante el redimensionamiento
    
    def update_skin_preview(self, skin_name, legend_name):
        """
        Actualiza la vista previa de la skin seleccionada
        
        Args:
            skin_name: Nombre de la skin para mostrar
            legend_name: Nombre de la leyenda
        """
        if not hasattr(self, 'skin_preview_label'):
            return
        
        # Mostrar mensaje de carga
        self.container.after(0, lambda: self.skin_preview_label.configure(
            image=None,
            text="Loading preview..."
        ))
        
        # Obtener imagen de la wiki
        image_path = self.get_skin_image_from_wiki(skin_name, legend_name)
        
        # Si no se pudo obtener de la wiki, usar imagen por defecto
        if not image_path or not os.path.exists(image_path):
            default_image_path = os.path.join(os.path.dirname(__file__), "assets", "default_skin.png")
            if os.path.exists(default_image_path):
                image_path = default_image_path
                self.log(f"[INFO] Using default image for {skin_name}")
        
        if image_path and os.path.exists(image_path):
            try:
                # Cargar imagen original
                pil_image = Image.open(image_path)
                
                # Guardar imagen original para redimensionamiento
                self.current_pil_image = pil_image.copy()
                self.current_image_path = image_path
                
                # Obtener tamaño disponible del wrapper (non-propagating)
                if hasattr(self, '_preview_wrapper') and self._preview_wrapper.winfo_exists():
                    frame_width = self._preview_wrapper.winfo_width() - 10
                    frame_height = self._preview_wrapper.winfo_height() - 10
                else:
                    frame_width = 300
                    frame_height = 300
                
                # Hard cap to max preview size
                frame_width = min(max(frame_width, 50), self.MAX_PREVIEW_W)
                frame_height = min(max(frame_height, 50), self.MAX_PREVIEW_H)
                
                # Calcular ratio para mantener aspecto (nunca agrandar)
                img_width, img_height = pil_image.size
                width_ratio = frame_width / img_width
                height_ratio = frame_height / img_height
                ratio = min(width_ratio, height_ratio, 1.0)
                
                # Calcular nuevo tamano
                new_width = max(1, int(img_width * ratio))
                new_height = max(1, int(img_height * ratio))
                
                # Redimensionar
                pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Convertir a CTkImage
                ctk_image = ctk.CTkImage(
                    light_image=pil_image,
                    dark_image=pil_image,
                    size=(new_width, new_height)
                )
                
                # Actualizar label en el hilo principal
                def update_ui():
                    self.skin_preview_label.configure(image=ctk_image, text="")
                    self.skin_preview_label.image = ctk_image  # Mantener referencia
                
                self.container.after(0, update_ui)
                
            except Exception as e:
                self.log(f"[ERROR] Could not load skin preview: {e}")
                self.container.after(0, lambda: self.skin_preview_label.configure(
                    image=None,
                    text="Error loading image"
                ))
        else:
            # Limpiar imagen actual
            self.current_pil_image = None
            self.current_image_path = None
            
            # Mostrar mensaje de no disponible
            self.container.after(0, lambda: self.skin_preview_label.configure(
                image=None,
                text="No preview available"
            ))
    
    def show(self):
        """Muestra el módulo"""
        if self.container:
            self.container.pack(fill="both", expand=True)
    
    def hide(self):
        """Oculta el módulo"""
        if self.container:
            self.container.pack_forget()
    
    def destroy(self):
        """Limpia los recursos"""
        # Marcar que estamos destruyendo (para detener threads)
        self._is_destroying = True
        
        # Limpiar caché de skins
        try:
            self.clear_skins_cache()
        except:
            pass
        
        # Destruir container
        if self.container:
            try:
                self.container.destroy()
            except:
                pass
            self.container = None
