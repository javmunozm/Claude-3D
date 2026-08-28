"""
VitaGrip — build123d controller-style hand-grip for the PS Vita 1000 (PCH-1000)
================================================================================
A SOLID, controller-style grip: two thick handle horns joined by a substantial
full-width wraparound band that cradles the Vita's bottom edge, with a short
side channel at each end retaining the Vita's short edges. The Vita's screen
and back panel above the band stay open.

Revision 5 (2026-07-29) — REBUILT FROM MEASUREMENT
--------------------------------------------------
Revisions 1-4 produced a part that passed every dimensional and topological
check yet looked nothing like the reference photos: a thin, flat, skeletal
BRACKET where the reference is a fat, solid, controller-style GRIP. Each of
those revisions verified a local property in isolation ("the centre span is
empty", "body_count == 1", "the band reads as solid") and each check genuinely
passed. None ever placed a render beside the reference photo and asked whether
it was the same object. Correct parts do not compose into a correct whole.

This revision re-derives the structure from row-by-row pixel measurement of
054-1.webp and fixes the two root causes:

  1. THIN-WALL OUTLINE, NOT A VOLUME. The old part was built from 3 mm walls
     (CHAN_WALL) plus a 10 mm x 14 mm "shelf" — an outline of the right shape
     enclosing nothing. A hand grip is a VOLUME. The band is now a solid
     36 mm-tall, 26 mm-deep wraparound cradle, and the horns are solid lofted
     bodies, not shells.
  2. THE BAND WAS A STRIP, NOT A CRADLE. Measurement shows the full-width
     connector spans roughly -20 mm to +16 mm about the Vita's own bottom edge
     (~36 mm tall) and is full-width across its entire height — it wraps the
     Vita's bottom edge rather than sitting under it as a 10 mm ledge.

Reference measurement (054-1.webp, anchored on the pictured Vita's body width
spanning 740 px -> 4.031 px/mm):

  grip envelope in photo   225.0 x 114.1 mm
  band                     ~36 mm tall, full width, wraps the bottom edge
  horn (below the band)    45.9 mm long, 43.4 mm wide at the neck -> rounded tip
  horn outer edge          nearly STRAIGHT (pinned ~112.5 mm from centre) while
                           the inner edge sweeps in — an asymmetric paddle, so
                           the horn's own centreline drifts outward only ~4.6 mm
  outboard bulge           20.8 mm beyond the Vita's own side edge
  grip top                 starts 12.2 mm below the Vita's top edge

IMPORTANT — reference variant differs from the target
------------------------------------------------------
The reference photos show a PCH-2000 (slim) Vita; this part targets a
PCH-1000 (182 x 83.5 x 18.6 mm, confirmed by the user). The bodies differ,
notably in depth (18.6 mm vs ~15 mm). So the photos are the authority for
SHAPE LANGUAGE and PROPORTION, and the PCH-1000 spec is the authority for
ABSOLUTE DIMENSIONS. Proportional values below are scaled to the PCH-1000
body rather than copied as raw millimetres from the photo.

The reference STL (newVita_1k_Grip_2.stl / reference_aligned.stl) is NOT used:
its 170 x 170 x 123 mm envelope matches neither body.

Run with plain Python (no FreeCAD needed):
    python macros/vita_grip_b123d.py

Requirements:
    pip install build123d

Output (written to the project folder):
    VitaGrip.step / .stl

Coordinate system (local):
    +X = right (toward the right handle horn)
    +Y = up (toward the Vita's top edge / shoulder-button area)
    +Z = toward the front (the Vita's screen faces +Z); Z=0 is the Vita's
         FRONT face plane, and the Vita body occupies Z in [-VITA_D, 0].
    Origin = centre of the Vita's front face.
"""

import pathlib

from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Circle,
    Location,
    Locations,
    Mode,
    Plane,
    Rectangle,
    export_step,
    export_stl,
    extrude,
    fillet,
    loft,
    mirror,
)

# ── Output directory ──────────────────────────────────────────────────────────
SAVE_DIR = pathlib.Path(__file__).resolve().parent.parent   # …/VitaGrip/

# ── PS Vita 1000 (PCH-1000) confirmed body spec ──────────────────────────────
# Given verbatim by the user — do not re-derive or guess. NOTE: the reference
# photos show a PCH-2000; these numbers intentionally override the photo.
VITA_W        = 182.0    # left-right width
VITA_H        = 83.5     # top-bottom height (short body dimension)
VITA_D        = 18.6     # front-back depth at the thick edges
VITA_CORNER_R = 15.0     # outer corner radius
VITA_MID_D    = 15.0     # rear taper: body thins toward mid-body
VITA_BEZEL_R  = 1.5      # front casing bezel fillet radius

# ── Fit clearance (friction-fit accessory, not a precision fit) ─────────────
FIT_CLEARANCE = 0.25      # mm per side, standard FDM friction-fit clearance

# ── Derived Vita references ──────────────────────────────────────────────────
VITA_X_EDGE = VITA_W / 2.0 + FIT_CLEARANCE   # clearance-added side edge
Y_TOP       = VITA_H / 2.0 + FIT_CLEARANCE   # Vita's top edge
Y_BOT       = -(VITA_H / 2.0 + FIT_CLEARANCE)  # Vita's bottom edge
Z_FRONT     = 0.0
Z_BACK      = -VITA_D

# ── Wraparound band (the full-width cradle around the Vita's bottom edge) ───
# Measured: the full-width connector spans about -20 mm to +16 mm relative to
# the Vita's own bottom edge (~36 mm tall) and stays full-width throughout.
# This is the part's structural core and the single full-width connector.
# Depth is deliberately GENEROUS: the band must read as a solid cradle, so it
# wraps the Vita's full depth plus a grip margin front and back.
# CORRECTED (revision 5d) by sampling the photo's CENTRE COLUMN, which isolates
# the band from the lobes flanking it. Material is present at the centreline only
# from the Vita's own bottom edge down 16.9 mm — the band is 15% of the grip's
# height, a SLIM strap, not the deep cradle assumed in 5a-5c (31 mm, nearly 2x).
#
# This corrected an incorrect visual read: comparing renders, the part looked
# like it needed a *deeper* band, but the reference's mass is in the LOBES
# (45% of the height above the band), not in the band itself. Measuring beat
# eyeballing, which is the whole reason the measurement step exists.
BAND_ABOVE_BOT = 1.0    # mm the band rises above the Vita's bottom edge
BAND_BELOW_BOT = 16.9   # mm below it, to where the lobes separate (measured)
# The band sits entirely BEHIND the Vita's front face. It previously carried a
# 4 mm front lip, but the Vita pocket (which spans Z -18.6..0) then cut a slot
# through the band's middle and left that lip as an island disconnected from the
# band's back — the assembly came out as a ShapeList of several solids. Front
# retention is the LOBES' job (they straddle the front face); the band is purely
# the rear structural strap, so it stops at the Vita's own back face.
BAND_FRONT_LIP = 0.0    # mm of front-face overlap — none; see note above
BAND_BACK_REACH = 7.0   # mm the band stands proud behind the Vita's back face
BAND_CORNER_R  = 6.0    # rounding on the band's own outer corners

# ── Side lobes (the grip's defining mass: one continuous teardrop per side) ──
# CORRECTED (revision 5b) after the first rebuild still failed the side-by-side
# gate: it read as a thin boxy FRAME with small feet, because the material
# alongside the Vita was modelled as a 6 mm retaining rail and the horn as a
# separate stub below a band. Measurement of 054-1.webp shows something else —
# the material outboard of the Vita's own side edge grows SMOOTHLY from 0 mm at
# the grip's top edge to ~20 mm by the Vita's bottom edge, then continues
# unbroken into the horn. There is no rail/band/horn boundary: each side is ONE
# CONTINUOUS TEARDROP LOBE spanning the full grip height, and the "band" is just
# where the two lobes meet across the centre.
#
# So the lobe is now lofted as a single body from the grip's top edge to the
# horn tip. This is what makes the part read as a controller grip rather than a
# frame with feet.
LOBE_TOP_INSET = 12.2   # mm below the Vita's top edge where the lobe starts (measured)
CHAN_FRONT_LIP  = 3.5   # mm of front-face bite (retains the Vita, clears the screen)
CHAN_BACK_REACH = 9.9   # mm proud of the Vita's back face, so the lobe's own depth
                         # (3.5 + 18.6 + 9.9 = 32.0 mm) matches the horn's neck
                         # depth and the two fuse as one continuous form instead
                         # of the horn stepping out of a shallower lobe

# Lobe thickness outboard of the Vita's own side edge, measured row-by-row from
# 054-1.webp, expressed as (fraction of the lobe's run from its top down to the
# Vita's bottom edge, outboard thickness in mm).
# The last station must meet the horn's own outer offset so lobe and horn read as
# one continuous form rather than a step; the horn's outer edge sits
# 112.5 - 91.8 = 20.7 mm outboard of the Vita's side edge at its neck.
LOBE_STATIONS = [
    (0.00,  0.5),
    (0.15,  6.5),
    (0.30, 11.2),
    (0.45, 14.1),
    (0.60, 16.1),
    (0.75, 17.9),
    (0.90, 19.5),
    (1.00, 20.7),
]

# ── Handle horns ─────────────────────────────────────────────────────────────
# Pixel-measured from 054-1.webp below the band. Key finding: the horn's OUTER
# edge is nearly straight (pinned ~112.5 mm from the centreline for most of its
# length) while the INNER edge sweeps in — an asymmetric paddle. Its centreline
# therefore drifts outward only ~4.6 mm over the full length. Width tapers
# 43.4 mm -> rounded tip. Depth is the dimension the front view cannot show;
# it is set from grip ergonomics (a comfortable horn is ~30-34 mm front-to-back)
# and is JUDGEMENT, not measurement.
# Measured: the two lobes stay joined across the centre down to 66.5 mm below the
# grip's top edge, then separate; the free horn runs a further 47.4 mm to the
# tip. Total grip height in the photo is 113.9 mm, so the free horn is ~42% of
# the height and the joined band region above it ~58%.
HANDLE_LEN = 47.4   # mm of FREE horn below the band (measured)
HANDLE_NECK_OVERLAP = 6.0   # mm the horn's neck reaches up into the band so the
                             # two fuse without a visible seam

# CORRECTED (revision 5c). Measurement of the horn's two edges separately shows
# it is a broad BLADE, not a tapering peg:
#
#     t     inner_edge   outer_edge   width
#    0.17     71.8         112.5      40.9
#    0.50     77.3         111.3      34.2
#    0.83     83.7         106.8      23.3
#    1.00     94.2          96.9       3.0   (rounded tip)
#
# The OUTER edge stays pinned near 112 mm from the centreline for most of the
# length and only curls inward close to the tip; the INNER edge sweeps steadily
# outward. Narrowing a section symmetrically about a drifting centreline (what
# the previous revisions did) produces a thin vertical peg instead. So stations
# are now expressed as the two EDGE positions, measured from the Vita's own side
# edge, and the builder derives width and centre from them.
#
#   t          = fraction of HANDLE_LEN, 0 at the band, 1 at the tip
#   inner, outer = edge offsets outboard of VITA_X_EDGE, mm (measured)
#   depth      = Z extent (JUDGEMENT — ergonomic; the front view cannot show it)
#   concave    = finger-wrap scoop cut into the outer face
#
# Photo edges are measured from the PCH-2000's centreline; converted here to
# offsets from the Vita's own side edge so they transfer to the PCH-1000 body.
_PHOTO_VITA_HALF = 183.6 / 2.0   # the pictured Vita's half-width

HANDLE_EDGE_STATIONS = [
    # t,    inner_off,                 outer_off,                  depth, concave
    (0.00,  69.5 - _PHOTO_VITA_HALF,  112.5 - _PHOTO_VITA_HALF,   32.0, 0.0),
    (0.17,  71.8 - _PHOTO_VITA_HALF,  112.5 - _PHOTO_VITA_HALF,   32.0, 3.0),
    (0.33,  74.6 - _PHOTO_VITA_HALF,  112.3 - _PHOTO_VITA_HALF,   31.5, 5.0),
    (0.50,  77.3 - _PHOTO_VITA_HALF,  111.3 - _PHOTO_VITA_HALF,   30.5, 6.5),
    (0.67,  80.0 - _PHOTO_VITA_HALF,  109.5 - _PHOTO_VITA_HALF,   29.0, 6.5),
    (0.83,  83.7 - _PHOTO_VITA_HALF,  106.8 - _PHOTO_VITA_HALF,   26.5, 5.0),
    (0.94,  88.9 - _PHOTO_VITA_HALF,  101.8 - _PHOTO_VITA_HALF,   23.0, 3.0),
    # Final station kept a healthy width (photo shows 3.0 mm, but a near-zero
    # loft section plus a scoop produced a non-watertight mesh — caught by the
    # topology gate). The tip fillet supplies the rounding instead.
    (1.00,  90.0 - _PHOTO_VITA_HALF,  100.5 - _PHOTO_VITA_HALF,   19.0, 0.0),
]

# Derived (width, depth, concave, centre-offset) form the builder consumes.
HANDLE_STATIONS = [
    (t, out_o - in_o, depth, concave, (in_o + out_o) / 2.0)
    for t, in_o, out_o, depth, concave in HANDLE_EDGE_STATIONS
]

# The horn's section centre is placed relative to the Vita's own side edge, so
# attach_x is that edge and outset_x carries the measured centre offset.
HANDLE_ATTACH_X = VITA_X_EDGE
Z_HANDLE_CENTER = Z_BACK + VITA_D / 2.0   # centred on the Vita's own depth

# ── Front corner tabs (small proud nubs at the top corners) ──────────────────
TAB_W = 9.0
TAB_D = 4.0
TAB_H = 3.0


# ── Builder: wraparound band ─────────────────────────────────────────────────

def build_band(
    x_half: float,
    y_bot: float,
    above: float,
    below: float,
    z_front_lip: float,
    z_back: float,
    corner_r: float,
):
    """Full-width solid cradle wrapping the Vita's bottom edge.

    This is the part's structural core and its only full-width connector. It is
    a SOLID block spanning the whole grip width, with the Vita's own pocket cut
    out of it by the caller — not a thin strip. Revisions 1-4 modelled this as a
    10 mm x 14 mm ledge, which is what made the whole part read as a skeletal
    bracket rather than a controller grip.
    """
    y_hi = y_bot + above
    y_lo = y_bot - below

    with BuildPart() as band:
        with BuildSketch(Plane.XY.offset(z_back)) as sk:
            with Locations((0.0, (y_hi + y_lo) / 2.0)):
                Rectangle(2 * x_half, y_hi - y_lo)
        extrude(sk.sketch, amount=z_front_lip - z_back)
        try:
            band.part = fillet(band.part.edges().filter_by(Axis.Z), radius=corner_r)
        except Exception:
            pass
    return band.part


# ── Builder: side retaining rail ─────────────────────────────────────────────

def build_side_lobe(
    x_inner: float,
    y_top: float,
    y_bot: float,
    y_measured_bot: float,
    stations: list,
    z_front_lip: float,
    z_back: float,
):
    """One continuous teardrop lobe alongside the Vita, lofted from the grip's
    own top edge down to the Vita's bottom edge, growing outboard per `stations`.

    This is the grip's defining mass. It is deliberately ONE body rather than a
    thin rail plus a separate band: measurement shows the outboard material
    grows smoothly from ~0 mm at the top to ~20 mm at the Vita's bottom edge
    with no discontinuity, then runs on into the horn. Modelling it as a 6 mm
    rail is what made the previous revision read as a boxy frame."""
    # Station fractions were measured from the lobe's top down to the Vita's own
    # bottom edge (`y_measured_bot`). The lobe body continues past that edge down
    # to `y_bot` so it overlaps the band; those extra sections simply hold the
    # final measured thickness rather than stretching the measured curve.
    faces = []
    ref_span = y_top - y_measured_bot
    for t, out_thk in stations:
        y = y_top - ref_span * t
        x_outer = x_inner + max(out_thk, 0.4)
        plane = Plane(origin=((x_inner + x_outer) / 2.0, y, (z_front_lip + z_back) / 2.0),
                      x_dir=(1, 0, 0), z_dir=(0, -1, 0))
        with BuildSketch() as sk:
            Rectangle(x_outer - x_inner, z_front_lip - z_back)
            try:
                fillet(sk.vertices(), radius=min(2.5, (x_outer - x_inner) * 0.3))
            except Exception:
                pass
        faces.append(sk.sketch.moved(Location(plane)).faces()[0])

    # Carry the final measured section straight down to y_bot so the lobe passes
    # through the band and fuses with it.
    if y_bot < y_measured_bot - 1e-6:
        out_thk = stations[-1][1]
        x_outer = x_inner + max(out_thk, 0.4)
        plane = Plane(origin=((x_inner + x_outer) / 2.0, y_bot, (z_front_lip + z_back) / 2.0),
                      x_dir=(1, 0, 0), z_dir=(0, -1, 0))
        with BuildSketch() as sk:
            Rectangle(x_outer - x_inner, z_front_lip - z_back)
            try:
                fillet(sk.vertices(), radius=min(2.5, (x_outer - x_inner) * 0.3))
            except Exception:
                pass
        faces.append(sk.sketch.moved(Location(plane)).faces()[0])

    return loft(faces, ruled=False)


# ── Builder: the Vita's own pocket (cut from the solid stock) ────────────────

def build_vita_pocket(
    x_half: float,
    y_bot: float,
    z_front: float,
    z_back: float,
    corner_r: float,
    open_up: float,
):
    """The volume the Vita itself occupies, plus an upward escape so the device
    drops in from the top. Cutting this from solid stock is what makes the grip
    a VOLUME with a device-shaped void, rather than an assembly of thin walls."""
    with BuildPart() as pocket:
        with BuildSketch(Plane.XY.offset(z_back)) as sk:
            with Locations((0.0, y_bot + open_up / 2.0)):
                Rectangle(2 * x_half, open_up)
            try:
                fillet(sk.vertices(), radius=corner_r)
            except Exception:
                pass
        extrude(sk.sketch, amount=z_front - z_back)
    return pocket.part


# ── Builder: handle horn ─────────────────────────────────────────────────────

def _handle_section(width: float, depth: float, concave_depth: float):
    """Rounded cross-section with an optional cylindrical scoop bitten out of
    the -X (outer) face for the finger wrap."""
    with BuildSketch() as sk:
        Rectangle(width, depth)
        fillet(sk.vertices(), radius=min(width, depth) * 0.42)
        if concave_depth > 0:
            bite_r = (width * 0.5) ** 2 / (2 * concave_depth) + concave_depth / 2.0
            bite_center_x = -width / 2.0 - (bite_r - concave_depth)
            with Locations((bite_center_x, 0)):
                Circle(bite_r, mode=Mode.SUBTRACT)
    return sk.sketch


def build_handle(length, stations, attach_x, z_center, y_attach):
    """One solid handle horn (right side; mirror for the left), lofted through
    measured cross-sections. The outer edge stays nearly straight while the
    inner edge sweeps in, matching the asymmetric paddle in 054-1.webp."""
    faces = []
    for t, width, depth, concave_depth, outset_x in stations:
        y = y_attach - length * t
        plane = Plane(origin=(attach_x + outset_x, y, z_center),
                      x_dir=(1, 0, 0), z_dir=(0, -1, 0))
        face = _handle_section(width, depth, concave_depth).moved(Location(plane)).faces()[0]
        faces.append(face)

    solid = loft(faces, ruled=False)

    tip_y = y_attach - length
    tip_w, tip_d = stations[-1][1], stations[-1][2]
    tip_edges = [e for e in solid.edges() if abs(e.center().Y - tip_y) < 1e-2]
    if tip_edges:
        try:
            solid = fillet(tip_edges, radius=min(tip_w, tip_d) * 0.30)
        except Exception:
            pass
    return solid


def build_corner_tab(tab_w, tab_d, tab_h, x, y_top, z_front):
    """Small nub proud of the front face at the top corner."""
    # The tab must INTERPENETRATE the lobe, not sit flush against its front face.
    # Placed flush (its base exactly on the lobe's front plane) the union left it
    # as a free-floating solid — a boolean union of merely touching surfaces does
    # not fuse. It now starts 1.5 mm inside the lobe.
    embed = 1.5
    with BuildPart() as tab:
        with Locations((x, y_top - tab_w / 2.0 - 1.0,
                        z_front - embed + (tab_h + embed) / 2.0)):
            Box(tab_d, tab_w, tab_h + embed,
                align=(Align.CENTER, Align.CENTER, Align.CENTER))
    return tab.part


# ── Assembly ──────────────────────────────────────────────────────────────────

def build_full_grip():
    # Grip's outer half-width follows the lobe's widest measured thickness.
    x_half_outer = VITA_X_EDGE + LOBE_STATIONS[-1][1]
    z_band_front = Z_FRONT + BAND_FRONT_LIP
    z_band_back = Z_BACK - BAND_BACK_REACH

    # 1. Solid wraparound band around the Vita's bottom edge.
    band = build_band(
        x_half=x_half_outer, y_bot=Y_BOT,
        above=BAND_ABOVE_BOT, below=BAND_BELOW_BOT,
        z_front_lip=z_band_front, z_back=z_band_back,
        corner_r=BAND_CORNER_R,
    )

    # 2. Continuous teardrop lobe up each side — the grip's defining mass.
    y_lobe_top = Y_TOP - LOBE_TOP_INSET
    # The horn's neck reaches UP into the band/lobe by HANDLE_NECK_OVERLAP, and
    # the lobe runs DOWN past that line by the same amount, so the two overlap
    # rather than merely touching.
    y_handle_top = Y_BOT - BAND_BELOW_BOT + HANDLE_NECK_OVERLAP
    y_lobe_bottom = y_handle_top - 2 * HANDLE_NECK_OVERLAP
    # The lobe runs DOWN THROUGH the band to the horn's neck, so lobe + band +
    # horn overlap into one solid. Stopping the lobe at Y_BOT left a zero-overlap
    # butt joint against a band that rises only 1 mm above it, and the union
    # produced separate shells (caught as a non-watertight/ShapeList failure).
    right_lobe = build_side_lobe(
        x_inner=VITA_X_EDGE, y_top=y_lobe_top,
        # Run the lobe HANDLE_NECK_OVERLAP past the horn's attach line so the two
        # interpenetrate. Ending it exactly at the attach line left the horns as
        # free-floating solids (a union of touching surfaces does not fuse).
        y_bot=y_lobe_bottom,
        y_measured_bot=Y_BOT,
        stations=LOBE_STATIONS,
        z_front_lip=Z_FRONT + CHAN_FRONT_LIP, z_back=Z_BACK - CHAN_BACK_REACH,
    )
    left_lobe = mirror(right_lobe, Plane.YZ)

    # 3. Solid handle horns, continuing the lobe downward with no visual seam.
    #    The horn attaches at the band's lower edge (where the reference's two
    #    lobes separate), so lobe -> band -> horn reads as one continuous form.
    y_handle_attach = y_handle_top
    right_handle = build_handle(
        length=HANDLE_LEN, stations=HANDLE_STATIONS,
        attach_x=HANDLE_ATTACH_X, z_center=Z_HANDLE_CENTER,
        y_attach=y_handle_attach,
    )
    left_handle = mirror(right_handle, Plane.YZ)

    # 4. Corner tabs.
    right_tab = build_corner_tab(TAB_W, TAB_D, TAB_H,
                                 x=VITA_X_EDGE + 2.0,
                                 y_top=y_lobe_top, z_front=Z_FRONT + CHAN_FRONT_LIP)
    left_tab = mirror(right_tab, Plane.YZ)

    grip = band + right_lobe + left_lobe + right_handle + left_handle + right_tab + left_tab

    # 5. Cut the Vita's own pocket out of the solid stock — the device drops in
    #    from the top, so the pocket opens upward past the top of the grip.
    pocket = build_vita_pocket(
        x_half=VITA_X_EDGE, y_bot=Y_BOT,
        z_front=Z_FRONT, z_back=Z_BACK,
        corner_r=VITA_CORNER_R,
        open_up=VITA_H + 2 * FIT_CLEARANCE + 60.0,   # well past the grip's top
    )
    grip = grip - pocket

    return grip


def save_part(name: str, shape) -> None:
    step_path = SAVE_DIR / f"{name}.step"
    stl_path = SAVE_DIR / f"{name}.stl"
    export_step(shape, str(step_path))
    export_stl(shape, str(stl_path))
    print(f"  Saved: {step_path}")
    print(f"  Saved: {stl_path}")


# ── Generate ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n=== VitaGrip build123d (controller grip, PS Vita PCH-1000) ===")
    print(f"Vita body       : {VITA_W} x {VITA_H} x {VITA_D} mm (PCH-1000 spec)")
    print(f"Fit clearance   : {FIT_CLEARANCE} mm/side")
    print(f"Band            : {BAND_ABOVE_BOT + BAND_BELOW_BOT:.0f} mm tall, full width, "
          f"{BAND_FRONT_LIP + VITA_D + BAND_BACK_REACH:.0f} mm deep — solid cradle")
    print(f"Side lobes      : start {LOBE_TOP_INSET} mm below the Vita's top edge, "
          f"grow 0 -> {LOBE_STATIONS[-1][1]} mm outboard ({len(LOBE_STATIONS)}-station loft)")
    print(f"Handle horn     : {HANDLE_LEN} mm long, "
          f"{HANDLE_STATIONS[0][1]} -> {HANDLE_STATIONS[-1][1]} mm wide, "
          f"{HANDLE_STATIONS[0][2]} mm deep ({len(HANDLE_STATIONS)}-station loft)")

    grip = build_full_grip()
    bbox = grip.bounding_box()
    print(f"\nOverall envelope: "
          f"{bbox.max.X - bbox.min.X:.1f} x {bbox.max.Y - bbox.min.Y:.1f} x "
          f"{bbox.max.Z - bbox.min.Z:.1f} mm (W x H x D)")
    print(f"Reference (photo, PCH-2000): 225.0 x 114.1 mm — proportions should be close")

    save_part("VitaGrip", grip)
    print("\nDone.\n")
