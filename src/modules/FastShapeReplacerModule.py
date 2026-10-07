"""
Fast Shape Replacer Module
---------------------------
Loads SVG shapes from a folder, generates a grid-template SVG for bulk
editing, and replaces the original shapes with the user's modifications
while preserving each file's original canvas dimensions.

Template structure (4 groups, 3 locked + 1 editable):
  <g id="labels">            LOCKED - filename labels
  <g id="borders">           LOCKED - black dashed cell outlines
  <g id="real_shape_margin">  LOCKED - red semi-transparent actual-size guides
  <g id="shapes">            EDITABLE - nested <svg id="shape_N"> + loose content

Workflow:
  Step 1 - Select a folder containing SVGs (1.svg, 2.svg, ...).
  Step 2 - Generate a grid-template SVG.  Edit externally.
  Step 3 - Load the modified template; shapes are written back.
"""

from src.utils import get_project_root
import os
import re
import copy
import math
import threading
import datetime
import random
import xml.etree.ElementTree as ET
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from .ToolModuleBase import ToolModule
from src.utils.ThemeManager import BMTTheme, ACCENTS

# -------------------------------------------------------------------
# SVG / namespace helpers
# -------------------------------------------------------------------
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"
SODIPODI_NS = "http://sodipodi.sourceforge.net/DTD/sodipodi-0.0.dtd"

ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)
ET.register_namespace("inkscape", INKSCAPE_NS)
ET.register_namespace("sodipodi", SODIPODI_NS)

# Grid constants
COLUMNS = 10
CELL_SIZE = 150          # safe-area square side (px)
CELL_PADDING = 6         # padding between border and content
CELL_GAP = 12            # gap between cells
LABEL_HEIGHT = 18        # space for the label above each cell
BORDER_STROKE = 2        # border width

_DIM_RE = re.compile(r"([\d.]+)")


def _parse_dim(val):
    """Extract a number from an SVG dimension string ('120px' -> 120.0)."""
    if not val:
        return None
    m = _DIM_RE.search(str(val))
    return float(m.group(1)) if m else None


def _svg(local):
    """Return a namespace-qualified SVG tag."""
    return f"{{{SVG_NS}}}{local}"


def _write_svg(tree, path):
    """Write an ElementTree as SVG 1.1 with utf-8 encoding for maximum
    compatibility (Windows Explorer thumbnails, Inkscape, browsers)."""
    ET.indent(tree, space="  ")
    tree.write(path, xml_declaration=True, encoding="utf-8")


# ===================================================================
# Module
# ===================================================================

class FastShapeReplacerModule(ToolModule):
    """Fast bulk shape replacer with grid-template workflow."""

    def __init__(self, parent, game_path, mods_path, icons=None):
        super().__init__(parent, game_path, mods_path, icons=icons)
        self.shapes_folder = ""
        self.template_path = ""
        self.shapes_meta = []   # [{filename, filepath, width_*, height_*, viewBox}, ...]

    # ToolModule interface ------------------------------------------
    def get_tool_name(self):
        return "Fast Shape Replacer"

    def get_tool_icon(self):
        return ""

    # ---------------------------------------------------------------
    # UI
    # ---------------------------------------------------------------
    def create_ui(self):
        self.container = ctk.CTkFrame(self.parent, fg_color=BMTTheme.BG_DARK)

        outer = ctk.CTkFrame(self.container, fg_color="#0E0E0E")
        outer.pack(fill="both", expand=True, padx=20, pady=20)
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_columnconfigure(1, weight=1)
        outer.grid_rowconfigure(1, weight=1)

        # Title
        title = ctk.CTkLabel(
            outer, text="Fast Shape Replacer",
        )
        BMTTheme.style_title(title, color=ACCENTS["Fast Shape Replacer"])
        title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        # ----- LEFT: Steps panel -----
        steps = ctk.CTkFrame(outer, fg_color="#171717", corner_radius=10)
        steps.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        steps.grid_columnconfigure(0, weight=1)

        # ===== STEP 1 =====
        self._section_label(steps, "Step 1 - Select Shapes Folder", row=0)

        s1_frame = ctk.CTkFrame(steps, fg_color="#2C2C2C", corner_radius=8)
        s1_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 5))
        s1_frame.grid_columnconfigure(0, weight=1)

        self.folder_label = ctk.CTkLabel(
            s1_frame, text="No folder selected",
            font=ctk.CTkFont(size=11), text_color="#999999", anchor="w",
        )
        self.folder_label.grid(row=0, column=0, sticky="ew", padx=10, pady=8)

        folder_icon = BMTTheme.get_icon("file_open")
        ctk.CTkButton(
            s1_frame,
            text="" if folder_icon else "Browse",
            image=folder_icon,
            width=35 if folder_icon else 70, 
            height=28,
            fg_color="#E65100", hover_color="#BF360C",
            command=self._select_folder,
        ).grid(row=0, column=1, padx=8, pady=8)

        self.shapes_count_label = ctk.CTkLabel(
            steps, text="",
            font=ctk.CTkFont(size=11), text_color="#999999",
        )
        self.shapes_count_label.grid(row=2, column=0, sticky="w", padx=18, pady=(0, 8))

        # ===== STEP 2 =====
        self._section_label(steps, "Step 2 - Generate Template", row=3)

        self.gen_btn = ctk.CTkButton(
            steps, text="Generate Grid Template",
            font=ctk.CTkFont(size=13, weight="bold"), height=40,
            fg_color="#F57C00", hover_color="#E65100",
            command=self._generate_template,
        )
        self.gen_btn.grid(row=4, column=0, sticky="ew", padx=15, pady=(0, 5))

        self.template_label = ctk.CTkLabel(
            steps, text="",
            font=ctk.CTkFont(size=11), text_color="#66BB6A",
        )
        self.template_label.grid(row=5, column=0, sticky="w", padx=18, pady=(0, 8))

        info_label = ctk.CTkLabel(
            steps,
            text=(
                "Edit the generated SVG externally.\n"
                "Replace shapes inside the red dashed borders.\n"
                "Leave untouched cells as-is (they will be re-saved)."
            ),
            font=BMTTheme.get_font(10), text_color="#777777", justify="left",
        )
        info_label.grid(row=6, column=0, sticky="w", padx=18, pady=(0, 10))

        # ===== STEP 3 =====
        self._section_label(steps, "Step 3 - Apply Changes", row=7)

        self.apply_btn = ctk.CTkButton(
            steps, text="Load Modified Template",
            font=ctk.CTkFont(size=13, weight="bold"), height=40,
            fg_color="#2E7D32", hover_color="#1B5E20",
            command=self._apply_template,
        )
        self.apply_btn.grid(row=8, column=0, sticky="ew", padx=15, pady=(0, 5))

        self.apply_status = ctk.CTkLabel(
            steps, text="",
            font=ctk.CTkFont(size=11), text_color="#66BB6A",
        )
        self.apply_status.grid(row=9, column=0, sticky="w", padx=18, pady=(0, 15))

        # ----- RIGHT: Log panel -----
        log_panel = ctk.CTkFrame(outer, fg_color="#171717", corner_radius=10)
        log_panel.grid(row=1, column=1, sticky="nsew", padx=(8, 0))
        log_panel.grid_rowconfigure(1, weight=1)
        log_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            log_panel, text="Log",
            font=BMTTheme.get_font(14, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))

        self.log_text = ctk.CTkTextbox(log_panel)
        BMTTheme.style_log_text(self.log_text)
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))

        self.log("Fast Shape Replacer ready")
        self.log("Select a folder with SVG shapes to begin")
        return self.container

    # ---------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------
    def _section_label(self, parent, text, row):
        label = ctk.CTkLabel(
            parent, text=text,
        )
        BMTTheme.style_subtitle(label, color=ACCENTS["Fast Shape Replacer"])
        label.grid(row=row, column=0, sticky="w", padx=15, pady=(12, 5))

    def log(self, msg):
        if hasattr(self, "log_text"):
            self.log_text.configure(state="normal")
            self.log_text.insert("end", f"{msg}\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")

    def _safe_log(self, msg):
        """Thread-safe log."""
        if self.container and self.container.winfo_exists():
            self.container.after(0, lambda m=msg: self.log(m))

    # ---------------------------------------------------------------
    # Step 1: select folder & scan
    # ---------------------------------------------------------------
    def _select_folder(self):
        path = filedialog.askdirectory(title="Select Shapes Folder")
        if not path:
            return
        self.shapes_folder = path
        self.folder_label.configure(text=path, text_color="#FFFFFF")
        self.log(f"Folder: {path}")
        threading.Thread(target=self._scan_folder, daemon=True).start()

    def _scan_folder(self):
        """Scan folder for SVG files and collect metadata."""
        folder = self.shapes_folder
        svg_files = sorted(
            [f for f in os.listdir(folder) if f.lower().endswith(".svg")],
            key=self._natural_sort_key,
        )
        if not svg_files:
            self._safe_log("No SVG files found in the selected folder")
            self.container.after(0, lambda: self.shapes_count_label.configure(
                text="0 SVGs found", text_color="#F44336"))
            return

        meta_list = []
        for fname in svg_files:
            # Skip the template itself if present
            if fname.lower().startswith("shapes_template"):
                continue
            fpath = os.path.join(folder, fname)
            info = self._read_svg_meta(fpath)
            if info:
                meta_list.append(info)
                self._safe_log(
                    f"  {fname}  ({info['width_val']:.0f} x {info['height_val']:.0f})"
                )

        self.shapes_meta = meta_list

        def _ui_update():
            n = len(meta_list)
            self.shapes_count_label.configure(
                text=f"{n} SVG{'s' if n != 1 else ''} found",
                text_color="#66BB6A",
            )
            self.gen_btn.configure(state="normal")
            self.log(f"Loaded metadata for {n} shapes")

        self.container.after(0, _ui_update)

    @staticmethod
    def _natural_sort_key(name):
        parts = re.split(r"(\d+)", name)
        return [int(p) if p.isdigit() else p.lower() for p in parts]

    @staticmethod
    def _read_svg_meta(filepath):
        """Read SVG and return metadata dict or None."""
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()

            w_attr = root.get("width", "")
            h_attr = root.get("height", "")
            vb = root.get("viewBox", "")

            w_val = _parse_dim(w_attr)
            h_val = _parse_dim(h_attr)

            if vb:
                parts = vb.replace(",", " ").split()
                if len(parts) >= 4:
                    if w_val is None:
                        w_val = float(parts[2])
                    if h_val is None:
                        h_val = float(parts[3])

            if w_val is None:
                w_val = 100.0
            if h_val is None:
                h_val = 100.0
            if not vb:
                vb = f"0 0 {w_val} {h_val}"

            return {
                "filename": os.path.basename(filepath),
                "filepath": filepath,
                "width_attr": w_attr if w_attr else str(w_val),
                "height_attr": h_attr if h_attr else str(h_val),
                "width_val": w_val,
                "height_val": h_val,
                "viewBox": vb,
            }
        except Exception as e:
            print(f"[FastShapeReplacer] Error reading {filepath}: {e}")
            return None

    # ---------------------------------------------------------------
    # Step 2: generate grid-template SVG
    # ---------------------------------------------------------------
    def _generate_template(self):
        if not self.shapes_meta:
            self.log("No shapes loaded. Select a folder first.")
            return
        threading.Thread(target=self._generate_template_thread, daemon=True).start()

    def _generate_template_thread(self):
        try:
            n = len(self.shapes_meta)
            rows = math.ceil(n / COLUMNS)

            cell_total_w = CELL_SIZE + CELL_GAP
            cell_total_h = CELL_SIZE + LABEL_HEIGHT + CELL_GAP
            total_w = COLUMNS * cell_total_w + CELL_GAP
            total_h = rows * cell_total_h + CELL_GAP

            # Inkscape namespace helpers
            ink_gm = f"{{{INKSCAPE_NS}}}groupmode"
            ink_lb = f"{{{INKSCAPE_NS}}}label"
            sod_ins = f"{{{SODIPODI_NS}}}insensitive"

            # Root <svg> -- version 1.1 for Explorer thumbnail support
            root = ET.Element(_svg("svg"))
            root.set("version", "1.1")
            root.set("width", str(total_w))
            root.set("height", str(total_h))
            root.set("viewBox", f"0 0 {total_w} {total_h}")

            # ---- Four separated groups (render order bottom->top) ----

            # 1. borders (LOCKED) - black dashed outlines
            borders_g = ET.SubElement(root, _svg("g"))
            borders_g.set("id", "borders")
            borders_g.set(ink_gm, "layer")
            borders_g.set(ink_lb, "borders")
            borders_g.set(sod_ins, "true")

            # 2. real_shape_margin (LOCKED) - red semi-transparent real dims
            margin_g = ET.SubElement(root, _svg("g"))
            margin_g.set("id", "real_shape_margin")
            margin_g.set(ink_gm, "layer")
            margin_g.set(ink_lb, "real_shape_margin")
            margin_g.set(sod_ins, "true")

            # 3. labels (LOCKED) - text on top so always readable
            labels_g = ET.SubElement(root, _svg("g"))
            labels_g.set("id", "labels")
            labels_g.set(ink_gm, "layer")
            labels_g.set(ink_lb, "labels")
            labels_g.set(sod_ins, "true")

            # 4. shapes (EDITABLE) - actual content
            shapes_g = ET.SubElement(root, _svg("g"))
            shapes_g.set("id", "shapes")
            shapes_g.set(ink_gm, "layer")
            shapes_g.set(ink_lb, "shapes")
            # NO insensitive = editable

            for idx, meta in enumerate(self.shapes_meta):
                col = idx % COLUMNS
                row_n = idx // COLUMNS

                cx = CELL_GAP + col * cell_total_w
                cy = CELL_GAP + row_n * cell_total_h
                sx = cx
                sy = cy + LABEL_HEIGHT

                # --- label (in labels group - on top) ---
                label = ET.SubElement(labels_g, _svg("text"))
                label.set("id", f"label_{idx}")
                label.set("x", str(cx + CELL_SIZE / 2))
                label.set("y", str(cy + LABEL_HEIGHT - 4))
                label.set("text-anchor", "middle")
                label.set("font-size", "11")
                label.set("font-family", "monospace")
                label.set("fill", "#888888")
                label.text = meta["filename"]

                # --- border (in borders group) - BLACK dashed ---
                border = ET.SubElement(borders_g, _svg("rect"))
                border.set("id", f"border_{idx}")
                border.set("x", str(sx))
                border.set("y", str(sy))
                border.set("width", str(CELL_SIZE))
                border.set("height", str(CELL_SIZE))
                border.set("fill", "none")
                border.set("stroke", "#000000")
                border.set("stroke-width", str(BORDER_STROKE))
                border.set("stroke-dasharray", "6,4")

                # --- real shape margin (in margin group) ---
                # Scale original dims to fit inside content area
                content_area = CELL_SIZE - 2 * CELL_PADDING
                ow, oh = meta["width_val"], meta["height_val"]
                scale = min(content_area / max(ow, 1), content_area / max(oh, 1))
                scaled_w = ow * scale
                scaled_h = oh * scale
                # Center within the cell content area
                margin_x = sx + CELL_PADDING + (content_area - scaled_w) / 2
                margin_y = sy + CELL_PADDING + (content_area - scaled_h) / 2

                margin_rect = ET.SubElement(margin_g, _svg("rect"))
                margin_rect.set("id", f"shape_margin_{idx}")
                margin_rect.set("x", str(margin_x))
                margin_rect.set("y", str(margin_y))
                margin_rect.set("width", str(scaled_w))
                margin_rect.set("height", str(scaled_h))
                margin_rect.set("fill", "#ff0000")
                margin_rect.set("fill-opacity", "0.10")
                margin_rect.set("stroke", "#ff0000")
                margin_rect.set("stroke-opacity", "0.5")
                margin_rect.set("stroke-width", "1")
                margin_rect.set("stroke-dasharray", "4,3")

                # --- shape content (in shapes group - editable) ---
                nested = ET.SubElement(shapes_g, _svg("svg"))
                nested.set("id", f"shape_{idx}")
                nested.set("x", str(sx + CELL_PADDING))
                nested.set("y", str(sy + CELL_PADDING))
                nested.set("width", str(content_area))
                nested.set("height", str(content_area))
                nested.set("viewBox", meta["viewBox"])
                nested.set("overflow", "visible")
                # Store original metadata
                nested.set("data-filename", meta["filename"])
                nested.set("data-original-width", meta["width_attr"])
                nested.set("data-original-height", meta["height_attr"])
                nested.set("data-original-viewbox", meta["viewBox"])

                # Copy SVG children into the nested element
                try:
                    orig_tree = ET.parse(meta["filepath"])
                    orig_root = orig_tree.getroot()
                    for child in list(orig_root):
                        nested.append(copy.deepcopy(child))
                except Exception as e:
                    self._safe_log(f"  Warning: {meta['filename']}: {e}")

                self._safe_log(f"  Added {meta['filename']}")

            # Write template
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            rand_id = random.randint(1000, 9999)
            template_name = f"shapes_template_{timestamp}_{rand_id}.svg"
            out_path = os.path.join(self.shapes_folder, template_name)
            _write_svg(ET.ElementTree(root), out_path)
            self.template_path = out_path

            def _ui():
                self.template_label.configure(text=f"Saved: {template_name}")
                self.apply_btn.configure(state="normal")
                self.log(f"Template generated: {out_path}")
                self.log(f"Grid: {COLUMNS} x {rows}  ({n} shapes)")
                self.log("Open it in your SVG editor, replace shapes inside")
                self.log("the cell borders, then use Step 3.")
                self.log("Locked layers: labels, borders, real_shape_margin")
                self.log("Editable layer: shapes")

            self.container.after(0, _ui)

        except Exception as e:
            self._safe_log(f"Error generating template: {e}")

    # ---------------------------------------------------------------
    # Step 3: load modified template & replace originals
    # ---------------------------------------------------------------
    def _apply_template(self):
        path = filedialog.askopenfilename(
            title="Select Modified Template SVG",
            initialdir=self.shapes_folder,
            filetypes=[("SVG files", "*.svg")],
        )
        if not path:
            return
        self.log(f"Loading template: {os.path.basename(path)}")
        threading.Thread(
            target=self._apply_template_thread, args=(path,), daemon=True
        ).start()

    # ---------------------------------------------------------------
    # Helpers for element-detection in apply
    # ---------------------------------------------------------------

    @staticmethod
    def _extract_transform_offset(elem):
        """Return effective (tx, ty) translation from ``transform`` attr.

        Handles:
        - ``translate(tx, ty)``  /  ``translate(tx)``
        - ``matrix(a,b,c,d, tx, ty)``
        - combinations (first match wins)
        """
        raw = (elem.get("transform") or "").strip()
        if not raw:
            return 0.0, 0.0

        # translate(tx, ty) or translate(tx)
        m = re.search(
            r"translate\(\s*([-\d.eE]+)(?:\s*[,\s]\s*([-\d.eE]+))?\s*\)", raw
        )
        if m:
            tx = float(m.group(1))
            ty = float(m.group(2)) if m.group(2) else 0.0
            return tx, ty

        # matrix(a, b, c, d, e, f)  →  e, f are translation
        m = re.search(
            r"matrix\(\s*"
            r"[-\d.eE]+\s*[,\s]\s*"   # a
            r"[-\d.eE]+\s*[,\s]\s*"   # b
            r"[-\d.eE]+\s*[,\s]\s*"   # c
            r"[-\d.eE]+\s*[,\s]\s*"   # d
            r"([-\d.eE]+)\s*[,\s]\s*" # e  ← tx
            r"([-\d.eE]+)\s*\)",      # f  ← ty
            raw,
        )
        if m:
            return float(m.group(1)), float(m.group(2))

        return 0.0, 0.0

    @staticmethod
    def _get_raw_position(elem):
        """Return (x, y) from the element's intrinsic attributes.

        Handles: rect/svg/image/use/text (x,y), circle/ellipse (cx,cy),
        line (x1,y1), path (first M), polygon/polyline (first point).
        Returns (None, None) if position cannot be determined.
        """
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

        if tag in ("rect", "image", "use", "svg", "text", "foreignObject"):
            rx, ry = elem.get("x"), elem.get("y")
            if rx is not None and ry is not None:
                try:
                    return (
                        float(re.sub(r"[a-zA-Z%]+", "", rx)),
                        float(re.sub(r"[a-zA-Z%]+", "", ry)),
                    )
                except ValueError:
                    pass

        if tag in ("circle", "ellipse"):
            cx, cy = elem.get("cx"), elem.get("cy")
            if cx is not None and cy is not None:
                try:
                    return float(cx), float(cy)
                except ValueError:
                    pass

        if tag == "line":
            x1, y1 = elem.get("x1"), elem.get("y1")
            if x1 is not None and y1 is not None:
                try:
                    return float(x1), float(y1)
                except ValueError:
                    pass

        if tag == "path":
            d = (elem.get("d") or "").strip()
            m = re.match(r"[Mm]\s*([-\d.eE]+)[,\s]+([-\d.eE]+)", d)
            if m:
                return float(m.group(1)), float(m.group(2))

        if tag in ("polygon", "polyline"):
            pts = (elem.get("points") or "").strip()
            m = re.match(r"([-\d.eE]+)[,\s]+([-\d.eE]+)", pts)
            if m:
                return float(m.group(1)), float(m.group(2))

        return None, None

    def _find_cell_for_position(self, x, y):
        """Given template-space coords, return the matching cell index or None."""
        n = len(self.shapes_meta)
        cell_total_w = CELL_SIZE + CELL_GAP
        cell_total_h = CELL_SIZE + LABEL_HEIGHT + CELL_GAP
        for idx in range(n):
            col = idx % COLUMNS
            row_n = idx // COLUMNS
            sx = CELL_GAP + col * cell_total_w
            sy = CELL_GAP + row_n * cell_total_h + LABEL_HEIGHT
            if sx <= x < sx + CELL_SIZE and sy <= y < sy + CELL_SIZE:
                return idx
        return None

    # -- IDs that are never treated as loose content --
    _IGNORED_IDS = frozenset({
        "labels", "borders", "real_shape_margin", "shapes",
    })

    def _collect_all_loose(self, shapes_group, shape_n_obj_ids):
        """Walk every descendant of *shapes_group* that is NOT inside a
        ``shape_N`` container, compute its absolute position in template
        space, and classify it into a grid cell.

        Returns ``(classified, unclassified)`` where:
        - classified = ``{cell_idx: [element, …]}``
        - unclassified = ``[element, …]``  (no position / outside grid)
        """
        classified: dict[int, list[ET.Element]] = {}
        unclassified: list[ET.Element] = []

        # ---- Build a parent-map so we can walk UP from any element ----
        parent_map: dict[ET.Element, ET.Element] = {}
        for parent in shapes_group.iter():
            for child in parent:
                parent_map[child] = parent

        # ---- Gather EVERY leaf / meaningful element ----
        # Skip: shapes_group itself, shape_N subtrees, locked layers
        for elem in shapes_group.iter():
            eid = elem.get("id", "")

            # Skip the shapes group itself
            if elem is shapes_group:
                continue

            # Skip locked / infrastructure groups
            if eid in self._IGNORED_IDS:
                continue

            # Skip shape_N containers and all their descendants
            if id(elem) in shape_n_obj_ids:
                continue

            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

            # Only process content-bearing elements (not plain <g> wrappers)
            # <g> wrappers are traversed automatically by .iter()
            if tag in ("g",):
                # If the group has NO content-bearing children, treat it as
                # content itself (empty group the user placed intentionally)
                has_children = any(True for _ in elem)
                if has_children:
                    continue  # let .iter() descend into its children

            # ---- Compute absolute position ----
            # Walk up from elem to shapes_group, accumulating transforms
            abs_x, abs_y = 0.0, 0.0

            # Own intrinsic position (from d=, x=, cx=, …)
            rx, ry = self._get_raw_position(elem)
            if rx is not None:
                abs_x += rx
            if ry is not None:
                abs_y += ry

            # Accumulate transform offsets from elem up to shapes_group
            node = elem
            while node is not None and node is not shapes_group:
                tx, ty = self._extract_transform_offset(node)
                abs_x += tx
                abs_y += ty
                # For <svg> wrappers, also add x/y attrs
                ntag = node.tag.split("}")[-1] if "}" in node.tag else node.tag
                if ntag == "svg" and node is not elem:
                    sx_attr = node.get("x")
                    sy_attr = node.get("y")
                    try:
                        if sx_attr:
                            abs_x += float(re.sub(r"[a-zA-Z%]+", "", sx_attr))
                        if sy_attr:
                            abs_y += float(re.sub(r"[a-zA-Z%]+", "", sy_attr))
                    except ValueError:
                        pass
                node = parent_map.get(node)

            # ---- Classify by grid cell ----
            cell = self._find_cell_for_position(abs_x, abs_y)
            if cell is not None:
                classified.setdefault(cell, []).append(elem)
            else:
                unclassified.append(elem)

        return classified, unclassified

    def _apply_template_thread(self, template_path):
        """Parse modified template and write back individual SVGs.

        Detection strategy (in priority order):
        1. ``shape_N`` containers  (original workflow)
        2. Loose elements classified by grid position
        3. **Fallback**: if neither works, assign ALL loose elements
           sequentially to cells ``0 … N-1``
        """
        try:
            tree = ET.parse(template_path)
            tpl_root = tree.getroot()

            # --- Locate the shapes group ---
            shapes_group = None
            for elem in tpl_root.iter():
                if elem.get("id") == "shapes":
                    shapes_group = elem
                    break

            if shapes_group is None:
                self._safe_log('ERROR: <g id="shapes"> not found in template')
                self._safe_log("Make sure the 'shapes' group was not renamed.")
                return

            # ----- Debug: show what's inside shapes group -----
            direct_children = list(shapes_group)
            self._safe_log(
                f"  shapes group has {len(direct_children)} direct children"
            )
            for i, ch in enumerate(direct_children[:8]):
                tag_s = ch.tag.split("}")[-1] if "}" in ch.tag else ch.tag
                self._safe_log(
                    f"    [{i}] <{tag_s}> id={ch.get('id','?')} "
                    f"transform={ch.get('transform','(none)')!r}"
                )
            if len(direct_children) > 8:
                self._safe_log(f"    … and {len(direct_children) - 8} more")

            # ----- Collect shape_N containers -----
            shape_elems: dict[int, ET.Element] = {}
            shape_n_obj_ids: set[int] = set()

            for child in shapes_group.iter():
                eid = child.get("id", "")
                m_id = re.match(r"^shape_(\d+)$", eid)
                if m_id:
                    idx_val = int(m_id.group(1))
                    shape_elems[idx_val] = child
                    for desc in child.iter():
                        shape_n_obj_ids.add(id(desc))

            # ----- Collect loose elements -----
            classified, unclassified = self._collect_all_loose(
                shapes_group, shape_n_obj_ids
            )

            total_classified = sum(len(v) for v in classified.values())
            self._safe_log(
                f"Found {len(shape_elems)} shape_N containers, "
                f"{total_classified} classified loose, "
                f"{len(unclassified)} unclassified loose"
            )
            for cidx in sorted(classified):
                for el in classified[cidx]:
                    tag_s = el.tag.split("}")[-1] if "}" in el.tag else el.tag
                    self._safe_log(f"  Loose <{tag_s}> -> cell {cidx}")

            # ----- Fallback: sequential assignment -----
            # If we have NO shape_N and NO classified, but there ARE
            # unclassified elements → assign them in XML order to cells.
            use_fallback = False
            if (not shape_elems and total_classified == 0
                    and len(unclassified) > 0):
                n_cells = len(self.shapes_meta)
                self._safe_log(
                    f"  Position detection found nothing. "
                    f"Fallback: assigning {len(unclassified)} elements "
                    f"sequentially to {n_cells} cells."
                )
                use_fallback = True
                for seq_idx, el in enumerate(unclassified):
                    if seq_idx < n_cells:
                        classified.setdefault(seq_idx, []).append(el)
                total_classified = sum(len(v) for v in classified.values())

            if not shape_elems and total_classified == 0:
                self._safe_log("ERROR: No shape content found inside shapes group")
                return

            replaced = 0
            skipped = 0

            all_cell_indices = set(shape_elems.keys()) | set(classified.keys())

            for idx in sorted(all_cell_indices):
                elem = shape_elems.get(idx)

                # Resolve metadata
                fname = orig_w = orig_h = orig_vb = None
                if elem is not None:
                    fname = elem.get("data-filename")
                    orig_w = elem.get("data-original-width")
                    orig_h = elem.get("data-original-height")
                    orig_vb = elem.get("data-original-viewbox")
                if not fname and idx < len(self.shapes_meta):
                    meta = self.shapes_meta[idx]
                    fname = meta["filename"]
                    orig_w = meta["width_attr"]
                    orig_h = meta["height_attr"]
                    orig_vb = meta["viewBox"]

                if not fname:
                    self._safe_log(
                        f"  cell {idx}: unable to resolve filename, skipped"
                    )
                    skipped += 1
                    continue

                out_path = os.path.join(self.shapes_folder, fname)

                # Parse original viewBox values
                vb_x = vb_y = vb_w = vb_h = 0.0
                if orig_vb:
                    vb_parts = orig_vb.split()
                    if len(vb_parts) == 4:
                        vb_x, vb_y = float(vb_parts[0]), float(vb_parts[1])
                        vb_w, vb_h = float(vb_parts[2]), float(vb_parts[3])

                # Build new SVG with original dimensions
                new_root = ET.Element(_svg("svg"))
                new_root.set("version", "1.1")
                if orig_w:
                    new_root.set("width", orig_w)
                if orig_h:
                    new_root.set("height", orig_h)
                if orig_vb:
                    new_root.set("viewBox", orig_vb)

                # ---- Copy children from the shape_N container ----
                if elem is not None:
                    # Check if the editor changed the viewBox on the shape_N
                    current_vb = elem.get("viewBox", "")
                    needs_vb_fix = (
                        current_vb
                        and orig_vb
                        and current_vb != orig_vb
                    )
                    if needs_vb_fix:
                        # The editor modified the viewBox; wrap children
                        # in a nested <svg> that maps from edited viewBox
                        # to the original viewBox.
                        bridge = ET.SubElement(new_root, _svg("svg"))
                        bridge.set("viewBox", current_vb)
                        bridge.set("width", str(vb_w))
                        bridge.set("height", str(vb_h))
                        bridge.set("x", str(vb_x))
                        bridge.set("y", str(vb_y))
                        target = bridge
                        self._safe_log(
                            f"  shape_{idx}: viewBox changed "
                            f"({orig_vb} -> {current_vb}), compensating"
                        )
                    else:
                        target = new_root

                    for sub in list(elem):
                        target.append(copy.deepcopy(sub))

                # ---- Merge loose / classified elements ----
                loose_items = classified.get(idx, [])
                if loose_items and vb_w > 0 and vb_h > 0:
                    content_area = CELL_SIZE - 2 * CELL_PADDING
                    col = idx % COLUMNS
                    row_n = idx // COLUMNS
                    cell_total_w = CELL_SIZE + CELL_GAP
                    cell_total_h = CELL_SIZE + LABEL_HEIGHT + CELL_GAP
                    cell_x = CELL_GAP + col * cell_total_w + CELL_PADDING
                    cell_y = (
                        CELL_GAP
                        + row_n * cell_total_h
                        + LABEL_HEIGHT
                        + CELL_PADDING
                    )

                    # The template uses preserveAspectRatio="xMidYMid meet"
                    # (default) on the shape_N nested <svg>.  That means
                    # UNIFORM scaling with centering offsets.
                    par_scale = min(
                        content_area / max(vb_w, 1),
                        content_area / max(vb_h, 1),
                    )
                    # Centering offsets inside the content area
                    offset_x = (content_area - vb_w * par_scale) / 2.0
                    offset_y = (content_area - vb_h * par_scale) / 2.0

                    # Reverse transform: template-space → viewBox-space
                    # Forward was: vb → template
                    #   tx = vb_x_coord * par_scale + cell_x + offset_x
                    # Reverse:
                    #   vb_x_coord = (tx - cell_x - offset_x) / par_scale
                    inv_scale = 1.0 / par_scale

                    wrapper = ET.SubElement(new_root, _svg("g"))
                    wrapper.set(
                        "transform",
                        f"translate({vb_x},{vb_y}) "
                        f"scale({inv_scale}) "
                        f"translate("
                        f"{-(cell_x + offset_x)},"
                        f"{-(cell_y + offset_y)})",
                    )
                    for le in loose_items:
                        wrapper.append(copy.deepcopy(le))

                _write_svg(ET.ElementTree(new_root), out_path)
                replaced += 1
                self._safe_log(f"  Replaced: {fname}")

            def _done():
                mode = " (fallback: sequential)" if use_fallback else ""
                self.apply_status.configure(
                    text=f"Done: {replaced} replaced, {skipped} skipped{mode}"
                )
                self.log(
                    f"Finished: {replaced} shapes replaced, "
                    f"{skipped} skipped{mode}"
                )

            self.container.after(0, _done)

        except Exception as e:
            self._safe_log(f"Error applying template: {e}")
