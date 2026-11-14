{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAll = f: nixpkgs.lib.genAttrs systems (s: f nixpkgs.legacyPackages.${s});
    in {
      packages = forAll (pkgs: {
        default = pkgs.python3Packages.buildPythonApplication {
          pname = "backglow";
          version = "0.1.0";
          pyproject = true;
          src = ./.;
          build-system = [ pkgs.python3Packages.setuptools ];
          dependencies = with pkgs.python3Packages; [ pygobject3 pywebview ];
          nativeBuildInputs = [ pkgs.wrapGAppsHook3 pkgs.gobject-introspection ];
          buildInputs = [ pkgs.gtk3 pkgs.webkitgtk_4_1 pkgs.glib-networking ];
          postInstall = ''
            install -Dm644 icons/backglow.svg $out/share/icons/hicolor/scalable/apps/backglow.svg
            install -Dm644 backglow.desktop $out/share/applications/backglow.desktop
            install -Dm644 60-backglow.rules $out/lib/udev/rules.d/60-backglow.rules
          '';
        };
      });
      nixosModules.default = { pkgs, ... }: {
        environment.systemPackages = [ self.packages.${pkgs.system}.default ];
        services.udev.packages = [ self.packages.${pkgs.system}.default ];
        boot.kernelModules = [ "i2c-dev" ];
      };
    };
}
