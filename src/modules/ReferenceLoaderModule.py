"""
Reference Loader Module
Carga referencias de skins desde archivos XML, muestra nombres reales
usando BrawlhallaLangReader y guarda el resultado como nombre_modded.xml.
"""

from src.utils import get_project_root
import os
import sys
import threading
import customtkinter as ctk
from tkinter import filedialog
from pathlib import Path
from PIL import Image
from .ToolModuleBase import ToolModule
from src.utils.ThemeManager import BMTTheme, ACCENTS

# Paths
LIB_PATH = get_project_root() / "Lib"
ASSETS_PATH = get_project_root() / "resources" / "assets" / "frame0"

if str(LIB_PATH) not in sys.path:
    sys.path.append(str(LIB_PATH))

try:
    import BrawlhallaLangReader  # type: ignore
except ImportError:
    BrawlhallaLangReader = None


class ReferenceLoaderModule(ToolModule):
    """Módulo de Reference Loader con soporte de lenguajes"""

    def __init__(self, parent, game_path, mods_path, icons=None):
        super().__init__(parent, game_path, mods_path, icons=icons)
        self.RefSourcePath = os.path.join(self.game_path, "resources", "data", "reference.swf")
        if not os.path.exists(self.RefSourcePath):
            # Fallback to local if running in BMT root
            self.RefSourcePath = os.path.abspath(os.path.join(get_project_root(), "resources", "data", "reference.swf"))
        self.TargetSourcePath = ""
        self.raw_skin_codes = []      # Technical codes from XML
        self.display_names = []       # Display names for dropdown
        self.code_to_display = {}     # code -> display mapping
        self.display_to_code = {}     # display -> code mapping
        self.folder_icon = None
        self.lang_reader = None

        # Load folder icon
        try:
            fp = ASSETS_PATH / "Folder.png"
            if fp.exists():
                self.folder_icon = ctk.CTkImage(Image.open(fp), size=(20, 20))
        except Exception:
            pass

        # Initialize language reader
        if BrawlhallaLangReader:
            try:
                lang_path = os.path.join(self.game_path, "languages")
                if os.path.exists(lang_path):
                    self.lang_reader = BrawlhallaLangReader.BrawlhallaLangReader(lang_path)
                    self.lang_reader.load_language(1)
                    print("[ReferenceLoader] Language reader initialized")
            except Exception as e:
                print(f"[ReferenceLoader] Language reader error: {e}")

    def get_tool_name(self):
        return "Reference Loader"

    def get_tool_icon(self):
        return ""

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def create_ui(self):
        """Crea la interfaz del Reference Loader."""
        self.container = ctk.CTkFrame(self.parent, fg_color="#0E0E0E")

        main_frame = ctk.CTkFrame(self.container, fg_color="#0E0E0E")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(
            main_frame,
            text="Reference Loader",
        )
        BMTTheme.style_title(title, color=ACCENTS["Reference Loader"])
        title.grid(row=0, column=0, sticky="w", pady=(0, 15))

        # Controls panel
        controls = ctk.CTkFrame(main_frame, fg_color="#171717", corner_radius=10)
        controls.grid(row=1, column=0, sticky="nsew")
        controls.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # ---- Reference SWF ----
        lbl_ref = ctk.CTkLabel(
            controls, text="Reference SWF:",
        )
        BMTTheme.style_subtitle(lbl_ref)
        lbl_ref.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 5))

        ref_frame = ctk.CTkFrame(controls, fg_color="#2C2C2C", corner_radius=8)
        ref_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        ref_frame.grid_columnconfigure(0, weight=1)

        self.ref_path_label = ctk.CTkLabel(
            ref_frame, text=os.path.basename(self.RefSourcePath) if os.path.exists(self.RefSourcePath) else "...", 
            font=BMTTheme.get_font(12), text_color=BMTTheme.WHITE, anchor="w",
        )
        self.ref_path_label.grid(row=0, column=0, sticky="ew", padx=15, pady=10)

        ref_btn = ctk.CTkButton(
            ref_frame,
            text="" if self.folder_icon else "...",
            image=self.folder_icon,
            width=40, height=40,
        )
        BMTTheme.style_primary_button(ref_btn, color=ACCENTS["Reference Loader"])
        ref_btn.configure(command=self.select_reference_path)
        ref_btn.grid(row=0, column=1, padx=10)

        # ---- Target SWF ----
        lbl_dest = ctk.CTkLabel(
            controls, text="Destination SWF:",
        )
        BMTTheme.style_subtitle(lbl_dest)
        lbl_dest.grid(row=2, column=0, sticky="w", padx=20, pady=(10, 5))

        tgt_frame = ctk.CTkFrame(controls, fg_color=BMTTheme.BG_SUBPANEL, corner_radius=BMTTheme.CORNER_RADIUS)
        tgt_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 10))
        tgt_frame.grid_columnconfigure(0, weight=1)

        self.tgt_path_label = ctk.CTkLabel(
            tgt_frame, text="...", 
            font=BMTTheme.get_font(12), text_color=BMTTheme.WHITE, anchor="w",
        )
        self.tgt_path_label.grid(row=0, column=0, sticky="ew", padx=15, pady=10)

        tgt_btn = ctk.CTkButton(
            tgt_frame,
            text="" if self.folder_icon else "...",
            image=self.folder_icon,
            width=40, height=40,
        )
        BMTTheme.style_primary_button(tgt_btn, color=ACCENTS["Reference Loader"])
        tgt_btn.configure(command=self.select_target_path)
        tgt_btn.grid(row=0, column=1, padx=10)

        # ---- Skin Selector ----
        lbl_skin = ctk.CTkLabel(
            controls, text="Skin Selector:",
        )
        BMTTheme.style_subtitle(lbl_skin)
        lbl_skin.grid(row=4, column=0, sticky="w", padx=20, pady=(10, 5))

        self.skin_search_entry = ctk.CTkEntry(
            controls, placeholder_text="Filter skins...",
            font=BMTTheme.get_font(12), fg_color=BMTTheme.BG_SUBPANEL,
            border_width=0, height=32,
        )
        self.skin_search_entry.grid(row=5, column=0, sticky="ew", padx=20, pady=(0, 5))
        self.skin_search_entry.bind("<KeyRelease>", self._on_filter)

        self.skin_selector = ctk.CTkOptionMenu(
            controls, values=["Select Skin"],
            font=BMTTheme.get_font(12), fg_color=BMTTheme.BG_SUBPANEL,
            button_color=ACCENTS["Reference Loader"],
            button_hover_color=BMTTheme.adjust_brightness(ACCENTS["Reference Loader"], -0.2),
            dropdown_fg_color=BMTTheme.BG_SUBPANEL,
            dropdown_hover_color=BMTTheme.BG_DARK,
            height=32,
        )
        self.skin_selector.grid(row=6, column=0, sticky="ew", padx=20, pady=(0, 15))
        self.skin_selector.set("Select Skin")

        # ---- Separator ----
        ctk.CTkFrame(controls, fg_color=BMTTheme.BG_SUBPANEL, height=2).grid(
            row=7, column=0, sticky="ew", padx=20, pady=8
        )

        # ---- Log ----
        lbl_log = ctk.CTkLabel(
            controls, text="Log:",
        )
        BMTTheme.style_subtitle(lbl_log)
        lbl_log.grid(row=8, column=0, sticky="w", padx=20, pady=(8, 3))

        self.log_text = ctk.CTkTextbox(
            controls, font=ctk.CTkFont(size=11),
            fg_color="#0D0D0D", corner_radius=8, height=120,
        )
        self.log_text.grid(row=9, column=0, sticky="nsew", padx=20, pady=(0, 10))
        controls.grid_rowconfigure(9, weight=1)

        # ---- Action button ----
        self.inject_btn = ctk.CTkButton(
            controls, text="Load References",
            height=45,
        )
        BMTTheme.style_primary_button(self.inject_btn, color=ACCENTS["Reference Loader"])
        self.inject_btn.configure(command=self.load_button_clicked)
        self.inject_btn.grid(row=10, column=0, sticky="ew", padx=20, pady=(0, 20))

        self.log("Reference Loader ready")
        return self.container

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def log(self, message):
        if hasattr(self, "log_text"):
            self.log_text.configure(state="normal")
            self.log_text.insert("end", f"{message}\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")

    def _get_display_name(self, code):
        """Translate a technical skin code to a human-readable name."""
        if not code:
            return "Default"
        if not self.lang_reader:
            return code
        try:
            real = self.lang_reader.get_skin_name(code, 1)
            if real and real != code:
                return f"{real}  [{code}]"
        except Exception:
            pass
        return code

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------
    def _on_filter(self, event=None):
        term = self.skin_search_entry.get().strip().lower()
        if not self.display_names:
            return
        if not term:
            values = self.display_names
        else:
            values = [d for d in self.display_names if term in d.lower()]
        self.skin_selector.configure(values=values if values else ["No matches"])

    # ------------------------------------------------------------------
    # XML Loading
    # ------------------------------------------------------------------
    def select_reference_path(self):
        selected = filedialog.askopenfilename(filetypes=[("SWF Files", "*.swf")])
        if selected:
            self.RefSourcePath = selected
            self.ref_path_label.configure(text=os.path.basename(selected))
            self.log(f"Selected Reference: {os.path.basename(selected)}")

    def set_target_path(self, selected):
        self.TargetSourcePath = selected
        self.tgt_path_label.configure(text=os.path.basename(selected))
        self.log(f"Selected Destination: {os.path.basename(selected)}")
        threading.Thread(
            target=self._load_skins_thread, args=(selected,), daemon=True
        ).start()

    def select_target_path(self):
        selected = filedialog.askopenfilename(filetypes=[("SWF Files", "*.swf")])
        if selected:
            self.set_target_path(selected)

    def _load_skins_thread(self, file_path):
        """Parse the Destination SWF and extract unique skin names."""
        self.container.after(0, lambda: self.log("Parsing Destination SWF..."))

        import Methods  # type: ignore
        try:
            swf = Methods.get_swf(file_path, False)
            if not swf:
                self.container.after(0, lambda: self.log("Failed to load SWF."))
                return
                
            tag_dict = {int(tag.getCharacterId()): tag for tag in swf.getTags() if hasattr(tag, "getCharacterId")}
            import re
            symbol_map = {}
            for cid, tag in tag_dict.items():
                if hasattr(tag, "getExportFileName"):
                    en = tag.getExportFileName()
                    if en:
                        en_str = re.sub(r'^(DefineSprite|DefineShape\d*)_\d+_', '', str(en))
                        if en_str not in symbol_map:
                            symbol_map[en_str] = int(cid)
                if "DefineSpriteTag" in tag.__class__.__name__:
                    for ctag in tag.getTags():
                        if "PlaceObject" in ctag.__class__.__name__:
                            try:
                                n = str(ctag.name) if hasattr(ctag, "name") and ctag.name else None
                                if n and hasattr(ctag, "characterId") and int(ctag.characterId) > 0:
                                    symbol_map[n] = int(ctag.characterId)
                            except Exception:
                                pass
                                
            import collections
            skin_counts = collections.Counter()
            for name in symbol_map.keys():
                if name.startswith("a_"):
                    parts = name.split('_')
                    if len(parts) >= 3:
                        skin_counts[parts[-1]] += 1
                        
            # Only keep the ones that actually appeared
            self.raw_skin_codes = [code for code, count in skin_counts.most_common()]
            if self.raw_skin_codes:
                self.container.after(0, lambda: self.log(f"Auto-detected main skin: {self.raw_skin_codes[0]}"))
            
            # Build display names
            self.code_to_display = {}
            self.display_to_code = {}
            for code in self.raw_skin_codes:
                disp = self._get_display_name(code)
                self.code_to_display[code] = disp
                self.display_to_code[disp] = code

            self.display_names = [self.code_to_display[c] for c in self.raw_skin_codes]
            self.container.after(0, self._update_selector)
            
        except Exception as e:
            self.container.after(0, lambda e=e: self.log(f"Error parsing SWF: {e}"))
            
    def _update_selector(self):
        if self.display_names:
            self.skin_selector.configure(values=self.display_names)
            # Auto-select the most common skin
            self.skin_selector.set(self.display_names[0])
            self.log(f"Loaded {len(self.display_names)} skins")
        else:
            self.skin_selector.configure(values=["No skins found"])
            self.log("No skins found in SWF")

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------
    def load_button_clicked(self):
        if not self.RefSourcePath or not os.path.exists(self.RefSourcePath):
            self.log("Select a valid Reference SWF first!")
            return
            
        if not self.TargetSourcePath or not os.path.exists(self.TargetSourcePath):
            self.log("Select a valid Destination SWF first!")
            return

        selected_display = self.skin_selector.get()
        if not selected_display or selected_display in ("Select Skin", "No skins found", "No matches"):
            self.log("Select a skin first!")
            return

        skin_code = self.display_to_code.get(selected_display, selected_display)

        self.log(f"Processing with skin: {skin_code}")
        threading.Thread(
            target=self._process_swf_thread,
            args=(self.RefSourcePath, self.TargetSourcePath, skin_code),
            daemon=True,
        ).start()

    @staticmethod
    def _patch_place_object_bytes(po_tag, new_cid):
        """Patch the characterId in a PlaceObject tag's raw bytes."""
        import jpype
        raw = bytes(po_tag.getData())
        if len(raw) < 3:
            return False
        flags = raw[0]
        has_char = bool(flags & 0x02)
        if not has_char:
            return False
        # characterId is at bytes [3:5] (after flags(1) + depth(2))
        new_bytes = bytearray(raw)
        new_bytes[3] = new_cid & 0xFF
        new_bytes[4] = (new_cid >> 8) & 0xFF
        # Write patched bytes back via SWFInputStream
        try:
            ByteArrayRange = jpype.JClass("com.jpexs.decompiler.flash.types.annotations.ByteArrayRange")
        except Exception:
            ByteArrayRange = None
        try:
            SWFInputStream = jpype.JClass("com.jpexs.decompiler.flash.SWFInputStream")
            java_bytes = jpype.JArray(jpype.JByte)(len(new_bytes))
            for i, b in enumerate(new_bytes):
                java_bytes[i] = jpype.JByte(b if b < 128 else b - 256)
            sis = SWFInputStream(po_tag.getSwf(), java_bytes)
            brange = sis.readByteRangeEx(len(new_bytes), "data")
            po_tag.readData(sis, brange, 0, False, False, False)
            po_tag.setModified(True)
            return True
        except Exception:
            return False

    def _clone_tag_smart(self, src_tag_id, tgt_swf, src_swf, src_tag_dict, used_tgt_ids, cloned_map, skin_suffix, dest_symbol_map):
        if src_tag_id in cloned_map:
            return cloned_map[src_tag_id]
            
        src_tag = src_tag_dict.get(src_tag_id)
        if not src_tag:
            return None
        
        # Allocate a new ID
        new_id = 1
        while new_id in used_tgt_ids:
            new_id += 1
        used_tgt_ids.add(new_id)
        tgt_tag_id = new_id
        
        # Register BEFORE recursion to prevent cycles
        cloned_map[src_tag_id] = tgt_tag_id
        
        tag_class_name = src_tag.__class__.__name__
        
        if "DefineSpriteTag" in tag_class_name:
            import jpype
            DefineSpriteTagClass = jpype.JClass("com.jpexs.decompiler.flash.tags.DefineSpriteTag")
            ShowFrameTagClass = jpype.JClass("com.jpexs.decompiler.flash.tags.ShowFrameTag")
            
            # Step 1: collect PlaceObject data from source sprite
            place_infos = []
            for ctag in src_tag.getTags():
                ctag_class = ctag.__class__.__name__
                if "PlaceObject" in ctag_class:
                    has_char = hasattr(ctag, "placeFlagHasCharacter") and bool(ctag.placeFlagHasCharacter)
                    old_cid = int(ctag.characterId) if has_char else 0
                    name = None
                    try:
                        if hasattr(ctag, "name") and ctag.name:
                            name = str(ctag.name)
                    except Exception:
                        pass
                    try:
                        depth = int(ctag.depth) if hasattr(ctag, "depth") else 0
                    except Exception:
                        depth = 0
                    place_infos.append((ctag, old_cid, name, depth))
            
            # Step 2: pre-clone all non-skin-part deps using getNeededCharactersDeep on the sprite
            try:
                dep_set = jpype.JClass("java.util.HashSet")()
                src_tag.getNeededCharactersDeep(dep_set)
                for dep_id in dep_set:
                    dep_id_int = int(dep_id)
                    if dep_id_int > 0 and dep_id_int not in cloned_map:
                        # Check if it's an a_ skin part
                        is_skin = False
                        for (_, ocid, nm, _) in place_infos:
                            if ocid == dep_id_int and nm and nm.startswith("a_"):
                                parts = nm.split('_')
                                if len(parts) >= 2 and f"{parts[0]}_{parts[1]}_{skin_suffix}" in dest_symbol_map:
                                    is_skin = True
                                    break
                        if not is_skin:
                            self._clone_tag_smart(dep_id_int, tgt_swf, src_swf, src_tag_dict,
                                                  used_tgt_ids, cloned_map, skin_suffix, dest_symbol_map)
            except Exception as dep_err:
                print(f"  [WARN] getNeededCharactersDeep failed for {src_tag_id}: {dep_err}")
            
            # Step 3: build fresh DefineSpriteTag, use byte-patch to set correct characterIds
            new_sprite = DefineSpriteTagClass(tgt_swf)
            new_sprite.setCharacterId(tgt_tag_id)
            
            for (src_ctag, old_cid, name, depth) in place_infos:
                new_po = src_ctag.cloneTag()
                new_po.setSwf(tgt_swf)
                
                if old_cid > 0:
                    new_cid = None
                    if name and name.startswith("a_"):
                        parts = name.split('_')
                        if len(parts) >= 2:
                            target_skin_name = f"{parts[0]}_{parts[1]}_{skin_suffix}"
                            if target_skin_name in dest_symbol_map:
                                new_cid = int(dest_symbol_map[target_skin_name])
                    if new_cid is None:
                        new_cid = cloned_map.get(old_cid)
                    
                    if new_cid is not None:
                        # Try direct field assignment first, then byte patch
                        new_po.characterId = new_cid
                        new_po.setModified(True)
                        print(f"  [REMAP] '{name}' depth={depth}: {old_cid} -> {new_cid}")
                    else:
                        print(f"  [WARN] '{name}' depth={depth}: {old_cid} not mapped")
                
                new_sprite.addTag(new_po)
            
            new_sprite.addTag(ShowFrameTagClass(tgt_swf))
            new_sprite.setModified(True)
            tgt_swf.addTag(new_sprite)
            
        else:
            # For all non-sprite tags: first clone deps, then clone self
            import jpype
            try:
                dep_set = jpype.JClass("java.util.HashSet")()
                src_tag.getNeededCharactersDeep(dep_set)
                for dep_id in dep_set:
                    dep_id_int = int(dep_id)
                    if dep_id_int > 0 and dep_id_int not in cloned_map:
                        self._clone_tag_smart(dep_id_int, tgt_swf, src_swf, src_tag_dict,
                                              used_tgt_ids, cloned_map, skin_suffix, dest_symbol_map)
            except Exception:
                pass
            
            cloned_tag = src_tag.cloneTag()
            cloned_tag.setCharacterId(tgt_tag_id)
            cloned_tag.setSwf(tgt_swf)
            cloned_tag.setModified(True)

            # Step 4: Patch DefineText font references
            is_text = "DefineText" in tag_class_name
            if is_text and hasattr(cloned_tag, "textRecords"):
                print(f"  [FONT] Patching text records for ID {src_tag_id} -> {tgt_tag_id}")
                for rec in cloned_tag.textRecords:
                    try:
                        if hasattr(rec, "fontId") and int(rec.fontId) > 0:
                            old_fid = int(rec.fontId)
                            if old_fid in cloned_map:
                                rec.fontId = cloned_map[old_fid]
                                print(f"    [FONT] Remapped record font: {old_fid} -> {cloned_map[old_fid]}")
                            else:
                                print(f"    [FONT] WARNING: Font {old_fid} not found in cloned_map!")
                    except Exception as e:
                        print(f"    [FONT] Error patching record: {e}")
            
            tgt_swf.addTag(cloned_tag)

            # Step 5: Font Companion Tags (DefineFontNameTag, DefineFontAlignZonesTag, etc.)
            if "DefineFont" in tag_class_name:
                print(f"  [FONT] Cloning companions for Font ID {src_tag_id} -> {tgt_tag_id}")
                found_comp = 0
                for t in src_swf.getTags():
                    t_cls = t.__class__.__name__
                    if "FontName" in t_cls or "FontAlignZones" in t_cls or "FontInfo" in t_cls:
                        fid = -1
                        if hasattr(t, "fontId"): fid = int(t.fontId)
                        elif hasattr(t, "fontID"): fid = int(t.fontID)
                        
                        if fid == src_tag_id:
                            c_tag = t.cloneTag()
                            c_tag.setSwf(tgt_swf)
                            if hasattr(c_tag, "fontId"): c_tag.fontId = tgt_tag_id
                            elif hasattr(c_tag, "fontID"): c_tag.fontID = tgt_tag_id
                            c_tag.setModified(True)
                            tgt_swf.addTag(c_tag)
                            found_comp += 1
                print(f"  [FONT] Found and cloned {found_comp} companions for font {src_tag_id}")
        
        return tgt_tag_id


    def _process_swf_thread(self, ref_path, dest_path, skin_suffix):
        self.container.after(0, lambda: self.log("Parsing SWFs for injection..."))
        import Methods  # type: ignore
        try:
            ref_swf = Methods.get_swf(ref_path, False)
            dest_swf = Methods.get_swf(dest_path, False)
            
            # Build dest_symbol_map
            import re
            dest_symbol_map = {}
            used_tgt_ids = set()
            for tag in dest_swf.getTags():
                cls_name = tag.__class__.__name__
                if 'Define' not in cls_name:
                    continue
                cid = None
                try:
                    if hasattr(tag, "getCharacterId"):
                        cid = int(tag.getCharacterId())
                        used_tgt_ids.add(cid)
                except Exception:
                    pass
                if cid is not None and hasattr(tag, "getExportFileName"):
                    try:
                        en = tag.getExportFileName()
                        if en:
                            en_str = re.sub(r'^(DefineSprite|DefineShape\d*)_\d+_', '', str(en))
                            if en_str not in dest_symbol_map:
                                dest_symbol_map[en_str] = cid
                    except Exception:
                        pass
                if "DefineSpriteTag" in cls_name:
                    for ctag in tag.getTags():
                        if "PlaceObject" in ctag.__class__.__name__:
                            try:
                                n = str(ctag.name) if hasattr(ctag, "name") and ctag.name else None
                                if n and hasattr(ctag, "characterId") and int(ctag.characterId) > 0:
                                    dest_symbol_map[n] = int(ctag.characterId)
                            except Exception:
                                pass

            
            # Build ref_tag_dict - only include DEFINE tags (DefineSpriteTag, DefineShapeTag,
            # DefineTextTag, DefineFontTag, etc.). PlaceObject2Tag also implements CharacterIdTag
            # in this FFDEC version, so isinstance(CharacterIdTag) doesn't work.
            # PlaceObject2Tag.getCharacterId() returns the CHARACTER IT PLACES (not its own ID),
            # causing it to overwrite the actual character definition in the dict.
            ref_tag_dict = {}
            for t in ref_swf.getTags():
                cls = t.__class__.__name__
                if 'Define' in cls and hasattr(t, 'getCharacterId'):
                    try:
                        cid = int(t.getCharacterId())
                        # PREVENT COMPANION TAGS FROM OVERWRITING THE MAIN FONT DEFINITION
                        if cid not in ref_tag_dict or ("FontName" not in cls and "FontAlignZones" not in cls and "FontInfo" not in cls):
                            ref_tag_dict[cid] = t
                    except Exception:
                        pass
            if 90 in ref_tag_dict and "DefineSpriteTag" in ref_tag_dict[90].__class__.__name__:
                ref_sprite = ref_tag_dict[90]
            else:
                max_places = 0
                for tag in ref_swf.getTags():
                    if "DefineSpriteTag" in tag.__class__.__name__:
                        places = sum(1 for t in tag.getTags() if "PlaceObject" in t.__class__.__name__)
                        if places > max_places:
                            max_places = places
                            ref_sprite = tag
                            
            if not ref_sprite:
                self.container.after(0, lambda: self.log("No valid Reference Sprite found in Reference SWF."))
                return
                
            ref_cid = ref_sprite.getCharacterId()
            self.container.after(0, lambda: self.log(f"Found Reference Sprite ID {ref_cid}. Cloning and mapping..."))
            
            # ---------------------------------------------------------------
            # Remove EndTag BEFORE cloning so all addTag() calls insert BEFORE it.
            # addTag() appends to the end of the tag list. If EndTag is present,
            # new shapes/sprites land AFTER it and become invisible to the parser.
            # ---------------------------------------------------------------
            end_tag_obj = None
            for t in dest_swf.getTags():
                if "EndTag" in t.__class__.__name__:
                    end_tag_obj = t
                    break
            if end_tag_obj is not None:
                try:
                    dest_swf.removeTag(end_tag_obj)
                except Exception:
                    end_tag_obj = None
            
            cloned_map = {}
            new_ref_id = self._clone_tag_smart(
                ref_cid, dest_swf, ref_swf, ref_tag_dict, used_tgt_ids, cloned_map, skin_suffix, dest_symbol_map
            )
            
            # Re-add EndTag at the very end
            if end_tag_obj is not None:
                dest_swf.addTag(end_tag_obj)
            
            # ---------------------------------------------------------------
            # CLEANUP: Remove orphaned cloned tags (deps of reference a_ sub-sprites
            # that were cloned by getNeededCharactersDeep but are never referenced
            # because the a_ sub-sprites themselves were remapped to dest skin versions).
            # ---------------------------------------------------------------
            import jpype as _jpype
            cloned_ids = set(cloned_map.values())
            
            # Build set of all character IDs actually referenced in dest_swf
            referenced_ids = set()
            if new_ref_id:
                referenced_ids.add(int(new_ref_id))
            
            for tag in dest_swf.getTags():
                cls_n = tag.__class__.__name__
                if 'Define' in cls_n:
                    try:
                        dep_set = _jpype.JClass("java.util.HashSet")()
                        tag.getNeededCharactersDeep(dep_set)
                        for d in dep_set:
                            referenced_ids.add(int(d))
                    except Exception:
                        pass
                    # DefineText font refs are NOT returned by getNeededCharactersDeep,
                    # so protect them explicitly to avoid removing the font as an orphan.
                    if 'DefineText' in cls_n and hasattr(tag, 'textRecords'):
                        try:
                            for rec in tag.textRecords:
                                if hasattr(rec, 'fontId') and int(rec.fontId) > 0:
                                    referenced_ids.add(int(rec.fontId))
                        except Exception:
                            pass

            # Also add SymbolClass export IDs as "referenced"
            for t in dest_swf.getTags():
                if "SymbolClassTag" in t.__class__.__name__:
                    try:
                        for tag_id in t.tags:
                            referenced_ids.add(int(tag_id))
                    except Exception:
                        pass
            
            # Find cloned tags that are not referenced by anything
            orphaned_ids = cloned_ids - referenced_ids
            tags_to_remove = []
            for t in dest_swf.getTags():
                cls_n = t.__class__.__name__
                if 'Define' in cls_n and hasattr(t, 'getCharacterId'):
                    try:
                        if int(t.getCharacterId()) in orphaned_ids:
                            tags_to_remove.append(t)
                    except Exception:
                        pass
            
            for t in tags_to_remove:
                try:
                    dest_swf.removeTag(t)
                except Exception:
                    pass
            
            if tags_to_remove:
                self.container.after(0, lambda n=len(tags_to_remove): self.log(f"Cleaned up {n} unused reference tags."))
            

            if new_ref_id:
                dest_swf.setModified(True)
                # Export the new sprite so it can be used
                export_name = f"a_Reference_{skin_suffix}"
                
                # Check if SymbolClass needs updating
                symbol_class = None
                for t in dest_swf.getTags():
                    if "SymbolClassTag" in t.__class__.__name__:
                        symbol_class = t
                        break
                        
                if symbol_class:
                    import jpype
                    try:
                        STRING = jpype.JClass("com.jpexs.decompiler.flash.types.STRING")
                    except Exception:
                        # Fallback if the package path is different in some versions
                        try:
                            STRING = jpype.JClass("com.jpexs.decompiler.flash.helpers.STRING")
                        except Exception:
                            STRING = str # Final fallback to python string if class not found
                    
                    try:
                        ArrayList = jpype.JClass("java.util.ArrayList")
                    except Exception:
                        import Methods  # type: ignore
                        ArrayList = Methods.HashSet # HashSet is also often used in FFDEC for tags

                    
                    tags_list = symbol_class.tags
                    names_list = symbol_class.names
                    
                    if hasattr(tags_list, "add") and hasattr(names_list, "add"):
                        import jpype
                        tags_list.add(jpype.java.lang.Integer(new_ref_id))
                        names_list.add(STRING(export_name))
                        symbol_class.setModified(True)
                        self.container.after(0, lambda: self.log(f"Exported injected sprite as {export_name}"))
                
                out_path = dest_path
                
                self.container.after(0, lambda: self.log(f"Saving and overwriting destination SWF..."))
                import jpype
                fos = jpype.java.io.FileOutputStream(out_path)
                dest_swf.saveTo(fos)
                fos.close()
                self.container.after(0, lambda: self.log(f"Job Complete! Overwrote {os.path.basename(out_path)}"))
            else:
                self.container.after(0, lambda: self.log("Failed to clone reference sprite."))
            
        except Exception as e:
            self.container.after(0, lambda e=e: self.log(f"Error processing SWF: {e}"))
