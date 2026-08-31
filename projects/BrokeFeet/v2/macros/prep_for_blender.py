"""Prepare the smoothed bone mesh as a Blender sculpting file.

Run with Blender's own Python, not the system one:

  E:\\Blender\\blender.exe --background --factory-startup \\
      --python macros/prep_for_blender.py

Produces:
  blender/BrokeFeetV1_sculpt.blend   <- open this, it starts in Sculpt mode
  blender/BrokeFeetV1_sculpt.stl     <- same geometry, if you prefer importing
  blender/TRANSFORM.json             <- the inverse transform, see below

WHAT IS DONE TO THE MESH, AND WHY
---------------------------------
1. RECENTRE. The pipeline mesh sits at (-144, -179, 2) mm. Blender's sculpt
   pivot and brush falloff both behave badly that far from the origin, so the
   model is translated to sit centred on (0, 0, 0).

2. NO SCALING -- 1 Blender unit = 1 mm, and this is a bug fix.

   The first handoff scaled by 0.001 so Blender's metric readout would show
   millimetres. That silently broke Dyntopo. `constant_detail_resolution` is a
   DIVISOR of the Blender unit (soft range 0.001-1000, default 3), so a 0.4 mm
   detail size on a metre-scaled object needs 1/0.0004 = 2500 -- above the soft
   maximum, and it did nothing. The operator sculpted for an hour and the mesh
   came back byte-identical: 229 243 verts, bbox equal to 9 decimals, with only
   `.sculpt_mask` values (max 0.84) proving the strokes had happened at all.

   At 1 unit = 1 mm the same 0.4 mm detail is 1/0.4 = 2.5, right beside
   Blender's default. `unit_settings.scale_length = 0.001` keeps the metric
   readout honest without touching the geometry.

3. NO REMESH -- and this is a measured reversal.

   Voxel remesh was the plan, for good reason: edge lengths run 0.07 to 4.65 mm
   (a 65x range) and sculpt brushes deform such a surface unevenly. But it
   destroys this model's topology. Measured, mapped back to the pipeline frame:

     | voxel  | faces     | bodies | genus | vs source        |
     |--------|-----------|--------|-------|------------------|
     | source |   458 770 |      1 |    72 | --               |
     | 0.40mm |   707 256 |      7 |    17 | 55 tunnels gone  |
     | 0.30mm | 1 263 476 |      1 |    30 | 42 tunnels gone  |
     | 0.25mm | 1 822 516 |     11 |    18 | 54 tunnels gone  |
     | 0.20mm | 2 840 388 |      1 |    29 | 43 tunnels gone  |

   Genus never recovers at ANY pitch, so this is not a resolution knob -- the
   voxel remesher cannot represent the 40+ thin interosseous tunnels and closes
   them regardless. Volume barely moves (<0.02 %), so volume would NOT have
   caught this; only genus and body count did.

   Centre + scale alone is exact: genus 72, 1 body, watertight, bbox delta
   0.0001 mm. That is what ships.

   For uneven brush behaviour, use Blender's **Dyntopo** (Sculpt mode > Dyntopo,
   ~0.4 mm detail size) which refines locally under the brush instead of
   rebuilding the whole surface, or Remesh only a masked region you are actively
   working on. Both keep the rest of the topology intact.

GETTING YOUR SCULPT BACK INTO THE PIPELINE
------------------------------------------
The transform is recorded in blender/TRANSFORM.json and is exactly invertible:

    pipeline_mm = blender_units * 1000 + CENTRE

macros/import_from_blender.py applies it, re-runs the structural gates, and
writes a pipeline-frame STL. Export from Blender as STL and feed it to that --
do not hand-transform it.

WHAT THIS DOES NOT DO
---------------------
It does not preserve the exact original triangles (voxel remesh rebuilds them)
and it does not attempt any repair. The input is already watertight, 1 body,
genus 72, 0 open edges; remeshing preserves those but does not check them --
import_from_blender.py re-checks on the way back.
"""

import json
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

ROOT = Path(r"D:\CAD\Claude-Projects\BrokeFeetV1")
SRC = ROOT / "BrokeFeetV1_smoothed.stl"
OUTDIR = ROOT / "blender"

DYNTOPO_MM = 0.4               # local refinement under the brush, not a remesh
MM_TO_BLENDER = 1.0            # 1 Blender unit = 1 mm; see docstring, do NOT
                               # scale to metres -- it breaks Dyntopo


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    clear_scene()

    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    # 1 Blender unit = 1 mm. scale_length carries the mm<->m conversion for the
    # UI readout so the GEOMETRY can stay at millimetre scale, which is what
    # keeps constant_detail_resolution inside its usable range.
    scene.unit_settings.scale_length = 0.001
    scene.unit_settings.length_unit = "MILLIMETERS"

    print(f"importing {SRC}")
    bpy.ops.wm.stl_import(filepath=str(SRC))
    obj = bpy.context.selected_objects[0]
    obj.name = "BrokeFeetV1_bone"
    bpy.context.view_layer.objects.active = obj

    me = obj.data
    n_in = len(me.polygons)

    # --- 1. recentre, in millimetre space, before any scaling -------------
    bm = bmesh.new()
    bm.from_mesh(me)
    lo = Vector((min(v.co.x for v in bm.verts),
                 min(v.co.y for v in bm.verts),
                 min(v.co.z for v in bm.verts)))
    hi = Vector((max(v.co.x for v in bm.verts),
                 max(v.co.y for v in bm.verts),
                 max(v.co.z for v in bm.verts)))
    centre = (lo + hi) / 2.0
    for v in bm.verts:
        v.co -= centre
    bm.to_mesh(me)
    bm.free()
    print(f"  recentred: bbox centre was "
          f"({centre.x:.3f}, {centre.y:.3f}, {centre.z:.3f}) mm")

    # --- 2. NO scaling. 1 Blender unit = 1 mm. See docstring: scaling to
    # metres puts constant_detail_resolution at 2500, past its soft maximum,
    # and Dyntopo silently does nothing.
    print("  no scaling: 1 Blender unit = 1 mm")

    # --- 3. NO remesh. See the module docstring: voxel remesh closes 42-55 of
    # this model's thin interosseous tunnels at every pitch tried, and volume
    # does not move enough to notice (<0.02 %). Original triangles ship.
    n_out = len(obj.data.polygons)
    print(f"  faces {n_in} (unchanged -- remesh would close ~55 tunnels)")

    bpy.ops.object.shade_smooth()

    # --- outputs -----------------------------------------------------------
    stl = OUTDIR / "BrokeFeetV1_sculpt.stl"
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.stl_export(filepath=str(stl), export_selected_objects=True,
                          global_scale=1.0)
    print(f"  wrote {stl}")

    transform = {
        "note": "pipeline_mm = blender_units * mm_per_blender_unit + centre_mm",
        "centre_mm": [centre.x, centre.y, centre.z],
        "blender_units_per_mm": MM_TO_BLENDER,
        "mm_per_blender_unit": 1.0 / MM_TO_BLENDER,
        "remeshed": False,
        "remesh_note": ("voxel remesh closes 42-55 tunnels at every pitch "
                        "tried (0.2-0.4 mm); original triangles kept"),
        "source": str(SRC.name),
        "source_faces": n_in,
        "sculpt_faces": n_out,
        # Topology to hold on the way back -- import_from_blender.py gates these.
        "expect_genus": 72,
        "expect_bodies": 1,
        "expect_watertight": True,
        "expect_volume_cm3": 121.050,
    }
    tj = OUTDIR / "TRANSFORM.json"
    tj.write_text(json.dumps(transform, indent=2))
    print(f"  wrote {tj}")

    # start the file in Sculpt mode so it opens ready to work, with Dyntopo
    # preconfigured -- it refines locally under the brush, which is the
    # replacement for the global remesh that could not be used here.
    bpy.ops.object.mode_set(mode="SCULPT")
    sculpt = scene.tool_settings.sculpt

    # X-symmetry is ON by default in Blender. On a LEFT clubfoot that mirrors
    # every stroke across the midline onto the wrong side of the foot. Off.
    sculpt.use_symmetry_x = False
    sculpt.use_symmetry_y = False
    sculpt.use_symmetry_z = False

    # Divisor of the Blender unit, soft range 0.001-1000, default 3. At
    # 1 unit = 1 mm this is 1/0.4 = 2.5. (At the old metre scale it computed to
    # 2500, past the soft max, and Dyntopo did nothing at all.)
    sculpt.detail_type_method = "CONSTANT"
    sculpt.constant_detail_resolution = 1.0 / DYNTOPO_MM
    sculpt.detail_refine_method = "SUBDIVIDE_COLLAPSE"
    print(f"  sculpt mode, symmetry OFF, Dyntopo constant detail "
          f"{1.0 / DYNTOPO_MM:.2f} (= {DYNTOPO_MM} mm edges)")

    # Turn Dyntopo ON rather than leaving it to Ctrl+D. Left off, a brush on
    # this mesh's uneven triangles is exactly what produced an unchanged mesh
    # last session.
    try:
        if not bpy.context.object.use_dynamic_topology_sculpting:
            bpy.ops.sculpt.dynamic_topology_toggle()
        print(f"  Dyntopo ENABLED: "
              f"{bpy.context.object.use_dynamic_topology_sculpting}")
    except Exception as e:                                  # noqa: BLE001
        print(f"  NOTE: could not enable Dyntopo headlessly ({e}); "
              f"press Ctrl+D in the viewport")

    blend = OUTDIR / "BrokeFeetV1_sculpt.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    print(f"  wrote {blend}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
