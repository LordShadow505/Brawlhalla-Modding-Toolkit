"""
ColorModToolModule.py - Brawlhalla Modding Toolkit (BMT)
Color Mod Tool: compact left color picker, centered 6x6 perfect square swatch grid,
enlarged live Bodvar preview, and clean mod exporter.
"""

import os
import re
import sys
import shutil
import colorsys
import math
import tkinter as tk
import xml.etree.ElementTree as ET
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk
import json
import threading
import urllib.request
from pathlib import Path

# Local imports
from .ToolModuleBase import ToolModule
from src.utils.ThemeManager import BMTTheme, ACCENTS, BMTToolTip
from src.svg_utils import render_svg

# LIB path for Methods, SwzReader & BrawlhallaLangReader
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
            lang_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(lang_mod)
            BrawlhallaLangReader = getattr(lang_mod, "BrawlhallaLangReader", None)
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
    print(f"[ColorModTool] Error loading Lib modules: {e}")

# =========================================================================
# COLOR SCHEME CONSTANTS
# =========================================================================

SHADE_COLUMNS = ["Very Light", "Light", "Base", "Dark", "Very Dark", "Accent"]
SHADE_KEYS = ["VL", "Lt", "", "Dk", "VD", "Acc"]

# 6x6 Matrix layout: Row Name -> [VL (col 0), Lt (col 1), Base (col 2), Dk (col 3), VD (col 4), Acc (col 5)]
MATRIX_ROWS = [
    ("Hair",    [None, "HairLt", "Hair", "HairDk", None, None]),
    ("Body 1",  ["Body1VL", "Body1Lt", "Body1", "Body1Dk", "Body1VD", "Body1Acc"]),
    ("Body 2",  ["Body2VL", "Body2Lt", "Body2", "Body2Dk", "Body2VD", "Body2Acc"]),
    ("Special", ["SpecialVL", "SpecialLt", "Special", "SpecialDk", "SpecialVD", "SpecialAcc"]),
    ("Cloth",   ["ClothVL", "ClothLt", "Cloth", "ClothDk", None, None]),
    ("Weapon",  ["WeaponVL", "WeaponLt", "Weapon", "WeaponDk", None, "WeaponAcc"]),
]

ALL_CHANNELS_LIST = [
    "HairLt", "Hair", "HairDk",
    "Body1VL", "Body1Lt", "Body1", "Body1Dk", "Body1VD", "Body1Acc",
    "Body2VL", "Body2Lt", "Body2", "Body2Dk", "Body2VD", "Body2Acc",
    "SpecialVL", "SpecialLt", "Special", "SpecialDk", "SpecialVD", "SpecialAcc",
    "ClothVL", "ClothLt", "Cloth", "ClothDk",
    "WeaponVL", "WeaponLt", "Weapon", "WeaponDk", "WeaponAcc"
]

# Bodvar Classic default palette (Scheme ID 0)
BODVAR_CLASSIC_PALETTE = {
    "HairLt": "#FFFFCC", "Hair": "#ECF185", "HairDk": "#9CA75F",
    "Body1VL": "#C6FFEF", "Body1Lt": "#84CE6F", "Body1": "#3F985B", "Body1Dk": "#2D4A44", "Body1VD": "#2D4A44", "Body1Acc": "#EB9947",
    "Body2VL": "#C6FFEF", "Body2Lt": "#84CE6F", "Body2": "#477860", "Body2Dk": "#2D4A44", "Body2VD": "#2D4A44", "Body2Acc": "#EB9947",
    "SpecialVL": "#FDFDF2", "SpecialLt": "#C6FFEF", "Special": "#20FFC1", "SpecialDk": "#00B98F", "SpecialVD": "#00B98F", "SpecialAcc": "#FCD652",
    "ClothVL": "#FDFDF2", "ClothLt": "#FFFFCC", "Cloth": "#B7C168", "ClothDk": "#68654F",
    "WeaponVL": "#FDFDF2", "WeaponLt": "#BFFFFC", "Weapon": "#54ABEB", "WeaponDk": "#2F3068", "WeaponAcc": "#EB9947"
}

# Fallback Black scheme
DEFAULT_BLACK_PALETTE = {
    "HairLt": "#38373E", "Hair": "#2C2B31", "HairDk": "#151518",
    "Body1VL": "#9C9B9F", "Body1Lt": "#4C525A", "Body1": "#2C2B31", "Body1Dk": "#151518", "Body1VD": "#151518", "Body1Acc": "#38373E",
    "Body2VL": "#4C525A", "Body2Lt": "#2C2B31", "Body2": "#222126", "Body2Dk": "#151518", "Body2VD": "#0D0D10", "Body2Acc": "#151518",
    "SpecialVL": "#C71C2E", "SpecialLt": "#991523", "Special": "#6B0F19", "SpecialDk": "#460910", "SpecialVD": "#460910", "SpecialAcc": "#6B0F19",
    "ClothVL": "#9C9B9F", "ClothLt": "#4C525A", "Cloth": "#2C2B31", "ClothDk": "#151518",
    "WeaponVL": "#9C9B9F", "WeaponLt": "#4C525A", "Weapon": "#2C2B31", "WeaponDk": "#151518", "WeaponAcc": "#4C525A"
}

# Bodvar SVG locked static colors (never changed in preview: horns, buckle, details, etc.)
BODVAR_LOCKED_SVG_COLORS = {
    "#68654F", "#353428", "#EB9947", "#FCD652", "#FFFADD"
}

DEFAULT_COSTUME_DISPLAY_NAMES = {
    "Airship": "Airship Scarlet",
    "BP11Azoth03": "Ascendant Azoth",
    "BP5GalaxyBeast": "Leonidas Onyx",
    "BP5Orion": "Orion Prime",
    "BPZariel": "Archfiend Zariel",
    "CyberSam": "Shin Sekai Koji",
    "Default": "Classic DEFAULT_CHARACTER",
    "DemonQueen": "Akuma no Kogo Hattori",
    "DianaEpic": "Soulbound Diana",
    "EpicBrynn": "Aurora Brynn",
    "EpicEmber": "Fangwild's Heart Ember",
    "EpicNinetails": "Inari Yumiko",
    "EpicRagnir": "Ragnir, King of Darkness",
    "EpicRaptor": "Raptor, the Betrayer",
    "Fenrir": "Fenrir Mordex",
    "MonsterBat": "Werebeast Rupture",
    "MythicNix": "Ascended Nix",
    "MythicWerewolf": "Ascended Mordex",
    "MythicWuShang": "Ascended Wu Shang",
    "PaleRider": "Apocalypse Mirage",
    "Seraph": "Seraph Artemis",
    "ShinobiBP1203": "Shinobi no Mono Jiro",
    "Viking": "Classic Bödvar",
}

DEFAULT_COSTUME_DEFINES = {
    "Airship": {
        "#C01D39": "HairLt",
        "#97172E": "Hair",
        "#5F0E2D": "HairDk",
        "#2D8EA0": "Body1Lt",
        "#1A616E": "Body1",
        "#0F3A4A": "Body1Dk",
        "#324D58": "Body2",
        "#172328": "Body2Dk",
        "#060A0B": "Body2VD",
        "#F4F1E5": "SpecialVL",
        "#D9D5B9": "SpecialLt",
        "#F11F1F": "Special",
        "#76716B": "ClothLt",
        "#403E3B": "Cloth",
        "#262524": "ClothDk",
        "#FFF4DD": "WeaponVL",
        "#FDD276": "WeaponLt",
        "#AC9156": "Weapon",
        "#847548": "WeaponDk",
    },
    "BP11Azoth03": {
        "#535159": "Body1Lt",
        "#33333D": "Body1",
        "#1E1E26": "Body1Dk",
        "#141419": "Body1VD",
        "#2B2B33": "Body1Acc",
        "#2F2E45": "Body2Dk",
        "#181828": "Body2VD",
        "#00FFFF": "SpecialVL",
        "#FF0099": "SpecialLt",
        "#0D10E8": "Special",
        "#000066": "SpecialDk",
        "#000042": "SpecialVD",
        "#5024F9": "SpecialAcc",
        "#EDE1CE": "Cloth",
        "#8C8281": "ClothDk",
        "#BA865E": "WeaponLt",
        "#362D24": "Weapon",
        "#221C10": "WeaponDk",
        "#4B3528": "WeaponAcc",
    },
    "BP5GalaxyBeast": {
        "#656A82": "Body1Lt",
        "#434661": "Body1",
        "#2C2F43": "Body1Dk",
        "#1A1A2C": "Body1VD",
        "#C7C8FD": "Body2Lt",
        "#7E80FF": "Body2",
        "#363777": "Body2Dk",
        "#121421": "Body2VD",
        "#493C7D": "Body2Acc",
        "#FFFEDD": "SpecialLt",
        "#FFE88C": "Special",
        "#DFB027": "SpecialVD",
        "#FFF2AC": "WeaponLt",
        "#D0B360": "Weapon",
        "#A27B2B": "WeaponDk",
        "#A08982": "WeaponAcc",
    },
    "BP5Orion": {
        "#FEFFED": "Body1VL",
        "#FFFC96": "Body1Lt",
        "#B19A67": "Body1",
        "#5B5D43": "Body1Dk",
        "#3A3A29": "Body1VD",
        "#787047": "Body1Acc",
        "#45483A": "Body2",
        "#2E2F25": "Body2Dk",
        "#151611": "Body2VD",
        "#AFFFC9": "SpecialLt",
        "#36F9D4": "Special",
        "#45F1F8": "SpecialDk",
        "#50BDFD": "SpecialVD",
        "#001BA1": "SpecialAcc",
    },
    "BPZariel": {
        "#E8E6D9": "HairLt",
        "#C3B7A7": "Hair",
        "#643B7F": "Body1Lt",
        "#38246B": "Body1",
        "#39033D": "Body1Dk",
        "#1E0235": "Body1VD",
        "#7F9EBB": "Body2",
        "#5D5797": "Body2Dk",
        "#FDFDD7": "SpecialLt",
        "#F9D46A": "Special",
        "#E59B46": "SpecialDk",
        "#FFFBD6": "Cloth",
        "#F6D36F": "ClothDk",
        "#FFFCE3": "WeaponLt",
        "#DDC996": "Weapon",
        "#B58A84": "WeaponDk",
        "#DEAA92": "WeaponAcc",
    },
    "CyberSam": {
        "#E2DEDD": "Body1VL",
        "#BAB6B5": "Body1Lt",
        "#7F7B7A": "Body1",
        "#5D5958": "Body1Dk",
        "#3D3C3A": "Body1VD",
        "#896068": "Body1Acc",
        "#7C8E90": "Body2VL",
        "#566666": "Body2Lt",
        "#343F43": "Body2",
        "#101B1F": "Body2Dk",
        "#000405": "Body2VD",
        "#3D2D38": "Body2Acc",
        "#FEFDF8": "SpecialVL",
        "#FFEEE4": "SpecialLt",
        "#FDCAD1": "Special",
        "#FF1E72": "SpecialDk",
        "#AA0C60": "SpecialVD",
        "#F9D4B9": "WeaponVL",
        "#B99585": "WeaponLt",
        "#785849": "Weapon",
        "#3F3A37": "WeaponDk",
    },
    "Default": {},
    "DemonQueen": {
        "#584F4A": "HairLt",
        "#332E2B": "Hair",
        "#24201E": "HairDk",
        "#A2356F": "Body1Lt",
        "#791D36": "Body1",
        "#4C0B21": "Body1Dk",
        "#302841": "Body2",
        "#0B0A10": "Body2Dk",
        "#EFFFDB": "SpecialVL",
        "#D6FFBB": "SpecialLt",
        "#ABFED2": "Special",
        "#83FFE5": "SpecialDk",
        "#37DFE0": "SpecialVD",
        "#F9FFFF": "ClothLt",
        "#CFC7F0": "Cloth",
        "#B39CD0": "ClothDk",
        "#FCDDA7": "WeaponLt",
        "#A08B8A": "Weapon",
        "#67527D": "WeaponDk",
        "#7F6885": "WeaponAcc",
    },
    "DianaEpic": {
        "#FDFDFD": "Body1VL",
        "#E5ECF5": "Body1",
        "#BAC1D6": "Body1Dk",
        "#868CB6": "Body1VD",
        "#80848E": "Body2VL",
        "#52545E": "Body2Lt",
        "#34323C": "Body2",
        "#14121C": "Body2Dk",
        "#040107": "Body2VD",
        "#FDFFD7": "SpecialLt",
        "#D3FFFD": "Special",
        "#85C4E2": "SpecialDk",
        "#FCF9F4": "Cloth",
        "#DED8D2": "ClothDk",
        "#DED6BF": "WeaponLt",
        "#B1A08A": "Weapon",
        "#937C6D": "WeaponDk",
    },
    "EpicBrynn": {
        "#FAE987": "HairLt",
        "#ECAB43": "Hair",
        "#C567D7": "HairDk",
        "#FFFDD4": "Body1Lt",
        "#E6C47C": "Body1",
        "#A77D6F": "Body1Dk",
        "#CA9778": "Body1Acc",
        "#2E3A43": "Body2",
        "#161220": "Body2Dk",
        "#E6FFAB": "SpecialVL",
        "#88F19D": "SpecialLt",
        "#00BDD3": "Special",
        "#4B87E9": "SpecialDk",
        "#5B5FF4": "SpecialVD",
        "#FBFDF2": "Cloth",
        "#BDBCA8": "ClothDk",
        "#F0FFE2": "WeaponVL",
        "#B4E1E6": "WeaponLt",
        "#8AADCD": "Weapon",
        "#7C7EB9": "WeaponDk",
        "#BC83CA": "WeaponAcc",
    },
    "EpicEmber": {
        "#C2BAAD": "HairLt",
        "#A99E8C": "Hair",
        "#746760": "HairDk",
        "#685C3D": "Body1Lt",
        "#47402B": "Body1",
        "#19140D": "Body1Dk",
        "#B8C26A": "Body2Lt",
        "#8FAC62": "Body2",
        "#727159": "Body2Dk",
        "#4C4E3E": "Body2VD",
        "#FFFEF4": "SpecialLt",
        "#FFF4C8": "Special",
        "#EBC16F": "SpecialVD",
        "#E3DED8": "Cloth",
        "#AEAD9C": "ClothDk",
        "#F2EABC": "WeaponLt",
        "#C7B488": "Weapon",
        "#AC8C6C": "WeaponDk",
        "#D4B581": "WeaponAcc",
    },
    "EpicNinetails": {
        "#FEFEFE": "HairLt",
        "#F7FAF1": "Hair",
        "#BDCABE": "HairDk",
        "#FFFFFF": "Body1",
        "#E3EDFF": "Body1Dk",
        "#BCCDFF": "Body1VD",
        "#BDF6FF": "Body1Acc",
        "#6976D9": "Body2Lt",
        "#51499D": "Body2",
        "#38335A": "Body2Dk",
        "#191823": "Body2VD",
        "#FFFBC4": "SpecialLt",
        "#5FFFF8": "Special",
        "#B390FF": "SpecialDk",
        "#6D35E6": "SpecialVD",
        "#D5FFCD": "ClothLt",
        "#96FFEB": "Cloth",
        "#A3C0FF": "ClothDk",
        "#F9EABF": "WeaponLt",
        "#E6C88A": "Weapon",
        "#BB9171": "WeaponDk",
        "#B1BDB2": "WeaponAcc",
    },
    "EpicRagnir": {
        "#434451": "Body1Lt",
        "#292B32": "Body1",
        "#191B22": "Body1Dk",
        "#0C0D11": "Body1VD",
        "#657EC2": "Body2VL",
        "#3F4D6F": "Body2Lt",
        "#2B3755": "Body2",
        "#94FACD": "SpecialVL",
        "#38D2FD": "SpecialLt",
        "#3E9AD6": "Special",
        "#5375E9": "SpecialDk",
        "#1C3FD8": "SpecialVD",
        "#B8B3CF": "ClothVL",
        "#938DAF": "ClothLt",
        "#948F9C": "Cloth",
        "#777480": "ClothDk",
    },
    "EpicRaptor": {
        "#B05529": "Body1Lt",
        "#621B0E": "Body1",
        "#400804": "Body1Dk",
        "#45211D": "Body2",
        "#290F0D": "Body2Dk",
        "#F7CEBE": "SpecialVL",
        "#F7867D": "SpecialLt",
        "#F74129": "Special",
        "#150200": "SpecialVD",
        "#5B2E2A": "ClothVL",
        "#301614": "ClothLt",
        "#402A28": "Cloth",
        "#221713": "ClothDk",
        "#C46763": "WeaponLt",
        "#63402F": "Weapon",
        "#3F2927": "WeaponDk",
        "#8B415B": "WeaponAcc",
    },
    "Fenrir": {
        "#919191": "Body1VL",
        "#5B5B5D": "Body1Lt",
        "#4A4B4D": "Body1",
        "#313131": "Body1Dk",
        "#141415": "Body1VD",
        "#6B898E": "Body1Acc",
        "#934231": "Body2",
        "#5F2215": "Body2Dk",
        "#F0FFFD": "SpecialVL",
        "#D3F5F0": "SpecialLt",
        "#61FFE9": "Special",
        "#FFF5D7": "WeaponLt",
        "#F3E3A5": "Weapon",
        "#BCA46B": "WeaponDk",
    },
    "MonsterBat": {
        "#9B703D": "HairLt",
        "#724F2A": "Hair",
        "#463A3C": "Body1Lt",
        "#2B2727": "Body1",
        "#1A1717": "Body1Dk",
        "#0F0C0C": "Body1VD",
        "#DB9493": "Body2Lt",
        "#B56766": "Body2",
        "#FB7439": "SpecialLt",
        "#F5110D": "Special",
        "#6E0C25": "SpecialDk",
        "#361C19": "SpecialVD",
        "#C24872": "SpecialAcc",
        "#C8B582": "ClothLt",
        "#7B6550": "Cloth",
        "#B6AEA8": "WeaponVL",
        "#77716A": "WeaponLt",
        "#4B4A42": "Weapon",
        "#35342D": "WeaponDk",
        "#70746B": "WeaponAcc",
    },
    "MythicNix": {
        "#9195F0": "Body1Lt",
        "#5E60AD": "Body1",
        "#37345F": "Body1Dk",
        "#1E1B38": "Body1VD",
        "#592F79": "Body1Acc",
        "#451C58": "Body2Lt",
        "#230E2D": "Body2",
        "#130719": "Body2Dk",
        "#E9CCFC": "SpecialVL",
        "#FE00EE": "SpecialLt",
        "#9824AB": "Special",
        "#600A75": "SpecialDk",
    },
    "MythicWerewolf": {
        "#3A555B": "Body1Lt",
        "#273B44": "Body1",
        "#1E2A35": "Body1Dk",
        "#0F1828": "Body1VD",
        "#EBFFE1": "SpecialVL",
        "#BBFFCF": "SpecialLt",
        "#6FABB1": "Special",
        "#324657": "SpecialDk",
        "#62899B": "ClothLt",
        "#324F68": "Cloth",
        "#1E283B": "ClothDk",
        "#FFEB96": "WeaponLt",
        "#DDC175": "Weapon",
        "#B98040": "WeaponDk",
        "#BACB94": "WeaponAcc",
    },
    "MythicWuShang": {
        "#756352": "Hair",
        "#4F453E": "HairDk",
        "#FEFFFA": "Body1VL",
        "#F4FBB8": "Body1Lt",
        "#FBC47F": "Body1",
        "#EA9157": "Body1Dk",
        "#B75B55": "Body1VD",
        "#8B6046": "Body2Lt",
        "#634236": "Body2",
        "#43302F": "Body2Dk",
        "#231C1F": "Body2VD",
        "#CFFFF7": "SpecialLt",
        "#9ADFE1": "Special",
        "#655A5B": "SpecialDk",
        "#40393A": "SpecialVD",
        "#F6F8EB": "Cloth",
        "#B0A688": "ClothDk",
        "#FAEDA3": "WeaponLt",
        "#D1AD4D": "Weapon",
        "#8D5D3C": "WeaponDk",
        "#A3976C": "WeaponAcc",
    },
    "PaleRider": {
        "#9D3437": "Body1",
        "#631A19": "Body1Dk",
        "#3F140F": "Body1VD",
        "#758D8A": "Body2",
        "#476162": "Body2Dk",
        "#55A6B2": "Body2VD",
        "#FDFFD5": "SpecialVL",
        "#BEFFD2": "SpecialLt",
        "#80FFD8": "Special",
        "#63E7E3": "SpecialDk",
        "#2A9ADB": "SpecialVD",
        "#DBDAC5": "Weapon",
        "#B4AC9D": "WeaponDk",
        "#B4CCCA": "WeaponAcc",
    },
    "Seraph": {
        "#FDFDFF": "Body1",
        "#EBEBF8": "Body1Dk",
        "#CAC8EB": "Body1VD",
        "#B4FDFF": "Body2VL",
        "#58CBFF": "Body2Lt",
        "#1E6FBB": "Body2",
        "#35358F": "Body2Dk",
        "#0B0433": "Body2VD",
        "#394ED6": "Body2Acc",
        "#FFC1B0": "SpecialLt",
        "#C2413B": "Special",
        "#7A2438": "SpecialDk",
        "#7A3DB5": "SpecialAcc",
        "#FFF7BA": "ClothLt",
        "#EFD35C": "Cloth",
        "#BA8B3B": "ClothDk",
    },
    "ShinobiBP1203": {
        "#0D1117": "HairDk",
        "#3E5357": "Body1VL",
        "#2B4142": "Body1Lt",
        "#252C35": "Body1",
        "#14222B": "Body1Dk",
        "#752834": "Body2VL",
        "#4B1C1B": "Body2Lt",
        "#32252A": "Body2",
        "#1C1618": "Body2Dk",
        "#FF8D7E": "SpecialVL",
        "#A5FFF4": "SpecialLt",
        "#30E0D1": "Special",
        "#3D798F": "SpecialDk",
        "#283F54": "SpecialVD",
        "#FF3300": "SpecialAcc",
        "#9BA7A6": "ClothLt",
        "#60686A": "Cloth",
        "#2D3439": "ClothDk",
        "#9B9BE8": "WeaponLt",
        "#7D86A2": "Weapon",
        "#475072": "WeaponDk",
    },
    "Viking": {
        "#ECF185": "Hair",
        "#9CA75F": "HairDk",
        "#84CE6F": "Body1Lt",
        "#3F985B": "Body1",
        "#477860": "Body2",
        "#2D4A44": "Body2Dk",
        "#C6FFEF": "SpecialLt",
        "#20FFC1": "Special",
        "#00B98F": "SpecialDk",
        "#FFFFCC": "ClothLt",
        "#B7C168": "Cloth",
        "#57BDB0": "Weapon",
        "#3A9489": "WeaponDk",
    },
}

DEFAULT_COSTUME_CLASSIC_PALETTES = {
    "Airship": {
        "HairLt": "#C01D39",
        "Hair": "#97172E",
        "HairDk": "#5F0E2D",
        "Body1Lt": "#2D8EA0",
        "Body1": "#1A616E",
        "Body1Dk": "#0F3A4A",
        "Body2": "#324D58",
        "Body2Dk": "#172328",
        "Body2VD": "#060A0B",
        "SpecialVL": "#F4F1E5",
        "SpecialLt": "#D9D5B9",
        "Special": "#F11F1F",
        "ClothLt": "#76716B",
        "Cloth": "#403E3B",
        "ClothDk": "#262524",
        "WeaponVL": "#FFF4DD",
        "WeaponLt": "#FDD276",
        "Weapon": "#AC9156",
        "WeaponDk": "#847548",
    },
    "BP11Azoth03": {
        "Body1Lt": "#535159",
        "Body1": "#33333D",
        "Body1Dk": "#1E1E26",
        "Body1VD": "#141419",
        "Body1Acc": "#2B2B33",
        "Body2Dk": "#2F2E45",
        "Body2VD": "#181828",
        "SpecialVL": "#00FFFF",
        "SpecialLt": "#FF0099",
        "Special": "#0D10E8",
        "SpecialDk": "#000066",
        "SpecialVD": "#000042",
        "SpecialAcc": "#5024F9",
        "Cloth": "#EDE1CE",
        "ClothDk": "#8C8281",
        "WeaponLt": "#BA865E",
        "Weapon": "#362D24",
        "WeaponDk": "#221C10",
        "WeaponAcc": "#4B3528",
    },
    "BP5GalaxyBeast": {
        "Body1Lt": "#656A82",
        "Body1": "#434661",
        "Body1Dk": "#2C2F43",
        "Body1VD": "#1A1A2C",
        "Body2Lt": "#C7C8FD",
        "Body2": "#7E80FF",
        "Body2Dk": "#363777",
        "Body2VD": "#121421",
        "Body2Acc": "#493C7D",
        "SpecialLt": "#FFFEDD",
        "Special": "#FFE88C",
        "SpecialVD": "#DFB027",
        "WeaponLt": "#FFF2AC",
        "Weapon": "#D0B360",
        "WeaponDk": "#A27B2B",
        "WeaponAcc": "#A08982",
    },
    "BP5Orion": {
        "Body1VL": "#FEFFED",
        "Body1Lt": "#FFFC96",
        "Body1": "#B19A67",
        "Body1Dk": "#5B5D43",
        "Body1VD": "#3A3A29",
        "Body1Acc": "#787047",
        "Body2": "#45483A",
        "Body2Dk": "#2E2F25",
        "Body2VD": "#151611",
        "SpecialLt": "#AFFFC9",
        "Special": "#36F9D4",
        "SpecialDk": "#45F1F8",
        "SpecialVD": "#50BDFD",
        "SpecialAcc": "#001BA1",
    },
    "BPZariel": {
        "HairLt": "#E8E6D9",
        "Hair": "#C3B7A7",
        "Body1Lt": "#643B7F",
        "Body1": "#38246B",
        "Body1Dk": "#39033D",
        "Body1VD": "#1E0235",
        "Body2": "#7F9EBB",
        "Body2Dk": "#5D5797",
        "SpecialLt": "#FDFDD7",
        "Special": "#F9D46A",
        "SpecialDk": "#E59B46",
        "Cloth": "#FFFBD6",
        "ClothDk": "#F6D36F",
        "WeaponLt": "#FFFCE3",
        "Weapon": "#DDC996",
        "WeaponDk": "#B58A84",
        "WeaponAcc": "#DEAA92",
    },
    "CyberSam": {
        "Body1VL": "#E2DEDD",
        "Body1Lt": "#BAB6B5",
        "Body1": "#7F7B7A",
        "Body1Dk": "#5D5958",
        "Body1VD": "#3D3C3A",
        "Body1Acc": "#896068",
        "Body2VL": "#7C8E90",
        "Body2Lt": "#566666",
        "Body2": "#343F43",
        "Body2Dk": "#101B1F",
        "Body2VD": "#000405",
        "Body2Acc": "#3D2D38",
        "SpecialVL": "#FEFDF8",
        "SpecialLt": "#FFEEE4",
        "Special": "#FDCAD1",
        "SpecialDk": "#FF1E72",
        "SpecialVD": "#AA0C60",
        "WeaponVL": "#F9D4B9",
        "WeaponLt": "#B99585",
        "Weapon": "#785849",
        "WeaponDk": "#3F3A37",
    },
    "Default": {},
    "DemonQueen": {
        "HairLt": "#584F4A",
        "Hair": "#332E2B",
        "HairDk": "#24201E",
        "Body1Lt": "#A2356F",
        "Body1": "#791D36",
        "Body1Dk": "#4C0B21",
        "Body2": "#302841",
        "Body2Dk": "#0B0A10",
        "SpecialVL": "#EFFFDB",
        "SpecialLt": "#D6FFBB",
        "Special": "#ABFED2",
        "SpecialDk": "#83FFE5",
        "SpecialVD": "#37DFE0",
        "ClothLt": "#F9FFFF",
        "Cloth": "#CFC7F0",
        "ClothDk": "#B39CD0",
        "WeaponLt": "#FCDDA7",
        "Weapon": "#A08B8A",
        "WeaponDk": "#67527D",
        "WeaponAcc": "#7F6885",
    },
    "DianaEpic": {
        "Body1VL": "#FDFDFD",
        "Body1": "#E5ECF5",
        "Body1Dk": "#BAC1D6",
        "Body1VD": "#868CB6",
        "Body2VL": "#80848E",
        "Body2Lt": "#52545E",
        "Body2": "#34323C",
        "Body2Dk": "#14121C",
        "Body2VD": "#040107",
        "SpecialLt": "#FDFFD7",
        "Special": "#D3FFFD",
        "SpecialDk": "#85C4E2",
        "Cloth": "#FCF9F4",
        "ClothDk": "#DED8D2",
        "WeaponLt": "#DED6BF",
        "Weapon": "#B1A08A",
        "WeaponDk": "#937C6D",
    },
    "EpicBrynn": {
        "HairLt": "#FAE987",
        "Hair": "#ECAB43",
        "HairDk": "#C567D7",
        "Body1Lt": "#FFFDD4",
        "Body1": "#E6C47C",
        "Body1Dk": "#A77D6F",
        "Body1Acc": "#CA9778",
        "Body2": "#2E3A43",
        "Body2Dk": "#161220",
        "SpecialVL": "#E6FFAB",
        "SpecialLt": "#88F19D",
        "Special": "#00BDD3",
        "SpecialDk": "#4B87E9",
        "SpecialVD": "#5B5FF4",
        "Cloth": "#FBFDF2",
        "ClothDk": "#BDBCA8",
        "WeaponVL": "#F0FFE2",
        "WeaponLt": "#B4E1E6",
        "Weapon": "#8AADCD",
        "WeaponDk": "#7C7EB9",
        "WeaponAcc": "#BC83CA",
    },
    "EpicEmber": {
        "HairLt": "#C2BAAD",
        "Hair": "#A99E8C",
        "HairDk": "#746760",
        "Body1Lt": "#685C3D",
        "Body1": "#47402B",
        "Body1Dk": "#19140D",
        "Body2Lt": "#B8C26A",
        "Body2": "#8FAC62",
        "Body2Dk": "#727159",
        "Body2VD": "#4C4E3E",
        "SpecialLt": "#FFFEF4",
        "Special": "#FFF4C8",
        "SpecialVD": "#EBC16F",
        "Cloth": "#E3DED8",
        "ClothDk": "#AEAD9C",
        "WeaponLt": "#F2EABC",
        "Weapon": "#C7B488",
        "WeaponDk": "#AC8C6C",
        "WeaponAcc": "#D4B581",
    },
    "EpicNinetails": {
        "HairLt": "#FEFEFE",
        "Hair": "#F7FAF1",
        "HairDk": "#BDCABE",
        "Body1": "#FFFFFF",
        "Body1Dk": "#E3EDFF",
        "Body1VD": "#BCCDFF",
        "Body1Acc": "#BDF6FF",
        "Body2Lt": "#6976D9",
        "Body2": "#51499D",
        "Body2Dk": "#38335A",
        "Body2VD": "#191823",
        "SpecialLt": "#FFFBC4",
        "Special": "#5FFFF8",
        "SpecialDk": "#B390FF",
        "SpecialVD": "#6D35E6",
        "ClothLt": "#D5FFCD",
        "Cloth": "#96FFEB",
        "ClothDk": "#A3C0FF",
        "WeaponLt": "#F9EABF",
        "Weapon": "#E6C88A",
        "WeaponDk": "#BB9171",
        "WeaponAcc": "#B1BDB2",
    },
    "EpicRagnir": {
        "Body1Lt": "#434451",
        "Body1": "#292B32",
        "Body1Dk": "#191B22",
        "Body1VD": "#0C0D11",
        "Body2VL": "#657EC2",
        "Body2Lt": "#3F4D6F",
        "Body2": "#2B3755",
        "SpecialVL": "#94FACD",
        "SpecialLt": "#38D2FD",
        "Special": "#3E9AD6",
        "SpecialDk": "#5375E9",
        "SpecialVD": "#1C3FD8",
        "ClothVL": "#B8B3CF",
        "ClothLt": "#938DAF",
        "Cloth": "#948F9C",
        "ClothDk": "#777480",
    },
    "EpicRaptor": {
        "Body1Lt": "#B05529",
        "Body1": "#621B0E",
        "Body1Dk": "#400804",
        "Body2": "#45211D",
        "Body2Dk": "#290F0D",
        "SpecialVL": "#F7CEBE",
        "SpecialLt": "#F7867D",
        "Special": "#F74129",
        "SpecialVD": "#150200",
        "ClothVL": "#5B2E2A",
        "ClothLt": "#301614",
        "Cloth": "#402A28",
        "ClothDk": "#221713",
        "WeaponLt": "#C46763",
        "Weapon": "#63402F",
        "WeaponDk": "#3F2927",
        "WeaponAcc": "#8B415B",
    },
    "Fenrir": {
        "Body1VL": "#919191",
        "Body1Lt": "#5B5B5D",
        "Body1": "#4A4B4D",
        "Body1Dk": "#313131",
        "Body1VD": "#141415",
        "Body1Acc": "#6B898E",
        "Body2": "#934231",
        "Body2Dk": "#5F2215",
        "SpecialVL": "#F0FFFD",
        "SpecialLt": "#D3F5F0",
        "Special": "#61FFE9",
        "WeaponLt": "#FFF5D7",
        "Weapon": "#F3E3A5",
        "WeaponDk": "#BCA46B",
    },
    "MonsterBat": {
        "HairLt": "#9B703D",
        "Hair": "#724F2A",
        "Body1Lt": "#463A3C",
        "Body1": "#2B2727",
        "Body1Dk": "#1A1717",
        "Body1VD": "#0F0C0C",
        "Body2Lt": "#DB9493",
        "Body2": "#B56766",
        "SpecialLt": "#FB7439",
        "Special": "#F5110D",
        "SpecialDk": "#6E0C25",
        "SpecialVD": "#361C19",
        "SpecialAcc": "#C24872",
        "ClothLt": "#C8B582",
        "Cloth": "#7B6550",
        "WeaponVL": "#B6AEA8",
        "WeaponLt": "#77716A",
        "Weapon": "#4B4A42",
        "WeaponDk": "#35342D",
        "WeaponAcc": "#70746B",
    },
    "MythicNix": {
        "Body1Lt": "#9195F0",
        "Body1": "#5E60AD",
        "Body1Dk": "#37345F",
        "Body1VD": "#1E1B38",
        "Body1Acc": "#592F79",
        "Body2Lt": "#451C58",
        "Body2": "#230E2D",
        "Body2Dk": "#130719",
        "SpecialVL": "#E9CCFC",
        "SpecialLt": "#FE00EE",
        "Special": "#9824AB",
        "SpecialDk": "#600A75",
    },
    "MythicWerewolf": {
        "Body1Lt": "#3A555B",
        "Body1": "#273B44",
        "Body1Dk": "#1E2A35",
        "Body1VD": "#0F1828",
        "SpecialVL": "#EBFFE1",
        "SpecialLt": "#BBFFCF",
        "Special": "#6FABB1",
        "SpecialDk": "#324657",
        "ClothLt": "#62899B",
        "Cloth": "#324F68",
        "ClothDk": "#1E283B",
        "WeaponLt": "#FFEB96",
        "Weapon": "#DDC175",
        "WeaponDk": "#B98040",
        "WeaponAcc": "#BACB94",
    },
    "MythicWuShang": {
        "Hair": "#756352",
        "HairDk": "#4F453E",
        "Body1VL": "#FEFFFA",
        "Body1Lt": "#F4FBB8",
        "Body1": "#FBC47F",
        "Body1Dk": "#EA9157",
        "Body1VD": "#B75B55",
        "Body2Lt": "#8B6046",
        "Body2": "#634236",
        "Body2Dk": "#43302F",
        "Body2VD": "#231C1F",
        "SpecialLt": "#CFFFF7",
        "Special": "#9ADFE1",
        "SpecialDk": "#655A5B",
        "SpecialVD": "#40393A",
        "Cloth": "#F6F8EB",
        "ClothDk": "#B0A688",
        "WeaponLt": "#FAEDA3",
        "Weapon": "#D1AD4D",
        "WeaponDk": "#8D5D3C",
        "WeaponAcc": "#A3976C",
    },
    "PaleRider": {
        "Body1": "#9D3437",
        "Body1Dk": "#631A19",
        "Body1VD": "#3F140F",
        "Body2": "#758D8A",
        "Body2Dk": "#476162",
        "Body2VD": "#55A6B2",
        "SpecialVL": "#FDFFD5",
        "SpecialLt": "#BEFFD2",
        "Special": "#80FFD8",
        "SpecialDk": "#63E7E3",
        "SpecialVD": "#2A9ADB",
        "Weapon": "#DBDAC5",
        "WeaponDk": "#B4AC9D",
        "WeaponAcc": "#B4CCCA",
    },
    "Seraph": {
        "Body1": "#FDFDFF",
        "Body1Dk": "#EBEBF8",
        "Body1VD": "#CAC8EB",
        "Body2VL": "#B4FDFF",
        "Body2Lt": "#58CBFF",
        "Body2": "#1E6FBB",
        "Body2Dk": "#35358F",
        "Body2VD": "#0B0433",
        "Body2Acc": "#394ED6",
        "SpecialLt": "#FFC1B0",
        "Special": "#C2413B",
        "SpecialDk": "#7A2438",
        "SpecialAcc": "#7A3DB5",
        "ClothLt": "#FFF7BA",
        "Cloth": "#EFD35C",
        "ClothDk": "#BA8B3B",
    },
    "ShinobiBP1203": {
        "HairDk": "#0D1117",
        "Body1VL": "#3E5357",
        "Body1Lt": "#2B4142",
        "Body1": "#252C35",
        "Body1Dk": "#14222B",
        "Body2VL": "#752834",
        "Body2Lt": "#4B1C1B",
        "Body2": "#32252A",
        "Body2Dk": "#1C1618",
        "SpecialVL": "#FF8D7E",
        "SpecialLt": "#A5FFF4",
        "Special": "#30E0D1",
        "SpecialDk": "#3D798F",
        "SpecialVD": "#283F54",
        "SpecialAcc": "#FF3300",
        "ClothLt": "#9BA7A6",
        "Cloth": "#60686A",
        "ClothDk": "#2D3439",
        "WeaponLt": "#9B9BE8",
        "Weapon": "#7D86A2",
        "WeaponDk": "#475072",
    },
    "Viking": {
        "Hair": "#ECF185",
        "HairDk": "#9CA75F",
        "Body1Lt": "#84CE6F",
        "Body1": "#3F985B",
        "Body2": "#477860",
        "Body2Dk": "#2D4A44",
        "SpecialLt": "#C6FFEF",
        "Special": "#20FFC1",
        "SpecialDk": "#00B98F",
        "ClothLt": "#FFFFCC",
        "Cloth": "#B7C168",
        "Weapon": "#57BDB0",
        "WeaponDk": "#3A9489",
    },
}

WIKI_COLORS_API_URL = "https://brawlhalla.wiki.gg/api.php?action=parse&page=Colors&prop=text&format=json"

DEFAULT_MODIFIABLE_COLORS_FALLBACK = {
    "battle_pass": [
        "Soul Fire", "Synthwave", "Frozen Forest", "Coat of Lions", "Starlight",
        "Willow Leaves", "Pact of Poison", "Darkheart", "Armageddon", "Kira-kira",
        "Ancient Curse", "Neon Hanafuda", "Dragonfire"
    ],
    "paid": [
        "RGB"
    ]
}

def hex_to_rgb(hex_str):
    h = hex_str.lstrip("#")
    if len(h) == 6:
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    return (0, 0, 0)

def rgb_to_hex(rgb):
    return f"#{int(rgb[0]):02X}{int(rgb[1]):02X}{int(rgb[2]):02X}"

def int_to_hex(val):
    if isinstance(val, str):
        v = val.strip()
        if v.startswith("0x") or v.startswith("0X") or v.startswith("#"):
            return f"#{int(v.replace('0x', '').replace('0X', '').replace('#', ''), 16) & 0xFFFFFF:06X}"
        try:
            return f"#{int(v) & 0xFFFFFF:06X}"
        except ValueError:
            return f"#{int(v, 16) & 0xFFFFFF:06X}"
    return f"#{(int(val) & 0xFFFFFF):06X}"

def hex_to_int(hex_str):
    h = hex_str.lstrip("#").replace("0x", "").replace("0X", "")
    return int(h, 16) if h else 0

def rgb_to_cmyk(r, g, b):
    if r == 0 and g == 0 and b == 0:
        return 0, 0, 0, 100
    c = 1 - r / 255.0
    m = 1 - g / 255.0
    y = 1 - b / 255.0
    k = min(c, m, y)
    if k == 1.0:
        return 0, 0, 0, 100
    c = (c - k) / (1 - k)
    m = (m - k) / (1 - k)
    y = (y - k) / (1 - k)
    return int(round(c * 100)), int(round(m * 100)), int(round(y * 100)), int(round(k * 100))

def cmyk_to_rgb(c, m, y, k):
    c, m, y, k = c / 100.0, m / 100.0, y / 100.0, k / 100.0
    r = 255 * (1 - c) * (1 - k)
    g = 255 * (1 - m) * (1 - k)
    b = 255 * (1 - y) * (1 - k)
    return int(max(0, min(255, round(r)))), int(max(0, min(255, round(g)))), int(max(0, min(255, round(b))))


class ColorModToolModule(ToolModule):
    """
    Color Mod Tool: interactive 6x6 channel matrix of perfect squares,
    compact color picker, enlarged live Bodvar preview, and carrier / mod sources exporters.
    """

    def __init__(self, parent, game_path="", mods_path="", icons=None, **kwargs):
        super().__init__(parent, game_path, mods_path, icons=icons)
        self.brawlhalla_dir = self.game_path or ""
        self.game_custom_folder = self.mods_path or ""
        self.assets_dir = Path(__file__).parent.parent.parent / "resources" / "assets"

        # Dynamic skin SVG system & Preview State
        self.templates_dir = self.assets_dir / "Templates"
        self.skin_svgs: list = sorted(list(self.templates_dir.glob("*.svg"))) if self.templates_dir.exists() else []
        # Default to Viking.svg if available, otherwise first file
        _default = next((i for i, p in enumerate(self.skin_svgs) if p.name.lower() == "viking.svg"), 0)
        self.skin_svg_index: int = _default
        self._skin_img_ref = None

        # Preview Zoom & Pan State
        self.preview_zoom = 1.0
        self.preview_pan_x = 0
        self.preview_pan_y = 0
        self._pan_drag_start_x = 0
        self._pan_drag_start_y = 0

        # QoL Checkboxes & Slideshow Timer State
        self._var_highlight_channel = None
        self._var_auto_cycle = None
        self._auto_cycle_timer_id = None

        # Pulsing Highlight State (2 second slow cycle)
        self._hl_time = 0
        self._hl_timer_id = None

        # Juicy Spring-Pop Micro-Animation State
        self._pop_anim_frame = 0
        self._pop_anim_timer_id = None
        self._pop_anim_scale = 1.0

        # Column Resizer Dimensions (1/5 : 2/5 : 2/5 Default Proportions)
        self.left_panel_width = 250
        self.right_panel_width = 460
        self._user_adjusted_sashes = False

        # Highlight Customization Options (Defaults: White outline, Magenta fill, 20% opacity, 1.0s speed)
        self._hl_outline_style = "Dotted"
        self._hl_outline_color = "#FFFFFF"
        self._hl_fill_color = "#FF007F"
        self._hl_opacity_val = 0.20 # 20% default fill opacity
        self._hl_speed_ms = 1000 # 1.0s default pulse speed

        # Matrix Tags Display Mode ("Full Names", "Compact", "None")
        self.tags_display_mode = "Full Names" 

        # Costumes & Color Exceptions registry from Game.swz
        self.costumes_data = {}
        self.color_exceptions = []
        self.official_schemes_raw = {}

        # Active Palette & Schemes State
        self.all_schemes = []       # list of (display_name, scheme_id, scheme_dict)
        self.selected_scheme_id = 0 # Classic = 0 default
        self.selected_scheme_name = "Classic"
        self.active_palette = dict(BODVAR_CLASSIC_PALETTE)
        self.selected_channel = "Hair" # Currently selected cell in the 6x6 grid
        self.saved_presets = []

        # Color Picker State
        self.picker_mode = "Hue" # "Hue", "Bright", "Wheel", "Grey"
        self.slider_mode = "HSB" # "HSB", "RGB", "Hex"
        r, g, b = hex_to_rgb(BODVAR_CLASSIC_PALETTE.get("Hair", "#ECF185"))
        self.cur_h, self.cur_s, self.cur_v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        self._picker_img_ref = None
        self._slider_img_ref = None

        # Custom Schemes State & Persistence Cache
        self.custom_schemes = [] # list of (name, sid, pal_dict, is_custom)
        cache_dir = os.path.join(os.getenv('APPDATA') or str(Path.home()), 'Brawlhalla Modding Toolkit')
        os.makedirs(cache_dir, exist_ok=True)
        self.custom_schemes_cache_file = os.path.join(cache_dir, "CustomColorSchemes.json")
        self._load_custom_schemes_cache()

        # Load all official schemes, costumes, and color exceptions from Game.swz
        self._load_official_schemes()

        # Background fetch for wiki modifiable colors (Battle Pass & Paid)
        threading.Thread(target=self._fetch_modifiable_colors_from_wiki, daemon=True).start()

    def create_ui(self):
        """Creates or shows the full user interface for Color Mod Tool."""
        if self.container is not None:
            self.show()
            self._render_skin_preview()
            return

        self._build_ui()
        self._sync_picker_from_color(self.active_palette.get(self.selected_channel, "#2C2B31"))
        self._render_skin_preview()

    def get_tool_name(self):
        return "Color Mod Tool"

    def get_tool_icon(self):
        return self.icons.get("color_mod_tool") if self.icons else "color_mod_tool"

    # =========================================================================
    # OFFICIAL GAME.SWZ SCHEMES EXTRACTION (ALL 78+ SCHEMES)
    # =========================================================================

    def _load_official_schemes(self):
        self.all_schemes = []
        self.costumes_data = {}
        self.color_exceptions = []
        self.official_schemes_raw = {}

        if not self.brawlhalla_dir or not SwzReader:
            self._set_fallback_schemes()
            return

        try:
            air_swf = os.path.join(self.brawlhalla_dir, "BrawlhallaAir.swf")
            init_swz = os.path.join(self.brawlhalla_dir, "Init.swz")
            game_swz = os.path.join(self.brawlhalla_dir, "Game.swz")

            if not os.path.exists(air_swf) or not os.path.exists(init_swz) or not os.path.exists(game_swz):
                self._set_fallback_schemes()
                return

            key = SwzReader.find_swz_key(air_swf, init_swz)
            if not key:
                self._set_fallback_schemes()
                return

            with open(game_swz, "rb") as f:
                entries = SwzReader.read_swz(f.read(), key)

            if len(entries) <= 7:
                self._set_fallback_schemes()
                return

            # Translations dictionary
            lang_dict = {}
            if BrawlhallaLangReader:
                try:
                    lang_dir = os.path.join(self.brawlhalla_dir, "languages")
                    reader = BrawlhallaLangReader(lang_dir)
                    lang_dict = reader.read_language_file(1) or {} # English names
                except Exception:
                    pass

            # 1. Entry 9 contains costumeTypes CSV
            if len(entries) > 9:
                try:
                    import csv
                    csv_text = entries[9].decode("utf-8", errors="ignore").splitlines()
                    if csv_text and csv_text[0].startswith("costumeTypes"):
                        csv_text = csv_text[1:]
                    reader = csv.DictReader(csv_text)
                    for row in reader:
                        c_name = row.get("CostumeName")
                        if not c_name:
                            continue
                        defines = {}
                        classic_pal = {}
                        for k, v in row.items():
                            if k.endswith("_Define") and v and v != "--" and not k.startswith("Hands"):
                                ch = k[:-7]
                                h = int_to_hex(v)
                                defines[h.upper()] = ch
                                classic_pal[ch] = h.upper()
                        disp_key = row.get("DisplayNameKey", "")
                        disp_name = lang_dict.get(disp_key, "") if disp_key else ""
                        if not disp_name:
                            hero = row.get("OwnerHero", "")
                            hero_disp = lang_dict.get(f"HeroType_{hero}_HeroDisplayName", hero)
                            disp_name = f"Classic {hero_disp}" if c_name in ("Viking", "Default", hero) else f"{c_name} {hero_disp}"

                        if defines:
                            self.costumes_data[c_name] = {
                                "defines": defines,
                                "classic_palette": classic_pal,
                                "display_name": disp_name
                            }
                    print(f"[ColorModTool] Loaded {len(self.costumes_data)} costumes data from Game.swz!")
                except Exception as e:
                    print(f"[ColorModTool] Error loading costumes from Game.swz: {e}")

            # 2. Entry 6 contains colorExceptionTypes CSV
            if len(entries) > 6:
                try:
                    import csv
                    csv_text = entries[6].decode("utf-8", errors="ignore").splitlines()
                    if csv_text and csv_text[0].startswith("colorExceptionTypes"):
                        csv_text = csv_text[1:]
                    reader = csv.DictReader(csv_text)
                    for row in reader:
                        target = row.get("TargetName")
                        scheme = row.get("ColorSchemeName")
                        if target and scheme:
                            self.color_exceptions.append(row)
                    print(f"[ColorModTool] Loaded {len(self.color_exceptions)} color exceptions from Game.swz!")
                except Exception as e:
                    print(f"[ColorModTool] Error loading color exceptions: {e}")

            # 3. Entry 7 contains ColorSchemeTypes XML
            xml_content = entries[7].decode("utf-8", errors="ignore")
            root = ET.fromstring(xml_content)
            cs_types = root.findall(".//ColorSchemeType")

            for cs in cs_types:
                name_elem = cs.find("ColorSchemeName")
                id_elem = cs.find("ColorSchemeID")
                disp_elem = cs.find("DisplayNameKey")

                internal_name = cs.get("ColorSchemeName") or (name_elem.text.strip() if name_elem is not None and name_elem.text else "")
                sid_str = cs.get("ColorSchemeID") or (id_elem.text.strip() if id_elem is not None and id_elem.text else "0")
                try:
                    sid = int(sid_str)
                except ValueError:
                    sid = 0

                if internal_name in ("Template", "Default", "Classic") or sid == 0:
                    self.all_schemes.append(("Classic", 0, dict(BODVAR_CLASSIC_PALETTE)))
                    self.official_schemes_raw[0] = dict(BODVAR_CLASSIC_PALETTE)
                    self.official_schemes_raw["Classic"] = dict(BODVAR_CLASSIC_PALETTE)
                    continue

                if not internal_name:
                    continue

                disp_key = cs.get("DisplayNameKey") or (disp_elem.text.strip() if disp_elem is not None and disp_elem.text else "")
                display_name = lang_dict.get(disp_key, internal_name) if disp_key else internal_name

                # Parse base colors from <Hair_Swap>, <Body1_Swap>, etc.
                pal = {}
                for ch in ALL_CHANNELS_LIST:
                    elem = cs.find(f"{ch}_Swap")
                    if elem is None:
                        elem = cs.find(ch)

                    if elem is not None and elem.text and elem.text.strip() not in ("--", ""):
                        pal[ch] = int_to_hex(elem.text.strip())
                    elif cs.get(f"{ch}_Swap"):
                        pal[ch] = int_to_hex(cs.get(f"{ch}_Swap"))
                    elif cs.get(ch):
                        pal[ch] = int_to_hex(cs.get(ch))
                    else:
                        pal[ch] = BODVAR_CLASSIC_PALETTE.get(ch, "#2C2B31")

                self.all_schemes.append((display_name, sid, pal))
                self.official_schemes_raw[sid] = pal
                self.official_schemes_raw[internal_name] = pal

            if not any(s[1] == 0 for s in self.all_schemes):
                self.all_schemes.insert(0, ("Classic", 0, dict(BODVAR_CLASSIC_PALETTE)))
                self.official_schemes_raw[0] = dict(BODVAR_CLASSIC_PALETTE)
                self.official_schemes_raw["Classic"] = dict(BODVAR_CLASSIC_PALETTE)

            self.all_schemes.sort(key=lambda s: s[1])
            print(f"[ColorModTool] Loaded {len(self.all_schemes)} official Color Schemes from Game.swz!")

        except Exception as e:
            print(f"[ColorModTool] Error loading schemes from Game.swz: {e}")
            self._set_fallback_schemes()

    def _load_custom_schemes_cache(self):
        self.custom_schemes = []
        if os.path.exists(self.custom_schemes_cache_file):
            try:
                with open(self.custom_schemes_cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            name = item.get("name", "Custom")
                            sid = item.get("id", "Custom")
                            pal = item.get("palette", {})
                            if pal:
                                self.custom_schemes.append((name, sid, pal, True))
            except Exception as e:
                print(f"[ColorModTool] Error loading custom schemes cache: {e}")

    def _save_custom_schemes_cache(self):
        try:
            data = []
            for item in self.custom_schemes:
                name, sid, pal = item[0], item[1], item[2]
                data.append({"name": name, "id": sid, "palette": pal})
            with open(self.custom_schemes_cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[ColorModTool] Error saving custom schemes cache: {e}")

    def _set_fallback_schemes(self):
        self.all_schemes = [
            ("Classic", 0, dict(BODVAR_CLASSIC_PALETTE)),
            ("Red", 1, dict(DEFAULT_BLACK_PALETTE)),
            ("Blue", 2, dict(DEFAULT_BLACK_PALETTE)),
            ("Yellow", 3, dict(DEFAULT_BLACK_PALETTE)),
            ("Green", 4, dict(DEFAULT_BLACK_PALETTE)),
            ("White", 10, dict(DEFAULT_BLACK_PALETTE)),
            ("Black", 11, dict(DEFAULT_BLACK_PALETTE)),
            ("Sunset", 16, dict(DEFAULT_BLACK_PALETTE)),
            ("Gray", 17, dict(DEFAULT_BLACK_PALETTE)),
            ("Cyan", 8, dict(DEFAULT_BLACK_PALETTE)),
        ]

    # =========================================================================
    # UI CONSTRUCTION (DARK GRAY BMT THEME & SQUARES)
    # =========================================================================

    def _build_ui(self):
        self.master_frame = ctk.CTkFrame(self.parent, fg_color="#18181b", corner_radius=0)
        self.container = self.master_frame
        self.container.pack(fill="both", expand=True)

        # ── TOP CONTROL TOOLBAR ──────────────────────────────────────────
        self._build_top_toolbar()

        # ── MAIN 3-COLUMN WORKSPACE (1/5 : 2/5 : 2/5 ASPECT RATIO) ───────
        self.workspace = ctk.CTkFrame(self.master_frame, fg_color="transparent")
        self.workspace.pack(fill="both", expand=True, padx=8, pady=(4, 8))
        self.workspace.bind("<Configure>", self._on_workspace_resize)

        # 1. LEFT PANEL (Color Picker - 1/5 width)
        self._build_left_picker_panel()

        # Sash 1 (Draggable Resizer between Left and Center columns)
        self.sash_1 = tk.Frame(self.workspace, width=5, bg="#18181b", cursor="sb_h_double_arrow")
        self.sash_1.pack(side="left", fill="y", padx=1)
        self.sash_1.bind("<Button-1>", self._on_sash1_press)
        self.sash_1.bind("<B1-Motion>", self._on_sash1_drag)
        self.sash_1.bind("<Enter>", lambda e: self.sash_1.configure(bg="#07c9d7"))
        self.sash_1.bind("<Leave>", lambda e: self.sash_1.configure(bg="#18181b"))

        # 3. RIGHT PANEL (Sprite Preview & QoL Controls - 2/5 width)
        self._build_right_preview_panel()

        # Sash 2 (Draggable Resizer between Center and Right columns)
        self.sash_2 = tk.Frame(self.workspace, width=5, bg="#18181b", cursor="sb_h_double_arrow")
        self.sash_2.pack(side="right", fill="y", padx=1)
        self.sash_2.bind("<Button-1>", self._on_sash2_press)
        self.sash_2.bind("<B1-Motion>", self._on_sash2_drag)
        self.sash_2.bind("<Enter>", lambda e: self.sash_2.configure(bg="#07c9d7"))
        self.sash_2.bind("<Leave>", lambda e: self.sash_2.configure(bg="#18181b"))

        # 2. CENTER PANEL (6x6 Matrix + Bottom Presets Strip - 2/5 width)
        self._build_center_matrix_panel()

    # ── TOP TOOLBAR ───────────────────────────────────────────────────────
    def _build_top_toolbar(self):
        top_bar = ctk.CTkFrame(self.master_frame, fg_color="#27272a", height=46, corner_radius=6, border_width=1, border_color="#3f3f46")
        top_bar.pack(fill="x", padx=8, pady=(6, 2))

        # Title: Color Mod Tool
        brand_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        brand_frame.pack(side="left", padx=(12, 14), pady=4)
        title_lbl = ctk.CTkLabel(brand_frame, text="Color Mod Tool", font=("Inter", 13, "bold"), text_color="#f4f4f5")
        title_lbl.pack(side="left")

        # Scheme Selector Button with Swatch Preview & Dropdown Arrow
        self.scheme_selector_btn = ctk.CTkFrame(
            top_bar,
            fg_color="#3f3f46",
            height=28,
            width=190,
            corner_radius=4,
            border_width=1,
            border_color="#52525b",
            cursor="hand2"
        )
        self.scheme_selector_btn.pack(side="left", padx=(0, 6), pady=6)
        self.scheme_selector_btn.pack_propagate(False)

        # Mini preview swatches container on the left
        self.btn_preview_frame = ctk.CTkFrame(self.scheme_selector_btn, fg_color="transparent")
        self.btn_preview_frame.pack(side="left", padx=(6, 6), pady=4)

        self.btn_swatches = []
        for _ in range(6):
            sw = ctk.CTkFrame(self.btn_preview_frame, width=5, height=14, fg_color="#2C2B31", corner_radius=1)
            sw.pack(side="left", padx=0.5)
            self.btn_swatches.append(sw)

        # Scheme name label
        self.btn_scheme_name_lbl = ctk.CTkLabel(
            self.scheme_selector_btn,
            text=self.selected_scheme_name or "Black",
            font=("Inter", 11, "bold"),
            text_color="#f4f4f5",
            anchor="w"
        )
        self.btn_scheme_name_lbl.pack(side="left", fill="x", expand=True)

        # Arrow indicator
        self.btn_arrow_lbl = ctk.CTkLabel(
            self.scheme_selector_btn,
            text="▼",
            font=("Inter", 8),
            text_color="#a1a1aa",
            width=16
        )
        self.btn_arrow_lbl.pack(side="right", padx=(2, 6))

        for w in (self.scheme_selector_btn, self.btn_preview_frame, self.btn_scheme_name_lbl, self.btn_arrow_lbl, *self.btn_swatches):
            w.bind("<Button-1>", lambda e: self._toggle_scheme_dropdown())
            w.bind("<Enter>", lambda e: self.scheme_selector_btn.configure(fg_color="#52525b"))
            w.bind("<Leave>", lambda e: self.scheme_selector_btn.configure(fg_color="#3f3f46"))

        top_bar_btn_kwargs = {
            "height": 26,
            "font": ("Inter", 11),
            "fg_color": "#3f3f46",
            "hover_color": "#52525b",
            "border_width": 1,
            "border_color": "#52525b",
            "text_color": "#f4f4f5",
            "corner_radius": 4
        }

        save_btn = ctk.CTkButton(top_bar, text="Save", width=55, command=self._save_current_preset, **top_bar_btn_kwargs)
        save_btn.pack(side="left", padx=3)
        BMTToolTip(save_btn, "Save current palette as a custom color scheme.")

        del_btn = ctk.CTkButton(top_bar, text="Delete", width=55, command=self._delete_current_preset, **top_bar_btn_kwargs)
        del_btn.pack(side="left", padx=3)
        BMTToolTip(del_btn, "Delete currently selected custom color scheme.")

        share_btn = ctk.CTkButton(top_bar, text="Share Palette", width=105, command=self._share_palette, **top_bar_btn_kwargs)
        share_btn.pack(side="left", padx=3)
        BMTToolTip(share_btn, "Export a .palette file to share this custom color scheme with other users.")

        import_btn = ctk.CTkButton(top_bar, text="Import Palette", width=105, command=self._import_palette, **top_bar_btn_kwargs)
        import_btn.pack(side="left", padx=3)
        BMTToolTip(import_btn, "Import a .palette file shared by other users into your Color Mod Tool.")

    # ── LEFT PANEL (COMPACT COLOR PICKER & QUICK TRANSFORM: 250px) ──────
    def _build_left_picker_panel(self):
        self.left_panel = ctk.CTkFrame(self.workspace, width=self.left_panel_width, fg_color="#27272a", corner_radius=6, border_width=1, border_color="#3f3f46")
        self.left_panel.pack(side="left", fill="y", padx=(0, 2))
        self.left_panel.pack_propagate(False)
        panel = self.left_panel

        ctk.CTkLabel(panel, text="COLOR PICKER", font=("Inter", 11, "bold"), text_color="#a1a1aa").pack(anchor="w", padx=10, pady=(6, 2))

        # Centered 2D Interactive Canvas & Slider Container
        cv_wrapper = ctk.CTkFrame(panel, fg_color="transparent")
        cv_wrapper.pack(fill="x", padx=6, pady=2)
        cv_container = ctk.CTkFrame(cv_wrapper, fg_color="transparent")
        cv_container.pack(anchor="center")

        # 2D Gradient Canvas (160x125)
        self.canvas_2d = tk.Canvas(cv_container, width=160, height=125, bg="#18181b", highlightthickness=1, highlightbackground="#3f3f46", cursor="crosshair")
        self.canvas_2d.pack(side="left", padx=(0, 4))
        self.canvas_2d.bind("<Button-1>", self._on_canvas_2d_click)
        self.canvas_2d.bind("<B1-Motion>", self._on_canvas_2d_drag)

        # Vertical Slider Canvas (20x125)
        self.slider_cv = tk.Canvas(cv_container, width=20, height=125, bg="#18181b", highlightthickness=1, highlightbackground="#3f3f46", cursor="sb_v_double_arrow")
        self.slider_cv.pack(side="left")
        self.slider_cv.bind("<Button-1>", self._on_slider_cv_click)
        self.slider_cv.bind("<B1-Motion>", self._on_slider_cv_drag)

        # Centered Active Color Swatch + Hex Input Row
        hex_row = ctk.CTkFrame(panel, fg_color="transparent")
        hex_row.pack(fill="x", padx=6, pady=(3, 2))
        hex_inner = ctk.CTkFrame(hex_row, fg_color="transparent")
        hex_inner.pack(anchor="center")

        self.swatch_preview = ctk.CTkFrame(hex_inner, width=24, height=22, fg_color=self.active_palette.get(self.selected_channel, "#2C2B31"), corner_radius=4)
        self.swatch_preview.pack(side="left", padx=(0, 4))

        self.hex_entry = ctk.CTkEntry(hex_inner, width=80, height=22, font=("Consolas", 10, "bold"), fg_color="#18181b", border_color="#3f3f46", text_color="#07c9d7")
        self.hex_entry.insert(0, self.active_palette.get(self.selected_channel, "#2C2B31"))
        self.hex_entry.pack(side="left", padx=(0, 4))
        self.hex_entry.bind("<Return>", self._on_hex_entry_submit)

        copy_btn = ctk.CTkButton(hex_inner, text="Copy", width=40, height=22, font=("Inter", 9), fg_color="#3f3f46", hover_color="#52525b", command=self._copy_current_hex)
        copy_btn.pack(side="left")

        # Color Model Sub-Tabs (2-row grid: [HSB] [RGB] [HSL] / [CMYK] [Hex])
        subtab_frame = ctk.CTkFrame(panel, fg_color="#18181b", corner_radius=6)
        subtab_frame.pack(fill="x", padx=8, pady=3)
        subtab_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.slider_tab_btns = {}
        modes = [
            ("HSB", 0, 0), ("RGB", 0, 1), ("HSL", 0, 2),
            ("CMYK", 1, 0), ("Hex", 1, 1)
        ]
        for smode, r, c in modes:
            span = 2 if smode == "Hex" else 1
            sbtn = ctk.CTkButton(
                subtab_frame,
                text=smode,
                height=20,
                font=("Inter", 9, "bold"),
                fg_color="#07c9d7" if smode == self.slider_mode else "transparent",
                text_color="#18181b" if smode == self.slider_mode else "#a1a1aa",
                hover_color="#3f3f46",
                corner_radius=4,
                command=lambda s=smode: self._set_slider_mode(s)
            )
            sbtn.grid(row=r, column=c, columnspan=span, padx=1.5, pady=1.5, sticky="ew")
            self.slider_tab_btns[smode] = sbtn

        # Sliders Controls
        self.sliders_container = ctk.CTkFrame(panel, fg_color="transparent")
        self.sliders_container.pack(fill="x", padx=8, pady=1)
        self._build_model_sliders()

        # Quick Transform Header & 4x3 Action Grid
        ctk.CTkLabel(panel, text="QUICK TRANSFORM", font=("Inter", 9, "bold"), text_color="#a1a1aa").pack(anchor="w", padx=10, pady=(4, 1))
        qgrid = ctk.CTkFrame(panel, fg_color="transparent")
        qgrid.pack(fill="x", padx=6, pady=1)
        qgrid.grid_columnconfigure((0, 1, 2), weight=1)

        qbtn_kwargs = {"height": 22, "font": ("Inter", 8, "bold"), "fg_color": "#3f3f46", "hover_color": "#52525b", "border_width": 1, "border_color": "#52525b", "text_color": "#f4f4f5"}

        # Row 0: Auto Shade | Harmonize | Randomize
        b_shade = ctk.CTkButton(qgrid, text="Auto Shade", command=self._action_auto_shade_all, **qbtn_kwargs)
        b_shade.grid(row=0, column=0, padx=1, pady=1, sticky="ew")
        BMTToolTip(b_shade, "Generate natural light-to-dark shades from the Base color of each row.")

        b_harm = ctk.CTkButton(qgrid, text="Harmonize", command=self._action_harmonize, **qbtn_kwargs)
        b_harm.grid(row=0, column=1, padx=1, pady=1, sticky="ew")
        BMTToolTip(b_harm, "Harmonize all row colors using color theory relations.")

        b_rand = ctk.CTkButton(qgrid, text="Randomize", command=self._action_randomize, **qbtn_kwargs)
        b_rand.grid(row=0, column=2, padx=1, pady=1, sticky="ew")
        BMTToolTip(b_rand, "Generate a fresh, harmonious randomized palette.")

        # Row 1: Hue +30° | Hue -30° | Flip Hue
        b_hplus = ctk.CTkButton(qgrid, text="Hue +30°", command=lambda: self._action_hue_shift(30), **qbtn_kwargs)
        b_hplus.grid(row=1, column=0, padx=1, pady=1, sticky="ew")
        BMTToolTip(b_hplus, "Shift entire palette hue clockwise by +30 degrees.")

        b_hminus = ctk.CTkButton(qgrid, text="Hue -30°", command=lambda: self._action_hue_shift(-30), **qbtn_kwargs)
        b_hminus.grid(row=1, column=1, padx=1, pady=1, sticky="ew")
        BMTToolTip(b_hminus, "Shift entire palette hue counter-clockwise by -30 degrees.")

        b_hflip = ctk.CTkButton(qgrid, text="Flip Hue", command=lambda: self._action_hue_shift(180), **qbtn_kwargs)
        b_hflip.grid(row=1, column=2, padx=1, pady=1, sticky="ew")
        BMTToolTip(b_hflip, "Flip palette hue by 180 degrees (complementary colors).")

        # Row 2: Brighten | Darken | Saturate
        b_bright = ctk.CTkButton(qgrid, text="Brighten", command=lambda: self._action_bright_shift(0.1), **qbtn_kwargs)
        b_bright.grid(row=2, column=0, padx=1, pady=1, sticky="ew")
        BMTToolTip(b_bright, "Increase overall palette brightness by +10%.")

        b_dark = ctk.CTkButton(qgrid, text="Darken", command=lambda: self._action_bright_shift(-0.1), **qbtn_kwargs)
        b_dark.grid(row=2, column=1, padx=1, pady=1, sticky="ew")
        BMTToolTip(b_dark, "Decrease overall palette brightness by -10%.")

        b_sat = ctk.CTkButton(qgrid, text="Saturate", command=lambda: self._action_saturate_shift(0.15), **qbtn_kwargs)
        b_sat.grid(row=2, column=2, padx=1, pady=1, sticky="ew")
        BMTToolTip(b_sat, "Boost color saturation across all channels.")

        # Row 3: Invert | Grayscale | Reset
        b_inv = ctk.CTkButton(qgrid, text="Invert", command=self._action_invert, **qbtn_kwargs)
        b_inv.grid(row=3, column=0, padx=1, pady=1, sticky="ew")
        BMTToolTip(b_inv, "Invert all RGB colors in the active palette.")

        b_grey = ctk.CTkButton(qgrid, text="Grayscale", command=self._action_greyscale, **qbtn_kwargs)
        b_grey.grid(row=3, column=1, padx=1, pady=1, sticky="ew")
        BMTToolTip(b_grey, "Convert entire palette to monochrome grayscale.")

        b_rst = ctk.CTkButton(qgrid, text="Reset", command=self._action_reset_palette, **qbtn_kwargs)
        b_rst.grid(row=3, column=2, padx=1, pady=1, sticky="ew")
        BMTToolTip(b_rst, "Reset all colors to original scheme defaults.")

        # Shading Slider Row
        shading_frame = ctk.CTkFrame(panel, fg_color="transparent")
        shading_frame.pack(fill="x", padx=8, pady=(3, 1))
        ctk.CTkLabel(shading_frame, text="Shading", font=("Inter", 9), text_color="#a1a1aa").pack(side="left")
        self.shading_slider = ctk.CTkSlider(shading_frame, from_=0.0, to=2.0, number_of_steps=40, height=11, progress_color="#07c9d7", command=self._on_shading_slider_change)
        self.shading_slider.set(1.0)
        self.shading_slider.pack(side="left", fill="x", expand=True, padx=4)
        self.shading_lbl = ctk.CTkLabel(shading_frame, text="100%", font=("Inter", 9), text_color="#f4f4f5", width=28)
        self.shading_lbl.pack(side="left")

    def _build_model_sliders(self):
        for widget in self.sliders_container.winfo_children():
            widget.destroy()

        if self.slider_mode == "HSB":
            self.s_h = self._create_slider_row("H", int(self.cur_h * 360), 0, 360, self._on_hsb_slider_change)
            self.s_s = self._create_slider_row("S", int(self.cur_s * 100), 0, 100, self._on_hsb_slider_change)
            self.s_b = self._create_slider_row("B", int(self.cur_v * 100), 0, 100, self._on_hsb_slider_change)
        elif self.slider_mode == "RGB":
            r, g, b = hex_to_rgb(self.active_palette.get(self.selected_channel, "#2C2B31"))
            self.s_r = self._create_slider_row("R", r, 0, 255, self._on_rgb_slider_change)
            self.s_g = self._create_slider_row("G", g, 0, 255, self._on_rgb_slider_change)
            self.s_b_rgb = self._create_slider_row("B", b, 0, 255, self._on_rgb_slider_change)
        elif self.slider_mode == "HSL":
            r, g, b = hex_to_rgb(self.active_palette.get(self.selected_channel, "#2C2B31"))
            h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
            self.s_hsl_h = self._create_slider_row("H", int(h * 360), 0, 360, self._on_hsl_slider_change)
            self.s_hsl_s = self._create_slider_row("S", int(s * 100), 0, 100, self._on_hsl_slider_change)
            self.s_hsl_l = self._create_slider_row("L", int(l * 100), 0, 100, self._on_hsl_slider_change)
        elif self.slider_mode == "CMYK":
            r, g, b = hex_to_rgb(self.active_palette.get(self.selected_channel, "#2C2B31"))
            c, m, y, k = rgb_to_cmyk(r, g, b)
            self.s_cmyk_c = self._create_slider_row("C", c, 0, 100, self._on_cmyk_slider_change)
            self.s_cmyk_m = self._create_slider_row("M", m, 0, 100, self._on_cmyk_slider_change)
            self.s_cmyk_y = self._create_slider_row("Y", y, 0, 100, self._on_cmyk_slider_change)
            self.s_cmyk_k = self._create_slider_row("K", k, 0, 100, self._on_cmyk_slider_change)
        elif self.slider_mode == "Hex":
            lbl = ctk.CTkLabel(self.sliders_container, text=f"Hex: {self.active_palette.get(self.selected_channel, '#2C2B31')}", font=("Consolas", 10, "bold"), text_color="#07c9d7")
            lbl.pack(pady=2)

    def _create_slider_row(self, label, val, min_v, max_v, callback):
        row = ctk.CTkFrame(self.sliders_container, fg_color="transparent")
        row.pack(fill="x", pady=0.5)
        ctk.CTkLabel(row, text=label, width=14, font=("Inter", 9), text_color="#a1a1aa").pack(side="left")
        slider = ctk.CTkSlider(row, from_=min_v, to=max_v, number_of_steps=max_v - min_v, height=11, progress_color="#07c9d7", command=lambda v: callback())
        slider.set(val)
        slider.pack(side="left", fill="x", expand=True, padx=3)
        val_lbl = ctk.CTkLabel(row, text=str(val), width=24, font=("Consolas", 9), text_color="#f4f4f5")
        val_lbl.pack(side="left")
        slider._val_lbl = val_lbl
        return slider

    # ── CENTER PANEL (RESPONSIVE RESIZABLE 6x6 PERFECT SQUARE MATRIX) ────
    def _build_center_matrix_panel(self):
        self.center_panel = ctk.CTkFrame(self.workspace, fg_color="#27272a", corner_radius=6, border_width=1, border_color="#3f3f46")
        self.center_panel.pack(side="left", fill="both", expand=True, padx=2)
        panel = self.center_panel

        matrix_wrapper = ctk.CTkFrame(panel, fg_color="transparent")
        matrix_wrapper.pack(fill="both", expand=True, padx=6, pady=6)

        # Top Header Bar: Title & Tags Mode Selector (Full Names / Compact / None)
        matrix_top_bar = ctk.CTkFrame(matrix_wrapper, fg_color="transparent")
        matrix_top_bar.pack(fill="x", padx=4, pady=(0, 2))

        ctk.CTkLabel(matrix_top_bar, text="PALETTE MATRIX (6x6)", font=("Inter", 11, "bold"), text_color="#a1a1aa").pack(side="left")

        tags_frame = ctk.CTkFrame(matrix_top_bar, fg_color="transparent")
        tags_frame.pack(side="right")

        ctk.CTkLabel(tags_frame, text="Tags:", font=("Inter", 10, "bold"), text_color="#71717a").pack(side="left", padx=(0, 4))
        self.tags_mode_opt = ctk.CTkOptionMenu(
            tags_frame,
            values=["Full Names", "Compact", "None"],
            command=self._on_tags_mode_changed,
            width=100, height=22, font=("Inter", 10),
            fg_color="#18181b", button_color="#3f3f46", button_hover_color="#52525b", text_color="#f4f4f5"
        )
        self.tags_mode_opt.set(self.tags_display_mode)
        self.tags_mode_opt.pack(side="left")
        BMTToolTip(self.tags_mode_opt, "Display mode for labels: Full Names, Compact abbreviations (H, B1, VL, Dk), or None.")

        self.matrix_canvas = tk.Canvas(matrix_wrapper, bg="#27272a", highlightthickness=0)
        self.matrix_canvas.pack(fill="both", expand=True, padx=2, pady=(2, 4))

        self._matrix_tile_hitboxes = []
        self.matrix_canvas.bind("<Configure>", self._on_matrix_canvas_resize)
        self.matrix_canvas.bind("<Button-1>", self._on_matrix_canvas_click)
        self.matrix_canvas.bind("<Motion>", self._on_matrix_canvas_motion)

        # Bottom Saved Schemes Mini-Palettes with Prev/Next Navigation
        bottom_saved = ctk.CTkFrame(matrix_wrapper, fg_color="#18181b", height=38, corner_radius=6, border_width=1, border_color="#3f3f46")
        bottom_saved.pack(fill="x", side="bottom", pady=(2, 0))

        scheme_prev_btn = ctk.CTkButton(
            bottom_saved, text="◀", width=26, height=26,
            fg_color="#27272a", hover_color="#3f3f46", text_color="#07c9d7",
            font=("Inter", 12, "bold"), corner_radius=4,
            command=self._prev_scheme
        )
        scheme_prev_btn.pack(side="left", padx=(4, 2), pady=4)
        BMTToolTip(scheme_prev_btn, "Previous Color Scheme (◀)")

        self.saved_strips_frame = ctk.CTkScrollableFrame(bottom_saved, fg_color="transparent", orientation="horizontal", height=28)
        self.saved_strips_frame.pack(side="left", fill="both", expand=True, padx=2, pady=2)

        scheme_next_btn = ctk.CTkButton(
            bottom_saved, text="▶", width=26, height=26,
            fg_color="#27272a", hover_color="#3f3f46", text_color="#07c9d7",
            font=("Inter", 12, "bold"), corner_radius=4,
            command=self._next_scheme
        )
        scheme_next_btn.pack(side="right", padx=(2, 4), pady=4)
        BMTToolTip(scheme_next_btn, "Next Color Scheme (▶)")

        self._refresh_saved_strips()

    def _on_matrix_canvas_resize(self, event):
        if event.width > 50 and event.height > 50:
            self._matrix_w = event.width
            self._matrix_h = event.height
            self._render_matrix_canvas()

    def _on_tags_mode_changed(self, mode):
        self.tags_display_mode = mode
        self._render_matrix_canvas()

    def _render_matrix_canvas(self):
        if not hasattr(self, "matrix_canvas") or not self.matrix_canvas:
            return

        w = getattr(self, "_matrix_w", self.matrix_canvas.winfo_width())
        h = getattr(self, "_matrix_h", self.matrix_canvas.winfo_height())
        if w <= 50 or h <= 50:
            return

        self.matrix_canvas.delete("all")
        self._matrix_tile_hitboxes = []

        tag_mode = getattr(self, "tags_display_mode", "Full Names")

        pad = 8
        gap = 5

        if tag_mode == "Full Names":
            label_w = max(70, int(w * 0.15))
            header_h = max(22, int(h * 0.06))
            col_headers = SHADE_COLUMNS # ["Very Light", "Light", "Base", "Dark", "Very Dark", "Accent"]
            compact_row_names = ["Hair", "Body 1", "Body 2", "Special", "Cloth", "Weapon"]
        elif tag_mode == "Compact":
            label_w = max(28, int(w * 0.06))
            header_h = max(18, int(h * 0.05))
            col_headers = ["VL", "Lt", "Mid", "Dk", "VD", "Acc"]
            compact_row_names = ["H", "B1", "B2", "S", "C", "W"]
        else: # "None"
            label_w = 0
            header_h = 0
            col_headers = []
            compact_row_names = []

        avail_w = w - label_w - pad * 2 - gap * 5
        avail_h = h - header_h - pad * 2 - gap * 5

        sq_size = max(32, min(int(avail_w / 6), int(avail_h / 6)))

        total_w = label_w + 6 * sq_size + 5 * gap
        total_h = header_h + 6 * sq_size + 5 * gap

        start_x = max(pad, (w - total_w) // 2)
        start_y = max(pad, (h - total_h) // 2)

        # Draw Column Headers (if enabled)
        if col_headers:
            h_font_size = max(8, min(10, int(sq_size * 0.14)))
            for c_idx, col_name in enumerate(col_headers):
                cx = start_x + label_w + c_idx * (sq_size + gap) + sq_size // 2
                cy = start_y + header_h // 2
                self.matrix_canvas.create_text(
                    cx, cy,
                    text=col_name,
                    fill="#a1a1aa",
                    font=("Inter", h_font_size, "bold")
                )

        # Draw 6 Category Rows with Auto-Sized Perfect Square Tiles
        r_font_size = max(9, min(11, int(sq_size * 0.16)))
        for r_idx, (cat_name, channels_in_row) in enumerate(MATRIX_ROWS):
            ry = start_y + header_h + r_idx * (sq_size + gap)

            if compact_row_names:
                r_text = compact_row_names[r_idx] if r_idx < len(compact_row_names) else cat_name
                self.matrix_canvas.create_text(
                    start_x + label_w - (8 if tag_mode == "Compact" else 10), ry + sq_size // 2,
                    text=r_text,
                    anchor="e",
                    fill="#f4f4f5",
                    font=("Inter", r_font_size, "bold")
                )

            for c_idx, ch_key in enumerate(channels_in_row):
                rx = start_x + label_w + c_idx * (sq_size + gap)
                x0, y0, x1, y1 = rx, ry, rx + sq_size, ry + sq_size

                if ch_key is not None:
                    col_hex = self.active_palette.get(ch_key, "#2C2B31")
                    is_selected = (ch_key == self.selected_channel)
                    border_color = "#07c9d7" if is_selected else "#3f3f46"
                    border_width = 3 if is_selected else 1

                    self.matrix_canvas.create_rectangle(
                        x0, y0, x1, y1,
                        fill=col_hex,
                        outline=border_color,
                        width=border_width,
                        tags=("tile", ch_key)
                    )
                    self._matrix_tile_hitboxes.append((x0, y0, x1, y1, ch_key))
                else:
                    self.matrix_canvas.create_rectangle(
                        x0, y0, x1, y1,
                        fill="#18181b",
                        outline="#27272a",
                        width=1
                    )

    def _redraw_matrix_canvas(self):
        self._render_matrix_canvas()

    def _on_matrix_canvas_click(self, event):
        if not hasattr(self, "_matrix_tile_hitboxes"):
            return
        for x0, y0, x1, y1, ch_key in self._matrix_tile_hitboxes:
            if x0 <= event.x <= x1 and y0 <= event.y <= y1:
                self._on_tile_clicked(ch_key)
                break

    def _on_matrix_canvas_motion(self, event):
        if not hasattr(self, "_matrix_tile_hitboxes"):
            return
        is_over_tile = any(x0 <= event.x <= x1 and y0 <= event.y <= y1 for x0, y0, x1, y1, _ in self._matrix_tile_hitboxes)
        if is_over_tile:
            self.matrix_canvas.configure(cursor="hand2")
        else:
            self.matrix_canvas.configure(cursor="")

    def _refresh_saved_strips(self):
        if not hasattr(self, "saved_strips_frame") or not self.saved_strips_frame:
            return

        for w in self.saved_strips_frame.winfo_children():
            w.destroy()

        # Combine custom schemes (first) + official schemes
        all_to_show = []
        for cs in self.custom_schemes:
            all_to_show.append((cs[0], cs[1], cs[2], True))
        for os_item in self.all_schemes:
            all_to_show.append((os_item[0], os_item[1], os_item[2], False))

        for name, sid, pal, is_custom in all_to_show:
            border_c = "#07c9d7" if is_custom else "#3f3f46"
            card = ctk.CTkFrame(self.saved_strips_frame, fg_color="#27272a", corner_radius=4, border_width=1, border_color=border_c, cursor="hand2")
            card.pack(side="left", padx=3, pady=1)

            preview_cols = [
                pal.get("Hair", "#ECF185"), pal.get("Body1", "#3F985B"), pal.get("Body2", "#477860"),
                pal.get("Special", "#20FFC1"), pal.get("Cloth", "#B7C168"), pal.get("Weapon", "#54ABEB")
            ]
            strip = ctk.CTkFrame(card, fg_color="transparent", width=42, height=16)
            strip.pack(padx=2, pady=2)

            swatches = []
            for c in preview_cols:
                sw = ctk.CTkFrame(strip, width=6, height=14, fg_color=c, corner_radius=1)
                sw.pack(side="left", padx=0.5)
                swatches.append(sw)

            def make_click_cb(s, p, n):
                return lambda e: self._load_preset_palette(s, p, n)

            click_cb = make_click_cb(sid, pal, name)
            for w in (card, strip, *swatches):
                w.bind("<Button-1>", click_cb)
                w.bind("<Enter>", lambda e, cd=card, ic=is_custom: cd.configure(border_color="#07c9d7" if ic else "#52525b"))
                w.bind("<Leave>", lambda e, cd=card, ic=is_custom: cd.configure(border_color="#07c9d7" if ic else "#3f3f46"))

    # ── RIGHT PANEL (ENLARGED SPRITE PREVIEW & EXPORTERS) ─────────────────
    def _build_right_preview_panel(self):
        self.right_panel = ctk.CTkFrame(self.workspace, width=self.right_panel_width, fg_color="#27272a", corner_radius=6, border_width=1, border_color="#3f3f46")
        self.right_panel.pack(side="right", fill="both", padx=(2, 0))
        self.right_panel.pack_propagate(False)
        panel = self.right_panel

        # Header
        hdr = ctk.CTkFrame(panel, fg_color="transparent")
        hdr.pack(fill="x", padx=10, pady=(6, 2))
        ctk.CTkLabel(hdr, text="SPRITE PREVIEW", font=("Inter", 11, "bold"), text_color="#a1a1aa").pack(side="left")

        # Skin navigation row: [◀]  [Skin Name]  [▶]
        nav_row = ctk.CTkFrame(panel, fg_color="transparent")
        nav_row.pack(fill="x", padx=10, pady=(2, 2))
        nav_row.columnconfigure(1, weight=1)

        prev_btn = ctk.CTkButton(
            nav_row, text="◀", width=30, height=24,
            fg_color="#3f3f46", hover_color="#52525b", text_color="#f4f4f5",
            font=("Inter", 11, "bold"), corner_radius=4,
            command=self._prev_skin
        )
        prev_btn.grid(row=0, column=0, padx=(0, 4))
        BMTToolTip(prev_btn, "Previous Skin Template")

        self.skin_name_lbl = ctk.CTkLabel(
            nav_row,
            text=self._current_skin_display_name(),
            font=("Inter", 11, "bold"),
            text_color="#07c9d7",
            anchor="center"
        )
        self.skin_name_lbl.grid(row=0, column=1, sticky="ew")

        next_btn = ctk.CTkButton(
            nav_row, text="▶", width=30, height=24,
            fg_color="#3f3f46", hover_color="#52525b", text_color="#f4f4f5",
            font=("Inter", 11, "bold"), corner_radius=4,
            command=self._next_skin
        )
        next_btn.grid(row=0, column=2, padx=(4, 0))
        BMTToolTip(next_btn, "Next Skin Template")

        # Load SVG button
        load_svg_btn = ctk.CTkButton(
            panel, text="Load SVG...", width=100, height=22,
            fg_color="transparent", hover_color="#3f3f46",
            text_color="#a1a1aa", border_color="#3f3f46", border_width=1,
            font=("Inter", 10), corner_radius=4,
            command=self._load_custom_svg
        )
        load_svg_btn.pack(anchor="e", padx=10, pady=(0, 2))
        BMTToolTip(load_svg_btn, "Load a custom skin SVG file to preview color changes on it.")

        # Interactive Zoomable & Pannable Sprite Canvas
        self.sprite_canvas = tk.Canvas(panel, width=300, height=260, bg="#18181b", highlightthickness=1, highlightbackground="#3f3f46", cursor="fleur")
        self.sprite_canvas.pack(fill="both", expand=True, padx=10, pady=(2, 2))
        self.sprite_canvas.bind("<MouseWheel>", self._on_preview_mousewheel)
        self.sprite_canvas.bind("<Button-4>", lambda e: self._zoom_preview(1.15))
        self.sprite_canvas.bind("<Button-5>", lambda e: self._zoom_preview(1.0 / 1.15))
        self.sprite_canvas.bind("<ButtonPress-1>", self._on_preview_pan_start)
        self.sprite_canvas.bind("<B1-Motion>", self._on_preview_pan_drag)
        self.sprite_canvas.bind("<Double-Button-1>", lambda e: self._reset_preview_zoom())

        # Status & Zoom row
        zoom_row = ctk.CTkFrame(panel, fg_color="transparent")
        zoom_row.pack(fill="x", padx=12, pady=(1, 2))

        self.sprite_info_lbl = ctk.CTkLabel(zoom_row, text="30 active color channels", font=("Inter", 10), text_color="#a1a1aa")
        self.sprite_info_lbl.pack(side="left")

        zoom_ctrl_frame = ctk.CTkFrame(zoom_row, fg_color="transparent")
        zoom_ctrl_frame.pack(side="right")

        self.zoom_lbl = ctk.CTkLabel(zoom_ctrl_frame, text="100%", font=("Consolas", 9, "bold"), text_color="#07c9d7", width=34)
        self.zoom_lbl.pack(side="left", padx=(0, 2))

        reset_zoom_btn = ctk.CTkButton(
            zoom_ctrl_frame, text="↺ Reset", width=48, height=18,
            font=("Inter", 9), fg_color="#3f3f46", hover_color="#52525b",
            corner_radius=3, command=self._reset_preview_zoom
        )
        reset_zoom_btn.pack(side="left")
        BMTToolTip(reset_zoom_btn, "Reset zoom level to 100% and re-center sprite view.")

        # QoL Options Frame with Dynamic Expandable Highlight Controls
        self.qol_frame = ctk.CTkFrame(panel, fg_color="#18181b", corner_radius=6, border_width=1, border_color="#3f3f46")
        self.qol_frame.pack(fill="x", padx=10, pady=(2, 4))

        qol_row = ctk.CTkFrame(self.qol_frame, fg_color="transparent")
        qol_row.pack(fill="x", padx=8, pady=4)

        self._var_highlight_channel = tk.BooleanVar(value=False)
        self.ck_highlight = ctk.CTkCheckBox(
            qol_row,
            text="Highlight Channel",
            variable=self._var_highlight_channel,
            command=self._toggle_highlight,
            font=("Inter", 10, "bold"),
            text_color="#e4e4e7",
            fg_color="#07c9d7",
            hover_color="#06b6d4",
            border_color="#52525b",
            checkmark_color="#18181b",
            corner_radius=4,
            height=18,
            checkbox_width=15,
            checkbox_height=15
        )
        self.ck_highlight.pack(side="left", padx=(0, 12))
        BMTToolTip(self.ck_highlight, "Highlight Channel: Pulsing outline and subtle tint over active channel shapes.")

        self._var_auto_cycle = tk.BooleanVar(value=False)
        self.ck_auto_cycle = ctk.CTkCheckBox(
            qol_row,
            text="Auto-Cycle (3s)",
            variable=self._var_auto_cycle,
            command=self._toggle_auto_cycle,
            font=("Inter", 10),
            text_color="#e4e4e7",
            fg_color="#07c9d7",
            hover_color="#06b6d4",
            border_color="#52525b",
            checkmark_color="#18181b",
            corner_radius=4,
            height=18,
            checkbox_width=15,
            checkbox_height=15
        )
        self.ck_auto_cycle.pack(side="left")
        BMTToolTip(self.ck_auto_cycle, "Auto-Cycle: Automatically rotates through all skins every 3 seconds to preview palette across models.")

        # Expandable Highlight Customization Container (English with Color Pickers)
        self.hl_options_container = ctk.CTkFrame(self.qol_frame, fg_color="#202024", corner_radius=4, border_width=1, border_color="#333338")

        # Row 1: Outline Style & Outline Color + Picker Sync Swatch
        hl_row1 = ctk.CTkFrame(self.hl_options_container, fg_color="transparent")
        hl_row1.pack(fill="x", padx=6, pady=(4, 2))

        ctk.CTkLabel(hl_row1, text="Outline:", font=("Inter", 9, "bold"), text_color="#a1a1aa").pack(side="left", padx=(2, 4))
        self.hl_outline_opt = ctk.CTkOptionMenu(
            hl_row1,
            values=["Dotted", "Dashed", "Solid", "None"],
            command=self._on_hl_opt_changed,
            width=78, height=20, font=("Inter", 9),
            fg_color="#27272a", button_color="#3f3f46", button_hover_color="#52525b", text_color="#f4f4f5"
        )
        self.hl_outline_opt.set("Dotted")
        self.hl_outline_opt.pack(side="left", padx=(0, 6))
        BMTToolTip(self.hl_outline_opt, "Outline style for active channel highlight.")

        ctk.CTkLabel(hl_row1, text="Color:", font=("Inter", 9, "bold"), text_color="#a1a1aa").pack(side="left", padx=(2, 4))
        self.hl_outline_color_opt = ctk.CTkOptionMenu(
            hl_row1,
            values=["White", "Magenta", "Cyan", "Yellow", "Active", "Custom"],
            command=self._on_hl_outline_color_changed,
            width=72, height=20, font=("Inter", 9),
            fg_color="#27272a", button_color="#3f3f46", button_hover_color="#52525b", text_color="#f4f4f5"
        )
        self.hl_outline_color_opt.set("White")
        self.hl_outline_color_opt.pack(side="left", padx=(0, 4))
        BMTToolTip(self.hl_outline_color_opt, "Select outline color.")

        self.hl_outline_swatch_btn = ctk.CTkButton(
            hl_row1, text="", width=20, height=20,
            fg_color=self._hl_outline_color, border_width=1, border_color="#52525b",
            hover_color="#71717a", corner_radius=3, command=self._open_outline_color_picker
        )
        self.hl_outline_swatch_btn.pack(side="left")
        BMTToolTip(self.hl_outline_swatch_btn, "Click to pick a custom Outline Color (Visual Color Picker).")

        # Row 2: Fill Tint Color + Custom Swatch & Opacity Slider
        hl_row2 = ctk.CTkFrame(self.hl_options_container, fg_color="transparent")
        hl_row2.pack(fill="x", padx=6, pady=(2, 2))

        ctk.CTkLabel(hl_row2, text="Fill Tint:", font=("Inter", 9, "bold"), text_color="#a1a1aa").pack(side="left", padx=(2, 4))
        self.hl_tint_opt = ctk.CTkOptionMenu(
            hl_row2,
            values=["Magenta", "White", "Yellow", "Cyan", "Active", "Custom"],
            command=self._on_hl_tint_color_changed,
            width=78, height=20, font=("Inter", 9),
            fg_color="#27272a", button_color="#3f3f46", button_hover_color="#52525b", text_color="#f4f4f5"
        )
        self.hl_tint_opt.set("Magenta")
        self.hl_tint_opt.pack(side="left", padx=(0, 4))
        BMTToolTip(self.hl_tint_opt, "Tint color applied over active channel.")

        self.hl_fill_swatch_btn = ctk.CTkButton(
            hl_row2, text="", width=20, height=20,
            fg_color=self._hl_fill_color, border_width=1, border_color="#52525b",
            hover_color="#71717a", corner_radius=3, command=self._open_fill_color_picker
        )
        self.hl_fill_swatch_btn.pack(side="left", padx=(0, 6))
        BMTToolTip(self.hl_fill_swatch_btn, "Click to pick a custom Fill Tint Color (Visual Color Picker).")

        ctk.CTkLabel(hl_row2, text="Opacity:", font=("Inter", 9, "bold"), text_color="#a1a1aa").pack(side="left", padx=(2, 4))
        self.hl_opacity_slider = ctk.CTkSlider(
            hl_row2, from_=0, to=60, number_of_steps=30, height=10, width=65,
            progress_color="#07c9d7", command=self._on_hl_opacity_changed
        )
        self.hl_opacity_slider.set(20)
        self.hl_opacity_slider.pack(side="left", padx=(0, 2))
        self.hl_opacity_lbl = ctk.CTkLabel(hl_row2, text="20%", font=("Consolas", 8, "bold"), text_color="#07c9d7", width=26)
        self.hl_opacity_lbl.pack(side="left")
        BMTToolTip(self.hl_opacity_slider, "Fill overlay opacity (0% to 60%).")

        # Row 3: Pulse Speed
        hl_row3 = ctk.CTkFrame(self.hl_options_container, fg_color="transparent")
        hl_row3.pack(fill="x", padx=6, pady=(2, 4))

        ctk.CTkLabel(hl_row3, text="Pulse Speed:", font=("Inter", 9, "bold"), text_color="#a1a1aa").pack(side="left", padx=(2, 4))
        self.hl_speed_opt = ctk.CTkOptionMenu(
            hl_row3,
            values=["1.0s (Normal)", "0.5s (Fast)", "2.0s (Slow)", "Static (No Pulse)"],
            command=self._on_hl_speed_changed,
            width=115, height=20, font=("Inter", 9),
            fg_color="#27272a", button_color="#3f3f46", button_hover_color="#52525b", text_color="#f4f4f5"
        )
        self.hl_speed_opt.set("1.0s (Normal)")
        self.hl_speed_opt.pack(side="left")
        BMTToolTip(self.hl_speed_opt, "Pulsing animation speed.")

        # Warning Notice Banner
        warning_icon_path = self.assets_dir / "IconsNew" / "warning_24dp_E3E3E3_FILL0_wght500_GRAD0_opsz24.png"
        warning_frame = ctk.CTkFrame(panel, fg_color="#272318", border_width=1, border_color="#ca8a04", corner_radius=6)
        warning_frame.pack(fill="x", padx=10, pady=(2, 4))

        if warning_icon_path.exists():
            try:
                w_pil = Image.open(warning_icon_path).convert("RGBA")
                self._warning_img_ref = ctk.CTkImage(light_image=w_pil, dark_image=w_pil, size=(18, 18))
                w_icon_lbl = ctk.CTkLabel(warning_frame, image=self._warning_img_ref, text="")
                w_icon_lbl.pack(side="left", padx=(8, 2), pady=4)
            except Exception as e:
                print(f"[ColorModTool] Warning icon load error: {e}")

        w_text_lbl = ctk.CTkLabel(
            warning_frame,
            text="Only Battle Pass and Paid (Mammoth Coins) color schemes can be modified in-game.",
            font=("Inter", 9, "bold"),
            text_color="#fde047",
            justify="left",
            wraplength=230
        )
        w_text_lbl.pack(side="left", fill="x", expand=True, padx=(2, 8), pady=4)

        # Export Mod Source Button
        self.export_mod_src_btn = ctk.CTkButton(
            panel,
            text="Export Mod Source",
            font=("Inter", 11, "bold"),
            height=30,
            fg_color="#07c9d7",
            text_color="#18181b",
            hover_color="#06b6d4",
            corner_radius=6,
            command=self._open_export_target_dialog
        )
        self.export_mod_src_btn.pack(fill="x", padx=10, pady=(2, 6))
        BMTToolTip(self.export_mod_src_btn, "Select a Battle Pass or Paid color scheme to replace and export as a mod source.")

    # =========================================================================
    # 2D CANVAS PICKER & SLIDER INTERACTION
    # =========================================================================

    def _set_picker_mode(self, mode):
        self.picker_mode = mode
        for m, btn in self.picker_tab_btns.items():
            btn.configure(
                fg_color="#07c9d7" if m == mode else "transparent",
                text_color="#18181b" if m == mode else "#a1a1aa"
            )
        self._redraw_picker_canvases()

    def _set_slider_mode(self, smode):
        self.slider_mode = smode
        for m, btn in self.slider_tab_btns.items():
            btn.configure(
                fg_color="#07c9d7" if m == smode else "transparent",
                text_color="#18181b" if m == smode else "#a1a1aa"
            )
        self._build_model_sliders()

    def _redraw_picker_canvases(self):
        w_2d, h_2d = 155, 135
        img_2d = Image.new("RGB", (w_2d, h_2d))
        pixels_2d = img_2d.load()

        if self.picker_mode == "Hue":
            for y in range(h_2d):
                v = 1.0 - (y / float(h_2d - 1))
                for x in range(w_2d):
                    s = x / float(w_2d - 1)
                    r, g, b = colorsys.hsv_to_rgb(self.cur_h, s, v)
                    pixels_2d[x, y] = (int(r * 255), int(g * 255), int(b * 255))
        elif self.picker_mode == "Bright":
            for y in range(h_2d):
                h = y / float(h_2d - 1)
                for x in range(w_2d):
                    s = x / float(w_2d - 1)
                    r, g, b = colorsys.hsv_to_rgb(h, s, self.cur_v)
                    pixels_2d[x, y] = (int(r * 255), int(g * 255), int(b * 255))
        elif self.picker_mode == "Wheel":
            cx, cy = w_2d / 2.0, h_2d / 2.0
            radius = min(cx, cy) - 2
            import math
            for y in range(h_2d):
                for x in range(w_2d):
                    dx, dy = x - cx, y - cy
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist <= radius:
                        angle = (math.atan2(dy, dx) + math.pi) / (2 * math.pi)
                        s = dist / radius
                        r, g, b = colorsys.hsv_to_rgb(angle, s, self.cur_v)
                        pixels_2d[x, y] = (int(r * 255), int(g * 255), int(b * 255))
                    else:
                        pixels_2d[x, y] = (24, 24, 27)
        elif self.picker_mode == "Grey":
            for y in range(h_2d):
                val = int((1.0 - (y / float(h_2d - 1))) * 255)
                for x in range(w_2d):
                    pixels_2d[x, y] = (val, val, val)

        self._picker_img_ref = ImageTk.PhotoImage(img_2d)
        self.canvas_2d.delete("all")
        self.canvas_2d.create_image(0, 0, anchor="nw", image=self._picker_img_ref)

        if self.picker_mode == "Hue":
            cx = int(self.cur_s * (w_2d - 1))
            cy = int((1.0 - self.cur_v) * (h_2d - 1))
            self.canvas_2d.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, outline="#ffffff", width=2)
            self.canvas_2d.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, outline="#000000", width=1)

        # Vertical Slider Strip
        w_sl, h_sl = 18, 135
        img_sl = Image.new("RGB", (w_sl, h_sl))
        pix_sl = img_sl.load()
        for y in range(h_sl):
            h = y / float(h_sl - 1)
            r, g, b = colorsys.hsv_to_rgb(h, 1.0, 1.0) if self.picker_mode != "Bright" else colorsys.hsv_to_rgb(self.cur_h, self.cur_s, 1.0 - (y / float(h_sl - 1)))
            for x in range(w_sl):
                pix_sl[x, y] = (int(r * 255), int(g * 255), int(b * 255))

        self._slider_img_ref = ImageTk.PhotoImage(img_sl)
        self.slider_cv.delete("all")
        self.slider_cv.create_image(0, 0, anchor="nw", image=self._slider_img_ref)

        marker_y = int(self.cur_h * (h_sl - 1)) if self.picker_mode != "Bright" else int((1.0 - self.cur_v) * (h_sl - 1))
        self.slider_cv.create_rectangle(0, marker_y - 2, w_sl, marker_y + 2, outline="#ffffff", fill="#07c9d7")

    def _on_canvas_2d_click(self, event):
        self._handle_canvas_2d_input(event.x, event.y)

    def _on_canvas_2d_drag(self, event):
        self._handle_canvas_2d_input(event.x, event.y)

    def _handle_canvas_2d_input(self, x, y):
        w, h = 155, 135
        nx = max(0.0, min(1.0, x / float(w - 1)))
        ny = max(0.0, min(1.0, y / float(h - 1)))

        if self.picker_mode == "Hue":
            self.cur_s = nx
            self.cur_v = 1.0 - ny
        elif self.picker_mode == "Bright":
            self.cur_s = nx
            self.cur_h = ny
        elif self.picker_mode == "Grey":
            self.cur_s = 0.0
            self.cur_v = 1.0 - ny

        self._apply_current_color_to_active_cell()

    def _on_slider_cv_click(self, event):
        self._handle_slider_cv_input(event.y)

    def _on_slider_cv_drag(self, event):
        self._handle_slider_cv_input(event.y)

    def _handle_slider_cv_input(self, y):
        h = 135
        ny = max(0.0, min(1.0, y / float(h - 1)))
        if self.picker_mode != "Bright":
            self.cur_h = ny
        else:
            self.cur_v = 1.0 - ny
        self._apply_current_color_to_active_cell()

    def _sync_picker_from_color(self, hex_color):
        r, g, b = hex_to_rgb(hex_color)
        self.cur_h, self.cur_s, self.cur_v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        self._redraw_picker_canvases()
        self.swatch_preview.configure(fg_color=hex_color)
        self.hex_entry.delete(0, "end")
        self.hex_entry.insert(0, hex_color)
        self._update_slider_values()

    def _set_slider_mode(self, mode):
        self.slider_mode = mode
        for smode, btn in self.slider_tab_btns.items():
            btn.configure(
                fg_color="#07c9d7" if smode == mode else "transparent",
                text_color="#18181b" if smode == mode else "#a1a1aa"
            )
        self._build_model_sliders()

    def _update_slider_values(self):
        if self.slider_mode == "HSB" and hasattr(self, "s_h"):
            self.s_h.set(int(self.cur_h * 360)); self.s_h._val_lbl.configure(text=str(int(self.cur_h * 360)))
            self.s_s.set(int(self.cur_s * 100)); self.s_s._val_lbl.configure(text=str(int(self.cur_s * 100)))
            self.s_b.set(int(self.cur_v * 100)); self.s_b._val_lbl.configure(text=str(int(self.cur_v * 100)))
        elif self.slider_mode == "RGB" and hasattr(self, "s_r"):
            r, g, b = hex_to_rgb(self.active_palette.get(self.selected_channel, "#2C2B31"))
            self.s_r.set(r); self.s_r._val_lbl.configure(text=str(r))
            self.s_g.set(g); self.s_g._val_lbl.configure(text=str(g))
            self.s_b_rgb.set(b); self.s_b_rgb._val_lbl.configure(text=str(b))
        elif self.slider_mode == "HSL" and hasattr(self, "s_hsl_h"):
            r, g, b = hex_to_rgb(self.active_palette.get(self.selected_channel, "#2C2B31"))
            h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
            self.s_hsl_h.set(int(h * 360)); self.s_hsl_h._val_lbl.configure(text=str(int(h * 360)))
            self.s_hsl_s.set(int(s * 100)); self.s_hsl_s._val_lbl.configure(text=str(int(s * 100)))
            self.s_hsl_l.set(int(l * 100)); self.s_hsl_l._val_lbl.configure(text=str(int(l * 100)))
        elif self.slider_mode == "CMYK" and hasattr(self, "s_cmyk_c"):
            r, g, b = hex_to_rgb(self.active_palette.get(self.selected_channel, "#2C2B31"))
            c, m, y, k = rgb_to_cmyk(r, g, b)
            self.s_cmyk_c.set(c); self.s_cmyk_c._val_lbl.configure(text=str(c))
            self.s_cmyk_m.set(m); self.s_cmyk_m._val_lbl.configure(text=str(m))
            self.s_cmyk_y.set(y); self.s_cmyk_y._val_lbl.configure(text=str(y))
            self.s_cmyk_k.set(k); self.s_cmyk_k._val_lbl.configure(text=str(k))

    def _on_hsb_slider_change(self):
        self.cur_h = self.s_h.get() / 360.0
        self.cur_s = self.s_s.get() / 100.0
        self.cur_v = self.s_b.get() / 100.0
        self.s_h._val_lbl.configure(text=str(int(self.s_h.get())))
        self.s_s._val_lbl.configure(text=str(int(self.s_s.get())))
        self.s_b._val_lbl.configure(text=str(int(self.s_b.get())))
        self._apply_current_color_to_active_cell()

    def _on_rgb_slider_change(self):
        r, g, b = int(self.s_r.get()), int(self.s_g.get()), int(self.s_b_rgb.get())
        self.s_r._val_lbl.configure(text=str(r))
        self.s_g._val_lbl.configure(text=str(g))
        self.s_b_rgb._val_lbl.configure(text=str(b))
        hex_c = rgb_to_hex((r, g, b))
        self.cur_h, self.cur_s, self.cur_v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        self._apply_color_to_active_cell(hex_c)

    def _on_hsl_slider_change(self):
        h = self.s_hsl_h.get() / 360.0
        s = self.s_hsl_s.get() / 100.0
        l = self.s_hsl_l.get() / 100.0
        self.s_hsl_h._val_lbl.configure(text=str(int(self.s_hsl_h.get())))
        self.s_hsl_s._val_lbl.configure(text=str(int(self.s_hsl_s.get())))
        self.s_hsl_l._val_lbl.configure(text=str(int(self.s_hsl_l.get())))
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        hex_c = rgb_to_hex((int(round(r * 255)), int(round(g * 255)), int(round(b * 255))))
        self.cur_h, self.cur_s, self.cur_v = colorsys.rgb_to_hsv(r, g, b)
        self._apply_color_to_active_cell(hex_c)

    def _on_cmyk_slider_change(self):
        c = int(self.s_cmyk_c.get())
        m = int(self.s_cmyk_m.get())
        y = int(self.s_cmyk_y.get())
        k = int(self.s_cmyk_k.get())
        self.s_cmyk_c._val_lbl.configure(text=str(c))
        self.s_cmyk_m._val_lbl.configure(text=str(m))
        self.s_cmyk_y._val_lbl.configure(text=str(y))
        self.s_cmyk_k._val_lbl.configure(text=str(k))
        r, g, b = cmyk_to_rgb(c, m, y, k)
        hex_c = rgb_to_hex((r, g, b))
        self.cur_h, self.cur_s, self.cur_v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        self._apply_color_to_active_cell(hex_c)

    def _apply_current_color_to_active_cell(self):
        r, g, b = colorsys.hsv_to_rgb(self.cur_h, self.cur_s, self.cur_v)
        hex_c = rgb_to_hex((int(r * 255), int(g * 255), int(b * 255)))
        self._apply_color_to_active_cell(hex_c)

    def _apply_color_to_active_cell(self, hex_color):
        self.active_palette[self.selected_channel] = hex_color
        self.swatch_preview.configure(fg_color=hex_color)
        self.hex_entry.delete(0, "end")
        self.hex_entry.insert(0, hex_color)

        if hasattr(self, "matrix_canvas"):
            self._redraw_matrix_canvas()

        self._redraw_picker_canvases()
        self._render_bodvar_preview()

    def _on_hex_entry_submit(self, event=None):
        txt = self.hex_entry.get().strip().upper()
        if not txt.startswith("#"):
            txt = "#" + txt
        if re.match(r"^#[0-9A-F]{6}$", txt):
            self._sync_picker_from_color(txt)
            self._apply_color_to_active_cell(txt)

    def _copy_current_hex(self):
        txt = self.hex_entry.get().strip()
        self.parent.clipboard_clear()
        self.parent.clipboard_append(txt)

    # =========================================================================
    # SEARCHABLE SCHEME DROPDOWN POPUP (SHOWING ~10 ITEMS WITH MINI PREVIEWS)
    # =========================================================================

    def _update_scheme_selector_btn(self):
        if hasattr(self, "btn_scheme_name_lbl"):
            self.btn_scheme_name_lbl.configure(text=self.selected_scheme_name or "Black")
        if hasattr(self, "btn_swatches") and self.btn_swatches:
            p_cols = [
                self.active_palette.get("Hair", "#ECF185"),
                self.active_palette.get("Body1", "#3F985B"),
                self.active_palette.get("Body2", "#477860"),
                self.active_palette.get("Special", "#20FFC1"),
                self.active_palette.get("Cloth", "#B7C168"),
                self.active_palette.get("Weapon", "#54ABEB")
            ]
            for sw, col in zip(self.btn_swatches, p_cols):
                sw.configure(fg_color=col)

    def _toggle_scheme_dropdown(self):
        if hasattr(self, "_scheme_dropdown_win") and self._scheme_dropdown_win and self._scheme_dropdown_win.winfo_exists():
            self._close_scheme_dropdown()
        else:
            self._open_scheme_dropdown()

    def _close_scheme_dropdown(self):
        if hasattr(self, "_scheme_dropdown_win") and self._scheme_dropdown_win:
            try:
                self._scheme_dropdown_win.destroy()
            except Exception:
                pass
            self._scheme_dropdown_win = None

    def _open_scheme_dropdown(self):
        self._close_scheme_dropdown()

        win = ctk.CTkToplevel(self.master_frame)
        self._scheme_dropdown_win = win
        win.overrideredirect(True)
        win.attributes("-topmost", True)

        self.master_frame.update_idletasks()
        try:
            bx = self.scheme_selector_btn.winfo_rootx()
            by = self.scheme_selector_btn.winfo_rooty() + self.scheme_selector_btn.winfo_height() + 3
        except Exception:
            bx, by = 100, 100

        bw, bh = 280, 380

        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        if bx + bw > sw:
            bx = sw - bw - 10
        if by + bh > sh:
            by = max(10, self.scheme_selector_btn.winfo_rooty() - bh - 3)

        win.geometry(f"{bw}x{bh}+{bx}+{by}")

        card = ctk.CTkFrame(
            win,
            fg_color="#18181b",
            corner_radius=8,
            border_width=1,
            border_color="#07c9d7"
        )
        card.pack(fill="both", expand=True)

        # Quick Search Bar
        search_box = ctk.CTkFrame(card, fg_color="transparent")
        search_box.pack(fill="x", padx=8, pady=(8, 4))

        self.scheme_search_entry = ctk.CTkEntry(
            search_box,
            placeholder_text="Search scheme (e.g. Red, Gala)...",
            height=28,
            fg_color="#27272a",
            border_color="#3f3f46",
            text_color="#f4f4f5",
            font=("Inter", 11)
        )
        self.scheme_search_entry.pack(fill="x")
        self.scheme_search_entry.focus_set()
        self.scheme_search_entry.bind("<KeyRelease>", self._on_search_scheme_changed)

        # Content container with Canvas & Scrollbar
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=6, pady=(2, 6))

        self._dd_row_h = 32
        self._dd_hovered_idx = -1
        self._dd_row_hitboxes = []
        self._dd_del_hitboxes = []

        self._dd_canvas = tk.Canvas(
            content_frame,
            bg="#18181b",
            highlightthickness=0,
            yscrollincrement=8
        )
        self._dd_scrollbar = ctk.CTkScrollbar(
            content_frame,
            orientation="vertical",
            command=self._dd_canvas.yview,
            button_color="#3f3f46",
            button_hover_color="#52525b",
            fg_color="transparent",
            width=10
        )
        self._dd_canvas.configure(yscrollcommand=self._dd_scrollbar.set)

        self._dd_canvas.pack(side="left", fill="both", expand=True)
        self._dd_scrollbar.pack(side="right", fill="y", padx=(2, 0))

        # Event bindings for instant interaction & fast scrolling
        self._dd_canvas.bind("<Motion>", self._on_dd_mouse_move)
        self._dd_canvas.bind("<Leave>", self._on_dd_mouse_leave)
        self._dd_canvas.bind("<Button-1>", self._on_dd_mouse_click)
        self._dd_canvas.bind("<MouseWheel>", self._on_dd_mouse_wheel)
        self._dd_scrollbar.bind("<MouseWheel>", self._on_dd_mouse_wheel)
        self.scheme_search_entry.bind("<MouseWheel>", self._on_dd_mouse_wheel)
        card.bind("<MouseWheel>", self._on_dd_mouse_wheel)
        win.bind("<MouseWheel>", self._on_dd_mouse_wheel)
        win.bind("<Escape>", lambda e: self._close_scheme_dropdown())
        win.bind("<FocusOut>", self._on_dropdown_focus_out)

        self._render_dropdown_canvas()

    def _on_dropdown_focus_out(self, event):
        if not hasattr(self, "_scheme_dropdown_win") or not self._scheme_dropdown_win:
            return
        self.master_frame.after(120, self._check_dropdown_focus)

    def _check_dropdown_focus(self):
        if not hasattr(self, "_scheme_dropdown_win") or not self._scheme_dropdown_win:
            return
        try:
            focus_widget = self.master_frame.focus_get()
            if focus_widget is None or str(self._scheme_dropdown_win) not in str(focus_widget):
                self._close_scheme_dropdown()
        except Exception:
            pass

    def _on_search_scheme_changed(self, event=None):
        if not hasattr(self, "_scheme_dropdown_win") or not self._scheme_dropdown_win:
            return
        self._dd_hovered_idx = -1
        self._dd_canvas.yview_moveto(0)
        self._render_dropdown_canvas()

    def _render_dropdown_canvas(self):
        if not hasattr(self, "_dd_canvas") or not self._dd_canvas:
            return
        self._dd_canvas.delete("all")
        self._dd_row_hitboxes = []
        self._dd_del_hitboxes = []

        q = ""
        if hasattr(self, "scheme_search_entry") and self.scheme_search_entry:
            try:
                q = self.scheme_search_entry.get().strip().lower()
            except Exception:
                pass

        matched_custom = []
        for cs in self.custom_schemes:
            name, sid, pal = cs[0], cs[1], cs[2]
            if not q or q in name.lower() or q in str(sid).lower():
                matched_custom.append((name, sid, pal, True))

        matched_official = []
        for os_item in self.all_schemes:
            name, sid, pal = os_item[0], os_item[1], os_item[2]
            if not q or q in name.lower() or q in str(sid).lower():
                matched_official.append((name, sid, pal, False))

        if not matched_custom and not matched_official:
            self._dd_canvas.configure(scrollregion=(0, 0, 250, 100))
            self._dd_canvas.create_text(
                125, 50,
                text="No color schemes found",
                fill="#71717a",
                font=("Inter", 11)
            )
            return

        w = 252
        cur_y = 4
        item_counter = 0

        # Section 1: CUSTOM SCHEMES (if any match)
        if matched_custom:
            self._dd_canvas.create_text(
                8, cur_y + 10,
                text=f"CUSTOM SCHEMES ({len(matched_custom)})",
                anchor="w",
                fill="#07c9d7",
                font=("Inter", 9, "bold")
            )
            self._dd_canvas.create_line(130, cur_y + 10, w - 8, cur_y + 10, fill="#27272a", width=1)
            cur_y += 20

            for name, sid, pal, is_custom in matched_custom:
                y0 = cur_y
                y1 = y0 + self._dd_row_h
                is_active = (name == self.selected_scheme_name)
                is_hover = (item_counter == self._dd_hovered_idx)

                bg_col = "#27272a" if (is_active or is_hover) else "#18181b"
                if bg_col != "#18181b":
                    self._dd_canvas.create_rectangle(2, y0+1, w, y1-1, fill=bg_col, outline="", tags=("row", f"item_{item_counter}"))

                # 6 swatches
                p_colors = [
                    pal.get("Hair", "#ECF185"), pal.get("Body1", "#3F985B"), pal.get("Body2", "#477860"),
                    pal.get("Special", "#20FFC1"), pal.get("Cloth", "#B7C168"), pal.get("Weapon", "#54ABEB")
                ]
                for s_i, c in enumerate(p_colors):
                    sx = 8 + s_i * 6
                    self._dd_canvas.create_rectangle(sx, y0+8, sx+5, y0+24, fill=c, outline="", tags=("row", f"item_{item_counter}"))

                # Name
                text_col = "#07c9d7" if is_active else "#f4f4f5"
                weight = "bold" if is_active else "normal"
                self._dd_canvas.create_text(
                    52, y0 + 16,
                    text=name,
                    anchor="w",
                    fill=text_col,
                    font=("Inter", 10, weight),
                    tags=("row", f"item_{item_counter}")
                )

                # Delete Button (Red ✕)
                del_x0, del_x1 = w - 24, w - 4
                self._dd_canvas.create_text(
                    w - 14, y0 + 16,
                    text="✕",
                    anchor="center",
                    fill="#ef4444" if is_hover else "#71717a",
                    font=("Inter", 10, "bold"),
                    tags=("row", f"del_{item_counter}")
                )
                self._dd_del_hitboxes.append((del_x0, y0 + 4, del_x1, y1 - 4, name, sid))

                self._dd_row_hitboxes.append((y0, y1, name, sid, pal, True, item_counter))
                cur_y += self._dd_row_h
                item_counter += 1

            cur_y += 6

        # Section 2: OFFICIAL SCHEMES
        if matched_official:
            self._dd_canvas.create_text(
                8, cur_y + 10,
                text=f"OFFICIAL SCHEMES ({len(matched_official)})",
                anchor="w",
                fill="#a1a1aa",
                font=("Inter", 9, "bold")
            )
            self._dd_canvas.create_line(135, cur_y + 10, w - 8, cur_y + 10, fill="#27272a", width=1)
            cur_y += 20

            for name, sid, pal, is_custom in matched_official:
                y0 = cur_y
                y1 = y0 + self._dd_row_h
                is_active = (name == self.selected_scheme_name)
                is_hover = (item_counter == self._dd_hovered_idx)

                bg_col = "#27272a" if (is_active or is_hover) else "#18181b"
                if bg_col != "#18181b":
                    self._dd_canvas.create_rectangle(2, y0+1, w, y1-1, fill=bg_col, outline="", tags=("row", f"item_{item_counter}"))

                # 6 swatches
                p_colors = [
                    pal.get("Hair", "#ECF185"), pal.get("Body1", "#3F985B"), pal.get("Body2", "#477860"),
                    pal.get("Special", "#20FFC1"), pal.get("Cloth", "#B7C168"), pal.get("Weapon", "#54ABEB")
                ]
                for s_i, c in enumerate(p_colors):
                    sx = 8 + s_i * 6
                    self._dd_canvas.create_rectangle(sx, y0+8, sx+5, y0+24, fill=c, outline="", tags=("row", f"item_{item_counter}"))

                # Name
                text_col = "#07c9d7" if is_active else "#f4f4f5"
                weight = "bold" if is_active else "normal"
                self._dd_canvas.create_text(
                    52, y0 + 16,
                    text=name,
                    anchor="w",
                    fill=text_col,
                    font=("Inter", 10, weight),
                    tags=("row", f"item_{item_counter}")
                )

                # ID badge
                id_col = "#07c9d7" if is_active else "#71717a"
                self._dd_canvas.create_text(
                    w - 8, y0 + 16,
                    text=f"#{sid}",
                    anchor="e",
                    fill=id_col,
                    font=("Consolas", 9),
                    tags=("row", f"item_{item_counter}")
                )

                self._dd_row_hitboxes.append((y0, y1, name, sid, pal, False, item_counter))
                cur_y += self._dd_row_h
                item_counter += 1

        self._dd_canvas.configure(scrollregion=(0, 0, 250, cur_y + 8))

    def _on_dd_mouse_move(self, event):
        if not hasattr(self, "_dd_canvas") or not self._dd_canvas:
            return
        canvas_y = self._dd_canvas.canvasy(event.y)
        new_hover = -1
        for y0, y1, name, sid, pal, is_custom, item_idx in self._dd_row_hitboxes:
            if y0 <= canvas_y <= y1:
                new_hover = item_idx
                break

        if self._dd_hovered_idx != new_hover:
            self._dd_hovered_idx = new_hover
            self._render_dropdown_canvas()

    def _on_dd_mouse_leave(self, event):
        if self._dd_hovered_idx != -1:
            self._dd_hovered_idx = -1
            self._render_dropdown_canvas()

    def _on_dd_mouse_click(self, event):
        if not hasattr(self, "_dd_canvas") or not self._dd_canvas:
            return
        canvas_x = self._dd_canvas.canvasx(event.x)
        canvas_y = self._dd_canvas.canvasy(event.y)

        # 1. Check delete button hitboxes first
        for dx0, dy0, dx1, dy1, name, sid in self._dd_del_hitboxes:
            if dx0 <= canvas_x <= dx1 and dy0 <= canvas_y <= dy1:
                self._delete_custom_scheme(name, sid)
                return

        # 2. Check row selection hitboxes
        for y0, y1, name, sid, pal, is_custom, item_idx in self._dd_row_hitboxes:
            if y0 <= canvas_y <= y1:
                self._on_scheme_selected(name)
                self._close_scheme_dropdown()
                return

    def _on_dd_mouse_wheel(self, event):
        if hasattr(self, "_dd_canvas") and self._dd_canvas and event.delta:
            units = int(-1 * (event.delta / 120) * 3)
            if units == 0:
                units = -1 if event.delta > 0 else 1
            self._dd_canvas.yview_scroll(units, "units")

    # =========================================================================
    # 6x6 MATRIX TILE SELECTION & ROW ACTIONS
    # =========================================================================

    def _on_tile_clicked(self, channel_key):
        self.selected_channel = channel_key
        self._render_matrix_canvas()
        cur_hex = self.active_palette.get(channel_key, "#2C2B31")
        self._sync_picker_from_color(cur_hex)
        if getattr(self, "_var_highlight_channel", None) and self._var_highlight_channel.get():
            self._render_skin_preview()

    def _on_scheme_selected(self, scheme_display_name):
        found = False
        for item in self.custom_schemes:
            name, sid, pal = item[0], item[1], item[2]
            if name == scheme_display_name:
                self.selected_scheme_id = sid
                self.selected_scheme_name = name
                costume_name = self._current_skin_name()
                self.active_palette = self._get_effective_palette(costume_name, sid, pal)
                found = True
                break

        if not found:
            for name, sid, pal in self.all_schemes:
                if name == scheme_display_name:
                    self.selected_scheme_id = sid
                    self.selected_scheme_name = name
                    costume_name = self._current_skin_name()
                    self.active_palette = self._get_effective_palette(costume_name, sid, pal)
                    found = True
                    break

        if found:
            self._update_scheme_selector_btn()
            self._refresh_matrix_tiles()
            self._sync_picker_from_color(self.active_palette.get(self.selected_channel, "#2C2B31"))
            self._render_skin_preview()

    def _load_preset_palette(self, sid, pal, name):
        self.selected_scheme_id = sid
        self.selected_scheme_name = name
        costume_name = self._current_skin_name()
        self.active_palette = self._get_effective_palette(costume_name, sid, pal)
        self._update_scheme_selector_btn()
        self._refresh_matrix_tiles()
        self._sync_picker_from_color(self.active_palette.get(self.selected_channel, "#2C2B31"))
        self._render_skin_preview()

    # =========================================================================
    # BATCH OPERATIONS (AUTO SHADE, HARMONIZE, RANDOMIZE, INVERT, GREY, RESET)
    # =========================================================================

    def _refresh_matrix_tiles(self):
        if hasattr(self, "matrix_canvas"):
            self._redraw_matrix_canvas()

    def _action_auto_shade_all(self):
        factors = {"VL": 0.50, "Lt": 0.25, "": 0.0, "Dk": -0.22, "VD": -0.42, "Acc": 0.18}
        intensity = self.shading_slider.get() if hasattr(self, "shading_slider") else 1.0
        for cat_name, channels in MATRIX_ROWS:
            base_ch = next((c for c in channels if c and not any(c.endswith(k) for k in ["VL", "Lt", "Dk", "VD", "Acc"])), channels[0])
            if not base_ch:
                continue
            base_hex = self.active_palette.get(base_ch, "#808080")
            r, g, b = hex_to_rgb(base_hex)
            h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)

            for ch in channels:
                if ch is None:
                    continue
                shade_key = next((sk for sk in ["VL", "Lt", "Dk", "VD", "Acc"] if ch.endswith(sk)), "")
                f = factors.get(shade_key, 0.0) * intensity
                new_v = max(0.04, min(0.98, v + f))
                new_s = max(0.04, min(0.98, s * (1.0 + f * 0.4)))
                nr, ng, nb = colorsys.hsv_to_rgb(h, new_s, new_v)
                self.active_palette[ch] = rgb_to_hex((int(nr * 255), int(ng * 255), int(nb * 255)))

        self._refresh_matrix_tiles()
        self._sync_picker_from_color(self.active_palette.get(self.selected_channel, "#2C2B31"))
        self._render_skin_preview()

    def _action_harmonize(self):
        base_hex = self.active_palette.get("Body1", self.active_palette.get("Hair", "#3F985B"))
        r, g, b = hex_to_rgb(base_hex)
        base_h, base_s, base_v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)

        harmonic_offsets = {
            "Hair": 0.0,
            "Body1": 0.0,
            "Body2": 0.08,
            "Special": 0.50,
            "Cloth": 0.42,
            "Weapon": 0.58
        }
        factors = {"VL": 0.48, "Lt": 0.24, "": 0.0, "Dk": -0.22, "VD": -0.42, "Acc": 0.20}

        for cat_name, channels in MATRIX_ROWS:
            h_offset = harmonic_offsets.get(cat_name, 0.0)
            target_h = (base_h + h_offset) % 1.0
            for ch in channels:
                if ch is None:
                    continue
                shade_key = next((sk for sk in ["VL", "Lt", "Dk", "VD", "Acc"] if ch.endswith(sk)), "")
                f = factors.get(shade_key, 0.0)
                new_v = max(0.04, min(0.98, base_v + f))
                new_s = max(0.04, min(0.98, base_s * (1.0 + f * 0.3)))
                nr, ng, nb = colorsys.hsv_to_rgb(target_h, new_s, new_v)
                self.active_palette[ch] = rgb_to_hex((int(nr * 255), int(ng * 255), int(nb * 255)))

        self._refresh_matrix_tiles()
        self._sync_picker_from_color(self.active_palette.get(self.selected_channel, "#2C2B31"))
        self._render_skin_preview()

    def _action_randomize(self):
        import random
        anchor_h = random.random()
        offsets = [0.0, 0.08, 0.50, 0.42, 0.58, random.random()]
        factors = {"VL": 0.48, "Lt": 0.24, "": 0.0, "Dk": -0.22, "VD": -0.42, "Acc": 0.20}

        for row_idx, (cat_name, channels) in enumerate(MATRIX_ROWS):
            h = (anchor_h + offsets[row_idx % len(offsets)]) % 1.0
            s = random.uniform(0.45, 0.85)
            v = random.uniform(0.45, 0.75)

            for ch in channels:
                if ch is None:
                    continue
                shade_key = next((sk for sk in ["VL", "Lt", "Dk", "VD", "Acc"] if ch.endswith(sk)), "")
                f = factors.get(shade_key, 0.0)
                new_v = max(0.04, min(0.98, v + f))
                new_s = max(0.04, min(0.98, s * (1.0 + f * 0.3)))
                nr, ng, nb = colorsys.hsv_to_rgb(h, new_s, new_v)
                self.active_palette[ch] = rgb_to_hex((int(nr * 255), int(ng * 255), int(nb * 255)))

        self._refresh_matrix_tiles()
        self._sync_picker_from_color(self.active_palette.get(self.selected_channel, "#2C2B31"))
        self._render_skin_preview()

    def _action_hue_shift(self, deg):
        shift = deg / 360.0
        for ch in ALL_CHANNELS_LIST:
            hex_c = self.active_palette.get(ch, "#2C2B31")
            r, g, b = hex_to_rgb(hex_c)
            h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            h = (h + shift) % 1.0
            nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
            self.active_palette[ch] = rgb_to_hex((int(nr * 255), int(ng * 255), int(nb * 255)))

        self._refresh_matrix_tiles()
        self._sync_picker_from_color(self.active_palette.get(self.selected_channel, "#2C2B31"))
        self._render_skin_preview()

    def _action_bright_shift(self, delta):
        for ch in ALL_CHANNELS_LIST:
            hex_c = self.active_palette.get(ch, "#2C2B31")
            r, g, b = hex_to_rgb(hex_c)
            h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            v = max(0.02, min(0.98, v + delta))
            nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
            self.active_palette[ch] = rgb_to_hex((int(nr * 255), int(ng * 255), int(nb * 255)))

        self._refresh_matrix_tiles()
        self._sync_picker_from_color(self.active_palette.get(self.selected_channel, "#2C2B31"))
        self._render_skin_preview()

    def _action_saturate_shift(self, delta):
        for ch in ALL_CHANNELS_LIST:
            hex_c = self.active_palette.get(ch, "#2C2B31")
            r, g, b = hex_to_rgb(hex_c)
            h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            s = max(0.0, min(1.0, s + delta))
            nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
            self.active_palette[ch] = rgb_to_hex((int(nr * 255), int(ng * 255), int(nb * 255)))

        self._refresh_matrix_tiles()
        self._sync_picker_from_color(self.active_palette.get(self.selected_channel, "#2C2B31"))
        self._render_skin_preview()

    def _action_invert(self):
        for ch in ALL_CHANNELS_LIST:
            hex_c = self.active_palette.get(ch, "#2C2B31")
            r, g, b = hex_to_rgb(hex_c)
            self.active_palette[ch] = rgb_to_hex((255 - r, 255 - g, 255 - b))

        self._refresh_matrix_tiles()
        self._sync_picker_from_color(self.active_palette.get(self.selected_channel, "#2C2B31"))
        self._render_skin_preview()

    def _action_greyscale(self):
        for ch in ALL_CHANNELS_LIST:
            hex_c = self.active_palette.get(ch, "#2C2B31")
            r, g, b = hex_to_rgb(hex_c)
            grey = int(0.299 * r + 0.587 * g + 0.114 * b)
            self.active_palette[ch] = rgb_to_hex((grey, grey, grey))

        self._refresh_matrix_tiles()
        self._sync_picker_from_color(self.active_palette.get(self.selected_channel, "#2C2B31"))
        self._render_skin_preview()

    def _action_reset_palette(self):
        costume_name = self._current_skin_name()
        self.active_palette = self._get_effective_palette(costume_name, self.selected_scheme_id)
        self._refresh_matrix_tiles()
        self._sync_picker_from_color(self.active_palette.get(self.selected_channel, "#2C2B31"))
        self._render_skin_preview()

    def _on_shading_slider_change(self, val):
        pct = int(float(val) * 100)
        self.shading_lbl.configure(text=f"{pct}%")
        self._action_auto_shade_all()

    # =========================================================================
    # DYNAMIC MULTI-SKIN SVG PREVIEW & ENGINE INTEGRATION
    # =========================================================================

    def _current_skin_name(self) -> str:
        if self.skin_svgs and self.skin_svg_index < len(self.skin_svgs):
            return self.skin_svgs[self.skin_svg_index].stem
        return "Viking"

    def _current_skin_display_name(self) -> str:
        stem = self._current_skin_name()
        if stem in ("Viking", "Bodvar"):
            return "Classic Bödvar"
        alias_map = {
            'BP5Orion': 'EpicOrion',
            'DianaEpic': 'EpicDiana',
            'EpicNinetails': 'EpicYumiko',
            'EpicRagnir': 'EpicDragon',
        }
        c_key = alias_map.get(stem, stem)
        if hasattr(self, 'costumes_data') and c_key in self.costumes_data:
            c_disp = self.costumes_data[c_key].get("display_name")
            if c_disp and c_disp != c_key:
                return c_disp
        if stem in DEFAULT_COSTUME_DISPLAY_NAMES:
            return DEFAULT_COSTUME_DISPLAY_NAMES[stem]
        if c_key in DEFAULT_COSTUME_DISPLAY_NAMES:
            return DEFAULT_COSTUME_DISPLAY_NAMES[c_key]
        return stem

    def _prev_skin(self):
        if not self.skin_svgs:
            return
        self.skin_svg_index = (self.skin_svg_index - 1) % len(self.skin_svgs)
        self._on_skin_changed()

    def _next_skin(self):
        if not self.skin_svgs:
            return
        self.skin_svg_index = (self.skin_svg_index + 1) % len(self.skin_svgs)
        self._on_skin_changed()

    def _load_custom_svg(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Load Skin SVG",
            filetypes=[("SVG files", "*.svg"), ("All files", "*.*")]
        )
        if not path:
            return
        p = Path(path)
        if p not in self.skin_svgs:
            self.skin_svgs.append(p)
        self.skin_svg_index = self.skin_svgs.index(p)
        self._on_skin_changed()

    def _on_skin_changed(self):
        if hasattr(self, 'skin_name_lbl'):
            self.skin_name_lbl.configure(text=self._current_skin_display_name())
        costume_name = self._current_skin_name()
        self.active_palette = self._get_effective_palette(costume_name, self.selected_scheme_id, self.active_palette)
        self._refresh_matrix_tiles()
        self._sync_picker_from_color(self.active_palette.get(self.selected_channel, "#2C2B31"))
        self._trigger_sprite_pop_animation()

    def _get_costume_defines(self, costume_name: str, svg_path: Path = None) -> dict:
        """
        Returns a mapping of {src_hex_upper: channel_name} for the given costume.
        First checks Game.swz costumeTypes, then DEFAULT_COSTUME_DEFINES.
        If still not found, inspects SVG fill colors to match against known costume definitions.
        """
        if hasattr(self, 'costumes_data') and costume_name in self.costumes_data:
            return dict(self.costumes_data[costume_name]["defines"])

        if costume_name in DEFAULT_COSTUME_DEFINES:
            return dict(DEFAULT_COSTUME_DEFINES[costume_name])

        # Auto-match by SVG colors if svg_path is given
        if svg_path and svg_path.exists():
            try:
                tree = ET.parse(str(svg_path))
                svg_colors = set()
                for el in tree.getroot().iter():
                    f = el.attrib.get("fill")
                    if f and f.startswith("#"): svg_colors.add(f.upper())
                    sc = el.attrib.get("stop-color")
                    if sc and sc.startswith("#"): svg_colors.add(sc.upper())
                    st = el.attrib.get("style", "")
                    if st:
                        for m in re.findall(r'#[0-9a-fA-F]{6}', st):
                            svg_colors.add(m.upper())

                best_costume = None
                best_overlap = 0
                all_candidates = dict(self.costumes_data) if hasattr(self, 'costumes_data') else {}
                all_candidates.update({k: {"defines": v} for k, v in DEFAULT_COSTUME_DEFINES.items()})

                for c_cand, c_info in all_candidates.items():
                    c_defines = c_info.get("defines", {})
                    overlap = len(svg_colors.intersection(set(c_defines.keys())))
                    if overlap > best_overlap:
                        best_overlap = overlap
                        best_costume = c_cand

                if best_costume and best_overlap >= 3:
                    return dict(all_candidates[best_costume]["defines"])
            except Exception:
                pass

        return dict(DEFAULT_COSTUME_DEFINES.get("Viking", {}))

    def _get_effective_palette(self, costume_name: str, scheme_id, raw_pal=None) -> dict:
        """
        Computes the effective palette for a given costume and scheme,
        taking into account per-costume classic defines and colorExceptionTypes reroutings.
        """
        # If Classic scheme (ID 0)
        if scheme_id == 0 or str(scheme_id) == "0" or scheme_id == "Classic":
            if hasattr(self, 'costumes_data') and costume_name in self.costumes_data:
                return dict(self.costumes_data[costume_name].get("classic_palette", BODVAR_CLASSIC_PALETTE))
            if costume_name in DEFAULT_COSTUME_CLASSIC_PALETTES:
                return dict(DEFAULT_COSTUME_CLASSIC_PALETTES[costume_name])
            return dict(BODVAR_CLASSIC_PALETTE)

        # Base palette from raw_pal or all_schemes
        base_pal = dict(raw_pal) if raw_pal else {}
        if not base_pal and hasattr(self, 'all_schemes'):
            for name, sid, pal in self.all_schemes:
                if sid == scheme_id or name == scheme_id:
                    base_pal = dict(pal)
                    break

        if not base_pal and hasattr(self, 'official_schemes_raw') and scheme_id in self.official_schemes_raw:
            base_pal = dict(self.official_schemes_raw[scheme_id])

        if not base_pal:
            base_pal = dict(BODVAR_CLASSIC_PALETTE)

        # Apply color exceptions from Game.swz if available
        if hasattr(self, 'color_exceptions') and self.color_exceptions:
            for exc in self.color_exceptions:
                t_name = exc.get("TargetName")
                s_name = exc.get("ColorSchemeName")
                if t_name == costume_name:
                    scheme_matches = False
                    if s_name == str(self.selected_scheme_name) or s_name == str(scheme_id):
                        scheme_matches = True
                    else:
                        if hasattr(self, 'all_schemes'):
                            for d_name, sid, pal in self.all_schemes:
                                if (sid == scheme_id or d_name == self.selected_scheme_name) and s_name in (d_name, str(sid)):
                                    scheme_matches = True
                                    break
                    if scheme_matches:
                        for k, target_ch in exc.items():
                            if k.endswith("_Swap") and target_ch and target_ch != "--":
                                src_ch = k[:-5]
                                if target_ch in base_pal:
                                    base_pal[src_ch] = base_pal[target_ch]

        return base_pal

    # =========================================================================
    # COLUMN RESIZERS & SASH DRAGGING
    # =========================================================================

    def _on_sash1_press(self, event):
        self._sash1_start_x = event.x_root
        self._sash1_start_w = getattr(self, "left_panel_width", 250)

    def _on_workspace_resize(self, event):
        if getattr(self, "_user_adjusted_sashes", False):
            return
        tot_w = event.width
        if tot_w > 400:
            # 1/5 (20%) Left | 2/5 (40%) Center | 2/5 (40%) Right
            self.left_panel_width = max(180, int(tot_w * 0.20))
            self.right_panel_width = max(260, int(tot_w * 0.40))
            if hasattr(self, "left_panel") and self.left_panel:
                self.left_panel.configure(width=self.left_panel_width)
            if hasattr(self, "right_panel") and self.right_panel:
                self.right_panel.configure(width=self.right_panel_width)

    def _on_sash1_drag(self, event):
        self._user_adjusted_sashes = True
        dx = event.x_root - self._sash1_start_x
        new_w = max(180, min(500, self._sash1_start_w + dx))
        self.left_panel_width = new_w
        if hasattr(self, "left_panel") and self.left_panel:
            self.left_panel.configure(width=new_w)

    def _on_sash2_press(self, event):
        self._sash2_start_x = event.x_root
        self._sash2_start_w = getattr(self, "right_panel_width", 460)

    def _on_sash2_drag(self, event):
        self._user_adjusted_sashes = True
        dx = self._sash2_start_x - event.x_root
        new_w = max(240, min(750, self._sash2_start_w + dx))
        self.right_panel_width = new_w
        if hasattr(self, "right_panel") and self.right_panel:
            self.right_panel.configure(width=new_w)

    # =========================================================================
    # BOTTOM PRESET BAR NAVIGATION (PREV / NEXT SCHEME)
    # =========================================================================

    def _prev_scheme(self):
        all_items = [(name, sid, pal) for name, sid, pal, is_c in self.custom_schemes] + [(name, sid, pal) for name, sid, pal in self.all_schemes]
        if not all_items:
            return
        cur_idx = next((i for i, (name, sid, pal) in enumerate(all_items) if name == self.selected_scheme_name), 0)
        new_idx = (cur_idx - 1) % len(all_items)
        new_name = all_items[new_idx][0]
        self._on_scheme_selected(new_name)

    def _next_scheme(self):
        all_items = [(name, sid, pal) for name, sid, pal, is_c in self.custom_schemes] + [(name, sid, pal) for name, sid, pal in self.all_schemes]
        if not all_items:
            return
        cur_idx = next((i for i, (name, sid, pal) in enumerate(all_items) if name == self.selected_scheme_name), 0)
        new_idx = (cur_idx + 1) % len(all_items)
        new_name = all_items[new_idx][0]
        self._on_scheme_selected(new_name)

    # =========================================================================
    # PREVIEW ZOOM, PAN & AUTO-CYCLE
    # =========================================================================

    def _on_preview_mousewheel(self, event):
        if event.delta > 0:
            self._zoom_preview(1.15)
        elif event.delta < 0:
            self._zoom_preview(1.0 / 1.15)

    def _zoom_preview(self, factor):
        new_zoom = max(0.4, min(5.0, self.preview_zoom * factor))
        if abs(new_zoom - self.preview_zoom) > 0.01:
            self.preview_zoom = new_zoom
            if hasattr(self, "zoom_lbl") and self.zoom_lbl:
                self.zoom_lbl.configure(text=f"{int(self.preview_zoom * 100)}%")
            self._render_skin_preview()

    def _reset_preview_zoom(self):
        self.preview_zoom = 1.0
        self.preview_pan_x = 0
        self.preview_pan_y = 0
        if hasattr(self, "zoom_lbl") and self.zoom_lbl:
            self.zoom_lbl.configure(text="100%")
        self._render_skin_preview()

    def _on_preview_pan_start(self, event):
        self._pan_drag_start_x = event.x
        self._pan_drag_start_y = event.y

    def _on_preview_pan_drag(self, event):
        dx = event.x - self._pan_drag_start_x
        dy = event.y - self._pan_drag_start_y
        self._pan_drag_start_x = event.x
        self._pan_drag_start_y = event.y
        self.preview_pan_x += dx
        self.preview_pan_y += dy
        self._render_skin_preview()

    # =========================================================================
    # JUICY SPRING-POP SPRITE ANIMATION & PULSING HIGHLIGHT
    # =========================================================================

    def _trigger_sprite_pop_animation(self):
        if self._pop_anim_timer_id is not None:
            try:
                self.master_frame.after_cancel(self._pop_anim_timer_id)
            except Exception:
                pass
            self._pop_anim_timer_id = None

        self._pop_anim_frame = 0
        self._on_pop_anim_step()

    def _on_pop_anim_step(self):
        # Juicy spring-pop easing keyframes: squash -> punch-in -> overshoot -> settle
        keyframes = [0.88, 0.96, 1.06, 1.02, 1.00]
        if self._pop_anim_frame < len(keyframes):
            self._pop_anim_scale = keyframes[self._pop_anim_frame]
            self._pop_anim_frame += 1
            self._render_skin_preview()
            if self._pop_anim_frame < len(keyframes):
                self._pop_anim_timer_id = self.master_frame.after(25, self._on_pop_anim_step)
            else:
                self._pop_anim_scale = 1.0
                self._pop_anim_timer_id = None
        else:
            self._pop_anim_scale = 1.0
            self._pop_anim_timer_id = None

    def _toggle_highlight(self):
        is_on = bool(self._var_highlight_channel and self._var_highlight_channel.get())
        if hasattr(self, "hl_options_container"):
            if is_on:
                self.hl_options_container.pack(fill="x", padx=6, pady=(0, 4))
            else:
                self.hl_options_container.pack_forget()

        if is_on:
            self._hl_time = 0
            self._schedule_hl_pulse()
        else:
            if self._hl_timer_id is not None:
                try:
                    self.master_frame.after_cancel(self._hl_timer_id)
                except Exception:
                    pass
                self._hl_timer_id = None
            self._render_skin_preview()

    def _on_hl_opt_changed(self, val=None):
        self._render_skin_preview()

    def _on_hl_outline_color_changed(self, val):
        if val == "Custom":
            self._open_outline_color_picker()
            return
        named_colors = {
            "White": "#FFFFFF",
            "Magenta": "#FF007F",
            "Cyan": "#00FFFF",
            "Yellow": "#FFE600",
        }
        if val in named_colors:
            self._hl_outline_color = named_colors[val]
            if hasattr(self, "hl_outline_swatch_btn") and self.hl_outline_swatch_btn:
                self.hl_outline_swatch_btn.configure(fg_color=self._hl_outline_color)
        self._render_skin_preview()

    def _on_hl_tint_color_changed(self, val):
        if val == "Custom":
            self._open_fill_color_picker()
            return
        named_colors = {
            "Magenta": "#FF007F",
            "White": "#FFFFFF",
            "Yellow": "#FFE600",
            "Cyan": "#00FFFF",
        }
        if val in named_colors:
            self._hl_fill_color = named_colors[val]
            if hasattr(self, "hl_fill_swatch_btn") and self.hl_fill_swatch_btn:
                self.hl_fill_swatch_btn.configure(fg_color=self._hl_fill_color)
        self._render_skin_preview()

    def _open_outline_color_picker(self):
        from src.utils.vcp_wrapper import ask_color
        initial = getattr(self, "_hl_outline_color", "#FFFFFF")
        chosen = ask_color(self.master_frame, initial_hex=initial)
        if chosen:
            self._hl_outline_color = chosen.upper()
            if hasattr(self, "hl_outline_color_opt") and self.hl_outline_color_opt:
                self.hl_outline_color_opt.set("Custom")
            if hasattr(self, "hl_outline_swatch_btn") and self.hl_outline_swatch_btn:
                self.hl_outline_swatch_btn.configure(fg_color=self._hl_outline_color)
            self._render_skin_preview()

    def _open_fill_color_picker(self):
        from src.utils.vcp_wrapper import ask_color
        initial = getattr(self, "_hl_fill_color", "#FF007F")
        chosen = ask_color(self.master_frame, initial_hex=initial)
        if chosen:
            self._hl_fill_color = chosen.upper()
            if hasattr(self, "hl_tint_opt") and self.hl_tint_opt:
                self.hl_tint_opt.set("Custom")
            if hasattr(self, "hl_fill_swatch_btn") and self.hl_fill_swatch_btn:
                self.hl_fill_swatch_btn.configure(fg_color=self._hl_fill_color)
            self._render_skin_preview()

    # Legacy alias compatibility
    def _pick_outline_color_from_picker(self):
        self._open_outline_color_picker()

    def _pick_fill_color_from_picker(self):
        self._open_fill_color_picker()

    def _on_hl_opacity_changed(self, val):
        pct = int(float(val))
        self._hl_opacity_val = pct / 100.0
        if hasattr(self, "hl_opacity_lbl") and self.hl_opacity_lbl:
            self.hl_opacity_lbl.configure(text=f"{pct}%")
        self._render_skin_preview()

    def _on_hl_speed_changed(self, val):
        if "0.5s" in val or "Fast" in val:
            self._hl_speed_ms = 500
        elif "2.0s" in val or "Slow" in val:
            self._hl_speed_ms = 2000
        elif "Static" in val or "No Pulse" in val or "Fijo" in val:
            self._hl_speed_ms = 0
        else:
            self._hl_speed_ms = 1000

        # Restart pulse timer if switching from Static back to an active speed!
        if self._var_highlight_channel and self._var_highlight_channel.get():
            if self._hl_speed_ms > 0:
                self._schedule_hl_pulse()
            else:
                if self._hl_timer_id is not None:
                    try:
                        self.master_frame.after_cancel(self._hl_timer_id)
                    except Exception:
                        pass
                    self._hl_timer_id = None
        self._render_skin_preview()

    def _schedule_hl_pulse(self):
        if self._hl_timer_id is not None:
            try:
                self.master_frame.after_cancel(self._hl_timer_id)
            except Exception:
                pass
        if getattr(self, "_hl_speed_ms", 1000) > 0:
            self._hl_timer_id = self.master_frame.after(33, self._on_hl_pulse_tick)
        else:
            self._hl_timer_id = None

    def _on_hl_pulse_tick(self):
        self._hl_timer_id = None
        if self._var_highlight_channel and self._var_highlight_channel.get():
            speed = getattr(self, "_hl_speed_ms", 1000)
            if speed > 0:
                self._hl_time = (self._hl_time + 33) % speed
                self._render_skin_preview()
                self._schedule_hl_pulse()

    def _toggle_auto_cycle(self):
        if self._var_auto_cycle and self._var_auto_cycle.get():
            self._schedule_auto_cycle_tick()
        else:
            if self._auto_cycle_timer_id is not None:
                try:
                    self.master_frame.after_cancel(self._auto_cycle_timer_id)
                except Exception:
                    pass
                self._auto_cycle_timer_id = None

    def _schedule_auto_cycle_tick(self):
        if self._auto_cycle_timer_id is not None:
            try:
                self.master_frame.after_cancel(self._auto_cycle_timer_id)
            except Exception:
                pass
        self._auto_cycle_timer_id = self.master_frame.after(3000, self._on_auto_cycle_tick)

    def _on_auto_cycle_tick(self):
        self._auto_cycle_timer_id = None
        if self._var_auto_cycle and self._var_auto_cycle.get():
            self._next_skin()
            self._schedule_auto_cycle_tick()

    def _render_skin_preview(self):
        if not self.skin_svgs:
            if hasattr(self, 'sprite_canvas'):
                self.sprite_canvas.delete("all")
                self.sprite_canvas.create_text(
                    150, 150, text="No Skin SVGs\nfound in Templates/",
                    fill="#71717a", font=("Inter", 12), justify="center"
                )
            return

        svg_path = self.skin_svgs[self.skin_svg_index]
        if not svg_path.exists():
            return

        try:
            costume_name = self._current_skin_name()
            channel_defines = self._get_costume_defines(costume_name, svg_path)

            svg_content = svg_path.read_text(encoding="utf-8")
            root = ET.fromstring(svg_content)

            # Check if active channel highlight is enabled
            do_highlight = bool(self._var_highlight_channel and self._var_highlight_channel.get())
            hl_target_channel = getattr(self, "selected_channel", "Body1")
            def _is_channel_match(ch):
                return bool(do_highlight and ch == hl_target_channel)

            # Calculate pulse factor based on configurable speed (Default 1.0s = 1000ms period)
            speed_ms = getattr(self, "_hl_speed_ms", 1000)
            if speed_ms > 0:
                pulse_factor = (1.0 + math.cos(getattr(self, "_hl_time", 0) * 2.0 * math.pi / speed_ms)) / 2.0 if do_highlight else 0.0
            else:
                pulse_factor = 1.0 if do_highlight else 0.0

            # Dynamic Stroke Opacity and Thinner Double-Dot Stroke (2 1.5)
            stroke_alpha = 0.35 + 0.65 * pulse_factor
            base_opacity = getattr(self, "_hl_opacity_val", 0.20)
            tint_alpha = max(0.04, base_opacity * (0.6 + 0.8 * pulse_factor)) if base_opacity > 0.01 else 0.0

            # Outline style from user selection (English)
            outline_style_name = self.hl_outline_opt.get() if hasattr(self, "hl_outline_opt") else "Dotted"
            if outline_style_name in ("Dotted", "Punteada"):
                dash_attr = "2 1.5"
                stroke_w = "1.0"
                has_stroke = True
            elif outline_style_name in ("Dashed", "Discontinua"):
                dash_attr = "4 3"
                stroke_w = "1.0"
                has_stroke = True
            elif outline_style_name in ("Solid", "Sólida"):
                dash_attr = ""
                stroke_w = "1.0"
                has_stroke = True
            else: # "None", "Sin borde"
                dash_attr = ""
                stroke_w = "0"
                has_stroke = False

            # Outline color from user selection or picker
            outline_color_choice = self.hl_outline_color_opt.get() if hasattr(self, "hl_outline_color_opt") else "White"
            if outline_color_choice == "Active":
                active_outline_hex = self.active_palette.get(hl_target_channel, "#FFFFFF")
            elif outline_color_choice == "Custom":
                active_outline_hex = getattr(self, "_hl_outline_color", "#FFFFFF")
            else:
                named_outline_map = {
                    "White": "#FFFFFF",
                    "Magenta": "#FF007F",
                    "Cyan": "#00FFFF",
                    "Yellow": "#FFE600",
                }
                active_outline_hex = named_outline_map.get(outline_color_choice, getattr(self, "_hl_outline_color", "#FFFFFF"))

            # Fill Tint target color from user selection or picker
            tint_name = self.hl_tint_opt.get() if hasattr(self, "hl_tint_opt") else "Magenta"
            named_tint_map = {
                "Magenta": "#FF007F",
                "White": "#FFFFFF",
                "Yellow": "#FFE600",
                "Cyan": "#00FFFF"
            }
            if tint_name == "Active":
                tint_target_hex = self.active_palette.get(hl_target_channel, "#FF007F")
            elif tint_name == "Custom":
                tint_target_hex = getattr(self, "_hl_fill_color", "#FF007F")
            else:
                tint_target_hex = named_tint_map.get(tint_name, getattr(self, "_hl_fill_color", "#FF007F"))

            def _blend_tint(hex_c, a):
                try:
                    r, g, b = hex_to_rgb(hex_c)
                    tr_hex = hex_c if tint_name == "Active" else tint_target_hex
                    tr, tg, tb = hex_to_rgb(tr_hex)
                    a_c = max(0.0, min(1.0, a))
                    nr = max(0, min(255, int(r * (1.0 - a_c) + tr * a_c)))
                    ng = max(0, min(255, int(g * (1.0 - a_c) + tg * a_c)))
                    nb = max(0, min(255, int(b * (1.0 - a_c) + tb * a_c)))
                    return rgb_to_hex((nr, ng, nb))
                except Exception:
                    return hex_c

            # Apply active palette colors ONLY to defined costume colors across all elements and stops
            for elem in root.iter():
                # 1. Fill attribute
                fill = elem.attrib.get("fill", "")
                if fill and fill.startswith("#") and fill.upper() in channel_defines:
                    ch = channel_defines[fill.upper()]
                    if ch in self.active_palette:
                        base_c = self.active_palette[ch]
                        if _is_channel_match(ch):
                            elem.attrib["fill"] = _blend_tint(base_c, tint_alpha)
                            if has_stroke:
                                elem.attrib["stroke"] = active_outline_hex
                                elem.attrib["stroke-width"] = stroke_w
                                if dash_attr:
                                    elem.attrib["stroke-dasharray"] = dash_attr
                                elif "stroke-dasharray" in elem.attrib:
                                    del elem.attrib["stroke-dasharray"]
                                elem.attrib["stroke-opacity"] = f"{stroke_alpha:.2f}"
                        else:
                            elem.attrib["fill"] = base_c

                # 2. Stop-color attribute (Gradients)
                sc = elem.attrib.get("stop-color", "")
                if sc and sc.startswith("#") and sc.upper() in channel_defines:
                    ch = channel_defines[sc.upper()]
                    if ch in self.active_palette:
                        base_c = self.active_palette[ch]
                        if _is_channel_match(ch):
                            elem.attrib["stop-color"] = _blend_tint(base_c, tint_alpha)
                        else:
                            elem.attrib["stop-color"] = base_c

                # 3. Style attribute (fill: and stop-color:)
                style = elem.attrib.get("style", "")
                if style:
                    def _replace_style_color(m):
                        prefix = m.group(1) # 'fill:' or 'stop-color:'
                        color_hex = m.group(2).upper()
                        if color_hex in channel_defines:
                            ch = channel_defines[color_hex]
                            if ch in self.active_palette:
                                base_c = self.active_palette[ch]
                                if _is_channel_match(ch):
                                    tinted = _blend_tint(base_c, tint_alpha)
                                    return f"{prefix}{tinted}"
                                return f"{prefix}{base_c}"
                        return m.group(0)

                    elem.attrib["style"] = re.sub(
                        r'(fill:\s*|stop-color:\s*)(#[0-9a-fA-F]{6})',
                        _replace_style_color,
                        style
                    )

            processed_svg_bytes = ET.tostring(root, encoding="utf-8")

            # Dynamic Canvas Dimensions with Zoom, Pan and Juicy Spring-Pop Scaling
            w_box = max(100, self.sprite_canvas.winfo_width() if self.sprite_canvas.winfo_width() > 10 else 300)
            h_box = max(100, self.sprite_canvas.winfo_height() if self.sprite_canvas.winfo_height() > 10 else 280)
            base_size = min(w_box, h_box) - 20
            
            effective_scale = getattr(self, "preview_zoom", 1.0) * getattr(self, "_pop_anim_scale", 1.0)
            target_size = max(40, int(base_size * effective_scale))

            rendered_img = render_svg(processed_svg_bytes, (target_size, target_size))
            if not rendered_img:
                return

            # Always render the clean checkerboard background by default
            bg = Image.new("RGBA", (w_box, h_box), (24, 24, 27, 255))
            draw = ImageDraw.Draw(bg)
            step = 16
            for y in range(0, h_box, step):
                for x in range(0, w_box, step):
                    if (x // step + y // step) % 2 == 0:
                        draw.rectangle([x, y, x + step, y + step], fill=(39, 39, 42, 255))

            offset_x = (w_box - rendered_img.width) // 2 + getattr(self, "preview_pan_x", 0)
            offset_y = (h_box - rendered_img.height) // 2 + getattr(self, "preview_pan_y", 0)
            bg.paste(rendered_img, (offset_x, offset_y), rendered_img)

            self._skin_img_ref = ImageTk.PhotoImage(bg)
            self.sprite_canvas.delete("all")
            self.sprite_canvas.create_image(0, 0, anchor="nw", image=self._skin_img_ref)

            # Update info label
            matched = len(channel_defines)
            if hasattr(self, 'sprite_info_lbl'):
                self.sprite_info_lbl.configure(
                    text=f"{matched} color channels active  |  {self._current_skin_display_name()}"
                )
        except Exception as e:
            print(f"[ColorModTool] Error rendering skin SVG preview: {e}")

    # -- legacy alias for backward compatibility --
    def _render_bodvar_preview(self):
        self._render_skin_preview()

    def _save_current_preset(self):
        default_name = self.selected_scheme_name
        if not default_name.endswith(" (Custom)") and not default_name.endswith(" Custom"):
            default_name = f"{default_name} Custom"

        dialog = ctk.CTkInputDialog(
            text="Enter custom color scheme name:",
            title="Save Custom Scheme"
        )
        name = dialog.get_input()
        if not name or not name.strip():
            return

        name = name.strip()
        custom_id = f"C{len(self.custom_schemes) + 1}"

        # If name already exists in custom schemes, update it; otherwise append
        existing_idx = next((i for i, cs in enumerate(self.custom_schemes) if cs[0].lower() == name.lower()), None)
        if existing_idx is not None:
            self.custom_schemes[existing_idx] = (name, self.custom_schemes[existing_idx][1], dict(self.active_palette), True)
        else:
            self.custom_schemes.append((name, custom_id, dict(self.active_palette), True))

        self._save_custom_schemes_cache()
        self.selected_scheme_name = name
        self.selected_scheme_id = custom_id

        self._update_scheme_selector_btn()
        self._refresh_saved_strips()
        messagebox.showinfo("Saved", f"Custom scheme '{name}' saved successfully!")

    def _delete_current_preset(self):
        matching_custom = next((cs for cs in self.custom_schemes if cs[0] == self.selected_scheme_name), None)
        if not matching_custom:
            messagebox.showwarning("Protected Scheme", "Official Brawlhalla color schemes cannot be deleted.\nOnly custom schemes can be deleted.")
            return

        confirm = messagebox.askyesno("Delete Custom Scheme", f"Are you sure you want to delete custom scheme '{self.selected_scheme_name}'?")
        if not confirm:
            return

        self.custom_schemes = [cs for cs in self.custom_schemes if cs[0] != self.selected_scheme_name]
        self._save_custom_schemes_cache()

        # Switch back to Classic
        self._on_scheme_selected("Classic")
        self._refresh_saved_strips()
        messagebox.showinfo("Deleted", "Custom scheme deleted successfully.")

    def _delete_custom_scheme(self, name, sid):
        confirm = messagebox.askyesno("Delete Custom Scheme", f"Are you sure you want to delete custom scheme '{name}'?")
        if not confirm:
            return

        self.custom_schemes = [cs for cs in self.custom_schemes if cs[0] != name]
        self._save_custom_schemes_cache()

        if self.selected_scheme_name == name:
            self._on_scheme_selected("Classic")

        self._refresh_saved_strips()
        self._render_dropdown_canvas()

    def _show_saved_schemes_dialog(self):
        self._open_scheme_dropdown()

    def _share_palette(self):
        file_path = filedialog.asksaveasfilename(
            title="Share Palette (Export .palette)",
            defaultextension=".palette",
            initialfile=f"{self.selected_scheme_name}.palette",
            filetypes=[("BMT Color Palette (*.palette)", "*.palette"), ("All Files (*.*)", "*.*")]
        )
        if not file_path:
            return

        try:
            palette_data = {
                "format": "BMT_COLOR_PALETTE",
                "version": "1.0.0",
                "name": self.selected_scheme_name,
                "palette": dict(self.active_palette)
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(palette_data, f, indent=2)

            messagebox.showinfo("Palette Exported", f"Palette '{self.selected_scheme_name}' successfully exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export palette:\n{e}")

    def _import_palette(self):
        file_path = filedialog.askopenfilename(
            title="Import Palette (.palette)",
            filetypes=[("BMT Color Palette (*.palette)", "*.palette"), ("JSON Palette (*.json)", "*.json"), ("All Files (*.*)", "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                raise ValueError("Invalid palette file format.")

            pal = data.get("palette")
            if not pal or not isinstance(pal, dict):
                raise ValueError("No valid palette color channels found in file.")

            name = data.get("name", Path(file_path).stem).strip()
            custom_id = f"C{len(self.custom_schemes) + 1}"

            # Add or update in custom schemes
            existing_idx = next((i for i, cs in enumerate(self.custom_schemes) if cs[0].lower() == name.lower()), None)
            if existing_idx is not None:
                self.custom_schemes[existing_idx] = (name, self.custom_schemes[existing_idx][1], dict(pal), True)
            else:
                self.custom_schemes.append((name, custom_id, dict(pal), True))

            self._save_custom_schemes_cache()
            self._on_scheme_selected(name)
            self._refresh_saved_strips()

            messagebox.showinfo("Palette Imported", f"Color palette '{name}' imported successfully!")
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import palette:\n{e}")

    # =========================================================================
    # WIKI MODIFIABLE COLORS DETECTION & TARGET SELECTION MODAL
    # =========================================================================

    def _fetch_modifiable_colors_from_wiki(self):
        """
        Dynamically extracts Battle Pass and Paid (Store Mammoth Coins) colors
        from the official Brawlhalla wiki API. Caches results locally so future additions
        are detected automatically without manual updates.
        """
        cache_dir = os.path.join(os.getenv('APPDATA') or str(Path.home()), 'Brawlhalla Modding Toolkit')
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, 'ModifiableColorsCache.json')

        try:
            req = urllib.request.Request(
                WIKI_COLORS_API_URL,
                headers={"User-Agent": "BrawlhallaModdingToolkit/1.0 (contact@bmt.local)"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                html = data.get("parse", {}).get("text", {}).get("*", "")

            if html:
                # 1. Battle Pass Colors
                bp_match = re.search(r'id="Battle_Pass_Colors".*?</div>\s*<h[23]>', html, re.DOTALL)
                bp_colors = []
                if bp_match:
                    bp_section = bp_match.group(0)
                    for m in re.finditer(r'<th[^>]*><a[^>]*>([^<]+)</a>', bp_section):
                        name = re.sub(r'\s*\(Color\)$', '', m.group(1).strip())
                        if name and name not in bp_colors:
                            bp_colors.append(name)

                # 2. Paid Colors (Under Store Colors section that cost Mammoth Coins)
                store_match = re.search(r'id="Store_Colors".*?</div>\s*<h[23]>', html, re.DOTALL)
                paid_colors = []
                if store_match:
                    store_section = store_match.group(0)
                    tables = re.findall(r'<table class="wikitable"[^>]*>(.*?)</table>', store_section, re.DOTALL)
                    for tbl in tables:
                        has_mammoth = "Coin_Mammoth" in tbl or "Mammoth_Coins" in tbl or "Mammoth Coins" in tbl
                        if has_mammoth:
                            name_m = re.search(r'<th[^>]*><a[^>]*>([^<]+)</a>', tbl)
                            if name_m:
                                cname = re.sub(r'\s*\(Color\)$', '', name_m.group(1).strip())
                                if cname and cname not in paid_colors and cname not in bp_colors:
                                    paid_colors.append(cname)

                if bp_colors or paid_colors:
                    result = {"battle_pass": bp_colors, "paid": paid_colors}
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump(result, f, indent=2)
                    return result
        except Exception as e:
            print(f"[ColorModTool] Wiki API fetch status: {e}, falling back to local cache.")

        # Fallback to local cache if present
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        return DEFAULT_MODIFIABLE_COLORS_FALLBACK

    def _open_export_target_dialog(self):
        """
        Opens a modal window asking 'Which color scheme do you want to replace?'
        listing only Battle Pass and Paid schemes detected automatically from the wiki and Game.swz.
        """
        mod_colors = self._fetch_modifiable_colors_from_wiki()
        bp_list = [c.lower() for c in mod_colors.get("battle_pass", [])]
        paid_list = [c.lower() for c in mod_colors.get("paid", [])]

        # Match with self.all_schemes loaded from Game.swz
        matched_bp = []
        matched_paid = []
        for name, sid, pal in self.all_schemes:
            nl = name.lower().strip()
            if any(nl == b or b in nl or nl in b for b in bp_list):
                matched_bp.append((name, sid, pal, "Battle Pass"))
            elif any(nl == p or p in nl or nl in p for p in paid_list):
                matched_paid.append((name, sid, pal, "Paid"))

        # Create Modal Dialog
        dialog = ctk.CTkToplevel(self.master_frame)
        dialog.title("Export Mod Source - Target Scheme Selection")
        dialog.geometry("540x600")
        dialog.transient(self.master_frame.winfo_toplevel())
        dialog.grab_set()
        dialog.configure(fg_color="#18181b")

        # Center on screen
        dialog.update_idletasks()
        try:
            px = self.master_frame.winfo_rootx() + (self.master_frame.winfo_width() - 540) // 2
            py = self.master_frame.winfo_rooty() + (self.master_frame.winfo_height() - 600) // 2
            dialog.geometry(f"540x600+{max(50, px)}+{max(50, py)}")
        except Exception:
            pass

        # Title & Subtitle Header
        hdr = ctk.CTkFrame(dialog, fg_color="#27272a", corner_radius=0)
        hdr.pack(fill="x", padx=0, pady=0)
        ctk.CTkLabel(
            hdr,
            text="Which color scheme do you want to replace?",
            font=("Inter", 14, "bold"),
            text_color="#f4f4f5"
        ).pack(anchor="w", padx=16, pady=(12, 2))
        ctk.CTkLabel(
            hdr,
            text="Only official Battle Pass and Paid (Mammoth Coins) schemes can be replaced in-game.",
            font=("Inter", 10),
            text_color="#a1a1aa"
        ).pack(anchor="w", padx=16, pady=(0, 12))

        # Search Bar
        search_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        search_frame.pack(fill="x", padx=16, pady=(10, 4))
        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search target scheme (e.g. Soul Fire, RGB)...",
            height=30,
            fg_color="#27272a",
            border_color="#3f3f46",
            text_color="#f4f4f5",
            font=("Inter", 11)
        )
        search_entry.pack(fill="x")

        # Category Tabs (No emojis)
        tab_frame = ctk.CTkFrame(dialog, fg_color="#27272a", height=28, corner_radius=6)
        tab_frame.pack(fill="x", padx=16, pady=(4, 8))

        selected_category = tk.StringVar(value="All")
        selected_target = [None] # (name, sid, pal, cat)

        # Bottom Bar (Packed FIRST with side="bottom" to prevent any overlap)
        bottom_bar = ctk.CTkFrame(dialog, fg_color="#27272a", height=50, corner_radius=0)
        bottom_bar.pack(side="bottom", fill="x")

        target_status_lbl = ctk.CTkLabel(
            bottom_bar,
            text="Selected Target: (None)",
            font=("Inter", 10, "bold"),
            text_color="#a1a1aa"
        )
        target_status_lbl.pack(side="left", padx=16)

        def on_export_swf_clicked():
            if not selected_target[0]:
                messagebox.showwarning("Select Target", "Please select a target color scheme to replace.", parent=dialog)
                return
            target_info = selected_target[0]
            dialog.destroy()
            self.export_color_mod(target_info)

        def on_export_source_clicked():
            if not selected_target[0]:
                messagebox.showwarning("Select Target", "Please select a target color scheme to replace.", parent=dialog)
                return
            target_info = selected_target[0]
            dialog.destroy()
            self.export_mod_creator_source(target_info)

        cancel_btn = ctk.CTkButton(
            bottom_bar, text="Cancel", width=65, height=28,
            fg_color="#3f3f46", hover_color="#52525b", text_color="#f4f4f5",
            command=dialog.destroy
        )
        cancel_btn.pack(side="right", padx=(4, 16), pady=10)

        export_src_btn = ctk.CTkButton(
            bottom_bar, text="Export Mod Source", width=130, height=28,
            fg_color="#3f3f46", hover_color="#52525b", text_color="#f4f4f5", font=("Inter", 11, "bold"),
            command=on_export_source_clicked
        )
        export_src_btn.pack(side="right", padx=4, pady=10)
        BMTToolTip(export_src_btn, "Exports the full Mod Source folder structure ready for Brawlhalla Mod Creator / BModLoader.")

        export_swf_btn = ctk.CTkButton(
            bottom_bar, text="Export Carrier SWF", width=140, height=28,
            fg_color="#07c9d7", hover_color="#06b6d4", text_color="#18181b", font=("Inter", 11, "bold"),
            command=on_export_swf_clicked
        )
        export_swf_btn.pack(side="right", padx=4, pady=10)
        BMTToolTip(export_swf_btn, "Patches and exports a ready-to-use UI_MainMenu_ColorMod.swf carrier file.")

        # Scrollable list container (Takes the remaining top space cleanly)
        cards_frame = ctk.CTkScrollableFrame(dialog, fg_color="#27272a", corner_radius=8, border_width=1, border_color="#3f3f46")
        cards_frame.pack(side="top", fill="both", expand=True, padx=16, pady=(0, 8))

        # Render list items
        card_widgets = []

        def render_cards():
            for w in cards_frame.winfo_children():
                w.destroy()
            card_widgets.clear()

            q = search_entry.get().strip().lower()
            cat = selected_category.get()

            all_eligible = []
            if cat in ("All", "Battle Pass"):
                all_eligible.extend(matched_bp)
            if cat in ("All", "Paid"):
                all_eligible.extend(matched_paid)

            filtered = [s for s in all_eligible if not q or q in s[0].lower() or q in str(s[1]).lower()]

            if not filtered:
                ctk.CTkLabel(cards_frame, text="No eligible schemes found.", font=("Inter", 11), text_color="#71717a").pack(pady=30)
                return

            for sname, ssid, spal, scat in filtered:
                is_sel = (selected_target[0] is not None and selected_target[0][0] == sname)
                b_color = "#07c9d7" if is_sel else "#3f3f46"
                bg_color = "#18181b" if is_sel else "#212124"

                row_card = ctk.CTkFrame(cards_frame, fg_color=bg_color, corner_radius=6, border_width=1, border_color=b_color, height=48, cursor="hand2")
                row_card.pack(fill="x", padx=4, pady=3)
                row_card.pack_propagate(False)

                # 6 Swatches
                sw_container = ctk.CTkFrame(row_card, fg_color="transparent")
                sw_container.pack(side="left", padx=(12, 10))
                p_colors = [
                    spal.get("Hair", "#ECF185"), spal.get("Body1", "#3F985B"), spal.get("Body2", "#477860"),
                    spal.get("Special", "#20FFC1"), spal.get("Cloth", "#B7C168"), spal.get("Weapon", "#54ABEB")
                ]
                sw_widgets = []
                for c in p_colors:
                    sw = ctk.CTkFrame(sw_container, width=7, height=22, fg_color=c, corner_radius=1)
                    sw.pack(side="left", padx=0.5)
                    sw_widgets.append(sw)

                # Name & ID
                info_f = ctk.CTkFrame(row_card, fg_color="transparent")
                info_f.pack(side="left", fill="both", expand=True)
                name_lbl = ctk.CTkLabel(info_f, text=sname, font=("Inter", 12, "bold"), text_color="#07c9d7" if is_sel else "#f4f4f5", anchor="w")
                name_lbl.pack(anchor="w", pady=(4, 0))
                id_lbl = ctk.CTkLabel(info_f, text=f"ID #{ssid}", font=("Consolas", 10), text_color="#a1a1aa", anchor="w")
                id_lbl.pack(anchor="w", pady=(0, 4))

                # Badge
                badge_bg = "#3b1747" if scat == "Battle Pass" else "#42280d"
                badge_fg = "#c084fc" if scat == "Battle Pass" else "#fcd34d"
                badge_lbl = ctk.CTkLabel(row_card, text=f" {scat} ", font=("Inter", 10, "bold"), fg_color=badge_bg, text_color=badge_fg, corner_radius=4, height=22)
                badge_lbl.pack(side="right", padx=(4, 14))

                def make_select_handler(target_tuple):
                    def handler(e=None):
                        selected_target[0] = target_tuple
                        target_status_lbl.configure(
                            text=f"Selected Target: {target_tuple[0]} (#{target_tuple[1]}) [{target_tuple[3]}]",
                            text_color="#07c9d7"
                        )
                        render_cards()
                    return handler

                h = make_select_handler((sname, ssid, spal, scat))
                for widget in (row_card, sw_container, *sw_widgets, info_f, name_lbl, id_lbl, badge_lbl):
                    widget.bind("<Button-1>", h)

        def set_category(cat):
            selected_category.set(cat)
            for k, btn in cat_btns.items():
                btn.configure(
                    fg_color="#07c9d7" if k == cat else "transparent",
                    text_color="#18181b" if k == cat else "#a1a1aa"
                )
            render_cards()

        cat_btns = {}
        for cat_name, cat_label in [("All", f"All Eligible ({len(matched_bp) + len(matched_paid)})"),
                                    ("Battle Pass", f"Battle Pass ({len(matched_bp)})"),
                                    ("Paid", f"Paid ({len(matched_paid)})")]:
            cbtn = ctk.CTkButton(
                tab_frame, text=cat_label, height=22, font=("Inter", 9, "bold"),
                fg_color="#07c9d7" if cat_name == "All" else "transparent",
                text_color="#18181b" if cat_name == "All" else "#a1a1aa",
                hover_color="#3f3f46", corner_radius=4,
                command=lambda c=cat_name: set_category(c)
            )
            cbtn.pack(side="left", fill="x", expand=True, padx=2, pady=2)
            cat_btns[cat_name] = cbtn

        search_entry.bind("<KeyRelease>", lambda e: render_cards())
        render_cards()

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

    def _detect_game_ui_main_menu(self) -> str:
        """Finds the live Brawlhalla game UI_MainMenu.swf path in Steam library."""
        steam_game_path = r"X:\SteamLibrary\steamapps\common\Brawlhalla\UI_MainMenu.swf"
        if os.path.exists(steam_game_path):
            return steam_game_path
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
            steam_path = winreg.QueryValueEx(key, "InstallPath")[0]
            vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
            if os.path.exists(vdf_path):
                content = open(vdf_path, "r", encoding="utf-8", errors="ignore").read()
                import re
                paths = re.findall(r'"path"\s+"([^"]+)"', content)
                for p in paths:
                    candidate = os.path.join(p.replace("\\\\", "\\"), "steamapps", "common", "Brawlhalla", "UI_MainMenu.swf")
                    if os.path.exists(candidate):
                        return candidate
        except Exception:
            pass
        return ""

    def _build_palette_obf_as3_code(self, target_scheme_id: int, target_scheme_name: str) -> str:
        """Builds clean, deobfuscated Obf.as ActionScript source with custom palette array."""
        channels_ordered = [
            "HairLt", "Hair", "HairDk",
            "Body1VL", "Body1Lt", "Body1", "Body1Dk", "Body1VD", "Body1Acc",
            "Body2VL", "Body2Lt", "Body2", "Body2Dk", "Body2VD", "Body2Acc",
            "SpecialVL", "SpecialLt", "Special", "SpecialDk", "SpecialVD", "SpecialAcc",
            "ClothVL", "ClothLt", "Cloth", "ClothDk",
            "WeaponVL", "WeaponLt", "Weapon", "WeaponDk", "WeaponAcc"
        ]

        palette_hex_list = []
        for ch in channels_ordered:
            hex_val = self.active_palette.get(ch, "#FFFFFF").lstrip("#")
            try:
                val = int(hex_val, 16)
            except Exception:
                val = 0xFFFFFF
            palette_hex_list.append(f"0x{val:06X}")

        lines = [
            ", ".join(palette_hex_list[0:3]),
            ", ".join(palette_hex_list[3:9]),
            ", ".join(palette_hex_list[9:15]),
            ", ".join(palette_hex_list[15:21]),
            ", ".join(palette_hex_list[21:25]),
            ", ".join(palette_hex_list[25:30]),
        ]
        palette_code = ",\n            ".join(lines)

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
      }}

      public static function initPalettes() : void
      {{
         paletteMap = {{}};
         paletteMap["{target_scheme_id}"] = [
            {palette_code}
         ];
         paletteMap["{target_scheme_name}"] = paletteMap["{target_scheme_id}"];
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
         if(costumeName == null || colorMap == null)
         {{
            return null;
         }}
         if(colorMap[costumeName] != null)
         {{
            return colorMap[costumeName] as Array;
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
         return Obf.d([41, 30, 46, 54, 50, 58, 7],15);
      }}

      public static function handFile() : String
      {{
         return Obf.d([35,15,40,21,64,38,58,55,12,0,26,37,27],3);
      }}

      public static function swapSuffix() : String
      {{
         return Obf.d([53, 41, 48, 46],20);
      }}

      public static function gcField() : String
      {{
         return Obf.d([53,61,0,0,15],56);
      }}

      public static function families() : Array
      {{
         return [Obf.d([3, 56, 63, 61],35),Obf.d([3, 56, 63, 61],35)];
      }}

      public static function paletteChannels() : Array
      {{
         return [
            "HairLt","Hair","HairDk",
            "Body1VL","Body1Lt","Body1","Body1Dk","Body1VD","Body1Acc",
            "Body2VL","Body2Lt","Body2","Body2Dk","Body2VD","Body2Acc",
            "SpecialVL","SpecialLt","Special","SpecialDk","SpecialVD","SpecialAcc",
            "ClothVL","ClothLt","Cloth","ClothDk",
            "WeaponVL","WeaponLt","Weapon","WeaponDk","WeaponAcc"
         ];
      }}
   }}
}}"""

    def _patch_carrier_swf_direct(self, carrier_path, out_swf_path, obf_as3):
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

        template_as3_path = Path(__file__).parent.parent / "utils" / "carriers" / "hand_scripts_template" / "BrawlForgeSuite.as"
        suite_as3 = ""
        if template_as3_path.exists():
            with open(template_as3_path, "r", encoding="utf-8") as f:
                suite_as3 = f.read()

        for pack in swf.getAS3Packs():
            path = str(pack.getPath()) if hasattr(pack, "getPath") else str(pack)
            if "Obf" in path:
                try:
                    pack.abc.replaceScriptPack(scriptReplacer, pack, obf_as3, None)
                    print("[ColorModTool] Replaced Obf script.")
                except Exception as e:
                    print(f"[ColorModTool] Error replacing Obf script: {e}")
            elif "BrawlForgeSuite" in path and "Bootstrap" not in path:
                if suite_as3:
                    try:
                        pack.abc.replaceScriptPack(scriptReplacer, pack, suite_as3, None)
                        print("[ColorModTool] Replaced BrawlForgeSuite script.")
                    except Exception as e:
                        print(f"[ColorModTool] Error replacing BrawlForgeSuite script: {e}")

        out_path = Path(out_swf_path).resolve()
        os.makedirs(out_path.parent, exist_ok=True)

        Methods.save_swf_to(swf, str(out_path))
        print(f"[ColorModTool] SWF Carrier successfully written to {out_path}")

    def export_color_mod(self, target_scheme_info):
        """Exports UI_MainMenu_ColorMod.swf carrier with the active custom palette replacing the target scheme."""
        tname, tsid, tpal, tcat = target_scheme_info

        carrier_file = self._detect_internal_carrier()
        if not carrier_file or not os.path.exists(carrier_file):
            messagebox.showerror("Carrier File Not Found", "Internal UI_MainMenu.swf carrier asset could not be located.")
            return

        dest_folder = filedialog.askdirectory(title=f"Select Destination Folder for UI_MainMenu_ColorMod.swf (Replacing {tname})")
        if not dest_folder:
            return

        out_swf_path = os.path.join(dest_folder, "UI_MainMenu_ColorMod.swf")

        try:
            obf_as3 = self._build_palette_obf_as3_code(tsid, tname)
            self._patch_carrier_swf_direct(carrier_file, out_swf_path, obf_as3)

            # Auto-patch live Steam game UI_MainMenu.swf if found
            live_game_ui = self._detect_game_ui_main_menu()
            live_patched = False
            if live_game_ui and os.path.exists(os.path.dirname(live_game_ui)):
                try:
                    self._patch_carrier_swf_direct(carrier_file, live_game_ui, obf_as3)
                    live_patched = True
                    print(f"[ColorModTool] Also directly patched live game file: {live_game_ui}")
                except Exception as ex:
                    print(f"[ColorModTool] Note: Could not auto-patch live game file: {ex}")

            live_msg = f"\n\nDirectly Installed into Game:\n{live_game_ui}" if live_patched else "\n\nUsage: Rename to UI_MainMenu.swf or install via Brawlhalla Mod Loader!"

            messagebox.showinfo(
                "Color Mod Export Complete!",
                f"Color Scheme Carrier SWF successfully created!\n\n"
                f"Target Scheme Replaced: {tname} (ID #{tsid}) [{tcat}]\n"
                f"Total Channels Modified: 30\n\n"
                f"Output File:\n{out_swf_path}"
                f"{live_msg}"
            )
        except Exception as e:
            print(f"[ColorModTool] Error during export: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Export Error", f"Could not export UI_MainMenu_ColorMod.swf:\n{e}")

    def export_mod_creator_source(self, target_scheme_info):
        """Exports the full Mod Creator Source folder structure with the active custom palette replacing the target scheme."""
        tname, tsid, tpal, tcat = target_scheme_info

        dest_folder = filedialog.askdirectory(title=f"Select Destination Mod Source Folder (Replacing {tname})")
        if not dest_folder:
            return

        try:
            obf_as3 = self._build_palette_obf_as3_code(tsid, tname)

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

            # 4. Obf.as with custom palette
            (tier_b_dir / "Obf.as").write_text(obf_as3, encoding="utf-8")

            # 5. Generate and write cryptographic BMT Certificate
            try:
                from src.utils.security_scanner import generate_bmt_certificate
                cert_data = generate_bmt_certificate("ColorModTool", f"ColorMod_{tname}", Path(dest_folder))
                (Path(dest_folder) / ".bmt_cert.json").write_text(json.dumps(cert_data, indent=2), encoding="utf-8")
            except Exception as ce:
                print(f"[ColorModTool] Warning: Could not write certificate: {ce}")

            messagebox.showinfo(
                "Mod Source Export Complete!",
                f"Mod Creator Source successfully created!\n\n"
                f"Target Scheme Replaced: {tname} (ID #{tsid}) [{tcat}]\n"
                f"Total Channels Modified: 30\n"
                f"BMT Security Certification: Embedded\n\n"
                f"Folder:\n{dest_folder}\n\n"
                f"Next Step: Open 'Brawlhalla Mod Creator', load this folder as your Mod Source, and compile it to .bmod!"
            )
        except Exception as e:
            print(f"[ColorModTool] Error exporting mod source: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Export Error", f"Could not export Mod Creator Source:\n{e}")

