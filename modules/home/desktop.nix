{ pkgs, hyprland, hyprgrass, ... }:
{
  # Top bar
  programs.waybar.enable = true;

  # Notification daemon
  services.swaync = {
    enable = true;
    settings = builtins.fromJSON (builtins.readFile ../../config/swaync/config.json);
  };

  # Idle daemon
  services.hypridle.enable = true;

  # Screen locker
  programs.hyprlock.enable = true;

  # OSD (volume/brightness overlay)
  services.swayosd.enable = true;

  # Clipboard manager — persists clipboard history
  services.cliphist.enable = true;

  # Fix for Hyprland UWSM
  wayland.windowManager.hyprland = {
    enable = true;
    package = hyprland.packages.${pkgs.system}.hyprland;
    plugins = [ hyprgrass.packages.${pkgs.system}.hyprgrass ];
    systemd.enable = false;
    extraConfig = ''
      source = ~/.config/hypr/modules/variables.conf
      source = ~/.config/hypr/modules/autostart.conf
      source = ~/.config/hypr/modules/binds.conf
      source = ~/.config/hypr/modules/env.conf
      source = ~/.config/hypr/modules/input.conf
      source = ~/.config/hypr/modules/look.conf
      source = ~/.config/hypr/modules/monitors.conf
      source = ~/.config/hypr/modules/perms.conf
      source = ~/.config/hypr/modules/plugins.conf
      source = ~/.config/hypr/modules/windows.conf
    '';
  };

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
