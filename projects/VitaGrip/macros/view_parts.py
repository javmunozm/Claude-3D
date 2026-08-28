"""
VitaGrip — viewer script
========================
Imports the builder from vita_grip_b123d.py (so the viewer never shows
stale geometry) and pushes the assembled grip to a running ocp-vscode
server.

Usage (two terminals):
    # Terminal 1 — start the viewer server (leave running)
    python -m ocp_vscode --port 3939 --axes --grid_xy --theme dark

    # Terminal 2 — send the part
    python macros/view_parts.py
"""

from ocp_vscode import show
from vita_grip_b123d import build_full_grip

if __name__ == "__main__":
    grip = build_full_grip()
    show(grip, names=["VitaGrip"])
    print("Sent VitaGrip to ocp-vscode viewer (http://localhost:3939)")
