{ self, ... }:
{
  # Each entry maps a repo path → its ~/.config destination
  xdg.configFile = {
    "alacritty".source  = "${self}/config/alacritty";
    "fastfetch".source  = "${self}/config/fastfetch";
    "hypr".source       = "${self}/config/hypr";
    "swaync".source     = "${self}/config/swaync";
    "swayosd".source    = "${self}/config/swayosd";
    "waybar".source     = "${self}/config/waybar";
    "wofi".source       = "${self}/config/wofi";
  };

  home.file."Pictures/Wallpapers" = {
    source    = "${self}/files/wallpapers";
    recursive = true; # fixed: was missing on all directory sources
  };
}