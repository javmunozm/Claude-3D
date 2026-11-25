"""Stage 1: real-world values in mm. Status word on each: user = given by the user 2026-11-24;
gcode = measured 2026-11-25 from sources/DeodorantBoxTop/*.gcode (XY x 0.997 to undo filament_shrink 99.7%)."""

PLATE_X = 200.0        # user; gcode: 200.000 on the original cover and the base
PLATE_Y = 212.0        # gcode: 212.000 on the original cover and the base (user first gave 210)
PLATE_T = 4.0          # user (corrected from 3 mm)

HOLE_X = 46.5          # user: long side of the hole, along X
HOLE_Y = 44.5          # user: short side, enlarged from ~37 (36.9-37.3 measured on the rhombus cover)
N_X = 3                # user / photos
N_Y = 4                # user / photos
MARGIN_X = 20.0        # user: hole edge to the plate edge, along X
MARGIN_Y = 3.6         # user: hole edge to the plate edge, along Y

POST_LEG = 18.0        # gcode: separate post joining base and cover, right-isosceles section, sharp legs 18.000
POST_R_APEX = 1.47     # gcode: post fillet at the right angle (fit rms 0.037); used only by the mating gate
POST_R_ACUTE = 1.34    # gcode: post fillets at the acute corners; used only by the mating gate
SOCKET_CLEAR = 0.2     # user: clearance per face
SOCKET_WALL = 2.5      # user
SOCKET_DEPTH = 4.0     # user: insertion height, below the plate
