{ pkgs, ... }:
{
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
}