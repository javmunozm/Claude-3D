"""Stage 3: the 3-way 90-degree corner connector.

Frame: arm axes along +X, +Y, +Z, meeting at the origin. The back corner is a sphere of the arm radius, so the part
spans -r_out .. reach on every axis (= overall). Each arm is revolved from one profile (outer tube with tip chamfer);
each bore is a revolved blind cut (entry cone, flat floor at x = r_out, so the three bores never meet).
"""

from build123d import Axis, Plane, Polygon, Polyline, Rot, Sphere, extrude, make_face, revolve


def _arm_z(r_out, reach, chamfer):
    """Solid arm along +Z from z = 0 (the sphere's equator) to the tip, outer tip edge chamfered.
    Starting below 0 would leave a full-radius lip outside the sphere."""
    pts = [(0, 0.0), (r_out, 0.0), (r_out, reach - chamfer), (r_out - chamfer, reach), (0, reach)]
    face = make_face(Polyline(*pts, close=True))
    return revolve(Plane.XZ * face, Axis.Z)


def _bore_z(bore_r, depth, reach, chamfer):
    """Blind bore cutter along +Z: flat floor at reach - depth, entry cone, 1 mm past the tip."""
    z0 = reach - depth
    pts = [(0, z0), (bore_r, z0), (bore_r, reach - chamfer), (bore_r + chamfer, reach),
           (bore_r + chamfer, reach + 1.0), (0, reach + 1.0)]
    face = make_face(Polyline(*pts, close=True))
    return revolve(Plane.XZ * face, Axis.Z)


def _gusset(plane, tip, w, t):
    """Plate in `plane` running along both arms (its local x and y) to `tip`, standing `w` above each arm axis
    at the tip, outer corner cut on the diagonal (tip, w)-(w, tip). t thick, centred on the plane."""
    plate = Polygon((0, 0), (tip, 0), (tip, w), (w, tip), (0, tip), align=None)
    return extrude(plane * plate, amount=t / 2, both=True)


# Z -> X is a +90 deg rotation about Y; Z -> Y is a -90 deg rotation about X.
_TO_AXIS = {"z": Rot(0, 0, 0), "x": Rot(0, 90, 0), "y": Rot(-90, 0, 0)}


def build_connector(bore_d, r_out, reach, socket, gusset_t, gusset_tip, gusset_w, end_chamfer, bore_chamfer, **_):
    arm = _arm_z(r_out, reach, end_chamfer)
    bore = _bore_z(bore_d / 2, socket, reach, bore_chamfer)

    # Sphere axis along (1, 1, -1): both poles land inside the X and Z arms (6.65 from their axes for r 8.15),
    # clear of bores and gussets. With the default Z axis the -Z pole sat exposed on the back corner and tessellated
    # into a degenerate triangle (open + non-manifold edge, build 1, 2026-11-15).
    body = Plane(origin=(0, 0, 0), z_dir=(1, 1, -1)) * Sphere(r_out)
    for k in ("x", "y", "z"):
        body = body + _TO_AXIS[k] * arm
    for pl in (Plane.XY, Plane.YZ, Plane.ZX):
        body = body + _gusset(pl, gusset_tip, gusset_w, gusset_t)
    for k in ("x", "y", "z"):
        body = body - _TO_AXIS[k] * bore
    return body
