{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.python310
    pkgs.python310Packages.wat
    pkgs.python310Packages.typing-extensions
    pkgs.python310Packages.pyyaml
    pkgs.python310Packages.jinja2
    pkgs.python310Packages.more-itertools
    # Add here any custom package or provide the appropriate nix expression for 'tartanllama expected'
  ];
}
