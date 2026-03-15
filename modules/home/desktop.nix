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

  # Udiskie
  services.udiskie = {
    enable = true;
    tray = "always"; # "always", "never", "auto"
    automount = true;
  };
}