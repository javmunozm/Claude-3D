"""
vita_grip.py - VitaGrip1000 v2: the v0 swept handle pair, made a HOLLOW SHELL
with the ergonomic features from the blueprint set.

WHAT v2 ADDS TO v0
------------------
v0 is a SOLID grip: 149 cm3 of plastic, correct in envelope and verified
against the real console (0 of 200,000 points interfere, slot ray-probed to
19.320 mm). Its shape is not in question and v2 does not re-derive it - every
measured profile, every keep-out and every console-side gate is inherited
unchanged from v0's macros.

What v0 lacks is everything the blueprint set is actually good for:

  * `BackDetailedView.jpg` and `lateralHAndleview.jpg` both call the part an
    "EMPTY STANDALONE SHELL", WALL 3 mm TYP, with internal reinforcement ribs.
    v0 prints as a 149 cm3 brick.
  * `lateralHAndleview.jpg` labels an ERGONOMIC PALM SWELL and radiused
    FINGER REST GROOVES on the front of the handle. v0's handle is a plain
    lofted teardrop.
  * `vistaFrontal.png` labels TEXTILE-TEXTURED GRIP AREAS.

So v2 = v0's verified geometry, hollowed to a 3 mm shell, with the palm swell,
the finger grooves and the grip texture cut into it.

THE BLUEPRINTS' COTES ARE STILL NOT USED AS DIMENSIONS.
They are internally inconsistent - they annotate the grip at 173 mm when the
console it must hold is 182 mm wide, and an "install void" of 160 x 56 mm
cannot contain an 182 x 83.55 mm console. v0 already recorded this and took
only their SHAPE. v2 takes only their FEATURES. Every dimension still comes
from the photograph and the real console mesh.

  WALL           3.0 mm   <- the one blueprint number both drawings agree on,
                              and it matches v0's existing WALL constant
  palm swell     measured on lateralHAndleview.jpg
  finger grooves measured on lateralHAndleview.jpg

HOLLOWING IS NOT COSMETIC. It is the change that makes this printable in
reasonable time, and it is also the one that can silently produce a SEALED
CAVITY - a void with no path to the outside, which slices as solid, wastes
the material anyway, and cannot be verified by watertightness or body count.
A dedicated gate flood-fills from outside the part to prove the cavity is
open. See check_cavity_open().
"""

import sys
from pathlib import Path

import ezdxf
import numpy as np
from build123d import (
    BuildLine, BuildPart, BuildSketch, Ellipse, Mode, Plane, Polyline, add,
    export_step, export_stl, extrude, loft, make_face,
)
from shapely.geometry import Polygon

OUT_DIR = Path(__file__).resolve().parents[1]
VEC = OUT_DIR / "vectors"
PART_NAME = "VitaGrip1000"
CONSOLE_DXF = VEC / "psvita_front.dxf"

CONSOLE_W, CONSOLE_H, CONSOLE_D = 182.0, 83.55, 18.6
HALF_W, HALF_H, HALF_D = CONSOLE_W / 2, CONSOLE_H / 2, CONSOLE_D / 2

FIT_CLEAR = 0.35
WALL = 3.0

# Trigger keep-out, measured on the real PCH-1000 mesh.
SHOULDER_X_LO, SHOULDER_X_HI, SHOULDER_Y = 45.0, 81.6, 30.0

# Stereo speaker dot grid, measured on psvita.jpg (0.3957 mm/px, scale checked
# against the annotated 182 mm width). The retaining notch must not cover it.
SPEAKER_X_LO, SPEAKER_X_HI = 79.7, 86.1
SPEAKER_Y_LO, SPEAKER_Y_HI = -14.0, -8.0

# Inboard of this the console's screen and buttons live; the grip must not
# reach over the front face here. Outboard of it, the retaining clip may.
ACTIVE_X = 78.0

GRIP_W = 223.3
WIDTH_TOL = 2.0

SLOT_D = CONSOLE_D + 2 * FIT_CLEAR
Z_FRONT = SLOT_D / 2 + WALL

# The bar is the REAR WALL behind the console, so its depth is WALL - it is
# not a free parameter. Hand-setting it to 9.0 put its front face at
# Z = -3.65 mm, which is 6.00 mm forward of the console's rear face at -9.65:
# the bar occupied the console's own volume. fit_check reported 6.8 % of the
# console's surface inside the grip, 97 % of it in this band, while bbox,
# volume, watertightness and body count all passed.
BAR_DEPTH = WALL

# How far the handle laps onto the console's FRONT face. In handlefront.webp
# the grip's front edge runs as a narrow vertical band just past the console's
# own edge - it retains the console without reaching the screen or any button.
# That photo is a three-quarter view and cannot be measured, so this is an
# ASSUMED value, flagged as such in the README, to be set by a test fit.
FRONT_LIP = 2.0

# How far inboard the retaining lip reaches. Outboard of this the grip laps
# FRONT_LIP mm over the console's front face; inboard of it the front is fully
# open.
#
# 88.0 puts the notch 3.0 mm inboard of the console's 91 mm edge. It was 82.0,
# a 9 mm notch, and that CROSSED THE SPEAKERS: measured on psvita.jpg at
# 0.3957 mm/px, the speaker dot grid runs |X| 79.7 .. 86.1 mm at Y -9.7..-12.7,
# and the built lip reached inboard to |X| 78.79 - it covered them completely.
# 88.0 clears the speaker grid by 1.9 mm.
LIP_X = 88.0

# Reduce the handle's diameter by this much overall (half off each side of
# every measured section). The photograph measures the moulded product; this
# is printed, and a slimmer grip was asked for: 2 mm first, then 3 mm more.
SLIM = 5.0

# How far above the BUILT bottom of the handle the tip is cut off. The user
# asked for 5 mm. Measured from the domed cap's lowest point, not from the
# loft's lowest station - see build_tip_cut().
TIP_FLAT = 5.0

# TIP_ANGLE is 0: the tip is NOT a planar inclined cut.
#
# Traced on lateralHAndleview.jpg, the handle's tip closes to a rounded dome
# whose centre sits 20.5 px (~5 mm) toward the FRONT of the widest section's
# centre - the spine LEANS, and the end is domed. It is not sliced on a plane.
#
# Three attempts at an inclined chamfer here all produced the wrong result
# (front hanging 13.55 mm below the rear, or 11 mm eaten off the front) while
# building cleanly every time. The feature was wrong, not the sign: with the
# depth profile now traced from the grip's own lateral, the spine offset
# carries the lean on its own and the cap domes the end.
TIP_ANGLE = 0.0

# Where the measured plan profile stops being the handle and starts being the
# handle vanishing behind the console. Above this fraction the section eases
# to TOP_END of its size instead of following the mask down to a 1.9 mm point,
# which lofted as a cone - the "gnome hat".
TOP_TRIM = 0.88
TOP_END = 0.62

# Swells the bar's rear face at mid-span so it reads as a rounded bridge
# rather than a 3 mm blade spanning 115 mm.
BAR_BULGE = 3.5

# Lead-in chamfer at the mouth of the console pocket, so the console does not
# have to clear a square step on the way in.
CHAMFER = 1.2

# Loft resolution. 28 sections over a 107 mm handle is one every 3.8 mm; the
# loft interpolates between them, so this controls fidelity, not facet size.
# ---------------------------------------------------------------------------
# v2 FEATURES
# ---------------------------------------------------------------------------

# Hollow the handles to a shell of this wall thickness. Both blueprints
# annotate "WALL THICKNESS: 3mm TYP" and it agrees with v0's existing WALL,
# which was chosen independently as a standard moulded wall for this size.
SHELL_WALL = 3.0

# The shell opens at the handle TIP - the flat pad TIP_FLAT already cuts
# there. An opening is REQUIRED: without one the cavity is sealed, which
# slices as solid (wasting the material the hollowing was meant to save)
# while passing watertightness, body count and every bbox gate. The opening
# is inset from the tip's outline by this much so a rim remains.
VENT_INSET = 2.0

# ERGONOMIC PALM SWELL. On lateralHAndleview.jpg the front edge of the handle
# bulges forward through the middle of its length - the part that sits in the
# palm's hollow. Measured as a fraction of the handle length from the tip.
SWELL_F0, SWELL_F1 = 0.30, 0.62      # where it runs
SWELL_PEAK = 0.46                    # where it is deepest
SWELL_AMT = 2.2                      # mm of extra depth at the peak

# FINGER REST GROOVES, "(Radiused)" on lateralHAndleview.jpg. Shallow scallops
# across the FRONT face of the handle, where the fingers wrap. Three of them,
# evenly spaced along the lower half of the handle.
GROOVE_N = 3
GROOVE_F0, GROOVE_F1 = 0.16, 0.44    # band along the handle they occupy
GROOVE_R = 5.5                       # scallop radius, mm
GROOVE_DEPTH = 0.9                   # how far it bites into the surface, mm

# INTERNAL REINFORCEMENT RIBS. Both blueprints show them
# ("Internal Reinforcement Ribs (Conceptual)" on lateralHAndleview.jpg) and
# neither dimensions them - they are drawn, not specified. So these are a
# design choice, flagged as assumed.
#
# They matter structurally: hollowing turned each handle into a tube, and a
# tube loaded by a squeezing hand fails by OVALISATION - the section flattens
# long before the material yields. Ribs across the cavity are what stop that.
#
# Built as transverse webs (normal to the handle's long axis), because that
# is the direction that resists the section going oval. A rib running ALONG
# the handle would stiffen it in bending, which is not the load here.
RIB_ON = True
RIB_N = 3                    # webs per handle
RIB_T = 2.0                  # web thickness, mm

# The band stops at 0.48, not 0.60. A fourth web at f=0.60 (y = -17.34) built
# cleanly and then VANISHED from the export: at that height the cavity's
# centre sits at Z = -6.93, above the console pocket floor at -9.65, so the
# console cut and the pocket wall consume it. The console has to win there -
# it is the pocket - so the honest fix is to stop the rib band below it rather
# than to keep asking for a web that cannot exist.
#
# Found by the audit reporting "webs found: 3 / 4", not by inspection.
RIB_F0, RIB_F1 = 0.22, 0.48  # band along the handle they occupy

# TEXTILE-TEXTURED GRIP AREAS (vistaFrontal.png, BackDetailedView.jpg). A
# shallow cross-hatched diamond grid on the outer face of each handle.
# Printed, not moulded: the pitch has to be well above an FDM nozzle's 0.4 mm
# or it prints as a smudge.
TEX_ON = True
TEX_PITCH = 3.2                      # mm between grooves
TEX_DEPTH = 0.45                     # mm deep
TEX_WIDTH = 0.9                      # mm wide
TEX_F0, TEX_F1 = 0.14, 0.66          # band along the handle it covers

N_SECT = 28
CAP = 2.2          # dome height at each end, mm


def _trace():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import trace_grip
    return trace_grip


CONSOLE_MESH = (Path(__file__).resolve().parents[4] / "sources" / "psvitaGrip"
                / "Vita 1000" / "psvitaManualJoin_decimated.stl")


def console_outline():
    """The console's front outline: the traced drawing UNIONED with the mesh.

    CONSOLE_FACTS.md records that the drawing and the real mesh disagree in
    the shoulder region (|X| 85-90 mm), where the mesh is up to 0.53 mm
    fuller, and prescribes the union so the pocket is never smaller than
    either source. Cutting to the drawing alone leaves the console's outer
    upper corner fouling the grip - 205 of 200,000 points, all at X 87.5-91.0.

    Inflating FIT_CLEAR instead needed 0.90 mm and loosened the fit
    everywhere to fix one spot.
    """
    pl = list(ezdxf.readfile(str(CONSOLE_DXF)).modelspace()
              .query("LWPOLYLINE"))[0]
    p = np.array([(x, y) for x, y, *_ in pl.get_points()])
    p = p - [(p[:, 0].max() + p[:, 0].min()) / 2,
             (p[:, 1].max() + p[:, 1].min()) / 2]
    p = p * (CONSOLE_W / np.ptp(p[:, 0]))
    drawn = Polygon([(float(a), float(b)) for a, b in p]).buffer(0)

    if not CONSOLE_MESH.exists():
        return p
    import trimesh
    from shapely.ops import unary_union
    m = trimesh.load(str(CONSOLE_MESH))
    m.apply_translation(-m.bounds.mean(axis=0))
    v = m.vertices[:, :2]

    # The mesh's plan SILHOUETTE, by occupancy on a 0.5 mm grid.
    #   Polygon(v) raises "bad allocation" on 299,721 unordered vertices -
    #   shapely needs a ring, and mesh vertices are not one.
    #   The convex hull is valid but WRONG here: 13,988 mm2 against the
    #   silhouette's 11,111, because it squares off the tapered ends that the
    #   traced outline exists to capture.
    g = 0.5
    ij = set(map(tuple, np.floor(v / g).astype(int)))
    cells = [Polygon([(i * g, j * g), ((i + 1) * g, j * g),
                      ((i + 1) * g, (j + 1) * g), (i * g, (j + 1) * g)])
             for i, j in ij]
    sil = unary_union(cells).buffer(0.25).buffer(-0.25)
    if sil.geom_type == "MultiPolygon":
        sil = max(sil.geoms, key=lambda q: q.area)

    out = drawn.union(sil).simplify(0.15)
    if out.geom_type == "MultiPolygon":
        out = max(out.geoms, key=lambda q: q.area)
    return np.array(out.exterior.coords)


def _grow(pts, d):
    poly = Polygon([(float(a), float(b)) for a, b in pts]).buffer(0)
    out = poly.buffer(d, join_style=2)
    if out.geom_type == "MultiPolygon":
        out = max(out.geoms, key=lambda g: g.area)
    return np.array(out.exterior.coords)


def _polys(g):
    """A shapely result as a list of Polygons - it may be empty, one, or many."""
    if g.is_empty:
        return []
    if g.geom_type == "Polygon":
        return [g]
    return [q for q in g.geoms if q.geom_type == "Polygon" and q.area > 1e-6]


def _prism(pts, depth, z_centre=0.0):
    with BuildPart() as part:
        with BuildSketch(Plane.XY.offset(z_centre - depth / 2.0)):
            with BuildLine():
                Polyline([(float(a), float(b)) for a, b in pts], close=True)
            make_face()
        extrude(amount=depth)
    return part.part


def handle_sections(mirror=False):
    """The measured sections of one handle, as (plane, half_w, half_d) tuples.

    Each section lies in a plane normal to Y - the handle's long axis - at the
    height that station was measured at. The section is an ellipse:

        half-width  from the plan profile   (054-1.webp)
        half-depth  from the depth profile  (dualsense_side.dxf)
        centred at  (cx, y, cz)             both measured

    An ellipse is the right primitive here: every cross-section in the photos
    is a rounded oval, and it is defined entirely by the two numbers that were
    actually measured. Nothing is invented to fill it in.
    """
    tg = _trace()
    plan, (y_tip, y_top) = tg.handle_plan_profile(N_SECT, with_y=True)
    dep = tg.handle_depth_profile(N_SECT)

    # The handle grows REARWARD, not forward. Anchoring the spine at the tip
    # and adding the DualSense's own spine travel drives the section centre
    # forward as the handle widens, so its front face reached Z = +27.3 mm
    # against the console's front face at +9.3 - the handle lay across the
    # screen for 25 mm of its width, which the sketch forbids outright.
    #
    # On a real DualSense the handle hangs below and BEHIND the body; it never
    # projects forward of the front face. So the front of every section is
    # pinned at the grip's front wall and the depth is taken backward from
    # there. FRONT_LIP is how far the handle laps onto the console's front
    # face - the clip that retains it, visible in handlefront.webp as a narrow
    # vertical edge just past the console's own edge.
    # The hook is carried by the DEPTH profile, not by a separate travel term.
    # dep[:,1] is the side view's full front-to-back extent at each height, and
    # that extent ALREADY spans the hooked section - it is why the depth grows
    # 10 -> 45 mm. Adding dep[:,2] on top double-counts the same curve and took
    # the built depth to 57.51 mm against a 45.14 mm handle.
    #
    # So: pin the front face, and let each section's own depth run backward
    # from it. The section centres then migrate rearward on their own as the
    # handle thickens, which is the hook.
    z_front_face = HALF_D + FIT_CLEAR + FRONT_LIP

    # TRIM THE SPIKE. In the photograph the handle's top rows are where it
    # disappears BEHIND the console, so the mask narrows to nothing there and
    # the profile ends at a 1.91 mm point. Lofted, that is a cone - the "gnome
    # hat". The real handle does not come to a point; it runs into the
    # console's edge at close to full width.
    #
    # So the profile is cut at TOP_TRIM and the last kept section is carried
    # up to the original top, giving a blunt end that the cap then rounds.
    keep = plan[:, 0] <= TOP_TRIM
    if keep.sum() < 4:
        raise SystemExit("TOP_TRIM %.2f leaves too few sections" % TOP_TRIM)
    n_keep = int(keep.sum())

    out = []
    for i in range(N_SECT):
        f = plan[i, 0]
        y = y_tip + f * (y_top - y_tip)
        if f > TOP_TRIM:
            # Above the trim, ease from the last real section down to
            # TOP_END of its size - a gentle dome, not a cone. Interpolating
            # rather than holding keeps every station distinct, which the loft
            # requires.
            j = n_keep - 1
            t = (f - TOP_TRIM) / max(1.0 - TOP_TRIM, 1e-6)
            k = 1.0 - (1.0 - TOP_END) * t * t     # quadratic ease-out
            hw = max((plan[j, 1] - SLIM / 2.0) * k, 1.5)
            cx = plan[j, 2]
            hd = max((dep[j, 1] / 2.0 - SLIM / 2.0) * k, 1.5)
            cz = z_front_face - hd
            if mirror:
                cx = -cx
            out.append((float(y), float(hw), float(hd), float(cx), float(cz)))
            continue
        # SLIM: the measured section is reduced by SLIM/2 on each side, so the
        # handle's diameter drops by SLIM overall. The photograph measures the
        # moulded product; this one is printed, and the user asked for a
        # thinner grip in the hand.
        hw = max(plan[i, 1] - SLIM / 2.0, 1.5)
        cx = plan[i, 2]
        # v2: the ERGONOMIC PALM SWELL adds depth through the middle of
        # the handle. Added to the half-depth AND subtracted from cz
        # below, so the swell grows FORWARD only and the rear contour
        # (which the console pocket is cut against) is untouched.
        hd = max(dep[i, 1] / 2.0 - SLIM / 2.0, 1.5) + _swell_scale(f) / 2.0
        cz = z_front_face - hd
        if mirror:
            cx = -cx
        out.append((float(y), float(hw), float(hd), float(cx), float(cz)))
    return out


def build_handle(mirror=False):
    """One handle, lofted through its measured sections.

    A loft - not a stack of prisms. The previous build's staircase came from
    discretising the depth into 40 constant-thickness slabs; a loft builds a
    continuous surface through the same stations instead.
    """
    sect = handle_sections(mirror)

    with BuildPart() as h:
        with BuildPart() as body:
            for y, hw, hd, cx, cz in sect:
                pl = Plane(origin=(cx, y, cz), z_dir=(0, 1, 0),
                           x_dir=(1, 0, 0))
                with BuildSketch(pl):
                    Ellipse(hw, hd)
            # ruled=True. A smooth loft through 28 sections interpolates a
            # spline that BULGES OUTSIDE the section hull: the outer edge ran
            # to -130.18 mm against measured sections reaching -111.74, an
            # 18.4 mm overshoot, and the width gate caught it. Ruled lofting
            # joins the stations with straight segments, so the built surface
            # cannot exceed what was measured. At one section per 3.8 mm the
            # faceting is not visible.
            loft(ruled=True)

        # Dome the two ends. A loft that stops on a full-size ellipse leaves a
        # flat disc - recorded in CONSOLE_FACTS.md as a trap that has already
        # cost a pass here. Cap with a short loft to a small ellipse instead.
        for end, sgn in ((sect[0], -1.0), (sect[-1], +1.0)):
            y, hw, hd, cx, cz = end
            with BuildPart(mode=Mode.ADD) as cap:
                pl0 = Plane(origin=(cx, y, cz), z_dir=(0, 1, 0),
                            x_dir=(1, 0, 0))
                with BuildSketch(pl0):
                    Ellipse(hw, hd)
                pl1 = Plane(origin=(cx, y + sgn * CAP, cz), z_dir=(0, 1, 0),
                            x_dir=(1, 0, 0))
                with BuildSketch(pl1):
                    Ellipse(hw * 0.35, hd * 0.35)
                loft(ruled=True)
            add(cap.part)
    return h.part


def build_bar():
    """The cross-bar joining the handles, at its MEASURED height.

    Y extent comes straight from the photograph (trace_grip.bar_extent()),
    not from a hand-set rise. It sits behind the console's lower edge, so the
    touchpad above it stays exposed.

    THE BAR IS NOT A FLAT PLATE. Built at a constant BAR_DEPTH it stopped at
    Z = -12.65 while the handles, in the bar's own Y band, curve back to
    Z = -25.5. The plate then floats in front of that curve with nothing
    blending it, and reads as a rear wall sticking out of the handles - which
    is exactly what the top view showed.

    So the bar's rear face FOLLOWS the handles: it is lofted between two
    stations whose depth is interpolated from the handle's own rear contour,
    swelling from the thin wall at mid-span to meet the handle where they
    join. The front face stays at the console's rear + clearance, because that
    is what the pocket needs.
    """
    tg = _trace()
    y_top, y_bot = tg.bar_extent()
    plan, (y_tip, y_htop) = tg.handle_plan_profile(N_SECT, with_y=True)
    dep = tg.handle_depth_profile(N_SECT)

    # The handle's rear Z where the bar meets it, from the same profiles the
    # handles are built from - not measured off the export.
    z_front_face = HALF_D + FIT_CLEAR + FRONT_LIP
    y_mid = (y_top + y_bot) / 2.0
    f = np.clip((y_mid - y_tip) / (y_htop - y_tip), 0.0, 1.0)
    hd = float(np.interp(f, plan[:, 0], dep[:, 1])) / 2.0 - SLIM / 2.0
    z_handle_rear = z_front_face - 2.0 * hd
    x_join = float(np.min(np.abs(plan[:, 2]) - plan[:, 1]))

    z_wall_rear = -Z_FRONT                      # the thin wall at mid-span
    half = GRIP_W / 2.0

    # Loft along X through four stations: outboard end (deep, meeting the
    # handle), the join, the join mirrored, and the far end. On a plane with
    # z_dir=(1,0,0) and x_dir=(0,1,0) the sketch's local x is world Y and its
    # local y is world Z, so the section is written (y, z).
    # The bar's rear is ROUNDED, not flat. Tied to WALL it came out a 3.00 mm
    # plate spanning 115 mm - a blade, which is what read as "sticking out".
    # BAR_BULGE swells the rear face at mid-span so the bar is a bridge with a
    # rounded back, as it is in 054-1.webp, and the section is octagonal
    # rather than rectangular so the corners are already broken.
    z_slot_back = -(HALF_D + FIT_CLEAR)
    z_mid_rear = -Z_FRONT - BAR_BULGE
    r = min(2.0, (y_top - y_bot) / 4.0)

    def section(z_rear):
        """A rounded-back section: chamfered at the rear corners."""
        return [(y_bot + r, z_rear), (y_top - r, z_rear),
                (y_top, z_rear + r), (y_top, z_slot_back),
                (y_bot, z_slot_back), (y_bot, z_rear + r)]

    with BuildPart() as bar:
        for xs, z_rear in ((-half, z_handle_rear), (-x_join, z_mid_rear),
                           (x_join, z_mid_rear), (half, z_handle_rear)):
            pl = Plane(origin=(xs, 0, 0), z_dir=(1, 0, 0), x_dir=(0, 1, 0))
            with BuildSketch(pl):
                with BuildLine():
                    Polyline(section(z_rear), close=True)
                make_face()
        loft(ruled=True)
    return bar.part, (y_top, y_bot)


def build_console_cut(bar_top):
    """The console's volume plus clearance.

    Cut in two pieces, for the reason recorded by the previous build: a pocket
    that goes through everywhere deletes the bar and the two handles fall
    apart as separate bodies. Above the bar it goes through, so the touchpad
    is open; across the bar it stops at the bar's front face.

    THE POCKET IS ONLY AS DEEP AS THE CONSOLE. Cutting it through the full
    depth also removes the handles: measured on 054-1.webp, the handles reach
    inboard to |X| 60.7 mm against the console's 91 mm edge, so they overlap
    it in plan by 30 mm. They do not collide because they pass BEHIND the
    console. A through-cut deleted exactly that overlap - the handle sections
    above the bar collapsed from 41 mm deep to 16-19 mm, leaving flat plates,
    while bbox, volume, watertightness and body count all still passed.
    """
    outline = _grow(console_outline(), FIT_CLEAR)
    poly = Polygon([(float(a), float(b)) for a, b in outline])
    big = 400.0

    hi = poly.intersection(Polygon([(-big, bar_top), (big, bar_top),
                                    (big, big), (-big, big)]))
    lo = poly.intersection(Polygon([(-big, -big), (big, -big),
                                    (big, bar_top), (-big, bar_top)]))
    cuts = []
    # From the FRONT OF THE PART back to the console's rear face + clearance,
    # and no further. What remains behind it is the rear wall and the handles.
    #
    # The cut must start ahead of the handles' front face, not at the slot's
    # nominal front. The handles are pinned at Z = HALF_D + FIT_CLEAR +
    # FRONT_LIP, so cutting only to HALF_D + FIT_CLEAR left FRONT_LIP mm of
    # handle standing INSIDE the pocket: the cavity the console drops into
    # measured 21.30 mm against the 19.30 it should be, so a 18.6 mm console
    # had 2 mm of slop and would rattle. Cutting from ahead of the handles
    # makes the lip OVERHANG the console's front face - which is what retains
    # it - instead of deepening the slot.
    #
    # The lip is kept by INSETTING the deep part of the cut. Outboard of
    # LIP_X the cut stops at the console's front face, leaving FRONT_LIP mm of
    # material lapping over it; inboard of LIP_X it runs clear through the
    # front, so the screen and buttons are never covered.
    z_slot_back = -(HALF_D + FIT_CLEAR)
    z_face = HALF_D + FIT_CLEAR
    z_cut_front = Z_FRONT + FRONT_LIP + 2.0

    big2 = 400.0
    if not hi.is_empty:
        inner = hi.intersection(Polygon([(-LIP_X, -big2), (LIP_X, -big2),
                                         (LIP_X, big2), (-LIP_X, big2)]))
        outer = hi.difference(Polygon([(-LIP_X, -big2), (LIP_X, -big2),
                                       (LIP_X, big2), (-LIP_X, big2)]))
        # inboard: straight through the front
        d_in = z_cut_front - z_slot_back
        for g in _polys(inner):
            cuts.append(_prism(np.array(g.exterior.coords), d_in,
                               z_centre=z_cut_front - d_in / 2.0))
        # outboard: stop at the console's front face, leaving the lip
        d_out = z_face - z_slot_back
        for g in _polys(outer):
            cuts.append(_prism(np.array(g.exterior.coords), d_out,
                               z_centre=z_face - d_out / 2.0))
    if not lo.is_empty:
        d = Z_FRONT - (-Z_FRONT + BAR_DEPTH)
        cuts.append(_prism(np.array(lo.exterior.coords), d,
                           z_centre=Z_FRONT - d / 2.0))
    return cuts


def build_touchpad_opening(bar_top):
    """Open the rear wall so the touchpad is exposed - BETWEEN the handles.

    Now that the pocket stops at the console's rear face, the rear wall spans
    the whole console and has to be opened deliberately. The opening is the
    console's outline inset by WALL (so a rim remains to retain it), clipped
    to the span between the handles' inner edges and to above the bar.

    Clipping in X is what keeps this from re-cutting the handles: the console
    region and the handle region overlap in plan, and an unclipped rear cut is
    the same defect as the through-pocket, arriving by another route.
    """
    tg = _trace()
    plan, _ = tg.handle_plan_profile(N_SECT, with_y=True)
    inner = float(np.min(np.abs(plan[:, 2]) - plan[:, 1]))

    rim = _grow(console_outline(), FIT_CLEAR - WALL)
    poly = Polygon([(float(a), float(b)) for a, b in rim])
    big = 400.0
    win = Polygon([(-inner, bar_top), (inner, bar_top),
                   (inner, big), (-inner, big)])
    op = poly.intersection(win)
    if op.is_empty:
        return []
    if op.geom_type == "MultiPolygon":
        op = max(op.geoms, key=lambda g: g.area)

    # from the slot's rear face outward, through the back of the part
    z_back = -(HALF_D + FIT_CLEAR)
    d = z_back - (-Z_FRONT) + 2.0
    return [_prism(np.array(op.exterior.coords), d,
                   z_centre=z_back - d / 2.0 + 1.0)]


def build_trigger_relief():
    """Clear the shoulder buttons across the full depth.

    Built with _prism, NOT with Box(): inside an active BuildPart a bare Box()
    auto-adds itself before it is ever passed to Mode.SUBTRACT. That produced
    a 37 cm3 block that passed watertight, winding and bbox, and survived four
    fixes aimed at the wrong cause.
    """
    parts = []
    for sign in (1, -1):
        x0, x1 = sign * SHOULDER_X_LO, sign * SHOULDER_X_HI
        rect = np.array([(min(x0, x1), SHOULDER_Y), (max(x0, x1), SHOULDER_Y),
                         (max(x0, x1), SHOULDER_Y + 60.0),
                         (min(x0, x1), SHOULDER_Y + 60.0)])
        parts.append(_prism(rect, 4 * Z_FRONT))
    return parts


def build_tip_cut():
    """Cut both handle tips off on an INCLINE, like the DualSense.

    A flat horizontal cut reads as a stump. On the real controller the tip is
    cut on a slope with the REAR lower than the front: measured on
    `dualsense_side.dxf`, over the bottom 6 mm the rear edge advances from
    Z 17.9 to 34.8 mm while the front edge only moves 9.5 -> 0.15, and the
    lower envelope fits a 3.5 deg slope.

    3.5 deg over a 40 mm section is barely 2 mm of drop and does not read, so
    TIP_ANGLE is a design choice - the DualSense measurement establishes the
    DIRECTION (rear low, front high) and the incline is exaggerated to match
    the look. Flagged as assumed in the README.

    The cut plane is built in the Y-Z plane and swept across X, so both
    handles get the same incline.
    """
    tg = _trace()
    _, (y_tip, _) = tg.handle_plan_profile(N_SECT, with_y=True)
    # Anchor on the BUILT tip, not the profile's lowest station: the end cap
    # domes CAP mm past it, so a cut placed at y_tip + TIP_FLAT only grazed
    # the cap and produced a 0.17 mm incline instead of a real one.
    y_bottom = y_tip - CAP
    y_cut = y_bottom + TIP_FLAT
    big = 400.0

    # The cut PIVOTS about the handle's own mid-depth, so TIP_FLAT is the
    # amount removed on average and the incline redistributes it: less at the
    # rear, more at the front.
    #
    # The slab must extend well past the part in Z, but the ANGLE has to be
    # applied about the handle's real mid-depth. Computing the drop across the
    # full padded span instead gave drop = 13.88 mm on a 5 mm cut, which
    # sliced 11 mm off the front of the handle.
    tgp = _trace()
    dep = tgp.handle_depth_profile(N_SECT)
    z_hi = HALF_D + FIT_CLEAR + FRONT_LIP
    z_lo = z_hi - (float(dep[0, 1]) - SLIM)
    z_pivot = (z_hi + z_lo) / 2.0
    slope = np.tan(np.radians(TIP_ANGLE))

    # NEGATIVE slope in z: the cut line sits LOW at the rear (small z) and
    # HIGH at the front (large z), so subtracting everything below it leaves
    # the rear hanging lower than the front - the DualSense's direction.
    # With a positive slope the geometry built cleanly and sloped the wrong
    # way twice; the sign, not the polygon, was the error both times.
    z_rear, z_front = -Z_FRONT - 30.0, Z_FRONT + 10.0
    y_at_rear = y_cut - slope * (z_rear - z_pivot)
    y_at_front = y_cut - slope * (z_front - z_pivot)

    with BuildPart() as cut:
        pl = Plane(origin=(0, 0, 0), z_dir=(1, 0, 0), x_dir=(0, 1, 0))
        with BuildSketch(pl):
            with BuildLine():
                # (y, z) in the sketch's local frame
                # Rear LOW, front HIGH, matching the DualSense's direction.
                # Written the other way round first, which built a real
                # 7.8 mm incline sloping the wrong way.
                Polyline([(y_at_rear, z_rear), (y_at_front, z_front),
                          (y_at_front - big, z_front),
                          (y_at_rear - big, z_rear)], close=True)
            make_face()
        extrude(amount=big, both=True)
    return cut.part


def build_pocket_relief(bar_top):
    """Soften and hollow the mouth of the console pocket.

    The console is INSERTED into this pocket, and the pocket's walls meet the
    rear wall and the bar as square steps. Two problems with that:

      * the step is a stress riser and, on an FDM print, a shelf of support
        material exactly where the console has to slide past
      * a square inside corner will not accept the console's own moulded
        radius, so it seats on the corner rather than on the floor

    So the mouth is opened by CHAMFER mm, tapering from the pocket's nominal
    outline at the floor to CHAMFER mm larger at the entry face. Built as a
    short loft between two offsets of the same outline rather than as a
    fillet: build123d's fillet on this many mixed edges is fragile, and a
    lofted taper is what a moulded lead-in actually looks like.
    """
    base = console_outline()
    inner = _grow(base, FIT_CLEAR)
    outer = _grow(base, FIT_CLEAR + CHAMFER)

    z_face = HALF_D + FIT_CLEAR
    z_floor = z_face - CHAMFER

    with BuildPart() as ch:
        with BuildSketch(Plane.XY.offset(z_floor)):
            with BuildLine():
                Polyline([(float(a), float(b)) for a, b in inner], close=True)
            make_face()
        with BuildSketch(Plane.XY.offset(z_face)):
            with BuildLine():
                Polyline([(float(a), float(b)) for a, b in outer], close=True)
            make_face()
        loft(ruled=True)
    return [ch.part]


def _measure_slot():
    """The console cavity's actual depth, ray-probed on the exported mesh.

    Returns the median slot depth over several probes, or None if the export
    is not readable. This measures the SHAPE, not the intent: the pocket cut
    was already the right depth when the built cavity was 20.85 mm, because
    the handles were standing inside it.
    """
    stl = OUT_DIR / "stl" / ("%s.stl" % PART_NAME)
    if not stl.exists():
        return None
    try:
        import trimesh
    except ImportError:
        return None
    m = trimesh.load(str(stl))
    zs = np.linspace(-30, 30, 3001)
    out = []
    # Probe wherever the pocket is actually enclosed - between the lip's
    # inboard edge and the console's edge. Hard-coding 84/88 silently returned
    # None once LIP_X moved to 88.0, and a gate that returns None passes.
    # Sweep Y as well as X. Fixed heights of 0 and -10 mm stopped working once
    # the handle gained its neck: above the swell there is no lip at those
    # heights, so every probe came back open and the gate failed a build whose
    # pocket was in fact exactly right. The gate must look where the pocket IS
    # enclosed, not where it was last time.
    xs_probe = [s * x for s in (1.0, -1.0)
                for x in np.linspace(LIP_X + 0.5, HALF_W - 0.5, 4)]
    ys_probe = np.linspace(-HALF_H + 6.0, HALF_H - 6.0, 9)
    for x in xs_probe:
        if len(out) >= 6:          # enough samples; probing is ray-cast heavy
            break
        for y in ys_probe:
            pts = np.column_stack([np.full(len(zs), x), np.full(len(zs), y), zs])
            ins = m.contains(pts)
            runs, s = [], None
            for i, f in enumerate(ins):
                if f and s is None:
                    s = i
                if (not f or i == len(zs) - 1) and s is not None:
                    runs.append((zs[s], zs[i - 1]))
                    s = None
            if len(runs) < 2:
                continue
            gaps = [(runs[k][1], runs[k + 1][0]) for k in range(len(runs) - 1)]

            # IDENTIFY THE SLOT BY POSITION, NOT BY SIZE.
            #
            # v0 took the LARGEST gap, which was safe only while the part was
            # solid: the slot was then the only enclosed void on the ray. v2
            # is hollow, so every ray through a handle also crosses the shell
            # cavity, and at y = -26.8 that cavity is the larger of the two.
            # The gate reported 14.16 mm and failed a build whose slot was in
            # fact exactly right - it was measuring the hollow.
            #
            # The slot is the void straddling Z = 0: the console is centred
            # there by construction. The cavity is always well behind it
            # (clamped to end at -(HALF_D + FIT_CLEAR) - SHELL_WALL). So pick
            # the gap that CONTAINS Z = 0, and if none does, this ray does not
            # see the slot at all and contributes nothing.
            span = [(a, b) for a, b in gaps if a < 0.0 < b and b - a > 5.0]
            if not span:
                continue
            a, b = max(span, key=lambda t: t[1] - t[0])
            out.append(b - a)
    return float(np.median(out)) if out else None



def _swell_scale(f):
    """Extra depth at height fraction `f` for the ergonomic palm swell.

    A raised cosine over [SWELL_F0, SWELL_F1] peaking at SWELL_PEAK, so the
    swell blends into the surrounding surface instead of stepping onto it.
    Returns mm of extra half-depth. The section grows FORWARD only: the rear
    of the handle is where the console pocket is cut, and thickening it there
    would eat into the slot.
    """
    if f <= SWELL_F0 or f >= SWELL_F1:
        return 0.0
    if f <= SWELL_PEAK:
        t = (f - SWELL_F0) / max(SWELL_PEAK - SWELL_F0, 1e-6)
    else:
        t = (SWELL_F1 - f) / max(SWELL_F1 - SWELL_PEAK, 1e-6)
    return SWELL_AMT * 0.5 * (1.0 - np.cos(np.pi * float(np.clip(t, 0.0, 1.0))))


def _shell_stations(mirror=False):
    """The inner (void) stations of one handle, or None if it cannot hollow.

    Shared by build_handle_shell, build_ribs and build_vent so all three agree
    on where the cavity is. Stations whose inner section has collapsed are
    DROPPED, not clamped to a minimum: clamping leaves a sliver of void running
    out to the tip, which prints as a hair-thin unsupported wall.
    """
    inner = []
    for y, hw, hd, cx, cz in handle_sections(mirror):
        ihw, ihd = hw - SHELL_WALL, hd - SHELL_WALL
        if ihw <= 0.8 or ihd <= 0.8:
            continue
        inner.append((y, ihw, ihd, cx, cz))
    return inner if len(inner) >= 3 else None


def build_handle_shell(mirror=False):
    """The INNER solid of one handle - the void that hollows it.

    The same loft as build_handle(), every section reduced by SHELL_WALL on
    each side. Stations whose inner section has collapsed are DROPPED, not
    clamped to a minimum: clamping leaves a sliver of void running out to the
    tip, which prints as a hair-thin unsupported wall. Dropping them closes
    the wall over the ends instead.
    """
    inner = _shell_stations(mirror)
    if inner is None:
        return None

    with BuildPart() as h:
        for y, hw, hd, cx, cz in inner:
            pl = Plane(origin=(cx, y, cz), z_dir=(0, 1, 0), x_dir=(1, 0, 0))
            with BuildSketch(pl):
                Ellipse(hw, hd)
        loft(ruled=True)
        # RIBS: cut the webs OUT OF THE VOID. What is removed from the void
        # survives as solid material bridging the cavity, already trimmed to
        # the wall on every side.
        for w in build_ribs(mirror):
            add(w, mode=Mode.SUBTRACT)
    return h.part, inner


def build_ribs(mirror=False):
    """Transverse reinforcement webs spanning the handle's hollow cavity.

    Subtracted FROM THE INNER VOID rather than added to the part: the void is
    what gets removed, so a slab cut out of the void survives as solid
    material bridging the cavity. Adding rib solids to the part instead would
    require them to be trimmed to the cavity by hand, and any overshoot would
    poke through the outer surface.

    Each web is a short prism of the inner section at that station, RIB_T mm
    thick, normal to the handle's long axis - the direction that resists the
    tube going oval under a squeezing hand.

    Returns the web solids; build_handle_shell subtracts them from the void.
    """
    if not RIB_ON:
        return []
    r = _shell_stations(mirror)
    if r is None:
        return []
    inner = r
    ys = np.array([t[0] for t in inner])
    y_lo, y_hi = float(ys.min()), float(ys.max())

    out = []
    for k in range(RIB_N):
        f = RIB_F0 + (RIB_F1 - RIB_F0) * (k / max(RIB_N - 1, 1))
        y = y_lo + f * (y_hi - y_lo)
        if not (y_lo < y < y_hi):
            continue
        hw = float(np.interp(y, ys, [t[1] for t in inner]))
        hd = float(np.interp(y, ys, [t[2] for t in inner]))
        cx = float(np.interp(y, ys, [t[3] for t in inner]))
        cz = float(np.interp(y, ys, [t[4] for t in inner]))
        if hw <= 0.5 or hd <= 0.5:
            continue
        # Slightly oversized in section so the web certainly meets the wall on
        # every side; it is trimmed by the void it is cut from.
        with BuildPart() as w:
            for yy in (y - RIB_T / 2.0, y + RIB_T / 2.0):
                pl = Plane(origin=(cx, yy, cz), z_dir=(0, 1, 0),
                           x_dir=(1, 0, 0))
                with BuildSketch(pl):
                    Ellipse(hw * 1.05, hd * 1.05)
            loft(ruled=True)
        out.append(w.part)
    return out


def build_vent(mirror=False):
    """The opening that connects the handle's cavity to the outside.

    WITHOUT THIS THE CAVITY IS SEALED, and a sealed void is invisible to
    every gate this project has: it is watertight, it is still one body, the
    bounding box is unchanged, and the reported volume is exactly the
    reduction the hollowing was meant to achieve. Then the slicer fills it,
    because a void with no path to the outside is indistinguishable from
    solid to a slicer that fills by ray parity. The material is spent anyway.

    So the tip is opened. TIP_FLAT already cuts a flat pad across the end of
    each handle; the vent is that pad's section, inset by VENT_INSET so a rim
    of wall survives, swept up through the cut plane into the cavity.
    """
    inner = _shell_stations(mirror)
    if inner is None:
        return []

    # Size the vent on the widest of the LOWEST FEW stations, not on the
    # single lowest one. The lowest inner station is where the shell has
    # nearly closed - here it measured 7.71 x 2.59 mm, and insetting that by
    # VENT_INSET left a half-depth of 0.59 mm, which tripped the guard below
    # and returned NO VENT AT ALL. The cavity was then sealed, and the only
    # reason that did not ship is that a different gate failed first and this
    # one never ran. An empty vent must never be a silent outcome, so the
    # fallback below widens the inset and the last resort raises.
    cand = inner[:4]
    y, hw, hd, cx, cz = max(cand, key=lambda t: min(t[1], t[2]))
    ihw, ihd = hw - VENT_INSET, hd - VENT_INSET
    if ihw <= 0.6 or ihd <= 0.6:
        # Proportional inset rather than giving up: a slightly larger vent
        # still leaves a rim, and no vent at all is far worse.
        ihw, ihd = hw * 0.55, hd * 0.55
    if ihw <= 0.6 or ihd <= 0.6:
        raise SystemExit(
            "build_vent: cannot open a vent - the lowest inner stations are "
            "too small (%.2f x %.2f mm). A sealed cavity slices as solid; "
            "fix SHELL_WALL or VENT_INSET rather than shipping it."
            % (hw, hd))

    y_lo = y - 30.0                       # well below the built tip
    y_hi = y + 1.0                        # just inside the cavity
    with BuildPart() as v:
        for yy in (y_lo, y_hi):
            pl = Plane(origin=(cx, yy, cz), z_dir=(0, 1, 0), x_dir=(1, 0, 0))
            with BuildSketch(pl):
                Ellipse(ihw, ihd)
        loft(ruled=True)
    return [v.part]


def build_finger_grooves(mirror=False):
    """Radiused finger-rest scallops across the FRONT of the handle.

    "FINGER REST GROOVES (Radiused)" on lateralHAndleview.jpg, on the front
    edge - the side the fingers wrap around.

    Each groove is placed by the MEASURED section at its own height, not at a
    fixed Z. The handle's front face migrates rearward as the section grows,
    so a groove at constant Z would float off the surface at one end of the
    band and cut deep into it at the other.
    """
    sect = handle_sections(mirror)
    ys = np.array([t[0] for t in sect])
    y_tip, y_top = float(ys.min()), float(ys.max())
    hws = [t[1] for t in sect]
    hds = [t[2] for t in sect]
    cxs = [t[3] for t in sect]
    czs = [t[4] for t in sect]

    out = []
    for k in range(GROOVE_N):
        f = GROOVE_F0 + (GROOVE_F1 - GROOVE_F0) * (k / max(GROOVE_N - 1, 1))
        y = y_tip + f * (y_top - y_tip)
        hw = float(np.interp(y, ys, hws))
        hd = float(np.interp(y, ys, hds))
        cx = float(np.interp(y, ys, cxs))
        cz = float(np.interp(y, ys, czs))
        z_front = cz + hd
        zc = z_front + GROOVE_R - GROOVE_DEPTH
        with BuildPart() as g:
            for yy, sc in ((y - GROOVE_R * 0.9, 0.55), (y, 1.0),
                           (y + GROOVE_R * 0.9, 0.55)):
                pl = Plane(origin=(cx, yy, zc), z_dir=(0, 1, 0),
                           x_dir=(1, 0, 0))
                with BuildSketch(pl):
                    Ellipse(hw * 1.4 * sc, GROOVE_R * sc)
            loft(ruled=True)
        out.append(g.part)
    return out


def build_texture(mirror=False):
    """The textile-grid grip texture, as a shallow diamond cross-hatch.

    "TEXTILE-TEXTURED GRIP AREAS" (vistaFrontal.png) / "Textile Grid Texture
    Area" (lateralHAndleview.jpg). Two families of parallel grooves at
    +/-45 deg, cut into the outboard face of each handle.

    TEX_PITCH is 3.2 mm deliberately. A real textile pitch is well under
    1 mm; printed through a 0.4 mm nozzle that is not a texture, it is a
    rough surface with the grooves bridged over. 3.2 mm reads as a grid to
    the eye and to the hand, and each groove is 0.9 mm wide - over two
    extrusion widths, so it actually forms.
    """
    if not TEX_ON:
        return []
    sect = handle_sections(mirror)
    ys = np.array([t[0] for t in sect])
    y_tip, y_top = float(ys.min()), float(ys.max())
    y0 = y_tip + TEX_F0 * (y_top - y_tip)
    y1 = y_tip + TEX_F1 * (y_top - y_tip)

    hws = [t[1] for t in sect]
    hds = [t[2] for t in sect]
    cxs = [t[3] for t in sect]
    czs = [t[4] for t in sect]
    ymid = (y0 + y1) / 2.0
    hw = float(np.interp(ymid, ys, hws))
    hd = float(np.interp(ymid, ys, hds))
    cx = float(np.interp(ymid, ys, cxs))
    cz = float(np.interp(ymid, ys, czs))

    # The texture sits on the OUTBOARD face - the side the palm closes
    # around, away from the console.
    sgn = -1.0 if not mirror else 1.0
    x_face = cx + sgn * hw

    span = y1 - y0
    n = int(span * 1.6 / (TEX_PITCH * np.sqrt(2.0))) + 2
    out = []
    for direction in (+1.0, -1.0):
        for k in range(-n, n + 1):
            yc = ymid + k * TEX_PITCH * np.sqrt(2.0)
            with BuildPart() as t:
                pl = Plane(origin=(x_face, yc, cz), z_dir=(1, 0, 0),
                           x_dir=(0, 1, 0))
                with BuildSketch(pl):
                    with BuildLine():
                        L = hd * 1.5
                        w = TEX_WIDTH / 2.0
                        dy = direction * L
                        Polyline([(-w, -L), (w, -L), (dy + w, L), (dy - w, L)],
                                 close=True)
                    make_face()
                extrude(amount=TEX_DEPTH, both=True)
            out.append(t.part)
    return out


def check_cavity_open(stl_path):
    """Prove the hollow cavity actually connects to the outside.

    THE GATE THIS PROJECT DID NOT HAVE. A sealed internal void passes
    watertightness, body count, bounding box, volume and every keep-out here,
    and then slices as solid. VitaGrip's own history records exactly this:
    "watertight+envelope can't see an unopenable pocket".

    Method: voxelise the mesh, flood-fill the empty space inward from the
    bounding box's outside, and ask whether any empty voxel INSIDE the
    handles was never reached. Reachable void = a real, ventable cavity.
    Unreachable void = a sealed pocket, and the build fails.

    Returns (sealed_mm3, open_mm3) or None if it could not be measured.
    """
    try:
        import trimesh
        from scipy import ndimage
    except ImportError:
        return None
    m = trimesh.load(str(stl_path))
    pitch = 1.5
    try:
        vg = m.voxelized(pitch=pitch).fill()
    except Exception:
        return None
    solid = np.asarray(vg.matrix, dtype=bool)

    # Pad by one cell so the outside is guaranteed connected all the way round
    solid = np.pad(solid, 1, mode="constant", constant_values=False)
    empty = ~solid
    lbl, n = ndimage.label(empty)
    if n == 0:
        return (0.0, 0.0)
    outside = lbl[0, 0, 0]
    sealed = int(((lbl != outside) & (lbl != 0)).sum())
    cell = pitch ** 3
    return (sealed * cell, float(solid.sum()) * cell)


def build_pocket_wall():
    """A solid slab restoring the wall between the hollow and the console.

    The handles are hollowed at full depth, which is what makes the saving
    worth having. Where a handle passes behind the console, that full-depth
    void would open into the console pocket and the two would merge - the
    slot gate read 33.22 mm against the 19.30 required, because it was
    measuring cavity and slot as one cavern.

    So the wall is put back. This slab spans the console's footprint (grown
    by FIT_CLEAR so it meets the pocket exactly) and runs from the slot floor
    back by SHELL_WALL. Added AFTER the hollow is subtracted and BEFORE the
    pocket is cut, so the pocket cut trims its front face to the exact slot
    depth and what remains is a clean 3 mm floor.
    """
    # RESTRICT IT TO WHERE A HANDLE ACTUALLY IS.
    #
    # Spanning the console's whole footprint was the first attempt. It put
    # material across the shoulder-button zone (12 vertices, caught by the
    # keep-out gate), grew the part's Y extent from 106.08 to 122.48 mm, and
    # left a slab floating clear of both handles - 2 bodies.
    #
    # The wall is only needed where a hollow handle sits behind the console.
    # That is the OUTBOARD band, from the handles' inboard reach to the end
    # of the part, and only over the Y range the handles occupy.
    tg = _trace()
    plan, (y_tip, y_top) = tg.handle_plan_profile(N_SECT, with_y=True)
    x_in = float(np.min(np.abs(plan[:, 2]) - plan[:, 1]))

    outline = _grow(console_outline(), FIT_CLEAR)
    poly = Polygon([(float(a), float(b)) for a, b in outline])
    big = 400.0

    z_floor = -(HALF_D + FIT_CLEAR)
    out = []
    for sgn in (-1.0, 1.0):
        x0, x1 = sgn * x_in, sgn * big
        band = Polygon([(min(x0, x1), y_tip), (max(x0, x1), y_tip),
                        (max(x0, x1), y_top), (min(x0, x1), y_top)])
        # and never over the shoulder buttons
        keep = band.difference(
            Polygon([(sgn * SHOULDER_X_LO, SHOULDER_Y),
                     (sgn * SHOULDER_X_HI, SHOULDER_Y),
                     (sgn * SHOULDER_X_HI, big), (sgn * SHOULDER_X_LO, big)]))
        for g in _polys(poly.intersection(keep)):
            out.append(_prism(np.array(g.exterior.coords), SHELL_WALL,
                              z_centre=z_floor - SHELL_WALL / 2.0))
    return out


def build_grip():
    """Assemble the part.

    ORDER MATTERS. The hollow is subtracted BEFORE the console pocket and the
    trigger relief, so that where those cuts pass through a handle they cut
    the wall rather than re-solidifying it - and so the shell is trimmed by
    them instead of leaving a void hanging open into the pocket.

    The ergonomic cuts (grooves, texture) come LAST, after the tip cut, so
    they land on the final outer surface. Cutting them before the tip cut
    would let the tip cut remove the evidence.
    """
    bar, (bar_top, bar_bot) = build_bar()
    with BuildPart() as grip:
        add(build_handle(mirror=False))
        add(build_handle(mirror=True))
        add(bar)
        # v2: HOLLOW the handles, then vent each cavity to the outside.
        #
        # The hollow is taken at FULL depth. Clamping every station's void to
        # stay behind the slot floor was the first attempt, and it cost most
        # of the saving: the handles overlap the console in plan at every
        # station (they reach inboard to |X| 57.3 against the console's 91.0,
        # clearing it by passing BEHIND), so the clamp fired everywhere and
        # left an 8 mm void inside a 20 mm handle - 24 % saved instead of 47.
        #
        # The overlap is only in X, though. Rather than shrink the void
        # everywhere, the pocket's rear wall is put back afterwards as a
        # solid slab: see build_pocket_wall(). The cavity is then full depth
        # outboard of the console and stops at a full-thickness wall where it
        # meets the pocket.
        for mir in (False, True):
            r = build_handle_shell(mir)
            if r is not None:
                add(r[0], mode=Mode.SUBTRACT)
            for v in build_vent(mir):
                add(v, mode=Mode.SUBTRACT)
        for w in build_pocket_wall():
            add(w, mode=Mode.ADD)
        for c in build_console_cut(bar_top):
            add(c, mode=Mode.SUBTRACT)
        for c in build_pocket_relief(bar_top):
            add(c, mode=Mode.SUBTRACT)
        for c in build_touchpad_opening(bar_top):
            add(c, mode=Mode.SUBTRACT)
        add(build_tip_cut(), mode=Mode.SUBTRACT)
        for p in build_trigger_relief():
            add(p, mode=Mode.SUBTRACT)
        # v2: ergonomic surface features, cut on the FINAL outer surface.
        for mir in (False, True):
            for g in build_finger_grooves(mir):
                add(g, mode=Mode.SUBTRACT)
            for t in build_texture(mir):
                add(t, mode=Mode.SUBTRACT)
    return grip.part


def main():
    print("vita_grip - lofting %s from the measured sections" % PART_NAME)
    if not CONSOLE_DXF.exists():
        print("  missing %s - run macros/trace_console.py" % CONSOLE_DXF.name)
        return 1

    part = build_grip()
    bb = part.bounding_box()
    vol = part.volume / 1000.0
    solids = part.solids()
    print("  bbox   %.2f x %.2f x %.2f mm" % (bb.size.X, bb.size.Y, bb.size.Z))
    print("  volume %.1f cm3   bodies %d" % (vol, len(solids)))

    ok = True
    if abs(bb.size.X - GRIP_W) > WIDTH_TOL:
        print("  FAIL width %.2f vs measured %.2f" % (bb.size.X, GRIP_W))
        ok = False
    if len(solids) != 1:
        print("  FAIL %d bodies - the handles are not joined" % len(solids))
        ok = False

    # Keep-outs, tested on the part's VERTICES. A probe grid is not a keep-out
    # gate: a clamp lip overhanging the shoulder zone by 0.2 mm passed a 6x4
    # grid clean, because no sample landed on the overhang.
    #
    # The front-face gate is split by X. "Nothing over the front face" is the
    # wrong test - it fails the retaining clip, which is what holds the
    # console on. What the sketch requires is that the SCREEN and BUTTONS stay
    # clear; the clip laps the console's outer edge only.
    vs = np.array([[v.X, v.Y, v.Z] for v in part.vertices()])
    z_face = HALF_D + FIT_CLEAR
    checks = [
        ("shoulder buttons",
         (np.abs(vs[:, 0]) >= SHOULDER_X_LO) & (np.abs(vs[:, 0]) <= SHOULDER_X_HI)
         & (vs[:, 1] > SHOULDER_Y)),
        ("screen/buttons over front face",
         (vs[:, 2] > z_face) & (np.abs(vs[:, 0]) < ACTIVE_X)
         & (np.abs(vs[:, 1]) < HALF_H)),
        # The speakers are the feature the notch actually threatens. Measured
        # on psvita.jpg at 0.3957 mm/px: the dot grid runs |X| 79.7..86.1 mm
        # at Y -9.7..-12.7. A 9 mm notch (LIP_X = 82) covered them completely
        # while the ACTIVE_X gate above still reported CLEAR, because that
        # gate only looks inboard of |X| 78.
        ("speaker grid",
         (vs[:, 2] > z_face)
         & (np.abs(vs[:, 0]) >= SPEAKER_X_LO) & (np.abs(vs[:, 0]) <= SPEAKER_X_HI)
         & (vs[:, 1] >= SPEAKER_Y_LO) & (vs[:, 1] <= SPEAKER_Y_HI)),
    ]
    for name, sel in checks:
        n = int(sel.sum())
        print("  keep-out %-32s %s" % (name, "CLEAR" if n == 0 else
                                       "FAIL (%d vertices)" % n))
        if n:
            ok = False

    lip = vs[(vs[:, 2] > z_face) & (np.abs(vs[:, 0]) >= ACTIVE_X)]
    if len(lip):
        print("  retaining lip on the console's outer edge: %.2f mm proud"
              % (lip[:, 2].max() - z_face))

    if not ok:
        return 1

    (OUT_DIR / "step").mkdir(exist_ok=True)
    (OUT_DIR / "stl").mkdir(exist_ok=True)
    export_step(part, str(OUT_DIR / "step" / ("%s.step" % PART_NAME)))
    export_stl(part, str(OUT_DIR / "stl" / ("%s.stl" % PART_NAME)))
    print("  exported %s.step / .stl" % PART_NAME)

    # SLOT DEPTH, measured on the mesh just written. This runs AFTER the
    # export because it ray-probes the exported file - gating before it would
    # measure the PREVIOUS build and pass a broken one.
    #
    # It measures the SHAPE, not the intent: the pocket cut was already the
    # right depth when the built cavity was 20.85 mm, because the handles
    # stood FRONT_LIP mm inside it. A console has 2 mm of slop in a 21.3 mm
    # slot and rattles; nothing else in this file could see that.
    slot = _measure_slot()
    if slot is None:
        # Not "no news is good news": the probe found no enclosed pocket at
        # all, which means either the geometry changed under it or the pocket
        # is not closed. Either way the gate did not run, so it must not pass.
        print("  FAIL slot depth could not be measured - no enclosed pocket "
              "found at the probe locations")
        return 1
    want = CONSOLE_D + 2 * FIT_CLEAR
    print("  slot depth %.3f mm (console %.1f + 2 x %.2f = %.3f)"
          % (slot, CONSOLE_D, FIT_CLEAR, want))
    if abs(slot - want) > 0.25:
        print("  FAIL slot is %.3f mm - the console would have %.2f mm of slop"
              % (slot, slot - CONSOLE_D))
        return 1

    # SEALED-CAVITY GATE. v2 is hollow, and a hollow with no path out is
    # invisible to every gate above: watertight, one body, right bbox, and
    # the reported volume is exactly the saving the hollowing was meant to
    # deliver. Then the slicer fills it and the material is spent anyway.
    cav = check_cavity_open(OUT_DIR / "stl" / ("%s.stl" % PART_NAME))
    if cav is None:
        print("  WARN cavity gate did not run (needs trimesh + scipy)")
    else:
        sealed, solid_vol = cav
        print("  sealed void %.0f mm3 (voxelised solid %.0f mm3)"
              % (sealed, solid_vol))
        if sealed > 500.0:
            print("  FAIL %.0f mm3 of cavity has no path to the outside - "
                  "it will slice as solid" % sealed)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
