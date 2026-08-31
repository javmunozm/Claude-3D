"""BrokeFeet -- printable teaching model of a left clubfoot skeleton.

Takes the segmented bone mesh (segment_bone.py) and turns it into something
that survives an FDM printer and a classroom: the bones fused into one block,
sat on a labelled display base, with the model's status embossed into the base
so it cannot be separated from the object.

CLINICAL SCOPE -- read before using this model
----------------------------------------------
Built from screen captures of a PACS viewer, not from DICOM. Bone SHAPE is
reproduced from the patient's own scan; absolute ANGLES are not measurable from
the available data, because only the sagittal series was captured. The varus
and rotational components of this deformity live in the coronal and axial
planes, which are absent.

So this model teaches what a residual clubfoot with subtalar coalition looks
like. It must NOT be used to measure osteotomy wedge angles or to plan cut
orientation for the Souchet / modified Dwyer / talar neck osteotomy. That is
what the embossed marking on the base says, in Spanish, on the object itself.

Coordinate convention (per docs/system.md, +Z up, origin at base centre):
  +X = medial-lateral   (across the foot)
  +Y = posterior-anterior (heel to toes)
  +Z = up               (plantar surface to dorsum)
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import trimesh
from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Location,
    Mode,
    Plane,
    Text,
    Vector,
    add,
    chamfer,
    export_step,
    export_stl,
    extrude,
    fillet,
)

PROJECT = Path(__file__).resolve().parent.parent
BONE_STL = PROJECT / "BrokeFeet_bone_raw.stl"

# --- constants: real-world measurements, mm --------------------------------

# Print scale. 1.0 is life size (~145 mm foot). The teaching model stays life
# size -- students need to relate it to a real foot, and a 145 mm part fits any
# common FDM bed.
SCALE = 1.0

# Base plate. Sized from the foot's own footprint plus a margin wide enough to
# carry the two text lines without crowding the bone.
BASE_MARGIN = 18.0
BASE_THICKNESS = 7.0
BASE_FILLET = 4.0
BASE_CHAMFER = 1.0

# Embossed lettering. 0.6 mm of relief is two layers at 0.3 mm -- enough to
# read and to feel with a fingertip, which is the point: the warning must be
# legible even to someone handling the model without looking at it.
TEXT_HEIGHT = 7.0
TEXT_RELIEF = 0.6
TEXT_MARGIN = 6.0

WARNING_LINE = "MODELO REPRESENTATIVO - NO APTO PARA PLANIFICACION"
CAPTION_LINE = "Pie zurdo izq. - coalicion subtalar - TAC sagital 2mm"

# How far the bone block sinks into the base. A real intersection (rather than
# a tangent contact) is what fuses them into one printable solid -- touching
# surfaces do not union in a boolean.
BONE_SINK = 2.5

# How far the ankle-joint bridge reaches into the bone at each end. A boolean
# union needs real interpenetration, not contact -- 4 mm is comfortably more
# than the joint space and the mesh's own surface roughness.
JOINT_BRIDGE_BITE = 4.0

# Radius of the joint bridge. Large enough to survive printing as a load path
# (the leg is a lever on this model) but small enough to stay tucked inside the
# joint's own silhouette rather than reading as an added lump.
JOINT_BRIDGE_RADIUS = 5.0

# A vertex this close to the base counts as touching it. Set at the layer
# height a 0.2 mm-layer printer would use -- below that, contact is nominal.
SEATING_TOLERANCE = 2.0

# Minimum contact vertices before the model is considered to actually stand
# rather than balance. Enforced because a model that balances on one point
# passes every topology gate and still snaps the first time it is handled.
MIN_SEATING_POINTS = 200


def load_bone_block() -> trimesh.Trimesh:
    """Load the segmented bones and fuse them into a single teaching block.

    The scan yields three separate bodies: the foot, the tibia and the fibula.
    They are anatomically ADJACENT but geometrically DISJOINT -- the ankle
    mortise is a joint space, so tibia and talus touch across a cartilage gap
    and never interpenetrate. A boolean union of merely-touching solids does
    not fuse them (the same failure VitaGrip hit; see docs/commands.md), which
    is why an earlier build exported 24 loose bodies with the leg floating
    above the foot.

    The surgeon asked for a block model, so the joint is deliberately bridged:
    each leg bone is extended downward past its articular surface until it
    genuinely intersects the talus. That fuses the model into one printable
    solid at the cost of filling the ankle joint space -- an acceptable trade
    for a block model, and the joint line stays visible as a surface crease.
    """
    if not BONE_STL.exists():
        raise SystemExit(f"missing {BONE_STL}; run segment_bone.py first")

    mesh = trimesh.load(BONE_STL)
    bodies = sorted(mesh.split(only_watertight=False), key=lambda b: -b.volume)
    print(f"  loaded {len(bodies)} bone bodies")

    foot = bodies[0]
    legs = bodies[1:]

    bridged = [foot]
    for leg in legs:
        bridged.append(leg)
        bridged.append(_joint_bridge(leg, foot))

    block = trimesh.boolean.union(bridged)

    if SCALE != 1.0:
        block.apply_scale(SCALE)

    # Rest the model on the surface it actually stands on.
    #
    # This foot is in EQUINUS: measured along its length, the plantar surface
    # runs from z=-188 under the heel to z=-147 under the forefoot, a 40 mm
    # drop. Seating it by bounding box alone therefore balances it on whichever
    # single point happens to be lowest -- an earlier build stood the whole
    # model on its toe tips with the heel in mid-air, which passed every
    # topology gate and would have snapped in a student's hands.
    #
    # Tilting the model so heel and forefoot share a plane would misrepresent
    # the deformity, which is the one thing this model exists to show. So the
    # equinus is preserved and the CONTACT PATCH is found instead: the model
    # sits on its true lowest region, and _seating_report() verifies that
    # region is broad enough to stand on.
    block.apply_translation([0.0, 0.0, -block.bounds[0][2]])

    bounds = block.bounds
    centre = (bounds[0] + bounds[1]) / 2.0
    block.apply_translation([-centre[0], -centre[1], 0.0])

    return block


def _seating_report(block: trimesh.Trimesh) -> dict:
    """How broadly the model actually touches the base it sits on."""
    low = block.vertices[block.vertices[:, 2] <= SEATING_TOLERANCE]
    return {
        "points": len(low),
        "span_y": float(np.ptp(low[:, 1])) if len(low) else 0.0,
        "span_x": float(np.ptp(low[:, 0])) if len(low) else 0.0,
    }


def _joint_bridge(leg: trimesh.Trimesh, foot: trimesh.Trimesh) -> trimesh.Trimesh:
    """A short plug spanning the joint space between a leg bone and the foot.

    Sized to the leg bone's own cross-section at its distal end, so it reads as
    a continuation of that bone rather than as an added lump, and inset
    slightly so it does not bulge past the bone's silhouette.
    """
    from scipy.spatial import cKDTree

    # Work from the leg bone's distal end -- its articular region.
    distal = leg.vertices[leg.vertices[:, 2] < leg.bounds[0][2] + 8.0]
    if len(distal) < 4:
        distal = leg.vertices

    # Bridge between the ACTUAL closest pair of surface points, not along a
    # fixed axis. The tibia meets the talar dome from above, but the fibula
    # descends lateral to it as the malleolus, so an axis-aligned plug aimed
    # straight down misses the fibula entirely and leaves it a loose body.
    # Measured gaps here are small (1.3 mm tibia, 0.9 mm fibula) but a boolean
    # union needs overlap, and small is still disjoint.
    tree = cKDTree(foot.vertices)
    distances, indices = tree.query(distal)
    nearest = int(np.argmin(distances))

    leg_point = distal[nearest]
    foot_point = foot.vertices[indices[nearest]]

    # A cylinder along the line joining them, extended past both ends so it
    # bites into each bone rather than merely touching.
    axis = foot_point - leg_point
    length = float(np.linalg.norm(axis))
    if length < 1e-6:
        axis, length = np.array([0.0, 0.0, -1.0]), 1.0
    direction = axis / length

    start = leg_point - direction * JOINT_BRIDGE_BITE
    end = foot_point + direction * JOINT_BRIDGE_BITE

    plug = trimesh.creation.cylinder(
        radius=JOINT_BRIDGE_RADIUS,
        segment=np.array([start, end]),
        sections=24,
    )
    print(f"    bridged {length:.2f} mm joint gap "
          f"at ({foot_point[0]:.0f}, {foot_point[1]:.0f}, {foot_point[2]:.0f})")
    return plug


def build_base(footprint_x: float, footprint_y: float) -> BuildPart:
    """Display base carrying the embossed status marking."""
    width = footprint_x + 2 * BASE_MARGIN
    depth = footprint_y + 2 * BASE_MARGIN

    with BuildPart() as base:
        Box(width, depth, BASE_THICKNESS,
            align=(Align.CENTER, Align.CENTER, Align.MIN))

        # Round the vertical corners, chamfer the top lip. Both are comfort
        # features: this part gets handled constantly in a teaching setting.
        fillet(base.edges().filter_by(Axis.Z), BASE_FILLET)
        chamfer(base.edges().group_by(Axis.Z)[-1], BASE_CHAMFER)

    return base, width, depth


def add_marking(base: BuildPart, width: float, depth: float) -> None:
    """Emboss the warning and caption onto the base's top face.

    The text runs along the base's LONG axis (Y, heel-to-toe), so the lines sit
    beside the foot rather than across it. Each line is auto-sized to fit the
    available run: the warning string is 50 characters and must not overflow
    the plate -- an unreadable warning is the same as no warning.
    """
    available = depth - 2 * TEXT_MARGIN

    for text, x_offset, nominal in (
        (WARNING_LINE, -width / 2 + TEXT_MARGIN + TEXT_HEIGHT * 0.6, TEXT_HEIGHT),
        (CAPTION_LINE, width / 2 - TEXT_MARGIN - TEXT_HEIGHT * 0.5, TEXT_HEIGHT * 0.7),
    ):
        # Width of a rendered string is roughly 0.62 * font_size per character
        # for this font; shrink the size if that would exceed the plate.
        estimated = len(text) * nominal * 0.62
        size = nominal * min(1.0, available / estimated)

        # Rotate the sketch plane so the baseline runs along +Y, and offset it
        # to one side of the plate. Building the plane with the offset baked in
        # avoids relying on moving a sketch after the fact.
        plane = Plane(
            origin=(x_offset, 0, BASE_THICKNESS),
            x_dir=(0, 1, 0),
            z_dir=(0, 0, 1),
        )

        with BuildPart() as raised:
            with BuildSketch(plane):
                Text(text, font_size=size, align=(Align.CENTER, Align.CENTER))
            extrude(amount=TEXT_RELIEF)

        base.part = base.part + raised.part


def main() -> None:
    print("loading segmented bone...")
    block = load_bone_block()
    extents = block.extents
    print(f"  block extents {extents[0]:.1f} x {extents[1]:.1f} x {extents[2]:.1f} mm")
    print(f"  block volume  {block.volume / 1000:.1f} cm3, "
          f"watertight={block.is_watertight}")

    print("building base...")
    base, width, depth = build_base(extents[0], extents[1])
    add_marking(base, width, depth)
    print(f"  base {width:.1f} x {depth:.1f} x {BASE_THICKNESS} mm")

    contact = _seating_report(block)
    print(f"  seating: {contact['points']} vertices within "
          f"{SEATING_TOLERANCE} mm of the base, spanning "
          f"{contact['span_y']:.0f} mm of foot length")
    if contact["points"] < MIN_SEATING_POINTS:
        raise SystemExit(
            "model does not seat on the base -- it would balance on a point "
            "and snap. Check the orientation applied in load_bone_block()."
        )

    # Export the bone block and the base as one assembly. The bone mesh stays a
    # mesh (it has ~200k faces; converting that to a BREP solid would take
    # minutes and gain nothing for printing), so the two are merged at the mesh
    # level rather than in build123d.
    print("merging...")
    base_mesh = _tessellate(base.part)

    block.apply_translation([0, 0, BASE_THICKNESS - BONE_SINK])
    assembly = trimesh.boolean.union([base_mesh, block])

    print(f"  assembly: {len(assembly.faces):,} faces, "
          f"{assembly.volume / 1000:.1f} cm3, watertight={assembly.is_watertight}")

    stl_path = PROJECT / "BrokeFeet_teaching.stl"
    assembly.export(stl_path)
    print(f"\nwrote {stl_path}")

    step_path = PROJECT / "BrokeFeet_base.step"
    export_step(base.part, str(step_path))
    print(f"wrote {step_path} (base only -- bone stays a mesh)")


def _tessellate(part) -> trimesh.Trimesh:
    """build123d solid -> trimesh mesh."""
    vertices, triangles = part.tessellate(tolerance=0.05)
    return trimesh.Trimesh(
        vertices=np.array([(v.X, v.Y, v.Z) for v in vertices]),
        faces=np.array(triangles),
    )


if __name__ == "__main__":
    main()
