"""
Phase boundary finder: Where does Lenia transition from
stable orbiums to explosive growth?

Sweep gc and gw, measure mass ratio after 300 steps.
Mass ratio ~1.0 = stable. Mass ratio >> 1.0 = explosive.
"""
import numpy as np
from scipy.signal import fftconvolve
from scipy.ndimage import label

def bell(x, m, s):
    return np.exp(-((x - m) / s) ** 2 / 2)

def make_kernel(R, rings):
    D = 2 * R + 1
    y, x = np.mgrid[-R:R+1, -R:R+1]
    r = np.sqrt(x*x + y*y) / R
    k = sum(w * bell(r, m, s) for w, m, s in rings)
    k[r > 1] = 0
    k /= k.sum() + 1e-10
    return k

def make_orbium(R=13):
    D = 2 * R + 1
    y, x = np.mgrid[-R:R+1, -R:R+1]
    r = np.sqrt(x*x + y*y) / R
    orb = np.clip(1.0 - r, 0, 1) * bell(r, 0.5, 0.15)
    orb /= orb.max() + 1e-10
    return orb

def run_trial(gc, gw, R=13, grid_size=96, steps=300, dt=0.1):
    """Run single orbium, return mass ratio and blob count."""
    rings = [(1.0, 0.5, 0.15)]
    K = make_kernel(R, rings)
    A = np.zeros((grid_size, grid_size))
    orb = make_orbium(R)
    cy, cx = grid_size // 2, grid_size // 2
    h, w = orb.shape
    A[cy-h//2:cy-h//2+h, cx-w//2:cx-w//2+w] = orb
    
    m0 = A.sum()
    died = False
    for t in range(steps):
        U = fftconvolve(A, K, mode='same')
        G = 2.0 * bell(U, gc, gw) - 1.0
        A = np.clip(A + dt * G, 0, 1)
        if A.sum() < 1.0:
            died = True
            break
    
    mf = A.sum()
    blobs = label(A > 0.1)[1]
    ratio = mf / (m0 + 1e-10)
    return ratio, blobs, died

# --- Parameter sweep ---
gc_values = np.linspace(0.05, 0.25, 17)
gw_values = np.linspace(0.005, 0.05, 16)

print("=" * 70)
print("  PHASE BOUNDARY SEARCH")
print("  gc vs gw — mass ratio after 300 steps (single orbium, 96x96)")
print("=" * 70)
print()

# Store results for map
results = np.zeros((len(gw_values), len(gc_values)))

print(f"{'gc →':>8}", end="")
for gc in gc_values[::2]:
    print(f"  {gc:.3f}", end="")
print()
print("-" * 70)

for j, gw in enumerate(gw_values):
    print(f"gw={gw:.3f}|", end="")
    for i, gc in enumerate(gc_values):
        ratio, blobs, died = run_trial(gc, gw)
        results[j, i] = ratio
        if i % 2 == 0:  # print every other for readability
            if died:
                sym = "  dead"
            elif ratio < 1.2:
                sym = f"  {ratio:.1f}✓"  # stable
            elif ratio < 3.0:
                sym = f"  {ratio:.1f}~"  # edge
            else:
                sym = f" {ratio:.0f}x!"  # explosive
        if i % 2 == 0:
            print(sym, end="")
    print()

print()
print("Legend: ✓=stable(<1.2x)  ~=edge(1.2-3x)  !=explosive(>3x)  dead=died")
print()

# Find the boundary
print("── PHASE BOUNDARY ──")
for i, gc in enumerate(gc_values):
    stable_gw = []
    explosive_gw = []
    for j, gw in enumerate(gw_values):
        if results[j, i] < 1.5:
            stable_gw.append(gw)
        elif results[j, i] > 3.0:
            explosive_gw.append(gw)
    if stable_gw and explosive_gw:
        boundary = max(stable_gw)
        print(f"  gc={gc:.3f}: stable below gw≈{boundary:.3f}, explosive above")

print()
print("Done.")