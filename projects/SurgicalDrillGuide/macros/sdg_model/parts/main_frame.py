"""main_frame: C-hook + bar + rack (traced ring), teeth, C-tip bore and pad, threaded boss, end-stop pin hole."""

from shapely.geometry import box as sbox

from build123d import Face, Pos, Solid, Vector, Wire

from ..constants import FUSE_OVERLAP
from ..mechanisms import cam_thread, sawtooth_cutter_face
from ..rings import rack_bottom_y, ring_face
from ..shapes import along_y, cone_y, cyl_y, extrude_z, one_solid, polygon_face, shapely_faces, teardrop_bore_x


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
