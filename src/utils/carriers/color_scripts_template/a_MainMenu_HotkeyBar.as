package
{
   import flash.display.MovieClip;
   import tier_color.ColorCarrierBootstrap;
   
   [Embed(source="/_assets/assets.swf", symbol="a_MainMenu_HotkeyBar")]
   public dynamic class a_MainMenu_HotkeyBar extends MovieClip
   {
      public var am_Back:MovieClip;
      public var am_Backer:MovieClip;
      public var am_CornerMenu:MovieClip;
      public var am_Select:MovieClip;
      
      public function a_MainMenu_HotkeyBar()
      {
         super();
         ColorCarrierBootstrap.attach(this);
      }
   }
}
