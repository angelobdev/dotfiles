{ pkgs, zen-browser, ... }:
{
  programs.vscode.enable = true;
  programs.waybar.enable = true;

  home.packages = [
    zen-browser.packages.${pkgs.stdenv.hostPlatform.system}.default
  ];
}