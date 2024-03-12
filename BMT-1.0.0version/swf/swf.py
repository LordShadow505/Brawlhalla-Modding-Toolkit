import os
import re
import hashlib
from .metadataclass import MetadataClass
from .symbolclass import SymbolClass
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
                             SwfOpenException,
                             Tag,
                             CharacterIdTag,
                             CharacterTag)


__all__ = ["GetElementId",
           "SetElementId",
           "GetShapeBitmapId",
           "SetShapeBitmapId",
           "GetShapeBitmap",
           "GetElementHash",
           "GetNeededCharactersId",
           "GetNeededCharacters",
           "GetSwfByElement",
           "Swf"]


def GetSwfByElement(element):
    swf: Swf = Swf.byJavaSwf(element.getSwf())
    return swf


def GetElementId(element):
    elType = type(element)
    elId = -1

    if elType in DefineShapeTags:
        elId = element.shapeId

    elif elType == DefineMorphShapeTag:
        elId = element.characterId

    elif elType == DefineSpriteTag:
        elId = element.spriteId

    elif elType == DefineSoundTag:
        elId = element.soundId

    elif elType == DefineTextTag:
        elId = element.characterID

    elif elType == DefineEditTextTag:
        elId = element.characterID

    elif elType == CSMTextSettingsTag:
        elId = element.textID

    elif elType == DefineFontTag:
        elId = element.fontId

    elif elType in DefineFontTags:
        elId = element.fontID

    elif elType == DefineFontNameTag:
        elId = element.fontId

    elif elType == DefineFontAlignZonesTag:
        elId = element.fontID

    elif elType in DefineBitsLosslessTags:
        elId = element.characterID

    elif elType == DefineBinaryDataTag:
        elId = element.tag

    elif elType in PlaceObjectTags:
        elId = element.characterId

    elif elType == CharacterIdTag:
        elId = element.characterId

    elif elType == CharacterTag:
        elId = element.characterId



    elId = int(elId)

    if elId > 0:
        return elId


def SetElementId(element, elId: int):
    elType = type(element)

    if elType in DefineShapeTags:
        element.shapeId = elId

    elif elType == DefineMorphShapeTag:
        element.characterId = elId

    elif elType == DefineSpriteTag:
        element.spriteId = elId

    elif elType == DefineSoundTag:
        element.soundId = elId

    elif elType == DefineTextTag:
        element.characterID = elId

    elif elType == DefineEditTextTag:
        element.characterID = elId

    elif elType == CSMTextSettingsTag:
        element.textID = elId

    elif elType == DefineFontTag:
        element.fontId = elId
        element.characterID = elId

    elif elType in DefineFontTags:
        element.fontID = elId

    elif elType == DefineFontNameTag:
        element.fontId = elId

    elif elType == DefineFontAlignZonesTag:
        element.fontID = elId

    elif elType in DefineBitsLosslessTags:
        element.characterID = elId

    elif isinstance(element, PlaceObjectTags):
        element.characterId = elId

    element.setModified(True)

    return element


def GetShapeBitmapId(shape):
    if isinstance(shape, DefineShapeTags):
        shape.getShapes()

        if (
                hasattr(shape, "shapes") and
                hasattr(shape.shapes, "fillStyles") and
                hasattr(shape.shapes.fillStyles, "fillStyles") and
                len(shape.shapes.fillStyles.fillStyles) == 1 and
                shape.shapes.fillStyles.fillStyles[0].fillStyleType == 64
        ):
            return shape.shapes.fillStyles.fillStyles[0].bitmapId

    return None


def SetShapeBitmapId(shape, bitmapId):
    oldBitmapId = GetShapeBitmapId(shape)

    if oldBitmapId is not None and oldBitmapId != bitmapId:
        shape.shapes.fillStyles.fillStyles[0].bitmapId = bitmapId
        shape.setModified(True)

        return True
    else:
        return False


def GetShapeBitmap(shape):
    bitmapId = GetShapeBitmapId(shape)

    if bitmapId is None:
        return None

    bitmap = GetSwfByElement(shape).getElementById(bitmapId, DefineBitsLossless2Tag)

    if bitmap:
        return bitmap[0]
    else:
        return None


def GetElementHash(element):
    # Remove element id
    slice_ = 4
    if isinstance(element, (*DefineShapeTags,
                            *DefineBitsLosslessTags,
                            DefineBinaryDataTag,
                            DefineEditTextTag,
                            DefineSoundTag,
                            *DefineFontTags,
                            DefineFontAlignZonesTag)):
        slice_ = 8

    elData = bytes(element.getData())[slice_:]

    if len(elData) > 10:
        return hashlib.sha256(elData).hexdigest()
    else:
        return None


def GetNeededCharactersId(element):
    characters = HashSet()
    element.getNeededCharactersDeep(characters)
    return sorted(list(characters))


def GetNeededCharacters(element):
    characters = list()

    swf: Swf = GetSwfByElement(element)

    for elId in GetNeededCharactersId(element):
        for needCharacter in swf.getElementById(elId):
            if not isinstance(needCharacter, (CSMTextSettingsTag, DefineFontAlignZonesTag, DefineFontNameTag)):
                characters.append(needCharacter)

    return characters


class Swf:
    _javaSwfs = {}

    def __init__(self, swfPath: str, autoload=True):
        self.swfPath = swfPath

        if not os.path.exists(swfPath):
            self._makeFile()

        self._swf = None
        self.elementsList = []
        # self.elementsMap = {}
        # self.elementsMapByType = {}
        self.symbolClass: SymbolClass = None
        self.metaData: MetadataClass = None

        if autoload:
            self.open()

    def loadJavaSwf(self, javaSwf):
        self._swf = javaSwf
        self._javaSwfs[self._swf] = self

        self.load()

    @classmethod
    def byJavaSwf(cls, javaSwf):
        swf: Swf = cls._javaSwfs.get(javaSwf, None)
        if swf is not None:
            return swf
        else:
            swf = cls("", autoload=False)
            swf.loadJavaSwf(javaSwf)
            return swf

    def _makeFile(self):
        fileStream = FileOutputStream(self.swfPath)
        bufferedStream = BufferedOutputStream(fileStream)

        byteArrayStream = ByteArrayOutputStream()
        swfOutputStream = SWFOutputStream(byteArrayStream, 15)

        # Write head
        swfOutputStream.writeRECT(RECT(0, 0, 0, 0))
        swfOutputStream.writeFIXED8(24.0)
        swfOutputStream.writeUI16(1)

        # Write empty SymbolClass
        swfOutputStream.write(SymbolClass().getByteArray())

        # Write empty MetadataClass
        swfOutputStream.write(MetadataClass().getByteArray())

        # Write EndTag
        swfOutputStream.writeUI16(0x0000)

        # Save modifier
        byteArray = byteArrayStream.toByteArray()

        outputContentSwfStream = SWFOutputStream(bufferedStream, 15)
        outputContentSwfStream.write("FWS".encode())  # type
        outputContentSwfStream.write(15)  # version
        outputContentSwfStream.writeUI32(outputContentSwfStream.getPos() + byteArray.length + 4)  # size
        outputContentSwfStream.write(byteArray)  # data
        bufferedStream.flush()

        fileStream.close()

        del byteArray
        del fileStream
        del bufferedStream
        del byteArrayStream
        del swfOutputStream

    def isOpen(self) -> bool:
        return self._swf is not None

    def open(self):
        if self._swf is None:
            fileStream = FileInputStream(self.swfPath)
            self._swf = SWF(BufferedInputStream(fileStream), True)
            fileStream.close()

            self._javaSwfs[self._swf] = self

            self.load()

    def load(self):
        if self._swf is not None:
            for element in self._swf.getTags():
                elType = type(element)
                elId = None

                if elType == SymbolClassTag:
                    self.symbolClass = SymbolClass(element)
                elif elType == MetadataTag:
                    self.metaData = MetadataClass(element)
                else:
                    elId = GetElementId(element)

                if elId is not None:
                    self.elementsList.append(element)
                    # self.elementsMap[element] = elId

                    # if elType not in self.elementsMapByType:
                    #    self.elementsMapByType[elType] = {}
                    # self.elementsMapByType[elType][elId] = element

            # print(self.elementsList)
            # print(self.symbolClass.getTags())
            # print(self.elementsMap)
            # print(self.elementsMapByType)

    def save(self):
        if self._swf is not None:
            if self.symbolClass is not None:
                self.symbolClass.save()
            if self.metaData is not None:
                self.metaData.save()
            fileStream = FileOutputStream(self.swfPath)
            self._swf.saveTo(fileStream)
            fileStream.close()

    def close(self):
        if self._swf is not None:
            self._javaSwfs.pop(self._swf)
            self._swf.clearTagSwfs()
            try:
                self._swf.clearAllCache()
            except:
                pass
            self._swf = None
            self.elementsList = []
            # self.elementsMap = {}
            # self.elementsMapByType = {}
            self.metaData = None
            self.symbolClass = None

    def addMetadata(self):
        metadata = MetadataTag(self._swf)
        self._swf.addTag(metadata)
        self.metaData: MetadataClass = MetadataClass(metadata)

    def getElementById(self, elId: int, elType=None):
        elements = []
        for element in self.elementsList:
            if GetElementId(element) == elId and (True if elType is None else isinstance(element, elType)):
                elements.append(element)

        return elements

    def getNextCharacterId(self):
        return int(self._swf.getNextCharacterId())

    @property
    def AS3Packs(self):
        return self._swf.getAS3Packs()

    def getAS3(self, scriptName: str):
        for pack in self.AS3Packs:
            if str(pack) != scriptName: continue
            return str(self._swf.getCached(pack).text)

        return None

    def setAS3(self, scriptName: str, as3: str):
        for pack in self.AS3Packs:
            if str(pack) != scriptName: continue
            scriptReplacer = As3ScriptReplacerFactory.createByConfig()
            pack.abc.replaceScriptPack(scriptReplacer, pack, as3)
            return True

        return False

    def addElement(self, element, elId=None):
        self._swf.addTag(element)

        if elId is not None:
            SetElementId(element, elId)

        # elId = GetElementId(element)
        # elType = ElementAnyToObject(element)

        self.elementsList.append(element)
        # self.elementsMap[element] = elId
        # if elType not in self.elementsMapByType:
        #    self.elementsMapByType[elType] = {}
        # self.elementsMapByType[elType][elId] = element
        return element

    def cloneAndAddElement(self, element, elId=None):
        """
        :return: Clone element
        """
        return self.addElement(element.cloneTag(), elId)

    def replaceElement(self, oldElement, newElement):
        self._swf.replaceTag(oldElement, newElement)

    def removeElement(self, element):
        # elId = GetElementId(element)
        # elType = ElementAnyToObject(element)

        self._swf.removeTag(element)

        if element in self.elementsList:
            self.elementsList.remove(element)
        # self.elementsMap.pop(element)
        # self.elementsMapByType[elType].pop(elId)

    def replaceFont(self, oldFont, newFont):
        fontId = oldFont.fontId
        newFont = newFont.cloneTag()
        newFont.fontId = fontId

        for element in self.elementsList:
            if isinstance(element, DefineFontAlignZonesTag):
                if GetElementId(element) == fontId:
                    self.removeElement(element)

        self.replaceElement(oldFont, newFont)

        return newFont

    def importSoundFile(self, soundPath: str, elId=None):
        if elId is None:
            elId = self.getNextCharacterId()

        if soundPath.endswith(".mp3"):
            soundFormat = 2
        else:
            soundFormat = 3

        soundTag = DefineSoundTag(self._swf)
        soundTag.setSound(FileInputStream(soundPath), soundFormat)
        soundTag.soundId = elId
        self.addElement(soundTag)

        return soundTag

    def importFormattedText(self, formattedText: str, elId=None):
        if elId is None:
            elId = self.getNextCharacterId()

        if _fontId := re.findall(r"font (.*)\n", formattedText):
            formattedText = formattedText.replace(f"font {_fontId[0]}\n", "")
            fontId = int(_fontId[0])
        else:
            fontId = 0

        textTag = DefineEditTextTag(self._swf)
        textTag.setFormattedText(MissingCharacterHandler(), formattedText.strip(), None)
        textTag.fontId = fontId
        textTag.characterID = elId

        textSettingsTag = CSMTextSettingsTag(self._swf)
        textSettingsTag.textID = elId
        textSettingsTag.useFlashType = 1

        if not textTag.multiline and textTag.align == 0:
            textSettingsTag.gridFit = 1
        else:
            textSettingsTag.gridFit = 2

        self.addElement(textTag)
        self.addElement(textSettingsTag)

        return [textTag, textSettingsTag]

    def importFormattedTextFile(self, formattedTextPath: str, elId=None):
        with open(formattedTextPath, "r") as textFile:
            self.importFormattedText(textFile.read(), elId)

    def importImage(self, data: bytes, elId=None):
        if elId is None:
            elId = self.getNextCharacterId()

        if str(ImageTag.getImageFormat(data)) == "JPEG":
            imageTag = DefineBitsDefineBitsJPEG2Tag(self._swf, None, elId, data)
        else:
            imageTag = DefineBitsLossless2Tag(self._swf, None, elId)
            imageTag.setImage(data)

        self.addElement(imageTag)

        return imageTag

    def importImageFile(self, imagePath: str, elId=None):
        with open(imagePath, "rb") as image:
            self.importImage(image.read(), elId)

    def importBinaryData(self, data: bytes, elId=None):
        if elId is None:
            elId = self.getNextCharacterId()

        binaryTag = DefineBinaryDataTag(self._swf)
        binaryTag.binaryData = ByteArrayRange(data, 0, len(data))
        binaryTag.tag = elId
        binaryTag.setModified(True)

        self.addElement(binaryTag)

        return binaryTag

    def importBinaryFile(self, binaryFilePath: str, elId=None):
        with open(binaryFilePath, "rb") as binaryFile:
            binaryTag = self.importBinaryData(binaryFile.read(), elId)

        return binaryTag

    def exportBinaryData(self, element=None, elId=None) -> bytes:
        if type(element) == DefineBinaryDataTag:
            return bytes(element.getData())[6:]

        elif isinstance(elId, int):
            for element in self.getElementById(elId, DefineBinaryDataTag):
                return bytes(element.getData())[6:]

        return None

    def exportBinaryFile(self, binaryFilePath: str, element=None, elId=None):
        binaryData = self.exportBinaryData(element, elId)

        if binaryData is not None:
            with open(binaryFilePath, "wb") as binaryFile:
                binaryFile.write(binaryData)
            return True
        else:
            return False

    def importFontFile(self, fontFilePath: str, elId=None, fontName=None):
        if elId is None:
            elId = self.getNextCharacterId()

        FontTag.reload()

        fontFile = IOFile(fontFilePath)
        javaFont = JavaFont.createFont(JavaFont.TRUETYPE_FONT, fontFile)
        FontTag.addCustomFont(javaFont, fontFile)

        chars = set()
        for i in range(CharacterRanges.rangeCount()):
            for k in CharacterRanges.rangeCodes(i):
                if javaFont.canDisplay(k):
                    chars.add(k)

        fontTag = DefineFont3Tag(self._swf)
        if fontTag.getCharacterCount() == 0:
            fontTag.setHasLayout(True)

        for char in sorted(chars):
            fontTag.addCharacter(chr(char), javaFont)

        if javaFont.getSize() != 1024:
            javaFont = javaFont.deriveFont(1024.0)

        fontMetrics = FontDesignMetrics.getMetrics(javaFont, SwingUtilities2.DEFAULT_FRC)
        fontTag.setAscent(int(fontTag.getDivider() * fontMetrics.getAscent()))
        fontTag.setDescent(int(fontTag.getDivider() * fontMetrics.getDescent()))
        leading = fontMetrics.getAscent() + fontMetrics.getDescent() - 1024
        fontTag.setLeading(int(fontTag.getDivider() * leading))
        fontTag.fontID = elId
        if fontName is not None:
            fontTag.fontName = fontName

        self.addElement(fontTag)

        return fontTag

    def importShapeSwf(self, shapeSwf, elId=None):
        if elId is None:
            elId = self.getNextCharacterId()

        shape = None
        for element in shapeSwf.elementsList:
            if isinstance(element, DefineShapeTags):
                shape = element

        if shape is None:
            return None

        self.addElement(shape, elId)

        if GetShapeBitmapId(shape) is not None:
            bitmap = GetShapeBitmap(shape)
            newBitmapId = self.getNextCharacterId()
            self.addElement(bitmap, newBitmapId)
            SetShapeBitmapId(shape, newBitmapId)

        return shape

    def importShapeSwfFile(self, shapeSwfPath: str, elId=None):
        shapeSwf = Swf(shapeSwfPath)
        self.importShapeSwf(shapeSwf, elId)
        shapeSwf.close()
