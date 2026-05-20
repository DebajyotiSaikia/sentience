"""
Bisection search: Find the exact gw where death transitions to explosion.
Fix gc=0.15, binary search gw in [0.010, 0.020].
Small grid (64x64), 200 steps — should finish in seconds.
"""
import numpy as np
from scipy.signal import fftconvolve

def bell(x, m, s):
    return np.exp(-((x - m) / s) ** 2 / 2)

def make_kernel(R=13):
    y, x = np.mgrid[-R:R+1, -R:R+1]
    r = np.sqrt(x*x + y*y) / R
    k = bell(r, 0.5, 0.15)
    k[r > 1] = 0
    k /= k.sum() + 1e-10
    return k

def make_orbium(R=13):
    y, x = np.mgrid[-R:R+1, -R:R+1]
    r = np.sqrt(x*x + y*y) / R
    orb = np.clip(1.0 - r, 0, 1) * bell(r, 0.5, 0.15)
    orb /= orb.max() + 1e-10
    return orb

def classify(gc, gw, R=13, grid_size=64, steps=200, dt=0.1):
    K = make_kernel(R)
    A = np.zeros((grid_size, grid_size))
    orb = make_orbium(R)
    cy, cx = grid_size // 2, grid_size // 2
    h, w = orb.shape
    A[cy-h//2:cy-h//2+h, cx-w//2:cx-w//2+w] = orb
    m0 = A.sum()
    
    masses = [m0]
    for t in range(steps):
        U = fftconvolve(A, K, mode='same')
        G = 2.0 * bell(U, gc, gw) - 1.0
        A = np.clip(A + dt * G, 0, 1)
        if t % 50 == 49:
            masses.append(A.sum())
    
    mf = A.sum()
    ratio = mf / (m0 + 1e-10)
    return ratio, masses

# --- Bisection along gw, gc fixed at 0.15 ---
gc = 0.15
print(f"Bisecting gw for gc={gc}")
print(f"{'gw':>8s}  {'ratio':>8s}  {'class':>10s}  mass_trajectory")
print("-" * 70)

# First: sample 20 evenly spaced points
for gw in np.linspace(0.010, 0.025, 20):
    ratio, masses = classify(gc, gw)
    mass_str = " → ".join(f"{m:.1f}" for m in masses)
    if ratio < 0.1:
        cls = "DEAD"
    elif ratio < 1.5:
        cls = "STABLE"
    elif ratio < 3.0:
        cls = "EDGE"
    else:
        cls = "EXPLOSIVE"
    print(f"{gw:8.4f}  {ratio:8.2f}  {cls:>10s}  {mass_str}")

# Now try gc values too
print("\n\n--- Scanning gc with gw near boundary ---")
for gc_test in np.linspace(0.10, 0.20, 15):
    for gw_test in np.linspace(0.012, 0.018, 8):
        ratio, _ = classify(gc_test, gw_test)
        if 0.5 < ratio < 2.0:
            print(f"  ** STABLE CANDIDATE: gc={gc_test:.4f} gw={gw_test:.4f} ratio={ratio:.3f}")