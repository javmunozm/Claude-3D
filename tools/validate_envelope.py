"""
validate_envelope.py - gate a downloaded mesh against a known spec envelope.

A downloaded 3D model is not evidence of its own dimensions. This repo has
already rejected one reference STL whose 170x170x123 mm envelope contradicted
a confirmed 182x83.5x18.6 mm body (see reference-analyst). This script makes
that check mechanical instead of remembered.

It reports, and never silently "fixes":
  - the mesh's real bounding box, sorted longest-to-shortest so an unknown
    axis convention cannot hide a match
  - the uniform scale factor that WOULD reconcile it with spec, and whether a
    single factor explains all three axes (a model in cm, inches or arbitrary
    units shows one consistent factor; a WRONG OBJECT does not)
  - watertightness, body count and genus, so a scan's quality is visible

Usage:
    python tools/validate_envelope.py <mesh> --spec 160 106 66
    python tools/validate_envelope.py <mesh> --spec 160 106 66 --tol 5
"""
import argparse, sys
import numpy as np
import trimesh


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mesh")
    ap.add_argument("--spec", nargs=3, type=float, required=True,
                    metavar=("A", "B", "C"), help="known envelope in mm, any axis order")
    ap.add_argument("--tol", type=float, default=3.0, help="percent tolerance (default 3)")
    a = ap.parse_args()

    m = trimesh.load(a.mesh, force="mesh")
    got = np.sort(m.extents)[::-1]          # longest first
    spec = np.sort(np.array(a.spec, float))[::-1]

    print("=" * 66)
    print(f"validate_envelope - {a.mesh}")
    print("=" * 66)
    print(f"  raw extents (x,y,z) : {np.round(m.extents,2)}")
    print(f"  sorted long->short  : {np.round(got,2)}")
    print(f"  spec  long->short   : {np.round(spec,2)}")

    ratio = got / spec
    pct = (ratio - 1.0) * 100.0
    print(f"\n  per-axis vs spec:")
    for i,(g,s,p) in enumerate(zip(got, spec, pct)):
        flag = "OK " if abs(p) <= a.tol else "OFF"
        print(f"    [{flag}] {g:8.2f} vs {s:8.2f} mm   {p:+7.2f}%")

    spread = ratio.max() - ratio.min()
    print(f"\n  scale factors       : {np.round(ratio,4)}")
    print(f"  factor spread       : {spread:.4f}")
    if spread < 0.02:
        print(f"  -> ONE uniform factor {ratio.mean():.4f} explains all three axes.")
        print(f"     Consistent with a units/scale issue, NOT a different object.")
    else:
        print(f"  -> NO single factor fits. Proportions differ from spec:")
        print(f"     this is a DIFFERENT SHAPE, not a mis-scaled one.")

    print(f"\n  watertight          : {m.is_watertight}")
    print(f"  bodies              : {m.body_count}")
    print(f"  euler / genus       : {m.euler_number} / "
          f"{(2 - m.euler_number)//2 if m.is_watertight else 'n/a'}")
    print(f"  faces               : {len(m.faces)}")

    ok = bool(np.all(np.abs(pct) <= a.tol))
    print("\n" + "=" * 66)
    print(f"VERDICT: {'ENVELOPE MATCHES SPEC' if ok else 'ENVELOPE DOES NOT MATCH SPEC'}")
    print("=" * 66)
    print("An envelope match is necessary, not sufficient: it says the bounding\n"
          "box agrees, not that the FORM is right. Audit the shape separately.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
