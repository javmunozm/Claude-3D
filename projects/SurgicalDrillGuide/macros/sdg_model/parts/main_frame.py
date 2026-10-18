"""main_frame: C-hook + bar + rack (traced ring), teeth, C-tip bore and pad, end-stop pin hole; round 6: uniform
Z 0..T_Z, handle lug (tenon), external snap finger with hook, bar top raised to a flat Y BAR_TOP_Y."""

import math

from shapely.geometry import Polygon
from shapely.geometry import box as sbox
from shapely.ops import unary_union

from ..mechanisms import sawtooth_cutter_face
from ..rings import rack_bottom_y, rack_flat_poly, ring_face, vertical_chord
from ..shapes import extrude_z, keep_below, one_solid, polygon_face, shapely_faces, teardrop_bore_x, xz_prism_y, \
    yz_prism_x


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


def coupling_region(D, coup):
    """Round 6 in-plane additions to the traced outline: lug + r root fillets, snap finger + root fillets, raised
    bar. Each fillet is a closing restricted to its own zone (a global closing would bridge lug and finger, and
    would round the ramp root to the left of the carriage clearance line). Returns {name: added region}."""
    ring = D["frame_poly"]
    yb = lambda x: vertical_chord(ring, x)[0]
    lug, fin, bar = coup["lug"], coup["finger"], coup["bar"]
    y_hi = max(yb(lug["x0"]), yb(fin["x1"])) + 2.0                    # inside the bar
    out = {}
    r = lug["r"]
    rect = sbox(lug["x0"], lug["y_end"], lug["x1"], y_hi)
    closed = ring.union(rect).buffer(r, quad_segs=32).buffer(-r, quad_segs=32)
    # fillets from the closing (root zone only); the lug body is the exact rectangle, so its end corners carry
    # no closing micro-facets (build 2: 0.04 mm2 of >45° triangles where the foot chamfers met them)
    root = closed.intersection(sbox(lug["x0"] - r - 0.5, yb(lug["x0"]) - r - 0.5, lug["x1"] + r + 0.5, y_hi))
    out["lug"] = unary_union([root, rect]).difference(ring)
    r, c = fin["r"], fin["tip_ch"]
    fpoly = Polygon([(fin["x0"], y_hi), (fin["x0"], fin["y_tip"] + c), (fin["x0"] + c, fin["y_tip"]),
                     (fin["x1"] - c, fin["y_tip"]), (fin["x1"], fin["y_tip"] + c), (fin["x1"], y_hi)])
    closed = ring.union(fpoly).buffer(r, quad_segs=32).buffer(-r, quad_segs=32)
    out["finger"] = closed.intersection(sbox(fin["x0"] - r - 0.5, fin["y_tip"] - 1, fin["x1"] + r + 0.5, y_hi)
                                        ).difference(ring)
    x0, y0, yt = bar["x0"], bar["y0"], bar["y_top"]
    run = (yt - y0) / math.tan(math.radians(bar["ramp_deg"]))
    xe = bar["x_hook"] + 1.0                                          # 1 mm into the hook column
    bpoly = Polygon([(x0, y0 - 3.0), (x0, y0), (x0 + run, yt), (xe, yt), (xe, y0 - 3.0)])
    rb = bar["blend_r"]
    closed = ring.union(bpoly).buffer(rb, quad_segs=32).buffer(-rb, quad_segs=32)
    blend = closed.intersection(sbox(bar["x_hook"] - 4 * rb, yt - 2 * rb, xe + rb, yt + 3 * rb))
    out["bar"] = unary_union([bpoly, blend]).difference(ring)
    return out


def _smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


def hook_outer_d(ho, s):
    """Outer offset d(s): smoothstep 0 -> d_full over s_blend, d_full to s_taper[0], smoothstep to d_hold by
    s_taper[1], d_hold to s_hold_end, smoothstep to 0 over end_len (every transition G1)."""
    (b0, b1), (t0, t1), se = ho["s_blend"], ho["s_taper"], ho["s_hold_end"]
    if s < b1:
        return ho["d_full"] * _smooth((s - b0) / (b1 - b0))
    if s < t0:
        return ho["d_full"]
    if s < t1:
        return ho["d_full"] + (ho["d_hold"] - ho["d_full"]) * _smooth((s - t0) / (t1 - t0))
    return ho["d_hold"] * (1.0 - _smooth((s - se) / ho["end_len"]))


def hook_outer_edge(ring, st):
    """Outer-edge point of one station: the first ring crossing from the centroid along the outward normal
    (tangent rotated -90°, i.e. away from the C's throat)."""
    from shapely.geometry import LineString, Point
    s, xc, yc, a = st
    n = (math.sin(math.radians(a)), -math.cos(math.radians(a)))
    hit = ring.exterior.intersection(LineString([(xc, yc), (xc + 30 * n[0], yc + 30 * n[1])]))
    pts = [Point(q) for g in getattr(hit, "geoms", [hit]) for q in g.coords]
    return min(pts, key=lambda p: p.distance(Point(xc, yc))), n


def hook_outer_region(D, ho):
    """Round 6 pass 3: the hook band as ONE convex outer curve. The convex hull of the d(s) sweep (which fills the
    sweep's dents and keeps every width it had) plus the traced ring's corner at the bore exit face, minus the ring;
    only the component outside the hook is kept (the hull's chord across the throat is discarded). The top end runs
    straight into that corner (a fillet there would come within 2.0 of the wire axis); the bar-bottom end is closed
    with an r ho["fillet_r"] concave fillet, limited to a window round its junction. Returns the added region."""
    from shapely.geometry import box as sbox
    ring, ct, sts = D["frame_poly"], D["ctip"], ho["stations"]
    sw = hook_outer_sweep(D, ho)
    p_end = hook_outer_edge(ring, sts[-1])[0]
    corner = ring.intersection(sbox(ct["x_exit"], p_end.y - 1.0, p_end.x + 1.0, D["wire_y"] - ho["wire_min"]))
    cand = unary_union([sw, corner]).convex_hull.difference(ring)
    band = unary_union([g for g in getattr(cand, "geoms", [cand]) if g.intersects(sw.buffer(-0.05))])
    r = ho["fillet_r"]
    p0 = hook_outer_edge(ring, min(sts, key=lambda q: abs(q[0] - ho["s_blend"][0])))[0]
    closed = ring.union(band).buffer(r, quad_segs=32).buffer(-r, quad_segs=32)
    fill = closed.intersection(p0.buffer(4 * r)).difference(ring).difference(band)
    fill = [g for g in getattr(fill, "geoms", [fill]) if g.area > 0.01 and g.distance(band) < 1e-6]
    return unary_union([band] + fill).simplify(0.005)


def hook_outer_sweep(D, ho):
    """Round 6 pass 2: material added OUTSIDE the C-hook's outer contour, d(s) wide (hook_outer_d). Built as a
    variable-radius disc sweep (hull of consecutive discs) centred on the live ring's outer contour, minus the
    ring, so the inner contour, throat, jaw face and bore region cannot move. Returns the added region."""
    ring = D["frame_poly"]
    ext = ring.exterior
    L_ring = ext.length
    sts = ho["stations"]
    Ls = [ext.project(hook_outer_edge(ring, st)[0]) for st in sts]
    for i in range(1, len(Ls)):                                     # unwrap: monotonic along the contour
        while abs(Ls[i] - Ls[i - 1]) > 0.5 * L_ring:
            Ls[i] += L_ring if Ls[i] < Ls[i - 1] else -L_ring
    sgn = 1.0 if Ls[-1] > Ls[0] else -1.0
    Lu = [sgn * q for q in Ls]                                      # increasing with s
    ss = [st[0] for st in sts]

    def s_of(L):
        for i in range(1, len(Lu)):
            if L <= Lu[i]:
                return ss[i - 1] + (ss[i] - ss[i - 1]) * (L - Lu[i - 1]) / (Lu[i] - Lu[i - 1])
        return ss[-1]

    from shapely.geometry import Point
    n = int(math.ceil((Lu[-1] - Lu[0]) / ho["step"]))
    discs = []
    for k in range(n + 1):
        L = Lu[0] + (Lu[-1] - Lu[0]) * k / n
        d = hook_outer_d(ho, s_of(L))
        p = ext.interpolate((sgn * L) % L_ring)
        discs.append(Point(p).buffer(d, quad_segs=24) if d > 0.01 else None)
    hulls = [unary_union([a, b]).convex_hull for a, b in zip(discs, discs[1:]) if a is not None and b is not None]
    return unary_union(hulls).difference(ring).simplify(0.005)


def snap_hook(coup):
    """Hook on the finger's -X face: XY profile (30° ramp, land, top) over Z z0..z1, trimmed by the 45° gable
    retention planes with the back-cut, and by the under-chamfer at Z z0. Overlaps the finger by 0.5 in +X."""
    fin, hk = coup["finger"], coup["hook"]
    fx0, d, k = fin["x0"], hk["depth"], hk["k"]
    (ya, yb_), zr = hk["ramp_y"], 0.5 * (hk["z0"] + hk["z1"])
    slope = (yb_ - ya) / d                                            # ramp rise per mm in -X
    pts = [(fx0 + 0.5, ya - 0.5 * slope), (fx0 - d, yb_), (fx0 - d, hk["ridge_y"] + 1.5),
           (fx0 + 0.5, hk["ridge_y"] + 1.5)]
    h = extrude_z(polygon_face(pts), hk["z0"], hk["z1"])
    p = (fx0, hk["ridge_y"], zr)
    h = keep_below(h, p, (k, 1, -1), "hook gable -Z flank")
    h = keep_below(h, p, (k, 1, 1), "hook gable +Z flank")
    a = d / hk["under_z"]
    h = keep_below(h, (fx0, 0, hk["z0"]), (-1, 0, -a), "hook under-chamfer")
    return h


def lug_foot_cutters(D, coup, t_z):
    """45° elephant's-foot cutters on the lug's Z 0 edges: both straight sides (up to where the root fillet
    starts) and the end. The fillets themselves are not chamfered (they sit in the socket mouth relief)."""
    lug = coup["lug"]
    c, x0, x1, ye = lug["foot"], lug["x0"], lug["x1"], lug["y_end"]
    yb = lambda x: vertical_chord(D["frame_poly"], x)[0]
    cut = []
    for xs, sgn in ((x0, +1), (x1, -1)):
        y_fs = yb(xs) - lug["r"] - 0.05
        tri = [(xs - sgn * 1.0, -1.0), (xs + sgn * (c + 1.0), -1.0), (xs - sgn * 1.0, c + 1.0)]
        cut.append(xz_prism_y(tri, ye - 1.0, y_fs))
    cut.append(yz_prism_x([(ye - 1.0, -1.0), (ye + c + 1.0, -1.0), (ye - 1.0, c + 1.0)], x0 - 1.0, x1 + 1.0))
    return cut


def build_main_frame(D, t_z, teeth, bore, coup, ctip, pin):
    """C-hook + bar + rack (traced ring) + rack teeth + closed C-tip wire bore + C-tip pad + end-stop pin hole;
    round 6: lug, snap finger + hook, raised bar (all uniform Z 0..t_z)."""
    frame = extrude_z(ring_face("frame"), 0.0, t_z)
    # Rack extension (user decision): the extruded extension region overlaps the traced rack by 0.5 mm.
    frame = one_solid(frame + extrude_z(polygon_face(list(D["rack_ext_poly"].exterior.coords)[:-1]), 0.0, t_z),
                      "frame + rack extension")
    zc = t_z / 2.0

    # C-tip pad (before the bore, so the bore is cut through it).
    _, region, _ = ctip_pad_region(D, ctip)
    for f in shapely_faces(region):
        frame = one_solid(frame + extrude_z(f, 0.0, t_z), "frame + C-tip pad")

    # Round 6 in-plane additions, grown 0.4 into the traced ring (a real overlap), clipped to the new outline.
    add = unary_union(list(coupling_region(D, coup).values()) + [hook_outer_region(D, D["hook_outer"])])
    outline = D["frame_poly"].union(add)
    for f in shapely_faces(add.buffer(0.4, quad_segs=16).intersection(outline)):
        frame = one_solid(frame + extrude_z(f, 0.0, t_z), "frame + lug/finger/bar/hook outer")
    frame = one_solid(frame + snap_hook(coup), "frame + snap hook")
    for cutter in lug_foot_cutters(D, coup, t_z):
        frame = one_solid(frame - cutter, "frame - lug foot chamfer")

    # End-stop pin hole (Z) near the rack's free end, between the rack top and the notch apex line.
    from build123d import Pos, Solid
    frame = one_solid(frame - (Pos(pin["x"], pin["y"], -1.0) * Solid.make_cylinder(pin["hole_d"] / 2.0, t_z + 2.0)),
                      "frame - pin hole")

    # Rack teeth (bottom face). r7: the underside is first made flat (rack_bottom_y) up to a point inside the last
    # notch's bottom span, so the wedge's end step is removed with that notch.
    yb = lambda x: rack_bottom_y(D, x)
    cut_face, a_list = sawtooth_cutter_face(yb, teeth["x0"], teeth["x1"], teeth["pitch"], teeth["depth"],
                                            teeth["land"], teeth["eps"], teeth["hook"])
    x_flat_end = a_list[-1] + 0.5 * (teeth["depth"] * math.tan(math.radians(teeth["hook"]))
                                     + teeth["pitch"] - teeth["land"])
    frame = one_solid(frame + extrude_z(polygon_face(list(rack_flat_poly(D, x_flat_end).exterior.coords)[:-1]),
                                        0.0, t_z), "frame + flat rack underside")
    frame = one_solid(frame - extrude_z(cut_face, -1.0, t_z + 1.0), "frame - teeth")

    # Closed C-tip bore on the rectified wire line. The cutter spans only the C-tip (the only frame material
    # at the wire height), so it cannot touch the rest of the hook.
    frame = one_solid(frame - teardrop_bore_x(bore["ctip_x0"], bore["ctip_x1"], D["wire_y"], zc, bore["d"],
                                              bore["apex_dir"]), "frame - C-tip bore")
    return frame, a_list
