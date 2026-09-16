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

El corte de inspeccion va en una cara de 39.5 y termina en ARCO, no en
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
FIT = 0.25                # holgura por cara en todo encaje

WINDOW_W = 20.0           # corte de inspeccion: ancho
WINDOW_R = WINDOW_W / 2   # radio del arco en los extremos

# --------------------------------------------------------------------------
# PIEZA A - la que se inserta en la base
# --------------------------------------------------------------------------

HOLDER_X = 40.0           # boca del holder, interna, con calibre
HOLDER_Y = 37.5

A_OUTER_X = HOLDER_X - 2 * FIT     # 39.50
A_OUTER_Y = HOLDER_Y - 2 * FIT     # 37.00

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
B_INNER_X = A_INNER_X              # 38.30
B_INNER_Y = A_INNER_Y              # 33.40

B_OUTER_X = B_INNER_X + 2 * B_WALL # 41.90
B_OUTER_Y = B_INNER_Y + 2 * B_WALL # 37.00

# Zocalo local en el extremo inferior: recibe el extremo de A.
SOCKET_DEPTH = 12.0
SOCKET_JAW = 2 * NOZZLE            # 1.2, mordaza exterior
SOCKET_X = A_OUTER_X + 2 * FIT     # 40.00
SOCKET_Y = A_OUTER_Y + 2 * FIT     # 37.50
SOCKET_OUTER_X = SOCKET_X + 2 * SOCKET_JAW   # 42.40
SOCKET_OUTER_Y = SOCKET_Y + 2 * SOCKET_JAW   # 39.90

# B conserva marco arriba y abajo: el corte va entre estas dos cotas.
B_WINDOW_Z0 = SOCKET_DEPTH + 8.0   # 20.0, despejando el zocalo
B_WINDOW_Z1 = HEIGHT - 10.0        # 140.0


def _window_slot(inner_y, wall_y, z0, z1, round_top, thickness):
    """Corte de inspeccion en la cara +Y (una de las de 39.5).

    Termina en ARCO abajo, y arriba solo si `round_top`. Cuando el corte
    sale por el borde superior de la pieza no hay nada que redondear ahi.
    """
    # Tramo recto, entre los centros de los arcos.
    recto_z0 = z0 + WINDOW_R
    recto_z1 = (z1 - WINDOW_R) if round_top else z1
    with Locations((0, inner_y / 2, recto_z0)):
        Box(WINDOW_W, thickness, recto_z1 - recto_z0,
            align=(Align.CENTER, Align.MIN, Align.MIN),
            mode=Mode.SUBTRACT)

    # Arco INFERIOR: cilindro con el eje en Y, atravesando la pared +Y.
    # rotation=(-90, 0, 0) lleva el eje del cilindro de Z a +Y, y con
    # Align.MIN en su altura arranca en el punto dado y crece hacia +Y.
    # Abajo el arco mira hacia arriba, asi que no necesita soporte.
    with Locations((0, inner_y / 2, z0 + WINDOW_R)):
        Cylinder(WINDOW_R, thickness,
                 rotation=(-90, 0, 0),
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)

    if round_top:
        # Remate SUPERIOR en PICO a 45 grados, no en arco.
        #
        # Un semicirculo es horizontal en su cuspide: la superficie solo
        # supera los 45 grados a 7.07 mm del centro, dejando 14.1 mm de
        # techo casi plano que el extrusor tendria que puentear. Dos rectas
        # a 45 grados que se juntan en un pico no tienen ningun tramo
        # horizontal, asi que cada capa se apoya en la anterior.
        #
        # Una caja girada 45 grados sobre Y tiene seccion de ROMBO en el
        # plano XZ, y su vertice superior es justamente el pico buscado.
        # Con lado = R*sqrt(2) el rombo mide 2R de ancho, o sea exactamente
        # el ancho del corte, y sus cuatro caras estan a 45 grados.
        lado = WINDOW_R * math.sqrt(2)
        with Locations((0, inner_y / 2, z1 - WINDOW_R)):
            Box(lado, thickness, lado,
                rotation=(0, 45, 0),
                align=(Align.CENTER, Align.MIN, Align.CENTER),
                mode=Mode.SUBTRACT)


def build_piece_a(height: float = HEIGHT):
    """Pieza A: la que se inserta en la base. Corte abierto por arriba."""
    with BuildPart() as a:
        Box(A_OUTER_X, A_OUTER_Y, height,
            align=(Align.CENTER, Align.CENTER, Align.MIN))
        Box(A_INNER_X, A_INNER_Y, height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT)
        # Sale por el borde superior: sin arco arriba, sin barra cruzando.
        _window_slot(A_INNER_Y, A_WALL_Y, A_WINDOW_Z0, height + 1.0,
                     round_top=False, thickness=A_WALL_Y * 3)
    return a.part


def build_piece_b(height: float = HEIGHT):
    """Pieza B: la que se acopla encima, con zocalo local en la base."""
    with BuildPart() as b:
        Box(B_OUTER_X, B_OUTER_Y, height,
            align=(Align.CENTER, Align.CENTER, Align.MIN))
        Box(SOCKET_OUTER_X, SOCKET_OUTER_Y, SOCKET_DEPTH,
            align=(Align.CENTER, Align.CENTER, Align.MIN))
        Box(B_INNER_X, B_INNER_Y, height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT)
        Box(SOCKET_X, SOCKET_Y, SOCKET_DEPTH,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT)
        # B conserva marco arriba: arco en los dos extremos.
        _window_slot(B_INNER_Y, B_WALL, B_WINDOW_Z0, B_WINDOW_Z1,
                     round_top=True, thickness=B_WALL * 3)
    return b.part


def main() -> None:
    out_dir = Path(__file__).resolve().parent.parent

    for nombre, part in (("A_base", build_piece_a()),
                         ("B_acople", build_piece_b())):
        step_path = out_dir / f"nespressoDispenserExtension_{nombre}.step"
        stl_path = out_dir / f"nespressoDispenserExtension_{nombre}.stl"
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
    print(f"corte   : en la cara de 39.5, ancho {WINDOW_W:.1f}, arco r={WINDOW_R:.1f}")
    print(f"paso    : reborde {CAPSULE_RIM:.2f} -> margen "
          f"{A_INNER_X - CAPSULE_RIM:+.2f}")
    print(f"          alto    {CAPSULE_HEIGHT:.2f} -> margen "
          f"{A_INNER_Y - CAPSULE_HEIGHT:+.2f}")


if __name__ == "__main__":
    main()
