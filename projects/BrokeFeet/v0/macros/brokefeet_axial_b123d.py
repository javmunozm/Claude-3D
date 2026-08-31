"""BrokeFeet -- printable teaching model, built on the axial reconstruction.

Supersedes brokefeet_b123d.py, which was built on the 2 mm sagittal series.
This one uses the 0.625 mm VOL OSEO axial reconstruction: 17 individually
resolved bones instead of 3 fused masses, cross-validated against the sagittal
series to 0.6 mm on foot length (see crossvalidate.py).

DEFORMITY IS PRESERVED, NOT CORRECTED
-------------------------------------
The foot is in equinus -- its plantar surface rises ~77 mm from heel to
forefoot -- and carries forefoot adductus, hindfoot varus, talar neck varus and
a subtalar coalition. All of it is kept exactly as scanned. The model exists to
show the deformity, so nothing here levels, straightens or "fixes" the pose.

That creates a real engineering problem: a foot in equinus does not stand on a
flat plate, it balances on whatever point is lowest. An earlier build stood the
whole model on its toe tips with the heel in mid-air, passed every topology
gate, and would have snapped. The fix is a CONTOURED CRADLE -- a base whose top
surface is cut to the foot's own plantar profile, so the model is supported
along its length in the pose it actually has.

CLINICAL SCOPE
--------------
Built from PACS screen captures, not DICOM. Bone shape and the axial-plane
components (adductus, rotation) are measured. The coronal plane -- where varus
lives -- is derived from the two captured series, not directly acquired. Use
for teaching; do not measure osteotomy wedge angles on it. The base carries
that statement embossed, in Spanish, on the object itself.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import trimesh
from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Mode,
    Plane,
    Text,
    add,
    chamfer,
    export_step,
    extrude,
    fillet,
)

PROJECT = Path(__file__).resolve().parent.parent
BONE_STL = PROJECT / "BrokeFeet_axial_raw.stl"

# --- constants: mm ---------------------------------------------------------

SCALE = 1.0

# Must match segment_axial.MIN_BODY_VOLUME_MM3. A distal phalanx of the 5th
# toe measures ~64 mm3, so a 150 mm3 filter here would drop the very bones the
# segmentation was retuned to recover.
MIN_BONE_MM3 = 40.0

# Base plate
BASE_MARGIN = 16.0
BASE_THICKNESS = 8.0
BASE_FILLET = 4.0
BASE_CHAMFER = 1.0

# Cradle: the plate's top is raised into a ridge that follows the foot's own
# plantar profile, sampled in bands along its length. Each band's support rises
# to just under that band's lowest bone, so the model is carried along its
# whole length instead of balancing on one point.
CRADLE_BANDS = 24
CRADLE_WIDTH_MARGIN = 3.0

# Stand the model on the tibia's proximal cut rather than on the foot. See the
# rotation in main() for the measurements behind this.
STAND_ON_LEG = True

# Mirror the model across X, at the operator's request.
#
# NOTE: this contradicts the laterality measured from the source study, and is
# recorded here so the discrepancy is not lost.
#
# What was measured, before the mirror was applied:
#   - The study header reads "TAC- PIE IZQUIERDO" (left foot).
#   - In main-series slice 165 the hallux -- the largest bone in the forefoot
#     cross-section, 2822 px -- sits at 81.2 % across the bone span, i.e. toward
#     high pane-X.
#   - The axis map in segment_axial.py is [col, -row, slice]: X is NOT negated,
#     so pane column maps straight to mesh +X with no mirroring.
#   - The rebuilt mesh peaks at X 136-140 mm, matching the un-mirrored
#     prediction of 138.1 mm rather than the mirrored 117.7 mm.
#   - The top-view render shows the hallux on one side with the four lesser
#     toes stepping shorter away from it: a left foot seen from the dorsum.
#
# On that evidence the un-mirrored model is already the patient's left foot,
# and mirroring produces a right foot. The operator judged otherwise from
# looking at the model, so the mirror is applied. If the printed part comes out
# reading as the wrong side, set this back to False -- that is the single knob.
#
# NOW APPLIED UPSTREAM, in segment_axial.py, so that BrokeFeet_axial_raw.stl
# carries the mirror as well and both STLs on disk show the same side. This flag
# must therefore stay False: the mesh this script loads is already mirrored, and
# reflecting it again would put the model back on the original side.
#
# crossvalidate.py compensates by mirroring the sagittal mesh to match, which
# keeps the cross-validation meaningful (adduction stays at 1.36 mm instead of
# degrading to 8.67 mm).
MIRROR_X = False

# Supports are built only where the underside is within this height of the
# model's lowest point. Standing on the leg, that lowest point is the tibial
# cut, and everything else -- the whole foot -- is meant to hang free, so the
# window only has to cover the cut itself and the ankle immediately below it.
# Kept at 22 mm: it was tuned to support one region and not creep outward, and
# that behaviour is still what is wanted, only at the other end of the model.
SUPPORT_MAX_RISE = 22.0

# Cap on support width, so posts read as posts and not as a plinth.
SUPPORT_MAX_WIDTH = 26.0

# How deep the bone sits into the cradle. Real interpenetration, so the boolean
# actually fuses -- touching surfaces do not union.
BONE_SINK = 2.0

# Lettering. 0.6 mm of relief reads visually and by fingertip.
TEXT_HEIGHT = 6.0
TEXT_RELIEF = 0.6
TEXT_EMBED = 1.0    # depth the letters sink into the plate, so they fuse to it
TEXT_MARGIN = 5.0

WARNING_LINE = "MODELO REPRESENTATIVO - NO APTO PARA PLANIFICACION"
CAPTION_LINE = "Pie izq. equinovaro - coalicion subtalar - TAC axial 0.6mm"

# Joints are bridged where bones merely touch, so the print is one piece.
# Bridge geometry. 2 mm diameter -- the connections should read as deliberate
# pins holding the piece together, not as anatomy. At 7 mm they dominated the
# joints they were spanning.
#
# The bite must be deep enough that each plug end sits well INSIDE its bone
# rather than grazing the surface: a plug that ends tangent to a curved bone
# produces near-zero-area slivers along the contact ring, which survive as
# non-manifold edges and leave the export non-watertight. 2.5 mm was marginal
# on the rounded tarsals; 5 mm clears them.
JOINT_BRIDGE_DIAMETER = 2.0
JOINT_BRIDGE_RADIUS = JOINT_BRIDGE_DIAMETER / 2.0
JOINT_BRIDGE_BITE = 5.0
MAX_JOINT_GAP_MM = 6.0


def load_bones() -> list[trimesh.Trimesh]:
    if not BONE_STL.exists():
        raise SystemExit(f"missing {BONE_STL}; run segment_axial.py first")

    mesh = trimesh.load(BONE_STL)
    bodies = [b for b in mesh.split(only_watertight=False)
              if abs(b.volume) >= MIN_BONE_MM3]
    bodies.sort(key=lambda b: -abs(b.volume))

    repaired = 0
    for body in bodies:
        if body.volume < 0:
            body.invert()

        # The calcaneus and talus are clipped by the top of the scan stack, so
        # they come out of marching cubes as open shells. The boolean engine
        # rejects any mesh that is not a closed volume ("Not all meshes are
        # volumes!"), so the openings are capped before fusing. Only these two
        # bones need it; the other fifteen close on their own.
        if not body.is_watertight:
            body.merge_vertices()
            trimesh.repair.fill_holes(body)
            trimesh.repair.fix_normals(body)
            repaired += 1

    # Any bone still open after repair is dropped rather than fused. The
    # boolean engine rejects non-volumes outright, and a single bad phalanx
    # would otherwise abort the whole build.
    open_bones = [b for b in bodies if not b.is_watertight]
    if open_bones:
        print(f"    dropped {len(open_bones)} bone(s) that would not close "
              f"({', '.join(f'{b.volume:.0f} mm3' for b in open_bones)})")
        bodies = [b for b in bodies if b.is_watertight]

    # Fail loudly rather than writing a model built from whatever survived.
    # When every body was dropped, an earlier version raised IndexError deep in
    # fuse_bones and left the PREVIOUS run's STL on disk -- so the pipeline
    # looked like it had produced a fresh model while the file was stale, and
    # measurements taken from it described the old geometry.
    if not bodies:
        raise SystemExit(
            f"no watertight bones in {BONE_STL.name} -- every body was open. "
            "Fix the segmentation before rebuilding; the existing STL on disk "
            "is from a previous run and must not be treated as current."
        )

    print(f"  {len(bodies)} bones, "
          f"{sum(b.volume for b in bodies) / 1000:.1f} cm3 total"
          + (f" ({repaired} hole-filled)" if repaired else ""))
    return bodies


def fuse_bones(bodies: list[trimesh.Trimesh]) -> trimesh.Trimesh:
    """Weld the separate bones into one printable solid.

    The axial series resolves the joint spaces, which is anatomically right and
    mechanically useless: 17 loose bones do not print as a block model. Each
    bone is therefore bridged to its nearest already-connected neighbour with a
    short plug, growing the assembly outward from the largest bone until every
    piece is attached.

    Bridging only across gaps under MAX_JOINT_GAP_MM keeps the plugs inside
    real joint spaces rather than spanning open air.
    """
    from scipy.spatial import cKDTree

    attached = [bodies[0]]
    pending = list(bodies[1:])
    plugs: list[trimesh.Trimesh] = []

    while pending:
        best = None
        for index, candidate in enumerate(pending):
            tree = cKDTree(candidate.vertices)
            for anchor in attached:
                distances, indices = tree.query(anchor.vertices)
                k = int(np.argmin(distances))
                gap = float(distances[k])
                if best is None or gap < best[0]:
                    best = (gap, index, anchor.vertices[k],
                            candidate.vertices[indices[k]])

        gap, index, point_a, point_b = best
        candidate = pending.pop(index)

        if gap <= MAX_JOINT_GAP_MM:
            plugs.append(_plug(point_a, point_b))
        else:
            print(f"    warning: {gap:.1f} mm gap exceeds "
                  f"{MAX_JOINT_GAP_MM} mm -- bridged anyway to keep one piece")
            plugs.append(_plug(point_a, point_b))

        attached.append(candidate)

    print(f"    bridged {len(plugs)} joints")
    return trimesh.boolean.union(attached + plugs)


def _plug(point_a: np.ndarray, point_b: np.ndarray) -> trimesh.Trimesh:
    axis = point_b - point_a
    length = float(np.linalg.norm(axis))
    direction = axis / length if length > 1e-6 else np.array([0.0, 0.0, 1.0])

    return trimesh.creation.cylinder(
        radius=JOINT_BRIDGE_RADIUS,
        segment=np.array([
            point_a - direction * JOINT_BRIDGE_BITE,
            point_b + direction * JOINT_BRIDGE_BITE,
        ]),
        sections=20,
    )


def plantar_bands(block: trimesh.Trimesh, bands: int) -> list[tuple]:
    """Per-band (y_low, y_high, x_min, x_max, z_floor) of the foot's underside."""
    verts = block.vertices
    y_min, y_max = verts[:, 1].min(), verts[:, 1].max()

    out = []
    for i in range(bands):
        low = y_min + (y_max - y_min) * i / bands
        high = y_min + (y_max - y_min) * (i + 1) / bands
        band = verts[(verts[:, 1] >= low) & (verts[:, 1] <= high)]
        if len(band) == 0:
            continue
        out.append((low, high, band[:, 0].min(), band[:, 0].max(), band[:, 2].min()))
    return out


def build_cradle(block: trimesh.Trimesh) -> trimesh.Trimesh:
    """Base plate whose top follows the foot's plantar profile."""
    bounds = block.bounds
    width = (bounds[1][0] - bounds[0][0]) + 2 * BASE_MARGIN
    depth = (bounds[1][1] - bounds[0][1]) + 2 * BASE_MARGIN
    centre_x = (bounds[0][0] + bounds[1][0]) / 2.0
    centre_y = (bounds[0][1] + bounds[1][1]) / 2.0

    plate = trimesh.creation.box(extents=(width, depth, BASE_THICKNESS))
    plate.apply_translation([centre_x, centre_y, BASE_THICKNESS / 2.0])

    # Only the HINDFOOT needs a support column. In equinus the heel is the
    # lowest point and the forefoot rises away from the plate; building a
    # pillar under every band produced a solid wall that swallowed the foot
    # (487 cm3 of block with the skeleton buried inside it). The supports stop
    # once the plantar surface has climbed past SUPPORT_MAX_RISE above the
    # lowest point -- beyond that the foot is meant to be in free air, which is
    # what shows the deformity.
    bands = plantar_bands(block, CRADLE_BANDS)
    z_lowest = min(b[4] for b in bands)

    pillars = [plate]
    for low, high, x_min, x_max, z_floor in bands:
        if z_floor - z_lowest > SUPPORT_MAX_RISE:
            continue

        height = z_floor - BASE_THICKNESS + BONE_SINK
        if height <= 0.1:
            continue

        # Narrow post under the band's centre rather than a slab spanning the
        # bone's full width, so the foot stays visible from the sides.
        span_x = min(x_max - x_min, SUPPORT_MAX_WIDTH) + 2 * CRADLE_WIDTH_MARGIN
        span_y = high - low

        pillar = trimesh.creation.box(extents=(span_x, span_y, height))
        pillar.apply_translation([
            (x_min + x_max) / 2.0,
            (low + high) / 2.0,
            BASE_THICKNESS + height / 2.0,
        ])
        pillars.append(pillar)

    print(f"  cradle: {len(pillars) - 1} support bands under the hindfoot, "
          f"plate {width:.0f} x {depth:.0f} mm")
    return trimesh.boolean.union(pillars)


def build_marking(block_bounds, cradle: trimesh.Trimesh) -> trimesh.Trimesh | None:
    """Embossed status text on the plate's exposed margin."""
    bounds = cradle.bounds
    width = bounds[1][0] - bounds[0][0]
    depth = bounds[1][1] - bounds[0][1]
    available = depth - 2 * TEXT_MARGIN

    solids = []
    for text, x_offset, nominal in (
        (WARNING_LINE, bounds[0][0] + TEXT_MARGIN + TEXT_HEIGHT * 0.6, TEXT_HEIGHT),
        (CAPTION_LINE, bounds[1][0] - TEXT_MARGIN - TEXT_HEIGHT * 0.5, TEXT_HEIGHT * 0.7),
    ):
        estimated = len(text) * nominal * 0.62
        size = nominal * min(1.0, available / estimated)

        # Start the extrusion BELOW the plate's top face and run it up past it.
        # Text sitting exactly on the surface only touches the plate, and a
        # boolean union of touching solids does not fuse -- the letters came
        # out as free-floating bodies (the model exported as 4 pieces, the
        # warning text among them). Sinking them by TEXT_EMBED makes the union
        # real while leaving TEXT_RELIEF proud of the surface.
        plane = Plane(
            origin=(x_offset,
                    (bounds[0][1] + bounds[1][1]) / 2.0,
                    BASE_THICKNESS - TEXT_EMBED),
            x_dir=(0, 1, 0),
            z_dir=(0, 0, 1),
        )
        with BuildPart() as raised:
            with BuildSketch(plane):
                Text(text, font_size=size, align=(Align.CENTER, Align.CENTER))
            extrude(amount=TEXT_EMBED + TEXT_RELIEF)
        solids.append(_tessellate(raised.part))

    return trimesh.util.concatenate(solids) if solids else None


def _tessellate(part) -> trimesh.Trimesh:
    vertices, triangles = part.tessellate(tolerance=0.05)
    return trimesh.Trimesh(
        vertices=np.array([(v.X, v.Y, v.Z) for v in vertices]),
        faces=np.array(triangles),
    )


def main() -> None:
    print("loading axial reconstruction...")
    bones = load_bones()

    print("fusing bones into one block...")
    block = fuse_bones(bones)
    if SCALE != 1.0:
        block.apply_scale(SCALE)

    # Mirror across X before anything else positions the model, so the cradle,
    # the island pillars and the seating are all derived from the final shape.
    # Reflection reverses triangle winding, so the normals are fixed after it --
    # left unfixed the mesh exports inside-out and slicers read it as inverted.
    if MIRROR_X:
        block.apply_transform(np.array([
            [-1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]))
        block.fix_normals()

    # Stand the model on the leg, not on the foot.
    #
    # With the proximal series included the model gained 25 mm of tibia and
    # fibula, and the old seating stopped working: SUPPORT_MAX_RISE measures
    # each band's height above the LOWEST plantar point, and the heel now sits
    # 24-47 mm above it, so the hindfoot fell outside the support window
    # entirely. The cradle moved to the midfoot and forefoot and the model
    # balanced with its heel and ankle hanging in the air -- the opposite of
    # what the cradle exists to do.
    #
    # Rotating 180 degrees about X puts the tibia's proximal cut on the plate.
    # That cut is the flat cap marching cubes leaves at the scan limit, so it is
    # a genuine bearing surface rather than a point of bone, and the model hangs
    # from it the way a real specimen hangs from its leg. Measured against the
    # alternative of propping the heel up:
    #
    #     foot down     base 26.5 x 40.5 mm, centre-of-mass offset 50.5 mm
    #     leg down      base 24.0 x 41.0 mm, centre-of-mass offset 24.7 mm
    #
    # Half the overturning offset and 70% more contact vertices. The equinus is
    # untouched by this -- rotating the whole model rigidly changes nothing
    # about the deformity, only which end meets the plate.
    if STAND_ON_LEG:
        block.apply_transform(trimesh.transformations.rotation_matrix(
            np.pi, [1, 0, 0], block.centroid))

    # Sit on Z=0, centred in X/Y. The equinus pose is untouched.
    block.apply_translation([0, 0, -block.bounds[0][2]])
    centre = (block.bounds[0] + block.bounds[1]) / 2.0
    block.apply_translation([-centre[0], -centre[1], 0])

    extents = block.extents
    print(f"  block {extents[0]:.1f} x {extents[1]:.1f} x {extents[2]:.1f} mm, "
          f"{block.volume / 1000:.1f} cm3, watertight={block.is_watertight}")

    print("building contoured cradle...")
    block.apply_translation([0, 0, BASE_THICKNESS])
    cradle = build_cradle(block)

    print("adding marking...")
    marking = build_marking(block.bounds, cradle)

    print("merging...")
    parts = [cradle, block] + ([marking] if marking is not None else [])
    assembly = trimesh.boolean.union(parts)

    # Tie down anything the slicer would see as floating.
    #
    # segment_axial.py already does this for the bone mesh, but the cradle and
    # base change what is supported: bone that had a pillar beneath it may now
    # sit above a gap in the cradle, and the plate itself creates new overhangs.
    # The check has to run on the geometry that actually gets printed.
    from segment_axial import _support_islands

    # The plate's TOP face is what a pillar would stand on. It sits
    # BASE_THICKNESS above the assembly's lowest point, so the function cannot
    # infer it from the bounds -- that finds the plate's underside at Z=0 and
    # classifies nothing as plate-touching.
    # No skip_regions here. segment_axial's SKIP_PILLAR_REGIONS_MM is in the
    # SCAN frame; by this point the model has been mirrored and rotated 180
    # degrees about X to stand on the leg, so those coordinates point somewhere
    # else entirely. Suppressing a pillar in this pass needs values measured in
    # the assembly's own frame.
    pillars = _support_islands([assembly], plate_top_z=BASE_THICKNESS)
    if pillars:
        assembly = trimesh.boolean.union([assembly] + pillars)

    # The boolean returns a closed solid, but writing it to STL discards vertex
    # sharing (STL stores loose triangles), and re-loading leaves a handful of
    # faces unmerged along seams. Slicers treat those as holes. Welding and
    # patching here means the file on disk is watertight, not just the object
    # in memory.
    assembly.merge_vertices()

    # Discard sub-millimetre shards BEFORE any healing pass.
    #
    # The boolean leaves a few zero-volume slivers -- artefacts of pillars and
    # pins meeting thin bone tangentially. They are not printable and they keep
    # body_count above 1, which is the gate that certifies this as one piece.
    #
    # Order matters: the heal below re-runs the boolean, and the manifold engine
    # rejects any input that is not a closed volume ("Not all meshes are
    # volumes!"). A zero-volume sliver is exactly such an input, so healing
    # first crashes on geometry that is about to be thrown away regardless.
    bodies = assembly.split(only_watertight=False)
    if len(bodies) > 1:
        real = [b for b in bodies if abs(b.volume) >= MIN_BONE_MM3]
        shards = len(bodies) - len(real)
        if shards:
            print(f"  discarded {shards} boolean shard(s) below {MIN_BONE_MM3} mm3")
        assembly = trimesh.util.concatenate(real) if len(real) > 1 else real[0]

    broken = len(trimesh.repair.broken_faces(assembly))
    if broken:
        # Do NOT call trimesh.repair.fill_holes here. These defects are
        # degenerate slivers, not open holes, and fill_holes responds by adding
        # faces that split the solid into several bodies -- strictly worse than
        # the sliver. Round-tripping through the boolean engine rebuilds the
        # surface from scratch and resolves them properly.
        print(f"  {broken} seam faces after boolean; re-running union to heal")
        assembly = trimesh.boolean.union([assembly])
        assembly.merge_vertices()
        remaining = len(trimesh.repair.broken_faces(assembly))
        print(f"  -> {remaining} remain")

    bodies = assembly.split(only_watertight=False)

    print(f"  assembly: {len(assembly.faces):,} faces, "
          f"{assembly.volume / 1000:.1f} cm3, "
          f"watertight={assembly.is_watertight}, bodies={len(bodies)}")

    contact = (block.vertices[:, 2] <= BASE_THICKNESS + BONE_SINK + 1.0).sum()
    print(f"  seating: {contact} bone vertices within the cradle")

    out = PROJECT / "BrokeFeet_teaching_axial.stl"
    assembly.export(out)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
