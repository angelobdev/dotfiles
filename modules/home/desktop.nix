{ pkgs, ... }:
{
  # Top bar
  programs.waybar.enable = true;

  # Notification daemon
  services.swaync.enable = true;

  # Idle daemon
  services.hypridle.enable = true;

  # Screen locker
  programs.hyprlock.enable = true;

  # OSD (volume/brightness overlay)
  services.swayosd.enable = true;

  # Clipboard manager — persists clipboard history
  services.cliphist.enable = true;

  # Gnome keyring
  services.gnome-keyring = {
    enable = true;
    components = [
      "pkcs11"
      "secrets"
      "ssh"
    ];
  };

  # Udiskie
  services.udiskie = {
    enable = true;
  };
}
