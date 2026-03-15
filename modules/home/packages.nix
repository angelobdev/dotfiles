{ pkgs, ... }:
{
  home.packages = with pkgs; [
    # System / Wayland utilities
    wl-clipboard      
    brightnessctl     
    hyprshot          
    hyprpicker        
    alacritty
    wofi
    hyprpaper
    udiskie
    zenity           

    # Apps
    fastfetch         
    nautilus          
    gnome-calculator
    smile             
  ];
}