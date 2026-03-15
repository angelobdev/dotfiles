{ config, lib, pkgs, ... }:
{
  imports = [
    ./hardware-configuration.nix
    ./modules/system/boot.nix
    ./modules/system/networking.nix
    ./modules/system/display.nix
    ./modules/system/audio.nix
    ./modules/system/fonts.nix
    ./modules/system/packages.nix
    ./modules/system/onepassword.nix
  ];

  users.users.angelo = {
    isNormalUser = true;
    extraGroups  = [ "wheel" ];
    packages     = with pkgs; [ tree ];
  };

  programs.dconf.enable = true;
  programs.dconf.profiles.user.databases = [{
    settings."org/gnome/desktop/interface" = {
      gtk-theme           = "Adwaita-dark";
      icon-theme          = "Flat-Remix-Red-Dark-NF";
      font-name           = "Adwaita 11";
      document-font-name  = "Adwaita 11";
      monospace-font-name = "FiraCode Nerd Font Mono 11";
    };
  }];

  nixpkgs.config.allowUnfree = true;
  nix.settings.experimental-features = [ "nix-command" "flakes" ];
  system.stateVersion = "25.11";
}