{ pkgs, ... }:
{
  home.packages = with pkgs; [
    # System / Wayland utilities
    wl-clipboard      # wl-copy / wl-paste
    brightnessctl     # backlight control
    hyprshot          # screenshot tool
    hyprpicker        # color picker
    zenity            # GTK dialog boxes (used by scripts)

    # Apps
    fastfetch         # system info
    nautilus          # file manager
    gnome-calculator
    smile             # emoji picker
  ];
}