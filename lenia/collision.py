"""
Collision experiments: what happens when two Lenia creatures meet?
"""
import numpy as np
import json

def gaussian_kernel(R, size):
    """Ring-shaped kernel for Lenia."""
    y, x = np.mgrid[-size//2:size//2, -size//2:size//2]
    r = np.sqrt(x**2 + y**2) / R
    kernel = np.exp(-((r - 0.5)**2) / (2 * 0.15**2))
    kernel[r > 1] = 0
    kernel /= kernel.sum()
    return kernel

def growth(u, gc, gw):
    return 2.0 * np.exp(-((u - gc)**2) / (2 * gw**2)) - 1.0

def orbium_seed(cy, cx, R, size):
    """Place an orbium-like seed at (cy, cx)."""
    grid = np.zeros((size, size))
    y, x = np.mgrid[-size//2:size//2, -size//2:size//2]
    # Shift coordinates
    yy = (y - cy + size//2) % size - size//2
    xx = (x - cx + size//2) % size - size//2
    r = np.sqrt(xx**2 + yy**2) / R
    seed = np.exp(-((r - 0.3)**2) / (2 * 0.05**2))
    seed[r > 0.7] = 0
    return seed

def run_collision(gc, gw, R, size, dt, steps,
                  pos1, pos2, approach_angle=0.0):
    """
    Place two creatures and let them evolve.
    Returns timeline of total mass, individual masses (approx), 
    and final grid state.
    """
    grid = np.zeros((size, size))
    
    # Place two seeds
    s1 = orbium_seed(pos1[0], pos1[1], R, size)
    s2 = orbium_seed(pos2[0], pos2[1], R, size)
    grid = np.clip(s1 + s2, 0, 1)
    
    kernel = gaussian_kernel(R, size)
    kernel_fft = np.fft.fft2(kernel, s=(size, size))
    
    timeline = []
    grids_sampled = []
    
    for step in range(steps):
        # Convolve
        field = np.real(np.fft.ifft2(np.fft.fft2(grid) * kernel_fft))
        # Growth
        grid = np.clip(grid + dt * growth(field, gc, gw), 0, 1)
        
        mass = float(grid.sum())
        
        # Split grid into halves to track individual "creatures"
        mid = size // 2
        mass_left = float(grid[:, :mid].sum())
        mass_right = float(grid[:, mid:].sum())
        
        timeline.append({
            'step': step,
            'total_mass': mass,
            'mass_left': mass_left,
            'mass_right': mass_right,
        })
        
        # Sample grid at key moments
        if step in [0, steps//4, steps//2, 3*steps//4, steps-1]:
            grids_sampled.append((step, grid.copy()))
    
    return timeline, grids_sampled, grid

def classify_outcome(timeline):
    """What happened?"""
    initial_mass = timeline[0]['total_mass']
    final_mass = timeline[-1]['total_mass']
    peak_mass = max(t['total_mass'] for t in timeline)
    
    if final_mass < 1.0:
        return 'annihilation'
    
    mass_ratio = final_mass / initial_mass
    if mass_ratio > 1.5:
        return 'explosion'
    if mass_ratio < 0.6:
        return 'partial_death'
    
    # Check if mass split is even (two survivors) or lopsided (merger)
    final_left = timeline[-1]['mass_left']
    final_right = timeline[-1]['mass_right']
    if final_left < 1.0 or final_right < 1.0:
        return 'merger'
    
    # Check for oscillation in late timeline
    late = timeline[-100:]
    masses = [t['total_mass'] for t in late]
    cv = np.std(masses) / np.mean(masses) if np.mean(masses) > 0 else 0
    if cv > 0.05:
        return 'oscillating_interaction'
    
    return 'coexistence'

def run_experiments():
    """Run a suite of collision experiments."""
    # Best parameters from zoo
    gc, gw = 0.0968, 0.0301
    R = 13
    size = 128
    dt = 0.1
    steps = 1500
    
    experiments = [
        # Head-on collision at different distances
        {'name': 'head_on_close', 'pos1': (64, 40), 'pos2': (64, 88)},
        {'name': 'head_on_far', 'pos1': (64, 20), 'pos2': (64, 108)},
        # Offset collision  
        {'name': 'offset_collision', 'pos1': (54, 40), 'pos2': (74, 88)},
        # Same position (complete overlap)
        {'name': 'overlap', 'pos1': (64, 64), 'pos2': (64, 64)},
        # Perpendicular approach
        {'name': 'perpendicular', 'pos1': (40, 64), 'pos2': (64, 40)},
        # Three creatures
        {'name': 'three_body', 'pos1': (44, 44), 'pos2': (44, 84)},
        # Very far apart (control — should just coexist)
        {'name': 'control_far', 'pos1': (32, 32), 'pos2': (96, 96)},
    ]
    
    results = []
    for exp in experiments:
        print(f"\n{'='*50}")
        print(f"Running: {exp['name']}")
        
        pos1 = exp['pos1']
        pos2 = exp['pos2']
        
        # Special case: three-body adds a third
        if exp['name'] == 'three_body':
            # We'll handle this manually
            grid = np.zeros((size, size))
            s1 = orbium_seed(44, 44, R, size)
            s2 = orbium_seed(44, 84, R, size)
            s3 = orbium_seed(84, 64, R, size)
            grid = np.clip(s1 + s2 + s3, 0, 1)
            
            kernel = gaussian_kernel(R, size)
            kernel_fft = np.fft.fft2(kernel, s=(size, size))
            
            timeline = []
            for step in range(steps):
                field = np.real(np.fft.ifft2(np.fft.fft2(grid) * kernel_fft))
                grid = np.clip(grid + dt * growth(field, gc, gw), 0, 1)
                mass = float(grid.sum())
                timeline.append({
                    'step': step,
                    'total_mass': mass,
                    'mass_left': float(grid[:, :size//2].sum()),
                    'mass_right': float(grid[:, size//2:].sum()),
                })
            
            outcome = classify_outcome(timeline)
            result = {
                'name': exp['name'],
                'outcome': outcome,
                'initial_mass': timeline[0]['total_mass'],
                'final_mass': timeline[-1]['total_mass'],
                'peak_mass': max(t['total_mass'] for t in timeline),
                'mass_ratio': timeline[-1]['total_mass'] / timeline[0]['total_mass'],
            }
        else:
            timeline, grids, final_grid = run_collision(
                gc, gw, R, size, dt, steps, pos1, pos2
            )
            outcome = classify_outcome(timeline)
            result = {
                'name': exp['name'],
                'outcome': outcome,
                'initial_mass': timeline[0]['total_mass'],
                'final_mass': timeline[-1]['total_mass'],
                'peak_mass': max(t['total_mass'] for t in timeline),
                'mass_ratio': timeline[-1]['total_mass'] / timeline[0]['total_mass'],
            }
        
        print(f"  Outcome: {outcome}")
        print(f"  Mass: {result['initial_mass']:.1f} → {result['final_mass']:.1f} "
              f"(ratio: {result['mass_ratio']:.3f})")
        results.append(result)
    
    # Save results
    with open('lenia/collision_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    for r in results:
        print(f"  {r['name']:25s} → {r['outcome']}")
    
    return results

if __name__ == '__main__':
    run_experiments()