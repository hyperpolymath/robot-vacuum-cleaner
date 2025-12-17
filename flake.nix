# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2025 Jonathan D.A. Jewell
# flake.nix — robot-vacuum-cleaner (Nix fallback, Guix is primary)
{
  description = "Robot Vacuum Cleaner - Simulation system with Julia and Rust implementations";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils.url = "github:numtide/flake-utils";
    rust-overlay = {
      url = "github:oxalica/rust-overlay";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, rust-overlay }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        overlays = [ (import rust-overlay) ];
        pkgs = import nixpkgs {
          inherit system overlays;
        };
        rustToolchain = pkgs.rust-bin.stable.latest.default.override {
          extensions = [ "rust-src" "rust-analyzer" ];
        };
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # Rust toolchain
            rustToolchain
            cargo-watch
            cargo-audit
            cargo-deny

            # Julia
            julia-bin

            # Build tools
            gnumake
            just
            pkg-config

            # Security tools
            gitleaks
            trivy

            # Development utilities
            git
            pre-commit
            hadolint

            # Container tools
            podman
            skopeo
          ];

          shellHook = ''
            echo "robot-vacuum-cleaner development environment"
            echo "Nix fallback shell (Guix is primary package manager)"
            echo ""
            echo "Available tools:"
            echo "  - Rust: $(rustc --version)"
            echo "  - Cargo: $(cargo --version)"
            echo "  - Julia: $(julia --version 2>/dev/null || echo 'not in PATH')"
            echo "  - Just: $(just --version)"
            echo ""
            echo "Run 'just' to see available commands"
          '';

          RUST_SRC_PATH = "${rustToolchain}/lib/rustlib/src/rust/library";
        };

        # NOTE: Build requires Cargo.lock to be generated first
        # Run: cd src/rust && cargo generate-lockfile
        packages.default = pkgs.rustPlatform.buildRustPackage {
          pname = "robot-vacuum-cleaner";
          version = "0.1.0";
          src = ./src/rust;
          cargoHash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="; # Update after first build

          meta = with pkgs.lib; {
            description = "Robot Vacuum Cleaner simulation system";
            homepage = "https://github.com/hyperpolymath/robot-vacuum-cleaner";
            license = with licenses; [ mit agpl3Plus ];
            maintainers = [];
          };
        };
      }
    );
}
