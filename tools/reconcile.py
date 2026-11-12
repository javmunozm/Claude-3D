"""
reconcile.py — detect drift between a structural check and its geometry source
==============================================================================
`docs/architecture.md` deliberately keeps verification scripts decoupled from
the geometry scripts (no build123d import) so a check can run without a CAD
environment installed. The cost of that decision is that the two files are
"kept in sync by hand" — and hand-sync fails silently.

It DID fail. BedLifter's structural_check.py was found validating a 9.332
degree design while the geometry script built 8.850 degrees, with five other
mismatched inputs including a collar diameter overstated by more than 2x
(a NON-conservative error, so the check passed a design it should have
questioned). Nothing in the workflow surfaced this, because both scripts ran
successfully on their own.

This module keeps the decoupling but makes the drift visible: a check script
declares the geometry values it assumes, and this compares them against the
values actually computed by the geometry module.

Usage in a structural check
---------------------------
    from tools.reconcile import reconcile

    reconcile(
        geometry_module="BedLifter.macros.bed_lifter_b123d",   # (BedLifter was removed 2026-11-11; the shape holds)
        pairs=[
            # (label, value used here, name in the geometry module, direction)
            ("tilt angle (deg)",   ANGLE_DEG,   "ANGLE_DEG",     "neutral"),
            ("head top rod dia",   10.0,        ("WHEEL_TOP_R", lambda r: r * 2), "lower-is-conservative"),
        ],
    )

`direction` tells the reader which way an error cuts:
    "higher-is-conservative"  — using a value above the true one is safe
    "lower-is-conservative"   — using a value below the true one is safe
    "neutral"                 — any mismatch is simply wrong

Any mismatch is reported. Non-conservative mismatches are marked CRITICAL,
because those are the ones that let an inadequate design pass.
"""

import importlib
import math
import sys


TOL = 1e-6


def _resolve(module, spec):
    """spec is either an attribute name, or (attr_name, transform_fn)."""
    if isinstance(spec, tuple):
        name, fn = spec
        return fn(getattr(module, name)), name
    return getattr(module, spec), spec


def _is_conservative(used, actual, direction):
    """True if the deviation errs on the safe side."""
    if direction == "higher-is-conservative":
        return used > actual
    if direction == "lower-is-conservative":
        return used < actual
    return False


def reconcile(geometry_module, pairs, strict=True, quiet=False):
    """Compare values used in a check against the geometry module's own values.

    Returns True if everything matches. If `strict` (the default), raises
    SystemExit on a non-conservative mismatch, and also when the geometry module
    cannot be imported, so a stale or unreconciled check cannot go on to print
    PASS. With `strict=False` an import failure returns None after a warning:
    the caller must then report its verdict as unverified.

    The import failure was a silent skip until 2026-11-11. On 2026-10-17 the
    `python` on PATH had no build123d, every pair was skipped, and the checks
    printed their verdicts as usual (docs/system.md, "Python environment").
    """
    try:
        mod = importlib.import_module(geometry_module)
    except Exception as exc:
        print(f"  [WARN]  cannot import {geometry_module} ({exc.__class__.__name__}: {exc})")
        print("          reconciliation SKIPPED — values below are unverified.")
        print("          Run with the repo venv (it has build123d), or verify these by hand against the source.")
        if strict:
            print("=" * 70)
            print("RECONCILIATION NOT RUN: no verdict below this line would be reconciled.")
            print("  Fix the import, or call reconcile(..., strict=False) and report the verdict as unverified.")
            print("=" * 70)
            sys.exit(2)
        return None

    rows = []
    for label, used, spec, direction in pairs:
        try:
            actual, attr = _resolve(mod, spec)
        except AttributeError:
            rows.append(("MISSING", label, used, None, "", f"no such attribute: {spec}"))
            continue

        if isinstance(actual, float) and isinstance(used, (int, float)):
            match = math.isclose(used, actual, rel_tol=1e-6, abs_tol=TOL)
        else:
            match = used == actual

        if match:
            rows.append(("OK", label, used, actual, attr, ""))
        else:
            safe = _is_conservative(used, actual, direction)
            status = "DRIFT" if safe else "CRITICAL"
            note = ("deviation is conservative" if safe
                    else "deviation is NOT conservative — check may pass an inadequate design")
            rows.append((status, label, used, actual, attr, note))

    if not quiet:
        print("-" * 70)
        print(f"Reconciliation against {geometry_module}")
        print("-" * 70)
        for status, label, used, actual, attr, note in rows:
            u = f"{used:.4g}" if isinstance(used, (int, float)) else str(used)
            a = f"{actual:.4g}" if isinstance(actual, (int, float)) else str(actual)
            print(f"  [{status:<8}] {label:<28} check={u:<10} geometry={a:<10} ({attr})")
            if note:
                print(f"             -> {note}")
        print()

    critical = [r for r in rows if r[0] in ("CRITICAL", "MISSING")]
    drift = [r for r in rows if r[0] == "DRIFT"]

    if critical:
        msg = (f"RECONCILIATION FAILED: {len(critical)} value(s) disagree with the "
               f"geometry source in a non-conservative direction.")
        if not quiet:
            print("=" * 70)
            print(msg)
            print("  Fix the check's inputs to match the geometry before trusting")
            print("  any PASS verdict below.")
            print("=" * 70)
        if strict:
            sys.exit(1)
        return False

    if drift and not quiet:
        print(f"  {len(drift)} conservative deviation(s) — check verdict remains valid.\n")

    return not critical
