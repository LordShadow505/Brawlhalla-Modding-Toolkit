package color
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
{INIT_PALETTE_LINES}
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
