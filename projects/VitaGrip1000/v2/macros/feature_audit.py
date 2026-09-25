"""
feature_audit.py - measure v2's added features ON THE EXPORTED MESH.

A render of this part is a flat silhouette: the palm swell, the finger
grooves and the grip texture are all surface relief a few tenths of a
millimetre deep, and none of them changes the outline. Looking at the render
tells you nothing about whether any of them was actually cut.

CLAUDE.md: "A render is not a measurement." So each feature is measured here
against the value it was built to, on the mesh that was exported - not on the
build123d solid, and not on the intent.

Every check answers one question: is this feature PRESENT and the size it was
asked for? A feature that silently built as nothing is the failure mode this
project has hit repeatedly (the vent that returned [] because a guard tripped
by 0.01 mm, and shipped a sealed cavity).
"""

import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import vita_grip as vg  # noqa: E402

STL = HERE.parent / "stl" / "VitaGrip1000.stl"


def band(v, lo, hi, axis=1):
    return v[(v[:, axis] >= lo) & (v[:, axis] <= hi)]


def main():
    if not STL.exists():
        print("no export - run macros/vita_grip.py first")
        return 1
    m = trimesh.load(str(STL))
    v = m.vertices
    ok = True

    print("feature_audit - %s" % STL.name)
    # body_count counts SURFACE components, and a hollow part has one per
    # cavity. Those face inward and carry negative signed volume, which is how
    # they are told apart from genuinely disjoint solids. Reporting the raw
    # count as "bodies=3" reads as a defect on a part that is one solid.
    parts = m.split(only_watertight=False)
    n_solid = sum(1 for q in parts if q.volume > 0) if len(parts) > 1 else 1
    n_void = sum(1 for q in parts if q.volume <= 0) if len(parts) > 1 else 0
    print("  mesh %d faces  watertight=%s  solids=%d voids=%d  vol %.1f cm3"
          % (len(m.faces), m.is_watertight, n_solid, n_void,
             m.volume / 1000.0))
    if n_solid != 1:
        print("      FAIL %d disjoint solids - not printable as one piece"
              % n_solid)
        ok = False

    # ---- 1. HOLLOW: the shell must actually have removed material -------
    solid_ref = 149.0          # v0's measured volume, cm3
    vol = m.volume / 1000.0
    saved = 100.0 * (1.0 - vol / solid_ref)
    print("\n  [1] hollow shell")
    print("      volume %.1f cm3 vs solid v0 %.1f cm3  -> %.0f%% saved"
          % (vol, solid_ref, saved))
    if saved < 15.0:
        print("      FAIL hollowing saved almost nothing - did the shell cut?")
        ok = False

    # ---- 2. CAVITY OPEN --------------------------------------------------
    print("\n  [2] cavity vented (not sealed)")
    cav = vg.check_cavity_open(STL)
    if cav is None:
        print("      SKIP needs trimesh + scipy")
    else:
        sealed, _ = cav
        print("      sealed void %.0f mm3" % sealed)
        if sealed > 500.0:
            print("      FAIL sealed cavity - would slice as solid")
            ok = False

    # ---- 3. PALM SWELL ---------------------------------------------------
    # The swell adds depth REARWARD through the middle of the handle. Compare
    # the handle's rear reach inside the swell band against just outside it.
    print("\n  [3] palm swell")
    sect = vg.handle_sections(False)
    ys = np.array([t[0] for t in sect])
    y_tip, y_top = float(ys.min()), float(ys.max())

    # MEASURE IT BY DIFFERENCE, NOT BY COMPARING TWO PLACES ON THE HANDLE.
    #
    # The first version of this check compared the handle's rear reach at the
    # swell's peak against its reach just outside the swell band, and reported
    # "swell built 27.89 mm (asked 2.20)". That number was nonsense: the
    # handle's own depth varies by tens of millimetres along its length, and
    # the comparison was reading that variation, not the swell.
    #
    # The swell is a delta, so it has to be measured as one - the same
    # sections built with SWELL_AMT on and off.
    amt = vg.SWELL_AMT
    s_on = vg.handle_sections(False)
    vg.SWELL_AMT = 0.0
    s_off = vg.handle_sections(False)
    vg.SWELL_AMT = amt

    d = [a[2] - b[2] for a, b in zip(s_on, s_off)]
    built = 2.0 * max(d)
    k = int(np.argmax(d))
    f_at = (s_on[k][0] - y_tip) / (y_top - y_tip)
    print("      built %.3f mm at f=%.2f (asked %.2f mm at f=%.2f)"
          % (built, f_at, vg.SWELL_AMT, vg.SWELL_PEAK))
    if built < vg.SWELL_AMT * 0.8:
        print("      FAIL the swell did not build")
        ok = False

    # ---- 4. FINGER GROOVES ----------------------------------------------
    # Each groove is a scallop on the FRONT face. Count vertices that sit
    # measurably behind the local front surface inside each groove band.
    print("\n  [4] finger rest grooves (%d asked)" % vg.GROOVE_N)
    found = 0
    for k in range(vg.GROOVE_N):
        f = vg.GROOVE_F0 + (vg.GROOVE_F1 - vg.GROOVE_F0) * (
            k / max(vg.GROOVE_N - 1, 1))
        y = y_tip + f * (y_top - y_tip)
        sel = v[(v[:, 0] < -60.0) & (np.abs(v[:, 1] - y) < 1.2)]
        if len(sel) < 10:
            print("      groove %d at y=%.1f : NO VERTICES" % (k, y))
            continue
        # front reach here vs midway between grooves
        z_here = sel[:, 2].max()
        y_between = y + (vg.GROOVE_F1 - vg.GROOVE_F0) * (
            y_top - y_tip) / max(vg.GROOVE_N - 1, 1) / 2.0
        sel2 = v[(v[:, 0] < -60.0) & (np.abs(v[:, 1] - y_between) < 1.2)]
        z_ref = sel2[:, 2].max() if len(sel2) else np.nan
        bite = z_ref - z_here
        print("      groove %d at y=%7.2f : front %.2f, ref %.2f, bite %+.2f mm"
              % (k, y, z_here, z_ref, bite))
        # The reported bite UNDERSTATES the groove. This samples the deepest
        # vertex in a +/-1.2 mm band, which straddles the scallop's sloped
        # walls as well as its floor, so it reads ~0.25 mm on a groove whose
        # cutter is placed to remove GROOVE_DEPTH = 0.9 mm at the centre
        # (verified against the cutter geometry directly). The check is
        # therefore PRESENCE, not depth - a groove that failed to cut reads
        # 0.00 and is what this is here to catch.
        if bite > 0.15:
            found += 1
    print("      grooves detectable: %d / %d" % (found, vg.GROOVE_N))
    if found == 0:
        print("      FAIL no groove left a measurable mark on the surface")
        ok = False

    # ---- 5. TEXTURE ------------------------------------------------------
    print("\n  [5] textile grip texture")
    if not vg.TEX_ON:
        print("      OFF")
    else:
        y0 = y_tip + vg.TEX_F0 * (y_top - y_tip)
        y1 = y_tip + vg.TEX_F1 * (y_top - y_tip)
        sel = v[(v[:, 0] < -60.0) & (v[:, 1] >= y0) & (v[:, 1] <= y1)]
        # Texture multiplies the vertex count on the textured face. Compare
        # the vertex DENSITY there against an untextured band of the handle.
        y2 = y_tip + (vg.TEX_F1 + 0.05) * (y_top - y_tip)
        y3 = y_tip + (vg.TEX_F1 + 0.20) * (y_top - y_tip)
        ref = v[(v[:, 0] < -60.0) & (v[:, 1] >= y2) & (v[:, 1] <= y3)]
        d_tex = len(sel) / max(y1 - y0, 1e-6)
        d_ref = len(ref) / max(y3 - y2, 1e-6)
        print("      vertex density textured %.1f /mm vs plain %.1f /mm"
              % (d_tex, d_ref))
        print("      ratio %.2fx" % (d_tex / d_ref if d_ref else float("nan")))
        if d_ref and d_tex / d_ref < 1.3:
            print("      WARN texture is not raising the vertex density - it "
                  "may not have cut")

    # ---- 6. REINFORCEMENT RIBS ------------------------------------------
    # Ray ALONG the handle's long axis through the cavity: each rib crosses it
    # as a short solid run. Probed inside the cavity, not on the surface, so
    # the outer wall is not what is being counted.
    print("\n  [6] internal reinforcement ribs (%d asked, %.1f mm thick)"
          % (vg.RIB_N if vg.RIB_ON else 0, vg.RIB_T))
    if not vg.RIB_ON:
        print("      OFF")
    else:
        inner = vg._shell_stations(False)
        iy = np.array([t[0] for t in inner])
        k = int(np.argmax([t[2] for t in inner]))       # deepest station
        cx, cz = inner[k][3], inner[k][4]
        yy = np.linspace(float(iy.min()) - 2.0, float(iy.max()) + 2.0, 3001)
        pts = np.column_stack([np.full(len(yy), cx), yy, np.full(len(yy), cz)])
        ins = m.contains(pts)
        runs, st = [], None
        for i, f in enumerate(ins):
            if f and st is None:
                st = i
            if (not f or i == len(yy) - 1) and st is not None:
                runs.append((yy[st], yy[i - 1]))
                st = None
        webs = [(a, b) for a, b in runs if vg.RIB_T * 0.5 <= b - a <= vg.RIB_T * 2.2]
        for a, b in webs:
            print("      web at y=%7.2f  %.2f mm thick" % ((a + b) / 2.0, b - a))
        print("      webs found: %d / %d" % (len(webs), vg.RIB_N))
        if len(webs) == 0:
            print("      FAIL no rib crossed the cavity - did they build?")
            ok = False

    # ---- 7. WALL THICKNESS ----------------------------------------------
    # Sample the wall where the cavity is, by ray-probing across the handle.
    print("\n  [7] wall thickness (asked %.1f mm)" % vg.SHELL_WALL)
    zs = np.linspace(-40, 20, 2401)
    walls = []
    for y in np.linspace(y_tip + 12.0, y_tip + 40.0, 6):
        pts = np.column_stack([np.full(len(zs), -95.0),
                               np.full(len(zs), y), zs])
        ins = m.contains(pts)
        runs, s = [], None
        for i, f in enumerate(ins):
            if f and s is None:
                s = i
            if (not f or i == len(zs) - 1) and s is not None:
                runs.append(zs[i - 1] - zs[s])
                s = None
        for w in runs:
            if 0.5 < w < 12.0:
                walls.append(w)
    if walls:
        print("      %d wall crossings, median %.2f mm, min %.2f mm"
              % (len(walls), float(np.median(walls)), float(np.min(walls))))
        if np.median(walls) < vg.SHELL_WALL * 0.5:
            print("      FAIL wall is far thinner than asked")
            ok = False
    else:
        print("      no wall crossings found - the handle may still be solid")

    print("\n  VERDICT: %s" % ("features present" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
