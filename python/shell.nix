{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.python39
    pkgs.python39Packages.typing-extensions
    pkgs.python39Packages.pyyaml
    pkgs.python39Packages.jinja2
    pkgs.python39Packages.more-itertools
    # Add here any custom package or provide the appropriate nix expression for 'tartanllama expected'
  ];
}
