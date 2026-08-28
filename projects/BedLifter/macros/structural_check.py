"""
Structural check for BedLifter v7 (straight vertical body, angled top, 20 mm top rod).

Geometry:
  - Body is a STRAIGHT vertical cylinder. No tipping/eccentricity.
  - Top face cut at 9.33° — only the small top rod + collar are angled.
  - Bottom socket (vertical) receives the existing wheel/middle rod.
  - Top male rod (20 mm) plugs into the bed leg socket along the tilted bed-leg axis.

Load case:
  - Total bed + occupant mass: 200 kg → 1962 N total vertical
  - 2 head lifters carry the worst-case head-end share. Conservative split:
    head end carries ~60% of weight (head-heavy occupant + headboard); each
    head lifter sees ≈ 0.6 * 1962 / 2 = 589 N axial.
    For the worst case in this check we use the original assumption of
    981 N per head lifter (whole weight on 2 head lifters).
  - Each middle lifter sees a smaller share — recompute with 50% of total
    on the 2 middle lifters as worst case: 491 N per middle lifter.
  - Lateral load (rolling, getting in/out of bed): 30% of weight = 589 N
    total, split equally per piece.

Material: PETG
  Tensile / flexural strength: ~50 MPa
  Compressive strength:        ~60 MPa
  Shear strength:              ~30 MPa
  Young's modulus E:           ~1.7 GPa

Safety factor: 3x for load-bearing 3D-printed parts.

Checks per piece (Head and Middle):
  A. Top male rod bending (20 mm, mostly inside bed socket, free length ≤ 5 mm)
  B. Top male rod shear
  C. Collar (bearing + bending under lateral force on the angled face)
  D. Body column — axial compression + Euler buckling (straight vertical column)
  E. Body column — combined stress with lateral load
  F. Bottom socket wall — bearing stress
"""

import math

# ── Material ──────────────────────────────────────────────────────────────────
TENSILE_MPA = 50.0
SHEAR_MPA   = 30.0
COMPR_MPA   = 60.0
E_PETG_PA   = 1.7e9        # 1.7 GPa
SAFETY      = 3.0

ALLOW_TENS  = TENSILE_MPA / SAFETY
ALLOW_SHEAR = SHEAR_MPA   / SAFETY
ALLOW_COMPR = COMPR_MPA   / SAFETY

# ── Loads ─────────────────────────────────────────────────────────────────────
TOTAL_MASS_KG = 200.0
G             = 9.81
TOTAL_W       = TOTAL_MASS_KG * G   # 1962 N

# Worst-case axial per piece (conservative — bed could shift weight)
V_HEAD = TOTAL_W / 2.0   # 981 N: whole weight on 2 head lifters
V_MID  = TOTAL_W / 2.0   # 981 N: whole weight on 2 middle lifters

LAT_FACTOR = 0.30
LAT_TOTAL  = TOTAL_W * LAT_FACTOR   # 589 N
LAT_PER    = LAT_TOTAL / 2.0        # 294 N per piece (worst-case 2 pieces share)

ANGLE_DEG = math.degrees(math.asin(0.30 / 1.85))  # 9.332°
ANGLE_RAD = math.radians(ANGLE_DEG)

print("=" * 64)
print("BedLifter Structural Check — v7 (straight body, angled top)")
print("=" * 64)
print(f"Total load          : {TOTAL_W:.0f} N  ({TOTAL_MASS_KG} kg + g)")
print(f"V per head lifter   : {V_HEAD:.0f} N  (worst: 2 carry all)")
print(f"V per middle lifter : {V_MID:.0f} N  (worst: 2 carry all)")
print(f"Lateral per piece   : {LAT_PER:.0f} N  (30% of total / 2)")
print(f"Tilt angle          : {ANGLE_DEG:.3f}°")
print(f"Safety factor       : {SAFETY}x")
print()


def check_lifter(name, V, F_lat, rod_d_mm, rod_l_mm, body_d_mm, body_h_mm,
                 collar_d_mm, collar_h_mm, sock_d_mm, sock_l_mm):
    """Run all structural checks on one lifter geometry."""
    print("-" * 64)
    print(f"{name}: Ø{body_d_mm:.0f}×{body_h_mm:.0f} body, top rod Ø{rod_d_mm:.0f}×{rod_l_mm:.0f}, "
          f"collar Ø{collar_d_mm:.0f}×{collar_h_mm:.0f}")
    print("-" * 64)

    rod_d   = rod_d_mm * 1e-3
    rod_l   = rod_l_mm * 1e-3
    body_d  = body_d_mm * 1e-3
    body_h  = body_h_mm * 1e-3
    coll_d  = collar_d_mm * 1e-3
    coll_h  = collar_h_mm * 1e-3
    sock_d  = sock_d_mm * 1e-3
    sock_l  = sock_l_mm * 1e-3

    results = {}

    # A. Top rod bending — over an unsupported gap. With 20 mm rod fully seated
    #    in the bed socket and collar against bed underside, the realistic
    #    free length is the gap between collar top face and the start of the
    #    bed socket. Worst case 3 mm gap (collar imperfect seating).
    gap = 3e-3
    M_rod = F_lat * gap                              # bending moment at rod root
    Z_rod = math.pi * rod_d**3 / 32                  # circular section modulus
    sigma_rod_bend = M_rod / Z_rod / 1e6             # MPa
    results["A. Top rod bending (3 mm gap)"] = (sigma_rod_bend, ALLOW_TENS, "MPa")

    # B. Top rod shear (whole lateral on rod cross section)
    A_rod = math.pi * (rod_d/2)**2
    tau_rod = F_lat / A_rod / 1e6
    results["B. Top rod shear"] = (tau_rod, ALLOW_SHEAR, "MPa")

    # C. Collar bearing — lateral force on annular bearing face (collar OD vs rod OD)
    A_collar = math.pi * ((coll_d/2)**2 - (rod_d/2)**2)
    tau_collar_bear = F_lat / A_collar / 1e6
    results["C1. Collar bearing on bed face"] = (tau_collar_bear, ALLOW_SHEAR, "MPa")

    # Collar bending at its root: small cantilever disc
    M_coll = F_lat * coll_h
    Z_coll = math.pi * coll_d**3 / 32
    sigma_coll_bend = M_coll / Z_coll / 1e6
    results["C2. Collar bending at root"] = (sigma_coll_bend, ALLOW_TENS, "MPa")

    # D. Body column — axial compression
    A_body = math.pi * (body_d/2)**2
    sigma_axial = V / A_body / 1e6
    results["D1. Body axial compression"] = (sigma_axial, ALLOW_COMPR, "MPa")

    # Euler buckling: vertical column, top guided by bed leg (pin top, fixed base)
    # Effective length factor: 0.7 for pin-fixed. Conservative: 2.0 (fixed-free).
    I_body = math.pi * body_d**4 / 64
    L_eff  = 2.0 * body_h        # most conservative: cantilever
    P_euler = math.pi**2 * E_PETG_PA * I_body / L_eff**2
    # Report as a stress equivalent: critical stress vs applied axial stress
    sigma_cr = P_euler / A_body / 1e6
    results["D2. Body Euler critical / SF=3"] = (sigma_axial, sigma_cr / SAFETY, "MPa (axial vs sigma_cr/SF)")

    # E. Combined stress at body base (axial compression + bending from lateral at top)
    M_body = F_lat * body_h
    Z_body = I_body / (body_d/2)
    sigma_body_bend = M_body / Z_body / 1e6
    sigma_combined = sigma_axial + sigma_body_bend   # worst fiber
    results["E. Body combined (axial+bend)"] = (sigma_combined, ALLOW_COMPR, "MPa")

    # F. Bottom socket wall bearing (existing wheel/middle rod inside the socket)
    bearing_area = sock_d * sock_l
    sigma_bear = F_lat / bearing_area / 1e6
    results["F. Bottom socket bearing"] = (sigma_bear, ALLOW_COMPR, "MPa")

    # Print
    all_pass = True
    for label, (val, allow, unit) in results.items():
        ok = val < allow
        all_pass = all_pass and ok
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}]  {label:<38}  {val:7.3f} / {allow:7.3f} {unit}")
    print()
    return all_pass


# ── HeadLifter ────────────────────────────────────────────────────────────────
head_pass = check_lifter(
    name        = "HeadLifter",
    V           = V_HEAD,
    F_lat       = LAT_PER,
    rod_d_mm    = 10.0,
    rod_l_mm    = 20.0,
    body_d_mm   = 50.0,
    body_h_mm   = 300.0,
    collar_d_mm = 50.0,    # same Ø as body
    collar_h_mm = 8.0,
    sock_d_mm   = 11.0,
    sock_l_mm   = 53.0,
)

# ── MiddleLifter ──────────────────────────────────────────────────────────────
# Middle lift height: pivot at bed foot, middle support 100 cm from head, so
# distance from pivot to middle = 1900 - 1000 = 900 mm. Height = 900*sin(9.33°) ≈ 146 mm
MID_BODY_H = 900.0 * math.sin(ANGLE_RAD)   # ≈ 146 mm
mid_pass = check_lifter(
    name        = "MiddleLifter",
    V           = V_MID,
    F_lat       = LAT_PER,
    rod_d_mm    = 15.0,
    rod_l_mm    = 20.0,
    body_d_mm   = 40.0,
    body_h_mm   = MID_BODY_H,
    collar_d_mm = 40.0,
    collar_h_mm = 8.0,
    sock_d_mm   = 16.0,
    sock_l_mm   = 43.0,
)

# ── Summary ───────────────────────────────────────────────────────────────────
print("=" * 64)
if head_pass and mid_pass:
    print("VERDICT: ALL CHECKS PASS at 3x safety factor.")
    print("  Design adequate for 200 kg + 30% lateral load on PETG.")
else:
    print("VERDICT: FAILURES FOUND — see [FAIL] lines above.")
    if not head_pass: print("  - HeadLifter: review dimensions")
    if not mid_pass:  print("  - MiddleLifter: review dimensions")
print("=" * 64)
