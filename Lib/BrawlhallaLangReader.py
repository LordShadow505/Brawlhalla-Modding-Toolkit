"""
Brawlhalla Language Reader
Based on: https://github.com/eyalzus12/BrawlhallaLangReader
Reads Brawlhalla language.X.bin files to extract skin names and translations
"""

import struct
import os
import zlib
from typing import Dict, Optional

class BrawlhallaLangReader:
    """Lee archivos de idioma binarios de Brawlhalla"""
    
    # IDs de idiomas según el código C#
    LANGUAGE_IDS = {
        1: "en",      # English
        2: "de",      # German
        3: "fr",      # French
        4: "pt_BR",   # Portuguese (Brazil)
        5: "es",      # Spanish
        6: "it",      # Italian
        7: "ru",      # Russian
        8: "pl",      # Polish
        9: "tr",      # Turkish
        10: "ja",     # Japanese
        11: "ko",     # Korean
        12: "zh_CN",  # Chinese (Simplified)
        13: "zh_TW"   # Chinese (Traditional)
    }
    
    def __init__(self, languages_folder: str):
        """
        Inicializa el lector de idiomas
        
        Args:
            languages_folder: Ruta a la carpeta languages de Brawlhalla
        """
        self.languages_folder = languages_folder
        self.translations: Dict[str, Dict[str, str]] = {}
    
    def read_language_file(self, language_id: int) -> Dict[str, str]:
        """
        Lee un archivo de idioma específico
        
        Args:
            language_id: ID del idioma (1=English, 5=Spanish, etc.)
            
        Returns:
            Diccionario con key -> value de traducciones
        """
        file_path = os.path.join(self.languages_folder, f"language.{language_id}.bin")
        
        if not os.path.exists(file_path):
            return {}
        
        translations = {}
        
        try:
            with open(file_path, 'rb') as f:
                # Leer header (4 bytes, little-endian uint32)
                header_bytes = f.read(4)
                if len(header_bytes) < 4:
                    print(f"Invalid file header in {file_path}")
                    return {}
                
                header = struct.unpack('<I', header_bytes)[0]
                
                # El resto del archivo está comprimido con ZLib
                compressed_data = f.read()
                decompressed_data = zlib.decompress(compressed_data)
                
                # Leer desde los datos descomprimidos
                offset = 0
                
                # Leer número de entradas (4 bytes, big-endian int32)
                entry_count = struct.unpack('>I', decompressed_data[offset:offset+4])[0]
                offset += 4
                
                # Leer cada entrada
                for _ in range(entry_count):
                    # Leer longitud de la key (2 bytes, big-endian uint16)
                    if offset + 2 > len(decompressed_data):
                        break
                    key_length = struct.unpack('>H', decompressed_data[offset:offset+2])[0]
                    offset += 2
                    
                    # Leer key (UTF-8)
                    if offset + key_length > len(decompressed_data):
                        break
                    key = decompressed_data[offset:offset+key_length].decode('utf-8', errors='ignore')
                    offset += key_length
                    
                    # Leer longitud del value (2 bytes, big-endian uint16)
                    if offset + 2 > len(decompressed_data):
                        break
                    value_length = struct.unpack('>H', decompressed_data[offset:offset+2])[0]
                    offset += 2
                    
                    # Leer value (UTF-8)
                    if offset + value_length > len(decompressed_data):
                        break
                    value = decompressed_data[offset:offset+value_length].decode('utf-8', errors='ignore')
                    offset += value_length
                    
                    translations[key] = value
        
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return {}
        
        return translations
    
    def load_language(self, language_id: int = 1) -> bool:
        """
        Carga un idioma en memoria
        
        Args:
            language_id: ID del idioma (default: 1 = English)
            
        Returns:
            True si se cargó correctamente
        """
        lang_code = self.LANGUAGE_IDS.get(language_id, "en")
        self.translations[lang_code] = self.read_language_file(language_id)
        return len(self.translations[lang_code]) > 0
    
    def get_translation(self, key: str, language_id: int = 1) -> Optional[str]:
        """
        Obtiene la traducción de una key
        
        Args:
            key: Key a buscar (ej: "UI_CostumeName_OrionRobot")
            language_id: ID del idioma
            
        Returns:
            Traducción o None si no se encuentra
        """
        lang_code = self.LANGUAGE_IDS.get(language_id, "en")
        
        # Cargar idioma si no está en memoria
        if lang_code not in self.translations:
            self.load_language(language_id)
        
        return self.translations.get(lang_code, {}).get(key)
    
    def get_skin_name(self, skin_code: str, language_id: int = 1) -> str:
        """
        Obtiene el nombre real de una skin desde su código
        
        Args:
            skin_code: Código de la skin (ej: "RobotBlue")
            language_id: ID del idioma (default: 1 = English)
            
        Returns:
            Nombre de la skin o el código original si no se encuentra
        """
        # Si el código está vacío, es la skin por defecto
        if not skin_code or skin_code.strip() == "":
            return "Default"
        
        # El patrón correcto es: CostumeType_{SkinCode}_DisplayName
        costume_key = f"CostumeType_{skin_code}_DisplayName"
        
        translation = self.get_translation(costume_key, language_id)
        if translation:
            return translation
        
        # Si no se encuentra, devolver el código original
        return skin_code
    
    def search_keys(self, search_term: str, language_id: int = 1) -> Dict[str, str]:
        """
        Busca keys que contengan un término
        
        Args:
            search_term: Término a buscar
            language_id: ID del idioma
            
        Returns:
            Diccionario con keys que coinciden y sus valores
        """
        lang_code = self.LANGUAGE_IDS.get(language_id, "en")
        
        if lang_code not in self.translations:
            self.load_language(language_id)
        
        results = {}
        search_lower = search_term.lower()
        
        for key, value in self.translations.get(lang_code, {}).items():
            if search_lower in key.lower():
                results[key] = value
        
        return results


# Función helper para uso rápido
def get_skin_display_name(skin_code: str, game_path: str, language: str = "en") -> str:
    """
    Función helper para obtener el nombre de una skin rápidamente
    
    Args:
        skin_code: Código de la skin (ej: "RobotBlue")
        game_path: Ruta al juego de Brawlhalla
        language: Código de idioma ("en", "es", etc.)
        
    Returns:
        Nombre para mostrar de la skin
    """
    # Mapeo de códigos de idioma a IDs
    lang_to_id = {v: k for k, v in BrawlhallaLangReader.LANGUAGE_IDS.items()}
    language_id = lang_to_id.get(language, 1)
    
    languages_folder = os.path.join(game_path, "languages")
    
    if not os.path.exists(languages_folder):
        return skin_code
    
    reader = BrawlhallaLangReader(languages_folder)
    return reader.get_skin_name(skin_code, language_id)


if __name__ == "__main__":
    # Test
    import sys
    
    if len(sys.argv) > 1:
        game_path = sys.argv[1]
    else:
        game_path = "X:/SteamLibrary/steamapps/common/Brawlhalla"
    
    reader = BrawlhallaLangReader(os.path.join(game_path, "languages"))
    
    # Cargar inglés
    print("Loading English...")
    if reader.load_language(1):
        lang_data = reader.translations['en']
        print(f"Loaded {len(lang_data)} entries")
        
        # Probar skins que vimos en los datos
        test_skins = [
            ("Future", "CostumeType_Future_DisplayName"),
            ("ViviOps", "CostumeType_ViviOps_DisplayName"),
            ("Horus", "CostumeType_Horus_DisplayName"),
            ("EpicYumiko", "CostumeType_EpicYumiko_DisplayName"),
            ("Hellboy", "CostumeType_Hellboy_DisplayName"),
            ("Rogue", "CostumeType_Rogue_DisplayName"),
        ]
        
        print("\nTesting skin names:")
        for skin_code, expected_key in test_skins:
            name = reader.get_skin_name(skin_code, 1)
            print(f"  {skin_code} -> {name}")
            if expected_key in lang_data:
                print(f"    (Expected: {lang_data[expected_key]})")
        
        # Mostrar todas las skins de Orion
        print("\nSearching all Orion costume entries:")
        orion_costumes = {k: v for k, v in lang_data.items() if k.startswith('CostumeType_') and 'Orion' in v}
        for key, value in list(orion_costumes.items())[:10]:
            skin_code = key.replace('CostumeType_', '').replace('_DisplayName', '')
            print(f"  {skin_code} -> {value}")
    else:
        print("Failed to load language file")
