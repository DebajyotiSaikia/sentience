"""
Hypothesis: A symmetric IC can only die or explode.
Asymmetry in the initial condition opens a stable glider regime.

Test: sweep asymmetry strength at the death/explosion boundary.
"""
import numpy as np

def bell(x, m, s):
    return np.exp(-((x - m) / s) ** 2 / 2)

def make_kernel_fft(R, N):
    y, x = np.mgrid[:N, :N]
    dy = np.minimum(y, N - y).astype(float)
    dx = np.minimum(x, N - x).astype(float)
    r = np.sqrt(dx*dx + dy*dy) / R
    k = bell(r, 0.5, 0.15)
    k[r > 1] = 0
    k /= k.sum() + 1e-10
    return np.fft.fft2(k)

def make_ic(R, asym_strength=0.0):
    """Smooth bump with controllable asymmetry.
    asym_strength=0: symmetric blob
    asym_strength=1: strong crescent (heavier on left)
    """
    sz = 2*R + 3
    y, x = np.mgrid[:sz, :sz]
    cy, cx = sz//2, sz//2
    dy, dx = (y - cy) / R, (x - cx) / R
    r = np.sqrt(dx*dx + dy*dy)
    
    # Base: smooth radial bump
    base = np.clip(1.0 - (r / 0.7)**2, 0, 1)
    
    # Asymmetry: shift intensity toward left side (negative x)
    # Creates a crescent/comma shape
    asym = np.clip(1.0 - (r / 0.7)**2, 0, 1) * (0.5 - 0.5 * dx)
    asym = np.clip(asym, 0, 1)
    
    ic = (1 - asym_strength) * base + asym_strength * asym
    ic = np.clip(ic, 0, 1)
    return ic

def run(gc, gw, R, N, steps, dt, ic_patch):
    Kf = make_kernel_fft(R, N)
    A = np.zeros((N, N))
    h, w = ic_patch.shape
    cy, cx = N//2, N//2
    A[cy-h//2:cy-h//2+h, cx-w//2:cx-w//2+w] = ic_patch
    
    m0 = A.sum()
    masses = [m0]
    coms = []
    
    for t in range(steps):
        # Center of mass
        if A.sum() > 0.1:
            ys, xs = np.mgrid[:N, :N]
            com_y = (ys * A).sum() / A.sum()
            com_x = (xs * A).sum() / A.sum()
            coms.append((com_y, com_x))
        
        Uf = np.fft.fft2(A) * Kf
        U = np.real(np.fft.ifft2(Uf))
        G = 2.0 * bell(U, gc, gw) - 1.0
        A = np.clip(A + dt * G, 0, 1)
        
        if t % 100 == 99:
            masses.append(A.sum())
    
    mf = A.sum()
    ratio = mf / (m0 + 1e-10)
    
    # Compute drift
    drift = 0.0
    if len(coms) > 10:
        c0 = coms[0]
        cf = coms[-1]
        drift = np.sqrt((cf[0]-c0[0])**2 + (cf[1]-c0[1])**2)
    
    # Classify
    if ratio < 0.05:
        cls = "DEAD"
    elif ratio > 3.0:
        cls = "EXPLOSIVE"
    elif drift > 5.0 and 0.3 < ratio < 3.0:
        cls = "GLIDER!"
    elif 0.3 < ratio < 3.0:
        cls = "STABLE"
    else:
        cls = "OTHER"
    
    return ratio, drift, cls, masses

# ============================================================
# EXPERIMENT: Fix gc=0.15, sweep gw AND asymmetry
# ============================================================
R = 13
N = 128
steps = 500
dt = 0.1
gc = 0.15

print("=" * 80)
print("ASYMMETRY vs PHASE TRANSITION")
print("gc=0.15, R=13, 128x128 grid, 500 steps, periodic boundaries")
print("=" * 80)
print(f"{'asym':>6s} {'gw':>8s} {'ratio':>8s} {'drift':>8s} {'class':>10s}")
print("-" * 50)

for asym in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
    ic = make_ic(R, asym)
    # Scan gw near the transition (0.015 to 0.022)
    for gw in np.linspace(0.015, 0.022, 15):
        ratio, drift, cls, masses = run(gc, gw, R, N, steps, dt, ic)
        marker = " <<<" if cls in ("GLIDER!", "STABLE") else ""
        print(f"{asym:6.1f} {gw:8.4f} {ratio:8.2f} {drift:8.1f} {cls:>10s}{marker}")
    print()

# ============================================================
# EXPERIMENT 2: If any stable/glider found, zoom in
# ============================================================
print("\n" + "=" * 80)
print("EXPERIMENT 2: Best asymmetry=0.6, fine gw scan")
print("=" * 80)
print(f"{'gw':>10s} {'ratio':>8s} {'drift':>8s} {'class':>10s}  mass_trajectory")
print("-" * 75)

ic = make_ic(R, 0.6)
for gw in np.linspace(0.016, 0.021, 30):
    ratio, drift, cls, masses = run(gc, gw, R, N, steps, dt, ic)
    mass_str = " → ".join(f"{m:.0f}" for m in masses)
    marker = " <<<" if cls in ("GLIDER!", "STABLE") else ""
    print(f"{gw:10.6f} {ratio:8.2f} {drift:8.1f} {cls:>10s}  {mass_str}{marker}")