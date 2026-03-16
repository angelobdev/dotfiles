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

  environment.systemPackages = with pkgs; [
    neovim
    wget
    git
    sddm-chili-theme
    stow
    libheif
    libheif.out
  ];

  environment.pathsToLink = [ "share/thumbnailers" ];
}
