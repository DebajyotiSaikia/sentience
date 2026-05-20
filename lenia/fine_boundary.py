"""
Fine-grained phase boundary search around the known stable orbium region.
The coarse sweep showed NO stable regime — only death or explosion.
Hypothesis: stability exists in a razor-thin band at the boundary.

Zooming into gc=0.14-0.16, gw=0.010-0.020 with fine resolution.
Also tracking whether the orbium MOVES (a key sign of true glider behavior).
"""
import numpy as np
from scipy.signal import fftconvolve
from scipy.ndimage import label, center_of_mass

def bell(x, m, s):
    return np.exp(-((x - m) / s) ** 2 / 2)

def make_kernel(R, rings):
    y, x = np.mgrid[-R:R+1, -R:R+1]
    r = np.sqrt(x*x + y*y) / R
    k = sum(w * bell(r, m, s) for w, m, s in rings)
    k[r > 1] = 0
    k /= k.sum() + 1e-10
    return k

def make_orbium(R=13):
    y, x = np.mgrid[-R:R+1, -R:R+1]
    r = np.sqrt(x*x + y*y) / R
    orb = np.clip(1.0 - r, 0, 1) * bell(r, 0.5, 0.15)
    orb /= orb.max() + 1e-10
    return orb

def run_trial(gc, gw, R=13, grid_size=128, steps=500, dt=0.1):
    """Run single orbium, track mass, blobs, and center-of-mass displacement."""
    rings = [(1.0, 0.5, 0.15)]
    K = make_kernel(R, rings)
    A = np.zeros((grid_size, grid_size))
    orb = make_orbium(R)
    cy, cx = grid_size // 2, grid_size // 2
    h, w = orb.shape
    A[cy-h//2:cy-h//2+h, cx-w//2:cx-w//2+w] = orb
    
    m0 = A.sum()
    if m0 < 0.01:
        return 0, 0, 0, 'dead'
    
    # Track center of mass at start
    com_start = center_of_mass(A)
    
    masses = [m0]
    for i in range(steps):
        U = fftconvolve(A, K, mode='same')
        G = 2.0 * bell(U, gc, gw) - 1.0
        A = np.clip(A + dt * G, 0, 1)
        if i % 50 == 49:
            masses.append(A.sum())
    
    mf = A.sum()
    if mf < 0.5:
        return 0, 0, 0, 'dead'
    
    ratio = mf / (m0 + 1e-10)
    blobs = label(A > 0.1)[1]
    
    # How far did center of mass move?
    com_end = center_of_mass(A)
    displacement = np.sqrt((com_end[0]-com_start[0])**2 + (com_end[1]-com_start[1])**2)
    
    # Check mass stability over time (variance of mass trajectory)
    mass_arr = np.array(masses)
    mass_cv = mass_arr.std() / (mass_arr.mean() + 1e-10)  # coefficient of variation
    
    if ratio < 0.8:
        phase = 'decay'
    elif ratio < 1.2 and blobs <= 2:
        phase = 'STABLE'
    elif ratio < 3.0:
        phase = 'edge'
    else:
        phase = 'explode'
    
    return ratio, blobs, displacement, phase

print("=" * 78)
print("  FINE-GRAINED PHASE BOUNDARY")
print("  gc ∈ [0.10, 0.22], gw ∈ [0.008, 0.022]")
print("  500 steps, 128x128 grid, single orbium")
print("=" * 78)

gc_vals = np.linspace(0.10, 0.22, 25)
gw_vals = np.linspace(0.008, 0.022, 29)

# Store results
results = {}
stable_points = []

print(f"\n{'':>8}", end='')
for gc in gc_vals[::3]:
    print(f" {gc:.3f}", end='')
print()
print("-" * 78)

for gw in gw_vals:
    print(f"gw={gw:.4f}|", end='')
    for gc in gc_vals:
        ratio, blobs, disp, phase = run_trial(gc, gw)
        results[(gc, gw)] = (ratio, blobs, disp, phase)
        
        if phase == 'STABLE':
            stable_points.append((gc, gw, ratio, blobs, disp))
            sym = ' ★ '
        elif phase == 'edge':
            sym = f'{ratio:.0f}~'
            sym = f'{sym:>4}'
        elif phase == 'explode':
            sym = f'{ratio:.0f}!'
            sym = f'{sym:>4}'
        elif phase == 'decay':
            sym = ' ↓  '
        else:  # dead
            sym = ' ·  '
        
        # Only print every 3rd gc to fit
        idx = list(gc_vals).index(gc) if gc in gc_vals else -1
        if idx % 3 == 0:
            print(f"{sym:>5}", end='')
    print()

print("\n" + "=" * 78)
if stable_points:
    print(f"\n  ★ STABLE POINTS FOUND: {len(stable_points)}")
    for gc, gw, ratio, blobs, disp in stable_points:
        print(f"    gc={gc:.4f}, gw={gw:.4f}: mass_ratio={ratio:.2f}, "
              f"blobs={blobs}, displacement={disp:.1f}px")
    print(f"\n  Stability exists in a band of width ~{max(p[1] for p in stable_points) - min(p[1] for p in stable_points):.4f} in gw")
else:
    print("\n  ⚠ NO STABLE POINTS FOUND")
    print("  The death→explosion transition is truly discontinuous!")
    print("  With this kernel shape, there is no stable glider regime.")
    print("\n  This means the standard Lenia orbium requires a DIFFERENT")
    print("  kernel or growth function than what we're using.")
    
    # Find the narrowest gap between death and explosion
    print("\n  Narrowest death→explosion transitions:")
    for gc in gc_vals[::2]:
        last_dead_gw = None
        first_explode_gw = None
        for gw in gw_vals:
            phase = results.get((gc, gw), (0,0,0,'?'))[3]
            if phase in ('dead', 'decay'):
                last_dead_gw = gw
            elif phase in ('explode', 'edge') and first_explode_gw is None:
                first_explode_gw = gw
        if last_dead_gw and first_explode_gw:
            gap = first_explode_gw - last_dead_gw
            print(f"    gc={gc:.3f}: dead at gw={last_dead_gw:.4f}, "
                  f"explode at gw={first_explode_gw:.4f}, gap={gap:.5f}")

print("\nDone.")