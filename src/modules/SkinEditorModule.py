"""
Skin Editor Module v5 — Professional dual-view SWF sprite editor.

Fixes from v4
~~~~~~~~~~~~~~
* Rotation pivot saved at drag start ⇒ no more drift / scale corruption.
* Export uses per-shape PNG dump (no SpriteExporter dependency).
* Position (X, Y) has entry + ± only (no slider).
* All fonts enlarged 2 pt for readability.
* Arrow keys always nudge (tree arrow bindings overridden).
* Copy / Paste all properties across parts.
* Step selector (0.01 – 10) for ± increment.
* Tag tooltip under cursor on canvas.
* Reference canvas highlights edited sprite & shows gizmo.
* Editor title shows DefineSprite name.
* SVG cursor files per mode (rotate, skew, pan, etc.).
* SVG render mode: cairosvg.svg2png(scale=…) for correct quality.
* Responsive toolbar (shorter buttons, no overflow on small windows).
"""

from __future__ import annotations
from src.utils import get_project_root

import hashlib, importlib.util, io, json, math, os, re, shutil, struct, zlib
import subprocess, sys, tempfile, threading, time, traceback
from dataclasses import dataclass, field

try:
    import skia
    HAS_SKIA = True
except ImportError:
    HAS_SKIA = False
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageDraw

from .ToolModuleBase import ToolModule
from src.utils.ThemeManager import BMTTheme, ACCENTS

# ── Color picker: ctk_color_picker (nativo CTK, modal) ──────────────
def _ask_color_se(initial_hex: str = "#ffffff", parent=None) -> str | None:
    """Open ctk_color_picker modal. Returns hex string or None."""
    try:
        from src.utils.vcp_wrapper import ask_color
        return ask_color(parent, initial_hex)
    except Exception as e:
        print(f"[SE] color picker error: {e}")
        return None

# ── SVG renderer utility ─────────────────────────────────────────────
from src.svg_utils import render_svg, get_svg_icon, create_svg_fallback, HAS_CAIROSVG, HAS_RESVG

# ── Lib path ─────────────────────────────────────────────────────────
LIB_PATH = get_project_root() / "Lib"
if str(LIB_PATH) not in sys.path:
    sys.path.insert(0, str(LIB_PATH))

_Methods = None
_ffdec_ok = False

RESOURCES = get_project_root() / "resources"
CURSOR_DIR = RESOURCES / "assets" / "cursors"


def _ensure_ffdec() -> bool:
    global _Methods, _ffdec_ok
    if _ffdec_ok:
        return True
    try:
        p = LIB_PATH / "Methods.py"
        if not p.exists():
            return False
        spec = importlib.util.spec_from_file_location("Methods", str(p))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _Methods = mod
        _ffdec_ok = True
        return True
    except Exception:
        traceback.print_exc()
        return False


def _ajvm():
    try:
        import jpype
        if not jpype.isThreadAttachedToJVM():
            jpype.attachThreadToJVM()
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════
#  CONSTANTS & THEME
# ═══════════════════════════════════════════════════════════════════════
TWIP = 20.0
FP   = 65536.0
MIN_ZOOM  = 0.02
MAX_ZOOM  = 50.0
ZOOM_STEP = 1.15
GRID_MINOR = 10
GRID_MAJOR = 5
HS = 6
ARROW_LEN = 60
REF_MIN_PO = 30
MAX_RENDER_DIM = 4000

AC  = ACCENTS["Skin Editor"]
ACD = BMTTheme.adjust_brightness(AC, -0.2)
ACL = BMTTheme.adjust_brightness(AC, 0.2)
BGD = BMTTheme.BG_DARK
BGP = BMTTheme.BG_PANEL
BGI = BMTTheme.BG_SUBPANEL
BGC = BMTTheme.BG_DARK
FGT = BMTTheme.WHITE
FGD = BMTTheme.GREY
RED = BMTTheme.RED
BLUE = BMTTheme.BLUE
GREEN = BMTTheme.GREEN
ORANGE = BMTTheme.ORANGE
PURPLE = BMTTheme.PURPLE

MODE_MOVE   = "move"
MODE_ROTATE = "rotate"
MODE_SCALE  = "scale"
MODE_SKEW   = "skew"

QUALITY_MAP = {"Low (100%)": 1.0, "Medium (300%)": 3.0,
               "High (600%)": 6.0, "Ultra (1000%)": 10.0}
STEP_VALUES = [0.01, 0.1, 1, 5, 10]

# Skin guide lines: (axis, world_pixel_coord)
# axis="h" → horizontal line at Y=y, axis="v" → vertical at X=x
SKIN_GUIDES = [
    ("h", 95),  ("h", 195), ("h", 245), ("h", 313),
    ("v", 390),
]
# Tag types in SWF that carry a character ID (first 2 body bytes)
_SWF_DEFINE_TYPES = {
    2, 22, 32, 83,   # DefineShape 1-4
    39,              # DefineSprite
    20, 36,          # DefineBitsLossless 1-2
    6, 21, 35, 90,  # DefineBits variants
    10, 48, 75,     # DefineFont variants
    14,             # DefineSound
    11, 33, 37,     # DefineText/EditText
    46,             # DefineMorphShape
    84,             # DefineMorphShape2
}

# ═══════════════════════════════════════════════════════════════════════
#  ICON / CURSOR HELPERS
# ═══════════════════════════════════════════════════════════════════════
_icon_cache: Dict[str, Any] = {}


def _load_icon(name: str, size: Tuple[int, int] = (18, 18)) -> Optional[ctk.CTkImage]:
    key = f"{name}_{size[0]}x{size[1]}"
    if key in _icon_cache:
        return _icon_cache[key]
    
    svg = CURSOR_DIR / f"{name}.svg"
    img = None
    
    if svg.exists():
        img = get_svg_icon(svg, size)
    
    if img is None:
        img = create_svg_fallback(size)
        
    ci = ctk.CTkImage(light_image=img, dark_image=img, size=size)
    _icon_cache[key] = ci
    return ci


# Pre-build cursors for each mode (standard Tk cursors — .cur files unreliable)
_MODE_CURSORS: Dict[str, str] = {}


def _init_cursors():
    _MODE_CURSORS[MODE_MOVE]   = "arrow"
    _MODE_CURSORS[MODE_ROTATE] = "exchange"
    _MODE_CURSORS[MODE_SCALE]  = "sizing"
    _MODE_CURSORS[MODE_SKEW]   = "crosshair"
    _MODE_CURSORS["pan"]       = "fleur"
    _MODE_CURSORS["hand_open"] = "hand2"


class _AbortHandler:
    """Minimal handler for FrameExporter (AbortRetryIgnoreHandler)."""
    def getNewInstance(self):
        return _AbortHandler()
    def handle(self, error):
        return 0


# ═══════════════════════════════════════════════════════════════════════
#  SWF BINARY HELPERS  (pure Python, no JPype needed)
# ═══════════════════════════════════════════════════════════════════════
def _swf_parse_raw_tags(swf_path: str) -> dict:
    """Parse an SWF file (compressed or not) and return
    dict {char_id: raw_bytes_of_whole_tag_record} for tags that have a char ID.
    Also returns (frame_rate, frame_count, rect_bytes) as metadata under
    key -1 = (frame_rate_raw, frame_count, rect_raw_bytes).
    """
    with open(swf_path, "rb") as f:
        data = bytearray(f.read())
    sig = bytes(data[:3])
    version = data[3]
    if sig == b"CWS":
        body = zlib.decompress(bytes(data[8:]))
        data = bytearray(b"FWS" + bytes([version]) + b"\x00"*4 + body)
        struct.pack_into("<I", data, 4, len(data))
    elif sig == b"ZWS":
        import importlib
        zstd = importlib.import_module("zstandard") if importlib.util.find_spec("zstandard") else None
        if zstd:
            offset_inner = 12  # ZWS: sig(3)+ver(1)+uncompressed_len(4)+compressed_len(4) = 12
            body = zstd.decompress(bytes(data[offset_inner:]))
            data = bytearray(b"FWS" + bytes([version]) + b"\x00"*4 + body)
            struct.pack_into("<I", data, 4, len(data))
        else:
            raise ValueError("zstandard module required for ZWS SWF")
    elif sig != b"FWS":
        raise ValueError(f"Unknown SWF sig: {sig}")

    # Parse RECT (bit-packed)
    offset = 8
    nbits = (data[offset] >> 3) & 0x1F
    rect_bit_len = 5 + nbits * 4
    rect_byte_len = (rect_bit_len + 7) // 8
    rect_raw = bytes(data[offset:offset + rect_byte_len])
    offset += rect_byte_len

    frame_rate_raw = struct.unpack_from("<H", data, offset)[0]
    frame_count    = struct.unpack_from("<H", data, offset + 2)[0]
    offset += 4

    result = {-1: (frame_rate_raw, frame_count, rect_raw, version)}

    while offset + 2 <= len(data):
        rec_start = offset
        th = struct.unpack_from("<H", data, offset)[0]
        tag_type = (th >> 6) & 0x3FF
        length   = th & 0x3F
        offset  += 2
        if length == 0x3F:
            length  = struct.unpack_from("<I", data, offset)[0]
            offset += 4
        body_start = offset
        offset    += length
        raw = bytes(data[rec_start:offset])
        if tag_type == 0:
            break
        if tag_type in _SWF_DEFINE_TYPES and length >= 2:
            cid = struct.unpack_from("<H", data, body_start)[0]
            result.setdefault(cid, raw)   # keep first occurrence
    return result


def _swf_write_minimal(raw_tags_dict: dict, target_cid: int, out_path: str):
    """Write a minimal SWF containing exactly the tags in raw_tags_dict
       (values are raw record bytes as returned by _swf_parse_raw_tags),
       plus a PlaceObject2 to place target_cid at depth 1, ShowFrame, End.
    """
    meta = raw_tags_dict.get(-1, (0x1800, 1, None, 8))
    frame_rate_raw, _fc, rect_raw, version = meta

    def _tag_record(tag_type, body: bytes) -> bytes:
        if len(body) < 63:
            return struct.pack("<H", (tag_type << 6) | len(body)) + body
        return struct.pack("<H", (tag_type << 6) | 0x3F) + struct.pack("<I", len(body)) + body

    # Default RECT: 640×480 at 20 TWIP = 12800×9600 units, 14 bits/value
    if rect_raw is None:
        bits = "01110"  # Nbits=14
        for v in (0, 12800, 0, 9600):
            bits += format(v, "014b")
        while len(bits) % 8:
            bits += "0"
        rect_raw = bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))

    buf = bytearray()
    buf += b"FWS" + bytes([version]) + b"\x00\x00\x00\x00"  # filesize placeholder
    buf += rect_raw
    buf += struct.pack("<HH", frame_rate_raw, 1)  # 1 frame

    # FileAttributes (type=69) — required for SWF8+
    buf += _tag_record(69, b"\x08\x00\x00\x00")

    # Write all define tags (skip meta key -1)
    for cid, raw in sorted((k, v) for k, v in raw_tags_dict.items() if k != -1):
        buf += raw

    # PlaceObject2 (type=26): hasChar(0x02)+hasDepth → flags=0x06, depth=1, char_id
    buf += _tag_record(26, struct.pack("<BHH", 0x06, 1, target_cid))
    # ShowFrame (type=1)
    buf += _tag_record(1, b"")
    # End (type=0)
    buf += _tag_record(0, b"")

    # Fix file size
    struct.pack_into("<I", buf, 4, len(buf))
    with open(out_path, "wb") as f:
        f.write(buf)


# ═══════════════════════════════════════════════════════════════════════
#  CACHE & PREFERENCES
# ═══════════════════════════════════════════════════════════════════════
_APP_DIR = os.path.join(os.getenv("APPDATA", tempfile.gettempdir()),
                        "Brawlhalla Modding Toolkit")

def _cache_root():
    b = os.path.join(_APP_DIR, "skin_editor_cache")
    os.makedirs(b, exist_ok=True)
    return b

def _clear_image_cache():
    c = _cache_root()
    if os.path.isdir(c):
        shutil.rmtree(c, ignore_errors=True)
        os.makedirs(c, exist_ok=True)

_PREFS_FILE = os.path.join(_APP_DIR, "skin_editor_prefs.json")
_DEFAULT_PREFS = {"render_mode": "png", "png_quality": 300, "show_grid": True,
                  "bg_color": "#181818", "grid_color": "#202020",
                  "last_swf_dir": "", "last_export_dir": "", "step": 1.0}

def _load_prefs():
    try:
        with open(_PREFS_FILE, "r", encoding="utf-8") as f:
            p = json.load(f)
        for k, v in _DEFAULT_PREFS.items():
            p.setdefault(k, v)
        return p
    except Exception:
        return dict(_DEFAULT_PREFS)

def _save_prefs(p):
    os.makedirs(os.path.dirname(_PREFS_FILE), exist_ok=True)
    try:
        with open(_PREFS_FILE, "w", encoding="utf-8") as f:
            json.dump(p, f, indent=2)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════
@dataclass
class PartData:
    place_tag: Any
    char_id: int
    depth: int
    name: str
    is_sprite: bool
    sx: float = 1.0;  sy: float = 1.0
    r0: float = 0.0;  r1: float = 0.0
    tx: float = 0.0;  ty: float = 0.0
    bx0: float = 0.0; by0: float = 0.0
    bx1: float = 0.0; by1: float = 0.0
    visible: bool = True
    _tree_id: str = ""


@dataclass
class FlatShape:
    shape_id: int
    direct_owner: Any
    owner_sprite_id: int
    ref_owner: Any = None
    a: float = 1.0; b: float = 0.0
    c: float = 0.0; d: float = 1.0
    tx: float = 0.0; ty: float = 0.0
    pa: float = 1.0; pb: float = 0.0
    pc: float = 0.0; pd: float = 1.0
    ptx: float = 0.0; pty: float = 0.0
    depth: int = 0
    bounds: Tuple[float, float, float, float] = (0, 0, 0, 0)
    base_image: Any = None
    photo: Any = None
    canvas_id: int = 0
    # Imagen ya transformada en espacio canvas (para hit-test de transparencia)
    canvas_img: Any = None   # PIL.Image o None
    canvas_img_x0: int = 0   # esquina superior-izquierda en canvas
    canvas_img_y0: int = 0
    # ── Zoom-aware render cache (keyed by module-level _shape_render_cache) ──
    # Not stored per-shape — the module holds the shared cache dict.



# ═══════════════════════════════════════════════════════════════════════
#  MATRIX HELPERS
# ═══════════════════════════════════════════════════════════════════════
def _mul(a1, b1, c1, d1, tx1, ty1, a2, b2, c2, d2, tx2, ty2):
    return (a1*a2 + b1*c2, a1*b2 + b1*d2,
            c1*a2 + d1*c2, c1*b2 + d1*d2,
            a1*tx2 + b1*ty2 + tx1, c1*tx2 + d1*ty2 + ty1)


def _inv_linear(a, b, c, d):
    det = a*d - b*c
    if abs(det) < 1e-15:
        return (1, 0, 0, 1)
    return (d/det, -b/det, -c/det, a/det)


def _point_in_quad(px, py, pts):
    n = len(pts)
    if n < 3:
        return False
    sign = None
    j = n - 1
    for i in range(n):
        x1, y1 = pts[j]; x2, y2 = pts[i]
        cross = (x2-x1)*(py-y1) - (y2-y1)*(px-x1)
        if sign is None:
            sign = cross >= 0
        elif (cross >= 0) != sign:
            # Fall back to AABB
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            return min(xs) <= px <= max(xs) and min(ys) <= py <= max(ys)
        j = i
    return True


# ╔═════════════════════════════════════════════════════════════════════╗
# ║  MODULE                                                            ║
# ╚═════════════════════════════════════════════════════════════════════╝
class SkinEditorModule(ToolModule):

    def get_tool_name(self):
        return "Skin Editor"

    def get_tool_icon(self):
        return "ae"

    # ──────────────────────────────────────────────────────────────────
    #  INIT
    # ──────────────────────────────────────────────────────────────────
    def __init__(self, parent, game_path, mods_path, icons=None):
        self.prefs = _load_prefs()
        _init_cursors()

        # SWF data
        self.swf = None
        self.swf_path = ""
        self.tag_dict: Dict[int, Any] = {}
        self.shape_tags: Dict[int, Any] = {}
        self.sprite_tags: Dict[int, Any] = {}
        self.shape_images: Dict[int, Image.Image] = {}
        self._svg_paths: Dict[int, str] = {}
        self._svg_raster_cache: Dict[Tuple, Image.Image] = {}
        self._cache_dir = _cache_root()
        self.export_zoom = self.prefs.get("png_quality", 300) / 100.0
        self.render_mode = self.prefs.get("render_mode", "png")
        # Zoom-level render cache: flushed when zoom changes beyond threshold
        # Maps shape_id -> {zoom_bucket: PhotoImage}
        self._shape_render_cache: dict = {}
        self._render_cache_zoom: float = 0.0   # last zoom that populated cache
        # Skia SVG DOMs
        self._svg_doms: Dict[int, Any] = {}


        self.sprite_parts: Dict[int, List[PartData]] = {}
        self.ref_sprite_id: int = -1
        self.edit_sprite_id: int = -1
        self.ref_shapes: List[FlatShape] = []
        self.edit_shapes: List[FlatShape] = []
        
        # Colección de IDs de items tildados en el Treeview para Select Mode
        self.checked_tids = set()

        self._rv = [1.0, 0.0, 0.0]  # ref  [zoom, panx, pany]
        self._ev = [1.0, 0.0, 0.0]  # edit
        self._rw = self._rh = 400
        self._ew = self._eh = 400

        # selection
        self.selected_part: Optional[PartData] = None
        self.selected_sprite_id: int = -1
        self.mode = MODE_MOVE

        # rotation pivot offset from selection center (view-space)
        self._pivot_offset = (0.0, 0.0)

        # drag
        self._active_canvas = None
        self._drag = ""
        self._drag_handle = ""
        self._drag_sx = self._drag_sy = 0
        self._drag_orig: dict = {}
        self._drag_anchor_v = (0.0, 0.0)
        self._drag_orig_bbox = None
        # FIXED: saved pivot for rotation (canvas coords, set once at drag start)
        self._drag_pivot_c: Tuple[float, float] = (0.0, 0.0)
        self._drag_mouse_start_angle = 0.0
        self._drag_mat_start_angle = 0.0
        self._drag_parent_mat = (1, 0, 0, 1, 0, 0)
        self._drag_throttle_id = None
        self._drag_mx = self._drag_my = 0
        self._shift = False

        # pan
        self._pan = False
        self._pan_sx = self._pan_sy = 0
        self._pan_orig = [0.0, 0.0]
        self._pan_view = None
        self._pan_tag = ""
        self._pan_last_dx = 0
        self._pan_last_dy = 0
        self._space_held = False

        # undo / redo
        self._undo: list = []
        self._redo: list = []
        self._photo_refs: list = []
        self._photo_refs_ref: list = []
        self._snapshot: list = []

        # gizmo cache
        self._sel_bbox = None
        self._sel_center_c = None

        # clipboard for copy/paste
        self._matrix_clipboard: Optional[dict] = None

        # step
        self._step = float(self.prefs.get("step", 1.0))

        # guide lines & overlay state (set as plain attrs, toggled via BooleanVar in UI)
        self._show_skin_guide    = True
        self._show_green_line    = True   # origin cross/center line
        self._show_edit_highlight = False # tint current-editing shape on ref canvas (OFF by default)
        self._highlight_color    = "#FFAA00"  # colour used for the shape tint
        self._uniform_scale      = True   # lock X/Y scale together (activado por defecto)
        self._guide_color        = "#424242"  # color for skin guide lines
        # Highlight fade state
        self._hl_alpha: int        = 0      # current alpha 0-80
        self._hl_fading_in: bool   = True
        self._hl_fade_id           = None   # after() id for fade loop
        self._hl_fade_running: bool = False
        # Reference skin overlay state
        self._ref_skin_enabled: bool   = False
        self._ref_skin_img_pil         = None  # PIL Image (original full res)
        self._ref_skin_photo           = None  # ImageTk.PhotoImage (cached)
        self._ref_skin_scale: float    = 0.50  # scale factor (50% default)
        self._ref_skin_ox: float       = 581.0 # pixel offset X from canvas center
        self._ref_skin_oy: float       = 278.0 # pixel offset Y from canvas center
        self._ref_skin_opacity: int    = 60    # 0-100 %
        self._ref_skin_front: bool     = False # draw in front of sprites?
        self._ref_skin_panel_open: bool = True

        # search filter text
        self._ref_search_text  = ""
        self._edit_search_text = ""

        # stored tree item IDs for filter restore
        self._all_ref_tree_ids:  list = []
        self._all_edit_tree_ids: list = []  # list of (tid, parent_id) tuples
        self._all_ref_opts:  list = []  # all sprite display strings for ref selector
        self._all_edit_opts: list = []  # all sprite display strings for edit selector

        # widgets (set in create_ui)
        self.ref_canvas: Optional[tk.Canvas] = None
        self.edit_canvas: Optional[tk.Canvas] = None
        self.tree: Optional[ttk.Treeview] = None
        self.edit_tree: Optional[ttk.Treeview] = None
        self.status_var = None
        self.coords_var = None
        self.mode_var = None
        self.hover_var = None
        self.prop_entries: Dict[str, ctk.CTkEntry] = {}
        self.prop_sliders: Dict[str, ctk.CTkSlider] = {}
        self.prop_name_label = None
        self.show_grid = None
        self.ref_selector = None
        self.edit_selector = None
        self.btn_mode_g = self.btn_mode_r = self.btn_mode_s = self.btn_mode_k = None
        self.btn_paste = None
        self.btn_reload = None
        self.btn_save = None
        self.btn_apply = None
        self.btn_cancel = None
        self.btn_export = None
        self.ref_title_label = None
        self.edit_title_label = None
        self.zoom_label_ref = None
        self.zoom_label_edit = None
        # BooleanVar toggles (created in create_ui)
        self._var_skin_guide:     Optional[tk.BooleanVar] = None
        self._var_green_line:     Optional[tk.BooleanVar] = None
        self._var_edit_highlight: Optional[tk.BooleanVar] = None
        self._var_show_ids:       Optional[tk.BooleanVar] = None
        self._var_uniform_scale:  Optional[tk.BooleanVar] = None
        self._var_guide_front:    Optional[tk.BooleanVar] = None  # draw guides in front of shapes
        self._var_select_mode:    Optional[tk.BooleanVar] = None  # select mode for tree checkboxes
        self._var_ref_skin:       Optional[tk.BooleanVar] = None  # reference skin overlay toggle
        self._sprite_id_map_ref: Dict[str, int] = {}
        self._sprite_id_map_edit: Dict[str, int] = {}
        self._part_tree_map: Dict[str, Tuple[PartData, int]] = {}
        self._sprite_tid_map: Dict[int, str] = {}
        self._tree_lock: bool = False  # guard: prevents tree events during programmatic selection
        self.selected_parts: list = []  # multi-selection list
        self._drag_orig_multi: dict = {}  # part -> original state snapshot for drag
        self._tid_to_sid: dict = {}     # tree-item-id -> sprite_id reverse map
        self._loading = False
        self._depth_ctr = 0

        super().__init__(parent, game_path, mods_path, icons=icons)

    # ═══════════════════════════════════════════════════════════════════
    #  UI
    # ═══════════════════════════════════════════════════════════════════
    def create_ui(self):
        self._setup_dark_styles()
        self.main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True)
        # Initialise toggle BooleanVars (must be created after root exists)
        self._var_skin_guide     = tk.BooleanVar(value=self._show_skin_guide)
        self._var_green_line     = tk.BooleanVar(value=self._show_green_line)
        self._var_edit_highlight = tk.BooleanVar(value=False)  # OFF by default
        self._var_show_ids       = tk.BooleanVar(value=False)
        self._var_uniform_scale  = tk.BooleanVar(value=self._uniform_scale)
        self._var_guide_front    = tk.BooleanVar(value=False)  # guides behind shapes by default
        self._var_select_mode    = tk.BooleanVar(value=False)  # Select Mode OFF by default
        self._var_ref_skin       = tk.BooleanVar(value=False)  # Ref skin OFF by default
        self._build_toolbar()
        body = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=4, pady=(0, 2))
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        self._body = body  # referencia para colapso
        self._left_collapsed = False
        self._props_collapsed = False
        self._build_left_panel(body)
        self._build_split_canvas(body)
        self._build_props(body)
        self._build_bottom_bar()
        self._build_statusbar()
        self._bind_keys()

    def _setup_dark_styles(self):
        s = ttk.Style(); s.theme_use("clam")
        s.configure("SE.Treeview", background=BGI, foreground=FGT,
                     fieldbackground=BGI, selectbackground=BMTTheme.adjust_brightness(BMTTheme.BG_SUBPANEL, 0.2),
                     selectforeground=BMTTheme.WHITE, rowheight=26,
                     font=("Roboto", 10), relief="flat", borderwidth=0)
        s.configure("SE.Treeview.Heading", background=BMTTheme.adjust_brightness(BMTTheme.BG_PANEL, 0.1),
                     foreground=FGT, font=("Roboto", 10, "bold"),
                     relief="flat", borderwidth=0, padding=2)
        s.map("SE.Treeview",
              background=[("selected", "#252530"), ("focus", "#2E2E3E")],
              foreground=[("selected", "#FFFFFF"), ("focus", "#FFFFFF")])
        s.configure("SE.Vertical.TScrollbar", background="#333",
                     troughcolor=BGI, borderwidth=0, relief="flat",
                     width=10, arrowsize=10)
        s.map("SE.Vertical.TScrollbar",
              background=[("active", "#555"), ("pressed", "#666")])
        s.layout("SE.Treeview", [("Treeview.field", {"sticky": "nswe",
                  "border": 0, "children": [("Treeview.padding",
                  {"sticky": "nswe", "children": [("Treeview.treearea",
                  {"sticky": "nswe"})]})]})])

        # Custom collapse/expand indicator icons
        from PIL import Image as _Img, ImageTk as _ITk  # local import for safety
        _icon_dir = RESOURCES / "assets" / "IconsNew"
        try:
            _img_closed = _Img.open(
                _icon_dir / "arrow_right_24dp_E3E3E3_FILL0_wght500_GRAD0_opsz24.png"
            ).resize((16, 16), _Img.LANCZOS)
            _img_open = _Img.open(
                _icon_dir / "arrow_drop_down_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.png"
            ).resize((16, 16), _Img.LANCZOS)
            _img_chk_on = _Img.open(
                _icon_dir / "check_box_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.png"
            ).resize((16, 16), _Img.LANCZOS)
            _img_chk_off = _Img.open(
                _icon_dir / "check_box_outline_blank_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.png"
            ).resize((16, 16), _Img.LANCZOS)
            self._ico_tree_closed  = _ITk.PhotoImage(_img_closed)
            self._ico_tree_open    = _ITk.PhotoImage(_img_open)
            self._ico_chk_on       = _ITk.PhotoImage(_img_chk_on)
            self._ico_chk_off      = _ITk.PhotoImage(_img_chk_off)
            # Override the Treeview Item indicator images
            s.element_create("SE.Treeview.Item.indicator", "image",
                             self._ico_tree_closed,
                             ("user2", "", self._ico_tree_open),
                             sticky="w", width=20, border=4)
        except Exception as _e:
            print(f"[SE] Tree indicators: {_e}")
            self._ico_chk_on = getattr(self, "_ico_chk_on", None)
            self._ico_chk_off = getattr(self, "_ico_chk_off", None)

    # ── Toolbar ───────────────────────────────────────────────────────
    def _build_toolbar(self):
        tb = ctk.CTkFrame(self.main_frame, height=46, fg_color=BGP,
                          corner_radius=8)
        tb.pack(fill="x", padx=4, pady=4); tb.pack_propagate(False)

        ico_plus     = _load_icon("plus", (14, 14))
        ico_rotate   = _load_icon("rotate_cw", (14, 14))
        ico_skew     = _load_icon("skew_horizontal", (14, 14))
        ico_resize   = _load_icon("resize_a_cross_diagonal", (14, 14))
        ico_pointer  = _load_icon("pointer_a", (14, 14))
        ico_zoom     = _load_icon("zoom", (14, 14))

        B  = dict(height=30, corner_radius=BMTTheme.CORNER_RADIUS)
        Bg = dict(fg_color=BMTTheme.BG_SUBPANEL, hover_color=BMTTheme.adjust_brightness(BMTTheme.BG_SUBPANEL, 0.2), text_color=FGT)

        title_lbl = ctk.CTkLabel(tb, text="Skin Editor", font=BMTTheme.get_font(15, "bold"))
        BMTTheme.style_title(title_lbl, color=AC)
        title_lbl.pack(side="left", padx=(10, 6))
        _sep(tb)

        self.btn_load = ctk.CTkButton(
            tb, text="Open", width=85, image=ico_plus,
            command=self._load_swf_dialog, **B)
        BMTTheme.style_primary_button(self.btn_load, color=AC)
        self.btn_load.configure(text_color=BMTTheme.BLACK) # Black text on yellow looks better
        self.btn_load.pack(side="left", padx=2, pady=7)

        self.btn_reload = ctk.CTkButton(tb, text="Reload", width=75, command=self._reload_swf, **B)
        BMTTheme.style_secondary_button(self.btn_reload)
        self.btn_reload.pack(side="left", padx=2, pady=7)

        self.btn_save = ctk.CTkButton(tb, text="Save", width=70, command=self._save_swf_dialog, state="disabled", **B)
        BMTTheme.style_secondary_button(self.btn_save)
        self.btn_save.pack(side="left", padx=2, pady=7)

        self.btn_export = ctk.CTkButton(tb, text="Export", width=75, command=self._show_export_dialog, state="disabled", **B)
        BMTTheme.style_secondary_button(self.btn_export)
        self.btn_export.pack(side="left", padx=2, pady=7)
        _sep(tb)

        # mode buttons — compact with icons
        self.btn_mode_g = ctk.CTkButton(tb, text=" G", width=42, image=ico_pointer, command=lambda: self._set_mode(MODE_MOVE), **B)
        BMTTheme.style_secondary_button(self.btn_mode_g)
        self.btn_mode_g.pack(side="left", padx=1, pady=7)

        self.btn_mode_r = ctk.CTkButton(tb, text=" R", width=42, image=ico_rotate, command=lambda: self._set_mode(MODE_ROTATE), **B)
        BMTTheme.style_secondary_button(self.btn_mode_r)
        self.btn_mode_r.pack(side="left", padx=1, pady=7)

        self.btn_mode_s = ctk.CTkButton(tb, text=" S", width=42, image=ico_resize, command=lambda: self._set_mode(MODE_SCALE), **B)
        BMTTheme.style_secondary_button(self.btn_mode_s)
        self.btn_mode_s.pack(side="left", padx=1, pady=7)

        self.btn_mode_k = ctk.CTkButton(tb, text=" K", width=42, image=ico_skew, command=lambda: self._set_mode(MODE_SKEW), **B)
        BMTTheme.style_secondary_button(self.btn_mode_k)
        self.btn_mode_k.pack(side="left", padx=1, pady=7)
        _sep(tb)

        # Botón de ventana de referencia
        self.btn_open_ref = ctk.CTkButton(tb, text="Load Reference", width=120, command=self._open_reference_window, **B)
        BMTTheme.style_primary_button(self.btn_open_ref, color=AC)
        self.btn_open_ref.configure(text_color=BMTTheme.BLACK)
        self.btn_open_ref.pack(side="left", padx=2, pady=7)

        self.show_grid = tk.BooleanVar(value=self.prefs.get("show_grid", True))
        self._ref_window = None  # referencia a la ventana de referencia

        # right side
        self.btn_redo = ctk.CTkButton(tb, text="Redo", width=55, command=self._do_redo, state="disabled", **B)
        BMTTheme.style_secondary_button(self.btn_redo)
        self.btn_redo.pack(side="right", padx=2, pady=7)
        self.btn_undo = ctk.CTkButton(tb, text="Undo", width=55, command=self._do_undo, state="disabled", **B)
        BMTTheme.style_secondary_button(self.btn_undo)
        self.btn_undo.pack(side="right", padx=2, pady=7)
        _sep(tb, side="right")
        self.btn_options = ctk.CTkButton(tb, text="Options", width=75, command=self._show_options, **B)
        BMTTheme.style_secondary_button(self.btn_options)
        self.btn_options.pack(side="right", padx=2, pady=7)

    # ── Left panel ────────────────────────────────────────────────────
    def _build_left_panel(self, par):
        # Contenedor con botón de colapso
        wrap = ctk.CTkFrame(par, fg_color="transparent")
        wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 0))
        wrap.rowconfigure(0, weight=1)
        wrap.columnconfigure(0, weight=1)

        fr = ctk.CTkFrame(wrap, width=270, fg_color=BGP, corner_radius=8)
        fr.grid(row=0, column=0, sticky="nsew")
        fr.grid_propagate(False)
        self._left_panel_frame = fr
        self._left_panel_wrap = wrap

        # Botón para colapsar (flecha)
        self._left_collapse_btn = ctk.CTkButton(
            wrap, text="", image=BMTTheme.get_icon("arrow_left", size=20), width=16, height=50, corner_radius=4,
            fg_color="#2A2A2A", hover_color="#3A3A3A", text_color=FGT,
            font=("Segoe UI", 12), command=self._toggle_left_panel)
        self._left_collapse_btn.grid(row=0, column=1, sticky="ns", pady=4)

        ctk.CTkLabel(fr, text="Reference Sprite", font=("Segoe UI", 12, "bold"),
                     text_color=AC).pack(padx=8, pady=(8, 2), anchor="w")
        self.ref_selector = ctk.CTkComboBox(
            fr, values=["(no SWF)"], width=250, height=28,
            fg_color=BGI, border_color="#333", button_color=ACD,
            dropdown_fg_color=BGI, text_color=FGT,
            font=("Segoe UI", 11), command=self._on_ref_selected)
        self.ref_selector.pack(padx=8, pady=2)

        ctk.CTkLabel(fr, text="Reference Parts",
                     font=("Segoe UI", 11, "bold"),
                     text_color=FGD).pack(padx=8, pady=(4, 2), anchor="w")
        tc1 = ctk.CTkFrame(fr, fg_color=BGI, corner_radius=6, height=130)
        tc1.pack(fill="x", padx=8, pady=2); tc1.pack_propagate(False)
        self.tree = ttk.Treeview(tc1, style="SE.Treeview",
                                 columns=("id", "type"),
                                 show="tree headings",
                                 selectmode="browse", height=5)
        self.tree.heading("#0", text="Name"); self.tree.heading("id", text="ID")
        self.tree.heading("type", text="Type")
        self.tree.column("#0", width=120, minwidth=50)
        self.tree.column("id", width=40, minwidth=30)
        self.tree.column("type", width=50, minwidth=30)
        vsb1 = ctk.CTkScrollbar(tc1, orientation="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb1.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb1.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_ref_tree_select)

        ctk.CTkFrame(fr, height=1, fg_color="#2A2A2A").pack(fill="x", padx=8, pady=4)

        # ── Editor: árbol jerárquico siempre visible ─────────────────────
        hdr_e = ctk.CTkFrame(fr, fg_color="transparent", height=22)
        hdr_e.pack(fill="x", padx=8, pady=(2, 0))
        ctk.CTkLabel(hdr_e, text="Editor Sprites", font=("Segoe UI", 12, "bold"),
                     text_color=GREEN).pack(side="left")
        # Select Mode toggle — right side of header
        self._select_mode_btn = ctk.CTkButton(
            hdr_e, text="Select Mode: OFF", width=110, height=20,
            fg_color="#2A2A2A", hover_color="#3A3A3A", text_color=FGD,
            font=("Segoe UI", 9), corner_radius=4,
            command=self._toggle_select_mode)
        # self._select_mode_btn.pack(side="right", padx=2)

        # Barra de búsqueda funcional que filtra en el árbol
        self._edit_search_var = tk.StringVar()
        self._edit_search_var.trace_add("write",
            lambda *_: self._filter_edit_tree(self._edit_search_var.get()))
        ctk.CTkEntry(fr, textvariable=self._edit_search_var,
                     placeholder_text="Search sprites/parts...", height=24,
                     width=250, fg_color=BGI, border_color="#333",
                     text_color=FGT, font=("Segoe UI", 10)
                     ).pack(padx=8, pady=(4, 2))

        # Treeview jerárquico: DefineSprite -> PlaceObject2 (sin columnas extra)
        tc2 = ctk.CTkFrame(fr, fg_color=BGI, corner_radius=6)
        tc2.pack(fill="both", expand=True, padx=8, pady=2)
        self.edit_tree = ttk.Treeview(tc2, style="SE.Treeview",
                                      columns=(),
                                      show="tree",
                                      selectmode="extended")
        self.edit_tree.column("#0", width=250, minwidth=80)
        vsb2 = ctk.CTkScrollbar(tc2, orientation="vertical", command=self.edit_tree.yview)
        self.edit_tree.configure(yscrollcommand=vsb2.set)
        self.edit_tree.pack(side="left", fill="both", expand=True)
        vsb2.pack(side="right", fill="y")
        self.edit_tree.bind("<<TreeviewSelect>>",  self._on_edit_tree_select)
        self.edit_tree.bind("<Button-1>",          self._on_edit_tree_click)
        self.edit_tree.bind("<Button-3>",          self._on_edit_tree_rclick)
        self.edit_tree.bind("<Double-Button-1>",   self._on_edit_tree_double)

        # Botones de acción
        bf = ctk.CTkFrame(fr, height=30, fg_color="transparent")
        bf.pack(fill="x", padx=8, pady=(2, 6))
        bs = dict(height=26, corner_radius=4, font=("Segoe UI", 10))
        ctk.CTkButton(bf, text="Show All", width=75, fg_color="#2A2A2A",
                      hover_color="#3A3A3A", text_color=FGT,
                      command=self._show_all, **bs).pack(side="left", padx=2)
        ctk.CTkButton(bf, text="Hide", width=60, fg_color="#2A2A2A",
                      hover_color="#3A3A3A", text_color=FGT,
                      command=self._toggle_vis, **bs).pack(side="left", padx=2)
        ctk.CTkButton(bf, text="Fit", width=50, fg_color="#2A2A2A",
                      hover_color="#3A3A3A", text_color=FGT,
                      command=lambda: self._fit_view("edit"), **bs
                      ).pack(side="left", padx=2)

        # Variables de compatibilidad (edit_selector ya no es ComboBox)
        self._ref_sel_search_var  = tk.StringVar()
        self._edit_sel_search_var = tk.StringVar()
        self.edit_selector = None  # ya no existe, usamos el árbol directamente

    # ── Split canvas ──────────────────────────────────────────────────
    def _build_split_canvas(self, par):
        split = ctk.CTkFrame(par, fg_color=BGP, corner_radius=8)
        split.grid(row=0, column=1, sticky="nsew", padx=4)
        split.columnconfigure(0, weight=1); split.columnconfigure(1, weight=1)
        split.rowconfigure(1, weight=1)

        _ck = dict(fg_color=AC, hover_color=ACD, text_color=FGT,
                   font=("Segoe UI", 10))

        # ── ref (left) ──
        rf = ctk.CTkFrame(split, fg_color=BGP, corner_radius=4)
        rf.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(4, 2), pady=4)
        rf.rowconfigure(1, weight=1)

        # title row
        hdr_r = ctk.CTkFrame(rf, fg_color="transparent", height=22)
        hdr_r.pack(fill="x", padx=6, pady=(2, 0))
        self.ref_title_label = ctk.CTkLabel(
            hdr_r, text="Reference View", font=("Segoe UI", 11, "bold"),
            text_color=AC)
        self.ref_title_label.pack(side="left")
        self.zoom_label_ref = ctk.CTkLabel(hdr_r, text="100%",
                                           font=("Segoe UI", 10), text_color=FGD)
        self.zoom_label_ref.pack(side="right", padx=4)

        # checkbox row for reference overlays
        ck_row_r = ctk.CTkFrame(rf, fg_color="transparent", height=22)
        ck_row_r.pack(fill="x", padx=6, pady=(0, 2))
        ctk.CTkCheckBox(ck_row_r, text="Skin Guide", variable=self._var_skin_guide,
                        command=self._redraw_ref, width=20, **_ck
                        ).pack(side="left", padx=4)
        # guide color button (shows current color)
        self._guide_color_btn = ctk.CTkButton(
            ck_row_r, text="Color", width=46, height=18, corner_radius=4,
            fg_color=self._guide_color, hover_color="#6A6A6A",
            text_color="#FFFFFF" if self._guide_color < "#888888" else "#000000",
            font=("Segoe UI", 9),
            command=self._pick_guide_color)
        self._guide_color_btn.pack(side="left", padx=2)
        ctk.CTkCheckBox(ck_row_r, text="Front", variable=self._var_guide_front,
                        command=self._redraw_ref, width=20, **_ck
                        ).pack(side="left", padx=2)
        ctk.CTkCheckBox(ck_row_r, text="Center Line", variable=self._var_green_line,
                        command=self._redraw_all, width=20, **_ck
                        ).pack(side="left", padx=4)
        ctk.CTkCheckBox(ck_row_r, text="Highlight Edit", variable=self._var_edit_highlight,
                        command=self._redraw_ref, width=20, **_ck
                        ).pack(side="left", padx=4)
        ctk.CTkCheckBox(ck_row_r, text="IDs", variable=self._var_show_ids,
                        command=self._redraw_all, width=20, **_ck
                        ).pack(side="left", padx=4)

        # ── Reference Skin Overlay ────────────────────────────────────────
        ref_skin_hdr = ctk.CTkFrame(rf, fg_color="transparent")
        ref_skin_hdr.pack(fill="x", padx=6, pady=(2, 0))
        ctk.CTkCheckBox(
            ref_skin_hdr, text="Reference Skin",
            variable=self._var_ref_skin,
            command=self._on_ref_skin_toggle,
            font=("Segoe UI", 10, "bold"), text_color="#88AAFF",
            fg_color="#3B82F6", hover_color="#2563EB", width=20
        ).pack(side="left", padx=4)
        self._ref_skin_toggle_btn = ctk.CTkButton(
            ref_skin_hdr, text="", image=BMTTheme.get_icon("arrow_right", size=20), width=22, height=18, corner_radius=4,
            fg_color="#2A2A2A", hover_color="#3A3A3A", text_color=FGD,
            font=("Segoe UI", 10), command=self._toggle_ref_skin_panel)
        self._ref_skin_toggle_btn.pack(side="right", padx=2)

        # Collapsible panel for ref skin controls
        self._ref_skin_panel = ctk.CTkFrame(rf, fg_color="#1A1A2A", corner_radius=6)
        self._ref_skin_panel_open = False
        # Row 1: Opacity
        _rsp_r1 = ctk.CTkFrame(self._ref_skin_panel, fg_color="transparent")
        _rsp_r1.pack(fill="x", padx=6, pady=(4, 0))
        ctk.CTkLabel(_rsp_r1, text="Opacity", font=("Segoe UI", 9), text_color=FGD, width=50).pack(side="left")
        self._ref_skin_opacity_var = tk.IntVar(value=self._ref_skin_opacity)
        self._ref_skin_opacity_slider = ctk.CTkSlider(
            _rsp_r1, from_=0, to=100, variable=self._ref_skin_opacity_var,
            width=120, height=14, command=self._on_ref_skin_opacity_change)
        self._ref_skin_opacity_slider.pack(side="left", padx=4)
        self._ref_skin_opacity_lbl = ctk.CTkLabel(_rsp_r1, text="60%", font=("Segoe UI", 9), text_color=FGD, width=30)
        self._ref_skin_opacity_lbl.pack(side="left")
        # Row 2: Scale + Z-order
        _rsp_r2 = ctk.CTkFrame(self._ref_skin_panel, fg_color="transparent")
        _rsp_r2.pack(fill="x", padx=6, pady=(2, 0))
        ctk.CTkLabel(_rsp_r2, text="Scale%", font=("Segoe UI", 9), text_color=FGD, width=50).pack(side="left")
        self._ref_skin_scale_var = tk.StringVar(value="50")
        self._ref_skin_scale_entry = ctk.CTkEntry(
            _rsp_r2, textvariable=self._ref_skin_scale_var,
            width=48, height=20, fg_color=BGI, border_color="#333",
            text_color=FGT, font=("Segoe UI", 9))
        self._ref_skin_scale_entry.pack(side="left", padx=2)
        self._ref_skin_scale_entry.bind("<Return>", lambda e: self._on_ref_skin_scale_change())
        self._ref_skin_scale_entry.bind("<FocusOut>", lambda e: self._on_ref_skin_scale_change())
        self._var_ref_skin_front = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            _rsp_r2, text="Front", variable=self._var_ref_skin_front,
            command=self._redraw_ref, width=20,
            fg_color="#555", hover_color="#666", font=("Segoe UI", 9), text_color=FGD
        ).pack(side="right", padx=4)
        # Row 3: Position X Y
        _rsp_r3 = ctk.CTkFrame(self._ref_skin_panel, fg_color="transparent")
        _rsp_r3.pack(fill="x", padx=6, pady=(2, 4))
        ctk.CTkLabel(_rsp_r3, text="Pos X", font=("Segoe UI", 9), text_color=FGD, width=36).pack(side="left")
        self._ref_skin_ox_var = tk.StringVar(value="581")
        self._ref_skin_ox_entry = ctk.CTkEntry(
            _rsp_r3, textvariable=self._ref_skin_ox_var,
            width=48, height=20, fg_color=BGI, border_color="#333",
            text_color=FGT, font=("Segoe UI", 9))
        self._ref_skin_ox_entry.pack(side="left", padx=2)
        self._ref_skin_ox_entry.bind("<Return>", lambda e: self._on_ref_skin_pos_change())
        self._ref_skin_ox_entry.bind("<FocusOut>", lambda e: self._on_ref_skin_pos_change())
        ctk.CTkLabel(_rsp_r3, text="Y", font=("Segoe UI", 9), text_color=FGD, width=14).pack(side="left")
        self._ref_skin_oy_var = tk.StringVar(value="278")
        self._ref_skin_oy_entry = ctk.CTkEntry(
            _rsp_r3, textvariable=self._ref_skin_oy_var,
            width=48, height=20, fg_color=BGI, border_color="#333",
            text_color=FGT, font=("Segoe UI", 9))
        self._ref_skin_oy_entry.pack(side="left", padx=2)
        self._ref_skin_oy_entry.bind("<Return>", lambda e: self._on_ref_skin_pos_change())
        self._ref_skin_oy_entry.bind("<FocusOut>", lambda e: self._on_ref_skin_pos_change())

        bgc = self.prefs.get("bg_color", "#181818")
        self.ref_canvas = tk.Canvas(rf, bg=bgc, highlightthickness=0,
                                    cursor=_MODE_CURSORS.get(MODE_MOVE, "crosshair"))
        self.ref_canvas.pack(fill="both", expand=True, padx=2, pady=(0, 4))

        # ── edit (right) ──
        ef = ctk.CTkFrame(split, fg_color=BGP, corner_radius=4)
        ef.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(2, 4), pady=4)
        ef.rowconfigure(1, weight=1)

        hdr_e = ctk.CTkFrame(ef, fg_color="transparent", height=22)
        hdr_e.pack(fill="x", padx=6, pady=(2, 0))
        self.edit_title_label = ctk.CTkLabel(
            hdr_e, text="Editor View", font=("Segoe UI", 11, "bold"),
            text_color=GREEN)
        self.edit_title_label.pack(side="left")
        self.zoom_label_edit = ctk.CTkLabel(hdr_e, text="100%",
                                            font=("Segoe UI", 10), text_color=FGD)
        self.zoom_label_edit.pack(side="right", padx=4)

        # checkbox row for editor overlays
        ck_row_e = ctk.CTkFrame(ef, fg_color="transparent", height=22)
        ck_row_e.pack(fill="x", padx=6, pady=(0, 2))
        ctk.CTkCheckBox(ck_row_e, text="Center Line", variable=self._var_green_line,
                        command=self._redraw_all, width=20, **_ck
                        ).pack(side="left", padx=4)
        ctk.CTkCheckBox(ck_row_e, text="Grid", variable=self.show_grid,
                        command=self._redraw_all, width=20, **_ck
                        ).pack(side="left", padx=4)
        self._var_snap_pixel = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(ck_row_e, text="Snap px", variable=self._var_snap_pixel,
                        width=20, **_ck).pack(side="left", padx=4)
        self._var_show_pivot = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(ck_row_e, text="Pivot", variable=self._var_show_pivot,
                        command=self._redraw_edit, width=20, **_ck
                        ).pack(side="left", padx=4)
        self._var_show_bounds = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(ck_row_e, text="Bounds", variable=self._var_show_bounds,
                        command=self._redraw_edit, width=20, **_ck
                        ).pack(side="left", padx=4)

        bgc = self.prefs.get("bg_color", "#181818")
        self.edit_canvas = tk.Canvas(ef, bg=bgc, highlightthickness=0,
                                     cursor=_MODE_CURSORS.get(MODE_MOVE, "crosshair"))
        self.edit_canvas.pack(fill="both", expand=True, padx=2, pady=(0, 4))

        for cv, tag in ((self.ref_canvas, "ref"), (self.edit_canvas, "edit")):
            cv.bind("<Configure>", lambda e, t=tag: self._on_cv_resize(e, t))
            cv.bind("<ButtonPress-1>", lambda e, t=tag: self._on_click(e, t))
            cv.bind("<B1-Motion>", lambda e, t=tag: self._on_drag(e, t))
            cv.bind("<ButtonRelease-1>", lambda e, t=tag: self._on_release(e, t))
            cv.bind("<ButtonPress-2>", lambda e, t=tag: self._pan_start(e, t))
            cv.bind("<B2-Motion>", lambda e, t=tag: self._pan_move(e, t))
            cv.bind("<ButtonRelease-2>", lambda e, t=tag: self._pan_end(e, t))
            cv.bind("<ButtonPress-3>", lambda e, t=tag: self._pan_start(e, t))
            cv.bind("<B3-Motion>", lambda e, t=tag: self._pan_move(e, t))
            cv.bind("<ButtonRelease-3>", lambda e, t=tag: self._pan_end(e, t))
            cv.bind("<MouseWheel>", lambda e, t=tag: self._on_scroll(e, t))
            cv.bind("<Motion>", lambda e, t=tag: self._on_motion(e, t))

    # ── Properties panel ──────────────────────────────────────────────
    def _build_props(self, par):
        # Contenedor con botón de colapso
        wrap_p = ctk.CTkFrame(par, fg_color="transparent")
        wrap_p.grid(row=0, column=2, sticky="nsew", padx=(0, 0))
        wrap_p.rowconfigure(0, weight=1)
        wrap_p.columnconfigure(1, weight=1)

        pf = ctk.CTkFrame(wrap_p, width=285, fg_color=BGP, corner_radius=8)
        pf.grid(row=0, column=1, sticky="nsew")
        pf.grid_propagate(False)
        self._props_panel_frame = pf
        self._props_panel_wrap = wrap_p

        # Botón para colapsar (flecha)
        self._props_collapse_btn = ctk.CTkButton(
            wrap_p, text="", image=BMTTheme.get_icon("arrow_right", size=20), width=16, height=50, corner_radius=4,
            fg_color="#2A2A2A", hover_color="#3A3A3A", text_color=FGT,
            font=("Segoe UI", 12), command=self._toggle_props_panel)
        self._props_collapse_btn.grid(row=0, column=0, sticky="ns", pady=4)

        ctk.CTkLabel(pf, text="Properties", font=("Segoe UI", 14, "bold"),
                     text_color=AC).pack(padx=10, pady=(8, 2), anchor="w")
        self.prop_name_label = ctk.CTkLabel(
            pf, text="(no selection)", font=("Segoe UI", 11),
            text_color=FGD)
        self.prop_name_label.pack(padx=10, anchor="w")
        ctk.CTkFrame(pf, height=1, fg_color="#333").pack(fill="x", padx=10, pady=4)

        # Step selector
        sf = ctk.CTkFrame(pf, fg_color="transparent", height=30)
        sf.pack(fill="x", padx=10, pady=2); sf.pack_propagate(False)
        ctk.CTkLabel(sf, text="Step:", font=("Segoe UI", 11),
                     text_color=FGD).pack(side="left")
        self._step_combo = ctk.CTkComboBox(
            sf, values=[str(v) for v in STEP_VALUES],
            width=80, height=26, fg_color=BGI, border_color="#333",
            button_color=ACD, dropdown_fg_color=BGI, text_color=FGT,
            font=("Segoe UI", 11), command=self._on_step_changed)
        self._step_combo.set(str(self._step))
        self._step_combo.pack(side="left", padx=4)
        ctk.CTkLabel(sf, text="(±)", font=("Segoe UI", 10),
                     text_color=FGD).pack(side="left")

        ctk.CTkFrame(pf, height=1, fg_color="#2A2A2A").pack(fill="x", padx=10, pady=2)

        sc = ctk.CTkScrollableFrame(pf, fg_color="transparent",
                                    scrollbar_button_color="#333",
                                    scrollbar_button_hover_color="#555")
        sc.pack(fill="both", expand=True, padx=4, pady=2)

        # ─ Layering ─
        self._make_section(sc, "Layering")
        self._make_pos_row(sc, "Depth", "depth", unit="")

        # ─ Position (entry + ± only, no slider) ─
        self._make_section(sc, "Position")
        self._make_pos_row(sc, "X", "tx")
        self._make_pos_row(sc, "Y", "ty")

        # ─ Scale (with slider + uniform-lock) ─
        self._make_section(sc, "Scale")
        self._make_prop_row(sc, "X", "scale_x", -5, 5)
        # uniform-scale lock
        lock_row = ctk.CTkFrame(sc, fg_color="transparent", height=22)
        lock_row.pack(fill="x", padx=4, pady=0)
        ctk.CTkCheckBox(lock_row, text="Lock X=Y (uniform)",
                        variable=self._var_uniform_scale,
                        fg_color=AC, hover_color=ACD, text_color=FGD,
                        font=("Segoe UI", 10), width=20,
                        command=lambda: setattr(self, "_uniform_scale",
                                                self._var_uniform_scale.get())
                        ).pack(side="left", padx=6)
        self._make_prop_row(sc, "Y", "scale_y", -5, 5)

        self._make_section(sc, "Rotation")
        self._make_prop_row(sc, "Angle", "rotation", -180, 180)

        self._make_section(sc, "Skew")
        self._make_prop_row(sc, "X", "skew_x", -90, 90)
        self._make_prop_row(sc, "Y", "skew_y", -90, 90)

        ctk.CTkFrame(sc, height=1, fg_color="#2A2A2A").pack(fill="x", padx=4, pady=4)
        self._make_section(sc, "Raw Matrix")
        for lbl, key in [("scaleX", "raw_sx"), ("scaleY", "raw_sy"),
                         ("rotSkew0", "raw_r0"), ("rotSkew1", "raw_r1"),
                         ("transX", "raw_tx"), ("transY", "raw_ty")]:
            self._make_raw_row(sc, lbl, key)

        # ─ buttons ─
        ctk.CTkFrame(pf, height=1, fg_color="#333").pack(fill="x", padx=10, pady=4)
        af = ctk.CTkFrame(pf, fg_color="transparent")
        af.pack(fill="x", padx=6, pady=(0, 2))
        bs2 = dict(height=28, corner_radius=4, font=("Segoe UI", 10))
        ctk.CTkButton(af, text="Reset", width=65, fg_color="#2A2A2A",
                      hover_color="#3A3A3A", text_color=FGT,
                      command=self._reset_transform, **bs2
                      ).pack(side="left", padx=2, pady=2)
        ctk.CTkButton(af, text="Mirror H", width=70, fg_color="#2A2A2A",
                      hover_color="#3A3A3A", text_color=FGT,
                      command=lambda: self._mirror("h"), **bs2
                      ).pack(side="left", padx=2, pady=2)
        ctk.CTkButton(af, text="Mirror V", width=70, fg_color="#2A2A2A",
                      hover_color="#3A3A3A", text_color=FGT,
                      command=lambda: self._mirror("v"), **bs2
                      ).pack(side="left", padx=2, pady=2)

        af2 = ctk.CTkFrame(pf, fg_color="transparent")
        af2.pack(fill="x", padx=6, pady=(0, 2))
        ctk.CTkButton(af2, text="Copy All", width=80, fg_color="#2A2A2A",
                      hover_color="#3A3A3A", text_color=FGT,
                      command=self._copy_all_props, **bs2
                      ).pack(side="left", padx=2, pady=2)
        self.btn_paste = ctk.CTkButton(
            af2, text="Paste All", width=80, fg_color="#2A2A2A",
            hover_color="#3A3A3A", text_color=FGT, state="disabled",
            command=self._paste_all_props, **bs2)
        self.btn_paste.pack(side="left", padx=2, pady=2)
        ctk.CTkButton(af2, text="Copy Mat", width=80, fg_color="#2A2A2A",
                      hover_color="#3A3A3A", text_color=FGT,
                      command=self._copy_matrix_text, **bs2
                      ).pack(side="left", padx=2, pady=2)

        # ─ shortcuts hint ─
        ctk.CTkFrame(pf, height=1, fg_color="#333").pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(pf, text=(
            "G Move  R Rotate  S Scale  K Skew\n"
            "Space Pan  Scroll Zoom  Shift Snap\n"
            "Ctrl+Z Undo  Ctrl+Y Redo\n"
            "Arrows Nudge  Del Hide"
        ), font=("Consolas", 9), text_color="#555", justify="left"
        ).pack(padx=10, pady=(0, 6), anchor="w")

    def _make_section(self, par, title):
        ctk.CTkLabel(par, text=title, font=("Segoe UI", 10, "bold"),
                     text_color=FGD).pack(padx=6, pady=(6, 1), anchor="w")

    def _make_pos_row(self, par, label, key, unit="px"):
        """Position row: label  [−]  entry  [+]   (no slider)."""
        row = ctk.CTkFrame(par, fg_color="transparent", height=30)
        row.pack(fill="x", padx=4, pady=1); row.pack_propagate(False)
        ctk.CTkLabel(row, text=label, width=30, font=("Segoe UI", 11),
                     text_color=FGD, anchor="w").pack(side="left")
        ctk.CTkButton(row, text="", image=BMTTheme.get_icon("remove", size=16), width=24, height=24, corner_radius=4,
                      fg_color="#2A2A2A", hover_color="#3A3A3A",
                      text_color=FGT, font=("Segoe UI", 12),
                      command=lambda: self._prop_increment(key, -1)
                      ).pack(side="left", padx=1)
        e = ctk.CTkEntry(row, width=70, height=24, fg_color=BGI,
                         border_color="#333", text_color=FGT,
                         font=("Consolas", 10), justify="right")
        e.pack(side="left", padx=3)
        e.bind("<Return>", lambda ev, k=key: self._on_prop(k))
        e.bind("<FocusOut>", lambda ev, k=key: self._on_prop(k))
        ctk.CTkButton(row, text="", image=BMTTheme.get_icon("add", size=16), width=24, height=24, corner_radius=4,
                      fg_color="#2A2A2A", hover_color="#3A3A3A",
                      text_color=FGT, font=("Segoe UI", 12),
                      command=lambda: self._prop_increment(key, 1)
                      ).pack(side="left", padx=1)
        ctk.CTkLabel(row, text=unit, width=20, font=("Segoe UI", 9),
                     text_color=FGD, anchor="w").pack(side="left")
        self.prop_entries[key] = e

    def _make_prop_row(self, par, label, key, mn, mx):
        """Property row with slider."""
        row = ctk.CTkFrame(par, fg_color="transparent", height=30)
        row.pack(fill="x", padx=4, pady=1); row.pack_propagate(False)
        ctk.CTkLabel(row, text=label, width=35, font=("Segoe UI", 11),
                     text_color=FGD, anchor="w").pack(side="left")
        ctk.CTkButton(row, text="", image=BMTTheme.get_icon("remove", size=16), width=22, height=22, corner_radius=4,
                      fg_color="#2A2A2A", hover_color="#3A3A3A",
                      text_color=FGT, font=("Segoe UI", 12),
                      command=lambda: self._prop_increment(key, -1)
                      ).pack(side="left", padx=1)
        sl = ctk.CTkSlider(row, from_=mn, to=mx, width=70, height=14,
                           fg_color="#2A2A2A", progress_color=AC,
                           button_color=AC, button_hover_color=ACD,
                           command=lambda v, k=key: self._on_slider(k, v))
        sl.set(0); sl.pack(side="left", padx=2)
        ctk.CTkButton(row, text="", image=BMTTheme.get_icon("add", size=16), width=22, height=22, corner_radius=4,
                      fg_color="#2A2A2A", hover_color="#3A3A3A",
                      text_color=FGT, font=("Segoe UI", 12),
                      command=lambda: self._prop_increment(key, 1)
                      ).pack(side="left", padx=1)
        e = ctk.CTkEntry(row, width=60, height=22, fg_color=BGI,
                         border_color="#333", text_color=FGT,
                         font=("Consolas", 10), justify="right")
        e.pack(side="left", padx=2)
        e.bind("<Return>", lambda ev, k=key: self._on_prop(k))
        e.bind("<FocusOut>", lambda ev, k=key: self._on_prop(k))
        self.prop_entries[key] = e
        self.prop_sliders[key] = sl

    def _make_raw_row(self, par, label, key):
        row = ctk.CTkFrame(par, fg_color="transparent", height=26)
        row.pack(fill="x", padx=4, pady=1); row.pack_propagate(False)
        ctk.CTkLabel(row, text=label, width=65, font=("Segoe UI", 10),
                     text_color=FGD, anchor="w").pack(side="left")
        e = ctk.CTkEntry(row, width=90, height=22, fg_color=BGI,
                         border_color="#333", text_color=FGT,
                         font=("Consolas", 9), justify="right")
        e.pack(side="left", padx=3)
        e.bind("<Return>", lambda ev, k=key: self._on_prop(k))
        e.bind("<FocusOut>", lambda ev, k=key: self._on_prop(k))
        self.prop_entries[key] = e

    # ── Bottom bar ────────────────────────────────────────────────────
    def _build_bottom_bar(self):
        bar = ctk.CTkFrame(self.main_frame, height=46, fg_color=BGP,
                           corner_radius=8)
        # bar.pack(fill="x", padx=4, pady=(0, 2)); bar.pack_propagate(False)
        bar.pack_propagate(False)
        B = dict(height=34, corner_radius=6, font=("Segoe UI", 13, "bold"))
        self.btn_cancel = ctk.CTkButton(
            bar, text="Cancel", width=100, fg_color="#8B0000",
            hover_color="#A52A2A", text_color="#FFF",
            command=self._cancel_changes, state="disabled", **B)
        self.btn_cancel.pack(side="right", padx=6, pady=6)
        self.btn_apply = ctk.CTkButton(
            bar, text="Apply", width=100, fg_color="#2E7D32",
            hover_color="#388E3C", text_color="#FFF",
            command=self._apply_changes, state="disabled", **B)
        self.btn_apply.pack(side="right", padx=4, pady=6)
        self.feedback_label = ctk.CTkLabel(
            bar, text="", font=("Segoe UI", 12, "bold"),
            text_color="#555")
        self.feedback_label.pack(side="right", padx=12)
        ctk.CTkLabel(bar, text="Apply → SWF memory  |  Save → disk",
                     font=("Segoe UI", 11), text_color=FGD
                     ).pack(side="left", padx=12)

    # ── Status bar ────────────────────────────────────────────────────
    def _build_statusbar(self):
        sb = ctk.CTkFrame(self.main_frame, height=24, fg_color=BGP,
                          corner_radius=4)
        sb.pack(fill="x", padx=4, pady=(0, 4)); sb.pack_propagate(False)
        self.status_var = tk.StringVar(value="Ready — Open a SWF file to begin")
        ctk.CTkLabel(sb, textvariable=self.status_var, font=("Segoe UI", 10),
                     text_color=FGD, anchor="w").pack(side="left", padx=8)
        self.mode_var = tk.StringVar(value="Mode: Move (G)")
        ctk.CTkLabel(sb, textvariable=self.mode_var, font=("Segoe UI", 10),
                     text_color=AC, anchor="e").pack(side="right", padx=10)
        self.hover_var = tk.StringVar(value="")
        ctk.CTkLabel(sb, textvariable=self.hover_var, font=("Segoe UI", 10),
                     text_color=ORANGE, anchor="e").pack(side="right", padx=10)
        self.coords_var = tk.StringVar(value="")
        ctk.CTkLabel(sb, textvariable=self.coords_var, font=("Consolas", 9),
                     text_color=FGD, anchor="e").pack(side="right", padx=6)

    # ── Reference window ──────────────────────────────────────────────
    def _open_reference_window(self):
        """Abre ventana flotante de referencia (visible solo cuando BMT tiene foco)."""
        if self._ref_window and self._ref_window.winfo_exists():
            self._ref_window.lift(); self._ref_window.focus_force(); return

        root = self.parent.winfo_toplevel()
        win = ctk.CTkToplevel(root)
        win.title("Reference Image")
        win.geometry("480x520")
        win.transient(root)  # Sigue al root, se oculta cuando se minimiza
        # NO usar -topmost: la ventana solo se ve cuando BMT tiene foco
        self._ref_window = win
        self._ref_img_pil = None
        self._ref_img_tk  = None
        self._ref_zoom    = 1.0
        self._ref_angle   = 0        # grados
        self._ref_flip_h  = False
        self._ref_pan_x   = 0.0
        self._ref_pan_y   = 0.0
        self._ref_pan_sx  = self._ref_pan_sy = 0
        self._ref_panning = False

        # Icono de la app
        try:
            from pathlib import Path as _P
            ico = get_project_root() / "resources" / "icons" / "Icon32.ico"
            if ico.exists():
                win.after(200, lambda: win.iconbitmap(str(ico)))
        except Exception:
            pass

        # ── Toolbar ──
        tb2 = ctk.CTkFrame(win, fg_color=BGP, height=38, corner_radius=0)
        tb2.pack(fill="x")
        tb2.pack_propagate(False)
        bkw = dict(width=32, height=28, corner_radius=4,
                   fg_color="#2A2A2A", hover_color="#3A3A3A",
                   text_color=FGT, font=ctk.CTkFont(size=13))
        ctk.CTkButton(tb2, text="", image=BMTTheme.get_icon("add", size=16),  command=lambda: self._ref_zoom_step(1.2), **bkw).pack(side="left", padx=2, pady=4)
        ctk.CTkButton(tb2, text="", image=BMTTheme.get_icon("remove", size=16),  command=lambda: self._ref_zoom_step(1/1.2), **bkw).pack(side="left", padx=1, pady=4)
        ctk.CTkButton(tb2, text="", image=BMTTheme.get_icon("crop", size=16) ,command=self._ref_fit,   **bkw).pack(side="left", padx=1, pady=4)
        ctk.CTkButton(tb2, text="", image=BMTTheme.get_icon("undo", size=16),  command=lambda: self._ref_rotate(-15), **bkw).pack(side="left", padx=4, pady=4)
        ctk.CTkButton(tb2, text="", image=BMTTheme.get_icon("redo", size=16),  command=lambda: self._ref_rotate(15),  **bkw).pack(side="left", padx=1, pady=4)
        ctk.CTkButton(tb2, text="", image=BMTTheme.get_icon("sync_alt", size=16),  command=self._ref_flip,  **bkw).pack(side="left", padx=4, pady=4)
        ctk.CTkButton(tb2, text="Reset", width=48, command=self._ref_reset_view,
                      fg_color="#333", hover_color="#444", text_color=FGD,
                      font=ctk.CTkFont(size=10), height=28, corner_radius=4
                      ).pack(side="left", padx=4, pady=4)
        ctk.CTkButton(tb2, text="Open", width=56, fg_color=AC, hover_color=ACD,
                      text_color="#000", height=28, corner_radius=4,
                      font=ctk.CTkFont(size=11, weight="bold"),
                      command=self._ref_window_load_image).pack(side="right", padx=6, pady=4)
        ctk.CTkButton(tb2, text="Paste", width=50, fg_color="#333", hover_color="#444",
                      text_color=FGT, height=28, corner_radius=4,
                      font=ctk.CTkFont(size=11),
                      command=self._ref_window_paste).pack(side="right", padx=2, pady=4)

        # ── Canvas ──
        ref_cv = tk.Canvas(win, bg="#0A0A0A", highlightthickness=0, cursor="fleur")
        ref_cv.pack(fill="both", expand=True)
        self._ref_cv = ref_cv
        self._ref_window_draw_hint()

        # Bindings de zoom / pan en la ventana de referencia
        ref_cv.bind("<MouseWheel>",      self._ref_on_scroll)
        ref_cv.bind("<ButtonPress-1>",   self._ref_pan_start)
        ref_cv.bind("<B1-Motion>",       self._ref_pan_move)
        ref_cv.bind("<ButtonRelease-1>", self._ref_pan_end)
        ref_cv.bind("<Configure>",       lambda e: self._ref_window_redraw())
        win.bind("<Control-v>",          lambda e: self._ref_window_paste())

        # Visibilidad: solo se muestra cuando BMT tiene foco
        self._ref_focus_in_id  = root.bind("<FocusIn>",
            lambda e: self._ref_sync_focus(e, True), add="+")
        self._ref_focus_out_id = root.bind("<FocusOut>",
            lambda e: self._ref_sync_focus(e, False), add="+")

        win.protocol("WM_DELETE_WINDOW", self._ref_window_close)

    def _ref_sync_focus(self, event, gaining):
        """Muestra u oculta la ventana de referencia segun el foco del root."""
        if not self._ref_window or not self._ref_window.winfo_exists():
            return
        # Solo reaccionar a eventos del root (widget == root), no de hijos
        root = self.parent.winfo_toplevel()
        if str(event.widget) != str(root) and str(event.widget) != ".":
            return
        if gaining:
            self._ref_window.deiconify()
        else:
            # Solo ocultar si el foco va a una ventana distinta (no a la propia ref)
            try:
                focused = root.focus_get()
                if focused and str(focused).startswith(str(self._ref_window)):
                    return
            except Exception:
                pass
            self._ref_window.withdraw()

    # ── Controles de imagen de referencia ───────────────────────────────
    def _ref_zoom_step(self, factor):
        self._ref_zoom = max(0.05, min(20.0, self._ref_zoom * factor))
        self._ref_window_redraw()

    def _ref_rotate(self, deg):
        self._ref_angle = (self._ref_angle + deg) % 360
        self._ref_window_redraw()

    def _ref_flip(self):
        self._ref_flip_h = not self._ref_flip_h
        self._ref_window_redraw()

    def _ref_fit(self):
        if self._ref_img_pil is None or not self._ref_cv: return
        cw = self._ref_cv.winfo_width() or 480
        ch = self._ref_cv.winfo_height() or 480
        iw, ih = self._ref_img_pil.size
        if iw <= 0 or ih <= 0: return
        self._ref_zoom = min(cw / iw, ch / ih) * 0.92
        self._ref_pan_x = self._ref_pan_y = 0.0
        self._ref_window_redraw()

    def _ref_reset_view(self):
        self._ref_zoom = 1.0; self._ref_angle = 0
        self._ref_flip_h = False; self._ref_pan_x = self._ref_pan_y = 0.0
        self._ref_window_redraw()

    def _ref_pan_start(self, e):
        self._ref_panning = True
        self._ref_pan_sx, self._ref_pan_sy = e.x, e.y

    def _ref_pan_move(self, e):
        if not self._ref_panning: return
        self._ref_pan_x += e.x - self._ref_pan_sx
        self._ref_pan_y += e.y - self._ref_pan_sy
        self._ref_pan_sx, self._ref_pan_sy = e.x, e.y
        self._ref_window_redraw()

    def _ref_pan_end(self, e):
        self._ref_panning = False

    def _ref_on_scroll(self, e):
        factor = 1.1 if e.delta > 0 else 1/1.1
        self._ref_zoom_step(factor)

    def _ref_window_load_image(self):
        path = filedialog.askopenfilename(
            title="Select Reference Image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"),
                       ("All files", "*.*")])
        if path:
            try:
                self._ref_img_pil = Image.open(path).convert("RGBA")
                self._ref_reset_view(); self._ref_fit()
            except Exception as ex:
                print(f"[Ref] load error: {ex}")

    def _ref_window_paste(self):
        try:
            from PIL import ImageGrab
            img = ImageGrab.grabclipboard()
            if img:
                self._ref_img_pil = img.convert("RGBA")
                self._ref_reset_view(); self._ref_fit()
        except Exception as ex:
            print(f"[Ref] paste error: {ex}")

    def _ref_window_draw_hint(self):
        cv = self._ref_cv
        cv.delete("all")
        W = cv.winfo_width() or 480; H = cv.winfo_height() or 480
        cv.create_text(W // 2, H // 2 - 14,
                       text="Click 'Open' or Ctrl+V to load image",
                       fill="#444", font=("Segoe UI", 13))
        cv.create_text(W // 2, H // 2 + 12,
                       text="Scroll = Zoom  |  Drag = Pan",
                       fill="#333", font=("Segoe UI", 10))

    def _ref_window_redraw(self):
        if not self._ref_window or not self._ref_window.winfo_exists(): return
        cv = self._ref_cv
        cv.delete("all")
        if self._ref_img_pil is None:
            self._ref_window_draw_hint(); return
        cw = cv.winfo_width(); ch = cv.winfo_height()
        if cw < 10 or ch < 10: return
        # Aplicar flip, rotate, zoom
        img = self._ref_img_pil.copy()
        if self._ref_flip_h:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        if self._ref_angle != 0:
            img = img.rotate(-self._ref_angle, expand=True,
                             resample=Image.BICUBIC)
        nw = max(1, int(img.width * self._ref_zoom))
        nh = max(1, int(img.height * self._ref_zoom))
        img = img.resize((nw, nh), Image.LANCZOS)
        self._ref_img_tk = ImageTk.PhotoImage(img)
        cx = cw // 2 + int(self._ref_pan_x)
        cy = ch // 2 + int(self._ref_pan_y)
        cv.create_image(cx, cy, image=self._ref_img_tk, anchor="center")
        # Mini HUD
        cv.create_text(6, ch - 6,
                       text=f"Zoom:{self._ref_zoom:.1f}x  Rot:{self._ref_angle}°",
                       fill="#444", font=("Segoe UI", 8), anchor="sw")

    def _ref_window_close(self):
        if self._ref_window:
            root = self.parent.winfo_toplevel()
            try:
                root.unbind("<FocusIn>",  self._ref_focus_in_id)
                root.unbind("<FocusOut>", self._ref_focus_out_id)
            except Exception:
                pass
            self._ref_window.destroy()
        self._ref_window  = None
        self._ref_img_pil = None
        self._ref_img_tk  = None


    def _toggle_left_panel(self):
        """Colapsa o expande el panel izquierdo."""
        if self._left_collapsed:
            self._left_panel_frame.grid()
            self._left_collapse_btn.configure(text="", image=BMTTheme.get_icon("arrow_left", size=20))
            self._left_collapsed = False
        else:
            self._left_panel_frame.grid_remove()
            self._left_collapse_btn.configure(text="", image=BMTTheme.get_icon("arrow_right", size=20))
            self._left_collapsed = True

    def _toggle_props_panel(self):
        """Colapsa o expande el panel de propiedades."""
        if self._props_collapsed:
            self._props_panel_frame.grid()
            self._props_collapse_btn.configure(text="", image=BMTTheme.get_icon("arrow_right", size=20))
            self._props_collapsed = False
        else:
            self._props_panel_frame.grid_remove()
            self._props_collapse_btn.configure(text="", image=BMTTheme.get_icon("arrow_left", size=20))
            self._props_collapsed = True


    def _bind_keys(self):
        top = self.parent.winfo_toplevel()
        top.bind("<Control-z>", lambda e: self._do_undo())
        top.bind("<Control-y>", lambda e: self._do_redo())
        top.bind("<Control-s>", lambda e: self._save_swf_dialog())
        top.bind("<Control-o>", lambda e: self._load_swf_dialog())
        top.bind("<Control-c>", lambda e: self._copy_all_props())
        top.bind("<Control-v>", lambda e: self._paste_all_props())
        top.bind("<Delete>", lambda e: self._toggle_vis())
        top.bind("<Escape>", lambda e: self._deselect_all())
        top.bind("<Home>", lambda e: self._fit_view("edit"))
        top.bind("<End>", lambda e: self._fit_view("ref"))
        # Arrow nudge (toplevel)
        for key, dx, dy in [("<Left>", -1, 0), ("<Right>", 1, 0),
                            ("<Up>", 0, -1), ("<Down>", 0, 1)]:
            top.bind(key, lambda e, x=dx, y=dy: self._nudge_handler(x, y, e))
        for key, dx, dy in [("<Shift-Left>", -10, 0), ("<Shift-Right>", 10, 0),
                            ("<Shift-Up>", 0, -10), ("<Shift-Down>", 0, 10)]:
            top.bind(key, lambda e, x=dx, y=dy: self._nudge_handler(x, y, e))
        # Override arrows on trees so they nudge instead of navigate
        for tr in (self.tree, self.edit_tree):
            for key, dx, dy in [("<Left>", -1, 0), ("<Right>", 1, 0),
                                ("<Up>", 0, -1), ("<Down>", 0, 1)]:
                tr.bind(key, lambda e, x=dx, y=dy: (self._nudge(x, y), "break")[-1])
            for key, dx, dy in [("<Shift-Left>", -10, 0), ("<Shift-Right>", 10, 0),
                                ("<Shift-Up>", 0, -10), ("<Shift-Down>", 0, 10)]:
                tr.bind(key, lambda e, x=dx, y=dy: (self._nudge(x, y), "break")[-1])
        # Mode keys
        top.bind("<KeyPress-g>", lambda e: self._set_mode(MODE_MOVE))
        top.bind("<KeyPress-r>", lambda e: self._set_mode(MODE_ROTATE))
        top.bind("<KeyPress-s>", lambda e: self._set_mode(MODE_SCALE) if not (e.state & 4) else None)
        top.bind("<KeyPress-k>", lambda e: self._set_mode(MODE_SKEW))
        top.bind("<KeyPress-Shift_L>", lambda e: setattr(self, "_shift", True))
        top.bind("<KeyRelease-Shift_L>", lambda e: setattr(self, "_shift", False))
        top.bind("<KeyPress-Shift_R>", lambda e: setattr(self, "_shift", True))
        top.bind("<KeyRelease-Shift_R>", lambda e: setattr(self, "_shift", False))
        top.bind("<KeyPress-space>", lambda e: self._space_down())
        top.bind("<KeyRelease-space>", lambda e: self._space_up())

    def _nudge_handler(self, dx, dy, event):
        w = event.widget
        # Allow entries to use arrows normally
        if isinstance(w, (tk.Entry, ttk.Entry)):
            return
        self._nudge(dx, dy)
        return "break"

    # ═══════════════════════════════════════════════════════════════════
    #  TRANSFORM MODE / CURSORS
    # ═══════════════════════════════════════════════════════════════════
    def _set_mode(self, mode):
        self.mode = mode
        names = {MODE_MOVE: "Move (G)", MODE_ROTATE: "Rotate (R)",
                 MODE_SCALE: "Scale (S)", MODE_SKEW: "Skew (K)"}
        if self.mode_var:
            self.mode_var.set(f"Mode: {names.get(mode, mode)}")
        for btn, m in [(self.btn_mode_g, MODE_MOVE), (self.btn_mode_r, MODE_ROTATE),
                       (self.btn_mode_s, MODE_SCALE), (self.btn_mode_k, MODE_SKEW)]:
            if btn:
                btn.configure(fg_color=AC if m == mode else "#333",
                              text_color="#000" if m == mode else FGT)
        if mode != MODE_ROTATE:
            self._pivot_offset = (0.0, 0.0)
        cur = _MODE_CURSORS.get(mode, "crosshair")
        for cv in (self.ref_canvas, self.edit_canvas):
            if cv:
                try:
                    cv.configure(cursor=cur)
                except Exception:
                    cv.configure(cursor="crosshair")
        self._redraw_edit()

    def _space_down(self):
        self._space_held = True
        cur = _MODE_CURSORS.get("pan", "fleur")
        for cv in (self.ref_canvas, self.edit_canvas):
            if cv:
                try:
                    cv.configure(cursor=cur)
                except Exception:
                    cv.configure(cursor="fleur")

    def _space_up(self):
        self._space_held = False
        cur = _MODE_CURSORS.get(self.mode, "crosshair")
        for cv in (self.ref_canvas, self.edit_canvas):
            if cv:
                try:
                    cv.configure(cursor=cur)
                except Exception:
                    cv.configure(cursor="crosshair")

    def _on_step_changed(self, v):
        try:
            self._step = float(v)
            self.prefs["step"] = self._step
            _save_prefs(self.prefs)
        except ValueError:
            pass

    # ═══════════════════════════════════════════════════════════════════
    #  SWF LOADING
    # ═══════════════════════════════════════════════════════════════════
    def _load_swf_dialog(self):
        init_dir = self.prefs.get("last_swf_dir") or self.game_path or None
        path = filedialog.askopenfilename(
            title="Select SWF file",
            filetypes=[("SWF", "*.swf"), ("All", "*.*")],
            initialdir=init_dir)
        if not path:
            return
        if not _ensure_ffdec():
            messagebox.showerror("Error", "Could not initialise ffdec / JPype.")
            return
        self.prefs["last_swf_dir"] = os.path.dirname(path)
        _save_prefs(self.prefs)
        self._do_load(path)

    def _reload_swf(self):
        if self.swf_path:
            self._do_load(self.swf_path)
        else:
            messagebox.showinfo("Reload", "No SWF loaded.")

    def _do_load(self, path):
        self.swf_path = path
        self._loading = True
        self._status(f"Loading {os.path.basename(path)} ...")
        self.btn_load.configure(state="disabled")
        if hasattr(self.parent, '_show_loading_overlay'):
            self.parent._show_loading_overlay(f"SWF: {os.path.basename(path)}")
        threading.Thread(target=self._load_thread, args=(path,), daemon=True).start()

    def _load_thread(self, path):
        try:
            _ajvm()
            swf = _Methods.get_swf(path, False)
            if swf is None:
                self._ui(lambda: messagebox.showerror("Error", "Could not open SWF."))
                return
            self.swf = swf
            self._ui(lambda: self._status("Parsing tags ..."))
            self._parse_tags()
            self._ui(lambda: self._status(f"Exporting shapes ({self.render_mode.upper()}) ..."))
            self._export_shapes()
            self._ui(self._on_loaded)
        except Exception as exc:
            traceback.print_exc()
            self._ui(lambda: messagebox.showerror("Error", f"Load failed:\n{exc}"))
        finally:
            self._loading = False
            self._ui(lambda: self.btn_load.configure(state="normal"))
            if hasattr(self.parent, '_stop_ov_anim'):
                def hide_ov():
                    self.parent._stop_ov_anim()
                    if self.parent._loading_overlay:
                        self.parent._loading_overlay.destroy()
                        self.parent._loading_overlay = None
                self._ui(hide_ov)

    def _parse_tags(self):
        from ffdec.classes import (DefineShapeTag, DefineShape2Tag,
                                   DefineShape3Tag, DefineShape4Tag,
                                   DefineSpriteTag)
        self.tag_dict.clear(); self.shape_tags.clear(); self.sprite_tags.clear()
        DST = (DefineShapeTag, DefineShape2Tag, DefineShape3Tag, DefineShape4Tag)
        for tag in self.swf.getTags():
            try:
                cid = int(tag.getCharacterId())
            except Exception:
                continue
            self.tag_dict[cid] = tag
            if isinstance(tag, DST):
                self.shape_tags[cid] = tag
            elif isinstance(tag, DefineSpriteTag):
                self.sprite_tags[cid] = tag
        print(f"[SE] {len(self.shape_tags)} shapes, {len(self.sprite_tags)} sprites")

    def _export_shapes(self):
        """Export each sprite's frame as PNG using FrameExporter.exportSpriteFrames."""
        from ffdec.classes import (FrameExporter, FrameExportSettings,
                                   FrameExportMode, SpriteExportMode,
                                   SpriteExportSettings, ArrayList)
        h = hashlib.md5(self.swf_path.encode()).hexdigest()[:12]
        d = os.path.join(self._cache_dir, h)
        zoom = self.export_zoom

        # Check cache — if enough files already exist, skip
        if os.path.isdir(d):
            existing_sprites = 0
            existing_shapes = 0
            for root_, dirs_, files_ in os.walk(d):
                existing_sprites += sum(1 for f in files_ if f.endswith('.png') and "_shapes" not in root_)
                if HAS_SKIA:
                    existing_shapes += sum(1 for f in files_ if f.endswith('.svg') and "_shapes" in root_)
                else:
                    existing_shapes += sum(1 for f in files_ if f.endswith('.png') and "_shapes" in root_)
            
            # Require both sprite frames AND shape vectors/images to consider it a cache hit
            if existing_sprites >= len(self.sprite_tags) and existing_shapes >= len(self.shape_tags):
                print(f"[SE] Cache hit ({existing_sprites} Sprite PNGs, {existing_shapes} Shape files)")
                return
        os.makedirs(d, exist_ok=True)
        if not self.sprite_tags:
            return

        # Also export shapes as PNG or SVG for individual shape images
        try:
            from ffdec.classes import (ReadOnlyTagList,
                                       ShapeExporter, ShapeExportMode,
                                       ShapeExportSettings)
            shape_dir = os.path.join(d, "_shapes")
            os.makedirs(shape_dir, exist_ok=True)
            jl = ArrayList()
            for t in self.shape_tags.values():
                jl.add(t)
            rotl = ReadOnlyTagList(jl)
            if HAS_SKIA:
                ses = ShapeExportSettings(ShapeExportMode.SVG, 1.0)
                ext = "SVG"
            else:
                ses = ShapeExportSettings(ShapeExportMode.PNG, zoom)
                ext = "PNG"
            r = ShapeExporter().exportShapes(None, shape_dir, self.swf, rotl, ses, None, 1.0 if HAS_SKIA else zoom)
            print(f"[SE] Exported {r.size() if r else 0} shape {ext}s")
        except Exception as exc:
            print(f"[SE] Shape export fallback error: {exc}")


        # Export sprite frames using FrameExporter
        import jpype
        evl = self.swf.getExportEventListener()
        ses = SpriteExportSettings(SpriteExportMode.PNG, zoom)
        exporter = FrameExporter()
        exported = 0
        
        # In JPype, passing None directly for an interface can fail overload resolution.
        # We explicitly cast None to the expected Java types so FFDec knows which overload to use.
        JList = jpype.JClass("java.util.List")
        null_list = jpype.JObject(None, JList)
        
        JHandler = jpype.JClass("com.jpexs.decompiler.flash.AbortRetryIgnoreHandler")
        null_handler = jpype.JObject(None, JHandler)
        
        for sid in self.sprite_tags:
            try:
                exporter.exportSpriteFrames(
                    null_handler, str(d), self.swf, sid, null_list, ses, evl)
                exported += 1
            except Exception as exc:
                print(f"[SE] Frame export error sprite {sid}: {exc}")
        print(f"[SE] Exported frames for {exported}/{len(self.sprite_tags)} sprites")

    def _export_dir(self):
        h = hashlib.md5(self.swf_path.encode()).hexdigest()[:12]
        return os.path.join(self._cache_dir, h)

    def _load_images(self):
        """Load exported shape PNGs into shape_images dict."""
        self.shape_images.clear()
        self._flush_render_cache()
        self._svg_paths.clear()
        self._svg_raster_cache.clear()
        d = self._export_dir()
        if not os.path.isdir(d):
            return
        shape_dir = os.path.join(d, "_shapes")
        if os.path.isdir(shape_dir):
            for fn in os.listdir(shape_dir):
                is_svg = fn.lower().endswith(".svg")
                is_png = fn.lower().endswith(".png")
                if not is_svg and not is_png:
                    continue
                m = re.search(r"(\d+)", os.path.splitext(fn)[0])
                if not m:
                    continue
                cid = int(m.group(1))
                fpath = os.path.join(shape_dir, fn)
                if is_svg and HAS_SKIA:
                    try:
                        stream = skia.Stream.MakeFromFile(fpath)
                        dom = skia.SVGDOM.MakeFromStream(stream)
                        if dom:
                            self._svg_doms[cid] = dom
                    except Exception:
                        pass
                elif is_png:
                    try:
                        self.shape_images[cid] = Image.open(fpath).convert("RGBA")
                    except Exception:
                        pass

        # Fallback: also try root-level PNGs (old cache format)
        if not self.shape_images:
            for fn in os.listdir(d):
                if not fn.lower().endswith(".png"):
                    continue
                m = re.search(r"(\d+)", os.path.splitext(fn)[0])
                if not m:
                    continue
                cid = int(m.group(1))
                fpath = os.path.join(d, fn)
                try:
                    self.shape_images[cid] = Image.open(fpath).convert("RGBA")
                except Exception:
                    pass
        print(f"[SE] Loaded {len(self.shape_images)} shape images, {len(self._svg_doms)} Skia SVGs")

    # ── Build parts ───────────────────────────────────────────────────
    def _build_all_parts(self):
        from ffdec.classes import (PlaceObjectTag, PlaceObject2Tag,
                                   PlaceObject3Tag, PlaceObject4Tag)
        PO = (PlaceObjectTag, PlaceObject2Tag, PlaceObject3Tag, PlaceObject4Tag)
        self.sprite_parts.clear()
        for sid, stag in self.sprite_tags.items():
            parts = []
            try:
                for sub in stag.getTags():
                    if not isinstance(sub, PO):
                        continue
                    p = self._make_part(sub)
                    if p is not None:
                        parts.append(p)
            except Exception:
                pass
            parts.sort(key=lambda p: p.depth)
            self.sprite_parts[sid] = parts

    def _make_part(self, ptag) -> Optional[PartData]:
        try:
            cid = int(ptag.characterId)
            dp  = int(ptag.depth)
        except Exception:
            return None
        sx, sy, r0, r1, tx, ty = self._read_mat(ptag.matrix)
        nm = self._pname(ptag, cid)
        bx0, by0, bx1, by1 = self._bounds(cid)
        return PartData(place_tag=ptag, char_id=cid, depth=dp, name=nm,
                        is_sprite=(cid in self.sprite_tags),
                        sx=sx, sy=sy, r0=r0, r1=r1, tx=tx, ty=ty,
                        bx0=bx0, by0=by0, bx1=bx1, by1=by1)

    def _pname(self, ptag, cid):
        nm = ""
        try:
            n = ptag.name
            if n:
                nm = str(n)
        except Exception:
            pass
        if not nm:
            try:
                ref = self.tag_dict.get(cid)
                if ref:
                    en = ref.getExportFileName()
                    if en:
                        nm = str(en)
            except Exception:
                pass
        return nm or (("Sprite_" if cid in self.sprite_tags else "Shape_") + str(cid))

    def _bounds(self, cid):
        try:
            ref = self.tag_dict.get(cid)
            if ref:
                r = ref.getRect()
                if r:
                    return (float(r.Xmin), float(r.Ymin),
                            float(r.Xmax), float(r.Ymax))
        except Exception:
            pass
        return (0.0, 0.0, 0.0, 0.0)

    def _read_mat(self, matrix):
        if matrix is None:
            return 1.0, 1.0, 0.0, 0.0, 0.0, 0.0
        try:
            hs = bool(matrix.hasScale); hr = bool(matrix.hasRotate)
            sx = float(matrix.scaleX) / FP if hs else 1.0
            sy = float(matrix.scaleY) / FP if hs else 1.0
            r0 = float(matrix.rotateSkew0) / FP if hr else 0.0
            r1 = float(matrix.rotateSkew1) / FP if hr else 0.0
            tx = float(matrix.translateX) / TWIP
            ty = float(matrix.translateY) / TWIP
            return sx, sy, r0, r1, tx, ty
        except Exception:
            return 1.0, 1.0, 0.0, 0.0, 0.0, 0.0

    def _detect_ref_sprite(self):
        best_id, best_n = -1, 0
        for sid, parts in self.sprite_parts.items():
            if len(parts) > best_n:
                best_n = len(parts); best_id = sid
        return best_id if best_n >= REF_MIN_PO else -1

    # ── On loaded ─────────────────────────────────────────────────────
    def _on_loaded(self):
        self._load_images()
        self._build_all_parts()
        opts = self._build_sprite_opts()
        self._sprite_id_map_ref = {o: sid for o, sid in opts}
        self._sprite_id_map_edit = dict(self._sprite_id_map_ref)

        has_reference = False
        skin_parts_count = 0
        
        valid_skin_prefixes = (
            "a_Forearm_", "a_Shin_", "a_Eyes_", "a_Hair_", "a_Jaw_",
            "a_Arm1_", "a_Leg1_", "a_Torso1_", "a_Torso2_",
            "a_Torso1Back_", "a_Torso2Back_"
        )
        
        import re
        for o, sid in opts:
            nm = ""
            if " — " in o:
                nm = o.split(" — ")[-1].split("  (")[0].strip()
                nm = re.sub(r'^(DefineSprite|DefineShape\d*)_\d+_', '', nm)
            
            if nm.startswith("a_Reference_"):
                has_reference = True
            elif any(nm.startswith(prefix) for prefix in valid_skin_prefixes):
                skin_parts_count += 1

        if skin_parts_count >= 5 and not has_reference:
            ans = messagebox.askyesno(
                "Missing Reference Sprite",
                "A skin was detected, but no reference sprite is present.\n"
                "A reference sprite is required for the Skin Editor to work properly.\n\n"
                "Do you want to generate one now?"
            )
            if ans:
                import collections
                suffix_counts = collections.Counter()
                for o, sid in opts:
                    nm = ""
                    if " — " in o:
                        nm = o.split(" — ")[-1].split("  (")[0].strip()
                        nm = re.sub(r'^(DefineSprite|DefineShape\d*)_\d+_', '', nm)
                    for prefix in valid_skin_prefixes:
                        if nm.startswith(prefix):
                            suffix = nm[len(prefix):]
                            if suffix:
                                suffix_counts[suffix] += 1
                            break
                
                skin_name = ""
                if suffix_counts:
                    skin_name = suffix_counts.most_common(1)[0][0]
                
                def _generate_ref_silently():
                    from src.modules.ReferenceLoaderModule import ReferenceLoaderModule
                    rl = ReferenceLoaderModule(self.parent, self.game_path, self.mods_path)
                    rl.container = self.parent
                    def dummy_log(msg):
                        print(f"[SilentRefLoader] {msg}")
                    rl.log = dummy_log

                    self.parent.after(0, lambda: self._status(f"Injecting reference sprite for {skin_name}..."))
                    
                    try:
                        rl._process_swf_thread(rl.RefSourcePath, self.swf_path, skin_name)
                        
                        def finish():
                            self._status("Reference sprite injected! Reloading SWF...")
                            self._reload_swf()
                            
                        self.parent.after(0, finish)
                        
                    except Exception as e:
                        print("Error generating reference:", e)
                        def handle_err():
                            messagebox.showerror("Error", f"Failed to generate reference sprite:\n{e}")
                        self.parent.after(0, handle_err)

                import threading
                threading.Thread(target=_generate_ref_silently, daemon=True).start()
                return

        ref_opts = [o for o, sid in opts if len(self.sprite_parts.get(sid, [])) >= 5]
        if not ref_opts:
            ref_opts = [o for o, _ in opts]
        self._all_ref_opts = [o for o, _ in opts]
        self._all_edit_opts = [o for o, _ in opts]
        if ref_opts and self.ref_selector:
            self.ref_selector.configure(values=ref_opts)
        edit_opts = [o for o, _ in opts]
        if edit_opts and self.edit_selector:
            self.edit_selector.configure(values=edit_opts)

        ref_id = self._detect_ref_sprite()
        if ref_id > 0:
            self.ref_sprite_id = ref_id
            for o, sid in opts:
                if sid == ref_id:
                    self.ref_selector.set(o); break
        elif opts:
            self.ref_sprite_id = opts[0][1]
            if self.ref_selector:
                self.ref_selector.set(opts[0][0])

        edit_set = False
        if self.ref_sprite_id > 0:
            for rp in self.sprite_parts.get(self.ref_sprite_id, []):
                if rp.is_sprite:
                    self.edit_sprite_id = rp.char_id
                    for o, sid in opts:
                        if sid == rp.char_id:
                            if self.edit_selector:
                                self.edit_selector.set(o)
                            break
                    edit_set = True; break
        if not edit_set and opts:
            self.edit_sprite_id = opts[0][1]
            if self.edit_selector:
                self.edit_selector.set(opts[0][0])

        self._populate_ref_tree(); self._populate_edit_tree()
        self._update_canvas_titles()
        self._take_snapshot()
        for b in (self.btn_save, self.btn_apply, self.btn_cancel, self.btn_export):
            if b:
                b.configure(state="normal")
        self._status(f"Loaded {os.path.basename(self.swf_path)} — "
                     f"{len(self.shape_tags)} shapes, {len(self.sprite_tags)} sprites")
        self._flatten_all()
        self._fit_view("ref"); self._fit_view("edit")

    def _build_sprite_opts(self):
        result = []
        for sid in sorted(self.sprite_tags.keys()):
            pc = len(self.sprite_parts.get(sid, []))
            nm = ""
            try:
                en = self.sprite_tags[sid].getExportFileName()
                if en: nm = str(en)
            except Exception:
                pass
            lbl = f"Sprite {sid}"
            if nm: lbl += f" — {nm}"
            lbl += f"  ({pc})"
            result.append((lbl, sid))
        result.sort(key=lambda x: -len(self.sprite_parts.get(x[1], [])))
        return result

    def _sprite_display_name(self, sid):
        """Returns 'Sprite(ID) - exportName' or 'Sprite(ID)'."""
        nm = self._get_export_name(sid)
        return f"Sprite({sid})" + (f" - {nm}" if nm else "")

    def _shape_display_name(self, cid):
        """Returns 'Shape(ID)' label."""
        return f"Shape({cid})"

    def _get_export_name(self, sid) -> str:
        """Returns the clean export name without 'DefineSprite_X_' prefix."""
        try:
            en = self.sprite_tags[sid].getExportFileName()
            if not en:
                return ""
            s = str(en)
            # Strip 'DefineSprite_123_' prefix if present
            import re as _re
            s = _re.sub(r'^DefineSprite_\d+_', '', s)
            return s
        except Exception:
            return ""

    def _is_skin_swf(self) -> bool:
        """Returns True if the SWF contains the key patterns of a Brawlhalla skin
        (a_Hair*, a_HairBack*, a_Torso1*, a_Torso2* all present)."""
        names = [self._get_export_name(sid).lower()
                 for sid in self.sprite_tags]
        markers = ["a_hair", "a_hairback", "a_torso1", "a_torso2"]
        return all(any(nm.startswith(m) for nm in names) for m in markers)

    # Skin category definitions — prefixes match the CLEANED export name (no DefineSprite_X_)
    _SKIN_CATEGORIES = [
        ("Head", "#CC3333", [
            ("Hair",    ["a_Hair",    "a_HairBack"]),
            ("Eyes",    ["a_Eyes",    "a_EyesTurn", "a_EyesKO",  "a_EyesHit",
                         "a_EyesDown","a_EyesAngry","a_EyesBent"]),
            ("Mouths",  ["a_Mouth",   "a_MouthWarCry","a_MouthSmile","a_MouthKO",
                         "a_MouthHit","a_MouthGrowl","a_MouthBlow"]),
            ("Face",    ["a_Nose",    "a_Jaw"]),
        ]),
        ("Upper Body", "#3366CC", [
            ("Torso",   ["a_Torso1",  "a_Torso1Back"]),
            ("Arms",    ["a_Shoulder", "a_Arm",     "a_ForeArm", "a_ForeArmAway",
                         "a_Forearm", "a_ForearmAway"]),
        ]),
        ("Lower Body", "#33AA55", [
            ("Torso 2", ["a_Torso2",  "a_Torso2Back"]),
            ("Waist",   ["a_Waist"]),
        ]),
        ("Legs", "#CCAA00", [
            ("Legs",    ["a_Leg"]),
            ("Shin",    ["a_Shin",    "a_ShinSide",  "a_ShinBack",
                         "a_ShinSideStraight","a_ShinSideBend","a_ShinFrontAngle"]),
            ("Foot",    ["a_Foot",    "a_Foot1",    "a_Foot1Side",
                         "a_Foot1Bent","a_FootSide"]),
        ]),
        ("Misc", "#8844CC", []),  # catch-all
    ]

    def _categorize_skin_sprites(self):
        """Returns (dict cat→subcat→[sids], dict cat→color)."""
        cat_fg  = {c[0]: c[1] for c in self._SKIN_CATEGORIES}
        result  = {c[0]: {} for c in self._SKIN_CATEGORIES}
        claimed = set()

        for cat_name, _, sub_list in self._SKIN_CATEGORIES[:-1]:
            for sub_name, prefixes in sub_list:
                result[cat_name][sub_name] = []
                for sid in sorted(self.sprite_tags.keys()):
                    if sid in claimed: continue
                    nm = self._get_export_name(sid)
                    for pfx in prefixes:
                        if nm.lower().startswith(pfx.lower()):
                            result[cat_name][sub_name].append(sid)
                            claimed.add(sid)
                            break

        result["Misc"]["Other"] = [
            sid for sid in sorted(self.sprite_tags.keys()) if sid not in claimed
        ]
        return result, cat_fg

    def _update_canvas_titles(self):
        if self.ref_title_label and self.ref_sprite_id > 0:
            self.ref_title_label.configure(
                text=f"Reference: {self._sprite_display_name(self.ref_sprite_id)}")
        if self.edit_title_label and self.edit_sprite_id > 0:
            # If multiple DIFFERENT sprites are in selected_parts, show all
            all_sids = list(dict.fromkeys(
                self._part_tree_map.get(getattr(p, '_tree_id', None), (None, None))[1]
                for p in self.selected_parts
                if getattr(p, '_tree_id', None) and
                   self._part_tree_map.get(p._tree_id) is not None
            ))
            all_sids = [s for s in all_sids if s is not None and s > 0]
            if len(all_sids) > 1:
                labels = ", ".join(self._sprite_display_name(s) for s in all_sids[:4])
                if len(all_sids) > 4:
                    labels += f" (+{len(all_sids)-4})"
                self.edit_title_label.configure(text=f"Editing: {labels}")
            else:
                self.edit_title_label.configure(
                    text=f"Editor: {self._sprite_display_name(self.edit_sprite_id)}")

    # ═══════════════════════════════════════════════════════════════════
    #  TREE POPULATION
    # ═══════════════════════════════════════════════════════════════════
    def _populate_ref_tree(self):
        self._part_tree_map.clear()
        self._all_ref_tree_ids = []
        for c in self.tree.get_children():
            self.tree.delete(c)
        for p in self.sprite_parts.get(self.ref_sprite_id, []):
            tp = "Sprite" if p.is_sprite else "Shape"
            lbl = (self._sprite_display_name(p.char_id)
                   if p.is_sprite else self._shape_display_name(p.char_id))
            if p.name:
                lbl += f"  [{p.name}]"
            tid = self.tree.insert("", "end", text=lbl,
                                   values=(p.char_id, tp))
            p._tree_id = tid
            self._part_tree_map[tid] = (p, self.ref_sprite_id)
            self._all_ref_tree_ids.append(tid)

    def _populate_edit_tree(self):
        """Builds hierarchical editor tree. Detects skin SWFs and shows categorized tree."""
        self._all_edit_tree_ids = []
        self._sprite_tid_map = {}
        self._tid_to_sid = {}   # reset reverse map
        for c in self.edit_tree.get_children():
            self.edit_tree.delete(c)

        self._part_tree_map.clear()

        CAT_TAGS = {
            "Head":       ("cat_head",  "#CC3333"),
            "Upper Body": ("cat_upper", "#5588EE"),
            "Lower Body": ("cat_lower", "#44BB66"),
            "Legs":       ("cat_legs",  "#DDAA00"),
            "Misc":       ("cat_misc",  "#AA66EE"),
        }
        is_skin = self._is_skin_swf()

        def _insert_sprite(parent_tid, sid):
            nm    = self._get_export_name(sid)   # already clean, no 'DefineSprite_X_'
            label = f"Sprite({sid})" + (f" - {nm}" if nm else "")
            stid = self.edit_tree.insert(
                parent_tid, "end", text=label,
                tags=("sprite_node",))
            self._sprite_tid_map[sid] = stid
            self._tid_to_sid[stid] = sid    # reverse map for selection lookup
            self._all_edit_tree_ids.append((stid, parent_tid))
            for p in self.sprite_parts.get(sid, []):
                tp = "Sprite" if p.is_sprite else "Shape"
                if p.is_sprite:
                    pnm = self._get_export_name(p.char_id)
                    part_label = f"Sprite({p.char_id})" + (f" - {pnm}" if pnm else "")
                else:
                    part_label = f"Shape({p.char_id})"
                    if p.name:
                        part_label += f"  [{p.name}]"
                ptid = self.edit_tree.insert(
                    stid, "end", text=part_label,
                    tags=("part_node",))
                p._tree_id = ptid
                self._part_tree_map[ptid] = (p, sid)
                self._all_edit_tree_ids.append((ptid, stid))

        if is_skin:
            cat_data, _ = self._categorize_skin_sprites()
            # Dark background colors for category bars
            cat_bg = {
                "Head":       "#4A1515",
                "Upper Body": "#152040",
                "Lower Body": "#153020",
                "Legs":       "#3A3000",
                "Misc":       "#2A1540",
            }
            # Per-category subcategory background (darker blend of parent bg)
            subcat_bg = {
                "Head":       "#2D0B0B",
                "Upper Body": "#0A1225",
                "Lower Body": "#091A10",
                "Legs":       "#1E1A00",
                "Misc":       "#160A25",
            }
            for cat_name in ["Head", "Upper Body", "Lower Body", "Legs", "Misc"]:
                tag, color = CAT_TAGS[cat_name]
                cat_tid = self.edit_tree.insert(
                    "", "end", text=f"  {cat_name.upper()}",
                    tags=(tag,))
                self.edit_tree.item(cat_tid, open=False)  # collapsed by default
                self._all_edit_tree_ids.append((cat_tid, ""))
                subs = cat_data.get(cat_name, {})
                has_multi = len([k for k, v in subs.items() if v]) > 1
                for sub_name, sids in subs.items():
                    if not sids:
                        continue
                    if has_multi:
                        sub_tag = f"subcat_{tag}"  # unique tag per category
                        sub_tid = self.edit_tree.insert(
                            cat_tid, "end", text=f"    {sub_name}",
                            tags=(sub_tag,))
                        self.edit_tree.item(sub_tid, open=False)  # collapsed
                        self._all_edit_tree_ids.append((sub_tid, cat_tid))
                        # Configure subcategory style with parent-derived color
                        self.edit_tree.tag_configure(
                            sub_tag, foreground="#C8C8C8",
                            background=subcat_bg.get(cat_name, "#181820"),
                            font=("Segoe UI", 9))
                        parent = sub_tid
                    else:
                        parent = cat_tid
                    for sid in sids:
                        _insert_sprite(parent, sid)

            for cat_name, (tag, color) in CAT_TAGS.items():
                self.edit_tree.tag_configure(
                    tag, foreground="#FFFFFF",
                    background=cat_bg.get(cat_name, "#222"),
                    font=("Segoe UI", 10, "bold"))
            # generic subcat_node fallback (for any unmatched)
            self.edit_tree.tag_configure(
                "subcat_node", foreground="#CCCCCC",
                background="#1C1C2A",
                font=("Segoe UI", 9))



        else:
            for sid in sorted(self.sprite_tags.keys()):
                _insert_sprite("", sid)

        self.edit_tree.tag_configure(
            "sprite_node", foreground="#B0C8E8",
            font=("Segoe UI", 10))
        self.edit_tree.tag_configure("part_node", foreground="#909090")

        # Expand + scroll to current sprite
        if self.edit_sprite_id >= 0 and self.edit_sprite_id in self._sprite_tid_map:
            stid = self._sprite_tid_map[self.edit_sprite_id]
            self.edit_tree.item(stid, open=True)
            self.edit_tree.see(stid)
        
        self._update_tree_checkboxes()

    # ═══════════════════════════════════════════════════════════════════
    #  FLATTEN
    # ═══════════════════════════════════════════════════════════════════
    def _flatten_all(self):
        self._flatten_ref(); self._flatten_edit(); self._redraw_all()

    def _flatten_ref(self):
        self.ref_shapes.clear(); self._depth_ctr = 0
        if self.ref_sprite_id < 0: return
        parts = self.sprite_parts.get(self.ref_sprite_id, [])
        parts.sort(key=lambda p: p.depth)
        for rp in parts:
            if not rp.visible: continue
            mat = (rp.sx, rp.r1, rp.r0, rp.sy, rp.tx, rp.ty)
            self._flatten_r(rp.char_id, self.ref_shapes, mat,
                            (1,0,0,1,0,0), rp)
        self.ref_shapes.sort(key=lambda f: f.depth)

    def _flatten_edit(self):
        self.edit_shapes.clear(); self._depth_ctr = 0
        if self.edit_sprite_id < 0: return
        parts = self.sprite_parts.get(self.edit_sprite_id, [])
        parts.sort(key=lambda p: p.depth)
        for ep in parts:
            if not ep.visible: continue
            mat = (ep.sx, ep.r1, ep.r0, ep.sy, ep.tx, ep.ty)
            self._flatten_r(ep.char_id, self.edit_shapes, mat,
                            (1,0,0,1,0,0), None,
                            direct_owner=ep, owner_sid=self.edit_sprite_id)
        self.edit_shapes.sort(key=lambda f: f.depth)

    def _flatten_r(self, cid, result, mat, parent_mat, ref_owner,
                   direct_owner=None, owner_sid=-1, dlim=10):
        if dlim <= 0: return
        if cid in self.shape_tags:
            bx0, by0, bx1, by1 = self._bounds(cid)
            result.append(FlatShape(
                shape_id=cid, direct_owner=direct_owner,
                owner_sprite_id=owner_sid, ref_owner=ref_owner,
                a=mat[0], b=mat[1], c=mat[2], d=mat[3],
                tx=mat[4], ty=mat[5],
                pa=parent_mat[0], pb=parent_mat[1],
                pc=parent_mat[2], pd=parent_mat[3],
                ptx=parent_mat[4], pty=parent_mat[5],
                depth=self._depth_ctr,
                bounds=(bx0, by0, bx1, by1),
                base_image=self.shape_images.get(cid)))
            self._depth_ctr += 1
        elif cid in self.sprite_tags:
            sub_parts = self.sprite_parts.get(cid, [])
            sub_parts.sort(key=lambda p: p.depth)
            for sp in sub_parts:
                if not sp.visible: continue
                sp_mat = (sp.sx, sp.r1, sp.r0, sp.sy, sp.tx, sp.ty)
                composed = _mul(*mat, *sp_mat)
                self._flatten_r(sp.char_id, result, composed, mat,
                                ref_owner, direct_owner=sp, owner_sid=cid,
                                dlim=dlim - 1)

    # ═══════════════════════════════════════════════════════════════════
    #  RENDERING
    # ═══════════════════════════════════════════════════════════════════
    def _redraw_all(self):
        self._redraw_ref(); self._redraw_edit()

    def _redraw_ref(self):
        cv = self.ref_canvas
        if not cv or not cv.winfo_exists(): return
        cv.delete("all"); self._photo_refs_ref.clear()
        self._rw = cv.winfo_width(); self._rh = cv.winfo_height()
        if self._rw < 10: return
        if self.show_grid and self.show_grid.get():
            self._draw_grid(cv, self._rv, self._rw, self._rh)
        if self._var_green_line and self._var_green_line.get():
            self._draw_origin(cv, self._rv, self._rw, self._rh)
        else:
            # Always draw a minimal origin marker
            ox, oy = self._v2c(0, 0, self._rv, self._rw, self._rh)
            cv.create_oval(ox-3, oy-3, ox+3, oy+3, fill="#333", outline="#555",
                           tags=("origin",))
        # Guides BEHIND shapes (default)
        guide_on = self._var_skin_guide and self._var_skin_guide.get()
        guide_front = self._var_guide_front and self._var_guide_front.get()
        if guide_on and not guide_front:
            self._draw_skin_guides(cv)
        # Reference skin overlay — BEHIND sprites
        ref_skin_front = hasattr(self, "_var_ref_skin_front") and self._var_ref_skin_front.get()
        if self._ref_skin_enabled and not ref_skin_front:
            self._draw_ref_skin_overlay()
        for fs in self.ref_shapes:
            self._draw_shape(cv, fs, self._rv, self._rw, self._rh,
                             self._photo_refs_ref)
        # Guides IN FRONT of shapes
        if guide_on and guide_front:
            self._draw_skin_guides(cv)
        # Reference skin overlay — IN FRONT of sprites
        if self._ref_skin_enabled and ref_skin_front:
            self._draw_ref_skin_overlay()
        # Highlight editing sprite region in ref (fade loop driven separately)
        hl_on = self._var_edit_highlight and self._var_edit_highlight.get()
        if hl_on:
            if not self._hl_fade_running:
                self._hl_alpha = 0
                self._hl_fading_in = True
                self._draw_ref_highlight()
        else:
            if self._hl_fade_running:
                self._stop_hl_fade()
        # Show part IDs if requested
        if self._var_show_ids and self._var_show_ids.get():
            self._draw_part_ids(cv, self.ref_shapes, self._rv, self._rw, self._rh)
        # If dragging from ref, show gizmo on ref too
        if self._active_canvas == "ref" and self.selected_part:
            self._draw_gizmo_on_ref()
        if self.zoom_label_ref:
            self.zoom_label_ref.configure(text=f"{int(self._rv[0]*100)}%")


    def _redraw_edit(self):
        cv = self.edit_canvas
        if not cv or not cv.winfo_exists(): return
        cv.delete("all"); self._photo_refs.clear()
        self._ew = cv.winfo_width(); self._eh = cv.winfo_height()
        if self._ew < 10: return
        if self.show_grid and self.show_grid.get():
            self._draw_grid(cv, self._ev, self._ew, self._eh)
        if self._var_green_line and self._var_green_line.get():
            self._draw_origin(cv, self._ev, self._ew, self._eh)
        for fs in self.edit_shapes:
            tag = f"own_{id(fs.direct_owner)}" if fs.direct_owner else "shape"
            self._draw_shape(cv, fs, self._ev, self._ew, self._eh,
                             self._photo_refs, extra_tag=tag)
        # Selection highlight — always drawn when a part is selected
        if self.selected_part:
            self._draw_edit_highlight(cv)
        # Bounds overlay
        if self._var_show_bounds and self._var_show_bounds.get():
            self._draw_all_bounds(cv, self.edit_shapes, self._ev, self._ew, self._eh)
        # Part IDs overlay
        if self._var_show_ids and self._var_show_ids.get():
            self._draw_part_ids(cv, self.edit_shapes, self._ev, self._ew, self._eh)
        self._draw_gizmo()
        if self.zoom_label_edit:
            self.zoom_label_edit.configure(text=f"{int(self._ev[0]*100)}%")

    def _draw_grid(self, cv, view, cw, ch):
        z = view[0]; gs = GRID_MINOR * z
        if gs < 3: return
        ox, oy = self._v2c(0, 0, view, cw, ch)
        x = ox % gs
        grid_color = self.prefs.get("grid_color", "#202020")
        # Un tono más claro para la grid principal
        grid_major = "#" + "".join(f"{min(255, int(c, 16)+8):02X}" for c in (grid_color[1:3], grid_color[3:5], grid_color[5:7])) if len(grid_color)==7 else "#2A2A2A"
        
        while x < cw:
            cv.create_line(x, 0, x, ch, fill=grid_color, width=1, tags=("grid",))
            x += gs
        y = oy % gs
        while y < ch:
            cv.create_line(0, y, cw, y, fill=grid_color, width=1, tags=("grid",))
            y += gs
        mg = GRID_MINOR * GRID_MAJOR * z
        if mg >= 8:
            x = ox % mg
            while x < cw:
                cv.create_line(x, 0, x, ch, fill=grid_major, width=1, tags=("grid",)); x += mg
            y = oy % mg
            while y < ch:
                cv.create_line(0, y, cw, y, fill=grid_major, width=1, tags=("grid",)); y += mg

    def _draw_origin(self, cv, view, cw, ch):
        ox, oy = self._v2c(0, 0, view, cw, ch)
        # Las líneas del centro se extienden a todo el ancho y alto del canvas
        cv.create_line(0, oy, cw, oy, fill="#444", width=1, dash=(4,4))
        cv.create_line(ox, 0, ox, ch, fill="#444", width=1, dash=(4,4))

    def _draw_skin_guides(self, cv):
        """Draw the skin reference guide lines on the ref canvas (world pixel coords)."""
        color = self._guide_color
        for axis, pos in SKIN_GUIDES:
            if axis == "h":
                # horizontal line at world Y = pos pixels
                cx0, cy = self._v2c(0, pos, self._rv, self._rw, self._rh)
                cx1 = self._rw
                cv.create_line(0, cy, cx1, cy,
                               fill=color, width=1, dash=(6, 4),
                               tags=("guide",))
                cv.create_text(4, cy - 8, text=f"Y={pos}", fill=color,
                               font=("Segoe UI", 8), anchor="w", tags=("guide",))
            else:
                # vertical line at world X = pos pixels
                cx, cy0 = self._v2c(pos, 0, self._rv, self._rw, self._rh)
                cv.create_line(cx, 0, cx, self._rh,
                               fill=color, width=1, dash=(6, 4),
                               tags=("guide",))
                cv.create_text(cx + 4, 4, text=f"X={pos}", fill=color,
                               font=("Segoe UI", 8), anchor="nw", tags=("guide",))

    def _draw_part_ids(self, cv, shapes, view, cw, ch):
        """Overlay CharacterID on each shape's visual center."""
        for fs in shapes:
            pts = self._corners_c(fs, view, cw, ch)
            if not pts: continue
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            if max(xs) < 0 or min(xs) > cw or max(ys) < 0 or min(ys) > ch:
                continue
            cx = (min(xs) + max(xs)) / 2
            cy = (min(ys) + max(ys)) / 2
            cv.create_text(cx, cy, text=str(fs.shape_id),
                           fill="#AAAAAA", font=("Segoe UI", 8),
                           tags=("ids",))

    def _draw_edit_highlight(self, cv):
        """Draw colored outline around shapes of selected part(s)."""
        # Primary selection: bright color
        primary_shapes = [f for f in self.edit_shapes
                          if f.direct_owner is self.selected_part]
        # Secondary (multi-selection) shapes: dimmer color
        secondary_parts = [p for p in self.selected_parts
                           if p is not self.selected_part]

        def _outline_part(part, color, width):
            for fs in self.edit_shapes:
                if fs.direct_owner is not part:
                    continue
                pts = self._corners_c(fs, self._ev, self._ew, self._eh)
                if not pts: continue
                coords = []
                for p in pts:
                    coords.extend(p)
                if len(coords) >= 6:
                    cv.create_polygon(*coords, fill="",
                                      outline=color, width=width,
                                      tags=("sel_hl",))

        # Draw secondary selections (dimmer)
        for p in secondary_parts:
            _outline_part(p, "#5588AA", 1)
        # Draw primary selection (bright)
        _outline_part(self.selected_part, self._highlight_color, 2)

    def _draw_all_bounds(self, cv, shapes, view, cw, ch):
        """Draw bounding boxes for all shapes."""
        for fs in shapes:
            pts = self._corners_c(fs, view, cw, ch)
            if not pts: continue
            coords = []
            for p in pts:
                coords.extend(p)
            if len(coords) >= 6:
                cv.create_polygon(*coords, fill="", outline="#3A3A5A",
                                  width=1, dash=(2, 4), tags=("bounds",))

    # ─── Zoom-aware quality render cache ──────────────────────────────
    _ZOOM_BUCKET_STEP = 0.05   # 5% increments — re-render every 5% zoom change
    _ZOOM_CACHE_LIMIT = 512    # max cached entries across all shapes

    def _zoom_bucket(self, zoom: float) -> float:
        """Round zoom to nearest bucket so cache is shared across tiny changes."""
        s = self._ZOOM_BUCKET_STEP
        return round(round(zoom / s) * s, 4)

    def _flush_render_cache(self):
        """Wipe the entire shape render cache (call after SWF reload)."""
        self._shape_render_cache.clear()
        self._render_cache_zoom = 0.0

    def _draw_shape(self, cv, fs, view, cw, ch, photo_store, extra_tag="shape"):
        # viewport culling
        pts = self._corners_c(fs, view, cw, ch)
        if pts:
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            if max(xs) < -100 or min(xs) > cw+100 or max(ys) < -100 or min(ys) > ch+100:
                return
                
        sid = fs.shape_id
        use_skia = HAS_SKIA and (sid in self._svg_doms)
        
        if not use_skia and fs.base_image is None:
            self._draw_ph(cv, fs, view, cw, ch, extra_tag); return
            
        try:
            bxmin, bymin = fs.bounds[0], fs.bounds[1]
            vz = view[0]
            
            if use_skia:
                svg_dom = self._svg_doms[sid]
                sz = svg_dom.containerSize()
                sw, sh = sz.width(), sz.height()
                EZ = 1.0  # SVGs are independent of export zoom
            else:
                src = fs.base_image
                sw, sh = src.width, src.height
                EZ = self.export_zoom
                
            if sw < 1 or sh < 1: return
            
            opx = -bxmin / TWIP * EZ; opy = -bymin / TWIP * EZ
            A = vz * fs.a / EZ; B = vz * fs.b / EZ
            C = vz * fs.c / EZ; D = vz * fs.d / EZ
            E = -(A*opx + B*opy) + (fs.tx - view[1]) * vz + cw/2
            F = -(C*opx + D*opy) + (fs.ty - view[2]) * vz + ch/2
            corners = [(E, F), (A*sw+E, C*sw+F),
                       (B*sh+E, D*sh+F), (A*sw+B*sh+E, C*sw+D*sh+F)]
            xs = [p[0] for p in corners]; ys = [p[1] for p in corners]
            x0, y0 = math.floor(min(xs)), math.floor(min(ys))
            x1, y1 = math.ceil(max(xs)), math.ceil(max(ys))
            
            # Viewport Clipping (Deferred / Bounded Rasterization)
            v_x0 = max(x0, -100)
            v_y0 = max(y0, -100)
            v_x1 = min(x1, cw + 100)
            v_y1 = min(y1, ch + 100)
            
            full_w, full_h = x1 - x0, y1 - y0
            if full_w < 1 or full_h < 1: return
            
            # ── Zoom-aware cache lookup ────────────────────────────────────
            zb = self._zoom_bucket(vz)
            rot_key = (round(A, 4), round(B, 4), round(C, 4), round(D, 4))
            
            # Dynamic Deferred Rendering: 
            # If the shape is small enough, rasterize it entirely so panning hits the cache 100%.
            # If it's massive, clip it to the viewport to prevent memory explosions (crashes).
            if full_w <= MAX_RENDER_DIM and full_h <= MAX_RENDER_DIM:
                cx0, cy0 = x0, y0
                cow, coh = full_w, full_h
                cache_key = (zb, rot_key)
            else:
                cx0, cy0 = v_x0, v_y0
                cow, coh = v_x1 - v_x0, v_y1 - v_y0
                if cow < 1 or coh < 1: return
                # Include the relative chunk position in the cache key
                cache_key = (zb, rot_key, cx0 - E, cy0 - F, cow, coh)
            
            det = A*D - B*C
            if abs(det) < 1e-12: return
            iA = D/det; iB = -B/det; iC = -C/det; iD = A/det
            
            # Adjust inverse transform offset for the origin of our rasterized chunk
            cp = iA*(cx0-E) + iB*(cy0-F)
            fp = iC*(cx0-E) + iD*(cy0-F)

            cached = self._shape_render_cache.get(sid, {}).get(cache_key)
            if cached is not None:
                # Cache hit
                out, _ = cached
            else:
                # Cache miss — rasterize bounded region
                if use_skia:
                    # Skia vector render (Infinite quality)
                    surface = skia.Surface(cow, coh)
                    canvas = surface.getCanvas()
                    canvas.clear(skia.ColorTRANSPARENT)
                    # Translation maps shape origin to chunk origin
                    canvas.concat(skia.Matrix.MakeAll(
                        A, B, E - cx0,
                        C, D, F - cy0,
                        0, 0, 1
                    ))
                    svg_dom.render(canvas)
                    
                    image = surface.makeImageSnapshot()
                    array = image.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)
                    out = Image.fromarray(array, 'RGBA')
                else:
                    # Fallback PIL raster affine
                    out = src.transform(
                        (cow, coh), Image.AFFINE,
                        (iA, iB, cp, iC, iD, fp),
                        resample=Image.BICUBIC
                    )
                    
                # Store PIL image in cache
                if sid not in self._shape_render_cache:
                    self._shape_render_cache[sid] = {}
                self._shape_render_cache[sid][cache_key] = (out, True)
                
                # Evict oldest entries if cache is too large
                total = sum(len(v) for v in self._shape_render_cache.values())
                if total > self._ZOOM_CACHE_LIMIT:
                    for _sid in list(self._shape_render_cache):
                        if len(self._shape_render_cache[_sid]) > 1:
                            oldest = next(iter(self._shape_render_cache[_sid]))
                            del self._shape_render_cache[_sid][oldest]
                        break

            photo = ImageTk.PhotoImage(out)
            photo_store.append(photo)
            fs.canvas_id  = cv.create_image(cx0, cy0, image=photo, anchor="nw",
                                            tags=("shape", extra_tag))
            fs.photo      = photo
            fs.canvas_img    = out
            fs.canvas_img_x0 = cx0
            fs.canvas_img_y0 = cy0
        except Exception as exc:
            print(f"[SE] Render error shape {sid}: {exc}")
            self._draw_ph(cv, fs, view, cw, ch, extra_tag)

    def _draw_ph(self, cv, fs, view, cw, ch, tag):
        pts = self._corners_c(fs, view, cw, ch)
        if not pts: return
        coords = []
        for p in pts:
            coords.extend(p)
        if len(coords) >= 6:
            cv.create_polygon(*coords, fill="", outline="#555", width=1,
                              dash=(3,3), tags=("ph", tag))

    def _corners_c(self, fs, view, cw, ch):
        bx0, by0, bx1, by1 = fs.bounds
        pts = [(bx0/TWIP, by0/TWIP), (bx1/TWIP, by0/TWIP),
               (bx1/TWIP, by1/TWIP), (bx0/TWIP, by1/TWIP)]
        out = []
        for x, y in pts:
            nx = fs.a*x + fs.b*y + fs.tx
            ny = fs.c*x + fs.d*y + fs.ty
            out.append(self._v2c(nx, ny, view, cw, ch))
        return out

    def _corners_v(self, fs):
        bx0, by0, bx1, by1 = fs.bounds
        pts = [(bx0/TWIP, by0/TWIP), (bx1/TWIP, by0/TWIP),
               (bx1/TWIP, by1/TWIP), (bx0/TWIP, by1/TWIP)]
        return [(fs.a*x + fs.b*y + fs.tx, fs.c*x + fs.d*y + fs.ty)
                for x, y in pts]

    # ── Reference highlight ───────────────────────────────────────────
    def _draw_ref_highlight(self):
        """Draw a smooth tinted overlay over the exact pixels of editing sprite shapes in ref canvas."""
        if self.edit_sprite_id < 0 and not self.checked_tids: return
        if not (self._var_edit_highlight and self._var_edit_highlight.get()): return

        # Start fade loop if not already running
        if not self._hl_fade_running:
            self._hl_fade_running = True
            self._hl_fade_loop()

    def _hl_fade_loop(self):
        """Smooth fade in/out loop: 2 second cycle at 50ms intervals (40 steps)."""
        if not self.ref_canvas or not self.ref_canvas.winfo_exists():
            self._hl_fade_running = False
            return
        if not (self._var_edit_highlight and self._var_edit_highlight.get()):
            self._hl_fade_running = False
            self._hl_alpha = 0
            return

        # 40 steps total, 20 in 20 out = 50ms each → 2s full cycle
        STEP = 5   # alpha increment per tick (0-80 range → 16 steps each dir)
        MAX_A = 75

        if self._hl_fading_in:
            self._hl_alpha = min(self._hl_alpha + STEP, MAX_A)
            if self._hl_alpha >= MAX_A:
                self._hl_fading_in = False
        else:
            self._hl_alpha = max(self._hl_alpha - STEP, 0)
            if self._hl_alpha <= 0:
                self._hl_fading_in = True

        # Redraw only the overlay without full redraw (performance)
        try:
            self.ref_canvas.delete("ref_hl")
        except Exception:
            pass

        select_mode = self._var_select_mode and self._var_select_mode.get()
        target_sids = set()
        
        if select_mode and getattr(self, "checked_tids", None):
            for tid in self.checked_tids:
                sid = self._tid_to_sid.get(tid, -1)
                if sid != -1: 
                    target_sids.add(sid)
        elif self.edit_sprite_id >= 0:
            target_sids.add(self.edit_sprite_id)

        shapes = [fs for fs in self.ref_shapes
                  if fs.ref_owner and getattr(fs.ref_owner, "char_id", -1) in target_sids]
        
        if shapes:
            try:
                cw = int(self._rw) or 1; ch = int(self._rh) or 1
                overlay = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
                draw = ImageDraw.Draw(overlay)
                hl_hex = self.prefs.get("hl_edit_color", "#FFD700")
                try:
                    # Convert hex to RGB
                    hl_hex = hl_hex.lstrip('#')
                    r, g, b = tuple(int(hl_hex[i:i+2], 16) for i in (0, 2, 4))
                except Exception:
                    r, g, b = 0xFF, 0xD7, 0x00
                    
                for fs in shapes:
                    if hasattr(fs, 'canvas_img') and fs.canvas_img:
                        solid = Image.new("RGBA", fs.canvas_img.size, (r, g, b, self._hl_alpha))
                        try:
                            a_ch = fs.canvas_img.getchannel("A")
                            overlay.paste(solid, (int(fs.canvas_img_x0), int(fs.canvas_img_y0)), mask=a_ch)
                        except Exception:
                            pass
                    else:
                        # Fallback a rectangulo si no hay imagen de canvas
                        pts = self._corners_c(fs, self._rv, self._rw, self._rh)
                        if pts and len(pts) >= 3:
                            flat = [coord for p in pts for coord in p]
                            draw.polygon(flat, fill=(r, g, b, self._hl_alpha))
                self._hl_photo = ImageTk.PhotoImage(overlay)
                self.ref_canvas.create_image(0, 0, image=self._hl_photo,
                                             anchor="nw", tags=("ref_hl",))
            except Exception:
                pass

        self._hl_fade_id = self.ref_canvas.after(50, self._hl_fade_loop)

    def _stop_hl_fade(self):
        """Stop the fade loop and clear the overlay."""
        self._hl_fade_running = False
        self._hl_alpha = 0
        if self._hl_fade_id:
            try:
                self.ref_canvas.after_cancel(self._hl_fade_id)
            except Exception:
                pass
            self._hl_fade_id = None
        try:
            self.ref_canvas.delete("ref_hl")
        except Exception:
            pass

    def _draw_gizmo_on_ref(self):
        """Draw a selection box on the ref canvas for the selected part."""
        if not self.selected_part: return
        shapes = [fs for fs in self.ref_shapes
                  if fs.ref_owner and fs.ref_owner.char_id == self.edit_sprite_id]
        sel_shapes = [fs for fs in shapes if fs.direct_owner is self.selected_part]
        if not sel_shapes: return
        mn_x = mn_y = float("inf"); mx_x = mx_y = float("-inf")
        for fs in sel_shapes:
            for cx, cy in self._corners_c(fs, self._rv, self._rw, self._rh):
                mn_x = min(mn_x, cx); mn_y = min(mn_y, cy)
                mx_x = max(mx_x, cx); mx_y = max(mx_y, cy)
        if mn_x >= mx_x: return
        self.ref_canvas.create_rectangle(
            mn_x-2, mn_y-2, mx_x+2, mx_y+2,
            outline=AC, width=2, dash=(5,3), tags=("ref_gizmo",))

    # ── Main gizmo ────────────────────────────────────────────────────
    def _draw_gizmo(self):
        if self.selected_part is None:
            self._sel_bbox = self._sel_center_c = None; return
        shapes = [f for f in self.edit_shapes
                  if f.direct_owner is self.selected_part]
        if not shapes:
            self._sel_bbox = self._sel_center_c = None; return
        mn_x = mn_y = float("inf"); mx_x = mx_y = float("-inf")
        for fs in shapes:
            for cx, cy in self._corners_c(fs, self._ev, self._ew, self._eh):
                mn_x = min(mn_x, cx); mn_y = min(mn_y, cy)
                mx_x = max(mx_x, cx); mx_y = max(mx_y, cy)
        if mn_x >= mx_x:
            self._sel_bbox = self._sel_center_c = None; return
        pad = 4
        self._sel_bbox = (mn_x-pad, mn_y-pad, mx_x+pad, mx_y+pad)
        x0, y0, x1, y1 = self._sel_bbox
        cx_c, cy_c = (x0+x1)/2, (y0+y1)/2
        self._sel_center_c = (cx_c, cy_c)
        cv = self.edit_canvas

        if self.mode == MODE_MOVE:
            cv.create_rectangle(x0, y0, x1, y1, outline=AC, width=1,
                                dash=(6,3), tags=("gizmo",))
            al = ARROW_LEN
            cv.create_line(cx_c, cy_c, cx_c+al, cy_c, fill=RED, width=2,
                           arrow="last", tags=("gizmo",))
            cv.create_text(cx_c+al+10, cy_c, text="X", fill=RED,
                           font=("Segoe UI", 10, "bold"), tags=("gizmo",))
            cv.create_line(cx_c, cy_c, cx_c, cy_c+al, fill=BLUE, width=2,
                           arrow="last", tags=("gizmo",))
            cv.create_text(cx_c, cy_c+al+10, text="Y", fill=BLUE,
                           font=("Segoe UI", 10, "bold"), tags=("gizmo",))

        elif self.mode == MODE_ROTATE:
            radius = max(30, min(x1-x0, y1-y0)/2 + 10)
            pv_cx = cx_c + self._pivot_offset[0] * self._ev[0]
            pv_cy = cy_c + self._pivot_offset[1] * self._ev[0]
            cv.create_oval(pv_cx-radius, pv_cy-radius,
                           pv_cx+radius, pv_cy+radius,
                           outline=AC, width=2, dash=(4,4), tags=("gizmo",))
            ang = math.atan2(self.selected_part.r0, self.selected_part.sx)
            lx = pv_cx + radius * math.cos(ang)
            ly = pv_cy + radius * math.sin(ang)
            cv.create_line(pv_cx, pv_cy, lx, ly, fill=AC, width=2,
                           tags=("gizmo",))
            cv.create_oval(lx-4, ly-4, lx+4, ly+4, fill=AC, outline="#000",
                           tags=("gizmo",))
            ps = 7
            cv.create_line(pv_cx-ps, pv_cy, pv_cx+ps, pv_cy, fill=ORANGE,
                           width=2, tags=("gizmo", "pivot"))
            cv.create_line(pv_cx, pv_cy-ps, pv_cx, pv_cy+ps, fill=ORANGE,
                           width=2, tags=("gizmo", "pivot"))
            cv.create_oval(pv_cx-3, pv_cy-3, pv_cx+3, pv_cy+3,
                           fill=ORANGE, outline="#000", tags=("gizmo", "pivot"))

        elif self.mode == MODE_SCALE:
            cv.create_rectangle(x0, y0, x1, y1, outline=AC, width=2,
                                dash=(6,3), tags=("gizmo",))
            mx_c, my_c = (x0+x1)/2, (y0+y1)/2
            hpos = {"tl":(x0,y0),"tm":(mx_c,y0),"tr":(x1,y0),
                    "ml":(x0,my_c),"mr":(x1,my_c),
                    "bl":(x0,y1),"bm":(mx_c,y1),"br":(x1,y1)}
            for hid,(hx,hy) in hpos.items():
                f = AC if hid in ("tl","tr","bl","br") else ACL
                cv.create_rectangle(hx-HS, hy-HS, hx+HS, hy+HS,
                                    fill=f, outline="#000", width=1,
                                    tags=("handle", hid))

        elif self.mode == MODE_SKEW:
            cv.create_rectangle(x0, y0, x1, y1, outline=PURPLE, width=2,
                                dash=(6,3), tags=("gizmo",))
            mx_c, my_c = (x0+x1)/2, (y0+y1)/2
            sl = 25
            for yy, nm in [(y0, "skew_top"), (y1, "skew_bottom")]:
                cv.create_line(mx_c-sl, yy, mx_c+sl, yy, fill=RED, width=3,
                               tags=("gizmo", nm))
                cv.create_polygon(mx_c+sl,yy-4, mx_c+sl,yy+4,
                                  mx_c+sl+6,yy, fill=RED, tags=("gizmo",nm))
                cv.create_polygon(mx_c-sl,yy-4, mx_c-sl,yy+4,
                                  mx_c-sl-6,yy, fill=RED, tags=("gizmo",nm))
            for xx, nm in [(x0, "skew_left"), (x1, "skew_right")]:
                cv.create_line(xx, my_c-sl, xx, my_c+sl, fill=BLUE, width=3,
                               tags=("gizmo", nm))
                cv.create_polygon(xx-4,my_c-sl, xx+4,my_c-sl,
                                  xx,my_c-sl-6, fill=BLUE, tags=("gizmo",nm))
                cv.create_polygon(xx-4,my_c+sl, xx+4,my_c+sl,
                                  xx,my_c+sl+6, fill=BLUE, tags=("gizmo",nm))

    # ═══════════════════════════════════════════════════════════════════
    #  CANVAS EVENTS
    # ═══════════════════════════════════════════════════════════════════
    def _on_cv_resize(self, ev, tag):
        if tag == "ref":
            self._rw, self._rh = ev.width, ev.height; self._redraw_ref()
        else:
            self._ew, self._eh = ev.width, ev.height; self._redraw_edit()

    def _on_click(self, ev, tag):
        try: self.parent.winfo_toplevel().focus_set()
        except Exception: pass
        if self._space_held:
            self._pan_start(ev, tag); return
        if tag == "ref":
            self._click_ref(ev)
        else:
            self._click_edit(ev)

    # ── Click ref ─────────────────────────────────────────────────────
    def _click_ref(self, ev):
        hit = self._hit_ref(ev.x, ev.y)
        if hit is None: return
        fs = hit
        if fs.ref_owner and fs.ref_owner.is_sprite:
            child_sid = fs.ref_owner.char_id
            self._open_in_editor(child_sid)
            if fs.direct_owner and fs.owner_sprite_id == child_sid:
                self.selected_part = fs.direct_owner
                self.selected_sprite_id = child_sid
                self.selected_parts = [self.selected_part]
                self._highlight_edit_tree(); self._update_props()
                try:
                    tid = self.selected_part._tree_id
                    if tid and self.edit_tree.exists(tid):
                        self._tree_lock = True
                        self.edit_tree.selection_set(tid)
                        self.edit_tree.see(tid)
                except Exception:
                    pass
                finally:
                    self._tree_lock = False
        if self.selected_part:
            self._active_canvas = "ref"
            self._drag = "move"
            self._drag_sx, self._drag_sy = ev.x, ev.y
            self._drag_orig = self._st(self.selected_part)
            self._drag_orig_multi = {id(p): self._st(p) for p in self.selected_parts}
            self._drag_parent_mat = (fs.pa, fs.pb, fs.pc, fs.pd, fs.ptx, fs.pty)
            self._flatten_edit(); self._redraw_edit()

    # ── Click edit ────────────────────────────────────────────────────
    def _click_edit(self, ev):
        # Pivot drag in rotate mode
        if self.selected_part and self.mode == MODE_ROTATE and self._sel_center_c:
            cx_c, cy_c = self._sel_center_c
            pv_cx = cx_c + self._pivot_offset[0] * self._ev[0]
            pv_cy = cy_c + self._pivot_offset[1] * self._ev[0]
            if abs(ev.x - pv_cx) <= 10 and abs(ev.y - pv_cy) <= 10:
                self._active_canvas = "edit"
                self._drag = "pivot"
                self._drag_sx, self._drag_sy = ev.x, ev.y
                return

        # Scale handle hit
        if self.selected_part and self._sel_bbox and self.mode == MODE_SCALE:
            h = self._hit_handle(ev.x, ev.y)
            if h:
                self._start_handle_drag(h, ev); return

        # Skew handle hit
        if self.selected_part and self._sel_bbox and self.mode == MODE_SKEW:
            sh = self._hit_skew(ev.x, ev.y)
            if sh:
                self._active_canvas = "edit"
                self._drag = f"skew_{sh}"
                self._drag_sx, self._drag_sy = ev.x, ev.y
                self._drag_orig = self._st(self.selected_part)
                return

        # Edit canvas hit test — no transparency: select the topmost
        # bounding-quad shape regardless of alpha (unlike reference panel)
        items = self.edit_canvas.find_overlapping(ev.x-5, ev.y-5, ev.x+5, ev.y+5)
        sel = None
        for iid in reversed(items):
            for t in self.edit_canvas.gettags(iid):
                if t.startswith("own_"):
                    oid = int(t[4:])
                    for p in self.sprite_parts.get(self.edit_sprite_id, []):
                        if id(p) == oid:
                            sel = p; break
                    if sel: break
            if sel: break

        if sel != self.selected_part:
            self.selected_part = sel
            # Sync selected_parts — single canvas-click replaces multi-selection
            self.selected_parts = [sel] if sel else []
            self.selected_sprite_id = self.edit_sprite_id if sel else -1
            self._pivot_offset = (0.0, 0.0)
            self._update_props(); self._highlight_edit_tree()
            self._redraw_edit()

        if self.selected_part is None: return
        # Safety: if selected_parts is empty (e.g. after open_in_editor resets),
        # always include at least the primary part
        if not self.selected_parts:
            self.selected_parts = [self.selected_part]
        self._active_canvas = "edit"
        self._drag_sx, self._drag_sy = ev.x, ev.y
        self._drag_orig = self._st(self.selected_part)
        self._drag_orig_multi = {id(p): self._st(p) for p in self.selected_parts}
        self._drag_parent_mat = (1, 0, 0, 1, 0, 0)

        if self.mode == MODE_MOVE:
            ax = self._hit_axis(ev.x, ev.y)
            self._drag = f"axis_{ax}" if ax else "move"
        elif self.mode == MODE_ROTATE:
            # FIXED v6: always compute pivot fresh from shape bounds — no stale (0,0)
            cx_c, cy_c = self._compute_pivot_canvas()
            pv_cx = cx_c + self._pivot_offset[0] * self._ev[0]
            pv_cy = cy_c + self._pivot_offset[1] * self._ev[0]
            self._drag_pivot_c = (pv_cx, pv_cy)
            self._drag_mouse_start_angle = math.atan2(ev.y - pv_cy, ev.x - pv_cx)
            self._drag_mat_start_angle = math.atan2(
                self.selected_part.r0, self.selected_part.sx)
            self._drag = "rotate"
        elif self.mode == MODE_SCALE:
            self._drag = "move"
        elif self.mode == MODE_SKEW:
            self._drag = "move"

    def _hit_axis(self, mx, my):
        if not self._sel_center_c: return None
        cx, cy = self._sel_center_c
        al = ARROW_LEN
        if cy-8 <= my <= cy+8 and cx <= mx <= cx+al+10:
            return "x"
        if cx-8 <= mx <= cx+8 and cy <= my <= cy+al+10:
            return "y"
        return None

    def _hit_handle(self, mx, my):
        if not self._sel_bbox: return None
        x0,y0,x1,y1 = self._sel_bbox
        cx,cy = (x0+x1)/2, (y0+y1)/2
        hpos = {"tl":(x0,y0),"tm":(cx,y0),"tr":(x1,y0),
                "ml":(x0,cy),"mr":(x1,cy),
                "bl":(x0,y1),"bm":(cx,y1),"br":(x1,y1)}
        for hid,(hx,hy) in hpos.items():
            if abs(mx-hx) <= HS+3 and abs(my-hy) <= HS+3:
                return hid
        return None

    def _hit_skew(self, mx, my):
        if not self._sel_bbox: return None
        x0,y0,x1,y1 = self._sel_bbox
        mc, mcy = (x0+x1)/2, (y0+y1)/2
        sl = 30
        if abs(my-y0) <= 8 and mc-sl-10 <= mx <= mc+sl+10: return "h_top"
        if abs(my-y1) <= 8 and mc-sl-10 <= mx <= mc+sl+10: return "h_bottom"
        if abs(mx-x0) <= 8 and mcy-sl-10 <= my <= mcy+sl+10: return "v_left"
        if abs(mx-x1) <= 8 and mcy-sl-10 <= my <= mcy+sl+10: return "v_right"
        return None

    def _start_handle_drag(self, handle, ev):
        self._active_canvas = "edit"
        self._drag = f"handle_{handle}"
        self._drag_handle = handle
        self._drag_sx, self._drag_sy = ev.x, ev.y
        self._drag_orig = self._st(self.selected_part)
        self._drag_orig_multi = {id(p): self._st(p) for p in self.selected_parts}
        self._drag_orig_bbox = self._sel_bbox
        if self._sel_bbox:
            x0,y0,x1,y1 = self._sel_bbox; cx,cy = (x0+x1)/2, (y0+y1)/2
            hpos = {"tl":(x0,y0),"tm":(cx,y0),"tr":(x1,y0),"ml":(x0,cy),
                    "mr":(x1,cy),"bl":(x0,y1),"bm":(cx,y1),"br":(x1,y1)}
            opp = {"tl":"br","tm":"bm","tr":"bl","ml":"mr",
                   "mr":"ml","bl":"tr","bm":"tm","br":"tl"}
            ac = hpos[opp[handle]]
            self._drag_anchor_v = self._c2v(*ac, self._ev, self._ew, self._eh)

    # ── Drag ──────────────────────────────────────────────────────────
    def _on_drag(self, ev, tag):
        if self._space_held and self._pan:
            self._pan_move(ev, tag); return
        if self._drag == "": return
        self._drag_mx, self._drag_my = ev.x, ev.y
        if self._drag_throttle_id is None:
            cv = self.ref_canvas if self._active_canvas == "ref" else self.edit_canvas
            self._drag_throttle_id = cv.after(16, self._drag_tick)

    def _drag_tick(self):
        self._drag_throttle_id = None
        mx, my = self._drag_mx, self._drag_my
        if not self.selected_part: return
        p = self.selected_part

        # Pivot drag
        if self._drag == "pivot":
            cx_c, cy_c = self._sel_center_c or (0, 0)
            self._pivot_offset = ((mx-cx_c)/self._ev[0],
                                  (my-cy_c)/self._ev[0])
            self._redraw_edit(); return

        view = self._rv if self._active_canvas == "ref" else self._ev
        cw = self._rw if self._active_canvas == "ref" else self._ew
        ch = self._rh if self._active_canvas == "ref" else self._eh
        zoom = view[0]

        if self._drag in ("move", "axis_x", "axis_y"):
            dsx = mx - self._drag_sx; dsy = my - self._drag_sy
            dvx = dsx / zoom; dvy = dsy / zoom
            pm = self._drag_parent_mat
            ia, ib, ic, id_ = _inv_linear(pm[0], pm[1], pm[2], pm[3])
            dtx = ia*dvx + ib*dvy; dty = ic*dvx + id_*dvy
            if self._drag == "axis_x": dty = 0
            elif self._drag == "axis_y": dtx = 0
            for pt in self.selected_parts:
                orig = self._drag_orig_multi.get(id(pt))
                if orig:
                    pt.tx = orig["tx"] + dtx
                    pt.ty = orig["ty"] + dty

        elif self._drag == "rotate":
            # FIXED v7: apply rotation as delta multiplication — preserves skew/scale
            pv_cx, pv_cy = self._drag_pivot_c
            cur_mouse_angle = math.atan2(my - pv_cy, mx - pv_cx)
            delta = cur_mouse_angle - self._drag_mouse_start_angle
            if self._shift:
                snap = math.pi / 12  # 15°
                delta = round(delta / snap) * snap
            
            c, s = math.cos(delta), math.sin(delta)
            ca, sa = math.cos(delta), math.sin(delta)
            pv_vx, pv_vy = self._c2v(pv_cx, pv_cy, self._ev, self._ew, self._eh)

            for pt in self.selected_parts:
                orig = self._drag_orig_multi.get(id(pt))
                if orig:
                    # Multiplicar la rotación delta por la matriz original
                    # R * M_orig donde R = [[c, -s], [s, c]]
                    pt.sx = c * orig["sx"] - s * orig["r0"]
                    pt.r0 = s * orig["sx"] + c * orig["r0"]
                    pt.r1 = c * orig["r1"] - s * orig["sy"]
                    pt.sy = s * orig["r1"] + c * orig["sy"]
                    # Rotar posición alrededor del pivot
                    ox, oy = orig["tx"], orig["ty"]
                    cdx, cdy = ox - pv_vx, oy - pv_vy
                    pt.tx = pv_vx + cdx * ca - cdy * sa
                    pt.ty = pv_vy + cdx * sa + cdy * ca

        elif self._drag.startswith("handle_"):
            self._do_handle_scale(mx, my)

        elif self._drag.startswith("skew_"):
            self._do_skew(mx, my)

        self._flatten_ref(); self._flatten_edit()
        self._redraw_ref(); self._redraw_edit()
        self._update_props()

    def _do_handle_scale(self, mx, my):
        p = self.selected_part
        if not p or not self._drag_orig_bbox: return
        h = self._drag_handle
        x0,y0,x1,y1 = self._drag_orig_bbox; cx,cy = (x0+x1)/2, (y0+y1)/2
        hpos = {"tl":(x0,y0),"tm":(cx,y0),"tr":(x1,y0),"ml":(x0,cy),
                "mr":(x1,cy),"bl":(x0,y1),"bm":(cx,y1),"br":(x1,y1)}
        opp = {"tl":"br","tm":"bm","tr":"bl","ml":"mr",
               "mr":"ml","bl":"tr","bm":"tm","br":"tl"}
        orig_h = hpos[h]; anch = hpos[opp[h]]
        dx_orig = orig_h[0]-anch[0]; dy_orig = orig_h[1]-anch[1]
        dx_new = mx-anch[0]; dy_new = my-anch[1]
        if h in ("tm","bm"):
            fx = 1.0; fy = dy_new/dy_orig if abs(dy_orig)>1 else 1.0
        elif h in ("ml","mr"):
            fx = dx_new/dx_orig if abs(dx_orig)>1 else 1.0; fy = 1.0
        else:
            fx = dx_new/dx_orig if abs(dx_orig)>1 else 1.0
            fy = dy_new/dy_orig if abs(dy_orig)>1 else 1.0
            if self._shift or (self._var_uniform_scale and self._var_uniform_scale.get()):
                f = (abs(fx)+abs(fy))/2
                fx = math.copysign(f, fx) if fx else f
                fy = math.copysign(f, fy) if fy else f
        av = self._drag_anchor_v
        for pt in self.selected_parts:
            orig = self._drag_orig_multi.get(id(pt))
            if not orig: continue
            pt.sx = orig["sx"]*fx; pt.sy = orig["sy"]*fy
            pt.r0 = orig["r0"]*fx; pt.r1 = orig["r1"]*fy
            pt.tx = av[0] + fx*(orig["tx"]-av[0])
            pt.ty = av[1] + fy*(orig["ty"]-av[1])

    def _do_skew(self, mx, my):
        if not self.selected_part: return
        dsx = mx - self._drag_sx; dsy = my - self._drag_sy
        zoom = self._ev[0]; sf = 0.003
        for pt in self.selected_parts:
            orig = self._drag_orig_multi.get(id(pt))
            if not orig: continue
            if self._drag in ("skew_h_top", "skew_h_bottom"):
                d = dsx / zoom * sf
                if self._drag == "skew_h_top": d = -d
                pt.r1 = orig["r1"] + d * math.sqrt(orig["sy"]**2 + orig["r1"]**2)
            elif self._drag in ("skew_v_left", "skew_v_right"):
                d = dsy / zoom * sf
                if self._drag == "skew_v_left": d = -d
                pt.r0 = orig["r0"] + d * math.sqrt(orig["sx"]**2 + orig["r0"]**2)

    def _on_release(self, ev, tag):
        if self._space_held:
            self._pan_end(ev, tag); return
        if self._drag_throttle_id:
            cv = self.ref_canvas if self._active_canvas == "ref" else self.edit_canvas
            if cv and cv.winfo_exists():
                cv.after_cancel(self._drag_throttle_id)
            self._drag_throttle_id = None
        if self._drag == "pivot":
            self._drag = ""; self._active_canvas = None; return
        if self._drag and self.selected_part:
            undo_list = []
            for pt in self.selected_parts:
                new_st = self._st(pt)
                orig_st = self._drag_orig_multi.get(id(pt))
                if orig_st and orig_st != new_st:
                    undo_list.append((pt, orig_st, new_st))
            if undo_list:
                self._push_undo(undo_list)
        # BUG-FIX: reset _active_canvas BEFORE _flatten_all so that _redraw_ref
        # does NOT draw the yellow gizmo box after merely clicking (no drag).
        self._drag = ""; self._active_canvas = None
        self._flatten_all()

    def _compute_pivot_canvas(self) -> Tuple[float, float]:
        """Return canvas-space pivot for rotation (centre of selected part's shapes).
        Always computed fresh so that it is never stale regardless of gizmo state."""
        if not self.selected_part:
            return (self._ew / 2, self._eh / 2)
        shapes = [f for f in self.edit_shapes
                  if f.direct_owner is self.selected_part]
        if not shapes:
            # fall back to the part's world-space tx/ty projected onto canvas
            return self._v2c(self.selected_part.tx, self.selected_part.ty,
                             self._ev, self._ew, self._eh)
        mn_x = mn_y = float("inf"); mx_x = mx_y = float("-inf")
        for fs in shapes:
            for cx, cy in self._corners_c(fs, self._ev, self._ew, self._eh):
                mn_x = min(mn_x, cx); mn_y = min(mn_y, cy)
                mx_x = max(mx_x, cx); mx_y = max(mx_y, cy)
        if mn_x >= mx_x:
            return self._v2c(self.selected_part.tx, self.selected_part.ty,
                             self._ev, self._ew, self._eh)
        return ((mn_x + mx_x) / 2, (mn_y + mx_y) / 2)

    def _collect_all_deps(self, sprite_id: int, depth: int = 0,
                          visited: Optional[Set[int]] = None) -> Set[int]:
        """Recursively collect all char IDs (shapes + nested sprites) for a sprite."""
        if visited is None:
            visited = set()
        if sprite_id in visited or depth > 10:
            return visited
        visited.add(sprite_id)
        for p in self.sprite_parts.get(sprite_id, []):
            if p.char_id in self.shape_tags:
                visited.add(p.char_id)
            elif p.char_id in self.sprite_tags:
                self._collect_all_deps(p.char_id, depth + 1, visited)
        return visited

    def _is_pixel_transparent_at(self, canvas_id: int, cx: int, cy: int) -> bool:
        """Check alpha at (cx,cy) for a specific canvas item ID.
        Returns True if transparent (alpha < 30), False if opaque or no image."""
        for fs in self.edit_shapes:
            if fs.canvas_id == canvas_id:
                if fs.canvas_img is None:
                    return False  # placeholder → treat opaque
                img = fs.canvas_img
                px = cx - fs.canvas_img_x0
                py = cy - fs.canvas_img_y0
                if 0 <= px < img.width and 0 <= py < img.height:
                    try:
                        if img.mode == "RGBA":
                            return img.getpixel((px, py))[3] < 30
                        elif img.mode == "LA":
                            return img.getpixel((px, py))[1] < 30
                        else:
                            return False  # no alpha → opaque
                    except Exception:
                        return False
                return False  # outside image bounds → opaque
        return False  # canvas_id not found → opaque

    # Keep old name as alias for compat
    def _is_pixel_transparent(self, part, cx, cy):
        for fs in self.edit_shapes:
            if fs.direct_owner is part:
                return self._is_pixel_transparent_at(fs.canvas_id, cx, cy)
        return False


    def _hit_ref(self, mx, my):
        """Hit-test reference canvas with per-pixel transparency support."""
        for fs in reversed(self.ref_shapes):
            pts = self._corners_c(fs, self._rv, self._rw, self._rh)
            if not pts or not _point_in_quad(mx, my, pts):
                continue
            # Check transparency via canvas_img
            if fs.canvas_img is None:
                return fs  # placeholder → treat as hit
            img = fs.canvas_img
            px = mx - fs.canvas_img_x0
            py = my - fs.canvas_img_y0
            if 0 <= px < img.width and 0 <= py < img.height:
                try:
                    if img.mode == "RGBA":
                        alpha = img.getpixel((px, py))[3]
                    elif img.mode == "LA":
                        alpha = img.getpixel((px, py))[1]
                    else:
                        alpha = 255
                    if alpha >= 30:
                        return fs  # Opaque pixel → this is our hit
                    # else transparent → keep looking below
                except Exception:
                    return fs
            else:
                # Outside image bounds but inside quad → hit
                return fs
        return None

    def _hit_edit_part(self, mx, my) -> Optional[PartData]:
        """Find which PartData is under (mx, my) in edit canvas."""
        items = self.edit_canvas.find_overlapping(mx-3, my-3, mx+3, my+3)
        for iid in reversed(items):
            for t in self.edit_canvas.gettags(iid):
                if t.startswith("own_"):
                    oid = int(t[4:])
                    for p in self.sprite_parts.get(self.edit_sprite_id, []):
                        if id(p) == oid:
                            return p
        return None

    # ── Pan ───────────────────────────────────────────────────────────
    def _pan_start(self, ev, tag):
        self._pan = True
        self._pan_sx, self._pan_sy = ev.x, ev.y
        view = self._rv if tag == "ref" else self._ev
        self._pan_orig = [view[1], view[2]]
        self._pan_view = view; self._pan_tag = tag
        self._pan_last_dx = 0; self._pan_last_dy = 0
        cur = _MODE_CURSORS.get("pan", "fleur")
        cv = self.ref_canvas if tag == "ref" else self.edit_canvas
        try:
            cv.configure(cursor=cur)
        except Exception:
            cv.configure(cursor="fleur")

    def _pan_move(self, ev, tag):
        if not self._pan or self._pan_view is None: return
        v = self._pan_view
        dx = ev.x - self._pan_sx; dy = ev.y - self._pan_sy
        v[1] = self._pan_orig[0] - dx / v[0]
        v[2] = self._pan_orig[1] - dy / v[0]
        cv = self.ref_canvas if self._pan_tag == "ref" else self.edit_canvas
        mv_dx = dx - self._pan_last_dx; mv_dy = dy - self._pan_last_dy
        cv.move("all", mv_dx, mv_dy)
        self._pan_last_dx = dx; self._pan_last_dy = dy

    def _pan_end(self, ev, tag):
        self._pan = False; self._pan_view = None
        cv = self.ref_canvas if tag == "ref" else self.edit_canvas
        cur = _MODE_CURSORS.get(self.mode, "crosshair")
        try:
            cv.configure(cursor=cur)
        except Exception:
            cv.configure(cursor="crosshair")
        if tag == "ref": self._redraw_ref()
        else: self._redraw_edit()

    def _on_scroll(self, ev, tag):
        view = self._rv if tag == "ref" else self._ev
        cw = self._rw if tag == "ref" else self._ew
        ch = self._rh if tag == "ref" else self._eh
        vx, vy = self._c2v(ev.x, ev.y, view, cw, ch)
        if ev.delta > 0: view[0] = min(MAX_ZOOM, view[0] * ZOOM_STEP)
        else: view[0] = max(MIN_ZOOM, view[0] / ZOOM_STEP)
        view[1] = vx - (ev.x - cw/2) / view[0]
        view[2] = vy - (ev.y - ch/2) / view[0]
        
        cv = self.ref_canvas if tag == "ref" else self.edit_canvas
        scroll_id = getattr(self, f"_{tag}_scroll_id", None)
        if scroll_id:
            cv.after_cancel(scroll_id)
            
        def do_redraw():
            if tag == "ref": self._redraw_ref()
            else: self._redraw_edit()
            
        setattr(self, f"_{tag}_scroll_id", cv.after(15, do_redraw))

    def _on_motion(self, ev, tag):
        view = self._rv if tag == "ref" else self._ev
        cw = self._rw if tag == "ref" else self._ew
        ch = self._rh if tag == "ref" else self._eh
        vx, vy = self._c2v(ev.x, ev.y, view, cw, ch)
        if self.coords_var:
            self.coords_var.set(f"X:{vx:.1f}  Y:{vy:.1f}")

        # Tag tooltip — show what's under cursor
        if tag == "ref":
            hit = self._hit_ref(ev.x, ev.y)
            if hit and hit.ref_owner:
                ro = hit.ref_owner
                tp = "Sprite" if ro.is_sprite else "Shape"
                self.hover_var.set(f"Define{tp}({ro.char_id}) — {ro.name}")
            else:
                self.hover_var.set("")
        elif tag == "edit":
            hp = self._hit_edit_part(ev.x, ev.y)
            if hp:
                tp = "Sprite" if hp.is_sprite else "Shape"
                self.hover_var.set(f"Define{tp}({hp.char_id}) — {hp.name}")
            else:
                self.hover_var.set("")

        # Cursor feedback
        if self._space_held or self._pan: return
        cv = self.ref_canvas if tag == "ref" else self.edit_canvas
        if tag == "edit" and self.selected_part:
            if self.mode == MODE_SCALE and self._sel_bbox:
                h = self._hit_handle(ev.x, ev.y)
                if h:
                    curs = {"tl":"size_nw_se","tr":"size_ne_sw",
                            "bl":"size_ne_sw","br":"size_nw_se",
                            "tm":"sb_v_double_arrow","bm":"sb_v_double_arrow",
                            "ml":"sb_h_double_arrow","mr":"sb_h_double_arrow"}
                    cv.configure(cursor=curs.get(h, "crosshair")); return
            elif self.mode == MODE_MOVE:
                ax = self._hit_axis(ev.x, ev.y)
                if ax == "x":
                    cv.configure(cursor="sb_h_double_arrow"); return
                elif ax == "y":
                    cv.configure(cursor="sb_v_double_arrow"); return
            elif self.mode == MODE_SKEW and self._sel_bbox:
                sh = self._hit_skew(ev.x, ev.y)
                if sh:
                    cv.configure(cursor="sb_h_double_arrow" if sh.startswith("h")
                                 else "sb_v_double_arrow"); return
            elif self.mode == MODE_ROTATE and self._sel_center_c:
                cx_c, cy_c = self._sel_center_c
                pv_cx = cx_c + self._pivot_offset[0] * self._ev[0]
                pv_cy = cy_c + self._pivot_offset[1] * self._ev[0]
                if abs(ev.x-pv_cx) <= 10 and abs(ev.y-pv_cy) <= 10:
                    cv.configure(cursor="fleur"); return
        cur = _MODE_CURSORS.get(self.mode, "crosshair")
        try:
            cv.configure(cursor=cur)
        except Exception:
            cv.configure(cursor="crosshair")

    # ═══════════════════════════════════════════════════════════════════
    #  TREE / SELECTOR EVENTS
    # ═══════════════════════════════════════════════════════════════════
    def _on_ref_tree_select(self, _):
        sel = self.tree.selection()
        if not sel: return
        entry = self._part_tree_map.get(sel[0])
        if not entry: return
        part, sid = entry
        if part.is_sprite:
            self._open_in_editor(part.char_id)

    def _on_edit_tree_click(self, event):
        """Maneja clics directos para el modo de selección (Select Mode)."""
        select_mode = self._var_select_mode and self._var_select_mode.get()
        if not select_mode:
            return  # Comportamiento normal

        iid = self.edit_tree.identify_row(event.y)
        if not iid: return
        
        # Solo alternar si el clic fue exactamente en el icono del checkbox ("image")
        element = self.edit_tree.identify_element(event.x, event.y)
        if element != "image":
            return  # Ignorar si hace clic en el texto o flecha de expansión

        tags = self.edit_tree.item(iid, "tags")
        if "part_node" in tags:
            return "break"  # Las partes no tienen checkbox, ignorar clics

        # Alternar la selección del CHECKBOX
        is_cat = any(t.startswith("cat_") or t.startswith("subcat_") for t in tags)

        def _collect_sprite_tids(parent_tid):
            result = []
            for child in self.edit_tree.get_children(parent_tid):
                child_tags = self.edit_tree.item(child, "tags")
                if "sprite_node" in child_tags:
                    result.append(child)
                elif any(t.startswith("subcat_") or t.startswith("cat_") for t in child_tags):
                    result.extend(_collect_sprite_tids(child))
            return result

        if iid in self.checked_tids:
            # Desmarcar nodo y sus hijos (si es categoría)
            self.checked_tids.remove(iid)
            if is_cat:
                for stid in _collect_sprite_tids(iid):
                    if stid in self.checked_tids:
                        self.checked_tids.remove(stid)
        else:
            # Marcar nodo y sus hijos
            self.checked_tids.add(iid)
            if is_cat:
                for stid in _collect_sprite_tids(iid):
                    self.checked_tids.add(stid)
        
        self._update_tree_checkboxes()

        # Update selected parts for Select Mode so batch operations work
        new_parts = []
        primary_part = None
        primary_sid  = -1

        for tid in self.checked_tids:
            tag = self.edit_tree.item(tid, "tags")
            if "sprite_node" in tag:
                sid = self._tid_to_sid.get(tid, -1)
                if sid == -1:
                    continue
                if primary_sid == -1:
                    primary_sid = sid
                for child_tid in self.edit_tree.get_children(tid):
                    entry = self._part_tree_map.get(child_tid)
                    if entry:
                        p, s = entry
                        new_parts.append(p)
                        if primary_part is None:
                            primary_part = p

        self.selected_parts = new_parts
        self.selected_part  = primary_part
        # No forzamos cambio de vista en Select Mode al marcar casillas, solo recopilamos para batch
        self.selected_sprite_id = primary_sid if primary_part else -1
        self._pivot_offset = (0.0, 0.0)
        self._update_props()
        self._redraw_edit()

        return "break"  # Bloquear evento original para que no altere self.edit_tree.selection()

    def _on_edit_tree_select(self, _):
        if self._tree_lock:
            return  # fired by _highlight_edit_tree or _on_edit_tree_click, ignore
        sel = self.edit_tree.selection()
        if not sel: return

        select_mode = self._var_select_mode and self._var_select_mode.get()
        if select_mode:
            # En Select Mode, una selección normal solo abre el sprite en el editor, 
            # pero NO altera las partes seleccionadas (self.selected_parts) del batch.
            for tid in sel:
                tags = self.edit_tree.item(tid, "tags")
                if "sprite_node" in tags:
                    sid = self._tid_to_sid.get(tid, -1)
                    if sid != -1 and sid != self.edit_sprite_id:
                        self._open_in_editor(sid)
                        self._fit_view("edit")
                        break
            return

        # Normal mode: process selection to open sprites / collect parts
        new_parts: list = []
        primary_part = None
        primary_sid  = -1

        for tid in sel:
            tags = self.edit_tree.item(tid, "tags")
            is_cat = any(t.startswith("cat_") or t.startswith("subcat_") for t in tags)
            if is_cat:
                continue

            if "sprite_node" in tags:
                sid = self._tid_to_sid.get(tid, -1)
                if sid == -1:
                    continue
                # Only open the FIRST sprite in the editor
                if primary_sid == -1:
                    if sid != self.edit_sprite_id:
                        self._open_in_editor(sid)
                        self._fit_view("edit")
                    primary_sid = sid
                # Collect ALL its part-children from the tree
                for child_tid in self.edit_tree.get_children(tid):
                    entry = self._part_tree_map.get(child_tid)
                    if entry:
                        p, s = entry
                        new_parts.append(p)
                        if primary_part is None:
                            primary_part = p

            elif "part_node" in tags:
                entry = self._part_tree_map.get(tid)
                if not entry:
                    continue
                part, sid = entry
                new_parts.append(part)
                if primary_part is None:
                    primary_part = part
                    if sid != self.edit_sprite_id:
                        if primary_sid == -1:
                            self._open_in_editor(sid)
                            self._fit_view("edit")
                    primary_sid = sid

        # Apply selection
        self.selected_parts = new_parts
        self.selected_part  = primary_part
        self.selected_sprite_id = primary_sid if primary_part else -1
        self._pivot_offset = (0.0, 0.0)
        self._update_props()
        self._redraw_edit()



    def _highlight_edit_tree(self):
        """Highlight in the tree the row corresponding to selected_part."""
        if not self.selected_part:
            try:
                self._tree_lock = True
                self.edit_tree.selection_set(())
            except Exception:
                pass
            finally:
                self._tree_lock = False
            return
        tids_to_sel = []
        if self.selected_parts:
            for p in self.selected_parts:
                if hasattr(p, '_tree_id') and p._tree_id:
                    try:
                        if self.edit_tree.exists(p._tree_id):
                            tids_to_sel.append(p._tree_id)
                    except Exception:
                        pass
        else:
            tid = self.selected_part._tree_id
            if tid and self.edit_tree.exists(tid):
                tids_to_sel = [tid]
        if tids_to_sel:
            try:
                self._tree_lock = True
                self.edit_tree.selection_set(tids_to_sel)
                self.edit_tree.see(tids_to_sel[0])
            except Exception:
                pass
            finally:
                self._tree_lock = False
        self._update_tree_checkboxes()

    def _update_tree_checkboxes(self):
        """Update checkbox icons based on selection."""
        chk_on = getattr(self, "_ico_chk_on", None)
        chk_off = getattr(self, "_ico_chk_off", None)
        if not chk_on or not chk_off: return
        sel = set(self.edit_tree.selection())
        for tid, _ in self._all_edit_tree_ids:
            tags = self.edit_tree.item(tid, "tags")
            if "sprite_node" in tags or "part_node" in tags:
                try:
                    img = chk_on if tid in sel else chk_off
                    self.edit_tree.item(tid, image=img)
                except Exception: pass

    def _on_edit_tree_double(self, event):
        """Doble click en nodo de árbol: si es sprite, abrirlo en editor."""
        iid = self.edit_tree.identify_row(event.y)
        if not iid: return
        tags = self.edit_tree.item(iid, "tags")
        if "sprite_node" in tags:
            vals = self.edit_tree.item(iid, "values")
            if vals:
                try:
                    self._open_in_editor(int(vals[0]))
                    self._fit_view("edit")
                except (ValueError, TypeError):
                    pass

    def _on_edit_tree_rclick(self, event):
        """Menú contextual en el árbol editor (click derecho)."""
        iid = self.edit_tree.identify_row(event.y)
        if not iid: return
        self.edit_tree.selection_set(iid)
        tags = self.edit_tree.item(iid, "tags")
        entry = self._part_tree_map.get(iid)

        menu = tk.Menu(self.parent, tearoff=0, bg="#1A1A1A", fg=FGT,
                       activebackground=AC, activeforeground="#000",
                       relief="flat")
        if any(t in tags for t in ("cat_head","cat_upper","cat_lower",
                                   "cat_legs","cat_misc","subcat_node")):
            is_open = self.edit_tree.item(iid, "open")
            menu.add_command(label="Collapse" if is_open else "Expand",
                             command=lambda i=iid: self.edit_tree.item(
                                 i, open=not self.edit_tree.item(i, "open")))
        elif "sprite_node" in tags:
            vals = self.edit_tree.item(iid, "values")
            sid  = int(vals[0]) if vals and vals[0] else -1
            menu.add_command(label=f"▶  Open in Editor  (ID {sid})",
                             command=lambda s=sid: (
                                 self._open_in_editor(s), self._fit_view("edit")))
            menu.add_separator()
            menu.add_command(label="Expand / Collapse",
                             command=lambda i=iid: self.edit_tree.item(
                                 i, open=not self.edit_tree.item(i, "open")))
        elif "part_node" in tags and entry:
            part, sid = entry
            kind = "Sprite" if part.is_sprite else "Shape"
            menu.add_command(label="Select Part",
                             command=lambda: self._on_edit_tree_select(None))
            menu.add_separator()
            menu.add_command(
                label=f"Copy {kind}({part.char_id}) to Sprite…",
                command=lambda p=part, s=sid: self._ctx_copy_to_sprite(p, s))
            menu.add_separator()
            menu.add_command(label="Copy Transform  (Ctrl+C)",
                             command=lambda p=part: self._ctx_copy_transform(p))
            menu.add_command(label="Paste Transform  (Ctrl+V)",
                             command=self._paste_all_props)
            menu.add_separator()
            menu.add_command(label=f"Open parent Sprite({sid})",
                             command=lambda s=sid: (
                                 self._open_in_editor(s), self._fit_view("edit")))
        if menu.index("end") is not None:
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

    def _ctx_copy_transform(self, part):
        """Copia sólo la transformación de 'part' al clipboard interno."""
        prev = self.selected_part
        self.selected_part = part
        self._copy_all_props()
        self.selected_part = prev

    def _ctx_copy_to_sprite(self, part, src_sprite_id: int):
        """Abre un diálogo para elegir sprite destino y copia el PlaceObject2."""
        import copy as _copy

        choices = [(sid, f"Sprite({sid})" + (f" - {self._get_export_name(sid)}"
                          if self._get_export_name(sid) else ""))
                   for sid in sorted(self.sprite_tags.keys())
                   if sid != src_sprite_id]
        if not choices:
            return

        dlg = ctk.CTkToplevel(self.parent)
        dlg.title("Copy to Sprite — Choose destination")
        dlg.geometry("420x460")
        dlg.configure(fg_color=BGD)
        dlg.transient(self.parent); dlg.grab_set()
        dlg.after(60, dlg.focus_force)

        kind = "Sprite" if part.is_sprite else "Shape"
        ctk.CTkLabel(dlg,
                     text=f"Copy  {kind}({part.char_id})\n"
                          f"from  Sprite({src_sprite_id})  →  select dest:",
                     font=("Segoe UI", 12), text_color=FGT,
                     justify="left").pack(padx=16, pady=(12, 4), anchor="w")

        sv = tk.StringVar()
        ctk.CTkEntry(dlg, textvariable=sv, placeholder_text="Filter…",
                     height=26, fg_color=BGI, border_color="#333",
                     text_color=FGT).pack(fill="x", padx=12, pady=(4, 2))

        lb_f = ctk.CTkFrame(dlg, fg_color=BGI, corner_radius=6)
        lb_f.pack(fill="both", expand=True, padx=12, pady=4)
        lb = tk.Listbox(lb_f, bg="#111", fg=FGT, selectbackground=AC,
                        selectforeground="#000", font=("Segoe UI", 11),
                        relief="flat", activestyle="none", borderwidth=0)
        vsb = ctk.CTkScrollbar(lb_f, orientation="vertical", command=lb.yview)
        lb.configure(yscrollcommand=vsb.set)
        lb.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        _visible = []
        def _fill(t=""):
            lb.delete(0, "end"); _visible.clear()
            for sid, label in choices:
                if not t or t.lower() in label.lower():
                    lb.insert("end", label)
                    _visible.append((sid, label))
        sv.trace_add("write", lambda *_: _fill(sv.get()))
        _fill()

        def _do_copy():
            sel = lb.curselection()
            if not sel: return
            target_sid, _ = _visible[sel[0]]
            new_part = _copy.copy(part)
            new_part._tree_id = None
            self.sprite_parts.setdefault(target_sid, []).append(new_part)
            dlg.destroy()
            self._populate_edit_tree()
            self._flatten_all()
            self._status(f"Copied {kind}({part.char_id}) → Sprite({target_sid})")

        bf = ctk.CTkFrame(dlg, fg_color="transparent", height=44)
        bf.pack(fill="x", padx=12, pady=(2, 10))
        ctk.CTkButton(bf, text="Copy Here", fg_color=AC, hover_color=ACD,
                      text_color="#000", height=32, corner_radius=6,
                      font=("Segoe UI", 12, "bold"),
                      command=_do_copy).pack(side="right", padx=4)
        ctk.CTkButton(bf, text="Cancel", fg_color="#333", hover_color="#444",
                      text_color=FGT, height=32, corner_radius=6,
                      command=dlg.destroy).pack(side="right", padx=4)
        lb.bind("<Double-Button-1>", lambda e: _do_copy())

    def _open_in_editor(self, sprite_id):
        if sprite_id not in self.sprite_tags: return
        prev_edit_id = self.edit_sprite_id
        self.edit_sprite_id = sprite_id
        self.selected_part = None
        self.selected_parts = []   # <-- clear multi-selection
        self.selected_sprite_id = -1
        self._pivot_offset = (0.0, 0.0)
        # Actualizar árbol: colapsar anterior, expandir nuevo
        if hasattr(self, '_sprite_tid_map') and self._sprite_tid_map:
            if prev_edit_id in self._sprite_tid_map:
                try:
                    self.edit_tree.item(self._sprite_tid_map[prev_edit_id], open=False)
                except Exception:
                    pass
            if sprite_id in self._sprite_tid_map:
                stid = self._sprite_tid_map[sprite_id]
                try:
                    self.edit_tree.item(stid, open=True)
                    self.edit_tree.see(stid)
                except Exception:
                    pass
        else:
            self._populate_edit_tree()
        self._update_canvas_titles()
        self._flatten_edit(); self._redraw_edit(); self._redraw_ref()
        self._update_props()
        self._status(f"Editing {self._sprite_display_name(sprite_id)}")

    def _on_ref_selected(self, sel):
        sid = self._sprite_id_map_ref.get(sel)
        if sid is None: return
        self.ref_sprite_id = sid
        self._populate_ref_tree(); self._update_canvas_titles()
        self._flatten_ref(); self._redraw_ref(); self._fit_view("ref")

    def _on_edit_selected(self, sel):
        """Mantener compatibilidad: usar el árbol jerárquico en vez del ComboBox."""
        sid = self._sprite_id_map_edit.get(sel) if sel else None
        if sid is None: return
        self._open_in_editor(sid); self._fit_view("edit")

    # ═══════════════════════════════════════════════════════════════════
    #  PROPERTIES
    # ═══════════════════════════════════════════════════════════════════
    def _update_props(self):
        if self.selected_part is None:
            if self.prop_name_label:
                self.prop_name_label.configure(text="(no selection)")
            for e in self.prop_entries.values():
                e.delete(0, "end"); e.configure(state="disabled")
            for sl in self.prop_sliders.values():
                sl.set(0)
            return
        p = self.selected_part
        if self.prop_name_label:
            tp = "Sprite" if p.is_sprite else "Shape"
            self.prop_name_label.configure(
                text=f"Define{tp}({p.char_id}) — {p.name}  D:{p.depth}")
        for e in self.prop_entries.values():
            e.configure(state="normal")

        sx_m = math.sqrt(p.sx**2 + p.r0**2)
        sy_m = math.sqrt(p.r1**2 + p.sy**2)
        det = p.sx*p.sy - p.r0*p.r1
        if det < 0: sy_m = -sy_m
        rot = math.degrees(math.atan2(p.r0, p.sx))
        skx = math.degrees(math.atan2(p.r1, p.sy))
        sky = math.degrees(math.atan2(p.r0, p.sx))

        vals = {
            "tx": f"{p.tx:.2f}", "ty": f"{p.ty:.2f}",
            "depth": f"{p.depth}",
            "scale_x": f"{sx_m:.4f}", "scale_y": f"{sy_m:.4f}",
            "rotation": f"{rot:.2f}",
            "skew_x": f"{skx:.2f}", "skew_y": f"{sky:.2f}",
            "raw_sx": f"{p.sx:.6f}", "raw_sy": f"{p.sy:.6f}",
            "raw_r0": f"{p.r0:.6f}", "raw_r1": f"{p.r1:.6f}",
            "raw_tx": f"{p.tx*TWIP:.1f}", "raw_ty": f"{p.ty*TWIP:.1f}",
        }
        for k, v in vals.items():
            e = self.prop_entries.get(k)
            if e:
                e.delete(0, "end"); e.insert(0, v)
            sl = self.prop_sliders.get(k)
            if sl:
                try: sl.set(float(v))
                except Exception: pass

    def _on_slider(self, key, value):
        if not self.selected_part: return
        p = self.selected_part; old = self._st(p); val = float(value)
        self._apply_prop(key, val)
        new = self._st(p)
        if old != new:
            self._push_undo([(p, old, new)])
        self._flatten_all()
        # Always refresh all entries/sliders — important when uniform scale is on
        self._update_props()

    def _on_prop(self, key):
        if not self.selected_part: return
        e = self.prop_entries.get(key)
        if not e: return
        try: val = float(e.get())
        except ValueError:
            self._update_props(); return
        p = self.selected_part; old = self._st(p)
        self._apply_prop(key, val)
        new = self._st(p)
        if old != new:
            self._push_undo([(p, old, new)])
        self._flatten_all(); self._update_props()

    def _apply_prop(self, key, val):
        p = self.selected_part
        snap = (hasattr(self, "_var_snap_pixel") and self._var_snap_pixel
                and self._var_snap_pixel.get())
        lock = (self._var_uniform_scale.get()
                if self._var_uniform_scale else self._uniform_scale)
        if key == "tx": p.tx = round(val) if snap else val
        elif key == "ty": p.ty = round(val) if snap else val
        elif key == "depth": p.depth = int(val)
        elif key == "scale_x":
            self._set_sx(p, val)
            if lock:
                self._set_sy(p, val)
        elif key == "scale_y":
            self._set_sy(p, val)
            if lock:
                self._set_sx(p, val)
        elif key == "rotation": self._set_rot(p, val)
        elif key == "skew_x": self._set_skewx(p, val)
        elif key == "skew_y": self._set_skewy(p, val)
        elif key == "raw_sx": p.sx = val
        elif key == "raw_sy": p.sy = val
        elif key == "raw_r0": p.r0 = val
        elif key == "raw_r1": p.r1 = val
        elif key == "raw_tx": p.tx = val / TWIP
        elif key == "raw_ty": p.ty = val / TWIP

    def _prop_increment(self, key, direction):
        """direction is +1 or -1."""
        if not self.selected_part: return
        step = self._step
        # Scale properties: use step / 10
        if key.startswith("scale"):
            delta = direction * step * 0.1
        elif key in ("tx", "ty"):
            delta = direction * step
        elif key == "depth":
            delta = direction * max(1, round(step))
        else:  # rotation, skew
            delta = direction * step
        e = self.prop_entries.get(key)
        if not e: return
        try: cur = float(e.get())
        except ValueError: cur = 0.0
        e.delete(0, "end")
        if key == "depth":
            e.insert(0, f"{int(cur + delta)}")
        else:
            e.insert(0, f"{cur + delta:.4f}")
        self._on_prop(key)

    def _set_sx(self, p, v):
        th = math.atan2(p.r0, p.sx)
        sy_m = math.sqrt(p.r1**2 + p.sy**2)
        d = p.sx*p.sy - p.r0*p.r1
        if d < 0: sy_m = -sy_m
        c, s = math.cos(th), math.sin(th)
        p.sx = v*c; p.r0 = v*s; p.r1 = -sy_m*s; p.sy = sy_m*c

    def _set_sy(self, p, v):
        th = math.atan2(p.r0, p.sx)
        sx_m = math.sqrt(p.sx**2 + p.r0**2)
        c, s = math.cos(th), math.sin(th)
        p.sx = sx_m*c; p.r0 = sx_m*s; p.r1 = -v*s; p.sy = v*c

    def _set_rot(self, p, deg):
        sx_m = math.sqrt(p.sx**2 + p.r0**2)
        sy_m = math.sqrt(p.r1**2 + p.sy**2)
        d = p.sx*p.sy - p.r0*p.r1
        if d < 0: sy_m = -sy_m
        th = math.radians(deg); c, s = math.cos(th), math.sin(th)
        p.sx = sx_m*c; p.r0 = sx_m*s; p.r1 = -sy_m*s; p.sy = sy_m*c

    def _set_skewx(self, p, deg):
        deg = max(-89.9, min(89.9, deg))
        sy_m = math.sqrt(p.r1**2 + p.sy**2)
        d = p.sx*p.sy - p.r0*p.r1
        if d < 0: sy_m = -sy_m
        th = math.radians(deg)
        p.r1 = sy_m*math.sin(th); p.sy = sy_m*math.cos(th)

    def _set_skewy(self, p, deg):
        deg = max(-89.9, min(89.9, deg))
        sx_m = math.sqrt(p.sx**2 + p.r0**2)
        th = math.radians(deg)
        p.r0 = sx_m*math.sin(th); p.sx = sx_m*math.cos(th)

    # ═══════════════════════════════════════════════════════════════════
    #  COPY / PASTE
    # ═══════════════════════════════════════════════════════════════════
    def _copy_all_props(self):
        # Auto-seleccionar la parte actual si no hay selección
        if not self.selected_part:
            if (self.edit_sprite_id >= 0
                    and self.edit_sprite_id in self.sprite_parts
                    and self.sprite_parts[self.edit_sprite_id]):
                self.selected_part = self.sprite_parts[self.edit_sprite_id][0]
                self.selected_parts = [self.selected_part]
                self.selected_sprite_id = self.edit_sprite_id
                self._update_props()
                self._redraw_edit()
            else:
                return
        self._matrix_clipboard = self._st(self.selected_part)
        if self.btn_paste:
            self.btn_paste.configure(state="normal")
        self._feedback("Copied!", AC)

    def _paste_all_props(self):
        if not self.selected_part or not self._matrix_clipboard: return
        old = self._st(self.selected_part)
        self._apply_st(self.selected_part, dict(self._matrix_clipboard))
        new = self._st(self.selected_part)
        if old != new:
            self._push_undo([(self.selected_part, old, new)])
        self._flatten_all(); self._update_props()
        self._feedback("Pasted!", GREEN)

    def _copy_matrix_text(self):
        if not self.selected_part: return
        p = self.selected_part
        txt = (f"MATRIX(a={p.sx:.6f}, b={p.r1:.6f}, c={p.r0:.6f}, "
               f"d={p.sy:.6f}, e={p.tx*TWIP:.0f}, f={p.ty*TWIP:.0f})")
        self.parent.clipboard_clear(); self.parent.clipboard_append(txt)
        self._feedback("Matrix → Clipboard", AC)

    # ═══════════════════════════════════════════════════════════════════
    #  UNDO / REDO
    # ═══════════════════════════════════════════════════════════════════
    def _st(self, p):
        return dict(sx=p.sx, sy=p.sy, r0=p.r0, r1=p.r1, tx=p.tx, ty=p.ty, depth=p.depth)

    def _apply_st(self, p, s):
        p.sx = s["sx"]; p.sy = s["sy"]
        p.r0 = s["r0"]; p.r1 = s["r1"]
        p.tx = s["tx"]; p.ty = s["ty"]
        if "depth" in s:
            p.depth = s["depth"]

    def _push_undo(self, changes):
        self._undo.append(changes); self._redo.clear()
        self._update_undo_btns()

    def _do_undo(self):
        if not self._undo: return
        changes = self._undo.pop(); self._redo.append(changes)
        for part, old, new in changes:
            self._apply_st(part, old)
        if changes:
            self.selected_parts = [c[0] for c in changes]
            self.selected_part  = changes[0][0]
        self._flatten_all(); self._update_props()
        self._highlight_edit_tree(); self._update_undo_btns()

    def _do_redo(self):
        if not self._redo: return
        changes = self._redo.pop(); self._undo.append(changes)
        for part, old, new in changes:
            self._apply_st(part, new)
        if changes:
            self.selected_parts = [c[0] for c in changes]
            self.selected_part  = changes[0][0]
        self._flatten_all(); self._update_props()
        self._highlight_edit_tree(); self._update_undo_btns()

    def _update_undo_btns(self):
        if self.btn_undo:
            self.btn_undo.configure(state="normal" if self._undo else "disabled")
        if self.btn_redo:
            self.btn_redo.configure(state="normal" if self._redo else "disabled")

    # ═══════════════════════════════════════════════════════════════════
    #  APPLY / CANCEL / SAVE
    # ═══════════════════════════════════════════════════════════════════
    def _take_snapshot(self):
        self._snapshot.clear()
        for sid, parts in self.sprite_parts.items():
            for p in parts:
                self._snapshot.append((p, self._st(p)))

    def _apply_changes(self):
        self._take_snapshot()
        self._undo.clear(); self._redo.clear(); self._update_undo_btns()
        self._feedback("Applied!", GREEN)
        threading.Thread(target=self._apply_thread, daemon=True).start()

    def _apply_thread(self):
        _ajvm()
        for sid, parts in self.sprite_parts.items():
            for p in parts:
                self._write_mat(p)
        self._ui(lambda: self._status("Changes applied to SWF in memory"))

    def _cancel_changes(self):
        if not self._snapshot: return
        for part, state in self._snapshot:
            self._apply_st(part, state)
        self._undo.clear(); self._redo.clear(); self._update_undo_btns()
        self._flatten_all(); self._update_props()
        self._feedback("Reverted!", RED)

    def _save_swf_dialog(self):
        if not self.swf: return
        path = filedialog.asksaveasfilename(
            title="Save SWF", defaultextension=".swf",
            filetypes=[("SWF", "*.swf")],
            initialfile=os.path.basename(self.swf_path))
        if not path: return
        self._status("Saving SWF ...")
        threading.Thread(target=self._save_thread, args=(path,), daemon=True).start()

    def _save_thread(self, path):
        try:
            _ajvm()
            for sid, parts in self.sprite_parts.items():
                for p in parts:
                    self._write_mat(p)
            _Methods.save_swf_to(self.swf, path)
            self._take_snapshot()
            self._ui(lambda: self._feedback("Saved!", GREEN))
            self._ui(lambda: self._status(f"Saved: {os.path.basename(path)}"))
            self._ui(lambda: messagebox.showinfo("Success",
                                                  f"SWF saved to:\n{path}"))
        except Exception as exc:
            traceback.print_exc()
            self._ui(lambda: messagebox.showerror("Error", f"Save failed:\n{exc}"))

    def _write_mat(self, part):
        try: 
            part.place_tag.depth = int(part.depth)
            part.place_tag.setModified(True)
        except Exception: pass
        
        m = part.place_tag.matrix
        if m is None: return
        m.scaleX = int(round(part.sx * FP))
        m.scaleY = int(round(part.sy * FP))
        m.rotateSkew0 = int(round(part.r0 * FP))
        m.rotateSkew1 = int(round(part.r1 * FP))
        m.translateX = int(round(part.tx * TWIP))
        m.translateY = int(round(part.ty * TWIP))
        m.hasScale = True
        m.hasRotate = (part.r0 != 0.0 or part.r1 != 0.0)

    # ═══════════════════════════════════════════════════════════════════
    #  PART ACTIONS
    # ═══════════════════════════════════════════════════════════════════
    def _deselect_all(self):
        """ESC: clear all selections."""
        self._tree_lock = True
        try:
            self.edit_tree.selection_set(())
        except Exception:
            pass
        finally:
            self._tree_lock = False
        self.selected_part  = None
        self.selected_parts = []
        self._pivot_offset  = (0.0, 0.0)
        self._update_props(); self._redraw_edit()

    def _nudge(self, dx, dy):
        if not self.selected_part: return
        snap = (hasattr(self, "_var_snap_pixel") and self._var_snap_pixel
                and self._var_snap_pixel.get())
        # Always operate on all selected_parts; fallback to single part
        targets = self.selected_parts if self.selected_parts else [self.selected_part]
        changes = []
        for p in targets:
            old = self._st(p)
            if snap:
                p.tx = round(p.tx + dx * self._step)
                p.ty = round(p.ty + dy * self._step)
            else:
                p.tx += dx * self._step
                p.ty += dy * self._step
            changes.append((p, old, self._st(p)))
        self._push_undo(changes)
        self._flatten_all(); self._update_props()

    def _reset_transform(self):
        if not self.selected_part: return
        old = self._st(self.selected_part)
        p = self.selected_part
        p.sx = p.sy = 1.0; p.r0 = p.r1 = 0.0; p.tx = p.ty = 0.0
        self._push_undo([(p, old, self._st(p))])
        self._flatten_all(); self._update_props()

    def _mirror(self, axis):
        if not self.selected_part: return
        old = self._st(self.selected_part)
        p = self.selected_part
        if axis == "h":
            p.sx = -p.sx; p.r0 = -p.r0
        else:
            p.sy = -p.sy; p.r1 = -p.r1
        self._push_undo([(p, old, self._st(p))])
        self._flatten_all(); self._update_props()

    def _toggle_vis(self):
        if not self.selected_part: return
        self.selected_part.visible = not self.selected_part.visible
        self._flatten_all()

    def _show_all(self):
        for sid, parts in self.sprite_parts.items():
            for p in parts:
                p.visible = True
        self._flatten_all()

    # ── Select Mode ──────────────────────────────────────────────────
    def _toggle_select_mode(self):
        """Toggle Select Mode for multi-selection checkboxes in tree."""
        current = self._var_select_mode.get()
        self._var_select_mode.set(not current)
        if self._var_select_mode.get():
            self._select_mode_btn.configure(
                text="Select Mode: ON", fg_color="#3B82F6",
                hover_color="#2563EB", text_color="#FFFFFF")
            # En Select Mode, los checkboxes son independientes de la seleccion,
            # pero inicializamos usando la seleccion actual si existe.
            sel = self.edit_tree.selection()
            self.checked_tids = set(sel)
        else:
            self._select_mode_btn.configure(
                text="Select Mode: OFF", fg_color="#2A2A2A",
                hover_color="#3A3A3A", text_color="#888888")
            # Clear all checkboxes and checked items state
            self.checked_tids.clear()
            chk_off = getattr(self, "_ico_chk_off", None)
            if chk_off:
                for tid, _ in self._all_edit_tree_ids:
                    try:
                        self.edit_tree.item(tid, image=chk_off)
                    except Exception:
                        pass
            
            # Rebuild selected parts from normal tree selection
            sel = self.edit_tree.selection()
            new_parts = []
            for tid in sel:
                for child_tid in self.edit_tree.get_children(tid):
                    entry = self._part_tree_map.get(child_tid)
                    if entry: new_parts.append(entry[0])
            self.selected_parts = new_parts
            self.selected_part = new_parts[0] if new_parts else None
            self._redraw_edit()
            
        self._update_tree_checkboxes()

    def _update_tree_checkboxes(self):
        """Update checkbox icons based on selection — only in Select Mode, only sprite/cat nodes."""
        chk_on  = getattr(self, "_ico_chk_on",  None)
        chk_off = getattr(self, "_ico_chk_off", None)
        if not chk_on or not chk_off: return

        select_mode = self._var_select_mode and self._var_select_mode.get()

        for tid, _ in self._all_edit_tree_ids:
            tags = self.edit_tree.item(tid, "tags")
            is_cat = any(t.startswith("cat_") or t.startswith("subcat_") for t in tags)
            is_sprite = "sprite_node" in tags
            is_part = "part_node" in tags

            if is_part:
                # Parts never show checkboxes — clear image
                try:
                    self.edit_tree.item(tid, image="")
                except Exception:
                    pass
                continue

            if not select_mode:
                try:
                    self.edit_tree.item(tid, image="")
                except Exception:
                    pass
                continue

            # In Select Mode: show checked/unchecked for sprites and cats
            if is_sprite or is_cat:
                sel = set(self.edit_tree.selection())
                # For categories: checked if any child sprite is selected
                if is_cat:
                    children = self.edit_tree.get_children(tid)
                    # Expand one level (subcats may nest sprites)
                    all_children = list(children)
                    for ch in children:
                        all_children.extend(self.edit_tree.get_children(ch))
                    is_checked = any(c in sel for c in all_children)
                else:
                    is_checked = tid in sel
                try:
                    img = chk_on if is_checked else chk_off
                    self.edit_tree.item(tid, image=img)
                except Exception:
                    pass

    # ── Reference Skin Overlay ────────────────────────────────────────
    _REF_SKIN_IMG_PATH = (
        RESOURCES / "assets" / "SkinEditorUI" /
        "Avatar.png"
    )

    def _on_ref_skin_toggle(self):
        """Called when the Reference Skin checkbox is toggled."""
        enabled = self._var_ref_skin.get()
        self._ref_skin_enabled = enabled
        if enabled:
            self._load_ref_skin_image()
        self._redraw_ref()

    def _load_ref_skin_image(self):
        """Load the reference skin PNG from disk (once)."""
        if self._ref_skin_img_pil is not None:
            return  # already loaded
        try:
            pref_path = self.prefs.get("ref_skin_img", "Avatar.png")
            path = Path(pref_path)
            if not path.is_absolute():
                path = RESOURCES / "assets" / "SkinEditorUI" / path
                
            if not path.exists():
                # Try glob fallback
                matches = list(RESOURCES.glob("assets/SkinEditorUI/Avatar*.png"))
                if matches:
                    path = matches[0]
                else:
                    print(f"[SE] Reference skin PNG not found at {path}.")
                    return
            self._ref_skin_img_pil = Image.open(str(path)).convert("RGBA")
            print(f"[SE] Loaded reference skin: {path.name}")
        except Exception as e:
            print(f"[SE] Error loading reference skin: {e}")

    def _toggle_ref_skin_panel(self):
        """Collapse/expand the reference skin controls panel."""
        self._ref_skin_panel_open = not self._ref_skin_panel_open
        if self._ref_skin_panel_open:
            self._ref_skin_panel.pack(fill="x", padx=6, pady=(0, 2))
            self._ref_skin_toggle_btn.configure(text="", image=BMTTheme.get_icon("arrow_drop_down", size=20))
        else:
            self._ref_skin_panel.pack_forget()
            self._ref_skin_toggle_btn.configure(text="", image=BMTTheme.get_icon("arrow_right", size=20))

    def _on_ref_skin_opacity_change(self, val=None):
        self._ref_skin_opacity = int(self._ref_skin_opacity_var.get())
        lbl = f"{self._ref_skin_opacity}%"
        if hasattr(self, "_ref_skin_opacity_lbl"):
            self._ref_skin_opacity_lbl.configure(text=lbl)
        self._ref_skin_photo = None  # invalidate cache
        self._redraw_ref()

    def _on_ref_skin_scale_change(self):
        try:
            pct = float(self._ref_skin_scale_var.get())
            self._ref_skin_scale = max(1.0, min(500.0, pct)) / 100.0
        except ValueError:
            pass
        self._ref_skin_photo = None  # invalidate cache
        self._redraw_ref()

    def _on_ref_skin_pos_change(self):
        try:
            self._ref_skin_ox = float(self._ref_skin_ox_var.get())
        except ValueError:
            pass
        try:
            self._ref_skin_oy = float(self._ref_skin_oy_var.get())
        except ValueError:
            pass
        self._redraw_ref()

    def _draw_ref_skin_overlay(self):
        """Composit the reference skin PNG onto the ref canvas at configured position/scale."""
        if not self._ref_skin_enabled: return
        if self._ref_skin_img_pil is None:
            self._load_ref_skin_image()
            if self._ref_skin_img_pil is None: return

        cw, ch = int(self._rw), int(self._rh)
        if cw < 1 or ch < 1: return

        # Compute target size based on world zoom
        orig_w, orig_h = self._ref_skin_img_pil.size
        zoom = self._rv[0]
        target_w = max(1, int(orig_w * self._ref_skin_scale * zoom))
        target_h = max(1, int(orig_h * self._ref_skin_scale * zoom))

        # Apply opacity by modifying alpha channel
        opacity_255 = int(self._ref_skin_opacity * 2.55)

        try:
            # Resize if needed (cache invalidated when zoom or options change)
            if self._ref_skin_photo is None or getattr(self, "_last_ref_zoom", None) != zoom:
                scaled = self._ref_skin_img_pil.resize(
                    (target_w, target_h), Image.NEAREST)
                # Apply opacity
                r, g, b, a = scaled.split()
                a = a.point(lambda x: int(x * opacity_255 / 255))
                scaled = Image.merge("RGBA", (r, g, b, a))
                self._ref_skin_photo_img = scaled  # keep ref
                self._ref_skin_photo = ImageTk.PhotoImage(scaled)
                self._last_ref_zoom = zoom

            # Position: Anchored to world space.
            cx_world = self._ref_skin_ox
            cy_world = self._ref_skin_oy
            ccx, ccy = self._v2c(cx_world, cy_world, self._rv, cw, ch)
            
            cx = ccx - target_w // 2
            cy = ccy - target_h // 2

            tag = "ref_skin_overlay"
            self.ref_canvas.create_image(cx, cy, image=self._ref_skin_photo,
                                         anchor="nw", tags=(tag,))
        except Exception as e:
            print(f"[SE] Error drawing ref skin overlay: {e}")

    def _fit_view(self, which):
        shapes = self.ref_shapes if which == "ref" else self.edit_shapes
        view = self._rv if which == "ref" else self._ev
        cw = self._rw if which == "ref" else self._ew
        ch = self._rh if which == "ref" else self._eh
        if not shapes:
            view[0], view[1], view[2] = 1.0, 0.0, 0.0
            if which == "ref": self._redraw_ref()
            else: self._redraw_edit()
            return
        mn_x = mn_y = float("inf"); mx_x = mx_y = float("-inf")
        for fs in shapes:
            for vx, vy in self._corners_v(fs):
                mn_x = min(mn_x, vx); mn_y = min(mn_y, vy)
                mx_x = max(mx_x, vx); mx_y = max(mx_y, vy)
        if mn_x >= mx_x: return
        cw2 = max(mx_x-mn_x, 1); ch2 = max(mx_y-mn_y, 1)
        pad = 40
        view[0] = max(MIN_ZOOM, min(MAX_ZOOM,
                                     min((cw-pad*2)/cw2, (ch-pad*2)/ch2)))
        view[1] = (mn_x+mx_x)/2; view[2] = (mn_y+mx_y)/2
        if which == "ref": self._redraw_ref()
        else: self._redraw_edit()

    # ═══════════════════════════════════════════════════════════════════
    #  EXPORT DIALOG
    # ═══════════════════════════════════════════════════════════════════
    def _show_export_dialog(self):
        if not self.swf:
            messagebox.showinfo("Export", "No SWF loaded."); return
        ExportSpritesDialog(self.parent, self)

    # ═══════════════════════════════════════════════════════════════════
    #  OPTIONS
    # ═══════════════════════════════════════════════════════════════════
    def _show_options(self):
        OptionsDialog(self.parent, self.prefs, self._on_options_changed)

    def _on_options_changed(self, prefs):
        self.prefs = prefs; _save_prefs(prefs)
        
        # Apply background colors immediately
        bgc = prefs.get("bg_color", "#181818")
        if getattr(self, "ref_canvas", None): self.ref_canvas.configure(bg=bgc)
        if getattr(self, "edit_canvas", None): self.edit_canvas.configure(bg=bgc)
        
        # Reload reference image if it changed
        self._ref_skin_photo = None
        self._ref_skin_img_pil = None

        new_mode = prefs.get("render_mode", "png")
        new_q = prefs.get("png_quality", 300) / 100.0
        changed = (new_mode != self.render_mode) or (abs(new_q-self.export_zoom) > 0.01)
        self.render_mode = new_mode; self.export_zoom = new_q
        self.show_grid.set(prefs.get("show_grid", True))
        if changed and self.swf_path:
            # Auto-limpiar caché al cambiar calidad/modo de renderizado
            _clear_image_cache()
            self._svg_raster_cache.clear()
            self.shape_images.clear()
            self._flush_render_cache()
            self._status("Render cache cleared. Reloading...")
            self._reload_swf()
        else:
            self._redraw_all()

    # ── Tree search / filter ──────────────────────────────────────────
    def _filter_ref_tree(self, text: str):
        """Show only ref-tree rows whose name or ID contains *text*."""
        t = text.strip().lower()
        for tid in self._all_ref_tree_ids:
            try:
                nm  = self.tree.item(tid, "text").lower()
            except Exception:
                continue
            vals = self.tree.item(tid, "values")
            vid = str(vals[0]).lower() if vals else ""
            match = (not t) or t in nm or t in vid
            try:
                if match:
                    self.tree.reattach(tid, "", "end")
                else:
                    self.tree.detach(tid)
            except Exception:
                pass

    def _filter_edit_tree(self, text: str):
        """Show only edit-tree rows whose name or ID matches *text*."""
        t = text.strip().lower()
        # Primero ocultamos todo
        for tid, parent_id in self._all_edit_tree_ids:
            try:
                self.edit_tree.detach(tid)
            except Exception:
                pass

        if not t:
            # Si no hay texto, restaurar todo
            for tid, parent_id in self._all_edit_tree_ids:
                try:
                    self.edit_tree.reattach(tid, parent_id, "end")
                except Exception:
                    pass
            return

        # Conjunto de padres que deben mostrarse obligatoriamente
        parents_to_show = set()
        nodes_to_show = set()

        for tid, parent_id in self._all_edit_tree_ids:
            try:
                nm = self.edit_tree.item(tid, "text").lower()
                vals = self.edit_tree.item(tid, "values")
                vid = str(vals[0]).lower() if vals else ""
                if t in nm or t in vid:
                    nodes_to_show.add(tid)
                    if parent_id:
                        parents_to_show.add(parent_id)
            except Exception:
                continue

        # Ahora restaurar: primero los padres, luego los hijos
        for tid, parent_id in self._all_edit_tree_ids:
            if not parent_id:  # Es un top-level (Sprite)
                if tid in nodes_to_show or tid in parents_to_show:
                    try: self.edit_tree.reattach(tid, "", "end")
                    except Exception: pass
            else:              # Es un hijo (Part)
                # Mostrar el hijo si él coincide, O si su padre completo coincidió
                if tid in nodes_to_show or parent_id in nodes_to_show:
                    try: self.edit_tree.reattach(tid, parent_id, "end")
                    except Exception: pass

    def _pick_guide_color(self):
        """Open color chooser for guide lines and update the button + redraw."""
        from tkinter import colorchooser
        result = colorchooser.askcolor(
            color=self._guide_color,
            title="Guide Line Color",
            parent=self.parent)
        if result and result[1]:
            self._guide_color = result[1]
            if hasattr(self, "_guide_color_btn") and self._guide_color_btn:
                self._guide_color_btn.configure(fg_color=self._guide_color)
            self._redraw_ref()

    def _filter_ref_selector(self, text: str):
        """Filter the Reference Sprite ComboBox values by search text."""
        t = text.strip().lower()
        filtered = [o for o in self._all_ref_opts if not t or t in o.lower()]
        if not filtered:
            filtered = ["(no match)"]
        if self.ref_selector:
            self.ref_selector.configure(values=filtered)

    # ═══════════════════════════════════════════════════════════════════
    #  COORDINATE HELPERS
    # ═══════════════════════════════════════════════════════════════════
    def _v2c(self, vx, vy, view, cw, ch):
        return ((vx-view[1])*view[0]+cw/2, (vy-view[2])*view[0]+ch/2)

    def _c2v(self, cx, cy, view, cw, ch):
        return ((cx-cw/2)/view[0]+view[1], (cy-ch/2)/view[0]+view[2])

    # ═══════════════════════════════════════════════════════════════════
    #  UTILITIES
    # ═══════════════════════════════════════════════════════════════════
    def _status(self, t):
        if self.status_var: self.status_var.set(t)

    def _ui(self, fn):
        try: self.parent.after(0, fn)
        except Exception: pass

    def _feedback(self, text, color):
        if hasattr(self, "feedback_label") and self.feedback_label:
            self.feedback_label.configure(text=text, text_color=color)
            self.parent.after(3000,
                              lambda: self.feedback_label.configure(text=""))

    def _collect_shape_ids(self, sprite_id, depth=0) -> Set[int]:
        ids: Set[int] = set()
        if depth > 10: return ids
        for p in self.sprite_parts.get(sprite_id, []):
            if p.char_id in self.shape_tags:
                ids.add(p.char_id)
            elif p.char_id in self.sprite_tags:
                ids.update(self._collect_shape_ids(p.char_id, depth+1))
        return ids

    def show(self):
        """Muestra el módulo (persistencia de sesión)."""
        if hasattr(self, 'main_frame') and self.main_frame:
            self.main_frame.pack(fill="both", expand=True)

    def hide(self):
        """Oculta el módulo sin destruirlo (persistencia de sesión)."""
        if hasattr(self, 'main_frame') and self.main_frame:
            self.main_frame.pack_forget()

    def destroy(self):
        if hasattr(self, 'main_frame') and self.main_frame:
            try:
                self.main_frame.destroy()
            except Exception:
                pass
            self.main_frame = None


# ╔═════════════════════════════════════════════════════════════════════╗
# ║  EXPORT DIALOG  — creates sprites/DefineSprite_X_a_Name/frame.swf  ║
# ╚═════════════════════════════════════════════════════════════════════╝
class ExportSpritesDialog(ctk.CTkToplevel):
    def __init__(self, parent, editor: SkinEditorModule):
        super().__init__(parent)
        self.editor = editor
        self.title("Export Sprites → frame.swf")
        self.geometry("660x700")
        self.configure(fg_color=BGD)
        self.transient(parent); self.grab_set()
        self.after(50, self.focus_force)
        self._vars: Dict[int, tk.BooleanVar] = {}
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Export Sprites as frame.swf",
                     font=("Segoe UI", 16, "bold"), text_color=AC
                     ).pack(padx=20, pady=(12, 2))
        ctk.CTkLabel(self,
                     text="Each selected sprite → sprites/DefineSprite_X_a_Name/frame.swf",
                     font=("Segoe UI", 11), text_color=FGD).pack(padx=20)

        # ── search in list ──
        sv = tk.StringVar()
        sv.trace_add("write", lambda *_: self._filter_list(sv.get()))
        ctk.CTkEntry(self, textvariable=sv, placeholder_text="Filter sprites...",
                     height=26, fg_color=BGI, border_color="#333",
                     text_color=FGT, font=("Segoe UI", 11)
                     ).pack(fill="x", padx=12, pady=(6, 2))

        # ── toolbar ──
        tb = ctk.CTkFrame(self, height=36, fg_color=BGP, corner_radius=6)
        tb.pack(fill="x", padx=12, pady=2); tb.pack_propagate(False)
        bs = dict(height=28, corner_radius=4, font=("Segoe UI", 11))
        ctk.CTkButton(tb, text="All",  width=60, fg_color="#2A2A2A",
                      hover_color="#3A3A3A", text_color=FGT,
                      command=self._all, **bs).pack(side="left", padx=3, pady=4)
        ctk.CTkButton(tb, text="None", width=60, fg_color="#2A2A2A",
                      hover_color="#3A3A3A", text_color=FGT,
                      command=self._none, **bs).pack(side="left", padx=3, pady=4)
        # Select only sprites visible in ref sprite
        ctk.CTkButton(tb, text="Ref Sprites", width=90, fg_color="#2A2A2A",
                      hover_color="#3A3A3A", text_color=FGT,
                      command=self._select_ref, **bs).pack(side="left", padx=3, pady=4)
        self.cnt = ctk.CTkLabel(tb, text="0 selected", font=("Segoe UI", 11),
                                text_color=FGD)
        self.cnt.pack(side="right", padx=10)

        # ── sprite list ──
        self._sc = ctk.CTkScrollableFrame(self, fg_color=BGI, corner_radius=6,
                                    scrollbar_button_color="#333",
                                    scrollbar_button_hover_color="#555")
        self._sc.pack(fill="both", expand=True, padx=12, pady=4)
        self._check_widgets: list = []
        for sid in sorted(self.editor.sprite_tags.keys()):
            pc = len(self.editor.sprite_parts.get(sid, []))
            nm = self.editor._sprite_display_name(sid)
            var = tk.BooleanVar(value=True); self._vars[sid] = var
            ck = ctk.CTkCheckBox(self._sc, text=f"{nm}  ({pc} parts)", variable=var,
                                 fg_color=AC, hover_color=ACD, text_color=FGT,
                                 font=("Segoe UI", 11), command=self._upd)
            ck.pack(anchor="w", padx=6, pady=1)
            self._check_widgets.append((sid, ck))

        # ── output dir ──
        df = ctk.CTkFrame(self, fg_color="transparent")
        df.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(df, text="Output:", font=("Segoe UI", 11),
                     text_color=FGD).pack(side="left")
        self.dir_e = ctk.CTkEntry(df, width=380, height=28, fg_color=BGI,
                                  border_color="#333", text_color=FGT,
                                  font=("Segoe UI", 11))
        init = self.editor.prefs.get("last_export_dir", "")
        if init: self.dir_e.insert(0, init)
        self.dir_e.pack(side="left", padx=6)
        folder_icon = BMTTheme.get_icon("file_open")
        ctk.CTkButton(df, text="" if folder_icon else "…", 
                      image=folder_icon,
                      width=36 if folder_icon else 36, height=28,
                      fg_color="#2A2A2A", hover_color="#3A3A3A",
                      text_color=FGT, command=self._browse).pack(side="left")

        # ── progress ──
        self.pbar = ctk.CTkProgressBar(self, fg_color="#333",
                                       progress_color=AC, height=6)
        self.pbar.pack(fill="x", padx=12, pady=4); self.pbar.set(0)
        self.stat = ctk.CTkLabel(self, text="Ready", font=("Segoe UI", 10),
                                 text_color=FGD)
        self.stat.pack(padx=12)

        # ── buttons ──
        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(fill="x", padx=12, pady=(4, 10))
        ctk.CTkButton(bf, text="Export frame.swf", width=150, height=36,
                      fg_color=AC, hover_color=ACD, text_color="#000",
                      font=("Segoe UI", 13, "bold"),
                      command=self._go).pack(side="right", padx=4)
        ctk.CTkButton(bf, text="Cancel", width=100, height=36,
                      fg_color="#333", hover_color="#444", text_color=FGT,
                      font=("Segoe UI", 12), command=self.destroy
                      ).pack(side="right", padx=4)
        self._upd()

    def _filter_list(self, text: str):
        t = text.strip().lower()
        for sid, ck in self._check_widgets:
            nm = self.editor._sprite_display_name(sid).lower()
            if t and t not in nm and t not in str(sid):
                ck.pack_forget()
            else:
                ck.pack(anchor="w", padx=6, pady=1)

    def _all(self):
        for v in self._vars.values(): v.set(True)
        self._upd()

    def _none(self):
        for v in self._vars.values(): v.set(False)
        self._upd()

    def _select_ref(self):
        """Select only sprites referenced inside the ref sprite."""
        ref_sids = {p.char_id
                    for p in self.editor.sprite_parts.get(self.editor.ref_sprite_id, [])
                    if p.is_sprite}
        for sid, var in self._vars.items():
            var.set(sid in ref_sids)
        self._upd()

    def _upd(self):
        n = sum(1 for v in self._vars.values() if v.get())
        self.cnt.configure(text=f"{n} selected")

    def _browse(self):
        d = filedialog.askdirectory(title="Output folder")
        if d:
            self.dir_e.delete(0, "end"); self.dir_e.insert(0, d)

    def _go(self):
        out = self.dir_e.get().strip()
        if not out:
            messagebox.showwarning("Export", "Select an output folder."); return
        sel = [s for s, v in self._vars.items() if v.get()]
        if not sel:
            messagebox.showwarning("Export", "No sprites selected."); return
        self.editor.prefs["last_export_dir"] = out
        _save_prefs(self.editor.prefs)
        threading.Thread(target=self._run, args=(out, sel),
                         daemon=True).start()

    def _run(self, out: str, ids: list):
        """Create sprites/<Name>/frame.swf for each selected sprite."""
        try:
            _ajvm()
            swf_path = self.editor.swf_path
            if not swf_path or not os.path.isfile(swf_path):
                self.after(0, lambda: messagebox.showerror(
                    "Export", "Original SWF file not found on disk.\n"
                               "Save/reload before exporting."))
                return

            self.after(0, lambda: self.stat.configure(text="Parsing SWF binary..."))
            raw = _swf_parse_raw_tags(swf_path)

            sprites_dir = os.path.join(out, "sprites")
            os.makedirs(sprites_dir, exist_ok=True)

            total = len(ids); done = 0; errors = 0
            for sid in ids:
                try:
                    # Build folder name: DefineSprite_X_a_ExportName
                    nm = ""
                    try:
                        en = self.editor.sprite_tags[sid].getExportFileName()
                        if en: nm = str(en)
                    except Exception:
                        pass
                    safe_nm = re.sub(r'[\\/:*?"<>|]', "_", nm) if nm else ""
                    folder_name = f"DefineSprite_{sid}"
                    if safe_nm:
                        folder_name += f"_a_{safe_nm}"
                    sprite_dir = os.path.join(sprites_dir, folder_name)
                    os.makedirs(sprite_dir, exist_ok=True)

                    # Collect all dependency char IDs
                    dep_ids = self.editor._collect_all_deps(sid)

                    # Build tag dict: only keep tags whose char_id is in deps
                    tag_dict: dict = {}
                    meta = raw.get(-1)
                    if meta:
                        tag_dict[-1] = meta
                    for cid in dep_ids:
                        if cid in raw:
                            tag_dict[cid] = raw[cid]

                    out_path = os.path.join(sprite_dir, "frame.swf")
                    _swf_write_minimal(tag_dict, sid, out_path)
                    done += 1
                except Exception as exc:
                    print(f"[SE Export] Sprite {sid} error: {exc}")
                    traceback.print_exc()
                    errors += 1

                prog = (done + errors) / total
                label = f"{done + errors}/{total}"
                self.after(0, lambda p=prog, l=label: (
                    self.pbar.set(p),
                    self.stat.configure(text=l)
                ))

            msg = (f"Exported {done}/{total} sprites to:\n{sprites_dir}\n"
                   f"Each in its own folder as frame.swf")
            if errors:
                msg += f"\n\n{errors} error(s) — check console."
            self.after(0, lambda: messagebox.showinfo("Export Complete", msg))
            self.after(0, lambda: self.stat.configure(text=f"Done — {done} exported"))
        except Exception as exc:
            traceback.print_exc()
            self.after(0, lambda: messagebox.showerror("Error", str(exc)))


# ╔═════════════════════════════════════════════════════════════════════╗
# ║  OPTIONS DIALOG                                                     ║
# ╚═════════════════════════════════════════════════════════════════════╝
class OptionsDialog(ctk.CTkToplevel):
    def __init__(self, parent, prefs, on_save=None):
        super().__init__(parent)
        self.prefs = dict(prefs); self.on_save = on_save
        self.title("Skin Editor Options")
        self.geometry("480x520")
        self.configure(fg_color=BGD)
        self.transient(parent); self.grab_set()
        self.after(50, self.focus_force)
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Options", font=("Segoe UI", 16, "bold"),
                     text_color=AC).pack(padx=20, pady=(12, 8))

        sc = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                    scrollbar_button_color="#333",
                                    scrollbar_button_hover_color="#555")
        sc.pack(fill="both", expand=True, padx=12, pady=4)

        self._sec(sc, "Render Mode")
        self._rm = tk.StringVar(value=self.prefs.get("render_mode", "png"))
        rf = ctk.CTkFrame(sc, fg_color="transparent")
        rf.pack(fill="x", padx=10, pady=4)
        ctk.CTkRadioButton(rf, text="PNG (pixel-crisp, fast)", variable=self._rm,
                           value="png", fg_color=AC, hover_color=ACD,
                           text_color=FGT, font=("Segoe UI", 12)).pack(anchor="w", pady=2)
        svg_lbl = "SVG (high quality, requires resvg or cairosvg)"
        if not (HAS_RESVG or HAS_CAIROSVG): svg_lbl += "  [NO RENDERER]"
        ctk.CTkRadioButton(rf, text=svg_lbl, variable=self._rm,
                           value="svg", fg_color=AC, hover_color=ACD,
                           text_color=FGT, font=("Segoe UI", 12)).pack(anchor="w", pady=2)

        self._sec(sc, "PNG Quality (shape cache)")
        qf = ctk.CTkFrame(sc, fg_color="transparent"); qf.pack(fill="x", padx=10, pady=4)
        self._qc = ctk.CTkComboBox(qf, values=list(QUALITY_MAP.keys()),
                                   width=150, height=28, fg_color=BGI,
                                   border_color="#333", button_color=ACD,
                                   dropdown_fg_color=BGI, text_color=FGT,
                                   font=("Segoe UI", 11))
        # Map stored int quality to label
        stored_q = self.prefs.get("png_quality", 300)
        default_lbl = "Medium (300%)"
        for lbl, mult in QUALITY_MAP.items():
            if abs(mult * 100 - stored_q) < 5:
                default_lbl = lbl; break
        self._qc.set(default_lbl)
        self._qc.pack(side="left")
        ctk.CTkLabel(qf, text="Higher = sharper, larger cache",
                     font=("Segoe UI", 10), text_color=FGD).pack(side="left", padx=8)

        self._sec(sc, "Display")
        self._gv = tk.BooleanVar(value=self.prefs.get("show_grid", True))
        ctk.CTkCheckBox(sc, text="Show grid", variable=self._gv,
                        fg_color=AC, hover_color=ACD, text_color=FGT,
                        font=("Segoe UI", 12)).pack(anchor="w", padx=14, pady=2)
        
        # Color pickers para grid y bg — usan el picker personalizado con guardado en tiempo real
        def _pick_bg():
            parent_win = sc.winfo_toplevel()
            c = _ask_color_se(self.prefs.get("bg_color", "#181818"), parent=parent_win)
            if c:
                self._bg_color_btn.configure(fg_color=c)
                self.prefs["bg_color"] = c
                _save_prefs(self.prefs)
                # Apply in real time
                if self.on_save: self.on_save(self.prefs)

        def _pick_grid():
            parent_win = sc.winfo_toplevel()
            c = _ask_color_se(self.prefs.get("grid_color", "#202020"), parent=parent_win)
            if c:
                self._grid_color_btn.configure(fg_color=c)
                self.prefs["grid_color"] = c
                _save_prefs(self.prefs)
                # Apply in real time
                if self.on_save: self.on_save(self.prefs)

        def _pick_hl():
            parent_win = sc.winfo_toplevel()
            c = _ask_color_se(self.prefs.get("hl_edit_color", "#FFD700"), parent=parent_win)
            if c:
                self._hl_color_btn.configure(fg_color=c)
                self.prefs["hl_edit_color"] = c
                _save_prefs(self.prefs)
                if self.on_save: self.on_save(self.prefs)

        def _pick_ref_img():
            parent_win = sc.winfo_toplevel()
            from tkinter import filedialog
            path = filedialog.askopenfilename(
                parent=parent_win, title="Select Reference Image",
                filetypes=[("Image Files", "*.png *.jpg *.jpeg")]
            )
            if path:
                self.prefs["ref_skin_img"] = str(path)
                self._ref_img_var.set(os.path.basename(path))
                _save_prefs(self.prefs)
                if self.on_save: self.on_save(self.prefs)

        cr = ctk.CTkFrame(sc, fg_color="transparent"); cr.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(cr, text="Background:", font=("Segoe UI", 11), text_color=FGD).pack(side="left", padx=4)
        self._bg_color_btn = ctk.CTkButton(cr, text="", width=30, height=20, corner_radius=4, fg_color=self.prefs.get("bg_color", "#181818"), command=_pick_bg)
        self._bg_color_btn.pack(side="left")
        ctk.CTkLabel(cr, text="Grid:", font=("Segoe UI", 11), text_color=FGD).pack(side="left", padx=4)
        self._grid_color_btn = ctk.CTkButton(cr, text="", width=30, height=20, corner_radius=4, fg_color=self.prefs.get("grid_color", "#202020"), command=_pick_grid)
        self._grid_color_btn.pack(side="left")
        ctk.CTkLabel(cr, text="Highlight:", font=("Segoe UI", 11), text_color=FGD).pack(side="left", padx=4)
        self._hl_color_btn = ctk.CTkButton(cr, text="", width=30, height=20, corner_radius=4, fg_color=self.prefs.get("hl_edit_color", "#FFD700"), command=_pick_hl)
        self._hl_color_btn.pack(side="left")

        # Ref Image chooser
        cri = ctk.CTkFrame(sc, fg_color="transparent"); cri.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(cri, text="Ref Image:", font=("Segoe UI", 11), text_color=FGD).pack(side="left", padx=4)
        ref_img_path = self.prefs.get("ref_skin_img", "Avatar.png")
        self._ref_img_var = tk.StringVar(value=os.path.basename(ref_img_path))
        ctk.CTkEntry(cri, textvariable=self._ref_img_var, width=120, height=22, state="disabled").pack(side="left", padx=2)
        ctk.CTkButton(cri, text="Browse...", width=60, height=22, command=_pick_ref_img, font=("Segoe UI", 10)).pack(side="left", padx=2)

        self._sec(sc, "Cache")
        cf = ctk.CTkFrame(sc, fg_color="transparent"); cf.pack(fill="x", padx=10, pady=4)
        bs = dict(height=28, corner_radius=4, font=("Segoe UI", 11))
        ctk.CTkButton(cf, text="Clear Cache", width=120,
                      fg_color="#8B0000", hover_color="#A52A2A", text_color="#FFF",
                      command=self._cc, **bs).pack(side="left", padx=4)
        ctk.CTkButton(cf, text="Open Folder", width=120,
                      fg_color="#2A2A2A", hover_color="#3A3A3A", text_color=FGT,
                      command=self._oc, **bs).pack(side="left", padx=4)
        try:
            tot = sum(os.path.getsize(os.path.join(dp, f))
                      for dp, _, fns in os.walk(_cache_root()) for f in fns)
            ctk.CTkLabel(sc, text=f"Cache: {tot/(1024*1024):.1f} MB",
                         font=("Segoe UI", 10), text_color=FGD
                         ).pack(anchor="w", padx=14, pady=2)
        except Exception: pass

        self._sec(sc, "Dependencies")
        status_lines = []
        if HAS_RESVG: status_lines.append(("resvg: INSTALLED", GREEN))
        else: status_lines.append(("resvg: NOT INSTALLED (recommended)", ORANGE))
        
        if HAS_CAIROSVG: status_lines.append(("cairosvg: INSTALLED", GREEN))
        else: status_lines.append(("cairosvg: NOT INSTALLED", FGD))

        for text, color in status_lines:
            ctk.CTkLabel(sc, text=text, font=("Segoe UI", 11),
                         text_color=color).pack(anchor="w", padx=14, pady=2)

        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(fill="x", padx=12, pady=(4, 10))
        ctk.CTkButton(bf, text="Save", width=110, height=36,
                      fg_color=AC, hover_color=ACD, text_color="#000",
                      font=("Segoe UI", 13, "bold"),
                      command=self._save).pack(side="right", padx=4)
        ctk.CTkButton(bf, text="Cancel", width=100, height=36,
                      fg_color="#333", hover_color="#444", text_color=FGT,
                      font=("Segoe UI", 12),
                      command=self.destroy).pack(side="right", padx=4)

    def _sec(self, par, t):
        ctk.CTkLabel(par, text=t, font=("Segoe UI", 13, "bold"),
                     text_color=AC).pack(anchor="w", padx=10, pady=(10, 2))
        ctk.CTkFrame(par, height=1, fg_color="#333").pack(fill="x", padx=10, pady=2)

    def _cc(self):
        _clear_image_cache()
        messagebox.showinfo("Cache", "Cleared. Reload SWF to re-export.")

    def _oc(self):
        p = _cache_root()
        if os.path.isdir(p): os.startfile(p)

    def _save(self):
        self.prefs["render_mode"] = self._rm.get()
        lbl = self._qc.get()
        mult = QUALITY_MAP.get(lbl, 3.0)
        self.prefs["png_quality"] = int(round(mult * 100))
        self.prefs["show_grid"] = self._gv.get()
        _save_prefs(self.prefs)
        if self.on_save: self.on_save(self.prefs)
        self.destroy()


# ═══════════════════════════════════════════════════════════════════════
#  MODULE-LEVEL HELPERS
# ═══════════════════════════════════════════════════════════════════════
def _sep(parent, side="left"):
    ctk.CTkFrame(parent, width=1, fg_color=FGD
                 ).pack(side=side, fill="y", pady=8, padx=4)
