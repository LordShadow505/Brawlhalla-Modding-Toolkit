
package SimpleSpriteExporter;

import com.jpexs.decompiler.flash.SWF;
import com.jpexs.decompiler.flash.exporters.modes.SpriteExportMode;
import dynamic_subjtable.Main;
import java.awt.Color;
import java.awt.Font;
import java.awt.Image;
import java.awt.Toolkit;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;

import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;
import javax.swing.JFileChooser;

import javax.swing.JList;
import javax.swing.JOptionPane;
import javax.swing.UIManager;
import javax.swing.UnsupportedLookAndFeelException;
import javax.swing.event.ListSelectionEvent;
import javax.swing.event.ListSelectionListener;
import jnafilechooser.api.JnaFileChooser;

public class GUI extends javax.swing.JFrame {

    SWF selectedSWF;

    SpriteExportMode SpriteEM = SpriteExportMode.SWF;
    double ExportScaleUsed = 1;
    String swfName;
    Boolean isSWF;

    public GUI() {

        initComponents();

        setIconImage(getIconImage());
        namesList.addListSelectionListener(new ListSelectionListener() {
            @Override
            public void valueChanged(ListSelectionEvent e) {
                namesListValueChanged(e);
            }
        });

    }

    @Override
    public Image getIconImage() {
        Image retValue = Toolkit.getDefaultToolkit().getImage(ClassLoader.getSystemResource("img/Icon.png"));
        return retValue;
    }

    @SuppressWarnings("unchecked")
    // <editor-fold defaultstate="collapsed" desc="Generated
    // <editor-fold defaultstate="collapsed" desc="Generated
    // <editor-fold defaultstate="collapsed" desc="Generated Code">//GEN-BEGIN:initComponents
    private void initComponents() {

        jPanel1 = new javax.swing.JPanel();
        jPanel2 = new javax.swing.JPanel();
        Import = new RSMaterialComponent.RSButtonMaterialIconOne();
        jPanel3 = new javax.swing.JPanel();
        selectedSwfPath = new javax.swing.JLabel();
        namesScrollPane = new necesario.RSScrollPane();
        jLabel1 = new javax.swing.JLabel();
        Skin = new javax.swing.JLabel();
        LOG = new javax.swing.JLabel();
        jLabel2 = new javax.swing.JLabel();
        Export = new rojeru_san.rsbutton.RSButtonRound();
        ExportSVG = new rojeru_san.rsbutton.RSButtonRound();
        ExportSWF = new rojeru_san.rsbutton.RSButtonRound();
        AllMode = new rojerusan.RSCheckBox();
        FolderMode = new rojerusan.RSCheckBox();
        ModsPathP = new javax.swing.JPanel();
        ModsPath = new javax.swing.JLabel();
        ModsPathB = new RSMaterialComponent.RSButtonFormaIcon();
        BrawlhallaPathB = new RSMaterialComponent.RSButtonFormaIcon();
        BrawlhallaPathP = new javax.swing.JPanel();
        BrawlhallaPath = new javax.swing.JLabel();
        SavePaths = new rojeru_san.rsbutton.RSButtonRound();
        LoadPaths = new rojeru_san.rsbutton.RSButtonRound();
        jLabel3 = new javax.swing.JLabel();
        jLabel4 = new javax.swing.JLabel();
        jLabel5 = new javax.swing.JLabel();
        jLabel6 = new javax.swing.JLabel();
        jLabel7 = new javax.swing.JLabel();
        jLabel8 = new javax.swing.JLabel();
        jLabel9 = new javax.swing.JLabel();

        setDefaultCloseOperation(javax.swing.WindowConstants.EXIT_ON_CLOSE);
        setTitle("Simple Sprite Exporter");
        setResizable(false);

        jPanel1.setBackground(new java.awt.Color(34, 36, 37));
        jPanel1.setLayout(new org.netbeans.lib.awtextra.AbsoluteLayout());

        jPanel2.setBackground(new java.awt.Color(25, 24, 31));

        Import.setBackground(new java.awt.Color(46, 125, 50));
        Import.setText(" Import SWF");
        Import.setBackgroundHover(new java.awt.Color(39, 86, 41));
        Import.setIcons(rojeru_san.efectos.ValoresEnum.ICONS.ADD);
        Import.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                ImportActionPerformed(evt);
            }
        });

        jPanel3.setBackground(new java.awt.Color(38, 50, 56));
        jPanel3.setForeground(new java.awt.Color(38, 50, 56));
        jPanel3.setPreferredSize(new java.awt.Dimension(605, 40));
        jPanel3.setLayout(new org.netbeans.lib.awtextra.AbsoluteLayout());

        selectedSwfPath.setFont(new java.awt.Font("Roboto", 0, 18)); // NOI18N
        selectedSwfPath.setForeground(new java.awt.Color(255, 255, 255));
        selectedSwfPath.setText("...");
        jPanel3.add(selectedSwfPath, new org.netbeans.lib.awtextra.AbsoluteConstraints(10, 10, -1, -1));

        javax.swing.GroupLayout jPanel2Layout = new javax.swing.GroupLayout(jPanel2);
        jPanel2.setLayout(jPanel2Layout);
        jPanel2Layout.setHorizontalGroup(
            jPanel2Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(jPanel2Layout.createSequentialGroup()
                .addComponent(Import, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                .addComponent(jPanel3, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addGap(0, 14, Short.MAX_VALUE))
        );
        jPanel2Layout.setVerticalGroup(
            jPanel2Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(jPanel2Layout.createSequentialGroup()
                .addGroup(jPanel2Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
                    .addComponent(Import, javax.swing.GroupLayout.PREFERRED_SIZE, 60, javax.swing.GroupLayout.PREFERRED_SIZE)
                    .addGroup(jPanel2Layout.createSequentialGroup()
                        .addContainerGap()
                        .addComponent(jPanel3, javax.swing.GroupLayout.PREFERRED_SIZE, 44, javax.swing.GroupLayout.PREFERRED_SIZE)))
                .addGap(88, 88, 88))
        );

        jPanel1.add(jPanel2, new org.netbeans.lib.awtextra.AbsoluteConstraints(0, 0, 826, 59));

        namesScrollPane.setBackground(new java.awt.Color(38, 50, 56));
        namesScrollPane.setForeground(new java.awt.Color(255, 255, 255));
        namesScrollPane.setColorBackground(new java.awt.Color(38, 50, 56));
        namesScrollPane.setFont(new java.awt.Font("Roboto Medium", 0, 18)); // NOI18N
        jPanel1.add(namesScrollPane, new org.netbeans.lib.awtextra.AbsoluteConstraints(20, 120, 223, 360));

        jLabel1.setBackground(new java.awt.Color(255, 255, 255));
        jLabel1.setFont(new java.awt.Font("Roboto", 0, 24)); // NOI18N
        jLabel1.setForeground(new java.awt.Color(255, 255, 255));
        jLabel1.setText("Skin:");
        jPanel1.add(jLabel1, new org.netbeans.lib.awtextra.AbsoluteConstraints(30, 80, -1, 30));

        Skin.setBackground(new java.awt.Color(255, 255, 255));
        Skin.setFont(new java.awt.Font("Roboto", 0, 24)); // NOI18N
        Skin.setForeground(new java.awt.Color(255, 255, 255));
        Skin.setText("...");
        jPanel1.add(Skin, new org.netbeans.lib.awtextra.AbsoluteConstraints(90, 80, -1, 30));

        LOG.setBackground(new java.awt.Color(255, 255, 255));
        LOG.setForeground(new java.awt.Color(255, 255, 255));
        LOG.setText("...");
        jPanel1.add(LOG, new org.netbeans.lib.awtextra.AbsoluteConstraints(300, 450, 220, -1));

        jLabel2.setBackground(new java.awt.Color(255, 255, 255));
        jLabel2.setForeground(new java.awt.Color(255, 255, 255));
        jLabel2.setText("Log:");
        jPanel1.add(jLabel2, new org.netbeans.lib.awtextra.AbsoluteConstraints(260, 450, -1, -1));

        Export.setBackground(new java.awt.Color(96, 46, 156));
        Export.setText("Export PNG");
        Export.setColorHover(new java.awt.Color(77, 42, 118));
        Export.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                ExportActionPerformed(evt);
            }
        });
        jPanel1.add(Export, new org.netbeans.lib.awtextra.AbsoluteConstraints(560, 380, 120, -1));

        ExportSVG.setText("Export SVG");
        ExportSVG.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                ExportSVGActionPerformed(evt);
            }
        });
        jPanel1.add(ExportSVG, new org.netbeans.lib.awtextra.AbsoluteConstraints(690, 380, 120, -1));

        ExportSWF.setBackground(new java.awt.Color(0, 105, 92));
        ExportSWF.setText("Export BMod Format Folder");
        ExportSWF.setToolTipText("Extract everything into a folder in the format Gfx_LEGEND.swf/sprites/DefineSprite...");
        ExportSWF.setColorHover(new java.awt.Color(0, 77, 64));
        ExportSWF.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                ExportSWFActionPerformed(evt);
            }
        });
        jPanel1.add(ExportSWF, new org.netbeans.lib.awtextra.AbsoluteConstraints(560, 430, 250, -1));

        AllMode.setText("All Mode");
        AllMode.setToolTipText("Extract all sprites to a single folder");
        AllMode.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                AllModeActionPerformed(evt);
            }
        });
        jPanel1.add(AllMode, new org.netbeans.lib.awtextra.AbsoluteConstraints(700, 330, 100, -1));

        FolderMode.setSelected(true);
        FolderMode.setText("Folder Mode");
        FolderMode.setToolTipText("Extract the sprites into a folder divided into multiple folders with the skin tags");
        FolderMode.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                FolderModeActionPerformed(evt);
            }
        });
        jPanel1.add(FolderMode, new org.netbeans.lib.awtextra.AbsoluteConstraints(560, 330, 140, -1));

        ModsPathP.setBackground(new java.awt.Color(38, 50, 56));
        ModsPathP.setForeground(new java.awt.Color(38, 50, 56));
        ModsPathP.setPreferredSize(new java.awt.Dimension(605, 40));
        ModsPathP.setLayout(new org.netbeans.lib.awtextra.AbsoluteLayout());

        ModsPath.setFont(new java.awt.Font("Roboto", 0, 18)); // NOI18N
        ModsPath.setForeground(new java.awt.Color(255, 255, 255));
        ModsPath.setText("...");
        ModsPathP.add(ModsPath, new org.netbeans.lib.awtextra.AbsoluteConstraints(10, 10, -1, -1));

        jPanel1.add(ModsPathP, new org.netbeans.lib.awtextra.AbsoluteConstraints(420, 180, 390, 50));

        ModsPathB.setBackground(new java.awt.Color(255, 143, 0));
        ModsPathB.setText("Mods Path");
        ModsPathB.setBackgroundHover(new java.awt.Color(221, 106, 16));
        ModsPathB.setForma(RSMaterialComponent.RSButtonFormaIcon.FORMA.ROUND_LEFT);
        ModsPathB.setIcons(rojeru_san.efectos.ValoresEnum.ICONS.FOLDER_OPEN);
        ModsPathB.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                ModsPathBActionPerformed(evt);
            }
        });
        jPanel1.add(ModsPathB, new org.netbeans.lib.awtextra.AbsoluteConstraints(260, 180, 160, 50));

        BrawlhallaPathB.setBackground(new java.awt.Color(255, 143, 0));
        BrawlhallaPathB.setText("Brawlhalla Path");
        BrawlhallaPathB.setBackgroundHover(new java.awt.Color(221, 106, 16));
        BrawlhallaPathB.setForma(RSMaterialComponent.RSButtonFormaIcon.FORMA.ROUND_LEFT);
        BrawlhallaPathB.setIcons(rojeru_san.efectos.ValoresEnum.ICONS.FOLDER_OPEN);
        BrawlhallaPathB.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                BrawlhallaPathBActionPerformed(evt);
            }
        });
        jPanel1.add(BrawlhallaPathB, new org.netbeans.lib.awtextra.AbsoluteConstraints(260, 120, 160, 50));

        BrawlhallaPathP.setBackground(new java.awt.Color(38, 50, 56));
        BrawlhallaPathP.setForeground(new java.awt.Color(38, 50, 56));
        BrawlhallaPathP.setPreferredSize(new java.awt.Dimension(605, 40));
        BrawlhallaPathP.setLayout(new org.netbeans.lib.awtextra.AbsoluteLayout());

        BrawlhallaPath.setFont(new java.awt.Font("Roboto", 0, 18)); // NOI18N
        BrawlhallaPath.setForeground(new java.awt.Color(255, 255, 255));
        BrawlhallaPath.setText("...");
        BrawlhallaPathP.add(BrawlhallaPath, new org.netbeans.lib.awtextra.AbsoluteConstraints(10, 10, -1, -1));

        jPanel1.add(BrawlhallaPathP, new org.netbeans.lib.awtextra.AbsoluteConstraints(420, 120, 390, 50));

        SavePaths.setBackground(new java.awt.Color(198, 40, 40));
        SavePaths.setText("Save Paths");
        SavePaths.setColorHover(new java.awt.Color(130, 36, 36));
        SavePaths.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                SavePathsActionPerformed(evt);
            }
        });
        jPanel1.add(SavePaths, new org.netbeans.lib.awtextra.AbsoluteConstraints(690, 240, 120, -1));

        LoadPaths.setBackground(new java.awt.Color(56, 142, 60));
        LoadPaths.setText("Load Paths");
        LoadPaths.setColorHover(new java.awt.Color(27, 94, 32));
        LoadPaths.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                LoadPathsActionPerformed(evt);
            }
        });
        jPanel1.add(LoadPaths, new org.netbeans.lib.awtextra.AbsoluteConstraints(560, 240, 120, -1));

        jLabel3.setBackground(new java.awt.Color(255, 255, 255));
        jLabel3.setFont(new java.awt.Font("Roboto Medium", 0, 12)); // NOI18N
        jLabel3.setForeground(new java.awt.Color(255, 255, 255));
        jLabel3.setText("6.- Export!");
        jPanel1.add(jLabel3, new org.netbeans.lib.awtextra.AbsoluteConstraints(260, 380, 280, -1));

        jLabel4.setFont(new java.awt.Font("Roboto Medium", 0, 12)); // NOI18N
        jLabel4.setForeground(new java.awt.Color(255, 255, 255));
        jLabel4.setText("1.- Select the installation path of Brawlhalla.");
        jPanel1.add(jLabel4, new org.netbeans.lib.awtextra.AbsoluteConstraints(260, 260, -1, -1));

        jLabel5.setFont(new java.awt.Font("Roboto Medium", 0, 12)); // NOI18N
        jLabel5.setForeground(new java.awt.Color(255, 255, 255));
        jLabel5.setText("the Brawlhalla files");
        jPanel1.add(jLabel5, new org.netbeans.lib.awtextra.AbsoluteConstraints(280, 300, 120, -1));

        jLabel6.setFont(new java.awt.Font("Roboto Medium", 0, 12)); // NOI18N
        jLabel6.setForeground(new java.awt.Color(255, 255, 255));
        jLabel6.setText("3.- Save the paths by clicking on \"Save\". ");
        jPanel1.add(jLabel6, new org.netbeans.lib.awtextra.AbsoluteConstraints(260, 320, -1, -1));

        jLabel7.setFont(new java.awt.Font("Roboto Medium", 0, 12)); // NOI18N
        jLabel7.setForeground(new java.awt.Color(255, 255, 255));
        jLabel7.setText("4.- Import an SWF file by clicking on \"Import SWF\".");
        jPanel1.add(jLabel7, new org.netbeans.lib.awtextra.AbsoluteConstraints(260, 340, -1, -1));

        jLabel8.setFont(new java.awt.Font("Roboto Medium", 0, 12)); // NOI18N
        jLabel8.setForeground(new java.awt.Color(255, 255, 255));
        jLabel8.setText("5.- Select the sprite export mode.");
        jPanel1.add(jLabel8, new org.netbeans.lib.awtextra.AbsoluteConstraints(260, 360, -1, -1));

        jLabel9.setFont(new java.awt.Font("Roboto Medium", 0, 12)); // NOI18N
        jLabel9.setForeground(new java.awt.Color(255, 255, 255));
        jLabel9.setText("2.- Select the path where you commonly extract ");
        jPanel1.add(jLabel9, new org.netbeans.lib.awtextra.AbsoluteConstraints(260, 280, -1, -1));

        javax.swing.GroupLayout layout = new javax.swing.GroupLayout(getContentPane());
        getContentPane().setLayout(layout);
        layout.setHorizontalGroup(
            layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addComponent(jPanel1, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
        );
        layout.setVerticalGroup(
            layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addComponent(jPanel1, javax.swing.GroupLayout.DEFAULT_SIZE, 496, Short.MAX_VALUE)
        );

        pack();
    }// </editor-fold>//GEN-END:initComponents


    // -------------------------------------------------------------------------------------------
    // PATH THINGS
    // -------------------------------------------------------------------------------------------

    private void BrawlhallaPathBActionPerformed(java.awt.event.ActionEvent evt) {

        JFileChooser chooser = new JFileChooser();
        chooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);
        int returnVal = chooser.showOpenDialog(this);
        if (returnVal == JFileChooser.APPROVE_OPTION) {
            File selectedDirectory = chooser.getSelectedFile();
            String BrawlhallaPathText = selectedDirectory.getAbsolutePath();
            BrawlhallaPath.setText(BrawlhallaPathText);

        }

    }

    private void ModsPathBActionPerformed(java.awt.event.ActionEvent evt) {
        JFileChooser chooser = new JFileChooser();
        chooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);
        int returnVal = chooser.showOpenDialog(this);
        if (returnVal == JFileChooser.APPROVE_OPTION) {
            File selectedDirectory = chooser.getSelectedFile();
            String ModsPathText = selectedDirectory.getAbsolutePath();
            ModsPath.setText(ModsPathText);

        }

    }

    private void SavePathsActionPerformed(java.awt.event.ActionEvent evt) {
       
        if (BrawlhallaPath.getText().equals("...") || ModsPath.getText().equals("...")) {
            JOptionPane.showMessageDialog(null, "Please select the Brawlhalla and Mods paths", "Error", JOptionPane.ERROR_MESSAGE);
        } else {
            
            try {
                File file = new File("paths.txt");
                FileWriter fw = new FileWriter(file);
                BufferedWriter bw = new BufferedWriter(fw);
                bw.write(BrawlhallaPath.getText());
                bw.newLine();
                bw.write(ModsPath.getText());
                bw.close();
                JOptionPane.showMessageDialog(null, "Paths saved successfully", "Success", JOptionPane.INFORMATION_MESSAGE);
            } catch (IOException ex) {
                Logger.getLogger(Main.class.getName()).log(Level.SEVERE, null, ex);
            }
        }
    }

    private void LoadPathsActionPerformed(java.awt.event.ActionEvent evt) {
        if (!new File("paths.txt").exists()) {
            JOptionPane.showMessageDialog(null, "No paths file found", "Error", JOptionPane.ERROR_MESSAGE);
            return;
        }
        try {
            File file = new File("paths.txt");
            FileReader fr = new FileReader(file);
            BufferedReader br = new BufferedReader(fr);
            BrawlhallaPath.setText(br.readLine());
            ModsPath.setText(br.readLine());
            br.close();
            JOptionPane.showMessageDialog(null, "Paths loaded successfully", "Success", JOptionPane.INFORMATION_MESSAGE);
        } catch (IOException ex) {
            Logger.getLogger(Main.class.getName()).log(Level.SEVERE, null, ex);
        }
    }

    // -------------------------------------------------------------------------------------------
    JList<String> namesList = new JList<>();
    

    // -------------------------------------------------------------------------------------------
    // IMPORT BUTTON
    // -------------------------------------------------------------------------------------------

    private void ImportActionPerformed(java.awt.event.ActionEvent evt) {

        JnaFileChooser fc = new JnaFileChooser();
        fc.addFilter("All Files", "swf");

        String brawlhallaPath = BrawlhallaPath.getText();
        fc.setCurrentDirectory(brawlhallaPath);

        LOG.setText("Importing...");

        boolean action = fc.showOpenDialog(null);
        if (action) {
            SWF selectedSWF = BrawlhallaModExporter.GetSwf(fc.getSelectedFile().getAbsolutePath(), false);
            LOG.setText("Imported: " + fc.getSelectedFile().getName());
            // System.out.println("Imported!: " + fc.getSelectedFile().getName());

            swfName = fc.getSelectedFile().getName();

            selectedSwfPath.setText(fc.getSelectedFile().getAbsolutePath());

            List<String> listNames = BrawlhallaModExporter.GetAllSkinNames((SWF) selectedSWF, 0);

            // Get swf name
            String[] names = new String[listNames.size()];
            listNames.toArray(names);
            namesList.setListData(names);
            namesScrollPane.setViewportView(namesList);
            // namenamesScrollPane black
            namesScrollPane.getViewport().getView().setBackground(new Color(38, 50, 56));
            namesScrollPane.getViewport().getView().setForeground(new Color(255, 255, 255));
            namesScrollPane.getViewport().getView().setFont(new Font("Roboto", 0, 18));

            namesList.setLayoutOrientation(JList.VERTICAL);

            System.out.println("Updated!");
            // print all names
            for (String name : names) {
                System.out.println(name);
            }

        } else {
            LOG.setText("Not imported!");
            System.out.println("Not imported!");
        }
    }
    // -------------------------------------------------------------------------------------------

    // -------------------------------------------------------------------------------------------
    // NAMES LIST
    // -------------------------------------------------------------------------------------------

    private void namesListValueChanged(javax.swing.event.ListSelectionEvent evt) {

        String selectedName = namesList.getSelectedValue();

        LOG.setText("Selected: " + selectedName);
        System.out.println("Selected: " + selectedName);

        Skin.setText(selectedName);

    }
    // -------------------------------------------------------------------------------------------

    // -------------------------------------------------------------------------------------------
    // EXPORT PNG BUTTON
    // -------------------------------------------------------------------------------------------

    private void ExportActionPerformed(java.awt.event.ActionEvent evt) {
        SpriteEM = SpriteExportMode.PNG;
        ExportScaleUsed = 3;
        Boolean isSWF = false;
        
        String modPath = ModsPath.getText();

        Boolean ExportFolder = true;

        if (AllMode.isSelected()) {
            ExportFolder = false;
            LOG.setText("Exporting ALL!");
        }
        if (FolderMode.isSelected()) {
            ExportFolder = true;
            LOG.setText("Exporting FOLDERS!");
        }

        System.out.println("Exporting!");
        LOG.setText("Exporting!");

        if (Skin.getText() != null && selectedSwfPath.getText() != null) {
            SWF selectedSWF = BrawlhallaModExporter.GetSwf(selectedSwfPath.getText(), false);

            try {
                BrawlhallaModExporter.ExtractSprites(Skin.getText(), selectedSWF, SpriteEM, ExportScaleUsed, swfName,
                        isSWF, ExportFolder, modPath);
            } catch (InterruptedException ex) {
                Logger.getLogger(GUI.class.getName()).log(Level.SEVERE, null, ex);
            }
            System.out.println("PNG Exported!");

            LOG.setText("PNG Exported!");

        } else {
            System.out.println("Not exported!");
            LOG.setText("Not exported!");
        }

    }
    // -------------------------------------------------------------------------------------------

    // -------------------------------------------------------------------------------------------
    // EXPORT SVG BUTTON
    // -------------------------------------------------------------------------------------------

    private void ExportSVGActionPerformed(java.awt.event.ActionEvent evt) {
        SpriteEM = SpriteExportMode.SVG;
        ExportScaleUsed = 1;
        Boolean isSWF = false;
        
        String modPath = ModsPath.getText();
      
        Boolean ExportFolder = true;

        if (AllMode.isSelected()) {
            ExportFolder = false;
            LOG.setText("Exporting ALL!");
        }
        if (FolderMode.isSelected()) {
            ExportFolder = true;
            LOG.setText("Exporting FOLDERS!");
        }

        System.out.println("Exporting!");
        LOG.setText("Exporting!");

        if (Skin.getText() != null && selectedSwfPath.getText() != null) {
            SWF selectedSWF = BrawlhallaModExporter.GetSwf(selectedSwfPath.getText(), false);

            try {
                BrawlhallaModExporter.ExtractSprites(Skin.getText(), selectedSWF, SpriteEM, ExportScaleUsed, swfName,
                        isSWF, ExportFolder, modPath);
            } catch (InterruptedException ex) {
                Logger.getLogger(GUI.class.getName()).log(Level.SEVERE, null, ex);
            }
            System.out.println("SVG Exported!");
            LOG.setText("SVG Exported!");
        } else {
            System.out.println("Not exported!");
            LOG.setText("Not exported!");
        }
    }
    // -------------------------------------------------------------------------------------------

    // -------------------------------------------------------------------------------------------
    // EXPORT SWF BUTTON
    // -------------------------------------------------------------------------------------------

    private void ExportSWFActionPerformed(java.awt.event.ActionEvent evt) {
        SpriteEM = SpriteExportMode.SWF;
        ExportScaleUsed = 1;
        Boolean isSWF = true;
        
        String modPath = ModsPath.getText();

        Boolean ExportFolder = true;

        if (AllMode.isSelected()) {
            ExportFolder = false;
            LOG.setText("Exporting ALL!");
        }
        if (FolderMode.isSelected()) {
            ExportFolder = true;
            LOG.setText("Exporting FOLDERS!");
        }

        System.out.println("Exporting!");
        LOG.setText("Exporting!");

        if (Skin.getText() != null && selectedSwfPath.getText() != null) {
            SWF selectedSWF = BrawlhallaModExporter.GetSwf(selectedSwfPath.getText(), false);

            try {
                BrawlhallaModExporter.ExtractSprites(Skin.getText(), selectedSWF, SpriteEM, ExportScaleUsed, swfName,
                        isSWF, ExportFolder, modPath);
            } catch (InterruptedException ex) {
                Logger.getLogger(GUI.class.getName()).log(Level.SEVERE, null, ex);
            }

            System.out.println("SWF Exported!");
            LOG.setText("SWF Exported!");
        } else {
            System.out.println("Not exported!");
            LOG.setText("Not exported!");
        }
    }

    // -------------------------------------------------------------------------------------------

    // -------------------------------------------------------------------------------------------
    // VIEW SKIN
    // -------------------------------------------------------------------------------------------

    private void FolderModeActionPerformed(java.awt.event.ActionEvent evt) {
        if (FolderMode.isSelected()) {
            LOG.setText("Folder Mode");
            AllMode.setSelected(false);
        }
    }

    private void AllModeActionPerformed(java.awt.event.ActionEvent evt) {
        if (AllMode.isSelected()) {
            LOG.setText("All Mode");
            FolderMode.setSelected(false);
        }
    }
    // -------------------------------------------------------------------------------------------

    /**
     * @param args the command line arguments
     */
    public static void main(String args[]) {
        /* Set the Nimbus look and feel */
        // <editor-fold defaultstate="collapsed" desc=" Look and feel setting code
        // (optional) ">
        /*
         * If Nimbus (introduced in Java SE 6) is not available, stay with the default
         * look and feel.
         * For details see
         * http://download.oracle.com/javase/tutorial/uiswing/lookandfeel/plaf.html
         */
        try {
            for (javax.swing.UIManager.LookAndFeelInfo info : javax.swing.UIManager.getInstalledLookAndFeels()) {
                if ("Nimbus".equals(info.getName())) {
                    javax.swing.UIManager.setLookAndFeel(info.getClassName());
                    break;
                }
            }
        } catch (ClassNotFoundException ex) {
            java.util.logging.Logger.getLogger(GUI.class.getName()).log(java.util.logging.Level.SEVERE, null, ex);
        } catch (InstantiationException ex) {
            java.util.logging.Logger.getLogger(GUI.class.getName()).log(java.util.logging.Level.SEVERE, null, ex);
        } catch (IllegalAccessException ex) {
            java.util.logging.Logger.getLogger(GUI.class.getName()).log(java.util.logging.Level.SEVERE, null, ex);
        } catch (javax.swing.UnsupportedLookAndFeelException ex) {
            java.util.logging.Logger.getLogger(GUI.class.getName()).log(java.util.logging.Level.SEVERE, null, ex);
        }
        // </editor-fold>

        /* Create and display the form */
        java.awt.EventQueue.invokeLater(new Runnable() {
            public void run() {
                try {
                    UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
                } catch (ClassNotFoundException | InstantiationException | IllegalAccessException
                        | UnsupportedLookAndFeelException ex) {
                    Logger.getLogger(GUI.class.getName()).log(Level.SEVERE, null, ex);
                }
                new GUI().setVisible(true);
            }
        });
    }

    // Variables declaration - do not modify//GEN-BEGIN:variables
    private rojerusan.RSCheckBox AllMode;
    private javax.swing.JLabel BrawlhallaPath;
    private RSMaterialComponent.RSButtonFormaIcon BrawlhallaPathB;
    private javax.swing.JPanel BrawlhallaPathP;
    private rojeru_san.rsbutton.RSButtonRound Export;
    private rojeru_san.rsbutton.RSButtonRound ExportSVG;
    private rojeru_san.rsbutton.RSButtonRound ExportSWF;
    private rojerusan.RSCheckBox FolderMode;
    private RSMaterialComponent.RSButtonMaterialIconOne Import;
    private javax.swing.JLabel LOG;
    private rojeru_san.rsbutton.RSButtonRound LoadPaths;
    private javax.swing.JLabel ModsPath;
    private RSMaterialComponent.RSButtonFormaIcon ModsPathB;
    private javax.swing.JPanel ModsPathP;
    private rojeru_san.rsbutton.RSButtonRound SavePaths;
    private javax.swing.JLabel Skin;
    private javax.swing.JLabel jLabel1;
    private javax.swing.JLabel jLabel2;
    private javax.swing.JLabel jLabel3;
    private javax.swing.JLabel jLabel4;
    private javax.swing.JLabel jLabel5;
    private javax.swing.JLabel jLabel6;
    private javax.swing.JLabel jLabel7;
    private javax.swing.JLabel jLabel8;
    private javax.swing.JLabel jLabel9;
    private javax.swing.JPanel jPanel1;
    private javax.swing.JPanel jPanel2;
    private javax.swing.JPanel jPanel3;
    private necesario.RSScrollPane namesScrollPane;
    private javax.swing.JLabel selectedSwfPath;
    // End of variables declaration//GEN-END:variables

    private void SetExportPath(String absolutePath) {
        throw new UnsupportedOperationException("Not supported yet."); // Generated from
                                                                       // nbfs://nbhost/SystemFileSystem/Templates/Classes/Code/GeneratedMethodBody
    }
}
