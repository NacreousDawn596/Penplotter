{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  buildInputs = [
    pkgs.arduino-cli
    pkgs.python312Full
    pkgs.python312Packages.tkinter
    pkgs.python312Packages.opencv4
    pkgs.python312Packages.flask
    pkgs.python312Packages.flask-cors
    pkgs.python312Packages.numpy
    pkgs.python312Packages.pillow
    pkgs.avrdude
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
    pkgs.python312Packages.pyinstaller
  ];

  shellHook = ''
    if [ ! -d "bin" ]; then
      ${pkgs.python312Full}/bin/python3 -m venv ./
    fi
    source ./bin/activate
    pip install -r requirements.txt
    arduino-cli core install arduino:avr
    arduino-cli lib install Stepper
  '';
}
