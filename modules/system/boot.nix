{ ... }:
{
  boot.loader.systemd-boot.enable      = true;
  boot.loader.efi.canTouchEfiVariables = true;
  boot.kernelPackages = (import <nixpkgs> {}).linuxPackages_latest;
}