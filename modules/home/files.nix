{ lib, ... }:
let
  dotfiles = "/home/angelo/.dotfiles";
in
{
  # Live symlinks via activation — edits take effect without rebuilding.
  # hyprland.conf itself is managed by the Hyprland home-manager module.
  home.activation.linkDotfiles = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    $DRY_RUN_CMD ln -sfn "${dotfiles}/config/alacritty"           "$HOME/.config/alacritty"
    $DRY_RUN_CMD ln -sfn "${dotfiles}/config/fastfetch"           "$HOME/.config/fastfetch"
    $DRY_RUN_CMD mkdir -p "$HOME/.config/hypr"
    $DRY_RUN_CMD ln -sfn "${dotfiles}/config/hypr/modules"        "$HOME/.config/hypr/modules"
    $DRY_RUN_CMD ln -sfn "${dotfiles}/config/hypr/scripts"        "$HOME/.config/hypr/scripts"
    $DRY_RUN_CMD ln -sfn "${dotfiles}/config/hypr/hypridle.conf"  "$HOME/.config/hypr/hypridle.conf"
    $DRY_RUN_CMD ln -sfn "${dotfiles}/config/hypr/hyprlock.conf"  "$HOME/.config/hypr/hyprlock.conf"
    $DRY_RUN_CMD ln -sfn "${dotfiles}/config/hypr/hyprpaper.conf" "$HOME/.config/hypr/hyprpaper.conf"
    $DRY_RUN_CMD mkdir -p "$HOME/.config/swaync"
    $DRY_RUN_CMD ln -sfn "${dotfiles}/config/swaync/style.css"    "$HOME/.config/swaync/style.css"
    $DRY_RUN_CMD ln -sfn "${dotfiles}/config/swayosd"             "$HOME/.config/swayosd"
    $DRY_RUN_CMD ln -sfn "${dotfiles}/config/waybar"              "$HOME/.config/waybar"
    $DRY_RUN_CMD ln -sfn "${dotfiles}/config/wofi"                "$HOME/.config/wofi"
  '';
}
