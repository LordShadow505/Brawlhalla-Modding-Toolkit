package tier_color
{
   public class ColorObf
   {
      public static var paletteMap:Object = {};

      public function ColorObf()
      {
      }

      public static function initPaletteMap() : void
      {
         paletteMap = {};
         // Example default (Black = 1):
         // paletteMap[1] = [0x38373E, 0x2C2B31, ...];
      }

      public static function getPaletteForScheme(schemeId:int) : Array
      {
         if(paletteMap == null)
         {
            initPaletteMap();
         }
         if(paletteMap[schemeId] != null)
         {
            return paletteMap[schemeId] as Array;
         }
         return null;
      }
   }
}
