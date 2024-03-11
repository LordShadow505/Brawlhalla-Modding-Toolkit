package SimpleSpriteExporter;

import com.jpexs.decompiler.flash.ReadOnlyTagList;
import com.jpexs.decompiler.flash.SWF;
import com.jpexs.decompiler.flash.exporters.modes.SpriteExportMode;
import com.jpexs.decompiler.flash.tags.DefineSpriteTag;
import java.awt.Color;
import java.awt.Component;
import java.awt.Desktop;
import java.awt.Font;
import java.awt.Image;
import java.awt.Toolkit;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.Properties;
import javax.swing.BorderFactory;
import javax.swing.DefaultListCellRenderer;
import javax.swing.DefaultListModel;
import javax.swing.JFileChooser;
import javax.swing.JList;
import javax.swing.JOptionPane;
import javax.swing.UIManager;
import javax.swing.UnsupportedLookAndFeelException;
import javax.swing.event.ListSelectionEvent;
import javax.swing.event.ListSelectionListener;
import javax.swing.filechooser.FileFilter;



public class SimpleSpriteExporter extends javax.swing.JFrame {
    



    SpriteExportMode SpriteEM = SpriteExportMode.SWF;
    double ExportScaleUsed = 1;

    SWF extractorSelectedSwf;

    List<SWFSearchFilter> extractorFilters = new ArrayList<>(); // Filtros


    final JList<String> extractorFiltersJList = new JList<>(); // Lista de filtros
    final JList<String> extractorFilteredTags = new JList<>(); // Lista de tags filtrados

    
    String swfName;

    static String gamePathString;
    static String modsPathString;


    public SimpleSpriteExporter() {
        initComponents();
        cargarConfiguracion();
        
        setIconImage(getIconImage());

        extractorFiltersJList.setModel(new DefaultListModel<>());
        extractorFilteredTags.setModel(new DefaultListModel<>());

        namesList.addListSelectionListener(new ListSelectionListener() {
            @Override
            public void valueChanged(ListSelectionEvent e) {
                namesListValueChanged(e);
            }
        });
        
    }
    
        @Override
    public Image getIconImage() {
        Image retValue = Toolkit.getDefaultToolkit().getImage(ClassLoader.getSystemResource("img/Icon64.png"));
        return retValue;
    }

    //-------------------------- FORM METHODS --------------------------
    @SuppressWarnings("unchecked")
    // <editor-fold defaultstate="collapsed" desc="Generated Code">//GEN-BEGIN:initComponents
    private void initComponents() {

        jPanel1 = new javax.swing.JPanel();
        jPanel2 = new javax.swing.JPanel();
        jLabel1 = new javax.swing.JLabel();
        jLabel2 = new javax.swing.JLabel();
        ButtonSkinRender = new RSMaterialComponent.RSButtonFormaIcon();
        ButtonColorSwapper = new RSMaterialComponent.RSButtonFormaIcon();
        ButtonSkinEditor = new RSMaterialComponent.RSButtonFormaIcon();
        ButtonSpriteExporter = new RSMaterialComponent.RSButtonFormaIcon();
        jLabel3 = new javax.swing.JLabel();
        jPanel3 = new javax.swing.JPanel();
        jPanel4 = new javax.swing.JPanel();
        selectSwfButton = new RSMaterialComponent.RSButtonIconUno();
        BrawlhallaPathB = new RSMaterialComponent.RSButtonFormaIcon();
        ModsPathB = new RSMaterialComponent.RSButtonFormaIcon();
        ModsPathP = new javax.swing.JPanel();
        ModsPath = new javax.swing.JLabel();
        BrawlhallaPathP = new javax.swing.JPanel();
        BrawlhallaPath = new javax.swing.JLabel();
        LOG = new javax.swing.JLabel();
        namesScrollPane = new necesario.RSScrollPane();
        removeSWFFilterButton = new rojeru_san.RSButton();
        rSScrollPane1 = new necesario.RSScrollPane();
        selectedSwfPath = new javax.swing.JLabel();
        Export = new rojeru_san.rsbutton.RSButtonRound();
        ExportSVG = new rojeru_san.rsbutton.RSButtonRound();
        AllMode = new rojerusan.RSCheckBox();
        FolderMode = new rojerusan.RSCheckBox();
        jSeparator1 = new javax.swing.JSeparator();
        exportSelectionButton = new rojeru_san.rsbutton.RSButtonRound();
        Skin = new javax.swing.JLabel();

        setDefaultCloseOperation(javax.swing.WindowConstants.EXIT_ON_CLOSE);
        setTitle("Simple Sprite Exporter");
        setResizable(false);

        jPanel1.setBackground(new java.awt.Color(25, 25, 25));
        jPanel1.setForeground(new java.awt.Color(30, 30, 30));
        jPanel1.setMinimumSize(new java.awt.Dimension(900, 600));
        jPanel1.setPreferredSize(new java.awt.Dimension(900, 600));
        jPanel1.setRequestFocusEnabled(false);
        jPanel1.setLayout(new org.netbeans.lib.awtextra.AbsoluteLayout());

        jPanel2.setBackground(new java.awt.Color(40, 40, 40));

        jLabel1.setFont(new java.awt.Font("Roboto Medium", 0, 15)); // NOI18N
        jLabel1.setForeground(new java.awt.Color(255, 255, 255));
        jLabel1.setText("Simple Sprite Exporter");

        jLabel2.setFont(new java.awt.Font("Roboto", 1, 12)); // NOI18N
        jLabel2.setForeground(new java.awt.Color(153, 153, 153));
        jLabel2.setText("Tools");

        ButtonSkinRender.setBackground(new java.awt.Color(40, 40, 40));
        ButtonSkinRender.setText("   Skin Render");
        ButtonSkinRender.setBackgroundHover(new java.awt.Color(40, 40, 40));
        ButtonSkinRender.setFont(new java.awt.Font("Roboto Medium", 0, 14)); // NOI18N
        ButtonSkinRender.setForma(RSMaterialComponent.RSButtonFormaIcon.FORMA.ROUND);
        ButtonSkinRender.setIcons(rojeru_san.efectos.ValoresEnum.ICONS.ACCESSIBILITY);
        ButtonSkinRender.setPositionIcon(rojeru_san.efectos.ValoresEnum.POSITIONICON.LEFT);
        ButtonSkinRender.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                ButtonSkinRenderActionPerformed(evt);
            }
        });

        ButtonColorSwapper.setBackground(new java.awt.Color(40, 40, 40));
        ButtonColorSwapper.setText("   Color Swapper");
        ButtonColorSwapper.setBackgroundHover(new java.awt.Color(40, 40, 40));
        ButtonColorSwapper.setFont(new java.awt.Font("Roboto Medium", 0, 14)); // NOI18N
        ButtonColorSwapper.setForma(RSMaterialComponent.RSButtonFormaIcon.FORMA.ROUND);
        ButtonColorSwapper.setIcons(rojeru_san.efectos.ValoresEnum.ICONS.PALETTE);
        ButtonColorSwapper.setPositionIcon(rojeru_san.efectos.ValoresEnum.POSITIONICON.LEFT);
        ButtonColorSwapper.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                ButtonColorSwapperActionPerformed(evt);
            }
        });

        ButtonSkinEditor.setBackground(new java.awt.Color(40, 40, 40));
        ButtonSkinEditor.setText("   Skin Editor");
        ButtonSkinEditor.setBackgroundHover(new java.awt.Color(40, 40, 40));
        ButtonSkinEditor.setFont(new java.awt.Font("Roboto Medium", 0, 14)); // NOI18N
        ButtonSkinEditor.setForma(RSMaterialComponent.RSButtonFormaIcon.FORMA.ROUND);
        ButtonSkinEditor.setIcons(rojeru_san.efectos.ValoresEnum.ICONS.EDIT);
        ButtonSkinEditor.setPositionIcon(rojeru_san.efectos.ValoresEnum.POSITIONICON.LEFT);
        ButtonSkinEditor.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                ButtonSkinEditorActionPerformed(evt);
            }
        });

        ButtonSpriteExporter.setBackground(new java.awt.Color(23, 93, 220));
        ButtonSpriteExporter.setText("   Sprite Exporter");
        ButtonSpriteExporter.setBackgroundHover(new java.awt.Color(23, 93, 220));
        ButtonSpriteExporter.setFont(new java.awt.Font("Roboto Medium", 0, 14)); // NOI18N
        ButtonSpriteExporter.setForma(RSMaterialComponent.RSButtonFormaIcon.FORMA.ROUND);
        ButtonSpriteExporter.setIcons(rojeru_san.efectos.ValoresEnum.ICONS.UNARCHIVE);
        ButtonSpriteExporter.setPositionIcon(rojeru_san.efectos.ValoresEnum.POSITIONICON.LEFT);
        ButtonSpriteExporter.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                ButtonSpriteExporterActionPerformed(evt);
            }
        });

        jLabel3.setFont(new java.awt.Font("Roboto", 1, 12)); // NOI18N
        jLabel3.setForeground(new java.awt.Color(153, 153, 153));
        jLabel3.setText("By LordShadow505");

        javax.swing.GroupLayout jPanel2Layout = new javax.swing.GroupLayout(jPanel2);
        jPanel2.setLayout(jPanel2Layout);
        jPanel2Layout.setHorizontalGroup(
            jPanel2Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(jPanel2Layout.createSequentialGroup()
                .addGroup(jPanel2Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
                    .addGroup(jPanel2Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.TRAILING)
                        .addComponent(ButtonSpriteExporter, javax.swing.GroupLayout.PREFERRED_SIZE, 167, javax.swing.GroupLayout.PREFERRED_SIZE)
                        .addComponent(ButtonSkinRender, javax.swing.GroupLayout.PREFERRED_SIZE, 167, javax.swing.GroupLayout.PREFERRED_SIZE)
                        .addComponent(ButtonColorSwapper, javax.swing.GroupLayout.PREFERRED_SIZE, 167, javax.swing.GroupLayout.PREFERRED_SIZE)
                        .addGroup(jPanel2Layout.createSequentialGroup()
                            .addGroup(jPanel2Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
                                .addGroup(jPanel2Layout.createSequentialGroup()
                                    .addContainerGap()
                                    .addComponent(jLabel1))
                                .addGroup(jPanel2Layout.createSequentialGroup()
                                    .addGap(6, 6, 6)
                                    .addComponent(jLabel2)))
                            .addGap(14, 14, 14))
                        .addComponent(ButtonSkinEditor, javax.swing.GroupLayout.PREFERRED_SIZE, 167, javax.swing.GroupLayout.PREFERRED_SIZE))
                    .addGroup(jPanel2Layout.createSequentialGroup()
                        .addContainerGap()
                        .addComponent(jLabel3)))
                .addContainerGap(javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
        );
        jPanel2Layout.setVerticalGroup(
            jPanel2Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(jPanel2Layout.createSequentialGroup()
                .addContainerGap()
                .addComponent(jLabel1)
                .addGap(14, 14, 14)
                .addComponent(jLabel2)
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.UNRELATED)
                .addComponent(ButtonSpriteExporter, javax.swing.GroupLayout.PREFERRED_SIZE, 34, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                .addComponent(ButtonColorSwapper, javax.swing.GroupLayout.PREFERRED_SIZE, 34, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                .addComponent(ButtonSkinRender, javax.swing.GroupLayout.PREFERRED_SIZE, 34, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                .addComponent(ButtonSkinEditor, javax.swing.GroupLayout.PREFERRED_SIZE, 34, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED, 349, Short.MAX_VALUE)
                .addComponent(jLabel3)
                .addGap(6, 6, 6))
        );

        jPanel1.add(jPanel2, new org.netbeans.lib.awtextra.AbsoluteConstraints(0, 0, 180, 600));

        jPanel3.setBackground(new java.awt.Color(14, 14, 14));

        javax.swing.GroupLayout jPanel3Layout = new javax.swing.GroupLayout(jPanel3);
        jPanel3.setLayout(jPanel3Layout);
        jPanel3Layout.setHorizontalGroup(
            jPanel3Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGap(0, 0, Short.MAX_VALUE)
        );
        jPanel3Layout.setVerticalGroup(
            jPanel3Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGap(0, 0, Short.MAX_VALUE)
        );

        jPanel1.add(jPanel3, new org.netbeans.lib.awtextra.AbsoluteConstraints(180, 0, 5, 600));

        jPanel4.setBackground(new java.awt.Color(14, 14, 14));

        javax.swing.GroupLayout jPanel4Layout = new javax.swing.GroupLayout(jPanel4);
        jPanel4.setLayout(jPanel4Layout);
        jPanel4Layout.setHorizontalGroup(
            jPanel4Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGap(0, 0, Short.MAX_VALUE)
        );
        jPanel4Layout.setVerticalGroup(
            jPanel4Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGap(0, 0, Short.MAX_VALUE)
        );

        jPanel1.add(jPanel4, new org.netbeans.lib.awtextra.AbsoluteConstraints(383, 0, 5, 600));

        selectSwfButton.setBackground(new java.awt.Color(23, 93, 220));
        selectSwfButton.setBackgroundHover(new java.awt.Color(10, 52, 127));
        selectSwfButton.setIcons(rojeru_san.efectos.ValoresEnum.ICONS.ADD);
        selectSwfButton.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                selectSwfButtonActionPerformed(evt);
            }
        });
        jPanel1.add(selectSwfButton, new org.netbeans.lib.awtextra.AbsoluteConstraints(350, 10, 30, 30));

        BrawlhallaPathB.setBackground(new java.awt.Color(20, 20, 20));
        BrawlhallaPathB.setText("Brawlhalla Path");
        BrawlhallaPathB.setAutoscrolls(true);
        BrawlhallaPathB.setBackgroundHover(new java.awt.Color(10, 10, 10));
        BrawlhallaPathB.setForma(RSMaterialComponent.RSButtonFormaIcon.FORMA.ROUND);
        BrawlhallaPathB.setIcons(rojeru_san.efectos.ValoresEnum.ICONS.FOLDER_OPEN);
        BrawlhallaPathB.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                BrawlhallaPathBActionPerformed(evt);
            }
        });
        jPanel1.add(BrawlhallaPathB, new org.netbeans.lib.awtextra.AbsoluteConstraints(400, 10, 140, 30));

        ModsPathB.setBackground(new java.awt.Color(20, 20, 20));
        ModsPathB.setText("Mods Path");
        ModsPathB.setBackgroundHover(new java.awt.Color(10, 10, 10));
        ModsPathB.setForma(RSMaterialComponent.RSButtonFormaIcon.FORMA.ROUND);
        ModsPathB.setIcons(rojeru_san.efectos.ValoresEnum.ICONS.FOLDER_OPEN);
        ModsPathB.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                ModsPathBActionPerformed(evt);
            }
        });
        jPanel1.add(ModsPathB, new org.netbeans.lib.awtextra.AbsoluteConstraints(400, 50, 140, 30));

        ModsPathP.setBackground(new java.awt.Color(64, 64, 64));
        ModsPathP.setForeground(new java.awt.Color(64, 64, 64));
        ModsPathP.setPreferredSize(new java.awt.Dimension(605, 40));
        ModsPathP.setLayout(new org.netbeans.lib.awtextra.AbsoluteLayout());

        ModsPath.setFont(new java.awt.Font("Roboto", 0, 12)); // NOI18N
        ModsPath.setForeground(new java.awt.Color(255, 255, 255));
        ModsPath.setText("...");
        ModsPathP.add(ModsPath, new org.netbeans.lib.awtextra.AbsoluteConstraints(10, 10, -1, -1));

        jPanel1.add(ModsPathP, new org.netbeans.lib.awtextra.AbsoluteConstraints(550, 50, 340, 30));

        BrawlhallaPathP.setBackground(new java.awt.Color(64, 64, 64));
        BrawlhallaPathP.setForeground(new java.awt.Color(64, 64, 64));
        BrawlhallaPathP.setPreferredSize(new java.awt.Dimension(605, 40));
        BrawlhallaPathP.setLayout(new org.netbeans.lib.awtextra.AbsoluteLayout());

        BrawlhallaPath.setFont(new java.awt.Font("Roboto", 0, 12)); // NOI18N
        BrawlhallaPath.setForeground(new java.awt.Color(255, 255, 255));
        BrawlhallaPath.setText("...");
        BrawlhallaPathP.add(BrawlhallaPath, new org.netbeans.lib.awtextra.AbsoluteConstraints(10, 10, -1, -1));

        jPanel1.add(BrawlhallaPathP, new org.netbeans.lib.awtextra.AbsoluteConstraints(550, 10, 340, 30));

        LOG.setBackground(new java.awt.Color(255, 255, 255));
        LOG.setForeground(new java.awt.Color(255, 255, 255));
        LOG.setText("...");
        jPanel1.add(LOG, new org.netbeans.lib.awtextra.AbsoluteConstraints(410, 580, 190, -1));

        namesScrollPane.setForeground(new java.awt.Color(255, 255, 255));
        namesScrollPane.setHorizontalScrollBarPolicy(javax.swing.ScrollPaneConstants.HORIZONTAL_SCROLLBAR_NEVER);
        namesScrollPane.setColorBackground(new java.awt.Color(30, 30, 30));
        namesScrollPane.setFont(new java.awt.Font("Roboto Medium", 0, 18)); // NOI18N
        jPanel1.add(namesScrollPane, new org.netbeans.lib.awtextra.AbsoluteConstraints(200, 60, 170, 490));

        removeSWFFilterButton.setBackground(new java.awt.Color(30, 30, 30));
        removeSWFFilterButton.setText("Remove Filter");
        removeSWFFilterButton.setColorHover(new java.awt.Color(183, 28, 28));
        removeSWFFilterButton.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                removeSWFFilterButtonActionPerformed(evt);
            }
        });
        jPanel1.add(removeSWFFilterButton, new org.netbeans.lib.awtextra.AbsoluteConstraints(200, 560, 170, 30));

        rSScrollPane1.setBackground(new java.awt.Color(64, 64, 64));
        rSScrollPane1.setVerticalScrollBarPolicy(javax.swing.ScrollPaneConstants.VERTICAL_SCROLLBAR_NEVER);
        rSScrollPane1.setColorBackground(new java.awt.Color(64, 64, 64));

        selectedSwfPath.setFont(new java.awt.Font("Roboto", 0, 12)); // NOI18N
        selectedSwfPath.setForeground(new java.awt.Color(255, 255, 255));
        selectedSwfPath.setText("...");
        rSScrollPane1.setViewportView(selectedSwfPath);

        jPanel1.add(rSScrollPane1, new org.netbeans.lib.awtextra.AbsoluteConstraints(190, 10, 160, 30));

        Export.setBackground(new java.awt.Color(96, 46, 156));
        Export.setText("Export PNG");
        Export.setColorHover(new java.awt.Color(77, 42, 118));
        Export.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                ExportActionPerformed(evt);
            }
        });
        jPanel1.add(Export, new org.netbeans.lib.awtextra.AbsoluteConstraints(410, 530, 120, -1));

        ExportSVG.setText("Export SVG");
        ExportSVG.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                ExportSVGActionPerformed(evt);
            }
        });
        jPanel1.add(ExportSVG, new org.netbeans.lib.awtextra.AbsoluteConstraints(540, 530, 120, -1));

        AllMode.setSelected(true);
        AllMode.setText("All Mode");
        AllMode.setToolTipText("Extract all sprites to a single folder");
        AllMode.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                AllModeActionPerformed(evt);
            }
        });
        jPanel1.add(AllMode, new org.netbeans.lib.awtextra.AbsoluteConstraints(550, 480, 100, -1));

        FolderMode.setText("Folder Mode");
        FolderMode.setToolTipText("Extract the sprites into a folder divided into multiple folders with the skin tags");
        FolderMode.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                FolderModeActionPerformed(evt);
            }
        });
        jPanel1.add(FolderMode, new org.netbeans.lib.awtextra.AbsoluteConstraints(410, 480, 140, -1));

        jSeparator1.setBackground(new java.awt.Color(14, 14, 14));
        jSeparator1.setForeground(new java.awt.Color(14, 14, 14));
        jSeparator1.setOrientation(javax.swing.SwingConstants.VERTICAL);
        jPanel1.add(jSeparator1, new org.netbeans.lib.awtextra.AbsoluteConstraints(670, 490, -1, 80));

        exportSelectionButton.setBackground(new java.awt.Color(0, 105, 92));
        exportSelectionButton.setText("Export SWF");
        exportSelectionButton.setToolTipText("Export SWF in single file");
        exportSelectionButton.setColorHover(new java.awt.Color(0, 77, 64));
        exportSelectionButton.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                exportSelectionButtonActionPerformed(evt);
            }
        });
        jPanel1.add(exportSelectionButton, new org.netbeans.lib.awtextra.AbsoluteConstraints(690, 530, 200, -1));

        Skin.setBackground(new java.awt.Color(255, 255, 255));
        Skin.setFont(new java.awt.Font("Roboto", 0, 24)); // NOI18N
        Skin.setForeground(new java.awt.Color(255, 255, 255));
        Skin.setText("...");
        jPanel1.add(Skin, new org.netbeans.lib.awtextra.AbsoluteConstraints(410, 100, 460, 30));

        javax.swing.GroupLayout layout = new javax.swing.GroupLayout(getContentPane());
        getContentPane().setLayout(layout);
        layout.setHorizontalGroup(
            layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(layout.createSequentialGroup()
                .addComponent(jPanel1, javax.swing.GroupLayout.PREFERRED_SIZE, 900, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addGap(0, 0, Short.MAX_VALUE))
        );
        layout.setVerticalGroup(
            layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addComponent(jPanel1, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
        );

        pack();
    }// </editor-fold>//GEN-END:initComponents

    private void ButtonSkinRenderActionPerformed(java.awt.event.ActionEvent evt) {
        JOptionPane.showMessageDialog(null, "Work In Progress", "WIP", JOptionPane.WARNING_MESSAGE);
    }                                                

    private void ButtonColorSwapperActionPerformed(java.awt.event.ActionEvent evt) {
        JOptionPane.showMessageDialog(null, "Work In Progress", "WIP", JOptionPane.WARNING_MESSAGE);
    }                                                  

    private void ButtonSkinEditorActionPerformed(java.awt.event.ActionEvent evt) {
        JOptionPane.showMessageDialog(null, "Work In Progress", "WIP", JOptionPane.WARNING_MESSAGE);
    }                                                

    private void ButtonSpriteExporterActionPerformed(java.awt.event.ActionEvent evt) {
    }                                                    

    //------------------------------------------------------------------









    // --------------------- EXPORT BUTTONS ----------------------------

    //------------------------ EXPORT PNG ---------------------

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
            SWF selectedSWF = EMethods2.GetSwf(selectedSwfPath.getText(), false);

            try {
                EMethods2.ExtractSprites(Skin.getText(), selectedSWF, SpriteEM, ExportScaleUsed, swfName,
                        isSWF, ExportFolder, modPath);
            } catch (InterruptedException ex) {
                //Logger.getLogger(SimpleSpriteExporter.class.getName()).log(Level.SEVERE, null, ex);
            }
            System.out.println("PNG Exported!");

            LOG.setText("PNG Exported!");

        } else {
            System.out.println("Not exported!");
            LOG.setText("Not exported!");
        }

    }        
    //------------------------------------------------------------------
    



    //------------------------ EXPORT SVG ---------------------

    private void ExportSVGActionPerformed(java.awt.event.ActionEvent evt) {SpriteEM = SpriteExportMode.SVG;
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
            SWF selectedSWF = EMethods2.GetSwf(selectedSwfPath.getText(), false);

            try {
                EMethods2.ExtractSprites(Skin.getText(), selectedSWF, SpriteEM, ExportScaleUsed, swfName,
                        isSWF, ExportFolder, modPath);
            } catch (InterruptedException ex) {
               // Logger.getLogger(SimpleSpriteExporter.class.getName()).log(Level.SEVERE, null, ex);
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



 // -------------------------------------------------------------------------------------------






 // -------------------------------------------------------------------------------------------
 // --------------------- PATHS BUTTONS ------------------------------------------------------
    private void BrawlhallaPathBActionPerformed(java.awt.event.ActionEvent evt) {                                                
        
        JFileChooser chooser = new JFileChooser();
        chooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);
        int returnVal = chooser.showOpenDialog(this);
        if (returnVal == JFileChooser.APPROVE_OPTION) {
            File selectedDirectory = chooser.getSelectedFile();
            String BrawlhallaPathText = selectedDirectory.getAbsolutePath();
            BrawlhallaPath.setText(BrawlhallaPathText);

            gamePathString = BrawlhallaPathText;

            guardarConfiguracion();

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

           modsPathString = ModsPathText;

           guardarConfiguracion();

       }
   }
 // -------------------------------------------------------------------------------------------


 //------------------ CONFIGURACIÓN ------------------------------------------------------------

    private void guardarConfiguracion() {
        Properties properties = new Properties();
        properties.setProperty("gamePathString", gamePathString);
        properties.setProperty("modsPathString", modsPathString);

        // Ubicación del archivo de configuración en la carpeta de AppData del usuario
        String appDataPath = System.getenv("APPDATA");
        String appFolderPath = appDataPath + File.separator + "SimpleSpriteExporter";
    
        // Comprobar si la carpeta de la aplicación existe, si no, crearla
        File appFolder = new File(appFolderPath);
        if (!appFolder.exists()) {
            if (appFolder.mkdirs()) {
                System.out.println("Carpeta de la aplicación creada en " + appFolderPath);
            } else {
                System.err.println("No se pudo crear la carpeta de la aplicación en " + appFolderPath);
            }
        }
    
        String configFile = appFolderPath + File.separator + "config.properties";
    
        try (FileOutputStream fileOut = new FileOutputStream(configFile)) {
            properties.store(fileOut, "Configuración de Mi Aplicación");
            System.out.println("Configuración guardada en " + configFile);
        } catch (IOException e) {
            e.printStackTrace();
            System.err.println("Error al guardar la configuración.");
        }
    }
    
 // -------------------------------------------------------------------------------------------

    private void cargarConfiguracion() {
        String appDataPath = System.getenv("APPDATA");
        String appFolderPath = appDataPath + File.separator + "SimpleSpriteExporter";
        String configFile = appFolderPath + File.separator + "config.properties";

        //Si no hay archivo de configuracion, mostrar un JoptionPane e indicar al usuario que debe seleccionar el gamePath y el modsPath
        if (!Paths.get(configFile).toFile().exists()) {
            JOptionPane.showMessageDialog(null, "It's the first time you open SSE." + "\nPlease select the Brawlhalla and Mods Path.", "Select Paths", JOptionPane.WARNING_MESSAGE);
            return;
        }
        

    
        try (FileInputStream fileIn = new FileInputStream(configFile)) {
            Properties properties = new Properties();
            properties.load(fileIn);
    
            // Obtener el valor de gamePathString desde el archivo de configuración
            gamePathString = properties.getProperty("gamePathString");
            BrawlhallaPath.setText(gamePathString);

            modsPathString = properties.getProperty("modsPathString");
            ModsPath.setText(modsPathString);

        } catch (IOException e) {
            // Si no se puede cargar la configuración, se mantendrá el valor predeterminado
            System.err.println("No se pudo cargar la configuración. Se usará el valor predeterminado.");
        }
    }

// -------------------------------------------------------------------------------------------






// -------------------------------------------------------------------------------------------


    private void removeSWFFilterButtonActionPerformed(java.awt.event.ActionEvent evt) {
        int[] selection = extractorFiltersJList.getSelectedIndices();

                for (int i = 0; i < selection.length; i++) {
                    SimpleSpriteExporter.this.extractorFilters.remove(selection[i] - i);
                }

                SimpleSpriteExporter.this.UpdateFilterJList(extractorFiltersJList);
                SimpleSpriteExporter.this.UpdateFilteredTagsJList(extractorFilteredTags);
    }

//------------------------------- EVENTS ------------------------------


//-------------------------- SELECT SWF BUTTON --------------------------
    

// ------------------------ CELL RENDERER  ------------------------------
    JList<String> namesList = new JList<>();

    DefaultListCellRenderer cellRenderer = new DefaultListCellRenderer() {
        @Override
        public Component getListCellRendererComponent(JList<?> list, Object value, int index, boolean isSelected, boolean cellHasFocus) {
            Component renderer = super.getListCellRendererComponent(list, value, index, isSelected, cellHasFocus);
    
            // Establece el interlineado deseado
            setBorder(BorderFactory.createEmptyBorder(5, 10, 5, 10));
            return renderer;
        }
    };
// -------------------------------------------------------------------------------------------





// ------------------------------- SELECT SWF BUTTON ---------------------------------
        
    private void selectSwfButtonActionPerformed(java.awt.event.ActionEvent evt) {

        if (gamePathString == null) {
            JOptionPane.showMessageDialog(null, "Brawlhalla Path not set", "BrawlhallaPath not set", 0);
            return;
        }

        else {

        
            final JFileChooser brawlPathSWF_FC = new JFileChooser(gamePathString);
        brawlPathSWF_FC.setFileFilter(new FileFilter() {
            public boolean accept(File f) {
                if (f.getName().endsWith(".swf") || f.isDirectory()) {
                    return true;
                }
                return false;
            }

            public String getDescription() {
                return null;
            }
        });
        
        int returnVal = brawlPathSWF_FC.showOpenDialog(null);

                if (returnVal == 0) {
                    selectedSwfPath.setText(brawlPathSWF_FC.getSelectedFile().getAbsolutePath());
                }
        

        SWF selectedSWF = EMethods2.GetSwf(brawlPathSWF_FC.getSelectedFile().getAbsolutePath(), false);
        LOG.setText("Imported: " + brawlPathSWF_FC.getSelectedFile().getName());

        swfName = brawlPathSWF_FC.getSelectedFile().getName();
        selectedSwfPath.setText(brawlPathSWF_FC.getSelectedFile().getAbsolutePath());


        List<String> listNames = EMethods2.GetAllSkinNames((SWF) selectedSWF, 0);

        System.out.println("listNames: " + listNames);

        SimpleSpriteExporter.this.extractorSelectedSwf = EMethods2.GetSwf(selectedSwfPath.getText(), Boolean.valueOf(false));

                if (SimpleSpriteExporter.this.extractorSelectedSwf == null) {
                    JOptionPane.showMessageDialog(null, "Swf failed to load. \n Path: " + selectedSwfPath.getText(),
                            "Failed to load SWF", 0);
                } else {
                    SimpleSpriteExporter.this.UpdateFilteredTagsJList(extractorFilteredTags);
                }

            // Get swf name
            String[] names = new String[listNames.size()];
            listNames.toArray(names);

            namesList.setListData(names);

            namesScrollPane.setViewportView(namesList);
            namesScrollPane.getViewport().getView().setBackground(new Color(30,30,30));
            namesScrollPane.getViewport().getView().setForeground(new Color(255, 255, 255));
            namesScrollPane.getViewport().getView().setFont(new Font("Roboto", 0, 18));
            namesList.setSelectionBackground(new Color(23,93,220));
            namesList.setCursor(new java.awt.Cursor(java.awt.Cursor.HAND_CURSOR));
            namesList.setBorder(null);
            namesList.setCellRenderer(cellRenderer);
            namesList.setFixedCellHeight(40);

            namesList.setLayoutOrientation(JList.VERTICAL);

            System.out.println("Updated!");
            for (String name : names) {
                System.out.println(name);
            }
           
        }
         
    }

// -------------------------------------------------------------------------------------------



// ----------------------------- NAMES LIST -------------------------------------

    private void namesListValueChanged(javax.swing.event.ListSelectionEvent evt) {
        String selectedName = namesList.getSelectedValue();
        LOG.setText("Selected: " + selectedName);
        System.out.println("Selected: " + selectedName);
    
        // Eliminar el filtro anterior
        SimpleSpriteExporter.this.extractorFilters.clear();
        // Actualizar la lista de filtros para reflejar la eliminación del filtro anterior
        SimpleSpriteExporter.this.UpdateFilterJList(extractorFiltersJList);
    
        String filterString = selectedName;
        System.out.println("Filter: " + filterString);
        if (filterString != null) {
            SWFSearchFilter newFilter = new SWFSearchFilter();
            newFilter.paramString = filterString;
            newFilter.type = (SWFSearchFilter.SWFFilterParam.endsWith);
    
            SimpleSpriteExporter.this.extractorFilters.add(newFilter);
    
            // Actualizar la lista de filtros con el nuevo filtro
            SimpleSpriteExporter.this.UpdateFilterJList(extractorFiltersJList);
            // Aplicar el filtro a extractorFilteredTags
            SimpleSpriteExporter.this.UpdateFilteredTagsJList(extractorFilteredTags);
        }

        DefaultListModel<String> model = (DefaultListModel<String>) extractorFilteredTags.getModel();
        
        // Seleccionar todos los elementos
        int[] selectedIndices = new int[model.size()];
        for (int i = 0; i < model.size(); i++) {
            selectedIndices[i] = i;
        }
        extractorFilteredTags.setSelectedIndices(selectedIndices);

        Skin.setText(selectedName);

    }


    //--------------------------------------------------------------------





    //-------------------------- EXPORT SELECTION BUTTON --------------------------
    final JFileChooser saveChooser = new JFileChooser();
    private void exportSelectionButtonActionPerformed(java.awt.event.ActionEvent evt) { 
        String selectedName = namesList.getSelectedValue();
        System.out.println("Selected Skin: " + selectedName);
    
        if (SimpleSpriteExporter.this.extractorSelectedSwf == null) {
            JOptionPane.showMessageDialog(null, "No SWF selected", "No SWF Selected", 0);
        } else if (SimpleSpriteExporter.this.extractorSelectedSwf != null) {
            String swfName = selectedSwfPath.getText();
    
            if (swfName.contains(SimpleSpriteExporter.gamePathString)) {
                swfName = swfName.substring(SimpleSpriteExporter.gamePathString.length());
            } else {
                System.out.println(swfName);
                swfName = swfName.substring(swfName.lastIndexOf("\\"));
            }
    
            List<String> assetsToExtract = new ArrayList<>();
    
            for (int i = 0; i < (extractorFilteredTags.getSelectedIndices()).length; i++) {
                assetsToExtract.add(extractorFilteredTags.getModel()
                        .getElementAt(extractorFilteredTags.getSelectedIndices()[i]));
            }
    
            SWF generatedSwf = EMethods2.ExportMod(assetsToExtract, SimpleSpriteExporter.this.extractorSelectedSwf, swfName);
    
            // Crear un nuevo JFileChooser con la ubicación inicial deseada
            JFileChooser saveChooser = new JFileChooser(ModsPath.getText());
    
            int shouldSave = saveChooser.showSaveDialog(null);
    
            if (shouldSave == 0) {
                String savePath = saveChooser.getSelectedFile().getAbsolutePath();
    
                System.out.println(saveChooser.getSelectedFile().getName());
                if (!saveChooser.getSelectedFile().getName().endsWith(".swf")) {
                    savePath = String.valueOf(savePath) + ".swf";
                }
    
                try {
                    EMethods2.SaveSwfTo(generatedSwf, savePath);
    
                    try {
                        if (Desktop.isDesktopSupported()) {
                            Desktop.getDesktop()
                                    .open(Paths.get(savePath, new String[0]).toFile().getParentFile());
                            System.out.println("desktop is supported");
                        } else {
                            JOptionPane.showMessageDialog(null, "SWF saved successfully to " + savePath,
                                    "SWF Saving Succeeded", 1);
                            System.out.println("desktop is not supported");
                        }
                    } catch (IOException e2) {
                        System.out.println(e2);
                    }
    
                } catch (FileNotFoundException e1) {
    
                    JOptionPane.showMessageDialog(null, "Failed to save SWF", "SWF Saving Failed", 0);
                    e1.printStackTrace();
                }
            }
        }
    }
    //--------------------------------------------------------------------




    //-------------------------- FILTROS -------------------------------------

    public void UpdateFilterJList(JList<String> list) {
        DefaultListModel<String> model = (DefaultListModel) list.getModel();
        model.removeAllElements();

        for (int i = 0; i < this.extractorFilters.size(); i++) {
            model.addElement(String.valueOf(((SWFSearchFilter) this.extractorFilters.get(i)).type.toString()) + " : "
                    + ((SWFSearchFilter) this.extractorFilters.get(i)).paramString);
        }


    }

    void UpdateFilteredTagsJList(JList<String> list) {
        // Obtener el modelo de datos del JList
        DefaultListModel<String> model = (DefaultListModel) list.getModel();
        // Limpiar el modelo de elementos anteriores
        model.removeAllElements();
    
        // Verificar si no hay ningún archivo SWF seleccionado
        if (this.extractorSelectedSwf == null) {
            return; // Salir de la función si no hay nada que mostrar
        }
    
        // Verificar si no hay filtros aplicados
        if (this.extractorFilters.size() == 0) {
            // Obtener la lista de etiquetas del archivo SWF seleccionado
            ReadOnlyTagList allTags = this.extractorSelectedSwf.getTags();
    
            // Iterar a través de las etiquetas del archivo SWF
            for (int i = 0; i < allTags.size(); i++) {
                // Verificar si la etiqueta es de tipo DefineSpriteTag
                if (allTags.get(i) instanceof DefineSpriteTag) {
                    // Obtener el nombre de clase de la etiqueta
                    String className = ((DefineSpriteTag) allTags.get(i)).getClassName();
                    if (className != null) {
                        // Agregar el nombre de clase al modelo (nombre completo)
                        model.addElement(className);
                    }
                }
            }
        } else {
            // Obtener la lista de etiquetas del archivo SWF seleccionado
            ReadOnlyTagList allTags = this.extractorSelectedSwf.getTags();
    
            // Iterar a través de las etiquetas del archivo SWF
            for (int i = 0; i < allTags.size(); i++) {
                // Verificar si la etiqueta es de tipo DefineSpriteTag
                if (allTags.get(i) instanceof DefineSpriteTag) {
                    // Obtener el nombre de clase de la etiqueta
                    String className = ((DefineSpriteTag) allTags.get(i)).getClassName();
                    if (className != null) {
                        // Inicializar una bandera para verificar si la etiqueta cumple con los filtros
                        Boolean fitsFilter = Boolean.valueOf(true);
                        // Iterar a través de los filtros
                        for (int fil = 0; fil < this.extractorFilters.size(); fil++) {
                            // Verificar si la etiqueta no cumple con el filtro actual
                            if (!((SWFSearchFilter) this.extractorFilters.get(fil)).checkSWFExtractParam(className,
                                    true)) {
                                fitsFilter = Boolean.valueOf(false);
                                // Salir del bucle si la etiqueta no cumple con el filtro actual
                                break;
                            }
                        }
                        // Verificar si la etiqueta cumple con todos los filtros
                        if (fitsFilter.booleanValue()) {
                            // Agregar el nombre de clase al modelo (nombre completo)
                            model.addElement(className);
                        }
                    }
                }
            }
        }
    }
    
    //--------------------------------------------------------------------




    /**
     * @param args the command line arguments
     */
    public static void main(String args[]) {
        /* Set the Nimbus look and feel */
        //<editor-fold defaultstate="collapsed" desc=" Look and feel setting code (optional) ">
        /* If Nimbus (introduced in Java SE 6) is not available, stay with the default look and feel.
         * For details see http://download.oracle.com/javase/tutorial/uiswing/lookandfeel/plaf.html 
         */
        try {
            for (javax.swing.UIManager.LookAndFeelInfo info : javax.swing.UIManager.getInstalledLookAndFeels()) {
                if ("Windows".equals(info.getName())) {
                    javax.swing.UIManager.setLookAndFeel(info.getClassName());
                    break;
                }
                System.out.println(info);
            }
        } catch (ClassNotFoundException ex) {
            java.util.logging.Logger.getLogger(SimpleSpriteExporter.class.getName()).log(java.util.logging.Level.SEVERE, null, ex);
        } catch (InstantiationException ex) {
            java.util.logging.Logger.getLogger(SimpleSpriteExporter.class.getName()).log(java.util.logging.Level.SEVERE, null, ex);
        } catch (IllegalAccessException ex) {
            java.util.logging.Logger.getLogger(SimpleSpriteExporter.class.getName()).log(java.util.logging.Level.SEVERE, null, ex);
        } catch (javax.swing.UnsupportedLookAndFeelException ex) {
            java.util.logging.Logger.getLogger(SimpleSpriteExporter.class.getName()).log(java.util.logging.Level.SEVERE, null, ex);
        }
        //</editor-fold>
        //</editor-fold>

        /* Create and display the form */
        java.awt.EventQueue.invokeLater(new Runnable() {
            public void run() {
                try {
                    UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
                } catch (ClassNotFoundException | InstantiationException | IllegalAccessException
                        | UnsupportedLookAndFeelException ex) {
                    //Logger.getLogger(SimpleSpriteExporter.class.getName()).log(Level.SEVERE, null, ex);
                }
                new SimpleSpriteExporter().setVisible(true);
            }
        });
    }

    // Variables declaration - do not modify//GEN-BEGIN:variables
    private rojerusan.RSCheckBox AllMode;
    private javax.swing.JLabel BrawlhallaPath;
    private RSMaterialComponent.RSButtonFormaIcon BrawlhallaPathB;
    private javax.swing.JPanel BrawlhallaPathP;
    private RSMaterialComponent.RSButtonFormaIcon ButtonColorSwapper;
    private RSMaterialComponent.RSButtonFormaIcon ButtonSkinEditor;
    private RSMaterialComponent.RSButtonFormaIcon ButtonSkinRender;
    private RSMaterialComponent.RSButtonFormaIcon ButtonSpriteExporter;
    private rojeru_san.rsbutton.RSButtonRound Export;
    private rojeru_san.rsbutton.RSButtonRound ExportSVG;
    private rojerusan.RSCheckBox FolderMode;
    private javax.swing.JLabel LOG;
    private javax.swing.JLabel ModsPath;
    private RSMaterialComponent.RSButtonFormaIcon ModsPathB;
    private javax.swing.JPanel ModsPathP;
    private javax.swing.JLabel Skin;
    private rojeru_san.rsbutton.RSButtonRound exportSelectionButton;
    private javax.swing.JLabel jLabel1;
    private javax.swing.JLabel jLabel2;
    private javax.swing.JLabel jLabel3;
    private javax.swing.JPanel jPanel1;
    private javax.swing.JPanel jPanel2;
    private javax.swing.JPanel jPanel3;
    private javax.swing.JPanel jPanel4;
    private javax.swing.JSeparator jSeparator1;
    private necesario.RSScrollPane namesScrollPane;
    private necesario.RSScrollPane rSScrollPane1;
    private rojeru_san.RSButton removeSWFFilterButton;
    private RSMaterialComponent.RSButtonIconUno selectSwfButton;
    private javax.swing.JLabel selectedSwfPath;
    // End of variables declaration//GEN-END:variables
    //--------------------------------------------------------------------

    





    //-------------------------- CUSTOM METHODS --------------------------
}
