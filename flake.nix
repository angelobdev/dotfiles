{
  description = "Angelo's NixOS dotfiles";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    zen-browser = {
      url = "github:youwen5/zen-browser-flake";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    hyprland = {
      url = "github:hyprwm/Hyprland";
    };

    hyprgrass = {
      url = "github:horriblename/hyprgrass";
      inputs.hyprland.follows = "hyprland"; # pin to same version as system
    };
  };

  outputs = { self, nixpkgs, home-manager, zen-browser, hyprland, hyprgrass, ... }: {
    nixosConfigurations.nixos = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        ./configuration.nix
        hyprland.nixosModules.hyprland   # ← use flake Hyprland, not nixpkgs
        home-manager.nixosModules.home-manager
        {
          home-manager = {
            useGlobalPkgs       = true;
            useUserPackages     = true;
            backupFileExtension = "backup";
            extraSpecialArgs    = { inherit self zen-browser hyprland hyprgrass; };
            users.angelo        = import ./home.nix;
          };
        }
      ];
    };
  };
}