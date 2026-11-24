"""Stage 1: real-world values in mm. Status word on each: user = given by the user 2026-11-24."""

PLATE_X = 200.0        # user: the 20 cm side, 3 holes along it
PLATE_Y = 210.0        # user
PLATE_T = 4.0          # user (corrected from 3 mm)

HOLE_X = 46.5          # user: long side of the hole, along X
HOLE_Y = 44.5          # user: short side, enlarged from ~37 (36.9-37.3 measured on the rhombus cover)
N_X = 3                # user / photos
N_Y = 4                # user / photos
MARGIN_X = 20.0        # user: hole edge to the plate edge, along X
MARGIN_Y = 3.6         # user: hole edge to the plate edge, along Y

PILLAR_LEG = 16.5      # user: the base pillar is a right-isosceles triangle, legs 16.5
SOCKET_CLEAR = 0.2     # user: clearance per face
SOCKET_WALL = 2.5      # user
SOCKET_DEPTH = 4.0     # user: insertion height, below the plate
