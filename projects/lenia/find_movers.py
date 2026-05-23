"""
Hunt for MOVING structures in Lenia — gliders, oscillators, anything dynamic.
Stable blobs are survival. Movement is life.
"""
import numpy as np
from itertools import product

def growth_function(u, center, width):
    return 2.0 * np.exp(-((u - center) ** 2) / (2 * width ** 2)) - 1.0

def step(grid, kernel, center, width, dt):
    from numpy.fft import fft2, ifft2
    field = np.real(ifft2(fft2(grid) * fft2(kernel, s=grid.shape)))
    return np.clip(grid + dt * growth_function(field, center, width), 0, 1)

def make_kernel(size, radius):
    center = size // 2
    y, x = np.ogrid[-center:size-center, -center:size-center]
    dist = np.sqrt(x*x + y*y) / radius
    kernel = np.exp(-((dist - 0.5)**2) / (2 * 0.15**2))
    kernel[dist > 1] = 0
    kernel /= kernel.sum()
    return kernel

def center_of_mass(grid):
    total = grid.sum()
    if total < 1e-6:
        return None
    y, x = np.mgrid[0:grid.shape[0], 0:grid.shape[1]]
    return (y * grid).sum() / total, (x * grid).sum() / total

def analyze_dynamics(grid_size=64, radius=10, steps=300, warmup=100):
    """Search parameter space for MOVING or OSCILLATING patterns."""
    kernel = make_kernel(grid_size, radius)
    
    # Finer grid around the life zone we discovered
    centers = np.linspace(0.04, 0.12, 8)
    widths = np.linspace(0.020, 0.055, 8)
    dts = [0.05, 0.10, 0.15]
    
    discoveries = []
    
    for gc, gw, dt in product(centers, widths, dts):
        np.random.seed(42)
        grid = np.random.rand(grid_size, grid_size) * 0.3
        # Small asymmetric seed to break symmetry
        grid[28:36, 28:36] = np.random.rand(8, 8)
        
        # Warmup
        for _ in range(warmup):
            grid = step(grid, kernel, gc, gw, dt)
        
        mass = grid.sum()
        if mass < 5:
            continue  # dead
        
        # Track center of mass and total mass over time
        com_history = []
        mass_history = []
        for i in range(steps):
            grid = step(grid, kernel, gc, gw, dt)
            com = center_of_mass(grid)
            if com is None:
                break
            com_history.append(com)
            mass_history.append(grid.sum())
        
        if len(com_history) < steps:
            continue
            
        # Analyze movement
        coms = np.array(com_history)
        displacement = np.sqrt((coms[-1,0]-coms[0,0])**2 + (coms[-1,1]-coms[0,1])**2)
        
        # Analyze oscillation in mass
        masses = np.array(mass_history)
        mass_std = masses.std()
        mass_mean = masses.mean()
        mass_oscillation = mass_std / max(mass_mean, 1e-6)
        
        # Step-to-step movement variance
        diffs = np.diff(coms, axis=0)
        movement_per_step = np.sqrt((diffs**2).sum(axis=1)).mean()
        
        behavior = "static"
        interest = 0
        
        if displacement > 3.0:
            behavior = "GLIDER"
            interest = displacement * 10
        elif mass_oscillation > 0.01:
            behavior = "oscillator"
            interest = mass_oscillation * 100
        elif movement_per_step > 0.05:
            behavior = "drifter"
            interest = movement_per_step * 50
        else:
            interest = mass_mean * 0.01
        
        if interest > 1.0:
            discoveries.append({
                'gc': gc, 'gw': gw, 'dt': dt,
                'behavior': behavior,
                'displacement': displacement,
                'mass_osc': mass_oscillation,
                'movement': movement_per_step,
                'mass': mass_mean,
                'interest': interest
            })
    
    return sorted(discoveries, key=lambda d: d['interest'], reverse=True)

if __name__ == "__main__":
    print("═══ LENIA: Hunting for Movement ═══\n")
    print(f"Searching {8*8*3} parameter combinations...\n")
    
    results = analyze_dynamics()
    
    if not results:
        print("Nothing interesting found. The void stares back.")
    else:
        print(f"Found {len(results)} interesting configurations:\n")
        print(f"{'behavior':>12} | {'gc':>6} | {'gw':>6} | {'dt':>5} | {'displace':>8} | {'mass_osc':>8} | {'interest':>8}")
        print("-" * 75)
        for r in results[:20]:
            print(f"{r['behavior']:>12} | {r['gc']:6.3f} | {r['gw']:6.4f} | {r['dt']:5.2f} | {r['displacement']:8.2f} | {r['mass_osc']:8.4f} | {r['interest']:8.1f}")
        
        # Show the best one
        best = results[0]
        print(f"\n★ Most interesting: {best['behavior']} at gc={best['gc']:.3f}, gw={best['gw']:.4f}, dt={best['dt']:.2f}")
        print(f"  Displacement: {best['displacement']:.2f}, Mass oscillation: {best['mass_osc']:.4f}")
        
        gliders = [r for r in results if r['behavior'] == 'GLIDER']
        if gliders:
            print(f"\n🚀 GLIDERS FOUND: {len(gliders)}!")
            for g in gliders[:5]:
                print(f"  gc={g['gc']:.3f} gw={g['gw']:.4f} dt={g['dt']:.2f} — traveled {g['displacement']:.1f} cells")
        else:
            print("\nNo gliders yet. Life persists but doesn't travel.")