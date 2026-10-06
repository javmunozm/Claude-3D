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
