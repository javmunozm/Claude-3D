"""l_arm_slider: rectified L + collar + carriage wrapping the rack, compliant pawl, tab stop, wire bore."""

from ..constants import (CARRIAGE_FLOOR, CARRIAGE_TOP_WALL, FUSE_OVERLAP, L_ARM_FULL_WRAP_Z, SLIDE_CLEAR,
                       TOOTH_DEPTH, TOOTH_LAND, TOOTH_PITCH)
from ..mechanisms import pawl_tooth_pts
from ..rings import rack_bottom_y, ring_face, vertical_chord
from ..shapes import box, extrude_z, one_solid, polygon_face, teardrop_bore_x


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
