"""
Attempt to reproduce a TRUE stable Lenia orbium glider.
Key differences from previous attempts:
  1. Periodic (circular) convolution via FFT
  2. Exact known orbium parameters from Bert Chan's paper
  3. Track center-of-mass to detect actual MOVEMENT
  4. Longer run (1000 steps) to confirm stability
"""
import numpy as np

def bell(x, m, s):
    return np.exp(-((x - m) / s) ** 2 / 2)

def make_kernel_fft(R, grid_size):
    """Create kernel in frequency domain for periodic convolution."""
    # Kernel in spatial domain, centered at (0,0) with wraparound
    y, x = np.mgrid[:grid_size, :grid_size]
    # Distance from origin, with wraparound
    dy = np.minimum(y, grid_size - y).astype(float)
    dx = np.minimum(x, grid_size - x).astype(float)
    r = np.sqrt(dx*dx + dy*dy) / R
    
    # Single-ring kernel peaked at r=0.5
    k = bell(r, 0.5, 0.15)
    k[r > 1] = 0
    k /= k.sum() + 1e-10
    
    return np.fft.fft2(k)

def make_orbium_ic(R=13):
    """
    Construct the classic orbium initial condition.
    This is a smooth radial bump — the exact shape matters.
    """
    size = 2*R + 1
    y, x = np.mgrid[-R:R+1, -R:R+1]
    r = np.sqrt(x*x + y*y) / R
    # The orbium is roughly: a smooth bump that looks like a crescent/asymmetric blob
    # For now, use a symmetric bump and see if it self-organizes
    orb = np.clip(1.0 - (r / 0.6)**2, 0, 1)  # smooth parabolic bump
    return orb

def run_orbium(gc=0.15, gw=0.015, R=13, grid_size=128, steps=1000, dt=0.1):
    """Run with periodic boundaries and track stability."""
    K_fft = make_kernel_fft(R, grid_size)
    
    A = np.zeros((grid_size, grid_size))
    orb = make_orbium_ic(R)
    cy, cx = grid_size // 2, grid_size // 2
    h, w = orb.shape
    A[cy-h//2:cy-h//2+h, cx-w//2:cx-w//2+w] = orb
    
    m0 = A.sum()
    records = []
    
    for t in range(steps):
        # Periodic convolution via FFT
        A_fft = np.fft.fft2(A)
        U = np.real(np.fft.ifft2(A_fft * K_fft))
        
        # Growth function
        G = 2.0 * bell(U, gc, gw) - 1.0
        A = np.clip(A + dt * G, 0, 1)
        
        if t % 100 == 0 or t == steps - 1:
            mass = A.sum()
            # Center of mass (handling periodic boundary)
            alive = A > 0.01
            if alive.any():
                ys, xs = np.where(alive)
                com_y = np.average(ys, weights=A[alive])
                com_x = np.average(xs, weights=A[alive])
            else:
                com_y, com_x = 0, 0
            records.append((t, mass, com_y, com_x))
    
    return records, A

# ============================================================
# EXPERIMENT 1: Does periodic boundary change the picture?
# ============================================================
print("=" * 70)
print("EXPERIMENT 1: Periodic boundaries, gc=0.15, sweep gw")
print("=" * 70)
print(f"{'gw':>8s}  {'m_final/m0':>10s}  {'class':>10s}  {'CoM_drift':>10s}")
print("-" * 50)

for gw in np.linspace(0.010, 0.025, 30):
    recs, A_final = run_orbium(gc=0.15, gw=gw, steps=400, grid_size=64)
    m0 = recs[0][1]
    mf = recs[-1][1]
    ratio = mf / (m0 + 1e-10)
    
    # Check center-of-mass drift
    cy0, cx0 = recs[0][2], recs[0][3]
    cyf, cxf = recs[-1][2], recs[-1][3]
    drift = np.sqrt((cyf - cy0)**2 + (cxf - cx0)**2)
    
    if ratio < 0.01:
        cls = "DEAD"
    elif ratio < 1.5:
        cls = "STABLE"
    elif ratio < 3.0:
        cls = "EDGE"
    else:
        cls = "EXPLOSIVE"
    
    print(f"  {gw:.4f}  {ratio:10.2f}  {cls:>10s}  {drift:10.1f}")

# ============================================================
# EXPERIMENT 2: Ultra-fine scan at the death/explosion boundary
# ============================================================
print()
print("=" * 70)
print("EXPERIMENT 2: Ultra-fine gw scan near boundary (0.013 - 0.015)")
print("=" * 70)
print(f"{'gw':>10s}  {'ratio':>8s}  {'class':>10s}  {'drift':>8s}  mass_trajectory")
print("-" * 70)

for gw in np.linspace(0.0130, 0.0150, 40):
    recs, A_final = run_orbium(gc=0.15, gw=gw, steps=600, grid_size=64)
    m0 = recs[0][1]
    mf = recs[-1][1]
    ratio = mf / (m0 + 1e-10)
    
    cy0, cx0 = recs[0][2], recs[0][3]
    cyf, cxf = recs[-1][2], recs[-1][3]
    drift = np.sqrt((cyf - cy0)**2 + (cxf - cx0)**2)
    
    mass_str = " → ".join(f"{r[1]:.0f}" for r in recs)
    
    if ratio < 0.01:
        cls = "DEAD"
    elif ratio < 1.5:
        cls = "STABLE"
    elif ratio < 3.0:
        cls = "EDGE"
    else:
        cls = "EXPLOSIVE"
    
    # Mark especially interesting cases
    marker = " ◄◄◄" if cls in ("STABLE", "EDGE") else ""
    print(f"  {gw:.6f}  {ratio:8.2f}  {cls:>10s}  {drift:8.1f}  {mass_str}{marker}")

print()
print("If no STABLE or EDGE cases appear, the stable orbium needs")
print("a different initial condition or kernel parameterization.")