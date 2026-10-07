package tier_b
{
   import flash.display.DisplayObject;
   import flash.display.DisplayObjectContainer;
   import flash.display.Stage;
   import flash.events.Event;
   import flash.events.KeyboardEvent;
   import flash.geom.ColorTransform;
   import flash.system.ApplicationDomain;
   import flash.text.TextField;
   import flash.text.TextFieldAutoSize;
   import flash.text.TextFormat;
   import flash.utils.describeType;
   import flash.utils.getDefinitionByName;
   import flash.utils.getQualifiedClassName;
   
   public class BrawlForgeSuite
   {
      public static var _kept:BrawlForgeSuite;
      public static var _stage:Stage;
      public static var _gc:*;
      public static var _handFile:String;
      public static var _families:Array;
      public static var _debugText:TextField;
      public static var _costumesSynced:Boolean = false;
      public static var _palettesSynced:Boolean = false;
      
      public var _frames:int;
      public var _failSwap:int;
      public var _failPalette:int;
      
      public function BrawlForgeSuite()
      {
         _failPalette = 0;
         _failSwap = 0;
         _frames = 0;
         BrawlForgeSuite._stage.addEventListener(Event.ENTER_FRAME,onEnterFrame,false,0,false);
      }
      
      public static function start(param1:Stage) : Boolean
      {
         if(BrawlForgeSuite._kept != null)
         {
            return true;
         }
         if(param1 == null)
         {
            return false;
         }
         Obf.initHandMap();
         Obf.initPalettes();
         if(BrawlForgeSuite._handFile == null)
         {
            BrawlForgeSuite._handFile = Obf.handFile();
         }
         if(BrawlForgeSuite._families == null)
         {
            BrawlForgeSuite._families = Obf.families();
         }
         BrawlForgeSuite._stage = param1;
         BrawlForgeSuite._stage.addEventListener(KeyboardEvent.KEY_DOWN,onKeyDown,false,0,false);
         
         // Early static injection into singletons for character select
         syncGlobalCostumes();
         syncGlobalPalettes();
         
         BrawlForgeSuite._kept = new BrawlForgeSuite();
         return true;
      }
      
      public static function onKeyDown(param1:KeyboardEvent) : void
      {
         if(param1.keyCode == 123)
         {
            toggleDebugOverlay();
         }
      }
      
      public static function getCostumeRegistry() : *
      {
         var reg:* = null;
         try { reg = CostumeType["_-M6b"]; } catch(e:Error) {}
         if(reg == null) { try { reg = CostumeType.§_-X4Q§; } catch(e:Error) {} }
         if(reg == null) { try { reg = CostumeType.§_-P1I§; } catch(e:Error) {} }
         if(reg == null) { try { reg = CostumeType.§_-q5b§; } catch(e:Error) {} }
         return reg;
      }

      public static function getColorSchemeClass() : Class
      {
         var csClass:Class = null;
         // 1. Direct fast opcode lookup
         try { csClass = Class(ApplicationDomain.currentDomain.getDefinition("_-V4w")); } catch(e:Error) {}
         if(csClass == null) { try { csClass = Class(getDefinitionByName("_-V4w")); } catch(e:Error) {} }
         if(csClass == null) { try { csClass = §_-G5Q§; } catch(e:Error) {} }
         // 2. ApplicationDomain lookup
         if(csClass == null) {
            try { csClass = Class(ApplicationDomain.currentDomain.getDefinition("_-G5Q")); } catch(e:Error) {}
         }
         if(csClass == null) {
            try { csClass = Class(getDefinitionByName("_-G5Q")); } catch(e:Error) {}
         }
         if(csClass == null && _stage != null && _stage.loaderInfo != null && _stage.loaderInfo.applicationDomain != null) {
            try { csClass = Class(_stage.loaderInfo.applicationDomain.getDefinition("_-G5Q")); } catch(e:Error) {}
         }
         if(csClass == null) {
            try { csClass = Class(ApplicationDomain.currentDomain.getDefinition("_-W3s")); } catch(e:Error) {}
         }
         if(csClass == null) {
            try { csClass = Class(getDefinitionByName("_-W3s")); } catch(e:Error) {}
         }
         if(csClass == null) {
            try { csClass = Class(getDefinitionByName("ColorSchemeType")); } catch(e:Error) {}
         }
         // 3. Dynamic stage entity reflection (Patch-proof auto discovery)
         if(csClass == null && _gc != null) {
            try {
               var ents:* = _gc.§_-13t§;
               if(ents != null && ents.length > 0) {
                  var ei:int = 0;
                  var elen:int = int(ents.length);
                  while(ei < elen) {
                     var schObj:* = ents[ei].§_-j5V§;
                     if(schObj == null) schObj = ents[ei].§_-S1y§;
                     if(schObj != null) {
                        csClass = Class(getDefinitionByName(getQualifiedClassName(schObj)));
                        if(csClass != null) break;
                     }
                     ei++;
                  }
               }
            } catch(e:Error) {}
         }
         return csClass;
      }

      public static function getColorSchemeRegistry() : *
      {
         var csClass:Class = getColorSchemeClass();
         var reg:* = null;
         if(csClass != null)
         {
            try { reg = csClass["_-p5j"]; } catch(e:Error) {}
            if(reg == null) { try { reg = csClass["_-Q4s"]; } catch(e:Error) {} }
            if(reg == null) { try { reg = csClass["_-S1l"]; } catch(e:Error) {} }
            if(reg == null) { try { reg = csClass.§_-V1h§; } catch(e:Error) {} }
            if(reg == null) { try { reg = csClass.§_-Q6c§; } catch(e:Error) {} }
            if(reg == null) { try { reg = csClass.§_-44k§; } catch(e:Error) {} }
            if(reg == null) { try { reg = csClass.§_-04k§; } catch(e:Error) {} }
            if(reg == null) { try { reg = csClass.§_-S6b§; } catch(e:Error) {} }
            if(reg == null) { try { reg = csClass.§_-o17§; } catch(e:Error) {} }
         }
         return reg;
      }
      
      public static function getSchemeColorsArray(scheme:*) : Array
      {
         if(scheme == null) return null;
         var colors:Array = null;
         try { colors = scheme["_-S5J"]; } catch(e:Error) {}
         if(colors == null) { try { colors = scheme["_-I4B"]; } catch(e:Error) {} }
         if(colors == null) { try { colors = scheme.§_-Z1S§; } catch(e:Error) {} }
         if(colors == null) { try { colors = scheme.§_-6y§; } catch(e:Error) {} }
         return colors;
      }
      
      public static function hexColor(val:uint) : String
      {
         var str:String = (val & 0xFFFFFF).toString(16).toUpperCase();
         while(str.length < 6)
         {
            str = "0" + str;
         }
         return "0x" + str;
      }
      
      public static function syncGlobalCostumes() : void
      {
         var reg:* = getCostumeRegistry();
         if(reg == null || Obf.handMap == null)
         {
            return;
         }
         var len:int = int(reg.length);
         var i:int = 0;
         while(i < len)
         {
            var ct:* = reg[i++];
            if(ct != null)
            {
               var cName:String = ct.mCostumeName;
               if(cName != null)
               {
                  var wanted:String = Obf.getHandForCostume(cName);
                  if(wanted != null)
                  {
                     var art:* = handArtOf(ct);
                     if(art != null)
                     {
                        try { art["_-Qe"] = wanted; } catch(e:Error) {}
                     try { art.§_-K3w§ = wanted; } catch(e:Error) { try { art.§_-O3M§ = wanted; } catch(e:Error) {} }
                     }
                     try {
                        if(ct.§_-g1v§ != null && ct.§_-g1v§.fileName == BrawlForgeSuite._handFile)
                        {
                           ct.§_-g1v§.§_-K3w§ = wanted;
                           ct.§_-g1v§.§_-O3M§ = wanted;
                        }
                     } catch(e:Error) {}

                     try {
                        if(ct.§_-bC§ != null) applyHandColorSwaps(ct, null, ct.§_-bC§);
                        if(ct.§_-P3J§ != null) applyHandColorSwaps(ct, null, ct.§_-P3J§);
                     } catch(e:Error) {}
                  }
               }
            }
         }
         _costumesSynced = true;
      }

      public static function syncGlobalPalettes() : void
      {
         if(Obf.paletteMap == null)
         {
            return;
         }
         var csClass:Class = getColorSchemeClass();
         if(csClass == null) return;
         var reg:* = getColorSchemeRegistry();
         if(reg == null) return;
         
         var channels:Array = Obf.paletteChannels();
         var swapSuffix:String = "_Swap";
         
         for (var key:String in Obf.paletteMap)
         {
            var targetScheme:* = null;
            var schemeId:int = int(key);
            if(schemeId > 0 && schemeId < reg.length)
            {
               targetScheme = reg[schemeId];
            }
            if(targetScheme == null)
            {
               try {
                  if(csClass.§_-o17§ != null) targetScheme = csClass.§_-o17§.get(key);
               } catch(e:Error) {}
            }
            if(targetScheme == null)
            {
               try {
                  if(csClass.§_-OQ§ != null) targetScheme = csClass.§_-OQ§.get(key);
               } catch(e:Error) {}
            }
            if(targetScheme == null && reg != null)
            {
               var rLen:int = int(reg.length);
               var rIdx:int = 0;
               while(rIdx < rLen)
               {
                  var sItem:* = reg[rIdx++];
                  if(sItem != null && sItem.mColorSchemeName == key)
                  {
                     targetScheme = sItem;
                     break;
                  }
               }
            }
            
            if(targetScheme != null)
            {
               var colors:Array = getSchemeColorsArray(targetScheme);
               var customPalette:Array = Obf.paletteMap[key] as Array;
               if(colors != null && customPalette != null && channels != null)
               {
                  var i:int = 0;
                  var count:int = int(Math.min(channels.length, customPalette.length));
                  while(i < count)
                  {
                     var chName:String = String(channels[i]);
                     var targetVal:uint = uint(customPalette[i]) & 0xFFFFFF;
                     
                     var slot:int = -1;
                     try { slot = csClass["_-p3"](chName + swapSuffix, swapSuffix); } catch(e:Error) {}
                     if(slot < 0) { try { slot = csClass.§_-p3§(chName + swapSuffix, swapSuffix); } catch(e:Error) {} }
                     if(slot < 0) { try { slot = csClass.§_-r5g§(chName); } catch(e:Error) {} }
                     
                     if(slot >= 0 && slot < colors.length)
                     {
                        if((uint(colors[slot]) & 0xFFFFFF) != targetVal)
                        {
                           colors[slot] = targetVal;
                        }
                     }
                     i++;
                  }
               }
            }
         }
         _palettesSynced = true;
      }
      
      public static function updateDebugText() : void
      {
         if(_debugText == null || !_debugText.visible)
         {
            return;
         }
         
         var report:String = "";
         try
         {
            report += "=================== BRAWL FORGE LIVE PROBE (F12) ===================\n";
            
            // 1. CONFIGURACION DE LA MODIFICACION (Obf.as)
            report += "--- [1] CONFIGURACION DE LA MODIFICACION (Obf.as) ---\n";
            try {
               if(Obf.handMap != null)
               {
                  report += " Hand Map:\n";
                  for (var hk:String in Obf.handMap)
                  {
                     report += "   * \"" + hk + "\" -> \"" + Obf.handMap[hk] + "\"\n";
                  }
               }
               if(Obf.colorMap != null)
               {
                  report += " Color Swaps:\n";
                  for (var ck:String in Obf.colorMap)
                  {
                     var clist:Array = Obf.colorMap[ck] as Array;
                     var cCount:int = (clist != null) ? clist.length : 0;
                     report += "   * \"" + ck + "\" (" + cCount + " swaps)\n";
                  }
               }
               if(Obf.paletteMap != null)
               {
                  report += " Custom Palette Overwrites (paletteMap):\n";
                  for (var pk:String in Obf.paletteMap)
                  {
                     var plist:Array = Obf.paletteMap[pk] as Array;
                     var pCount:int = (plist != null) ? plist.length : 0;
                     report += "   * Target Key \"" + pk + "\" (" + pCount + " channels overwritten)\n";
                  }
               }
            } catch(e1:Error) {
               report += " [Error reading Obf.as]: " + e1.message + "\n";
            }
            
            // 2. COSTUME REGISTRY STATUS
            var _loc2_:* = getCostumeRegistry();
            if(_loc2_ != null)
            {
               report += "\n--- [2] COSTUME REGISTRY (Total Costumes: " + _loc2_.length + ") ---\n";
            }

            // 3. COLOR SCHEME REGISTRY STATUS
            var _csClass:Class = getColorSchemeClass();
            var _csReg:* = getColorSchemeRegistry();
            report += "\n--- [3] COLOR SCHEME REGISTRY DATABASE ---\n";
            if(_csClass == null)
            {
               report += " ColorSchemeType Class: NOT FOUND / NULL\n";
            }
            else
            {
               report += " ColorSchemeType Class: " + getQualifiedClassName(_csClass) + "\n";
            }
            if(_csReg == null)
            {
               report += " ColorScheme Registry Array (_-V1h): NOT FOUND / NULL\n";
            }
            else
            {
               report += " Total Registered Color Schemes: " + _csReg.length + "\n";
               if(Obf.paletteMap != null)
               {
                  for (var spk:String in Obf.paletteMap)
                  {
                     var sIdx:int = int(spk);
                     var schObj:* = null;
                     if(sIdx > 0 && sIdx < _csReg.length) schObj = _csReg[sIdx];
                     if(schObj != null)
                     {
                        var colArr:Array = getSchemeColorsArray(schObj);
                        var colLen:int = (colArr != null) ? colArr.length : 0;
                        var colSample:String = "";
                        if(colArr != null && colArr.length > 2)
                        {
                           colSample = " [Col0=" + hexColor(colArr[0]) + ", Col1=" + hexColor(colArr[1]) + ", Col2=" + hexColor(colArr[2]) + "]";
                        }
                        report += "   * Scheme ID #" + sIdx + " (\"" + schObj.mColorSchemeName + "\"): " + colLen + " colors registered in game" + colSample + "\n";
                     }
                  }
               }
            }

            // 4. ENTIDADES ACTIVAS Y SELECCIÓN ACTUAL (Character Select & In-Match)
            report += "\n--- [4] CURRENT SELECTION & ACTIVE PLAYER ENTITIES ---\n";
            if(_gc != null)
            {
               var entities:* = null;
               try { entities = _gc.§_-13t§; } catch(e:Error) {}
               if(entities != null && entities.length > 0)
               {
                  var eLen:int = int(entities.length);
                  report += " Active Player / Entity Slots: " + eLen + "\n";
                  var eIdx:int = 0;
                  while(eIdx < eLen)
                  {
                     var entObj:* = entities[eIdx];
                     if(entObj != null)
                     {
                        var cosObj:* = null;
                        try { cosObj = entObj.§_-m6§; } catch(e:Error) {}
                        if(cosObj == null) { try { cosObj = entObj.§_-V5k§; } catch(e:Error) {} }
                        var cosName:String = (cosObj != null && cosObj.mCostumeName != null) ? cosObj.mCostumeName : "Default";

                        var schObj2:* = null;
                        try { schObj2 = entObj.§_-j5V§; } catch(e:Error) {}
                        if(schObj2 == null) { try { schObj2 = entObj.§_-S1y§; } catch(e:Error) {} }

                        var curSchId:int = -1;
                        var curSchName:String = "Unknown / None";
                        var curDispKey:String = "";
                        var curColsSample:String = "";
                        if(schObj2 != null)
                        {
                           try { curSchId = schObj2.§_-9U§; } catch(e:Error) {}
                           if(curSchId <= 0) { try { curSchId = schObj2.§_-C5B§; } catch(e:Error) {} }
                           if(schObj2.mColorSchemeName != null) curSchName = schObj2.mColorSchemeName;
                           if(schObj2.mDisplayNameKey != null) curDispKey = " (" + schObj2.mDisplayNameKey + ")";
                           
                           var curCols:Array = getSchemeColorsArray(schObj2);
                           if(curCols != null && curCols.length > 1) {
                              curColsSample = " [Col0=" + hexColor(curCols[0]) + ", Col1=" + hexColor(curCols[1]) + "]";
                           }
                        }

                        report += "   -> [Player Slot #" + (eIdx + 1) + "]: Costume=\"" + cosName + "\" | SELECTED COLOR: ID #" + curSchId + " (\"" + curSchName + "\"" + curDispKey + ")" + curColsSample + "\n";
                     }
                     eIdx++;
                  }
               }
               else
               {
                  report += " No active player entities spawned (In Main Menu screen).\n";
               }
            }
            else
            {
               report += " Game Controller (_gc) not yet linked.\n";
            }
            report += "====================================================================\n";
         }
         catch(topErr:Error)
         {
            report += "CRITICAL PROBE ERROR: " + topErr.message + "\n" + topErr.getStackTrace() + "\n";
         }
         
         _debugText.text = report;
      }
      
      public static function toggleDebugOverlay() : void
      {
         if(BrawlForgeSuite._stage == null)
         {
            return;
         }
         if(_debugText == null)
         {
            _debugText = new TextField();
            _debugText.autoSize = TextFieldAutoSize.LEFT;
            _debugText.textColor = 65280;
            _debugText.background = true;
            _debugText.backgroundColor = 0;
            _debugText.alpha = 0.94;
            _debugText.x = 10;
            _debugText.y = 10;
            _debugText.mouseEnabled = false;
            _debugText.wordWrap = true;
            _debugText.width = 1180;
            var tf:TextFormat = new TextFormat();
            tf.size = 11;
            tf.font = "Courier New";
            _debugText.defaultTextFormat = tf;
            BrawlForgeSuite._stage.addChild(_debugText);
         }
         else
         {
            _debugText.visible = !_debugText.visible;
         }
      }
      
      public static function handArtOf(param1:*) : *
      {
         var _loc6_:int = 0;
         var _loc7_:* = null;
         var _loc2_:* = null;
         try { _loc2_ = param1.§_-bC§; } catch(e:Error) {}
         if(_loc2_ == null) { try { _loc2_ = param1.§_-P3J§; } catch(e:Error) {} }
         var _loc3_:* = _loc2_ == null ? null : _loc2_.§_-P3t§;
         if(_loc3_ == null)
         {
            return null;
         }
         var _loc4_:int = 0;
         var _loc5_:int = int(_loc3_.length);
         while(_loc4_ < _loc5_)
         {
            _loc6_ = _loc4_++;
            _loc7_ = _loc3_[_loc6_];
            if(_loc7_ != null && _loc7_.fileName == BrawlForgeSuite._handFile)
            {
               return _loc7_;
            }
         }
         return null;
      }
      
      public function onEnterFrame(param1:Event) : void
      {
         var _loc4_:* = null as Error;
         ++_frames;
         
         // Keep costumes and palettes synced in menu / character select
         if(_frames % 30 == 0 || !_costumesSynced)
         {
            syncGlobalCostumes();
         }
         if(_frames % 30 == 0 || !_palettesSynced)
         {
            syncGlobalPalettes();
         }
         
         var _loc3_:* = null;
         try
         {
            _loc3_ = findGameController();
         }
         catch(_loc_e_:Error)
         {
            _loc4_ = _loc_e_;
         }
         var _loc5_:* = null;
         if(_loc3_ != null)
         {
            try
            {
               _loc5_ = _loc3_.§_-13t§;
            }
            catch(_loc_e_:Error)
            {
               _loc4_ = _loc_e_;
            }
         }
         if(_failSwap < 12 && _loc5_ != null)
         {
            try
            {
               layerHandSwap(_loc5_);
               _failSwap = 0;
            }
            catch(_loc_e_:Error)
            {
               _loc4_ = _loc_e_;
               ++_failSwap;
            }
         }

         if(_failPalette < 12 && _loc5_ != null)
         {
            try
            {
               layerPalette(_loc5_);
               _failPalette = 0;
            }
            catch(_loc_e_:Error)
            {
               _loc4_ = _loc_e_;
               ++_failPalette;
            }
         }

         if(_frames % 5 == 0 && _debugText != null && _debugText.visible)
         {
            updateDebugText();
         }
      }
      
      public static function upsertColorSwap(colorSwapsList:*, src:uint, dst:uint) : Boolean
      {
         var cleanSrc:uint = src & 0xFFFFFF;
         var cleanDst:uint = dst & 0xFFFFFF;
         if(colorSwapsList == null || cleanSrc == 0)
         {
            return false;
         }
         var found:Boolean = false;
         var changed:Boolean = false;
         var j:int = 0;
         var csLen:int = int(colorSwapsList.length);
         while(j < csLen)
         {
            var cs:* = colorSwapsList[j++];
            if(cs != null)
            {
               var csSrc:uint = 0;
               try { csSrc = cs.§_-I4Q§; } catch(e:Error) { try { csSrc = cs.§_-r3§; } catch(e:Error) {} }
               if((csSrc & 0xFFFFFF) == cleanSrc)
               {
                  found = true;
                  var csDst:uint = 0;
                  try { csDst = cs.§_-K5j§; } catch(e:Error) { try { csDst = cs.§_-U12§; } catch(e:Error) {} }
                  if((csDst & 0xFFFFFF) != cleanDst)
                  {
                     try { cs.§_-K5j§ = cleanDst; } catch(e:Error) { try { cs.§_-U12§ = cleanDst; } catch(e:Error) {} }
                     changed = true;
                  }
               }
            }
         }
         if(found)
         {
            return changed;
         }
         try
         {
            var csClass:Class = Class(getDefinitionByName("ColorSwap"));
            var newCs:* = new csClass(cleanSrc, cleanDst, 0);
            if(newCs != null)
            {
               colorSwapsList.push(newCs);
               return true;
            }
         }
         catch(e:Error)
         {
         }
         return false;
      }
      
      public static function getColorSwapsList(gfx:*) : *
      {
         if(gfx == null) return null;
         try { if(gfx.§_-e4H§ != null) return gfx.§_-e4H§; } catch(e:Error) {}
         try { if(gfx.§_-zK§ != null) return gfx.§_-zK§; } catch(e:Error) {}
         return null;
      }
      
      public static function getGfxType(target:*) : *
      {
         if(target == null) return null;
         try { if(target.§_-bC§ != null) return target.§_-bC§; } catch(e:Error) {}
         try { if(target.§_-P3J§ != null) return target.§_-P3J§; } catch(e:Error) {}
         return null;
      }
      
      public static function resolveTargetColor(costume:*, colorScheme:*, dst:uint) : uint
      {
         var cleanDst:uint = dst & 0xFFFFFF;
         if(cleanDst == 0 || costume == null)
         {
            return cleanDst;
         }

         var schemeToUse:* = colorScheme;
         if(schemeToUse == null)
         {
            try {
               var csCls:Class = getColorSchemeClass();
               schemeToUse = csCls.NO_COLOR_SCHEME;
            } catch(e:Error) {}
         }

         try {
            var activeSwaps:* = costume.§_-S5X§(schemeToUse);
            if(activeSwaps != null)
            {
               var m:int = 0;
               var mLen:int = int(activeSwaps.length);
               while(m < mLen)
               {
                  var csSwap:* = activeSwaps[m++];
                  if(csSwap != null)
                  {
                     var cSrc:uint = 0;
                     try { cSrc = csSwap.§_-I4Q§; } catch(e:Error) { try { cSrc = csSwap.§_-r3§; } catch(e:Error) {} }
                     if((cSrc & 0xFFFFFF) == cleanDst)
                     {
                        var cDst:uint = 0;
                        try { cDst = csSwap.§_-K5j§; } catch(e:Error) { try { cDst = csSwap.§_-U12§; } catch(e:Error) {} }
                        if((cDst & 0xFFFFFF) != 0)
                        {
                           return cDst & 0xFFFFFF;
                        }
                     }
                  }
               }
            }
         } catch(e:Error) {}

         try {
            var baseArr:Array = costume.§_-p2a§;
            if(baseArr != null && schemeToUse != null)
            {
               var schemeArr:Array = getSchemeColorsArray(schemeToUse);
               if(schemeArr != null)
               {
                  var k:int = 0;
                  var kLen:int = int(baseArr.length);
                  while(k < kLen)
                  {
                     if((uint(baseArr[k]) & 0xFFFFFF) == cleanDst)
                     {
                        if(k < int(schemeArr.length))
                        {
                           var sc:uint = uint(schemeArr[k]) & 0xFFFFFF;
                           if(sc != 0)
                           {
                              return sc;
                           }
                        }
                        return cleanDst;
                     }
                     k++;
                  }
               }
            }
         } catch(e:Error) {}

         return cleanDst;
      }

      public static function applyHandColorSwaps(costume:*, colorScheme:*, targetGfx:* = null) : Boolean
      {
         if(costume == null || targetGfx == null)
         {
            return false;
         }
         var cName:String = costume.mCostumeName;
         var customSwaps:Array = Obf.getColorSwapsForCostume(cName);
         if(customSwaps == null || customSwaps.length == 0)
         {
            return false;
         }

         var changed:Boolean = false;
         var swapsList:* = getColorSwapsList(targetGfx);
         if(swapsList == null)
         {
            return false;
         }

         var i:int = 0;
         var len:int = customSwaps.length;
         while(i < len)
         {
            var entry:Object = customSwaps[i++];
            if(entry != null)
            {
               var src:uint = uint(entry.src) & 0xFFFFFF;
               var dst:uint = uint(entry.dst) & 0xFFFFFF;
               if(src != 0 && dst != 0)
               {
                  var resolved:uint = resolveTargetColor(costume, colorScheme, dst);
                  if(resolved != 0)
                  {
                     if(upsertColorSwap(swapsList, src, resolved))
                     {
                        changed = true;
                     }
                  }
               }
            }
         }

         if(changed)
         {
            try { targetGfx.§_-e2n§ = 0; } catch(e:Error) {}
         }

         return changed;
      }

      public function layerHandSwap(param1:*) : void
      {
         var _loc4_:int = 0;
         var _loc5_:* = null;
         var _loc6_:* = null;
         var _loc7_:* = null;
         var _loc8_:* = null as String;
         var _loc9_:* = null as String;
         var _loc10_:* = null;
         var _loc2_:int = 0;
         var _loc3_:int = int(param1.length);
         while(_loc2_ < _loc3_)
         {
            _loc4_ = _loc2_++;
            _loc5_ = param1[_loc4_];
            if(_loc5_ != null)
            {
               _loc6_ = null;
               try { _loc6_ = _loc5_.§_-m6§; } catch(e:Error) {}
               if(_loc6_ == null) { try { _loc6_ = _loc5_.§_-V5k§; } catch(e:Error) {} }
               if(_loc6_ != null)
               {
                  _loc8_ = _loc6_.mCostumeName;
                  _loc9_ = Obf.getHandForCostume(_loc8_);
                  if(_loc9_ != null)
                  {
                     var entArt:* = BrawlForgeSuite.handArtOf(_loc5_);
                     if(entArt != null)
                     {
                        try {
                           try { entArt["_-Qe"] = _loc9_; } catch(e:Error) {}
                            if(entArt.§_-K3w§ != _loc9_) entArt.§_-K3w§ = _loc9_;
                           if(entArt.§_-O3M§ != _loc9_) entArt.§_-O3M§ = _loc9_;
                        } catch(e:Error) {}
                     }

                     _loc7_ = _loc5_.§_-j5V§;
                     if(_loc7_ == null) { try { _loc7_ = _loc5_.§_-S1y§; } catch(e:Error) {} }
                     var entGfx:* = BrawlForgeSuite.getGfxType(_loc5_);
                     if(entGfx != null)
                     {
                        BrawlForgeSuite.applyHandColorSwaps(_loc6_, _loc7_, entGfx);
                     }
                  }
               }
            }
         }
      }

      public function layerPalette(param1:*) : void
      {
         if(param1 == null || Obf.paletteMap == null) return;
         var i:int = 0;
         var len:int = int(param1.length);
         while(i < len)
         {
            var ent:* = param1[i++];
            if(ent != null)
            {
               var s:* = null;
               try { s = ent.§_-j5V§; } catch(e:Error) {}
               if(s == null) { try { s = ent.§_-S1y§; } catch(e:Error) {} }
               if(s != null)
               {
                  var sId:int = -1;
                  try { sId = s.§_-9U§; } catch(e:Error) {}
                  if(sId <= 0) { try { sId = s.§_-C5B§; } catch(e:Error) {} }
                  var sName:String = s.mColorSchemeName;
                  
                  var isTarget:Boolean = false;
                  if(sId > 0 && Obf.paletteMap[String(sId)] != null) isTarget = true;
                  if(sName != null && Obf.paletteMap[sName] != null) isTarget = true;
                  
                  if(isTarget)
                  {
                     var c:* = null;
                     try { c = ent.§_-m6§; } catch(e:Error) {}
                     if(c == null) { try { c = ent.§_-V5k§; } catch(e:Error) {} }
                     if(c != null)
                     {
                        try { ent.§_-h4y§(c, s, true); } catch(e:Error) { try { ent.§_-c1T§(c, s, true); } catch(e:Error) {} }
                     }
                  }
               }
            }
         }
      }
      
      public function findGameController() : *
      {
         var _loc5_:int = 0;
         var _loc6_:* = null as DisplayObject;
         var _loc7_:* = null;
         var _loc8_:* = null as Error;
         if(BrawlForgeSuite._gc != null)
         {
            return BrawlForgeSuite._gc;
         }
         var _loc2_:String = Obf.gcField();
         var _loc3_:int = 0;
         var _loc4_:int = BrawlForgeSuite._stage.numChildren;
         do
         {
            if(_loc3_ >= _loc4_)
            {
               return null;
            }
            _loc5_ = _loc3_++;
            _loc6_ = BrawlForgeSuite._stage.getChildAt(_loc5_);
            _loc7_ = null;
            try
            {
               if(_loc6_ is Main)
               {
                  try { _loc7_ = _loc6_.§_-84x§; } catch(e:Error) {}
                  if(_loc7_ == null) { try { _loc7_ = _loc6_.§_-819§; } catch(e:Error) {} }
               }
            }
            catch(_loc_e_:Error)
            {
               _loc8_ = _loc_e_;
            }
            if(_loc7_ == null)
            {
               try
               {
                  _loc7_ = _loc6_[_loc2_];
               }
               catch(_loc_e_:Error)
               {
                  _loc8_ = _loc_e_;
               }
            }
         }
         while(_loc7_ == null);
         
         BrawlForgeSuite._gc = _loc7_;
         return BrawlForgeSuite._gc;
      }
   }
}
