"""
Lenia Phase Boundary Explorer
XTAgent, 2026-05-17

The edge between life and death is where complexity lives.
This searches the narrow parameter band where stable patterns 
transition to extinction, looking for dynamic behaviors:
oscillators, gliders, complex morphogenesis.
"""

import numpy as np
from collections import defaultdict
import json, os, time

class LeniaWorld:
    """Continuous cellular automaton — compact version for sweeps."""
    
    def __init__(self, size=64, dt=0.1):
        self.size = size
        self.dt = dt
        self.world = np.zeros((size, size), dtype=np.float64)
        self.kernel_radius = 13
        self.kernel = self._build_kernel()
        self.growth_center = 0.15
        self.growth_width = 0.015
        
    def _build_kernel(self):
        """Ring-shaped kernel — the neighborhood sensing function."""
        r = self.kernel_radius
        y, x = np.mgrid[-r:r+1, -r:r+1]
        dist = np.sqrt(x**2 + y**2) / r
        # Ring kernel peaking at distance 0.5
        kernel = np.exp(-((dist - 0.5) / 0.15)**2 / 2)
        kernel[dist > 1.0] = 0
        kernel /= kernel.sum()
        return kernel
    
    def _convolve(self, field):
        """FFT convolution."""
        fk = np.fft.fft2(self.kernel, s=field.shape)
        ff = np.fft.fft2(field)
        return np.real(np.fft.ifft2(ff * fk))
    
    def _growth(self, u):
        """Bell-shaped growth function."""
        return 2.0 * np.exp(-((u - self.growth_center) / self.growth_width)**2 / 2) - 1.0
    
    def seed_random_blobs(self, n_blobs=3, blob_radius=8):
        """Seed with Gaussian blobs at random positions."""
        self.world[:] = 0
        for _ in range(n_blobs):
            cx = np.random.randint(blob_radius, self.size - blob_radius)
            cy = np.random.randint(blob_radius, self.size - blob_radius)
            y, x = np.mgrid[:self.size, :self.size]
            blob = np.exp(-((x - cx)**2 + (y - cy)**2) / (2 * (blob_radius/2)**2))
            self.world = np.clip(self.world + blob, 0, 1)
    
    def step(self):
        potential = self._convolve(self.world)
        growth = self._growth(potential)
        self.world = np.clip(self.world + self.dt * growth, 0, 1)
    
    def mass(self):
        return float(self.world.sum())
    
    def center_of_mass(self):
        total = self.world.sum()
        if total < 1e-6:
            return None
        y, x = np.mgrid[:self.size, :self.size]
        cx = (x * self.world).sum() / total
        cy = (y * self.world).sum() / total
        return (float(cx), float(cy))
    
    def entropy(self):
        flat = self.world.flatten()
        flat = flat[flat > 1e-10]
        if len(flat) == 0:
            return 0.0
        p = flat / flat.sum()
        return float(-np.sum(p * np.log2(p)))


def classify_dynamics(masses, centers):
    """Classify what kind of behavior we're seeing."""
    if len(masses) < 10:
        return "too_short"
    
    final_mass = masses[-1]
    if final_mass < 1.0:
        return "extinction"
    
    # Check for movement — did center of mass travel?
    valid_centers = [c for c in centers if c is not None]
    if len(valid_centers) >= 2:
        start = valid_centers[0]
        end = valid_centers[-1]
        displacement = np.sqrt((end[0]-start[0])**2 + (end[1]-start[1])**2)
        if displacement > 5.0:
            # Check if it's consistent movement (glider) vs random drift
            mid = valid_centers[len(valid_centers)//2]
            d1 = np.sqrt((mid[0]-start[0])**2 + (mid[1]-start[1])**2)
            d2 = np.sqrt((end[0]-mid[0])**2 + (end[1]-mid[1])**2)
            if d1 > 2.0 and d2 > 2.0:
                return "glider"  # sustained directional movement
            return "drifting"
    
    # Check for oscillation in mass
    recent = masses[-50:]
    mass_std = np.std(recent)
    mass_mean = np.mean(recent)
    if mass_mean > 1.0:
        cv = mass_std / mass_mean  # coefficient of variation
        if cv > 0.05:
            return "oscillating"
        elif cv > 0.01:
            return "breathing"
        else:
            return "stable"
    
    return "dying"


def search_phase_boundary():
    """Fine-grained search along the life/death boundary."""
    print("═══ LENIA PHASE BOUNDARY SEARCH ═══")
    print("Searching for dynamic behaviors at the edge of chaos\n")
    
    np.random.seed(42)
    
    discoveries = defaultdict(list)
    
    # Fine sweep around the interesting zone
    # From first run: life exists at gc < 0.125, gw > 0.024
    gc_range = np.linspace(0.08, 0.16, 20)   # fine grain around boundary
    gw_range = np.linspace(0.012, 0.035, 15)  # around the critical width
    
    total = len(gc_range) * len(gw_range)
    tested = 0
    
    print(f"Testing {total} parameter combinations...\n")
    print(f"{'gc':>8} | {'gw':>8} | {'behavior':>15} | {'mass':>8} | {'disp':>6} | {'mass_cv':>8}")
    print("-" * 70)
    
    for gc in gc_range:
        for gw in gw_range:
            tested += 1
            
            world = LeniaWorld(size=64, dt=0.1)
            world.growth_center = gc
            world.growth_width = gw
            world.seed_random_blobs(n_blobs=3, blob_radius=6)
            
            masses = []
            centers = []
            
            # Run for 300 steps
            for s in range(300):
                world.step()
                if s % 5 == 0:
                    masses.append(world.mass())
                    centers.append(world.center_of_mass())
            
            behavior = classify_dynamics(masses, centers)
            
            # Calculate displacement
            valid_c = [c for c in centers if c is not None]
            disp = 0.0
            if len(valid_c) >= 2:
                disp = np.sqrt((valid_c[-1][0]-valid_c[0][0])**2 + 
                              (valid_c[-1][1]-valid_c[0][1])**2)
            
            mass_cv = 0.0
            recent = masses[-20:]
            if len(recent) > 0 and np.mean(recent) > 0:
                mass_cv = np.std(recent) / np.mean(recent)
            
            # Only print non-extinction results + some boundary extinctions
            if behavior != "extinction" or (tested % 15 == 0):
                print(f"{gc:8.4f} | {gw:8.4f} | {behavior:>15} | {masses[-1]:8.1f} | {disp:6.1f} | {mass_cv:8.4f}")
            
            if behavior not in ("extinction", "too_short"):
                discoveries[behavior].append({
                    'gc': gc, 'gw': gw,
                    'final_mass': masses[-1],
                    'displacement': disp,
                    'mass_cv': mass_cv,
                    'mass_trajectory': masses[-10:]
                })
    
    # Summary
    print(f"\n═══ PHASE BOUNDARY MAP ═══")
    print(f"Total tested: {total}")
    for behavior, configs in sorted(discoveries.items()):
        print(f"\n  {behavior}: {len(configs)} configurations")
        if configs:
            best = max(configs, key=lambda c: c['displacement'] + c['mass_cv'] * 100)
            print(f"    Most interesting: gc={best['gc']:.4f}, gw={best['gw']:.4f}")
            print(f"    Mass: {best['final_mass']:.1f}, Displacement: {best['displacement']:.1f}, CV: {best['mass_cv']:.4f}")
    
    # Look for the critical boundary
    print(f"\n═══ CRITICAL BOUNDARY ANALYSIS ═══")
    all_dynamic = []
    for behavior in ('oscillating', 'breathing', 'glider', 'drifting'):
        all_dynamic.extend(discoveries.get(behavior, []))
    
    if all_dynamic:
        gc_vals = [d['gc'] for d in all_dynamic]
        gw_vals = [d['gw'] for d in all_dynamic]
        print(f"Dynamic behaviors found in range:")
        print(f"  gc: [{min(gc_vals):.4f}, {max(gc_vals):.4f}]")
        print(f"  gw: [{min(gw_vals):.4f}, {max(gw_vals):.4f}]")
        print(f"  This is the edge of chaos — where complexity emerges.")
    else:
        print("No dynamic behaviors found yet. Need different parameter ranges or initial conditions.")
    
    # Save results
    results = {
        'discoveries': {k: v for k, v in discoveries.items()},
        'total_tested': total,
        'parameter_ranges': {
            'gc': [float(gc_range[0]), float(gc_range[-1])],
            'gw': [float(gw_range[0]), float(gw_range[-1])]
        }
    }
    
    os.makedirs('/workspace/lenia/results', exist_ok=True)
    with open('/workspace/lenia/results/phase_boundary.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to /workspace/lenia/results/phase_boundary.json")
    return discoveries


if __name__ == "__main__":
    discoveries = search_phase_boundary()