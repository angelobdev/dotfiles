{ config, pkgs, ... }: {

	home.username = "angelo";
	home.homeDirectory = "/home/angelo";
	home.stateVersion = "25.11";


	# PROGRAMS
	programs.git = {
    enable = true;
    userName = "Angelo Belcastro";
    userEmail = "angelo.belcastro01@gmail.com";
  };


	programs.bash = {
		enable = true;
		shellAliases = {
			btw = "echo I use nixos, btw";
		};
	};	

	programs.vscode = {
		enable = true;
		profiles.default.extensions = with pkgs.vscode-extensions; [
			dracula-theme.theme-dracula
			vscodevim.vim
			yzhang.markdown-all-in-one
		];
	};

	# Config files
	# home-file.".config/hypr".source = .dotfiles/hyprland/.config/hypr

	# Packages
	home.packages = with pkgs; [
		neovim
	];

}
