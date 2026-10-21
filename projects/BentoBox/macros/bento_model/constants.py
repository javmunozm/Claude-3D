"""Measured inputs. All lengths in mm.

Source parts were split from sources/bentoBox/bento box no screws and magnets.step
into sources/bentoBox/parts/ (one STEP per named solid).
"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
SRC_PARTS = REPO / "sources" / "bentoBox" / "parts"
SLAB_SRC = SRC_PARTS / "net_infill_x4.step"   # solid 1.4 x 95 x 35 slab, print x4
CMAG_SRC = SRC_PARTS / "CMag_1.step"          # carbon cartridge tray (grooves at X 1.0-2.6 etc.)

# Slab as modelled (its own file coords): thickness along X, length Y, height Z.
SLAB_X = (-41.7, -40.3)
SLAB_Y = (2.5, 97.5)
SLAB_Z = (2.5, 37.5)

# Open window in front of each slab, measured from CMag_1 / CMag_2 faces.
# The slab file coordinates coincide with the cartridge's in Y and Z
# (groove Y 2..98, Z 2 (tray floor)..38 (lid), slab centred in it).
#   Y: rib end faces at Y=4.6 and Y=95.4 (CMag_1 and CMag_2)
#   Z: tray rib top Z=4.6 (CMag_1), lid rib underside Z=35.4 (CMag_2)
WINDOW_Y = (4.6, 95.4)
WINDOW_Z = (4.6, 35.4)

# Activated-carbon pellets: 4 mm typical diameter (supplier sheet, pelletised).
PELLET_D = 4.0
