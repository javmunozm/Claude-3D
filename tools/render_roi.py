"""Region-of-interest contact sheet: clip a mesh to a box, render a few fixed angles
at small size onto ONE image, print the numbers beside it.

Use this instead of full-part renders when the question is about one region (a
corner, an edge, a tip). One small sheet costs a fraction of several full views.
Like every render it is not a measurement: read the printed numbers first.

usage:
  python tools/render_roi.py mesh.stl out.png --center X Y Z --size S
         [--views top under iso_a ...] [--ref other.stl] [--px 400]

  --center X Y Z   centre of the box, in the STL's own frame
  --size S         box edge in mm (cube). Default 40.
  --views          any of: top under front back left right iso_a iso_b under_a under_b
                   default: top under iso_a
  --ref other.stl  second row: the same box and views on a reference mesh
                   (e.g. the previous bake), so a change reads side by side
  --px N           tile edge in pixels (default 400; the sheet is N*views by N*rows)

Frame note: Z up. For VitaGripPS5 the R corner is about (85, 65, -12), the L corner
the same with x negated, a handle tip about (+-95, -62, -18).
"""
import argparse
import numpy as np
import pyvista as pv

pv.OFF_SCREEN = True

# camera direction from the box centre toward the camera, and the up vector
VIEWS = {
    "top":     ((0, 0, 1),     (0, 1, 0)),
    "under":   ((0, 0, -1),    (0, 1, 0)),
    "front":   ((0, -1, 0),    (0, 0, 1)),
    "back":    ((0, 1, 0),     (0, 0, 1)),
    "left":    ((-1, 0, 0),    (0, 0, 1)),
    "right":   ((1, 0, 0),     (0, 0, 1)),
    "iso_a":   ((1, -1, 0.9),  (0, 0, 1)),
    "iso_b":   ((-1, -1, 0.9), (0, 0, 1)),
    "under_a": ((1, 1, -0.9),  (0, 0, 1)),   # from below and behind, +x side
    "under_b": ((-1, 1, -0.9), (0, 0, 1)),
}


def clip(path, c, s):
    m = pv.read(path)
    h = s / 2.0
    b = (c[0] - h, c[0] + h, c[1] - h, c[1] + h, c[2] - h, c[2] + h)
    # exact clip, not crinkle: crinkle keeps whole cells, and this mesh has 80 mm
    # needle triangles on the bar rear face that would drag the box out to x -71
    r = m.clip_box(bounds=b, invert=False, crinkle=False)
    r = r.extract_surface() if not isinstance(r, pv.PolyData) else r
    n_all = m.n_cells
    if r.n_cells:
        r = r.compute_normals(split_vertices=True, feature_angle=35.0)
    return r, n_all


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stl")
    ap.add_argument("out")
    ap.add_argument("--center", nargs=3, type=float, required=True)
    ap.add_argument("--size", type=float, default=40.0)
    ap.add_argument("--views", nargs="*", default=["top", "under", "iso_a"])
    ap.add_argument("--ref", default=None)
    ap.add_argument("--px", type=int, default=400)
    a = ap.parse_args()
    for v in a.views:
        if v not in VIEWS:
            ap.error("unknown view %r; choose from %s" % (v, sorted(VIEWS)))

    c = np.array(a.center)
    rows = [("mesh", a.stl, "#2b6fd4")]
    if a.ref:
        rows.append(("ref", a.ref, "#8c8f94"))

    cols = len(a.views)
    p = pv.Plotter(off_screen=True, shape=(len(rows), cols), window_size=(a.px * cols, a.px * len(rows)),
                   border=False)
    dist = a.size * 2.5
    for ri, (tag, path, col) in enumerate(rows):
        m, n_all = clip(path, c, a.size)
        if m.n_cells:
            bb = np.array(m.bounds).reshape(3, 2)
            print("%-4s %s: %d of %d faces in box; x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f" %
                  (tag, path.replace("\\", "/").split("/")[-1], m.n_cells, n_all, *bb.ravel()))
        else:
            print("%-4s %s: NO faces in the box (check --center / --size)" % (tag, path))
        for ci, vname in enumerate(a.views):
            p.subplot(ri, ci)
            p.set_background("#f4f6f9")
            if m.n_cells:
                p.add_mesh(m, color=col, smooth_shading=True, specular=0.4, specular_power=20)
            d, up = VIEWS[vname]
            d = np.array(d, float); d /= np.linalg.norm(d)
            p.camera_position = [tuple(c + d * dist), tuple(c), up]
            p.camera.view_angle = 30
            p.add_text("%s %s" % (tag, vname), position="upper_left", font_size=8, color="black")
    p.screenshot(a.out)
    print("wrote", a.out, "(%dx%d)" % (a.px * cols, a.px * len(rows)))


if __name__ == "__main__":
    main()
