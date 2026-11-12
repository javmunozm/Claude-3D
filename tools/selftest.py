"""Self-test of the toolchain: does this machine build, export, gate and render correctly?

Written 2026-11-11, after a disk format. The venv was rebuilt by hand and checked by hand
(docs/system.md), and three faults sat unnoticed until each was run: `python` on PATH had no
packages, the shell hook was not registered, and three skills had frontmatter no YAML parser
accepts. This script runs those checks, and one real pass through every shared tool, in a
temporary folder. Nothing is written into the repo.

    python tools/selftest.py            # one line per check; exit code 1 on any FAIL
    python tools/selftest.py --keep D:/tmp/selftest   # keep the files to look at them

Every gate gets a control it must fail (a two-body mesh, a wrong envelope, a part with a
bump): a check that cannot fail proves nothing. Run it after rebuilding the venv, after an
edit to tools/ or .claude/hooks/, and on any new machine.
"""
import argparse
import contextlib
import importlib.metadata
import io
import json
import math
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(ROOT))
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok)))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f": {detail}" if detail else ""), flush=True)
    return bool(ok)


def run(*args, timeout=300):
    """Run a repo script with this interpreter. Returns (returncode, stdout + stderr)."""
    r = subprocess.run([sys.executable, "-B", *[str(a) for a in args]], capture_output=True, text=True,
                       timeout=timeout, cwd=str(ROOT))
    return r.returncode, r.stdout + "\n" + r.stderr


def last(text, key=None):
    """The first line that contains `key`, or the last non-empty line."""
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    hits = [l for l in lines if key and key in l]
    return (hits[0] if hits else lines[-1] if lines else "")[:160]


def environment():
    venv = (ROOT / ".venv").resolve()
    exe = Path(sys.executable).resolve()
    check("interpreter is the repo venv", venv in exe.parents, str(exe))
    pins = {}
    for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*([A-Za-z0-9_.-]+)==(\S+)", line)
        if m:
            pins[m.group(1)] = m.group(2)
    wrong = []
    for name, want in pins.items():
        try:
            got = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            got = "not installed"
        if got != want:
            wrong.append(f"{name} {got} (pinned {want})")
    check("installed versions match requirements.txt", not wrong, "; ".join(wrong) or f"{len(pins)} packages")


def build(out):
    """A 40 x 30 x 20 block with a through hole of diameter 10, plus a variant with a lump on top."""
    from build123d import Box, Cylinder, Pos, Sphere, Text, export_step, export_stl, extrude, import_step

    part = Box(40, 30, 20) - Cylinder(5, 20)
    want = 40 * 30 * 20 - math.pi * 25 * 20
    check("build123d boolean volume", part.is_valid and len(part.solids()) == 1 and abs(part.volume - want) < 1e-6 * want,
          f"{part.volume:.4f} mm3 against {want:.4f} by hand")
    try:
        glyph = extrude(Text("A", 10), 1)
        check("text extrusion (FontManager patch, docs/system.md)", glyph.volume > 0, f"{glyph.volume:.2f} mm3")
    except Exception as e:
        check("text extrusion (FontManager patch, docs/system.md)", False, f"{type(e).__name__}: {str(e)[:120]}")
    (out / "stl").mkdir(parents=True, exist_ok=True)
    (out / "step").mkdir(exist_ok=True)
    stl, step = out / "stl" / "block.stl", out / "step" / "block.step"
    export_stl(part, str(stl))
    export_step(part, str(step))
    back = import_step(str(step))
    check("STEP export and re-import", abs(back.volume - part.volume) < 1e-6 * want, f"{back.volume:.4f} mm3")
    bumped = out / "stl" / "block_bump.stl"
    export_stl(part + Pos(12, 8, 10) * Sphere(1.5), str(bumped))
    return stl, bumped, want


def gates(out, stl, volume):
    import trimesh

    rc, text = run(TOOLS / "render_check.py", stl, "--views", "front")
    png = out / "renders" / "block_front.png"
    check("render_check on a good part", rc == 0 and png.exists() and "topology gates PASS" in text, last(text, "VERDICT"))
    m = trimesh.load(str(stl))
    check("STL volume equals the solid's", abs(m.volume - volume) < 2e-3 * volume, f"{m.volume:.2f} mm3 (mesh) against {volume:.2f}")
    two = out / "stl" / "two_bodies.stl"
    other = m.copy()
    other.apply_translation([80, 0, 0])
    trimesh.util.concatenate([m, other]).export(str(two))
    rc, text = run(TOOLS / "render_check.py", two)
    check("render_check fails a two-body mesh (control)", rc == 1 and "FAIL" in text, f"rc {rc}")
    rc, text = run(TOOLS / "render_check.py", two, "--expect-bodies", "2")
    check("render_check --expect-bodies 2 passes it", rc == 0, f"rc {rc}")
    rc, text = run(TOOLS / "render_check.py", stl, "--reference", png)
    check("render_check refuses --reference without --views", rc == 2, f"rc {rc}")
    rc, text = run(TOOLS / "render_check.py", stl, "--views", "front", "--reference", png)
    check("render_check --reference writes the side-by-side image", rc == 0 and (out / "renders" / "block_vs_reference.png").exists(), f"rc {rc}")

    rc, text = run(TOOLS / "render_views.py", stl, "--views", "front", "back")
    n = len(list((out / "renders").glob("block__*.png")))
    check("render_views (lit, offscreen)", rc == 0 and n >= 3, f"rc {rc}, {n} images")
    roi = out / "roi.png"
    rc, text = run(TOOLS / "render_roi.py", stl, roi, "--center", "0", "0", "0", "--size", "30")
    check("render_roi", rc == 0 and roi.exists(), f"rc {rc}, {roi.stat().st_size if roi.exists() else 0} bytes")
    rc, text = run(TOOLS / "render_review.py", stl, "--outdir", out / "review", "--views", "front")
    n = len(list((out / "review").glob("*.png"))) if (out / "review").exists() else 0
    check("render_review (smooth + zebra)", rc == 0 and n >= 2, f"rc {rc}, {n} images")

    rc, text = run(TOOLS / "validate_envelope.py", stl, "--spec", "40", "30", "20")
    check("validate_envelope on the true envelope", rc == 0, last(text, "VERDICT"))
    rc, text = run(TOOLS / "validate_envelope.py", stl, "--spec", "40", "40", "40")
    check("validate_envelope fails a wrong envelope (control)", rc == 1, f"rc {rc}")

    from tools.mesh_to_step import triangles_to_shape, write_step
    shape, is_solid, method = triangles_to_shape(m.vertices, m.faces, progress=0)
    check("mesh_to_step", is_solid and method == "direct" and write_step(shape, str(out / "from_mesh.step")),
          f"solid {is_solid}, method {method}")


def sweep(out, stl, bumped):
    reg = out / "regions.json"
    reg.write_text(json.dumps({"thresholds": {"turn": 8.0, "bump": 0.3, "tooth": 0.3}, "symmetric": True}), encoding="utf-8")
    d = out / "sweep"

    def one(mesh, tag, baseline=None):
        args = [TOOLS / "form_sweep.py", mesh, "--regions", reg, "--out", d, "--tag", tag]
        if baseline:
            args += ["--baseline", d / f"sweep_{baseline}.json"]
        rc, text = run(*args)
        js = d / f"sweep_{tag}.json"
        return rc, text, (json.loads(js.read_text(encoding="utf-8")) if js.exists() else {})

    rc, text, a = one(stl, "a")
    check("form_sweep with a thresholds-only regions.json", rc == 0 and len(a.get("reports", {})) >= 7 and len(a.get("unswept", [])) == 3,
          f"rc {rc}, {len(a.get('reports', {}))} tables, {len(a.get('unswept', []))} stages UNSWEPT")
    rc, text, a2 = one(stl, "a", "a")
    check("form_sweep against its own baseline: 0 regressions", rc == 0 and a2.get("regression_components") == 0,
          f"rc {rc}, {a2.get('regression_components')} components")
    rc, text, b = one(bumped, "b", "a")
    check("form_sweep finds the added lump (control)", rc == 0 and (b.get("regression_components") or 0) > 0,
          f"rc {rc}, {b.get('regression_components')} NEW/WORSE components")
    bad = out / "regions_bad.json"
    bad.write_text("{}", encoding="utf-8")
    rc, text = run(TOOLS / "form_sweep.py", stl, "--regions", bad, "--out", d, "--tag", "x")
    check("form_sweep refuses a regions.json without thresholds", rc == 2, f"rc {rc}")


def libraries(out):
    from build123d import Box

    import tools.reconcile as rec
    from tools import stage_cache

    k1 = stage_cache.fingerprint([rec], args=[1.0, "a"])
    k2 = stage_cache.fingerprint([rec], args=[1.0, "a"])
    k3 = stage_cache.fingerprint([rec], args=[1.0000001, "a"])
    cache = stage_cache.Cache(out / "cache")
    calls = []

    def builder():
        calls.append(1)
        return Box(10, 20, 30), {"note": "x"}

    first, _ = cache.shape("box", k1, builder)
    second, side = cache.shape("box", k1, builder)
    check("stage_cache key and reload", k1 == k2 and k1 != k3 and len(calls) == 1 and abs(second.volume - first.volume) < 1e-6
          and side == {"note": "x"}, f"built {len(calls)}x for 2 requests; {cache.summary()}")

    geom = type(sys)("selftest_geom")
    geom.D = 10.0
    sys.modules["selftest_geom"] = geom
    codes = []
    with contextlib.redirect_stdout(io.StringIO()):  # the import warning prints even when quiet: it is meant to be seen
        ok = rec.reconcile("selftest_geom", [("d", 10.0, "D", "neutral")], quiet=True) is True
        ok &= rec.reconcile("selftest_geom", [("d", 9.0, "D", "lower-is-conservative")], quiet=True) is True
        for module, pairs in (("selftest_geom", [("d", 12.0, "D", "lower-is-conservative")]), ("selftest_no_such_module", [])):
            try:
                rec.reconcile(module, pairs, quiet=True)
                codes.append(None)
            except SystemExit as e:
                codes.append(e.code)
        lenient = rec.reconcile("selftest_no_such_module", [], strict=False, quiet=True)
    check("reconcile: match, conservative drift, critical drift, unimportable module",
          ok and codes == [1, 2] and lenient is None, f"exit codes {codes} (want [1, 2]); strict=False returns {lenient!r}")


def harness():
    rc, text = run(ROOT / ".claude/hooks/test_hooks.py")
    check("hook tests (.claude/hooks/test_hooks.py)", rc == 0 and "ALL PASS" in text, last(text))
    try:
        cfg = json.loads((ROOT / ".claude/settings.json").read_text(encoding="utf-8"))
        cmds = [h.get("command", "") for groups in cfg.get("hooks", {}).values() for g in groups for h in g.get("hooks", [])]
        scripts = re.findall(r"[\w./:\\-]*\.claude[/\\]hooks[/\\]\w+\.py", " ".join(cmds))
        missing = [s for s in scripts if not Path(s).exists()]
        ok = any("shell_guard.py" in c for c in cmds) and any("git_state.py" in c for c in cmds) and not missing
        check("hooks registered in .claude/settings.json", ok, f"{len(cmds)} hook commands" + (f"; missing {missing}" if missing else ""))
    except (OSError, ValueError) as e:
        check("hooks registered in .claude/settings.json", False, f"{type(e).__name__}: {e}")
    try:
        import yaml
    except ImportError:
        check("skill frontmatter parses as YAML", False, "PyYAML is not installed in this interpreter")
        return
    bad = []
    skills = sorted((ROOT / ".claude/skills").glob("*/SKILL.md"))
    for p in skills:
        m = re.match(r"---\s*\n(.*?)\n---", p.read_text(encoding="utf-8"), re.S)
        try:
            fm = yaml.safe_load(m.group(1)) if m else None
            if not isinstance(fm, dict) or not fm.get("name") or not fm.get("description"):
                bad.append(f"{p.parent.name}: no name/description")
        except yaml.YAMLError as e:
            bad.append(f"{p.parent.name}: {str(e).splitlines()[0]}")
    check("skill frontmatter parses as YAML", not bad, "; ".join(bad) or f"{len(skills)} skills")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--keep", default=None, help="write the files here and keep them (default: a temporary folder)")
    a = ap.parse_args()
    t0 = time.time()
    tmp = None
    if a.keep:
        out = Path(a.keep).resolve()
        if ROOT in out.parents or out == ROOT:
            ap.error("--keep must be outside the repo")
        out.mkdir(parents=True, exist_ok=True)
    else:
        tmp = tempfile.TemporaryDirectory(prefix="claude3d_selftest_")
        out = Path(tmp.name)
    for step in (environment, lambda: stages(out), harness):
        try:
            step()
        except Exception as e:  # a crash in one group is a FAIL, and the rest still runs
            check(f"{getattr(step, '__name__', 'geometry')} group ran to the end", False, f"{type(e).__name__}: {str(e)[:200]}")
    failed = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)} of {len(RESULTS)} checks pass in {time.time() - t0:.0f} s"
          + (f"; files in {out}" if a.keep else "") + ("" if not failed else "\nFAILED: " + "; ".join(failed)))
    if tmp:
        tmp.cleanup()
    return 1 if failed else 0


def stages(out):
    stl, bumped, volume = build(out)
    gates(out, stl, volume)
    sweep(out, stl, bumped)
    libraries(out)


if __name__ == "__main__":
    sys.exit(main())
