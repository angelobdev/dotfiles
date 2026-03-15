{ pkgs, ... }:
{
  programs.zsh.enable = true;
  programs.direnv.enable = true;
  
  services.udisks2.enable = true;

  environment.systemPackages = with pkgs; [
    neovim
    wget
    git
    kitty
    alacritty
    waybar
    wofi
    hyprpaper
    udiskie
  ];
}