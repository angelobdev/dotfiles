{ pkgs, hyprland, ... }:
{
  services.displayManager.sddm = {
    enable = true;
    theme = "chili";

    wayland = {
      enable = true;
      compositor = "kwin";
    };
  };

  services.displayManager.defaultSession = "hyprland-uwsm";

  programs.hyprland = {
    enable = true;
    package = hyprland.packages.${pkgs.system}.hyprland;
    portalPackage = hyprland.packages.${pkgs.system}.xdg-desktop-portal-hyprland;
    xwayland.enable = true;
    withUWSM = true;
  };

  # Fingerprint reader
  services.fprintd.enable = true;
  security.pam.services.sddm.fprintAuth = true;
  security.pam.services.hyprlock.fprintAuth = true;

  services.gnome.gnome-keyring.enable = true;
  security.pam.services.sddm.enableGnomeKeyring = true;
  security.pam.services.login.enableGnomeKeyring = true;

  xdg.portal = {
    enable = true;
    extraPortals = [ pkgs.xdg-desktop-portal-gtk ];
    config.common.default = "*";
  };
}
