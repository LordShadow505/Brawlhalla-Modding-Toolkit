import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from tkinter import filedialog
import cairosvg
import os
import re
from PIL import Image, ImageTk
import threading

fontsFolder = os.path.join(os.path.dirname(__file__), '..', 'fonts')
font_path = os.path.join(fontsFolder, "Roboto-Medium.ttf")

# Variables globales
folder_path = ""
svg_files = []
sprites_info = {}  # Diccionario para almacenar la información de los sprites

def extract_numeric_part(filename):
    match = re.search(r'_(\d+)_', filename)
    return int(match.group(1)) if match else 0

def open_folder():
    global folder_path
    folder_path = filedialog.askdirectory(parent=root, title="Select a folder", mustexist=True)
    if folder_path:
        initialize_coordinates()
        load_svg_files()
        print("SVG files loaded")

def initialize_coordinates():
    # Verificar si el archivo de coordenadas existe
    coordinates_file = os.path.join(os.path.dirname(__file__), "coordenadas.txt")
    if not os.path.exists(coordinates_file):
        print("Creando archivo de coordenadas...")
        # Crear las coordenadas predeterminadas para cada sprite encontrado en la carpeta
        with open(coordinates_file, mode='w') as file:
            for file_name in os.listdir(folder_path):
                if file_name.endswith('.svg'):
                    sprite_name = file_name.split("_")[3]
                    file.write(f"\n{sprite_name} {{\n")
                    file.write("SpriteID = 0\n")
                    file.write("ShapeID = 0\n")
                    file.write("Width = 0\n")
                    file.write("Height = 0\n")
                    file.write("hasRotate = false\n")
                    file.write("rotateAngle = 0\n")
                    file.write("hasScale = false\n")
                    file.write("rotateSkew0 = 0\n")
                    file.write("rotateSkew1 = 0\n")
                    file.write("scaleX = 0\n")
                    file.write("scaleY = 0\n")
                    file.write("translateX = 0\n")
                    file.write("translateY = 0\n")
                    file.write("x = 300\n")
                    file.write("y = 300\n")
                    file.write("}\n")


def load_svg_files():
    global svg_files
    svg_files = [file for file in os.listdir(folder_path) if file.endswith('.svg')]
    svg_files.sort(key=extract_numeric_part)

    display_svg_files()
    print("SVG files loaded")

def display_svg_files():
    if canvas.winfo_children():
        print("Ya existe el canvas")
        print("Elementos del canvas:", canvas.winfo_children())
        return

    # Crear el lienzo
    sprite_canvas = tk.Canvas(canvas, bg="#191919", highlightthickness=0, width=600, height=600)
    sprite_canvas.pack(fill=tk.BOTH, expand=True)
    
    # Cargar la imagen de fondo y redimensionarla
    background_image = Image.open('Canvas.png')
    background_image = background_image.resize((600, 600), resample=Image.LANCZOS)
    background_photo = ImageTk.PhotoImage(background_image)

    # Agregar la imagen de fondo al lienzo
    sprite_canvas.create_image(0, 0, image=background_photo, anchor=tk.NW)

    # Mantener una referencia a la imagen para evitar que sea eliminada por el recolector de basura
    sprite_canvas.background_photo = background_photo


    for file in svg_files:
        file_path = os.path.join(folder_path, file)
        sprite_name, sprite_info = convert_and_load_svg(file_path, sprite_canvas, rotateAngle=0, translatex=0, translatey=0)
        
        # Verificar si el sprite se pudo cargar
        if sprite_name is not None and sprite_info is not None:
            sprites_info[sprite_name] = sprite_info  # Almacenar información del sprite
            sprite_listbox.insert(tk.END, sprite_name)  # Agregar nombre del sprite a la lista

def display_svg_files2(sprite_name, new_x, new_y, new_r):

        print("Actualizando sprite:", sprite_name, new_x, new_y, new_r)
        sprite_info = sprites_info[sprite_name]
        sprite_id = sprite_info['id']
        sprite_canvas = canvas.winfo_children()[0]
        sprite_canvas.coords(sprite_id, new_x+224, new_y+145)
        sprite_info['x'] = new_x
        sprite_info['y'] = new_y
        sprite_info['rotateAngle'] = new_r
        sprites_info[sprite_name] = sprite_info

        image_path = None

        # Buscar el archivo SVG correspondiente al sprite_name en la carpeta
        for filename in os.listdir(folder_path):
            if f"_{sprite_name}_" in filename:  # Verificar si el nombre del sprite está en el nombre del archivo
                image_path = os.path.join(folder_path, filename)
                break
        
        if image_path:
            update_image(image_path, sprite_canvas, sprite_name, new_r)
        else:
            print(f"No se encontró el archivo SVG para {sprite_name}")



def update_image(image_path, parent_frame, sprite_name, rotation=0):
    try:
        # Convertir SVG a PNG
        temp_png = "temp.png"
        cairosvg.svg2png(url=image_path, write_to=temp_png, scale=2.0, dpi=300)

        # Abrir la imagen PNG
        image = Image.open(temp_png)

        # Obtener las dimensiones de la imagen
        width, height = image.size

        # Calcular el centro de la imagen
        center_x = width / 2
        center_y = height / 2

        # Rotar la imagen desde el centro
        rotated_image = image.rotate(rotation, resample=Image.BICUBIC, expand=True, center=(center_x, center_y))

        # Convertir la imagen rotada a PhotoImage
        photo_image = ImageTk.PhotoImage(rotated_image)


        # Actualizar la imagen en el lienzo
        sprite_info = sprites_info[sprite_name]
        sprite_id = sprite_info['id']
        parent_frame.itemconfig(sprite_id, image=photo_image)

        # Actualizar la referencia al objeto PhotoImage en el diccionario de sprites_info
        sprites_info[sprite_name]['image'] = photo_image

    except Exception as e:
        print("Error cargando SVG:", str(e))




def convert_and_load_svg(file_path, parent_frame, rotateAngle=0, translatex=0, translatey=0):
    try:

        # Convertir SVG a PNG
        temp_png = "temp.png"
        cairosvg.svg2png(url=file_path, write_to=temp_png, scale=2.0, dpi=300)

        # Abrir la imagen PNG
        image = Image.open(temp_png)

        # Rotar la imagen según el ángulo proporcionado
        rotated_image = image.rotate(rotateAngle, resample=Image.BICUBIC)  # Asegurar que la imagen no se corte

        # Convertir la imagen rotada a PhotoImage
        photo_image = ImageTk.PhotoImage(rotated_image)

        sprite_name = file_path.split("_")[3]
        #obtener el tamaño de la imagen en flaot
        imgwidth, imgheight = rotated_image.size


        # Verificar si el nombre del sprite ya está en el diccionario de sprites
        if sprite_name in sprites_info:
            # Si ya existe, agregar un sufijo para diferenciarlo
            sprite_name += f"_{file_path.split('_')[-1].split('.')[0]}"

        with open(os.path.join(os.path.dirname(__file__),"coordenadas.txt")) as file:
            lines = file.readlines()
            found = False

            # Inicializar sprite_info
            sprite_info = {
                'SpriteID': 0,
                'ShapeID': 0,
                'Width': 0,
                'Height': 0,
                'hasRotate': False,
                'rotateAngle': 0,
                'hasScale': False,
                'rotateSkew0': 0,
                'rotateSkew1': 0,
                'scaleX': 0,
                'scaleY': 0,
                'translateX': 0,
                'translateY': 0,
                'x': 300,
                'y': 300
            }

            # Buscar el nombre del sprite en las líneas del archivo
            for i in range(len(lines)):
                if sprite_name in lines[i]:
                    
                    for j in range(i+1, min(i+16, len(lines))):
                        line = lines[j].strip()
                        if line.startswith("SpriteID"):
                            sprite_id = int(line.split("=")[1].strip())
                            sprite_info['id'] = sprite_id

                        elif line.startswith("ShapeID"):
                            shape_id = int(line.split("=")[1].strip())
                            sprite_info['shape_id'] = shape_id

                        elif line.startswith("Width"):
                            width = int(line.split("=")[1].strip())
                            sprite_info['Width'] = width

                        elif line.startswith("Height"):
                            height = int(line.split("=")[1].strip())
                            sprite_info['Height'] = height

                        elif line.startswith("hasRotate"):
                            hasRotate = line.split("=")[1].strip()
                            sprite_info['hasRotate'] = hasRotate

                        elif line.startswith("rotateAngle"):
                            rotateAngle = float(line.split("=")[1].strip())
                            sprite_info['rotateAngle'] = rotateAngle
                            rotated_image = image.rotate(rotateAngle, expand=True)
                            photo_image = ImageTk.PhotoImage(rotated_image)

                        elif line.startswith("hasScale"):
                            hasScale = line.split("=")[1].strip()
                            sprite_info['hasScale'] = hasScale

                        elif line.startswith("rotateSkew0"):
                            rotateSkew0 = float(line.split("=")[1].strip())
                            sprite_info['rotateSkew0'] = rotateSkew0

                        elif line.startswith("rotateSkew1"):
                            rotateSkew1 = float(line.split("=")[1].strip())
                            sprite_info['rotateSkew1'] = rotateSkew1

                        elif line.startswith("scaleX"):
                            scaleX = float(line.split("=")[1].strip())
                            sprite_info['scaleX'] = scaleX

                        elif line.startswith("scaleY"):
                            scaleY = float(line.split("=")[1].strip())
                            sprite_info['scaleY'] = scaleY

                        elif line.startswith("translateX"):
                            translateX = float(line.split("=")[1].strip())
                            sprite_info['translateX'] = translateX

                        elif line.startswith("translateY"):
                            translateY = float(line.split("=")[1].strip())
                            sprite_info['translateY'] = translateY

                        elif line.startswith("x"):
                            x = float(line.split("=")[1].strip())*2
                            sprite_info['x'] = x

                        elif line.startswith("y"):
                            y = float(line.split("=")[1].strip())*2
                            sprite_info['y'] = y

                    found = True
                    break

            scale_x = (sprite_info["Width"]) / imgwidth
            scale_y = (sprite_info["Height"]) / imgheight
            # Si no se encontraron coordenadas para el sprite, agregar el sprite al final del archivo
            if not found:
                with open(os.path.join(os.path.dirname(__file__),"coordenadas.txt"), mode='a') as file:
                    file.write(f"\n{sprite_name} {{\n")
                    file.write("SpriteID = 0\n")
                    file.write("ShapeID = 0\n")
                    file.write("Width = 0\n")
                    file.write("Height = 0\n")
                    file.write("hasRotate = false\n")
                    file.write("rotateAngle = 0\n")
                    file.write("hasScale = false\n")
                    file.write("rotateSkew0 = 0\n")
                    file.write("rotateSkew1 = 0\n")
                    file.write("scaleX = 0\n")
                    file.write("scaleY = 0\n")
                    file.write("translateX = 0\n")
                    file.write("translateY = 0\n")
                    file.write("x = 300\n")
                    file.write("y = 300\n")
                    file.write("}\n")
                    print(f"Sprite {sprite_name} añadido al archivo de coordenadas")

        # Crear el lienzo para el sprite
        sprite_canvas = ctk.CTkCanvas(parent_frame, width=800, height=800, bg="#191919", borderwidth=0)


        #quiero que el background sea la imagen del canvas, debe tener el indice mas bajo y estar
        #en el fondo

        #sprite_id = parent_frame.create_image(224, 145, image=photo_image, anchor=tk.NW)
        sprite_id = parent_frame.create_image(x+224, y+145, image=photo_image, anchor=tk.NW)
        
        #sprite_canvas.image = background_image
        sprite_canvas.image = photo_image

        
        x = sprite_info['x']*scale_x
        y = sprite_info['y']*scale_y
        # Devolver el nombre del sprite, su información y su identificador en el lienzo
        return sprite_name, {
            'id': sprite_id,
            'x': sprite_info['x'], 
            'y': sprite_info['y'], 
            'rotateAngle': sprite_info['rotateAngle'],
            'translateX': sprite_info['translateX'],
            'translateY': sprite_info['translateY']
            }

    except Exception as e:
        print("Error cargando SVG:", str(e))
        return None, None  # Devuelve None para indicar que el sprite no se pudo cargar






def update_sprite_position(sprite_name, new_x, new_y, new_r):
    # Actualizar la posición del sprite en el diccionario de información de sprites
    sprite_info = sprites_info[sprite_name]
    sprite_info['x'] = new_x
    sprite_info['y'] = new_y
    sprite_info['rotateAngle'] = new_r
    sprites_info[sprite_name] = sprite_info


    # Actualizar la posición del sprite en el archivo de texto
    with open(os.path.join(os.path.dirname(__file__),"coordenadas.txt"), mode='r+') as file:
        lines = file.readlines()
        file.seek(0)
        for i, line in enumerate(lines):
            if sprite_name in line:
                #lines[i+14] = f"x = {new_x}\n"  # Usar la clave correcta 'x' en lugar de 'id'
                #lines[i+15] = f"y = {new_y}\n"  # Usar la clave correcta 'y' en lugar de 'id'
                lines[i+6] = f"rotateAngle = {new_r}\n"  # Usar la clave correcta 'rotateAngle' en lugar de 'id'

                break
        file.writelines(lines)
        file.truncate()

    # Actualizar la posición del sprite en el lienzo
    display_svg_files2(sprite_name, new_x, new_y, new_r)

def update_sprite_position_arrows(sprite_name, new_x, new_y, new_r, new_Tx, new_Ty):
    # Actualizar la posición del sprite en el diccionario de información de sprites
    sprite_info = sprites_info[sprite_name]
    sprite_info['x'] = new_x
    sprite_info['y'] = new_y
    sprite_info['translateX'] = new_Tx
    sprite_info['translateY'] = new_Ty
    sprite_info['rotateAngle'] = new_r
    sprites_info[sprite_name] = sprite_info


    # Actualizar la posición del sprite en el archivo de texto
    with open(os.path.join(os.path.dirname(__file__),"coordenadas.txt"), mode='r+') as file:
        lines = file.readlines()
        file.seek(0)
        for i, line in enumerate(lines):
            if sprite_name in line:
                #lines[i+14] = f"x = {new_x/2}\n"  # Usar la clave correcta 'x' en lugar de 'id'
                #lines[i+15] = f"y = {new_y/2}\n"  # Usar la clave correcta 'y' en lugar de 'id'
                #lines[i+6] = f"rotateAngle = {new_r}\n"  # Usar la clave correcta 'rotateAngle' en lugar de 'id'
                lines[i+12] = f"translateX = {new_Tx}\n"  # Usar la clave correcta 'rotateAngle' en lugar de 'id'
                lines[i+13] = f"translateY = {new_Ty}\n"  # Usar la clave correcta 'rotateAngle' en lugar de 'id'
                break
        file.writelines(lines)
        file.truncate()

    # Actualizar la posición del sprite en el lienzo
    display_svg_files2(sprite_name, new_x, new_y, new_r)

def continuous_canvas_update():
    while True:
        root.update_idletasks()
        root.update()

def update_coordinates():
    # Obtener el nombre del sprite seleccionado
    selected_index = sprite_listbox.curselection()[0]
    sprite_name = sprite_listbox.get(selected_index)

    # Obtener las nuevas coordenadas ingresadas por el usuario
    new_x = int(x_entry.get())
    new_y = int(y_entry.get())
    new_r = int(r_entry.get())

    # Actualizar la posición del sprite
    update_sprite_position(sprite_name, new_x, new_y)

root = ctk.CTk()
root.title("Skin Editor Tool")
style = ttk.Style()
style.theme_use('xpnative')
style.configure("Vertical.TScrollbar", background="green", bordercolor="red", arrowcolor="white")

root.state('zoomed')
root.resizable(True, True)

my_font = ctk.CTkFont(font_path, 14, "bold")

# Paneles izquierdo y derecho
left_pane = ctk.CTkFrame(root)
left_pane.pack(side=ctk.LEFT, fill=ctk.BOTH)

# Lista para mostrar los sprites y sus coordenadas
sprite_listbox = tk.Listbox(left_pane, width=50, height=20
                            , font=my_font, bg="#191919", fg="white"
                            , selectbackground="#175DDC", selectforeground="white")
sprite_listbox.pack(side=tk.TOP, padx=10, pady=10)
sprite_listbox.config(exportselection=False)

def on_sprite_select(event):
    # Check if any item is selected in the listbox
    if not sprite_listbox.curselection():
        return

    # Obtener el nombre del sprite seleccionado
    selected_index = sprite_listbox.curselection()[0]
    sprite_name = sprite_listbox.get(selected_index)

    # Obtener las coordenadas del sprite
    sprite_info = sprites_info[sprite_name]
    x = sprite_info['x']
    y = sprite_info['y']
    rotateAngle = sprite_info['rotateAngle']

    # Actualizar las entradas de texto con las coordenadas del sprite
    x_entry.delete(0, tk.END)
    x_entry.insert(0, str(x))
    y_entry.delete(0, tk.END)
    y_entry.insert(0, str(y))
    r_entry.delete(0, tk.END)
    r_entry.insert(0, str(rotateAngle))

    sprite_listbox.config(state=tk.NORMAL)

    # Permitir mover el sprite con las flechas del teclado
    root.bind("<Up>", move_sprite)
    root.bind("<Down>", move_sprite)
    root.bind("<Left>", move_sprite)
    root.bind("<Right>", move_sprite)
    root.bind("<w>", move_sprite)
    root.bind("<s>", move_sprite)
    root.bind("<a>", move_sprite)
    root.bind("<d>", move_sprite)


# Enlazar el evento de selección de la listbox
sprite_listbox.bind('<<ListboxSelect>>', on_sprite_select)

# Entradas de texto para editar las coordenadas
# x label and entry
# Create a new frame for widgets managed by grid
grid_frame = ctk.CTkFrame(left_pane)
grid_frame.pack(fill=tk.BOTH, expand=True)  # Use pack manager for this frame

# x label and entry
x_label = ctk.CTkLabel(grid_frame, text="X:")
x_label.grid(row=0, column=0, padx=(20, 0))

x_entry = ctk.CTkEntry(grid_frame, width=70)
x_entry.grid(row=0, column=1, padx=5)

# y label and entry
y_label = ctk.CTkLabel(grid_frame, text="Y:")
y_label.grid(row=0, column=2)

y_entry = ctk.CTkEntry(grid_frame, width=70)
y_entry.grid(row=0, column=3, padx=5)

# r label and entry
r_label = ctk.CTkLabel(grid_frame, text="R:")
r_label.grid(row=1, column=0, padx=(20, 0))

r_entry = ctk.CTkEntry(grid_frame, width=70)
r_entry.grid(row=1, column=1, padx=5, pady=10)




def update_coordinates(event):
    # Check if any item is selected in the listbox
    #iprime el id del sprite seleccionado en el canvas

    print(canvas.find_withtag("current"))

    if not sprite_listbox.curselection():
        return

    # Obtener el nombre del sprite seleccionado
    selected_index = sprite_listbox.curselection()[0]
    sprite_name = sprite_listbox.get(selected_index)

    # Obtener las nuevas coordenadas ingresadas por el usuario
    new_x = float(x_entry.get())
    new_y = float(y_entry.get())
    new_r = float(r_entry.get())

    # Actualizar la posición del sprite
    update_sprite_position(sprite_name, new_x, new_y, new_r)

# Bind the <KeyRelease> event to the entry fields, ENTER key is pressed
x_entry.bind('<Return>', update_coordinates)
y_entry.bind('<Return>', update_coordinates)
r_entry.bind('<Return>', update_coordinates)

def block_arrow_keys(event):
    # Bloquear las teclas de flecha
    if event.keysym in ["Up", "Down", "Left", "Right"]:
        return "break"  # Evitar que el evento se propague

# Enlace de teclas para bloquear las teclas de flecha en el Listbox
sprite_listbox.bind("<Up>", block_arrow_keys)
sprite_listbox.bind("<Down>", block_arrow_keys)
sprite_listbox.bind("<Left>", block_arrow_keys)
sprite_listbox.bind("<Right>", block_arrow_keys)




def move_sprite(event):
    # Obtener el nombre del sprite seleccionado
    selected_index = sprite_listbox.curselection()
    if not selected_index:
        return

    sprite_index = selected_index[0]
    sprite_name = sprite_listbox.get(sprite_index)

    # Determinar la cantidad de movimiento basado en la tecla presionada
    if event.keysym == "Up" and event.keysym == "Left":
        dx, dy = -1, -1
        tx, ty = -20, -20
    elif event.keysym == "Up" or event.keysym == "w":
        dx, dy = 0, -1
        tx, ty = 0, -20
    elif event.keysym == "Down" or event.keysym == "s":
        dx, dy = 0, 1
        tx, ty = 0, 20
    elif event.keysym == "Left" or event.keysym == "a":
        dx, dy = -1, 0
        tx, ty = -20, 0
    elif event.keysym == "Right" or event.keysym == "d":
        dx, dy = 1, 0
        tx, ty = 20, 0
    else:
        return

    # Obtener la posición actual del sprite
    sprite_info = sprites_info[sprite_name]
    print(sprite_info)
    current_x = sprite_info['x']
    current_y = sprite_info['y']
    current_r = sprite_info['rotateAngle']
    current_Tx = sprite_info['translateX']
    current_Ty = sprite_info['translateY']

    # Calcular la nueva posición del sprite
    new_x = current_x + dx
    new_y = current_y + dy
    new_r = current_r
    new_Tx = current_Tx + tx
    new_Ty = current_Ty + ty

    x_entry.delete(0, tk.END)
    x_entry.insert(0, str(new_x))
    y_entry.delete(0, tk.END)
    y_entry.insert(0, str(new_y))


    # Actualizar la posición del sprite
    update_sprite_position_arrows(sprite_name, new_x, new_y, new_r, new_Tx, new_Ty)

# Enlace de teclas para detectar las teclas de flecha
root.bind("<Up>", move_sprite)
root.bind("<Down>", move_sprite)
root.bind("<Left>", move_sprite)
root.bind("<Right>", move_sprite)
root.bind("<w>", move_sprite)
root.bind("<s>", move_sprite)
root.bind("<a>", move_sprite)
root.bind("<d>", move_sprite)

update_button = ctk.CTkButton(grid_frame, text="Update Coordinates", command=update_coordinates,
                              width=30, height=30, 
                            corner_radius=10, fg_color="#175DDC",
                            font=my_font)
update_button.grid(row=0, column=5, columnspan=10,padx=10, pady=10)

# Agregar imagen de fondo al lienzo
canvas = ctk.CTkCanvas(root, bg="#191919")
canvas.config(background="#191919", highlightthickness=0)
canvas.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True, padx=10, pady=10, ipadx=10, ipady=10)



canvas.config(width=600, height=600)

# Botón para abrir carpeta
open_button = ctk.CTkButton(grid_frame, text="Open SVG Folder", 
                            width=30, height=30, command=open_folder, 
                            corner_radius=10, fg_color="#175DDC",
                            font=my_font)

open_button.grid(row=1, column=5, columnspan=10,padx=10, pady=10)

# Inicializar variables globales
svg_files = []

# Bind events


# Start continuous canvas update thread
canvas_thread = threading.Thread(target=continuous_canvas_update, daemon=True)
canvas_thread.start()

root.mainloop()
