# En el archivo run.py

# Importar todo el contenido de la carpeta ffdec
from ffdec import *
import os
from py4j.java_gateway import JavaClass
import re


# Importar todo el contenido de la carpeta swf
from swf import *

import tkinter as tk
from tkinter import filedialog

from ffdec.classes import (IOFile,
                             HashSet,
                             JavaFont,
                             FileInputStream,
                             FileOutputStream,
                             BufferedInputStream,
                             BufferedOutputStream,
                             ByteArrayOutputStream,
                             SWFOutputStream,
                             SwingUtilities2,
                             FontDesignMetrics,
                             SWF,
                             RECT,
                             ImageTag,
                             FontTag,
                             MissingCharacterHandler,
                             ByteArrayRange,
                             As3ScriptReplacerFactory,
                             SymbolClassTag,
                             SpriteExportMode,
                             FrameExportMode,
                             FrameExportSettings,
                             SpriteExportSettings,
                             DefineMorphShapeTag,
                             DefineShapeTags,
                             DefineSpriteTag,
                             DefineSoundTag,
                             DefineEditTextTag,
                             DefineTextTag,
                             CSMTextSettingsTag,
                             DefineFontTag,
                             DefineFont3Tag,
                             DefineFontTags,
                             DefineFontNameTag,
                             DefineFontAlignZonesTag,
                             DefineBitsDefineBitsJPEG2Tag,
                             DefineBitsLosslessTags,
                             DefineBitsLossless2Tag,
                             DefineBinaryDataTag,
                             CharacterRanges,
                             PlaceObjectTags,
                             MetadataTag,
                             AbortRetryIgnoreHandler,
                             ReadOnlyTagList,
                             FrameExporter,
                             SwfOpenException,
                             Tag,
                             CharacterIdTag,
                             CharacterTag)

def get_all_skin_names(swf, level):

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

def export_mod(names, swf, source_swf_name, skin_name):
    output_swf = SWF()  # Assuming SWF is a class or custom data structure
    output_swf.frameRate = 24.0

    print(f"Exporting {len(names)} assets")
    print(f"Nombre de la skin: {skin_name}")
    
    # Find all tags that match the skin name
    matching_tags = []
    for tag in swf.getTags():
        if isinstance(tag, CharacterIdTag):
            exp_name = tag.getExportFileName()
            exp_name = exp_name[exp_name.lastIndexOf("_") + 1:].lower()
            if exp_name == skin_name.lower():
                matching_tags.append(tag)

    # Add the matching tags and their dependencies to the output SWF
    for tag in matching_tags:
        add_tag_and_dependencies(tag, output_swf, swf)

    # Add SymbolClassTags to the output SWF
    for tag in swf.getTags():
        if isinstance(tag, SymbolClassTag):
            output_swf.addTag(tag)

    return output_swf


def add_tag_and_dependencies(tag, output_swf, source_swf):
    # Add the tag to the output SWF
    output_swf.addTag(tag)

    # Get the dependencies of the tag
    dependencies = HashSet()
    tag.getNeededCharactersDeep(dependencies)

    # Add the dependencies to the output SWF
    for dependency in dependencies:
        for source_tag in source_swf.getTags():
            if isinstance(source_tag, CharacterIdTag) and source_tag.getCharacterId() == dependency:
                add_tag_and_dependencies(source_tag, output_swf, source_swf)
                break





def export_skin_mod(skin_code_name, swf):
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
    return Tag.getClassName().substring(0, Tag.getClassName().lastIndexOf("_"))


def set_partname(Tag, new_part_name, part_only):
    if part_only:
        Tag.setClassName(f"{new_part_name}{get_codename(Tag)}")
    else:
        Tag.setClassName(new_part_name)

def get_codename(tag):
    class_name = tag.getClassName()

    if class_name is not None:
        return class_name[class_name.lastIndexOf("_"):]
    
    return None


def get_swf(swf_name, local_location):
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
            fileStream = FileOutputStream(path)
            swf.saveTo(fileStream)
            fileStream.close()



def is_define_shape_any_tag(tag):
    return isinstance(tag, DefineShapeTags)

