"""Floor plate between the grip ends (right half, x >= 0) and its blend into the grip end's underside.
No window or camera hole yet (a later pass)."""
import numpy as np

from ..shapes import box, blend_wire, loft_wires, one_solid


def build_plate_half(x_s, x2, z2, y0, y1, z0, z1):
    """Boxes only, so every face that meets the floor or the plate bottom is a plane: main slab x 0..x_s (touches
    the blend loft's trimmed end at x_s), an upper slab z2..z1 out to x2 (over the blend loft's top, into the grip).
    Both run from the plate front y0 to the rear face y1."""
    a = box(0.0, x_s, y0, y1, z0, z1)
    b = box(0.0, x2, y0, y1, z2, z1)
    return one_solid(a.fuse(b), "plate boxes")


def build_blend(profiles, x_s, y1, what="plate blend"):
    """profiles: [(y, blend_profile dict)], front to rear. Loft, then trim at x >= x_s and y <= y1 (exact planes)."""
    s = loft_wires([blend_wire(y, p) for y, p in profiles], what)
    return one_solid(s.intersect(box(x_s, 300.0, -100.0, y1, -100.0, 100.0)), what + " trimmed")


def front_round_cutter(blend, y0, x0, x1, r, ramp, step=0.25, cross=0.005, air=0.3, r_min=0.004, start=0.25):
    """Cutter for the round between the blend's front face (plane y0) and its underside, to be cut from the LONE
    blend before any fuse. Lofted along x through sections in the planes x0 + start .. x1 (a vertex start at x0
    inverted the loft: trial t3; a 0.004 mm end face at x0 folded: t1). Per section: radius
    r(x) = r_min + (r - r_min) smoothstep((x - x0) / ramp); the underside line is the secant through the blend's
    underside at y0 + 1e-4 and y0 + max(r, 0.05) (z-rays); the arc is tangent to the front plane and that line,
    drawn at r (1 + cross) about the same centre so it crosses both faces instead of touching them. The rest of
    each section lies in air, scaled with r. Returns (cutter, info rows [x, r, corner z, slope k, top z on y0])."""
    from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
    from OCP.gp import gp_Lin, gp_Pnt, gp_Dir
    from build123d import Edge, Wire, Vector, Vertex, Solid
    hit = IntCurvesFace_ShapeIntersector()
    hit.Load(blend.wrapped, 1e-7)

    def z_low(x, y):
        hit.Perform(gp_Lin(gp_Pnt(x, y, -100.0), gp_Dir(0.0, 0.0, 1.0)), -1e9, 1e9)
        zs = [hit.Pnt(i).Z() for i in range(1, hit.NbPnt() + 1)]
        if not zs:
            raise RuntimeError("front round: no blend under (%.3f, %.3f)" % (x, y))
        return min(zs)

    objs, info = [], []
    for x in np.arange(x0 + start, x1 + 1e-9, step):
        t = min(1.0, (x - x0) / ramp)
        rx = r_min + (r - r_min) * t * t * (3.0 - 2.0 * t)
        a = air * max(rx / r, 0.1)
        ya, yb = y0 + 1e-4, y0 + max(rx, 0.05)
        za = z_low(x, ya)
        k = (z_low(x, yb) - za) / (yb - ya)                     # secant slope (the tangent-point slope folded: t4)
        zl = za - k * (ya - y0)                                 # the line's height at y0
        s = np.hypot(1.0, k)
        n2, t2 = np.array([-k, 1.0]) / s, np.array([1.0, k]) / s
        c = np.array([y0, zl])
        o = c + np.array([rx, k * rx + rx * s])
        rr = rx * (1.0 + cross)
        h = np.sqrt(rr * rr - rx * rx)
        pa = np.array([y0, o[1] - h])
        pb = c + ((o - rx * n2 - c) @ t2 - h) * t2
        pm = o + rr * (c - o) / np.linalg.norm(c - o)
        # past pb the cutter runs on for L = a to a point 0.1 L UNDER the real underside, then drops into air: past
        # the secant's far point the underside falls below the line, and a straight drop at pb (t5) or at the end of
        # a 5.7 deg dive along the line (t6) cut an 84 deg micro-step there
        L = a
        dlt = (zl + k * (pb[0] + L - y0)) - z_low(x, pb[0] + L)         # surface below the line at pb + L
        pd = np.array([pb[0] + L, z_low(x, pb[0] + L) - 0.1 * L])
        v = lambda p: Vector(float(x), float(p[0]), float(p[1]))
        ring = [pb, pd, pd - a * n2, c + np.array([-a - L, -a - L]), pa + np.array([-a, 0.0]), pa]
        edges = [Edge.make_three_point_arc(v(pa), v(pm), v(pb))]
        edges += [Edge.make_line(v(p), v(q)) for p, q in zip(ring[:-1], ring[1:])]
        objs.append(Wire(edges))
        info.append([round(float(q), 4) for q in (x, rx, zl, k, pa[1], dlt, L)])
    return one_solid(Solid.make_loft(objs, ruled=False), "front round cutter"), info


def nose_fillet(P, y0, z_top, z_bot, r, laws, n=41, skip_missing=False, spine_rev=False, check=True):
    """Pass plate: round the lone plate's (boxes + blend) top and bottom edges on the plane y0 with variable-radius
    fillets (BRepFilletAPI). P's coplanar faces are unified first, so each edge's neighbours are one plane each.
    laws: {"top": (x1, x_e, r_e), "bottom": (...)}: radius r for x <= x1, smoothstep to r_e at x_e, r_e beyond.
    Each contour starts at the edge through x 0 and runs on along tangent edges. Returns (solid, info)."""
    from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
    from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
    from OCP.TColgp import TColgp_Array1OfPnt2d
    from OCP.gp import gp_Pnt2d
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_SOLID, TopAbs_REVERSED
    from OCP.TopoDS import TopoDS
    from build123d import Solid

    def solid_of(shape, what):
        out, ex = [], TopExp_Explorer(shape, TopAbs_SOLID)
        while ex.More():
            out.append(Solid(TopoDS.Solid_s(ex.Current())))
            ex.Next()
        if len(out) != 1:
            raise RuntimeError("%s: %d solids" % (what, len(out)))
        return one_solid(out[0], what)

    uf = ShapeUpgrade_UnifySameDomain(P.wrapped, True, True, False)
    uf.Build()
    P = solid_of(uf.Shape(), "plate unified")
    mk = BRepFilletAPI_MakeFillet(P.wrapped)
    info = {}
    for name, zz in (("top", z_top), ("bottom", z_bot)):
        if laws.get(name) is None:      # run 3: this edge is rounded after the fuse (nose_post_fillet)
            continue
        x1, xe, re = laws[name]
        law = lambda x: re + (r - re) * (1.0 - _ss(x, x1, xe))
        seed = [e for e in P.edges() if abs(e.bounding_box().min.Y - y0) < 1e-6 and abs(e.bounding_box().max.Y - y0) < 1e-6
                and abs(e.bounding_box().min.Z - zz) < 1e-6 and abs(e.bounding_box().max.Z - zz) < 1e-6
                and e.bounding_box().min.X < 1e-6]
        if not seed and skip_missing:
            continue
        if len(seed) != 1:
            raise RuntimeError("nose fillet %s: %d seed edges at y %.2f z %.2f" % (name, len(seed), y0, zz))
        mk.Add(seed[0].wrapped)
        ic = mk.Contour(seed[0].wrapped)
        rows = []
        for k in range(1, mk.NbEdges(ic) + 1):
            # UandR's U is relative along the spine: a REVERSED spine edge runs from its curve's last parameter
            ek = mk.Edge(ic, k)
            c = BRepAdaptor_Curve(ek)
            f, l = c.FirstParameter(), c.LastParameter()
            if spine_rev and ek.Orientation() == TopAbs_REVERSED:
                f, l = l, f
            arr = TColgp_Array1OfPnt2d(1, n)
            for i in range(n):
                t = i / (n - 1.0)
                arr.SetValue(i + 1, gp_Pnt2d(t, law(c.Value(f + t * (l - f)).X())))
            mk.SetRadius(arr, ic, k)
            p0, p1 = c.Value(f), c.Value(l)
            rows.append([round(v, 3) for v in (p0.X(), p0.Z(), p1.X(), p1.Z(), law(p0.X()), law(p1.X()))])
        info[name] = rows
    mk.Build()
    if not mk.IsDone():
        raise RuntimeError("nose fillet at y %.2f failed" % y0)
    if not check:
        return Solid(TopoDS.Solid_s(TopExp_Explorer(mk.Shape(), TopAbs_SOLID).Current())), info
    return solid_of(mk.Shape(), "plate nose fillet y %.2f" % y0), info


def nose_post_fillet(S, y0, z_top, law, n=41, extra=False):
    """Pass plate run 3: round the top edge on the plane y0 AFTER the fuse with the grip end, as one contour that runs
    on along the grip's tangent edges (no cusp where the plate meets the grip). law = (r, x1, x_e, r_e, l_end, r_tip):
    radius r for x <= x1, smoothstep to r_e at x_e; over the contour's last l_end mm (arc length) it falls
    (smoothstep) to r_tip. Returns (solid, info rows [x0, y0, z0, x1, y1, z1, r0, r1] per spine edge)."""
    from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
    from OCP.TColgp import TColgp_Array1OfPnt2d
    from OCP.gp import gp_Pnt2d
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    from OCP.GCPnts import GCPnts_AbscissaPoint
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_SOLID, TopAbs_REVERSED
    from OCP.TopoDS import TopoDS
    from build123d import Solid

    r, x1, xe, re, l_end, r_tip = law[:6]
    extra = extra or (len(law) > 6 and bool(law[6]))     # law[6] = 1: also add the next floor edge (front)
    seed = [e for e in S.edges() if abs(e.bounding_box().min.Y - y0) < 1e-6 and abs(e.bounding_box().max.Y - y0) < 1e-6
            and abs(e.bounding_box().min.Z - z_top) < 1e-6 and abs(e.bounding_box().max.Z - z_top) < 1e-6
            and e.bounding_box().min.X < 1e-6]
    if len(seed) != 1:
        raise RuntimeError("nose post fillet: %d seed edges at y %.2f z %.2f" % (len(seed), y0, z_top))
    mk = BRepFilletAPI_MakeFillet(S.wrapped)
    mk.Add(seed[0].wrapped)
    seeds = [seed[0]]
    if extra:
        # the plate edge's contour stops at a vertex where the next edge on the floor (z_top) is not tangent (the
        # corner web's top edge, 5.7 deg): add it as a second contour, which runs on along its own tangent edges
        sb = seed[0].bounding_box()
        far = max(seed[0].vertices(), key=lambda v: v.X)
        nxt = [e for e in S.edges() if abs(e.bounding_box().min.Z - z_top) < 1e-6
               and abs(e.bounding_box().max.Z - z_top) < 1e-6 and not e.is_same(seed[0])
               and min(abs(v.X - far.X) + abs(v.Y - far.Y) + abs(v.Z - far.Z) for v in e.vertices()) < 1e-6]
        if len(nxt) != 1:
            raise RuntimeError("nose post fillet: %d floor edges at the plate edge's end (%.3f)" % (len(nxt), sb.max.X))
        mk.Add(nxt[0].wrapped)
        seeds.append(nxt[0])
    eds = []
    for sd in seeds:
        ic = mk.Contour(sd.wrapped)
        ce = []
        for k in range(1, mk.NbEdges(ic) + 1):
            c = BRepAdaptor_Curve(mk.Edge(ic, k))
            f, l = c.FirstParameter(), c.LastParameter()
            ce.append((ic, k, c, f, l, GCPnts_AbscissaPoint.Length_s(c)))
        if eds:
            # a later contour must start at the previous one's end: reverse its listing if OCC gave it far end first
            pe = eds[-1]
            ends = [pe[2].Value(pe[3]), pe[2].Value(pe[4])]

            def touches(q):
                return min(min(q[2].Value(q[3]).Distance(p), q[2].Value(q[4]).Distance(p)) for p in ends) < 1e-6
            if not touches(ce[0]) and touches(ce[-1]):
                ce = ce[::-1]
        eds += ce
    # orientation of each edge along the chain: the end nearer the previous edge's far end comes first
    prev, chain = None, []
    for ic, k, c, f, l, L in eds:
        a, b = c.Value(f), c.Value(l)
        if prev is None:
            fwd = a.X() < b.X()
        else:
            fwd = a.Distance(prev) <= b.Distance(prev)
        chain.append((ic, k, c, f, l, L, fwd))
        prev = b if fwd else a
    total = sum(q[5] for q in chain)
    # OCC may list the contour from its far end: measure s from the x 0 end
    c0, cl = chain[0], chain[-1]
    start = c0[2].Value(c0[3] if c0[6] else c0[4])
    from_far = start.X() > 1e-3

    def rad(x, s):
        if from_far:
            s = total - s
        base = re + (r - re) * (1.0 - _ss(x, x1, xe))
        if l_end > 0.0:
            base = r_tip + (base - r_tip) * _ss(total - s, 0.0, l_end)
        return base

    rows, s0 = [], 0.0
    for ic, k, c, f, l, L, fwd in chain:
        arr = TColgp_Array1OfPnt2d(1, n)
        for i in range(n):
            t = i / (n - 1.0)          # UandR's U runs along the curve's own parameter
            p = c.Value(f + t * (l - f))
            s = s0 + (t * L if fwd else (1.0 - t) * L)
            arr.SetValue(i + 1, gp_Pnt2d(t, rad(p.X(), s)))
        mk.SetRadius(arr, ic, k)
        p0, p1 = c.Value(f), c.Value(l)
        rows.append([round(v, 3) for v in (p0.X(), p0.Y(), p0.Z(), p1.X(), p1.Y(), p1.Z(),
                                            arr.Value(1).Y(), arr.Value(n).Y())] + [int(fwd)])
        s0 += L
    mk.Build()
    if not mk.IsDone():
        raise RuntimeError("nose post fillet at y %.2f failed" % y0)
    out, ex = [], TopExp_Explorer(mk.Shape(), TopAbs_SOLID)
    while ex.More():
        out.append(Solid(TopoDS.Solid_s(ex.Current())))
        ex.Next()
    if len(out) != 1:
        raise RuntimeError("nose post fillet: %d solids" % len(out))
    return one_solid(out[0], "nose post fillet y %.2f" % y0), rows


def _ss(x, a, b):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def nose_law(x, p, front):
    """Per-section parameters of a plate-edge nose (pass plate): radius, front-most inset d (u of the arc's front-most
    point; > 0 cuts the whole face, -r c is the natural crossing) and crossing c for the top (t) and bottom (b) arcs.
    Full half-round (one circle, r_full) for x <= x1; then r_t (both on the rear) shrink to r_end and lift off into air,
    r_b on the front goes to the old FRONT_ROUND (r_bf, crossing c_bf) and runs on to the cutter's end."""
    r0, c0, d0, x1 = p["r"], p["cross"], p["inset"], p["x1"]
    # the inset stays d0 (> 0: the front face is cut away) until the arcs have parted (a flat between them), then
    # goes to the natural crossing: the face re-emerges across the flat, transversally (a re-emergence at the merged
    # circle's front-most point is tangent and left an invalid face: trial t1)
    sd = _ss(x, p["x_d0"], p["x_d0"] + p["d_ramp"])
    r_t = r0 + (p["r_end"] - r0) * _ss(x, x1, p["x_shrink"])
    xl = p.get("x_lift", p["x_shrink"])
    lift = _ss(x, xl, xl + p["lift"])
    if front:
        r_b = r0 + (p["r_bf"] - r0) * _ss(x, x1, p["x_bf"])
        c_b = c0 + (p["c_bf"] - c0) * _ss(x, p["x_c0"], p["x_bf"])
        lift_b = 0.0
    else:
        r_b, c_b, lift_b = r_t, c0, lift
    d_t = d0 + (-r_t * c0 - d0) * sd - (r_t * (1.0 + c0) + p["lift_gap"]) * lift
    d_b = d0 + (-r_b * c_b - d0) * sd - (r_b * (1.0 + c_b) + p["lift_gap"]) * lift_b
    return dict(r_t=r_t, r_b=r_b, c_t=c0, c_b=c_b, d_t=d_t, d_b=d_b)


def _join_edges(edges, tol=1e-6):
    """One B-spline edge, exactly the chain of edges (arcs stay rational arcs): a constant edge count per loft section."""
    from OCP.GeomConvert import GeomConvert_CompCurveToBSplineCurve, GeomConvert
    from OCP.Geom import Geom_TrimmedCurve
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
    from build123d import Edge
    cc = None
    for e in edges:
        ad = e.geom_adaptor()
        bs = GeomConvert.CurveToBSplineCurve_s(Geom_TrimmedCurve(ad.Curve().Curve(), ad.FirstParameter(),
                                                                 ad.LastParameter()))
        if cc is None:
            cc = GeomConvert_CompCurveToBSplineCurve(bs)
        elif not cc.Add(bs, tol, True):
            raise RuntimeError("nose: profile edges do not join")
    return Edge(BRepBuilderAPI_MakeEdge(cc.BSplineCurve()).Edge())


def nose_section(x, y0, sgn, zt, q, zl, k, z_low=None, A=1.0, L=0.3):
    """Cutter section in the plane x, in (u, z) with u = sgn (y - y0) into the plate. Profile (one edge): the top arc
    (centre r_t under the top plane zt, radius r_t (1 + c_t), front-most point at u = d_t) from its top point (r_t c_t
    above the plane: air) to its front-most point, a straight flat to the bottom arc's front-most point, the bottom
    arc (tangent at r_b to the line z = zl + k u, radius r_b (1 + c_b), front-most at d_b) to its lowest point (r_b c_b
    under the line). Then into air: L along the line to 0.1 L under the underside (z_low(u), or the line), down A, to
    u = -A, up to zt + A, back over the top point."""
    from build123d import Edge, Wire, Vector
    v = lambda p: Vector(float(x), float(y0 + sgn * p[0]), float(p[1]))
    s = np.hypot(1.0, k)
    n = np.array([-k, 1.0]) / s
    Rt, Rb = q["r_t"] * (1.0 + q["c_t"]), q["r_b"] * (1.0 + q["c_b"])
    ct = np.array([q["d_t"] + Rt, zt - q["r_t"]])
    cbu = q["d_b"] + Rb
    cb = np.array([cbu, zl + k * cbu + q["r_b"] * s])
    arc = lambda c, R, a0, a1: Edge.make_three_point_arc(
        *[v(c + R * np.array([np.cos(a), np.sin(a)])) for a in (a0, 0.5 * (a0 + a1), a1)])
    a_end = np.arctan2(-n[1], -n[0])                                    # direction -n: the lowest point
    prof = [arc(ct, Rt, 0.5 * np.pi, np.pi)]
    ft, fb = ct - np.array([Rt, 0.0]), cb - np.array([Rb, 0.0])
    if np.linalg.norm(fb - ft) > 1e-7:
        prof.append(Edge.make_line(v(ft), v(fb)))
    prof.append(arc(cb, Rb, np.pi, a_end + 2.0 * np.pi))
    pt, pb = ct + np.array([0.0, Rt]), cb - Rb * n
    uq = pb[0] + L
    zq = (z_low(uq) if z_low else zl + k * uq) - 0.1 * L
    ring = [pb, np.array([uq, zq]), np.array([uq, zq - A]), np.array([-A, zq - A]), np.array([-A, zt + A]),
            np.array([pt[0], zt + A]), pt]
    edges = [_join_edges(prof)] + [Edge.make_line(v(a), v(b)) for a, b in zip(ring[:-1], ring[1:])]
    return Wire(edges)


def nose_cutter(P, y0, sgn, zt, zb_flat, x_flat, p, front, x0, x_end, step=0.25, prism_on=True):
    """Cutter for one plate edge (front y0 = PLATE_Y0, sgn +1; rear PLATE_Y1, sgn -1), to be cut from the LONE plate
    (boxes + blend) before the fuse with the grip end. x0..p["x1"]: a prism of the full half-round section (bottom
    plane zb_flat); p["x1"]..x_end: a loft through sections every `step` (nose_law), the underside a secant of P's
    underside (z-rays) for x > x_flat. Returns (cutter, info rows [x, r_t, r_b, d_t, d_b, zl, k])."""
    from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
    from OCP.gp import gp_Lin, gp_Pnt, gp_Dir
    from build123d import Face, Solid, Vector
    hit = IntCurvesFace_ShapeIntersector()
    hit.Load(P.wrapped, 1e-7)

    def z_low(x, u):
        hit.Perform(gp_Lin(gp_Pnt(x, y0 + sgn * u, -100.0), gp_Dir(0.0, 0.0, 1.0)), -1e9, 1e9)
        zs = [hit.Pnt(i).Z() for i in range(1, hit.NbPnt() + 1)]
        if not zs:
            raise RuntimeError("nose: no plate under (%.3f, u %.3f)" % (x, u))
        return min(zs)

    def section(x):
        q = nose_law(x, p, front)
        if x <= x_flat:
            zl, k, zf = zb_flat, 0.0, None
        else:
            ua, ub = 1e-4, max(q["r_b"], 0.05)
            za = z_low(x, ua)
            k = (z_low(x, ub) - za) / (ub - ua)
            zl = za - k * ua
            zf = lambda u: z_low(x, u)
        info = [round(float(t), 5) for t in (x, q["r_t"], q["r_b"], q["d_t"], q["d_b"], zl, k)]
        return nose_section(x, y0, sgn, zt, q, zl, k, zf), info

    w0, _ = section(p["x1"])
    prism = one_solid(Solid.extrude(Face(section_at(w0, x0 - p["x1"])), Vector(p["x1"] - x0, 0.0, 0.0)), "nose prism")
    wires, info = [], []
    for x in np.arange(p["x1"], x_end + 1e-9, step):
        w, i = section(float(x))
        wires.append(w)
        info.append(i)
    loft = one_solid(Solid.make_loft(wires, ruled=False), "nose loft")
    if sgn > 0:
        # only the rear frame (sgn -1) gives a loft the right way out (the front's grew the plate by 14.5 mm3, and
        # reversing it left unorientable faces: trials t4, t5); build the front as the rear of the mirrored plate
        raise ValueError("nose_cutter: build the front with nose_cutter_front (mirrored frame)")
    if not prism_on:
        return loft, info
    # the prism and the loft are cut one after the other (their fuse left invalid faces at x1: trial t3)
    return [prism, loft], info


def nose_cutter_any(P, y0, sgn, *a, **k):
    """nose_cutter for either edge: the front (sgn +1) is built as the rear edge of P mirrored in y, then mirrored back."""
    from build123d import Plane
    if sgn < 0:
        return nose_cutter(P, y0, sgn, *a, **k)
    cut, info = nose_cutter(P.mirror(Plane.XZ), -y0, -1.0, *a, **k)
    cut = [c.mirror(Plane.XZ) for c in cut] if isinstance(cut, list) else cut.mirror(Plane.XZ)
    return cut, info


def section_at(w, dx):
    from build123d import Location
    return w.moved(Location((dx, 0.0, 0.0)))


def corner_round_web(plate_side, grip, r, z_top, z_start, alpha_end, x_guess, y_guess, step=0.2, fine_z=-12.8,
                     fine_step=0.1, z_min=-16.0, cross=0.005, air=0.25, sink=0.6, region=(62.0, 74.0, -16.0, -6.0,
                                                                                         -18.0, -5.0)):
    """Concave rolling-ball round of radius r between the plate side (plate_side: shapes whose surfaces are the
    plate front plane and the front round below it) and the grip, as a lone web solid to fuse in.
    Ball centres C are solved in planes z = const, from z_start down (step, fine_step below fine_z) until the angle
    between the two contact normals falls under alpha_end. Each section lies in the plane through C and both contact
    points: an arc about C from contact direction u1 to u2 at radius r (1 + cross), so it crosses both faces, closed
    through points `air` mm inside the material. Over the last `sink` mm of the ball path the arc radius grows to
    r / cos(alpha / 2) (+0.2 %), so the web's end sinks into the material instead of ending in a face. Trimmed at
    z <= z_top (the floor plane). Returns (web, info rows [z, Cx, Cy, alpha deg, arc radius])."""
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    from scipy.optimize import fsolve
    from build123d import Edge, Wire, Vector, Vertex, Solid, Compound
    from ..shapes import box

    def local(shapes):
        fs = []
        for s in shapes:
            for f in s.faces():
                bb = f.bounding_box()
                if not (bb.max.X < region[0] or bb.min.X > region[1] or bb.max.Y < region[2] or bb.min.Y > region[3]
                        or bb.max.Z < region[4] or bb.min.Z > region[5]):
                    fs.append(f)
        return Compound(fs).wrapped

    s1, s2 = local(plate_side), local([grip])

    def near(p, shp):
        d = BRepExtrema_DistShapeShape(Vertex(*p).wrapped, shp)
        q = d.PointOnShape2(1)
        return d.Value(), np.array([q.X(), q.Y(), q.Z()])

    def solve(z, g):
        f = lambda v: [near((v[0], v[1], z), s1)[0] - r, near((v[0], v[1], z), s2)[0] - r]
        sol, _, ok, msg = fsolve(f, g, xtol=1e-10, full_output=True)
        res = max(abs(q) for q in f(sol))
        if ok != 1 or res > 1e-6:
            raise RuntimeError("corner round: no ball centre at z %.3f (%s, residual %.2e)" % (z, msg, res))
        return sol

    # stations evenly spaced along the ball path (ds = fine_step): the next z plane comes from the last step's dz / ds
    # (t1, z steps 0.2 then 0.1: radius dips to 0.68 where the spacing changed and 0.49 in the sink)
    st, g, z, dzds = [], np.array([x_guess, y_guess]), z_start, 1.0
    while z > z_min:
        g = solve(z, g)
        c = np.array([g[0], g[1], z])
        u1 = (near(c, s1)[1] - c) / r
        u2 = (near(c, s2)[1] - c) / r
        al = np.degrees(np.arccos(np.clip(u1 @ u2, -1.0, 1.0)))
        if st:
            dzds = max(0.2, abs(z - st[-1][0][2]) / np.linalg.norm(c - st[-1][0]))
        st.append((c, u1 / np.linalg.norm(u1), u2 / np.linalg.norm(u2), al))
        if al < alpha_end and z < fine_z:
            break
        z -= fine_step * dzds
    else:
        raise RuntimeError("corner round: the crease never fell under %.1f deg" % alpha_end)
    s = np.concatenate([[0.0], np.cumsum([np.linalg.norm(b[0] - a[0]) for a, b in zip(st[:-1], st[1:])])])
    objs, info = [], []
    for (c, u1, u2, al), si in zip(st, s):
        t = min(1.0, max(0.0, (si - (s[-1] - sink)) / sink))
        r0, r1 = r * (1.0 + cross), r / np.cos(np.radians(al) / 2.0) * 1.002
        rr = r0 + max(0.0, r1 - r0) * t * t * (3.0 - 2.0 * t)
        bis = (u1 + u2) / np.linalg.norm(u1 + u2)
        v = lambda p: Vector(*[float(q) for q in p])
        pa, pm, pb = c + rr * u1, c + rr * bis, c + rr * u2
        qa, qb = c + (rr + air) * u1, c + (rr + air) * u2
        dd = c + (max(rr, r / np.cos(np.radians(al) / 2.0)) + air) * bis
        edges = [Edge.make_three_point_arc(v(pa), v(pm), v(pb))]
        edges += [Edge.make_line(v(p), v(q)) for p, q in ((pb, qb), (qb, dd), (dd, qa), (qa, pa))]
        objs.append(Wire(edges))
        info.append([round(float(q), 4) for q in (c[2], c[0], c[1], al, rr)])
    web = one_solid(Solid.make_loft(objs, ruled=False), "corner round web")
    return one_solid(web.intersect(box(region[0], region[1], region[2], region[3], region[4], z_top)),
                     "corner round web trimmed"), info
