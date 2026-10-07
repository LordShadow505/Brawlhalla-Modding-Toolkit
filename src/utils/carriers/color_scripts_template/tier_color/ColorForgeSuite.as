package tier_color
{
   import flash.display.DisplayObject;
   import flash.display.DisplayObjectContainer;
   import flash.display.Stage;
   import flash.events.Event;
   import flash.system.ApplicationDomain;
   import flash.utils.describeType;
   import flash.utils.getDefinitionByName;

   public class ColorForgeSuite
   {
      public static var _kept:ColorForgeSuite;
      public static var _stage:Stage;
      public static var _gc:*;
      public static var _cachedSchemeClass:Class;
      public static var _cachedRegistryProp:String;
      public static var _cachedColorsProp:String;
      public static var _cachedSlotMethod:String;
      public static var _palettesSynced:Boolean = false;
      public var _frames:int = 0;

      public static var CHANNELS:Array = [
         "HairLt","Hair","HairDk",
         "Body1VL","Body1Lt","Body1","Body1Dk","Body1VD","Body1Acc",
         "Body2VL","Body2Lt","Body2","Body2Dk","Body2VD","Body2Acc",
         "SpecialVL","SpecialLt","Special","SpecialDk","SpecialVD","SpecialAcc",
         "ClothVL","ClothLt","Cloth","ClothDk",
         "WeaponVL","WeaponLt","Weapon","WeaponDk","WeaponAcc"
      ];

      public function ColorForgeSuite()
      {
         _frames = 0;
         ColorForgeSuite._stage.addEventListener(Event.ENTER_FRAME, onEnterFrame, false, 0, false);
      }

      public static function start(stageRef:Stage) : Boolean
      {
         if(ColorForgeSuite._kept != null) return true;
         if(stageRef == null) return false;

         ColorObf.initPaletteMap();
         ColorForgeSuite._stage = stageRef;

         // Initial palette sync on startup
         syncAllPalettes();

         ColorForgeSuite._kept = new ColorForgeSuite();
         return true;
      }

      public function onEnterFrame(e:Event) : void
      {
         _frames++;
         if(_frames % 30 == 0 || !_palettesSynced)
         {
            syncAllPalettes();
         }

         try {
            var gc:* = findGameController();
            if(gc != null)
            {
               var ents:* = gc.§_-13t§;
               if(ents != null)
               {
                  layerActiveEntities(ents);
               }
            }
         } catch(err:Error) {}
      }

      public static function getColorSchemeClass() : Class
      {
         if(_cachedSchemeClass != null) return _cachedSchemeClass;
         try {
            if(ApplicationDomain.currentDomain.hasDefinition("§_-G5Q§")) {
               _cachedSchemeClass = Class(ApplicationDomain.currentDomain.getDefinition("§_-G5Q§"));
               return _cachedSchemeClass;
            }
         } catch(e:Error) {}
         return null;
      }

      public static function getSchemeRegistry(csCls:Class) : *
      {
         if(csCls == null) return null;
         if(_cachedRegistryProp != null) {
            try { return csCls[_cachedRegistryProp]; } catch(e:Error) {}
         }
         try { if(csCls.§_-44k§ != null) { _cachedRegistryProp = "§_-44k§"; return csCls.§_-44k§; } } catch(e:Error) {}
         try { if(csCls.§_-25A§ != null) { _cachedRegistryProp = "§_-25A§"; return csCls.§_-25A§; } } catch(e:Error) {}
         return null;
      }

      public static function getSchemeColors(scheme:*) : Array
      {
         if(scheme == null) return null;
         if(_cachedColorsProp != null) {
            try { return scheme[_cachedColorsProp] as Array; } catch(e:Error) {}
         }
         try { if(scheme.§_-6y§ != null) { _cachedColorsProp = "§_-6y§"; return scheme.§_-6y§ as Array; } } catch(e:Error) {}
         try { if(scheme.§_-Z1S§ != null) { _cachedColorsProp = "§_-Z1S§"; return scheme.§_-Z1S§ as Array; } } catch(e:Error) {}
         return null;
      }

      public static function getSlotIndex(csCls:Class, channelName:String) : int
      {
         try {
            return csCls.§_-p3§(channelName + "_Swap", "_Swap");
         } catch(e:Error) {}
         return -1;
      }

      public static function syncAllPalettes() : Boolean
      {
         if(ColorObf.paletteMap == null) return false;
         var csCls:Class = getColorSchemeClass();
         if(csCls == null) return false;
         var reg:* = getSchemeRegistry(csCls);
         if(reg == null) return false;

         var changed:Boolean = false;
         for (var sidStr:String in ColorObf.paletteMap)
         {
            var sid:int = int(sidStr);
            if(sid < 0 || sid >= reg.length) continue;
            var scheme:* = reg[sid];
            if(scheme == null) continue;
            var colors:Array = getSchemeColors(scheme);
            if(colors == null) continue;

            var targetColors:Array = ColorObf.paletteMap[sid] as Array;
            if(targetColors == null) continue;

            var maxCh:int = Math.min(CHANNELS.length, targetColors.length);
            for (var i:int = 0; i < maxCh; i++)
            {
               var ch:String = String(CHANNELS[i]);
               var colVal:uint = uint(targetColors[i]) & 0xFFFFFF;
               var slot:int = getSlotIndex(csCls, ch);
               if(slot >= 0 && slot < colors.length)
               {
                  if(colors[slot] != colVal)
                  {
                     colors[slot] = colVal;
                     changed = true;
                  }
               }
            }
         }
         _palettesSynced = true;
         return changed;
      }

      public static function layerActiveEntities(entities:*) : void
      {
         if(entities == null || ColorObf.paletteMap == null) return;
         try {
            var len:int = int(entities.length);
            for (var j:int = 0; j < len; j++)
            {
               var ent:* = entities[j];
               if(ent == null) continue;
               var s:* = ent.§_-j5V§;
               if(s == null) continue;
               var sid:int = int(s.§_-C5B§);
               if(ColorObf.paletteMap[sid] != null)
               {
                  try {
                     var c:* = ent.§_-m6§;
                     if(c == null) c = ent.§_-V5k§;
                     ent.§_-p28§(c, s, true);
                  } catch(err:Error) {}
               }
            }
         } catch(e:Error) {}
      }

      public function findGameController() : *
      {
         if(ColorForgeSuite._gc != null) return ColorForgeSuite._gc;
         try {
            var num:int = ColorForgeSuite._stage.numChildren;
            for (var i:int = 0; i < num; i++)
            {
               var ch:DisplayObject = ColorForgeSuite._stage.getChildAt(i);
               if(ch is Main)
               {
                  try { if(ch.§_-84x§ != null) { ColorForgeSuite._gc = ch.§_-84x§; return ColorForgeSuite._gc; } } catch(e:Error) {}
                  try { if(ch.§_-819§ != null) { ColorForgeSuite._gc = ch.§_-819§; return ColorForgeSuite._gc; } } catch(e:Error) {}
               }
            }
         } catch(e:Error) {}
         return null;
      }
   }
}
