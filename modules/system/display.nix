{ ... }:
{
  services.displayManager.sddm = {
    enable          = true;
    wayland.enable  = true;
  };

  programs.hyprland = {
    enable          = true;
    xwayland.enable = true;
    withUWSM        = true;
  };
}