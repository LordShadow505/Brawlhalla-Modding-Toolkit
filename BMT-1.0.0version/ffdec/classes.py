from jpype import JClass


# Agregar las nuevas librerías
AbortRetryIgnoreHandler = JClass("com.jpexs.decompiler.flash.AbortRetryIgnoreHandler")
ReadOnlyTagList = JClass("com.jpexs.decompiler.flash.ReadOnlyTagList")
SwfOpenException = JClass("com.jpexs.decompiler.flash.SwfOpenException")
Tag = JClass("com.jpexs.decompiler.flash.tags.Tag")
CharacterIdTag = JClass("com.jpexs.decompiler.flash.tags.base.CharacterIdTag")
CharacterTag = JClass("com.jpexs.decompiler.flash.tags.base.CharacterTag")

# Continuar con las importaciones originales
JavaFont = JClass("java.awt.Font")
IOFile = JClass("java.io.File")
HashSet = JClass("java.util.HashSet")
ArrayList = JClass('java.util.ArrayList')
FileInputStream = JClass('java.io.FileInputStream')
FileOutputStream = JClass('java.io.FileOutputStream')
BufferedInputStream = JClass('java.io.BufferedInputStream')
BufferedOutputStream = JClass('java.io.BufferedOutputStream')
ByteArrayOutputStream = JClass('java.io.ByteArrayOutputStream')
SwingUtilities2 = JClass("sun.swing.SwingUtilities2")
FontDesignMetrics = JClass("sun.font.FontDesignMetrics")

# FFDEc_lib
# Swf
SWF = JClass('com.jpexs.decompiler.flash.SWF')
SWFHeader = JClass('com.jpexs.decompiler.flash.SWFHeader')
SWFOutputStream = JClass('com.jpexs.decompiler.flash.SWFOutputStream')

Configuration = JClass('com.jpexs.decompiler.flash.configuration.Configuration')
HighlightedTextWriter = JClass('com.jpexs.decompiler.flash.helpers.HighlightedTextWriter')
ScriptExportMode = JClass('com.jpexs.decompiler.flash.exporters.modes.ScriptExportMode')

As3ScriptReplacerFactory = JClass('com.jpexs.decompiler.flash.importers.As3ScriptReplacerFactory')

# Exporters
FrameExporter = JClass('com.jpexs.decompiler.flash.exporters.FrameExporter')
SpriteExportMode = JClass('com.jpexs.decompiler.flash.exporters.modes.SpriteExportMode')
SpriteExportSettings = JClass('com.jpexs.decompiler.flash.exporters.settings.SpriteExportSettings')
FrameExportSettings = JClass('com.jpexs.decompiler.flash.exporters.settings.FrameExportSettings')
FrameExportMode = JClass('com.jpexs.decompiler.flash.exporters.modes.FrameExportMode')

# Types
RECT = JClass('com.jpexs.decompiler.flash.types.RECT')
FILLSTYLE = JClass('com.jpexs.decompiler.flash.types.FILLSTYLE')
MATRIX = JClass('com.jpexs.decompiler.flash.types.MATRIX')

# Helpers
ByteArrayRange = JClass("com.jpexs.helpers.ByteArrayRange")

# Tags
ImageTag = JClass("com.jpexs.decompiler.flash.tags.base.ImageTag")
MissingCharacterHandler = JClass("com.jpexs.decompiler.flash.tags.base.MissingCharacterHandler")
DefineBitsDefineBitsJPEG2Tag = JClass('com.jpexs.decompiler.flash.tags.DefineBitsJPEG2Tag')
DefineBitsLosslessTag = JClass('com.jpexs.decompiler.flash.tags.DefineBitsLosslessTag')
DefineBitsLossless2Tag = JClass('com.jpexs.decompiler.flash.tags.DefineBitsLossless2Tag')
DefineBitsLosslessTags = [
    DefineBitsDefineBitsJPEG2Tag,
    DefineBitsLosslessTag,
    DefineBitsLossless2Tag
]
DefineShapeTag = JClass('com.jpexs.decompiler.flash.tags.DefineShapeTag')
DefineShape2Tag = JClass('com.jpexs.decompiler.flash.tags.DefineShape2Tag')
DefineShape3Tag = JClass('com.jpexs.decompiler.flash.tags.DefineShape3Tag')
DefineShape4Tag = JClass('com.jpexs.decompiler.flash.tags.DefineShape4Tag')
DefineShapeTags = (
    DefineShapeTag,
    DefineShape2Tag,
    DefineShape3Tag,
    DefineShape4Tag
)
DefineMorphShapeTag = JClass("com.jpexs.decompiler.flash.tags.DefineMorphShapeTag")
FontTag = JClass('com.jpexs.decompiler.flash.tags.base.FontTag')
DefineFontTag = JClass('com.jpexs.decompiler.flash.tags.DefineFontTag')
DefineFont2Tag = JClass('com.jpexs.decompiler.flash.tags.DefineFont2Tag')
DefineFont3Tag = JClass('com.jpexs.decompiler.flash.tags.DefineFont3Tag')
DefineFont4Tag = JClass('com.jpexs.decompiler.flash.tags.DefineFont4Tag')
DefineFontTags = (
    DefineFontTag,
    DefineFont2Tag,
    DefineFont3Tag,
    DefineFont4Tag
)
DefineSpriteTag = JClass('com.jpexs.decompiler.flash.tags.DefineSpriteTag')
DefineSoundTag = JClass('com.jpexs.decompiler.flash.tags.DefineSoundTag')
DefineTextTag = JClass('com.jpexs.decompiler.flash.tags.DefineTextTag')
DefineEditTextTag = JClass('com.jpexs.decompiler.flash.tags.DefineEditTextTag')
CSMTextSettingsTag = JClass('com.jpexs.decompiler.flash.tags.CSMTextSettingsTag')
DefineFontNameTag = JClass('com.jpexs.decompiler.flash.tags.DefineFontNameTag')
CharacterRanges = JClass('com.jpexs.decompiler.flash.tags.font.CharacterRanges')
DefineFontAlignZonesTag = JClass('com.jpexs.decompiler.flash.tags.DefineFontAlignZonesTag')
SymbolClassTag = JClass('com.jpexs.decompiler.flash.tags.SymbolClassTag')
DefineBinaryDataTag = JClass("com.jpexs.decompiler.flash.tags.DefineBinaryDataTag")
MetadataTag = JClass("com.jpexs.decompiler.flash.tags.MetadataTag")
RemoveObjectTag = JClass("com.jpexs.decompiler.flash.tags.RemoveObjectTag")
RemoveObject2Tag = JClass("com.jpexs.decompiler.flash.tags.RemoveObject2Tag")
PlaceObjectTag = JClass("com.jpexs.decompiler.flash.tags.PlaceObjectTag")
PlaceObject2Tag = JClass("com.jpexs.decompiler.flash.tags.PlaceObject2Tag")
PlaceObject3Tag = JClass("com.jpexs.decompiler.flash.tags.PlaceObject3Tag")
PlaceObject4Tag = JClass("com.jpexs.decompiler.flash.tags.PlaceObject4Tag")
PlaceObjectTags = (PlaceObjectTag,
                   PlaceObject2Tag,
                   PlaceObject3Tag,
                   PlaceObject4Tag)
FrameLabelTag = JClass("com.jpexs.decompiler.flash.tags.FrameLabelTag")
ShowFrameTag = JClass("com.jpexs.decompiler.flash.tags.ShowFrameTag")

class ActionScriptTag:
    pass
