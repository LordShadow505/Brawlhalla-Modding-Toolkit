"""
Clase Base para Módulos de Herramientas
"""

import customtkinter as ctk
from abc import ABC, abstractmethod
from src.utils.ThemeManager import BMTTheme, ACCENTS


class ToolModule(ABC):
    """Clase base abstracta para todas las herramientas del toolkit"""
    
    def __init__(self, parent, game_path, mods_path, icons=None):
        """
        Inicializa el módulo de herramienta
        
        Args:
            parent: Widget padre donde se renderizará la herramienta
            game_path: Ruta a la carpeta de Brawlhalla
            mods_path: Ruta a la carpeta de mods
            icons: Diccionario de iconos del toolkit
        """
        self.parent = parent
        self.game_path = game_path
        self.mods_path = mods_path
        self.icons = icons if icons else {}
        self.container = None
        self.theme = BMTTheme
        self.accents = ACCENTS
        
    @abstractmethod
    def create_ui(self):
        """Crea la interfaz de usuario de la herramienta"""
        pass
    
    @abstractmethod
    def get_tool_name(self):
        """Retorna el nombre de la herramienta"""
        pass
    
    @abstractmethod
    def get_tool_icon(self):
        """Retorna el ícono de la herramienta"""
        pass
    
    def destroy(self):
        """Limpia los recursos de la herramienta"""
        if self.container:
            self.container.destroy()
    
    def show(self):
        """Muestra la herramienta"""
        if self.container:
            self.container.pack(fill="both", expand=True)
    
    def hide(self):
        """Oculta la herramienta"""
        if self.container:
            self.container.pack_forget()
