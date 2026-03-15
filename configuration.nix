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
    shell        = pkgs.zsh;
    packages     = with pkgs; [ tree ];
  };

  nixpkgs.config.allowUnfree = true;
  nix.settings.experimental-features = [ "nix-command" "flakes" ];
  system.stateVersion = "25.11";
}