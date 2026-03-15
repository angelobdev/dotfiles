{ pkgs, zen-browser, ... }:
{
  programs.vscode = {
    enable = true;
    package = pkgs.vscode;
    userSettings = {
      "password-store" = "gnome-libsecret";
      "workbench.iconTheme" = "material-icon-theme";
      "git.enableSmartCommit" = true;
      "git.confirmSync" = false;
    };
  };

  home.packages = [
    zen-browser.packages.${pkgs.stdenv.hostPlatform.system}.default
  ];
}