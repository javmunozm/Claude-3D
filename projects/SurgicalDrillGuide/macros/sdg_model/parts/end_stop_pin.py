"""end_stop_pin: removable printed pin through the Z hole near the rack tip."""

from build123d import Pos, Solid


def build_pin(pin):
    """Removable end-stop pin (separate part), in its assembled position."""
    return Pos(pin["x"], pin["y"], pin["z0"]) * Solid.make_cylinder(pin["d"] / 2.0, pin["z1"] - pin["z0"])
