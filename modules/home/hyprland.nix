{ pkgs, hyprgrass, ... }:
{
  wayland.windowManager.hyprland = {
    enable  = true;
    plugins = [
      hyprgrass.packages.${pkgs.stdenv.hostPlatform.system}.default
    ];
  };
}