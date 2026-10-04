"""
build_case_ext.py - VitaGripPS5 grip case, round 16 (r15 with the R rim cut dropped, user 2026-10-03: RIM_CUT_ON = False
skips rim_mirror, the R rim is built as r13 built it; nothing else changed; r15 copy: audit/r16/build_case_ext_r15.py),
round 15 (one fix pass on r14, per audit/r14/review_r14.md "round 15
priorities"; user choice 2026-10-03) on round 14 (fix pass on the baked r13; register audit/r14/register_r14.md,
approved by the user 2026-10-02) on round 13 (finishing) on round 12 (register audit/r12/review_r12.md).

Round 15 (report audit/r15/fix_report_r15.md; baseline macro audit/r15/build_case_ext_r14.py). FINISH_ON kept.
P1 (D58 / D59 / D62): r14's vertical-prism rim cut (rim_outline) is gone from main(); L stays as scanned. rim_mirror
cuts the R rim wall down to the MIRRORED L wall, per (y, z) (not a vertical prism), with >= 6 mm blends at the start
and end, a z fade above FLOOR_Z and below the lower flank, and no action within WALL + 1 of a pit.
P2 (D60 / D61): the bar's rear-bottom edge is rolled over its whole length (r = min(1.5, 0.45 h), full for |x| <= 66, 10 mm
taper) by bar_edge_cut, ONE boolean with a lofted circle-segment cutter, instead of r14's vertex displacement. Tried first
and dropped: re-tessellating the rear face (retessellate_rear: 2 902 -> 162 946 faces in the zone), a pymeshlab isotropic
remesh of the band after the cut (43 150 faces < 0.2 deg, 9 131 folds, the volume changed by 15 mm3), cutter stations every
0.25 mm (1 360 new slivers), an extended chord at the arc ends (640 faces < 1e-4 mm2 against 256). P3: the r14 rim top-edge
roll (D50) is OFF (D50_ON): 162 new folds, and it cannot roll the flared flank. P4 (D56): bar_back_fill. collapse_slivers
(new, first thing in finish): edge collapse of faces with a min angle < 0.2 deg, checked per collapse (link condition, no
turn > 70 deg), because the two cuts leave thin pieces. The finish lock on the rim wall below the top-roll band is gone.

Round 14 (report audit/r14/fix_report_r14.md; baseline macro audit/r14/build_case_ext_r13.py). Stages added in main(),
all before finish(): trim_handles (D49: plane cut y = TRIM_Y on both handles + a TRIM_R rolling-ball roll on the cut
edge), roll_rim (D50 / D51: rim top edge r RIM_ROLL_R, bar rear-bottom edge r BAR_ROLL_R, same rolling-ball operator, as
height-field cuts), and the P2 / P4 form fixes named at their stages. finish_locks: the back-underside lock now covers
only columns whose back is thinner than BACK_LOCK_T and reaches oval + 4 at the rear. FINISH_ON still switches the
r13 finishing pass.

Round 13 (finishing; report audit/r13/fix_report_r13.md; baseline macro audit/r13/build_case_ext_r12.py). No redesign.
One switch, FINISH_ON (False rebuilds r12): (a) D39: in top_cut the cut floor may not go below the FILM_T rim beyond
the wall-end line (the ball opening had shaved it to films 0.00-0.01); (b) a last stage, finish(): the degenerate face is
collapsed, every fold > 150 deg with a free vertex is relaxed (travel <= FINISH_FIX_TRAVEL), and the free surface gets a
light Taubin smooth (normal component; tangential too only next to edges > 120 deg), travel <= FINISH_TRAVEL, with a fold
check (> FINISH_FOLD) and an area guard. Zero travel on the locks (finish_locks): top plane, pocket walls and floor,
lips and fingers, pit walls (WALL + 1), window and camera hole; quick fix (user 2026-10-02): also the back underside
under the pocket ring and the bottom bar's lower edge strip.

Round 12 changes (report: audit/r12/fix_report_r12.md):
P1/P1b the top is ONE planar cut at TOP_Z = LIP_TOP_Z 11.40 across the whole part, handles included; its edge with the
skin, with the top-edge opening line and with the corner clip is rolled (a ball opening of the target height field,
radius up to TOP_R_MAX, less beside the finger pits). One height-field difference (top_cut) replaces r11's front cut +
parabolic blend, the end roll and the top-edge opening prism B.
P2 the end roll (which cut the lobe down to FLOOR_Z) is gone; beyond the wall-end line the cut floor keeps a concave
base fillet FILL_RF (lobe material left in place, below the shoulder-button band). D42: zone pit fade widened.

Round 11 changes (report: audit/r11/fix_report_r11.md):
P1 the corner is no longer cut out and patched. The trigger-zone clear (a difference of everything below the floor
inside a polygon) and the refill (a separately built block unioned back) are removed. The corner underside is the
same smooth target U as the rest of the back, applied by the same underside warp and the same back cut; the paddles
hang below U (measured on the step-3c body: one material interval per column inside the clip, lowest Z -20..-26 vs
U -15..-21) and go with that cut. The flat face left by the top-edge opening beside each wall end S is replaced by
an end roll in the front-cut height field: the lobe's top rolls down to the floor toward the wall-end normal line,
over a width limited by WALL + END_PIT_M from the upper pit.
P2 LIP_T 3.4 -> 1.2 (audit/r11/lip_sizing_r11.md): lip top Z 11.40, console face 1.40 below it. The front cut's rim
level (LIP_TOP_Z) follows, so only the band round the pocket comes down; PIT_REQ_TOP_Z follows LIP_TOP_Z.

Round 10 changes (register IDs; causes measured in audit/r10/fix_report_r10.md):
G1b (D1/D2/D11/D12/D16/D19/D20/D21/D23) the trigger-zone refill is bounded by the lobe's own body above the floor
(not the scan silhouette) and its top follows that body's underside (r9: flat plane at FLOOR_Z + 0.5 -> ledge); the
zone's reach to the silhouette and its unfaded weight ramp in over Y1 - 7 .. Y1 - 1 (r9: switched at Y1 - 1 / Y1); the
pit exclusion fades over 3 mm. G4b (D22/D15/D28/D32) the bottom opening's lower edge is per side, from the measured
front face: in the air in front of the face, then one steep rise to the pocket bottom where the ring wall in front of
it is >= WALL + 0.15 at every Z (no wedge). G8 (D24/D25) deep fill follows the smoothed target Ts, not the scan's own
detail (the scan's 0.74 mm kink at Y -4.5 came through Us); the warp's forced full weight under the ring ramps in over
2.5 mm from the ring edge (r9: hard switch -> Dw -14.1 / -4.6 across one row at Y -11.5). G2b (D26) the lobe underside
target is lowered to its per-column convex hull. D8 (option B, D3 yields) the plan trim runs after step 4 (the step-4
fill widened the lobe after r9's trim) with its weight centred on the lower flank (the widest Z, -9..-2), away from the
pit tops. D17 front-cut blend softness 2.5 -> 4.5. Last stage: rolling-ball fillets per edge family (FILLET_R).

Round 9 changes (register IDs): G4 (D9/D6) the bottom-edge opening is one outline whose lower edge is a C1 curve from
(+-56, crotch - 0.5) to (+-70, -9) (r8: two boxes left a < 1 mm fin). G5 (D5) pit_required's box reaches LIP_TOP_Z.
D8 option B: step 3d plan_trim removes width (never adds) toward the user's bowed arc, capped by the pit walls; the
bow it could reach is logged. G2 (D10/D13/D15) the moderate part of the step-4 underside offset D is a vertex warp of
the scan's own underside (no dead band at D ~ 0); only the residual is slab / cut. G3 (D3) the fill fades in 1..5 mm
inside the silhouette (r8: 4..10). G1 (D1/D4/D7/D11/D12/D16) the trigger-zone outline is a smooth contour, reaches the
silhouette above Y1 - 1 and stays WALL + 3 clear of the pits. G6 (D17) the front cut rolls into the skin (smooth-min)
from 5 mm outboard of the ring. G7 (D18) diagnosed as scan shape, not smoothed (HSM_ITERS = 0). --dump writes the
step-4 fields and intermediate STLs for diagnosis.

"You have a DualSense, just extend the middle of the control and you will have the curvature."
The 1:1 DualSense scan is cut at x = 0 (halves moved -+DX, the gap bridged by the cut section carried straight
across) and then STRETCHED in Y over 1:1 Y_STR0..Y_STR1 by DY (r7: a stretch, not r6's inserted slice). The free
handles (below the crotch) are lengthened along their own axis and their cross-section scaled by HANDLE_GIRTH,
with a C1 blend from the root. The round-5 oval pocket and lip fingers are kept; a broad lobe swell keeps WALL
round every finger pit. The back is one convex arc per column from the handle belly to the top edge (fills the
waist, never above the required back); at the top corners the DualSense triggers are replaced below the floor
by that arc, rolled up into the corner clip. Rear window, camera hole, 2 flex fingers per end.

    python build_case_ext.py --out <path.stl>

--out is required and may not point into projects/VitaGripPS5/stl/: the user approves every STL
bake. Nothing runs on import. build_case.py (round 4) is imported for helpers only.

Frame: X width, Y fore-aft (handle tips at -Y, Vita top edge / L-R at +Y), Z up = console face
normal. Units mm.
"""

import argparse
import pathlib
import sys
import time

import numpy as np
import shapely
import trimesh
from scipy import ndimage
from scipy.spatial import cKDTree
from shapely.geometry import Point, Polygon, box as sbox
from shapely.ops import unary_union

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import build_case as bc  # noqa: E402  (round 4: helpers only, its main() is guarded)

STL_DIR = bc.STL_DIR
BIG = 400.0

# ---------------------------------------------------------------- step 1: extend the middle (X and Y)
DX = 26.0                    # brief: rigid move of each half (survey 2026-09-25)
DY = 30.0                    # brief (round 6): upper part moved +30
Y_STR0, Y_STR1 = -8.0, 40.0  # chosen (r7): 1:1 Y zone stretched by DY (user: "a stretch, not an inserted slice");
#   starts above the crotch (-13.5) so the handles keep their root, ends below the pocket's top edge (1:1 45.5)
Y_STR_R = 8.0                # chosen: stretch density ramps in/out over this (C1), flat between

# ---------------------------------------------------------------- step 2: handles
HANDLE_GIRTH = 1.10          # brief: cross-section scale of the free handles (user may change)
HANDLE_EXTRA = 22.0          # chosen: added root->tip length (brief: >= 20; 2 mm margin)
ROOT_BELOW_CROTCH = 1.0      # chosen: handle root = crotch (x = 0 section min Y) - this
GIRTH_BLEND = 12.0           # chosen: scale ramps 1 -> HANDLE_GIRTH over this length below the root (C1 cosine)
STRETCH_R1, STRETCH_U2, STRETCH_U3 = 8.0, 20.0, 30.0   # chosen: stretch density ramps up over 0..R1 below
#   the root, holds to U2, ramps down to 0 at U3; below U3 the tip is carried rigidly (rounded tip kept)
HANDLE_STATIONS_U = (16.0, 24.0, 27.0)   # chosen: girth gate stations (mm below the root, 1:1). r14 (D55): the third was
#   34 (final y -70.5), which the y -68 trim removes; 27 is final y about -62, outside the 3 mm roll zone (y < -65)

# ---------------------------------------------------------------- step 3: oval pocket (round 5, re-levelled)
CONSOLE_T = 18.6             # brief: PCH-1000 thickness
CLEAR_Y, CLEAR_Z = 0.50, 0.20   # brief
CAP_XC = 70.0                # brief: end-cap centres at x = +-70.0
CAP_A, CAP_B = 21.65, 42.275     # brief: cap semi-axes X x Y -> pocket 183.30 x 84.55
YC = 33.275                  # brief (round 6): pocket Y -9.0 .. 75.55
FACE_Z = 10.0                # brief (round 6): Vita face
LIP_U = FACE_Z + CLEAR_Z     # 10.2 lip underside
LIP_T = 1.2                  # r11: print-tolerance-expert, audit/r11/lip_sizing_r11.md (r10: 3.4)
LIP_TOP_Z = LIP_U + LIP_T    # 11.4 (r10: 13.6)
FLOOR_Z = FACE_Z - CONSOLE_T - CLEAR_Z   # -8.8
BACK_T = 3.5                 # brief
BACK_Z = FLOOR_Z - BACK_T    # -12.3 : the back's underside must be at or below this under the pocket
WALL = 3.0                   # brief
POCKET_Y_TOP = YC + CAP_B    # 75.55
POCKET_Y_BOTTOM = YC - CAP_B  # -9.0

# ---------------------------------------------------------------- step 4: back = one convex arc per column (r7)
Y_MONO = YC                  # chosen: above this Y the back may only rise toward the top edge (removes the
#   trigger remnants the user X'd on r6; they sat at |x| 70-80, Y 58-78, down to Z -29 against -20 around them)
X_MONO, X_MONO_RAMP = 55.0, 10.0   # chosen: the trigger zones are the ends only, fading in over |x| 55..65 (the
#   centre top bar keeps the DualSense's own contour; run 2 cut 1-3 mm off it)
ZONE_EDGE = 1.5              # chosen: the replaced zone stays this far inside the plan edge (at the edge its 1 mm
#   staircase side walls stood out as teeth at the wall end, run 18)
Y_TZ0, Y_TZ_R = 52.0, 8.0   # chosen: trigger zones fade in over Y 52..60 (lobe underside smooth below ~60, the
#   paddles above; read on the pre-step-4 body render, r7 run 12)
FILL_SIGMA = 3.0             # chosen: gaussian sigma (mm) of the underside offset field D (no dilation)
FILL_EDGE0, FILL_EDGE = -2.0, 4.0  # r9 (G3): the target fades in from 1 to 5 mm inside the scan's plan silhouette
#   (dP is measured to the plan eroded by OMEGA_ERODE 3). r8 (1, 6 = 4..10 mm inside) kept 16-46 % of the scan's own
#   concavity at the outer edge (D/net 0.84 / 0.54 at |x| 97 / 99, measured r9) -> the 0.7-0.8 mm hollow D3. The
#   moderate part of D is now a vertex warp (no slab staircase near the edge), so the fade can sit closer to it.
HIDE = 0.5                   # chosen: where nothing is added the slab bottom sits this far inside the scan
SLOPE0, SLOPE_W = 1.0, 1.0 # chosen: D fades out between underside slope 1 (45 deg) and 2 (63 deg)
HARD_R = 6.0                # chosen: outside the ring / pit the required-back ceiling rises as d^2 / (2 HARD_R)
HARD_K = 1.0                 # chosen: smooth-min softness (mm) between the target underside and that ceiling
END_ROLL_R = 12.0          # chosen: the back rolls up to the required back over this distance from the corner clip
MIN_RUN = 5                # chosen: column runs shorter than this (cells) are left as scanned

# ---------------------------------------------------------------- step 5: back fill
BACK_GRID = 1.0              # chosen: height-field grid step
BACK_MARGIN = 0.2            # chosen: required back + this
PAD_MIN = 3.0                # chosen (= WALL): material under a finger-pit bottom (in the convex-arc target)
DELTA_OUT = -3.0             # chosen: lobe-swell need outside the pits (negative = no swell)
OMEGA_ERODE = 3.0            # chosen: the slab domain stays this far inside the scan's plan silhouette
SLAB_OVER = 2.0              # chosen: outside the ring the slab top is this far above the scan underside
PLATE_R = 1.75               # chosen (round 5): bullnose radius of the slab's exposed lower edge

# ---------------------------------------------------------------- step 3b: lobe swell around the pits
LOBE_CX, LOBE_CZ = 80.0, 0.0   # chosen: radial centre of the swell in the lobe's X-Z section (inside the lobe)
LOBE_DTH = 2.0               # chosen: angular grid (deg)
LOBE_SIGMA = 10.0            # chosen (r7): smoothing (mm) along Y and along the section outline. r6 used 3.5 and
#   the swell read as two bumps per side (user X'd them); broad, it is one fuller end (2.0 in r6 run 2: 37 deg
#   normal jump per mm at Y 57)
LOBE_Y_PAD = 40.0            # chosen (r7): field domain reaches this far beyond the pits in Y (r6: 25, = 7 sigma)
LOBE_TH_FADE0, LOBE_TH_FADE = 100.0, 50.0   # chosen (r7): the field runs round the whole section and fades to 0
#   from |theta| 100 to 150 deg (r7 run 3 cut it off at 100 deg: a seam along the underside at |x| ~ 76)
LOBE_DIL = 3.0               # chosen: need grey-dilated by this many cells first (run 2 without: shortfall 1.3-1.7)
LOBE_MARGIN = 0.3            # chosen: required wall = WALL + this
PLAN_PAD = 10.0              # chosen (r7): the plan warp fades in/out over this at both ends of its Y range
PLAN_SIGMA = 4.0             # chosen (r7): gaussian sigma (mm, along Y) of the plan-hull shortfall
LOBE_R0, LOBE_RAMP = 4.0, 10.0  # chosen: the swell ramps in from r = 4 to r = 14 (pit and outer wall at r >= 14)
PIT_REQ_TOP_Z = LIP_U + 3.4  # r11 (D8 R, measured): kept at r10's 13.6, decoupled from the r11 lip top (11.4). Bisect:
#   hw bow R 0.97 both rounds; lw (step 3b swell) R 5.07 (r10) -> 3.94 with the box at 11.4, so the step-4d trim had
#   nothing to take and R ended 3.39 @ 26 %. With 13.6: R 3.72 @ 32 %, pit walls >= 3.48 to the local top 11.40, frame
#   and lip unchanged (the front cut trims the swell to the lowered band). r9 (G5): box reaches the lip top (r8: - WALL)

# ---------------------------------------------------------------- r9 additions
HSM_ITERS = 0                # r9 (G7): Taubin passes on the free handles -- OFF. D18 is carried from the scan (final
#   top = handle-warped scan top to 0.01 mm at the line, same 25-35 deg turn there), but it is shape, not a narrow
#   seam: 20 passes (r9 run 2) moved vertices up to 2.0 mm (p99 1.09), cut girth to x1.081-1.095 and only lowered
#   the R turn 30.3 -> 20.8 deg, bump 0.39 -> 0.41 mm. Removing it means reshaping the handle (user's call).
HSM_ROOT, HSM_TIP, HSM_RAMP = 4.0, 6.0, 6.0   # smoothing weight 0 at the root - 4 / the tip + 6, full 6 mm further in
PT_Y_LO, PT_Y_HI = -37.0, 62.0   # r9 (D8, option B): span of the user's drawn line (README r8 "Plan bow": ~99 mm,
#   r8's peak at Y 44 read as 18 % down -> top corner ~Y 62)
PT_PEAK = 0.36               # user: bow peak ~36 % down from the top corner
PT_BOW = {-1: 3.4, 1: 3.8}   # user: bow off the chord, L / R (mm)
PT_WIN = (-14.0, -8.0, 46.0, 52.0)  # r10: removal ramps out over Y 46..52 (r9: 52..60). D33 (measured, run b4: trim off -> L upper pit wall 3.49 at Z -8.3): the trim on the step-4 body folded the skin beside the L upper pit's end (enclosed air 4.49 mm2 at Z -8.3, x -99.7..-95.3, Y 53.5-57.3). Run b1 (r9 window, r10 weight)
#   left the L upper pit's upper-outer corner wall 2.76 at Z -8.3, air at (-96.4, 54.0)
PT_SIGMA = 3.0               # chosen: gaussian sigma (mm along Y) of the removal
PT_MARGIN = 0.35             # r10 (r9: 0.10): the per-Y radial check misses the diagonal distance at a pit's end corner
WARP_A = np.inf              # r9 (G2): the fill carried by the underside vertex warp saturates at this depth (tanh).
#   r9 run 2 used 8: the slab residual's own HIDE band then left the back 3.34-3.40 at (+-67, -8) (< BACK_T 3.5)
WARP_THICK = 0.6             # chosen: the warp never lifts the underside by more than this fraction of the column
CUT_BLEND_K, CUT_BLEND_D0, CUT_BLEND_D, CUT_BLEND_DELTA = 4.5, 5.0, 4.0, 0.3   # r10 (D17): K 2.5 -> 4.5. r9 (G6): the front cut is
#   smooth-min(H, skin + DELTA) with softness K near the line where H meets the skin; K is 0 within CUT_BLEND_D0 of
#   the ring (r9 run 2 ramped from the rim and thinned the upper pit walls at Z 13.0-13.5 to 2.51-3.20) and full
#   CUT_BLEND_D further out (the D17 crease sits ~8.8 mm outboard of the ring)
ZONE_W0, ZONE_SIGMA = 1e-3, 0.7   # r9 (G1): trigger-zone outline = 0.5 contour of the gaussian(sigma, cells) zone mask

# ---------------------------------------------------------------- r10 additions
ZONE_Y_RAMP = 6.0            # r10 (G1b): over Y1 - 1 - this .. Y1 - 1 the zone's inset and edge fade ramp to the corner
#   values (r9 switched both at one row: the D16 / D19 seam along Y 55-60.5)
ZONE_PIT_CLEAR, ZONE_PIT_FADE = 0.5, 8.0   # r12 (D42, review_r11: the 2 mm switch zu -> U at pit distance 5-7 is
#   the crease): the zone weight fades in from WALL + 0.5 over 8 mm. r10/r11: 1.5, 3.0 (r9: hard edge at WALL + 3)
ZONE_CLEAR_DZ = 0.05          # r10 (D34): the zone clear's top sits this far above FLOOR_Z (no coincident plane)
REFILL_IN = 0.5              # r10 (G1b): the refill stays this far inside the plan of the body above the floor
USM_D0, USM_W = 1.0, 2.0     # r10 (G8): where the fill D < -USM_D0 (full at -USM_D0 - USM_W) the target follows Ts
GRING_RAMP = 2.5             # r10 (G8): the warp's forced full weight under the ring ramps in over this from its edge
HULL_X0, HULL_Y1 = 68.0, 50.0   # r10 (G2b): lobe underside (|x| > HULL_X0, Y < HULL_Y1, faded 4 mm) lowered to its
#   per-column lower convex hull (only lowers: adds material, never above the ceiling)
PT_T0, PT_TW = -20.0, 25.0   # r10 (D8): plan-trim weight exp(-((theta - T0) / TW)^2), theta about (+-LOBE_CX,
#   LOBE_CZ); r9 cos^2 put 77 % of the removal on the pit tops (theta ~ 29 deg) and bound at 0.83 mm of room there.
#   Measured on r9: the plan width at Y 26-50 is carried by Z -9..-2 (theta -20..-5); at Z 10-13 it is 4-5 mm inside
OPEN_WALL = WALL + 0.15      # r10 (G4b): ring wall left in front of the opening's closed end, at every Z
OPEN_AIR = 0.4               # r10 (G4b): where the opening is through, its lower edge stays this far in front of the face
FILLET_R = {"corner": 1.5, "bottom-opening": 1.2, "front-cut": 2.5, "top-edge": 1.3, "back-bar": 1.9}  # user, r10
FILLET_DIH = 30.0            # edges sharper than this are fillet candidates (the auditor's family threshold)
FILLET_BAND, FILLET_H = 1.6, 2.0   # refine within FILLET_BAND * r of a candidate edge to edges <= r / FILLET_H
FILLET_CAP = 1.5             # a vertex needing a move > FILLET_CAP * r is left (the radius does not fit there; logged)
FILLET_TCAP, FILLET_MAXF = 120.0, 400000   # per family: time (s) and face caps; on either the family is skipped
FILLET_ORDER = ()   # r11: none. The r10 D29 clamp guarded only Z 13.3 (D37); its redo with a stop-short beside the
#   pits (and D27/D30/D31 by a new method) was not reached in the r11 pass (budget). r10: only D29 held. Run b3 (all five): top-edge and corner hit the 400 k face cap; back-bar 147 s, 8949 faces reverted (folds), 11 still flipped; bottom-opening 402 s, 57 791 of 64 223 moves shrunk to 0, 28 flipped; 35 156 faces < 1e-4 mm2 after
FILLET_ON = True             # r10 first pass: a global version (band 2.4 r, edges <= r / 3, all families at once) grew
#   the mesh 75 366 -> 1 450 038 faces and hung (> 280 s, 4.1 GB). Now one family at a time in a local box.
END_RE_MAX = 10.0            # r11 (P1, "no cropped face"): widest end roll (mm in plan, from the wall-end normal line)
END_PIT_M = 0.5              # r11: the roll keeps full height within WALL + this of an upper pit (its width shrinks there)
END_C = 0.15                 # r11: the roll ends this far above FLOOR_Z on the line (no plane coincident with the
#   top-edge opening's FLOOR_Z bottom, the D34 mechanism)
END_OVER, END_K = 2.0, 1.0   # r11: roll profile aims END_OVER above the skin; smooth-min softness into the skin
CORNER_STEP = 0.25           # r11 continuation (user: "finer surface for the corner only"): grid step in the corner windows
CORNER_XB = ((-106.0, -52.0), (52.0, 106.0))   # back-cut fine windows in x (the trigger zones, |x| > 55)
CORNER_YB = ((44.0, 82.0),)                    # ... and in Y (zone from Y 52, the pit ends from ~46)
CORNER_XB2 = ((-106.0, -80.0), (80.0, 106.0))  # front-cut fine windows (the end roll: from S (+-87, 59.4) outward)
CORNER_YB2 = ((48.0, 80.0),)
CORNER_UNDER = 0.3           # r11 continuation: in the zones the slab bottom sits this far below U (the cut trims it)
TOP_Z = LIP_TOP_Z            # r12 (P1, user): ONE planar top at the latch top, across the whole part, handles included
TOP_STEP = 0.25              # r12: grid of the top-cut height field (uniform: the rolled edge is a grey opening on it)
TOP_R_MAX = 3.0              # r12 (P1b, user): rolled-edge radius, the largest that fits up to this
TOP_RADII = (0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0)   # r12: openings computed at these radii, blended per node
TOP_PIT_M = 0.15             # r12: the rolled edge stays WALL + this clear of every finger pit (radius shrinks there)
TOP_TAU = 0.05               # r12: where the roll would take off less than this, the cut lifts into the air (no shaving)
TOP_WALL_K = 40.0            # r12: vertical cuts inside the height field (B line, clip K) as walls of slope 1:40 (88.6 deg),
#   so the cut surface is a smooth function on the grid (a binary step gives a 0.25 mm staircase)
TOP_RAY_BAND = (-6.0, 1.5)   # r12: exact 0.25 mm skin rays where the 1 mm skin is within this of TOP_Z (else interpolated)
BTN_Z_LO, BTN_MARGIN = -1.5, 1.0   # r12 (P2, shoulder_buttons_r11.md): button band bottom; the fill stays this far below it
FILM_T = 2.0                 # r12 (D39): beyond the line the cut floor stays this far above the rising lobe underside
TOP_PIT_GUARD = 0.35         # r12 (G11): the top cut never goes below the plane within WALL + this of a finger pit
FILL_RF = 6.0                # r12 (P2): concave base fillet beyond the wall-end line, top at FLOOR_Z + 6.0 = -2.8 <= -2.5
PT_PASSES = 2                # r10 (D8): the trim's weight is not uniform in Z, so after one pass the widest Z moves up
#   (run b1: L bow 4.34 at 22 % after one pass); a second pass trims the new widest Z

# ---------------------------------------------------------------- r13: finishing (user 2026-10-02: fill small
# imperfections, smooth the surfaces). ONE switch: False rebuilds r12 exactly (audit/r13/build_case_ext_r12.py)
FINISH_ON = True
FINISH_TRAVEL = 0.2          # user: the light smooth moves no vertex more than this (mm) from the r12 surface
FINISH_FIX_TRAVEL = 0.5      # chosen: local fold repair (D43 / D45 / single folds) may move its vertices up to this
FINISH_S_TRAVEL = 0.5        # r13 (D43): repair cap within 2.5 mm of a wall end S. Tried 1.0: folds unchanged (36), because
#   33 of the 38 fold vertices there lie on the pocket's oval wall (locked): the cusp is where the pocket wall, cut after
#   top_cut, meets the B wall end at an acute angle. Not reachable by vertex relaxation; left at FINISH_FIX_TRAVEL
FINISH_FIX_DIH = 150.0      # the auditor's fold threshold: edges above it seed the local repair
FINISH_FOLD = 120.0          # user: a move that leaves an incident dihedral above this (and above its value before) is undone
FINISH_PAIRS = 8             # chosen: Taubin lambda/mu pairs (volume preserving low-pass)
FINISH_LAMBDA, FINISH_MU = 0.5, -0.53
FINISH_THIN = 0.3            # a vertex with an opposite surface at distance g along its normal moves at most this * g
FINISH_DEG_EMAX = 0.05       # degenerate-face collapse edge limit (r12's face has a 0.029 edge, above fix_degenerate's 0.02)

# ---------------------------------------------------------------- r14 (register audit/r14/register_r14.md, user 2026-10-02)
TRIM_Y = -68.0               # D49 (user): plane cut, everything with y < TRIM_Y goes, both handles
TRIM_R = 3.0                 # D49: rolling-ball roll on the cut edge (a ball opening, not a CAD fillet: the L outline's
#   own corner radius is 1.16)
TRIM_STEP = 0.25             # D49: grid of the cut height field (over x, z; the height is y)
TRIM_CAP_H = 0.55            # D49: interior vertex spacing of the re-triangulated end faces
TRIM_LMAX = 0.60             # D49: the roll zone is refined to edges <= this (mm) before the vertices move
# r14 first try for D49, NOT kept: the roll as a height-field boolean cut (roll_cut, tau 0.02 / 0.05 / 0.10 / 0.30).
# tau 0.02 and 0.05 gave genus 3 (euler -4); 0.10 and 0.30 genus 2, but every variant left a ragged tangent junction
# in the render and ~140 extra folds / 465 degenerate faces, so the finish smooth could not act. roll_warp replaces it.
TRIM_BAND = 3.0              # D49: the roll acts where the skin is within this of the plane in y (the arc spans <= 2.3)
RIM_ROLL_R = 1.0             # D50 (register): rim top edge, rolling ball
BAR_ROLL_R = 1.5             # D51 (register): bar rear-bottom edge, rolling ball
ROLL_STEP = 0.15             # D50 / D51: grid of the roll field (over the plan, the height is z)
ROLL_LMAX = 0.35             # D50 / D51: the roll zone's edges are split (no closure) while longer than this (mm), at most
RIM_IN = 0.2                 # D48 / D52: the smoothed outline is moved this far inside the lobe, so the cut takes the ripple's peaks
RIM_SEC_Z, RIM_SIGMA = -11.5, 1.25   # D48 / D52: the section whose outline is smoothed (the register's z -11.5), sigma along it
ROLL_SMOOTH = 6              # passes of neighbour averaging of the take-off along the wall crease chain
ROLL_ITERS = 2               #   this many passes. The skin there is already 0.3-0.4 mm; at 0.25 and 60 passes the splits of
#   its long thin triangles ran away (0.05 mm edges, 300 k faces, 8 000 flipped faces)
RIM_WALL_FRAC, BAR_WALL_FRAC = 0.35, 0.45   # D50 / D51: the two rolls together may use at most 0.8 of the wall's height
ROLL_TAU = 0.02              # (roll_cut only, not used by r14's rolls) take-off below which that cut lifts off the skin
BACK_LOCK_T = 4.2            # r14 (user): the back-underside lock holds only columns whose back is thinner than this

# ---------------------------------------------------------------- r15 (review audit/r14/review_r14.md, user 2026-10-03)
RIM_M_Y = (58.0, 79.0)       # P1: rim_mirror grid (y, z) and step; the cutter is a height field x = f(y, z)
RIM_M_Z = (-23.0, -4.0)
RIM_M_STEP = 0.40            # (0.25 doubled the edge count along the crest: the same crest, sampled twice as finely, counts twice)
RIM_M_START = (60.5, 66.5)   # P1: cut weight ramps 0 -> 1 over >= 6 mm at the start ...
RIM_M_END = (70.0, 76.5)     #     ... and 1 -> 0 over 6.5 mm at the end
RIM_M_ZTOP = (-8.8, -6.3)    # P1: acts only at z <= FLOOR_Z, fading to 0 by -6.3 (the flank above the ledge stays R's own)
RIM_M_ZBOT = (-19.6, -16.5)  # P1: full weight down to z -16.5, 0 at -19.6 (L's bowl bottom is -19.1..-20.5 at y 63-70). Tried
#   (-17.5, -14.0): a visible dent where R is 0.3-0.8 mm lower than L on the lower flank; (-19.5, -12.5): the dent remained
#   as a scoop and a ridge in the corner closeup (the cut stopped halfway down a flank on which R is wider all the way);
#   (-22.0, -17.5): R followed L to the bowl, but where L has no material below its bowl bottom the cut stopped with a 0.4 mm
#   step at x 79-80 (sections y 66.5 / 68.5)
RIM_M_LIFT, RIM_M_TAU = 0.5, 0.40  # P1: cutter sits LIFT outside the skin where nothing is cut, and comes in over TAU
RIM_CUT_ON = False           # r16 (user 2026-10-03, "Drop the R rim cut"): rim_mirror is skipped. The r15 cut left a lens-shaped scoop on the
#   R flank at y 62-66 and raised the rim-box sharp edges (R 686 vs r13 307). True rebuilds r15's R rim.
RETRI_L = 1.0                # P2: rear-wall zone is refined (longest-edge, crack-free) to edges <= this before the roll
RETRI_ZONE = (80.0, 76.0, -9.0, -16.8)   # P2: |x| <= 80, y >= 76, z in (-16.8, -9.0)
BAR_TAPER = (66.0, 10.0)     # P2: bar roll full for |x| <= 66, tapering to 0 over 10 mm
BACK_FILL = 0.10             # P4 (D56): fill of the strip x -67..-63, y -9..-8 (mm)
BAR_X_END, BAR_DX = 74.0, 2.0 # P2: bar_edge_cut lofts sections every BAR_DX out to |x| = BAR_X_END
D19_ON = False               # r15: r14's D19 / D16 R crease smooth moved the unapproved slit lip M1b3 by 0.339 mm (measured r13 -> r14
#   and r13 -> r15 with it on, at (82.9, 56.2, -22.5)); the brief says keep that travel <= 0.05 or drop the smooth. The crease
#   it targeted (84.5, 58.5, -22) lies 2.8 mm from the lip start, so the two cannot be separated: the smooth is dropped
SLIVER_COLLAPSE = True
SLIVER_ANG, SLIVER_EMAX = 0.2, 0.30   # (0.60 and 6 passes: 467 left against 473, max move 0.56: not worth the move)# r15: collapse_slivers (the gate counts faces with min angle < 0.2 deg; r13: 307)
BAR_OUT = 0.05            # P2: the cutter's arc ends start this far outside the underside / wall plane
D50_ON, BAR_CUT_ON = False, True  # r15: D50 (the r14 rim top-edge roll_warp) is OFF. Bisected on the mirror-stage body: it alone
#   adds 162 edges > 150 deg (cells x 72-88, y 72-80, z -12..-8: the K wall and the rear corner arc; 125-164 flipped faces
#   before the finish) and it cannot roll the flared corner flank at all (a vertex displacement along z leaves the flank by
#   0.7 tl). The rim top edge stays as r13 built it. (Left in roll_rim, switchable, for the record.)
RIM_M_SIGMA = 0.4          # P1: the mirrored L wall is smoothed (Gaussian, mm) before it becomes the R wall: copying the scan's
#   0.25 mm facet noise gave 480 edges > 90 deg in the R rim box
BAR_EPS, BAR_K, BAR_RMIN = 0.04, 8, 0.12  # P2: circle moved eps into the corner (crosses the faces at ~16 deg), arc segments, min r

# ---------------------------------------------------------------- front cut, top edge, bottom edge (round 5)
CAP_R = 10.0                 # chosen: outboard of the rim the cut surface rises as d^2 / (2 CAP_R)
CAP_GRID = 1.0
X_LR_END = 87.0              # chosen (r5): L/R reach |x| ~85 (+-2) + 2 -> wall ends at x 87 on the arc
END_R = 2.0
D0_MARGIN = 0.3
X_OPEN = CAP_XC              # brief: bottom edge open above the floor for |x| < 70
X_OPEN_FAR = 56.0            # chosen: bottom-edge opening also runs out to the crotch - 0.5 for |x| < this
#   (the scan's bottom edge reaches Y -13.48 at x = 0; r5 stopped at -13 and left a 0.5 mm fin)
# r9 (G4): lower edge of the opening for |x| 56..70 as a C1 Hermite curve, y relative to crotch - 0.5 except the end
# (pocket end, POCKET_Y_BOTTOM). The scan face in front of the opening (r8 measured): R y -13.7 at x 56-62, -14.2 at 64,
# -15.2 at 66, -17.5 at 68; L about 0.7 mm further +Y. Dip over x 56-62 is in air (no material at any Z there).
C_EDGE_X = (X_OPEN_FAR, 62.0, 64.0, 66.5, X_OPEN)
C_EDGE_DY = (0.0, -1.0, 0.1, None, None)       # relative to crotch - 0.5 (None: absolute below)
C_EDGE_Y_ABS = (None, None, None, -11.3, POCKET_Y_BOTTOM)
C_EDGE_SLOPE = (0.0, 0.0, 0.75, 0.9, 0.5)

# ---------------------------------------------------------------- window, camera
PANEL_W, PANEL_H = 108.0, 55.0     # brief
PANEL_FROM_TOP, PANEL_FROM_BOTTOM = 16.0, 12.5
WINDOW_GROW = 1.0
WINDOW_R = 3.5
CAMERA_FROM_TOP = 7.0
CAMERA_HOLE_D = 12.0
CONSOLE_TOP_Y = POCKET_Y_TOP - CLEAR_Y
CONSOLE_BOT_Y = POCKET_Y_BOTTOM + CLEAR_Y
WIN_Y1 = CONSOLE_TOP_Y - PANEL_FROM_TOP + WINDOW_GROW
WIN_Y0 = CONSOLE_BOT_Y + PANEL_FROM_BOTTOM - WINDOW_GROW
WINDOW_W = PANEL_W + 2 * WINDOW_GROW
CAMERA_Y = CONSOLE_TOP_Y - CAMERA_FROM_TOP

# ---------------------------------------------------------------- fingers (round 5, unchanged)
FINGER_W = 15.0
FINGER_T_ROOT, FINGER_T_TIP = 1.8, 0.9
FINGER_GAP = 2.5
FINGER_ROOT_BELOW_FLOOR = 5.0
FINGER_ROOT_R = 1.0
FINGER_SLOT = 1.0
FINGER_INNER_SLOT = 1.5
PIT_CORNER_R = 2.5
LIP_OVERHANG = 1.5
LIP_LEAD_DEG = 30.0
LIP_RET_DEG = 127.0
LIP_FLAT = 0.50
LIP_LAND = 0.8
FINGER_END_CLEAR = 3.9       # chosen (r5: 3.0): at 3.0 the upper pit kept only 2.5 to the top-corner clip (all Z)
CLEAN_TOL = 0.01
ROOT_Z = FLOOR_Z - FINGER_ROOT_BELOW_FLOOR   # -13.8


# ================================================================ geometry helpers
DROPPED = []
DUMP = None      # r9: set by --dump (prefix for step-4 fields and intermediate STLs); diagnostics only


def boolean(op, a, b, what, fill_voids=False):
    """Manifold boolean; zero-volume shells (< 0.01 mm3) are dropped and logged, more than one real body raises.
    fill_voids: sealed air pockets (inner shells, negative volume) are made solid and logged instead of raising."""
    fn = {"union": trimesh.boolean.union, "difference": trimesh.boolean.difference,
          "intersection": trimesh.boolean.intersection}[op]
    r = fn([a, b], engine="manifold")
    if r is None or len(r.faces) == 0:
        raise RuntimeError("%s (%s) returned an empty mesh" % (what, op))
    comps = r.split(only_watertight=False)
    if fill_voids:
        voids = [c for c in comps if c.volume < -0.01]
        if voids:
            DROPPED.append("%s: filled %d sealed void(s) %s" % (what, len(voids), [
                "%.2f mm3 %s" % (-c.volume, np.round(c.bounds, 1).tolist()) for c in voids]))
            comps = [c for c in comps if c.volume >= -0.01]
            r = trimesh.util.concatenate(comps)
    real = [c for c in comps if c.volume > 0.01]
    junk = [c for c in comps if c.volume <= 0.01]
    if len(real) != 1 or any(c.volume < -0.01 for c in junk):
        raise RuntimeError("%s (%s): shells %s" % (what, op, ["%.2f %s" % (c.volume, np.round(c.bounds, 1).tolist())
                                                              for c in comps]))
    if junk:
        DROPPED.append("%s: dropped %d sliver shell(s) %s" % (what, len(junk), [np.round(c.bounds, 1).tolist()
                                                                               for c in junk]))
        return real[0]
    return r


def mprism(poly, z0, z1, log=None, what=""):
    gs = [q for q in getattr(poly, "geoms", [poly]) if q.area >= 0.01]
    if log is not None and len(gs) > 1:
        log.append("  %s plan: %d pieces, areas %s" % (what, len(gs), [round(q.area, 1) for q in gs]))
    return trimesh.util.concatenate([bc.prism(q, z0, z1) for q in gs])


def ramp(t):
    t = np.clip(t, 0.0, 1.0)
    return (1.0 - np.cos(np.pi * t)) / 2.0


def fine_axis(base, bands, step=None):
    """r11: rectilinear axis = the base nodes plus a CORNER_STEP grid over each band (one height field, locally fine)."""
    step = CORNER_STEP if step is None else step
    a = np.concatenate([base] + [np.arange(lo, hi + 1e-9, step) for lo, hi in bands])
    a = np.unique(np.round(a, 6))
    return a[np.concatenate([[True], np.diff(a) > 0.05])]


def ball_open(h, r, step):
    """r12: grey opening of the height field h (material below it) by a ball of radius r, i.e. the surface a ball rolled
    under h can reach. Every convex edge sharper than radius r becomes a circular arc of radius r tangent to both
    faces; concave edges and smooth regions are unchanged; the result is never above h (it only removes)."""
    if r <= 1e-6:
        return h.copy()
    n = int(np.ceil(r / step))
    o = np.arange(-n, n + 1) * step
    DX_, DY_ = np.meshgrid(o, o, indexing="ij")
    rr = DX_ ** 2 + DY_ ** 2
    fp = rr <= r * r + 1e-9
    s = np.where(fp, np.sqrt(np.maximum(r * r - rr, 0.0)), 0.0)
    e = ndimage.grey_erosion(h, footprint=fp, structure=s, mode="nearest")      # ball centre heights
    return ndimage.grey_dilation(e, footprint=fp, structure=s, mode="nearest")  # union of the balls


def oval_loop(n_cap=241, n_line=141):
    """Pocket outline (ccw) and unit outward normals: straight top/bottom + elliptical caps."""
    t = np.linspace(-np.pi / 2, np.pi / 2, n_cap)
    rc = np.column_stack([CAP_XC + CAP_A * np.cos(t), YC + CAP_B * np.sin(t)])
    rn = np.column_stack([CAP_B * np.cos(t), CAP_A * np.sin(t)])
    xs = np.linspace(CAP_XC, -CAP_XC, n_line)[1:-1]
    top = np.column_stack([xs, np.full(len(xs), POCKET_Y_TOP)])
    t2 = np.linspace(np.pi / 2, 3 * np.pi / 2, n_cap)
    lc = np.column_stack([-CAP_XC + CAP_A * np.cos(t2), YC + CAP_B * np.sin(t2)])
    ln = np.column_stack([CAP_B * np.cos(t2), CAP_A * np.sin(t2)])
    bot = np.column_stack([-xs, np.full(len(xs), POCKET_Y_BOTTOM)])
    P = np.vstack([rc, top, lc, bot])
    N = np.vstack([rn, np.tile([0.0, 1.0], (len(xs), 1)), ln, np.tile([0.0, -1.0], (len(xs), 1))])
    N = N / np.linalg.norm(N, axis=1)[:, None]
    return P, N


def c_edge_y(y0):
    return [y0 + d if d is not None else a for d, a in zip(C_EDGE_DY, C_EDGE_Y_ABS)]


def c_plan_outline(y0):
    """Bottom-edge opening (r9, G4): Y from the lower edge up to POCKET_Y_BOTTOM + 0.1 for |x| <= X_OPEN; lower edge
    flat at y0 for |x| <= X_OPEN_FAR, then the C1 Hermite curve C_EDGE_* to (+-X_OPEN, POCKET_Y_BOTTOM)."""
    from scipy.interpolate import CubicHermiteSpline
    cs = CubicHermiteSpline(C_EDGE_X, c_edge_y(y0), C_EDGE_SLOPE)
    xr = np.linspace(X_OPEN_FAR, X_OPEN, 113)
    right = np.column_stack([xr, cs(xr)])                       # x 56 -> 70
    left = right[::-1] * [-1.0, 1.0]                            # x -70 -> -56
    top = POCKET_Y_BOTTOM + 0.1
    return np.vstack([[(-X_OPEN, top)], left, right, [(X_OPEN, top)]])


def front_face(mesh, sgn, xg):
    """r10 (G4b): Y of the outer face in front of the pocket bottom, per x: rays from (x, POCKET_Y_BOTTOM - 0.3, z)
    toward -Y, at every Z from the floor to the lip top; only rays that start in material (first hit = exit) count.
    Returns (min over Z, max over Z) per x (nan where no ray starts in material)."""
    zs = np.arange(FLOOR_Z + 0.3, LIP_TOP_Z - 0.2, 0.5)
    Xg, Zg = np.meshgrid(xg, zs, indexing="ij")
    O = np.column_stack([sgn * Xg.ravel() + JIT[0], np.full(Xg.size, POCKET_Y_BOTTOM - 0.3), Zg.ravel()])
    Dd = np.tile([0.0, -1.0, 0.0], (len(O), 1))
    h = first_hits(mesh, O, Dd)
    yf = np.array([np.nan if q is None or mesh.face_normals[q[1]][1] >= 0 else q[0][1] for q in h]).reshape(Xg.shape)
    with np.errstate(all="ignore"):
        return np.nanmin(yf, axis=1), np.nanmax(yf, axis=1)


def c_plan_r10(mesh, y0, log):
    """r10 (G4b, D22/D15): bottom-edge opening, lower edge per side from the measured front face. Where the ring wall
    in front of the pocket bottom could not keep OPEN_WALL at every Z, the opening is through: its edge stays OPEN_AIR
    in front of the face at every Z (no material left there). From the first x where the wall keeps OPEN_WALL at every
    Z, the opening is closed: one steep end, so the wall it leaves ends square (r9: the C1 curve crossed the face at a
    shallow angle and left a 0.7 mm knife wedge at |x| 64-65). The face is undercut (Y -11.2 at Z -8.5, -13.5..-16 at
    Z 3-9 for |x| 56-66), so a wall 3 mm inside it at every Z cannot be kept in front of the pocket there."""
    xg = np.arange(X_OPEN_FAR, X_OPEN + 1e-6, 0.25)
    top = POCKET_Y_BOTTOM + 0.1
    sides = {}
    for sgn in (1, -1):
        fmin, fmax = front_face(mesh, sgn, xg)
        ok = np.isfinite(fmax) & (fmax <= POCKET_Y_BOTTOM - OPEN_WALL)
        # the closed end: first x from which the wall keeps OPEN_WALL for the rest of the range
        tail = np.flatnonzero(~ok)
        ic = len(xg) if not len(tail) else tail[-1] + 1
        ic = min(ic, len(xg) - 1)
        xc = xg[ic]
        e = np.minimum(y0, np.where(np.isfinite(fmin), fmin, y0) - OPEN_AIR)[:ic]
        e = np.minimum.accumulate(e)                 # never back toward the face: one monotone dip into the air
        pts = [(sgn * x, v) for x, v in zip(xg[:ic], e)] + [(sgn * xc, e[-1] if len(e) else y0), (sgn * xc, top)]
        sides[sgn] = pts
        log.append("  bottom opening side %+d: through to |x| %.2f (edge %.2f..%.2f, face min %.2f / max %.2f at the "
                   "end), closed from |x| %.2f where the wall in front of the pocket is >= %.2f at every Z (face max %.2f)"
                   % (sgn, xg[ic - 1] if ic else X_OPEN_FAR, e.max() if len(e) else y0, e.min() if len(e) else y0,
                      fmin[ic - 1] if ic else np.nan, fmax[ic - 1] if ic else np.nan, xc, OPEN_WALL, fmax[ic]))
    left = sides[-1][::-1]                          # (-xc, top) ... (-56, ..)
    return Polygon(left + sides[1])


def hf_solid(xs, ys, Hlo, Hhi):
    """Closed solid between the grid surfaces z = Hlo(x, y) and z = Hhi(x, y) (Hhi > Hlo everywhere)."""
    Hlo = np.broadcast_to(Hlo, (len(xs), len(ys))).astype(float)
    Hhi = np.broadcast_to(Hhi, (len(xs), len(ys))).astype(float)
    if (Hhi - Hlo).min() < 0.01:
        raise RuntimeError("height-field solid: top not above bottom (min gap %.3f)" % (Hhi - Hlo).min())
    nx, ny = len(xs), len(ys)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    nv = nx * ny
    V = np.vstack([np.column_stack([X.ravel(), Y.ravel(), Hlo.ravel()]),
                   np.column_stack([X.ravel(), Y.ravel(), Hhi.ravel()])])
    idx = np.arange(nv).reshape(nx, ny)
    a, b, c, d = idx[:-1, :-1].ravel(), idx[1:, :-1].ravel(), idx[1:, 1:].ravel(), idx[:-1, 1:].ravel()
    F = [np.column_stack([a, c, b]), np.column_stack([a, d, c]),
         np.column_stack([a, b, c]) + nv, np.column_stack([a, c, d]) + nv]
    loop = np.concatenate([idx[:, 0], idx[-1, 1:], idx[-2::-1, -1], idx[0, -2:0:-1]])
    p, q = loop, np.roll(loop, -1)
    F += [np.column_stack([p, q, q + nv]), np.column_stack([p, q + nv, p + nv])]
    m = trimesh.Trimesh(V, np.vstack(F), process=True)
    if not m.is_watertight or m.volume <= 0:
        raise RuntimeError("height-field solid not watertight / inverted")
    return m


def first_hits(mesh, O, D):
    loc, ri, tri = mesh.ray.intersects_location(np.asarray(O, float), np.asarray(D, float), multiple_hits=False)
    out = [None] * len(O)
    for l_, r_, t_ in zip(loc, ri, tri):
        out[r_] = (l_, t_)
    return out


JIT = np.array([0.01372, 0.02914])   # probe offset: rays exactly on 1 mm height-field grid vertices are missed


def z_from(mesh, X, Y, below=True):
    """First surface Z hit by vertical rays from below (below=True) or from above; nan where none."""
    X, Y = np.asarray(X, float), np.asarray(Y, float)
    n = X.size
    z0, dz = (-300.0, 1.0) if below else (300.0, -1.0)
    O = np.column_stack([X.ravel() + JIT[0], Y.ravel() + JIT[1], np.full(n, z0)])
    h = first_hits(mesh, O, np.tile([0, 0, dz], (n, 1)))
    return np.array([np.nan if q is None else q[0][2] for q in h]).reshape(X.shape)


def top_z(mesh, xy):
    xy = np.asarray(xy, float)
    return z_from(mesh, xy[:, 0], xy[:, 1], below=False)


# ================================================================ step 1
def extend_axis(mesh, axis, c, d_lo, d_hi):
    """Cut the mesh at coordinate[axis] = c, move the low part by d_lo and the high part by d_hi along axis,
    bridge the two open cut loops with the section carried straight across (one quad per loop edge)."""
    e = np.zeros(3)
    e[axis] = 1.0
    other = [k for k in range(3) if k != axis]
    halves = []
    for sgn in (-1.0, 1.0):
        o = np.zeros(3)
        o[axis] = c
        h = mesh.slice_plane(o, sgn * e, cap=False)
        v = h.vertices.copy()
        v[np.abs(v[:, axis] - c) < 1e-7, axis] = c
        halves.append(trimesh.Trimesh(v, h.faces, process=True))
    L, R = halves

    def boundary(m):
        return m.edges[trimesh.grouping.group_rows(m.edges_sorted, require_count=1)]

    bL, bR = boundary(L), boundary(R)
    uL, uR = np.unique(bL), np.unique(bR)
    if np.abs(L.vertices[uL, axis] - c).max() > 1e-9 or np.abs(R.vertices[uR, axis] - c).max() > 1e-9:
        raise RuntimeError("open boundary not on the cut plane")
    if len(uL) != len(uR):
        raise RuntimeError("cut loops differ: %d vs %d vertices" % (len(uL), len(uR)))
    d, j = cKDTree(R.vertices[uR][:, other]).query(L.vertices[uL][:, other])
    if d.max() > 1e-6:
        raise RuntimeError("cut loops do not match (max %.2e)" % d.max())
    nL = len(L.vertices)
    mp = np.zeros(nL, int)
    mp[uL] = uR[j] + nL
    VL = L.vertices.copy()
    VL[:, axis] += d_lo
    VR = R.vertices.copy()
    VR[:, axis] += d_hi
    a, b = bL[:, 0], bL[:, 1]
    V = np.vstack([VL, VR])
    for bridge in (np.vstack([np.column_stack([b, a, mp[a]]), np.column_stack([b, mp[a], mp[b]])]),
                   np.vstack([np.column_stack([a, b, mp[a]]), np.column_stack([mp[a], b, mp[b]])])):
        m = trimesh.Trimesh(V, np.vstack([L.faces, R.faces + nL, bridge]), process=False)
        if m.is_winding_consistent and m.is_watertight and m.volume > 0:
            m.metadata["ext_info"] = dict(loop_verts=len(uL), bridge_tris=len(bridge))
            return m
    raise RuntimeError("extension along axis %d: no bridge winding gives a watertight positive solid" % axis)


def stretch_axis(mesh, axis, a, b, d, r):
    """Move every vertex with coordinate[axis] >= b by d, and stretch the zone a..b to a..b+d with a C1
    flat-topped density (ramps over r at each end): the surface stays one continuous curve, no inserted band."""
    uu = np.linspace(a, b, 4801)
    w = ramp((uu - a) / r) * (1.0 - ramp((uu - (b - r)) / r))
    k = d / np.trapz(w, uu)
    f = 1.0 + k * w
    U = a + np.concatenate([[0.0], np.cumsum((f[1:] + f[:-1]) / 2.0 * np.diff(uu))])
    V = mesh.vertices.copy()
    c = V[:, axis]
    V[:, axis] = np.where(c <= a, c, np.where(c >= b, c + d, np.interp(c, uu, U)))
    m = trimesh.Trimesh(V, mesh.faces, process=False)
    if not m.is_watertight or not m.is_winding_consistent or m.volume <= 0:
        raise RuntimeError("stretch along axis %d broke the mesh" % axis)
    m.metadata["stretch_info"] = dict(peak=f.max())
    return m


def convex_back(zu, valid, req, ys, y_mono):
    """Per X column, per contiguous run of cells: above y_mono the underside may only rise (running max: cuts
    dips such as the trigger remnants), then the whole run is replaced by its lower convex hull taken under
    min(that, req) -- one convex arc from the handle belly to the top edge, never above the required back."""
    T = np.full(zu.shape, np.nan)
    for i in range(zu.shape[0]):
        v = valid[i]
        edges = np.flatnonzero(np.diff(np.concatenate([[0], v.astype(int), [0]])))
        for s, e in zip(edges[::2], edges[1::2]):
            if e - s < MIN_RUN:
                T[i, s:e] = zu[i, s:e]
                continue
            y, z = ys[s:e], zu[i, s:e].copy()
            k = np.flatnonzero(y >= y_mono)
            if len(k):
                z[k] = np.maximum.accumulate(z[k])
            t = np.minimum(z, req[i, s:e])
            hx, hy = [], []
            for p, q in zip(y, t):
                while len(hx) >= 2 and (hx[-1] - hx[-2]) * (q - hy[-2]) - (hy[-1] - hy[-2]) * (p - hx[-2]) <= 0:
                    hx.pop()
                    hy.pop()
                hx.append(p)
                hy.append(q)
            T[i, s:e] = np.interp(y, hx, hy)
    return T


# ================================================================ step 2: handles
def handle_section(mesh, y, sgn):
    """Largest section polygon (x, z) of the handle on side sgn at Y = y (None if none)."""
    sec = mesh.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    if sec is None:
        return None
    best = None
    for d in sec.discrete:
        if len(d) < 4:
            continue
        pg = Polygon(d[:, [0, 2]]).buffer(0)
        if pg.is_empty or np.sign(pg.centroid.x) != sgn:
            continue
        if best is None or pg.area > best.area:
            best = pg
    return best


def stretch_profile():
    uu = np.linspace(0.0, 120.0, 12001)
    r = ramp(uu / STRETCH_R1) * (1.0 - ramp((uu - STRETCH_U2) / (STRETCH_U3 - STRETCH_U2)))
    k1 = HANDLE_EXTRA / np.trapz(r, uu)
    f = 1.0 + k1 * r
    U = np.concatenate([[0.0], np.cumsum((f[1:] + f[:-1]) / 2.0 * np.diff(uu))])
    s = 1.0 + (HANDLE_GIRTH - 1.0) * ramp(uu / GIRTH_BLEND)
    return uu, f, U, s, k1


def handle_warp(mesh, y_root, log):
    """Below y_root: stretch each handle along its own centreline (C1 density profile, tip carried rigidly)
    and scale its Y-section about the section centroid by s(u) (C1 ramp from 1 at the root)."""
    uu, f, U, s, k1 = stretch_profile()
    V = mesh.vertices.copy()
    info = dict(k=1.0 + k1, uu=uu, U=U, s=s)
    for sgn in (-1, 1):
        sel = (np.sign(V[:, 0]) == sgn) & (V[:, 1] < y_root)
        tip = V[sel, 1].min()
        ys = np.arange(y_root, tip + 0.3, -0.5)
        us, cx, cz = [], [], []
        for y in ys:
            pg = handle_section(mesh, y, sgn)
            if pg is None or pg.area < 1.0:
                continue
            us.append(y_root - y)
            cx.append(pg.centroid.x)
            cz.append(pg.centroid.y)
        us, cx, cz = np.array(us), ndimage.gaussian_filter1d(np.array(cx), 2.0, mode="nearest"), \
            ndimage.gaussian_filter1d(np.array(cz), 2.0, mode="nearest")
        Cx, Cz = np.interp(uu, us, cx), np.interp(uu, us, cz)
        dCx, dCz = np.gradient(Cx, uu), np.gradient(Cz, uu)
        gx, gz = (f - 1.0) * dCx, (f - 1.0) * dCz
        Cnx = Cx + np.concatenate([[0.0], np.cumsum((gx[1:] + gx[:-1]) / 2.0 * np.diff(uu))])
        Cnz = Cz + np.concatenate([[0.0], np.cumsum((gz[1:] + gz[:-1]) / 2.0 * np.diff(uu))])
        u = y_root - V[sel, 1]
        sc = np.interp(u, uu, s)
        x_new = np.interp(u, uu, Cnx) + sc * (V[sel, 0] - np.interp(u, uu, Cx))
        z_new = np.interp(u, uu, Cnz) + sc * (V[sel, 2] - np.interp(u, uu, Cz))
        V[sel, 1] = y_root - np.interp(u, uu, U)
        V[sel, 0] = x_new
        V[sel, 2] = z_new
        info[sgn] = dict(tip_old=tip, u_tip=y_root - tip, Cx=Cx, Cz=Cz, Cnx=Cnx, Cnz=Cnz)
        k = np.argmin(np.abs(uu - (y_root - tip)))
        log.append("  handle side %+d: tip 1:1 Y %.2f (root->tip %.2f), centroid at root (%.1f, %.1f), at tip "
                   "(%.1f, %.1f) -> tip moved (%.1f, %.1f, %.1f)"
                   % (sgn, tip, y_root - tip, cx[0], cz[0], cx[-1], cz[-1], Cnx[k] - Cx[k], -(U[k] - uu[k]),
                      Cnz[k] - Cz[k]))
    m = trimesh.Trimesh(V, mesh.faces, process=False)
    if not m.is_watertight or not m.is_winding_consistent or m.volume <= 0:
        raise RuntimeError("handle warp broke the mesh")
    return m, info


# ================================================================ step 3b: lobe swell around the finger pits
def pit_required(fp, y, side, margin=LOBE_MARGIN):
    """Required material region (|x|, z) in the Y-section at y around one pit: the pit's x-range at y,
    ROOT_Z .. LIP_TOP_Z - WALL, buffered by the wall left after the Y offset (sphere-like)."""
    from shapely.geometry import LineString
    yb0, yb1 = fp.bounds[1], fp.bounds[3]
    yc_ = min(max(y, yb0 + 1e-3), yb1 - 1e-3)
    dy = abs(y - yc_)
    if dy >= WALL:
        return None
    seg = LineString([(-BIG, yc_), (BIG, yc_)]).intersection(fp)
    if seg.is_empty:
        return None
    a, b = sorted(side * np.array([seg.bounds[0], seg.bounds[2]]))
    # r9 (D5): the box reaches LIP_TOP_Z (r8 stopped at LIP_TOP_Z - WALL = 10.6; above it only the rounded buffer
    # was required and the upper pit walls fell to 2.67-2.97 over Z 13.0-13.5)
    return sbox(a, ROOT_Z, b, PIT_REQ_TOP_Z).buffer(np.sqrt(WALL ** 2 - dy ** 2) + margin, resolution=16)


def lobe_warp(mesh, pit_fps, fingers, log):
    """Swell the lobe radially (in its X-Z section, about (+-LOBE_CX, LOBE_CZ)) by a smooth field delta(y, theta)
    so that every pit keeps WALL of material to the outside. C1, monotone in r: no pad solid, no crease."""
    from shapely.geometry import LineString
    from scipy.interpolate import RegularGridInterpolator
    V = mesh.vertices.copy()
    th = np.radians(np.arange(-180.0, 180.01, LOBE_DTH))
    for sgn in (-1, 1):
        fps = [fp for fp, (p, n, fr) in zip(pit_fps, fingers) if np.sign(p[0]) == sgn]
        yf = [fp.centroid.y for fp in fps]
        ys = np.arange(min(yf) - LOBE_Y_PAD, max(yf) + LOBE_Y_PAD + 0.01, 1.0)
        Yg, Tg = np.meshgrid(ys, th, indexing="ij")
        dx_, dz_ = np.cos(Tg).ravel(), np.sin(Tg).ravel()
        O = np.column_stack([sgn * (LOBE_CX + 80.0 * dx_), Yg.ravel() + JIT[1], LOBE_CZ + 80.0 * dz_])
        D = np.column_stack([-sgn * dx_, np.zeros_like(dx_), -dz_])
        h = first_hits(mesh, O, D)
        r_o = np.array([np.nan if q is None else 80.0 - np.linalg.norm(q[0] - o) for q, o in zip(h, O)]).reshape(Yg.shape)
        need = np.full(Yg.shape, DELTA_OUT)
        for i, y in enumerate(ys):
            polys = [q for q in (pit_required(fp, y, sgn) for fp in fps) if q is not None]
            if not polys:
                continue
            R = unary_union(polys)
            for j, t in enumerate(th):
                if abs(t) > np.radians(85.0):
                    continue
                seg = LineString([(LOBE_CX, LOBE_CZ), (LOBE_CX + 80 * np.cos(t), LOBE_CZ + 80 * np.sin(t))]).intersection(R)
                if seg.is_empty:
                    continue
                cs = np.array([c for g_ in getattr(seg, "geoms", [seg]) for c in g_.coords])
                r_req = np.hypot(cs[:, 0] - LOBE_CX, cs[:, 1] - LOBE_CZ).max()
                ro = r_o[i, j] if np.isfinite(r_o[i, j]) else 0.0
                need[i, j] = max(need[i, j], r_req - ro)
        cell_th = LOBE_SIGMA / (20.0 * np.radians(LOBE_DTH))     # theta cells for LOBE_SIGMA mm at r ~ 20
        # one-shot scaled bump (r7): the iterated envelope widens with every pass and at sigma 10 still fell 3-4 mm
        # short after 40; a single gaussian of the dilated need, scaled to meet the need, keeps its width bounded
        rr_ = int(np.ceil(LOBE_DIL))
        yy_, xx_ = np.mgrid[-rr_:rr_ + 1, -rr_:rr_ + 1]
        nd = ndimage.grey_dilation(np.maximum(need, 0.0), footprint=(xx_ ** 2 + yy_ ** 2) <= LOBE_DIL ** 2)
        gb = ndimage.gaussian_filter(nd, (LOBE_SIGMA, cell_th), mode="nearest")
        pos = need > 0
        sc = max(1.0, float((need[pos] / np.maximum(gb[pos], 1e-6)).max())) if pos.any() else 1.0
        delta = sc * gb
        short = float((need - delta).max())
        dplus = 0.5 * (delta + np.sqrt(delta ** 2 + 0.3 ** 2))     # smooth max(delta, 0)
        f = RegularGridInterpolator((ys, th), dplus, bounds_error=False, fill_value=0.0)
        sel = sgn * V[:, 0] > LOBE_CX - 12.0
        rx, rz = sgn * V[sel, 0] - LOBE_CX, V[sel, 2] - LOBE_CZ
        r = np.hypot(rx, rz)
        t = np.arctan2(rz, rx)
        dd = f(np.column_stack([V[sel, 1], t])) * ramp((r - LOBE_R0) / LOBE_RAMP) \
            * (1.0 - ramp((np.abs(t) - np.radians(LOBE_TH_FADE0)) / np.radians(LOBE_TH_FADE)))
        k = r > 1e-9
        scale = np.ones_like(r)
        scale[k] = (r[k] + dd[k]) / r[k]
        V[sel, 0] = sgn * (LOBE_CX + rx * scale)
        V[sel, 2] = LOBE_CZ + rz * scale
        pk = np.unravel_index(np.argmax(need), need.shape)
        log.append("  lobe swell side %+d: need max %.2f at Y %.0f theta %.0f deg; bump scale x%.2f, delta max %.2f, "
                   "shortfall %.3f, delta at the Y domain ends %.3f; %d vertices moved > 0.05 mm"
                   % (sgn, need.max(), ys[pk[0]], np.degrees(th[pk[1]]), sc, dplus.max(), short,
                      max(dplus[0].max(), dplus[-1].max()), int((dd > 0.05).sum())))
    m = trimesh.Trimesh(V, mesh.faces, process=False)
    if not m.is_watertight or not m.is_winding_consistent or m.volume <= 0:
        raise RuntimeError("lobe warp broke the mesh")
    return m


def plan_warp(mesh, y_lo, y_hi, log):
    """Swell each end outward so its plan outline x_out(y) (max |x| of the Y-section) becomes convex between y_lo
    and y_hi: need(y) = upper convex hull of x_out - x_out, applied radially about (+-LOBE_CX, LOBE_CZ) with a
    cos^2 weight in the section angle (full at the equator, 0 at the top and bottom). User's r6 markup: the outer
    edge is one curve from the top corner into the handle; r6/r7-run-20 held x ~ 102-103 straight over Y 0-44."""
    V = mesh.vertices.copy()
    ys = np.arange(y_lo - PLAN_PAD, y_hi + 0.01, 1.0)
    for sgn in (-1, 1):
        xo = []
        for y in ys:
            s = mesh.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
            v = None if s is None else s.vertices[np.sign(s.vertices[:, 0]) == sgn]
            xo.append(np.nan if v is None or not len(v) else np.abs(v[:, 0]).max())
        xo = np.array(xo)
        k = np.isfinite(xo)
        hx, hy = [], []
        for p, q in zip(ys[k], xo[k]):                     # upper hull: pop while the turn is not clockwise
            while len(hx) >= 2 and (hx[-1] - hx[-2]) * (q - hy[-2]) - (hy[-1] - hy[-2]) * (p - hx[-2]) >= 0:
                hx.pop()
                hy.pop()
            hx.append(p)
            hy.append(q)
        need = np.where(k, np.interp(ys, hx, hy) - xo, 0.0) * ramp((ys - (y_lo - PLAN_PAD)) / PLAN_PAD) \
            * (1.0 - ramp((ys - (y_hi - PLAN_PAD)) / PLAN_PAD))
        need = ndimage.gaussian_filter1d(np.maximum(need, 0.0), PLAN_SIGMA, mode="nearest")
        sel = sgn * V[:, 0] > LOBE_CX - 12.0
        rx, rz = sgn * V[sel, 0] - LOBE_CX, V[sel, 2] - LOBE_CZ
        r = np.hypot(rx, rz)
        t = np.arctan2(rz, rx)
        dd = np.interp(V[sel, 1], ys, need, left=0.0, right=0.0) * np.cos(np.clip(t, -np.pi / 2, np.pi / 2)) ** 2 \
            * ramp((r - LOBE_R0) / LOBE_RAMP)
        scale = np.ones_like(r)
        kk = r > 1e-9
        scale[kk] = (r[kk] + dd[kk]) / r[kk]
        V[sel, 0] = sgn * (LOBE_CX + rx * scale)
        V[sel, 2] = LOBE_CZ + rz * scale
        i = int(np.argmax(need))
        log.append("  plan warp side %+d: hull shortfall max %.2f at Y %.0f (Y %.0f..%.0f), %d vertices moved > 0.05 mm"
                   % (sgn, need[i], ys[i], y_lo, y_hi, int((dd > 0.05).sum())))
    m = trimesh.Trimesh(V, mesh.faces, process=False)
    if not m.is_watertight or not m.is_winding_consistent or m.volume <= 0:
        raise RuntimeError("plan warp broke the mesh")
    return m


# ================================================================ r9 helpers
def smooth_handles(mesh, y_root, log):
    """G7 (D18): Taubin-smooth the free handles (weight 0 at root - HSM_ROOT and at tip + HSM_TIP, full HSM_RAMP
    further in) so the scan's shell seam is not carried onto the case. Topology unchanged."""
    m2 = mesh.copy()
    trimesh.smoothing.filter_taubin(m2, lamb=0.5, nu=-0.53, iterations=HSM_ITERS)
    V0, V1 = mesh.vertices, m2.vertices
    w = np.zeros(len(V0))
    for sgn in (-1, 1):
        sel = (np.sign(V0[:, 0]) == sgn) & (np.abs(V0[:, 0]) > 50.0)
        tip = V0[sel, 1].min()
        y = V0[sel, 1]
        w[sel] = ramp((y_root - HSM_ROOT - y) / HSM_RAMP) * ramp((y - tip - HSM_TIP) / HSM_RAMP)
    V = V0 + w[:, None] * (V1 - V0)
    mv = np.linalg.norm(V - V0, axis=1)
    m = trimesh.Trimesh(V, mesh.faces, process=False)
    if not m.is_watertight or not m.is_winding_consistent or m.volume <= 0:
        raise RuntimeError("handle smoothing broke the mesh")
    log.append("STEP 2b handle smoothing (Taubin x%d): %d vertices weighted, moved max %.3f p99 %.3f mm, vol %+.1f mm3"
               % (HSM_ITERS, int((w > 0).sum()), mv.max(), np.percentile(mv[w > 0], 99), m.volume - mesh.volume))
    return m


def side_xout(mesh, ys, sgn):
    xo = []
    for y in ys:
        s = mesh.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
        v = None if s is None else s.vertices[np.sign(s.vertices[:, 0]) == sgn]
        xo.append(np.nan if v is None or not len(v) else np.abs(v[:, 0]).max())
    return np.array(xo)


def corner_clip_outline(lw, oval, P, N, Y1):
    """Top-corner clip outline K (round 7; factored out in r9): oval offset G(y) from D0 (the lobe's outer reach at
    Y1..Y1+8, + margin) shrinking to WALL at the top edge, plus everything below Y1."""
    oy = bc.outer_x(lw, np.arange(Y1, Y1 + 8.01, 0.5), np.linspace(-20.0, LIP_TOP_Z, 24))
    D0 = 0.0
    for i, sx in enumerate((-1, 1)):
        xo = oy[i].max(axis=1)
        for yv, xv in zip(np.arange(Y1, Y1 + 8.01, 0.5), xo):
            if np.isfinite(xv) and xv > 0:
                D0 = max(D0, oval.exterior.distance(Point(sx * xv, yv)))
    D0 += D0_MARGIN
    up = P[:, 1] >= YC
    tt = np.clip((P[up, 1] - Y1) / (POCKET_Y_TOP - Y1), 0.0, 1.0)
    G = WALL + (D0 - WALL) * (1.0 + np.cos(np.pi * tt)) / 2.0
    curve = P[up] + N[up] * G[:, None]
    K = Polygon(curve).buffer(0).union(sbox(-BIG, -BIG, BIG, Y1))
    return D0, curve, K


def pt_weight(t):
    """r10 (D8): plan-trim weight in the lobe section angle t (rad): centred on the lower flank, ~0 at the pit tops."""
    return np.exp(-((np.degrees(t) - PT_T0) / PT_TW) ** 2)


def plan_trim(mesh, pit_fps, fingers, K, log):
    """D8 option B (user): remove width so the plan outline over the user's span follows a bowed arc (bow PT_BOW off
    the chord, peak PT_PEAK down from the top corner). Removal only, radial about (+-LOBE_CX, LOBE_CZ) with the
    plan warp's cos^2 weight; capped so every pit keeps WALL + PT_MARGIN (radial, Y-sections). If the requested arc
    needs more removal than the walls allow, the bow is raised to the smallest feasible value (reported)."""
    from shapely.geometry import LineString
    V = mesh.vertices.copy()
    ys = np.arange(PT_Y_LO, PT_Y_HI + 0.01, 1.0)
    th = np.radians(np.arange(-84.0, 84.01, LOBE_DTH))
    s_ = (PT_Y_HI - ys) / (PT_Y_HI - PT_Y_LO)
    b_ = (1.0 - PT_PEAK) / PT_PEAK
    f = s_ * (1.0 - s_) ** b_ / (PT_PEAK * (1.0 - PT_PEAK) ** b_)
    a0, a1, b0, b1 = PT_WIN
    win = ramp((ys - a0) / (a1 - a0)) * (1.0 - ramp((ys - b0) / (b1 - b0)))
    info = {}
    for sgn in (-1, 1):
        xo = side_xout(mesh, ys, sgn)
        from shapely.geometry import LineString as _LS
        kx = _LS([(0.0, PT_Y_HI), (sgn * BIG, PT_Y_HI)]).intersection(K.boundary)
        kx = np.array([abs(c[0]) for g_ in getattr(kx, "geoms", [kx]) for c in g_.coords])
        x_top = min(xo[-1], kx.max()) if len(kx) else xo[-1]     # the clip trims the corner later
        chord = xo[0] + (x_top - xo[0]) * (ys - ys[0]) / (ys[-1] - ys[0])
        dev = xo - chord
        # wall allowance per (y, theta): ray radius minus the required radius (margin 0) minus PT_MARGIN
        fps = [fp for fp, (p, n, fr) in zip(pit_fps, fingers) if np.sign(p[0]) == sgn]
        Yg, Tg = np.meshgrid(ys, th, indexing="ij")
        dx_, dz_ = np.cos(Tg).ravel(), np.sin(Tg).ravel()
        O = np.column_stack([sgn * (LOBE_CX + 80.0 * dx_), Yg.ravel() + JIT[1], LOBE_CZ + 80.0 * dz_])
        h = first_hits(mesh, O, np.column_stack([-sgn * dx_, np.zeros_like(dx_), -dz_]))
        r_o = np.array([np.nan if q is None else 80.0 - np.linalg.norm(q[0] - o) for q, o in zip(h, O)]).reshape(Yg.shape)
        rmax = np.full(len(ys), np.inf)
        for i, y in enumerate(ys):
            polys = [q for q in (pit_required(fp, y, sgn, margin=0.0) for fp in fps) if q is not None]
            if not polys:
                continue
            R = unary_union(polys)
            for j, t in enumerate(th):
                seg = LineString([(LOBE_CX, LOBE_CZ), (LOBE_CX + 80 * np.cos(t), LOBE_CZ + 80 * np.sin(t))]).intersection(R)
                if seg.is_empty or not np.isfinite(r_o[i, j]):
                    continue
                cs = np.array([c for g_ in getattr(seg, "geoms", [seg]) for c in g_.coords])
                allow = r_o[i, j] - np.hypot(cs[:, 0] - LOBE_CX, cs[:, 1] - LOBE_CZ).max() - PT_MARGIN
                rmax[i] = min(rmax[i], max(allow, 0.0) / max(pt_weight(t), 1e-3))

        def rem_of(B):
            r = np.maximum(dev - B * f, 0.0) * win
            return ndimage.gaussian_filter1d(r, PT_SIGMA, mode="nearest")

        Breq = PT_BOW[sgn]
        B = Breq
        if (rem_of(B) > rmax).any():
            lo, hi = Breq, Breq + 25.0
            for _ in range(40):
                mid = 0.5 * (lo + hi)
                lo, hi = (mid, hi) if (rem_of(mid) > rmax).any() else (lo, mid)
            B = hi
        rem = rem_of(B)
        sel = sgn * V[:, 0] > LOBE_CX - 12.0
        rx, rz = sgn * V[sel, 0] - LOBE_CX, V[sel, 2] - LOBE_CZ
        r = np.hypot(rx, rz)
        t = np.arctan2(rz, rx)
        dd = np.interp(V[sel, 1], ys, rem, left=0.0, right=0.0) * pt_weight(t) * ramp((r - LOBE_R0) / LOBE_RAMP)
        # r10 (D34, measured): the move is horizontal only. Radial (r9), it also moved Z: on the step-4 body that
        # lifted the trigger-zone clear plane (Z = FLOOR_Z) off its plane beside the upper pits' ends, and the later
        # cuts at FLOOR_Z (pocket, top-edge / bottom openings) left a hairline sliver there: one extra handle per
        # side in x +-85..89.4, y 56.8..62.5 at Z -8.80 (an extra 3rd material piece in the Z -8.80 section only)
        V[sel, 0] = V[sel, 0] - sgn * dd
        ib = int(np.nanargmax(dev))
        bind = np.flatnonzero(np.isfinite(rmax) & (rem > rmax - 0.02))
        log.append("  plan trim side %+d: outline bow off its chord (Y %.0f..%.0f) %.2f at Y %.0f (%.0f %% down); "
                   "bow requested %.2f -> used %.2f; removal max %.2f at Y %.0f; wall-bound at Y %s"
                   % (sgn, ys[0], ys[-1], dev[ib], ys[ib], 100 * s_[ib], Breq, B, rem.max(), ys[int(np.argmax(rem))],
                      "-" if not len(bind) else "%.0f..%.0f" % (ys[bind].min(), ys[bind].max())))
        info[sgn] = dict(B=B, Breq=Breq, rem=rem, rmax=rmax, xo=xo)
    m = trimesh.Trimesh(V, mesh.faces, process=False)
    if not m.is_watertight or not m.is_winding_consistent or m.volume <= 0:
        raise RuntimeError("plan trim broke the mesh")
    return m, info


def mask_outline(mask, xs, ys, sigma):
    """G1: smooth outline of a cell mask: 0.5 contour of its gaussian (no 1 mm box staircase)."""
    import contourpy
    S = ndimage.gaussian_filter(mask.astype(float), sigma, mode="constant")
    cg = contourpy.contour_generator(x=xs, y=ys, z=S.T)
    polys = [Polygon(l) for l in cg.lines(0.5) if len(l) >= 4]
    out = Polygon()
    for p in polys:
        out = out.symmetric_difference(p.buffer(0))
    return out.buffer(0)


def b_polygon(S, nSd):
    """Top-edge opening plan (r5-r11 prism B): chord S_L - S_R plus both wall-end normal rays, everything above them,
    with the wall ends rounded END_R in plan."""
    FR = S[1] + nSd[1] * 600.0
    FL = S[-1] + nSd[-1] * 600.0
    Htop = Polygon([tuple(FL), tuple(S[-1]), tuple(S[1]), tuple(FR), (FR[0], 900.0), (FL[0], 900.0)])
    rounders = []
    for sx in (-1, 1):
        n_ = nSd[sx]
        v = np.array([n_[1], -n_[0]]) if sx > 0 else np.array([-n_[1], n_[0]])
        if v[1] > 0:
            v = -v
        s0 = S[sx]
        sq = Polygon([tuple(s0), tuple(s0 + END_R * n_), tuple(s0 + END_R * (n_ + v)), tuple(s0 + END_R * v)])
        rounders.append(sq.difference(Point(*(s0 + END_R * (n_ + v))).buffer(END_R, resolution=32)))
    return unary_union([Htop] + rounders)


def top_cut(body, oval, S, nSd, K, Y1, pit_fps, log):
    """r12: the whole top as one height field Hc on a uniform TOP_STEP grid; everything above Hc is removed.
    h0 = min(skin, TOP_Z, B floor, K wall) is the target before rounding: the skin itself, the flat plane, the
    top-edge opening (FLOOR_Z beyond the wall-end lines, with a concave base fillet FILL_RF next to the line, below
    the button band) and the corner clip, the last two as 1:TOP_WALL_K walls so they are smooth on the grid.
    ho = the ball opening of h0, radius rmap per node (TOP_R_MAX, less where a finger pit is closer than
    WALL + TOP_PIT_M + r to the edge). Where the opening takes off less than TOP_TAU the cut lifts into the air,
    so the untouched skin is never shaved."""
    from scipy.interpolate import RegularGridInterpolator as RGI
    t0 = time.time()
    st, Z0 = TOP_STEP, TOP_Z
    bb = body.bounds
    xs3 = np.arange(np.floor(bb[0][0]) - 4.0, np.ceil(bb[1][0]) + 4.0 + 1e-9, st)
    ys3 = np.arange(np.floor(bb[0][1]) - 4.0, np.ceil(bb[1][1]) + 4.0 + 1e-9, st)
    X3, Y3 = np.meshgrid(xs3, ys3, indexing="ij")
    P3 = np.column_stack([X3.ravel(), Y3.ravel()])
    pts = shapely.points(P3[:, 0], P3[:, 1])
    k4 = int(round(1.0 / st))
    xs1, ys1 = xs3[::k4], ys3[::k4]
    Sk1 = z_from(body, *np.meshgrid(xs1, ys1, indexing="ij"), below=False)
    fin = np.isfinite(Sk1)
    S1 = np.where(fin, Sk1, -100.0)
    Ski = RGI((xs1, ys1), S1, bounds_error=False, fill_value=-100.0)(P3).reshape(X3.shape)
    nanw = RGI((xs1, ys1), (~fin).astype(float), bounds_error=False, fill_value=1.0)(P3).reshape(X3.shape) > 0
    Smx = RGI((xs1, ys1), ndimage.maximum_filter(S1, size=3), method="nearest", bounds_error=False,
              fill_value=-100.0)(P3).reshape(X3.shape)
    Bp = b_polygon(S, nSd)
    inB = shapely.contains_xy(Bp, P3[:, 0], P3[:, 1]).reshape(X3.shape)
    tB = shapely.distance(Bp.boundary, pts).reshape(X3.shape) * np.where(inB, 1.0, -1.0)   # > 0: in the opening
    Kp = sbox(-BIG, Y1 - 1.0, BIG, BIG).difference(K)
    inKc = shapely.contains_xy(Kp, P3[:, 0], P3[:, 1]).reshape(X3.shape)
    sdK = shapely.distance(Kp.boundary, pts).reshape(X3.shape) * np.where(inKc, 1.0, -1.0)   # > 0: clipped away
    lo, hi = Z0 + TOP_RAY_BAND[0], Z0 + TOP_RAY_BAND[1]
    need = ((Ski >= lo) & (Ski <= hi)) | (nanw & (Smx >= lo)) | ((tB > -3.0) & (tB < 25.0) & (Smx > FLOOR_Z - 12.0)) \
        | ((np.abs(sdK) < 4.0) & (Smx >= lo))
    Sk3 = np.where(Ski > -50.0, Ski, np.nan)
    Sk3[nanw & ~need] = np.nan
    Sk3[need] = z_from(body, X3[need], Y3[need], below=False)
    have = np.isfinite(Sk3)
    ie = ndimage.distance_transform_edt(~have, return_distances=False, return_indices=True)
    Ske = np.where(have, Sk3, np.minimum(Sk3[tuple(ie)], Z0 - TOP_R_MAX - 0.5))
    # the B floor: FLOOR_Z, with a concave quarter-round of FILL_RF at the foot of the line (tangent to the floor)
    tp = np.clip(tB, 0.0, None)
    F = np.where(tp < FILL_RF, FLOOR_Z + FILL_RF - np.sqrt(np.maximum(FILL_RF ** 2 - (FILL_RF - tp) ** 2, 0.0)), FLOOR_Z)
    # D39 (fill, not cut): where the lobe underside beyond the line rises toward the floor, the floor-plane cut left
    # films 0.00-0.15 mm thick. There the cut floor follows the underside FILM_T above it (a rim of the lobe's own
    # material), up to FILL_ZCAP (below the button band); past that the column goes, with a blunt FILM_T end
    zcap = BTN_Z_LO - BTN_MARGIN - 0.3
    fz = (tB > 0.0) & (tB < 20.0) & (np.abs(X3) > 83.0)
    zub = np.full(X3.shape, np.nan)
    zub[fz] = z_from(body, X3[fz], Y3[fz], below=True)
    zc = zcap - FILM_T
    Ff = np.where(np.isfinite(zub), zub + FILM_T - (FILM_T + 1.0) * ramp((zub - zc) / 0.5), -1e3)
    Ff = np.where(fz, FLOOR_Z + (Ff - FLOOR_Z) * ramp((np.abs(X3) - 85.0) / 2.0), -1e3)
    F = np.maximum(F, Ff)
    # The B wall crosses the line at the button band bottom and leans <= 0.32 mm into the kept side above it, so no
    # material enters the finger envelope (Z >= BTN_Z_LO). Run b leaned it out instead (on the line at the top): the
    # 23 mm reach fell L 91 -> 88 %, R 87 -> 86 %. Run a's lean-in took the upper pit wall to 2.84 at (88.0, 57.3)
    # (G11); the pit guard in the cut below now holds WALL + TOP_PIT_GUARD there instead
    toffB = (Z0 + 0.5 - BTN_Z_LO) / TOP_WALL_K
    hB = np.maximum(F, Z0 + 0.5 - TOP_WALL_K * (tB + toffB))
    hK = np.maximum(Z0 + 0.5 - TOP_WALL_K * (sdK + 0.1), -60.0)
    inOv = shapely.contains_xy(oval, P3[:, 0], P3[:, 1]).reshape(X3.shape)
    h0 = np.minimum(np.minimum(Ske, Z0), np.minimum(hB, hK))
    h0 = np.where(inOv, np.minimum(Z0, hB), h0)
    # radius per node: from the pit distance of the nearest edge node of the flat region
    flat = h0 >= Z0 - 1e-6
    bnd = flat & ~ndimage.binary_erosion(flat)
    dpit = shapely.distance(unary_union(pit_fps), pts).reshape(X3.shape)
    rb = np.clip(dpit - WALL - TOP_PIT_M, 0.0, TOP_R_MAX)
    ib = ndimage.distance_transform_edt(~bnd, return_distances=False, return_indices=True)
    rmap = rb[tuple(ib)]
    rmap = np.minimum(rmap, ndimage.gaussian_filter(ndimage.minimum_filter(rmap, size=int(2.0 / st) + 1), 0.5 / st))
    rmap = np.minimum(rmap, rb[tuple(ib)])
    R_ = np.array(TOP_RADII)
    O_ = np.stack([ball_open(h0, r, st) for r in R_])
    j = np.clip(np.searchsorted(R_, rmap, side="right") - 1, 0, len(R_) - 2)
    f = np.clip((rmap - R_[j]) / (R_[j + 1] - R_[j]), 0.0, 1.0)
    I_, J_ = np.indices(h0.shape)
    ho = O_[j, I_, J_] * (1.0 - f) + O_[j + 1, I_, J_] * f
    over = float((ho - h0).max())
    Skm = np.where(np.isfinite(Sk3), Sk3, -1e3)
    dev = Skm - ho
    w_air = 1.0 - ramp(dev / TOP_TAU)
    Hc = ho + w_air * (np.maximum(Skm, ho) + 1.0 - ho)
    Hc = np.minimum(Hc, np.maximum(ho, Z0))
    # r13 (D39), tried twice and NOT kept (audit/r13/fix_report_r13.md): Hc = max(Hc, Ff) beyond the line, so the ball
    # opening cannot shave the FILM_T rim. Run a (every column with Ff): the top-cut difference left 11 sliver shells
    # 0.00-0.12 mm3 (Z -3.8..4.5). Run b (only where Ff > underside + 0.05): built, but the mask switches per 0.25 mm
    # node, so the cut jumps between the rim (~-4) and the opening floor (~-8.4): a row of saw-teeth along the foot of
    # the wall end (render r13 corner). A rim needs a smooth weight, not a mask; D39 left open
    # pit guard: nothing below the plane within WALL + TOP_PIT_GUARD of a finger pit (a smooth 1:40 field, no step)
    Hc = np.maximum(Hc, np.minimum(Z0, Z0 + 0.5 - TOP_WALL_K * (dpit - (WALL + TOP_PIT_GUARD))))
    ztop = float(np.nanmax(Sk3)) + 5.0
    v_ = body.volume
    body = boolean("difference", body, hf_solid(xs3, ys3, Hc, np.full(Hc.shape, ztop)), "top cut (r12)")
    rr = rmap[bnd]
    log.append("TOP CUT (r12): grid %d x %d at %.2f, skin rays 1 mm %d + exact %d | plane Z %.2f | opening above h0 by "
               "max %.2e | removed %.1f cm3 | %.1f s" % (len(xs3), len(ys3), st, Sk1.size, int(need.sum()), Z0, over,
                                                       (v_ - body.volume) / 1e3, time.time() - t0))
    log.append("  rolled-edge radius on the %d edge nodes of the flat region: min %.2f p05 %.2f p50 %.2f; < %.1f on %d "
               "nodes (%.1f %%)" % (bnd.sum(), rr.min(), np.percentile(rr, 5), np.median(rr), TOP_R_MAX,
                                    int((rr < TOP_R_MAX - 1e-6).sum()), 100.0 * (rr < TOP_R_MAX - 1e-6).mean()))
    sel = bnd & (rmap < TOP_R_MAX - 1e-6)
    if sel.any():
        lab, nl = ndimage.label(ndimage.binary_dilation(sel, iterations=4) & bnd)
        for q in range(1, nl + 1):
            mm = (lab == q) & sel
            if mm.sum() < 2:
                continue
            log.append("    r < %.1f: %d nodes, min r %.2f, x %.1f..%.1f y %.1f..%.1f"
                       % (TOP_R_MAX, mm.sum(), rmap[mm].min(), X3[mm].min(), X3[mm].max(), Y3[mm].min(), Y3[mm].max()))
    info = dict(xs3=xs3, ys3=ys3, Sk3=Sk3.astype(np.float32), h0=h0.astype(np.float32), ho=ho.astype(np.float32),
                Hc=Hc.astype(np.float32), rmap=rmap.astype(np.float32), bnd=bnd, tB=tB.astype(np.float32),
                sdK=sdK.astype(np.float32))
    return body, info



# ================================================================ fingers (round 4 shapes, round 5 levels)
def pit_solid(frame):
    hw = FINGER_W / 2.0 + FINGER_SLOT
    a0, a1, R = -FINGER_INNER_SLOT, FINGER_T_ROOT + FINGER_GAP, PIT_CORNER_R
    prof = sbox(a0, -hw, a1 - R, hw).union(sbox(a0, -hw + R, a1, hw - R))
    prof = prof.union(Point(a1 - R, hw - R).buffer(R, resolution=16)).union(
        Point(a1 - R, -hw + R).buffer(R, resolution=16))
    m = trimesh.creation.extrude_polygon(prof, LIP_TOP_Z + 10.0 - ROOT_Z)
    m.apply_translation([0, 0, ROOT_Z])
    m.apply_transform(np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], float))
    m.apply_transform(frame)
    return m, prof


def pit_plan(pm):
    return Polygon(np.asarray(pm.vertices[pm.vertices[:, 2] < ROOT_Z + 0.01][:, :2])).convex_hull


def finger_solid(frame):
    L = LIP_U - ROOT_Z
    slope = (FINGER_T_ROOT - FINGER_T_TIP) / L

    def beam_u(z):
        return FINGER_T_ROOT - slope * (z - ROOT_Z)

    t_below = beam_u(ROOT_Z - 1.0)
    z_tip = LIP_U + (LIP_OVERHANG - LIP_FLAT) / np.tan(np.radians(LIP_RET_DEG))
    t_top = -LIP_OVERHANG + (LIP_TOP_Z - z_tip) * np.tan(np.radians(LIP_LEAD_DEG))
    u_head = max(FINGER_T_TIP, t_top + LIP_LAND)
    z_ch = (LIP_U - u_head + FINGER_T_ROOT + slope * ROOT_Z) / (1.0 + slope)
    pp = [(0.0, ROOT_Z - 1.0), (t_below, ROOT_Z - 1.0), (beam_u(z_ch), z_ch),
          (u_head, LIP_U), (u_head, LIP_TOP_Z), (t_top, LIP_TOP_Z),
          (-LIP_OVERHANG, z_tip), (-LIP_FLAT, LIP_U), (0.0, LIP_U)]
    # r11: at LIP_T 1.2 u_head = FINGER_T_TIP, so the chamfer point equals (u_head, LIP_U): drop coincident points
    # (the duplicate made the extruded finger a non-volume)
    pp = [q for i, q in enumerate(pp) if i == 0 or np.hypot(q[0] - pp[i - 1][0], q[1] - pp[i - 1][1]) > 1e-6]
    prof = Polygon(pp)
    strip = sbox(-FINGER_INNER_SLOT + 0.05, ROOT_Z - 1.0, FINGER_T_ROOT + FINGER_GAP - 0.05, ROOT_Z)
    low = unary_union([prof, strip]).intersection(sbox(-5.0, ROOT_Z - 1.0, 10.0, ROOT_Z + 3.0))
    low = low.buffer(FINGER_ROOT_R, resolution=16).buffer(-FINGER_ROOT_R, resolution=16)
    prof = unary_union([prof, low])
    if prof.geom_type != "Polygon":
        raise RuntimeError("finger profile is not one polygon")
    m = trimesh.creation.extrude_polygon(prof, FINGER_W)
    m.apply_translation([0, 0, -FINGER_W / 2.0])
    m.apply_transform(frame)
    return m, dict(z_tip=z_tip, t_top=t_top, u_head=u_head, land=u_head - t_top, z_ch=z_ch)


def arc_station(poly, side, y_target):
    ext = poly.exterior
    best = None
    for sd in np.arange(0.0, ext.length, 0.1):
        p = ext.interpolate(sd).coords[0]
        if side * p[0] <= CAP_XC:
            continue
        if best is None or abs(p[1] - y_target) < abs(best[1] - y_target):
            best = (sd, p[1])
    return bc.outline_frame(poly, best[0], FINGER_W / 2.0)


# ================================================================ build
def build():
    log = []
    t0 = time.time()
    scan = bc.load_scan()
    ex = extend_axis(scan, 0, 0.0, -DX, DX)
    ext = stretch_axis(ex, 1, Y_STR0, Y_STR1, DY, Y_STR_R)
    log.append("scan 1:1 bounds %s, watertight %s, vol %.1f cm3, euler %d"
               % (np.round(scan.bounds, 2).tolist(), scan.is_watertight, scan.volume / 1e3, scan.euler_number))
    log.append("STEP 1 X extend: loop %d verts, +%.1f cm3 | Y stretch (1:1 Y %.1f..%.1f -> +%.0f, peak density "
               "x%.3f): +%.1f cm3 | watertight %s winding %s euler %d | bounds %s"
               % (ex.metadata["ext_info"]["loop_verts"], (ex.volume - scan.volume) / 1e3, Y_STR0, Y_STR1, DY,
                  ext.metadata["stretch_info"]["peak"], (ext.volume - ex.volume) / 1e3,
                  ext.is_watertight, ext.is_winding_consistent, ext.euler_number, np.round(ext.bounds, 2).tolist()))

    # --- step 2: handles
    sec0 = ext.section(plane_origin=[0, 0, 0], plane_normal=[1, 0, 0])
    crotch = float(sec0.vertices[:, 1].min())
    y_root = crotch - ROOT_BELOW_CROTCH
    sr = ext.section(plane_origin=[0, y_root, 0], plane_normal=[0, 1, 0])
    nl = len(sr.discrete)
    if nl != 2:
        raise RuntimeError("section at the handle root Y %.2f has %d loops (expected the 2 handles)" % (y_root, nl))
    hw, hinfo = handle_warp(ext, y_root, log)
    if HSM_ITERS > 0:
        hw = smooth_handles(hw, y_root, log)
    log.append("STEP 2 handles: crotch Y %.2f -> root Y %.2f (2 loops) | stretch peak x%.3f over u %.0f..%.0f..%.0f, "
               "+%.1f mm | girth x%.2f (ramp %.0f mm) | vol %.1f -> %.1f cm3"
               % (crotch, y_root, hinfo["k"], STRETCH_R1, STRETCH_U2, STRETCH_U3, HANDLE_EXTRA, HANDLE_GIRTH,
                  GIRTH_BLEND, ext.volume / 1e3, hw.volume / 1e3))

    P, N = oval_loop()
    oval = Polygon(P)
    R0 = oval.buffer(WALL, resolution=64)
    log.append("oval pocket %.2f x %.2f, Y %.3f..%.3f | Z lip top %.2f lip underside %.2f face %.2f floor %.2f "
               "back <= %.2f finger root %.2f"
               % (oval.bounds[2] - oval.bounds[0], oval.bounds[3] - oval.bounds[1], oval.bounds[1],
                  oval.bounds[3], LIP_TOP_Z, LIP_U, FACE_Z, FLOOR_Z, BACK_Z, ROOT_Z))

    ys_ = YC + CAP_B * np.sqrt(1.0 - ((X_LR_END - CAP_XC) / CAP_A) ** 2)
    g = np.array([(X_LR_END - CAP_XC) / CAP_A ** 2, (ys_ - YC) / CAP_B ** 2])
    nS = g / np.linalg.norm(g)
    S = {1: np.array([X_LR_END, ys_]), -1: np.array([-X_LR_END, ys_])}
    nSd = {1: nS, -1: np.array([-nS[0], nS[1]])}
    Y1 = ys_
    log.append("wall end S at (+-%.2f, %.2f), outline normal (+-%.3f, %.3f)" % (X_LR_END, ys_, nS[0], nS[1]))

    # fingers (positions only depend on the oval)
    fingers = []
    y_up = None
    for yt in np.arange(Y1, YC, -0.25):
        p, n = arc_station(oval, 1, yt)
        cs = bc.finger_footprint(p, n)
        if max(c[1] for c in cs) <= Y1 - FINGER_END_CLEAR:
            y_up = yt
            break
    y_lo = 2 * YC - y_up
    for sx in (-1, 1):
        for yt in (y_up, y_lo):
            p, n = arc_station(oval, sx, yt)
            fr = bc.local_frame(p, n)
            fingers.append((p, n, fr))
            log.append("finger side %+d at (%.2f, %.2f) normal (%.3f, %.3f) = %.1f deg from X"
                       % (sx, p[0], p[1], n[0], n[1], np.degrees(np.arctan2(abs(n[1]), abs(n[0])))))
    pit_fps = [pit_plan(pit_solid(fr)[0]) for p, n, fr in fingers]

    # --- step 3b: lobe swell so every pit keeps WALL to the outside -- broad (r7), one fuller end, not bumps
    lw = lobe_warp(hw, pit_fps, fingers, log)
    log.append("STEP 3b lobe swell: vol %.1f -> %.1f cm3 (+%.1f mm3)" % (hw.volume / 1e3, lw.volume / 1e3,
                                                                       lw.volume - hw.volume))
    # --- step 3c (r7): plan outline convex from the handle root to past the corner clip's start
    v_ = lw.volume
    lw = plan_warp(lw, y_root, Y1 + 8.0, log)
    log.append("STEP 3c plan warp: +%.1f mm3" % (lw.volume - v_))
    # --- step 3d (r9, D8 option B) moved after step 4 in r10: the step-4 fill widened the lobe after r9's trim

    # --- top-corner clip outline (applied after the front cut), measured here on the swollen lobe so that step 4
    #     can roll the back over into it. The slab stays inside the plan and the front cut acts above the lip
    #     only, so neither moves the lobe's outer x at Z -20..LIP_TOP_Z that D0 is measured on.
    D0, curve, K = corner_clip_outline(lw, oval, P, N, Y1)

    # --- step 4+5 (r7): back = one convex arc per column (no triggers), never above the required back
    body = lw
    xs = np.arange(-125.0, 125.0 + 1e-6, BACK_GRID)
    ysg = np.arange(-95.0, 100.0 + 1e-6, BACK_GRID)
    X, Y = np.meshgrid(xs, ysg, indexing="ij")
    zu = z_from(body, X, Y)
    zt = z_from(body, X, Y, below=False)
    valid = np.isfinite(zu)
    idx = ndimage.distance_transform_edt(~valid, return_distances=False, return_indices=True)
    zu_f, zt_f = zu[tuple(idx)], zt[tuple(idx)]
    pts = shapely.points(X.ravel(), Y.ravel())
    inQ = shapely.contains_xy(R0, X.ravel(), Y.ravel()).reshape(X.shape)
    cells = shapely.box(X[valid] - 0.5, Y[valid] - 0.5, X[valid] + 0.5, Y[valid] + 0.5)
    splan = shapely.union_all(cells).buffer(-OMEGA_ERODE)
    omega = unary_union([R0, splan])
    omega = max(getattr(omega, "geoms", [omega]), key=lambda q: q.area)
    inO = shapely.contains_xy(omega, X.ravel(), Y.ravel()).reshape(X.shape)
    req = np.full(X.shape, np.inf)
    req[inQ] = BACK_Z - BACK_MARGIN
    for fp in pit_fps:
        inP = shapely.contains_xy(fp.buffer(1.0), X.ravel(), Y.ravel()).reshape(X.shape)
        req[inP] = np.minimum(req[inP], ROOT_Z - PAD_MIN - BACK_MARGIN)
    T = convex_back(zu, valid, req, ysg, Y_MONO)
    # the end rolls over into the corner clip (user's r6 markup: the crest curves down over the corner) instead
    # of meeting it as a flat vertical face: quarter-round in (distance to the clip, Z) up to the required back
    dC = shapely.distance(shapely.LineString(curve[curve[:, 1] >= Y1]), pts).reshape(X.shape)
    inK = shapely.contains_xy(K, X.ravel(), Y.ravel()).reshape(X.shape) & (Y >= Y1 - END_ROLL_R)
    ZR = BACK_Z - BACK_MARGIN
    q = np.clip(1.0 - dC / END_ROLL_R, 0.0, 1.0)
    zr = ZR - (ZR - T) * np.sqrt(1.0 - q ** 2)
    roll = inK & (dC < END_ROLL_R) & (T < ZR)
    w = ramp((np.abs(X) - X_MONO) / X_MONO_RAMP)
    T = np.where(roll, np.maximum(T, T + w * (zr - T)), T)
    net = np.where(valid, T - zu, 0.0)                     # > 0: material removed, < 0: material added
    # One smooth new underside U = zu + D drives the fill and the trigger-zone refill. r7 runs 5-8 treated fill,
    # removal and the pocket ring with separate per-cell formulas and every boundary between them became a step
    # on the part (terraces at |x| 55-70). The fill fades out before the plan edge (the staircase edge of the
    # slab domain, spikes along the lobe flank in run 5).
    dP = shapely.distance(splan.boundary, pts).reshape(X.shape) * np.where(
        shapely.contains_xy(splan, X.ravel(), Y.ravel()).reshape(X.shape), 1.0, -1.0)
    # ... and fades out where the scan underside is steep: a 1 mm height field cannot follow a flank, so fill or
    # cut there zig-zags (run 11: a sawtooth along the lobe's inner flank)
    ke = ramp((dP - FILL_EDGE0) / FILL_EDGE)
    gy, gx_ = np.gradient(zu_f, BACK_GRID)
    ws = ndimage.gaussian_filter(1.0 - ramp((np.hypot(gx_, gy) - SLOPE0) / SLOPE_W), 1.5, mode="nearest")
    # removal too, on the ends: between the pocket centre and the trigger zone the scan underside already drops
    # into the trigger (x 70: -17.8 at Y 36 -> -20.2 at Y 52) while the target stays level; fill-only (r7) followed
    # the scan down and the zone lifted it back over Y 52-60 -> crease + basin at Y 53 (form-auditor, r7)
    wx = ramp((np.abs(X) - X_MONO) / X_MONO_RAMP)
    # r9: no removal within WALL + 1 of a finger pit (full from WALL + 4): with the r9 edge fade the removal reached
    # the lobe flank beside the R upper pit and left 1.07-2.06 mm below the floor (r9 runs 4-5)
    dpit = shapely.distance(unary_union(pit_fps), pts).reshape(X.shape)
    wx = wx * ramp((dpit - (WALL + 1.0)) / 3.0)
    # r9: the relaxed edge fade (FILL_EDGE0/FILL_EDGE) is for the fill only (D3 is a fill shortfall); the removal
    # keeps r8's fade (1..7 mm inside the eroded plan): with the relaxed fade it lifted the lobe flank beside the R
    # upper pit (runs 4-6: 1.07-2.06 mm below the floor, sliver shells at (95.5, 53..57))
    ke8 = ramp((dP - 1.0) / 6.0)
    D = ndimage.gaussian_filter(np.minimum(net, 0.0) * ke * ws, FILL_SIGMA / BACK_GRID, mode="nearest") * ke * ws \
        + ndimage.gaussian_filter(np.maximum(net, 0.0) * wx * ke8 * ws, FILL_SIGMA / BACK_GRID, mode="nearest") * ke8 * ws
    # trigger zones (top corners): the scan below the floor is REPLACED by a height field on the smoothed target.
    # The triggers are two stacked paddles hooked round the lobe's end; cutting up to the target from below
    # (runs 1-12) only reaches their undersides and left notched remnants
    # (not faded at the plan edge above Y1, where the corner clip bounds it: faded there, run 14 left paddle
    # fragments along the corner edge)
    # (r9: the zone keeps r8's edge fade 1..7 mm inside the eroded plan; with the r9 fade the refill and the warped
    # flank parted at the zone's first row near the plan edge -> an air slot at (96, 52.5) 2.06 mm from the R upper pit)
    # r10 (G1b): the unfaded corner weight ramps in over Y1 - 7 .. Y1 - 1 (r9 switched it at Y1: a jump in U along the
    # corner edge = the D16 / D19 seam) and the weight fades out over ZONE_PIT_FADE toward the pits (r9: hard edge D20)
    yz = ramp((Y - (Y1 - 1.0 - ZONE_Y_RAMP)) / ZONE_Y_RAMP)
    wz0 = ramp((np.abs(X) - X_MONO) / X_MONO_RAMP) * ramp((Y - Y_TZ0) / Y_TZ_R) * (ke8 + (1.0 - ke8) * yz)
    wz = wz0 * ramp((dpit - (WALL + ZONE_PIT_CLEAR)) / ZONE_PIT_FADE)
    Ts = ndimage.gaussian_filter(np.where(np.isfinite(T), T, zu_f), FILL_SIGMA / BACK_GRID, mode="nearest")
    Us = zu_f + D
    # r10 (G8, measured): zu_f + gauss(net) carries the scan's own detail wherever the fill is deep: the scan's 0.74 mm
    # kink at Y -4.5 (zu -1.94 / -2.68 at Y -5 / -4, x +-30) came through as the D25 crease. Deep fill follows Ts.
    qf = ramp((-D - USM_D0) / USM_W) * ke * ws
    Us = Us + qf * (Ts - Us)
    Us = Us + wz * (Ts - Us)
    # hard need (back wall under the pocket ring, material under the pits) as a ceiling SURFACE S: flat at the
    # required level inside, rising as d^2 / (2 HARD_R) outside; U = smooth-min(target, Sc) <= Sc everywhere.
    # r7 run 10 used r6's dilating envelope, an OFFSET from the scan underside: the 6-9 mm the ring band needs
    # behind the top edge (scan underside Z -3..-7 there) spread 8 mm sideways and was applied under the trigger's
    # much lower underside, making the corner 7 mm deeper instead of 8 shallower
    # (no pit term: the lobe swell already keeps WALL round each pit in every direction of its section, downward
    # included; as a ceiling it asked for fill on the steep flank beside the upper pits -> serrations, run 15)
    Sc = ZR + shapely.distance(R0, pts).reshape(X.shape) ** 2 / (2.0 * HARD_R)
    mn = np.minimum(Us, Sc)
    U = mn - HARD_K * np.log(np.exp(-(Us - mn) / HARD_K) + np.exp(-(Sc - mn) / HARD_K))
    # r10 (G2b, D26, measured): U itself was non-convex along Y under the R lobe (0.34 at (82, 40), L 0.14): the
    # removal part of D ramps -0.5 -> +1.0 over Y 41-53 there. Lower U to its per-column lower convex hull (adds
    # material only, so never above the ceiling Sc), faded at |x| HULL_X0..+4, Y HULL_Y1..+4, at the edge and on slopes.
    Uh = U.copy()
    ky = (ysg >= 0.0) & (ysg <= HULL_Y1 + 4.0)
    for i in np.flatnonzero(np.abs(xs) > HULL_X0):
        v = valid[i] & ky
        edges = np.flatnonzero(np.diff(np.concatenate([[0], v.astype(int), [0]])))
        for s, e in zip(edges[::2], edges[1::2]):
            if e - s < MIN_RUN:
                continue
            hx, hy = [], []
            for p, q in zip(ysg[s:e], U[i, s:e]):
                while len(hx) >= 2 and (hx[-1] - hx[-2]) * (q - hy[-2]) - (hy[-1] - hy[-2]) * (p - hx[-2]) <= 0:
                    hx.pop()
                    hy.pop()
                hx.append(p)
                hy.append(q)
            Uh[i, s:e] = np.interp(ysg[s:e], hx, hy)
    wH = ramp((np.abs(X) - HULL_X0) / 4.0) * (1.0 - ramp((Y - HULL_Y1) / 4.0)) * ke * ws
    dUh = ndimage.gaussian_filter(np.maximum(U - Uh, 0.0) * wH, 1.0, mode="nearest")
    log.append("STEP 4 (G2b) lobe underside lowered to its column hull: max %.2f mm" % dUh.max())
    U = U - dUh
    D = U - zu_f
    short = float(np.where(np.isfinite(req) & valid, U - req, -99.0).max())
    # r9 (G2, measured): r8 applied D only through the slab (fill hidden HIDE inside the scan for D > ~-0.36) and the
    # eased cut (nothing for D < ~0.37), so over |D| < ~0.37 the raw scan stayed and the underside caught up with U
    # at 1.7-4x D's gradient on the D = +-0.37 contours: the D10 / D13 lines (hot cells D p10..p90 -0.4..0.6, R y 46:
    # z -13.06 / -13.64 / -13.80 at x 60 / 61 / 62). Now the moderate part Dw of D moves the scan's own underside
    # vertices (column-weighted vertical warp: underside by Dw, top fixed), so the underside IS zu + Dw with no
    # dead band; only the residual D - Dw (deep fill under the pocket ring, saturating as tanh) is slab / cut.
    hy = ramp((Y - (y_root - 8.0)) / 6.0)                       # not on the free handles (girth kept)
    # (r10: tried the zone weight without the pit fade here as a D33 fix: D33 unchanged (2.83) and the part went to
    # genus 3 (run b4). Reverted. D33's cause was the plan trim, see PT_WIN.)
    # not deep inside the trigger zones: there the back cut alone takes the paddles to U (one smooth weight, no outline).
    # r11 run a tried the warp there too (wzf = 1): it sheared the paddles' steep faces and the corner underside came
    # out crumpled (87-89 % of faces turning > 8 deg within 2 mm, 0.03 mm air gaps, a 180 deg fold at (66.3, 76.7, -13))
    # r12 (D40, measured on the run-a back-cut dump, x 66 / 76 / -76): the warp held the underside at U up to the node
    # at y 53 (Dw 2.40 / 2.52 / 1.43, wz 0.04) and was off at y 54 (wz 0.15), while the cut's offset went 3 -> 0 over
    # the same cell: between the nodes the half-warped scan hung up to 1.42 below U (max(-2.4 t, -3 (1 - t))). Now the
    # warp fades over wz 0.05..0.35 (several cells) and the cut is at U already from wz 0.05 (ecut below)
    wzf = 1.0 - ramp((wz - 0.05) / 0.30)
    thick = np.maximum(zt_f - zu_f, 0.0)
    lim = np.maximum(WARP_THICK * thick, 1e-3)
    Dfill = D if np.isinf(WARP_A) else -WARP_A * np.tanh(-D / WARP_A)
    # no warp where the column surfaces jump between grid cells (steep faces, silhouettes): there the interpolated
    # column weight is erratic (r9 run 4: 0.94 mm teeth on the handle root's inboard face at (68.3, -19.4))
    jmp = np.maximum(ndimage.maximum_filter(zu_f, 3) - ndimage.minimum_filter(zu_f, 3),
                     ndimage.maximum_filter(zt_f, 3) - ndimage.minimum_filter(zt_f, 3))
    cw = ndimage.gaussian_filter(1.0 - ramp((jmp - 2.0) / 2.0), 1.0, mode="nearest")
    # full under the ring / pocket: the back must reach U (r9 run 5: 3.37 at (38, -8)). r10 (G8, D24, measured): r9
    # switched to 1 at the ring edge itself; on the bar's steep front face (Y -12..-11) Dw went -4.6 -> -14.1 across
    # one row and the face's vertices were sheared by their exact Y (0.64-0.70 serration). Ramp in over GRING_RAMP.
    dR0in = shapely.distance(R0.exterior, pts).reshape(X.shape)
    cw = np.where(inQ, np.maximum(cw, ramp(dR0in / GRING_RAMP)), cw)
    Dw = np.where(D >= 0.0, lim * np.tanh(D / lim), Dfill) * hy * wzf * cw * valid
    from scipy.interpolate import RegularGridInterpolator as RGI
    Vb = body.vertices.copy()
    fD, fu, ft = (RGI((xs, ysg), A_, bounds_error=False, fill_value=0.0) for A_ in (Dw, zu_f, zt_f))
    dwv, zuv, ztv = fD(Vb[:, :2]), fu(Vb[:, :2]), ft(Vb[:, :2])
    sv = np.clip((ztv - Vb[:, 2]) / np.maximum(ztv - zuv, 0.5), 0.0, 1.0)
    Vb[:, 2] = Vb[:, 2] + dwv * sv
    v_ = body.volume
    body = trimesh.Trimesh(Vb, body.faces, process=False)
    if not body.is_watertight or not body.is_winding_consistent or body.volume <= 0:
        raise RuntimeError("underside warp broke the mesh")
    log.append("STEP 4a underside warp: Dw %.2f..%.2f, %d vertices moved > 0.05 mm, vol %+.1f cm3"
               % (Dw.min(), Dw.max(), int((np.abs(dwv * sv) > 0.05).sum()), (body.volume - v_) / 1e3))
    zu_w = zu_f + Dw                                            # the warped underside
    Dr = D - Dw                                                 # residual for the slab (< 0) and the cut (> 0)
    top = np.where(inQ, LIP_TOP_Z + 1.0, zu_w + np.minimum(SLAB_OVER, 0.5 * (zt_f - zu_w)))
    # where nothing is added the slab bottom sits HIDE mm inside the scan (as r6's negative offset did): a chord
    # between two grid samples otherwise pokes out of a curved surface (run 13: a serrated line along the flank)
    Dn = np.minimum(Dr, 0.0)
    bot = zu_w + Dn + HIDE * (1.0 - ramp(-Dn / 1.0))
    # r11 (corner, continuation): in the trigger zones the slab reaches CORNER_UNDER below U and the back cut trims it
    # to U, so the zone underside is U itself. Before, where the scan sat within ~0.5 of U the underside was a
    # patchwork of scan skin (HIDE kept the slab inside it) and cut surface: the crinkled band / torn flaps (r11 p1)
    wzs = ramp((wz - 0.05) / 0.10)
    bot = bot + wzs * (np.minimum(bot, U - CORNER_UNDER) - bot)
    dO = shapely.distance(omega.exterior, pts).reshape(X.shape)
    rise = np.where(dO < PLATE_R, PLATE_R - np.sqrt(np.maximum(PLATE_R ** 2 - (PLATE_R - dO) ** 2, 0.0)), 0.0)
    bot = np.minimum(bot + rise, top - 0.5)
    bot[~inO] = top[~inO] - 1.0
    # the slab exists only where it adds material (plus the pocket ring, 2 mm margin): as a hidden sliver over the
    # whole plan (runs 5-14) it poked out of the steep lower flank, where 0.5 mm vertical is ~0.2 mm of cover
    fc = valid & ((Dr < -0.05) | inQ | (wzs > 0.01))
    fpoly = shapely.union_all(shapely.box(X[fc] - 0.5, Y[fc] - 0.5, X[fc] + 0.5, Y[fc] + 0.5)).buffer(2.0)
    dom = omega.intersection(fpoly).simplify(0.05).buffer(0)
    dom = unary_union([Polygon(g.exterior, [h for h in g.interiors if Polygon(h).area > 1.0])
                       for g in getattr(dom, "geoms", [dom]) if g.geom_type == "Polygon" and g.area > 1.0])
    slab_hf = hf_solid(xs, ysg, bot, top)
    v0 = body.volume
    # r9: with the warp carrying the fill for Y > y_root - 2, the residual slab can fall into separate pieces (the
    # handle bellies below the root, as before, and the ring) -> one boolean per piece
    for dg in getattr(dom, "geoms", [dom]):
        pm_ = mprism(dg, -300.0, 300.0)
        if not pm_.is_volume:      # r11: a domain piece whose hole touches its outline extrudes to a non-volume
            dg2 = dg.buffer(0.05, join_style=2).buffer(-0.05, join_style=2)
            pm_ = mprism(dg2, -300.0, 300.0)
            log.append("  slab domain piece %s: prism not a volume, cleaned by +-0.05 (area %.1f -> %.1f, volume %s)"
                       % (np.round(dg.bounds, 1).tolist(), dg.area, dg2.area, pm_.is_volume))
        slab = boolean("intersection", slab_hf, pm_, "back slab domain")
        body = boolean("union", body, slab, "back slab", fill_voids=True)
    v1 = body.volume
    # r11 (P1, user: "it should all be one piece"): the r8-r10 trigger-zone CLEAR (difference below the floor inside a
    # polygon) + REFILL (union of a separately built block) is gone. Its outline made D11, D12, D20, D21, D23 and the
    # r10 slit D35. Measured on the step-3c body (r10 dump, 2 mm grid, x 56-108, y 46-80): inside the corner clip
    # every column is ONE material interval up to Y 76 and the paddles hang below U (lowest Z -20..-26 against U
    # -15..-21), so the back cut below takes them off like any other removal. The r8-r10 notes it replaced:
    # (trigger-zone replacement: everything below the floor goes, then the height field U .. (floor or scan) + 0.5
    # r9 (G1): the zone outline is the smooth 0.5 contour of the cell mask (r8: a union of 1 mm boxes, whose first
    # column x +-55.5 / first row Y 52.5 / corner staircase were the D11 / D4-D12 / D7 seams); above Y1 - 1, where
    # the corner clip bounds the part, the zone reaches the scan's silhouette (r8 stopped ZONE_EDGE inside it and the
    # paddle remnant between that edge and the clip outline gave the D1 / D16 teeth)
    # (r9 run 3 also left the steep flank (ws < 0.5) out of the zone: holes all over the paddle area, 26 sliver
    # shells, not watertight -- reverted)
    # (r9 runs 4-7: where the zone overlapped the R upper pit's end (Y 52.5-55) the cleared + refilled material left
    # 1.07-2.06 mm below the floor beside the pit and sliver shells at (95.5, 53..57) -> the zone keeps WALL + 3 clear
    # of every pit; the paddles start above Y ~58, beyond the pits' ends)
    # r10 (G1b): the inset from the silhouette ramps 1.5 -> 0 over Y1 - 7 .. Y1 - 1 (r9: switched at Y1 - 1); the pit
    # exclusion is WALL + 1.5 with the weight already faded to 0 there (r9: WALL + 3, hard)
    # r10 (D34): the clear's top on FLOOR_Z met the later FLOOR_Z cuts in a zero-thickness contact (extra handle).)
    # The zone weight wz survives only as the target blend Us -> Ts above (a smooth weight, no outline).
    v2 = v3 = v1
    rep_v = 0.0
    # last, the cut up to U where D > 0 (removal outside the zone; inside it U is already the refill's bottom);
    # 3 mm below U elsewhere, i.e. under the part (1 mm in run 11 nicked the flanks), easing in over the first
    # 0.5 mm of D (r8 run 1: a hard switch at D = 0 cut exactly to a chord of the flank -> stepped hairlines)
    # r11 (P1): in the trigger zones (same smooth weight wz as the target blend, pit fade included) the cut goes to U
    # whatever Dr is: across the paddles' steep faces Dr changes sign between 1 mm nodes, and the easing made the cut
    # jump 3 mm there (r11 run b: 180 deg fold at (66.4, 76.9, -14.6), 76-85 % of corner faces turning > 8 deg)
    ecut = np.maximum(ramp(Dr / 0.5), ramp(wz / 0.05))
    # r11 (corner, continuation; user: "finer surface for the corner only"): the cut is ONE height field on a
    # rectilinear grid that is CORNER_STEP fine over the corner windows and 1 mm elsewhere; U (a smoothed field) is
    # evaluated by bicubic spline there, the offset term bilinearly (identical to the 1 mm field at its nodes)
    from scipy.interpolate import RectBivariateSpline
    xf, yf = fine_axis(xs, CORNER_XB), fine_axis(ysg, CORNER_YB)
    Xf, Yf = np.meshgrid(xf, yf, indexing="ij")
    Uf = RectBivariateSpline(xs, ysg, U, kx=3, ky=3).ev(Xf, Yf)
    of = RGI((xs, ysg), 3.0 * (1.0 - ecut), bounds_error=False, fill_value=3.0)(np.column_stack([Xf.ravel(), Yf.ravel()]))
    body = boolean("difference", body, hf_solid(xf, yf, np.full(Xf.shape, -300.0),
                                                np.maximum(Uf - of.reshape(Xf.shape), -299.0)), "back cut")
    log.append("back cut grid %d x %d (%.2f mm over |x| %s, Y %s)" % (len(xf), len(yf), CORNER_STEP, CORNER_XB, CORNER_YB))
    if DUMP:   # r12 (D40, review_r11: "which operand hangs is not verified"): the back-cut arrays themselves
        np.savez(DUMP + "_backcut.npz", xf=xf, yf=yf, Uf=Uf, cutf=Uf - of.reshape(Xf.shape), xs=xs, ys=ysg, U=U,
                 bot=bot, top=top, ecut=ecut, wzs=wzs, wzf=wzf, wz=wz, Dr=Dr, Dw=Dw, zu=zu, zu_w=zu_w, D=D, fc=fc)
        body.export(DUMP + "_afterback.stl")
    log.append("STEP 4+5 convex back (monotone above Y %.1f, hull under min(scan, required)): target adds max %.2f, "
               "removes max %.2f | underside above the required back by at most %.3f mm | D %.2f..%.2f | slab "
               "+%.1f cm3 | trigger zones (|x| > %.0f, Y > %.0f): cleared %.1f cm3, refilled %.1f cm3 | cut -%.1f cm3"
               % (Y_MONO, -np.nanmin(net), np.nanmax(net), short, D.min(), D.max(), (v1 - v0) / 1e3, X_MONO, Y_TZ0,
                  (v1 - v2) / 1e3, rep_v / 1e3, (v3 - body.volume) / 1e3))
    # --- step 4d (r10, D8 option B; r9's step 3d): remove width toward the user's bowed arc, on the finished back
    v_ = body.volume
    for _ in range(PT_PASSES):
        body, ptinfo = plan_trim(body, pit_fps, fingers, K, log)
    log.append("STEP 4d plan trim (after step 4, weight centred at theta %.0f deg, %d passes): %+.1f mm3"
               % (PT_T0, PT_PASSES, body.volume - v_))

    # --- r12 (P1 + P1b + P2, user 2026-10-02): ONE top cut. It replaces r11's front cut + parabolic blend (D17), the
    #     end roll (D41) and the top-edge opening prism B. Everything above TOP_Z goes, handles included; the edge
    #     where that plane meets the skin, the B line and the clip K is rolled (ball opening, radius up to TOP_R_MAX);
    #     beyond the wall-end line the cut floor is FLOOR_Z with a concave base fillet (the fill: lobe material that
    #     is no longer cut away, below the button band). Measured before the cut, applied in one difference.
    if DUMP:
        np.savez(DUMP + "_fields.npz", xs=xs, ys=ysg, zu=zu, zt=zt, net=net, T=T, D=D, U=U, Us=Us, wz=wz, ke=ke,
                 ws=ws, wx=wx, dP=dP, Sc=Sc, Dw=Dw)
        hw.export(DUMP + "_hw.stl")
        lw.export(DUMP + "_lw.stl")
        body.export(DUMP + "_precut.stl")
    body, tinfo = top_cut(body, oval, S, nSd, K, Y1, pit_fps, log)
    if DUMP:
        np.savez(DUMP + "_top.npz", **tinfo)

    # --- top-corner lobe clip (all Z): oval offset G(y) shrinking to WALL at the top (K from step 4)
    A_m = mprism(sbox(-BIG, Y1 - 1.0, BIG, BIG).difference(K), -300.0, 300.0, log, "A")
    body = boolean("difference", body, A_m, "top-corner lobe clip")
    log.append("top-corner clip: lobe offset D0 %.2f (incl. margin %.1f) -> WALL %.1f at the top edge"
               % (D0, D0_MARGIN, WALL))

    # --- bottom edge open above the floor for |x| < X_OPEN, ring ends rounded
    # r9 (G4, D9/D6): ONE opening. r8 used two boxes (|x| < 70 down to Y -13.0, |x| < 56 down to crotch - 0.5) and
    # left the strip |x| 56..66, Y -13.7..-13.0 between the first box's edge and the scan's front face as a < 1 mm fin
    # (R) / sliver (L). The lower edge is now one C1 curve from (+-56, crotch - 0.5) to the pocket end (+-70, -9):
    # it dips into the air in front of the scan face over |x| 56..62 and crosses the receding face steeply
    # (x ~ 63-64) so the material corner it leaves is a wedge, not a sheet.
    # r10 (G4b): the lower edge is now per side from the measured face (c_plan_r10); the r9 C_EDGE curve is unused
    C_plan = c_plan_r10(body, crotch - 0.5, log).buffer(0)
    log.append("bottom-edge opening (r10): plan %.1f mm2, x %.2f..%.2f" % (C_plan.area, C_plan.bounds[0], C_plan.bounds[2]))
    body = boolean("difference", body, mprism(C_plan, FLOOR_Z, 100.0, log, "C"), "bottom edge open")

    # --- pocket, pits, fingers
    body = boolean("difference", body, bc.prism(oval, FLOOR_Z, 100.0), "pocket")
    pits = []
    for p, n, fr in fingers:
        pm, _ = pit_solid(fr)
        pits.append(pm)
        body = boolean("difference", body, pm, "finger pit at %s" % np.round(p, 1).tolist())
    finfo = []
    for p, n, fr in fingers:
        f_, fi = finger_solid(fr)
        body = boolean("union", body, f_, "finger at %s" % np.round(p, 1).tolist())
        finfo.append((p, n, fi))
    fi = finfo[0][2]
    log.append("lip: tip Z %.3f, lead-in top t %.3f, head outer u %.3f -> top land %.3f, chamfer from Z %.2f"
               % (fi["z_tip"], fi["t_top"], fi["u_head"], fi["land"], fi["z_ch"]))

    # --- window + camera
    wprof = sbox(-WINDOW_W / 2 + WINDOW_R, WIN_Y0 + WINDOW_R, WINDOW_W / 2 - WINDOW_R,
                 WIN_Y1 - WINDOW_R).buffer(WINDOW_R, resolution=24)
    body = boolean("difference", body, bc.prism(wprof, -300.0, FLOOR_Z + 2.0), "window")
    cam = Point(0.0, CAMERA_Y).buffer(CAMERA_HOLE_D / 2.0, resolution=32)
    body = boolean("difference", body, bc.prism(cam, -300.0, FLOOR_Z + 2.0), "camera hole")
    log.append("window %.2f x %.2f Y %.3f..%.3f R %.1f | camera D %.1f at Y %.3f; bridge %.2f"
               % (WINDOW_W, WIN_Y1 - WIN_Y0, WIN_Y0, WIN_Y1, WINDOW_R, CAMERA_HOLE_D, CAMERA_Y,
                  CAMERA_Y - CAMERA_HOLE_D / 2 - WIN_Y1))
    log.extend(DROPPED)
    log.append("build %.1f s" % (time.time() - t0))
    ctx = dict(scan=scan, ext=ext, hw=hw, oval=oval, P=P, N=N, R0=R0, S=S, Y1=Y1, fingers=finfo, pits=pits,
               pit_fps=pit_fps, y_root=y_root, hinfo=hinfo, wprof=wprof, cam=cam, omega=omega)
    return body, ctx, log


# ================================================================ r10: fillets (last stage)
def edge_family(p):
    """Edge family by location: the form-auditor's classification (audit/r9/scripts/rv_review.py, 'fillet')."""
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    ax = np.abs(x)
    fam = np.full(len(p), "lobe/other", dtype=object)
    fam[y < -14] = "handle"
    fam[(z < FLOOR_Z - 1.0) & (ax < 66)] = "back-bar"
    fam[(z > 12.5) & (ax > 60)] = "front-cut"
    fam[y > 74] = "top-edge"
    fam[(-17 < y) & (y < -8) & (ax < 74) & (z > FLOOR_Z - 1.0)] = "bottom-opening"
    fam[(y > 52) & (ax > 55)] = "corner"
    return fam


def functional(p, ctx):
    """Pocket / lip, pits / fingers, window / camera surfaces: never moved by a fillet (auditor's exclusion)."""
    inOval = shapely.contains_xy(ctx["oval"].buffer(1.0), p[:, 0], p[:, 1]) & (p[:, 2] > FLOOR_Z - 0.5)
    inPit = shapely.contains_xy(unary_union(ctx["pit_fps"]).buffer(1.0), p[:, 0], p[:, 1]) & (p[:, 2] > ROOT_Z - 1.5)
    inWin = (shapely.contains_xy(ctx["wprof"].buffer(1.0), p[:, 0], p[:, 1]) & (p[:, 2] < FLOOR_Z + 0.5)) | \
        (np.hypot(p[:, 0], p[:, 1] - CAMERA_Y) < CAMERA_HOLE_D / 2 + 1.0)
    return inOval | inPit | inWin


def refine_local(V, F, want_split, t_end, max_faces, iters=40, closure=True):
    """Crack-free refinement: split edges for which want_split(midpoint, length) is True, plus (closure) the longest
    edge of every face that has a split edge, so a face is never bisected across a short edge (r10 run 2: green
    bisections across short edges made slivers and grew the mesh to 1.45 M faces). Stops at t_end / max_faces.
    closure=False (r14): only the edges want_split names are split. closure=callable(V, F) -> bool per face: only those
    faces get the closure (r14, rolled wall edges: the skin faces do, the vertical wall strip keeps its two vertex rows)."""
    for _ in range(iters):
        E = np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), axis=1)
        Eu, inv = np.unique(E, axis=0, return_inverse=True)
        inv = inv.ravel().reshape(3, -1).T                      # per face: unique-edge index of (01), (12), (20)
        L = np.linalg.norm(V[Eu[:, 0]] - V[Eu[:, 1]], axis=1)
        mp = 0.5 * (V[Eu[:, 0]] + V[Eu[:, 1]])
        split = want_split(mp, L)
        if not split.any():
            return V, F, "converged"
        longest = inv[np.arange(len(F)), np.argmax(L[inv], axis=1)]
        clm = None if closure is True or closure is False else closure(V, F)   # callable: faces that get the closure
        for _c in range(0 if closure is False else 20):          # closure
            fs = split[inv].any(axis=1)
            if clm is not None:
                fs = fs & clm
            add = longest[fs][~split[longest[fs]]]
            if not len(add):
                break
            split[add] = True
        if len(F) + 3 * split.sum() > max_faces:
            return V, F, "face cap (%d faces + %d splits)" % (len(F), split.sum())
        if time.time() > t_end:
            return V, F, "time cap"
        nid = np.full(len(Eu), -1)
        nid[split] = len(V) + np.arange(split.sum())
        V = np.vstack([V, mp[split]])
        M = nid[inv]
        a, b, c = F[:, 0], F[:, 1], F[:, 2]
        m01, m12, m20 = M[:, 0], M[:, 1], M[:, 2]
        s01, s12, s20 = m01 >= 0, m12 >= 0, m20 >= 0
        n = s01.astype(int) + s12 + s20
        out = [F[n == 0]]
        pats = [(n == 3, ((a, m01, m20), (m01, b, m12), (m20, m12, c), (m01, m12, m20))),
                ((n == 1) & s01, ((a, m01, c), (m01, b, c))),
                ((n == 1) & s12, ((a, b, m12), (a, m12, c))),
                ((n == 1) & s20, ((a, b, m20), (m20, b, c))),
                ((n == 2) & s01 & s12, ((m01, b, m12), (a, m01, m12), (a, m12, c))),
                ((n == 2) & s12 & s20, ((m20, m12, c), (a, b, m12), (a, m12, m20))),
                ((n == 2) & s20 & s01, ((a, m01, m20), (m01, b, c), (m01, c, m20)))]
        for k, ts in pats:
            out += [np.column_stack(t)[k] for t in ts]
        F = np.vstack(out)
    return V, F, "iteration cap"


def fillet_family(m, ctx, fam_name, r, log, tcap=FILLET_TCAP, max_faces=FILLET_MAXF):
    """r10 (D27-D31): rolling-ball fillet of ONE edge family, inside a local box. Candidate edges: dihedral >
    FILLET_DIH, family fam_name, not functional. The mesh is refined only inside the box, within FILLET_BAND r of a
    candidate edge, to edges <= r / FILLET_H. A ball of radius r counts when no surface sample is closer to its centre
    than r; a band vertex that no inside ball reaches (convex edge) moves onto the nearest one, a vertex that no outside
    ball reaches (concave edge) onto the nearest outside ball. Functional vertices never move. A move > FILLET_CAP r
    is refused and logged (the radius does not fit there). Returns (mesh, info)."""
    t0 = time.time()
    t_end = t0 + tcap
    ang = np.degrees(m.face_adjacency_angles)
    em = m.vertices[m.face_adjacency_edges].mean(axis=1)
    cand = (ang > FILLET_DIH) & (edge_family(em) == fam_name) & ~functional(em, ctx)
    info = dict(fam=fam_name, r=r, edges=int(cand.sum()))
    if not cand.any():
        log.append("  fillet %s: no candidate edges" % fam_name)
        return m, info
    ev = m.vertices[m.face_adjacency_edges[cand]]
    ln = np.linalg.norm(ev[:, 1] - ev[:, 0], axis=1)
    info["length"] = float(ln.sum())
    ns = np.maximum(1, np.ceil(ln / 0.2).astype(int))
    rep = np.repeat(np.arange(len(ev)), ns)
    tt = (np.concatenate([np.arange(k) for k in ns]) + 0.5) / np.repeat(ns, ns)
    Q = ev[rep, 0] + tt[:, None] * (ev[rep, 1] - ev[rep, 0])
    trQ = cKDTree(Q)
    lo, hi = Q.min(axis=0) - (FILLET_BAND + 2.0) * r, Q.max(axis=0) + (FILLET_BAND + 2.0) * r

    def inbox(P):
        return np.all((P >= lo) & (P <= hi), axis=1)

    def want(P, L):
        k = inbox(P) & (L > r / FILLET_H)
        d = np.full(len(P), np.inf)
        d[k] = trQ.query(P[k])[0]
        return k & (d < FILLET_BAND * r + L / 2)

    V, F, why = refine_local(m.vertices.copy(), m.faces.copy(), want, t_end, max_faces)
    mr = trimesh.Trimesh(V, F, process=False)
    info.update(faces_before=len(m.faces), faces_after=len(F), refine=why)
    if not mr.is_watertight or why != "converged":
        log.append("  fillet %s r %.1f: STOPPED at refinement (%s; %d -> %d faces, watertight %s, %.1f s)"
                   % (fam_name, r, why, len(m.faces), len(F), mr.is_watertight, time.time() - t0))
        info["status"] = "stopped: " + why
        return m, info
    FN = mr.face_normals
    tri = V[F]
    cen = tri.mean(axis=1)
    fbox = inbox(cen)
    # surface samples near the box (the whole box, both sides of thin walls): vertices, centroids, edge midpoints
    S = np.vstack([V[inbox(V)], cen[fbox]] + [0.5 * (tri[fbox, i] + tri[fbox, (i + 1) % 3]) for i in range(3)])
    trS = cKDTree(S)
    # ball tangent points: band faces only, 10 points per face with the face normal
    dq = trQ.query(cen[fbox])[0]
    fi = np.flatnonzero(fbox)[dq < (FILLET_BAND + 1.0) * r]
    pts = np.vstack([tri[fi, 0], tri[fi, 1], tri[fi, 2], cen[fi]]
                    + [0.5 * (tri[fi, i] + tri[fi, (i + 1) % 3]) for i in range(3)]
                    + [0.5 * (tri[fi, i] + cen[fi]) for i in range(3)])
    nrm = np.tile(FN[fi], (10, 1))
    kv = np.flatnonzero(inbox(V))
    kv = kv[trQ.query(V[kv])[0] < FILLET_BAND * r]
    kv = kv[~functional(V[kv], ctx)]
    Vn = V.copy()
    refused = []
    ffun = np.flatnonzero(fbox & functional(cen, ctx))
    fplan = unary_union(list(ctx["pit_fps"]) + [ctx["oval"]])
    if len(ffun):
        fsub = trimesh.Trimesh(V, F[ffun], process=False)

        def convex_floor(P):
            return trimesh.proximity.closest_point(fsub, P)[1]
    else:
        convex_floor = None
    for sgn_, kind in ((-1.0, "convex"), (1.0, "concave")):
        if time.time() > t_end:
            info["status"] = "stopped: time cap in the ball search"
            log.append("  fillet %s: STOPPED, time cap in the ball search" % fam_name)
            return m, info
        C = pts + sgn_ * r * nrm
        kc = trS.query(C)[0] >= r - 1e-3
        d, j = cKDTree(C[kc]).query(V[kv])
        phi = d - r
        need = phi > 1e-4
        cap = need & (phi > FILLET_CAP * r)
        go = need & ~cap
        cc = C[kc][j[go]]
        u = V[kv[go]] - cc
        newp = cc + r * u / np.linalg.norm(u, axis=1)[:, None]
        # floors: a moved vertex keeps WALL (BACK_T under the pocket) from every functional surface (pocket, pits,
        # lips, window); if the full move breaks that, the move is shrunk (s = 0.75 .. 0) and the place is logged
        # (r10 D29 test: unclamped, the R upper pit wall at Z 13.3 fell 3.48 -> 1.16)
        if convex_floor is not None:
            old = V[kv[go]]
            dold = np.abs(convex_floor(old))
            needw = np.where((old[:, 2] < FLOOR_Z) & shapely.contains_xy(ctx["oval"], old[:, 0], old[:, 1]), BACK_T, WALL)
            needw = np.minimum(needw, dold)
            s = np.ones(len(old))
            # ... and the Z-section wall (gate G11): a vertex that ends below the lip top within WALL (in plan) of a
            # pit / the pocket would open air in that section (D29 test: R upper pit 3.48 -> 1.34 at Z 13.3)
            d2o = shapely.distance(fplan, shapely.points(old[:, 0], old[:, 1]))
            for s_try in (1.0, 0.75, 0.5, 0.25, 0.0):
                p_ = old + s_try * (newp - old)
                d2 = shapely.distance(fplan, shapely.points(p_[:, 0], p_[:, 1]))
                d2need = np.where(old[:, 2] < LIP_TOP_Z - 0.2, np.minimum(WALL, d2o), WALL)
                sec = (p_[:, 2] < LIP_TOP_Z - 0.2) & (p_[:, 2] > FLOOR_Z) & (d2 < d2need - 1e-3)
                bad = (s == s_try) & ((np.abs(convex_floor(p_)) < needw - 1e-3) | sec)
                s[bad] = max(s_try - 0.25, 0.0)
            newp = old + s[:, None] * (newp - old)
            if (s < 1).any():
                shr = s < 1
                info.setdefault("shrunk", []).append((kind, old[shr], s[shr]))
        mv = np.linalg.norm(newp - V[kv[go]], axis=1)
        cur = np.linalg.norm(Vn[kv[go]] - V[kv[go]], axis=1)
        take = mv > cur
        Vn[kv[go][take]] = newp[take]
        info[kind] = (int(go.sum()), float(mv.max()) if len(mv) else 0.0)
        if cap.any():
            refused.append((kind, V[kv[cap]], phi[cap]))
    # faces the projection turned over (fold): put their vertices back, repeat (logged as "reverted")
    rev = []
    for _ in range(8):
        out = trimesh.Trimesh(Vn, F, process=False)
        fl = np.flatnonzero(np.einsum("ij,ij->i", out.face_normals, FN) < 0.2)
        fl = fl[np.linalg.norm(Vn[F[fl]] - V[F[fl]], axis=(1, 2)) > 0]
        if not len(fl):
            break
        rev.append(out.triangles_center[fl])
        vv = np.unique(F[fl])
        Vn[vv] = V[vv]
    out = trimesh.Trimesh(Vn, F, process=False)
    if rev:
        rc = np.vstack(rev)
        log.append("    reverted (fold) %d faces' vertices, e.g. at %s" % (len(rc), np.round(rc[:: max(1, len(rc) // 5)][:5], 1).tolist()))
    flip = int((np.einsum("ij,ij->i", out.face_normals, FN) < 0).sum())
    info.update(flip=flip, dvol=out.volume - m.volume, refused=refused, t=time.time() - t0)
    log.append("  fillet %s r %.1f: %d edges %.0f mm | refine %d -> %d faces | convex %d moved (max %.2f), concave %d "
               "moved (max %.2f) | refused %s | %d faces flipped | vol %+.1f mm3 | %.1f s"
               % (fam_name, r, info["edges"], info["length"], len(m.faces), len(F), *info.get("convex", (0, 0)),
                  *info.get("concave", (0, 0)), ["%s %d" % (k_, len(p_)) for k_, p_, _ in refused] or "none", flip,
                  info["dvol"], info["t"]))
    for k_, p_, ph in refused:
        o = np.argsort(-ph)[:5]
        log.append("    refused %s: %s (needed move / r: %s)" % (k_, np.round(p_[o], 1).tolist(), np.round(ph[o] / r, 2).tolist()))
    for k_, p_, s_ in info.get("shrunk", []):
        o = np.argsort(s_)[:5]
        ext = np.ptp(p_, axis=0) if len(p_) > 1 else np.zeros(3)
        log.append("    shrunk to keep WALL/BACK (%s): %d vertices over a %.1f x %.1f x %.1f box, e.g. %s (move kept: %s)"
                   % (k_, len(p_), *ext, np.round(p_[o], 1).tolist(), np.round(s_[o], 2).tolist()))
    info["status"] = "applied" if flip == 0 else "applied, %d faces flipped" % flip
    return out, info


def fix_degenerate(m, log, tol=1e-4, emax=0.02, passes=4):
    """r10: zero-area faces (< tol mm2). Measured on run b8: all 26 have a shortest edge of 0.0019-0.0144 mm. Each such
    edge is collapsed to its midpoint (only edges < emax, one per vertex per pass); the faces that lose a vertex go.
    Kept only if the result stays watertight, winding-consistent and of the same genus; else the input is kept.
    (r10 first try, flipping the longest edge, broke watertightness: the flip can duplicate an existing edge.)"""
    n0 = int((m.area_faces < tol).sum())
    g0 = m.euler_number
    cur = m
    for _ in range(passes):
        V, F = cur.vertices.copy(), cur.faces
        bad = np.flatnonzero(cur.area_faces < tol)
        if not len(bad):
            break
        mp = np.arange(len(V))
        used = np.zeros(len(V), bool)
        for f in bad:
            tri = F[f]
            e = [(tri[i], tri[(i + 1) % 3]) for i in range(3)]
            p, q = min(e, key=lambda t: np.linalg.norm(V[t[0]] - V[t[1]]))
            if np.linalg.norm(V[p] - V[q]) >= emax or used[p] or used[q]:
                continue
            V[p] = 0.5 * (V[p] + V[q])
            mp[q] = p
            used[p] = used[q] = True
        F2 = mp[F]
        keep = (F2[:, 0] != F2[:, 1]) & (F2[:, 1] != F2[:, 2]) & (F2[:, 2] != F2[:, 0])
        nxt = trimesh.Trimesh(V, F2[keep], process=False)
        nxt.remove_unreferenced_vertices()
        if not (nxt.is_watertight and nxt.is_winding_consistent and nxt.euler_number == g0):
            log.append("  degenerate collapse pass broke the mesh (watertight %s, euler %d vs %d): stopped"
                       % (nxt.is_watertight, nxt.euler_number, g0))
            break
        cur = nxt
    # caps left (collinear, no short edge; final r10 run: 7, shortest edges 0.22-0.43 mm): flip the longest edge with
    # the neighbour across it, only if the new edge does not exist yet (that check is what the first try lacked)
    for _ in range(passes):
        bad = np.flatnonzero(cur.area_faces < tol)
        if not len(bad):
            break
        F = cur.faces.copy()
        V = cur.vertices
        es = set(map(tuple, np.sort(cur.edges_unique, axis=1)))
        nb = {}
        for (f1, f2), e in zip(cur.face_adjacency, cur.face_adjacency_edges):
            k_ = tuple(sorted(e))
            nb.setdefault(f1, {})[k_] = f2
            nb.setdefault(f2, {})[k_] = f1
        used = set()
        for f in bad:
            a, b, c = F[f]
            p, q, o = max([(a, b, c), (b, c, a), (c, a, b)], key=lambda t: np.linalg.norm(V[t[0]] - V[t[1]]))
            g = nb.get(f, {}).get(tuple(sorted((p, q))))
            if g is None or f in used or g in used:
                continue
            d = [v for v in F[g] if v not in (p, q)][0]
            if tuple(sorted((o, d))) in es or o == d:
                continue
            t1, t2 = np.array([o, p, d]), np.array([o, d, q])
            if min(np.linalg.norm(np.cross(V[t[1]] - V[t[0]], V[t[2]] - V[t[0]])) for t in (t1, t2)) < 2 * tol:
                continue
            F[f], F[g] = t1, t2
            es.add(tuple(sorted((o, d))))
            used.update((f, g))
        nxt = trimesh.Trimesh(V, F, process=False)
        if not (nxt.is_watertight and nxt.is_winding_consistent and nxt.euler_number == g0):
            log.append("  degenerate flip pass broke the mesh: stopped")
            break
        cur = nxt
    n1 = int((cur.area_faces < tol).sum())
    log.append("degenerate faces (< %.0e mm2): %d -> %d (shortest-edge collapse < %.2f mm); watertight %s, euler %d"
               % (tol, n0, n1, emax, cur.is_watertight, cur.euler_number))
    return cur


def collapse_slivers(m, fixed, log, ang=SLIVER_ANG, emax=SLIVER_EMAX, tol=1e-4, passes=3):
    """r15: edge-collapse cleanup of slivers (faces with min angle < ang deg or area < tol). The boolean cuts of r15 (the R rim
    mirror cut, the bar rear-bottom cut) re-triangulate the old 60-140 mm triangles around the cut line and leave thin
    pieces whose short edge is 0.002-0.2 mm. For each such face the shortest edge (p, q) shorter than emax is collapsed
    (to the fixed vertex if one is fixed, else to the midpoint) when: both are not fixed, the link condition holds (the two
    vertices share exactly the two apexes of the edge's faces: no new non-manifold edge), and no other face around them
    turns by more than ~70 deg or loses its orientation. r10's fix_degenerate collapses all at once and gives up on the first
    broken mesh; this one checks every collapse. Kept only if watertight, one genus, same winding."""
    t0 = time.time()
    V, F = m.vertices.copy(), m.faces.copy()
    g0 = m.euler_number

    def tri_nrm(P, tri):
        n = np.cross(P[tri[1]] - P[tri[0]], P[tri[2]] - P[tri[0]])
        return n, np.linalg.norm(n)

    n_start = None
    moved_max = 0.0
    total = 0
    for ps in range(passes):
        T = V[F]
        a = np.linalg.norm(T[:, 1] - T[:, 2], axis=1)
        b = np.linalg.norm(T[:, 0] - T[:, 2], axis=1)
        c = np.linalg.norm(T[:, 0] - T[:, 1], axis=1)
        with np.errstate(all="ignore"):
            A = np.degrees(np.arccos(np.clip((b * b + c * c - a * a) / (2 * b * c), -1, 1)))
            B = np.degrees(np.arccos(np.clip((a * a + c * c - b * b) / (2 * a * c), -1, 1)))
        mina = np.nan_to_num(np.minimum(np.minimum(A, B), 180.0 - A - B), nan=0.0)
        area = 0.5 * np.linalg.norm(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]), axis=1)
        cand = np.flatnonzero((mina < ang) | (area < tol))
        if n_start is None:
            n_start = len(cand)
        if not len(cand):
            break
        cand = cand[np.argsort(np.minimum(np.minimum(a, b), c)[cand])]
        vf = [set() for _ in range(len(V))]
        for fi, tri in enumerate(F):
            for v in tri:
                vf[v].add(fi)
        alive = np.ones(len(F), bool)
        done = 0

        def nb(v):
            s = set()
            for g in vf[v]:
                s.update(F[g].tolist())
            s.discard(v)
            return s

        for f in cand:
            if not alive[f]:
                continue
            tri = F[f]
            es = [(tri[i], tri[(i + 1) % 3]) for i in range(3)]
            p, q = min(es, key=lambda t: np.linalg.norm(V[t[0]] - V[t[1]]))
            L = np.linalg.norm(V[p] - V[q])
            if L >= emax or (fixed[p] and fixed[q]):
                continue
            s_, r_ = (p, q) if (fixed[p] or not fixed[q]) else (q, p)       # survivor, removed
            tgt = V[s_] if fixed[s_] else 0.5 * (V[p] + V[q])
            fe = [g for g in vf[p] if alive[g] and q in F[g]]
            if len(fe) != 2:
                continue
            opp = {x for g in fe for x in F[g].tolist() if x not in (p, q)}
            if (nb(p) & nb(q)) != opp:
                continue
            ok = True
            Vt = V.copy()
            Vt[s_] = tgt
            for g in (vf[p] | vf[q]) - set(fe):
                if not alive[g]:
                    continue
                old = F[g]
                new = np.where(old == r_, s_, old)
                n0, l0 = tri_nrm(V, old)
                n1, l1 = tri_nrm(Vt, new)
                if l1 < 1e-12:
                    ok = False
                    break
                if l0 > 2e-4 and (n0 @ n1) / (l0 * l1) < 0.35:
                    ok = False
                    break
            if not ok:
                continue
            V[s_] = tgt
            moved_max = max(moved_max, L / 2.0 if not fixed[s_] else L)
            for g in fe:
                alive[g] = False
                for v in F[g]:
                    vf[v].discard(g)
            for g in list(vf[r_]):
                F[g] = np.where(F[g] == r_, s_, F[g])
                vf[s_].add(g)
            vf[r_] = set()
            done += 1
        F = F[alive]
        total += done
        if done == 0:
            break
    out = trimesh.Trimesh(V, F, process=False)
    out.remove_unreferenced_vertices()
    ok = out.is_watertight and out.is_winding_consistent and out.euler_number == g0 and out.volume > 0
    T = out.vertices[out.faces]
    cnt = int((np.minimum.reduce([np.degrees(np.arccos(np.clip(((T[:, (i + 1) % 3] - T[:, i]) * (T[:, (i + 2) % 3] - T[:, i])).sum(1) /
                                  np.maximum(np.linalg.norm(T[:, (i + 1) % 3] - T[:, i], axis=1) * np.linalg.norm(T[:, (i + 2) % 3] - T[:, i], axis=1), 1e-30), -1, 1)))
                                  for i in range(3)]) < ang).sum())
    log.append("  sliver collapse (< %.2f deg or < %.0e mm2, edge < %.2f): candidates %d -> %d, %d collapses, max move %.3f, %d faces, "
               "watertight %s winding %s euler %d (target %d) | %s | %.1f s"
               % (ang, tol, emax, n_start or 0, cnt, total, moved_max, len(out.faces), out.is_watertight, out.is_winding_consistent,
                  out.euler_number, g0, "KEPT" if ok else "REJECTED, input kept", time.time() - t0))
    return out if ok else m


def clean(body, tol=CLEAN_TOL):
    """Round-trip through manifold3d in float32 and collapse edges shorter than tol (slivers)."""
    import manifold3d as mf
    M = mf.Manifold(mf.Mesh(vert_properties=np.asarray(body.vertices, np.float32),
                            tri_verts=np.asarray(body.faces, np.uint32)))
    if hasattr(M, "simplify"):
        M = M.simplify(tol)
    o = M.to_mesh()
    r = trimesh.Trimesh(np.asarray(o.vert_properties)[:, :3].astype(np.float64), np.asarray(o.tri_verts),
                        process=True)
    print("clean: manifold3d simplify(%.3f) -> %d faces (was %d), volume change %.3f mm3"
          % (tol, len(r.faces), len(body.faces), r.volume - body.volume), flush=True)
    return r


# ================================================================ r13: finishing (last stage)
def finish_locks(V, ctx):
    """Zero-travel locks, each defined geometrically (plan outlines from the build, Z from the constants)."""
    x, y, z = V[:, 0], V[:, 1], V[:, 2]
    pits = unary_union(ctx["pit_fps"])
    L = {}
    L["top plane Z %.2f (z >= %.3f)" % (TOP_Z, TOP_Z - 1e-3)] = z >= TOP_Z - 1e-3
    L["pocket walls + floor (oval + 0.05, z >= FLOOR_Z - 0.05)"] = \
        shapely.contains_xy(ctx["oval"].buffer(0.05), x, y) & (z >= FLOOR_Z - 0.05)
    kf = "lips + fingers (pit outline + 0.05, z >= ROOT_Z - 1.5)"
    L[kf] = shapely.contains_xy(pits.buffer(0.05), x, y) & (z >= ROOT_Z - 1.5)
    L["pit walls (within WALL + 1 of a pit outline, all z)"] = shapely.contains_xy(pits.buffer(WALL + 1.0), x, y) & ~L[kf]
    L["window + camera hole (outline + 0.05, z <= FLOOR_Z + 2.05)"] = (z <= FLOOR_Z + 2.05) & (
        shapely.contains_xy(ctx["wprof"].buffer(0.05), x, y) | (np.hypot(x, y - CAMERA_Y) <= CAMERA_HOLE_D / 2 + 0.05))
    # r13 quick fix (audit/r13/check_r13.md): the smooth raised the back underside at (-65.0, -8.47) by 0.013 (back
    # 3.499 -> 3.486 on a 0.5 mm grid) and put a 0.22 mm p-p wobble into the bottom bar's lower edge (r12 0.024)
    # r14 (user 2026-10-02): the lock holds only columns whose back is thinner than BACK_LOCK_T (underside above
    # FLOOR_Z - BACK_LOCK_T), so the D40 ridge (back 5.8), the D11 seam and the R creases D19 / D16 (back 5-13) can be
    # smoothed, and reaches oval + 4 at the rear so the bar's rear edge (y 78.55, = oval + 3.0) moves as one piece (D51 b:
    # the r13 boundary sat exactly on the rear face and left a 0.12 mm wobble). Back >= BACK_LOCK_T minus the smooth's
    # travel 0.2 stays >= 4.0, above the 3.5 required.
    L["back underside under the pocket (oval + 4, back thinner than %.1f)" % BACK_LOCK_T] = \
        shapely.contains_xy(ctx["oval"].buffer(4.0), x, y) & (z <= FLOOR_Z - 0.5) & (z >= FLOOR_Z - BACK_LOCK_T)
    L["trim end faces (y <= TRIM_Y + 1e-3)"] = y <= TRIM_Y + 1e-3
    # r14: the rim wall (cut by rim_outline: planar quads on a smooth curve) and the rolls (warp_roll) are finished as built.
    # The finish smooth (tangential on the vertices near edges > 120 deg) slid their vertices along the wall and put the
    # vertical striping back (r14 run 2 render: clean band after the cut and rolls, striped after finish)
    # r15: the lock on the rim wall below the top roll is gone (L is finished as in r13: the review asked L within 0.05 of
    # r13); the top-roll band (z >= -10.4) and the rear wall / bar roll (y >= 77) are still finished as built
    L["rim top roll (|x| >= 72, y >= 61, outside oval + 3.4, z -10.4..-8; rear wall y >= 77; z -15..-8)"] = \
        (z <= -8.0) & (z >= -15.0) & ((((np.abs(x) >= 72.0) & (y >= 61.0) & (z >= -10.4)
                                        & ~shapely.contains_xy(ctx["oval"].buffer(WALL + 0.4), x, y))) | (y >= 77.0))
    # z up to FLOOR_Z + 0.5: with z <= -11.5 only, the front-face triangles reaching up to the floor kept free upper
    # vertices and the edge line (z -11 crossing) still read 0.072 / 0.086 p-p (+x / -x)
    L["bottom-bar lower edge + front face (|x| 26..62, y -12..-8.5, z -13..FLOOR_Z + 0.5)"] = \
        (np.abs(x) >= 26.0) & (np.abs(x) <= 62.0) & (y >= -12.0) & (y <= -8.5) & (z >= -13.0) & (z <= FLOOR_Z + 0.5)
    return L


def _dihedral(V, F, adj):
    n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    n /= np.maximum(np.linalg.norm(n, axis=1), 1e-30)[:, None]
    return np.degrees(np.arccos(np.clip((n[adj[:, 0]] * n[adj[:, 1]]).sum(1), -1.0, 1.0)))


def _vnormals(V, F):
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    vn = np.zeros_like(V)
    for k in range(3):
        np.add.at(vn, F[:, k], fn)
    return vn / np.maximum(np.linalg.norm(vn, axis=1), 1e-30)[:, None]


def _relax(V, Vref, A, deg, mov, lam, capv, F, adj, ae, au, normal_only=False):
    """One umbrella step lam * L(V) on the movable vertices (normal_only: its component along the area-weighted vertex
    normal, so the step changes the form and does not slide the triangulation), travel from Vref clamped per vertex to
    capv, no vertex above TOP_Z; then every move that leaves an incident dihedral above FINISH_FOLD (and above its
    value before) is undone, for the 4 vertices of that edge, until none is left. Returns (V, vertices undone)."""
    a0 = _dihedral(V, F, adj)
    Lp = (A @ V) / deg[:, None] - V
    if normal_only is not False:   # True, or a per-vertex mask (True: normal component only)
        vn = _vnormals(V, F)
        no = np.broadcast_to(np.asarray(normal_only, bool), (len(V),))
        Lp = np.where(no[:, None], (Lp * vn).sum(1)[:, None] * vn, Lp)
    Vn = V.copy()
    Vn[mov] += lam * Lp[mov]
    d = Vn - Vref
    dl = np.linalg.norm(d, axis=1)
    Vn = Vref + d * np.minimum(1.0, capv / np.maximum(dl, 1e-12))[:, None]
    Vn[:, 2] = np.where(mov & (Vref[:, 2] <= TOP_Z), np.minimum(Vn[:, 2], TOP_Z), Vn[:, 2])
    und = np.zeros(len(V), bool)
    ar0 = np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1)
    for _ in range(12):
        a1 = _dihedral(Vn, F, adj)
        bad = (a1 > FINISH_FOLD) & (a1 > a0 + 1e-6)
        ar1 = np.linalg.norm(np.cross(Vn[F[:, 1]] - Vn[F[:, 0]], Vn[F[:, 2]] - Vn[F[:, 0]]), axis=1)
        badf = (ar1 < 2e-4) & (ar1 < ar0)   # area guard (2x area): no face may collapse toward degenerate
        if not bad.any() and not badf.any():
            break
        vb = np.unique(np.concatenate([ae[bad].ravel(), au[bad].ravel(), F[badf].ravel()]))
        vb = vb[np.any(Vn[vb] != V[vb], axis=1)]
        if not len(vb):
            break
        Vn[vb] = V[vb]
        und[vb] = True
    return Vn, int(und.sum())


def finish(m, ctx, log):
    """r13 (finishing, user 2026-10-02): no redesign. (1) the degenerate face is collapsed; (2) local fold repair:
    the free vertices of every edge folded above FINISH_FIX_DIH, plus 2 rings, are relaxed (umbrella, lambda 0.5)
    until no fold above FINISH_FIX_DIH is left there, travel <= FINISH_FIX_TRAVEL; (3) a light Taubin smooth of every
    free vertex (FINISH_PAIRS lambda/mu pairs), travel <= FINISH_TRAVEL from the r12 surface (and <= FINISH_THIN x the
    gap to the opposite surface along the normal). Locked vertices (finish_locks) never move. Every step keeps the
    mesh watertight with the same genus, else it is not taken."""
    from scipy import sparse
    t0 = time.time()
    if SLIVER_COLLAPSE:
        # r15: the cuts leave thin pieces; every lock except the rim-top-roll / rear-wall one is hard here (a collapse moves a
        # vertex at most SLIVER_EMAX / 2, and must not thin the back under the pocket or move the user's locks)
        Lk = finish_locks(m.vertices, ctx)
        hard = np.zeros(len(m.vertices), bool)
        for k_, v_ in Lk.items():
            if not k_.startswith("rim top roll"):
                hard |= v_
        m = collapse_slivers(m, hard, log)
    m = fix_degenerate(m, log, emax=FINISH_DEG_EMAX)
    m = trimesh.Trimesh(m.vertices.copy(), m.faces.copy(), process=True)
    V0, F = m.vertices.copy(), m.faces
    g0, wt0, vol0 = m.euler_number, m.is_watertight, m.volume
    L = finish_locks(V0, ctx)
    lock = np.zeros(len(V0), bool)
    for k_, v_ in L.items():
        log.append("  lock %-62s %6d vertices" % (k_, int(v_.sum())))
        lock |= v_
    log.append("  locked (union) %d of %d vertices" % (lock.sum(), len(V0)))
    E = m.edges_unique
    A = sparse.coo_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])),
                          shape=(len(V0), len(V0))).tocsr()
    deg = np.asarray(A.sum(1)).ravel()
    adj, ae, au = m.face_adjacency, m.face_adjacency_edges, m.face_adjacency_unshared
    free = ~lock
    # gap to the opposite surface along +-normal (thin walls, air slits), within 1 mm: face centres in a 45 deg cone
    # about the vertex normal whose own normal faces the other way. It caps the travel there
    vn = m.vertex_normals
    gap = np.full(len(V0), np.inf)
    fc_, fn_ = m.triangles_center, m.face_normals
    dq, iq = cKDTree(fc_).query(V0, k=64, distance_upper_bound=1.0)
    okq = np.isfinite(dq)
    iq = np.where(okq, iq, 0)
    rel = fc_[iq] - V0[:, None, :]
    cosn = np.abs((rel * vn[:, None, :]).sum(2)) / np.maximum(dq, 1e-9)
    opp = (fn_[iq] * vn[:, None, :]).sum(2) < -0.3
    hit = okq & opp & (cosn > 0.707) & (dq > 0.01)
    gap = np.where(hit.any(1), np.where(hit, dq, np.inf).min(1), np.inf)
    log.append("  thin-wall cap: %d vertices with an opposite surface within 1 mm (min gap %.3f)"
               % (int(np.isfinite(gap).sum()), gap[np.isfinite(gap)].min() if np.isfinite(gap).any() else np.nan))
    # (2) local fold repair
    a = _dihedral(V0, F, adj)
    seed = np.zeros(len(V0), bool)
    seed[ae[a > FINISH_FIX_DIH].ravel()] = True
    zone = seed.copy()
    for _ in range(2):
        zone |= (A @ zone.astype(float)) > 0
    zone &= free
    log.append("  fold repair: %d folds > %.0f, seed %d vertices (%d locked), zone %d free vertices"
               % (int((a > FINISH_FIX_DIH).sum()), FINISH_FIX_DIH, seed.sum(), int((seed & lock).sum()), zone.sum()))
    capv = np.where(zone, FINISH_FIX_TRAVEL, FINISH_TRAVEL)
    nearS = np.zeros(len(V0), bool)
    for sx in (-1, 1):   # D43: the cusp at the wall end S (Z -4.2..0.7) may move up to FINISH_S_TRAVEL
        nearS |= (np.hypot(V0[:, 0] - ctx["S"][sx][0], V0[:, 1] - ctx["S"][sx][1]) < 2.5) & (V0[:, 2] > -5.0) & (V0[:, 2] < 1.0)
    capv = np.where(zone & nearS, FINISH_S_TRAVEL, capv)
    log.append("  D43 zone (2.5 mm of S, Z -5..1): %d free repair vertices, travel cap %.2f; fold seeds there %d, of them "
               "locked %d (%s)" % (int((zone & nearS).sum()), FINISH_S_TRAVEL, int((seed & nearS).sum()),
                                   int((seed & nearS & lock).sum()),
                                   ", ".join("%s %d" % (k_.split(" (")[0], int((seed & nearS & v_).sum())) for k_, v_ in L.items())))
    capv = np.minimum(capv, FINISH_THIN * gap)   # everywhere (also in the repair zone). The min slit-ray gap 0.022 that
    # prompted it is at (-83.8, 74.0, -11.0) (D47), not at the handle tip, and this cap did not change it
    V = V0.copy()
    zedge = zone[ae].any(1)
    for it in range(40):
        nf = int(((_dihedral(V, F, adj) > FINISH_FIX_DIH) & zedge).sum())
        if nf == 0:
            break
        V, nu = _relax(V, V0, A, deg, zone, 0.5, capv, F, adj, ae, au)
    a1 = _dihedral(V, F, adj)
    log.append("  fold repair: %d iterations, folds > %.0f in the zone %d -> %d (all: %d -> %d), zone travel max %.3f"
               % (it, FINISH_FIX_DIH, int(((a > FINISH_FIX_DIH) & zedge).sum()), int(((a1 > FINISH_FIX_DIH) & zedge).sum()),
                  int((a > FINISH_FIX_DIH).sum()), int((a1 > FINISH_FIX_DIH).sum()),
                  np.linalg.norm(V - V0, axis=1)[zone].max() if zone.any() else 0.0))
    # (3) light Taubin smooth of the free surface
    # normal component only, except on the 1-ring of edges sharper than FINISH_FOLD (slivers whose normals are noise:
    # they need the tangential part to relax; measured on r12, normal-only left 736 of 1545 such edges, full 182)
    sharp = np.zeros(len(V0), bool)
    sharp[ae[_dihedral(V, F, adj) > FINISH_FOLD].ravel()] = True
    sharp |= (A @ sharp.astype(float)) > 0
    log.append("  smooth: full umbrella (tangential too) on %d free vertices near edges > %.0f deg, normal-only on the rest"
               % (int((sharp & free).sum()), FINISH_FOLD))
    nund = 0
    for _ in range(FINISH_PAIRS):
        for lam in (FINISH_LAMBDA, FINISH_MU):
            V, nu = _relax(V, V0, A, deg, free, lam, capv, F, adj, ae, au, normal_only=~sharp)
            nund += nu
    out = trimesh.Trimesh(V, F, process=False)
    tr = np.linalg.norm(V - V0, axis=1)
    sm = free & ~zone
    ok = out.is_watertight == wt0 and out.is_winding_consistent and out.euler_number == g0 and out.volume > 0
    log.append("  smooth: %d Taubin pairs (%.2f / %.2f), %d vertex moves undone by the fold check (> %.0f deg)"
               % (FINISH_PAIRS, FINISH_LAMBDA, FINISH_MU, nund, FINISH_FOLD))
    log.append("  travel, smoothed vertices (%d): max %.4f p99 %.4f p50 %.4f | repair zone (%d): max %.4f p99 %.4f | "
               "locked: max %.6f" % (sm.sum(), tr[sm].max(), np.percentile(tr[sm], 99), np.median(tr[sm]), zone.sum(),
                                    tr[zone].max() if zone.any() else 0, np.percentile(tr[zone], 99) if zone.any() else 0,
                                    tr[lock].max()))
    dn = ((V - V0) * vn).sum(1)
    log.append("  normal travel of the smoothed vertices (+ out): p01 %.4f p50 %.4f p99 %.4f mean %.5f | volume %.1f -> "
               "%.1f mm3 (%+.1f) | max z %.4f | dihedral > 150: %d -> %d, > 120: %d -> %d | %.1f s"
               % (np.percentile(dn[sm], 1), np.median(dn[sm]), np.percentile(dn[sm], 99), dn[sm].mean(), vol0, out.volume,
                  out.volume - vol0, V[:, 2].max(), int((a > 150).sum()), int((_dihedral(V, F, adj) > 150).sum()),
                  int((a > 120).sum()), int((_dihedral(V, F, adj) > 120).sum()), time.time() - t0))
    if not ok:
        log.append("  finishing NOT taken: watertight %s winding %s euler %d vs %d" % (
            out.is_watertight, out.is_winding_consistent, out.euler_number, g0))
        return m
    return out


# ================================================================ r14: trim and rolled edges (before finish)
def _first_hit_h(mesh, axis, sgn, U, V_, uax, vax):
    """Coordinate along `axis` of the first surface hit by rays that start at sgn * 300 on that axis and travel toward
    -sgn; the plan coordinates are (U, V_) on axes (uax, vax). nan where no hit."""
    n = U.size
    O = np.zeros((n, 3))
    O[:, uax], O[:, vax], O[:, axis] = U.ravel(), V_.ravel(), sgn * 300.0
    D = np.zeros((n, 3))
    D[:, axis] = -sgn
    h = first_hits(mesh, O, D)
    return np.array([np.nan if q is None else q[0][axis] for q in h]).reshape(U.shape)


def roll_cut(body, axis, sgn, u_rng, v_rng, step, rfun, plane_w=None, what="", log=None, tau=None):
    """r14: roll one convex edge with a rolling ball, as a height-field cut (the r12 top_cut operator, ball_open).
    Seen from the +sgn side of `axis` the surface is w = sgn * (first-hit coordinate) with material below it. The skin
    is sampled on a (u, v) grid (the other two axes, in ascending order, offset by JIT so no ray sits on a vertex),
    plane_w (optional) caps it (a plane cut), nodes without a hit are a cliff (the silhouette). rfun(U, V, g, ok, dcl)
    returns the roll radius per node (0 = leave alone; dcl = plan distance to the cliff). The cut removes everything
    above the opened surface; where it would take off less than ROLL_TAU it lifts off the skin, and the cliff nodes
    carry the nearest inside value (no gouge, no lip at the wall). Returns (body, info)."""
    uax, vax = [k for k in range(3) if k != axis]
    us = np.arange(u_rng[0], u_rng[1] + 1e-9, step) + JIT[0]
    vs = np.arange(v_rng[0], v_rng[1] + 1e-9, step) + JIT[1]
    U, V_ = np.meshgrid(us, vs, indexing="ij")
    g_skin = sgn * _first_hit_h(body, axis, sgn, U, V_, uax, vax)
    ok = np.isfinite(g_skin)
    if not ok.any():
        raise RuntimeError("roll_cut %s: no skin hit" % what)
    ie = ndimage.distance_transform_edt(~ok, return_distances=False, return_indices=True)
    gf_skin = g_skin[tuple(ie)]                                  # nearest-filled skin
    g0 = gf_skin if plane_w is None else np.minimum(gf_skin, plane_w)   # target before rounding
    dcl = ndimage.distance_transform_edt(ok) * step
    r = rfun(U, V_, g0, ok, dcl)
    if r.max() <= 1e-9:
        return body, dict(removed=0.0, rmax=0.0, active=0)
    gopen = np.where(ok, g0, g0[ok].min() - 60.0)               # cliff outside the silhouette
    R_ = np.arange(0.0, r.max() + 1e-9, 0.5)
    if R_[-1] < r.max() - 1e-9:
        R_ = np.append(R_, r.max())
    O_ = np.stack([ball_open(gopen, rr, step) for rr in R_])
    j = np.clip(np.searchsorted(R_, r, side="right") - 1, 0, len(R_) - 2)
    f = np.clip((r - R_[j]) / (R_[j + 1] - R_[j]), 0.0, 1.0)
    I_, J_ = np.indices(g0.shape)
    ho = O_[j, I_, J_] * (1.0 - f) + O_[j + 1, I_, J_] * f
    tau = ROLL_TAU if tau is None else tau
    dev = gf_skin - ho                                           # > 0: material taken off
    w_air = 1.0 - ramp(dev / tau)
    Hc = ho + w_air * (np.maximum(gf_skin, ho) + 1.0 - ho)
    Hc = np.where(ok, Hc, Hc[tuple(ie)])                         # outside the silhouette: continue the inside value
    active = ok & (dev > tau)
    if not active.any():
        return body, dict(removed=0.0, rmax=float(r.max()), active=0)
    hf = hf_solid(us, vs, Hc, np.full(Hc.shape, max(float(Hc.max()), float(gf_skin.max())) + 5.0))
    V3 = np.zeros_like(hf.vertices)
    V3[:, uax], V3[:, vax], V3[:, axis] = hf.vertices[:, 0], hf.vertices[:, 1], sgn * hf.vertices[:, 2]
    F3 = hf.faces
    M3 = np.zeros((3, 3))
    M3[uax, 0], M3[vax, 1], M3[axis, 2] = 1.0, 1.0, float(sgn)   # (u, v, w) -> (x, y, z)
    if np.linalg.det(M3) < 0:   # reflected: restore the outward winding
        F3 = F3[:, [0, 2, 1]]
    cut = trimesh.Trimesh(V3, F3, process=True)
    v_ = body.volume
    body = boolean("difference", body, cut, what)
    info = dict(removed=v_ - body.volume, rmax=float(r.max()), active=int(active.sum()), dev_max=float(dev[ok].max()),
                nodes=int(Hc.size), faces=len(cut.faces))
    if log is not None:
        log.append("  %s: grid %d x %d at %.3f, roll r <= %.2f, %d active nodes, max take-off %.3f mm, removed %.2f mm3"
                   % (what, len(us), len(vs), step, r.max(), info["active"], info["dev_max"], info["removed"]))
    return body, info


def roll_fields(body, axis, sgn, u_rng, v_rng, step, rfun):
    """The skin height field seen from the +sgn side of `axis` (w = sgn * first-hit coordinate, material below it), its
    ball opening for the radius map rfun, and delta = skin - opening (>= 0, the take-off), all on one (u, v) grid."""
    uax, vax = [k for k in range(3) if k != axis]
    us = np.arange(u_rng[0], u_rng[1] + 1e-9, step) + JIT[0]
    vs = np.arange(v_rng[0], v_rng[1] + 1e-9, step) + JIT[1]
    U, V_ = np.meshgrid(us, vs, indexing="ij")
    g = sgn * _first_hit_h(body, axis, sgn, U, V_, uax, vax)
    ok = np.isfinite(g)
    if not ok.any():
        raise RuntimeError("roll_fields: no skin hit")
    # single ray misses inside the part (between triangles) are not cliffs: a pinhole of cliff made the opening dive
    # 50 mm at its neighbours (r14 run 1). Close one-node holes; nodes filled this way take the nearest skin value.
    okc = ndimage.binary_closing(np.pad(ok, 2, mode="edge"), structure=np.ones((3, 3), bool))[2:-2, 2:-2]
    ie = ndimage.distance_transform_edt(~ok, return_distances=False, return_indices=True)
    gf = g[tuple(ie)]
    ok = okc
    dcl = ndimage.distance_transform_edt(ok) * step
    r = rfun(U, V_, gf, ok, dcl)
    ho = gf.copy()
    if r.max() > 1e-9:
        gopen = np.where(ok, gf, gf[ok].min() - 60.0)
        R_ = np.arange(0.0, r.max() + 1e-9, 0.5)
        if R_[-1] < r.max() - 1e-9:
            R_ = np.append(R_, r.max())
        O_ = np.stack([ball_open(gopen, rr, step) for rr in R_])
        j = np.clip(np.searchsorted(R_, r, side="right") - 1, 0, len(R_) - 2)
        f = np.clip((r - R_[j]) / (R_[j + 1] - R_[j]), 0.0, 1.0)
        I_, J_ = np.indices(gf.shape)
        ho = O_[j, I_, J_] * (1.0 - f) + O_[j + 1, I_, J_] * f
    # a feature thinner than the ball (a 0.25 mm tab where the rear wall steps by 0.2 mm at x 56) is not rolled, it is
    # opened away: the take-off there is capped at 1.5 r so the roll never shaves more than it was asked to
    delta = np.where(ok, np.minimum(np.maximum(gf - ho, 0.0), 1.5 * r), 0.0)
    return dict(us=us, vs=vs, g=gf, ok=ok, ho=ho, delta=delta, r=r, uax=uax, vax=vax)


def roll_warp(body, axis, sgn, u_rng, v_rng, step, rfun, lmax, zone_fn, what, log, wall=False, dil=1.5,
              delta_fn=None, gate=False, zthr=0.03):
    """r14 (D49): the rolled edge as a vertex displacement, not a boolean. A cut against the skin leaves a ragged
    tangent junction and ~140 extra folds (r14 first try, roll_cut, tau 0.02-0.3), and the finish smooth then cannot
    act on them. Here the mesh is refined (crack-free, edges <= lmax where the roll acts) and every vertex moves along
    `axis` by delta(u, v) = skin - opening, so the new surface is the ball opening and the topology is unchanged.
    zone_fn(points) -> bool: which points may be refined / moved at all (the grid is a plan field, the body has other
    material over the same (u, v)).
    wall=True (D50 / D51): the edge is the crease between this skin and a vertical wall. Only vertices in the top layer
    of the skin (within 0.25 of the grid skin) move, the wall's own other vertices stay, refinement splits only
    skin-layer edges (no closure), and the crease vertices move by the tangent length r * tan(turn / 2) of their own
    skin / wall corner (a grid cannot carry the vertical tangent of the arc at the wall).
    delta_fn(fields) -> signed displacement field along `axis` (r14 P4, the underside fixes: z' - z for sgn = -1),
    replacing the ball opening's; gate=True moves / refines only vertices within 0.3 of the grid skin (the surface
    the field was measured on, not the other surfaces over the same plan); zthr = |delta| that opens the zone."""
    from scipy.interpolate import RegularGridInterpolator as RGI
    fl = roll_fields(body, axis, sgn, u_rng, v_rng, step, rfun)
    if delta_fn is not None:
        fl["delta"] = delta_fn(fl)
    us, vs, delta = fl["us"], fl["vs"], fl["delta"]
    uax, vax = fl["uax"], fl["vax"]
    if np.abs(delta).max() <= 1e-6:
        return body, dict(moved=0, dmax=0.0, flipped=0, watertight=True)
    fd = RGI((us, vs), delta, bounds_error=False, fill_value=0.0)
    fg = RGI((us, vs), fl["g"], bounds_error=False, fill_value=np.nan)
    fr = RGI((us, vs), fl["r"], bounds_error=False, fill_value=0.0)
    # refinement zone: where the roll acts (delta > 0) dilated by dil mm
    zone = ndimage.binary_dilation(np.abs(delta) > zthr, iterations=int(np.ceil(dil / step)))   # (0.001: also took the
    #   already-rolled 3 mm edge at the top plane, whose huge flat triangles then never reached lmax)
    fz = RGI((us, vs), zone.astype(float), method="nearest", bounds_error=False, fill_value=0.0)
    V, F = body.vertices.copy(), body.faces.copy()
    n0 = len(F)

    def depth(P3):      # distance of a point from the grid skin (w), either side (a long edge passing above it is not on it)
        return np.abs(fg(P3[:, [uax, vax]]) - sgn * P3[:, axis])

    def want(mp, L):
        k = (L > lmax) & (L < 6.0) & (fz(mp[:, [uax, vax]]) > 0.5) & zone_fn(mp)
        if wall:
            k &= depth(mp) < 0.2
        if gate:
            k &= depth(mp) < 0.3
        return k

    V, F, st = refine_local(V, F, want, time.time() + 240.0, 600000, iters=ROLL_ITERS if (wall or gate) else 60,
                            closure=False if wall else True)
    P = V[:, [uax, vax]]
    dv = np.where(zone_fn(V), fd(P), 0.0)
    if gate:
        dv = np.where(depth(V) < 0.3, dv, 0.0)
    nwall = 0
    if wall:
        fnr = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
        fnr /= np.maximum(np.linalg.norm(fnr, axis=1), 1e-30)[:, None]
        wf = np.abs(fnr[:, axis]) < 0.3                         # wall faces
        sf = fnr[:, axis] * sgn > 0.3                           # faces of this skin
        nw, ns = np.zeros_like(V), np.zeros_like(V)
        for k in range(3):
            np.add.at(nw, F[wf, k], fnr[wf])
            np.add.at(ns, F[sf, k], fnr[sf])
        has = (np.linalg.norm(nw, axis=1) > 1e-9) & (np.linalg.norm(ns, axis=1) > 1e-9)
        cosT = (nw * ns).sum(1) / np.maximum(np.linalg.norm(nw, axis=1) * np.linalg.norm(ns, axis=1), 1e-30)
        turn = np.arccos(np.clip(cosT, -1.0, 1.0))
        top = depth(V) < 0.25
        crease = has & top & zone_fn(V) & (fr(P) > 1e-4)    # only where the roll is asked for (r14 run 2: without it the
        #   crease-chain smoothing carried take-off 0.7 mm onto a pocket floor edge 9 mm from the rim)
        tl = fr(P) * np.tan(0.5 * np.minimum(turn, np.radians(100.0)))   # (a 90 deg corner: r; capped at 100 deg turn)
        # the corner angle differs from vertex to vertex (facet noise): smooth the take-off along the crease chain, else
        # the wall's top edge is a sawtooth (r14 first render: vertical needles on the rim wall)
        from scipy import sparse
        Eu = np.unique(np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), axis=1), axis=0)
        ce = crease[Eu[:, 0]] & crease[Eu[:, 1]]
        A = sparse.coo_matrix((np.ones(2 * int(ce.sum())), (np.r_[Eu[ce, 0], Eu[ce, 1]], np.r_[Eu[ce, 1], Eu[ce, 0]])),
                              shape=(len(V), len(V))).tocsr()
        dg = np.asarray(A.sum(1)).ravel()
        for _ in range(ROLL_SMOOTH):
            tl = np.where(crease & (dg > 0), 0.5 * tl + 0.5 * (A @ tl) / np.maximum(dg, 1), tl)
        dv = np.where(top, dv, 0.0)
        dv = np.where(crease, tl, dv)
        nwall = int(crease.sum())
    mov = np.abs(dv) > 1e-6
    V2 = V.copy()
    V2[:, axis] = V[:, axis] - sgn * dv
    m = trimesh.Trimesh(V2, F, process=False)
    # fold / flip check: no face may flip against its own refined original
    n_old = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    n_new = np.cross(V2[F[:, 1]] - V2[F[:, 0]], V2[F[:, 2]] - V2[F[:, 0]])
    flipped = int(((n_old * n_new).sum(1) < 0).sum())
    info = dict(moved=int(mov.sum()), dmax=float(np.abs(dv).max()), faces=(n0, len(F)), refine=st, flipped=flipped,
                watertight=m.is_watertight, winding=m.is_winding_consistent, crease=nwall)
    if log is not None:
        log.append("  %s: grid %d x %d at %.3f, roll r <= %.2f | refined %d -> %d faces (%s) | %d vertices moved (%d on the "
                   "wall crease), max %.3f | flipped faces %d | watertight %s"
                   % (what, len(us), len(vs), step, fl["r"].max(), n0, len(F), st, info["moved"], nwall, info["dmax"],
                      flipped, m.is_watertight))
    return m, info


def retri_cap(body, y0, h, log):
    """The plane cut leaves each end face as a planar polygon triangulated with only its outline vertices (long thin
    triangles: bisecting those made 4260 faces < 1e-4 mm2 and 342 folds in the first r14 try). Replace every such cap
    by a Delaunay triangulation of its outline vertices plus an interior hex grid of spacing h (kept 0.8 h clear of
    the outline), so the roll has vertices to move. The outline vertices are the old ones: the skin is untouched."""
    from scipy.spatial import Delaunay
    V, F = body.vertices, body.faces
    cap = np.all(np.abs(V[F][:, :, 1] - y0) < 1e-4, axis=1)
    if not cap.any():
        raise RuntimeError("retri_cap: no cap faces at y %.3f" % y0)
    Fc, Fo = F[cap], F[~cap]
    E = np.sort(np.vstack([Fc[:, [0, 1]], Fc[:, [1, 2]], Fc[:, [2, 0]]]), axis=1)
    u, cnt = np.unique(E, axis=0, return_counts=True)
    bnd = u[cnt == 1]
    nb = {}
    for a, b in bnd:
        nb.setdefault(a, []).append(b)
        nb.setdefault(b, []).append(a)
    if any(len(v) != 2 for v in nb.values()):
        raise RuntimeError("retri_cap: outline vertices with other than 2 boundary edges")
    seen, loops = set(), []
    for s in nb:
        if s in seen:
            continue
        lp, prev, cur = [s], None, s
        while True:
            seen.add(cur)
            nxt = [q for q in nb[cur] if q != prev][0]
            if nxt in seen:
                break
            lp.append(nxt)
            prev, cur = cur, nxt
        loops.append(np.array(lp))
    Vn, Fn = [V], [Fo]
    nv = len(V)
    bset = set(map(tuple, bnd))
    for lp in loops:
        P = V[lp][:, [0, 2]]
        poly = Polygon(P)
        if not poly.is_valid or poly.area < 1.0:
            raise RuntimeError("retri_cap: outline polygon invalid / tiny (area %.2f)" % poly.area)
        inner = poly.buffer(-0.8 * h)
        x0_, z0_, x1_, z1_ = poly.bounds
        pts = []
        for i, zz in enumerate(np.arange(z0_, z1_ + h, h * 0.8660254)):
            xs_ = np.arange(x0_ + (0.5 * h if i % 2 else 0.0), x1_ + h, h)
            pts += [(xx, zz) for xx in xs_]
        pts = np.array(pts)
        pts = pts[shapely.contains_xy(inner, pts[:, 0], pts[:, 1])] if len(pts) else pts
        Pall = np.vstack([P, pts]) if len(pts) else P
        tri = Delaunay(Pall).simplices
        cen = Pall[tri].mean(axis=1)
        tri = tri[shapely.contains_xy(poly, cen[:, 0], cen[:, 1])]
        ids = np.concatenate([lp, nv + np.arange(len(pts))]).astype(int)
        T = ids[tri]
        # the outline edges must all be edges of the triangulation
        te = set(map(tuple, np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), axis=1).tolist()))
        lps = set(lp.tolist())
        miss = [e for e in bset if e[0] in lps and e not in te]
        if miss:
            raise RuntimeError("retri_cap: %d outline edges lost in the Delaunay" % len(miss))
        Vi = np.column_stack([pts[:, 0], np.full(len(pts), y0), pts[:, 1]]) if len(pts) else np.zeros((0, 3))
        Vn.append(Vi)
        Fn.append(T)
        nv += len(pts)
    Vall = np.vstack(Vn)
    Fall = np.vstack(Fn)
    # outward normal of the end face is -y: flip the new triangles that face +y
    isnew = np.arange(len(Fall)) >= len(Fo)
    nrm = np.cross(Vall[Fall[:, 1]] - Vall[Fall[:, 0]], Vall[Fall[:, 2]] - Vall[Fall[:, 0]])[:, 1]
    flip = isnew & (nrm > 0)
    Fall[flip] = Fall[flip][:, [0, 2, 1]]
    m = trimesh.Trimesh(Vall, Fall, process=False)
    log.append("  cap at y %.2f re-triangulated: %d cap faces -> %d (hex %.2f, %d interior points), watertight %s, winding %s, "
               "euler %d" % (y0, int(cap.sum()), int(isnew.sum()), h, nv - len(V), m.is_watertight, m.is_winding_consistent,
                             m.euler_number))
    return m


def trim_handles(body, log):
    """D49 (user): everything with y < TRIM_Y goes, on both handles (one plane), and the new edge is rolled with a
    TRIM_R rolling ball. The plane cut is exact (a box difference). Seen from -y the trimmed handle is a height field
    f(x, z) = first-hit y (the end face is the plateau f = TRIM_Y); w = -y. The roll is applied as a vertex
    displacement along y (roll_warp) within TRIM_BAND of the plane."""
    big = trimesh.creation.box(extents=(BIG, 100.0, BIG))
    big.apply_translation((0.0, TRIM_Y - 50.0, 0.0))
    body = boolean("difference", body, big, "trim handles at y %.1f" % TRIM_Y)
    log.append("  trim plane y %.2f: both handles cut, y min now %.4f" % (TRIM_Y, body.bounds[0][1]))
    body = retri_cap(body, TRIM_Y, TRIM_CAP_H, log)
    cap = -TRIM_Y

    def rfun(U, V_, g0, ok, dcl):
        return TRIM_R * ramp((g0 - (cap - TRIM_BAND - 0.5)) / 0.5)

    for sgn_x, rng in ((-1, (-112.0, -72.0)), (1, (72.0, 112.0))):
        body, info = roll_warp(body, 1, -1, rng, (-45.0, 15.0), TRIM_STEP, rfun, TRIM_LMAX,
                               lambda p: p[:, 1] < TRIM_Y + TRIM_BAND + 1.5,
                               "trim handle %s roll %.1f" % ("L" if sgn_x < 0 else "R", TRIM_R), log)
        if info["moved"] == 0 or not info["watertight"] or info["flipped"] > 20:
            raise RuntimeError("trim roll %s failed: %s" % (sgn_x, info))
    return body


def retessellate_rear(body, log):
    """r15 P2 (D60): crack-free longest-edge refinement (refine_local with closure) of every edge longer than RETRI_L in the
    rear-wall zone RETRI_ZONE = (|x| max, y min, z max, z min). The wall strip is 2.3 mm high and 150 mm long and was
    triangulated with a few 60-140 mm triangles; longest-edge bisection halves the long edge each pass and keeps the angles."""
    xm, y0, zt, zb = RETRI_ZONE

    def want(mp, L):
        return (L > RETRI_L) & (np.abs(mp[:, 0]) <= xm) & (mp[:, 1] >= y0) & (mp[:, 2] <= zt) & (mp[:, 2] >= zb)

    n0 = len(body.faces)
    V, F, st = refine_local(body.vertices.copy(), body.faces.copy(), want, time.time() + 240.0, 600000, iters=60, closure=True)
    m = trimesh.Trimesh(V, F, process=False)
    el = np.linalg.norm(V[F] - V[np.roll(F, 1, axis=1)], axis=2).max(1)
    cen = V[F].mean(1)
    zone = (np.abs(cen[:, 0]) <= xm) & (cen[:, 1] >= y0) & (cen[:, 2] <= zt) & (cen[:, 2] >= zb)
    log.append("  P2 rear zone re-tessellated: faces %d -> %d (%s), longest edge in the zone %.2f (p99 %.2f), watertight %s, euler %d"
               % (n0, len(F), st, el[zone].max(), np.percentile(el[zone], 99), m.is_watertight, m.euler_number))
    if not m.is_watertight:
        raise RuntimeError("retessellate_rear broke the mesh")
    return m


def bar_back_fill(body, log):
    """r15 P4 (D56): the back under the pocket reads 3.4256 on a 0.05 mm window at (-65.05, -8.70) (3.499 on r13's coarse
    grid). The underside in the strip x -67..-63, y -9..-8 is lowered by BACK_FILL (fill, never cut), ramped out over 0.8 mm
    on all sides, as a vertex displacement gated to the underside layer (the underside_fix mechanism)."""
    def fn(fl):
        U, V_ = np.meshgrid(fl["us"], fl["vs"], indexing="ij")
        # full (1) inside x -67..-63, y -9..-8; ramps 0.8 mm wide just OUTSIDE the strip (zero at x -62.2: the bottom-bar
        # strip lock begins at |x| 62; the first version ramped inside the strip and moved a lock vertex by 0.035)
        w = ramp((U + 67.8) / 0.8) * (1.0 - ramp((U + 63.0) / 0.8)) * ramp((V_ + 9.8) / 0.8) * (1.0 - ramp((V_ + 8.0) / 0.8))
        return np.where(fl["ok"], -BACK_FILL * w, 0.0)

    zero = lambda U, V_, g0, ok, dcl: np.zeros(U.shape)
    body, info = roll_warp(body, 2, -1, (-70.0, -60.0), (-12.0, -5.0), 0.15, zero, 0.45, lambda p: np.ones(len(p), bool),
                           "P4 back fill x -67..-63 y -9..-8 by %.2f" % BACK_FILL, log, delta_fn=fn, gate=True, zthr=0.01, dil=0.5)
    if not info["watertight"] or info["flipped"] > 50:
        raise RuntimeError("bar_back_fill failed: %s" % info)
    return body


def _earclip(P):
    """Ear clipping of a simple polygon given CCW as an (n, 2) array; returns triangles as index triples (CCW)."""
    idx = list(range(len(P)))
    tris = []

    def cross(o, a, b):
        return (P[a][0] - P[o][0]) * (P[b][1] - P[o][1]) - (P[a][1] - P[o][1]) * (P[b][0] - P[o][0])

    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            if cross(i0, i1, i2) <= 1e-12:
                continue
            inside = False
            for j in idx:
                if j in (i0, i1, i2):
                    continue
                if cross(i0, i1, j) >= -1e-12 and cross(i1, i2, j) >= -1e-12 and cross(i2, i0, j) >= -1e-12:
                    inside = True
                    break
            if not inside:
                tris.append((i0, i1, i2))
                idx.pop(k)
                break
        else:
            raise RuntimeError("ear clipping failed")
    tris.append((idx[0], idx[1], idx[2]))
    return tris


def bar_edge_cut(body, log):
    """r15 P2 (D60 / D61): the bar's rear-bottom edge (the 90 deg crease between the rear wall y ~ 78.55 and the underside)
    rolled over its WHOLE length, as one boolean cut. Per section x (every BAR_DX): the wall plane y_w, the underside plane
    through the crease (slope s) and the wall height h are measured on the mesh (rays); the cutter is the region between a
    circle of radius r and the exterior corner, r = min(BAR_ROLL_R, BAR_WALL_FRAC h) tapering to 0 over BAR_TAPER[1] beyond
    |x| = BAR_TAPER[0] (floor BAR_RMIN at the loft ends). The circle is moved BAR_EPS into the corner, so it crosses both
    planes at acos(1 - eps/r) (about 16 deg for r 1) instead of tangentially: no sliver-thin junction (the tangent junction is
    what made r14's height-field roll_cut ragged). The sections are lofted; the jog of the rear face at x 56.2 / 66.4 is
    followed to the section spacing."""
    # section stations: BAR_DX apart where the parameters are smooth (|x| < 50), 0.5 in the taper / underside rise, 0.125 at the
    # two jogs of the rear face. Every station puts a vertex on the cut line of each old face it crosses; at 0.25 mm that was
    # 600 vertices per line and 1 360 new faces with a min angle < 0.2 deg (the old faces are 140 mm long triangles)
    xs = np.unique(np.round(np.concatenate([
        np.arange(-50.0, 50.0 + 1e-9, BAR_DX), np.arange(-BAR_X_END, -50.0, 0.5), np.arange(50.0, BAR_X_END + 1e-9, 0.5),
        np.arange(55.5, 57.5 + 1e-9, 0.125), np.arange(65.5, 67.5 + 1e-9, 0.125), [-BAR_X_END, BAR_X_END]]), 4))
    n = len(xs)
    jit = JIT[0]

    def hit(O, D, ax):
        loc, ri, _ = body.ray.intersects_location(np.asarray(O, float), np.asarray(D, float), multiple_hits=False)
        out = np.full(len(O), np.nan)
        out[ri] = loc[:, ax]
        return out

    up = np.tile([0.0, 0.0, 1.0], (n, 1))
    toward = np.tile([0.0, -1.0, 0.0], (n, 1))
    x_ = xs + jit
    zu0 = hit(np.column_stack([x_, np.full(n, 77.9), np.full(n, -300.0)]), up, 2)
    yw = hit(np.column_stack([x_, np.full(n, 120.0), zu0 + 0.5]), toward, 1)
    za = hit(np.column_stack([x_, yw - 0.1, np.full(n, -300.0)]), up, 2)
    zb = hit(np.column_stack([x_, yw - 0.6, np.full(n, -300.0)]), up, 2)
    s = (za - zb) / 0.5
    zc = za + s * 0.1
    lev = np.arange(0.1, 3.6, 0.1)
    Y = np.full((n, len(lev)), np.nan)
    for j, dz in enumerate(lev):
        Y[:, j] = hit(np.column_stack([x_, np.full(n, 120.0), zc + dz]), toward, 1)
    # the wall may be tilted (the recess at x 56-66 leans 0.1 per mm): a line through the wall hits at dz 0.3 and 0.9 is the
    # wall plane; the wall ends where a hit leaves it by 0.04
    j3, j9 = int(round(0.3 / 0.1)) - 1, int(round(0.9 / 0.1)) - 1
    ytilt = (Y[:, j9] - Y[:, j3]) / 0.6
    yref = Y[:, [j3]] + ytilt[:, None] * (lev[None, :] - 0.3)
    flat = np.abs(Y - yref) < 0.04
    run = np.cumprod(flat, axis=1).sum(1)
    h = run * 0.1 + 0.05
    bad = ~(np.isfinite(zc) & np.isfinite(yw) & np.isfinite(s) & np.isfinite(ytilt))
    if bad.any():
        raise RuntimeError("bar_edge_cut: %d sections without a measurement (x %s)" % (bad.sum(), xs[bad][:5]))
    r0 = np.minimum(BAR_ROLL_R, BAR_WALL_FRAC * h)
    r = np.maximum(r0 * (1.0 - ramp((np.abs(xs) - BAR_TAPER[0]) / BAR_TAPER[1])), BAR_RMIN)
    ywc = Y[:, j3] - 0.3 * ytilt                  # wall plane at the crease height
    ywr = Y[:, j3] + (r - 0.3) * ytilt            # wall plane at the height of the tangent point (z_c + r)
    bar_edge_cut.last = dict(xs=xs, h=h, r=r, yw=ywr, zc=zc, s=s)      # diagnostics
    # the arc runs from phi_n + th to -th, so th < -phi_n / 2 (phi_n = -90 deg + atan s: the steeper the underside rises toward
    # the rear, the smaller th): eps is limited so that the arc keeps at least 20 % of the corner angle
    phin0 = np.arctan2(-1.0, s)
    th_max = 0.8 * (-phin0) / 2.0
    eps = np.minimum(BAR_EPS, r * (1.0 - np.cos(th_max)))
    th = np.arccos(1.0 - eps / r)
    K = BAR_K
    sections = []
    # underside line: z_u(y) = zc + s (y - ywc); wall: the vertical line y = ywr. The circle is r - eps from each (moved eps
    # into the corner), so it crosses the wall at phi = -th and the underside at phi_n + th (phi_n = the underside normal).
    # The arc must START ON the real underside: where that is below the plane model the cut would leave a vertical step
    # (0.07 mm at x 0, where the underside rises to a ridge at y 78.0 and drops to the crease); one measured correction
    q_ = np.sqrt(1.0 + s ** 2)
    Cy_ = ywr - r + eps
    Cz_ = zc + s * (Cy_ - ywc) + (r - eps) * q_
    phin_ = np.arctan2(-1.0, s)
    Uy_ = Cy_ + r * np.cos(phin_ + th)
    zact = hit(np.column_stack([x_, Uy_, np.full(n, -300.0)]), up, 2)
    dz_ = np.where(np.isfinite(zact), np.clip(zact - (Cz_ + r * np.sin(phin_ + th)), -0.3, 0.3), 0.0)
    for k in range(n):
        q = q_[k]
        Cy = Cy_[k]
        Cz = Cz_[k] + dz_[k]
        phin = phin_[k]
        phi = np.linspace(phin + th[k], -th[k], K + 1)
        arc = np.column_stack([Cy + r[k] * np.cos(phi), Cz + r[k] * np.sin(phi)])
        Uz, Wz = arc[0, 1], arc[-1, 1]
        # the two ends of the arc lie ON the underside / the wall plane by construction. A vertex or an edge lying in a face to
        # within 1e-6 made 1 100 degenerate faces in the boolean. Moving the ends BAR_OUT out of the body (below the underside,
        # past the wall plane) puts the crossing 3.5 x BAR_OUT inside the planned point, along the arc. BAR_OUT 0.004 left
        # strips 14 um wide (slivers), 0.05 makes them 0.17 mm. (Tried instead: extending the chord 0.06 mm past each end,
        # which put a vertex of the cutter off the face but made MORE tiny faces: 640 < 1e-4 mm2 against 256.)
        arc[0, 1] -= BAR_OUT
        arc[-1, 0] += BAR_OUT
        P = np.vstack([arc, [[ywr[k] + 0.6, Wz], [ywr[k] + 0.6, Uz - 0.6], [arc[0, 0], Uz - 0.6]]])
        sections.append(P)
    S = np.array(sections)                                   # (n, M, 2) in (y, z)
    M = S.shape[1]
    area2 = np.sum(S[0, :, 0] * np.roll(S[0, :, 1], -1) - np.roll(S[0, :, 0], -1) * S[0, :, 1])
    if area2 < 0:                                             # make the section CCW in (y, z)
        S = S[:, ::-1, :]
    V3 = np.zeros((n * M, 3))
    for k in range(n):
        V3[k * M:(k + 1) * M, 0] = xs[k]
        V3[k * M:(k + 1) * M, 1:] = S[k]
    F = []
    for k in range(n - 1):
        for i in range(M):
            a, b = k * M + i, k * M + (i + 1) % M
            c, d = (k + 1) * M + (i + 1) % M, (k + 1) * M + i
            F += [(a, b, c), (a, c, d)]
    tri = _earclip(S[0])
    for (i0, i1, i2) in tri:
        F.append(((n - 1) * M + i0, (n - 1) * M + i1, (n - 1) * M + i2))      # +x cap (CCW in y, z)
        F.append((i0, i2, i1))                                                # -x cap
    cut = trimesh.Trimesh(V3, np.array(F), process=True)
    if not cut.is_watertight or cut.volume <= 0:
        raise RuntimeError("bar_edge_cut: cutter not watertight / inverted (vol %.3f)" % cut.volume)
    v_ = body.volume
    body = boolean("difference", body, cut, "bar rear-bottom edge cut")
    log.append("  P2 bar rear-bottom edge: %d sections (dx %.2f, |x| <= %.1f), wall height h %.2f..%.2f, r %.2f..%.2f (full for |x| <= %.0f, "
               "taper %.0f mm), eps %.2f, cutter %d faces | removed %.2f mm3 | watertight %s, euler %d, faces %d"
               % (n, BAR_DX, BAR_X_END, h.min(), h.max(), r.min(), r.max(), BAR_TAPER[0], BAR_TAPER[1], BAR_EPS, len(cut.faces),
                  v_ - body.volume, body.is_watertight, body.euler_number, len(body.faces)))
    return body


def roll_rim(body, log):
    """D50 / D51 (register r14): the two plan-trim edges r13 left sharp. D50: the rim top edge of the corner wall
    (|x| > 56, y > 58.5), D51: the bar's rear-bottom edge (|x| < 62, tapering to 0 at 70, y > 72). Each is a rolling-ball
    roll within a few mm of the silhouette, as a height-field cut (roll_cut); where the edge is already rolled (the
    3 mm top edge at the bar rear) the opening changes nothing."""

    body0 = body

    def wall_h(U, V_, ok, dcl, top_z, bot_z):
        """Height of the vertical wall at the silhouette, taken from the nearest edge node (the radii shrink to fit)."""
        th = top_z - bot_z
        E = ok & (dcl <= 1.6 * ROLL_STEP) & np.isfinite(th)
        if not E.any():
            return np.full(U.shape, np.inf)
        ie = ndimage.distance_transform_edt(~E, return_distances=False, return_indices=True)
        return th[tuple(ie)]

    def away(U, V_):
        """0 on the window / camera hole (locked), 1 clear of them."""
        cam = ramp((np.hypot(U, V_ - CAMERA_Y) - (CAMERA_HOLE_D / 2 + 3.5)) / 1.0)
        win = np.maximum(ramp((np.abs(U) - (WINDOW_W / 2 + 3.0)) / 1.0), ramp((V_ - (WIN_Y1 + 3.5)) / 1.0))
        return cam * win

    def rim_top(U, V_, g0, ok, dcl):
        zb = _first_hit_h(body0, 2, -1, U, V_, 0, 1)
        hw = wall_h(U, V_, ok, dcl, g0, zb)
        r = np.minimum(RIM_ROLL_R, RIM_WALL_FRAC * hw)
        # r15: the corner flank (|x| > 74, y < 72.5) is the scan's flared lower flank (30-35 deg off vertical, L as scanned);
        # a vertex displacement along z cannot roll its top edge (the crease vertex would leave the flank by 0.7 tl). The roll
        # acts only where the wall is vertical (the K wall y > 73, the rear wall)
        vert = np.maximum(ramp((V_ - 72.5) / 1.5), 1.0 - ramp((np.abs(U) - 72.0) / 2.0))
        return r * (1.0 - ramp((dcl - 1.4) / 0.8)) * ramp((V_ - 58.5) / 2.5) * away(U, V_) * vert

    # r15 P2 (failed approach, kept as retessellate_rear for the record): the r14 D51 roll was a vertex displacement of the
    # old rear face, which has no vertices to move at x 5..27 (60-140 mm triangles). Longest-edge refinement to 1 mm in the
    # zone (closure=True) took the zone from 2 902 to 162 946 faces (mean 0.007 mm2): the wall and the top-roll strips are
    # 142 mm long slivers, bisecting them gives 1 mm x 0.01 slivers, so the roll would have been fine but the mesh unusable.
    # D51 is therefore a boolean cut (bar_edge_cut) that does not need vertices on the old face.
    for what, args in (("D50 rim top edge", (2, 1, (-108.0, 108.0), (56.0, 81.0), ROLL_STEP, rim_top)),):
        if not D50_ON:
            break
        body, info = roll_warp(body, *args, ROLL_LMAX, lambda p: np.ones(len(p), bool), what, log, wall=True, dil=0.6)
        if info["moved"] == 0 or not info["watertight"] or info["flipped"] > 500:
            raise RuntimeError("%s failed: %s" % (what, info))
    if BAR_CUT_ON:
        body = bar_edge_cut(body, log)      # D51
    return body


def rim_outline_warp(body, log):
    """NOT USED (r14, tried and not kept; see rim_outline for what replaced it). Result on the cached r13 body: the
    z -11.5 outline ripple went from 3.0 / 14.0 mm (L / R, p-p > 0.2) to 0.0 / 0.0 and the half-width R - L at y 64..72 from
    +0.9..+1.6 to +0.02, but the sections at z -9.5 and -12.5 (skin / underside contours next to the wall) got worse (L 0.9
    -> 12.5 mm, R 1.3 -> 14.1 mm at z -9.5) and the lobe underside beside the corner was torn into shards (a horizontal
    shear of the skin and underside by up to 1.3 mm over 4 mm). A vertex warp of the wall cannot move the skin that is
    tied to it. Original docstring follows.
    D48 + D52 (register r14). The corner rim wall is not the clip K (that is smooth) but the scan lobe's own flank,
    so its plan outline carries the scan ripple (R: 0.43-0.55 mm p-p over 14 mm, wavelength ~2 mm) and the R lobe is
    1.3-1.95 mm wider than the L lobe at y 66-70. Both are fixed by one vertex warp, no boolean: the outline of the
    Z = RIM_SEC_Z section is smoothed (Gaussian, sigma RIM_SIGMA mm along the outline: the ripple is gone to 0.1 %),
    the R half is then moved onto the mirror of the smoothed L half (L is the scanned truth: user / register,
    'left as scanned'), and every vertex within a few mm of the wall moves horizontally with it (wall vertices snap onto
    the curve, so the wall is vertical; the skin and the underside fall off over max(2, 3 |move|) mm). Zone: |x| > 36,
    y > 61, z -15..-8, ramped in over 8 / 3 mm; nothing near the pocket, window, camera or pits."""
    from scipy.ndimage import gaussian_filter1d
    sec = body.section(plane_origin=[0, 0, RIM_SEC_Z], plane_normal=[0, 0, 1])
    loops = [np.asarray(q)[:, :2] for q in sec.discrete if len(q) > 20]
    outer = max(loops, key=lambda q: Polygon(q).area)
    d = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(outer, axis=0), axis=1))]
    ss = np.arange(0.0, d[-1] - 0.05, 0.1)
    raw = np.column_stack([np.interp(ss, d, outer[:, 0]), np.interp(ss, d, outer[:, 1])])
    sm = gaussian_filter1d(raw, RIM_SIGMA / 0.1, axis=0, mode="wrap")
    zw = ramp((np.abs(raw[:, 0]) - 36.0) / 8.0) * ramp((raw[:, 1] - 61.0) / 3.0)
    tgt = raw + zw[:, None] * (sm - raw)                                  # D48 for both halves
    Lz = (raw[:, 0] < 0) & (zw > 0.01)
    ML = tgt[Lz] * [-1.0, 1.0]                                            # the smoothed L half, mirrored
    kt = cKDTree(ML)
    Rz = (raw[:, 0] > 0) & (zw > 0.01)
    dm, im = kt.query(raw[Rz])
    ok = dm < 2.5
    ri = np.flatnonzero(Rz)
    tgt[ri[ok]] = raw[ri[ok]] + zw[ri[ok], None] * (ML[im[ok]] - raw[ri[ok]])   # D52: R follows the mirrored L
    off = tgt - raw
    V = body.vertices.copy()
    sel = (np.abs(V[:, 0]) > 34.0) & (V[:, 1] > 60.0) & (V[:, 2] <= -8.0) & (V[:, 2] >= -15.0)
    kr = cKDTree(raw)
    rho, j = kr.query(V[sel, :2])
    o = off[j]
    mag = np.linalg.norm(o, axis=1)
    Rf = np.maximum(2.0, 3.0 * mag)
    wgt = 1.0 - ramp(rho / Rf)
    # wall vertices (an incident face is vertical) snap onto the curve (r14 first try snapped only the ones within 0.1 of
    # the z -11.5 outline: the other z levels kept their own 0.1-0.25 zigzag, p-p 4-12 mm of > 0.2 at z -9.5 / -12.5);
    # the skin and underside vertices keep their offset from the curve
    fnz = body.face_normals[:, 2]
    wallv = np.zeros(len(V), bool)
    wallv[body.faces[np.abs(fnz) < 0.35].ravel()] = True
    # frame of the smoothed outline (the raw one's tangent swings +-45 deg on a 2 mm ripple): a vertex keeps its depth into
    # the part (d_n) and its place along the wall (d_t), a wall vertex has its depth set to 0 (it lies on the curve)
    tg = np.gradient(sm, axis=0)
    tg /= np.linalg.norm(tg, axis=1)[:, None] + 1e-12
    area2 = np.sum(sm[:, 0] * np.roll(sm[:, 1], -1) - np.roll(sm[:, 0], -1) * sm[:, 1])
    nn = np.column_stack([-tg[:, 1], tg[:, 0]]) * (1.0 if area2 > 0 else -1.0)      # inward normal
    rel = V[sel, :2] - raw[j]
    dn = (rel * nn[j]).sum(1)
    dtn = (rel * tg[j]).sum(1)
    dn = np.where(wallv[sel] & (rho < 1.2), 0.0, dn)
    full = tgt[j] + dn[:, None] * nn[j] + dtn[:, None] * tg[j]
    Vn = V.copy()
    Vn[np.flatnonzero(sel), :2] = V[sel, :2] + wgt[:, None] * (full - V[sel, :2])
    m = trimesh.Trimesh(Vn, body.faces, process=False)
    n_old = np.cross(V[body.faces[:, 1]] - V[body.faces[:, 0]], V[body.faces[:, 2]] - V[body.faces[:, 0]])
    n_new = np.cross(Vn[body.faces[:, 1]] - Vn[body.faces[:, 0]], Vn[body.faces[:, 2]] - Vn[body.faces[:, 0]])
    flipped = int(((n_old * n_new).sum(1) < 0).sum())
    mv = np.linalg.norm(Vn - V, axis=1)
    log.append("  D48 / D52 rim outline (z %.1f section, sigma %.2f, R onto mirrored L): outline %d pts, zone moves max %.3f, "
               "R-side offset max %.3f (median %.3f over %d pts) | %d vertices moved, max %.3f | flipped faces %d | watertight %s"
               % (RIM_SEC_Z, RIM_SIGMA, len(raw), np.linalg.norm(off, axis=1).max(), np.linalg.norm(off[ri[ok]], axis=1).max(),
                  np.median(np.linalg.norm(off[ri[ok]], axis=1)), int(ok.sum()), int((mv > 1e-6).sum()), mv.max(), flipped,
                  m.is_watertight))
    if not m.is_watertight or flipped > 200:
        raise RuntimeError("rim_outline broke the mesh (flipped %d, watertight %s)" % (flipped, m.is_watertight))
    return m


def rim_mirror(body, ctx, log):
    """r15 P1 (D58 / D59 / D62). R is 1.2-2.3 mm wider than the mirrored L at y 63-72 (scan asymmetry; L is the scanned
    truth). The R lobe's outer wall is cut down to the mirrored L wall, as a HEIGHT-FIELD cut: over the (y, z) plane the
    cutter is {x > x_t(y, z)}, x_t = x_R - W * max(x_R - x_L, 0). L is not touched (r14's cut, a vertical prism applied to both
    sides, straightened L's flared wall by 0.9-1.7 mm and left a 2 mm cliff at its start, both measured by the r14 review).
    W = start ramp x end ramp x z fades x pit clearance: 0 within WALL + 1 of a pit (the user's pit-wall lock), 0 above
    z -6.3 (full at FLOOR_Z and below), 0 below z -17.5 (full from -14). Nothing is added, only cut; the cutter sits LIFT
    outside the skin where d = 0, so no surface coincides and the cut edge crosses the skin at a finite angle."""
    c0, c1 = RIM_M_Y
    z0, z1 = RIM_M_Z
    st = RIM_M_STEP
    ys = np.arange(c0, c1 + 1e-9, st)
    zs = np.arange(z0, z1 + 1e-9, st)
    Y, Z = np.meshgrid(ys + JIT[0], zs + JIT[1], indexing="ij")
    xr = _first_hit_h(body, 0, 1, Y, Z, 1, 2)
    xl = -_first_hit_h(body, 0, -1, Y, Z, 1, 2)
    okr = np.isfinite(xr) & (xr > 50.0)      # a ray grazing a horizontal face can return a wrong-sided hit (x -89 at z -8.8)
    xl = np.where(xl > 50.0, xl, np.nan)
    from scipy.ndimage import gaussian_filter
    wl = np.isfinite(xl).astype(float)
    gw = gaussian_filter(wl, RIM_M_SIGMA / st, mode="nearest")
    xs_ = gaussian_filter(np.where(np.isfinite(xl), xl, 0.0), RIM_M_SIGMA / st, mode="nearest") / np.maximum(gw, 1e-9)
    xl = np.where(np.isfinite(xl) & (gw > 0.9), xs_, xl)    # smooth only where the Gaussian window is full
    e = np.where(okr & np.isfinite(xl), xr - xl, 0.0)
    e = np.where(np.abs(e) < 4.0, e, 0.0)    # R and L outer walls never differ by more than ~2.3 mm here
    wy = ramp((Y - RIM_M_START[0]) / (RIM_M_START[1] - RIM_M_START[0])) * \
        (1.0 - ramp((Y - RIM_M_END[0]) / (RIM_M_END[1] - RIM_M_END[0])))
    fz = ramp((Z - RIM_M_ZBOT[0]) / (RIM_M_ZBOT[1] - RIM_M_ZBOT[0])) * \
        (1.0 - ramp((Z - RIM_M_ZTOP[0]) / (RIM_M_ZTOP[1] - RIM_M_ZTOP[0])))
    pits = unary_union(ctx["pit_fps"])
    dpit = shapely.distance(pits, shapely.points(np.where(okr, xr, 90.0).ravel(), Y.ravel())).reshape(Y.shape)
    wp = ramp((dpit - (WALL + 1.05)) / 1.0)
    d = wy * fz * wp * np.maximum(e, 0.0)
    d[0, :] = d[-1, :] = d[:, 0] = d[:, -1] = 0.0
    xt = xr - d + RIM_M_LIFT * (1.0 - ramp(d / RIM_M_TAU))
    ie = ndimage.distance_transform_edt(~okr, return_distances=False, return_indices=True)
    xt = np.where(okr, xt, xt[tuple(ie)])
    hf = hf_solid(ys + JIT[0], zs + JIT[1], xt, np.full(xt.shape, float(xt.max()) + 5.0))
    V3 = np.zeros_like(hf.vertices)
    V3[:, 1], V3[:, 2], V3[:, 0] = hf.vertices[:, 0], hf.vertices[:, 1], hf.vertices[:, 2]   # (u, v, h) -> (y, z, x), even
    cut = trimesh.Trimesh(V3, hf.faces, process=True)
    v_ = body.volume
    body = boolean("difference", body, cut, "R rim mirror cut")
    log.append("  P1 R rim cut to the mirrored L wall (height field x(y, z), grid %.2f, W start %s end %s): max depth %.3f, "
               "%d nodes cut (> 0.01), removed %.1f mm3 | watertight %s, euler %d, faces %d"
               % (st, RIM_M_START, RIM_M_END, d.max(), int((d > 0.01).sum()), v_ - body.volume, body.is_watertight,
                  body.euler_number, len(body.faces)))
    return body


def rim_outline(body, log):
    """NOT USED since r15 (r14's cut: it acted on BOTH sides as a vertical prism, so it straightened L's flared wall by
    0.9-1.7 mm and left a 2 mm cliff at its start; replaced by rim_mirror). Original docstring follows.
    D48 + D52 (register r14), as one plan cut. The corner rim wall is the scan lobe's own flank (not the clip K, which
    is smooth), so it carries the scan ripple (R: 0.43-0.55 mm p-p over 14 mm, ~2 mm wavelength) and the R lobe is
    1.3-1.95 mm wider than the L lobe at y 66-70. The outline of the Z = RIM_SEC_Z section is smoothed (Gaussian, sigma
    RIM_SIGMA along it: the ripple drops to 0.1 %) and moved RIM_IN mm inward; the L rim is cut at that curve and the R
    rim at its mirror image (L is the scanned truth: user / register 'left handle as scanned'), by a vertical-walled
    prism difference. The new wall is the smooth curve itself wherever the lobe was outside it (everywhere in the zone
    but troughs deeper than RIM_IN), exactly mirror-symmetric, and nothing is added or pushed (cut, not a warp: the
    first try, rim_outline_warp, tore the skin). Zone: |x| 74 -> 82 and y 62 -> 65 ramped in; the wall left to the
    pocket stays >= 3.1 (plan distance to the oval there is 3.3-10.7 minus RIM_IN)."""
    from scipy.ndimage import gaussian_filter1d
    sec = body.section(plane_origin=[0, 0, RIM_SEC_Z], plane_normal=[0, 0, 1])
    loops = [np.asarray(q)[:, :2] for q in sec.discrete if len(q) > 20]
    outer = max(loops, key=lambda q: Polygon(q).area)
    d = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(outer, axis=0), axis=1))]
    ss = np.arange(0.0, d[-1] - 0.05, 0.1)
    raw = np.column_stack([np.interp(ss, d, outer[:, 0]), np.interp(ss, d, outer[:, 1])])
    sm = gaussian_filter1d(raw, RIM_SIGMA / 0.1, axis=0, mode="wrap")
    tg = np.gradient(sm, axis=0)
    tg /= np.linalg.norm(tg, axis=1)[:, None] + 1e-12
    area2 = np.sum(sm[:, 0] * np.roll(sm[:, 1], -1) - np.roll(sm[:, 0], -1) * sm[:, 1])
    nn = np.column_stack([-tg[:, 1], tg[:, 0]]) * (1.0 if area2 > 0 else -1.0)      # inward normal of the outline
    Sin = sm + RIM_IN * nn                                                        # smoothed, RIM_IN inside
    zw = ramp((np.abs(raw[:, 0]) - 74.0) / 8.0) * ramp((raw[:, 1] - 62.0) / 3.0)
    inz = zw > 0.01
    tgt = raw + zw[:, None] * (Sin - raw)                                         # L: its own smoothed curve
    kt = cKDTree(Sin[inz & (raw[:, 0] < 0)] * [-1.0, 1.0])                        # R: the mirror of the L curve
    Rz = np.flatnonzero(inz & (raw[:, 0] > 0))
    dm, im = kt.query(raw[Rz])
    ML = (Sin[inz & (raw[:, 0] < 0)] * [-1.0, 1.0])[im]
    good = dm < 2.5
    tgt[Rz[good]] = raw[Rz[good]] + zw[Rz[good], None] * (ML[good] - raw[Rz[good]])
    s_in = ((tgt - raw) * nn).sum(1)                                              # > 0: the target is inside the lobe
    tgt = np.where((s_in < 0.03)[:, None], raw - 0.6 * nn, tgt)                   # nothing to cut here: band outside
    v_ = body.volume
    nseg = 0
    for side in (-1, 1):
        idx = np.flatnonzero(inz & (np.sign(raw[:, 0]) == side))
        if len(idx) < 5:
            continue
        for run in np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1):
            if len(run) < 20 or not (s_in[run] >= 0.03).any():
                continue
            a = tgt[run]
            band = Polygon(np.vstack([a, (a - 6.0 * nn[run])[::-1]])).buffer(0)
            if band.is_empty or band.area < 0.5:
                continue
            body = boolean("difference", body, mprism(band, -300.0, 300.0), "rim outline cut %s" % ("L" if side < 0 else "R"))
            nseg += 1
    log.append("  D48 / D52 rim outline cut (z %.1f section, sigma %.2f, %.2f in; R at the mirror of L): %d cuts, removed %.1f mm3, "
               "inward move on the cut outline max %.3f (R %.3f) | watertight %s, euler %d, faces %d"
               % (RIM_SEC_Z, RIM_SIGMA, RIM_IN, nseg, v_ - body.volume, s_in[inz].max(),
                  s_in[Rz[good]].max() if good.any() else 0.0, body.is_watertight, body.euler_number, len(body.faces)))
    return body


def underside_fix(body, ctx, log):
    """P4 (user: 'fill, do not cut'; register D40 / D11 / D19 R / D16 R). Each is a small underside defect: a graph over
    (x, y) seen from below, so the field is measured on that grid and applied as a vertex displacement (roll_warp with a
    custom delta, gated to the underside layer), a continuous operation with no seam. All lie under the pocket where the
    back is 5-13 mm thick, so the r13 back lock (re-scoped to back < BACK_LOCK_T) does not hold them.
    D40: the 0.25-0.31 mm ridge at y 53.2-53.5: its height over the sigma-2.5 trend (minus 0.05) is dilated by 1.2 mm and
         smoothed (0.8 mm) and the trend is lowered by that: the neighbouring underside rises to the ridge (fill only).
    D11: the 0.05-0.11 mm kink at x -57: Gaussian smoothing along x (sigma 1.5), travel <= 0.1 (both ways).
    D19 R / D16 R: the creases near (84.5, 58.5): Gaussian smoothing in x, y (sigma 2.0 and a longer ramp than the L
         side needs), travel <= 0.3 (both ways)."""
    from scipy.ndimage import gaussian_filter1d, gaussian_filter, maximum_filter1d
    Z = {}

    pits = unary_union(ctx["pit_fps"])

    def win(fl, x0, x1, y0, y1, rx=1.5, ry=1.0):
        U, V_ = np.meshgrid(fl["us"], fl["vs"], indexing="ij")
        # the r13 pit-wall lock (everything within WALL + 1 of a pit outline, all z) is a user lock: deviation 0.000.
        # r14 run 2 measured the D19 smooth moving the underside there by 0.23, so no field acts inside it
        dpit = shapely.distance(pits, shapely.points(U.ravel(), V_.ravel())).reshape(U.shape)
        return ramp((np.abs(U) - x0) / rx) * (1.0 - ramp((np.abs(U) - (x1 - rx)) / rx)) * \
            ramp((V_ - y0) / ry) * (1.0 - ramp((V_ - (y1 - ry)) / ry)) * ramp((dpit - (WALL + 1.0 + 0.05)) / 1.0)

    def d40(fl):
        st = fl["us"][1] - fl["us"][0]
        z = -fl["g"]
        trend = gaussian_filter1d(z, 2.5 / st, axis=1, mode="nearest")
        m = np.maximum(trend - z - 0.05, 0.0)
        sz = int(round(2 * 1.2 / st)) | 1
        A = gaussian_filter1d(maximum_filter1d(m, size=sz, axis=1), 0.8 / st, axis=1, mode="nearest")
        dz = np.minimum(trend - A - z + 0.05, 0.0)
        return np.where(fl["ok"], dz * win(fl, 56.0, 86.0, 49.5, 57.5, 2.0, 1.5), 0.0)

    def d11(fl):
        st = fl["us"][1] - fl["us"][0]
        z = -fl["g"]
        dz = np.clip(gaussian_filter1d(z, 1.5 / st, axis=0, mode="nearest") - z, -0.1, 0.1)
        return np.where(fl["ok"], dz * win(fl, 54.5, 59.5, 58.0, 73.0, 1.0, 2.0), 0.0)

    def d19(fl):
        st = fl["us"][1] - fl["us"][0]
        z = -fl["g"]
        dz = np.clip(gaussian_filter(z, 2.0 / st, mode="nearest") - z, -0.3, 0.3)
        return np.where(fl["ok"], dz * win(fl, 79.0, 91.0, 54.5, 63.5, 2.0, 1.5), 0.0)

    zero = lambda U, V_, g0, ok, dcl: np.zeros(U.shape)
    jobs = [("D40 ridge fill R", d40, (50.0, 90.0), (49.0, 58.0), 1), ("D40 ridge fill L", d40, (-90.0, -50.0), (49.0, 58.0), -1),
            ("D11 seam smooth L", d11, (-61.0, -53.0), (57.0, 74.0), -1), ("D19 / D16 crease smooth R", d19, (77.0, 93.0), (53.0, 65.0), 1)]
    for what, fn, ur, vr, sgn_x in jobs:
        if not D19_ON and what.startswith("D19"):
            log.append("  %s: OFF in r15 (D19_ON)" % what)
            continue
        body, info = roll_warp(body, 2, -1, ur, vr, 0.15, zero, 0.45, lambda p: np.ones(len(p), bool), what, log,
                               delta_fn=fn, gate=True, zthr=0.01, dil=0.5)
        if not info["watertight"] or info["flipped"] > 200:
            raise RuntimeError("%s failed: %s" % (what, info))
    return body


# ================================================================ gates
def vert05(mesh, y, side):
    zs = np.arange(-40.0, 40.0, 0.25)
    O = np.column_stack([np.full(len(zs), side * 250.0), np.full(len(zs), y), zs])
    h = first_hits(mesh, O, np.tile([-side, 0, 0.0], (len(zs), 1)))
    xo = np.array([np.nan if q is None or side * q[0][0] < 30 else side * q[0][0] for q in h])
    ok = np.isfinite(xo)
    if ok.sum() < 4:
        return np.nan, np.nan, np.nan
    v = (np.nanmax(xo) - xo[ok]) < 0.5
    return v.mean(), zs[ok].max() - zs[ok].min(), np.nanmax(xo)


def crease_line(mesh, O, D, keep):
    """Max angle between face normals of consecutive first hits (rays 1 mm apart)."""
    h = first_hits(mesh, O, D)
    ok = [i for i, q in enumerate(h) if q is not None and keep(q[0])]
    best, angs = (0.0, None), []
    for i0, i1 in zip(ok[:-1], ok[1:]):
        if i1 != i0 + 1:
            continue
        a = np.degrees(np.arccos(np.clip(mesh.face_normals[h[i0][1]] @ mesh.face_normals[h[i1][1]], -1, 1)))
        angs.append(a)
        if a > best[0]:
            best = (a, (np.asarray(O[i0]) + np.asarray(O[i1])) / 2)
    return best, (np.median(angs) if angs else np.nan)


def xcrease(mesh, side, z, ys):
    O = np.column_stack([np.full(len(ys), side * 250.0), ys, np.full(len(ys), z)])
    return crease_line(mesh, O, np.tile([-side, 0, 0.0], (len(ys), 1)), lambda p: side * p[0] > 55)


def zsection(mesh, z):
    s = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if s is None:
        return Polygon()
    T = np.eye(4)
    T[2, 3] = -z
    pl, _ = s.to_planar(to_2D=T, check=False)
    return unary_union([p for p in pl.polygons_full if p is not None and p.area > 0])


def gates(m, ctx):
    g = []
    ext, hw, scan, oval, P, N = ctx["ext"], ctx["hw"], ctx["scan"], ctx["oval"], ctx["P"], ctx["N"]
    y_root, hinfo = ctx["y_root"], ctx["hinfo"]
    pos, neg = bc.bodies(m)
    g.append("G1 watertight %s | bodies (+vol) %d, internal shells (-vol) %d | euler %d -> genus %d (target 2)"
             % (m.is_watertight, len(pos), len(neg), m.euler_number, (2 - m.euler_number) // 2))
    e = m.extents
    g.append("G2 extents X %.2f Y %.2f Z %.2f (overall thickness) | bounds %s | volume %.1f cm3"
             % (e[0], e[1], e[2], np.round(m.bounds, 2).tolist(), m.volume / 1e3))

    # G3 handles: length, girth, root crease
    for sgn in (-1, 1):
        v = m.vertices[np.sign(m.vertices[:, 0]) == sgn]
        tip_new = v[:, 1].min()
        tip_old = hinfo[sgn]["tip_old"]
        g.append("G3 handle %s: root Y %.2f | tip 1:1 %.2f -> final %.2f (trim plane y %.1f) | root->tip %.2f -> %.2f (%+.2f "
                 "longer than 1:1; r13 untrimmed %+.2f; r14 expectation %+.2f)"
                 % ("L" if sgn < 0 else "R", y_root, tip_old, tip_new, TRIM_Y, y_root - tip_old, y_root - tip_new,
                    tip_old - tip_new, HANDLE_EXTRA, tip_old - TRIM_Y))
        for u in HANDLE_STATIONS_U:
            a = handle_section(ext, y_root - u, sgn)
            yn = y_root - np.interp(u, hinfo["uu"], hinfo["U"])
            b = handle_section(m, yn, sgn)
            if a is None or b is None:
                g.append("    girth u %.0f: section missing" % u)
                continue
            ra = (b.bounds[2] - b.bounds[0]) / (a.bounds[2] - a.bounds[0])
            rz = (b.bounds[3] - b.bounds[1]) / (a.bounds[3] - a.bounds[1])
            g.append("    girth u %4.1f (1:1 Y %.1f -> final Y %.1f): width X x%.3f, depth Z x%.3f, sqrt(area) x%.3f, "
                     "perimeter x%.3f" % (u, y_root - u, yn, ra, rz, np.sqrt(b.area / a.area), b.length / a.length))
        ys = np.arange(y_root + 6.0, y_root - 30.0, -1.0)
        row = []
        for z in (-16.0, -8.0, 0.0, 8.0):
            (a1, p1), _ = xcrease(m, sgn, z, ys)
            (a0, p0), _ = xcrease(ext, sgn, z, ys)
            row.append("Z%.0f %.1f [scan %.1f]" % (z, a1, a0))
        g.append("    root crease (normal jump, rays along X 1 mm apart, Y root+6..root-30): " + " | ".join(row))

    # G4 end wall: rays from the pocket edge outward along the outline normal
    fp = [f[0] for f in ctx["fingers"]]
    for z in (FLOOR_Z + 0.5, -4.0, 0.0, 5.0, LIP_U, LIP_TOP_Z - 0.3):
        O, D, W = [], [], []
        for p, n in zip(P, N):
            if abs(p[0]) <= CAP_XC or p[1] > ctx["Y1"] - END_R - 0.5:
                continue
            if min(np.linalg.norm(p - q) for q in fp) < FINGER_W / 2 + FINGER_SLOT + 2.0:
                continue
            O.append((p[0] - 0.3 * n[0], p[1] - 0.3 * n[1], z))
            D.append((n[0], n[1], 0.0))
            W.append(p)
        hits = bc.ray_hits(m, O, D)
        th = np.array([(h[1] - h[0]) if len(h) >= 2 else 0.0 for h in hits])
        i = int(np.argmin(th))
        g.append("G4 end wall at Z %6.2f: %d rays, min %.2f at %s, rays < 3.0: %d, rays with no wall: %d"
                 % (z, len(th), th[i], np.round(W[i], 1).tolist(), int((th < WALL - 0.01).sum()),
                    sum(1 for h in hits if len(h) == 0)))

    # G5 back wall map under the pocket
    xs = np.arange(-90.0, 90.1, 2.0)
    ysb = np.arange(-8.0, 75.1, 2.0)
    X, Y = np.meshgrid(xs, ysb, indexing="ij")
    excl = unary_union([ctx["wprof"].buffer(0.6), ctx["cam"].buffer(0.6)] + [q.buffer(0.6) for q in ctx["pit_fps"]])
    k = shapely.contains_xy(oval.buffer(-0.6), X.ravel(), Y.ravel()) & ~shapely.contains_xy(excl, X.ravel(), Y.ravel())
    xy = np.column_stack([X.ravel()[k], Y.ravel()[k]]) + JIT
    hh = bc.ray_hits(m, [(x, y, FLOOR_Z + 0.5) for x, y in xy], [(0, 0, -1.0)] * len(xy))
    th = np.array([(h[1] - h[0]) if len(h) >= 2 else np.nan for h in hh])
    zf = np.array([-h[0] if len(h) else np.nan for h in hh])
    i0, i1 = np.nanargmin(th), np.nanargmax(th)
    g.append("G5 back wall under the pocket (%d probes, 2 mm grid; floor Z %.2f..%.2f): min %.2f at %s, max %.2f at %s, "
             "probes < 3.5: %d, no back: %d" % (len(xy), np.nanmin(zf), np.nanmax(zf), th[i0], xy[i0].tolist(),
                                                th[i1], xy[i1].tolist(), int((th < BACK_T - 0.01).sum()),
                                                int(np.isnan(th).sum())))
    rows = []
    for yb in (-8, 4, 16, 28, 40, 52, 64, 72):
        cols = []
        for xb in (-80, -60, -40, -20, 0, 20, 40, 60, 80):
            kk = (np.abs(xy[:, 0] - xb) < 10) & (np.abs(xy[:, 1] - yb) < 6)
            cols.append("%5.1f" % np.nanmin(th[kk]) if kk.any() and np.isfinite(th[kk]).any() else "    -")
        rows.append("    Y%4d: %s" % (yb, " ".join(cols)))
    g.append("    back-wall min per cell (X -80..80 step 20, +-10; Y +-6):\n" + "\n".join(rows))

    # G6 material added outside the extended scan (after the handle warp)
    add = trimesh.boolean.difference([m, hw], engine="manifold")
    pieces = sorted(add.split(only_watertight=False), key=lambda c: -abs(c.volume)) if add is not None else []
    g.append("G6 material outside the extended (+handle-warped) scan: %.1f mm3 in %d pieces; largest:"
             % (add.volume if add is not None else 0, len(pieces)))
    for c in pieces[:6]:
        g.append("    %.1f mm3  X %.1f..%.1f  Y %.1f..%.1f  Z %.1f..%.1f" % ((c.volume,) + tuple(c.bounds.T.ravel())))
    for name, poly, z0, z1 in (("below floor, under the pocket (oval)", oval, -BIG, FLOOR_Z),
                               ("below floor, ring (oval..oval+3)", ctx["R0"].difference(oval), -BIG, FLOOR_Z),
                               ("below floor, outside the ring", sbox(-BIG, -BIG, BIG, BIG).difference(ctx["R0"]), -BIG, FLOOR_Z),
                               ("above floor (anywhere)", sbox(-BIG, -BIG, BIG, BIG), FLOOR_Z, BIG)):
        q = trimesh.boolean.intersection([add, mprism(poly, z0, z1)], engine="manifold")
        g.append("    added, %s: %.1f mm3" % (name, q.volume if q is not None and len(q.faces) else 0.0))
    # how far the new underside is below the scan's underside (protrusion), sampled on a grid
    Xg, Yg = np.meshgrid(np.arange(-110.0, 110.1, 2.0), np.arange(-15.0, 80.1, 2.0), indexing="ij")
    zf_, zs_ = z_from(m, Xg, Yg), z_from(hw, Xg, Yg)
    dz = zs_ - zf_
    outQ = ~shapely.contains_xy(ctx["R0"], Xg.ravel(), Yg.ravel()).reshape(Xg.shape)
    j = np.nanargmax(np.where(outQ, dz, -99))
    g.append("    underside lowered (scan underside - final underside): max %.2f under the ring/pocket, max %.2f "
             "outside the ring at %s" % (np.nanmax(np.where(~outQ, dz, -99)), np.where(outQ, dz, -99).ravel()[j],
                                         np.round([Xg.ravel()[j], Yg.ravel()[j]], 1).tolist()))

    # G7 end-wall sections: vertical fraction, crease
    for y in (50.0, 35.0, 20.0, 5.0, -5.0):
        row = []
        for sd in (-1, 1):
            f, span, xm = vert05(m, y, sd)
            f0, span0, xm0 = vert05(hw, y, sd)
            row.append("%s %.0f%% of %.1f (x %.1f) [scan %.0f%% of %.1f]"
                       % ("L" if sd < 0 else "R", 100 * f, span, xm, 100 * f0, span0))
        g.append("G7 vert05 @Y %5.1f: %s" % (y, " | ".join(row)))
    ysr = np.arange(ctx["Y1"] - 2.0, -12.0, -1.0)
    for z in (-16.0, -12.0, -6.0, 0.0, 6.0, 12.0):
        row = []
        for sd in (-1, 1):
            (a, pa), med = xcrease(m, sd, z, ysr)
            (a0, p0), med0 = xcrease(hw, sd, z, ysr)
            row.append("%s max %.1f @Y %s med %.1f [scan %.1f @Y %s]"
                       % ("L" if sd < 0 else "R", a, "-" if pa is None else "%.1f" % pa[1], med, a0,
                          "-" if p0 is None else "%.1f" % p0[1]))
        g.append("G7 crease (normal jump 1 mm apart, rays along X, Y %.0f..-12) Z %5.1f: %s" % (ctx["Y1"] - 2, z, " | ".join(row)))
    # underside crease: rays up along X lines (the offset-field boundary, the old pad location)
    for yl in (-6.0, 10.0, 30.0, 48.0, 60.0, 70.0):
        xsl = np.arange(-110.0, 110.1, 1.0)
        O = np.column_stack([xsl + JIT[0], np.full(len(xsl), yl + JIT[1]), np.full(len(xsl), -300.0)])
        D = np.tile([0, 0, 1.0], (len(xsl), 1))
        (a, pa), med = crease_line(m, O, D, lambda p: p[2] < FLOOR_Z - 0.1)     # underside only (not the
        (a0, p0), _ = crease_line(hw, O, D, lambda p: p[2] < FLOOR_Z - 0.1)     # floor seen through a hole)
        g.append("G7u underside crease along Y %.0f (rays up, 1 mm apart): max %.1f at x %s med %.1f [scan %.1f at x %s]"
                 % (yl, a, "-" if pa is None else "%.0f" % pa[0], med, a0, "-" if p0 is None else "%.0f" % p0[0]))

    # G8 window + camera open, with solid controls
    wy = (WIN_Y0 + WIN_Y1) / 2
    wx, wh = WINDOW_W / 2 - 6, (WIN_Y1 - WIN_Y0) / 2 - 6
    win = [tuple(np.add(q, JIT)) for q in ((0, wy), (wx, wy + wh), (-wx, wy + wh), (wx, wy - wh), (-wx, wy - wh))]
    out = [tuple(np.add(q, JIT)) for q in ((30, WIN_Y1 + 1.0), (-30, WIN_Y0 - 1.5), (0, WIN_Y0 - 5.0))]
    h1 = bc.ray_hits(m, [(x, y, 60) for x, y in win], [(0, 0, -1)] * len(win))
    h2 = bc.ray_hits(m, [(x, y, 60) for x, y in out], [(0, 0, -1)] * len(out))
    g.append("G8 window hits inside %s (expect 0) | controls %s (expect > 0)" % ([len(h) for h in h1], [len(h) for h in h2]))
    rc = CAMERA_HOLE_D / 2
    cin = [(0, CAMERA_Y)] + [(0.8 * rc * np.cos(a), CAMERA_Y + 0.8 * rc * np.sin(a)) for a in np.arange(4) * np.pi / 2]
    cin = [tuple(np.add(q, JIT)) for q in cin]
    cout = [tuple(np.add(q, JIT)) for q in ((rc + 1.5, CAMERA_Y), (-(rc + 1.5), CAMERA_Y))]
    h1 = bc.ray_hits(m, [(x, y, 60) for x, y in cin], [(0, 0, -1)] * len(cin))
    h2 = bc.ray_hits(m, [(x, y, 60) for x, y in cout], [(0, 0, -1)] * 2)
    g.append("G8 camera hits inside %s (expect 0) | controls %s (expect > 0)" % ([len(h) for h in h1], [len(h) for h in h2]))

    # G9 heights around the rim
    v = m.vertices
    near = shapely.contains_xy(ctx["R0"].buffer(0.01), v[:, 0], v[:, 1])
    g.append("G9 max Z within the rim (oval + %.1f) %.3f vs lip top %.2f | max Z overall %.2f at %s"
             % (WALL, v[near, 2].max(), LIP_TOP_Z, v[:, 2].max(), np.round(v[np.argmax(v[:, 2])], 1).tolist()))
    fpts = [f[0] for f in ctx["fingers"]]
    sel = [(p, n) for p, n in zip(P, N) if abs(p[0]) > CAP_XC and p[1] < ctx["Y1"] - 3
           and min(np.linalg.norm(p - q) for q in fpts) >= FINGER_W / 2 + FINGER_SLOT + 3.0]
    for dd in (0.5, 2.0, 6.0, 10.0, 15.0):
        xy = np.array([p + n * (WALL + dd) for p, n in sel])
        z1, z0 = top_z(m, xy), top_z(hw, xy)
        g.append("G9 top Z at rim + %4.1f (end arcs, Y %.0f..%.0f): final min/med/max %.2f/%.2f/%.2f | scan %.2f/%.2f/%.2f"
                 % (dd, POCKET_Y_BOTTOM, ctx["Y1"] - 3, np.nanmin(z1), np.nanmedian(z1), np.nanmax(z1),
                    np.nanmin(z0), np.nanmedian(z0), np.nanmax(z0)))
    fpts = [f[0] for f in ctx["fingers"]]
    for sd in (-1, 1):
        rows = []
        for p, n in zip(P, N):
            if sd * p[0] <= CAP_XC - 15 or p[1] > ctx["Y1"] - END_R - 0.5:
                continue
            if min(np.linalg.norm(p - q) for q in fpts) < FINGER_W / 2 + FINGER_SLOT + 3.0:
                continue
            rows.append((p, p + n * (WALL + 0.5), p + n * (WALL + 2.0)))
        z05 = top_z(m, np.array([r[1] for r in rows]))
        z2 = top_z(m, np.array([r[2] for r in rows]))
        py = np.array([r[0][1] for r in rows])
        txt = []
        for y0 in np.arange(-10.0, 60.0, 5.0):
            kk = (py >= y0) & (py < y0 + 5)
            if kk.any():
                txt.append("Y%.0f:%.1f/%.1f" % (y0, np.nanmin(z05[kk]), np.nanmin(z2[kk])))
        g.append("G9c %s rim-outside top Z (min at +0.5 / +2.0 mm, per 5 mm of Y; lip top %.1f): %s"
                 % ("L" if sd < 0 else "R", LIP_TOP_Z, " ".join(txt)))
    # bottom corners: top Z along lines leaving the ring end at x = +-70 (the r5 cliff)
    for sd in (-1, 1):
        pts_ = np.array([(sd * (X_OPEN + dx_), POCKET_Y_BOTTOM - WALL - dy_) for dx_ in (0.0, 3.0, 6.0)
                         for dy_ in (0.5, 2.0, 4.0, 6.0)])
        z1 = top_z(m, pts_)
        g.append("G9b bottom corner %s: top Z at x=%+.0f/+3/+6, y=ring-0.5/-2/-4/-6: %s"
                 % ("L" if sd < 0 else "R", sd * X_OPEN, np.round(z1.reshape(3, 4), 1).tolist()))

    # G10 nothing in front of the top edge above the floor
    xy = []
    for p, n in zip(P, N):
        if p[1] > YC + 5 and 56.0 <= abs(p[0]) <= X_LR_END - 0.5:
            for dd in np.arange(0.3, 12.0, 1.0):
                xy.append(p + n * dd)
    xy = np.array(xy)
    zt = top_z(m, xy)
    j = np.nanargmax(zt)
    g.append("G10 in front of L/R (%d probes): max first-hit Z %.3f at %s vs floor %.2f (NaN = no material)"
             % (len(xy), zt[j], np.round(xy[j], 1).tolist(), FLOOR_Z))
    arc = [i for i in range(len(P)) if P[i, 0] > CAP_XC]
    ic = min(arc, key=lambda i: abs(P[i, 1] - YC))
    g.append("    control on the arc between the pits %s: top Z %.2f (expect lip top)"
             % (np.round(P[ic] + N[ic] * 1.5, 1).tolist(), top_z(m, np.array([P[ic] + N[ic] * 1.5]))[0]))

    # G11 finger pits: wall on Z sections (pit plan -> outside air) and material under the pit bottom
    for (p, n, fi), fp_ in zip(ctx["fingers"], ctx["pit_fps"]):
        rows = []
        for z in (ROOT_Z + 0.3, FLOOR_Z - 0.5, FLOOR_Z + 0.5, 0.0, 5.0, LIP_U, LIP_TOP_Z - 0.3):
            S_ = zsection(m, z)
            air = sbox(p[0] - 30, p[1] - 30, p[0] + 30, p[1] + 30).difference(S_)
            outside = air.difference(unary_union(ctx["pit_fps"] + [oval]).buffer(0.05))
            d = fp_.distance(outside) if not outside.is_empty else np.inf
            rows.append("Z%.1f %.2f" % (z, d))
        gp = np.array(fp_.buffer(-0.5).exterior.coords)[::3] + JIT
        hh = bc.ray_hits(m, [(x, y, ROOT_Z - 0.05) for x, y in gp], [(0, 0, -1.0)] * len(gp))
        under = np.array([ROOT_Z + h[0] if len(h) else 0.0 for h in hh])     # exit Z = -h[0]
        g.append("G11 pit (%.1f, %.1f): wall to outside air on Z sections: %s | material under pit bottom min %.2f | "
                 "land %.3f" % (p[0], p[1], " ".join(rows), under.min(), fi["land"]))
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="STL path (not inside projects/VitaGripPS5/stl)")
    ap.add_argument("--dump", default=None, help="prefix: also write step-4 fields (.npz) and intermediate STLs")
    ap.add_argument("--no-fillet", action="store_true", help="diagnostics: skip the last stage (fillets)")
    ap.add_argument("--no-bar", action="store_true", help="r16 variant: BAR_CUT_ON = False (bar rear-bottom roll skipped)")
    a = ap.parse_args()
    if a.no_bar:
        global BAR_CUT_ON
        BAR_CUT_ON = False
    out = pathlib.Path(a.out).resolve()
    if STL_DIR.resolve() in out.parents:
        sys.exit("refusing to write into %s: the user approves every STL bake" % STL_DIR)
    if a.dump:
        dp = pathlib.Path(a.dump).resolve()
        if STL_DIR.resolve() in dp.parents:
            sys.exit("refusing to dump into %s" % STL_DIR)
        global DUMP
        DUMP = str(dp)
    t = time.time()
    body, ctx, log = build()
    for line in log:
        print(line, flush=True)
    body = clean(body)
    if DUMP:
        body.export(DUMP + "_prefillet.stl")
        with open(DUMP + "_ctx.txt", "w") as fh:
            fh.write("\n".join([ctx["oval"].wkt, ctx["wprof"].wkt] + [q.wkt for q in ctx["pit_fps"]]))
    # r10: fillets are the last stage (user: after every other fix)
    flog = []
    body = fix_degenerate(body, flog)
    if FILLET_ON and not a.no_fillet:
        for fam_ in FILLET_ORDER:
            body, _ = fillet_family(body, ctx, fam_, FILLET_R[fam_], flog)
            print(flog[-1] if not flog[-1].startswith("    ") else "", flush=True)
        body = fix_degenerate(body, flog)
    else:
        flog.append("fillet stage: OFF")
    flog.append("R14 stages:")
    body = trim_handles(body, flog)       # D49 (+ D54 / D55 consequences)
    if RIM_CUT_ON:                        # r16: OFF (user 2026-10-03, "Drop the R rim cut"): R rim built as r13 built it
        body = rim_mirror(body, ctx, flog)    # r15 P1: R rim wall onto the mirrored L wall (r14: rim_outline, both sides)
    else:
        flog.append("  R rim cut (rim_mirror): OFF (RIM_CUT_ON = False), R rim as r13")
    body = roll_rim(body, flog)           # D50 / D51
    body = underside_fix(body, ctx, flog)   # D40 / D11 / D19 R / D16 R
    body = bar_back_fill(body, flog)      # r15 P4 (D56)
    if FINISH_ON:   # r13: the finishing pass is the very last geometry stage
        flog.append("FINISH (r13):")
        body = finish(body, ctx, flog)
    else:
        flog.append("finishing stage: OFF (r12 geometry)")
    for line in flog:
        print(line, flush=True)
    tmp = out.with_suffix(".tmp.stl")
    body.export(str(tmp))
    back = trimesh.load(str(tmp))
    pos, neg = bc.bodies(back)
    if len(pos) > 1 and not neg and sorted(c.volume for c in pos)[-2] < 1.0:
        print("reloaded STL: dropping %d sliver bodies %s" % (len(pos) - 1, [
            "%.3f mm3 %s" % (c.volume, np.round(c.bounds, 1).tolist()) for c in pos if c is not max(pos, key=lambda q: q.volume)]))
        max(pos, key=lambda q: q.volume).export(str(tmp))
        back = trimesh.load(str(tmp))
        pos, neg = bc.bodies(back)
    print("reloaded STL: watertight %s, winding %s, %d bodies, %d inner shells, genus %d, %d faces"
          % (back.is_watertight, back.is_winding_consistent, len(pos), len(neg), (2 - back.euler_number) // 2,
             len(back.faces)), flush=True)
    if not back.is_watertight or len(pos) != 1 or neg:
        sys.exit("reloaded STL fails watertight / one body; left at %s, not written to --out" % tmp)
    tmp.replace(out)
    print("wrote %s (%.1f s)" % (out, time.time() - t), flush=True)
    for line in gates(back, ctx):
        print(line, flush=True)
    print("done %.1f s" % (time.time() - t))


if __name__ == "__main__":
    main()
