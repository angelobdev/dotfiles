{ pkgs, ... }:
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

  # Start GNOME Keyring at login so NetworkManager can retrieve secrets
  services.gnome.gnome-keyring.enable = true;
  security.pam.services.sddm.enableGnomeKeyring = true;
}