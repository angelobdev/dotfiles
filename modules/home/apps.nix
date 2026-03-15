{ pkgs, zen-browser, ... }:
{
  programs.vscode.enable = true;

  home.packages = [
    zen-browser.packages.${pkgs.stdenv.hostPlatform.system}.default
  ];
}