{ pkgs, ... }:
{
  programs.zsh.enable = true;
  programs.direnv.enable = true;
  
  services.udisks2.enable = true;
  services.power-profiles-daemon.enable = true;

  environment.systemPackages = with pkgs; [
    neovim
    wget
    git
    sddm-chili-theme
  ];
}