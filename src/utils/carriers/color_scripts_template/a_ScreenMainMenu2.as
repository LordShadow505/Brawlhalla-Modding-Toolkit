package
{
   import flash.display.MovieClip;
   import tier_b.BrawlForgeSuiteBootstrap;
   import color.ColorForgeSuite;

   [Embed(source="/_assets/assets.swf", symbol="symbol1")]
   public dynamic class a_ScreenMainMenu2 extends MovieClip
   {
      public function a_ScreenMainMenu2()
      {
         super();
         BrawlForgeSuiteBootstrap.attach(this);
         ColorForgeSuite.attach(this);
      }
   }
}
