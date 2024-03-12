import json
import sys
from ffdec import *
from swf import *

import subprocess
import tkinter as tk
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import scrolledtext
from tkinter import Scrollbar
from pathlib import Path
import os
from PIL import Image
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage
import customtkinter as ctk
from customtkinter import CTkFrame
from Lib import Methods
from CTkListbox import *


'''
Methods:
def get_all_skin_names(swf, level):
def get_sprites_list(skin_name, swf):
def extract_sprites(skin_name, swf, mode, export_size, swf_name, is_swf, export_folder, mod_path, filter_list_size):
def export_mod(names, swf, source_swf_name, skin_name):
def export_skin_mod(skin_code_name, swf):
def add_modded_sub_tags(all_tags, i, to_swf):
def remove_modded_sub_tags(i, from_swf, removed_tags):
def update_all_class_names(in_swf):
def get_partname(tag):
def set_partname(tag, new_part_name, part_only):
def get_codename(tag):
def get_swf(swf_name, local_location):
def save_swf_to(swf, path):
def is_define_shape_any_tag(tag):
'''

class SpriteExporterPanel(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.SpriteEM = "SWF"
        self.ExportScaleUsed = 1
        self.FilterList = ""
        self.extractorSelectedSwf = None
        self.extractorFilters = []
        self.brawlPathSWF_FC = ""

        self.swfName = ""
        self.gamePathString = ""
        self.modsPathString = ""

        self.extractorFilters = []
        self.extractorFiltersJList = tk.Listbox(self)
        self.extractorFilteredTags = tk.Listbox(self)

        self.GUI()

    def GUI(self):
        ctk.set_appearance_mode("Dark")
        fontsFolder = os.path.join(os.path.dirname(__file__), '..', 'fonts')
        font_path = os.path.join(fontsFolder, "Roboto-Medium.ttf")
        icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'icon.png')


        def relative_to_assets(path: str) -> str:
            return os.path.join(os.path.dirname(__file__), 'assets', 'frame0', path)



        self.title("Brawlhalla Modding Toolkit")

        self.geometry("900x600")
        self.configure(bg = "#0E0E0E")


        #================================================================================================
        # CANVAS
        #================================================================================================

        canvas = Canvas(
            self,
            bg = "#0E0E0E",
            height = 600,
            width = 900,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge"
        )

        canvas.place(x = 0, y = 0)
        canvas.create_rectangle(
            0.0,
            0.0,
            184.0,
            600.0,
            fill="#171717",
            outline="")

        canvas.create_rectangle(
            492.0,
            0.0,
            900.0,
            600.0,
            fill="#171717",
            outline="")

        #================================================================================================

        #================================================================================================
        # TOOLS BUTTONS
        #================================================================================================

        my_font = ctk.CTkFont(font_path, 14, "bold")

        def ColorSwapperTool():
            #Acceder al directorio de la herramienta Color Swapper
            #Es decir el directorio actual
            print("Color Swapper clicked")
            self.ColorSwapperTool = os.path.join(os.path.dirname(__file__), 'ColorSwapperTool.py')
            if os.path.exists(self.ColorSwapperTool):
                messagebox.showwarning("Warning", "This tool is still under development, please make a backup first")
                
                subprocess.Popen(["python", self.ColorSwapperTool])
                messagebox.showinfo("Info", "Step zero: Make a copy of your .xml and .swf files."
                                            "\nThis tool overwrites colors in the .swf file."
                                            "\nFirst step: Export an XML from FFDEC using Export XML."
                                            "\nSecond step: Edit the colors you want."
                                            "\nThird step: Press Replace."
                                            "\nFourth step: Reload with Reload."
                                            "\nFifth step: Go to FFDEC and select Import XML."
                                            "\nSixth step: gg!")
                
        def SkinEditorTool():
            print("Skin Editor clicked")
            #self.SkinEditorTool = os.path.join(os.path.dirname(__file__), 'SkinEditorTool.py')
            #if os.path.exists(self.SkinEditorTool):
            #    subprocess.Popen(["python", self.SkinEditorTool])
            messagebox.showwarning(":c", "This tool is in the Pre-Pre-Pre-Alpha stage, please be patient while the first version is released.")


        def change_image_hover(event, button, hover_image):
            button.configure(image=hover_image)

        def change_image_leave(event, button, original_image):
            button.configure(image=original_image)

        def change_text_color(button, active_color, inactive_color, buttons):
            for btn in buttons:
                if btn == button:
                    btn.configure(fg_color=active_color)
                else:
                    btn.configure(fg_color=inactive_color)

        active_color = '#175DDC'
        inactive_color = '#171717'

        SpriteExporterButtonImage = ctk.CTkImage(Image.open(relative_to_assets("SpriteExporterButtonImage1.png")), size=(17, 17))
        SpriteExporterButtonImage_hover = ctk.CTkImage(Image.open(relative_to_assets("SpriteExporterButtonImage2.png")), size=(17, 17))

        ColorSwapperButtonImage = ctk.CTkImage(Image.open(relative_to_assets("ColorSwapperButtonImage1.png")), size=(17, 17))
        ColorSwapperButtonImage_hover = ctk.CTkImage(Image.open(relative_to_assets("ColorSwapperButtonImage2.png")), size=(17, 17))

        SkinEditorButtonImage = ctk.CTkImage(Image.open(relative_to_assets("SkinEditorButtonImage1.png")), size=(17, 17))
        SkinEditorButtonImage_hover = ctk.CTkImage(Image.open(relative_to_assets("SkinEditorButtonImage2.png")), size=(17, 17)) 


        SpriteExporterButton = ctk.CTkButton(
            self, 
            image=SpriteExporterButtonImage,
            command=lambda: (change_text_color(SpriteExporterButton, active_color, inactive_color,
                            [SpriteExporterButton, ColorSwapperButton, SkinEditorButton]), 
                            print("Sprite Exporter clicked")),
            text="Sprite Exporter",
            font=my_font,
            bg_color='#171717',
            fg_color='#171717',
            hover_color='#175DDC',
            compound="left",
            anchor="w",
            width=164.0,
            height=37.0
        )
        SpriteExporterButton.place(
            x=9.0,
            y=73.0,

        )

        ColorSwapperButton = ctk.CTkButton(
            self,
            image=ColorSwapperButtonImage,
            command=lambda: (change_text_color(ColorSwapperButton, active_color, inactive_color,
                            [SpriteExporterButton, ColorSwapperButton, SkinEditorButton]), 
                            ColorSwapperTool()),
            text="Color Swapper",
            font=my_font,
            bg_color='#171717',
            fg_color='#171717',
            hover_color='#175DDC',
            compound="left",
            anchor="w",   
            width=164.0,
            height=37.0
        )
        ColorSwapperButton.place(
            x=10.0,
            y=122.0,

        )

        SkinEditorButton = ctk.CTkButton(
            self,
            image=SkinEditorButtonImage,
            command=lambda: (change_text_color(SkinEditorButton, active_color, inactive_color,
                            [SpriteExporterButton, ColorSwapperButton, SkinEditorButton]), 
                            SkinEditorTool()),
            text="Skin Editor",
            font=my_font,
            bg_color='#171717',
            fg_color='#171717',
            hover_color='#175DDC',
            compound="left",
            anchor="w",
            width=164.0,
            height=37.0
        )
        SkinEditorButton.place(
            x=11.0,
            y=171.0,

        )

        SpriteExporterButton.bind("<Enter>", lambda event: change_image_hover(event, SpriteExporterButton, SpriteExporterButtonImage_hover))
        SpriteExporterButton.bind("<Leave>", lambda event: change_image_leave(event, SpriteExporterButton, SpriteExporterButtonImage))

        ColorSwapperButton.bind("<Enter>", lambda event: change_image_hover(event, ColorSwapperButton, ColorSwapperButtonImage_hover))
        ColorSwapperButton.bind("<Leave>", lambda event: change_image_leave(event, ColorSwapperButton, ColorSwapperButtonImage))

        SkinEditorButton.bind("<Enter>", lambda event: change_image_hover(event, SkinEditorButton, SkinEditorButtonImage_hover))
        SkinEditorButton.bind("<Leave>", lambda event: change_image_leave(event, SkinEditorButton, SkinEditorButtonImage))

        #================================================================================================



        #================================================================================================
        # FOLDERS BUTTONS
        #================================================================================================

        ModsFolderButtonImage = ctk.CTkImage(
            Image.open(relative_to_assets("ModsFolderButtonImage.png")),
            )

        ModsFolderButton = ctk.CTkButton(
            self,
            image=ModsFolderButtonImage,
            text="",
            width=43,
            height=29,
            anchor="n",
            bg_color='#171717',
            fg_color="#0D0F10",
            hover_color="#000000",
            command=self.select_mods_path
        )

        ModsFolderButton.place(
            x=839,
            y=46
        )

        BrawlhallaFolderButtonImage = ctk.CTkImage(
            Image.open(relative_to_assets("BrawlhallaFolderButtonImage.png")),
            )

        BrawlhallaFolderButton = ctk.CTkButton(
            self,
            image=BrawlhallaFolderButtonImage,
            text="",
            width=43,
            height=29,
            bg_color='#171717',
            fg_color="#0D0F10",
            anchor="n",
            hover_color="#000000",
            command=self.select_brawlhalla_path
                            
        )

        BrawlhallaFolderButton.place(
            x=839.0,
            y=10.0
        )

        #================================================================================================



        #================================================================================================
        # FILTER AND REMOVE FILTER BUTTONS
        #================================================================================================



        ImportSwfButtonImage = ctk.CTkImage(
            Image.open(relative_to_assets("ImportSwfButtonImage.png")),
            )
        ImportSwfButton = ctk.CTkButton(
            self,
            image=ImportSwfButtonImage,
            command=lambda: (print("ImportSwfButton clicked"),
                            self.select_swf()),
            text="",
            bg_color='#171717',
            fg_color='#175DDC',
            hover_color='#1A237E',
            width=40.0,
            height=28.0

        )
        ImportSwfButton.place(
            x=440.0,
            y=10.0,

        )

        RemoveFilterButtonImage = ctk.CTkImage(
            Image.open(relative_to_assets("RemoveFilterButtonImage.png")),
            )
        RemoveFilterButton = ctk.CTkButton(
            self,
            image=RemoveFilterButtonImage,
            command=lambda: print("RemoveFilterButton clicked"),
            text="Remove Filter",
            font=my_font,
            bg_color='#171717',
            fg_color='#B71C1C',
            hover_color='#450A0A',
            width=142.0,
            height=30.0
        )
        RemoveFilterButton.place(
            x=196.0,
            y=553.0,

        )

        def ExportModeActive(button, ExportModeActive_active_color, ExportModeActive_inactive_color, buttons):
            for btn in buttons:
                if btn == button:
                    btn.configure(fg_color=ExportModeActive_active_color)
                else:
                    btn.configure(fg_color=ExportModeActive_inactive_color)

        ExportModeActive_active_color = '#0D0F10'
        ExportModeActive_inactive_color = '#171717'

        self.FolderMode = tk.BooleanVar()
        self.AllMode = tk.BooleanVar()

        #================================================================================================



        #================================================================================================
        # EXPORT BUTTONS
        #================================================================================================


        ExportPngButton = ctk.CTkButton(
            self,
            text="Export PNG",
            font=my_font,
            bg_color='#171717',
            fg_color='#6A1B9A',
            hover_color='#3B0764',
            command=self.export_action_performed,
            width=122.0,
            height=37.0
        )
        ExportPngButton.place(
            x=504.0,
            y=546.0,

        )

        ExportSVGButton = ctk.CTkButton(
            self,
            text="Export SVG",
            font=my_font,
            bg_color='#171717',
            fg_color='#1565C0',
            hover_color='#1E3A8A',
            command=self.export_svg_action_performed,
            width=122.0,
            height=37.0
        )
        ExportSVGButton.place(
            x=635.0,
            y=546.0,

        )

        ExportSWFButton = ctk.CTkButton(
            self,
            text="Export SWF",
            font=my_font,
            bg_color='#171717',
            fg_color='#004D40',
            hover_color='#052E16',
            command=self.exportSWF,
            width=122.0,
            height=37.0
        )
        ExportSWFButton.place(
            x=766.0,
            y=546.0,

        )

        #================================================================================================



        #================================================================================================
        # CANVAS
        #================================================================================================

        canvas.create_rectangle(
            188.0,
            0.0,
            488.0,
            600.0,
            fill="#171717",
            outline="")

        canvas.create_text(
            12.0,
            32.0,
            anchor="nw",
            text="Tools",
            fill="#2C2C2C",
            font=(my_font, 20)
        )

        canvas.create_text(
            505.0,
            89.0,
            anchor="nw",
            text="Log:",
            fill="#2C2C2C",
            font=(my_font, 16)
        )

        canvas.create_rectangle(
            196.0,
            10.0,
            431.0,
            38.0,
            fill="#2C2C2C",
            outline="")

        canvas.create_rectangle(
            504.0,
            47.0,
            827.0,
            73.0,
            fill="#2C2C2C",
            outline="")

        canvas.create_rectangle(
            504.0,
            10.0,
            827.0,
            37.0,
            fill="#2C2C2C",
            outline="")


        self.selectedSwfPath = tk.Label(
            self, 
            text="...", 
            bg="#404040", 
            fg="white",
            font=("my_font", 15 * -1)
            )
        self.selectedSwfPath.place(
            x=196.0,
            y=10.0,
            width=235,
            height=28

        )



        self.modsPathLabel = tk.Label(
            anchor="nw",
            text="Set Mods Folder ->",
            bg="#404040", 
            fg="white",
            font=("my_font", 15 * -1)
        )
        self.modsPathLabel.place(
            x=504,
            y=47,
            width=323,
            height=27
        )

        self.brawlhallaPathLabel = tk.Label(
            anchor="nw",
            text="Set Brawlhalla Folder ->",
            bg="#404040", 
            fg="white",
            font=("my_font", 15 * -1)
        )
        self.brawlhallaPathLabel.place(
            x=504,
            y=10,
            width=323,
            height=27
        )

        #================================================================================================
        # NAMES LIST


        self.namesList = tk.Listbox()
        self.namesList.bind('<Delete>', self.remove_swf_filter)
        self.namesList.configure(
            bg="#0E0E0E",
            fg="#FFFFFF",
            font=("my_font", 12),
            highlightthickness=0,
            borderwidth=0,
            activestyle=tk.NONE,
            selectbackground="#175DDC",
            selectmode="single",
        )

        self.namesList.place(
            x=196.0,
            y=51.0,
            width=254.0,
            height=457.0

        )

        scrollbar = ctk.CTkScrollbar(self)
        scrollbar.place(x=450, y=51)

        # Configurar la lista para que use la barra de desplazamiento
        self.namesList.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.namesList.yview, height=457)

        self.logTextArea = ctk.CTkTextbox(self)
        self.logTextArea.configure(
            width=376, 
            height=185, 
            fg_color="#0E0E0E",
            bg_color="#171717",
            font=("my_font", 12),
            )
        
        self.logTextArea.place(
            x=504.0,
            y=116.0,
        )
        #================================================================================================

        canvas.create_rectangle(
            503.0,
            531.0,
            888.0,
            533.0,
            fill="#2C2C2C",
            outline="")

        canvas.create_rectangle(
            503.0,
            85.0,
            888.0,
            87.0,
            fill="#2C2C2C",
            outline="")

        canvas.create_rectangle(
            196.0,
            555.0,
            229.0,
            581.0,
            fill="#FFFFFF",
            outline="")

        self.load_configuration()

        '''
        self.namesList = tk.Listbox()

        self.namesList.bind('<Delete>', self.remove_swf_filter)  # Para vincular la eliminación con la tecla Delete

        # Definición del renderizador de celdas
        self.namesList.grid(row=10, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
       '''

            


    def configure_gui(self):


        '''
        self.title("Sprite Exporter")
        self.geometry("720x600")
        self.configure(bg="#191919")

        self.selectSwfButton = tk.Button(self, text="Select SWF File", command=self.select_swf)
        self.selectSwfButton.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        self.selectedSwfPath = tk.Label(self, text="...", bg="#404040", fg="white")
        self.selectedSwfPath.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        self.exportButton = tk.Button(self, text="Export", command=self.export)
        self.exportButton.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        self.extractorFiltersJList = tk.Listbox(self, selectmode="multiple")
        self.extractorFiltersJList.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")

        self.extractorFilteredTags = tk.Listbox(self, selectmode="multiple")
        self.extractorFilteredTags.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")

        self.logTextArea = scrolledtext.ScrolledText(self, width=50, height=10, bg="#404040", fg="white")
        self.logTextArea.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")

        export_button_png = tk.Button(self, text="Export PNG", command=self.export_action_performed)
        export_button_png.grid(row=5, column=0, padx=10, pady=5, sticky="ew")

        export_button_svg = tk.Button(self, text="Export SVG", command=self.export_svg_action_performed)
        export_button_svg.grid(row=5, column=1, padx=10, pady=5, sticky="ew")

        self.FolderMode = tk.BooleanVar()
        folder_mode_checkbox = tk.Checkbutton(self, text="Folder Mode", variable=self.FolderMode, command=self.folder_mode_action_performed)
        folder_mode_checkbox.grid(row=6, column=0, padx=10, pady=5, sticky="ew")

        self.AllMode = tk.BooleanVar()
        all_mode_checkbox = tk.Checkbutton(self, text="All Mode", variable=self.AllMode, command=self.all_mode_action_performed)
        all_mode_checkbox.grid(row=6, column=1, padx=10, pady=5, sticky="ew")

        self.selectBrawlhallaPathButton = tk.Button(self, text="Brawlhalla Path", command=self.select_brawlhalla_path)
        self.selectBrawlhallaPathButton.grid(row=7, column=0, padx=10, pady=5, sticky="ew")

        self.selectModsPathButton = tk.Button(self, text="Mods Path", command=self.select_mods_path)
        self.selectModsPathButton.grid(row=7, column=1, padx=10, pady=5, sticky="ew")

        self.brawlhallaPathLabel = tk.Label(self, text="...", bg="#404040", fg="white")
        self.brawlhallaPathLabel.grid(row=8, column=0, padx=10, pady=5, sticky="ew")

        self.modsPathLabel = tk.Label(self, text="...", bg="#404040", fg="white")
        self.modsPathLabel.grid(row=8, column=1, padx=10, pady=5, sticky="ew")

        self.removeSWFFilterButton = tk.Button(self, text="Remove SWF Filter", command=self.remove_swf_filter)
        self.removeSWFFilterButton.grid(row=9, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        self.namesList = tk.Listbox()

        self.namesList.bind('<Delete>', self.remove_swf_filter)  # Para vincular la eliminación con la tecla Delete

        # Definición del renderizador de celdas
        self.namesList.bind("<<ListboxSelect>>", self.update_rendered_list)
        self.namesList.grid(row=10, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")

        self.exportButton = tk.Button(self, text="Export SWF", command=self.exportSWF)
        self.exportButton.grid(row=11, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        self.load_configuration()
        '''
    def select_swf(self):
        if self.gamePathString is None:
            messagebox.showinfo("Brawlhalla Path not set", "Please set Brawlhalla Path.")
            return

        brawlPathSWF_FC = filedialog.askopenfilename(initialdir=self.gamePathString, filetypes=[("SWF files", "*.swf")])

        if brawlPathSWF_FC:
            self.selectedSwfPath.configure(text=brawlPathSWF_FC)

            print("SWF Path: " + brawlPathSWF_FC)
            self.extractorSelectedSwf = Methods.get_swf(brawlPathSWF_FC, False)
            self.swfName = brawlPathSWF_FC.split('/')[-1]

            if self.extractorSelectedSwf is None:
                messagebox.showinfo("Failed to load SWF", "Swf failed to load. Path: " + brawlPathSWF_FC)
            else:
                self.update_filtered_tags_list()

            listNames = Methods.get_all_skin_names(self.extractorSelectedSwf, 0)

            names = list(listNames)
            #Agrega los nombres de las skins a la lista y la inserta en el panel
            self.namesList.delete(0, tk.END)
            for name in names:
                self.namesList.insert(tk.END, name)

            print("Updated!")
            for name in names:
                print(name)

    def update_filtered_tags_list(self):
        pass

    def export(self):
        if not self.extractorSelectedSwf:
            messagebox.showerror("Error", "No SWF file selected.")
            return
        # Lógica de exportación aquí

    def export_action_performed(self):
        self.SpriteEM = "PNG"
        self.ExportScaleUsed = 3
        is_swf = False

        mod_path = self.modsPathString
        export_folder = self.AllMode.get()

        if self.AllMode.get():
            export_folder = False
            self.logTextArea.set("Exporting ALL!")
        if self.FolderMode.get():
            export_folder = True
            self.logTextArea.set("Exporting FOLDERS!")

        print("Exporting!")
        # en el logTextArea agrega el texto que se le pase como argumento
        self.logTextArea.insert("end", "Exporting!\n")

        filter_list_size = len(self.FilterList.split(","))
        print("FilterListSize: " + str(filter_list_size))


        if self.FilterList != "" and self.selectedSwfPath.get() is not None and filter_list_size > 1:
            filter_list_array = self.FilterList.split(",")

            print("FilterListArray: " + self.FilterList)
            selected_swf = Methods.get_swf(self.selectedSwfPath.get(), False)
            try:
                Methods.extract_sprites(self.FilterList, selected_swf, self.SpriteEM, self.ExportScaleUsed,
                                        self.swfName, is_swf, export_folder, mod_path, filter_list_size)
            except RuntimeError as ex:
                # Logger.getLogger(SimpleSpriteExporter.class.getName()).log(Level.SEVERE, null, ex)
                pass

            print("PNG Exported!")
            self.logTextArea.set("PNG Exported!")

            #obtener el elemento seleccionado de la lista


        elif self.namesList.curselection():  # Verifica si hay algún elemento seleccionado en la lista
            selected_index = self.namesList.curselection()[0]  # Obtiene el índice del elemento seleccionado
            selected_name = self.namesList.get(selected_index)  # Obtiene el nombre del elemento seleccionado
            print("Selected name:", selected_name)
            self.logTextArea.insert(tk.END, f"Selected name: {selected_name}\n")
            print("SWF Path: " + self.selectedSwfPath.cget('text'))
            selected_swf = Methods.get_swf(self.selectedSwfPath.cget('text'), False)
            print(selected_name, selected_swf)
            try:
                Methods.extract_sprites(selected_name, selected_swf, self.SpriteEM, self.ExportScaleUsed,
                                        self.swfName, is_swf, export_folder, mod_path, filter_list_size)
            except RuntimeError as ex:
                # Logger.getLogger(SimpleSpriteExporter.class.getName()).log(Level.SEVERE, null, ex)
                pass

            print("PNG Exported!")
            self.logTextArea.insert("end", "PNG Exported!\n")

        else:
            print("Not exported!")
            self.logTextArea.insert("end", "PNG Not exported!\n")


    def export_svg_action_performed(self):
        self.SpriteEM = "SVG"
        self.ExportScaleUsed = 1
        is_swf = False

        mod_path = self.modsPathString
        export_folder = self.AllMode.get()

        if self.AllMode.get():
            export_folder = False
            self.logTextArea.set("Exporting ALL!")
        if self.FolderMode.get():
            export_folder = True
            self.logTextArea.set("Exporting FOLDERS!")

        print("Exporting!")
        self.logTextArea.insert("end", "Exporting!\n")

        filter_list_size = len(self.FilterList.split(","))
        print("FilterListSize: " + str(filter_list_size))

        if self.FilterList != "" and self.selectedSwfPath.get() is not None and filter_list_size > 1:
            filter_list_array = self.FilterList.split(",")

            print("FilterListArray: " + self.FilterList)
            selected_swf = Methods.get_swf(self.selectedSwfPath.get(), False)

            try:
                Methods.extract_sprites(self.FilterList, selected_swf, self.SpriteEM, self.ExportScaleUsed,
                                        self.swfName, is_swf, export_folder, mod_path, filter_list_size)
            except RuntimeError as ex:
                # Logger.getLogger(SimpleSpriteExporter.class.getName()).log(Level.SEVERE, null, ex)
                pass

            print("SVG Exported!")
            self.logTextArea.set("SVG Exported!")

        elif self.namesList.curselection():  # Verifica si hay algún elemento seleccionado en la lista
            selected_index = self.namesList.curselection()[0]  # Obtiene el índice del elemento seleccionado
            selected_name = self.namesList.get(selected_index)  # Obtiene el nombre del elemento seleccionado
            print("Selected name:", selected_name)
            self.logTextArea.insert(tk.END, f"Selected name: {selected_name}\n")
            print("SWF Path: " + self.selectedSwfPath.cget('text'))
            selected_swf = Methods.get_swf(self.selectedSwfPath.cget('text'), False)
            print(selected_name, selected_swf)
            try:
                Methods.extract_sprites(selected_name, selected_swf, self.SpriteEM, self.ExportScaleUsed,
                                        self.swfName, is_swf, export_folder, mod_path, filter_list_size)
            except RuntimeError as ex:
                # Logger.getLogger(SimpleSpriteExporter.class.getName()).log(Level.SEVERE, null, ex)
                pass

            print("SVG Exported!")
            self.logTextArea.insert("end", "SVG Exported!\n")

        else:
            print("Not exported!")
            self.logTextArea.insert("end", "SVG Not Exported!\n")

    def folder_mode_action_performed(self):
        if self.FolderMode.get():
            self.logTextArea.config("Folder Mode")
            self.AllMode.set(False)


    def all_mode_action_performed(self):
        if self.AllMode.get():
            self.logTextArea.config("All Mode")
            self.FolderMode.set(False)


    def select_brawlhalla_path(self):
        selected_directory = filedialog.askdirectory()
        if selected_directory:
            self.gamePathString = selected_directory
            self.brawlhallaPathLabel.config(text=selected_directory)
            self.save_configuration()


    def select_mods_path(self):
        selected_directory = filedialog.askdirectory()
        if selected_directory:
            self.modsPathString = selected_directory
            self.modsPathLabel.config(text=selected_directory)
            self.save_configuration()

    def save_configuration(self):
        config_data = {
            "gamePathString": self.gamePathString,
            "modsPathString": self.modsPathString
        }

        app_folder_path = os.path.join(os.getenv("APPDATA"), "SimpleSpriteExporter")
        if not os.path.exists(app_folder_path):
            os.makedirs(app_folder_path)

        config_file_path = os.path.join(app_folder_path, "config.json")
        with open(config_file_path, "w") as config_file:
            json.dump(config_data, config_file, indent=4)

    def load_configuration(self):
        config_file_path = os.path.join(os.getenv("APPDATA"), "SimpleSpriteExporter", "config.json")
        self.logTextArea.insert("end", "Loading configuration...\n")
        self.logTextArea.insert("end", f"Config file path: {config_file_path}\n")
        if os.path.exists(config_file_path):
            with open(config_file_path, "r") as config_file:
                config_data = json.load(config_file)

            self.gamePathString = config_data.get("gamePathString", "")
            self.modsPathString = config_data.get("modsPathString", "")

            self.brawlhallaPathLabel.config(text=self.gamePathString)
            self.modsPathLabel.config(text=self.modsPathString)
        else:
            messagebox.showwarning("Select Paths", "It's the first time you open SSE.\nPlease select the Brawlhalla and Mods Path.")

    def remove_swf_filter(self, event=None):
        selection = self.extractorFiltersJList.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a filter to remove.")
            return

        selection = list(selection)  # Convertir a lista para evitar problemas con los índices al eliminar
        for index in sorted(selection, reverse=True):
            self.extractorFilters.pop(index)

        self.update_filter_list()
        self.update_filtered_tags_list()

    def exportSWF(self):
        selectedName = self.namesList.get(tk.ACTIVE)
        print("Selected Skin: " + selectedName)
        if self.extractorSelectedSwf is None:
            messagebox.showinfo("No SWF selected", "No SWF Selected")
            return

        swfName = self.selectedSwfPath.cget('text')
        print("SWF Path: " + swfName)
        swfName = swfName.replace(self.gamePathString, '') if self.gamePathString in swfName else os.path.basename(swfName)
        print("SWF Name: " + swfName)
        
        #obtener el elemento seleccionado de la lista
        print("Selected name:", selectedName)
        assetsToExtract = [self.extractorFilteredTags.get(i) for i in self.extractorFilteredTags.curselection()]
        generatedSwf = Methods.export_mod(assetsToExtract, self.extractorSelectedSwf, swfName, selectedName)

        saveChooser = filedialog.asksaveasfile(initialdir=self.modsPathString, filetypes=[("SWF files", "*.swf")])
        if saveChooser:
            savePath = saveChooser.name
            if not savePath.endswith(".swf"):
                savePath += ".swf"

            try:
                Methods.save_swf_to(generatedSwf, savePath)
                messagebox.showinfo("SWF saved successfully", f"SWF saved successfully to {savePath}")
                os.startfile(os.path.dirname(savePath))
            except (FileNotFoundError, IOError) as e:
                messagebox.showerror("Failed to save SWF", "Failed to save SWF")
                print(e)

    def CrearRenderActionPerformed(self):
        # Aquí empieza la implementación del método CrearRenderActionPerformed
        pass
                    


if __name__ == "__main__":
    app = SpriteExporterPanel()
    app.mainloop()     