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
    hyprgrass.url = "github:horriblename/hyprgrass";
    hyprland.follows = "hyprgrass/hyprland";
  };

  outputs =
    {
      self,
      nixpkgs,
      home-manager,
      zen-browser,
      hyprland,
      hyprgrass,
      ...
    }:
    {
      nixosConfigurations.nixos = nixpkgs.lib.nixosSystem {
        system = "x86_64-linux";
        specialArgs = { inherit hyprland; };
        modules = [
          ./configuration.nix
          home-manager.nixosModules.home-manager
          {
            home-manager = {
              useGlobalPkgs = true;
              useUserPackages = true;
              backupFileExtension = "backup";
              extraSpecialArgs = { inherit self zen-browser hyprland hyprgrass; };
              users.angelo = import ./home.nix;
            };
          }
        ];
      };
    };
}
