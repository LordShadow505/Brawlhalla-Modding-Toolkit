import xml.etree.ElementTree as ET
import math
import sys

def load_sprites(filename):
    sprites = {}
    tree = ET.parse(filename)
    root = tree.getroot()
    for item in root.findall('.//item'):
        if item.get('type') == 'DefineSpriteTag':
            sprite_id = int(item.get('spriteId'))
            sub_tags = item.findall('.//subTags/item')
            shape_id = None
            for sub_tag in sub_tags:
                if sub_tag.get('type') == 'PlaceObject2Tag':
                    shape_id = int(sub_tag.get('characterId'))
                    break  # Exit loop after finding the shape ID
            matrix_data = {}
            matrix = sub_tag.find('./matrix')
            if matrix is not None:
                has_rotate = matrix.get('hasRotate')
                rotate_skew0 = int(matrix.get('rotateSkew0'))
                rotate_skew1 = int(matrix.get('rotateSkew1'))
                if has_rotate == "true":
                    angle_rad = math.atan2(rotate_skew1, rotate_skew0)
                    angle_deg = math.degrees(angle_rad)
                else:
                    angle_deg = 0
                matrix_data = {
                    'hasRotate': has_rotate,
                    'rotateAngle': angle_deg,
                    'hasScale': matrix.get('hasScale'),
                    'rotateSkew0': rotate_skew0,
                    'rotateSkew1': rotate_skew1,
                    'scaleX': matrix.get('scaleX'),
                    'scaleY': matrix.get('scaleY'),
                    'translateX': matrix.get('translateX'),
                    'translateY': matrix.get('translateY')
                }
            sprites[sprite_id] = {'shape_id': shape_id, 'matrix_data': matrix_data}
    return sprites

def load_names(filename):
    names = {}
    tree = ET.parse(filename)
    root = tree.getroot()
    for item in root.findall('.//item'):
        if item.get('type') == 'SymbolClassTag':
            tags = [int(tag.text) for tag in item.findall('./tags/item')]
            names_list = [name.text for name in item.findall('./names/item')]
            for tag, name in zip(tags, names_list):
                names[tag] = name
    return names

def load_shape_bounds(filename):
    shape_bounds = {}
    tree = ET.parse(filename)
    root = tree.getroot()
    for item in root.findall('.//item'):
        shape_tag_types = ['DefineShapeTag', 'DefineShape2Tag', 'DefineShape3Tag', 'DefineShape4Tag']
        if item.get('type') in shape_tag_types:
            shape_id = int(item.get('shapeId'))
            shape_bounds_elem = item.find('./shapeBounds')
            if shape_bounds_elem is not None:
                Xmax = int(shape_bounds_elem.get('Xmax'))
                Xmin = int(shape_bounds_elem.get('Xmin'))
                Ymax = int(shape_bounds_elem.get('Ymax'))
                Ymin = int(shape_bounds_elem.get('Ymin'))
                width = abs(Xmax - Xmin)
                height = abs(Ymax - Ymin)
                shape_bounds_data = {
                    'Width': width,
                    'Height': height,
                }
                shape_bounds[shape_id] = shape_bounds_data
    return shape_bounds

def write_to_file(filename, sprites, names, shape_bounds):
    with open(filename, 'w') as f:
        sys.stdout = f
        for sprite_id, data in sprites.items():
            shape_id = data['shape_id']
            matrix_data = data['matrix_data']
            sprite_name = names.get(sprite_id, 'Unknown')
            name = sprite_name.split("_")[1]
            shape_bounds_data = shape_bounds.get(shape_id)
            print(f"{name} {{", file=f)
            #print(f"Name = {sprite_name}", file=f)
            print(f"SpriteID = {sprite_id}", file=f)
            if shape_id is not None:
                print(f"ShapeID = {shape_id}", file=f)
                if shape_bounds_data:
                    for key, value in shape_bounds_data.items():
                        print(f"{key} = {value}", file=f)
            for key, value in matrix_data.items():
                print(f"{key} = {value}", file=f)
            
            print("x = 0", file=f)
            print("y = 0", file=f)
            print("}\n", file=f)

filename = 'swf.xml'

sprites = load_sprites(filename)
names = load_names(filename)
shape_bounds = load_shape_bounds(filename)

write_to_file('output.txt', sprites, names, shape_bounds)
