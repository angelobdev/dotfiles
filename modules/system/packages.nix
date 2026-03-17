{ pkgs, ... }:
{
  programs.zsh.enable = true;
  programs.direnv = {
    enable = true;
    nix-direnv.enable = true;
  };

  services.udisks2.enable = true;
  services.power-profiles-daemon.enable = true;
  services.gvfs.enable = true;
  services.blueman.enable = true;
  services.flatpak.enable = true;

  environment.systemPackages = with pkgs; [
    neovim
    wget
    git
    sddm-chili-theme
    stow
    libheif
    libheif.out
    xdg-desktop-portal-gnome
    xdg-desktop-portal-gtk
    xdg-desktop-portal-hyprland
    kdePackages.xdg-desktop-portal-kde
    xdg-desktop-portal-wlr
  ];

  environment.pathsToLink = [ "share/thumbnailers" ];
}
