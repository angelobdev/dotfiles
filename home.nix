{ config, pkgs, zen-browser, ... }: 

{
	home.username = "angelo";
	home.homeDirectory = "/home/angelo";
	home.stateVersion = "25.11";


	# PROGRAMS
	programs.git = {
    enable = true;
		settings = {
			user = {
				name = "Angelo Belcastro";
				email = "angelo.belcastro01@gmail.com";
			};
		};
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
			yzhang.markdown-all-in-one
		];
	};

	# Config files
	# home-file.".config/hypr".source = .dotfiles/hyprland/.config/hypr

	# Packages
	home.packages = with pkgs; [
		zen-browser.packages.${pkgs.stdenv.hostPlatform.system}.default
	];

}
