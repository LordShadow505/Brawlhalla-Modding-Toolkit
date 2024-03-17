import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import colorchooser, messagebox, filedialog, ttk
import customtkinter as ctk
from customtkinter import CTkFrame
from PIL import Image
import os
import colorsys
from vcolorpicker import getColor, rgb2hex


# Configuración de la apariencia
ctk.set_appearance_mode("Dark")
fontsFolder = os.path.join(os.path.dirname(__file__), '..', 'fonts')
font_path = os.path.join(fontsFolder, "Roboto-Medium.ttf")
icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'icon.png')
# Función para reemplazar los colores en el archivo XML
def replace_color():
    global tree, colors_new
    for old_color, new_color in colors_new.items():
        for color_node in tree.findall(".//color"):
            color_value = tuple(int(color_node.attrib[attr]) for attr in ('red', 'green', 'blue'))
            if color_value == old_color:
                for attr in ('red', 'green', 'blue'):
                    color_node.attrib[attr] = str(new_color[('red', 'green', 'blue').index(attr)])
    tree.write(rutaarchivo)
    messagebox.showinfo("Success", "Colors replaced successfully")

# Función para seleccionar un color
def select_color(color):
    global selected_color
    selected_color = color
    color_var.set(color)

def ask_color(colors_new):
    
    pick_color = getColor(colors_new) # open the color picker
    pick_color = rgb2hex(pick_color) # convert the color to hex
    pick_color = tuple(int(pick_color[i:i+2], 16) for i in (0, 2, 4))
    return pick_color

def ask_color_all():
    
    pick_color = getColor() # open the color picker
    pick_color = rgb2hex(pick_color) # convert the color to hex
    pick_color = tuple(int(pick_color[i:i+2], 16) for i in (0, 2, 4))
    return pick_color

def edit_color(color_key):
    global colors_new
    print(colors_new[color_key])
    new_color = ask_color(colors_new[color_key])
    
    if new_color:
        colors_new[color_key] = tuple(int(c) for c in new_color)
        update_color_buttons()

# Función para asignar un color a todos los colores
def assign_color_to_all():
    global colors_new
    new_color = ask_color_all()

    if new_color:
        for key in colors_new:
            colors_new[key] = new_color
        update_color_buttons()

def reduce_colors():
    global tree, colors_new
    threshold = 5  # Umbral de variación permitida en RGB

    # Diccionario para almacenar los colores similares y sus promedios
    similar_colors = {}

    # Agrupar los colores similares
    for old_color in colors_old:
        similar_group = [old_color]
        for compare_color in colors_old:
            if old_color != compare_color:
                r_diff = abs(old_color[0] - compare_color[0])
                g_diff = abs(old_color[1] - compare_color[1])
                b_diff = abs(old_color[2] - compare_color[2])
                if r_diff <= threshold and g_diff <= threshold and b_diff <= threshold:
                    similar_group.append(compare_color)
        similar_colors[old_color] = similar_group

    # Calcular el promedio de cada grupo de colores similares
    for old_color, similar_group in similar_colors.items():
        if len(similar_group) > 1:  # Solo se promedian grupos con más de un color
            avg_color = (
                sum(color[0] for color in similar_group) // len(similar_group),
                sum(color[1] for color in similar_group) // len(similar_group),
                sum(color[2] for color in similar_group) // len(similar_group)
            )
            # Reemplazar todos los colores similares por el promedio calculado
            for color in similar_group:
                colors_new[color] = avg_color

    # Actualizar los botones de colores
    update_color_buttons()

# Función para actualizar los botones de colores
def update_color_buttons():
    global colors_frame, colors_old, colors_new
    for widget in colors_frame.winfo_children():
        widget.destroy()
    row = 0
    col = 0
    num_col = 6
    for color_key, color_value in colors_old.items():
        # Creamos un Frame para envolver cada conjunto de colores
        if colors_new[color_key] != color_value:
            border_color = "#16A34A"  # Cambiar el color del borde a amarillo si el color ha sido editado
            frame_bg = "#18181B"  # Cambiar el color del frame a azul si el color ha sido editado
        else:
            border_color = "#000000"  # Mantener el color original del borde
            frame_bg = "#18181B"  # Mantener el color original del frame
        color_frame = tk.Frame(colors_frame, bg=frame_bg, padx=10, pady=10, highlightbackground=border_color, highlightthickness=2)
        color_frame.grid(row=row, column=col, padx=5, pady=5)
        
        def adjust_color_brightness(color_value, factor):
            r, g, b = color_value
            h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            l_adjusted = l + factor if l < 0.5 else l - factor
            r, g, b = colorsys.hls_to_rgb(h, l_adjusted, s)
            return int(r * 255), int(g * 255), int(b * 255)

        old_color_label = tk.Label(color_frame, text="OLD", fg="#%02x%02x%02x" % adjust_color_brightness(color_value, factor=0.4 ), bg="#%02x%02x%02x" % color_value, font=my_font)
        old_color_label.grid(row=0, column=0, padx=0, pady=2)

        new_color_label = tk.Label(color_frame, text="NEW", fg="#%02x%02x%02x" % adjust_color_brightness(colors_new[color_key], factor=0.4 ), bg="#%02x%02x%02x" % colors_new[color_key], font=my_font)
        new_color_label.grid(row=0, column=1, padx=0, pady=2)

        color_button = ctk.CTkButton(color_frame, 
                            fg_color='#%02x%02x%02x' % color_value,
                            text_color="#%02x%02x%02x" % adjust_color_brightness(color_value, factor=0.2 ),
                            hover_color="#%02x%02x%02x" % adjust_color_brightness(color_value, factor=0.1 ),
                            width=20, 
                            height=20,
                            command=lambda key=color_key: edit_color(key),
                            corner_radius=10,
                            text="Edit")

        color_button.grid(row=1, column=0, columnspan=2, padx=2, pady=0)

        col += 1
        if col >= num_col:
            col = 0
            row += 1


# Función para cargar el archivo XML
def load_xml():
    global tree, colors_old, colors_new
    tree = ET.parse(rutaarchivo)
    colors_old = {}
    colors_new = {}
    for color_node in tree.findall(".//color"):
        old_color = tuple(int(color_node.attrib[attr]) for attr in ('red', 'green', 'blue'))
        colors_old[old_color] = old_color
        colors_new[old_color] = old_color
    update_color_buttons()

# Seleccionar archivo XML
rutaarchivo = filedialog.askopenfilename(title="Select the XML", filetypes=[("XML files", "*.xml")])

# Inicialización de variables
selected_color = None
colors_old = {}
colors_new = {}

# Configuración de la ventana principal
root = ctk.CTk()
root.title("Color Swapper Tool")
style=ttk.Style()
style.theme_use('xpnative')
style.configure("Vertical.TScrollbar", background="green", bordercolor="red", arrowcolor="white")
root.state('zoomed')
root.resizable(True, True)
root.geometry("850x600")

my_font = ctk.CTkFont(font_path, 14, "bold")

color_var = tk.StringVar()

# Frame para los botones de reemplazar y cargar XML
replace_frame = tk.Frame(root, bg='#333333')
replace_frame.pack(side="left", padx=10)

# Botón para reemplazar
replace_button = ctk.CTkButton(replace_frame, text="Replace", command=replace_color,  compound="left", fg_color="#BE123C", hover_color="#4C0519")
replace_button.pack(pady=10, padx=5, fill=tk.X)

# Button to load XML
load_button = ctk.CTkButton(replace_frame, text="Reload", command=load_xml,  compound="left", fg_color="#16A34A", hover_color="#052E16")
load_button.pack(pady=10, padx=5, fill=tk.X)

# Button to assign a color to all colors
assign_color_button = ctk.CTkButton(replace_frame, text="Assign color to all", command=assign_color_to_all, compound="left", fg_color="#7E22CE", hover_color="#3B0764")
assign_color_button.pack(pady=10, padx=5, fill=tk.X)

# Button to reduce similar colors
reduce_button = ctk.CTkButton(replace_frame, text="Reduce colors", command=reduce_colors, compound="left", fg_color="#EA580C", hover_color="#7C2D12")
reduce_button.pack(pady=10, padx=5, fill=tk.X)

# Canvas y Scrollbar vertical
canvas = tk.Canvas(root)
scrollbar = ctk.CTkScrollbar(root, command=canvas.yview)
scrollable_frame = tk.Frame(canvas)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(bg='#09090B')  # Fondo oscuro
scrollable_frame.configure(bg='#333333')  # Fondo oscuro para el frame scrollable

scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.configure(yscrollcommand=scrollbar.set)

colors_frame = scrollable_frame  # Ahora los botones se agregarán al frame scrollable_frame

if __name__ == "__main__":
    load_xml()
    root.mainloop()
