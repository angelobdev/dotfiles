{
  pkgs,
  hyprland,
  hyprgrass,
  ...
}:
{
  wayland.windowManager.hyprland = {
    enable = true;
    systemd.enable = false;
    package = hyprland.packages.${pkgs.stdenv.hostPlatform.system}.hyprland;
    portalPackage = hyprland.packages.${pkgs.stdenv.hostPlatform.system}.xdg-desktop-portal-hyprland;
    plugins = [
      hyprgrass.packages.${pkgs.stdenv.hostPlatform.system}.default
    ];
  };
}
