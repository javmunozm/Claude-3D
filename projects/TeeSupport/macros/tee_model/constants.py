"""Stage 1: real-world values, millimetres.

Status words: USER (stated by the user), PHOTO (label in the product photo), PLACEHOLDER (fdm-tolerance must set it),
DESIGNED (a design choice in the approved plan, work/plan_build.md).
"""

ROD_D = 8.0            # USER 2026-11-15 ("usa 8 mm"); matches PHOTO "Inner Dia 8mm". Not caliper-measured.
BORE_CLEARANCE = 0.3   # PLACEHOLDER: diametral rod-in-bore clearance, to be set by fdm-tolerance.
WALL = 4.0             # USER: wall 2 -> 4 mm.
OVERALL = 50.0         # USER: overall size, tip of one arm to the far skin of another (photo's 38 mm, measured the same way).
GUSSET_T = 6.0         # USER: at least 5; 6 approved 2026-11-15.
GUSSET_TIP_PROUD = 4.0  # DESIGNED (option C, user-approved 2026-11-15): the gusset plate runs to the tips of both
                        # arms and stands this far proud of the tube surface there. Replaced the 30 mm triangle,
                        # which added no section beyond 22 mm from the centre (measured, work/plan_build.md pass 2).
END_CHAMFER = 0.5      # DESIGNED: outer edge chamfer at each arm tip.
BORE_CHAMFER = 0.8     # DESIGNED: entry chamfer of each bore (rod lead-in).

GUSSET_T_MIN = 5.0     # USER minimum.
