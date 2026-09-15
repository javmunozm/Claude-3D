"""
socket_placement.py - the ONE datum for the Vita socket cut.

WHY THIS MODULE EXISTS
----------------------
`build_socket_grip.py` computed the scale factor and the console pose inline.
Anything else that wanted to SEE that pose - an overlay render, an interactive
placement window - had to recompute it, and this repo has already shipped a
gate that re-derived a placement and tested a pose 30 mm off the built one
while reporting a clean pass (see docs/lessons.md, "the gate must share the
datum it tests").

So the pose is computed here, once, and the builder, the overlay renderer and
the pyvista window all import it. If this function is wrong, every tool is
wrong the same way and the disagreement is visible - which is the point.

THE POSE, AND THE THREE BUGS THAT SHAPED IT
-------------------------------------------
Each of these was caught by the PERCENTAGE OF VOLUME the cut removed, because
that was the only signal available without a picture. A plausible socket for a
182 x 84 mm console is double digits; each bug read 1-2 %.

1. ORIENTATION. console_solid.stl stands on edge: X=width 182.7, Y=depth 19.3,
   Z=height 84.25. The grip frame is X=width, Y=fore-aft, Z=up, with the Vita
   lying flat and screen up. Unrotated, the console presented only its 19.3 mm
   edge and the cut removed 1.3 %. Rotating 90 deg about X swaps Y and Z.

2. Y PLACEMENT. The first attempt centred the console at Y = -31, 30 % up from
   the trigger end, and the cut removed 1.2 %. Measured on the scaled shell,
   the CENTRE of the body does not exist below about Y = -15:

       Y -35   centre: no material     outer (grips): Zmax 19.84
       Y -15   centre Zmax 33.90       outer          Zmax 27.28
       Y +25   centre Zmax 32.24       outer          Zmax 31.42

   That region is the open span between the two grips - the gap a DualSense
   has under its shoulder buttons. A console placed there hangs in air. Solid
   body runs Y -15..78, so a centre near +20 puts the whole 84.25 mm footprint
   over material.

3. Z PLACEMENT. The top face is a DOME, not a plane: measured under the
   footprint it runs 35.55 mm at the middle down to 26.0 at the edges. Sinking
   from the PEAK engages only the peak, and that cut came out 2.2 %. The datum
   is therefore the LOWEST top-of-shell across the footprint - the console has
   to clear the whole dome, not its summit. Columns are binned 5 mm in X-Y,
   each column's top taken, and the 5th percentile of those used.
"""

import pathlib

import numpy as np
import trimesh

HERE = pathlib.Path(__file__).resolve().parent
PROJ = HERE.parent
DERIVED = PROJ / "derived"

GRIP_SRC = DERIVED / "dualsense_stripped.stl"
CONSOLE = PROJ / "console_solid.stl"

REF_GRIP_W = 222.4      # 054-1.webp at the corrected 0.246279 mm/px anchor
FIT_CLEAR = 0.35        # per side, on the console before it is used as a cutter

DEFAULT_Y = 35.0        # console Y centre, in grip coords
DEFAULT_SINK = 17.0     # console bottom below the local top face, mm

# TILT: the shell's top face is not flat, it FALLS toward the rear.
#
# Measured on the scaled shell across the console footprint, 95th percentile
# of Z in 8 mm bins along Y:
#
#     Y  -3.5  top 33.90        Y +44.5  top 29.35
#     Y  +4.5  top 33.07        Y +52.5  top 27.28
#     Y +12.5  top 33.07        Y +60.5  top 25.63
#     Y +20.5  top 32.24        Y +68.5  top 23.15
#     Y +28.5  top 31.00        Y +76.5  top 20.26
#     Y +36.5  top 30.59
#
# Least-squares slope dZ/dY = -0.1611 -> 9.15 degrees. A console laid FLAT on
# that surface meets it along one line and gapes at both ends; matching the
# tilt is what puts the Vita's face parallel to the DualSense's.
DEFAULT_TILT = 0.0      # degrees about X - see REVERTED below

# REVERTED TO 0, AND WHY THE 9.15 NUMBER IS NOT THE POINT.
#
# The slope above is real and correctly measured. Applying it as a rigid
# rotation still made the part WORSE, and the volume gate did not notice:
#
#     tilt   0.00  sink 21.0   socket: one solid slab      3.7 % -> see below
#     tilt  -9.15  sink 21.0   removes 17.67 %, floor YES  <- LOOKED FINE
#
# Rendered, the -9.15 pose showed the socket broken into scattered
# disconnected patches around the touchpad and stick wells instead of one
# pocket, and only 3.7 % of grip vertices fell inside the cutter, down from
# 16.9 % at the original pose. The removal PERCENTAGE went UP while the socket
# fell apart, because a percentage sums disconnected scraps just as happily as
# it sums one coherent volume.
#
# That is this repo's recurring failure in a new place: a scalar gate passing
# on geometry that is visibly wrong. The tilt was reverted after LOOKING at
# the render, not after reading a number.
#
# Why a single rotation cannot work here: the shell's top is a dome falling in
# BOTH directions, not an inclined plane. Measured across X under the
# footprint it is a symmetric double hump - the two grip domes with a valley
# between them, -80/0/+80 all reading 29.76 and +-40 both 33.07 - so there is
# no roll about Y to correct either. A rigid body has one orientation; this
# surface needs a different one at every point. The parallelism check said so
# before the render did: gap spread 5.25 mm along Y at the best rotation.
#
# If the Vita's face must sit parallel to the shell, the way there is to let
# the console cut its own flat seat into the dome (a deeper sink at tilt 0),
# not to rotate the console to chase a curved surface.

# TILTING COSTS DEPTH, AND THE SINK HAD TO BE RE-SOLVED FOR IT.
#
# Rotating the console about its own centre lifts one end out of the shell and
# buries the other, so the same nominal sink bites less. Measured at Y 35:
#
#     tilt   0.00  sink 10.0   removes 14.25 %
#     tilt  -9.15  sink 10.0   removes  8.55 %   <- the tilt alone loses 40 %
#     tilt  -9.15  sink 12.0   removes  9.87 %
#     tilt  -9.15  sink 14.0   removes 11.86 %
#     tilt  -9.15  sink 16.0   removes 14.42 %   <- parity with the flat pose
#
# This is the same failure as the original "sunk from the dome's PEAK" bug: a
# depth measured from the wrong datum engages less material than it looks like
# it should. Sink is therefore measured from the console's OWN LOWEST CORNER
# after rotation, not from its centre.

# The percentage of grip volume a CREDIBLE socket removes. The three placement
# bugs above all read 1-2 %; the accepted pose reads 13.4. This is the gate
# that caught every one of them, so it is stated as a number, not a habit.
MIN_PLAUSIBLE_REMOVAL_PCT = 5.0

# THE REAR TOUCH PANEL WINDOW
# ---------------------------
# The PCH-1000 has a touch panel on its BACK. The console seat has ~17-24 mm of
# solid shell beneath it (ray-probed from the seat floor at Z 4.50 down to the
# underside at Z -12.9..-19.0), so the panel is buried unless a window is cut
# through it.
#
# WHERE THE SIZE COMES FROM, AND WHY IT IS NOT A PRECISE NUMBER.
#
# `Fixed_dimensions.webp` (IGN) draws a RED ANNOTATION BOX around the rear
# touch pad on its BACK view: 246 x 101 px, x 128..374, y 770..871. That box is
# the source's own marking. It is used because SIX attempts to segment the
# panel tonally (brightness, local variance, red-exclusion, value-window,
# contiguous-run, column-profile) returned mutually inconsistent answers - the
# panel reads as 94-95 % of console width at most thresholds, i.e. the console
# shell itself, not the panel.
#
# Converting those px to mm is the weak link. The console's own width in that
# view reads 403-452 px depending on method:
#
#     403 px -> 0.4516 mm/px -> panel 111.1 x 45.6 mm
#     452 px -> 0.4027 mm/px -> panel  99.1 x 40.7 mm
#
# and the 403 px read is known bad: at that scale the console's HEIGHT comes
# out 70.00 mm against its 83.55 spec, 16 % short, which an orthographic view
# cannot be. So the true panel is somewhere in 99-111 x 41-46 mm.
#
# CUT AT THE LOW END, DELIBERATELY. A window smaller than the real panel still
# exposes it and leaves more shell material; one larger than it eats into the
# console's structural back and the shell's support. This is 99 x 41 +-6 mm,
# and it should be stated that way rather than as 99.00.
#
# Not sourced from console_solid.stl: that mesh is a voxel-remeshed ENVELOPE
# with no surface features (measured: 10667 mm2 of +Y-facing area in a single
# 1.25 mm bin, one flat slab, no recess). Not sourced from
# `BackDetailedView.jpg` either - that is the AI-generated fake blueprint,
# 173 mm overall width for a 182 mm console (see docs/projects.md).
WINDOW_W = 99.0         # rear touch panel window, X
WINDOW_H = 41.0         # rear touch panel window, Y

# THE WINDOW IS NOT CENTRED ON THE CONSOLE - IT IS PLACED ON THE PANEL.
#
# The first version centred the window on the console cutter's own bounds,
# which is the middle of a 84.95 mm footprint (riser included). That is the
# middle of the CONSOLE, not the position of the touch panel, and the two are
# not the same place.
#
# Measured on `Fixed_dimensions.webp`'s FRONT view, which carries a clean black
# screen rectangle and so gives a readable datum where the BACK view does not:
#
#     screen   x 131..371  y 272..408   ->  240 x 136 px, ratio 1.76 (16:9=1.78)
#     console  x  20..448  y 262..448   ->  428 px for 182.0 mm = 0.4252 mm/px
#
#     screen centre y 340   console centre y 355   -> -15 px = -6.4 mm
#
# The screen sits 6.4 mm TOWARD THE CONSOLE'S TOP EDGE, with more bezel below
# it than above. The rear touch panel follows the same layout.
#
# THE SIGN IS NEGATIVE, AND IT WAS WRONG THE FIRST TIME.
#
# This comment originally asserted that the console's top edge maps to grip +Y,
# reasoning from the +90 deg rotation about X. That was asserted, not tested,
# and it was backwards. Measured by transforming a known point:
#
#     console TOP    (0, 0, +40) --R_x(+90)--> (0, -40, 0)
#     console BOTTOM (0, 0, -40) --R_x(+90)--> (0, +40, 0)
#
# The console's top edge is grip -Y. A +6.4 offset moved the window 6.4 mm
# toward the console's BOTTOM - 12.8 mm from where it belongs - and the build
# reported it cleanly: 86.7 cm3 removed, 13.26 %, watertight, 1 body. Nothing
# in the scalars noticed. This is the same axis error as "the console was
# measured lying on its face" in the project README, which is why the mapping
# is now a measured transform and not a sentence about a rotation.
#
# Scale sanity: at 0.4252 mm/px the console's height reads 79.1 mm against its
# 83.55 spec, 5 % under - usable. The BACK view's equivalent read was 16 % out,
# which is why the panel's POSITION is taken from the front view even though
# its SIZE came from the back view's annotation box.
WINDOW_Y_OFFSET = -6.4  # mm toward the console's top edge (which is -Y, see above)


def window_cutter(grip, console, w=WINDOW_W, h=WINDOW_H):
    """A box that opens the rear touch panel through the seat floor.

    Centred on the console's own footprint in Y, on the grip's centreline in X,
    and running from just inside the seat down clear past the shell's
    underside, so the cut is a THROUGH-opening rather than a blind recess.

    Takes `console` (the already-placed cutter) rather than re-deriving the
    console pose, for the same reason the rest of this module exists: a second
    implementation of a placement is how this repo shipped a gate that tested a
    pose 30 mm off the built one.
    """
    # Console centre, then shifted onto the panel. The offset direction is
    # solid (the panel sits high on the face, more bezel below than above);
    # its MAGNITUDE is a rough read - the same grid gave a 17 px discrepancy
    # on the X centre, which is pure edge-reading error, so treat 6.4 as
    # "about 6 mm toward the top", not as a measured constant.
    ycen = float((console.bounds[0][1] + console.bounds[1][1]) / 2.0) + WINDOW_Y_OFFSET
    zseat = float(console.bounds[0][2])
    # Start INSIDE the seat, not at its floor: a cutter whose top face is
    # coplanar with the floor it cuts leaves the boolean no volume to resolve
    # and can survive as a skin (the same coplanar-tangent failure this module
    # already documents for the riser).
    ztop = zseat + 5.0
    zbot = float(grip.bounds[0][2]) - 10.0
    win = trimesh.creation.box(extents=[w, h, ztop - zbot])
    win.apply_translation([0.0, ycen, (ztop + zbot) / 2.0])
    return win, {"window_w": w, "window_h": h,
                 "window_y": ycen, "window_z": (zbot, ztop)}


def load_grip(scale=None):
    """The stripped DualSense, centred and scaled to the reference width.

    Returns (mesh, factor). Scale is UNIFORM: width governs, and the resulting
    156.3 mm length against the reference's 112.3 is a consequence of a
    DualSense being proportionally longer front-to-back than a Vita grip. It
    is not a defect - see build_socket_grip.py's header.
    """
    g = trimesh.load(str(GRIP_SRC))
    g.apply_translation(-g.bounds.mean(axis=0))
    f = scale if scale else REF_GRIP_W / g.extents[0]
    g.apply_scale(f)
    return g, f


def local_top(grip, console_extents, y):
    """Lowest top-of-shell across the console's footprint at this Y.

    Bug 3 above: sinking from the dome's peak only engages the peak. Columns
    are binned in X-Y, each column's max Z taken, and the 5th percentile
    returned so a few high triangles cannot raise the datum.

    Raises ValueError if there is no material under the footprint - bug 2,
    the console hanging in the gap between the grips.
    """
    band = grip.vertices[
        (np.abs(grip.vertices[:, 1] - y) <= console_extents[1] / 2.0)
        & (np.abs(grip.vertices[:, 0]) < console_extents[0] / 2.0)
    ]
    if len(band) < 100:
        raise ValueError(
            "no grip material under the console footprint at Y=%.1f - the "
            "console would hang in the gap between the grips" % y)
    bx = np.round(band[:, 0] / 5.0).astype(int)
    by = np.round(band[:, 1] / 5.0).astype(int)
    key = bx.astype(np.int64) * 100000 + by
    order = np.argsort(key)
    k_s, z_s = key[order], band[order, 2]
    bounds_i = np.flatnonzero(np.diff(k_s)) + 1
    tops = [seg.max() for seg in np.split(z_s, bounds_i) if len(seg) >= 3]
    return float(np.percentile(tops, 5)) if tops else float(band[:, 2].max())


def load_cutter(grip, y=DEFAULT_Y, sink=DEFAULT_SINK, clear=FIT_CLEAR,
                tilt=DEFAULT_TILT):
    """The console solid, oriented, grown by clearance, tilted, and placed.

    Returns (mesh, info). `info` carries the numbers the callers print, so a
    render and a build report the same pose from the same computation.
    """
    c = trimesh.load(str(CONSOLE))

    # THE CUTTER MUST BE A SOLID BODY, AND console_solid.stl IS NOT ONE.
    #
    # Measured on the file as shipped:
    #
    #     genus 50 (Euler -98), 1954 boundary edges, bbox fill 57.3 %
    #
    # It reports is_watertight True and still has fifty tunnels bored through
    # it - an artefact of make_console_cutter.py's voxel-fill-and-
    # marching-cubes remesh (the failure this repo already recorded as
    # "voxel remesh closes tunnels"). A Vita is a near-rectangular slab and
    # should fill 85-90 % of its bounding box.
    #
    # Every cut made through this operand inherited those tunnels: the boolean
    # dutifully carves each one into the socket's walls. It is also where the
    # genus 50 in the finished part came from - NOT from the DualSense strip,
    # which bisects clean:
    #
    #     dualsense_stripped   genus  0   watertight   fill 39.8 %
    #     console_solid        genus 50   watertight   fill 57.3 %
    #
    # The convex hull fixes it outright: genus 0, watertight, fill 86.5 %, the
    # same 182.70 x 19.30 x 84.25 extents. A hull is the right call *for a
    # cutter* specifically - it defines the void the console drops into, so
    # erring convex is erring toward a pocket that clears the real object.
    # Never use a hull for the console as a VISIBLE part; it is 50.8 % larger
    # in volume because it fills the real console's concavities.
    #
    # A PRISMATIC CUTTER WAS TRIED HERE ON 2026-09-14 AND REVERTED.
    #
    # The hull is a barrel - measured, width and depth by height:
    #
    #     Z  4.50  width 179.91  depth 81.71   <- seat floor, NARROWEST
    #     Z 10.50  width 183.40  depth 84.95   <- widest, mid-height
    #     Z 16.50  width 181.69  depth 83.99   <- pinching back in
    #     Z 18.50  width 183.40  depth 84.95   <- riser seam, steps out again
    #
    # so the seat floor was cut 179.91 mm wide against a 182.70 mm console,
    # and the side wall leans and curves in plan. Replacing it with a straight
    # extrusion of the console's plan silhouette made every scalar better -
    # wall vertical (one Z band, not a sweep), cutter bottom spread 15.00 mm
    # -> 0.0000, genus 4 -> 1, seat floor flat at 4.50 across the band that
    # had been twisted - and the USER REPORTED THE RESULT AS WORSE ON SIGHT.
    #
    # The prism is therefore not the fix, and the barrel numbers above are not
    # the defect that matters. Do not re-apply it without first establishing,
    # from a picture, what is actually wrong with the seat. See
    # docs/lessons.md, "every scalar improved and the part got worse".
    c = c.convex_hull
    c.apply_translation(-c.bounds.mean(axis=0))
    raw_extents = tuple(c.extents)

    # Bug 1: lay it flat, screen up.
    c.apply_transform(trimesh.transformations.rotation_matrix(
        np.pi / 2.0, [1, 0, 0]))

    # Grow by the fit clearance so the printed socket is not a press fit.
    # Scaling a solid scales it about its centre, which is what is wanted:
    # clearance on every face.
    cw, cd, ch = c.extents
    c.apply_scale([(cw + 2 * clear) / cw,
                   (cd + 2 * clear) / cd,
                   (ch + 2 * clear) / ch])

    # Match the shell's fall toward the rear, so the Vita's face lies parallel
    # to the DualSense's rather than meeting it along a single line.
    if tilt:
        c.apply_transform(trimesh.transformations.rotation_matrix(
            np.radians(tilt), [1, 0, 0]))

    # Sink from the console's OWN LOWEST CORNER, not its centre. After a
    # rotation the centre no longer says how deep the body reaches, and
    # sinking from it silently loses 40 % of the bite (see DEFAULT_TILT).
    ztop = local_top(grip, c.extents, y)
    c.apply_translation([0.0, y, 0.0])
    z = ztop - sink - c.bounds[0][2]
    c.apply_translation([0.0, 0.0, z])

    # PROJECT THE CUTTER UPWARD IN Z, SO THE POCKET IS OPEN AT THE TOP.
    #
    # Without this the cutter is a closed slab suspended in the shell, and the
    # difference leaves a SEALED INTERNAL VOID - a cavity with the console's
    # shape and no way in. It cannot be printed, and the Vita cannot be
    # inserted. This repo has already paid for exactly that defect twice:
    # "sealed cavity passes every gate" and "sealed void invisible to every
    # solid-part gate" - watertight, bbox and volume checks all pass while the
    # part slices solid.
    #
    # Extruding the cutter's top face to well above the shell's crown makes the
    # cut a THROUGH-POCKET: material is removed from the seat all the way out
    # of the top surface, so the socket is an opening the console drops into.
    #
    # The extrusion is built as a box spanning the cutter's own X-Y footprint,
    # from its top face up past the shell, then unioned on. Using the cutter's
    # bounds rather than the console's nominal size keeps the opening exactly
    # as wide as the pocket below it, clearance included.
    top_of_shell = float(grip.bounds[1][2])
    cut_top = float(c.bounds[1][2])
    if cut_top < top_of_shell + 1.0:
        lo, hi = c.bounds[0], c.bounds[1]
        # Reach clear of the crown so no thin skin of shell survives above the
        # opening; the exact overshoot is immaterial, only that it exceeds it.
        riser_top = top_of_shell + 10.0

        # THE RISER MUST OVERLAP THE HULL, NOT SIT ON IT.
        #
        # The first version started the riser exactly at the cutter's top face.
        # The union then returned TWO DISJOINT BODIES - measured:
        #
        #     union result: bodies 2, genus -1
        #       piece 1  vol 269.4 cm3  Z  4.50..24.50   (the hull)
        #       piece 2  vol 328.0 cm3  Z 24.50..45.55   (the riser)
        #
        # They met face-to-face at Z 24.50 and never merged: coplanar tangent
        # faces give the boolean engine no volume to fuse, so it keeps both.
        # Used as a cutter, two separate solids leave a THIN WALL of shell
        # material standing in the seam between them - a skin across the pocket
        # that should not exist. The ray probe saw it as 57 of 63 rays stopping
        # at Z 24.50 instead of reaching the seat floor.
        #
        # Dropping the riser's base well inside the hull makes the overlap a
        # real volume, and the union collapses to one body. This is the same
        # class of failure as the `use_self` empty-union already recorded for
        # this project: a boolean that reports success while returning
        # something unusable.
        overlap = max(2.0, (hi[2] - lo[2]) * 0.25)
        riser_base = cut_top - overlap

        # THE RISER TAKES THE CONSOLE'S OWN OUTLINE, NOT ITS BOUNDING BOX.
        #
        # A box riser squares off what the Vita rounds: measured in plan, the
        # console's silhouette is 14227.6 mm2 against a 15392.4 mm2 bounding
        # rectangle - 92.4 %. A box therefore overcuts 1164.8 mm2 of plan
        # area, all of it at the four rounded corners, leaving the opening
        # above the seat a rectangle while the pocket below it is Vita-shaped.
        #
        # Extruding the hull's own XY silhouette keeps the opening the same
        # shape as the seat all the way out of the top surface.
        sil = c.vertices[:, :2]
        try:
            from scipy.spatial import ConvexHull
            ring = sil[ConvexHull(sil).vertices]
        except Exception:
            # Without scipy, fall back to the rectangle rather than failing -
            # but say so, because the opening will be the wrong shape.
            print("  (scipy unavailable: riser falls back to a bounding box, "
                  "so the opening will be rectangular)")
            ring = np.array([[lo[0], lo[1]], [hi[0], lo[1]],
                             [hi[0], hi[1]], [lo[0], hi[1]]])
        riser = trimesh.creation.extrude_polygon(
            __import__("shapely").geometry.Polygon(ring).buffer(0),
            height=riser_top - riser_base)
        riser.apply_translation([0.0, 0.0, riser_base])
        c = trimesh.boolean.union([c, riser])
        if c.body_count > 1:
            raise ValueError(
                "the riser did not merge with the console hull: %d bodies. A "
                "multi-body cutter leaves a wall of material in the seam."
                % c.body_count)

    return c, {
        "raw_extents": raw_extents,
        "placed_extents": tuple(c.extents),
        "y": y,
        "sink": sink,
        "clear": clear,
        "tilt": tilt,
        "local_top": ztop,
        "z_centre": float(c.bounds.mean(axis=0)[2]),
    }


def pose(scale=None, y=DEFAULT_Y, sink=DEFAULT_SINK, clear=FIT_CLEAR,
         tilt=DEFAULT_TILT, window=True):
    """Grip and cutters in their final relative pose, ready to boolean or draw.

    Returns (grip, console_cutter, window_cutter, info). `window_cutter` is
    None when `window=False`. It is returned SEPARATELY rather than unioned
    into the console cutter: the two cuts have different datums (the console
    sets the seat, the window is centred on that seat's own footprint) and
    keeping them apart is what lets a caller draw or gate them independently.
    """
    g, f = load_grip(scale)
    c, info = load_cutter(g, y=y, sink=sink, clear=clear, tilt=tilt)
    info["scale"] = f
    info["grip_extents"] = tuple(g.extents)
    w = None
    if window:
        w, winfo = window_cutter(g, c)
        info.update(winfo)
    return g, c, w, info
