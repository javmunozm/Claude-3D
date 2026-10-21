"""Carbon slab with a honeycomb of hex holes in the cartridge's open window.

The original slab is imported (keeps its outline and corner fillets) and
pointy-top hexagons are cut through its thickness. Pointy-top hexes on a
triangular lattice give a constant web between every pair of neighbours.
"""
import math

from build123d import Compound, Plane, Pos, RegularPolygon, extrude, import_step

from .constants import SLAB_SRC, SLAB_X, WINDOW_Y, WINDOW_Z
from .parameters import EDGE_MARGIN, HOLE_FLAT, WEB


def hex_centres():
    """Centres (y, z) of every hole that fits wholly inside the window."""
    pitch = HOLE_FLAT + WEB                 # centre-to-centre, neighbours share a flat
    half_w = HOLE_FLAT / 2                  # half width along Y (flats face +-Y)
    half_h = HOLE_FLAT / math.sqrt(3)       # half height along Z (vertex up)
    row_dz = pitch * math.sqrt(3) / 2
    y0, y1 = WINDOW_Y[0] + EDGE_MARGIN + half_w, WINDOW_Y[1] - EDGE_MARGIN - half_w
    z0, z1 = WINDOW_Z[0] + EDGE_MARGIN + half_h, WINDOW_Z[1] - EDGE_MARGIN - half_h

    n_rows = int((z1 - z0) // row_dz) + 1
    z_start = (z0 + z1) / 2 - (n_rows - 1) * row_dz / 2
    cy = (y0 + y1) / 2
    pts = []
    for r in range(n_rows):
        z = z_start + r * row_dz
        off = 0.0 if r % 2 == 0 else pitch / 2
        k = math.floor((cy - off - y0) / pitch)
        y = cy - off - k * pitch
        while y <= y1 + 1e-9:
            if y >= y0 - 1e-9:
                pts.append((y, z))
            y += pitch
    return pts


def hex_prism(y, z, length):
    """Hex prism along X, flats facing +-Y, vertices at +-Z."""
    # Plane.YZ: local x = global Y, local y = global Z, normal +X.
    # rotation=90 puts a vertex on local y (global Z), so the flats face +-Y.
    face = Plane.YZ * RegularPolygon(HOLE_FLAT / 2, 6, major_radius=False, rotation=90)
    return Pos(SLAB_X[0] - 1, y, z) * extrude(face, amount=length)


def build():
    slab = import_step(str(SLAB_SRC)).solids()[0]
    centres = hex_centres()
    t = SLAB_X[1] - SLAB_X[0]
    cutters = Compound([hex_prism(y, z, t + 2) for y, z in centres])
    result = slab - cutters
    return result, centres
