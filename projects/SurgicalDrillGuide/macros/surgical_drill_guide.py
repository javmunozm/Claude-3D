"""SurgicalDrillGuide (rebuild, 2026-09-23): ratcheting K-wire / drill guide, three printed parts.

Replaces the v1 macro (snapshot: attempts/v1-zbore-separate-parts/macros/). v1 bored the wire through the
part THICKNESS (Z) and had no long bar; this rebuild follows the confirmed topology (docs/MEASUREMENTS.md §1-2):

    main_frame    C-hook + long bottom bar + toothed rack, ONE part. Closed C-tip wire bore on the rectified
                  wire line. Boss with a FEMALE thread under the bar for the handle.
    l_arm_slider  riser + top bar + V crown (rectified L) + collar + carriage, ONE part. Slides on the rack.
                  Wire bore along the FULL top bar. Integral compliant (flexure) pawl + release tab.
    handle        revolved grip + ferrule + MALE thread. Separate, removable, fully printed.

EVERY in-plane (XY) outline is imported at build time from vectors/import/*.dxf (vector-tracer 2026-09-23,
accuracy-reviewed). No primitive stands in for a traced outline. Primitives are used only for DESIGNED features
that no photo shows (bores, rack channel, teeth, pawl, boss, thread) and for fusion-overlap blocks that sit
entirely inside a traced outline (they change no silhouette).

Coordinate frame = the vector datum (vectors/README.md): origin at the rack left tip on the rack top edge,
+X along the rack towards the hook, +Y up, +Z = instrument thickness. Z = 0 is the frame's bed face.
This deliberately departs from the repo's "origin at bottom-face centre" convention: all three parts share the
traced datum so the assembly poses and the coaxiality gate need no re-derived placement.

Status words on constants: MEASURED / DERIVED (from rings at build time) / ASSUMED (no measurement exists;
user decision or design choice) / DESIGNED (a substitution for something the photos do not show) /
PLACEHOLDER (a clearance that print-tolerance-expert must set).

Run:  python "D:\\CAD\\Claude-Projects\\projects\\SurgicalDrillGuide\\macros\\surgical_drill_guide.py"
Gates: python "D:\\CAD\\Claude-Projects\\projects\\SurgicalDrillGuide\\macros\\sdg_gates.py"
"""

import math
from pathlib import Path

import ezdxf
from shapely.geometry import LineString, Polygon
from shapely.geometry import box as sbox

from build123d import (
    Axis,
    Box,
    Compound,
    Edge,
    Face,
    Plane,
    Pos,
    Rot,
    Solid,
    Vector,
    Wire,
    export_step,
    export_stl,
    import_dxf,
    revolve,
)

# ═════════════════════════════════════════════════════════════════════════════
# 1. CONSTANTS
# ═════════════════════════════════════════════════════════════════════════════

PROJECT = Path(__file__).resolve().parents[1]
IMPORT_DIR = PROJECT / "vectors" / "import"
OUT_DIR = PROJECT
PREFIX = "SurgicalDrillGuide"

RING_FILES = {
    "frame": "main_frame_body.dxf",
    "l_arm": "l_arm_body.dxf",               # RECTIFIED L (top bar parallel to X); riser rebuilt at 7.50 mm
    "collar": "l_arm_collar.dxf",
    "carriage": "l_arm_carriage.dxf",
    "wire_axis": "l_arm_wire_axis.dxf",       # LINE, Y 51.80, parallel to X
    "grip_half": "handle_grip_revolve_half.dxf",
    "ferrule_half": "handle_ferrule_revolve_half.dxf",
}

# ── Z (breadth). No photo measures Z (MEASUREMENTS §8). ─────────────────────────
T_Z = 10.0               # ASSUMED (user decision 2026-09-23): frame, rack and hook thickness
Z_MID = T_Z / 2.0        # DERIVED: mid-plane; wire bores and handle axis lie on it
WRAP_WALL_Z = 3.0        # ASSUMED: collar/carriage side-wall thickness beside the rack (each side)
SLIDE_CLEAR = 0.30       # PLACEHOLDER (print-tolerance-expert, keep 0.30): rack-channel clearance per side in Z
SLIDE_CLEAR_Y = 0.20     # PLACEHOLDER (print-tolerance-expert, round 3): channel clearance per side in Y (only
                         # derive_channel uses it; less Y play = less pawl-overlap loss when the slider cocks)
CARRIAGE_TOP_WALL = 2.5  # DESIGNED (user decision, round 4; 2.0 in round 3 failed 10.86 vs 9.17 MPa at b 5):
                         # carriage top wall over the channel ceiling; the traced top (1.675-1.740) is raised
CARRIAGE_FLOOR = 2.5     # DESIGNED (user decision, round 4; traced floor 1.97-2.05 failed 9.60 vs 9.17 MPa at b 5):
                         # carriage floor under the channel, OUTSIDE the pawl tongue. The tongue keeps the traced
                         # bottom (t 1.97-2.02): its hard-stop stress is displacement-set (3E*delta*c/x^2), so a
                         # thicker tongue would RAISE it past SF 3. A 45° chamfer steps the floor up to the tongue
                         # at the anchor (no square re-entrant corner at the tongue root).
# The carriage +X end is squared over its full height at the traced end face at channel mid-height (DERIVED,
# X 106.475); this removes the 0.048 mm sliver the round-3 top box left at X 106.438-106.486 (form-auditor).
# User decision (fix round 2026-09-23): the L-arm (riser, top bar, crown) takes the collar/carriage Z, so the
# slider is one 16.6 mm slab: Z = -SLIDE_CLEAR - WRAP_WALL_Z .. T_Z + SLIDE_CLEAR + WRAP_WALL_Z (-3.3 .. 13.3),
# still centred on Z_MID. Overrides the 10 mm decision for the L-arm only.
L_ARM_FULL_WRAP_Z = True  # ASSUMED (user decision)

# ── C-tip pad (user decision: thicken, never cut; >= 1.5 mm wall PERPENDICULAR to the faces round the bore) ──
CTIP_WALL_MIN = 1.5      # user requirement
CTIP_PAD_MARGIN = 0.3    # DESIGNED: extra wall above the requirement (sleeve half-height = r_bore + 1.5 + 0.3)
CTIP_PAD_EXIT_MARGIN = 0.3  # DESIGNED: sleeve exit face this far past where the bore's lower edge leaves the ring
CTIP_PAD_BLEND_R = 1.5   # DESIGNED: morphological-closing radius that fillets the pad into the traced hook

# ── Boss pad (user decision: frame locally as thick as the boss, flush both faces, blended into the bar) ──
# Round 3: boss Ø22 -> pad Z -6..16 (6 mm per face). The old 5 mm taper would start at X 106.311, 0.175 mm INSIDE
# the carriage end at MIN (106.486); the taper is shortened/steepened instead of moving the carriage (user rule).
BOSS_PAD_BLEND = 2.8     # DESIGNED: taper length each side, 22 -> 10 mm: 6 mm per face over 2.8 mm = 65.0°
BOSS_PAD_CARRIAGE_CLEAR = 2.0  # DESIGNED: minimum X gap, carriage end at MIN -> start of the pad taper

# ── Rack extension (user decision: extend the rack so the ~74 mm maximum opening is restored) ─────────────
# The traced free end (end face + bottom chamfer) is moved RACK_EXT towards -X; the gap is filled with the rack
# section (top edge Y 0, bottom = the traced bottom line extended); teeth continue in phase at TOOTH_PITCH.
RACK_EXT = 4.6           # DESIGNED (user decision to extend; 4.5 -> 4.6 in round 3, user accepted): length added to
                         # the traced rack at its free end. With PIN_FIT_CLEAR 0.20 and the pin's c/2 slop, 4.5
                         # leaves a worst-case MAX->pin gap of 0.044 (< PIN_STOP_MIN_GAP 0.10): MAX falls to 36
                         # teeth, tip gap 72.432, and the build refuses. 4.6 gives 0.144 worst / 0.244 centred.
TARGET_MAX_GAP = 74.0    # user requirement: tip gap at wire height at the last pawl-seated pose (build asserts)

# ── End-stop pin (user decision: removable printed pin through a Z hole near the rack tip) ─────────────────
PIN_D = 3.0              # DESIGNED: pin diameter
PIN_FIT_CLEAR = 0.20     # PLACEHOLDER (print-tolerance-expert, round 3): hole Ø = PIN_D + this = 3.20, snug
                         # slip fit for a removable pin (coupon 3.15 / 3.20 / 3.25)
PIN_TIP_WALL = 1.7       # DESIGNED: rack material between the hole and the rack's free end
PIN_PROTRUDE = WRAP_WALL_Z + SLIDE_CLEAR  # DESIGNED: pin ends flush with the slider's outer Z faces
PIN_STOP_MIN_GAP = 0.10  # DESIGNED: the seated MAX pose must leave at least this gap to the pin, AFTER the pin's
                         # slop c/2 (round 3; see RACK_EXT)

# ── Wire and bores ──────────────────────────────────────────────────────────────
WIRE_D = 3.0             # ASSUMED (user decision): Ø3 mm K-wire
BORE_D = 3.4             # ASSUMED (user decision): bore drawn Ø3.4, reamed to 3.2 after printing
REAM_D = 3.2             # ASSUMED (user decision): final bore after reaming
TEARDROP_APEX_DIR = +1   # DESIGNED: teardrop point towards +Z (print with the -Z face on the bed)
BORE_OVERRUN = 3.0       # DESIGNED: bore cutters run this far past each traced face (through-hole)

# ── Rack teeth (bottom face, MEASUREMENTS §3b) ──────────────────────────────────
TOOTH_PITCH = 1.61       # MEASURED (cd1 FFT, 3.443 px/mm; 1.58 at the ruler scale)
TOOTH_DEPTH = 0.80       # ASSUMED: unresolved in the photos (upper bound 2.4 mm); chosen for FDM at 1.61 pitch
TOOTH_LAND = 0.20        # DESIGNED: flat tip land between notches (a sharp tip does not print)
TOOTH_CUT_EPS = 0.05     # DESIGNED: cutter lands sit this far below the envelope (no coincident faces)
TEETH_START_MARGIN = 0.20  # DESIGNED: first notch starts this far right of the tip-chamfer end
TEETH_X_END = 100.7      # DERIVED in MEASUREMENTS §3b (teeth end at the "30" graduation), ±1.5 mm
TOOTH_HOOK_DEG = 10.0    # DESIGNED (user decision, round 3; MECHANISM_STRATEGY §3): the rack notch locking wall
                         # and the pawl tooth locking face are undercut by this angle (apex leans -X), so tension
                         # on the jaws pulls the tooth DEEPER into the notch. No-release condition >= 8.6°.

# ── Compliant pawl (DESIGNED substitution: the reference pawl, pivot screw and lever are not photographed
#    internally, U7). Tension tongue anchored at its -X end, tooth at its +X free end, release tab below. ──
PAWL_ANCHOR_X = 72.5     # DESIGNED: tongue root (carriage bottom wall is intact left of this)
PAWL_FREE_X = 94.0       # DESIGNED: tongue free end (tongue length = 21.5 mm)
PAWL_SLOT_W = 0.80       # DESIGNED: free-end slot, in-plane (prints as a vertical gap), >= 2 nozzle widths
PAWL_WINDOW_TOP_Y = -7.5  # DESIGNED: side walls are cut back to this Y over the tongue so the tooth can pass
PAWL_SEAT_CLEAR = 0.10   # PLACEHOLDER (print-tolerance-expert): tooth-to-notch clearance when seated
PAWL_TOOTH_MARGIN = 0.50  # DESIGNED: tooth right face stays this far inside the tongue free end
TAB_W = 3.0              # DESIGNED: release tab width along X (hangs from the tongue free end)
TAB_BOTTOM_Y = -24.0     # DESIGNED: tab reaches ~24 mm below the rack top (reference lever ~27 mm, cd2)
PAD_LEN = 9.0            # DESIGNED: thumb pad length along +X from the tab
PAD_T = 3.0              # DESIGNED: thumb pad thickness in Y
# Tab hard stop (user decision, round 3): a leg down from the carriage floor past the pad's +X end and a beam
# under the pad. Only the block under the tab column touches (gap TAB_STOP_DROP); elsewhere the beam is
# STOP_RELIEF below the pad, so a pad that rotates with the flexure does not land on its +X end first.
TAB_STOP_DROP = 0.73     # DESIGNED (user decision round 5; was 0.80): max tooth drop. Release needs the worst tooth
                         # overlap 0.630 + 0.10 margin; pawl tongue SF 3.29 at the stop (3.00 at 0.80), the stress
                         # being displacement-set (print-tolerance-expert)
STOP_LEG_W = 2.5         # DESIGNED: leg width along X (right face flush with the squared carriage end, round 5)
STOP_BEAM_T = 2.5        # DESIGNED: beam thickness in Y
STOP_RELIEF = 2.0        # DESIGNED: beam-to-pad gap away from the tab column

# ── Handle boss + thread (user decision: FEMALE in a boss under the bar, MALE on the handle) ─────────────
# Round 3 (user decision): Tr16x4 in a Ø22 boss replaces Tr10x2 in Ø16 (handle root Ø7.5 -> Ø11.5).
THREAD_PITCH = 4.0       # DESIGNED (user decision): Tr16x4, ISO 2904 pitch for d = 16
THREAD_MAJOR_D = 16.0    # DESIGNED (user decision): male major diameter
THREAD_H = 2.25          # DESIGNED: male thread height (ISO h3 = 0.5P + ac, ac 0.25) -> male root Ø11.5
THREAD_FLANK_DEG = 15.0  # DESIGNED: half flank angle (30° trapezoidal)
THREAD_CREST_W = 0.366 * THREAD_PITCH  # DESIGNED: ISO crest flat 0.366P
THREAD_RADIAL_CLEAR = 0.30  # PLACEHOLDER (print-tolerance-expert, round 3): female = male + this, radially
THREAD_AXIAL_CLEAR = 0.15   # PLACEHOLDER (print-tolerance-expert, round 3): female groove wider by this per flank
HANDLE_CORE_GRIP_DEPTH = 2.0  # DESIGNED: the Ø16 handle core runs this far below the traced grip top, into the
                              # grip (where the grip radius is >= 12.4, measured on the ring at build time)
THREAD_ENGAGE = 8.0      # DESIGNED: male thread length above the ferrule shoulder
THREAD_TIP_CHAMFER = 1.0  # DESIGNED: 45° lead-in on the MALE tip only (the female mouth never was 45°; see below)
# Female mouth (round 4: named as built; rounds 2-3 described it as the 45° chamfer above, which it never was).
# The cutter ran from r = major + chamfer + 0.5 at 0.5 outside the face to r = MINOR at depth `chamfer`: slope 2.5
# (68.2° from the axis), face radius 8.55, r 8.425 at 0.05 in (form-auditor measured 8.42). Kept: it clears the
# male crest (8.0) at the face by 0.55, leaves full female ridges from depth 1.0, and leaves a 2.45 mm seating
# annulus (8.55 -> 11.0) for the collar. A true 45° countersink to r 9.3 would cut it to 1.70 mm.
BOSS_MOUTH_FACE_CLEAR = 0.25  # DESIGNED (round 4, = as built): mouth radius at the boss face = female major + this
BOSS_MOUTH_DEPTH = 1.0        # DESIGNED (round 4, = as built): the mouth cone reaches the female minor at this depth
# Handle collar (user decision, round 4, option (a) of MECHANISM_STRATEGY "Round 3 re-check at 25 N"): a Ø22
# collar whose flat top face SEATS ON THE BOSS FACE, so side load puts the thread in tension instead of radial
# bearing. DEVIATION from the traced ferrule (r 7.19-7.49), accepted by the user.
HANDLE_COLLAR_OD = 22.0       # DESIGNED (user decision, round 4): = BOSS_OD, flush with the boss
HANDLE_COLLAR_T = 3.0         # DESIGNED (round 4): cylindrical length of the collar below its seating face
HANDLE_COLLAR_TAPER_R = 7.0   # DESIGNED (round 4): under the collar a 45° cone runs from r 11 down to this radius
                              # (inside the Ø16 core), so the flange has no square root corner
THREAD_CAM_N = 72        # DESIGNED: cam-section resolution (5° steps); see cam_thread()
BOSS_OD = 22.0           # ASSUMED (user decision, round 3): boss diameter (reference post Ø4.85 + nut Ø9.8 are
                         # replaced by this); the pad's flat band is +-BOSS_OD/2 about the handle axis
BOSS_HOLE_FLOOR = 1.2    # DESIGNED: blind-hole floor left under the bar (hole never opens into the bar)

# ── Fusion (booleans only fuse where solids OVERLAP) ────────────────────────────
FUSE_OVERLAP = 1.5       # DESIGNED: interpenetration of mating features (riser into collar, etc.)
BUTT_FLAT = 0.06         # DESIGNED: the traced butt rises only 0.05 mm over its 4.45 mm radius; revolved, that
                         # near-flat cone tessellated to a degenerate pole triangle (STL not watertight, measured
                         # 2026-09-23). Facing the butt 0.06 mm makes it a plane (also a stable print face).

# ── Opening poses: travel in whole tooth pitches so the pawl is seated in every pose ─────────────────────
# MIN = 0 (photographed pose). MAX = the last seated pose before the collar meets the end-stop pin (DERIVED in
# parameters()). MID = half of MAX, rounded. The pre-fix MAX (37 teeth, 59.57 mm) is unreachable with a pin.

# ── Export ──────────────────────────────────────────────────────────────────────
TESS_TOL = 0.03          # STL chordal tolerance, mm
TESS_ANG = 0.2           # STL angular tolerance, rad


# ═════════════════════════════════════════════════════════════════════════════
# 2. RING IMPORT (build time) and DERIVED values
# ═════════════════════════════════════════════════════════════════════════════

def ring_face(name):
    """Traced ring -> build123d Face via import_dxf (the consumption path the vectors README prescribes)."""
    shapes = import_dxf(str(IMPORT_DIR / RING_FILES[name]))
    wires = Wire.combine(shapes.edges())
    if len(wires) != 1:
        raise RuntimeError(f"{name}: expected one closed ring, got {len(wires)} wires")
    face = Face(wires[0])
    if face.normal_at().Z < 0:
        face = -face
    return face


def ring_points(name):
    """Same file, vertex list (for DERIVED numeric reads: chords, edges)."""
    return ring_points_file(RING_FILES[name])


def ring_points_file(fname):
    doc = ezdxf.readfile(str(IMPORT_DIR / fname))
    for e in doc.modelspace():
        if e.dxftype() == "LWPOLYLINE":
            return [(float(v[0]), float(v[1])) for v in e.get_points()]
        if e.dxftype() == "LINE":
            return [tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2]]
    raise RuntimeError(f"{name}: no ring/line found")


def vertical_chord(poly, x):
    """(ymin, ymax) of a polygon along the vertical line at x (None if it misses)."""
    g = poly.intersection(LineString([(x, -500), (x, 500)]))
    if g.is_empty:
        return None
    ys = [c[1] for geom in getattr(g, "geoms", [g]) for c in geom.coords]
    return min(ys), max(ys)


def derive():
    """Every value read from the traced rings. Recomputed each build so corrections flow through."""
    d = {}
    fr = ring_points("frame")
    d["frame_poly"] = Polygon(fr)

    # Wire axis (LINE) — rectified, parallel to X.
    (wx0, wy0), (wx1, wy1) = ring_points("wire_axis")
    if abs(wy1 - wy0) > 1e-6:
        raise RuntimeError("wire axis is not parallel to X; the build assumes the rectified line")
    d["wire_y"], d["wire_x0"], d["wire_x1"] = wy0, min(wx0, wx1), max(wx0, wx1)

    # Rack bottom envelope = the longest edge of the frame ring (tooth-tip envelope, X ~2.5 -> ~108.7).
    edges = [(fr[i], fr[(i + 1) % len(fr)]) for i in range(len(fr))]
    (bx0, by0), (bx1, by1) = max(edges, key=lambda e: math.dist(e[0], e[1]))
    if bx0 > bx1:
        (bx0, by0), (bx1, by1) = (bx1, by1), (bx0, by0)
    if not (by0 < -8 and by1 < -8):
        raise RuntimeError("longest frame edge is not the rack/bar bottom edge")
    d["rack_bottom_line"] = (bx0, by0, bx1, by1)

    # Rack extension: traced tip-end profile (ring vertices left of the chamfer end bx0) shifted -RACK_EXT,
    # plus a band of rack section bridging it back to the traced rack (0.5 mm overlap into the ring).
    d["frame_ring_poly"] = d["frame_poly"]
    ov = 0.5
    ybl = lambda x: by0 + (x - bx0) * (by1 - by0) / (bx1 - bx0)
    tip = [p for p in fr if p[0] <= bx0 + 1e-6]
    k0 = fr.index(tip[0])
    tip = [fr[(k0 + i) % len(fr)] for i in range(len(tip))]       # ring order, top-left corner first
    top_y = tip[0][1]
    tip_poly = Polygon([(bx0 + ov, top_y)] + tip + [(bx0 + ov, ybl(bx0 + ov))])
    tip_moved = Polygon([(x - RACK_EXT, y) for x, y in tip_poly.exterior.coords])
    band = Polygon([(bx0 - RACK_EXT, top_y), (bx0 + ov, top_y), (bx0 + ov, ybl(bx0 + ov)),
                    (bx0 - RACK_EXT, ybl(bx0 - RACK_EXT))])
    ext = tip_moved.union(band)
    if ext.geom_type != "Polygon":
        raise RuntimeError("rack extension is not one polygon")
    d["rack_ext_poly"] = ext
    d["frame_poly"] = d["frame_ring_poly"].union(ext)
    d["rack_tip_x"] = min(p[0] for p in tip) - RACK_EXT

    # Handle axis = the axis edge of the revolve half rings (min X); ferrule shoulder = ferrule ring max Y.
    gh = ring_points("grip_half")
    fh = ring_points("ferrule_half")
    d["handle_axis_x"] = min(p[0] for p in gh)
    if abs(min(p[0] for p in fh) - d["handle_axis_x"]) > 1e-3:
        raise RuntimeError("grip and ferrule revolve halves do not share an axis")
    d["ferrule_top_y"] = max(p[1] for p in fh)
    d["ferrule_bot_y"] = min(p[1] for p in fh)
    d["grip_top_y"] = max(p[1] for p in gh)

    # Bar bottom at the handle axis (boss top).
    d["bar_bottom_at_axis"] = vertical_chord(d["frame_poly"], d["handle_axis_x"])[0]

    # Collar/carriage extents and the L-arm riser base.
    col = ring_points("collar")
    car = ring_points("carriage")
    la = ring_points("l_arm")
    d["collar_x0"] = min(p[0] for p in col)
    d["carriage_x1"] = max(p[0] for p in car)
    d["carriage_x0"] = min(p[0] for p in car)
    d["carriage_y0"] = min(p[1] for p in car)
    d["carriage_y1"] = max(p[1] for p in car)
    # Round 4: the traced carriage polygon and its highest bottom point (the floor piece's top sits 1.0 above it).
    # The squared +X end (carriage_end_x) needs the channel, so parameters() sets it.
    d["carriage_poly"] = Polygon(car)
    d["carriage_bottom_max"] = max(vertical_chord(d["carriage_poly"], x)[0]
                                   for x in [d["carriage_x0"] + 0.5 + k * 0.5 for k in range(70)]
                                   if x < max(p[0] for p in car) - 0.5)
    d["riser_base_y"] = min(p[1] for p in la)
    base = sorted(p[0] for p in la if abs(p[1] - d["riser_base_y"]) < 1e-6)
    d["riser_x0"], d["riser_x1"] = base[0], base[-1]
    return d


def rack_bottom_y(D, x):
    bx0, by0, bx1, by1 = D["rack_bottom_line"]
    return by0 + (x - bx0) * (by1 - by0) / (bx1 - bx0)


def derive_channel(D, travel_max):
    """Rack channel through collar+carriage: the frame's Y envelope over every X the slider ever covers."""
    x_lo = D["collar_x0"] - travel_max
    x_hi = D["carriage_x1"]
    lo, hi = +1e9, -1e9
    n = int((x_hi - x_lo) / 0.25) + 1
    for i in range(n + 1):
        x = x_lo + (x_hi - x_lo) * i / n
        c = vertical_chord(D["frame_poly"], x)
        if c is None:
            continue
        lo, hi = min(lo, c[0]), max(hi, c[1])
    return lo - SLIDE_CLEAR_Y, hi + SLIDE_CLEAR_Y, (lo, hi, x_lo, x_hi)


# ═════════════════════════════════════════════════════════════════════════════
# 3. BUILDERS (pure: dimensions in, shape out)
# ═════════════════════════════════════════════════════════════════════════════

def one_solid(shape, what):
    """Hard gate at construction: a boolean result must be exactly one solid."""
    sols = shape.solids()
    if len(sols) != 1:
        info = "; ".join(f"#{i} vol {s.volume:.2f} bbox {s.bounding_box()}" for i, s in enumerate(sols))
        raise RuntimeError(f"{what}: {len(sols)} solids ({info})")
    return sols[0]


def extrude_z(face, z0, z1):
    return Solid.extrude(face.moved(Pos(0, 0, z0)), Vector(0, 0, z1 - z0))


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def polygon_face(pts_xy):
    return Face(Wire.make_polygon([(x, y, 0) for x, y in pts_xy], close=True))


def teardrop_bore_x(x0, x1, y, z, d, apex_dir=+1):
    """Bore along X: circle Ø d plus a 45° point towards apex_dir*Z (support-free when Z is the build axis)."""
    r = d / 2.0
    s = r / math.sqrt(2.0)
    zc = z
    apex = Vector(x0, y, zc + apex_dir * r * math.sqrt(2.0))
    t1 = Vector(x0, y + s, zc + apex_dir * s)
    t2 = Vector(x0, y - s, zc + apex_dir * s)
    bottom = Vector(x0, y, zc - apex_dir * r)
    w = Wire([Edge.make_line(apex, t1), Edge.make_three_point_arc(t1, bottom, t2), Edge.make_line(t2, apex)])
    return Solid.extrude(Face(w), Vector(x1 - x0, 0, 0))


def thread_radius_fn(r_root, r_crest, crest_w, pitch, flank_deg):
    """Axial trapezoid profile r(z), periodic in pitch, crest centred on z = 0."""
    t = math.tan(math.radians(flank_deg))
    hc = crest_w / 2.0
    h = r_crest - r_root

    def f(z):
        z = (z + pitch / 2.0) % pitch - pitch / 2.0
        a = abs(z)
        if a <= hc:
            return r_crest
        if a <= hc + h * t:
            return r_crest - (a - hc) / t
        return r_root
    return f


def cam_thread(r_root, r_crest, crest_w, pitch, flank_deg, length, n):
    """Single-start right-hand trapezoidal thread INCLUDING its core, along +Z from z = 0.

    The cross-section perpendicular to the axis of a single-start thread is a cam, r(theta) = profile(theta*P/2pi).
    Extruding that cam with 360° of twist per pitch reproduces the helical thread exactly (verified in the
    prototype: radius vs z matched the design to 0.001 mm). A helical sweep was tried first and REJECTED: the
    swept ridge is a valid solid but OCC fuses it with a core cylinder into the ridge alone (core lost).
    """
    f = thread_radius_fn(r_root, r_crest, crest_w, pitch, flank_deg)
    pts = []
    for i in range(n):
        th = 2.0 * math.pi * i / n
        r = f(i / n * pitch)
        pts.append((r * math.cos(th), r * math.sin(th), 0.0))
    face = Face(Wire.make_polygon(pts, close=True))
    return Solid.extrude_linear_with_rotation(face, (0, 0, 0), (0, 0, length), 360.0 * length / pitch)


def along_y(shape, x, y0, z):
    """Map a shape built along +Z (axis at the origin) onto an axis parallel to +Y through (x, y0, z)."""
    return Pos(x, y0, z) * Rot(-90, 0, 0) * shape


def cone_y(x, y0, y1, r0, r1, z):
    """Frustum along +Y from y0 (radius r0) to y1 (radius r1)."""
    return along_y(Solid.make_cone(r0, r1, y1 - y0), x, y0, z)


def cyl_y(x, y0, y1, r, z):
    return along_y(Solid.make_cylinder(r, y1 - y0), x, y0, z)


def sawtooth_cutter_face(yb, x_start, x_end, pitch, depth, land, eps, hook_deg=0.0, below=2.0):
    """In-plane cutter for ratchet notches in the rack BOTTOM face.

    Notch k: locking wall from the apex (a_k, yb+depth) down to the mouth (a_k + depth*tan(hook), yb) (rack
    material on its -X side; hook_deg > 0 undercuts it so the apex leans -X), ramp from the apex down to
    (a_k + pitch - land, yb). The slider may move +X (jaws close) over the ramps; -X (open) is blocked.
    The ramp and the apex are unchanged by the hook; the land at the mouth grows by depth*tan(hook).
    """
    tb = math.tan(math.radians(hook_deg))
    pts = []
    n = int((x_end - x_start - (pitch - land)) // pitch) + 1
    a_list = [x_start + k * pitch for k in range(n)]
    y_lo = min(yb(x_start), yb(x_end)) - below
    pts.append((x_start - 0.5, y_lo))
    for a in a_list:
        y = yb(a)
        # The ramp keeps the tooth's slope depth/(pitch-land) and is merely EXTENDED below the envelope by eps
        # (it meets the envelope at a + pitch - land). Before the fix-round the ramp ended at y - eps at
        # a + pitch - land, i.e. slope (depth+eps)/(pitch-land) = 0.603 vs the tooth's 0.567 (form-auditor),
        # which narrowed the seat gap along the ramp.
        pts += [(a + (depth + eps) * tb, y - eps), (a, y + depth), (a + (pitch - land) * (1.0 + eps / depth), y - eps)]
    pts.append((a_list[-1] + pitch, y_lo))
    return polygon_face(pts), a_list


def _line_x(p, u, y):
    """x where the line through p with direction u crosses height y."""
    return p[0] + u[0] * (y - p[1]) / u[1]


def pawl_tooth_pts(a, yb_a, pitch, depth, land, clear, y_root, hook_deg=0.0):
    """Pawl tooth = the notch triangle offset inward by `clear` (normal offset of the wall and the ramp),
    extended down to y_root (into the tongue). With hook_deg the locking face is parallel to the undercut wall."""
    be = math.radians(hook_deg)
    ax_, ay_ = a, yb_a + depth                                   # notch apex
    uw = (math.sin(be), -math.cos(be))                           # wall direction, apex -> mouth
    nw = (math.cos(be), math.sin(be))                            # wall normal into the notch
    L = math.hypot(pitch - land, depth)
    ur = ((pitch - land) / L, -depth / L)                        # ramp direction, apex -> land
    nr = (-depth / L, -(pitch - land) / L)                       # ramp normal into the notch
    pw = (ax_ + clear * nw[0], ay_ + clear * nw[1])
    pr = (ax_ + clear * nr[0], ay_ + clear * nr[1])
    # apex = offset wall ∩ offset ramp: pw + s*uw = pr + t*ur
    det = uw[0] * (-ur[1]) - uw[1] * (-ur[0])
    s = ((pr[0] - pw[0]) * (-ur[1]) - (pr[1] - pw[1]) * (-ur[0])) / det
    apex = (pw[0] + s * uw[0], pw[1] + s * uw[1])
    x_right = _line_x(pr, ur, yb_a - clear)                      # offset ramp meets y = yb - clear
    x_bot = _line_x(pw, uw, y_root)                              # locking face continued into the tongue
    pts = [(x_bot, y_root), apex, (x_right, yb_a - clear), (x_right, y_root)]
    return pts, (apex[0], x_right, apex[1])


def shapely_faces(geom):
    """shapely (Multi)Polygon without holes -> list of build123d Faces."""
    out = []
    for g in getattr(geom, "geoms", [geom]):
        if g.is_empty or g.area < 1e-6:
            continue
        if len(g.interiors):
            raise RuntimeError("pad region has holes; not expected")
        out.append(polygon_face(list(g.exterior.coords)[:-1]))
    return out


def ctip_pad_region(D, ctip):
    """C-tip pad (user decision: thicken, do not cut). A sleeve around the wire line over the enclosed span,
    blended into the traced hook by a morphological closing, restricted to X_entry..X_exit so the jaw face at
    the wire height (and so the tip gap) does not move. Returns (added region, region to extrude, sleeve)."""
    ring = D["frame_poly"]
    x_in, x_out, h = ctip["x_entry"], ctip["x_exit"], ctip["half_h"]
    sleeve = sbox(x_in, D["wire_y"] - h, x_out, D["wire_y"] + h)
    r = ctip["blend_r"]
    closed = ring.union(sleeve).buffer(r, quad_segs=16).buffer(-r, quad_segs=16)
    span = sbox(x_in, D["wire_y"] - h - r - 1.0, x_out, D["wire_y"] + h + r + 1.0)
    added = closed.difference(ring).intersection(span)
    # extrude region = the added material grown 0.4 mm INTO the ring (a real overlap for the union), clipped to
    # the closed outline and the span, so the pad never extends past the new outline.
    region = added.buffer(0.4).intersection(closed).intersection(span)
    return added, region, sleeve


def build_main_frame(D, t_z, teeth, bore, boss, thread, ctip, pin):
    """C-hook + bar + rack (traced ring) + rack teeth + closed C-tip wire bore + C-tip pad + threaded handle
    boss in a flush boss pad (as thick as the boss) + end-stop pin hole."""
    frame = extrude_z(ring_face("frame"), 0.0, t_z)
    # Rack extension (user decision): the extruded extension region overlaps the traced rack by 0.5 mm.
    frame = one_solid(frame + extrude_z(polygon_face(list(D["rack_ext_poly"].exterior.coords)[:-1]), 0.0, t_z),
                      "frame + rack extension")
    hx, zc = D["handle_axis_x"], t_z / 2.0

    # Boss pad: the bar thickened to the boss Ø (flush with the boss on both Z faces), tapered back to T_Z.
    # An XZ hexagon prism along Y, clipped to the traced bar outline (the in-plane outline is unchanged).
    bz0, bz1 = zc - boss["od"] / 2.0, zc + boss["od"] / 2.0
    px0, px1 = boss["pad_x0"], boss["pad_x1"]
    bl = boss["pad_blend"]
    y0, y1 = D["bar_bottom_at_axis"] - 3.0, 3.0
    # The taper face runs from (px0, Z 0) to (px0 + bl, bz0) and is continued 0.5 mm INTO the bar (vertex at
    # Z 0.5) along the SAME line, so it meets the bar face exactly at px0 over bl (round 2 put the vertex at
    # (px0, 0.5): the face met Z 0 0.714 mm inboard, 4.286 mm long at 35°, not 5.0 at 31° - form-auditor R3).
    xin = 0.5 * bl / (0.0 - bz0)
    hexa = [(px0 - xin, 0.5), (px0 + bl, bz0), (px1 - bl, bz0), (px1 + xin, 0.5), (px1 + xin, t_z - 0.5),
            (px1 - bl, bz1), (px0 + bl, bz1), (px0 - xin, t_z - 0.5)]
    prism = Solid.extrude(Face(Wire.make_polygon([(x, y0, z) for x, z in hexa], close=True)),
                          Vector(0, y1 - y0, 0))
    pad = prism & extrude_z(ring_face("frame"), bz0 - 1.0, bz1 + 1.0)
    frame = one_solid(frame + pad, "frame + boss pad")

    # Boss under the bar, axis along -Y at the handle axis; runs FUSE_OVERLAP up into the pad (a real overlap).
    y_top = D["bar_bottom_at_axis"]
    y_bot = D["ferrule_top_y"]
    boss_body = cyl_y(hx, y_bot, y_top + FUSE_OVERLAP, boss["od"] / 2.0, zc)
    frame = one_solid(frame + boss_body, "frame + boss")

    # C-tip pad (before the bore, so the bore is cut through it).
    _, region, _ = ctip_pad_region(D, ctip)
    for f in shapely_faces(region):
        frame = one_solid(frame + extrude_z(f, 0.0, t_z), "frame + C-tip pad")

    # End-stop pin hole (Z) near the rack's free end, between the rack top and the notch apex line.
    frame = one_solid(frame - (Pos(pin["x"], pin["y"], -1.0) * Solid.make_cylinder(pin["hole_d"] / 2.0, t_z + 2.0)),
                      "frame - pin hole")

    # Rack teeth (bottom face).
    yb = lambda x: rack_bottom_y(D, x)
    cut_face, a_list = sawtooth_cutter_face(yb, teeth["x0"], teeth["x1"], teeth["pitch"], teeth["depth"],
                                            teeth["land"], teeth["eps"], teeth["hook"])
    frame = one_solid(frame - extrude_z(cut_face, -1.0, t_z + 1.0), "frame - teeth")

    # Closed C-tip bore on the rectified wire line. The cutter spans only the C-tip (the only frame material
    # at the wire height), so it cannot touch the rest of the hook.
    frame = one_solid(frame - teardrop_bore_x(bore["ctip_x0"], bore["ctip_x1"], D["wire_y"], zc, bore["d"],
                                              bore["apex_dir"]), "frame - C-tip bore")

    # Female thread: the male cam grown radially, phase-locked to the male (start Y differs by whole pitches).
    th = thread
    f_root = th["r_root"] + th["rclear"]
    f_crest = th["r_crest"] + th["rclear"]
    f_len = (y_top - boss["floor"]) - (y_bot - 2 * th["pitch"])
    female = along_y(cam_thread(f_root, f_crest, th["crest_w"] + 2 * th["aclear"], th["pitch"], th["flank"],
                                f_len, th["n"]), hx, y_bot - 2 * th["pitch"], zc)
    # Mouth cone (named in round 4, geometry unchanged): r_face at the boss face -> f_root at depth mouth_depth,
    # continued 0.5 outside the face along the same line (the cutter overruns the face; no coincident face).
    r_face, m_d = boss["mouth_r_face"], boss["mouth_depth"]
    slope = (r_face - f_root) / m_d
    mouth = cone_y(hx, y_bot - 0.5, y_bot + m_d, r_face + 0.5 * slope, f_root, zc)
    frame = one_solid(frame - female - mouth, "frame - female thread")
    return frame, a_list


def build_l_arm_slider(D, t_z, wall_z, chan, bore, pawl, a_seat):
    """Rectified L (Z 0..t_z) + collar + carriage (wrapping the rack) + compliant pawl + wire bore."""
    z0, z1 = -SLIDE_CLEAR - wall_z, t_z + SLIDE_CLEAR + wall_z
    lz0, lz1 = (z0, z1) if L_ARM_FULL_WRAP_Z else (0.0, t_z)

    body = extrude_z(ring_face("l_arm"), lz0, lz1)
    # Riser base extended DOWN into the collar (collar top slopes 6.595 -> 6.576; riser base flat at 6.587).
    riser_slug = box(D["riser_x0"], D["riser_x1"], D["riser_base_y"] - FUSE_OVERLAP, D["riser_base_y"] + 0.5,
                     lz0, lz1)
    collar = extrude_z(ring_face("collar"), z0, z1)
    carriage_traced = extrude_z(ring_face("carriage"), z0, z1)
    x_end = D["carriage_end_x"]
    y_top = chan["y1"] + CARRIAGE_TOP_WALL
    y_fl = chan["y0"] - CARRIAGE_FLOOR
    # Carriage top wall (round 3, 2.5 in round 4): raised to chan_y1 + CARRIAGE_TOP_WALL over the whole carriage,
    # square +X end corner (removes the traced corner rounding that thinned to a 0.23 mm feather edge). Starts
    # 1.0 below the traced top (overlap) and inside the collar at its -X end.
    carriage = carriage_traced + box(D["carriage_x0"], x_end + 0.5, D["carriage_y1"] - 1.0, y_top, z0, z1)
    # Carriage floor (round 4): CARRIAGE_FLOOR under the channel, left of the pawl anchor (with a 45° chamfer up
    # to the traced bottom at the anchor) and right of the free-end slot. Starts inside the collar (collar bottom
    # Y <= -13.2 there), top 1.0 inside the traced wall. The pawl window cut below trims the right piece at its
    # left end; the tongue is taken from the TRACED carriage, so its thickness does not change.
    y_in = D["carriage_bottom_max"] + 1.0
    px0 = pawl["anchor_x"]
    y_b_anchor = vertical_chord(D["carriage_poly"], px0)[0] + 0.05
    left = polygon_face([(D["carriage_x0"] - FUSE_OVERLAP, y_in), (px0, y_in), (px0, y_b_anchor),
                         (px0 - (y_b_anchor - y_fl), y_fl), (D["carriage_x0"] - FUSE_OVERLAP, y_fl)])
    right = box(pawl["free_x"] + pawl["slot_w"] - 0.5, x_end + 0.5, y_fl, y_in, z0, z1)
    # Square +X end over the full height, then trim at the traced end face at channel mid-height.
    end_fill = box(x_end - 1.0, x_end + 0.5, y_fl, y_top, z0, z1)
    carriage = carriage + extrude_z(left, z0, z1) + right + end_fill
    carriage = carriage - box(x_end, x_end + 5.0, y_fl - 5.0, y_top + 5.0, z0 - 1.0, z1 + 1.0)
    # Collar/carriage junction: the traced rings overlap by only 0.03-0.6 mm; this slug lies inside
    # collar ∪ carriage (collar right face is bridged/hidden there) and makes the overlap a real volume.
    cx = D["carriage_x0"]
    junction = box(cx - FUSE_OVERLAP, cx + FUSE_OVERLAP, D["carriage_y0"] + 0.2, D["carriage_y1"] - 0.2, z0, z1)
    slider = one_solid(body + riser_slug + collar + carriage + junction, "slider fuse")

    # Rack channel (through collar and carriage).
    slider = one_solid(slider - box(D["collar_x0"] - 2.0, D["carriage_x1"] + 2.0, chan["y0"], chan["y1"],
                                    -SLIDE_CLEAR, t_z + SLIDE_CLEAR), "slider - channel")

    # Compliant pawl: open a window (side walls cut back to PAWL_WINDOW_TOP_Y, bottom wall removed), then put
    # back the tongue (carriage bottom wall between anchor and free end), the tooth and the release tab.
    # Every pawl feature is an in-plane profile over the full carriage Z, so every gap is a vertical wall
    # when printed flat (no Z-gaps, no hidden overhangs).
    px0, pxf = pawl["anchor_x"], pawl["free_x"]
    slider = one_solid(slider - box(px0, pxf + pawl["slot_w"], D["carriage_y0"] - 3.0, pawl["window_top_y"],
                                    z0 - 1, z1 + 1), "slider - pawl window")
    tongue = carriage_traced & box(px0 - FUSE_OVERLAP, pxf, D["carriage_y0"] - 3.0, chan["y0"], z0, z1)
    tooth_pts, _ = pawl_tooth_pts(a_seat, rack_bottom_y(D, a_seat), TOOTH_PITCH, TOOTH_DEPTH, TOOTH_LAND,
                                  pawl["seat_clear"], chan["y0"] - 0.5, pawl["hook"])
    tooth = extrude_z(polygon_face(tooth_pts), z0, z1)
    tab = box(pxf - pawl["tab_w"], pxf, pawl["tab_bottom_y"], D["carriage_y0"] + 0.8, z0, z1)
    pad_bot = pawl["tab_bottom_y"] - pawl["pad_t"] + 0.5
    pad = box(pxf - pawl["tab_w"], pxf + pawl["pad_len"], pad_bot, pawl["tab_bottom_y"] + 0.5, z0, z1)
    slider = one_solid(slider + tongue + tooth + tab + pad, "slider + pawl")

    # Tab hard stop (round 3): leg from the carriage floor down past the pad's +X end, beam under the pad, and a
    # contact block under the tab column only, TAB_STOP_DROP below the pad bottom.
    st = pawl["stop"]
    # Round 5: the leg's +X face is flush with the squared carriage end (was carriage_x1 - 0.1 = traced 106.386,
    # a 0.089 step behind the end). Built 0.5 past the end so it overlaps (no coincident faces in the union), then
    # the whole +X end is trimmed at carriage_end_x in one cut: a single plane over the full height.
    leg_x1 = x_end
    leg_x0 = leg_x1 - st["leg_w"]
    if leg_x0 < pxf + pawl["pad_len"] + 0.5:
        raise RuntimeError(f"stop leg X {leg_x0:.3f} is within 0.5 of the pad end {pxf + pawl['pad_len']:.3f}")
    beam_top = pad_bot - st["relief"]
    beam_bot = beam_top - st["beam_t"]
    leg = box(leg_x0, leg_x1 + 0.5, beam_bot, D["carriage_y0"] + 1.0, z0, z1)
    beam = box(pxf - pawl["tab_w"] - 0.5, leg_x0 + FUSE_OVERLAP, beam_bot, beam_top, z0, z1)
    block = box(pxf - pawl["tab_w"] - 0.5, pxf + 0.5, beam_top - FUSE_OVERLAP, pad_bot - st["drop"], z0, z1)
    slider = one_solid(slider + leg + beam + block, "slider + tab stop")
    slider = one_solid(slider - box(x_end, x_end + 5.0, beam_bot - 5.0, y_top + 5.0, z0 - 1.0, z1 + 1.0),
                       "slider - end trim (leg flush)")

    # Wire bore along the full top bar: enters the riser outer face, exits the crown.
    slider = one_solid(slider - teardrop_bore_x(D["wire_x0"] - bore["overrun"], D["wire_x1"] + bore["overrun"],
                                                D["wire_y"], t_z / 2.0, bore["d"], bore["apex_dir"]),
                       "slider - wire bore")
    return slider


def build_handle(D, t_z, thread):
    """Revolved grip + ferrule (traced half-profiles) + male thread on the ferrule top."""
    hx, zc = D["handle_axis_x"], t_z / 2.0
    ax = Axis((hx, 0, 0), (0, 1, 0))
    grip = revolve(ring_face("grip_half"), ax, 360)
    ferrule = revolve(ring_face("ferrule_half"), ax, 360)
    # Handle core (round 3, user decision): the male thread is Ø16 major, and no section between it and the grip
    # may be narrower. The traced ferrule is r 7.19-7.49 and the traced halves leave a 0.25 mm gap at the grip
    # top (grip top Y -52.315, ferrule bottom Y -52.066; round 2 bridged it with a Ø8 neck). One Ø(major)
    # cylinder from HANDLE_CORE_GRIP_DEPTH inside the grip up to the shoulder replaces the bridge: DEVIATION.
    y_core0 = D["grip_top_y"] - HANDLE_CORE_GRIP_DEPTH
    r_core = thread["r_crest"]
    r_grip = horizontal_chord(Polygon(ring_points("grip_half")), y_core0)[1] - hx
    if r_grip < r_core + 1.0:
        raise RuntimeError(f"handle core bottom Y {y_core0:.3f}: grip radius {r_grip:.3f} does not embed r {r_core}")
    # Round 4 collar (user decision): one revolved profile = Ø22 cylinder (flat seating face at the shoulder Y,
    # square to the axis) + a 45° cone under it down to r taper_r. One revolve, so no internal coincident faces.
    y_sh = D["ferrule_top_y"]
    st = thread["seat"]
    rc, rt = st["collar_r"], st["taper_r"]
    y_c0 = y_sh - st["collar_t"]
    y_c1 = y_c0 - (rc - rt)
    collar = revolve(Face(Wire.make_polygon([(hx, y_sh, 0), (hx + rc, y_sh, 0), (hx + rc, y_c0, 0),
                                             (hx + rt, y_c1, 0), (hx, y_c1, 0)], close=True)), ax, 360)
    # The core now ends INSIDE the collar, 0.5 below the male's start (which is one pitch below the face, inside
    # the collar): the core surface r 8.0 would otherwise coincide with the male crest r 8.0 (the round-3 hang).
    y_core1 = y_sh - thread["pitch"] - 0.5
    r_at = rc - max(0.0, y_c0 - y_core1)
    if not (y_c1 < y_core1 < y_sh and r_at > r_core + 0.5):
        raise RuntimeError(f"core top Y {y_core1:.3f} is not inside the collar")
    core = along_y(Solid.make_cylinder(r_core, y_core1 - y_core0), hx, y_core0, 0.0)
    # Traced ferrule (r <= 7.49) clipped 1.0 below the face so its top face is buried in the collar.
    ferrule = ferrule & box(hx - 20, hx + 20, y_core0 - 5, y_sh - 1.0, -20, 20)
    handle = one_solid(grip + ferrule + core + collar, "handle revolve fuse").moved(Pos(0, 0, zc))
    y_butt = handle.bounding_box().min.Y
    handle = one_solid(handle - box(hx - 30, hx + 30, y_butt - 5, y_butt + BUTT_FLAT, zc - 30, zc + 30),
                       "handle butt flat")

    th = thread
    y_sh = D["ferrule_top_y"]
    # Phase origin: whole pitches (2P) from the female's origin at y_sh - 2P. Round 3 fix: the male starts AT the
    # shoulder, not one pitch below it. Below the shoulder it lay inside the Ø16 core whose surface coincides with
    # the male crest (r_crest), and that coincident fuse made the handle is_valid False; its STL export then hung
    # (> 81 min at 0.03/0.2). Starting at y_sh, the male's bottom face lands flat on the core's top face: the fuse
    # is valid, one solid, and the STL exports in 0.7 s (probe cad3/probe.py, 2026-09-23).
    # Round 4: the male starts ONE PITCH below the face (phase kept: still whole pitches from the female origin),
    # inside the Ø22 collar where nothing sits at r 8.0, so the male/collar fuse is a real overlap (no flat landing).
    y_start = y_sh - th["pitch"]
    length = th["engage"] + th["pitch"]
    male = along_y(cam_thread(th["r_root"], th["r_crest"], th["crest_w"], th["pitch"], th["flank"], length,
                              th["n"]), hx, y_start, zc)
    y_tip = y_sh + th["engage"]
    clip = cyl_y(hx, y_start - 0.1, y_tip - th["chamfer"] + 0.01, th["r_crest"] + 1.0, zc) + cone_y(
        hx, y_tip - th["chamfer"], y_tip, th["r_crest"], th["r_crest"] - th["chamfer"], zc)
    male = male & clip
    handle = one_solid(handle + male, "handle + male thread")
    return handle


# ═════════════════════════════════════════════════════════════════════════════
# 4. PARAMETER BUNDLES (derived from constants + rings)
# ═════════════════════════════════════════════════════════════════════════════

def horizontal_chord(poly, y):
    g = poly.intersection(LineString([(-500, y), (500, y)]))
    if g.is_empty:
        return None
    xs = [c[0] for geom in getattr(g, "geoms", [g]) for c in geom.coords]
    return min(xs), max(xs)


def derive_pin(D):
    """End-stop pin position (DERIVED from the rings) and the travel at which the collar meets it."""
    fr = D["frame_poly"]
    r_hole = (PIN_D + PIN_FIT_CLEAR) / 2.0
    x = 3.0 - RACK_EXT
    for _ in range(5):
        y_top = vertical_chord(fr, x)[1]
        y_apex = rack_bottom_y(D, x) + TOOTH_DEPTH           # notch apex line (the teeth band's upper limit)
        y = 0.5 * (y_top + y_apex)
        x_tip = horizontal_chord(fr, y)[0]
        x = x_tip + PIN_TIP_WALL + r_hole
    col = Polygon(ring_points("collar"))
    collar_face = min(horizontal_chord(col, y + dy)[0] for dy in [PIN_D / 2.0 * k / 10.0 for k in range(-10, 11)])
    # Round 3: the pin may sit c/2 towards the collar in its hole (slip fit), so the worst-case contact travel
    # is to the HOLE's +X edge, not the centred pin's.
    travel_stop_centred = collar_face - (x + PIN_D / 2.0)
    travel_stop = collar_face - (x + r_hole)
    n_max = int(math.floor((travel_stop - PIN_STOP_MIN_GAP) / TOOTH_PITCH))
    return {"x": x, "y": y, "d": PIN_D, "hole_d": PIN_D + PIN_FIT_CLEAR, "x_tip": x_tip, "y_top": y_top,
            "travel_stop_centred": travel_stop_centred,
            "y_apex": y_apex, "collar_face": collar_face, "travel_stop": travel_stop, "n_max": n_max,
            "z0": -PIN_PROTRUDE, "z1": T_Z + PIN_PROTRUDE}


def parameters():
    D = derive()
    pin = derive_pin(D)
    D["pin"] = pin
    pose_teeth = {"min": 0, "mid": int(round(pin["n_max"] / 2.0)), "max": pin["n_max"]}
    D["pose_teeth"] = pose_teeth
    travel = {k: n * TOOTH_PITCH for k, n in pose_teeth.items()}
    ch_y0, ch_y1, ch_env = derive_channel(D, travel["max"])
    chan = {"y0": ch_y0, "y1": ch_y1, "envelope": ch_env}
    # Round 4: squared carriage end = the traced end face at the channel mid-height (DERIVED).
    D["carriage_end_x"] = horizontal_chord(D["carriage_poly"], 0.5 * (ch_y0 + ch_y1))[1]
    bx0 = D["rack_bottom_line"][0]
    # Teeth: the traced-rack phase (first wall bx0 + margin) continued -X, in whole pitches, into the extension.
    x0_traced = bx0 + TEETH_START_MARGIN
    m_ext = int(math.floor((x0_traced - (bx0 - RACK_EXT + TEETH_START_MARGIN)) / TOOTH_PITCH + 1e-9))
    teeth = {"x0": x0_traced - m_ext * TOOTH_PITCH, "x1": TEETH_X_END, "x0_traced": x0_traced, "n_ext": m_ext, "pitch": TOOTH_PITCH, "depth": TOOTH_DEPTH,
             "land": TOOTH_LAND, "eps": TOOTH_CUT_EPS, "hook": TOOTH_HOOK_DEG}
    # C-tip bore cutter: X range of the C-tip chord at the wire height, plus overrun.
    c = D["frame_poly"].intersection(LineString([(140.0, D["wire_y"]), (200.0, D["wire_y"])]))
    cx = [q[0] for g in getattr(c, "geoms", [c]) for q in g.coords]
    # C-tip pad: sleeve from the jaw face at the wire height to just past where the bore's lower edge leaves
    # the traced arm on the outer (45°) edge.
    lo = horizontal_chord(D["frame_poly"].intersection(sbox(140, 40, 200, 70)), D["wire_y"] - BORE_D / 2.0)
    ctip = {"x_entry": min(cx), "x_exit": lo[1] + CTIP_PAD_EXIT_MARGIN,
            "half_h": BORE_D / 2.0 + CTIP_WALL_MIN + CTIP_PAD_MARGIN, "blend_r": CTIP_PAD_BLEND_R}
    D["ctip"] = ctip
    # Tip gap at wire height = jaw face (x_entry) - crown face on the wire line; must reach TARGET_MAX_GAP at MAX.
    crown_x = horizontal_chord(Polygon(ring_points("l_arm")), D["wire_y"])[1]
    D["gap_min"] = min(cx) - crown_x
    D["gap_max"] = D["gap_min"] + travel["max"]
    if D["gap_max"] < TARGET_MAX_GAP:
        raise RuntimeError(f"MAX tip gap {D['gap_max']:.3f} < {TARGET_MAX_GAP}: increase RACK_EXT")
    bore = {"d": BORE_D, "apex_dir": TEARDROP_APEX_DIR, "overrun": BORE_OVERRUN,
            "ctip_x0": min(cx) - BORE_OVERRUN, "ctip_x1": max(max(cx), ctip["x_exit"]) + BORE_OVERRUN,
            "ctip_chord": (min(cx), max(cx))}
    r_crest = THREAD_MAJOR_D / 2.0
    thread = {"pitch": THREAD_PITCH, "r_crest": r_crest, "r_root": r_crest - THREAD_H, "crest_w": THREAD_CREST_W,
              "flank": THREAD_FLANK_DEG, "rclear": THREAD_RADIAL_CLEAR, "aclear": THREAD_AXIAL_CLEAR,
              "engage": THREAD_ENGAGE, "chamfer": THREAD_TIP_CHAMFER, "n": THREAD_CAM_N}
    hx = D["handle_axis_x"]
    half = BOSS_OD / 2.0                     # flat band = the boss width (boss flush with the pad faces)
    boss = {"od": BOSS_OD, "floor": BOSS_HOLE_FLOOR, "pad_blend": BOSS_PAD_BLEND, "half_len": half,
            "mouth_r_face": r_crest + THREAD_RADIAL_CLEAR + BOSS_MOUTH_FACE_CLEAR, "mouth_depth": BOSS_MOUTH_DEPTH,
            "pad_x0": hx - half - BOSS_PAD_BLEND, "pad_x1": hx + half + BOSS_PAD_BLEND,
            "taper_deg": math.degrees(math.atan2((BOSS_OD - T_Z) / 2.0, BOSS_PAD_BLEND))}
    # Seating arithmetic (round 4). The model is the seated pose: collar face = boss face = ferrule shoulder Y.
    # Screwing in, the collar reaches the boss face first iff the male tip is still short of the hole floor and
    # nothing of the handle wider than the male crest lies above the collar face (the Ø16 core ends inside it).
    y_face = D["ferrule_top_y"]
    seat = {"face_y": y_face, "collar_r": HANDLE_COLLAR_OD / 2.0, "collar_t": HANDLE_COLLAR_T,
            "taper_r": HANDLE_COLLAR_TAPER_R,
            "tip_to_floor": (D["bar_bottom_at_axis"] - BOSS_HOLE_FLOOR) - (y_face + THREAD_ENGAGE),
            "annulus": (boss["mouth_r_face"], min(HANDLE_COLLAR_OD, BOSS_OD) / 2.0)}
    seat["annulus_w"] = seat["annulus"][1] - seat["annulus"][0]
    if seat["tip_to_floor"] <= 0.0 or seat["annulus_w"] <= 0.0 or HANDLE_COLLAR_OD > BOSS_OD:
        raise RuntimeError(f"collar cannot seat first: tip->floor {seat['tip_to_floor']:.3f}, annulus "
                           f"{seat['annulus_w']:.3f}, collar Ø{HANDLE_COLLAR_OD} vs boss Ø{BOSS_OD}")
    thread["seat"] = seat
    if boss["pad_x0"] < D["carriage_x1"] + BOSS_PAD_CARRIAGE_CLEAR:
        raise RuntimeError(f"boss pad starts at X {boss['pad_x0']:.3f}, inside the carriage clearance at MIN "
                           f"({D['carriage_x1']:.3f} + {BOSS_PAD_CARRIAGE_CLEAR})")
    pawl = {"anchor_x": PAWL_ANCHOR_X, "free_x": PAWL_FREE_X, "slot_w": PAWL_SLOT_W,
            "window_top_y": PAWL_WINDOW_TOP_Y, "seat_clear": PAWL_SEAT_CLEAR, "tab_w": TAB_W,
            "tab_bottom_y": TAB_BOTTOM_Y, "pad_len": PAD_LEN, "pad_t": PAD_T, "hook": TOOTH_HOOK_DEG,
            "stop": {"drop": TAB_STOP_DROP, "leg_w": STOP_LEG_W, "beam_t": STOP_BEAM_T, "relief": STOP_RELIEF}}
    return D, travel, chan, teeth, bore, thread, boss, pawl


def seat_notch(a_list, pawl, D):
    """The notch the pawl tooth sits in at MIN opening: the right-most one whose tooth fits in the tongue."""
    best = None
    for a in a_list:
        _, (xl, xr, _) = pawl_tooth_pts(a, rack_bottom_y(D, a), TOOTH_PITCH, TOOTH_DEPTH, TOOTH_LAND,
                                        pawl["seat_clear"], 0.0, pawl["hook"])
        if xl > pawl["anchor_x"] + 2.0 and xr <= pawl["free_x"] - PAWL_TOOTH_MARGIN:
            best = a
    if best is None:
        raise RuntimeError("no rack notch lies under the pawl tongue")
    k = a_list.index(best)
    if k - max(D["pose_teeth"].values()) < 0:
        raise RuntimeError("pawl would run off the toothed length at MAX opening")
    return best, k


def build_pin(pin):
    """Removable end-stop pin (separate part), in its assembled position."""
    return Pos(pin["x"], pin["y"], pin["z0"]) * Solid.make_cylinder(pin["d"] / 2.0, pin["z1"] - pin["z0"])


def build_all():
    D, travel, chan, teeth, bore, thread, boss, pawl = parameters()
    frame, a_list = build_main_frame(D, T_Z, teeth, bore, boss, thread, D["ctip"], D["pin"])
    a_seat, k_seat = seat_notch(a_list, pawl, D)
    slider = build_l_arm_slider(D, T_Z, WRAP_WALL_Z, chan, bore, pawl, a_seat)
    handle = build_handle(D, T_Z, thread)
    pin = build_pin(D["pin"])
    info = {"D": D, "travel": travel, "chan": chan, "teeth": teeth, "bore": bore, "thread": thread, "boss": boss,
            "pawl": pawl, "a_list": a_list, "a_seat": a_seat, "k_seat": k_seat}
    return {"main_frame": frame, "l_arm_slider": slider, "handle": handle, "end_stop_pin": pin}, info


def slider_at(slider, travel):
    """Opening pose: the slider moves -X by `travel` (MIN = 0 = the photographed pose)."""
    return slider.moved(Pos(-travel, 0, 0))


def part_path(name, ext):
    return OUT_DIR / f"{PREFIX}_{name}.{ext}"


# ═════════════════════════════════════════════════════════════════════════════
# 5. GENERATE
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parts, info = build_all()
    D, chan = info["D"], info["chan"]
    print(f"wire Y {D['wire_y']:.3f}  handle axis X {D['handle_axis_x']:.3f}  ferrule shoulder Y {D['ferrule_top_y']:.3f}"
          f"  bar bottom at axis {D['bar_bottom_at_axis']:.3f}")
    print(f"channel Y {chan['y0']:.3f} .. {chan['y1']:.3f} (frame envelope {chan['envelope'][0]:.3f} .. "
          f"{chan['envelope'][1]:.3f} over X {chan['envelope'][2]:.2f} .. {chan['envelope'][3]:.2f})")
    print(f"teeth: {len(info['a_list'])} notches X {info['a_list'][0]:.3f} .. {info['a_list'][-1] + TOOTH_PITCH:.3f};"
          f" pawl seated in notch {info['k_seat']} (a = {info['a_seat']:.3f}) at MIN")
    # Round 4 (round-3 lesson): an invalid solid can HANG the STL export instead of raising, so every part is
    # checked before anything is written.
    bad = []
    for name, shp in parts.items():
        print(f"{name:13s} valid {shp.is_valid}  solids {len(shp.solids())}  volume {shp.volume:10.2f} mm3  "
              f"bbox {shp.bounding_box()}")
        if not shp.is_valid or len(shp.solids()) != 1:
            bad.append(name)
    if bad:
        raise SystemExit(f"invalid part(s) {bad}: nothing exported")
    st = info["thread"]["seat"]
    print(f"seating (arithmetic): collar face = boss face Y {st['face_y']:.3f}; male tip -> hole floor "
          f"{st['tip_to_floor']:.3f}; seating annulus r {st['annulus'][0]:.3f}..{st['annulus'][1]:.3f} "
          f"(width {st['annulus_w']:.3f}); carriage end X {D['carriage_end_x']:.3f}")
    for name, shp in parts.items():
        export_step(shp, str(part_path(name, "step")))
        export_stl(shp, str(part_path(name, "stl")), tolerance=TESS_TOL, angular_tolerance=TESS_ANG)
    pin = D["pin"]
    added, _, _ = ctip_pad_region(D, D["ctip"])
    print(f"pin: X {pin['x']:.3f} Y {pin['y']:.3f} hole Ø{pin['hole_d']:.2f}; collar face {pin['collar_face']:.3f}; "
          f"travel to pin contact {pin['travel_stop_centred']:.3f} (pin centred) / {pin['travel_stop']:.3f} (pin c/2 "
          f"towards the collar); MAX = {pin['n_max']} teeth = {info['travel']['max']:.3f}; tip gap MAX {D['gap_max']:.3f}")
    bs = info["boss"]
    print(f"boss pad: flat X {D['handle_axis_x'] - bs['half_len']:.3f}..{D['handle_axis_x'] + bs['half_len']:.3f}, taper "
          f"{bs['pad_blend']} mm at {bs['taper_deg']:.1f}° from X {bs['pad_x0']:.3f}; carriage end {D['carriage_end_x']:.3f} "
          f"(squared; traced max {D['carriage_x1']:.3f}) -> taper start {bs['pad_x0'] - D['carriage_end_x']:.3f} "
          f"(>= {BOSS_PAD_CARRIAGE_CLEAR}, checked against the traced max)")
    print(f"C-tip pad: X {D['ctip']['x_entry']:.3f}..{D['ctip']['x_exit']:.3f}, half-height {D['ctip']['half_h']:.2f}; "
          f"added to the traced outline {added.area:.2f} mm2")
    for pose, t in info["travel"].items():
        asm = Compound(children=[parts["main_frame"], slider_at(parts["l_arm_slider"], t), parts["handle"],
                                 parts["end_stop_pin"]])
        export_stl(asm, str(part_path(f"assembly_{pose}", "stl")), tolerance=TESS_TOL, angular_tolerance=TESS_ANG)
        print(f"assembly_{pose}: travel {t:.3f} mm written")
