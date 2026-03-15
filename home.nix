{
  config,
  pkgs,
  self,
  zen-browser,
  hyprland,
  hyprgrass,
  ...
}:
{
  home.username = "angelo";
  home.homeDirectory = "/home/angelo";
  home.stateVersion = "25.11";

  programs.home-manager.enable = true;

  imports = [
    ./modules/home/git.nix
    ./modules/home/zsh.nix
    ./modules/home/files.nix
    ./modules/home/desktop.nix
    ./modules/home/packages.nix
    ./modules/home/theme.nix
    ./modules/home/hyprland.nix
  ];
}
