"""
HandModdingToolModule.py - Brawlhalla Modding Toolkit (BMT)
Module for customizing legend hand models, colors, and exporting UI_MainMenu.swf carriers / Mod Sources.
Supports multiple skin hand swaps via the Hand Studio queue system.
"""

import os
import re
import sys
import json
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image
from pathlib import Path

# Local imports
from .ToolModuleBase import ToolModule
from src.utils.ThemeManager import BMTTheme, ACCENTS, BMTToolTip
from src.utils.vcp_wrapper import ask_color
from src.svg_utils import render_svg

# LIB path for Methods, FFDEC & BrawlhallaLangReader
LIB_PATH = Path(__file__).parent.parent.parent / "Lib"
if str(LIB_PATH) not in sys.path:
    sys.path.append(str(LIB_PATH))

Methods = None
BrawlhallaLangReader = None
SwzReader = None

try:
    import importlib.util
    if "Methods" in sys.modules:
        Methods = sys.modules["Methods"]
    else:
        methods_path = LIB_PATH / "Methods.py"
        if methods_path.exists():
            spec = importlib.util.spec_from_file_location("Methods", str(methods_path))
            Methods = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(Methods)
            sys.modules["Methods"] = Methods

    if "BrawlhallaLangReader" in sys.modules:
        BrawlhallaLangReader = sys.modules["BrawlhallaLangReader"]
    else:
        langreader_path = LIB_PATH / "BrawlhallaLangReader.py"
        if langreader_path.exists():
            spec = importlib.util.spec_from_file_location("BrawlhallaLangReader", str(langreader_path))
            BrawlhallaLangReader = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(BrawlhallaLangReader)
            sys.modules["BrawlhallaLangReader"] = BrawlhallaLangReader

    if "SwzReader" in sys.modules:
        SwzReader = sys.modules["SwzReader"]
    else:
        swzreader_path = LIB_PATH / "SwzReader.py"
        if swzreader_path.exists():
            spec = importlib.util.spec_from_file_location("SwzReader", str(swzreader_path))
            SwzReader = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(SwzReader)
            sys.modules["SwzReader"] = SwzReader
except Exception as e:
    print(f"[HandModdingTool] Could not load Lib modules: {e}")

# Mapping of Hand Shape Suffix -> SVG Character ID in HandShapes
HAND_SHAPE_MAP = {
    "Bare": "2807",
    "Base2": "2805",
    "BaseClaw": "2803",
    "BaseHand": "2801",
    "BlueRing": "2799",
    "Claw": "2797",
    "Claw2": "2795",
    "Cloven": "2793",
    "Doom": "2791",
    "Feather": "2789",
    "FinnRobot": "2787",
    "FurBare": "2785",
    "Glove": "2783",
    "Glove2": "2781",
    "Glow": "2779",
    "Hoof": "2777",
    "Jewelry": "2775",
    "KFP": "2773",
    "Mitt": "2771",
    "Padded": "2769",
    "Paw": "2767",
    "Regal": "2765",
    "Reptile": "2763",
    "Rings": "2761",
    "Segment": "2759",
    "SegmentClaw": "2757",
    "SU": "2755",
    "AT": "2751",
    "Turtles": "2753",
}

# Fallback known legend costumes in case game language file is unavailable
FALLBACK_COSTUMES = [
    ("Fiona (Tezca)", "LuchadorFiona"),
    ("Base Tezca", "Luchador"),
    ("Chelsea (Tezca)", "LuchadorChelsea"),
    ("El Macho (Tezca)", "LuchadorMacho"),
    ("Base Bodvar", "Viking"),
    ("Bear'dvar (Bodvar)", "VikingBear"),
    ("Cyber Bodvar", "VikingCyber"),
    ("Wreck-it Bodvar", "VikingWreckIt"),
    ("Base Hattori", "Ninja"),
    ("Demon Bride (Hattori)", "NinjaBride"),
    ("Kill-Thrill Hattori", "NinjaMotorcycle"),
    ("Base Orion", "Valkyrie"),
    ("Metadev Orion", "ValkyrieMetadev"),
    ("Harpe (Orion)", "ValkyrieHarpe"),
    ("Base Val", "TechnoNinja"),
    ("Metadev Val", "MetadevVal"),
    ("Base Nix", "Reaper"),
    ("Metadev Nix", "MetadevNix"),
    ("Mythic Nix", "MythicNix"),
    ("Base Asuri", "Cat"),
    ("Apex Predator (Asuri)", "CatApex"),
    ("Base Mordex", "Werewolf"),
    ("Fenrir Mordex", "WerewolfFenrir"),
    ("Base Yumiko", "Ninetails"),
    ("Tokyo Yumiko", "NinetailsTokyo"),
]


def obf_string(text: str, key: int = 15):
    """Obfuscates a string into integer array for BrawlForge carrier."""
    ab = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.'
    arr = []
    for i, char in enumerate(text):
        if char in ab:
            v = ab.index(char)
            arr.append((v + key + i * 7) % 65)
        else:
            arr.append(0)
    return arr, key


class HandModdingToolModule(ToolModule):
    """Module for customizing legend hand shapes, managing multi-skin Hand Studio queues, and exporting SWF/Mod Source."""

    def __init__(self, parent, game_path, mods_path, icons=None):
        super().__init__(parent, game_path, mods_path, icons=icons)
        self.hand_shapes_dir = Path(__file__).parent.parent.parent / "resources" / "assets" / "HandShapes"
        self.tool_icon_path = Path(__file__).parent.parent.parent / "resources" / "assets" / "Tool Icons" / "Hand_Modding_Tool.png"
        
        # Internal bundled carrier detection (no user input needed)
        self.carrier_path = self._detect_internal_carrier()
        self.gfx_hands_path = self._detect_gfx_hands()
        
        self.selected_hand_name = "Bare"
        self.custom_costume_name = "LuchadorFiona"
        
        # All loaded skins: list of (display_label, costume_code)
        self.all_skins = []
        self.filtered_skins = []
        
        # Detected fill colors for the CURRENT hand SVG: list of orig_hex
        self.detected_colors = []
        # Color mapping: original_hex -> user_custom_hex
        self.color_map = {}
        self.color_buttons = {}

        # Hand Studio queue list: list of dicts {skin_label, costume_name, hand_name, color_map}
        self.studio_modifications = []
        self.editing_studio_index = None

        # Skin Palette Colors state
        self.skin_palette_colors = []
        self._skin_palette_cache = {}
        self.skin_palette_boxes_frame = None
        self.skin_palette_progress = None
        self.target_skin_badge_label = None
        self.gfx_status_label = None

        # Debouncing & Async Batch Loading state
        self._palette_debounce_id = None
        self._batch_after_id = None
        self._palette_render_queue = []
        self._palette_total_count = 0
        self._skin_search_index = []

        # UI references
        self.svg_preview_label = None
        self.status_label = None
        self.studio_scroll = None
        self.studio_title_label = None
        self.btn_send_to_studio = None
        self.edit_actions_frame = None

        # Load all skins from LangReader or Fallback
        self._load_game_skins()

    def get_tool_name(self):
        return "Hand Modding Tool"

    def get_tool_icon(self):
        if self.tool_icon_path.exists():
            try:
                img = Image.open(self.tool_icon_path).convert("RGBA")
                return ctk.CTkImage(light_image=img, dark_image=img, size=(24, 24))
            except Exception:
                pass
        return ""

    def _detect_internal_carrier(self) -> str:
        """Finds the internal carrier SWF bundled in the toolkit without user prompt."""
        candidates = [
            Path(__file__).parent.parent / "utils" / "carriers" / "UI_MainMenu.swf",
            Path(__file__).parent.parent.parent / "resources" / "carriers" / "UI_MainMenu.swf",
            Path(__file__).parent.parent.parent / "src" / "carriers" / "UI_MainMenu.swf",
            Path(__file__).parent.parent.parent / "brawlforge-modding-kit" / "hands-only" / "UI_MainMenu.swf",
            Path(r"x:\Lord Shadow\Documents\Programacion\Brawlhalla\Bmods\BhModLoaderCore\core\assets\carrier_UI_MainMenu.swf"),
        ]
        for c in candidates:
            if c.exists():
                return str(c)
        return ""

    def _detect_gfx_hands(self):
        if self.game_path:
            cand = Path(self.game_path) / "Gfx_Hands.swf"
            if cand.exists():
                return str(cand)
        # Default Steam paths check
        steam_paths = [
            r"X:\SteamLibrary\steamapps\common\Brawlhalla\Gfx_Hands.swf",
            r"C:\Program Files (x86)\Steam\steamapps\common\Brawlhalla\Gfx_Hands.swf",
            r"C:\Program Files\Steam\steamapps\common\Brawlhalla\Gfx_Hands.swf",
            r"D:\SteamLibrary\steamapps\common\Brawlhalla\Gfx_Hands.swf",
        ]
        for sp in steam_paths:
            if os.path.exists(sp):
                return sp
        return ""

    def _load_game_skins(self):
        """Loads all skins from Brawlhalla languages binary files using BrawlhallaLangReader."""
        self.all_skins = []
        
        lang_dir = None
        if self.game_path:
            cand = Path(self.game_path) / "languages"
            if cand.exists():
                lang_dir = cand

        if not lang_dir:
            for sp in [r"X:\SteamLibrary\steamapps\common\Brawlhalla\languages",
                        r"C:\Program Files (x86)\Steam\steamapps\common\Brawlhalla\languages",
                        r"D:\SteamLibrary\steamapps\common\Brawlhalla\languages"]:
                if os.path.exists(sp):
                    lang_dir = Path(sp)
                    break

        if lang_dir and BrawlhallaLangReader:
            try:
                reader = BrawlhallaLangReader.BrawlhallaLangReader(str(lang_dir))
                reader.load_language(1) # English
                translations = reader.translations.get("en", {})

                skins_set = {}
                for k, v in translations.items():
                    if k.startswith("CostumeType_") and k.endswith("_DisplayName"):
                        m = re.match(r"CostumeType_(.*)_DisplayName$", k)
                        if m:
                            code = m.group(1)
                            label = f"{v} ({code})"
                            skins_set[code] = (label, code)

                sorted_skins = sorted(list(skins_set.values()), key=lambda x: x[0].lower())
                self.all_skins = sorted_skins
                print(f"[HandModdingTool] Loaded {len(self.all_skins)} skins from Brawlhalla languages!")
            except Exception as e:
                print(f"[HandModdingTool] Error loading skins from LangReader: {e}")

        if not self.all_skins:
            self.all_skins = FALLBACK_COSTUMES

        self.filtered_skins = list(self.all_skins)

        # Build fast pre-tokenized lookup index for sub-millisecond search
        self._skin_search_index = [
            (label, code, f"{label} {code}".lower())
            for label, code in self.all_skins
        ]

    def create_ui(self):
        """Builds the modern responsive 3-column Hand Modding Tool UI."""
        self.container = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        # Header Title Banner
        header = ctk.CTkFrame(self.container, fg_color="#1E1E1E", corner_radius=10)
        header.pack(fill="x", padx=20, pady=(15, 10))

        title_lbl = ctk.CTkLabel(
            header, text="Hand Modding Studio",
            font=ctk.CTkFont(size=20, weight="bold"), text_color="#E91E63"
        )
        title_lbl.pack(side="left", padx=20, pady=12)

        desc_lbl = ctk.CTkLabel(
            header, text="Batch customize legend hand models & colors | Multi-skin Hand Studio",
            font=ctk.CTkFont(size=12), text_color="#AAAAAA"
        )
        desc_lbl.pack(side="left", padx=10, pady=12)

        # Main 3-Column Layout Container
        main_layout = ctk.CTkFrame(self.container, fg_color="transparent")
        main_layout.pack(fill="both", expand=True, padx=20, pady=5)
        # Requested proportions: Column 0 medium (weight 3), Column 1 large (weight 5), Column 2 small (weight 2)
        main_layout.grid_columnconfigure(0, weight=3)
        main_layout.grid_columnconfigure(1, weight=5)
        main_layout.grid_columnconfigure(2, weight=2)
        main_layout.grid_rowconfigure(0, weight=1)

        # -------------------------------------------------------------
        # LEFT COLUMN (MEDIUM): Required Files & Target Skin Selector
        # -------------------------------------------------------------
        left_frame = ctk.CTkFrame(main_layout, fg_color="#171717", corner_radius=10)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 7))

        left_scroll = ctk.CTkScrollableFrame(left_frame, fg_color="transparent")
        left_scroll.pack(fill="both", expand=True, padx=12, pady=12)

        # 1. Gfx_Hands.swf configuration (Auto-detected)
        ctk.CTkLabel(
            left_scroll, text="1. Gfx_Hands.swf File",
            font=ctk.CTkFont(size=15, weight="bold"), text_color="white"
        ).pack(anchor="w", pady=(0, 6))

        gfx_card = ctk.CTkFrame(left_scroll, fg_color="#242424", corner_radius=8, border_width=1, border_color="#333333")
        gfx_card.pack(fill="x", pady=(0, 10))

        gfx_header_row = ctk.CTkFrame(gfx_card, fg_color="transparent")
        gfx_header_row.pack(fill="x", padx=10, pady=(8, 4))

        is_auto_detected = bool(self.gfx_hands_path and os.path.exists(self.gfx_hands_path))
        status_text = "Detected Automatically" if is_auto_detected else "Set Gfx_Hands.swf"
        status_color = "#00E676" if is_auto_detected else "#FFA726"

        self.gfx_status_label = ctk.CTkLabel(
            gfx_header_row, text=status_text,
            font=ctk.CTkFont(size=11, weight="bold"), text_color=status_color
        )
        self.gfx_status_label.pack(side="left")

        btn_browse_txt = "Change" if is_auto_detected else "Set Gfx_Hands.swf"
        self.btn_gfx_browse = ctk.CTkButton(
            gfx_header_row, text=btn_browse_txt, width=65 if is_auto_detected else 130, height=24,
            fg_color="#E91E63", hover_color="#C2185B", font=ctk.CTkFont(size=11, weight="bold"),
            command=self._browse_gfx_hands
        )
        self.btn_gfx_browse.pack(side="right")

        self.gfx_entry = ctk.CTkEntry(gfx_card, font=ctk.CTkFont(size=11), fg_color="#1A1A1A", border_color="#333333")
        self.gfx_entry.pack(fill="x", padx=10, pady=(0, 8))
        if self.gfx_hands_path:
            self.gfx_entry.insert(0, self.gfx_hands_path)

        # Separator
        ctk.CTkFrame(left_scroll, height=2, fg_color="#2C2C2C").pack(fill="x", pady=(4, 10))

        # 2. Legend & Skin Selector
        ctk.CTkLabel(
            left_scroll, text=f"2. Target Legend Skin ({len(self.all_skins)} Skins)",
            font=ctk.CTkFont(size=15, weight="bold"), text_color="white"
        ).pack(anchor="w", pady=(0, 8))

        # Search Bar
        ctk.CTkLabel(left_scroll, text="Search Skin / Legend:", font=ctk.CTkFont(size=11), text_color="#AAAAAA").pack(anchor="w", pady=(2, 2))
        self.search_entry = ctk.CTkEntry(left_scroll, placeholder_text="Type skin name (e.g. Fiona, Val, Nix...)", font=ctk.CTkFont(size=12), fg_color="#1A1A1A")
        self.search_entry.pack(fill="x", pady=(0, 6))
        self.search_entry.bind("<KeyRelease>", self._filter_skins)
        self.search_entry.bind("<Return>", self._commit_skin_search)

        # Skin Selector Dropdown
        ctk.CTkLabel(left_scroll, text="Select Skin:", font=ctk.CTkFont(size=11), text_color="#AAAAAA").pack(anchor="w", pady=(2, 2))
        skin_labels = [s[0] for s in self.filtered_skins]
        self.skin_menu = ctk.CTkOptionMenu(
            left_scroll,
            values=skin_labels if skin_labels else ["No skins found"],
            command=self._on_skin_dropdown_selected,
            fg_color="#242424", button_color="#E91E63", button_hover_color="#C2185B"
        )
        self.skin_menu.pack(fill="x", pady=(0, 8))
        if skin_labels:
            self.skin_menu.set(skin_labels[0])

        # Costume ID / Manual Costume Name
        ctk.CTkLabel(left_scroll, text="Internal Costume Name (mCostumeName):", font=ctk.CTkFont(size=11), text_color="#AAAAAA").pack(anchor="w", pady=(2, 2))
        self.costume_entry = ctk.CTkEntry(left_scroll, font=ctk.CTkFont(size=12), fg_color="#1A1A1A")
        self.costume_entry.pack(fill="x", pady=(0, 10))
        self.costume_entry.insert(0, self.custom_costume_name)

        # -------------------------------------------------------------
        # MIDDLE COLUMN (LARGE): Hand Model, Colors & Skin Palette Studio
        # -------------------------------------------------------------
        mid_frame = ctk.CTkFrame(main_layout, fg_color="#171717", corner_radius=10)
        mid_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 7))

        # Bottom pinned action bar (Always visible without scrolling)
        mid_bottom_frame = ctk.CTkFrame(mid_frame, fg_color="transparent")
        mid_bottom_frame.pack(side="bottom", fill="x", padx=12, pady=(0, 12))

        # ACTION: Send to Hand Studio Button (ALWAYS VISIBLE OUTSIDE SCROLL)
        self.btn_send_to_studio = ctk.CTkButton(
            mid_bottom_frame, text="Send to Hand Studio",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#00C853", hover_color="#009624",
            height=36,
            command=self._send_to_studio_item
        )
        self.btn_send_to_studio.pack(fill="x", pady=(4, 0))

        # Edit mode actions bar (Save Update & Cancel)
        self.edit_actions_frame = ctk.CTkFrame(mid_bottom_frame, fg_color="transparent")
        self.btn_save_edit = ctk.CTkButton(
            self.edit_actions_frame, text="Save Update",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#FF9800", hover_color="#F57C00",
            height=30,
            command=self._save_studio_edit
        )
        self.btn_save_edit.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_cancel_edit = ctk.CTkButton(
            self.edit_actions_frame, text="Cancel",
            font=ctk.CTkFont(size=12),
            fg_color="#424242", hover_color="#616161",
            height=30, width=60,
            command=self._cancel_studio_edit
        )
        self.btn_cancel_edit.pack(side="right")
        self.edit_actions_frame.pack_forget()

        # Scrollable content area
        mid_scroll = ctk.CTkScrollableFrame(mid_frame, fg_color="transparent")
        mid_scroll.pack(side="top", fill="both", expand=True, padx=12, pady=(12, 6))

        # Section 3 Header
        self.hand_model_title_lbl = ctk.CTkLabel(
            mid_scroll, text="3.Hand Model & Colors",
            font=ctk.CTkFont(size=15, weight="bold"), text_color="white"
        )
        self.hand_model_title_lbl.pack(anchor="w", pady=(0, 6))

        # Dedicated Target Skin Card (Never cut off)
        self.target_skin_card = ctk.CTkFrame(mid_scroll, fg_color="#201524", corner_radius=8, border_width=1, border_color="#E91E63")
        self.target_skin_card.pack(fill="x", pady=(0, 8))

        self.target_skin_badge_label = ctk.CTkLabel(
            self.target_skin_card,
            text=f"Target Skin: {skin_labels[0] if skin_labels else 'None'}",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#FFFFFF",
            wraplength=480, justify="left", anchor="w"
        )
        self.target_skin_badge_label.pack(fill="x", padx=10, pady=8)

        # Hand Shape Model Dropdown
        ctk.CTkLabel(mid_scroll, text="Hand Shape Model:", font=ctk.CTkFont(size=11), text_color="#AAAAAA").pack(anchor="w", pady=(2, 2))
        shape_names = list(HAND_SHAPE_MAP.keys())
        self.shape_menu = ctk.CTkOptionMenu(
            mid_scroll,
            values=shape_names,
            command=self._on_hand_shape_changed,
            fg_color="#242424", button_color="#E91E63", button_hover_color="#C2185B"
        )
        self.shape_menu.pack(fill="x", pady=(0, 8))
        self.shape_menu.set(self.selected_hand_name)

        # Real-time Hand Preview Canvas Frame
        preview_box = ctk.CTkFrame(mid_scroll, fg_color="#0E0E0E", corner_radius=8, height=115)
        preview_box.pack(fill="x", pady=(0, 10))
        preview_box.pack_propagate(False)

        self.svg_preview_label = ctk.CTkLabel(preview_box, text="", image=None)
        self.svg_preview_label.pack(expand=True)

        # ── DUAL COLOR PANELS CONTAINER (Side-by-side) ──
        dual_colors_frame = ctk.CTkFrame(mid_scroll, fg_color="transparent")
        dual_colors_frame.pack(fill="x", pady=(0, 6))
        dual_colors_frame.grid_columnconfigure(0, weight=2)
        dual_colors_frame.grid_columnconfigure(1, weight=3)

        # [LEFT SUBPANEL] Detected Hand Colors
        hand_colors_sub = ctk.CTkFrame(dual_colors_frame, fg_color="transparent")
        hand_colors_sub.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        hand_colors_header = ctk.CTkFrame(hand_colors_sub, fg_color="transparent")
        hand_colors_header.pack(fill="x", pady=(0, 4))

        self.colors_title_lbl = ctk.CTkLabel(
            hand_colors_header, text="Detected Hand Colors:",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="white"
        )
        self.colors_title_lbl.pack(side="left")

        btn_reset_colors = ctk.CTkButton(
            hand_colors_header, text="Reset", width=50, height=20,
            fg_color="#424242", hover_color="#616161", font=ctk.CTkFont(size=10),
            command=self._reset_colors
        )
        btn_reset_colors.pack(side="right")

        self.color_boxes_frame = ctk.CTkFrame(hand_colors_sub, fg_color="#242424", corner_radius=8)
        self.color_boxes_frame.pack(fill="both", expand=True)

        # [RIGHT SUBPANEL] Skin Palette Colors
        skin_palette_sub = ctk.CTkFrame(dual_colors_frame, fg_color="transparent")
        skin_palette_sub.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

        skin_palette_header = ctk.CTkFrame(skin_palette_sub, fg_color="transparent")
        skin_palette_header.pack(fill="x", pady=(0, 4))

        self.palette_title_lbl = ctk.CTkLabel(
            skin_palette_header, text="Skin Palette Colors:",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#E91E63"
        )
        self.palette_title_lbl.pack(side="left")

        self.skin_palette_progress = ctk.CTkProgressBar(
            skin_palette_sub, height=3, fg_color="#1E1E1E", progress_color="#E91E63", corner_radius=2
        )
        self.skin_palette_progress.pack(fill="x", pady=(0, 4))
        self.skin_palette_progress.pack_forget()

        self.skin_palette_boxes_frame = ctk.CTkFrame(skin_palette_sub, fg_color="#242424", corner_radius=8)
        self.skin_palette_boxes_frame.pack(fill="both", expand=True)

        # Initial load of colors for default selected shape & skin
        self._reload_detected_colors_for_current_shape()
        self._reload_skin_palette_colors()
        self._update_hand_model_title()

        # -------------------------------------------------------------
        # RIGHT COLUMN: Hand Studio (Queued Modifications List)
        # -------------------------------------------------------------
        right_frame = ctk.CTkFrame(main_layout, fg_color="#171717", corner_radius=10)
        right_frame.grid(row=0, column=2, sticky="nsew")

        right_header = ctk.CTkFrame(right_frame, fg_color="transparent")
        right_header.pack(fill="x", padx=12, pady=(12, 6))

        self.studio_title_label = ctk.CTkLabel(
            right_header, text="4. Hand Studio (0 Queued)",
            font=ctk.CTkFont(size=15, weight="bold"), text_color="#AB47BC"
        )
        self.studio_title_label.pack(side="left")

        btn_clear_studio = ctk.CTkButton(
            right_header, text="Clear All", width=70, height=24,
            fg_color="#333333", hover_color="#D32F2F", font=ctk.CTkFont(size=11),
            command=self._clear_studio
        )
        btn_clear_studio.pack(side="right")

        self.studio_scroll = ctk.CTkScrollableFrame(right_frame, fg_color="transparent")
        self.studio_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Initial render of empty Hand Studio
        self._render_studio_list()

        # -------------------------------------------------------------
        # BOTTOM ACTION BAR: Export Buttons & Log Status
        # -------------------------------------------------------------
        bottom_bar = ctk.CTkFrame(self.container, fg_color="#171717", corner_radius=10)
        bottom_bar.pack(fill="x", padx=20, pady=(10, 18))

        self.status_label = ctk.CTkLabel(
            bottom_bar, text="Ready: Select skins and build your Hand Studio queue",
            font=ctk.CTkFont(size=12), text_color="#A0A0A0"
        )
        self.status_label.pack(side="left", padx=20, pady=12)

        export_swf_btn = ctk.CTkButton(
            bottom_bar, text="Export UI_MainMenu_HandMod.swf",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#E91E63", hover_color="#C2185B",
            height=36, width=220,
            command=self.export_hand_mod
        )
        export_swf_btn.pack(side="right", padx=(10, 16), pady=12)

        export_source_btn = ctk.CTkButton(
            bottom_bar, text="Export Mod Source (Scripts)",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#7B1FA2", hover_color="#4A148C",
            height=36, width=210,
            command=self.export_mod_creator_source
        )
        export_source_btn.pack(side="right", padx=(10, 0), pady=12)

        return self.container

    # -----------------------------------------------------------------
    # HAND STUDIO QUEUE MANAGEMENT
    # -----------------------------------------------------------------
    def _send_to_studio_item(self):
        """Adds or updates the current skin modification into Hand Studio queue."""
        costume_name = self.costume_entry.get().strip()
        if not costume_name:
            messagebox.showwarning("Missing Costume Name", "Please enter or select a valid costume name (mCostumeName).")
            return

        skin_label = self.skin_menu.get()
        hand_name = self.selected_hand_name

        item_data = {
            "skin_label": skin_label,
            "costume_name": costume_name,
            "hand_name": hand_name,
            "color_map": dict(self.color_map)
        }

        # Check if costume already exists in list, update if so, else append
        existing_idx = None
        for idx, existing in enumerate(self.studio_modifications):
            if existing["costume_name"] == costume_name:
                existing_idx = idx
                break
        
        if existing_idx is not None:
            self.studio_modifications[existing_idx] = item_data
            if self.status_label:
                self.status_label.configure(text=f"Updated existing skin '{skin_label}' with {hand_name}!", text_color="#4CAF50")
        else:
            self.studio_modifications.append(item_data)
            if self.status_label:
                self.status_label.configure(text=f"Added '{skin_label}' -> {hand_name} to Hand Studio!", text_color="#4CAF50")

        self._render_studio_list()

    def _edit_studio_item(self, index: int):
        if not (0 <= index < len(self.studio_modifications)):
            return

        item = self.studio_modifications[index]
        self.editing_studio_index = index

        # Load into editor widgets
        self.costume_entry.delete(0, tk.END)
        self.costume_entry.insert(0, item["costume_name"])
        self.skin_menu.set(item["skin_label"])
        self.shape_menu.set(item["hand_name"])
        self.selected_hand_name = item["hand_name"]

        # Restore color mapping if saved
        if "color_map" in item and item["color_map"]:
            self.color_map = dict(item["color_map"])
        else:
            self.color_map = {}

        self._reload_detected_colors_for_current_shape()

        # Show edit actions bar and hide regular send button
        if self.btn_send_to_studio:
            self.btn_send_to_studio.pack_forget()
        if self.edit_actions_frame:
            self.edit_actions_frame.pack(fill="x", pady=(4, 0))

        self._update_hand_model_title(item["skin_label"])

        if self.status_label:
            self.status_label.configure(text=f"Editing modification for '{item['skin_label']}'...", text_color="#FFB300")

    def _save_studio_edit(self):
        if self.editing_studio_index is not None and 0 <= self.editing_studio_index < len(self.studio_modifications):
            costume_name = self.costume_entry.get().strip()
            skin_label = self.skin_menu.get()
            hand_name = self.selected_hand_name
            self.studio_modifications[self.editing_studio_index] = {
                "skin_label": skin_label,
                "costume_name": costume_name,
                "hand_name": hand_name,
                "color_map": dict(self.color_map)
            }
            self._cancel_studio_edit()
            self._render_studio_list()
            if self.status_label:
                self.status_label.configure(text=f"Saved changes for '{skin_label}'!", text_color="#4CAF50")

    def _cancel_studio_edit(self):
        self.editing_studio_index = None
        if self.edit_actions_frame:
            self.edit_actions_frame.pack_forget()
        if self.btn_send_to_studio:
            self.btn_send_to_studio.pack(fill="x", pady=(4, 0))
        self._update_hand_model_title()
        if self.status_label:
            self.status_label.configure(text="Edit cancelled.", text_color="#A0A0A0")

    def _delete_studio_item(self, index: int):
        if 0 <= index < len(self.studio_modifications):
            removed = self.studio_modifications.pop(index)
            if self.editing_studio_index == index:
                self._cancel_studio_edit()
            elif self.editing_studio_index is not None and self.editing_studio_index > index:
                self.editing_studio_index -= 1
            self._render_studio_list()
            if self.status_label:
                self.status_label.configure(text=f"Removed '{removed['skin_label']}' from Hand Studio.", text_color="#A0A0A0")

    def _clear_studio(self):
        if not self.studio_modifications:
            return
        if messagebox.askyesno("Clear Hand Studio", "Are you sure you want to remove all queued hand modifications?"):
            self.studio_modifications.clear()
            self._cancel_studio_edit()
            self._render_studio_list()
            if self.status_label:
                self.status_label.configure(text="Hand Studio cleared.", text_color="#A0A0A0")

    def _render_studio_list(self):
        """Renders the queued modification cards inside self.studio_scroll."""
        if not self.studio_scroll:
            return

        for w in self.studio_scroll.winfo_children():
            w.destroy()

        count = len(self.studio_modifications)
        if self.studio_title_label:
            self.studio_title_label.configure(text=f"4. Hand Studio ({count} Queued)")

        if count == 0:
            empty_card = ctk.CTkFrame(self.studio_scroll, fg_color="#1E1E1E", corner_radius=8)
            empty_card.pack(fill="x", pady=20, padx=5)

            ctk.CTkLabel(
                empty_card, text="Hand Studio is Empty",
                font=ctk.CTkFont(size=14, weight="bold"), text_color="#888888"
            ).pack(pady=(15, 4))

            guide_lines = [
                "1. Select a target skin from column 2",
                "2. Choose a hand shape model from column 3",
                "3. Click 'Send to Hand Studio'",
                "4. Export all your customizations together!"
            ]
            for line in guide_lines:
                ctk.CTkLabel(
                    empty_card, text=line,
                    font=ctk.CTkFont(size=11), text_color="#666666"
                ).pack(pady=1)
            ctk.CTkFrame(empty_card, height=10, fg_color="transparent").pack()
            return

        for idx, item in enumerate(self.studio_modifications):
            is_active_edit = (self.editing_studio_index == idx)
            card_bg = "#2A2030" if is_active_edit else "#222222"
            border_color = "#AB47BC" if is_active_edit else "#333333"

            card = ctk.CTkFrame(self.studio_scroll, fg_color=card_bg, corner_radius=8, border_width=1, border_color=border_color)
            card.pack(fill="x", pady=4, padx=2)

            # Actions buttons (PACKED FIRST ON RIGHT TO GUARANTEE CONSTANT VISIBILITY)
            btns_frame = ctk.CTkFrame(card, fg_color="transparent")
            btns_frame.pack(side="right", padx=(2, 6), pady=6)

            btn_edit = ctk.CTkButton(
                btns_frame, text="Edit", width=36, height=22,
                fg_color="#3F51B5", hover_color="#303F9F", font=ctk.CTkFont(size=10, weight="bold"),
                command=lambda i=idx: self._edit_studio_item(i)
            )
            btn_edit.pack(side="left", padx=(0, 3))

            btn_del = ctk.CTkButton(
                btns_frame, text="X", width=24, height=22,
                fg_color="#424242", hover_color="#D32F2F", font=ctk.CTkFont(size=10, weight="bold"),
                command=lambda i=idx: self._delete_studio_item(i)
            )
            btn_del.pack(side="left")

            # Info frame (Packed on left with expand=True and wraplength so text never pushes buttons off)
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, padx=(8, 2), pady=6)

            # Skin Label with auto-wrapping
            ctk.CTkLabel(
                info_frame, text=item["skin_label"],
                font=ctk.CTkFont(size=11, weight="bold"), text_color="white",
                anchor="w", justify="left", wraplength=135
            ).pack(fill="x")

            # Tags frame
            tags_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            tags_frame.pack(fill="x", pady=(2, 0))

            # Internal Code Badge
            code_badge = ctk.CTkLabel(
                tags_frame, text=f"ID: {item['costume_name']}",
                font=ctk.CTkFont(size=9), text_color="#888888", anchor="w"
            )
            code_badge.pack(side="left")

            # Arrow
            ctk.CTkLabel(
                tags_frame, text="->",
                font=ctk.CTkFont(size=9, weight="bold"), text_color="#AB47BC"
            ).pack(side="left", padx=3)

            # Hand Shape Badge
            hand_badge = ctk.CTkLabel(
                tags_frame, text=f"{item['hand_name']}",
                font=ctk.CTkFont(size=9, weight="bold"), text_color="#E91E63", anchor="w"
            )
            hand_badge.pack(side="left")

    # -----------------------------------------------------------------
    # UI EVENT HANDLERS
    # -----------------------------------------------------------------
    def _browse_gfx_hands(self):
        file_path = filedialog.askopenfilename(
            title="Select Gfx_Hands.swf",
            filetypes=[("SWF files", "*.swf"), ("All files", "*.*")]
        )
        if file_path:
            self.gfx_hands_path = file_path
            self.gfx_entry.delete(0, tk.END)
            self.gfx_entry.insert(0, file_path)
            if self.gfx_status_label:
                self.gfx_status_label.configure(text="Detected Automatically", text_color="#00E676")
            if hasattr(self, "btn_gfx_browse") and self.btn_gfx_browse:
                self.btn_gfx_browse.configure(text="Change", width=65)

    def _commit_skin_search(self, event=None):
        """Immediately executes skin selection and palette loading when user presses Enter."""
        if self._palette_debounce_id:
            try:
                self.container.after_cancel(self._palette_debounce_id)
            except Exception:
                pass
            self._palette_debounce_id = None
        self._reload_skin_palette_colors()

    def _filter_skins(self, event=None):
        query = self.search_entry.get().strip().lower()
        if not query:
            self.filtered_skins = list(self.all_skins)
        else:
            q_words = query.split()
            self.filtered_skins = [
                (label, code) for label, code, tokens in self._skin_search_index
                if all(w in tokens for w in q_words)
            ]

        skin_labels = [s[0] for s in self.filtered_skins]
        if self.skin_menu:
            self.skin_menu.configure(values=skin_labels if skin_labels else ["No matching skins"])
            if skin_labels:
                first_label = skin_labels[0]
                first_code = self.filtered_skins[0][1]
                self.skin_menu.set(first_label)
                self.custom_costume_name = first_code
                self.costume_entry.delete(0, tk.END)
                self.costume_entry.insert(0, first_code)
                self._update_hand_model_title(first_label)

                # Generous debounce timer (800ms) so typing never freezes or interrupts the user
                if self._palette_debounce_id:
                    try:
                        self.container.after_cancel(self._palette_debounce_id)
                    except Exception:
                        pass
                self._palette_debounce_id = self.container.after(800, self._reload_skin_palette_colors)

    def _update_hand_model_title(self, skin_name=None):
        name = skin_name
        if not name and hasattr(self, "skin_menu") and self.skin_menu:
            name = self.skin_menu.get()
        if hasattr(self, "target_skin_badge_label") and self.target_skin_badge_label:
            if name and name not in ["No skins found", "No matching skins"]:
                self.target_skin_badge_label.configure(text=f"Target Skin: {name}")
            else:
                self.target_skin_badge_label.configure(text="Target Skin: None")

    def _on_skin_dropdown_selected(self, selected_label):
        # Cancel any pending search debounce since user explicitly picked a skin
        if self._palette_debounce_id:
            try:
                self.container.after_cancel(self._palette_debounce_id)
            except Exception:
                pass
            self._palette_debounce_id = None

        for label, code in self.all_skins:
            if label == selected_label:
                self.custom_costume_name = code
                self.costume_entry.delete(0, tk.END)
                self.costume_entry.insert(0, code)
                self._update_hand_model_title(label)
                self._reload_skin_palette_colors()
                break



    def _get_fallback_skin_palette(self, costume_name: str) -> list:
        """Deterministic curated theme colors for costume names when game SWZ is not present."""
        h_val = sum(ord(c) * (i + 1) for i, c in enumerate(costume_name))
        base_hues = [
            (h_val * 47) % 360,
            (h_val * 73 + 40) % 360,
            (h_val * 19 + 120) % 360,
            (h_val * 31 + 180) % 360,
            (h_val * 53 + 240) % 360,
            (h_val * 89 + 300) % 360,
            (h_val * 97 + 60) % 360,
            (h_val * 61 + 150) % 360,
            (h_val * 83 + 210) % 360,
            (h_val * 41 + 270) % 360,
        ]
        import colorsys
        cols = []
        for hue in base_hues:
            r, g, b = colorsys.hls_to_rgb(hue / 360.0, 0.48, 0.75)
            cols.append(f"#{int(r*255):02X}{int(g*255):02X}{int(b*255):02X}")
        return cols

    def _load_swz_costumes_table(self):
        """Loads and decrypts Game.swz to get official costume color definitions directly from the game."""
        self._swz_costumes_table = {}
        if not self.game_path or not os.path.exists(self.game_path):
            return
        
        try:
            if not SwzReader:
                return
            air_swf = os.path.join(self.game_path, "BrawlhallaAir.swf")
            init_swz = os.path.join(self.game_path, "Init.swz")
            game_swz = os.path.join(self.game_path, "Game.swz")

            if not os.path.exists(air_swf) or not os.path.exists(init_swz) or not os.path.exists(game_swz):
                return

            key = SwzReader.find_swz_key(air_swf, init_swz)
            if not key:
                return

            with open(game_swz, "rb") as f:
                entries = SwzReader.read_swz(f.read(), key)

            if len(entries) > 9:
                import csv, io
                costumes_csv = entries[9].decode("utf-8", errors="ignore")
                lines = costumes_csv.splitlines()
                if len(lines) > 1:
                    reader = csv.DictReader(io.StringIO("\n".join(lines[1:])))
                    for row in reader:
                        name = row.get("CostumeName", "").strip()
                        disp = row.get("DisplayNameKey", "").strip()
                        if name:
                            self._swz_costumes_table[name.lower()] = row
                        if disp:
                            self._swz_costumes_table[disp.lower()] = row
                            clean_disp = disp.replace("CostumeType_", "").replace("_DisplayName", "")
                            self._swz_costumes_table[clean_disp.lower()] = row
                    print(f"[HandModdingTool] Loaded {len(self._swz_costumes_table)} official skin definitions from Game.swz!")
        except Exception as e:
            print(f"[HandModdingTool] Note: SWZ table load skipped ({e})")

    def _extract_skin_palette(self, costume_name: str, skin_label: str) -> list:
        """Extracts all official in-game palette colors for the costume from the decrypted Game.swz registry."""
        cache_key = f"{costume_name}::{skin_label}"
        if hasattr(self, "_skin_palette_cache") and cache_key in self._skin_palette_cache:
            return self._skin_palette_cache[cache_key]

        if not hasattr(self, "_swz_costumes_table") or not self._swz_costumes_table:
            self._load_swz_costumes_table()

        row = None
        if hasattr(self, "_swz_costumes_table") and self._swz_costumes_table:
            candidates = [costume_name]
            if skin_label:
                words = re.findall(r'[A-Za-z0-9]+', skin_label)
                candidates.extend(words)

            for cand in candidates:
                if cand.lower() in self._swz_costumes_table:
                    row = self._swz_costumes_table[cand.lower()]
                    break

        colors_found = []
        seen_hex = set()

        if row:
            owner_hero = row.get("OwnerHero", "").strip()
            owner_row = self._swz_costumes_table.get(owner_hero.lower()) if owner_hero else None

            color_cols = [c for c in row.keys() if c.endswith("_Define") or c.endswith("_Swap")]

            # 1. Skin's own defined colors
            for col in color_cols:
                val = row.get(col, "").strip()
                if val and (val.startswith("0x") or val.startswith("#")):
                    try:
                        hex_str = f"#{int(val, 16):06X}"
                        if hex_str not in seen_hex:
                            seen_hex.add(hex_str)
                            channel = col.replace("_Define", "").replace("_Swap", "")
                            colors_found.append({"name": channel, "hex": hex_str})
                    except Exception:
                        pass

            # 2. Inherited base hero colors for any missing channels
            if owner_row:
                for col in color_cols:
                    val = owner_row.get(col, "").strip()
                    if val and (val.startswith("0x") or val.startswith("#")):
                        try:
                            hex_str = f"#{int(val, 16):06X}"
                            if hex_str not in seen_hex:
                                seen_hex.add(hex_str)
                                channel = col.replace("_Define", "").replace("_Swap", "")
                                colors_found.append({"name": channel, "hex": hex_str})
                        except Exception:
                            pass

        if not colors_found:
            fallback_cols = self._get_fallback_skin_palette(costume_name)
            fallback_channels = ["HairLt", "Hair", "HairDk", "Body1Lt", "Body1", "Body1Dk", "Body2Lt", "Body2", "SpecialLt", "Special", "Cloth", "Weapon"]
            for idx, col_hex in enumerate(fallback_cols[:12]):
                ch_name = fallback_channels[idx] if idx < len(fallback_channels) else f"Channel{idx+1}"
                colors_found.append({
                    "name": ch_name,
                    "hex": col_hex.upper()
                })

        if hasattr(self, "_skin_palette_cache"):
            self._skin_palette_cache[cache_key] = colors_found
        return colors_found

    def _reload_skin_palette_colors(self):
        costume_name = self.costume_entry.get().strip() if hasattr(self, "costume_entry") and self.costume_entry else self.custom_costume_name
        skin_label = self.skin_menu.get() if hasattr(self, "skin_menu") and self.skin_menu else "Default"
        self.skin_palette_colors = self._extract_skin_palette(costume_name, skin_label)
        self._render_skin_palette_boxes()

    def _draw_rect_split_card(self, parent, orig_hex: str, curr_hex: str, width=44, height=34):
        """Creates a compact rounded rectangle split swatch (Top=Old, Bottom=New) with smooth anti-aliasing."""
        card = ctk.CTkFrame(
            parent, width=width, height=height, corner_radius=6,
            border_width=1, border_color="#444444", fg_color="#181818", cursor="hand2"
        )
        card.pack_propagate(False)

        top_half = ctk.CTkFrame(card, fg_color=orig_hex, corner_radius=3, height=(height // 2) - 2)
        top_half.pack(fill="both", expand=True, padx=2, pady=(2, 1))

        bot_half = ctk.CTkFrame(card, fg_color=curr_hex, corner_radius=3, height=(height // 2) - 2)
        bot_half.pack(fill="both", expand=True, padx=2, pady=(1, 2))

        return card

    def _bind_card_interactive(self, widget, on_click, on_enter=None, on_leave=None):
        """Recursively binds click and hover events to a card widget and all of its children."""
        widget.bind("<Button-1>", lambda e: on_click())
        if on_enter:
            widget.bind("<Enter>", lambda e: on_enter())
        if on_leave:
            widget.bind("<Leave>", lambda e: on_leave())
        for child in widget.winfo_children():
            self._bind_card_interactive(child, on_click, on_enter, on_leave)

    def _copy_to_clipboard(self, hex_val: str, card_widget=None):
        try:
            self.container.clipboard_clear()
            self.container.clipboard_append(hex_val)
            self.container.update()
        except Exception:
            pass
        if self.status_label:
            self.status_label.configure(text=f"Copied {hex_val} to clipboard!", text_color="#00E676")
            if hasattr(self, "_status_reset_id") and self._status_reset_id:
                try:
                    self.container.after_cancel(self._status_reset_id)
                except Exception:
                    pass
            self._status_reset_id = self.container.after(
                1800,
                lambda: self.status_label.configure(
                    text="Ready: Select skins and build your Hand Studio queue",
                    text_color="#A0A0A0"
                ) if self.status_label and self.status_label.winfo_exists() else None
            )
        if card_widget and card_widget.winfo_exists():
            orig_border = card_widget.cget("border_color")
            card_widget.configure(border_color="#00E676")
            self.container.after(
                600,
                lambda: card_widget.configure(border_color=orig_border) if card_widget.winfo_exists() else None
            )

    def _render_skin_palette_boxes(self):
        if not self.skin_palette_boxes_frame:
            return

        if self._batch_after_id:
            try:
                self.container.after_cancel(self._batch_after_id)
            except Exception:
                pass
            self._batch_after_id = None

        for w in self.skin_palette_boxes_frame.winfo_children():
            w.destroy()

        if not self.skin_palette_colors:
            if hasattr(self, "skin_palette_progress") and self.skin_palette_progress:
                self.skin_palette_progress.pack_forget()
            ctk.CTkLabel(
                self.skin_palette_boxes_frame, text="No palette swatches available.",
                font=ctk.CTkFont(size=11), text_color="#777777"
            ).pack(pady=10)
            return

        # Prepare progressive batch queue
        self._palette_render_queue = list(self.skin_palette_colors)
        self._palette_total_count = len(self._palette_render_queue)

        if hasattr(self, "skin_palette_progress") and self.skin_palette_progress:
            self.skin_palette_progress.pack(fill="x", pady=(2, 4))
            self.skin_palette_progress.set(0.0)

        # 2-column responsive layout
        self.skin_palette_boxes_frame.grid_columnconfigure(0, weight=1)
        self.skin_palette_boxes_frame.grid_columnconfigure(1, weight=1)

        self._render_palette_batch()

    def _render_palette_batch(self):
        if not self.skin_palette_boxes_frame:
            return

        copy_icon = BMTTheme.get_icon("content_copy", 14)
        BATCH_SIZE = 6

        for _ in range(BATCH_SIZE):
            if not self._palette_render_queue:
                break
            idx = self._palette_total_count - len(self._palette_render_queue)
            item = self._palette_render_queue.pop(0)
            col_hex = item["hex"]
            role_name = item["name"]

            r, c = divmod(idx, 2)

            card = ctk.CTkFrame(
                self.skin_palette_boxes_frame, fg_color="#1C1C1C", corner_radius=6,
                border_width=1, border_color="#333333", cursor="hand2", height=38
            )
            card.grid(row=r, column=c, padx=3, pady=3, sticky="nsew")

            # Swatch square
            swatch = ctk.CTkFrame(
                card, width=20, height=20, corner_radius=4,
                fg_color=col_hex, border_width=1, border_color="#4A4A4A"
            )
            swatch.pack(side="left", padx=(6, 6), pady=6)

            # Info labels
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, pady=3)

            ctk.CTkLabel(
                info_frame, text=role_name,
                font=ctk.CTkFont(size=10, weight="bold"), text_color="#FFFFFF", anchor="w"
            ).pack(fill="x")

            ctk.CTkLabel(
                info_frame, text=col_hex,
                font=ctk.CTkFont(size=9), text_color="#AAAAAA", anchor="w"
            ).pack(fill="x")

            # Hover Copy Icon
            copy_lbl = ctk.CTkLabel(card, text="", image=copy_icon, width=18)
            copy_lbl.pack(side="right", padx=(0, 6))

            def on_skin_enter(cd=card):
                if cd.winfo_exists():
                    cd.configure(border_color="#E91E63", fg_color="#2A1B24")

            def on_skin_leave(cd=card):
                if cd.winfo_exists():
                    cd.configure(border_color="#333333", fg_color="#1C1C1C")

            self._bind_card_interactive(
                card,
                on_click=lambda h=col_hex, cd=card: self._copy_to_clipboard(h, cd),
                on_enter=on_skin_enter,
                on_leave=on_skin_leave
            )

        # Update smooth micro progress bar
        rendered_count = self._palette_total_count - len(self._palette_render_queue)
        progress_val = rendered_count / max(1, self._palette_total_count)
        if hasattr(self, "skin_palette_progress") and self.skin_palette_progress:
            self.skin_palette_progress.set(progress_val)

        if self._palette_render_queue:
            self._batch_after_id = self.container.after(10, self._render_palette_batch)
        else:
            self._batch_after_id = None
            if hasattr(self, "skin_palette_progress") and self.skin_palette_progress:
                self.container.after(200, self.skin_palette_progress.pack_forget)

    def _on_hand_shape_changed(self, shape_name):
        self.selected_hand_name = shape_name
        self._reload_detected_colors_for_current_shape()

    def _reload_detected_colors_for_current_shape(self):
        """Extracts unique fill colors dynamically from the selected hand SVG and creates clickable color swatches."""
        chid = HAND_SHAPE_MAP.get(self.selected_hand_name, "2807")
        svg_file = self.hand_shapes_dir / f"{chid}.svg"

        self.detected_colors = []
        if svg_file.exists():
            try:
                content = svg_file.read_text(encoding="utf-8")
                matches = re.findall(r'fill="(#[a-fA-F0-9]{6})"', content)
                seen = set()
                for c in matches:
                    c_up = c.upper()
                    if c_up not in seen:
                        seen.add(c_up)
                        self.detected_colors.append(c_up)
            except Exception as e:
                print(f"[HandModdingTool] Error reading SVG colors: {e}")

        # Update color mapping defaults
        new_map = {}
        for c in self.detected_colors:
            new_map[c] = self.color_map.get(c, c)
        self.color_map = new_map

        self._render_color_boxes()
        self._update_svg_preview()

    def _render_color_boxes(self):
        if not self.color_boxes_frame:
            return

        for widget in self.color_boxes_frame.winfo_children():
            widget.destroy()

        if not self.detected_colors:
            ctk.CTkLabel(
                self.color_boxes_frame, text="No vector fill colors detected in shape.",
                font=ctk.CTkFont(size=11), text_color="#777777"
            ).pack(pady=10)
            return

        # Rectangular swatches container - Flowing grid without labels
        swatches_container = ctk.CTkFrame(self.color_boxes_frame, fg_color="transparent")
        swatches_container.pack(fill="both", expand=True, padx=6, pady=6)

        cols_count = max(2, min(4, len(self.detected_colors)))
        for c_idx in range(cols_count):
            swatches_container.grid_columnconfigure(c_idx, weight=1)

        for idx, orig_hex in enumerate(self.detected_colors):
            current_hex = self.color_map.get(orig_hex, orig_hex)
            r, c = divmod(idx, cols_count)

            card = self._draw_rect_split_card(swatches_container, orig_hex, current_hex, width=44, height=34)
            card.grid(row=r, column=c, padx=4, pady=4)

            # Hover highlight
            def on_card_enter(cd=card):
                if cd.winfo_exists():
                    cd.configure(border_color="#00C853", border_width=2)

            def on_card_leave(cd=card):
                if cd.winfo_exists():
                    cd.configure(border_color="#444444", border_width=1)

            self._bind_card_interactive(
                card,
                on_click=lambda orig=orig_hex: self._pick_color_for(orig),
                on_enter=on_card_enter,
                on_leave=on_card_leave
            )

            # Tooltip
            if BMTToolTip:
                try:
                    BMTToolTip(card, message=f"Top: Original ({orig_hex})\nBottom: Custom ({current_hex})\n(Click to customize)")
                except Exception:
                    pass

    def _pick_color_for(self, orig_hex):
        current_hex = self.color_map.get(orig_hex, orig_hex)
        chosen = ask_color(self.container, initial_hex=current_hex)
        if chosen:
            self.color_map[orig_hex] = chosen.upper()
            self._render_color_boxes()
            self._update_svg_preview()

    def _reset_colors(self):
        for c in self.detected_colors:
            self.color_map[c] = c
        self._render_color_boxes()
        self._update_svg_preview()

    def _update_svg_preview(self):
        """Renders the SVG preview with custom colors at non-distorted 2/3 size."""
        chid = HAND_SHAPE_MAP.get(self.selected_hand_name, "2807")
        svg_file = self.hand_shapes_dir / f"{chid}.svg"

        if not svg_file.exists():
            if self.svg_preview_label:
                self.svg_preview_label.configure(text=f"SVG shape {chid}.svg not found", image=None)
            return

        try:
            svg_text = svg_file.read_text(encoding="utf-8")

            # Parse original SVG dimensions
            svg_w, svg_h = 59.4, 37.4
            w_match = re.search(r'width="([\d.]+)px"', svg_text)
            h_match = re.search(r'height="([\d.]+)px"', svg_text)
            if w_match and h_match:
                svg_w = float(w_match.group(1))
                svg_h = float(h_match.group(1))

            target_h = 110
            target_w = int(target_h * (svg_w / svg_h)) if svg_h > 0 else 160

            # Replace fill colors
            for default_hex, custom_hex in self.color_map.items():
                if default_hex.lower() != custom_hex.lower():
                    svg_text = re.sub(
                        re.escape(f'fill="{default_hex}"'),
                        f'fill="{custom_hex}"',
                        svg_text,
                        flags=re.IGNORECASE
                    )

            pil_img = render_svg(svg_text, (target_w, target_h))
            if pil_img:
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(target_w, target_h))
                if self.svg_preview_label:
                    self.svg_preview_label.configure(image=ctk_img, text="")
        except Exception as e:
            print(f"[HandModdingTool] Error rendering SVG preview: {e}")
            if self.svg_preview_label:
                self.svg_preview_label.configure(text=f"Error loading preview: {e}", image=None)

    # -----------------------------------------------------------------
    # EXPORT & AS3 CODE GENERATION
    # -----------------------------------------------------------------
    def _get_items_to_export(self):
        """Returns the list of modification dicts to export (from Hand Studio or current active editor)."""
        if self.studio_modifications:
            return list(self.studio_modifications)

        costume_name = self.costume_entry.get().strip()
        if not costume_name:
            return []

        return [{
            "skin_label": self.skin_menu.get(),
            "costume_name": costume_name,
            "hand_name": self.selected_hand_name,
            "color_map": dict(self.color_map)
        }]

    def _resolve_best_costume_name(self, c_name: str) -> str:
        """
        Resolves the single best matching costume code in the game files/registry.
        Checks from the full name and camelCase suffixes from longest to shortest,
        picking the longest/best match that exists in known game skins.
        """
        if not c_name:
            return c_name

        known_codes = set()
        if hasattr(self, 'all_skins') and self.all_skins:
            for item in self.all_skins:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    known_codes.add(item[1])
                elif isinstance(item, str):
                    known_codes.add(item)

        # Candidates from longest to shortest
        candidates = [c_name]
        for i in range(1, len(c_name)):
            if c_name[i].isupper():
                suffix = c_name[i:]
                if len(suffix) >= 3 and suffix not in candidates:
                    candidates.append(suffix)

        if known_codes:
            for cand in candidates:
                if cand in known_codes:
                    return cand

        return c_name

    def _build_multi_obf_as3_code(self, items: list) -> str:
        """Generates Obf.as ActionScript containing handMap and colorMap dictionary mappings for ALL items in items list using plaintext strings."""
        init_lines = []
        first_costume_name = self._resolve_best_costume_name(items[0]["costume_name"])
        first_hand_name = items[0]["hand_name"]

        for it in items:
            c_name = self._resolve_best_costume_name(it["costume_name"])
            h_name = it["hand_name"]
            init_lines.append(f'         handMap["{c_name}"] = "{h_name}";')

        for it in items:
            c_name = self._resolve_best_costume_name(it["costume_name"])
            c_map = it.get("color_map", {})
            if c_map:
                entries = []
                for orig_hex, custom_hex in c_map.items():
                    src_val = f"0x{orig_hex.lstrip('#')}"
                    dst_val = f"0x{custom_hex.lstrip('#')}"
                    entries.append(f"{{src: {src_val}, dst: {dst_val}}}")
                if entries:
                    init_lines.append(f'         colorMap["{c_name}"] = [{", ".join(entries)}];')

        init_map_code = "\n".join(init_lines)

        first_c_arr, first_c_key = obf_string(first_costume_name, 15)
        first_h_arr, first_h_key = obf_string(first_hand_name, 20)

        # Build 25 entries for families array using the first hand model
        fam_arr, fam_key = obf_string(first_hand_name, 35)
        fam_entry = f"Obf.d({fam_arr},{fam_key})"
        families_code = "[" + ",".join([fam_entry] * 25) + "]"

        return f"""package tier_b
{{
   public class Obf
   {{
      public static var AB:String = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.";

      public static var handMap:Object = {{}};
      public static var colorMap:Object = {{}};
      public static var paletteMap:Object = {{}};

      public function Obf()
      {{
      }}

      public static function initHandMap() : void
      {{
         handMap = {{}};
         colorMap = {{}};
{init_map_code}
      }}

      public static function initPalettes() : void
      {{
         paletteMap = {{}};
      }}

      public static function getHandForCostume(costumeName:String) : String
      {{
         if(costumeName == null || handMap == null)
         {{
            return null;
         }}
         if(handMap[costumeName] != null)
         {{
            return handMap[costumeName] as String;
         }}
         return null;
      }}

      public static function getColorSwapsForCostume(costumeName:String) : Array
      {{
         if(costumeName == null)
         {{
            return null;
         }}
         if(colorMap == null)
         {{
            initHandMap();
         }}
         
         // 1. Direct match
         if(colorMap[costumeName] != null)
         {{
            return colorMap[costumeName] as Array;
         }}
         
         // 2. Search configured keys camel suffixes
         for (var k:String in colorMap)
         {{
            var keySuffixes:Array = getCamelSuffixes(k);
            var ki:int = 0;
            var klen:int = keySuffixes.length;
            while(ki < klen)
            {{
               var ks:String = keySuffixes[ki++];
               if(ks == costumeName)
               {{
                  return colorMap[k] as Array;
               }}
            }}
         }}
         
         // 3. Search costumeName camel suffixes
         var costSuffixes:Array = getCamelSuffixes(costumeName);
         var ci:int = 0;
         var clen:int = costSuffixes.length;
         while(ci < clen)
         {{
            var cs:String = costSuffixes[ci++];
            if(colorMap[cs] != null)
            {{
               return colorMap[cs] as Array;
            }}
         }}
         
         return null;
      }}

      public static function d(param1:Array, param2:int) : String
      {{
         var _loc6_:int = 0;
         var _loc7_:int = 0;
         var _loc3_:String = "";
         var _loc4_:int = 0;
         var _loc5_:int = int(param1.length);
         while(_loc4_ < _loc5_)
         {{
            _loc6_ = _loc4_++;
            _loc7_ = int((int(param1[_loc6_]) - param2 - _loc6_ * 7) % 65);
            if(_loc7_ < 0)
            {{
               _loc7_ += 65;
            }}
            _loc3_ += "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.".charAt(_loc7_);
         }}
         return _loc3_;
      }}

      public static function targetCostume() : String
      {{
         return Obf.d({first_c_arr},{first_c_key});
      }}

      public static function handFile() : String
      {{
         return Obf.d([35,15,40,21,64,38,58,55,12,0,26,37,27],3);
      }}

      public static function swapSuffix() : String
      {{
         return Obf.d({first_h_arr},{first_h_key});
      }}

      public static function gcField() : String
      {{
         return Obf.d([53,61,0,0,15],56);
      }}

      public static function families() : Array
      {{
         return {families_code};
      }}

      public static function paletteChannels() : Array
      {{
         return [Obf.d([34,8,23,39,1,55],1),Obf.d([28,2,17,33],60),Obf.d([39,13,28,44,63,51],6),Obf.d([25,19,15,43,14,15,12],63),Obf.d([16,10,6,34,5,61,50],54),Obf.d([55,49,45,8,44],28),Obf.d([21,15,11,39,10,58,46],59),Obf.d([21,15,11,39,10,11,0],59),Obf.d([51,45,41,4,40,20,3,10],24),Obf.d([17,11,7,35,7,7,4],55),Obf.d([8,2,63,26,63,53,42],46),Obf.d([62,56,52,15,52],35),Obf.d([13,7,3,31,3,50,38],51),Obf.d([13,7,3,31,3,3,57],51),Obf.d([13,7,3,31,3,47,30,37],51),Obf.d([17,60,56,61,9,8,26,4,1],38),Obf.d([8,51,47,52,0,64,17,50,39],29),Obf.d([17,60,56,61,9,8,26],38),Obf.d([13,56,52,57,5,4,22,47,35],34),Obf.d([13,56,52,57,5,4,22,0,54],34),Obf.d([38,16,12,17,30,29,47,4,52,59],59),Obf.d([48,38,48,60,55,37,34],20),Obf.d([39,29,39,51,46,18,7],11),Obf.d([18,8,18,30,25],55),Obf.d([44,34,44,56,51,15,3],16),Obf.d([34,62,0,22,28,34,10,7],51),Obf.d([25,53,56,13,19,25,56,45],42),Obf.d([54,17,20,42,48,54],6),Obf.d([30,58,61,18,24,30,53,41],47),Obf.d([14,42,45,2,8,14,34,17,24],31)];
      }}
   }}
}}"""

    def export_hand_mod(self):
        """Exports UI_MainMenu_HandMod.swf carrier with all queued Hand Studio modifications."""
        items = self._get_items_to_export()
        if not items:
            messagebox.showwarning("No Modifications to Export", "Please add at least one skin modification to Hand Studio.")
            return

        carrier_file = self.carrier_path or self._detect_internal_carrier()
        if not carrier_file or not os.path.exists(carrier_file):
            messagebox.showerror("Carrier File Not Found", "Internal UI_MainMenu.swf carrier asset could not be located.")
            return

        dest_folder = filedialog.askdirectory(title="Select Destination Folder for UI_MainMenu_HandMod.swf")
        if not dest_folder:
            return

        out_swf_path = os.path.join(dest_folder, "UI_MainMenu_HandMod.swf")

        try:
            if self.status_label:
                self.status_label.configure(text=f"Patching SWF with {len(items)} modification(s)...", text_color="#FFB300")

            obf_as3 = self._build_multi_obf_as3_code(items)
            self._patch_carrier_swf_direct(carrier_file, out_swf_path, obf_as3, items=items)

            if self.status_label:
                self.status_label.configure(text=f"Exported successfully with {len(items)} modification(s)!", text_color="#4CAF50")

            summary_lines = "\n".join([f"  * {it['skin_label']} -> {it['hand_name']}" for it in items])
            messagebox.showinfo(
                "Export Complete!",
                f"Hand Mod UI_MainMenu_HandMod.swf successfully created!\n\n"
                f"Total Modifications Exported: {len(items)}\n"
                f"{summary_lines}\n\n"
                f"Output File:\n{out_swf_path}\n\n"
                f"Usage: Rename to UI_MainMenu.swf or install via Brawlhalla Mod Loader!"
            )
        except Exception as e:
            print(f"[HandModdingTool] Error during export: {e}")
            import traceback
            traceback.print_exc()
            if self.status_label:
                self.status_label.configure(text=f"Export failed: {e}", text_color="#F44336")
            messagebox.showerror("Export Error", f"Could not export UI_MainMenu_HandMod.swf:\n{e}")

    def export_mod_creator_source(self):
        """Exports the full Mod Creator Source folder structure with all queued Hand Studio modifications."""
        items = self._get_items_to_export()
        if not items:
            messagebox.showwarning("No Modifications to Export", "Please add at least one skin modification to Hand Studio.")
            return

        dest_folder = filedialog.askdirectory(title="Select Destination Mod Source Folder")
        if not dest_folder:
            return

        try:
            if self.status_label:
                self.status_label.configure(text=f"Generating Mod Creator Source with {len(items)} modification(s)...", text_color="#FFB300")

            obf_as3 = self._build_multi_obf_as3_code(items)

            scripts_root = Path(dest_folder) / "UI_MainMenu.swf" / "scripts"
            tier_b_dir = scripts_root / "tier_b"
            os.makedirs(tier_b_dir, exist_ok=True)

            template_dir = Path(__file__).parent.parent / "utils" / "carriers" / "hand_scripts_template"

            # 1. a_ScreenMainMenu2.as
            screen_src = template_dir / "a_ScreenMainMenu2.as"
            if screen_src.exists():
                shutil.copy2(str(screen_src), str(scripts_root / "a_ScreenMainMenu2.as"))
            else:
                (scripts_root / "a_ScreenMainMenu2.as").write_text(
                    'package\n{\n   import flash.display.MovieClip;\n   import tier_b.BrawlForgeSuiteBootstrap;\n   \n   [Embed(source="/_assets/assets.swf", symbol="a_ScreenMainMenu2")]\n   public dynamic class a_ScreenMainMenu2 extends MovieClip\n   {\n      public function a_ScreenMainMenu2()\n      {\n         super();\n         BrawlForgeSuiteBootstrap.attach(this);\n      }\n   }\n}\n',
                    encoding="utf-8"
                )

            # 2. BrawlForgeSuite.as
            bfs_src = template_dir / "BrawlForgeSuite.as"
            if bfs_src.exists():
                shutil.copy2(str(bfs_src), str(tier_b_dir / "BrawlForgeSuite.as"))

            # 3. BrawlForgeSuiteBootstrap.as
            bfsb_src = template_dir / "BrawlForgeSuiteBootstrap.as"
            if bfsb_src.exists():
                shutil.copy2(str(bfsb_src), str(tier_b_dir / "BrawlForgeSuiteBootstrap.as"))

            # 4. Obf.as with all getHandForCostume mappings
            (tier_b_dir / "Obf.as").write_text(obf_as3, encoding="utf-8")

            # 5. Generate and write cryptographic BMT Certificate
            try:
                import json
                from src.utils.security_scanner import generate_bmt_certificate
                cert_data = generate_bmt_certificate("HandModTool", "HandMod_Custom", Path(dest_folder))
                (Path(dest_folder) / ".bmt_cert.json").write_text(json.dumps(cert_data, indent=2), encoding="utf-8")
            except Exception as ce:
                print(f"[HandModdingTool] Warning: Could not write certificate: {ce}")

            if self.status_label:
                self.status_label.configure(text=f"Mod Source exported to {dest_folder}!", text_color="#4CAF50")

            summary_lines = "\n".join([f"  * {it['skin_label']} -> {it['hand_name']}" for it in items])
            messagebox.showinfo(
                "Mod Source Export Complete!",
                f"Mod Creator Source successfully created!\n\n"
                f"Total Modifications Exported: {len(items)}\n"
                f"BMT Security Certification: Embedded\n"
                f"{summary_lines}\n\n"
                f"Folder:\n{dest_folder}\n\n"
                f"Next Step: Open 'Brawlhalla Mod Creator', load this folder as your Mod Source, and compile it to .bmod!"
            )
        except Exception as e:
            print(f"[HandModdingTool] Error exporting mod source: {e}")
            import traceback
            traceback.print_exc()
            if self.status_label:
                self.status_label.configure(text=f"Export failed: {e}", text_color="#F44336")
            messagebox.showerror("Export Error", f"Could not export Mod Creator Source:\n{e}")

    def _patch_carrier_swf_direct(self, carrier_path, out_swf_path, obf_as3, items=None):
        """Patches Obf and BrawlForgeSuite in UI_MainMenu.swf carrier using clean AS3 replacement."""
        if Methods is None:
            raise RuntimeError("Methods module not available.")

        Methods._init_ffdec()
        import jpype
        try:
            if not jpype.isThreadAttachedToJVM():
                jpype.attachThreadToJVM()
        except Exception:
            pass
        As3ScriptReplacerFactory = jpype.JClass("com.jpexs.decompiler.flash.importers.As3ScriptReplacerFactory")
        scriptReplacer = As3ScriptReplacerFactory.createByConfig(True)

        swf = Methods.get_swf(str(carrier_path), "")
        if not swf:
            raise RuntimeError("Could not load SWF carrier with FFDEC.")

        # Read latest BrawlForgeSuite.as template
        template_as3_path = Path(__file__).parent.parent / "utils" / "carriers" / "hand_scripts_template" / "BrawlForgeSuite.as"
        suite_as3 = ""
        if template_as3_path.exists():
            with open(template_as3_path, "r", encoding="utf-8") as f:
                suite_as3 = f.read()

        # Replace Obf and BrawlForgeSuite in SWF AS3 packs
        for pack in swf.getAS3Packs():
            path = str(pack.getPath()) if hasattr(pack, "getPath") else str(pack)
            if "Obf" in path:
                try:
                    pack.abc.replaceScriptPack(scriptReplacer, pack, obf_as3, None)
                    print("[HandModdingTool] Replaced Obf script.")
                except Exception as e:
                    print(f"[HandModdingTool] Error replacing Obf script: {e}")
            elif "BrawlForgeSuite" in path and "Bootstrap" not in path:
                if suite_as3:
                    try:
                        pack.abc.replaceScriptPack(scriptReplacer, pack, suite_as3, None)
                        print("[HandModdingTool] Replaced BrawlForgeSuite script.")
                    except Exception as e:
                        print(f"[HandModdingTool] Error replacing BrawlForgeSuite script: {e}")

        out_path = Path(out_swf_path).resolve()
        os.makedirs(out_path.parent, exist_ok=True)

        Methods.save_swf_to(swf, str(out_path))
        print(f"[HandModdingTool] SWF Carrier successfully written to {out_path}")
