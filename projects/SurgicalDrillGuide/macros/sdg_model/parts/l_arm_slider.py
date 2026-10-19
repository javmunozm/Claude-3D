"""l_arm_slider: rectified L + collar + carriage wrapping the rack, lower block with the shoe pocket, the +Z
assembly window, the jam bore and the screw hole (r8 rigid pawl), wire bore."""

from ..constants import CARRIAGE_FLOOR, CARRIAGE_TOP_WALL, FUSE_OVERLAP, L_ARM_FULL_WRAP_Z, SLIDE_CLEAR
from ..rings import ring_face
from ..shapes import box, cyl_y, extrude_z, one_solid, teardrop_bore_x, teardrop_bore_y


def build_l_arm_slider(D, t_z, wall_z, chan, bore, shoe):
    """Rectified L (Z 0..t_z) + collar + carriage (wrapping the rack) + lower block (shoe pocket, window, jam bore,
    screw hole) + wire bore. `shoe` is the derive_shoe bundle (MIN pose)."""
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
    y_in = D["carriage_bottom_max"] + 1.0
    # Carriage top wall raised to chan_y1 + CARRIAGE_TOP_WALL over the whole carriage, square +X end corner; starts
    # 1.0 below the traced top (overlap) and inside the collar at its -X end. Floor CARRIAGE_FLOOR under the channel
    # (top 1.0 inside the traced wall), square +X end over the full height.
    carriage = carriage_traced + box(D["carriage_x0"], x_end + 0.5, D["carriage_y1"] - 1.0, y_top, z0, z1)
    floor = box(D["carriage_x0"] - FUSE_OVERLAP, x_end + 0.5, y_fl, y_in, z0, z1)
    end_fill = box(x_end - 1.0, x_end + 0.5, y_fl, y_top, z0, z1)
    # r8 lower block: full slab Z, from the floor (overlap 1.0 into it) down to the block floor underside.
    bk = shoe["block"]
    block = box(bk["x0"], bk["x1"], bk["y0"], y_fl + 1.0, z0, z1)
    carriage = carriage + floor + end_fill + block
    carriage = carriage - box(x_end, x_end + 5.0, bk["y0"] - 5.0, y_top + 5.0, z0 - 1.0, z1 + 1.0)
    # Collar/carriage junction: the traced rings overlap by only 0.03-0.6 mm; this slug lies inside
    # collar ∪ carriage (collar right face is bridged/hidden there) and makes the overlap a real volume.
    cx = D["carriage_x0"]
    junction = box(cx - FUSE_OVERLAP, cx + FUSE_OVERLAP, D["carriage_y0"] + 0.2, D["carriage_y1"] - 0.2, z0, z1)
    slider = one_solid(body + riser_slug + collar + carriage + junction, "slider fuse")

    # Rack channel (through collar and carriage).
    slider = one_solid(slider - box(D["collar_x0"] - 2.0, D["carriage_x1"] + 2.0, chan["y0"], chan["y1"],
                                    -SLIDE_CLEAR, t_z + SLIDE_CLEAR), "slider - channel")
    # Shoe pocket: the channel's Z, from the insertion level up into the channel (removes the floor over it).
    pk = shoe["pocket"]
    slider = one_solid(slider - box(pk["x0"], pk["x1"], pk["y0"], chan["y0"] + 0.5, pk["z0"], pk["z1"]),
                       "slider - shoe pocket")
    # +Z assembly window (user decision r8): through the +Z side wall over the pocket X, from the insertion level to
    # WINDOW_TOP_BELOW_CHANNEL under the channel floor.
    wn = shoe["window"]
    slider = one_solid(slider - box(wn["x0"], wn["x1"], wn["y0"], wn["y1"], pk["z1"] - 0.5, z1 + 1.0),
                       "slider - assembly window")
    # Jam bore (washer + turning jam nut) on the screw axis, open to the +Z face; screw hole through the block floor.
    sc, jm = shoe["screw"], shoe["jam"]
    r = jm["bore_d"] / 2.0
    jam = cyl_y(sc["x"], jm["bore_y0"], jm["bore_y1"], r, sc["z"])
    jam_open = box(sc["x"] - r, sc["x"] + r, jm["bore_y0"], jm["bore_y1"], sc["z"], z1 + 1.0)
    slider = one_solid(slider - jam - jam_open, "slider - jam bore")
    slider = one_solid(slider - teardrop_bore_y(sc["x"], bk["y0"] - 1.0, jm["bore_y0"] + 0.5, sc["z"], sc["hole_d"],
                                                bore["apex_dir"]), "slider - screw hole")

    # Wire bore along the full top bar: enters the riser outer face, exits the crown.
    slider = one_solid(slider - teardrop_bore_x(D["wire_x0"] - bore["overrun"], D["wire_x1"] + bore["overrun"],
                                                D["wire_y"], t_z / 2.0, bore["d"], bore["apex_dir"]),
                       "slider - wire bore")
    return slider
