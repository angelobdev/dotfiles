{ self, config, ... }:
{
  # Each entry maps a repo path → its ~/.config destination
  xdg.configFile = {
    "alacritty".source = "${self}/config/alacritty";
    "fastfetch".source = "${self}/config/fastfetch";
    # hyprland.conf is managed by home-manager's Hyprland module; link everything else
    "hypr/modules".source = "${self}/config/hypr/modules";
    "hypr/scripts".source = "${self}/config/hypr/scripts";
    "hypr/hypridle.conf".source = "${self}/config/hypr/hypridle.conf";
    "hypr/hyprlock.conf".source = "${self}/config/hypr/hyprlock.conf";
    "hypr/hyprpaper.conf".source = "${self}/config/hypr/hyprpaper.conf";
    "swaync".source = "${self}/config/swaync";
    "swayosd".source = "${self}/config/swayosd";
    # Live symlink — edits take effect without rebuilding
    "waybar".source = config.lib.file.mkOutOfStoreSymlink "${self}/config/waybar";
    "wofi".source = "${self}/config/wofi";
  };
}
