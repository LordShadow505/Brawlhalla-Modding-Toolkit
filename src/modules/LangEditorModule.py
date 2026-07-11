"""Lang Editor Module – efficient virtual canvas scroll"""
import os, struct, zlib, threading
from tkinter import messagebox, filedialog, messagebox
import tkinter as tk
import customtkinter as ctk

from src.modules.ToolModuleBase import ToolModule
from src.utils.ThemeManager import BMTTheme

ACCENT      = BMTTheme.GREEN
ACCENT_DARK = BMTTheme.adjust_brightness(ACCENT, -0.25)
BG_DARK     = BMTTheme.BG_DARK
BG_PANEL    = BMTTheme.BG_PANEL
BG_SUB      = BMTTheme.BG_SUBPANEL

COL_NUM_W = 58    # # column px
COL_KEY_W = 320   # key column px
ROW_H     = 28    # row height px
OVERSCAN  = 30    # rows rendered above+below viewport

LANG_MAP = {
    1: "EN",
    2: "ZH-T",
    3: "ZH-S",
    4: "FR",
    5: "DE",
    6: "IT",
    7: "JA",
    8: "PT-BR",
    9: "RU",
    10: "ES",
    11: "KO",
    12: "TR",
    13: "ES-LA"
}

def _hex(c):
    return c[1] if isinstance(c,(list,tuple)) else str(c)

# ── binary I/O ─────────────────────────────────────────────────────────────────
def _read_bin(path):
    with open(path,"rb") as f:
        hdr = f.read(4)
        raw = zlib.decompress(f.read())
    off=0; count=struct.unpack(">I",raw[off:off+4])[0]; off+=4
    order=[]; entries={}
    for _ in range(count):
        if off+2>len(raw): break
        kl=struct.unpack(">H",raw[off:off+2])[0]; off+=2
        key=raw[off:off+kl].decode("utf-8","replace"); off+=kl
        if off+2>len(raw): break
        vl=struct.unpack(">H",raw[off:off+2])[0]; off+=2
        val=raw[off:off+vl].decode("utf-8","replace"); off+=vl
        entries[key]=val; order.append(key)
    return {"_header":hdr,"_order":order,"_entries":entries}

def _write_bin(orig, modified, out_path):
    pairs=[(k,modified[k]) for k in orig["_order"] if k in modified]
    payload=struct.pack(">I",len(pairs))
    for k,v in pairs:
        kb=k.encode(); vb=v.encode()
        payload+=struct.pack(">H",len(kb))+kb+struct.pack(">H",len(vb))+vb
    os.makedirs(os.path.dirname(out_path),exist_ok=True)
    with open(out_path,"wb") as f:
        f.write(orig["_header"]); f.write(zlib.compress(payload))

def _safe_destroy(w):
    try: w.destroy()
    except: pass


class LangEditorModule(ToolModule):
    TOOL_NAME="Lang Editor"; ICON_KEY="lang_editor"

    def __init__(self,parent,game_path,mods_path,icons=None):
        super().__init__(parent,game_path,mods_path,icons)
        self._file_path=""
        self._orig={}; self._entries={}; self._modified={}
        self._display_keys=[]; self._key_to_idx={}
        self._order_idx={}
        self._entry_vars={}   # {key: StringVar} – persists forever
        self._visible={}      # {display_idx: {"win":id,"frame":f,"nlbl":l,"klbl":l}}
        self._cw=600          # canvas width
        self._sa=None         # search after-id

    def get_tool_name(self): return self.TOOL_NAME
    def get_tool_icon(self):  return self.icons.get(self.ICON_KEY)

    # ── create_ui ──────────────────────────────────────────────────────────────
    def create_ui(self):
        self.container=ctk.CTkFrame(self.parent,fg_color=BG_DARK)
        self.container.pack(fill="both",expand=True)
        self.container.grid_columnconfigure(1,weight=1)
        self.container.grid_rowconfigure(0,weight=1)
        self._build_left(); self._build_right()

    # ── LEFT ───────────────────────────────────────────────────────────────────
    def _build_left(self):
        p=ctk.CTkFrame(self.container,fg_color=BG_PANEL,width=224,corner_radius=0)
        p.grid(row=0,column=0,sticky="nsew",padx=(0,2)); p.grid_propagate(False)

        hdr=ctk.CTkFrame(p,fg_color=ACCENT,corner_radius=0,height=48)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ctk.CTkLabel(hdr,text="  Language Files", image=BMTTheme.get_icon('book'), compound="left",
                     font=BMTTheme.get_font(13,"bold"),text_color="#fff").pack(side="left",padx=10)

        tb=ctk.CTkFrame(p,fg_color="transparent")
        tb.pack(fill="x",padx=8,pady=(8,4))
        ctk.CTkButton(tb,text="",width=34,height=30,image=BMTTheme.get_icon("refresh"),
                      fg_color=BG_SUB,hover_color=ACCENT,
                      command=self._refresh_list).pack(side="left",padx=(0,4))
        ctk.CTkButton(tb,text="  Browse…",height=30,
                      image=BMTTheme.get_icon("file_open"),compound="left",
                      fg_color=BG_SUB,hover_color=ACCENT,font=BMTTheme.get_font(11),
                      command=self._browse).pack(side="left",fill="x",expand=True)

        self._file_list=ctk.CTkScrollableFrame(p,fg_color=BG_DARK,scrollbar_button_color=ACCENT)
        self._file_list.pack(fill="both",expand=True,padx=6,pady=(0,6))

        cf=ctk.CTkFrame(p,fg_color="#0a0a0a",corner_radius=6)
        cf.pack(fill="x",padx=6,pady=(0,8))
        ctk.CTkLabel(cf,text="Credits",font=BMTTheme.get_font(9,"bold"),text_color=ACCENT).pack(anchor="w",padx=8,pady=(6,2))
        ctk.CTkLabel(cf,text="Python port by Lord Shadow\nBased on WallyLangEditor (C#)",
                     font=BMTTheme.get_font(8),text_color="#777",justify="left").pack(anchor="w",padx=8,pady=(0,8))
        self._refresh_list()

    def _refresh_list(self):
        for w in self._file_list.winfo_children(): _safe_destroy(w)
        folder=self._lang_folder(); bins=[]
        if folder:
            bins=sorted([f for f in os.listdir(folder) if f.lower().endswith(".bin")],key=self._sort_key)
        if not bins:
            ctk.CTkLabel(self._file_list,text="No .bin files found.\nSet Brawlhalla path\nor Browse.",
                         font=BMTTheme.get_font(10),text_color=BMTTheme.GREY,justify="center").pack(pady=20)
            return
        for fname in bins:
            fp = os.path.join(folder, fname)
            num = self._sort_key(fname)
            lang = LANG_MAP.get(num, "")

            btn_f = ctk.CTkFrame(self._file_list, fg_color="transparent")
            btn_f.pack(fill="x", pady=1)

            btn = ctk.CTkButton(btn_f, text=fname, anchor="w", font=BMTTheme.get_font(11), height=32,
                                fg_color="transparent", hover_color=ACCENT, text_color=BMTTheme.WHITE, corner_radius=6,
                                command=lambda p=fp: self._load(p))
            btn.pack(side="left", fill="x", expand=True)

            if lang:
                ll = ctk.CTkLabel(btn_f, text=lang, font=BMTTheme.get_font(9, "bold"),
                                  text_color=ACCENT_DARK, width=60, anchor="e")
                ll.pack(side="right", padx=(0, 8))

    def _sort_key(self,f):
        try: return int(f.replace("language.","").replace(".bin",""))
        except: return 9999

    def _lang_folder(self):
        if self.game_path:
            p=os.path.join(self.game_path,"languages")
            if os.path.isdir(p): return p
        return None

    def _browse(self):
        p=filedialog.askopenfilename(title="Select .bin",filetypes=[("Lang","*.bin"),("All","*.*")])
        if p: self._load(p)

    # ── RIGHT ──────────────────────────────────────────────────────────────────
    def _build_right(self):
        right=ctk.CTkFrame(self.container,fg_color=BG_DARK,corner_radius=0)
        right.grid(row=0,column=1,sticky="nsew")
        right.grid_rowconfigure(3,weight=1); right.grid_columnconfigure(0,weight=1)
        self._right=right

        top=ctk.CTkFrame(right,fg_color=BG_PANEL,height=54,corner_radius=0)
        top.grid(row=0,column=0,sticky="ew"); top.grid_propagate(False)
        top.grid_columnconfigure(1,weight=1)

        self._file_lbl=ctk.CTkLabel(top,text="No file loaded",font=BMTTheme.get_font(13,"bold"),text_color=ACCENT)
        self._file_lbl.grid(row=0,column=0,padx=14,pady=14,sticky="w")
        self._stats_lbl=ctk.CTkLabel(top,text="",font=BMTTheme.get_font(10),text_color=BMTTheme.GREY)
        self._stats_lbl.grid(row=0,column=1,padx=4,sticky="w")

        bf=ctk.CTkFrame(top,fg_color="transparent")
        bf.grid(row=0,column=2,padx=10,sticky="e")
        self._export_btn=ctk.CTkButton(bf,text="  Export .bin",width=120,height=32,
                                       image=BMTTheme.get_icon("save"),compound="left",
                                       fg_color=ACCENT,hover_color=ACCENT_DARK,
                                       font=BMTTheme.get_font(12,"bold"),state="disabled",command=self._export)
        self._export_btn.pack(side="left",padx=(0,6))
        self._clear_btn=ctk.CTkButton(bf,text="Clear Edits",width=100,height=32,
                                      fg_color=BG_SUB,hover_color="#6B2020",
                                      font=BMTTheme.get_font(11),state="disabled",command=self._clear_edits)
        self._clear_btn.pack(side="left")

        self._build_search(right)

        # Fixed column header
        hdr=tk.Frame(right,bg=_hex(BG_PANEL),height=28)
        hdr.grid(row=2,column=0,sticky="ew")
        tk.Label(hdr,text="  #",bg=_hex(BG_PANEL),fg=ACCENT,font=("Segoe UI",9,"bold"),anchor="e"
                 ).place(x=0,y=0,width=COL_NUM_W,height=28)
        tk.Label(hdr,text="  Key",bg=_hex(BG_PANEL),fg=ACCENT,font=("Segoe UI",9,"bold"),anchor="w"
                 ).place(x=COL_NUM_W,y=0,width=COL_KEY_W,height=28)
        tk.Label(hdr,text="  Value",bg=_hex(BG_PANEL),fg=ACCENT,font=("Segoe UI",9,"bold"),anchor="w"
                 ).place(x=COL_NUM_W+COL_KEY_W,y=0)

        # Canvas + scrollbar in a frame
        cvf=tk.Frame(right,bg=_hex(BG_DARK))
        cvf.grid(row=3,column=0,sticky="nsew",padx=(10,0),pady=(0,10))
        cvf.grid_rowconfigure(0,weight=1); cvf.grid_columnconfigure(0,weight=1)

        self._canvas=tk.Canvas(cvf,bg=_hex(BG_DARK),highlightthickness=0,bd=0)
        self._canvas.grid(row=0,column=0,sticky="nsew")

        sb=ctk.CTkScrollbar(cvf,orientation="vertical",command=self._on_sb_scroll,
                             button_color=ACCENT,button_hover_color=ACCENT_DARK)
        sb.grid(row=0,column=1,sticky="ns",padx=(0,10))
        self._sb=sb
        self._canvas.configure(yscrollcommand=sb.set)

        self._canvas.bind("<Configure>",self._on_cfg)
        self._canvas.bind("<MouseWheel>",self._on_wheel)
        self._canvas.bind("<Button-4>",lambda e:self._scroll(-1))
        self._canvas.bind("<Button-5>",lambda e:self._scroll(1))

        self._ph=self._canvas.create_text(300,120,
            text="Load a language file from the left\nor use 'Browse…' to open any .bin.",
            fill=_hex(BMTTheme.GREY),font=("Segoe UI",12),justify="center")

    def _build_search(self,parent):
        bar=ctk.CTkFrame(parent,fg_color=BG_PANEL,height=48,corner_radius=0)
        bar.grid(row=1,column=0,sticky="ew",pady=(2,2)); bar.grid_propagate(False)
        bar.columnconfigure(1,weight=1); bar.columnconfigure(3,weight=1)
        ctk.CTkLabel(bar,text=" Search:", image=BMTTheme.get_icon('search', size=16), compound="left", font=BMTTheme.get_font(11),text_color=BMTTheme.GREY
                     ).grid(row=0,column=0,padx=(12,4),pady=10)
        self._sv=tk.StringVar()
        self._sv.trace_add("write",self._on_search)
        ctk.CTkEntry(bar,textvariable=self._sv,placeholder_text="Search keys or values…",
                     height=28,font=BMTTheme.get_font(11),fg_color=BG_SUB,border_width=0
                     ).grid(row=0,column=1,padx=4,sticky="ew")
        ctk.CTkLabel(bar,text=" Replace:", image=BMTTheme.get_icon('sync_alt', size=16), compound="left", font=BMTTheme.get_font(11),text_color=BMTTheme.GREY
                     ).grid(row=0,column=2,padx=(12,4))
        self._rv=tk.StringVar()
        ctk.CTkEntry(bar,textvariable=self._rv,placeholder_text="Replacement…",
                     height=28,font=BMTTheme.get_font(11),fg_color=BG_SUB,border_width=0
                     ).grid(row=0,column=3,padx=4,sticky="ew")
        ctk.CTkButton(bar,text="Replace All",width=100,height=28,fg_color=BG_SUB,hover_color=ACCENT,
                      font=BMTTheme.get_font(11),command=self._replace_all).grid(row=0,column=4,padx=(4,8))
        self._mod_only=tk.BooleanVar(value=False)
        ctk.CTkCheckBox(bar,text="Edited only",variable=self._mod_only,font=BMTTheme.get_font(10),
                        text_color=BMTTheme.GREY,fg_color=ACCENT,hover_color=ACCENT_DARK,
                        command=self._apply_filter).grid(row=0,column=5,padx=(0,12))

    # ── load ───────────────────────────────────────────────────────────────────
    def _load(self,path):
        self._file_lbl.configure(text="Loading…",text_color=BMTTheme.GREY)
        self.container.update_idletasks()
        def _do():
            try:
                data=_read_bin(path)
                self.container.after(0,lambda:self._on_loaded(path,data))
            except Exception as e:
                msg=str(e)
                self.container.after(0,lambda:self._on_err(msg))
        threading.Thread(target=_do,daemon=True).start()

    def _on_loaded(self,path,data):
        self._file_path=path; self._orig=data
        self._entries=dict(data["_entries"]); self._modified={}
        self._entry_vars={}; self._order_idx={k:i+1 for i,k in enumerate(data["_order"])}
        fname=os.path.basename(path)
        self._file_lbl.configure(text=f"  {fname}",text_color=ACCENT)
        self._stats_lbl.configure(text=f"{len(data['_order'])} entries  |  0 edited",text_color=BMTTheme.GREY)
        self._export_btn.configure(state="normal"); self._clear_btn.configure(state="normal")
        self._sv.set(""); self._update_display(list(data["_order"]))

    def _on_err(self,msg):
        self._file_lbl.configure(text="Error loading file",text_color="#FF5252")
        messagebox.showerror("Load Error",f"Could not read .bin:\n{msg}")

    # ── virtual scroll core ────────────────────────────────────────────────────
    def _update_display(self,keys):
        # clear old rows
        for rd in self._visible.values(): _safe_destroy(rd["frame"])
        self._visible.clear()
        self._display_keys=keys
        self._key_to_idx={k:i for i,k in enumerate(keys)}

        n=len(keys); total_h=max(n*ROW_H,10)
        self._canvas.configure(scrollregion=(0,0,self._cw,total_h))
        self._canvas.yview_moveto(0)

        if keys:
            self._canvas.itemconfigure(self._ph,state="hidden")
        else:
            self._canvas.itemconfigure(self._ph,state="normal")
            return
        self._refresh_vp()

    def _refresh_vp(self):
        n=len(self._display_keys)
        if n==0: return
        total_h=n*ROW_H; ch=self._canvas.winfo_height()
        if ch<2: ch=600
        tf,bf=self._canvas.yview()
        ty=tf*total_h; by=bf*total_h

        first=max(0,int(ty/ROW_H)-OVERSCAN)
        last =min(n-1,int(by/ROW_H)+OVERSCAN)

        # destroy outside range
        for idx in list(self._visible):
            if idx<first or idx>last:
                _safe_destroy(self._visible.pop(idx)["frame"])

        # create missing in range
        for idx in range(first,last+1):
            if idx not in self._visible:
                self._create_row(idx)

    def _create_row(self,di):
        key=self._display_keys[di]
        is_mod=key in self._modified
        bg=_hex(BG_DARK)

        if key not in self._entry_vars:
            var=tk.StringVar(value=self._modified.get(key,self._entries.get(key,"")))
            self._entry_vars[key]=var
            var.trace_add("write",lambda *a,k=key:self._on_var(k))
        else:
            var=self._entry_vars[key]

        frame=tk.Frame(self._canvas,bg=bg,height=ROW_H)

        nlbl=tk.Label(frame,text=str(self._order_idx.get(key,"?")),bg=bg,
                      fg=ACCENT if is_mod else "#555566",font=("Segoe UI",9),anchor="e")
        nlbl.place(x=0,y=0,width=COL_NUM_W,height=ROW_H)

        klbl=tk.Label(frame,text=key,bg=bg,
                      fg=ACCENT if is_mod else _hex(BMTTheme.GREY),font=("Segoe UI",9),anchor="w")
        klbl.place(x=COL_NUM_W,y=0,width=COL_KEY_W,height=ROW_H)

        vx=COL_NUM_W+COL_KEY_W
        ent=tk.Entry(frame,textvariable=var,bg="#18181b",fg=_hex(BMTTheme.WHITE),
                     insertbackground=ACCENT,relief="flat",font=("Segoe UI",9),
                     highlightthickness=0,bd=0)
        ent.place(x=vx,y=3,relwidth=1.0,width=-(vx+14),height=ROW_H-6)

        win=self._canvas.create_window(0,di*ROW_H,window=frame,anchor="nw",width=self._cw)

        # bind wheel on every widget so scrolling works everywhere
        for w in (frame,nlbl,klbl,ent):
            w.bind("<MouseWheel>",self._on_wheel,add="+")
            w.bind("<Button-4>",lambda e:self._scroll(-1),add="+")
            w.bind("<Button-5>",lambda e:self._scroll(1),add="+")

        self._visible[di]={"win":win,"frame":frame,"nlbl":nlbl,"klbl":klbl}

    def _on_sb_scroll(self,*args):
        self._canvas.yview(*args); self._refresh_vp()

    def _on_wheel(self,event):
        self._canvas.yview_scroll(int(-1*(event.delta/120)),"units")
        self._refresh_vp()

    def _scroll(self,n):
        self._canvas.yview_scroll(n,"units"); self._refresh_vp()

    def _on_cfg(self,event):
        self._cw=event.width
        for rd in self._visible.values():
            self._canvas.itemconfig(rd["win"],width=event.width)
        self._canvas.coords(self._ph,event.width//2,120)
        n=len(self._display_keys)
        if n: self._canvas.configure(scrollregion=(0,0,event.width,n*ROW_H))
        self._refresh_vp()

    # ── var change ─────────────────────────────────────────────────────────────
    def _on_var(self,key):
        if not self._entries: return
        nv=self._entry_vars[key].get(); ov=self._entries.get(key,"")
        was=key in self._modified
        if nv!=ov: self._modified[key]=nv; is_mod=True
        else:      self._modified.pop(key,None); is_mod=False
        if was!=is_mod:
            di=self._key_to_idx.get(key)
            if di is not None and di in self._visible:
                rd=self._visible[di]
                try:
                    rd["nlbl"].configure(fg=ACCENT if is_mod else "#555566")
                    rd["klbl"].configure(fg=ACCENT if is_mod else _hex(BMTTheme.GREY))
                except: pass
            self._update_stats()

    # ── search ─────────────────────────────────────────────────────────────────
    def _on_search(self,*_):
        if self._sa:
            try: self.container.after_cancel(self._sa)
            except: pass
        self._sa=self.container.after(300,self._apply_filter)

    def _apply_filter(self):
        if not self._orig: return
        term=self._sv.get().lower(); mo=self._mod_only.get()
        filtered=[]
        for key in self._orig["_order"]:
            if mo and key not in self._modified: continue
            val=self._modified.get(key,self._entries.get(key,""))
            if term and term not in key.lower() and term not in val.lower(): continue
            filtered.append(key)
        self._update_display(filtered)

    def _replace_all(self):
        if not self._orig: return
        s=self._sv.get(); r=self._rv.get()
        if not s: messagebox.showwarning("Replace All","Enter a search term first."); return
        count=0
        for key in self._display_keys:
            cur=self._modified.get(key,self._entries.get(key,""))
            if s in cur:
                new=cur.replace(s,r)
                if new!=self._entries.get(key,""):
                    self._modified[key]=new
                    if key in self._entry_vars: self._entry_vars[key].set(new)
                else:
                    self._modified.pop(key,None)
                    if key in self._entry_vars: self._entry_vars[key].set(self._entries.get(key,""))
                count+=1
        self._update_display(self._display_keys); self._update_stats()
        messagebox.showinfo("Replace All",f"Replaced '{s}' in {count} entries.")

    def _clear_edits(self):
        if not self._modified: return
        if not messagebox.askyesno("Clear Edits","Undo ALL unsaved edits?"): return
        keys=list(self._modified.keys()); self._modified={}
        for k in keys:
            if k in self._entry_vars: self._entry_vars[k].set(self._entries.get(k,""))
        self._apply_filter(); self._update_stats()

    def _update_stats(self):
        n=len(self._orig.get("_order",[])); m=len(self._modified)
        self._stats_lbl.configure(text=f"{n} entries  |  {m} edited",
                                  text_color=ACCENT if m>0 else BMTTheme.GREY)

    def _export(self):
        if not self._file_path: messagebox.showwarning("Export","No file loaded."); return
        if not self._modified: messagebox.showwarning("Export","No edits to export."); return
        out_dir=filedialog.askdirectory(title="Select output folder")
        if not out_dir: return
        fname=os.path.basename(self._file_path)
        out_path=os.path.join(out_dir,"languages",fname)
        final=dict(self._modified)
        if os.path.exists(out_path):
            try:
                ex=_read_bin(out_path); merged=dict(ex["_entries"]); merged.update(self._modified)
                final={k:v for k,v in merged.items() if v!=self._orig["_entries"].get(k)}
            except: pass
        try:
            _write_bin(self._orig,final,out_path)
            messagebox.showinfo("Export",f"Successfully exported {len(final)} entries → languages/{fname}\n\n{out_dir}")
        except Exception as e:
            messagebox.showerror("Export Error",str(e))

