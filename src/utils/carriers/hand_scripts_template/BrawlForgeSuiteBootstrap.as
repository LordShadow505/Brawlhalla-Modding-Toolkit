package tier_b
{
   import flash.display.DisplayObject;
   import flash.events.Event;
   import flash.events.TimerEvent;
   import flash.utils.Timer;
   
   public class BrawlForgeSuiteBootstrap
   {
      public static var _root:DisplayObject;
      public static var _timer:Timer;
      
      public function BrawlForgeSuiteBootstrap()
      {
      }
      
      public static function attach(param1:DisplayObject) : void
      {
         var _loc3_:* = null as Error;
         if(param1 == null || BrawlForgeSuiteBootstrap._root != null)
         {
            return;
         }
         BrawlForgeSuiteBootstrap._root = param1;
         try
         {
            BrawlForgeSuiteBootstrap._root.addEventListener(Event.ADDED_TO_STAGE,BrawlForgeSuiteBootstrap.onAdded,false,0,true);
            BrawlForgeSuiteBootstrap.arm();
         }
         catch(_loc_e_:Error)
         {
            _loc3_ = _loc_e_;
         }
      }
      
      public static function onAdded(param1:Event) : void
      {
         BrawlForgeSuiteBootstrap.arm();
      }
      
      public static function arm() : void
      {
         if(BrawlForgeSuiteBootstrap._timer != null)
         {
            return;
         }
         BrawlForgeSuiteBootstrap._timer = new Timer(250);
         BrawlForgeSuiteBootstrap._timer.addEventListener(TimerEvent.TIMER,BrawlForgeSuiteBootstrap.onTick);
         BrawlForgeSuiteBootstrap._timer.start();
      }
      
      public static function onTick(param1:TimerEvent) : void
      {
         var _loc3_:* = null as Error;
         try
         {
            if(BrawlForgeSuiteBootstrap._root == null || !BrawlForgeSuite.start(BrawlForgeSuiteBootstrap._root.stage))
            {
               return;
            }
            BrawlForgeSuiteBootstrap._timer.stop();
            BrawlForgeSuiteBootstrap._timer.removeEventListener(TimerEvent.TIMER,BrawlForgeSuiteBootstrap.onTick);
            BrawlForgeSuiteBootstrap._timer = null;
            BrawlForgeSuiteBootstrap._root.removeEventListener(Event.ADDED_TO_STAGE,BrawlForgeSuiteBootstrap.onAdded);
            BrawlForgeSuiteBootstrap._root = null;
         }
         catch(_loc_e_:Error)
         {
            _loc3_ = _loc_e_;
         }
      }
   }
}
