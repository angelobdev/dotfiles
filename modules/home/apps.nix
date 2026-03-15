{ pkgs, zen-browser, ... }:
{
  programs.vscode = {
    enable = true;
    package = pkgs.vscode;
    userSettings = {
      "password-store" = "gnome-libsecret";
      "workbench.iconTheme" = "material-icon-theme";
    };
  };

  home.packages = [
    zen-browser.packages.${pkgs.stdenv.hostPlatform.system}.default
  ];
}