"""Replacement base wedge for a NespressoPodDispenser print that failed part-way.

The original print was run inverted (tower on the bed, base wedge printed last)
and the extruder ground the filament after 22.2 mm, so the piece in hand is the
upper ~187.8 mm - it has the ramp, lip and dispensing mouth - and what is
missing is the BOTTOM wedge:

    Z = -105.0 (bed) up to Z = -82.8   (22.2 mm tall)

That region is not a solid block. Sampling the exported STL across the cut
plane shows it is a U-channel:

    back wall     Y = 52.8 .. 54.6, full 60.2 mm width, constant over the height
    side walls    |X| = 28.1 .. 30.1, each a triangle whose front edge follows
                  the sloped underside and shrinks to nothing at the bed

The joint is a SOCKET: the foot is built up past the cut plane as a U-shaped
trench, and the printed part's wall bottom slides down into it. The trench has
a wall on each side of the band, so the printed part is gripped on both its
inner and its outer face.

This is why the socket works where a tongue does not. A tongue has to fit
INSIDE the 2 mm wall band, competing for the same material as the foot's own
wall, and ends up hanging over the open dispensing mouth with nothing beneath
it. The socket instead sits OUTBOARD and INBOARD of that band - both of which
are free space - so it needs no room within the wall at all, and nothing has
to be cut away from the printed part.

Sampling the parent mesh shows the receiving bands are dead constant over the
whole joint height, which is what makes a straight slide-in fit possible:

    back wall     Y = 52.60 .. 54.55
    side walls    |X| = 28.15 .. 30.05

Print this the right way up (bed at Z = -105, wedge growing upward). In that
orientation the sloped underside becomes the top surface and needs no support.
"""

from pathlib import Path

from build123d import (
    Axis,
    BuildPart,
    BuildSketch,
    Mode,
    Plane,
    Polygon,
    chamfer,
    export_step,
    export_stl,
    extrude,
    fillet,
)

# --------------------------------------------------------------------------
# Geometry inherited from the parent model (nespresso_dispenser.py)
# --------------------------------------------------------------------------

WIDTH = 60.2
DEPTH = 109.2

WALL = 2.0

X_OUT = WIDTH / 2      # 30.1
Y_BACK = DEPTH / 2     # +54.6
Y_LIP = -9.6
X_IN = X_OUT - WALL    # 28.1

Z_BOT = -105.0         # bed
Z_RAMP_LIP = -75.0     # where the sloped underside meets the lip

# Foot: the side profile's bottom edge runs from the back face inward.
Y_FOOT = Y_BACK - 1.6  # 53.0

# --------------------------------------------------------------------------
# Repair parameters
# --------------------------------------------------------------------------

Z_CUT = -82.8          # top of the missing piece = 22.2 mm of printed height

SOCKET_H = 8.0         # how far the socket walls rise above the cut plane,
                       # i.e. how deep the printed part sits into the foot
SOCKET_JAW = 1.2       # thickness of each jaw (inner and outer) of the trench
COLLAR_OVERLAP = 1.0   # how far the collar reaches down into the wedge
FIT_CLEAR = 0.20       # per-face gap: trench is this much wider than the wall

# Receiving bands measured off the parent mesh - the material that slides into
# the trench. Constant over the whole joint height (verified every 1 mm).
P_BACK_IN = 52.60      # back wall, inner face
P_BACK_OUT = 54.55     # back wall, outer face
P_SIDE_IN = 28.15      # side wall, inner face
P_SIDE_OUT = 30.05     # side wall, outer face

LEAD_IN = 0.4          # chamfer at the jaw tips to guide the part in.
                       # Must stay well under SOCKET_JAW/2 - a chamfer near
                       # half the jaw thickness has no material to cut into
                       # and the kernel refuses it.

FILLET_R = 1.5         # matches the parent part's outer vertical corners


def underside_y(z: float) -> float:
    """Y of the sloped underside at height z (the wedge's front edge).

    Straight line from the foot at the bed up to the bottom of the lip.
    """
    t = (z - Z_BOT) / (Z_RAMP_LIP - Z_BOT)
    return Y_FOOT + t * (Y_LIP - Y_FOOT)


def build_repair():
    """Return the replacement base wedge, tongue included."""
    y_front_cut = underside_y(Z_CUT)  # ~6.68

    with BuildPart() as part:
        # ---- side walls -------------------------------------------------
        # Profile in the Y-Z plane: back face, down to the bed, forward along
        # the foot, then back up the sloped underside to the cut plane.
        side_profile = [
            (Y_BACK, Z_CUT),
            (Y_BACK, Z_BOT),
            (Y_FOOT, Z_BOT),
            (y_front_cut, Z_CUT),
        ]
        with BuildSketch(Plane.YZ) as side_sk:
            Polygon(*side_profile, align=None)
        extrude(side_sk.sketch, amount=X_OUT, both=True)

        with BuildSketch(Plane.YZ) as core_sk:
            Polygon(*side_profile, align=None)
        extrude(core_sk.sketch, amount=X_IN, both=True, mode=Mode.SUBTRACT)

        # ---- back wall --------------------------------------------------
        # Spans between the side walls for the full height of the wedge.
        with BuildSketch(Plane.YZ) as back_sk:
            Polygon(
                (Y_BACK, Z_CUT),
                (Y_BACK, Z_BOT),
                (Y_BACK - WALL, Z_BOT),
                (Y_BACK - WALL, Z_CUT),
                align=None,
            )
        extrude(back_sk.sketch, amount=X_IN, both=True)

        # ---- socket -------------------------------------------------------
        # A U-shaped trench rising above the cut plane. The printed part's
        # wall bottom slides straight down into it and is gripped on both
        # faces. Nothing has to be removed from the printed part.
        #
        # Built as a solid collar (outer jaw face -> inner jaw face) with the
        # trench then cut out of it, so the jaws and the wedge below fuse
        # into one body rather than meeting at coincident faces.
        z1 = Z_CUT + SOCKET_H

        # trench: the receiving band, opened up by FIT_CLEAR on every face
        t_back_in = P_BACK_IN - FIT_CLEAR
        t_back_out = P_BACK_OUT + FIT_CLEAR
        t_side_in = P_SIDE_IN - FIT_CLEAR
        t_side_out = P_SIDE_OUT + FIT_CLEAR

        # Collar: the trench plus a jaw on each side of it.
        #
        # The outer jaw necessarily stands PROUD of the original envelope -
        # the trench's outer face is already at the part's outer surface, so
        # there is nowhere inboard for it to go. It reads as a thin band
        # around the base, 1.2 mm deep and SOCKET_H tall. Clamping it to the
        # envelope instead just deletes it, leaving a one-sided socket that
        # cannot grip.
        c_back_in = t_back_in - SOCKET_JAW
        c_back_out = t_back_out + SOCKET_JAW
        c_side_in = t_side_in - SOCKET_JAW
        c_side_out = t_side_out + SOCKET_JAW

        # The collar starts slightly BELOW the cut plane so it overlaps the
        # wedge rather than merely abutting it. Meeting on a coincident face
        # leaves the two as separate bodies (body_count 2); a real overlap
        # gives the fuse something to resolve.
        z_collar = Z_CUT - COLLAR_OVERLAP
        with BuildSketch(Plane.XY.offset(z_collar)) as collar_sk:
            Polygon(
                (-c_side_out, c_back_out),
                (c_side_out, c_back_out),
                (c_side_out, y_front_cut),
                (c_side_in, y_front_cut),
                (c_side_in, c_back_in),
                (-c_side_in, c_back_in),
                (-c_side_in, y_front_cut),
                (-c_side_out, y_front_cut),
                align=None,
            )
        extrude(collar_sk.sketch, amount=SOCKET_H + COLLAR_OVERLAP)

        # Cut the trench out of the collar, leaving the two jaws.
        with BuildSketch(Plane.XY.offset(Z_CUT)) as trench_sk:
            Polygon(
                (-t_side_out, t_back_out),
                (t_side_out, t_back_out),
                (t_side_out, y_front_cut),
                (t_side_in, y_front_cut),
                (t_side_in, t_back_in),
                (-t_side_in, t_back_in),
                (-t_side_in, y_front_cut),
                (-t_side_out, y_front_cut),
                align=None,
            )
        extrude(trench_sk.sketch, amount=SOCKET_H, mode=Mode.SUBTRACT)

        # ---- finishing ---------------------------------------------------
        # Lead-in chamfer around the mouth of the trench, so the printed part
        # self-centres as it goes in instead of catching on a square lip.
        mouth = (
            part.edges()
            .group_by(Axis.Z)[-1]
            .filter_by(lambda e: e.length > 2.0)
        )
        if mouth:
            chamfer(mouth, LEAD_IN)

        # Soften the wedge's outer vertical corners to match the parent part.
        # Restricted to edges below the cut plane: the socket jaws above it
        # are thin and a 1.5 mm fillet there would eat most of a jaw.
        verticals = (
            part.edges()
            .filter_by(Axis.Z)
            .filter_by(lambda e: abs(abs(e.center().X) - X_OUT) < 1e-6)
            .filter_by(lambda e: e.center().Z < Z_CUT)
        )
        if verticals:
            fillet(verticals, FILLET_R)

    return part.part


def main() -> None:
    part = build_repair()

    out_dir = Path(__file__).resolve().parent.parent
    step_path = out_dir / "NespressoPodDispenser_BaseRepair.step"
    stl_path = out_dir / "NespressoPodDispenser_BaseRepair.stl"

    export_step(part, str(step_path))
    export_stl(part, str(stl_path))

    bb = part.bounding_box()
    print(f"volume : {part.volume / 1000:.2f} cm^3")
    print(
        "bbox   : "
        f"{bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm"
    )
    print(f"Z span : {bb.min.Z:.2f} .. {bb.max.Z:.2f}")
    print(f"wrote  : {step_path}")
    print(f"wrote  : {stl_path}")


if __name__ == "__main__":
    main()
