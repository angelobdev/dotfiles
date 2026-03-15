{ config, lib, pkgs, ... }:
{
  # For interactive shell sessions (zsh/bash)
  home.sessionPath = [
    "/etc/profiles/per-user/${config.home.username}/bin"
    "$HOME/.nix-profile/bin"
    "/run/current-system/sw/bin"
  ];

  # For systemd user services (waybar, dunst, etc.)
  # These don't inherit the login shell PATH
  systemd.user.sessionVariables = {
    PATH = lib.concatStringsSep ":" [
      "/etc/profiles/per-user/${config.home.username}/bin"
      "$HOME/.nix-profile/bin"
      "/nix/var/nix/profiles/default/bin"
      "/run/current-system/sw/bin"
      "$PATH"
    ];
  };
}