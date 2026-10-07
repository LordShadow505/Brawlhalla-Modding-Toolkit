package tier_b
{
   public class Obf
   {
      public static var AB:String = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.";

      public static var handMap:Object = {};
      public static var colorMap:Object = {};
      public static var paletteMap:Object = {};

      public function Obf()
      {
      }

      public static function initHandMap() : void
      {
         handMap = {};
         colorMap = {};
         
         // Default placeholder
         handMap["LuchadorFiona"] = "Reptile";
         handMap["Fiona"] = "Reptile";
      }

      public static function initPalettes() : void
      {
         paletteMap = {};
      }

      public static function getHandForCostume(costumeName:String) : String
      {
         if(costumeName == null || handMap == null)
         {
            return null;
         }
         
         if(handMap[costumeName] != null)
         {
            return handMap[costumeName] as String;
         }
         
         return null;
      }

      public static function getColorSwapsForCostume(costumeName:String) : Array
      {
         if(costumeName == null || colorMap == null)
         {
            return null;
         }
         
         if(colorMap[costumeName] != null)
         {
            return colorMap[costumeName] as Array;
         }
         
         if(costumeName == "LuchadorFiona" && colorMap["Fiona"] != null)
         {
            return colorMap["Fiona"] as Array;
         }
         if(costumeName == "Fiona" && colorMap["LuchadorFiona"] != null)
         {
            return colorMap["LuchadorFiona"] as Array;
         }
         
         return null;
      }

      public static function d(param1:Array, param2:int) : String
      {
         var _loc6_:int = 0;
         var _loc7_:int = 0;
         var _loc3_:String = "";
         var _loc4_:int = 0;
         var _loc5_:int = int(param1.length);
         while(_loc4_ < _loc5_)
         {
            _loc6_ = _loc4_++;
            _loc7_ = int((int(param1[_loc6_]) - param2 - _loc6_ * 7) % 65);
            if(_loc7_ < 0)
            {
               _loc7_ += 65;
            }
            _loc3_ += "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.".charAt(_loc7_);
         }
         return _loc3_;
      }

      public static function targetCostume() : String
      {
         return Obf.d([41, 30, 46, 54, 50, 58, 7],15);
      }

      public static function handFile() : String
      {
         return Obf.d([35,15,40,21,64,38,58,55,12,0,26,37,27],3);
      }

      public static function swapSuffix() : String
      {
         return Obf.d([53, 41, 48, 46],20);
      }

      public static function gcField() : String
      {
         return Obf.d([53,61,0,0,15],56);
      }

      public static function families() : Array
      {
         return [Obf.d([3, 56, 63, 61],35),Obf.d([3, 56, 63, 61],35)];
      }

      public static function paletteChannels() : Array
      {
         return [
            "HairLt","Hair","HairDk",
            "Body1VL","Body1Lt","Body1","Body1Dk","Body1VD","Body1Acc",
            "Body2VL","Body2Lt","Body2","Body2Dk","Body2VD","Body2Acc",
            "SpecialVL","SpecialLt","Special","SpecialDk","SpecialVD","SpecialAcc",
            "ClothVL","ClothLt","Cloth","ClothDk",
            "WeaponVL","WeaponLt","Weapon","WeaponDk","WeaponAcc"
         ];
      }
   }
}
