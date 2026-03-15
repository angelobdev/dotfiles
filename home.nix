{ config, pkgs, self, zen-browser, ... }:
{
  home.username    = "angelo";
  home.homeDirectory = "/home/angelo";
  home.stateVersion  = "25.11";

  programs.home-manager.enable = true;

  imports = [
    ./modules/home/git.nix
    ./modules/home/zsh.nix
    ./modules/home/apps.nix
    ./modules/home/files.nix
    ./modules/home/desktop.nix 
    ./modules/home/packages.nix
  ];
}