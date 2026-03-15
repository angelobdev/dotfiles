{ pkgs, ... }:
{
  fonts.packages = with pkgs; [
    adwaita-fonts
    nerd-fonts.fira-code
    nerd-fonts.symbols-only
  ];
}
