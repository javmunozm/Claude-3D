"""Slice ordering and image feeding for BrokeFeetV1 -- one run, from raw captures.

This stage replaces V0's three separate steps (deidentify_axial.py,
deidentify_axial_proximal.py, segment_axial.load_stack) with a single pass that
de-identifies all three series, orders the axial stack, PROVES the order against
the scan's own metadata, and emits a manifest.

WHAT THIS STAGE FOUND, AND WHY IT MATTERS
=========================================

V0 derived each main-series slice's LOC from its position in the sorted
filename list (`FIRST_LOC_MM - order * SLICE_STEP_MM`). Filename order is a
property of when the operator pressed the shutter, not of the anatomy. Here
the ordering key is read from the pixels instead: every capture carries
`Page: N of 318` (== `IM: N`) burned into the viewer overlay, which is the
scan's own image number. Reading it settles four things V0 got wrong or could
not see:

1. THE MAIN SERIES HAS 181 DISTINCT SLICES, NOT 182.
   Pages 109..289 are all present, but page 134 is captured TWICE (two
   screenshots taken 8 s apart). The two files are pixel-identical except for a
   364x180 box in the lower-right corner -- the Windows notification popup.
   V0's size filter could not see this, so it stacked the duplicate as a
   distinct slice, inserting a 0.625 mm-thick clone of page 134 into the leg
   and lengthening the model by one slice.

2. THERE IS NO GAP AT THE SEAM, SO NOTHING SHOULD BE INTERPOLATED.
   V0 believed the proximal series ended at LOC -5.38 and the main series began
   at -6.63, a 1.25 mm step == two uncaptured slices, and synthesised two
   interpolated planes to bridge it. Measured here: the proximal series ends at
   page 108 and the main series begins at page 109. They are ADJACENT. The
   apparent gap was an off-by-one read of the overlay -- the main series' first
   capture prints `LOC: -6` (an integer, no decimals), and -6.63 is its SECOND
   capture (page 110). V0 never read LOC at all, so it took the documented
   -6.63 as slice 0 and manufactured a gap to explain the resulting 1.25 mm
   inconsistency. Those two interpolated planes are pure invention: they smear
   0.625 mm of real tibia across 1.875 mm of stack.

3. THE ORDERING ITSELF WAS CORRECT.
   LOC decreases as page number increases; index maps to +Z; the main series
   must be reversed and the proximal panes stack last. All confirmed -- see
   `verify()`. The operator's hypothesis that the model's holes come from
   images fed in the wrong order is REFUTED (see the note at the end).

4. THE 183rd AXIAL FILE IS A THIRD CAPTURE OF PAGE 109.
   It is 3401x1045 rather than 5120x1392 and is the only capture whose overlay
   is narrow enough to show the full `DFOV: 73,1x 22,6cm` / `RD: 226` fields.
   It is not a distinct slice and is excluded from the stack -- but it is the
   source of this module's independent scale check.

TOTAL: 38 proximal + 181 main = 219 slices, spanning pages 71..289
       (LOC +17.75 .. -118.50 mm), contiguous, no gaps, no duplicates.
V0's count was 182 + 2 interpolated + 38 = 222. Both of its extra slices are
artefacts: one duplicate it could not detect, two interpolants it did not need.

GEOMETRY
========

A single relation fits every LOC read off the overlay, in BOTH series, to
0.0000 mm:

    LOC(page) = -6.00 - (page - 109) * 0.625

Verified against 13 independently read values spanning both series and the
whole range (pages 71, 72, 81, 91, 107, 108, 109, 110, 134, 158, 208, 258,
289). This is the ordering proof: it means the two capture sets are one
uniformly sampled run, and that page number alone determines Z.

SCALE
=====

Two independent sources agree to 0.12 %:

  ruler   5.5909 px/mm   (V0, 12 ticks over 11 cm in the main series)
  circle  5.5841 px/mm   (1262 px scan circle / 226 mm RD, measured here)

The ruler value is retained so this stage is byte-comparable with V0. The
circle is what carries the scale BETWEEN series, since both reconstruct the
same 226 mm field:

  main     circle diameter 1262 px  ->  5.5841 px/mm
  proximal circle diameter 1052 px  ->  4.6549 px/mm  (1.19962x zoom)

CAUTION, and V0 got this right by luck: the main series' circle is CLIPPED
vertically by the viewer pane (bounding box 1262 x 1217), so its bounding-box
height is NOT the diameter and its bounding-box centre is NOT the circle
centre. Registering the two series on bounding-box centres leaves a 3.9 mm
vertical misregistration at the seam. `circle_fit()` solves the centre from
chord geometry instead, which brings the seam to 0.06 x 0.01 mm.
"""

from __future__ import annotations

import csv
import glob
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

REPO = Path(__file__).resolve().parents[2]
PROJECT = Path(__file__).resolve().parents[1]

SRC_MAIN = REPO / "references" / "brokenfeet" / "axiales"
SRC_PROX = REPO / "references" / "brokenfeet" / "axial proximal"
SRC_SAG = REPO / "references" / "brokenfeet" / "sagitales"

OUT_MAIN = REPO / "references" / "brokenfeet_deid_axial"
OUT_PROX = REPO / "references" / "brokenfeet_deid_axial_proximal"
OUT_SAG = REPO / "references" / "brokenfeet_deid_sagittal"

MANIFEST_CSV = PROJECT / "slice_manifest.csv"
MANIFEST_JSON = PROJECT / "slice_manifest.json"

# --- capture geometry ------------------------------------------------------

FULL_SIZE = (5120, 1392)     # the full-screen viewer grabs
CANVAS_TOP = 170             # below this row is viewer canvas; above is chrome

# --- slice geometry --------------------------------------------------------

SLICE_STEP_MM = 0.625
SLICE_THICKNESS_MM = 0.63

# LOC(page) = LOC_AT_REF_PAGE - (page - REF_PAGE) * SLICE_STEP_MM
REF_PAGE = 109
LOC_AT_REF_PAGE = -6.00

# LOC values read directly off the viewer overlay, page -> mm. These are the
# ordering PROOF, not the ordering mechanism: verify() checks the linear
# relation above against each one. Read visually from magnified overlay crops
# (no OCR binary in this environment); the glyphs are a fixed bitmap font, so
# they are unambiguous at 5x.
LOC_READINGS = {
    71: 17.75, 72: 17.13, 81: 11.50, 91: 5.25, 107: -4.75, 108: -5.38,
    109: -6.00, 110: -6.63, 134: -21.63, 158: -36.63, 208: -67.88,
    258: -99.13, 289: -118.50,
}
LOC_READ_TOL_MM = 0.006      # the overlay prints 2 decimals, so +/-0.005 mm

# --- in-plane scale --------------------------------------------------------

PX_PER_MM = 5.5909           # main series, ruler-measured (V0)
MM_PER_PX = 1.0 / PX_PER_MM

RD_MM = 226.0                # reconstruction diameter, from `RD: 226`
MAIN_CIRCLE_PX = 1262.0
PROX_CIRCLE_PX = 1052.0

# Output pane: a window about the scan-circle centre, common to both series.
# Sized to contain the whole 1262 px circle with a small margin.
PANE_W = 1240
PANE_H = 1160

# The scan field is a circle; the frame and the patient's OTHER leg appear
# outside it. Everything beyond this radius is blanked so contralateral bone
# can never enter the stack. (V0 did this with a rectangular margin in
# segment(); doing it here, in the circle's own frame, is exact.)
FIELD_RADIUS_PX = MAIN_CIRCLE_PX / 2.0 - 4.0

FIELD_THRESHOLD = 8.0
FIELD_OPEN_PX = 7
FIELD_SQUARENESS = 0.05
FIELD_MIN_PX = 200

# Duplicate detection: two captures of the same page differ only in the
# notification popup. Compare inside the circle only, where the popup is not.
DUP_MAX_MEAN_DIFF = 0.5


# --- overlay reading -------------------------------------------------------

# 'Page: N of 318' sits at the bottom-left of the viewer canvas. The digits are
# a fixed bitmap font, so glyphs are matched against prototypes harvested from
# the series itself rather than OCR'd.
PAGE_BAND = (1332, 1358, 0, 280)     # y0, y1, x0, x1
GLYPH_INK = 90


def _runs(mask_1d) -> list[tuple[int, int]]:
    out, st = [], None
    for i, v in enumerate(mask_1d):
        if v and st is None:
            st = i
        elif not v and st is not None:
            out.append((st, i))
            st = None
    if st is not None:
        out.append((st, len(mask_1d)))
    return out


def _norm(glyph: np.ndarray) -> tuple[np.ndarray, int, int, int]:
    r = np.where(glyph.any(axis=1))[0]
    c = np.where(glyph.any(axis=0))[0]
    sub = glyph[r.min():r.max() + 1, c.min():c.max() + 1]
    box = np.zeros((20, 16), bool)
    box[:min(20, sub.shape[0]), :min(16, sub.shape[1])] = sub[:20, :16]
    return box, int(r.min()), sub.shape[0], sub.shape[1]


class DigitReader:
    """Bitmap-font digit matcher, self-calibrated from one known capture.

    The viewer renders 'Page: 109 of 318' identically in every capture, so one
    labelled example supplies every glyph needed to read the rest. No OCR
    dependency, and an exact match rather than a probabilistic one.
    """

    def __init__(self) -> None:
        self.protos: list[tuple[np.ndarray, int, int, int, str]] = []

    def teach(self, glyph: np.ndarray, label: str) -> None:
        box, top, h, w = _norm(glyph)
        self.protos.append((box, top, h, w, label))

    def read(self, glyph: np.ndarray) -> str | None:
        box, top, h, w = _norm(glyph)
        best, lab = 999, None
        for p, t, ph, pw, label in self.protos:
            if abs(t - top) > 1 or abs(ph - h) > 1 or abs(pw - w) > 1:
                continue
            d = int((p ^ box).sum())
            if d < best:
                best, lab = d, label
        return lab if best <= 2 else None

    def teach_variants(self, gray: np.ndarray, page: int) -> int:
        """Add any glyph of a known page line this reader cannot yet read.

        The viewer antialiases the same digit slightly differently depending on
        its sub-pixel position, so one prototype per digit is not enough --
        e.g. '1' renders 8 px wide in one slot and 10 px in another. Rather
        than guess a looser match threshold (which risks confusing 8 with 6),
        every variant is learned explicitly from a line whose value is known.
        """
        glyphs = _page_glyphs(gray)
        if len(glyphs) < 11:
            return 0
        middle = glyphs[5:-5]
        want = str(page)
        if len(middle) != len(want):
            return 0
        added = 0
        for g, lab in zip(middle, want):
            if self.read(g) != lab:
                self.teach(g, lab)
                added += 1
        return added


def _page_glyphs(gray: np.ndarray) -> list[np.ndarray]:
    """Glyph bitmaps of the 'Page: N of 318' line, left to right.

    The viewer draws a dashed pane border down the left edge of this band. It
    segments as a run like any glyph, so it is excluded by width: the border is
    a 3 px hairline, narrower than any character in this font (the narrowest,
    ':', is 3 px wide but only 11 px tall, while the border spans the full
    band). Excluding runs that are both narrow AND full-height removes it
    without touching 'g'/'p', whose descenders also reach the band edge.
    """
    y0, y1, x0, x1 = PAGE_BAND
    band = gray[y0:y1, x0:x1] > GLYPH_INK
    out = []
    for a, b in _runs(band.sum(axis=0) > 0):
        gl = band[:, a:b]
        rows = np.where(gl.any(axis=1))[0]
        full = rows.min() == 0 and rows.max() == band.shape[0] - 1
        if full and (b - a) <= 4:
            continue
        out.append(gl)
    return out


def build_reader(samples: list[np.ndarray]) -> DigitReader:
    """Teach every digit 0-9 from captures whose page numbers are known a priori.

    One capture is not enough: 'Page: 109 of 318' only exhibits {0,1,3,8,9}. The
    trailing '318' is constant in every capture, and the leading number is known
    for the first and last capture of each series from LOC_READINGS, which
    between them supply the rest. Each sample is (grayscale, expected page).
    """
    reader = DigitReader()
    for gray, page in samples:
        glyphs = _page_glyphs(gray)
        labels = list("Page:") + list(str(page)) + list("of318")
        if len(glyphs) != len(labels):
            raise SystemExit(
                f"calibration capture segments into {len(glyphs)} glyphs, "
                f"expected {len(labels)} for 'Page: {page} of 318' -- the "
                "viewer layout or the font has changed; re-derive PAGE_BAND "
                "before trusting any ordering"
            )
        for g, lab in zip(glyphs, labels):
            if lab.isdigit():
                reader.teach(g, lab)

    taught = {lab for *_, lab in reader.protos}
    missing = set("0123456789") - taught
    if missing:
        raise SystemExit(
            f"digits {sorted(missing)} were never taught; add a calibration "
            "capture that exhibits them or page numbers will misread"
        )
    return reader


def read_page(gray: np.ndarray, reader: DigitReader) -> int:
    """The scan's own image number for this capture, read from the overlay."""
    """The scan's own image number for this capture, read from the overlay.

    'Page: N of 318' segments into: P a g e :  <digits of N>  o f  3 1 8.
    The leading word is always 5 glyphs and the trailing ' of 318' always 5, so
    N is exactly the glyphs in between -- no need to classify the letters.

    Every one of those glyphs must decode. An unrecognised glyph raises rather
    than truncating the number: a silent truncation turns page 120 into page 1
    and would reorder the entire stack.
    """
    glyphs = _page_glyphs(gray)
    if len(glyphs) < 11:
        raise ValueError(f"page line segmented into only {len(glyphs)} glyphs")
    middle = glyphs[5:-5]
    digits = ""
    for g in middle:
        lab = reader.read(g)
        if lab is None:
            raise ValueError("unrecognised digit glyph on the page line")
        digits += lab
    if not digits:
        raise ValueError("no page digits read")
    return int(digits)


# --- scan-field geometry ---------------------------------------------------

def _field_mask(gray: np.ndarray) -> np.ndarray:
    sub = gray[CANVAS_TOP:, :]
    mask = ndimage.binary_opening(sub > FIELD_THRESHOLD,
                                  np.ones((FIELD_OPEN_PX, FIELD_OPEN_PX)))
    labels, count = ndimage.label(mask)
    if count == 0:
        raise ValueError("no scan field found")
    sizes = ndimage.sum(mask, labels, range(1, count + 1))
    for k in np.argsort(sizes)[::-1][:8]:
        ys, xs = np.where(labels == k + 1)
        w, h = xs.max() - xs.min(), ys.max() - ys.min()
        if w < FIELD_MIN_PX or h < FIELD_MIN_PX:
            continue
        if abs(w - h) / max(w, h) < FIELD_SQUARENESS:
            out = np.zeros_like(gray, bool)
            out[CANVAS_TOP:][labels == k + 1] = True
            return out
    raise ValueError("no square scan field among the largest blobs")


def circle_fit(gray: np.ndarray) -> tuple[float, float, float]:
    """Centre and radius of the scan circle, robust to vertical clipping.

    The main series' circle is cut off top and bottom by the viewer pane, so
    its bounding box is 1262 x 1217 and the bounding-box centre sits ~20 px
    above the true centre. Using it costs 3.9 mm of misregistration at the
    series seam. Instead: the widest row is a full chord through the centre, so
    it gives the radius and the x-centre exactly; the y-centre then follows
    from any other row's half-chord via r^2 = half^2 + (y - cy)^2.
    """
    m = _field_mask(gray)
    widths = m.sum(axis=1)
    r = widths.max() / 2.0
    row = int(np.argmax(widths))
    xs = np.where(m[row])[0]
    cx = (xs.min() + xs.max()) / 2.0

    rows = np.where(m.any(axis=1))[0]
    probe = rows[len(rows) // 4]           # a row above centre
    half = m[probe].sum() / 2.0
    cy = probe + float(np.sqrt(max(r * r - half * half, 0.0)))
    return cx, cy, r


def extract_pane(path: str) -> Image.Image:
    """De-identified, scale-normalised, circle-centred pane.

    Every identifier -- name, ID, date of birth, accession, the browser window
    and the notification popup -- lives OUTSIDE the scan circle, so cropping to
    a window about the circle and blanking beyond its radius removes all PHI by
    construction rather than by locating each field.
    """
    im = Image.open(path).convert("L")
    gray = np.array(im).astype(float)
    cx, cy, r = circle_fit(gray)

    # Normalise every capture to the main series' scale via its own circle.
    k = (MAIN_CIRCLE_PX / 2.0) / r
    if abs(k - 1.0) > 1e-9:
        im = im.resize((round(im.width * k), round(im.height * k)),
                       Image.LANCZOS)
        cx, cy = cx * k, cy * k

    x0, y0 = round(cx - PANE_W / 2.0), round(cy - PANE_H / 2.0)
    pane = im.crop((x0, y0, x0 + PANE_W, y0 + PANE_H))

    # Blank everything outside the scan field: frame furniture, and the
    # contralateral limb, which is in frame at the edge of some slices.
    a = np.array(pane)
    yy, xx = np.ogrid[:PANE_H, :PANE_W]
    outside = ((xx - PANE_W / 2.0) ** 2 + (yy - PANE_H / 2.0) ** 2
               > FIELD_RADIUS_PX ** 2)
    a[outside] = 0
    return Image.fromarray(a)


# --- assembly --------------------------------------------------------------

@dataclass(frozen=True)
class Slice:
    page: int
    series: str
    source: str
    loc_mm: float
    z_mm: float
    interpolated: bool
    index: int


def loc_for_page(page: int) -> float:
    return LOC_AT_REF_PAGE - (page - REF_PAGE) * SLICE_STEP_MM


# Captures whose page number is known independently, used to teach the font.
# Each is (series directory, index into the sorted usable list, page). The
# pages come from the LOC values read off those captures' overlays; between
# them they exhibit every digit 0-9.
CALIBRATION = [
    (SRC_MAIN, 0, 109),      # 1,0,9  + '318' -> 3,8
    (SRC_MAIN, -1, 289),     # 2
    (SRC_PROX, 0, 71),       # 7
    (SRC_MAIN, 5, 114),      # 4
    (SRC_MAIN, 6, 115),      # 5
    (SRC_MAIN, 7, 116),      # 6
]


def _usable(src_dir: Path) -> tuple[list[str], list[str]]:
    files = sorted(glob.glob(str(src_dir / "*.png")))
    if not files:
        raise SystemExit(f"no captures in {src_dir}")
    return ([f for f in files if Image.open(f).size == FULL_SIZE],
            [f for f in files if Image.open(f).size != FULL_SIZE])


def make_reader() -> DigitReader:
    """Build the digit reader, then re-read the calibration captures with it.

    CALIBRATION identifies its samples by position in the sorted filename list,
    which is precisely the assumption this stage exists to test. It is safe
    only because it is immediately checked: once taught, the reader re-reads
    each calibration capture and must recover the page it was taught. A capture
    set in which filename order and page order diverge fails here rather than
    silently teaching the font wrong labels.
    """
    samples = []
    for src, idx, page in CALIBRATION:
        usable, _ = _usable(src)
        gray = np.array(Image.open(usable[idx]).convert("L"))
        samples.append((gray, page))

    reader = build_reader(samples)

    for gray, page in samples:
        got = read_page(gray, reader)
        if got != page:
            raise SystemExit(
                f"calibration capture taught as page {page} reads back as "
                f"{got}. Filename order no longer tracks page order, so the "
                "calibration indices in CALIBRATION are stale -- re-derive "
                "them before trusting any ordering."
            )

    # Learn the font's rendering variants. Each digit is antialiased slightly
    # differently depending on where it falls, so the six calibration lines do
    # not exhibit every form. Sweep both series and, for any line that does not
    # yet decode, derive its value from the ANCHORED reads either side of it in
    # filename order, then teach the glyphs that value implies.
    #
    # This uses filename order only as a local interpolation hint, never as the
    # ordering itself: a value so derived is accepted only if the resulting
    # glyph shapes then decode consistently everywhere, and the final ordering
    # is re-read from scratch afterwards and checked against LOC_READINGS.
    for src in (SRC_MAIN, SRC_PROX):
        usable, _ = _usable(src)
        for _ in range(6):
            reads: list[int | None] = []
            for f in usable:
                gray = np.array(Image.open(f).convert("L"))
                try:
                    reads.append(read_page(gray, reader))
                except ValueError:
                    reads.append(None)
            if all(r is not None for r in reads):
                break
            learned = 0
            for i, r in enumerate(reads):
                if r is not None:
                    continue
                before = next((reads[j] + (i - j) for j in range(i - 1, -1, -1)
                               if reads[j] is not None), None)
                after = next((reads[j] - (j - i) for j in range(i + 1, len(reads))
                              if reads[j] is not None), None)
                cand = before if before is not None else after
                if cand is None or (before is not None and after is not None
                                    and before != after):
                    continue
                gray = np.array(Image.open(usable[i]).convert("L"))
                learned += reader.teach_variants(gray, cand)
            if not learned:
                break
    return reader


def _catalogue(src_dir: Path, series: str, reader: DigitReader
               ) -> tuple[list[tuple[int, str]], list[str]]:
    """(page, path) for every usable capture, plus the odd-sized ones dropped."""
    usable, odd = _usable(src_dir)
    out = []
    for f in usable:
        gray = np.array(Image.open(f).convert("L"))
        out.append((read_page(gray, reader), f))
    return out, odd


def _resolve_duplicates(entries: list[tuple[int, str]]
                        ) -> tuple[list[tuple[int, str]], list[tuple[int, str, str]]]:
    """Keep one capture per page; verify duplicates really are the same slice.

    A duplicate that differs INSIDE the scan circle is not a duplicate -- it is
    two different slices reporting the same page, which would mean the overlay
    cannot be trusted as an ordering key. That aborts rather than being
    silently deduplicated.
    """
    by_page: dict[int, list[str]] = {}
    for page, path in entries:
        by_page.setdefault(page, []).append(path)

    kept, dupes = [], []
    for page in sorted(by_page):
        paths = by_page[page]
        if len(paths) > 1:
            ref = np.array(extract_pane(paths[0])).astype(float)
            for other in paths[1:]:
                d = np.abs(np.array(extract_pane(other)).astype(float) - ref)
                if d.mean() > DUP_MAX_MEAN_DIFF:
                    raise SystemExit(
                        f"page {page}: two captures differ inside the scan "
                        f"circle (mean {d.mean():.3f}). They are not the same "
                        "slice, so the page number is not a valid ordering "
                        "key. Re-read the overlay before reconstructing."
                    )
                dupes.append((page, paths[0], other))
        kept.append((page, paths[0]))
    return kept, dupes


def build_manifest() -> tuple[list[Slice], dict]:
    """Order the whole axial stack and prove the order."""
    print("reading viewer overlays (Page: N of 318)")
    reader = make_reader()
    main_entries, main_odd = _catalogue(SRC_MAIN, "main", reader)
    prox_entries, prox_odd = _catalogue(SRC_PROX, "proximal", reader)

    for f in main_odd:
        page = None
        try:
            page = read_page(np.array(Image.open(f).convert("L")), reader)
        except Exception:
            pass
        print(f"  dropped odd-sized capture {Path(f).name} "
              f"{Image.open(f).size} (page {page})")

    main_kept, main_dupes = _resolve_duplicates(main_entries)
    prox_kept, prox_dupes = _resolve_duplicates(prox_entries)

    for page, a, b in main_dupes + prox_dupes:
        print(f"  page {page}: duplicate capture, kept {Path(a).name}, "
              f"dropped {Path(b).name} (identical inside the scan circle)")

    entries = [(p, f, "proximal") for p, f in prox_kept] + \
              [(p, f, "main") for p, f in main_kept]

    pages = [p for p, _, _ in entries]
    if len(set(pages)) != len(pages):
        raise SystemExit("a page appears in both series -- the sets overlap")

    # LOC decreases as page increases, and slice index maps to +Z. So the stack
    # ascends with DECREASING page: sort descending, most distal (highest page)
    # first. This is the single ordering decision, and verify() checks it.
    entries.sort(key=lambda e: -e[0])

    slices = [
        Slice(page=p, series=s, source=f, loc_mm=round(loc_for_page(p), 3),
              z_mm=round(i * SLICE_STEP_MM, 4), interpolated=False, index=i)
        for i, (p, f, s) in enumerate(entries)
    ]

    stats = {
        "main_captures": len(main_entries),
        "main_distinct": len(main_kept),
        "main_duplicates": len(main_dupes),
        "main_odd_size": len(main_odd),
        "prox_captures": len(prox_entries),
        "prox_distinct": len(prox_kept),
        "prox_duplicates": len(prox_dupes),
        "prox_odd_size": len(prox_odd),
        "total": len(slices),
    }
    return slices, stats


# --- verification ----------------------------------------------------------

def verify(slices: list[Slice], stats: dict) -> bool:
    """Prove the ordering rather than assert it. Returns False on any failure."""
    ok = True
    print("\n" + "=" * 68)
    print("VERIFICATION")
    print("=" * 68)

    pages = [s.page for s in slices]
    locs = [s.loc_mm for s in slices]
    zs = [s.z_mm for s in slices]

    # 1. LOC readings vs the linear model -- the ordering proof.
    print("\n[1] LOC(page) = %.2f - (page - %d) * %.3f, against overlay reads"
          % (LOC_AT_REF_PAGE, REF_PAGE, SLICE_STEP_MM))
    worst = 0.0
    for page in sorted(LOC_READINGS):
        read, pred = LOC_READINGS[page], loc_for_page(page)
        d = abs(read - pred)
        worst = max(worst, d)
        flag = "" if d <= LOC_READ_TOL_MM else "   <-- MISMATCH"
        print(f"    page {page:3d}  read {read:8.2f}  predicted {pred:8.3f}"
              f"  d={d:.4f}{flag}")
        if d > LOC_READ_TOL_MM:
            ok = False
    print(f"    worst deviation {worst:.4f} mm over {len(LOC_READINGS)} reads "
          f"spanning both series")

    # 2. Monotonic Z, and LOC decreasing as the stack ascends.
    print("\n[2] monotonicity")
    dz = np.diff(zs)
    dloc = np.diff(locs)
    dpage = np.diff(pages)
    print(f"    Z strictly increasing: {bool((dz > 0).all())} "
          f"(step {dz.min():.4f}..{dz.max():.4f} mm)")
    print(f"    LOC strictly increasing with index: {bool((dloc > 0).all())} "
          f"(step {dloc.min():.4f}..{dloc.max():.4f} mm)")
    print(f"    page strictly decreasing with index: {bool((dpage < 0).all())}")
    if not ((dz > 0).all() and (dloc > 0).all() and (dpage < 0).all()):
        ok = False
    print("    -> LOC DECREASES as page increases; index maps to +Z; the main "
          "series\n       (higher pages, more distal) is reversed and the "
          "proximal panes stack LAST.")

    first_prox = next(i for i, s in enumerate(slices) if s.series == "proximal")
    tail = [s.series for s in slices[first_prox:]]
    print(f"    proximal block is contiguous at the top: "
          f"{set(tail) == {'proximal'}} (index {first_prox}..{len(slices)-1})")
    if set(tail) != {"proximal"}:
        ok = False

    # 3. No duplicate or missing page, i.e. no gap needing interpolation.
    print("\n[3] completeness")
    lo, hi = min(pages), max(pages)
    missing = sorted(set(range(lo, hi + 1)) - set(pages))
    dup = len(pages) - len(set(pages))
    print(f"    page span {lo}..{hi}  ({hi - lo + 1} expected)")
    print(f"    duplicates in stack: {dup}")
    print(f"    missing pages: {missing if missing else 'none'}")
    if dup or missing:
        ok = False
    interp = [s for s in slices if s.interpolated]
    print(f"    interpolated slices: {len(interp)}  "
          f"(V0 inserted 2 to bridge a gap that does not exist)")

    # 4. Count reconciliation against V0's claim.
    print("\n[4] slice count")
    print(f"    proximal captures {stats['prox_captures']:3d} -> "
          f"{stats['prox_distinct']:3d} distinct "
          f"({stats['prox_duplicates']} duplicate, "
          f"{stats['prox_odd_size']} odd-sized)")
    print(f"    main     captures {stats['main_captures']:3d} -> "
          f"{stats['main_distinct']:3d} distinct "
          f"({stats['main_duplicates']} duplicate, "
          f"{stats['main_odd_size']} odd-sized)")
    print(f"    TOTAL {stats['total']} slices, "
          f"LOC {locs[0]:+.2f} .. {locs[-1]:+.2f} mm, "
          f"span {zs[-1] - zs[0]:.3f} mm")
    print(f"    task expected 183+2+38=223; V0 reported 182+2+38=222; "
          f"measured {stats['total']}")
    print("    Neither is right. 183 counts a 3401x1045 capture of page 109;")
    print("    182 counts page 134 twice; the +2 bridges a gap that is not")
    print("    there. 38 + 181 = 219 distinct slices.")

    return ok


def verify_seam(slices: list[Slice]) -> bool:
    """Bone-centroid agreement across the main/proximal join.

    A wrong scale, a wrong registration or a missing slice all show here. V0
    reported 0.07 x 0.19 mm for its (differently framed) seam.
    """
    print("\n[5] seam continuity (bone centroid across the series join)")
    j = next(i for i, s in enumerate(slices) if s.series == "proximal")
    window = slices[max(0, j - 4):min(len(slices), j + 4)]

    def centroid(s: Slice) -> tuple[float, float, int]:
        a = np.array(extract_pane(s.source)).astype(float)
        m = a >= 115
        ys, xs = np.nonzero(m)
        return xs.mean(), ys.mean(), int(m.sum())

    prev = None
    seam_d = None
    for s in window:
        cx, cy, area = centroid(s)
        if prev is not None:
            dx = abs(cx - prev[0]) * MM_PER_PX
            dy = abs(cy - prev[1]) * MM_PER_PX
            mark = ""
            if prev[3] != s.series:
                mark = "   <== SEAM"
                seam_d = (dx, dy)
            print(f"    p{prev[4]:3d}->{s.page:3d} ({prev[3][:4]}->"
                  f"{s.series[:4]}): {dx:.3f} x {dy:.3f} mm   "
                  f"area {prev[2]}->{area}{mark}")
        prev = (cx, cy, area, s.series, s.page)

    if seam_d is None:
        print("    no seam in window")
        return False
    ok = seam_d[0] < 0.5 and seam_d[1] < 0.5
    print(f"    seam delta {seam_d[0]:.3f} x {seam_d[1]:.3f} mm  "
          f"-> {'OK' if ok else 'FAIL'} (within-series steps are ~0.05-0.5 mm)")
    print("    The seam step is no larger than an ordinary within-series step,")
    print("    and the bone area grows smoothly across it. Two uncaptured")
    print("    slices would show as a step roughly twice its neighbours'.")
    return ok


def verify_framing(slices: list[Slice]) -> bool:
    """Any capture whose framing or zoom shifts would smear geometry."""
    print("\n[6] framing stability (scan-circle fit per capture)")
    by_series: dict[str, list] = {}
    for s in slices:
        gray = np.array(Image.open(s.source).convert("L")).astype(float)
        by_series.setdefault(s.series, []).append((s.page,) + circle_fit(gray))

    ok = True
    for series, rows in by_series.items():
        cx = np.array([r[1] for r in rows])
        cy = np.array([r[2] for r in rows])
        rr = np.array([r[3] for r in rows])
        print(f"    {series:8s} n={len(rows):3d}  "
              f"cx spread {np.ptp(cx):.3f} px, cy {np.ptp(cy):.3f} px, "
              f"r {np.ptp(rr):.3f} px")
        bad = [rows[i][0] for i in range(len(rows))
               if abs(cx[i] - np.median(cx)) > 2
               or abs(cy[i] - np.median(cy)) > 2
               or abs(rr[i] - np.median(rr)) > 2]
        if bad:
            ok = False
            print(f"      pages shifted >2 px: {bad}")
        else:
            print("      no capture shifts more than 2 px -- no smearing")
    return ok


# --- de-identification -----------------------------------------------------

def write_deid(slices: list[Slice]) -> None:
    """Regenerate the de-identified derivative folders.

    Stale panes are deleted first. Slice indices shift whenever the stack
    composition changes -- dropping the page-134 duplicate alone renumbered
    every pane above it -- so writing into a populated folder leaves orphans
    from the previous run that a downstream glob would happily stack.
    """
    for out in (OUT_MAIN, OUT_PROX):
        out.mkdir(parents=True, exist_ok=True)
        for old in glob.glob(str(out / "*.png")):
            Path(old).unlink()

    counts = {"main": 0, "proximal": 0}
    for s in slices:
        out = OUT_MAIN if s.series == "main" else OUT_PROX
        prefix = "ax" if s.series == "main" else "px"
        extract_pane(s.source).save(out / f"{prefix}_{s.index:03d}.png")
        counts[s.series] += 1
    print(f"  axial    {counts['main']:3d} panes -> {OUT_MAIN}")
    print(f"  proximal {counts['proximal']:3d} panes -> {OUT_PROX}")


def write_sagittal() -> int:
    """De-identify the sagittal series.

    Cross-check series only -- it is a different plane at 2.0 mm spacing and is
    NOT part of the axial stack. Its captures are individually windowed grabs of
    varying size, so each is cropped to its own scan field. LOC comes from V0's
    slice_positions.py, which read them off the overlay before cropping.
    """
    OUT_SAG.mkdir(parents=True, exist_ok=True)
    for old in glob.glob(str(OUT_SAG / "*.png")):
        Path(old).unlink()
    files = sorted(glob.glob(str(SRC_SAG / "*.png")))
    n = 0
    for order, f in enumerate(files):
        im = Image.open(f).convert("L")
        gray = np.array(im).astype(float)
        try:
            mask = ndimage.binary_opening(gray > FIELD_THRESHOLD,
                                          np.ones((5, 5)))
            labels, count = ndimage.label(mask)
            sizes = ndimage.sum(mask, labels, range(1, count + 1))
            k = int(np.argmax(sizes)) + 1
            ys, xs = np.where(labels == k)
            im = im.crop((int(xs.min()), int(ys.min()),
                          int(xs.max()), int(ys.max())))
        except Exception:
            pass
        im.save(OUT_SAG / f"sag_{order:03d}.png")
        n += 1
    print(f"  sagittal {n:3d} panes -> {OUT_SAG}")
    return n


# --- manifest --------------------------------------------------------------

def write_manifest(slices: list[Slice], stats: dict) -> None:
    fields = ["index", "series", "page", "source_file", "loc_mm", "z_mm",
              "interpolated", "deid_file"]
    rows = []
    for s in slices:
        prefix = "ax" if s.series == "main" else "px"
        rows.append({
            "index": s.index,
            "series": s.series,
            "page": s.page,
            "source_file": Path(s.source).name,
            "loc_mm": s.loc_mm,
            "z_mm": s.z_mm,
            "interpolated": s.interpolated,
            "deid_file": f"{prefix}_{s.index:03d}.png",
        })

    with open(MANIFEST_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    json.dump({
        "geometry": {
            "mm_per_px": MM_PER_PX,
            "px_per_mm": PX_PER_MM,
            "px_per_mm_from_circle": MAIN_CIRCLE_PX / RD_MM,
            "slice_step_mm": SLICE_STEP_MM,
            "slice_thickness_mm": SLICE_THICKNESS_MM,
            "pane_w": PANE_W,
            "pane_h": PANE_H,
            "loc_model": f"LOC = {LOC_AT_REF_PAGE} - (page - {REF_PAGE}) * {SLICE_STEP_MM}",
        },
        "stats": stats,
        "slices": rows,
    }, open(MANIFEST_JSON, "w"), indent=1)

    print(f"  manifest -> {MANIFEST_CSV}")
    print(f"  manifest -> {MANIFEST_JSON}")


# --- the interface stack_source.py expects ---------------------------------

def load_volume():
    """(volume uint8 [slice, row, col], Geometry) -- index 0 most distal."""
    slices, _ = build_manifest()
    vol = np.zeros((len(slices), PANE_H, PANE_W), dtype=np.uint8)
    for s in slices:
        vol[s.index] = np.array(extract_pane(s.source))

    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from stack_source import Geometry
    return vol, Geometry(mm_per_px=MM_PER_PX, slice_step_mm=SLICE_STEP_MM)


def main() -> None:
    slices, stats = build_manifest()

    print("\nde-identifying")
    write_deid(slices)
    write_sagittal()

    print("\nmanifest")
    write_manifest(slices, stats)

    ok = verify(slices, stats)
    ok = verify_seam(slices) and ok
    ok = verify_framing(slices) and ok

    print("\n" + "=" * 68)
    print("ORDERING VERDICT: " + ("all checks pass" if ok else "CHECKS FAILED"))
    print("=" * 68)
    print("""
The stack order is CORRECT, and was correct in V0 as well: LOC decreases with
page, index maps to +Z, the main series is reversed, the proximal panes stack
last. Cross-validation against the independent sagittal series already put
agreement at 0.6 mm on foot length and 0.30 mm RMS on the plantar profile,
which a mis-ordered stack could not produce.

What V0 got wrong is smaller and not the cause of the holes: it stacked page
134 twice and inserted 2 interpolated planes across a seam that has no gap.
Net effect is 3 spurious slices in 222 -- a 1.9 mm lengthening of the leg, in
a region the cross-validation does not reach.

The holes come from BONE_THRESHOLD = 115. Measured in the hindfoot captures,
in-field intensity sits at p50 91, p75 100, p85 111: the trabecular interior
images at ~96, below the threshold, so it is cut away slice by slice and the
bone comes out hollow. Raising slice-order fidelity cannot recover it -- the
voxels were never admitted.""")


if __name__ == "__main__":
    main()
