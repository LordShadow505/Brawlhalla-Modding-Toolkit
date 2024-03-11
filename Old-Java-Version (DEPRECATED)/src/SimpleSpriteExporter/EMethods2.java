package SimpleSpriteExporter;

import com.jpexs.decompiler.flash.AbortRetryIgnoreHandler;
import com.jpexs.decompiler.flash.ReadOnlyTagList;
import com.jpexs.decompiler.flash.SWF;
import com.jpexs.decompiler.flash.SwfOpenException;
import com.jpexs.decompiler.flash.exporters.FrameExporter;
import com.jpexs.decompiler.flash.exporters.modes.SpriteExportMode;
import com.jpexs.decompiler.flash.exporters.settings.SpriteExportSettings;
import com.jpexs.decompiler.flash.tags.DefineShape2Tag;
import com.jpexs.decompiler.flash.tags.DefineShape3Tag;
import com.jpexs.decompiler.flash.tags.DefineShape4Tag;
import com.jpexs.decompiler.flash.tags.DefineShapeTag;
import com.jpexs.decompiler.flash.tags.DefineSoundTag;
import com.jpexs.decompiler.flash.tags.DefineSpriteTag;
import com.jpexs.decompiler.flash.tags.MetadataTag;
import com.jpexs.decompiler.flash.tags.SymbolClassTag;
import com.jpexs.decompiler.flash.tags.Tag;
import com.jpexs.decompiler.flash.tags.base.CharacterIdTag;
import com.jpexs.decompiler.flash.tags.base.CharacterTag;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import javax.swing.JFileChooser;

public class EMethods2 {
    




    //-----------------------------------------------------------------------------------
    public static List<String> GetAllSkinNames(SWF swf, int level) {
        if (swf != null) {

            List<String> namesFound = new ArrayList<String>();

            for (Tag t : swf.getTags()) {
                if (t instanceof CharacterIdTag) {
                    if (t.getTagName().contains("DefineSprite")) {
                        String tName = ((CharacterTag) t).getExportFileName();

                        if (!tName.contains("Shades")) {

                            int substringPoint = tName.lastIndexOf("_") + 1;

                            tName = tName.substring(substringPoint);

                            if (!namesFound.contains(tName)) {
                                namesFound.add(tName);
                            }
                        }
                    }
                }
            }

            System.out.println("Skin Names Found: " + namesFound);
            return namesFound;
        }
        return null;
    }
    //-----------------------------------------------------------------------------------





    //-----------------------------------------------------------------------------------
    public static List<Tag> GetSpritesList(String skinName, SWF swf) {

        System.out.println("SWF version = " + swf.version);
        System.out.println("FrameCount = " + swf.frameCount);

        String nameToFind = skinName;
        List<Tag> tagsFound = new ArrayList<>();

        for (Tag t : swf.getTags()) {
            if (t instanceof CharacterIdTag) {
                String expName = t.getExportFileName();
                expName = expName.substring(expName.lastIndexOf("_") + 1, expName.length()).toLowerCase();
                if (expName.equals(nameToFind.toLowerCase())) {
                    tagsFound.add(t);
                }
            } else {
            }

        }
        return tagsFound;
    }
    //-----------------------------------------------------------------------------------





    //-----------------------------------------------------------------------------------
    public static void ExtractSprites(String skinName, SWF swf, SpriteExportMode mode, double exportSize,
            String swfName, Boolean isSWF, Boolean ExportFolder, String modPath) throws InterruptedException {

        if (swf != null) {
            String nameToFind = skinName;
            String namesFound = "";

            System.out.println("Extracting " + nameToFind);

            List<Tag> tagsFound = GetSpritesList(skinName, swf);

            System.out.println("SWF:" + swf);

            AbortRetryIgnoreHandler handler = new AbortRetryIgnoreHandler() {

                @Override
                public AbortRetryIgnoreHandler getNewInstance() {

                    return null;
                }

                @Override
                public int handle(Throwable arg0) {

                    return 0;
                }

            };

            com.jpexs.decompiler.flash.EventListener evl = swf.getExportEventListener();
            SpriteExportSettings ses = new SpriteExportSettings(mode, exportSize);
            FrameExporter frameExporter = new FrameExporter();

            System.out.println(tagsFound.size() + " tags found");

            JFileChooser fileChooser = new JFileChooser();

            fileChooser.setCurrentDirectory(new File(modPath));

            fileChooser.setDialogTitle("Select a folder to save the sprites");
            fileChooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);
            int userSelection = fileChooser.showSaveDialog(null);

            if (userSelection == JFileChooser.APPROVE_OPTION) {
                String destinationFolder = fileChooser.getSelectedFile().getAbsolutePath();

                if (isSWF) {
                    for (Tag t : tagsFound) {
                        if (t instanceof DefineSpriteTag) {
                            try {
                                frameExporter.exportSpriteFrames(handler,
                                        destinationFolder + "/" + swfName + "/sprites", swf,
                                        ((DefineSpriteTag) t).getCharacterId(), null, ses, evl);
                            } catch (IOException e) {

                                e.printStackTrace();
                            } catch (InterruptedException e) {

                                e.printStackTrace();
                            }
                        }
                    }
                }

                else {
                    for (Tag t : tagsFound) {
                        if (ExportFolder == true) {
                            if (t instanceof DefineSpriteTag) {

                                try {
                                    frameExporter.exportSpriteFrames(handler, destinationFolder + "/Mod_Sprites", swf,
                                            ((DefineSpriteTag) t).getCharacterId(), null, ses, evl);
                                } catch (IOException e) {

                                    e.printStackTrace();
                                } catch (InterruptedException e) {

                                    e.printStackTrace();
                                }
                            }
                        }

                        else {
                            if (t instanceof DefineSpriteTag) {
                                try {

                                    frameExporter.exportSpriteFrames(handler, destinationFolder + "/Mod_Sprites", swf,
                                            ((DefineSpriteTag) t).getCharacterId(), null, ses, evl);
                                    Path spritesFolder = Paths.get(destinationFolder, "Sprites");
                                    if (!Files.exists(spritesFolder)) {
                                        Files.createDirectory(spritesFolder);
                                    }

                                    Path modSpritesFolder = Paths.get(destinationFolder, "Mod_Sprites");

                                    List<Path> subfolders = Files.list(modSpritesFolder)
                                            .filter(Files::isDirectory)
                                            .collect(Collectors.toList());

                                    // Si el modo de exportación es PNG, se renombran los archivos a .png
                                    if (mode == SpriteExportMode.PNG) {
                                        for (Path subfolder : subfolders) {

                                            List<Path> pngFiles = Files.list(subfolder)
                                                    .filter(path -> path.toString().endsWith(".png"))
                                                    .collect(Collectors.toList());

                                            for (int i = 0; i < pngFiles.size(); i++) {
                                                Path oldPngPath = pngFiles.get(i);
                                                String fileName = subfolder.getFileName().toString() + "_" + (i + 1)
                                                        + ".png";
                                                Path newPngPath = spritesFolder.resolve(fileName);
                                                Files.move(oldPngPath, newPngPath);
                                            }

                                            Files.walk(modSpritesFolder)
                                                    .sorted(Comparator.reverseOrder())
                                                    .map(Path::toFile)
                                                    .forEach(File::delete);

                                        }
                                    }
                                    if (mode == SpriteExportMode.SVG) {
                                        for (Path subfolder : subfolders) {

                                            List<Path> pngFiles = Files.list(subfolder)
                                                    .filter(path -> path.toString().endsWith(".svg"))
                                                    .collect(Collectors.toList());

                                            for (int i = 0; i < pngFiles.size(); i++) {
                                                Path oldPngPath = pngFiles.get(i);
                                                String fileName = subfolder.getFileName().toString() + "_" + (i + 1)
                                                        + ".svg";
                                                Path newPngPath = spritesFolder.resolve(fileName);
                                                Files.move(oldPngPath, newPngPath);
                                            }

                                            Files.walk(modSpritesFolder)
                                                    .sorted(Comparator.reverseOrder())
                                                    .map(Path::toFile)
                                                    .forEach(File::delete);

                                        }
                                    }

                                } catch (IOException e) {
                                    e.printStackTrace();
                                } catch (SecurityException e) {
                                    e.printStackTrace();
                                }
                            }

                        }

                    }
                }

                System.out.println("Sprites exported to " + destinationFolder);
            } else {
                System.out.println("Export cancelled by user");
            }
        }
    }
    //-----------------------------------------------------------------------------------







    //-----------------------------------------------------------------------------------
    public static SWF ExportMod(List<String> names, SWF swf, String sourceSwfName) {
        ReadOnlyTagList allTags = swf.getTags();

        SWF outputSwf = new SWF();
        outputSwf.frameRate = 24.0F;

        System.out.println("Exporting " + names.size() + " assets");

        for (int i = 0; i < allTags.size(); i++) {
            if (allTags.get(i) instanceof DefineSpriteTag) {

                String codename = ((DefineSpriteTag) allTags.get(i)).getClassName();
                //System.out.println("Codename: " + codename);
                if (codename != null &&
                    names.contains(codename)) {
                    outputSwf.addTag(allTags.get(i));
                    //System.out.println("A: " + ((DefineSpriteTag) allTags.get(i)).getClassName());
                    AddModdedSubTags(allTags, Integer.valueOf(i), outputSwf);
                }
            }

            if (allTags.get(i) instanceof DefineSoundTag) {

                String codename = ((DefineSoundTag) allTags.get(i)).getClassName();
                if (codename != null &&
                        names.contains(codename)) {
                    outputSwf.addTag(allTags.get(i));
                }
            }

            if (allTags.get(i) instanceof SymbolClassTag) {
                outputSwf.addTag(allTags.get(i));
            }
        }

        if (outputSwf.getMetadata() == null) {
            outputSwf.addTag((Tag) new MetadataTag(outputSwf));
        }
        (outputSwf.getMetadata()).xmlMetadata = sourceSwfName;

        return outputSwf;
    }
//-----------------------------------------------------------------------------------





//-----------------------------------------------------------------------------------
    public static SWF ExportSkinMod(String SkinCodeName, SWF swf) throws FileNotFoundException {
        ReadOnlyTagList allTags = swf.getTags();

        SWF outputSwf = new SWF();
        outputSwf.frameRate = 24.0F;

        for (int i = 0; i < allTags.size(); i++) {
            if (allTags.get(i) instanceof DefineSpriteTag) {

                String codename = GetCodename((DefineSpriteTag) allTags.get(i));
                if (codename != null &&
                        codename.toLowerCase().equals(SkinCodeName.toLowerCase())) {
                    outputSwf.addTag(allTags.get(i));

                    System.out.println("A: " + ((DefineSpriteTag) allTags.get(i)).getClassName());

                    AddModdedSubTags(allTags, Integer.valueOf(i), outputSwf);
                }
            }

            if (allTags.get(i) instanceof SymbolClassTag) {
                outputSwf.addTag(allTags.get(i));
            }
        }

        return outputSwf;
    }
//-----------------------------------------------------------------------------------





//-----------------------------------------------------------------------------------   
    public static void AddModdedSubTags(ReadOnlyTagList allTags, Integer i, SWF toSWF) {
        Set<Integer> needed = new HashSet<>();
        allTags.get(i.intValue()).getNeededCharactersDeep(needed);

        Object[] neededArray = needed.toArray();

        List<Integer> needDEBUG = new ArrayList<>();

        int t;
        for (t = 0; t < neededArray.length; t++) {
            needDEBUG.add((Integer) neededArray[t]);
        }

        for (t = 0; t < neededArray.length; t++) {
            int n = ((Integer) neededArray[t]).intValue();
            Tag toAdd = null;

            int posInArray = 0;
            for (int a = 0; a < allTags.size(); a++) {
                if (allTags.get(a) instanceof CharacterIdTag
                        && ((CharacterIdTag) allTags.get(a)).getCharacterId() == n) {
                    posInArray = a;

                    break;
                }
            }
            if (toSWF.getTags().indexOf(allTags.get(posInArray)) == -1) {
                toSWF.addTag(allTags.get(posInArray));
            }
        }
    }
//-----------------------------------------------------------------------------------





//-----------------------------------------------------------------------------------
    public static Integer RemoveModdedSubTags(Integer i, SWF fromSWF, List<Integer> removedTags) {
        Integer totalRemoved = Integer.valueOf(0);

        ReadOnlyTagList allTags = fromSWF.getTags();
        Set<Integer> needed = new HashSet<>();
        Tag startTag = allTags.get(i.intValue());
        startTag.getNeededCharactersDeep(needed);

        Object[] neededArray = needed.toArray();

        for (int t = 0; t < neededArray.length; t++) {
            int n = ((Integer) neededArray[t]).intValue();

            if (!removedTags.contains(Integer.valueOf(n))) {

                removedTags.add(Integer.valueOf(n));

                int posInArray = 0;
                for (int a = 0; a < allTags.size(); a++) {
                    if (allTags.get(a) instanceof CharacterIdTag
                            && ((CharacterIdTag) allTags.get(a)).getCharacterId() == n) {
                        posInArray = a;

                        break;
                    }
                }

                if (allTags.get(posInArray) instanceof DefineSpriteTag) {
                    totalRemoved = Integer.valueOf(totalRemoved.intValue()
                            + RemoveModdedSubTags(Integer.valueOf(posInArray), fromSWF, removedTags).intValue());
                } else {
                    fromSWF.removeTag(allTags.get(posInArray));
                    totalRemoved = Integer.valueOf(totalRemoved.intValue() + 1);
                }
            }
        }
        fromSWF.removeTag(startTag);

        return totalRemoved;
    }

//-----------------------------------------------------------------------------------





//-----------------------------------------------------------------------------------
    public static boolean UpdateAllClassNames(SWF inSwf) {
        ReadOnlyTagList allTags = inSwf.getTags();
        SymbolClassTag symbolClass = null;
        int i;
        for (i = 0; i < allTags.size(); i++) {
            if (allTags.get(i) instanceof SymbolClassTag) {
                symbolClass = (SymbolClassTag) allTags.get(i);
                allTags.get(i).setModified(true);
            }
        }

        if (symbolClass == null) {
            return false;
        }

        for (i = 0; i < symbolClass.names.size(); i++) {

            for (int s = 0; s < allTags.size(); s++) {
                if (allTags.get(s) instanceof DefineSpriteTag &&
                        ((DefineSpriteTag) allTags.get(s)).spriteId == ((Integer) symbolClass.tags.get(i)).intValue()) {
                    symbolClass.names.set(i, ((DefineSpriteTag) allTags.get(s)).getClassName());
                }
            }
        }

        return true;
    }

//-----------------------------------------------------------------------------------





//-----------------------------------------------------------------------------------

    public static String GetPartname(DefineSpriteTag tag) {
        return tag.getClassName().substring(0, tag.getClassName().lastIndexOf("_"));
    }
//-----------------------------------------------------------------------------------





//-----------------------------------------------------------------------------------

    public static void SetPartname(DefineSpriteTag tag, String newPartName, boolean partOnly) {
        if (partOnly) {
            tag.setClassName(String.valueOf(newPartName) + GetCodename(tag));
        } else {
            tag.setClassName(newPartName);
        }
    }
//-----------------------------------------------------------------------------------





//-----------------------------------------------------------------------------------

    public static String GetCodename(DefineSpriteTag tag) {
        String className = tag.getClassName();

        if (className != null) {
            return className.substring(className.lastIndexOf("_"));
        }
        return null;
    }
//-----------------------------------------------------------------------------------





//-----------------------------------------------------------------------------------

    public static SWF GetSwf(String swfName, Boolean localLocation) {
        String swfPath = "data/" + swfName;

        if (!localLocation.booleanValue()) {
            swfPath = swfName;
        }

        try {
            FileInputStream fis = new FileInputStream(swfPath);

            SWF swf = new SWF(fis, true);
            fis.close();

            return swf;
        } catch (SwfOpenException ex) {
            System.out.println("ERROR: Invalid SWF file");
        } catch (IOException ex) {
            System.out.println("ERROR: Error during SWF opening");
        } catch (InterruptedException ex) {
            System.out.println("ERROR: Parsing interrupted");
        }

        return null;
    }
//-----------------------------------------------------------------------------------





//-----------------------------------------------------------------------------------

    public static boolean SaveSwfTo(SWF swf, String path) throws FileNotFoundException {
        OutputStream os = new FileOutputStream(path);
        try {
            swf.saveTo(os);
            os.close();
            System.out.println("Saved to " + path);
            return true;
        } catch (IOException e) {
            System.out.println("ERROR: Error during SWF saving");
            return false;
        }
    }

    public static boolean IsDefineShapeAnyTag(Tag tag) {
        return !(!(tag instanceof DefineShapeTag) && !(tag instanceof DefineShape2Tag)
                && !(tag instanceof DefineShape3Tag) && !(tag instanceof DefineShape4Tag));
    }
}
