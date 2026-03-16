{ pkgs, zen-browser, ... }:
{
  programs.vscode.enable = true;

  home.packages = with pkgs; [
    # System / Wayland utilities
    wl-clipboard
    brightnessctl
    hyprshot
    hyprpicker
    alacritty
    wofi
    hyprpaper
    udiskie
    zenity
    libsecret
    nixd
    nixfmt
    pavucontrol
    networkmanagerapplet

    # Apps
    fastfetch
    nautilus
    gnome-calculator
    smile
    zen-browser.packages.${pkgs.stdenv.hostPlatform.system}.default
    jetbrains-toolbox
  ];
}
