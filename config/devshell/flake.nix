{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { nixpkgs, ... }:
    let pkgs = nixpkgs.legacyPackages.x86_64-linux; in {
      devShells.x86_64-linux.default = pkgs.mkShell {
        packages = with pkgs; [
          # Node.js
          nodejs_24          

          # Java
          jdk25
          maven
          gradle

          # Python
          python3
          python3Packages.pip
          python3Packages.virtualenv

          # Extras
          git          
        ];

        shellHook = ''
          echo ""
          echo "🛠  Dev environment active"
          echo "  node   $(node --version)"
          echo "  java   $(java --version 2>&1 | head -1)"
          echo "  python $(python3 --version)"
          echo ""
        '';
      };
    };
}