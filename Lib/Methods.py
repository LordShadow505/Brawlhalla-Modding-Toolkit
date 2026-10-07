import os
import re
import tkinter as tk
from tkinter import filedialog

# -- Lazy Loading mechanism for FFDEC --
_ffdec_loaded = False

def _init_ffdec():
    global _ffdec_loaded
    if _ffdec_loaded: return
    
    global IOFile, HashSet, JavaFont, FileInputStream, FileOutputStream
    global BufferedInputStream, BufferedOutputStream, ByteArrayOutputStream, SWFOutputStream
    global SwingUtilities2, FontDesignMetrics, SWF, RECT, ImageTag, FontTag
    global MissingCharacterHandler, ByteArrayRange, As3ScriptReplacerFactory, SymbolClassTag
    global SpriteExportMode, ShapeExportMode, FrameExportMode, FrameExportSettings
    global SpriteExportSettings, ShapeExportSettings, DefineMorphShapeTag, DefineShapeTags
    global DefineSpriteTag, DefineShapeTag, DefineShape2Tag, DefineShape3Tag, DefineShape4Tag
    global DefineSoundTag, DefineEditTextTag, DefineTextTag, CSMTextSettingsTag, DefineFontTag
    global DefineFont3Tag, DefineFontTags, DefineFontNameTag, DefineFontAlignZonesTag
    global DefineBitsDefineBitsJPEG2Tag, DefineBitsLosslessTags, DefineBitsLossless2Tag
    global DefineBinaryDataTag, CharacterRanges, PlaceObjectTags, MetadataTag, AbortRetryIgnoreHandler
    global ReadOnlyTagList, FrameExporter, ShapeExporter, SwfOpenException, Tag, CharacterIdTag, CharacterTag
    global java, JArray
    
    import jpype
    from jpype import JArray
    from jpype import java
    from ffdec.classes import (IOFile, HashSet, JavaFont, FileInputStream, FileOutputStream,
                             BufferedInputStream, BufferedOutputStream, ByteArrayOutputStream,
                             SWFOutputStream, SwingUtilities2, FontDesignMetrics, SWF, RECT,
                             ImageTag, FontTag, MissingCharacterHandler, ByteArrayRange,
                             As3ScriptReplacerFactory, SymbolClassTag, SpriteExportMode,
                             ShapeExportMode, FrameExportMode, FrameExportSettings,
                             SpriteExportSettings, ShapeExportSettings, DefineMorphShapeTag,
                             DefineShapeTags, DefineSpriteTag, DefineShapeTag, DefineShape2Tag,
                             DefineShape3Tag, DefineShape4Tag, DefineSoundTag, DefineEditTextTag,
                             DefineTextTag, CSMTextSettingsTag, DefineFontTag, DefineFont3Tag,
                             DefineFontTags, DefineFontNameTag, DefineFontAlignZonesTag,
                             DefineBitsDefineBitsJPEG2Tag, DefineBitsLosslessTags, DefineBitsLossless2Tag,
                             DefineBinaryDataTag, CharacterRanges, PlaceObjectTags, MetadataTag,
                             AbortRetryIgnoreHandler, ReadOnlyTagList, FrameExporter, ShapeExporter,
                             SwfOpenException, Tag, CharacterIdTag, CharacterTag)
    
    _ffdec_loaded = True

def get_all_skin_names(swf, level):
    _init_ffdec()

    if swf is None:
        return None  # Return None if SWF is invalid

    names_found = []

    for Tag in swf.getTags():
        if isinstance(Tag, CharacterIdTag):
            if "DefineSprite" in Tag.getTagName():
                t_name = Tag.getExportFileName()
                if "Shades" not in t_name:
                    # Extract skin name after the last underscore
                    substring_point = t_name.lastIndexOf("_") + 1
                    skin_name = t_name[substring_point:]

                    # Add unique skin name to the list
                    if skin_name not in names_found:
                        names_found.append(skin_name)

    # Print and return the list of skin names
    print("Skin Names Found:", names_found)
    return names_found



def get_sprites_list(skin_name, swf):
    _init_ffdec()
    print("SWF version =", swf.version)
    print("FrameCount =", swf.frameCount)

    name_to_find = skin_name.lower()
    tags_found = []

    for t in swf.getTags():
        if isinstance(t, CharacterIdTag):
            exp_name = t.getExportFileName()
            exp_name = exp_name[exp_name.lastIndexOf("_") + 1:].lower()
            if exp_name == name_to_find:
                tags_found.append(t)
                #print("Tag Found:", t)  # Imprime el objeto completo


    return tags_found

def extract_sprites(skinName, swf, mode, exportSize, swfName, isSWF, ExportFolder, modPath, FilterListSize):
    _init_ffdec()
    print("FilterListSize2:", FilterListSize)
    print("SkinNames Extract:", skinName)

    if mode == "PNG":
        mode = SpriteExportMode.PNG
    elif mode == "SVG":
        mode = SpriteExportMode.SVG

    tagsFound = list()  # Declaración fuera de los bloques if
    
    if swf is not None:
        if FilterListSize == 1:
            nameToFind = skinName
            namesFound = ""
            print("Extracting", nameToFind)

            tagsFound = get_sprites_list(skinName, swf)  # Asignación en el primer bloque if

            print("SWF:", swf)
            print("TagsFound:", tagsFound)
        elif FilterListSize > 1:
            print("FilterListSize > 1:", FilterListSize)
            print("SkinNames Extract:", skinName)

            nameToFind = skinName.split(",")
            tagsFound = list()  # Asignación en el segundo bloque if

            for name in nameToFind:
                tagsFound.addAll(get_sprites_list(name, swf))

            print("SWF:", swf)
            print("TagsFound:", tagsFound)
            print(len(tagsFound), "tags found")

        handler = AbortRetryIgnoreHandler()
        evl = swf.getExportEventListener()
        ses = SpriteExportSettings(mode, exportSize)
        frameExporter = FrameExporter()


        print(len(tagsFound), "tags found")

        root = tk.Tk()
        root.withdraw()

        '''
        No matching overloads found for com.jpexs.decompiler.flash.exporters.FrameExporter.exportSpriteFrames(com.jpexs.decompiler.flash.AbortRetryIgnoreHandler,str,com.jpexs.decompiler.flash.SWF,JInt,int,com.jpexs.decompiler.flash.exporters.settings.SpriteExportSettings,com.jpexs.decompiler.flash.EventListener), options are:
        public java.util.List com.jpexs.decompiler.flash.exporters.          FrameExporter.exportSpriteFrames(com.jpexs.decompiler.flash.AbortRetryIgnoreHandler,java.lang.String,com.jpexs.decompiler.flash.SWF,int,java.util.List,com.jpexs.decompiler.flash.exporters.settings.SpriteExportSettings,com.jpexs.decompiler.flash.EventListener) throws java.io.IOException,java.lang.InterruptedException
        '''

        folder_selected = filedialog.askdirectory(initialdir=modPath, title="Select a folder to save the sprites")
        
        if folder_selected:
            destinationFolder = folder_selected

            if isSWF:
                for t in tagsFound:
                    if isinstance(t, DefineSpriteTag):
                        try:
                
                            frameExporter.exportSpriteFrames(handler, os.path.join(destinationFolder, "Mod_Sprites"), swf, t.getCharacterId(), None, ses, evl)

                        except IOError as e:
                            print(e)
                        except Exception as e:
                            print(e)
            else:
                for t in tagsFound:
                    if ExportFolder:
                        if isinstance(t, DefineSpriteTag):
                            try:
                                frameExporter.exportSpriteFrames(handler, os.path.join(destinationFolder, "Mod_Sprites"), swf, t.getCharacterId(), None, ses, evl)
                            except IOError as e:
                                print(e)
                            except Exception as e:
                                print(e)
                    else:
                        if isinstance(t, DefineSpriteTag):
                            try:
                                


                                frameExporter.exportSpriteFrames(handler, os.path.join(destinationFolder, "Mod_Sprites"), swf, t.getCharacterId(), None, ses, evl)

                                spritesFolder = os.path.join(destinationFolder, "Sprites")
                                if not os.path.exists(spritesFolder):
                                    os.makedirs(spritesFolder)

                                modSpritesFolder = os.path.join(destinationFolder, "Mod_Sprites")

                                subfolders = [subfolder for subfolder in os.listdir(modSpritesFolder) if os.path.isdir(os.path.join(modSpritesFolder, subfolder))]

                                # Si el modo de exportación es PNG, se renombran los archivos a .png
                                if mode == SpriteExportMode.PNG:
                                    for subfolder in subfolders:
                                        pngFiles = [png_file for png_file in os.listdir(os.path.join(modSpritesFolder, subfolder)) if png_file.endswith('.png')]

                                        for i, pngFile in enumerate(pngFiles):
                                            oldPngPath = os.path.join(modSpritesFolder, subfolder, pngFile)
                                            fileName = f"{subfolder}_{i+1}.png"
                                            newPngPath = os.path.join(spritesFolder, fileName)
                                            os.rename(oldPngPath, newPngPath)

                                    for root, dirs, files in os.walk(modSpritesFolder, topdown=False):
                                        for name in files:
                                            os.remove(os.path.join(root, name))
                                        for name in dirs:
                                            os.rmdir(os.path.join(root, name))

                                if mode == SpriteExportMode.SVG:
                                    for subfolder in subfolders:
                                        svgFiles = [svg_file for svg_file in os.listdir(os.path.join(modSpritesFolder, subfolder)) if svg_file.endswith('.svg')]

                                        for i, svgFile in enumerate(svgFiles):
                                            oldSvgPath = os.path.join(modSpritesFolder, subfolder, svgFile)
                                            fileName = f"{subfolder}_{i+1}.svg"
                                            newSvgPath = os.path.join(spritesFolder, fileName)
                                            os.rename(oldSvgPath, newSvgPath)

                                    for root, dirs, files in os.walk(modSpritesFolder, topdown=False):
                                        for name in files:
                                            os.remove(os.path.join(root, name))
                                        for name in dirs:
                                            os.rmdir(os.path.join(root, name))

                            except (IOError, Exception) as e:
                                print(e)

                print("Sprites exported to", destinationFolder)
        else:
            print("Export cancelled by user")

def extract_shapes(swf, export_format="SVG", export_folder=None):
    _init_ffdec()
    """
    Extrae todas las shapes (formas) de un archivo SWF y las exporta en SVG.
    """
    if not swf:
        print("No SWF file provided.")
        return

    if export_format.upper() != "SVG":
        print("Solo se admite la exportación en SVG.")
        return

    shape_tags = [tag for tag in swf.getTags() if isinstance(tag, (DefineShapeTag, DefineShape2Tag, DefineShape3Tag, DefineShape4Tag))]
    
    print(f"Encontradas {len(shape_tags)} shapes.")
    if not shape_tags:
        print("No hay shapes para exportar.")
        return

    shape_exporter = ShapeExporter()
    ses = ShapeExportSettings(ShapeExportMode.SVG, 1.0)

    if not export_folder:
        root = tk.Tk()
        root.withdraw()
        export_folder = filedialog.askdirectory(title="Selecciona una carpeta para exportar las shapes")

    if not export_folder:
        print("Exportación cancelada por el usuario.")
        return

    os.makedirs(export_folder, exist_ok=True)

    # Crear la lista Java ArrayList a partir de la lista Python de shape_tags
    java_tags = java.util.ArrayList()
    for tag in shape_tags:
        java_tags.add(tag)

    # Exportar cada shape
    for shape_tag in shape_tags:
            output_path = os.path.join(export_folder)

            # Usar la lista Java en ReadOnlyTagList
            readonly_tags = ReadOnlyTagList(java_tags)  # Pasar la lista Java correctamente
            svg_content = shape_exporter.exportShapes(None, export_folder, swf, readonly_tags, ses, None, 1.0)




def export_mod(names, swf, source_swf_name, skin_name):
    _init_ffdec()
    output_swf = SWF()
    output_swf.frameRate = 24.0

    print(f"Exporting {len(names)} assets")
    print(f"Nombre de la skin: {skin_name}")
    
    # Construir un diccionario de characterId a tag
    char_id_to_tag = {}
    for tag in swf.getTags():
        if isinstance(tag, CharacterIdTag):
            char_id_to_tag[tag.getCharacterId()] = tag

    # Encontrar los tags que coinciden con el nombre de la skin
    matching_tags = []
    for tag in swf.getTags():
        if isinstance(tag, CharacterIdTag):
            exp_name = tag.getExportFileName()
            if exp_name is not None:
                exp_name = exp_name[exp_name.lastIndexOf("_") + 1:].lower()
                if exp_name == skin_name.lower():
                    matching_tags.append(tag)

    # Conjunto de IDs de caracteres ya agregados
    added_char_ids = set()

    # Procesar cada tag coincidente
    for tag in matching_tags:
        add_tag_and_dependencies(tag, output_swf, swf, char_id_to_tag, added_char_ids)

    # Agregar los SymbolClassTags
    for tag in swf.getTags():
        if isinstance(tag, SymbolClassTag):
            output_swf.addTag(tag)

    return output_swf


def add_tag_and_dependencies(tag, output_swf, source_swf, char_id_to_tag, added_char_ids):
    _init_ffdec()
    char_id = tag.getCharacterId()
    
    # Si ya hemos agregado este char_id, no hacer nada
    if char_id in added_char_ids:
        return
    
    # Agregar el tag actual
    output_swf.addTag(tag)
    added_char_ids.add(char_id)
    
    # Obtener las dependencias
    dependencies = HashSet()
    tag.getNeededCharactersDeep(dependencies)
    
    # Procesar cada dependencia
    for dependency in dependencies:
        if dependency in char_id_to_tag:
            dep_tag = char_id_to_tag[dependency]
            add_tag_and_dependencies(dep_tag, output_swf, source_swf, char_id_to_tag, added_char_ids)


def export_skin_mod(skin_code_name, swf):
    _init_ffdec()
    all_tags = swf.getTags()

    output_swf = SWF()
    output_swf.frameRate = 24.0

    for i in range(len(all_tags)):
        if isinstance(all_tags[i], DefineSpriteTag):
            codename = get_codename(all_tags[i])
            if codename is not None and codename.lower() == skin_code_name.lower():
                output_swf.addTag(all_tags[i])
                print("A:", all_tags[i].getClassName())
                add_modded_sub_tags(all_tags, i, output_swf)

        if isinstance(all_tags[i], SymbolClassTag):
            output_swf.addTag(all_tags[i])

    return output_swf


def add_modded_sub_tags(all_tags, i, to_swf):
    _init_ffdec()
    needed = set()
    all_tags[i].getNeededCharactersDeep(needed)
    needed_array = list(needed)

    need_debug = []

    for n in needed_array:
        need_debug.append(n)

    for n in needed_array:
        for a in range(len(all_tags)):
            if isinstance(all_tags[a], CharacterIdTag) and all_tags[a].getCharacterId() == n:
                if to_swf.getTags().index(all_tags[a]) == -1:
                    to_swf.addTag(all_tags[a])
                    break

def remove_modded_sub_tags(i, from_swf, removed_tags):
    _init_ffdec()
    total_removed = 0

    all_tags = from_swf.getTags()
    needed = set()
    start_tag = all_tags[i]
    start_tag.getNeededCharactersDeep(needed)

    needed_array = list(needed)

    for n in needed_array:
        if n not in removed_tags:
            removed_tags.append(n)

            for a in range(len(all_tags)):
                if isinstance(all_tags[a], CharacterIdTag) and all_tags[a].getCharacterId() == n:
                    if isinstance(all_tags[a], DefineSpriteTag):
                        total_removed += remove_modded_sub_tags(a, from_swf, removed_tags)
                    else:
                        from_swf.removeTag(all_tags[a])
                        total_removed += 1

    from_swf.removeTag(start_tag)

    return total_removed


def update_all_class_names(in_swf):
    _init_ffdec()
    all_tags = in_swf.getTags()
    symbol_class = None

    for i in range(len(all_tags)):
        if isinstance(all_tags[i], SymbolClassTag):
            symbol_class = all_tags[i]
            all_tags[i].setModified(True)

    if symbol_class is None:
        return False

    for i in range(len(symbol_class.names)):
        for s in range(len(all_tags)):
            if isinstance(all_tags[s], DefineSpriteTag) and all_tags[s].spriteId == symbol_class.tags[i]:
                symbol_class.names[i] = all_tags[s].getClassName()

    return True


def get_partname(Tag):
    _init_ffdec()
    return Tag.getClassName().substring(0, Tag.getClassName().lastIndexOf("_"))


def set_partname(Tag, new_part_name, part_only):
    _init_ffdec()
    if part_only:
        Tag.setClassName(f"{new_part_name}{get_codename(Tag)}")
    else:
        Tag.setClassName(new_part_name)

def get_codename(tag):
    _init_ffdec()
    class_name = tag.getClassName()

    if class_name is not None:
        return class_name[class_name.lastIndexOf("_"):]
    
    return None


def get_swf(swf_name, local_location):
    _init_ffdec()
    swf_path = swf_name if not local_location else swf_name

    try:
        print("Opening " + swf_path)
        fileStream = FileInputStream(swf_path)
        swf = SWF(BufferedInputStream(fileStream), True)
        fileStream.close()
        return swf
    
    except SwfOpenException:
        print("ERROR: Invalid SWF file")


    return None



def save_swf_to(swf, path):
    _init_ffdec()
    fileStream = FileOutputStream(path)
    swf.saveTo(fileStream)
    fileStream.close()



def is_define_shape_any_tag(tag):
    _init_ffdec()
    return isinstance(tag, DefineShapeTags)

