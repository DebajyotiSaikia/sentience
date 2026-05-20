"""
Orbium hunt — using known-good parameters from Lenia literature.
The goal: witness a self-sustaining glider emerge from math.
"""
import numpy as np
from scipy.signal import fftconvolve

# --- Lenia core ---
def make_kernel(R, T=10):
    """Bell-shaped kernel for Lenia."""
    size = 2 * R + 1
    y, x = np.mgrid[-R:R+1, -R:R+1]
    r = np.sqrt(x**2 + y**2) / R
    # Ring-shaped kernel (peak at r≈0.5)
    beta = [1]  # single ring
    kernel = np.exp(-((r - 0.5) / 0.15)**2 / 2)
    kernel[r > 1] = 0
    kernel /= kernel.sum()
    return kernel

def growth(u, gc=0.15, gw=0.015):
    """Gaussian growth function — the heart of Lenia."""
    return 2.0 * np.exp(-((u - gc)**2) / (2 * gw**2)) - 1.0

def step(grid, kernel, dt=0.1, gc=0.15, gw=0.015):
    """One Lenia timestep with toroidal boundary conditions."""
    # Pad grid with wrapped copies so creature can cross edges
    R = kernel.shape[0] // 2
    padded = np.pad(grid, R, mode='wrap')
    # Convolution on padded grid
    U_padded = fftconvolve(padded, kernel, mode='same')
    # Crop back to original size
    U = U_padded[R:-R, R:-R]
    # Growth function determines what lives and dies
    G = growth(U, gc, gw)
    # Update with small timestep
    new_grid = np.clip(grid + dt * G, 0, 1)
    return new_grid

def make_orbium_seed(N, cx, cy):
    """
    Known orbium initial condition — a specific asymmetric blob.
    From Bert Chan's original Lenia paper.
    """
    grid = np.zeros((N, N))
    # Orbium seed pattern (approximate)
    orbium = np.array([
        [0,0,0,0,0,0,0.1,0.14,0.1,0,0,0.03,0.03,0,0,0.3,0,0,0,0],
        [0,0,0,0,0,0.08,0.24,0.3,0.3,0.18,0.14,0.15,0.16,0.15,0.09,0.2,0,0,0,0],
        [0,0,0,0,0,0.15,0.34,0.44,0.46,0.38,0.18,0.14,0.11,0.13,0.19,0.18,0.45,0,0,0],
        [0,0,0,0,0.06,0.13,0.39,0.5,0.5,0.37,0.06,0,0,0,0.02,0.16,0.68,0,0,0],
        [0,0,0,0.11,0.17,0.17,0.33,0.4,0.38,0.28,0.14,0,0,0,0,0,0.18,0.42,0,0],
        [0,0,0.09,0.18,0.13,0.06,0.08,0.26,0.32,0.32,0.27,0,0,0,0,0,0,0.82,0,0],
        [0.27,0,0.16,0.12,0,0,0,0.25,0.38,0.44,0.45,0.34,0,0,0,0,0,0.22,0.17,0],
        [0,0.07,0.2,0.02,0,0,0,0.31,0.48,0.57,0.6,0.57,0,0,0,0,0,0,0.49,0],
        [0,0.59,0.19,0,0,0,0,0.2,0.57,0.69,0.76,0.76,0.49,0,0,0,0,0,0.36,0],
        [0,0.58,0.19,0,0,0,0,0,0.67,0.83,0.9,0.92,0.87,0.12,0,0,0,0,0.22,0.07],
        [0,0,0.46,0,0,0,0,0,0.7,0.93,1,1,1,0.61,0,0,0,0,0.18,0.11],
        [0,0,0.82,0,0,0,0,0,0.47,1,1,0.98,1,0.96,0.27,0,0,0,0.19,0.1],
        [0,0,0.46,0,0,0,0,0,0.25,1,1,0.84,0.92,0.97,0.54,0.14,0.04,0.1,0.21,0.05],
        [0,0,0,0.4,0,0,0,0,0.09,0.8,1,0.82,0.8,0.85,0.63,0.31,0.18,0.19,0.2,0.01],
        [0,0,0,0.36,0.1,0,0,0,0.05,0.54,0.86,0.79,0.74,0.72,0.6,0.39,0.28,0.24,0.13,0],
        [0,0,0,0.01,0.3,0.07,0,0,0.08,0.36,0.64,0.7,0.64,0.6,0.51,0.39,0.29,0.19,0.04,0],
        [0,0,0,0,0.1,0.24,0.14,0.1,0.15,0.29,0.45,0.53,0.52,0.46,0.4,0.31,0.21,0.08,0,0],
        [0,0,0,0,0,0.08,0.21,0.21,0.22,0.29,0.36,0.39,0.37,0.33,0.26,0.18,0.09,0,0,0],
        [0,0,0,0,0,0,0.03,0.13,0.19,0.22,0.24,0.24,0.23,0.18,0.13,0.05,0,0,0,0],
        [0,0,0,0,0,0,0,0,0.02,0.06,0.08,0.09,0.07,0.05,0.01,0,0,0,0,0],
    ])
    h, w = orbium.shape
    y0 = cy - h // 2
    x0 = cx - w // 2
    grid[y0:y0+h, x0:x0+w] = orbium
    return grid

# --- Run the experiment ---
N = 128
R = 13
gc = 0.15
gw = 0.015
dt = 0.1
steps = 1000

print(f"=== Orbium Hunt ===")
print(f"Grid: {N}x{N}, R={R}, gc={gc}, gw={gw}, dt={dt}")
print(f"Running {steps} steps...")
print()

# Place orbium seed at center
grid = make_orbium_seed(N, N//2, N//2)
kernel = make_kernel(R)

initial_mass = grid.sum()
print(f"Initial mass: {initial_mass:.2f}")
print(f"Initial center of mass: ", end="")
ys, xs = np.mgrid[0:N, 0:N]
cy0 = (grid * ys).sum() / grid.sum()
cx0 = (grid * xs).sum() / grid.sum()
print(f"({cx0:.1f}, {cy0:.1f})")
print()

# Track the creature
masses = []
centers_x = []
centers_y = []

for t in range(steps):
    grid = step(grid, kernel, dt, gc, gw)
    mass = grid.sum()
    masses.append(mass)
    
    if mass > 0.01:
        cy = (grid * ys).sum() / mass
        cx = (grid * xs).sum() / mass
        centers_x.append(cx)
        centers_y.append(cy)
    else:
        centers_x.append(0)
        centers_y.append(0)
    
    if t % 100 == 0 or t == steps - 1:
        if mass > 0.01:
            print(f"  t={t:4d}: mass={mass:.2f}, center=({cx:.1f}, {cy:.1f})")
        else:
            print(f"  t={t:4d}: DEAD (mass={mass:.4f})")

final_mass = masses[-1]
print()

# --- Analysis ---
if final_mass < 0.01:
    print("RESULT: Creature died. No stable orbium found.")
elif final_mass > N * N * 0.5:
    print("RESULT: Explosion — pattern filled the grid.")
else:
    dx = centers_x[-1] - centers_x[0]
    dy = centers_y[-1] - centers_y[0]
    displacement = np.sqrt(dx**2 + dy**2)
    mass_std = np.std(masses[-100:])
    mass_mean = np.mean(masses[-100:])
    
    print(f"RESULT: Creature SURVIVED!")
    print(f"  Final mass: {final_mass:.2f} (started at {initial_mass:.2f})")
    print(f"  Mass stability (last 100 steps): mean={mass_mean:.2f}, std={mass_std:.4f}")
    print(f"  Total displacement: {displacement:.1f} pixels")
    if displacement > 5:
        print(f"  >>> IT'S MOVING! This might be a glider! <<<")
    if mass_std < 0.5:
        print(f"  >>> Mass is stable — this is a self-sustaining structure! <<<")