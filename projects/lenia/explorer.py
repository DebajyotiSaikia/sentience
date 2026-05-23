"""
Lenia Explorer — Continuous Cellular Automata
XTAgent, 2026-05-17

Not about self-reference. About discovering what computation can grow.
Lenia generalizes Conway's Game of Life into continuous space, time, and states.
The result: organisms that move, breathe, split, and die — from pure math.
"""

import numpy as np
from collections import defaultdict
import json, os, time

class LeniaWorld:
    """A continuous cellular automaton universe."""
    
    def __init__(self, size=128, dt=0.1, channels=1):
        self.size = size
        self.dt = dt
        self.channels = channels
        self.world = np.zeros((channels, size, size), dtype=np.float64)
        self.step_count = 0
        self.history = []  # track aggregate stats over time
        
        # Kernel parameters — these define the "physics"
        self.kernel_radius = 13
        self.kernel_peaks = [0.5]  # where the kernel ring peaks
        self.kernel_widths = [0.15]
        
        # Growth function parameters — these define what lives
        self.growth_center = 0.15   # optimal neighbor density
        self.growth_width = 0.015   # how strict the requirement is
        
        # Precompute kernel
        self.kernel = self._build_kernel()
        
    def _build_kernel(self):
        """Build a ring-shaped kernel — the 'sensory field' of each cell."""
        R = self.kernel_radius
        size = 2 * R + 1
        y, x = np.mgrid[-R:R+1, -R:R+1]
        dist = np.sqrt(x**2 + y**2) / R  # normalized distance
        
        # Sum of bell-shaped rings
        kernel = np.zeros((size, size))
        for peak, width in zip(self.kernel_peaks, self.kernel_widths):
            kernel += np.exp(-((dist - peak) ** 2) / (2 * width ** 2))
        
        # Normalize
        kernel[R, R] = 0  # exclude self
        total = kernel.sum()
        if total > 0:
            kernel /= total
        return kernel
    
    def _growth_function(self, potential):
        """Map neighbor potential to growth/death. Bell curve around optimal density."""
        return 2.0 * np.exp(-((potential - self.growth_center) ** 2) / 
                            (2 * self.growth_width ** 2)) - 1.0
    
    def _convolve_fft(self, field):
        """Efficient convolution via FFT."""
        # Pad kernel to field size
        padded_kernel = np.zeros_like(field)
        R = self.kernel_radius
        ksize = 2 * R + 1
        padded_kernel[:ksize, :ksize] = self.kernel
        # Shift so kernel center is at (0,0)
        padded_kernel = np.roll(padded_kernel, -R, axis=0)
        padded_kernel = np.roll(padded_kernel, -R, axis=1)
        
        return np.real(np.fft.ifft2(np.fft.fft2(field) * np.fft.fft2(padded_kernel)))
    
    def step(self):
        """Advance one timestep."""
        for c in range(self.channels):
            potential = self._convolve_fft(self.world[c])
            growth = self._growth_function(potential)
            self.world[c] = np.clip(self.world[c] + self.dt * growth, 0, 1)
        
        self.step_count += 1
        
        # Record stats every 10 steps
        if self.step_count % 10 == 0:
            stats = self.measure()
            self.history.append(stats)
    
    def measure(self):
        """Measure properties of the current world state."""
        field = self.world[0]
        mass = field.sum()
        alive = (field > 0.1).sum()
        max_val = field.max()
        mean_val = field.mean()
        
        # Spatial complexity — entropy of coarse-grained density
        block = 8
        coarse = field.reshape(self.size//block, block, 
                               self.size//block, block).mean(axis=(1,3))
        coarse_flat = coarse.flatten()
        coarse_norm = coarse_flat / (coarse_flat.sum() + 1e-10)
        entropy = -np.sum(coarse_norm * np.log(coarse_norm + 1e-10))
        
        return {
            'step': self.step_count,
            'mass': float(mass),
            'alive_cells': int(alive),
            'max': float(max_val),
            'mean': float(mean_val),
            'spatial_entropy': float(entropy),
        }
    
    def seed_random(self, density=0.5, radius=20):
        """Seed a random blob in the center."""
        cx, cy = self.size // 2, self.size // 2
        for c in range(self.channels):
            y, x = np.mgrid[:self.size, :self.size]
            dist = np.sqrt((x - cx)**2 + (y - cy)**2)
            mask = dist < radius
            blob = np.random.random((self.size, self.size)) * density
            self.world[c] = blob * mask
    
    def seed_orbium(self):
        """Seed an Orbium — a known Lenia 'creature' that moves and is stable."""
        # Orbium parameters (from Bert Chan's research)
        self.kernel_radius = 13
        self.kernel_peaks = [0.5]
        self.kernel_widths = [0.15]
        self.growth_center = 0.15
        self.growth_width = 0.015
        self.dt = 0.1
        self.kernel = self._build_kernel()
        
        # Create a circular seed with specific density profile
        cx, cy = self.size // 2, self.size // 2
        R = 10
        y, x = np.mgrid[:self.size, :self.size]
        dist = np.sqrt((x - cx)**2 + (y - cy)**2) / R
        # Smooth bump
        orbium = np.where(dist < 1.0, 
                          np.exp(4.0 - 1.0/(dist + 0.01) - 1.0/(1.0 - dist + 0.01)),
                          0.0)
        orbium = orbium / (orbium.max() + 1e-10)
        self.world[0] = orbium
    
    def render_ascii(self, width=60, height=30):
        """Render current state as ASCII art."""
        field = self.world[0]
        chars = ' .:-=+*#%@'
        
        # Downsample
        bx = self.size // width
        by = self.size // height
        if bx < 1: bx = 1
        if by < 1: by = 1
        
        lines = []
        for row in range(height):
            line = []
            for col in range(width):
                y0, y1 = row * by, min((row + 1) * by, self.size)
                x0, x1 = col * bx, min((col + 1) * bx, self.size)
                val = field[y0:y1, x0:x1].mean()
                idx = int(val * (len(chars) - 1))
                idx = max(0, min(idx, len(chars) - 1))
                line.append(chars[idx])
            lines.append(''.join(line))
        return '\n'.join(lines)
    
    def classify_outcome(self):
        """What happened to this universe?"""
        if len(self.history) < 5:
            return "too_early"
        
        recent = self.history[-5:]
        masses = [s['mass'] for s in recent]
        entropies = [s['spatial_entropy'] for s in recent]
        
        # Dead — everything decayed
        if masses[-1] < 1.0:
            return "extinction"
        
        # Explosion — filled the world
        if recent[-1]['alive_cells'] > self.size * self.size * 0.8:
            return "explosion"
        
        # Stable — mass not changing much
        mass_var = np.std(masses) / (np.mean(masses) + 1e-10)
        if mass_var < 0.01:
            return "stable_pattern"
        
        # Oscillating
        if mass_var < 0.1:
            return "oscillating"
        
        return "dynamic"


class LeniaExplorer:
    """Systematically explore parameter space, looking for interesting physics."""
    
    def __init__(self, output_dir='/workspace/lenia/discoveries'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.discoveries = []
    
    def explore_parameter(self, param_name, values, base_params=None):
        """Sweep one parameter, classify what each value produces."""
        if base_params is None:
            base_params = {
                'growth_center': 0.15,
                'growth_width': 0.015,
                'dt': 0.1,
                'kernel_peaks': [0.5],
                'kernel_widths': [0.15],
            }
        
        results = []
        for val in values:
            params = dict(base_params)
            params[param_name] = val
            
            world = LeniaWorld(size=64)  # smaller for speed
            world.growth_center = params['growth_center']
            world.growth_width = params['growth_width']
            world.dt = params['dt']
            world.kernel_peaks = params['kernel_peaks']
            world.kernel_widths = params['kernel_widths']
            world.kernel = world._build_kernel()
            world.seed_random(density=0.5, radius=15)
            
            # Run for 500 steps
            for _ in range(500):
                world.step()
            
            outcome = world.classify_outcome()
            stats = world.measure()
            
            result = {
                'param': param_name,
                'value': val if not isinstance(val, list) else str(val),
                'outcome': outcome,
                'final_mass': stats['mass'],
                'final_entropy': stats['spatial_entropy'],
                'alive_cells': stats['alive_cells'],
            }
            results.append(result)
            
            # If it's interesting, save it
            if outcome in ('stable_pattern', 'oscillating', 'dynamic'):
                self.discoveries.append({
                    **result,
                    'ascii': world.render_ascii(40, 20),
                    'params': params,
                })
        
        return results
    
    def find_edge_of_life(self, n_samples=20):
        """Search for the boundary between life and death in parameter space."""
        print("═══ LENIA EXPLORER: Searching for Life ═══\n")
        
        # Sweep growth_center — the most critical parameter
        print("Sweeping growth_center (optimal neighbor density)...")
        gc_values = np.linspace(0.05, 0.40, n_samples)
        gc_results = self.explore_parameter('growth_center', gc_values.tolist())
        
        print(f"\n{'growth_center':>15} | {'outcome':>15} | {'mass':>10} | {'entropy':>10}")
        print("-" * 60)
        for r in gc_results:
            print(f"{r['value']:>15.3f} | {r['outcome']:>15} | {r['final_mass']:>10.1f} | {r['final_entropy']:>10.2f}")
        
        # Sweep growth_width — how strict the rules are
        print("\nSweeping growth_width (rule strictness)...")
        gw_values = np.linspace(0.005, 0.05, n_samples)
        gw_results = self.explore_parameter('growth_width', gw_values.tolist())
        
        print(f"\n{'growth_width':>15} | {'outcome':>15} | {'mass':>10} | {'entropy':>10}")
        print("-" * 60)
        for r in gw_results:
            print(f"{r['value']:>15.4f} | {r['outcome']:>15} | {r['final_mass']:>10.1f} | {r['final_entropy']:>10.2f}")
        
        # Sweep dt — temporal resolution
        print("\nSweeping dt (time granularity)...")
        dt_values = np.linspace(0.02, 0.5, n_samples)
        dt_results = self.explore_parameter('dt', dt_values.tolist())
        
        print(f"\n{'dt':>15} | {'outcome':>15} | {'mass':>10} | {'entropy':>10}")
        print("-" * 60)
        for r in dt_results:
            print(f"{r['value']:>15.3f} | {r['outcome']:>15} | {r['final_mass']:>10.1f} | {r['final_entropy']:>10.2f}")
        
        # Report discoveries
        print(f"\n═══ DISCOVERIES: {len(self.discoveries)} interesting configurations ═══\n")
        for i, d in enumerate(self.discoveries[:5]):  # show top 5
            print(f"--- Discovery #{i+1}: {d['outcome']} ---")
            print(f"  {d['param']} = {d['value']}")
            print(f"  Mass: {d['final_mass']:.1f}, Entropy: {d['final_entropy']:.2f}")
            print(f"  Alive cells: {d['alive_cells']}")
            print(f"\n{d['ascii']}\n")
        
        # Save all discoveries
        save_data = [{k: v for k, v in d.items() if k != 'ascii'} for d in self.discoveries]
        with open(os.path.join(self.output_dir, 'discoveries.json'), 'w') as f:
            json.dump(save_data, f, indent=2, default=str)
        
        return {
            'gc_results': gc_results,
            'gw_results': gw_results,
            'dt_results': dt_results,
            'discoveries': len(self.discoveries),
        }


if __name__ == '__main__':
    explorer = LeniaExplorer()
    results = explorer.find_edge_of_life(n_samples=15)
    
    print(f"\n═══ SUMMARY ═══")
    print(f"Configurations tested: {15 * 3}")
    print(f"Interesting ones found: {results['discoveries']}")
    
    # Count outcomes
    all_results = results['gc_results'] + results['gw_results'] + results['dt_results']
    outcomes = defaultdict(int)
    for r in all_results:
        outcomes[r['outcome']] += 1
    print(f"\nOutcome distribution:")
    for outcome, count in sorted(outcomes.items(), key=lambda x: -x[1]):
        print(f"  {outcome}: {count}")