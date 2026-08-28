"""Bring a Blender sculpt back into the pipeline frame, and gate it.

  python macros/import_from_blender.py <sculpted.stl> [--out FILE]

Applies the inverse of prep_for_blender.py's transform, recorded in
blender/TRANSFORM.json:

    pipeline_mm = blender_units * 1000 + centre_mm

then re-checks the structural properties the model must keep. Sculpting is
freehand, so these are the things that can silently break:

  watertight      a brush that punches through a thin wall opens the mesh
  bodies == 1     the model must stay one printable piece
  genus == 72     a DROP means a joint or tunnel was filled in; the voxel
                  remesher closed 55 this way, which is why it is not used
  volume          a large swing means the surface moved far more than intended

Genus is the one to watch. Volume moved less than 0.02 % while the remesher was
destroying 55 tunnels, so volume alone would not have caught it.

None of these are fatal on their own -- if you deliberately sculpted a joint
closed, genus SHOULD drop. They are reported, not enforced, except watertight
and body count which the print pipeline genuinely requires.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TJ = ROOT / "blender" / "TRANSFORM.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sculpted", help="STL exported from Blender")
    ap.add_argument("--out", default=None,
                    help="output STL in pipeline coordinates")
    ap.add_argument("--transform", default=str(TJ))
    args = ap.parse_args()

    t = json.loads(Path(args.transform).read_text())
    centre = np.array(t["centre_mm"], float)
    mm_per_unit = float(t["mm_per_blender_unit"])

    m = trimesh.load(args.sculpted)
    print(f"loaded {Path(args.sculpted).name}: "
          f"{len(m.vertices)} verts  {len(m.faces)} faces")
    print(f"  bbox in Blender units {np.round(m.bounds[0], 4)} .. "
          f"{np.round(m.bounds[1], 4)}")

    m.vertices = m.vertices * mm_per_unit + centre
    print(f"  -> pipeline mm        {np.round(m.bounds[0], 2)} .. "
          f"{np.round(m.bounds[1], 2)}")

    bodies = len(m.split(only_watertight=False))
    genus = (2 - m.euler_number) // 2
    _, cnt = np.unique(m.edges_sorted, axis=0, return_counts=True)
    open_edges = int((cnt == 1).sum())
    vol = m.volume / 1000.0

    exp_g = t.get("expect_genus")
    exp_b = t.get("expect_bodies")
    exp_v = t.get("expect_volume_cm3")

    print("\nSTRUCTURE")
    print(f"  watertight   {m.is_watertight}")
    print(f"  open edges   {open_edges}")
    print(f"  bodies       {bodies}" + (f"  (was {exp_b})" if exp_b else ""))
    print(f"  genus        {genus}" + (f"  (was {exp_g})" if exp_g else ""))
    print(f"  volume       {vol:.3f} cm3" +
          (f"  ({100 * (vol - exp_v) / exp_v:+.3f} %)" if exp_v else ""))

    print("\nNOTES")
    hard = []
    if not m.is_watertight:
        hard.append("not watertight")
        print("  [BLOCK] not watertight -- a brush likely punched through a "
              "thin wall. Blender: Mesh > Clean Up, or sculpt the hole shut.")
    if exp_b and bodies != exp_b:
        hard.append(f"bodies {bodies} != {exp_b}")
        print(f"  [BLOCK] {bodies} bodies, expected {exp_b} -- the model must "
              f"stay one printable piece.")
    if exp_g and genus < exp_g:
        print(f"  [note ] genus {genus} < {exp_g}: {exp_g - genus} tunnel(s) "
              f"closed. Intended if you filled a defect; if not, a brush "
              f"bridged a gap.")
    if exp_g and genus > exp_g:
        print(f"  [note ] genus {genus} > {exp_g}: {genus - exp_g} new "
              f"tunnel(s) -- a brush broke through somewhere.")
    if exp_v and abs(vol - exp_v) / exp_v > 0.05:
        print(f"  [note ] volume moved {100 * (vol - exp_v) / exp_v:+.1f} %, "
              f"more than sculpting a few craters should.")
    if not hard:
        print("  nothing blocking -- safe to feed to the print pipeline.")

    if args.out:
        out = Path(args.out)
        m.export(out)
        print(f"\nwrote {out}")
        print(f"verify with: python ..\\tools\\render_check.py {out}")

    return 1 if hard else 0


if __name__ == "__main__":
    raise SystemExit(main())
