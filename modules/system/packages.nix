{ pkgs, ... }:
{
  environment.systemPackages = with pkgs; [
    neovim
    wget
    git
    kitty
    alacritty
    waybar
    wofi
    hyprpaper
  ];
}