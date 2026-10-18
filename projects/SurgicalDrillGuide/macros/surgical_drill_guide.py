"""SurgicalDrillGuide (rebuild, 2026-09-23): ratcheting K-wire / drill guide, three printed parts.

Replaces the v1 macro (snapshot: attempts/v1-zbore-separate-parts/macros/). v1 bored the wire through the
part THICKNESS (Z) and had no long bar; this rebuild follows the confirmed topology (docs/MEASUREMENTS.md §1-2):

    main_frame    C-hook + long bottom bar + toothed rack, ONE part, uniform Z 0..10. Closed C-tip wire bore on
                  the rectified wire line. Round 6: lug (tenon) under the bar for the handle, external snap
                  finger beside it, bar top raised to a flat Y 7.5 on the hook side.
    l_arm_slider  riser + top bar + V crown (rectified L) + collar + carriage, ONE part. Slides on the rack.
                  Wire bore along the FULL top bar. Integral compliant (flexure) pawl + release tab.
    handle        revolved grip + Ø16 core + square head with a blind socket for the lug and a snap notch
                  (round 6; the thread is gone). Separate, removable, prints standing.

EVERY in-plane (XY) outline is imported at build time from vectors/import/*.dxf (vector-tracer 2026-09-23,
accuracy-reviewed). No primitive stands in for a traced outline. Primitives are used only for DESIGNED features
that no photo shows (bores, rack channel, teeth, pawl, boss, thread) and for fusion-overlap blocks that sit
entirely inside a traced outline (they change no silhouette).

Coordinate frame = the vector datum (vectors/README.md): origin at the rack left tip on the rack top edge,
+X along the rack towards the hook, +Y up, +Z = instrument thickness. Z = 0 is the frame's bed face.
This deliberately departs from the repo's "origin at bottom-face centre" convention: all three parts share the
traced datum so the assembly poses and the coaxiality gate need no re-derived placement.

Status words on constants: MEASURED / DERIVED (from rings at build time) / ASSUMED (no measurement exists;
user decision or design choice) / DESIGNED (a substitution for something the photos do not show) /
PLACEHOLDER (a clearance that print-tolerance-expert must set).

Stages (one file each in the package sdg_model/; split 2026-09-25 from the single-file macro, output
byte-identical). The package name is unique to this project: flat modules named constants.py etc. were measured
to collide across projects in one process (the second project silently read the first one's constants).
    sdg_model/constants.py        1  constants
    sdg_model/rings.py            2  traced-ring import and DERIVED values
    sdg_model/shapes.py           3a generic shape helpers
    sdg_model/mechanisms.py       3b ratchet notch cutter, pawl tooth
    sdg_model/parts/<part>.py     3c one builder per part
    sdg_model/parameters.py       4  parameter bundles + build-time arithmetic checks
    surgical_drill_guide.py       5  this file: build, validate, export. Holds no geometry.
Every stage name is re-exported here, so `import surgical_drill_guide as sdg` (sdg_gates.py) and
tools/reconcile.py (docs/mechanism_sizing.py) keep working unchanged.

Run:  python "D:\\CAD\\Claude-Projects\\projects\\SurgicalDrillGuide\\macros\\surgical_drill_guide.py"
      ... --part handle     builds and exports ONE part (assemblies are not rewritten)
Gates: python "D:\\CAD\\Claude-Projects\\projects\\SurgicalDrillGuide\\macros\\sdg_gates.py"
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build123d import Compound, Pos, Solid, export_step, export_stl  # noqa: E402,F401  (Solid: used by sdg_gates)

from sdg_model.constants import *  # noqa: E402,F401,F403
from sdg_model.mechanisms import _line_x, pawl_tooth_pts, sawtooth_cutter_face, tooth_face_x  # noqa: E402,F401
from sdg_model.parameters import derive_pin, parameters, seat_notch  # noqa: E402,F401
from sdg_model.parts.end_stop_pin import build_pin  # noqa: E402
from sdg_model.parts.handle import build_handle  # noqa: E402
from sdg_model.parts.l_arm_slider import build_l_arm_slider  # noqa: E402
from sdg_model.parts.main_frame import build_main_frame, ctip_pad_region, hook_outer_region  # noqa: E402
from sdg_model.rings import (derive, derive_channel, horizontal_chord, rack_bottom_y, ring_face,  # noqa: E402,F401
                             ring_points, ring_points_file, vertical_chord)
from sdg_model.shapes import (along_y, box, cone_y, cyl_y, extrude_z, one_solid, polygon_face,  # noqa: E402,F401
                              shapely_faces, teardrop_bore_x)

PART_NAMES = ("main_frame", "l_arm_slider", "handle", "end_stop_pin")


def build_all():
    D, travel, chan, teeth, bore, coup, pawl = parameters()
    frame, a_list = build_main_frame(D, T_Z, teeth, bore, coup, D["ctip"], D["pin"])
    a_seat, k_seat = seat_notch(a_list, pawl, D)
    slider = build_l_arm_slider(D, T_Z, WRAP_WALL_Z, chan, bore, pawl, a_seat)
    handle = build_handle(D, T_Z, coup)
    pin = build_pin(D["pin"])
    info = {"D": D, "travel": travel, "chan": chan, "teeth": teeth, "bore": bore, "coup": coup,
            "pawl": pawl, "a_list": a_list, "a_seat": a_seat, "k_seat": k_seat}
    return {"main_frame": frame, "l_arm_slider": slider, "handle": handle, "end_stop_pin": pin}, info


def rack_notches(D, teeth):
    """Notch positions without building the frame: the same cutter call build_main_frame makes."""
    _, a_list = sawtooth_cutter_face(lambda x: rack_bottom_y(D, x), teeth["x0"], teeth["x1"], teeth["pitch"],
                                     teeth["depth"], teeth["land"], teeth["eps"], teeth["hook"])
    return a_list


def build_one(name):
    """One part only (the others are not built). The slider's seat notch comes from rack_notches()."""
    D, travel, chan, teeth, bore, coup, pawl = parameters()
    if name == "main_frame":
        return build_main_frame(D, T_Z, teeth, bore, coup, D["ctip"], D["pin"])[0]
    if name == "l_arm_slider":
        a_seat, _ = seat_notch(rack_notches(D, teeth), pawl, D)
        return build_l_arm_slider(D, T_Z, WRAP_WALL_Z, chan, bore, pawl, a_seat)
    if name == "handle":
        return build_handle(D, T_Z, coup)
    return build_pin(D["pin"])


def slider_at(slider, travel):
    """Opening pose: the slider moves -X by `travel` (MIN = 0 = the photographed pose)."""
    return slider.moved(Pos(-travel, 0, 0))


def part_path(name, ext):
    folder = OUT_DIR / {"stl": "stl", "step": "step", "png": "renders"}.get(ext, "")
    folder.mkdir(exist_ok=True)
    return folder / f"{PREFIX}_{name}.{ext}"


def check_valid(parts):
    """Round 4 (round-3 lesson): an invalid solid can HANG the STL export instead of raising, so every part is
    checked before anything is written."""
    bad = []
    for name, shp in parts.items():
        print(f"{name:13s} valid {shp.is_valid}  solids {len(shp.solids())}  volume {shp.volume:10.2f} mm3  "
              f"bbox {shp.bounding_box()}")
        if not shp.is_valid or len(shp.solids()) != 1:
            bad.append(name)
    if bad:
        raise SystemExit(f"invalid part(s) {bad}: nothing exported")


def export_part(name, shp):
    export_step(shp, str(part_path(name, "step")))
    export_stl(shp, str(part_path(name, "stl")), tolerance=TESS_TOL, angular_tolerance=TESS_ANG)


# ═════════════════════════════════════════════════════════════════════════════
# 5. GENERATE
# ═════════════════════════════════════════════════════════════════════════════

def main_all():
    parts, info = build_all()
    D, chan = info["D"], info["chan"]
    print(f"wire Y {D['wire_y']:.3f}  handle axis X {D['handle_axis_x']:.3f}  ferrule shoulder Y {D['ferrule_top_y']:.3f}"
          f"  bar bottom at axis {D['bar_bottom_at_axis']:.3f}")
    print(f"channel Y {chan['y0']:.3f} .. {chan['y1']:.3f} (frame envelope {chan['envelope'][0]:.3f} .. "
          f"{chan['envelope'][1]:.3f} over X {chan['envelope'][2]:.2f} .. {chan['envelope'][3]:.2f})")
    print(f"teeth: {len(info['a_list'])} notches X {info['a_list'][0]:.3f} .. {info['a_list'][-1] + TOOTH_PITCH:.3f};"
          f" pawl teeth seated in notches {info['k_seat']} (inner a = {info['a_seat'][0]:.3f}) at MIN")
    check_valid(parts)
    cp = info["coup"]
    st = cp["seat"]
    print(f"coupling (arithmetic): lug end -> socket floor {st['lug_end_to_floor']:.3f} (push stop, seated); floor "
          f"{st['floor_t']:.3f}; head top -> bar bottom {st['head_bar_gap'][0]:.3f}..{st['head_bar_gap'][1]:.3f}; "
          f"fillet -> mouth chamfer min {st['mouth_margin']['-X']:.3f} / {st['mouth_margin']['+X']:.3f} (-X / +X)")
    print(f"snap (arithmetic): hook engagement {st['hook_engage_x']:.3f} in X; tip -> notch back "
          f"{st['hook_to_notch_back']:.3f}; pull slack at the hook tip {st['pull_slack_tip']:.3f}; finger L "
          f"{st['finger_L']:.3f}; new material from X {cp['x_min']:.3f} (carriage end {D['carriage_end_x']:.3f} + "
          f"{COUPLING_CARRIAGE_CLEAR}); bar top Y {cp['bar']['y_top']} from X {cp['bar']['x0']:.3f}, hook inner "
          f"contour at X {cp['bar']['x_hook']:.3f}")
    for name, shp in parts.items():
        export_part(name, shp)
    pin = D["pin"]
    added, _, _ = ctip_pad_region(D, D["ctip"])
    print(f"pin: X {pin['x']:.3f} Y {pin['y']:.3f} hole Ø{pin['hole_d']:.2f}; collar face {pin['collar_face']:.3f}; "
          f"travel to pin contact {pin['travel_stop_centred']:.3f} (pin centred) / {pin['travel_stop']:.3f} (pin c/2 "
          f"towards the collar); MAX = {pin['n_max']} teeth = {info['travel']['max']:.3f}; tip gap MAX {D['gap_max']:.3f}")
    print(f"C-tip pad: X {D['ctip']['x_entry']:.3f}..{D['ctip']['x_exit']:.3f}, half-height {D['ctip']['half_h']:.2f}; "
          f"added to the traced outline {added.area:.2f} mm2")
    for pose, t in info["travel"].items():
        asm = Compound(children=[parts["main_frame"], slider_at(parts["l_arm_slider"], t), parts["handle"],
                                 parts["end_stop_pin"]])
        export_stl(asm, str(part_path(f"assembly_{pose}", "stl")), tolerance=TESS_TOL, angular_tolerance=TESS_ANG)
        print(f"assembly_{pose}: travel {t:.3f} mm written")


def main_one(name):
    parts = {name: build_one(name)}
    check_valid(parts)
    export_part(name, parts[name])
    print(f"{name}: STEP + STL written. Assembly STLs NOT rewritten; run without --part before the gates.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Build SurgicalDrillGuide parts.")
    ap.add_argument("--part", choices=PART_NAMES, help="build and export this part only")
    args = ap.parse_args()
    if args.part:
        main_one(args.part)
    else:
        main_all()
