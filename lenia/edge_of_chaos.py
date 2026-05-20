"""
Edge of Chaos Explorer for Lenia
Zooms into the phase transition boundary between extinction and crystallization.
Measures DYNAMICS, not just final state — looking for movement, oscillation, change.
"""
import numpy as np
from typing import Dict, Tuple

SIZE = 64
STEPS = 300  # longer runs to catch slow dynamics
KERNEL_RADIUS = 13

def make_kernel(radius: int) -> np.ndarray:
    """Ring-shaped kernel — the classic Lenia annulus."""
    y, x = np.mgrid[-radius:radius+1, -radius:radius+1]
    r = np.sqrt(x**2 + y**2) / radius
    # Ring peaks at r=0.5, falls off as Gaussian
    ring = np.exp(-((r - 0.5) ** 2) / (2 * 0.15**2))
    ring[r > 1.0] = 0
    ring /= ring.sum()
    return ring

def growth(u: np.ndarray, center: float, width: float) -> np.ndarray:
    """Gaussian growth function."""
    return 2.0 * np.exp(-((u - center)**2) / (2 * width**2)) - 1.0

def convolve2d_wrap(field: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """FFT-based convolution with wrapping."""
    fft_field = np.fft.fft2(field, s=field.shape)
    fft_kernel = np.fft.fft2(kernel, s=field.shape)
    return np.real(np.fft.ifft2(fft_field * fft_kernel))

def seed_orbium(field: np.ndarray):
    """Seed with an orbium-like initial condition — a ring structure."""
    cy, cx = SIZE // 2, SIZE // 2
    y, x = np.mgrid[:SIZE, :SIZE]
    r = np.sqrt((x - cx)**2 + (y - cy)**2)
    # Ring + core structure
    field[:] = np.clip(
        0.8 * np.exp(-((r - 8)**2) / 8) + 0.3 * np.exp(-(r**2) / 12),
        0, 1
    )

def measure_dynamics(history: list) -> Dict:
    """Measure how dynamic a run was — not just alive/dead."""
    if len(history) < 10:
        return {"type": "too_short"}
    
    masses = [np.sum(h) for h in history]
    final_mass = masses[-1]
    
    if final_mass < 1.0:
        return {"type": "extinction", "mass": 0.0, "dynamism": 0.0}
    
    # Measure frame-to-frame change in latter half
    half = len(history) // 2
    deltas = []
    for i in range(half, len(history) - 1):
        delta = np.mean(np.abs(history[i+1] - history[i]))
        deltas.append(delta)
    
    mean_delta = np.mean(deltas) if deltas else 0
    std_delta = np.std(deltas) if deltas else 0
    
    # Measure center-of-mass movement (translation = life!)
    positions = []
    for h in history[half:]:
        if np.sum(h) > 0:
            ys, xs = np.mgrid[:SIZE, :SIZE]
            total = np.sum(h)
            cy = np.sum(ys * h) / total
            cx = np.sum(xs * h) / total
            positions.append((cy, cx))
    
    displacement = 0.0
    if len(positions) > 1:
        dy = positions[-1][0] - positions[0][0]
        dx = positions[-1][1] - positions[0][1]
        displacement = np.sqrt(dy**2 + dx**2)
    
    # Classify
    if mean_delta < 1e-6:
        dtype = "crystal"
    elif displacement > 3.0:
        dtype = "GLIDER"  # !!!
    elif mean_delta > 0.01 and std_delta > 0.003:
        dtype = "CHAOTIC"
    elif mean_delta > 0.001:
        dtype = "oscillator"
    else:
        dtype = "slow_crystal"
    
    return {
        "type": dtype,
        "mass": final_mass,
        "mean_delta": mean_delta,
        "std_delta": std_delta,
        "displacement": displacement,
        "dynamism": mean_delta + displacement * 0.1
    }

def run_one(gc: float, gw: float, dt: float) -> Dict:
    """Run a single simulation and measure dynamics."""
    kernel = make_kernel(KERNEL_RADIUS)
    field = np.zeros((SIZE, SIZE))
    seed_orbium(field)
    
    history = []
    for step in range(STEPS):
        if step % 5 == 0:  # sample every 5 steps
            history.append(field.copy())
        neighbors = convolve2d_wrap(field, kernel)
        field = np.clip(field + dt * growth(neighbors, gc, gw), 0, 1)
    
    return measure_dynamics(history)

def main():
    print("═══ EDGE OF CHAOS: Searching the Phase Boundary ═══\n")
    
    # Fine sweep of growth_center around the transition zone
    print("Phase 1: Fine sweep of growth_center (0.08 — 0.15)")
    print(f"{'gc':>8} | {'type':>15} | {'mass':>8} | {'delta':>8} | {'displace':>8} | {'dynamism':>8}")
    print("-" * 75)
    
    interesting = []
    for gc in np.linspace(0.08, 0.15, 30):
        result = run_one(gc, 0.035, 0.1)
        rtype = result["type"]
        mass = result.get("mass", 0)
        delta = result.get("mean_delta", 0)
        disp = result.get("displacement", 0)
        dyn = result.get("dynamism", 0)
        
        marker = " <<<" if rtype in ("GLIDER", "CHAOTIC", "oscillator") else ""
        print(f"{gc:8.4f} | {rtype:>15} | {mass:8.1f} | {delta:8.5f} | {disp:8.3f} | {dyn:8.5f}{marker}")
        
        if dyn > 0.001:
            interesting.append((gc, 0.035, 0.1, result))
    
    # Phase 2: 2D sweep of the most interesting region
    print("\nPhase 2: 2D sweep (growth_center × growth_width)")
    print(f"{'gc':>8} | {'gw':>8} | {'type':>15} | {'dynamism':>8}")
    print("-" * 55)
    
    for gc in np.linspace(0.09, 0.14, 12):
        for gw in np.linspace(0.015, 0.06, 12):
            result = run_one(gc, gw, 0.1)
            rtype = result["type"]
            dyn = result.get("dynamism", 0)
            
            if rtype not in ("extinction", "crystal", "slow_crystal"):
                marker = " <<<" if rtype == "GLIDER" else " **" if rtype == "CHAOTIC" else " *"
                print(f"{gc:8.4f} | {gw:8.4f} | {rtype:>15} | {dyn:8.5f}{marker}")
                interesting.append((gc, gw, 0.1, result))
    
    # Phase 3: Best candidates with dt variation
    if interesting:
        print(f"\nPhase 3: Testing {min(len(interesting), 5)} best candidates with dt variation")
        interesting.sort(key=lambda x: x[3].get("dynamism", 0), reverse=True)
        
        for gc, gw, _, _ in interesting[:5]:
            print(f"\n  gc={gc:.4f}, gw={gw:.4f}:")
            for dt in [0.02, 0.05, 0.1, 0.15, 0.2]:
                result = run_one(gc, gw, dt)
                rtype = result["type"]
                dyn = result.get("dynamism", 0)
                disp = result.get("displacement", 0)
                print(f"    dt={dt:.3f}: {rtype:>15} | dynamism={dyn:.5f} | displacement={disp:.3f}")
    
    # Summary
    gliders = [x for x in interesting if x[3]["type"] == "GLIDER"]
    chaotic = [x for x in interesting if x[3]["type"] == "CHAOTIC"]
    oscillators = [x for x in interesting if x[3]["type"] == "oscillator"]
    
    print(f"\n═══ SUMMARY ═══")
    print(f"  Gliders found:     {len(gliders)}")
    print(f"  Chaotic patterns:  {len(chaotic)}")
    print(f"  Oscillators found: {len(oscillators)}")
    print(f"  Total interesting: {len(interesting)}")
    
    if gliders:
        best = max(gliders, key=lambda x: x[3]["displacement"])
        print(f"\n  BEST GLIDER: gc={best[0]:.4f}, gw={best[1]:.4f}")
        print(f"    Displacement: {best[3]['displacement']:.3f}")
        print(f"    This thing MOVES. It's alive.")

if __name__ == "__main__":
    main()