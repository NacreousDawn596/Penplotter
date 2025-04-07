{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  buildInputs = [
    pkgs.python312Full
    pkgs.python312Packages.tkinter
    pkgs.python312Packages.opencv4
    pkgs.gcc
    pkgs.stdenv
    pkgs.mesa
    pkgs.zlib
    pkgs.gtk3
    pkgs.gtk3.dev
    pkgs.gtk2
    pkgs.gtk2.dev
    pkgs.tk
    pkgs.imagemagick
  ];

  shellHook = ''
    if [ ! -d "bin" ]; then
      ${python}/bin/python3 -m venv ./
    fi
    source ./bin/activate
    pip install -r requirements.txt
  '';
}

