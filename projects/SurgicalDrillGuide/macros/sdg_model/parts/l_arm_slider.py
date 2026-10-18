"""l_arm_slider: rectified L + collar + carriage wrapping the rack, compliant pawl, tab stop, wire bore."""

from build123d import Pos, Solid
from shapely.geometry import Point, Polygon
from shapely.geometry import box as sbox
from shapely.ops import nearest_points

from ..constants import (CARRIAGE_FLOOR, CARRIAGE_TOP_WALL, COUPLING_CARRIAGE_CLEAR, FUSE_OVERLAP, L_ARM_FULL_WRAP_Z, SLIDE_CLEAR,
                       TOOTH_DEPTH, TOOTH_LAND, TOOTH_PITCH)
from ..mechanisms import pawl_tooth_pts, tooth_face_x
from ..rings import rack_bottom_y, ring_face, ring_points
from ..shapes import box, extrude_z, one_solid, polygon_face, shapely_faces, teardrop_bore_x


def root_fillet(y_fb, r):
    """r7 fix D1 (shared with the gates): circle of radius r tangent to the flexure underside y_fb (from below) and to
    the traced collar wall. Returns the centre, the wall contact point and the X where the arc meets the underside."""
    col = Polygon(ring_points("collar"))
    cy = y_fb - r
    lo = col.intersection(sbox(-1e3, cy - 1e-3, 1e3, cy + 1e-3)).bounds[2]   # wall X at the centre height
    hi = lo + 3.0 * r
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if Point(mid, cy).distance(col.exterior) < r else (lo, mid)
    cx = 0.5 * (lo + hi)
    t2 = nearest_points(col.exterior, Point(cx, cy))[0]
    return {"cx": cx, "cy": cy, "wall": (t2.x, t2.y), "x_end": cx, "collar": col}


def pawl_layout(D, chan, pawl, a_seats):
    """r7 pawl layout in the MIN pose (shared by the builder and the gates): tooth polygons (inner first), inner
    tooth face X at the tongue top, block start, flexure underside, block bottom, pad and stop heights."""
    y0, st = chan["y0"], pawl["stop"]
    teeth = [pawl_tooth_pts(a, rack_bottom_y(D, a), TOOTH_PITCH, TOOTH_DEPTH, TOOTH_LAND, pawl["seat_clear"],
                            y0 - 0.5, pawl["hook"])[0] for a in a_seats]
    x_in = tooth_face_x(teeth[0], y0)
    xb = x_in - pawl["block_gap"]
    pad_bot = pawl["tab_bottom_y"] - pawl["pad_t"] + 0.5
    y_fb = y0 - pawl["flex_t"]
    rf = root_fillet(y_fb, pawl["root_r"])
    leg_x0 = D["carriage_end_x"] - st["leg_x0_in"]
    top_end = pawl["anchor_x"] + pawl["root_top_r"]          # top-side root fillet end (outer Z bands)
    return {"teeth": teeth, "x_in": x_in, "xb": xb, "free_len": xb - rf["x_end"], "y_fb": y_fb, "root": rf,
            "root_top_end": top_end, "free_len_outer": xb - max(top_end, rf["x_end"]),
            "leg_x0": leg_x0, "leg_x1": leg_x0 + st["leg_w"],
            "pad_x0": x_in - st["block_w"],
            "y_blk": y0 - pawl["block_depth"], "pad_bot": pad_bot, "pad_top": pawl["tab_bottom_y"] + 0.5,
            "inner_x": x_in, "outer_x": st["outer_x"], "inner_top": pad_bot - st["drop"],
            "outer_top": pad_bot - st["outer_gap"], "beam_top": pad_bot - st["outer_gap"] - st["outer_h"]}


def build_l_arm_slider(D, t_z, wall_z, chan, bore, pawl, a_seats):
    """Rectified L (Z 0..t_z) + collar + carriage (wrapping the rack) + compliant pawl + wire bore.
    a_seats: the notches the pawl teeth sit in at MIN (seat_notch), inner first."""
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
    L = pawl_layout(D, chan, pawl, a_seats)
    y_fb = L["y_fb"]                                   # r7: flexure underside; the 45° root bevel starts here
    if not (y_fl < y_fb < y_in):
        raise RuntimeError(f"flexure underside Y {y_fb:.3f} outside the floor band {y_fl:.3f}..{y_in:.3f}")
    left = polygon_face([(D["carriage_x0"] - FUSE_OVERLAP, y_in), (px0, y_in), (px0, y_fb),
                         (px0 - (y_fb - y_fl), y_fl), (D["carriage_x0"] - FUSE_OVERLAP, y_fl)])
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
    # r7 root bevel: 45° from the flexure underside at the anchor down-left to the floor bottom (cuts the traced
    # carriage bottom and the collar corner above the floor bottom, so the root has no square re-entrant corner).
    bevel = polygon_face([(px0, y_fb), (px0 + 1.0, y_fb), (px0 + 1.0, y_fl), (px0 - (y_fb - y_fl), y_fl)])
    slider = one_solid(slider - extrude_z(bevel, z0 - 1.0, z1 + 1.0), "slider - flexure root bevel")
    # r7 pawl: uniform flexure (thickness flex_t) from the anchor into a rigid tooth block, PAWL_TEETH teeth on
    # the block, tab from the block's free end down to the pad, pad from the block start to PAD_X1.
    xb, y0 = L["xb"], chan["y0"]
    flex = box(px0 - FUSE_OVERLAP, xb + FUSE_OVERLAP, y_fb, y0, z0, z1)
    block = box(xb, pxf, L["y_blk"], y0, z0, z1)
    teeth = [extrude_z(polygon_face(p), z0, z1) for p in L["teeth"]]
    tab = box(pxf - pawl["tab_w"], pxf, pawl["tab_bottom_y"], L["y_blk"] + 0.8, z0, z1)
    pad = box(L["pad_x0"], pawl["pad_x1"], L["pad_bot"], pawl["tab_bottom_y"] + 0.5, z0, z1)
    pawl_body = flex + block + tab + pad
    for t_ in teeth:
        pawl_body = pawl_body + t_
    slider = one_solid(slider + pawl_body, "slider + pawl")
    # r7 fix D1: the bevel left a sharp V where it cut into the collar. Put the collar back (its traced outline,
    # overlapping the floor and flexure) and fill the flexure-collar corner down to one root_r fillet. Material is
    # only added below the flexure, between the collar wall and the arc.
    rf = L["root"]
    wx, wy = rf["wall"]
    restore = rf["collar"].intersection(sbox(wx - 1.0, y_fl - 0.3, px0 + 1.0, y_fb + 0.3))
    corner = box(wx - 1.0, rf["cx"], wy, y_fb + 0.5, z0, z1) - \
        Pos(rf["cx"], rf["cy"], z0 - 1.0) * Solid.make_cylinder(pawl["root_r"], z1 - z0 + 2.0)
    fill = corner
    for f_ in shapely_faces(restore):
        fill = fill + extrude_z(f_, z0, z1)
    slider = one_solid(slider + fill, "slider + flexure root fillet")
    # r7 reinforce: in the outer Z bands the side walls stop at the anchor X with a square step on the flexure's
    # top (tension) side. Fillet it at root_top_r; built over the full Z, then the channel is cut back out of it.
    r2 = pawl["root_top_r"]
    top = box(px0 - 0.5, px0 + r2, y0 - 0.3, y0 + r2, z0, z1) - \
        Pos(px0 + r2, y0 + r2, z0 - 1.0) * Solid.make_cylinder(r2, z1 - z0 + 2.0)
    slider = one_solid(slider + top, "slider + flexure root top fillet")
    slider = one_solid(slider - box(px0 - 1.0, px0 + r2 + 0.5, y0, y0 + r2 + 0.5, -SLIDE_CLEAR, t_z + SLIDE_CLEAR),
                       "slider - channel at the root top fillet")

    # r7 two-point tab stop: leg from the carriage floor down past the pad's +X end, a beam under the pad, an inner
    # stop block (contact = its +X top edge at the inner tooth face X, gap TAB_STOP_DROP) and an outer one (contact
    # at STOP_OUTER_X, gap STOP_OUTER_GAP).
    st = pawl["stop"]
    # r7 reinforce: the leg's -X face stays leg_x0_in inside the squared carriage end; below the floor underside the
    # leg is leg_w wide and its +X face passes the end. Above the floor underside the end is trimmed at
    # carriage_end_x in one cut (a single plane from the floor underside to the top wall).
    leg_x0, leg_x1 = L["leg_x0"], L["leg_x1"]
    if leg_x0 < pawl["pad_x1"] + 0.5:
        raise RuntimeError(f"stop leg X {leg_x0:.3f} is within 0.5 of the pad end {pawl['pad_x1']:.3f}")
    if leg_x1 >= x_end + COUPLING_CARRIAGE_CLEAR:
        raise RuntimeError(f"stop leg +X face {leg_x1:.3f} reaches the coupling line {x_end + COUPLING_CARRIAGE_CLEAR:.3f}")
    beam_top = L["beam_top"]
    beam_bot = beam_top - st["beam_t"]
    w = st["block_w"]
    leg = box(leg_x0, leg_x1, beam_bot, D["carriage_y0"] + 1.0, z0, z1)
    # Fillet where the leg's -X face meets the floor underside (the leg-bending tension side).
    rt = st["leg_top_r"]
    if leg_x0 - rt < pxf + pawl["slot_w"] + 0.5:
        raise RuntimeError(f"leg top fillet starts at X {leg_x0 - rt:.3f}, within 0.5 of the free-end slot")
    leg_fil = box(leg_x0 - rt, leg_x0 + 0.5, y_fl - rt, y_fl + 0.5, z0, z1) - \
        Pos(leg_x0 - rt, y_fl - rt, z0 - 1.0) * Solid.make_cylinder(rt, z1 - z0 + 2.0)
    beam = box(L["inner_x"] - w - 0.5, leg_x0 + FUSE_OVERLAP, beam_bot, beam_top, z0, z1)
    inner = box(L["inner_x"] - w, L["inner_x"], beam_top - FUSE_OVERLAP, L["inner_top"], z0, z1)
    outer = box(L["outer_x"] - w, L["outer_x"], beam_top - FUSE_OVERLAP, L["outer_top"], z0, z1)
    # r7 fix 1h: fillet in the beam-leg inside corner (beam top meets the leg's -X face).
    rr = st["fillet_r"]
    if leg_x0 - rr < L["outer_x"] + 0.5:
        raise RuntimeError(f"beam-leg fillet starts at X {leg_x0 - rr:.3f}, within 0.5 of the outer stop {L['outer_x']}")
    fil = box(leg_x0 - rr, leg_x0 + FUSE_OVERLAP, beam_top - FUSE_OVERLAP, beam_top + rr, z0, z1) - \
        Pos(leg_x0 - rr, beam_top + rr, z0 - 1.0) * Solid.make_cylinder(rr, z1 - z0 + 2.0)
    slider = one_solid(slider + leg + beam + inner + outer + fil + leg_fil, "slider + tab stops")
    slider = one_solid(slider - box(x_end, x_end + 5.0, y_fl, y_top + 5.0, z0 - 1.0, z1 + 1.0),
                       "slider - end trim above the floor underside")

    # Wire bore along the full top bar: enters the riser outer face, exits the crown.
    slider = one_solid(slider - teardrop_bore_x(D["wire_x0"] - bore["overrun"], D["wire_x1"] + bore["overrun"],
                                                D["wire_y"], t_z / 2.0, bore["d"], bore["apex_dir"]),
                       "slider - wire bore")
    return slider
