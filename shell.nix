{ pkgs ? import <nixpkgs> {} }:

let
  pythonWithTk = pkgs.python313Full.withPackages (ps: with ps; [
    pip
    tkinter
  ]);
in
pkgs.mkShell {
  buildInputs = with pkgs; [
    pythonWithTk
    tcl
    tk
  ];

  shellHook = ''
    export VENV_DIR="$PWD/.venv"
    # create the virtual environment if it doesn't exist
    if [ ! -d "$VENV_DIR" ]; then
      ${pythonWithTk}/bin/python -m venv $VENV_DIR
    fi
    # Activate the virtual environment
    source $VENV_DIR/bin/activate
    export PYTHONPATH="${pythonWithTk}/lib/python3.13/site-packages:$PYTHONPATH"
    export TCL_LIBRARY="${pkgs.tcl}/lib/tcl${pkgs.tcl.version}"
    export TK_LIBRARY="${pkgs.tk}/lib/tk${pkgs.tk.version}"
    if [ -f requirements.txt ]; then
      pip install -r requirements.txt
    fi
    python --version
  '';
}
