import re
import xml.etree.ElementTree as ET


symbols = []

def load_symbols(archivoe):
    
    tree = ET.parse(filename)
    root = tree.getroot()
    for item in root.findall('.//item'):
        if item.get('type') == 'SymbolClassTag':
            tags = [int(tag.text) for tag in item.findall('./tags/item')]
            names = [name.text for name in item.findall('./names/item')]
            symbols.extend(zip(tags, names))
    return symbols

filename = 'swf.xml'
symbols = load_symbols(filename)




def obtener_dimensiones_desde_archivo(archivo):
    with open(archivo, 'r') as f:
        contenido = f.read()
    
    matches_shapes = re.findall(r'<item type="DefineShape\d*Tag" forceWriteAsLong="true" shapeId="(\d+)">\s+<shapeBounds type="RECT" Xmax="(-?\d+)" Xmin="(-?\d+)" Ymax="(-?\d+)" Ymin="(-?\d+)"', contenido)
    matches_sprites = re.findall(r'<item type="DefineSpriteTag" forceWriteAsLong="false" frameCount="\d+" hasEndTag="true" spriteId="(\d+)">\s+<subTags>\s+<item type="PlaceObject2Tag" characterId="(\d+)"', contenido)
    
    shape_sprite_mapping = {}  # Mapa para almacenar el mapeo de ShapeID a SpriteID(s)
    for sprite_id, shape_id in matches_sprites: # Mapear cada SpriteID a su ShapeID correspondiente
        if shape_id in shape_sprite_mapping: # Si ya existe una entrada para este ShapeID, agregar el SpriteID a la lista
            shape_sprite_mapping[shape_id].append(sprite_id) 
        else:
            shape_sprite_mapping[shape_id] = [sprite_id]
    
    for match in matches_shapes:
        shape_id = match[0] if match[0] else '0'  # Si el shape_id está vacío, establecerlo como '0'
        xmax = int(match[1])
        xmin = int(match[2])
        ymax = int(match[3])
        ymin = int(match[4])
        
        ancho = xmax - xmin
        alto = abs(ymax - ymin)

            
        
        print("ShapeID:", shape_id, ", Ancho:", ancho, ", Alto:", alto, end=" , ")
        
        # Verificar si hay SpriteIDs correspondientes a este ShapeID
        if shape_id in shape_sprite_mapping:
            sprite_ids = shape_sprite_mapping[shape_id]
            name = next((name for tag, name in symbols if tag == int(sprite_ids[0])), "No encontrado")
            print("Nombre:", name, end=" , ")
            print("SpriteID(s):", ", ".join(sprite_ids))
        else:
            print("SpriteID(s): No encontrado")

# Ejemplo de uso
archivo = "swf.xml"  # Reemplaza "tu_archivo.xml" con la ruta de tu archivo XML
obtener_dimensiones_desde_archivo(archivo)
symbols = load_symbols(archivo)