"""Nespresso pod dispenser cage - solid-wall version (no hex perforations).

Rebuilt from `references/nespressoDispenser/nespresso-cage-forward-facing.3mf`,
which is a forward-facing gravity cage: pods stack in a vertical chute and roll
down a rear-to-front ramp to a dispensing mouth at the bottom front.

The reference model's walls are pierced by a dense honeycomb pattern. Every hex
is a separate perimeter the slicer must trace, which is what makes that model
slow to print. This version reproduces the same envelope, wall thicknesses and
ramp with PLAIN SOLID WALLS, so each layer is a handful of long perimeters
instead of hundreds of short ones.

Geometry measured off the reference mesh (all values mm):

  outer envelope      60.2 (X) x 109.2 (Y) x 210.0 (Z)
  wall thickness      2.0   (back, front and both sides)
  ramp thickness      3.0   (perpendicular), inclined ~60.8 deg from horizontal
  front wall          starts at Z = +28.8, runs to the top
  ramp leading edge   reaches Y = -9.6 at Z = -75.0

Origin is the centre of the reference bounding box: X across the width,
+Y toward the BACK, -Y toward the FRONT (the dispensing side), +Z up.
"""

from pathlib import Path

from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Locations,
    Mode,
    Plane,
    Polygon,
    export_step,
    export_stl,
    extrude,
    fillet,
)

# --------------------------------------------------------------------------
# Dimensions (from the reference mesh)
# --------------------------------------------------------------------------

WIDTH = 60.2          # X, outer
DEPTH = 109.2         # Y, outer
HEIGHT = 210.0        # Z, outer

WALL = 2.0            # side / back / front wall thickness
RAMP_T = 3.0          # ramp thickness, measured perpendicular to its face

X_OUT = WIDTH / 2     # 30.1
Y_BACK = DEPTH / 2    # +54.6 (back face)
Y_FRONT = -DEPTH / 2  # -54.6 (front face)
Z_TOP = HEIGHT / 2    # +105.0
Z_BOT = -HEIGHT / 2   # -105.0

X_IN = X_OUT - WALL   # 28.1, inner face of the side walls

# Front wall spans only the upper part; below it is the dispensing mouth.
Z_FRONT_WALL_BOTTOM = 28.785

# Ramp plane, fitted to the reference's inclined section only: the line
# y = RAMP_SLOPE * z + RAMP_Y0 is the ramp's UPPER (pod-bearing) surface.
# It passes through the knee at (Y = -12.0, Z = -45) and reaches the front
# wall (Y = -54.6) at Z = 28.79, i.e. exactly Z_FRONT_WALL_BOTTOM.
RAMP_SLOPE = -0.577253
RAMP_Y0 = -37.9792

# Ramp runs from where it meets the front wall down to its leading edge.
Z_RAMP_TOP = 28.793    # ramp surface reaches Y = -54.6 (the front wall)
Z_RAMP_KNEE = -45.0    # ramp meets the vertical retaining lip here
Z_RAMP_LIP = -75.0     # bottom of the lip, at Y = -9.6

Y_LIP = -9.6           # front face of the vertical retaining lip
Y_LIP_BACK = -12.0     # ramp underside where it joins the lip

FILLET_R = 1.5         # soften the outer vertical corners

# Outer profile of a side wall in the Y-Z plane, lifted directly from the
# reference's X = +30.1 face (its boundary loop is exactly these 8 points).
# Read clockwise from the top back corner:
#   back spine runs full height down to the base, then forward along the
#   bottom to the retaining lip, up the lip, then up the ramp's underside
#   to the bottom of the front wall and back to the top.
SIDE_PROFILE = [
    (Y_BACK, Z_TOP),                    # top back corner
    (Y_BACK, Z_BOT),                    # bottom back corner
    (Y_BACK - 1.6, Z_BOT),              # base foot, front edge
    (Y_LIP, Z_RAMP_LIP),                # bottom of the retaining lip
    (Y_LIP, Z_RAMP_KNEE),               # top of the retaining lip
    (Y_LIP_BACK, Z_RAMP_KNEE),          # ramp underside, lower end
    (Y_FRONT, Z_FRONT_WALL_BOTTOM),     # ramp underside meets the front wall
    (Y_FRONT, Z_TOP),                   # top front corner
]


def ramp_y(z: float) -> float:
    """Y coordinate of the ramp's upper surface at height z."""
    return RAMP_SLOPE * z + RAMP_Y0


def build_dispenser():
    """Return the solid-walled dispenser cage as a single part."""
    with BuildPart() as cage:
        # ---- side walls -------------------------------------------------
        # Profiled slabs on both sides; they carry the whole structure and
        # define the outer silhouette (back spine, base foot, lip, ramp).
        with BuildSketch(Plane.YZ) as side_sk:
            Polygon(*SIDE_PROFILE, align=None)
        extrude(side_sk.sketch, amount=X_OUT, both=True)
        # Hollow out the middle, leaving WALL-thick skins at each side.
        with BuildSketch(Plane.YZ) as core_sk:
            Polygon(*SIDE_PROFILE, align=None)
        extrude(core_sk.sketch, amount=X_IN, both=True, mode=Mode.SUBTRACT)

        # ---- back wall --------------------------------------------------
        # Spans the full height between the side walls.
        with Locations((0, Y_BACK - WALL / 2, 0)):
            Box(WIDTH - 2 * WALL, WALL, HEIGHT)

        # ---- front wall -------------------------------------------------
        # Only above the dispensing mouth.
        front_h = Z_TOP - Z_FRONT_WALL_BOTTOM
        with Locations(
            (0, Y_FRONT + WALL / 2, Z_FRONT_WALL_BOTTOM + front_h / 2)
        ):
            Box(WIDTH - 2 * WALL, WALL, front_h)

        # ---- ramp and retaining lip -------------------------------------
        # The inclined chute floor, plus the short vertical lip at its lower
        # end that stops the leading pod from rolling straight out. Both span
        # the full inner width between the side walls, drawn as one profile
        # in the Y-Z plane and extruded across X.
        #
        # Perpendicular thickness RAMP_T becomes an offset along Y of
        # RAMP_T * sqrt(1 + m^2) for a plane written as y = m*z + c.
        y_off = RAMP_T * (1 + RAMP_SLOPE**2) ** 0.5

        with BuildSketch(Plane.YZ) as ramp_sk:
            Polygon(
                (ramp_y(Z_RAMP_TOP), Z_RAMP_TOP),        # top of ramp face
                (Y_LIP_BACK, Z_RAMP_KNEE),               # knee: ramp -> lip
                (Y_LIP, Z_RAMP_KNEE),                    # top of lip, front
                (Y_LIP, Z_RAMP_LIP),                     # bottom of lip
                (Y_LIP + WALL, Z_RAMP_LIP),              # lip, back face
                (Y_LIP + WALL, Z_RAMP_KNEE),             # top of lip, back
                (Y_LIP_BACK + y_off, Z_RAMP_KNEE),       # knee, underside
                (ramp_y(Z_RAMP_TOP) + y_off, Z_RAMP_TOP),  # top, underside
                align=None,
            )
        extrude(ramp_sk.sketch, amount=X_IN, both=True)

        # ---- soften the four outer vertical corners ----------------------
        verticals = (
            cage.edges()
            .filter_by(Axis.Z)
            .filter_by(lambda e: abs(abs(e.center().X) - X_OUT) < 1e-6)
        )
        if verticals:
            fillet(verticals, FILLET_R)

    return cage.part


def main() -> None:
    part = build_dispenser()

    out_dir = Path(__file__).resolve().parent.parent
    step_path = out_dir / "NespressoPodDispenser.step"
    stl_path = out_dir / "NespressoPodDispenser.stl"

    export_step(part, str(step_path))
    export_stl(part, str(stl_path))

    bb = part.bounding_box()
    print(f"volume : {part.volume / 1000:.1f} cm^3")
    print(
        "bbox   : "
        f"{bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm"
    )
    print(f"wrote  : {step_path}")
    print(f"wrote  : {stl_path}")


if __name__ == "__main__":
    main()
