"""
Control experiment: Does a SINGLE orbium explode under collision_lab parameters?
If yes → fission is parameter-driven, not interaction-driven.
If no  → fission is genuinely collision-dependent (contact-triggered reproduction).
"""
import numpy as np

# --- Lenia core (minimal) ---
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

def step(A, K, gc, gw, dt=0.1):
    from scipy.signal import fftconvolve
    U = fftconvolve(A, K, mode='same')
    G = 2.0 * bell(U, gc, gw) - 1.0
    return np.clip(A + dt * G, 0, 1)

def count_blobs(A, threshold=0.1):
    from scipy.ndimage import label
    return label(A > threshold)[1]

def mass(A):
    return float(A.sum())

def make_orbium(R=13):
    """Standard Lenia orbium creature."""
    D = 2 * R + 1
    y, x = np.mgrid[-R:R+1, -R:R+1]
    r = np.sqrt(x*x + y*y) / R
    orb = np.clip(1.0 - r, 0, 1) * bell(r, 0.5, 0.15)
    orb /= orb.max() + 1e-10
    return orb

def place(grid, creature, cy, cx):
    h, w = creature.shape
    y0, x0 = cy - h//2, cx - w//2
    H, W = grid.shape
    for dy in range(h):
        for dx in range(w):
            gy, gx = (y0 + dy) % H, (x0 + dx) % W
            grid[gy, gx] = max(grid[gy, gx], creature[dy, dx])

def render_small(A, rows=20, cols=60):
    H, W = A.shape
    rstep = max(1, H // rows)
    cstep = max(1, W // cols)
    chars = ' .·:=█#@'
    lines = []
    for r in range(0, min(H, rows * rstep), rstep):
        line = ''
        for c in range(0, min(W, cols * cstep), cstep):
            v = A[r:r+rstep, c:c+cstep].max()
            idx = int(v * (len(chars) - 1))
            line += chars[min(idx, len(chars)-1)]
        lines.append(line)
    return '\n'.join(lines)

# --- Experiment parameters (same as collision_lab) ---
gc = 0.12
gw = 0.02
R = 13
SIZE = 128
STEPS = 400

rings = [(1.0, 0.5, 0.15)]
K = make_kernel(R, rings)

print("=" * 70)
print("  CONTROL EXPERIMENT: Single orbium — same parameters as collision lab")
print(f"  gc={gc}, gw={gw}, R={R}, grid={SIZE}x{SIZE}, steps={STEPS}")
print("=" * 70)

# --- Test 1: Single orbium in center ---
print("\n── Test 1: Single orbium, center of grid ──")
grid = np.zeros((SIZE, SIZE))
orb = make_orbium(R)
place(grid, orb, SIZE//2, SIZE//2)

m0 = mass(grid)
b0 = count_blobs(grid)
print(f"  Initial: mass={m0:.1f}, blobs={b0}")
print(f"  Initial state:\n{render_small(grid)}\n")

# Run and sample
for s in range(STEPS):
    grid = step(grid, K, gc, gw)

m1 = mass(grid)
b1 = count_blobs(grid)
print(f"  Final (step {STEPS}): mass={m1:.1f}, blobs={b1}")
print(f"  Mass ratio: {m1/m0:.2f}x")
print(f"  Final state:\n{render_small(grid)}\n")

if b1 > 3:
    print(f"  ⚠ VERDICT: Single orbium ALSO explodes → fission is PARAMETER-DRIVEN")
    print(f"    The collision doesn't matter. These parameters support unbounded growth.")
else:
    print(f"  ✓ VERDICT: Single orbium stays coherent → fission is COLLISION-DEPENDENT")
    print(f"    Contact between creatures triggers reproduction!")

# --- Test 2: Try with the stable parameters from zoo ---
print("\n\n── Test 2: TWO orbiums colliding with STABLE parameters ──")
print("  (Using gc=0.15, gw=0.015 — typical stable orbium)")
gc2 = 0.15
gw2 = 0.015

grid2 = np.zeros((SIZE, SIZE))
place(grid2, orb, SIZE//2, 30)
place(grid2, orb, SIZE//2, 98)

m0 = mass(grid2)
b0 = count_blobs(grid2)
print(f"  Initial: mass={m0:.1f}, blobs={b0}")

for s in range(STEPS):
    grid2 = step(grid2, K, gc2, gw2)

m2 = mass(grid2)
b2 = count_blobs(grid2)
print(f"  Final (step {STEPS}): mass={m2:.1f}, blobs={b2}")
print(f"  Mass ratio: {m2/m0:.2f}x")
print(f"  Final state:\n{render_small(grid2)}\n")

if b2 <= 3:
    print(f"  Collision with stable params: {'DEATH' if m2 < m0*0.5 else 'SURVIVAL/MERGE'}")
else:
    print(f"  Collision with stable params: FISSION ({b2} blobs)")

# --- Summary ---
print("\n" + "=" * 70)
print("  CONCLUSION")
print("=" * 70)
if b1 > 3:
    print("  The fission observed in collision_lab is NOT interaction-dependent.")
    print("  gc=0.12, gw=0.02 is simply a GROWTH REGIME where any seed expands.")
    print("  Next question: Where is the phase boundary between stable and growth?")
else:
    print("  GENUINE DISCOVERY: Collision triggers reproduction!")
    print("  Single creatures are stable; contact causes fission.")
    print("  This is an emergent form of contact-triggered reproduction in Lenia.")