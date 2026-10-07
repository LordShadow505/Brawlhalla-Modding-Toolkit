package tier_color
{
   import flash.display.DisplayObject;
   import flash.events.Event;
   import flash.events.TimerEvent;
   import flash.utils.Timer;

   public class ColorCarrierBootstrap
   {
      public static var _root:DisplayObject;
      public static var _timer:Timer;

      public function ColorCarrierBootstrap()
      {
      }

      public static function attach(target:DisplayObject) : void
      {
         if(target == null || ColorCarrierBootstrap._root != null) return;
         ColorCarrierBootstrap._root = target;
         try {
            ColorCarrierBootstrap._root.addEventListener(Event.ADDED_TO_STAGE, ColorCarrierBootstrap.onAdded, false, 0, true);
            ColorCarrierBootstrap.arm();
         } catch(e:Error) {}
      }

      public static function onAdded(e:Event) : void
      {
         ColorCarrierBootstrap.arm();
      }

      public static function arm() : void
      {
         if(ColorCarrierBootstrap._timer != null) return;
         ColorCarrierBootstrap._timer = new Timer(250);
         ColorCarrierBootstrap._timer.addEventListener(TimerEvent.TIMER, ColorCarrierBootstrap.onTick);
         ColorCarrierBootstrap._timer.start();
      }

      public static function onTick(e:TimerEvent) : void
      {
         try {
            if(ColorCarrierBootstrap._root == null || !ColorForgeSuite.start(ColorCarrierBootstrap._root.stage))
            {
               return;
            }
            ColorCarrierBootstrap._timer.stop();
            ColorCarrierBootstrap._timer.removeEventListener(TimerEvent.TIMER, ColorCarrierBootstrap.onTick);
            ColorCarrierBootstrap._timer = null;
            ColorCarrierBootstrap._root.removeEventListener(Event.ADDED_TO_STAGE, ColorCarrierBootstrap.onAdded);
            ColorCarrierBootstrap._root = null;
         } catch(e:Error) {}
      }
   }
}
