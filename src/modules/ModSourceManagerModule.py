"""
Mod Source Manager Module
Gestiona y visualiza todos los proyectos de mods en una cuadrícula
Permite acceso rápido a las carpetas de cada proyecto
"""

from src.utils import get_project_root
import os
import shutil
import json
import threading
import customtkinter as ctk
from .ToolModuleBase import ToolModule
from PIL import Image
from datetime import datetime
from src.utils.ThemeManager import BMTTheme, ACCENTS


class ModSourceManagerModule(ToolModule):
    """Módulo de Mod Source Manager - Launcher de proyectos"""
    
    def __init__(self, parent, game_path, mods_path, icons=None):
        super().__init__(parent, game_path, mods_path, icons=icons)
        
        # Cargar configuración guardada
        self.config_path = os.path.join(os.getenv('APPDATA'), 'Brawlhalla Modding Toolkit', 'ModSourceManager.json')
        saved_path = self.load_saved_path()
        
        # Usar ruta guardada o mods_path por defecto
        self.mod_sources_path = saved_path if saved_path else mods_path
        
        self.projects = []
        self.filtered_projects = []
        self.sort_mode = "date_created"  # Por defecto ordenar por fecha de creación
        self.grid_frame = None
        self.default_render = None
        self.project_cache = {}  # Cache para optimizar carga
        self.image_cache = {}  # Cache para imágenes cargadas
        self.search_var = ctk.StringVar()  # Variable para búsqueda
        self.search_var.trace_add("write", lambda *args: self.filter_projects())
        
        # Paths para caches
        self.cache_dir = os.path.join(os.getenv('APPDATA'), 'Brawlhalla Modding Toolkit', 'Cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        self.projects_cache_file = os.path.join(self.cache_dir, 'ModSourceProjects.json')
        
        # Cargar cache de proyectos si existe
        self.load_projects_from_cache()
        
    def get_tool_name(self):
        return "Mod Source Manager"
    
    def get_tool_icon(self):
        return ""
    
    def load_default_render(self):
        """Carga la imagen por defecto RenderDefault.png"""
        try:
            from pathlib import Path
            default_path = get_project_root() / "resources" / "assets" / "frame0" / "RenderDefault.png"
            if default_path.exists():
                img = Image.open(default_path)
                # Escalar manteniendo aspect ratio 16:9
                img.thumbnail((256, 144), Image.Resampling.LANCZOS)
                self.default_render = ctk.CTkImage(light_image=img, dark_image=img, size=(256, 144))
            else:
                # Crear imagen placeholder si no existe
                self.default_render = None
        except Exception as e:
            print(f"Error loading default render: {e}")
            self.default_render = None
    
    def create_ui(self):
        """Crea la interfaz del Mod Source Manager"""
        self.container = ctk.CTkFrame(self.parent, fg_color=BMTTheme.BG_DARK)
        
        # Frame principal
        main_frame = ctk.CTkFrame(self.container, fg_color=BMTTheme.BG_DARK)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Cargar imagen por defecto
        self.load_default_render()
        
        # Cargar proyectos desde cache o escanear si está vacío
        if not self.projects and self.mod_sources_path and os.path.exists(self.mod_sources_path):
            self.scan_projects()
        else:
            self.apply_sort()
        
        # ===== HEADER =====
        header_frame = ctk.CTkFrame(main_frame, fg_color="#171717", corner_radius=10)
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Título y botón de ruta
        top_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        top_row.pack(fill="x", padx=20, pady=15)
        
        title = ctk.CTkLabel(
            top_row,
            text="Mod Source Manager",
            font=BMTTheme.get_font(24, "bold"),
        )
        BMTTheme.style_title(title, color=ACCENTS["Mod Source Manager"])
        title.pack(side="left")
        
        # Botón seleccionar carpeta
        select_folder_btn = ctk.CTkButton(
            top_row,
            text="Select Mod Sources Folder",
            height=35,
        )
        BMTTheme.style_primary_button(select_folder_btn, color=ACCENTS["Mod Source Manager"])
        select_folder_btn.configure(command=self.select_mod_sources_folder)
        select_folder_btn.pack(side="right", padx=5)
        
        # Botón crear nuevo mod
        create_mod_btn = ctk.CTkButton(
            top_row,
            text="Create New Mod",
            height=35,
        )
        BMTTheme.style_primary_button(create_mod_btn, color=BMTTheme.GREEN)
        create_mod_btn.configure(command=self.create_new_mod)
        create_mod_btn.pack(side="right", padx=5)
        
        # Botón Refrescar
        refresh_btn = ctk.CTkButton(
            top_row,
            text="Refresh",
            height=35,
            width=100
        )
        BMTTheme.style_primary_button(refresh_btn, color=BMTTheme.BLUE_GREY)
        refresh_btn.configure(command=self.scan_projects)
        refresh_btn.pack(side="right", padx=5)
        
        # Ruta actual
        path_text = self.mod_sources_path if self.mod_sources_path else "No folder selected"
        self.path_label = ctk.CTkLabel(
            header_frame,
            text=f"{path_text}",
            font=BMTTheme.get_font(12),
            text_color="#757575"
        )
        self.path_label.pack(padx=20, pady=(0, 10))
        
        # ===== FILTROS Y ORDENAMIENTO =====
        filter_frame = ctk.CTkFrame(main_frame, fg_color="#171717", corner_radius=10)
        filter_frame.pack(fill="x", pady=(0, 20))
        
        filter_content = ctk.CTkFrame(filter_frame, fg_color="transparent")
        filter_content.pack(fill="x", padx=20, pady=15)
        
        # Barra de búsqueda
        search_container = ctk.CTkFrame(filter_content, fg_color="transparent")
        search_container.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(
            search_container,
            text="Search:",
            font=BMTTheme.get_font(14, "bold"),
            text_color="#9E9E9E"
        ).pack(side="left", padx=(0, 10))
        
        self.search_entry = ctk.CTkEntry(
            search_container,
            placeholder_text="Search mods...",
            width=200,
            height=32,
            textvariable=self.search_var
        )
        self.search_entry.pack(side="left")
        
        # Label de ordenamiento
        ctk.CTkLabel(
            filter_content,
            text="Sort by:",
            font=BMTTheme.get_font(14, "bold"),
            text_color="#9E9E9E"
        ).pack(side="left", padx=(0, 10))
        
        # Botones de ordenamiento
        sort_buttons = [
            ("A-Z", "alphabetical", "AZ"),
            ("Date Modified", "date_modified", "DM"),
            ("Date Created", "date_created", "DC")
        ]
        
        self.sort_buttons_widgets = {}
        for label, mode, icon in sort_buttons:
            btn = ctk.CTkButton(
                filter_content,
                text=f"{icon} {label}",
                font=ctk.CTkFont(size=13),
                height=32,
                width=140,
                fg_color="#424242" if mode != self.sort_mode else "#00BCD4",
                hover_color="#616161" if mode != self.sort_mode else "#00838F",
                command=lambda m=mode: self.change_sort_mode(m)
            )
            btn.pack(side="left", padx=5)
            self.sort_buttons_widgets[mode] = btn
        
        # Separador (no mostrar botón refrescar, será automático)
        
        # ===== GRID DE PROYECTOS =====
        # Frame scrollable para la cuadrícula
        self.scroll_frame = ctk.CTkScrollableFrame(
            main_frame,
            fg_color="#171717",
            corner_radius=10
        )
        self.scroll_frame.pack(fill="both", expand=True)
        
        # Grid container
        self.grid_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Frame de loading
        self.loading_frame = ctk.CTkFrame(self.grid_frame, fg_color="transparent")
        
        # Progress bar
        self.progress_label = ctk.CTkLabel(
            self.loading_frame,
            text="",
            font=ctk.CTkFont(family="Roboto", size=14),
            text_color="#00BCD4"
        )
        
        self.progress_bar = ctk.CTkProgressBar(
            self.loading_frame,
            width=400,
            height=20,
            fg_color="#2C2C2C",
            progress_color="#00BCD4"
        )
        
        # Mensaje inicial
        if self.mod_sources_path and os.path.exists(self.mod_sources_path):
            # Si ya hay ruta, no mostrar mensaje
            pass
        else:
            self.empty_message = ctk.CTkLabel(
                self.grid_frame,
                text="Select a Mod Sources folder to get started\n\nClick 'Select Mod Sources Folder' above",
                font=ctk.CTkFont(size=16),
                text_color="#757575"
            )
            self.empty_message.pack(pady=100)
        
        return self.container
    
    def load_saved_path(self):
        """Carga la ruta guardada de la configuración"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('mod_sources_path', '')
        except Exception as e:
            print(f"Error loading saved path: {e}")
        return ''
    
    def save_path(self):
        """Guarda la ruta actual en la configuración"""
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            config = {
                'mod_sources_path': self.mod_sources_path
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving path: {e}")
    
    def select_mod_sources_folder(self):
        """Selecciona la carpeta de mod sources"""
        folder = ctk.filedialog.askdirectory(title="Select Mod Sources Folder")
        if folder:
            self.mod_sources_path = folder
            self.path_label.configure(text=f"{folder}")
            self.save_path()  # Guardar la ruta seleccionada
            self.scan_projects()
    
    def scan_projects(self):
        """Escanea la carpeta de mod sources y encuentra todos los proyectos"""
        if not self.mod_sources_path or not os.path.exists(self.mod_sources_path):
            return
        
        # Mostrar loading
        self.show_loading()
        
        # Run scanning in a background thread to avoid blocking the UI
        threading.Thread(target=self._scan_projects_bg, daemon=True).start()
    
    def _scan_projects_bg(self):
        """Background thread: scan folders and collect project data without blocking UI."""
        projects = []
        
        try:
            items = os.listdir(self.mod_sources_path)
            
            folders = []
            for item in items:
                item_path = os.path.join(self.mod_sources_path, item)
                if os.path.isdir(item_path):
                    folders.append((item, item_path))
            
            total_folders = len(folders)
            # Only update progress every ~5% to avoid excessive UI overhead
            update_interval = max(1, total_folders // 20)
            
            for idx, (name, item_path) in enumerate(folders):
                # Update UI progress occasionally (not every iteration)
                if idx % update_interval == 0 or idx == total_folders - 1:
                    self._bg_update_progress(idx + 1, total_folders, f"Scanning: {name}")
                
                render_path = os.path.join(item_path, "Render.png")
                has_render = os.path.exists(render_path)
                
                # Usar cache para fechas si está disponible
                cache_key = item_path
                if cache_key in self.project_cache:
                    cached = self.project_cache[cache_key]
                    current_mtime = os.path.getmtime(item_path)
                    if cached['mtime'] == current_mtime:
                        project_data = cached['data'].copy()
                        project_data['render_path'] = render_path if has_render else None
                        projects.append(project_data)
                        continue
                
                date_created = os.path.getctime(item_path)
                date_modified = os.path.getmtime(item_path)
                
                project_data = {
                    'name': name,
                    'path': item_path,
                    'render_path': render_path if has_render else None,
                    'date_created': date_created,
                    'date_modified': date_modified
                }
                
                self.project_cache[cache_key] = {
                    'mtime': date_modified,
                    'data': project_data.copy()
                }
                
                projects.append(project_data)
            
            self.projects = projects
            
            # Finish on main thread
            if hasattr(self, 'container') and self.container:
                self.container.after(0, self._finish_scan)
            
        except Exception as e:
            print(f"Error scanning projects: {e}")
            if hasattr(self, 'container') and self.container:
                self.container.after(0, self.hide_loading)
    
    def _bg_update_progress(self, current, total, message):
        """Thread-safe progress update via after()."""
        if hasattr(self, 'container') and self.container:
            try:
                self.container.after(0, lambda c=current, t=total, m=message: 
                    self.update_loading_progress(c, t, m))
            except Exception:
                pass
    
    def _finish_scan(self):
        """Called on main thread after background scan completes."""
        self.hide_loading()
        self.apply_sort()
    
    def show_loading(self):
        """Muestra la barra de progreso"""
        # Limpiar grid
        if self.grid_frame and self.grid_frame.winfo_exists():
            for widget in self.grid_frame.winfo_children():
                widget.destroy()
        
        # Mostrar loading frame
        if hasattr(self, 'loading_frame') and self.loading_frame.winfo_exists():
            self.loading_frame.pack(expand=True, pady=100)
            self.progress_label.pack(pady=(0, 20))
            self.progress_bar.pack()
            self.progress_bar.set(0)
    
    def hide_loading(self):
        """Oculta la barra de progreso"""
        if hasattr(self, 'loading_frame') and self.loading_frame.winfo_exists():
            self.loading_frame.pack_forget()
    
    def update_loading_progress(self, current, total, message):
        """Actualiza el progreso de carga"""
        if not hasattr(self, 'progress_bar') or not hasattr(self, 'progress_label'):
            return
        
        try:
            if total > 0 and self.progress_bar.winfo_exists() and self.progress_label.winfo_exists():
                progress = current / total
                self.progress_bar.set(progress)
                self.progress_label.configure(
                    text=f"{message}\n{current}/{total} folders found"
                )
                # Use update_idletasks instead of update to avoid re-entrancy
                self.progress_bar.update_idletasks()
        except Exception:
            pass
    
    def apply_sort(self):
        """Aplica el ordenamiento seleccionado"""
        # Primero ordenar todos los proyectos
        if self.sort_mode == "alphabetical":
            sorted_projects = sorted(self.projects, key=lambda x: x['name'].lower())
        elif self.sort_mode == "date_modified":
            sorted_projects = sorted(self.projects, key=lambda x: x['date_modified'], reverse=True)
        elif self.sort_mode == "date_created":
            sorted_projects = sorted(self.projects, key=lambda x: x['date_created'], reverse=True)
        else:
            sorted_projects = self.projects
        
        # Aplicar filtro de búsqueda
        search_text = self.search_var.get().lower().strip()
        
        if not search_text:
            # Si no hay búsqueda, mostrar todos
            self.filtered_projects = sorted_projects
        else:
            # Filtrar por coincidencias parciales
            self.filtered_projects = [
                p for p in sorted_projects 
                if search_text in p['name'].lower()
            ]
        
        # Actualizar grid
        self.update_grid()
    
    def filter_projects(self):
        """Filtra proyectos basándose en el texto de búsqueda (llamado por StringVar)"""
        # Simplemente reaplicar el ordenamiento, que incluye el filtro
        self.apply_sort()
    
    def change_sort_mode(self, mode):
        """Cambia el modo de ordenamiento"""
        self.sort_mode = mode
        
        # Actualizar colores de botones
        for btn_mode, btn_widget in self.sort_buttons_widgets.items():
            if btn_mode == mode:
                btn_widget.configure(fg_color="#00BCD4", hover_color="#00838F")
            else:
                btn_widget.configure(fg_color="#424242", hover_color="#616161")
        
        # Aplicar ordenamiento
        self.apply_sort()
    
    def update_grid(self):
        """Actualiza la cuadrícula de proyectos"""
        # Verificar que grid_frame existe
        if not self.grid_frame or not self.grid_frame.winfo_exists():
            return
        
        # Limpiar grid actual
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        
        if not self.filtered_projects:
            self.empty_message = ctk.CTkLabel(
                self.grid_frame,
                text="No projects found in this folder\n\nMake sure the folder contains mod projects",
                font=ctk.CTkFont(size=16),
                text_color="#757575"
            )
            self.empty_message.pack(pady=100)
            return
        
        # Configurar grid (4 columnas para tarjetas menos anchas)
        columns = 4
        for i in range(columns):
            self.grid_frame.grid_columnconfigure(i, weight=1, uniform="col")
        
        # Crear cards para cada proyecto
        for idx, project in enumerate(self.filtered_projects):
            row = idx // columns
            col = idx % columns
            
            self.create_project_card(project, row, col)
    
    def create_project_card(self, project, row, col):
        """Crea una tarjeta de proyecto"""
        # Frame de la tarjeta
        card = ctk.CTkFrame(
            self.grid_frame,
            fg_color="#212121",
            corner_radius=10,
            cursor="hand2"
        )
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        # Click en toda la tarjeta
        card.bind("<Button-1>", lambda e, p=project['path']: self.open_project_folder(p))
        
        # Imagen de render
        image_frame = ctk.CTkFrame(card, fg_color="#2C2C2C", corner_radius=8)
        image_frame.pack(padx=10, pady=(10, 5))
        
        # Usar cache de imágenes para evitar recargar
        render_img = None
        cache_key = project['render_path'] if project['render_path'] else 'default'
        
        if cache_key in self.image_cache:
            render_img = self.image_cache[cache_key]
        else:
            try:
                if project['render_path'] and os.path.exists(project['render_path']):
                    img = Image.open(project['render_path'])
                    # Escalar manteniendo aspect ratio 16:9 a tamaño más grande
                    img.thumbnail((256, 144), Image.Resampling.LANCZOS)
                    render_img = ctk.CTkImage(light_image=img, dark_image=img, size=(256, 144))
                    self.image_cache[cache_key] = render_img
                else:
                    render_img = self.default_render
            except Exception as e:
                print(f"Error loading image for {project['name']}: {e}")
                render_img = None
        
        if render_img:
            img_label = ctk.CTkLabel(
                image_frame,
                image=render_img,
                text=""
            )
            img_label.pack(padx=5, pady=5)
            img_label.bind("<Button-1>", lambda e, p=project['path']: self.open_project_folder(p))
        else:
            # Placeholder si no hay imagen
            placeholder = ctk.CTkLabel(
                image_frame,
                text="No Image",
                font=ctk.CTkFont(size=16),
                text_color="#757575",
                width=256,
                height=144
            )
            placeholder.pack(padx=5, pady=5)
            placeholder.bind("<Button-1>", lambda e, p=project['path']: self.open_project_folder(p))
        
        # Nombre del proyecto
        name_label = ctk.CTkLabel(
            card,
            text=project['name'],
            font=BMTTheme.get_font(16, "bold"),
            text_color="#FFFFFF",
            wraplength=250
        )
        name_label.pack(pady=(8, 3))
        name_label.bind("<Button-1>", lambda e, p=project['path']: self.open_project_folder(p))
        
        # Fecha de modificación
        date_modified = datetime.fromtimestamp(project['date_modified']).strftime("%d/%m/%Y")
        date_label = ctk.CTkLabel(
            card,
            text=f"Modified: {date_modified}",
            font=BMTTheme.get_font(10),
            text_color="#757575"
        )
        date_label.pack(pady=(0, 12))
        date_label.bind("<Button-1>", lambda e, p=project['path']: self.open_project_folder(p))
        
        # Hover effect
        def on_enter(e):
            card.configure(fg_color="#2C2C2C")
        
        def on_leave(e):
            card.configure(fg_color="#212121")
        
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        image_frame.bind("<Enter>", on_enter)
        image_frame.bind("<Leave>", on_leave)
    
    def open_project_folder(self, folder_path):
        """Abre la carpeta del proyecto en el explorador de archivos"""
        try:
            if os.path.exists(folder_path):
                # Abrir en explorador de Windows usando os.startfile
                os.startfile(folder_path)
            else:
                print(f"Folder not found: {folder_path}")
        except Exception as e:
            print(f"Error opening folder: {e}")
    
    def create_new_mod(self):
        """Crea un nuevo proyecto de mod"""
        if not self.mod_sources_path or not os.path.exists(self.mod_sources_path):
            # Mostrar mensaje de error simple
            print("Error: Please select a Mod Sources folder first!")
            return
        
        # Pedir nombre del mod
        dialog = ctk.CTkInputDialog(
            text="Enter the name for the new mod:",
            title="Create New Mod"
        )
        mod_name = dialog.get_input()
        
        if not mod_name or mod_name.strip() == "":
            return  # Cancelado o vacío
        
        mod_name = mod_name.strip()
        
        # Crear carpeta del mod
        mod_folder = os.path.join(self.mod_sources_path, mod_name)
        
        if os.path.exists(mod_folder):
            # Ya existe
            print(f"Error: A mod with the name '{mod_name}' already exists!")
            return
        
        try:
            # Crear carpeta
            os.makedirs(mod_folder, exist_ok=True)
            
            # Copiar archivos de template
            render_template = os.path.join("resources", "assets", "frame0", "Render.mdp")
            screenshots_template = os.path.join("resources", "assets", "frame0", "Screenshots.mdp")
            
            if os.path.exists(render_template):
                shutil.copy2(render_template, os.path.join(mod_folder, "Render.mdp"))
            
            if os.path.exists(screenshots_template):
                shutil.copy2(screenshots_template, os.path.join(mod_folder, "Screenshots.mdp"))
            
            # Refrescar lista de proyectos
            self.scan_projects()
            
            # Abrir la carpeta del nuevo mod
            os.startfile(mod_folder)
            
            print(f"Mod '{mod_name}' created successfully!")
            
        except Exception as e:
            print(f"Error creating mod: {e}")
    
    def load_projects_from_cache(self):
        """Carga la lista de proyectos desde el archivo de cache"""
        try:
            if os.path.exists(self.projects_cache_file):
                with open(self.projects_cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    # Verificar si la ruta base es la misma
                    if cached_data.get('base_path') == self.mod_sources_path:
                        self.projects = cached_data.get('projects', [])
                        print(f"[OK] Loaded {len(self.projects)} projects from cache")
        except Exception as e:
            print(f"Error loading projects cache: {e}")

    def save_projects_to_cache(self):
        """Guarda la lista actual de proyectos en el archivo de cache"""
        try:
            cache_data = {
                'base_path': self.mod_sources_path,
                'last_scan': datetime.now().isoformat(),
                'projects': self.projects
            }
            with open(self.projects_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=4)
        except Exception as e:
            print(f"Error saving projects cache: {e}")

    def show(self):
        """Muestra el módulo"""
        if hasattr(self, 'container') and self.container:
            self.container.pack(fill="both", expand=True)
        
        # No refrescar automáticamente para usar el cache, 
        # a menos que esté totalmente vacío
        if not self.projects and self.mod_sources_path and os.path.exists(self.mod_sources_path):
            self.scan_projects()
        else:
            self.apply_sort()

    def _finish_scan(self):
        """Called on main thread after background scan completes."""
        self.hide_loading()
        self.save_projects_to_cache() # Guardar en cache al terminar
        self.apply_sort()
