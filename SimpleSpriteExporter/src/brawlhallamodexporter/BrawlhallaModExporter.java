package brawlhallamodexporter;

import com.jpexs.decompiler.flash.AbortRetryIgnoreHandler;
import com.jpexs.decompiler.flash.SWF;
import com.jpexs.decompiler.flash.SwfOpenException;
import com.jpexs.decompiler.flash.tags.DefineSpriteTag;
import com.jpexs.decompiler.flash.tags.Tag;
import com.jpexs.decompiler.flash.tags.base.CharacterIdTag;
import com.jpexs.decompiler.flash.tags.base.CharacterTag;

import com.jpexs.decompiler.flash.exporters.FrameExporter;

import com.jpexs.decompiler.flash.exporters.modes.SpriteExportMode;
import com.jpexs.decompiler.flash.exporters.settings.SpriteExportSettings;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.stream.Collectors;
import javax.swing.JFileChooser;

public class BrawlhallaModExporter {

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

    public static String GetPartNameFromExpName(String expName, String skinName, boolean includeSkin) {

        if (expName.length() >= 18) {

            String str = expName;
            str = str.replaceAll("[^0-9]+", " ");
            int ID = Integer.parseInt((str.trim().split(" "))[0]);

            if (includeSkin) {

                return expName.substring(13 + String.valueOf(ID).length(), expName.length());
            } else {

                return expName.substring(13 + String.valueOf(ID).length(), expName.length() - skinName.length());
            }
        }
        return "NAME_TOO_SHORT";
    }

    public static SWF GetSwf(String swfName, Boolean localLocation) {
        String swfPath = "data/" + swfName;

        if (!localLocation) {
            swfPath = swfName;
        }

        File f = new File(swfPath);
        if (f.exists()) {
            System.out.println("SWF " + swfPath);
        } else {
            System.out.println(swfPath + " no...");
        }

        try (FileInputStream fis = new FileInputStream(swfPath)) {

            SWF swf = new SWF(fis, true);

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

    public static void LoadSkin(String skinName) {

    }

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

    static void SetExportPath(String absolutePath) {
        String exportPath = absolutePath;

        System.out.println("Export path set to " + exportPath);

    }

}


