{ pkgs, ... }:
{
  # GTK theme
  gtk = {
    enable = true;

    theme = {
      name    = "adw-gtk3-dark";
      package = pkgs.adw-gtk3;
    };

    iconTheme = {
      name    = "Papirus-Dark";
      package = pkgs.papirus-icon-theme;
    };

    cursorTheme = {
      name    = "macOS";
      package = pkgs.apple-cursor;
      size    = 24;
    };

    gtk3.extraConfig.gtk-application-prefer-dark-theme = true;
    gtk4.extraConfig.gtk-application-prefer-dark-theme = true;
  };

  # Qt follows GTK dark theme
  qt = {
    enable         = true;
    platformTheme.name = "gtk";
    style.name         = "adwaita-dark";
  };

  # Cursor for Hyprland/Wayland
  home.pointerCursor = {
    name    = "macOS";
    package = pkgs.apple-cursor;
    size    = 24;
    gtk.enable = true;
    x11.enable = true;
  };

  # Make sure dark mode env vars are set
  home.sessionVariables = {
    GTK_THEME       = "adw-gtk3-dark";
    XCURSOR_THEME   = "macOS";
    XCURSOR_SIZE    = "24";
  };
}