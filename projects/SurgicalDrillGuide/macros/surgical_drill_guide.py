"""SurgicalDrillGuide (rebuild, 2026-09-23): ratcheting K-wire / drill guide, five printed parts (r8).

r8 (2026-10-18): the compliant pawl is replaced by a rigid printed SHOE in a pocket of the carriage's lower block,
driven into the rack by an M6 knurled screw from below (DIN 464 + DIN 557 nuts, bought). The assemblies are written
in the locked state and include the screw / nut clearance volumes (hw_*.stl, not printed).

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
      ... --no-cache        rebuild and rewrite everything
Gates: python "D:\\CAD\\Claude-Projects\\projects\\SurgicalDrillGuide\\macros\\sdg_gates.py"

Incremental build (2026-10-27, tools/stage_cache.py): each part is keyed on its builder's arguments, the source and
constants of the modules it uses, and the traced DXFs. An unchanged part loads from <out>/work/cache/ and its files are
not rewritten; an assembly is rewritten only when one of its parts changed. The build prints what it rebuilt.
SDG_OUT_DIR (environment) sends every output, the cache included, to another folder: previews never touch stl/.
"""

import argparse
import hashlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))

from build123d import Compound, Pos, Solid, export_step, export_stl  # noqa: E402,F401  (Solid: used by sdg_gates)

from sdg_model.constants import *  # noqa: E402,F401,F403
from sdg_model.constants import IMPORT_DIR  # noqa: E402

OUT_DIR = Path(os.environ.get("SDG_OUT_DIR", OUT_DIR))  # noqa: F405
from sdg_model.mechanisms import _line_x, pawl_tooth_pts, sawtooth_cutter_face  # noqa: E402,F401
from sdg_model.parameters import derive_pin, derive_shoe, parameters  # noqa: E402,F401
from sdg_model.parts.end_stop_pin import build_pin  # noqa: E402
from sdg_model.parts.handle import build_handle  # noqa: E402
from sdg_model.parts.l_arm_slider import build_l_arm_slider  # noqa: E402
from sdg_model.parts.main_frame import build_main_frame, ctip_pad_region, hook_outer_region  # noqa: E402
from sdg_model.parts.shoe import build_hardware, build_shoe  # noqa: E402
from sdg_model.rings import (derive, derive_channel, horizontal_chord, rack_bottom_y, ring_face,  # noqa: E402,F401
                             ring_points, ring_points_file, vertical_chord)
from sdg_model.shapes import (along_y, box, cone_y, cyl_y, extrude_z, one_solid, polygon_face,  # noqa: E402,F401
                              shapely_faces, teardrop_bore_x, teardrop_bore_y)

import sdg_model.mechanisms as _m_mech  # noqa: E402
import sdg_model.parts.end_stop_pin as _m_pin  # noqa: E402
import sdg_model.parts.handle as _m_handle  # noqa: E402
import sdg_model.parts.l_arm_slider as _m_slider  # noqa: E402
import sdg_model.parts.main_frame as _m_frame  # noqa: E402
import sdg_model.parts.shoe as _m_shoe  # noqa: E402
import sdg_model.rings as _m_rings  # noqa: E402
import sdg_model.shapes as _m_shapes  # noqa: E402
import stage_cache  # noqa: E402

PART_NAMES = ("main_frame", "l_arm_slider", "handle", "end_stop_pin", "shoe")
HW_NAMES = ("hw_screw", "hw_jam", "hw_drive_nut")   # bought parts, clearance volumes only (STL, not printed)
_COMMON = (_m_shapes, _m_mech, _m_rings)            # helpers every part builder may call


def open_cache(enabled=True):
    return stage_cache.Cache(OUT_DIR / "work" / "cache", enabled=enabled)


def _specs(P):
    """name -> (builder module, builder arguments, build function returning (shape, side data))."""
    D, travel, chan, teeth, bore, coup, shoe = P
    spec = {
        "main_frame": (_m_frame, (D, T_Z, teeth, bore, coup, D["ctip"], D["pin"]),
                       lambda a: (lambda r: (r[0], [float(x) for x in r[1]]))(build_main_frame(*a))),
        "l_arm_slider": (_m_slider, (D, T_Z, WRAP_WALL_Z, chan, bore, shoe), lambda a: (build_l_arm_slider(*a), None)),
        "handle": (_m_handle, (D, T_Z, coup), lambda a: (build_handle(*a), None)),
        "end_stop_pin": (_m_pin, (D["pin"],), lambda a: (build_pin(*a), None)),
        "shoe": (_m_shoe, (shoe, bore["apex_dir"]), lambda a: (build_shoe(*a), None)),
    }
    for h in HW_NAMES:
        spec[h] = (_m_shoe, (shoe, h), lambda a: (build_hardware(a[0])[a[1]], None))
    return spec


def _key(mod, args):
    """The part's cache key, or None (always rebuilt) if an argument cannot be keyed."""
    try:
        return stage_cache.fingerprint((mod,) + _COMMON, args, sorted(Path(IMPORT_DIR).glob("*.dxf")))
    except TypeError as e:
        print(f"  (not cached: {e})")
        return None


def _get(cache, name, mod, args, fn):
    key = _key(mod, args)
    if key is None:
        shp, data = fn(args)
        cache.rebuilt.append(name)
        return shp, data, f"uncached-{os.urandom(8).hex()}"
    shp, data = cache.shape(name, key, lambda: fn(args))
    return shp, data, key


def build_all(wire=WIRE_D, cache=None):
    """Every part and the hardware. With a cache, unchanged parts are loaded, not rebuilt. Returns (parts, info)."""
    cache = cache or open_cache(enabled=False)
    P = parameters(wire)
    D, travel, chan, teeth, bore, coup, shoe = P
    got = {n: _get(cache, n, *s) for n, s in _specs(P).items()}
    frame, a_list = got["main_frame"][0], got["main_frame"][1]
    if [round(a, 9) for a in a_list] != [round(a, 9) for a in shoe["a_list"]]:
        raise RuntimeError("frame notches differ from the notches the shoe was derived on")
    info = {"D": D, "travel": travel, "chan": chan, "teeth": teeth, "bore": bore, "coup": coup,
            "shoe": shoe, "a_list": a_list, "hw": {h: got[h][0] for h in HW_NAMES},
            "keys": {n: g[2] for n, g in got.items()}}
    return {n: got[n][0] for n in PART_NAMES}, info


def rack_notches(D, teeth):
    """Notch positions without building the frame: the same cutter call build_main_frame makes."""
    _, a_list = sawtooth_cutter_face(lambda x: rack_bottom_y(D, x), teeth["x0"], teeth["x1"], teeth["pitch"],
                                     teeth["depth"], teeth["land"], teeth["eps"], teeth["hook"])
    return a_list


def build_one(name, wire=WIRE_D, cache=None):
    """One part only (the others are not built). Returns (shape, key)."""
    cache = cache or open_cache(enabled=False)
    shp, _, key = _get(cache, name, *_specs(parameters(wire))[name])
    return shp, key


def slider_at(slider, travel):
    """Opening pose: the slider moves -X by `travel` (MIN = 0 = the photographed pose)."""
    return slider.moved(Pos(-travel, 0, 0))


def shoe_at(shoe, travel, drop=0.0):
    """Shoe (or hardware) at an opening pose; drop = the release travel (-Y), 0 = locked."""
    return shoe.moved(Pos(-travel, -drop, 0))


def part_path(name, ext, suffix=""):
    folder = OUT_DIR / {"stl": "stl", "step": "step", "png": "renders"}.get(ext, "")
    folder.mkdir(exist_ok=True)
    return folder / f"{PREFIX}_{name}{suffix}.{ext}"


def variant_suffix(name, wire):
    """Output suffix of a part / assembly for a wire variant: the bored parts and the assemblies carry the
    variant's suffix; the shared parts (handle, end_stop_pin, shoe, hardware) never do."""
    suffix = WIRE_VARIANTS[wire][2]
    return suffix if (name in BORE_PARTS or name.startswith("assembly_")) else ""


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


def export_part(name, shp, suffix="", cache=None, key=None):
    """STEP + STL. With a cache and a key, files already written from this key are left alone."""
    step, stl = part_path(name, "step", suffix), part_path(name, "stl", suffix)
    if cache is not None and key and not (cache.needs_write(step, key) or cache.needs_write(stl, key)):
        cache.skip(step)
        cache.skip(stl)
        return
    export_step(shp, str(step))
    export_stl(shp, str(stl), tolerance=TESS_TOL, angular_tolerance=TESS_ANG)
    if cache is not None and key:
        cache.wrote(step, key)
        cache.wrote(stl, key)


def export_stl_keyed(shp, path, cache, key):
    if not cache.needs_write(path, key):
        cache.skip(path)
        return
    export_stl(shp, str(path), tolerance=TESS_TOL, angular_tolerance=TESS_ANG)
    cache.wrote(path, key)


def assembly_key(keys, travel):
    h = hashlib.sha256(repr(sorted(keys.items())).encode() + repr(float(travel)).encode())
    return h.hexdigest()


# ═════════════════════════════════════════════════════════════════════════════
# 5. GENERATE
# ═════════════════════════════════════════════════════════════════════════════

def main_all(wire=WIRE_D, use_cache=True):
    """Default wire: every part, hardware and assembly. Other wire variants: only the bored parts and the assemblies
    (suffixed); the shared parts are built for the assemblies but never written (they stay the default build's).
    With the cache, only changed parts are rebuilt and only files whose inputs changed are rewritten."""
    variant = bool(WIRE_VARIANTS[wire][2])
    cache = open_cache(enabled=use_cache)
    parts, info = build_all(wire, cache)
    keys = info["keys"]
    print(f"wire variant Ø{wire}: bore drawn Ø{info['bore']['d']}, reamed Ø{info['bore']['ream_d']}, suffix "
          f"'{info['bore']['suffix']}'")
    D, chan = info["D"], info["chan"]
    print(f"wire Y {D['wire_y']:.3f}  handle axis X {D['handle_axis_x']:.3f}  ferrule shoulder Y {D['ferrule_top_y']:.3f}"
          f"  bar bottom at axis {D['bar_bottom_at_axis']:.3f}")
    print(f"channel Y {chan['y0']:.3f} .. {chan['y1']:.3f} (frame envelope {chan['envelope'][0]:.3f} .. "
          f"{chan['envelope'][1]:.3f} over X {chan['envelope'][2]:.2f} .. {chan['envelope'][3]:.2f})")
    S = info["shoe"]
    print(f"teeth: {len(info['a_list'])} notches X {info['a_list'][0]:.3f} .. {info['a_list'][-1] + TOOTH_PITCH:.3f};"
          f" shoe teeth in notches {S['k_seat']} (inner a = {S['a_seat'][0]:.3f}) at MIN")
    print(f"shoe: X {S['x0']:.3f}..{S['x1']:.3f} Y {S['y_bot']:.3f}..{S['face']:.3f} (+ teeth {S['tooth_h']:.4f}) Z "
          f"{S['z0']:.2f}..{S['z1']:.2f}; slot X {S['slot']['x0']:.3f}..{S['slot']['x1']:.3f} Y {S['slot']['y0']:.3f}.."
          f"{S['slot']['y1']:.3f}; release travel {S['travel']:.4f}")
    pk, wn, bk, sc, jm = S["pocket"], S["window"], S["block"], S["screw"], S["jam"]
    print(f"pocket X {pk['x0']:.3f}..{pk['x1']:.3f} Y from {pk['y0']:.3f}; window Y {wn['y0']:.3f}..{wn['y1']:.3f}; block "
          f"X {bk['x0']:.3f}..{bk['x1']:.3f} bottom {bk['y0']:.3f}; screw X {sc['x']:.3f} head top {sc['head_top']:.3f} tip "
          f"{sc['tip']:.3f}; jam stack {jm['washer_bot']:.3f}..{jm['top']:.3f}, bore Y {jm['bore_y0']:.3f}..{jm['bore_y1']:.3f};"
          f" engagement lock {S['engage_lock']:.3f} / release {S['engage_rel']:.3f}")
    check_valid(parts)
    check_valid(info["hw"])
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
        if variant and name not in BORE_PARTS:
            continue
        export_part(name, shp, variant_suffix(name, wire), cache, keys[name])
    if not variant:
        for name, shp in info["hw"].items():
            export_stl_keyed(shp, part_path(name, "stl"), cache, keys[name])
    pin = D["pin"]
    added, _, _ = ctip_pad_region(D, D["ctip"])
    print(f"pin: X {pin['x']:.3f} Y {pin['y']:.3f} hole Ø{pin['hole_d']:.2f}; collar face {pin['collar_face']:.3f}; "
          f"travel to pin contact {pin['travel_stop_centred']:.3f} (pin centred) / {pin['travel_stop']:.3f} (pin c/2 "
          f"towards the collar); MAX = {pin['n_max']} teeth = {info['travel']['max']:.3f}; tip gap MAX {D['gap_max']:.3f}")
    print(f"C-tip pad: X {D['ctip']['x_entry']:.3f}..{D['ctip']['x_exit']:.3f}, half-height {D['ctip']['half_h']:.2f}; "
          f"added to the traced outline {added.area:.2f} mm2")
    for pose, t in info["travel"].items():
        an = f"assembly_{pose}"
        path = part_path(an, "stl", variant_suffix(an, wire))
        akey = assembly_key(keys, t)
        if not cache.needs_write(path, akey):
            cache.skip(path)
            continue
        asm = Compound(children=[parts["main_frame"], slider_at(parts["l_arm_slider"], t), parts["handle"],
                                 parts["end_stop_pin"], shoe_at(parts["shoe"], t)]
                       + [shoe_at(h, t) for h in info["hw"].values()])
        export_stl(asm, str(path), tolerance=TESS_TOL, angular_tolerance=TESS_ANG)
        cache.wrote(path, akey)
        print(f"{an}{variant_suffix(an, wire)}: travel {t:.3f} mm written")
    cache.save()
    print(cache.summary())


def main_one(name, wire=WIRE_D, use_cache=True):
    if WIRE_VARIANTS[wire][2] and name not in BORE_PARTS:
        raise SystemExit(f"{name} is shared by every wire variant: build it without --wire")
    cache = open_cache(enabled=use_cache)
    shp, key = build_one(name, wire, cache)
    check_valid({name: shp})
    export_part(name, shp, variant_suffix(name, wire), cache, key)
    cache.save()
    print(cache.summary())
    print(f"{name}: done. Assembly STLs NOT rewritten; run without --part before the gates.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Build SurgicalDrillGuide parts.")
    ap.add_argument("--part", choices=PART_NAMES, help="build and export this part only")
    ap.add_argument("--wire", type=float, default=WIRE_D, choices=sorted(WIRE_VARIANTS),
                    help="wire Ø (default 3.0; 1.5 writes the bored parts and assemblies with the suffix _wire1p5)")
    ap.add_argument("--no-cache", action="store_true", help="rebuild every part and rewrite every file")
    args = ap.parse_args()
    if args.part:
        main_one(args.part, args.wire, not args.no_cache)
    else:
        main_all(args.wire, not args.no_cache)
