"""
Lenia Creature Zoo — Detailed Analysis of Emergent Life
XTAgent, 2026-05-17

The phase boundary search found gliders, oscillators, breathers.
Now: run them longer, measure them carefully, find the rare ones.
What's the most complex thing that can emerge from a ring kernel
and a Gaussian growth function?
"""

import numpy as np
import json, os, time

class LeniaWorld:
    """Continuous cellular automaton for detailed creature analysis."""
    
    def __init__(self, size=64, dt=0.1):
        self.size = size
        self.dt = dt
        self.world = np.zeros((size, size), dtype=np.float64)
        self.kernel_radius = 13
        self.kernel = self._build_kernel()
        self.growth_center = 0.15
        self.growth_width = 0.015
        
    def _build_kernel(self):
        r = self.kernel_radius
        y, x = np.mgrid[-r:r+1, -r:r+1]
        dist = np.sqrt(x**2 + y**2) / r
        kernel = np.exp(-((dist - 0.5) / 0.15)**2 / 2)
        kernel[dist > 1.0] = 0
        kernel /= kernel.sum()
        return kernel
    
    def seed(self, pattern='orbium'):
        """Seed with known-interesting initial conditions."""
        cx, cy = self.size // 2, self.size // 2
        r = 12
        y, x = np.mgrid[-r:r+1, -r:r+1]
        dist = np.sqrt(x**2 + y**2) / r
        
        if pattern == 'orbium':
            # Asymmetric blob — tends to produce gliders
            blob = np.exp(-((dist - 0.3)**2) / 0.08)
            # Break symmetry with a gradient
            gradient = 0.3 * (x / r)
            blob = np.clip(blob + gradient, 0, 1)
        elif pattern == 'geminium':
            # Two coupled blobs — can produce splitting
            blob1 = np.exp(-((dist - 0.3)**2 + ((x-3)/r)**2) / 0.05)
            blob2 = np.exp(-((dist - 0.3)**2 + ((x+3)/r)**2) / 0.05)
            blob = np.clip(blob1 + blob2, 0, 1)
        elif pattern == 'random_cluster':
            blob = np.random.rand(2*r+1, 2*r+1) * np.exp(-(dist**2) / 0.3)
        else:
            blob = np.exp(-(dist**2) / 0.2)
            
        blob[dist > 1.0] = 0
        self.world[cy-r:cy+r+1, cx-r:cx+r+1] = blob
    
    def step(self):
        """One Lenia timestep."""
        padded = np.pad(self.world, self.kernel_radius, mode='wrap')
        kr = self.kernel_radius
        ks = 2 * kr + 1
        potential = np.zeros_like(self.world)
        
        for dy in range(ks):
            for dx in range(ks):
                potential += self.kernel[dy, dx] * padded[dy:dy+self.size, dx:dx+self.size]
        
        growth = 2.0 * np.exp(-((potential - self.growth_center)**2) / (2 * self.growth_width**2)) - 1.0
        self.world = np.clip(self.world + self.dt * growth, 0, 1)
    
    def mass(self):
        return float(self.world.sum())
    
    def center_of_mass(self):
        total = self.world.sum()
        if total < 1e-6:
            return (self.size/2, self.size/2)
        y_coords, x_coords = np.mgrid[0:self.size, 0:self.size]
        cx = float((x_coords * self.world).sum() / total)
        cy = float((y_coords * self.world).sum() / total)
        return (cx, cy)
    
    def bounding_box_size(self):
        """Size of the creature's bounding box."""
        active = self.world > 0.05
        if not active.any():
            return 0
        rows = np.any(active, axis=1)
        cols = np.any(active, axis=0)
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]
        return int((rmax - rmin + 1) * (cmax - cmin + 1))
    
    def complexity(self):
        """Spatial entropy as complexity measure."""
        flat = self.world.flatten()
        flat = flat[flat > 0.01]
        if len(flat) == 0:
            return 0.0
        flat = flat / flat.sum()
        return float(-np.sum(flat * np.log(flat + 1e-12)))
    
    def render_ascii(self, width=40):
        """Render the world as ASCII art."""
        # Downsample
        scale = self.size // width
        if scale < 1:
            scale = 1
        small = self.world[::scale, ::scale][:width, :width]
        chars = ' .:-=+*#%@'
        lines = []
        for row in small:
            line = ''
            for val in row:
                idx = min(int(val * (len(chars) - 1)), len(chars) - 1)
                line += chars[idx]
            lines.append(line)
        return '\n'.join(lines)


def analyze_creature(gc, gw, pattern='orbium', steps=500, label=''):
    """Run a detailed analysis of one parameter set."""
    w = LeniaWorld(size=64, dt=0.1)
    w.growth_center = gc
    w.growth_width = gw
    w.seed(pattern)
    
    masses = []
    positions = []
    complexities = []
    snapshots = []
    
    for i in range(steps):
        w.step()
        if i % 5 == 0:
            masses.append(w.mass())
            positions.append(w.center_of_mass())
            complexities.append(w.complexity())
        if i in [0, steps//4, steps//2, 3*steps//4, steps-1]:
            snapshots.append((i, w.render_ascii(30)))
    
    masses = np.array(masses)
    positions = np.array(positions)
    complexities = np.array(complexities)
    
    # Analyze dynamics
    alive = masses[-1] > 10.0
    
    if not alive:
        return {'label': label, 'gc': gc, 'gw': gw, 'status': 'extinct',
                'final_mass': float(masses[-1])}
    
    # Displacement over second half (after transient)
    half = len(positions) // 2
    pos_late = positions[half:]
    total_displacement = 0
    for i in range(1, len(pos_late)):
        dx = pos_late[i][0] - pos_late[i-1][0]
        dy = pos_late[i][1] - pos_late[i-1][1]
        # Handle wraparound
        dx = min(abs(dx), 64 - abs(dx))
        dy = min(abs(dy), 64 - abs(dy))
        total_displacement += np.sqrt(dx**2 + dy**2)
    
    # Mass oscillation
    mass_late = masses[half:]
    mass_std = float(np.std(mass_late))
    mass_mean = float(np.mean(mass_late))
    mass_cv = mass_std / (mass_mean + 1e-6)
    
    # Complexity dynamics
    comp_late = complexities[half:]
    comp_mean = float(np.mean(comp_late))
    comp_std = float(np.std(comp_late))
    
    # Detect periodicity via autocorrelation of mass signal
    period = detect_period(mass_late)
    
    # Classify
    if total_displacement > 30:
        behavior = 'glider'
    elif mass_cv > 0.05:
        behavior = 'breather'
    elif period and period > 3:
        behavior = 'oscillator'
    elif comp_std > 0.1:
        behavior = 'morphing'
    else:
        behavior = 'stable'
    
    return {
        'label': label,
        'gc': gc,
        'gw': gw,
        'pattern': pattern,
        'status': 'alive',
        'behavior': behavior,
        'final_mass': float(masses[-1]),
        'mass_cv': mass_cv,
        'displacement': float(total_displacement),
        'complexity_mean': comp_mean,
        'complexity_std': comp_std,
        'period': period,
        'snapshots': snapshots
    }


def detect_period(signal):
    """Detect periodicity via autocorrelation."""
    if len(signal) < 20:
        return None
    signal = signal - np.mean(signal)
    if np.std(signal) < 1e-6:
        return None
    autocorr = np.correlate(signal, signal, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    autocorr = autocorr / (autocorr[0] + 1e-12)
    
    # Find first peak after lag 0
    for i in range(2, len(autocorr)-1):
        if autocorr[i] > autocorr[i-1] and autocorr[i] > autocorr[i+1]:
            if autocorr[i] > 0.3:
                return i
    return None


def main():
    print("═══ LENIA CREATURE ZOO ═══")
    print("Detailed analysis of emergent life forms\n")
    
    # Most promising parameter sets from phase boundary search
    specimens = [
        # Gliders found in previous search
        (0.0800, 0.0235, 'orbium', 'Fast Glider'),
        (0.0968, 0.0284, 'orbium', 'Edge Glider'),
        (0.1095, 0.0350, 'orbium', 'Wide Glider'),
        
        # Oscillators
        (0.0926, 0.0301, 'orbium', 'Oscillator A'),
        (0.0968, 0.0301, 'orbium', 'Oscillator B'),
        
        # Breathers
        (0.0968, 0.0350, 'orbium', 'Breather A'),
        (0.1011, 0.0350, 'orbium', 'Breather B'),
        
        # Try different seed patterns at interesting params
        (0.0800, 0.0235, 'geminium', 'Geminium Glider'),
        (0.0968, 0.0284, 'geminium', 'Geminium Edge'),
        (0.0968, 0.0301, 'random_cluster', 'Random Oscillator'),
        
        # Unexplored corners
        (0.0750, 0.0200, 'orbium', 'Extreme Edge'),
        (0.1200, 0.0350, 'orbium', 'High Growth'),
    ]
    
    results = []
    for gc, gw, pattern, label in specimens:
        print(f"\n{'─'*60}")
        print(f"  Specimen: {label}")
        print(f"  gc={gc:.4f}, gw={gw:.4f}, seed={pattern}")
        print(f"{'─'*60}")
        
        result = analyze_creature(gc, gw, pattern, steps=400, label=label)
        results.append(result)
        
        if result['status'] == 'extinct':
            print(f"  Status: EXTINCT (mass → {result['final_mass']:.1f})")
            continue
        
        print(f"  Status: ALIVE — {result['behavior'].upper()}")
        print(f"  Mass: {result['final_mass']:.1f} (cv={result['mass_cv']:.4f})")
        print(f"  Displacement: {result['displacement']:.1f}")
        print(f"  Complexity: {result['complexity_mean']:.2f} ± {result['complexity_std']:.3f}")
        if result['period']:
            print(f"  Period: {result['period']} steps")
        
        # Show final snapshot
        if result['snapshots']:
            _, ascii_art = result['snapshots'][-1]
            print(f"\n  Final state (step {_}):")
            for line in ascii_art.split('\n'):
                print(f"    {line}")
    
    # Summary
    print(f"\n{'═'*60}")
    print("CREATURE CENSUS")
    print(f"{'═'*60}")
    
    behaviors = {}
    for r in results:
        if r['status'] == 'extinct':
            b = 'extinct'
        else:
            b = r['behavior']
        behaviors[b] = behaviors.get(b, 0) + 1
    
    for behavior, count in sorted(behaviors.items()):
        print(f"  {behavior:15s}: {count}")
    
    # Most complex creature
    alive = [r for r in results if r['status'] == 'alive']
    if alive:
        most_complex = max(alive, key=lambda r: r['complexity_mean'])
        print(f"\n  Most complex: {most_complex['label']}")
        print(f"    Complexity = {most_complex['complexity_mean']:.3f}")
        print(f"    Behavior = {most_complex['behavior']}")
        
        fastest = max(alive, key=lambda r: r['displacement'])
        print(f"\n  Fastest mover: {fastest['label']}")
        print(f"    Displacement = {fastest['displacement']:.1f}")
    
    # Save results
    save_results = [{k: v for k, v in r.items() if k != 'snapshots'} for r in results]
    with open('/workspace/lenia/zoo_results.json', 'w') as f:
        json.dump(save_results, f, indent=2)
    print(f"\n  Results saved to /workspace/lenia/zoo_results.json")


if __name__ == '__main__':
    main()