# Brawlhalla Modding Toolkit

**BMT** is the ultimate multi-tool designed to streamline and enhance the Brawlhalla modding experience. With a comprehensive suite of powerful features, it provides a seamless workflow for creators to modify game assets efficiently.

---

## Modules Overview

### Sprite Exporter
The Sprite Exporter simplifies and accelerates the modding process by allowing you to easily export Sprites, Shapes, or SWF files.

![Sprite Exporter](wiki/sprite%20Exporter/1.png)

**How to Use:**
Select a legend from the legend selector, then choose a skin from the left panel to export it in your desired format. *(Note: If a specific legend, skin, or weapon is not available in the quick selector, you can load it manually.)*

**Export Modes:**
* **Sprite Mode:** Exports all sprites into a designated folder, providing functionality similar to FFDEC.
* **Shape Mode:** Exports all shapes into a designated folder, providing functionality similar to FFDEC.
* **SWF Mode:** Exports and cleans an SWF file to include exclusively the assets of the selected skin. Normally, opening a raw `.swf` file reveals hundreds of shapes from various skins. This mode filters out unrelated assets, generating a clean and simple `.swf` file containing only the selected skin.

![SWF Mode Comparison](wiki/sprite%20Exporter/2.png)

### Reference Loader
The Reference Loader allows you to effortlessly load and manage reference images or files, ensuring accurate alignment and proportion when designing custom mods or redesigning existing assets.

### Color Converter
The Color Converter is a specialized utility for translating and adapting color values (HEX, INT, RGB) to match Brawlhalla's native formats, enabling precise color swapping and palette adjustments.

### Fast Shape Replacer
The Fast Shape Replacer streamlines the process of injecting new vector shapes into the game's SWF files. It automates the replacement process, saving significant time when updating complex character assets.

### Skin Editor
The Skin Editor provides a robust, visual interface for modifying character skins. Powered by a high-performance vector rendering engine, it allows you to preview and edit infinite-quality SVGs directly within the toolkit.

### Lang Editor
The Lang Editor is a dedicated tool for reading, parsing, and injecting modifications into the game's text strings (XML/BIN), making language and UI text adjustments seamless.

### SVG Maker
The SVG Maker facilitates the creation and post-processing of SVG files, optimizing paths and nodes to ensure compatibility and high performance when injected back into the game engine.

---

## Acknowledgments and Licenses

Brawlhalla Modding Toolkit utilizes the following open-source libraries and projects. We are grateful for their contributions to the development community.

* **[FFDEC (JPEXS Free Flash Decompiler)](https://github.com/jindrapetrik/jpexs-decompiler)** - The core system that allows decompiling, extracting, and injecting sprites/shapes into Brawlhalla's SWF files.
* **[Skia Engine (skia-python)](https://github.com/kyamagu/skia-python)** - High-performance vector rendering engine used in the Skin Editor for infinite-quality SVGs and GPU caching.
* **[CustomTkinter (CTK)](https://github.com/TomSchimansky/CustomTkinter)** - Modern UI library for Python, bringing this beautiful and responsive design to life.
* **[CTK Color Picker](https://github.com/kandelucky/ctk-color-picker)** - Advanced color selector (HEX, INT, RGB) seamlessly integrated with CustomTkinter for the Color Swapper.
* **[Brawlhalla Language Edit](https://github.com/bucccket/BrawlhallaLanguageEdit) & [Lang Reader](https://github.com/allhailcheese/BrawlhallaLangReader)** - Parsing and injection tools used to read and modify the game's text strings (XML/BIN).
* **[Cairo](https://github.com/Kozea/cairosvg) & [Resvg](https://github.com/linebender/resvg)** - Auxiliary libraries for 2D vector parsing and rendering.
* **[JPype1 & Py4J](https://github.com/jpype-project/jpype)** - Communication bridges between the Python frontend and the FFDEC Java backend.

*Original concept based on [Epicsninja BrawlhallaModTools](https://github.com/Epicsninja/BrawlhallaModTools) and Python Implementation based on [BhModCreator](https://github.com/Farbigoz/BhModCreator).*
