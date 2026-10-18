"""SurgicalDrillGuide stage 2: traced-ring import (build time) and values DERIVED from the rings."""

import math

import ezdxf
from shapely.geometry import LineString, Polygon

from build123d import Face, Wire, import_dxf

from .constants import IMPORT_DIR, RACK_EXT, RACK_FLAT_X1, RING_FILES, SLIDE_CLEAR_Y


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


def horizontal_chord(poly, y):
    g = poly.intersection(LineString([(-500, y), (500, y)]))
    if g.is_empty:
        return None
    xs = [c[0] for geom in getattr(g, "geoms", [g]) for c in geom.coords]
    return min(xs), max(xs)


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


def rack_line_y(D, x):
    """The traced rack bottom line (tooth-tip envelope of the photographed rack)."""
    bx0, by0, bx1, by1 = D["rack_bottom_line"]
    return by0 + (x - bx0) * (by1 - by0) / (bx1 - bx0)


def rack_flat_y(D):
    """r7: the flat underside level = the traced line's Y at RACK_FLAT_X1."""
    return rack_line_y(D, RACK_FLAT_X1)


def rack_bottom_y(D, x):
    """r7: rack underside, flat at rack_flat_y for x <= RACK_FLAT_X1, the traced line beyond."""
    return rack_flat_y(D) if x <= RACK_FLAT_X1 else rack_line_y(D, x)


def rack_flat_poly(D, x_end):
    """r7: wedge between the flat underside and the traced line, from the tip-chamfer end (45° run down to the flat,
    so the chamfer is kept) to x_end, grown 0.5 up into the rack (overlap). x_end must lie inside a notch so the
    sub-micron step left there is cut away with the teeth."""
    # Full build r7: the wedge starts 0.3 inside the traced bottom run (not at the chamfer end, where the moved tip
    # and the extension band already meet with a micro-step: a vertex there tessellated to a zero-length edge and
    # an open STL). Its 45° edge starts 0.05 inside the rack, so it crosses the traced line cleanly.
    bx0 = D["rack_bottom_line"][0]
    xs = bx0 - RACK_EXT + 0.3
    ys = vertical_chord(D["frame_poly"], xs)[0] + 0.05
    yf = rack_flat_y(D)
    return Polygon([(xs, ys + 0.45), (xs, ys), (xs + (ys - yf), yf), (x_end, yf),
                    (x_end, rack_line_y(D, x_end) + 0.5)])


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
