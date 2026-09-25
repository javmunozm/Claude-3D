"""Extension de capacidad para el dispensador de capsulas Nespresso.

DOS piezas independientes de 150 mm cada una, que se acoplan entre si:

  PIEZA A - "base": la que SE INSERTA en la base del dispensador.
      Su exterior esta atado a la boca del holder (40 x 37.5 internos,
      con calibre), asi que no se puede ensanchar. Para que el reborde
      de la capsula pase, las dos caras de 39.5 bajan a 0.6 (1 pasada).
      Su corte de inspeccion SALE por el borde superior: no queda barra
      cruzando arriba.

  PIEZA B - "acople": la que SE ACOPLA encima.
      No entra en ningun hueco, asi que es libre por fuera: pared 1.8 en
      las cuatro caras. Lleva en su extremo inferior un ZOCALO LOCAL que
      recibe el extremo de A, y solo ahi se ensancha.

El corte de inspeccion va en una cara de 37 y termina en ARCO, no en
esquina viva: se imprime sin soportes, porque un borde superior recto
seria un puente y un semicirculo se autosoporta.

Las capsulas bajan DE LADO (acostadas), no de plano.

Capsula Nespresso Original, de su ficha tecnica
(`sources/nespressoDispenserExtension/capsuleDimensions.webp`):

  reborde   Q37 +0.1/-0.2   -> peor caso 37.10  <- manda para el deslizamiento
  cuerpo    Q29.4 +-0.25
  alto      27.2 +-0.35     -> peor caso 27.55

Origen de cada pieza: centro de la seccion en planta, Z = 0 en su base.
"""

import math
from pathlib import Path

from build123d import (
    Align,
    Axis,
    Box,
    BuildLine,
    add,
    BuildPart,
    BuildSketch,
    Cylinder,
    fillet,
    Line,
    Locations,
    Mode,
    Plane,
    export_step,
    export_stl,
    extrude,
    make_face,
)

# --------------------------------------------------------------------------
# Capsula (ficha tecnica, peor caso)
# --------------------------------------------------------------------------

CAPSULE_RIM = 37.10       # reborde: manda en el eje X
CAPSULE_HEIGHT = 27.55    # alto: manda en el eje Y

# --------------------------------------------------------------------------
# Comun
# --------------------------------------------------------------------------

HEIGHT = 150.0            # alto de cada pieza
NOZZLE = 0.6
FIT_HOLDER = 0.25         # holgura por cara: A dentro del holder
FIT_SOCKET = 0.15         # holgura por cara: A dentro del zocalo de B

WINDOW_W = 20.0           # corte de inspeccion: ancho
WINDOW_R = WINDOW_W / 2   # radio del arco en los extremos
STEP_FILLET = 1.3         # fillet on step transitions (slim -> wide)
EDGE_FILLET = 1.0         # fillet on outer vertical edges (body section)

# --------------------------------------------------------------------------
# PIEZA A - la que se inserta en la base
# --------------------------------------------------------------------------

HOLDER_X = 40.0           # boca del holder, interna, con calibre
HOLDER_Y = 37.5

A_OUTER_X = HOLDER_X - 2 * FIT_HOLDER     # 39.50
A_OUTER_Y = HOLDER_Y - 2 * FIT_HOLDER     # 37.00

# Las caras de 39.5 (perpendiculares a Y) fijan el interior en X. Con 1.8 el
# interior daria 35.90 y el reborde de 37.10 no pasaria.
#
# A 1.2 (2 x 0.6) el interior queda en 37.10, que es EXACTAMENTE el reborde en
# su peor caso: margen +0.00. Contra una capsula nominal (Q37.00) quedan
# +0.10, y contra el minimo de la ficha (Q36.80), +0.30. Decision del usuario,
# tomada sabiendo que no hay holgura en el peor caso; el FDM suele cerrar el
# interior 0.1-0.2 mm, asi que conviene comprobarlo en un cupon antes de
# imprimir los 150 mm completos.
A_WALL_Y = 2 * NOZZLE              # 1.2, caras de 39.5
A_WALL_X = 3 * NOZZLE              # 1.8, caras de 37.0

A_INNER_X = A_OUTER_X - 2 * A_WALL_Y   # 38.30
A_INNER_Y = A_OUTER_Y - 2 * A_WALL_X   # 33.40

# El corte arranca a 10 mm de la base y SALE por arriba.
A_WINDOW_Z0 = 10.0

# --------------------------------------------------------------------------
# PIEZA B - la que se acopla encima
# --------------------------------------------------------------------------

B_WALL = 3 * NOZZLE                # 1.8 en las cuatro caras

# El interior de B iguala al de A, para que el chute sea continuo y no haya
# escalon donde la capsula pueda trabarse.
B_INNER_X = A_INNER_X
B_INNER_Y = A_INNER_Y

# Zocalo local en el extremo inferior: recibe el extremo de A.
SOCKET_DEPTH = 12.0
SOCKET_JAW = 2 * NOZZLE            # 1.2, mordaza exterior
SOCKET_X = A_OUTER_X + 2 * FIT_SOCKET     # 39.80
SOCKET_Y = A_OUTER_Y + 2 * FIT_SOCKET     # 37.30
SOCKET_OUTER_X = SOCKET_X + 2 * SOCKET_JAW   # 42.40
SOCKET_OUTER_Y = SOCKET_Y + 2 * SOCKET_JAW   # 39.90

B_MIN_WALL = 2 * NOZZLE             # 1.2, minimum printable wall around socket
B_OUTER_X = max(B_INNER_X + 2 * B_WALL, SOCKET_X + 2 * B_MIN_WALL)
B_OUTER_Y = max(B_INNER_Y + 2 * B_WALL, SOCKET_Y + 2 * B_MIN_WALL)

# B conserva marco arriba y abajo: el corte va entre estas dos cotas.
B_WINDOW_Z0 = SOCKET_DEPTH          # 12.0, justo encima del zocalo
B_WINDOW_Z1 = HEIGHT - 10.0        # 140.0

# --------------------------------------------------------------------------
# PIEZA A - perfil escalonado
# --------------------------------------------------------------------------
# Los primeros 38 mm mantienen el perfil slim para entrar en el holder (o en
# otro bloque). Los ultimos 12 mm vuelven al slim para enchufar en el zocalo
# de B. El cuerpo intermedio ensancha al exterior de B.

A_INSERT_BOTTOM = 38.0
A_INSERT_TOP = SOCKET_DEPTH          # 12.0
A_WIDE_X = B_OUTER_X                 # 42.20
A_WIDE_Y = B_OUTER_Y                 # 39.70


def _window_slot(inner_x, wall_x, z0, z1, round_top, thickness):
    """Corte de inspeccion en la cara +X (una de las de 37).

    Termina en ARCO abajo, y arriba solo si `round_top`. Cuando el corte
    sale por el borde superior de la pieza no hay nada que redondear ahi.
    """
    recto_z0 = z0 + WINDOW_R
    recto_z1 = (z1 - WINDOW_R) if round_top else z1
    with Locations((inner_x / 2, 0, recto_z0)):
        Box(thickness, WINDOW_W, recto_z1 - recto_z0,
            align=(Align.MIN, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT)

    with Locations((inner_x / 2, 0, z0 + WINDOW_R)):
        Cylinder(WINDOW_R, thickness,
                 rotation=(0, -90, 0),
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)

    if round_top:
        lado = WINDOW_R * math.sqrt(2)
        with Locations((inner_x / 2, 0, z1 - WINDOW_R)):
            Box(thickness, lado, lado,
                rotation=(45, 0, 0),
                align=(Align.MIN, Align.CENTER, Align.CENTER),
                mode=Mode.SUBTRACT)


def build_piece_a(height: float = HEIGHT):
    """Pieza A: escalonada. Slim abajo y arriba, ancha en el medio."""
    z_wide_start = A_INSERT_BOTTOM                   # 38
    z_wide_end = height - A_INSERT_TOP               # 138
    h_wide = z_wide_end - z_wide_start               # 100

    with BuildPart() as a:
        # --- Exterior escalonado ---
        # Tramo inferior slim (0 -> 38)
        Box(A_OUTER_X, A_OUTER_Y, z_wide_start,
            align=(Align.CENTER, Align.CENTER, Align.MIN))
        # Tramo medio ancho (38 -> 138)
        with Locations((0, 0, z_wide_start)):
            Box(A_WIDE_X, A_WIDE_Y, h_wide,
                align=(Align.CENTER, Align.CENTER, Align.MIN))
        # Tramo superior slim (138 -> 150)
        with Locations((0, 0, z_wide_end)):
            Box(A_OUTER_X, A_OUTER_Y, A_INSERT_TOP,
                align=(Align.CENTER, Align.CENTER, Align.MIN))

        # Fillet step transitions before cutting the chute/window, so the
        # edges are still intact full-length segments.
        wide_half_x = A_WIDE_X / 2
        wide_half_y = A_WIDE_Y / 2
        step_edges = []
        for e in a.edges():
            cz = e.center().Z
            if not (abs(cz - z_wide_start) < 0.2
                    or abs(cz - z_wide_end) < 0.2):
                continue
            cx, cy = abs(e.center().X), abs(e.center().Y)
            on_wide = (abs(cx - wide_half_x) < 0.2
                       or abs(cy - wide_half_y) < 0.2)
            if on_wide:
                step_edges.append(e)
        if step_edges:
            fillet(step_edges, radius=STEP_FILLET)

        # --- Chute interior continuo ---
        Box(A_INNER_X, A_INNER_Y, height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT)

        # Sale por el borde superior: sin arco arriba, sin barra cruzando.
        wall_thick = (A_WIDE_X - A_INNER_X) / 2 + 1.0
        _window_slot(A_INNER_X, A_WALL_Y, A_WINDOW_Z0, height + 1.0,
                     round_top=False, thickness=wall_thick)
    return a.part


def build_piece_b(height: float = HEIGHT):
    """Pieza B: la que se acopla encima, con zocalo en la base."""
    with BuildPart() as b:
        Box(B_OUTER_X, B_OUTER_Y, height,
            align=(Align.CENTER, Align.CENTER, Align.MIN))

        # Fillet outer vertical edges before Boolean cuts.
        b_half_x = B_OUTER_X / 2
        b_half_y = B_OUTER_Y / 2
        vert_edges = [e for e in b.edges()
                      if (abs(abs(e.center().X) - b_half_x) < 0.2
                          and abs(abs(e.center().Y) - b_half_y) < 0.2
                          and e.length > 10)]
        if vert_edges:
            fillet(vert_edges, radius=EDGE_FILLET)

        Box(B_INNER_X, B_INNER_Y, height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT)
        Box(SOCKET_X, SOCKET_Y, SOCKET_DEPTH,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT)
        # B conserva marco arriba: arco en los dos extremos.
        _window_slot(B_INNER_X, B_WALL, B_WINDOW_Z0, B_WINDOW_Z1,
                     round_top=True, thickness=B_WALL * 3)
    return b.part


def main() -> None:
    out_dir = Path(__file__).resolve().parent.parent

    for nombre, part in (("A_base", build_piece_a()),
                         ("B_acople", build_piece_b())):
        step_path = out_dir / "step" / f"nespressoDispenserExtension_{nombre}.step"
        stl_path = out_dir / "stl" / f"nespressoDispenserExtension_{nombre}.stl"
        step_path.parent.mkdir(exist_ok=True)
        stl_path.parent.mkdir(exist_ok=True)
        export_step(part, str(step_path))
        export_stl(part, str(stl_path))
        bb = part.bounding_box()
        print(f"--- pieza {nombre} ---")
        print(f"  volumen : {part.volume / 1000:.1f} cm^3")
        print(f"  bbox    : {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f}")
        print(f"  escrito : {stl_path.name}")

    print()
    print(f"chute A : {A_INNER_X:.2f} x {A_INNER_Y:.2f}")
    print(f"chute B : {B_INNER_X:.2f} x {B_INNER_Y:.2f}  (igual -> sin escalon)")
    print(f"corte   : en la cara de 37, ancho {WINDOW_W:.1f}, arco r={WINDOW_R:.1f}")
    print(f"paso    : reborde {CAPSULE_RIM:.2f} -> margen "
          f"{A_INNER_X - CAPSULE_RIM:+.2f}")
    print(f"          alto    {CAPSULE_HEIGHT:.2f} -> margen "
          f"{A_INNER_Y - CAPSULE_HEIGHT:+.2f}")


if __name__ == "__main__":
    main()
