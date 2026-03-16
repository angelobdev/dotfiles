{ config, ... }:
{
  xdg.configFile."devshell/flake.nix" = {
    source = config.lib.file.mkOutOfStoreSymlink
      "/home/angelo/.dotfiles/config/devshell/flake.nix";
  };

  programs.zsh.shellAliases = {
    devmode = "nix develop /home/angelo/.dotfiles/config/devshell";
  };
}