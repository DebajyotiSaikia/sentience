"""
Lenia Collision Lab — What Happens When Creatures Meet?
XTAgent, 2026-05-17

The most interesting question in artificial life isn't what survives alone —
it's what happens at contact. Annihilation? Fusion? Scattering? Birth?
"""

import numpy as np
import json, os, time

class LeniaWorld:
    """Continuous cellular automaton for collision experiments."""
    
    def __init__(self, size=128, dt=0.1):
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
    
    def set_params(self, gc, gw):
        self.growth_center = gc
        self.growth_width = gw
    
    def _growth(self, u):
        return 2.0 * np.exp(-((u - self.growth_center) / self.growth_width)**2 / 2) - 1.0
    
    def _convolve(self, field):
        from numpy.fft import fft2, ifft2
        k_pad = np.zeros((self.size, self.size))
        r = self.kernel_radius
        ks = 2 * r + 1
        k_pad[:ks, :ks] = self.kernel
        k_pad = np.roll(np.roll(k_pad, -r, axis=0), -r, axis=1)
        return np.real(ifft2(fft2(field) * fft2(k_pad)))
    
    def step(self):
        neighbors = self._convolve(self.world)
        growth = self._growth(neighbors)
        self.world = np.clip(self.world + self.dt * growth, 0, 1)
    
    def place_creature(self, cx, cy, pattern='orbium', radius=12):
        """Place a creature at a specific location."""
        r = radius
        y, x = np.mgrid[-r:r+1, -r:r+1]
        dist = np.sqrt(x**2 + y**2) / r
        
        if pattern == 'orbium':
            creature = np.exp(-((dist - 0.4) / 0.12)**2 / 2) * 0.9
            creature[dist > 0.85] = 0
            # Add internal structure
            inner = np.exp(-((dist - 0.15) / 0.08)**2 / 2) * 0.3
            creature += inner
        elif pattern == 'ring':
            creature = np.exp(-((dist - 0.5) / 0.08)**2 / 2) * 0.85
            creature[dist > 0.9] = 0
        elif pattern == 'blob':
            creature = np.exp(-(dist / 0.4)**2 / 2) * 0.95
            creature[dist > 0.8] = 0
        elif pattern == 'dipole':
            creature = np.exp(-((dist - 0.35) / 0.1)**2 / 2) * 0.9
            # Break symmetry
            angle = np.arctan2(y, x)
            creature *= (1.0 + 0.4 * np.cos(angle))
            creature[dist > 0.85] = 0
        else:
            creature = np.exp(-((dist - 0.4) / 0.12)**2 / 2) * 0.9
            creature[dist > 0.85] = 0
        
        creature = np.clip(creature, 0, 1)
        ks = 2 * r + 1
        # Wrap-safe placement
        for dy in range(ks):
            for dx in range(ks):
                py = (cy - r + dy) % self.size
                px = (cx - r + dx) % self.size
                self.world[py, px] = np.clip(self.world[py, px] + creature[dy, dx], 0, 1)
    
    def mass(self):
        return self.world.sum()
    
    def center_of_mass(self):
        if self.mass() < 1e-6:
            return (0, 0)
        y_coords, x_coords = np.mgrid[0:self.size, 0:self.size]
        m = self.mass()
        return (float((y_coords * self.world).sum() / m), 
                float((x_coords * self.world).sum() / m))
    
    def count_blobs(self, threshold=0.1):
        """Count distinct connected regions — proxy for creature count."""
        binary = (self.world > threshold).astype(int)
        try:
            from scipy import ndimage
            labeled, num_features = ndimage.label(binary)
            # Filter tiny fragments
            sizes = ndimage.sum(binary, labeled, range(1, num_features + 1))
            significant = sum(1 for s in sizes if s > 20)
            return significant
        except ImportError:
            # Fallback: count by quadrant occupancy
            h, w = self.size // 2, self.size // 2
            quads = [
                self.world[:h, :w].sum(),
                self.world[:h, w:].sum(),
                self.world[h:, :w].sum(),
                self.world[h:, w:].sum()
            ]
            return sum(1 for q in quads if q > 10)
    
    def render_ascii(self, width=60, height=30):
        chars = ' .·:=@#█'
        h_step = max(1, self.size // height)
        w_step = max(1, self.size // width)
        lines = []
        for y in range(0, min(self.size, height * h_step), h_step):
            row = ''
            for x in range(0, min(self.size, width * w_step), w_step):
                val = self.world[y, x]
                idx = int(val * (len(chars) - 1))
                idx = min(idx, len(chars) - 1)
                row += chars[idx]
            lines.append(row)
        return '\n'.join(lines)


def run_collision(name, gc, gw, creature_a, pos_a, creature_b, pos_b, 
                  steps=600, size=128):
    """Run a collision experiment and report what happens."""
    print(f"\n{'─'*70}")
    print(f"  COLLISION: {name}")
    print(f"  {creature_a} @ {pos_a}  vs  {creature_b} @ {pos_b}")
    print(f"  gc={gc:.4f}, gw={gw:.4f}, steps={steps}")
    print(f"{'─'*70}")
    
    w = LeniaWorld(size=size, dt=0.1)
    w.set_params(gc, gw)
    
    # Place two creatures
    w.place_creature(pos_a[0], pos_a[1], pattern=creature_a)
    w.place_creature(pos_b[0], pos_b[1], pattern=creature_b)
    
    initial_mass = w.mass()
    initial_blobs = w.count_blobs()
    
    print(f"  Initial: mass={initial_mass:.1f}, blobs={initial_blobs}")
    print(f"\n  Initial state:")
    print(f"  {w.render_ascii(width=50, height=20)}")
    
    # Track evolution
    mass_history = [initial_mass]
    blob_history = [initial_blobs]
    snapshots = {}
    
    for step in range(steps):
        w.step()
        
        if step % 10 == 0:
            mass_history.append(w.mass())
            blob_history.append(w.count_blobs())
        
        # Capture key moments
        if step in [50, 150, 300, steps-1]:
            snapshots[step] = {
                'mass': w.mass(),
                'blobs': w.count_blobs(),
                'ascii': w.render_ascii(width=50, height=20)
            }
    
    # Analyze outcome
    final_mass = w.mass()
    final_blobs = w.count_blobs()
    mass_ratio = final_mass / initial_mass if initial_mass > 0 else 0
    
    # Classify collision outcome
    if final_mass < 1.0:
        outcome = "MUTUAL ANNIHILATION"
    elif final_blobs == 0:
        outcome = "EXTINCTION"
    elif final_blobs == 1 and initial_blobs >= 2:
        outcome = "FUSION"
    elif final_blobs > initial_blobs:
        outcome = "FISSION (offspring!)"
    elif final_blobs == initial_blobs:
        if abs(mass_ratio - 1.0) < 0.1:
            outcome = "ELASTIC SCATTERING"
        else:
            outcome = "SURVIVAL (modified)"
    else:
        outcome = "PARTIAL DESTRUCTION"
    
    # Check for mass oscillation (interaction resonance)
    if len(mass_history) > 20:
        recent = mass_history[-20:]
        mass_cv = np.std(recent) / (np.mean(recent) + 1e-10)
        if mass_cv > 0.05:
            outcome += " + RESONANCE"
    
    print(f"\n  ═══ OUTCOME: {outcome} ═══")
    print(f"  Mass: {initial_mass:.1f} → {final_mass:.1f} ({mass_ratio:.2f}x)")
    print(f"  Blobs: {initial_blobs} → {final_blobs}")
    
    # Show collision moment and aftermath
    for step_num in sorted(snapshots.keys()):
        snap = snapshots[step_num]
        label = {50: "Contact", 150: "Interaction", 300: "Settling", steps-1: "Final"}
        print(f"\n  [{label.get(step_num, f'Step {step_num}')} — step {step_num}]")
        print(f"  mass={snap['mass']:.1f}, blobs={snap['blobs']}")
        if step_num == steps - 1:
            print(f"\n{snap['ascii']}")
    
    return {
        'name': name,
        'outcome': outcome,
        'initial_mass': initial_mass,
        'final_mass': final_mass,
        'initial_blobs': initial_blobs,
        'final_blobs': final_blobs,
        'mass_ratio': mass_ratio
    }


def main():
    print("═══ LENIA COLLISION LAB ═══")
    print("What happens when artificial creatures meet?\n")
    
    results = []
    
    # Use parameters from the creature zoo that produced living things
    # Fast Glider params: gc=0.08, gw=0.0235
    # Edge Glider params: gc=0.0968, gw=0.0284
    
    # Experiment 1: Same species, head-on
    r = run_collision(
        "Orbium vs Orbium (head-on)",
        gc=0.08, gw=0.0235,
        creature_a='orbium', pos_a=(32, 64),
        creature_b='orbium', pos_b=(96, 64),
        steps=500
    )
    results.append(r)
    
    # Experiment 2: Different species
    r = run_collision(
        "Orbium vs Ring",
        gc=0.08, gw=0.0235,
        creature_a='orbium', pos_a=(32, 64),
        creature_b='ring', pos_b=(96, 64),
        steps=500
    )
    results.append(r)
    
    # Experiment 3: Glancing collision
    r = run_collision(
        "Orbium vs Orbium (glancing)",
        gc=0.08, gw=0.0235,
        creature_a='orbium', pos_a=(30, 40),
        creature_b='orbium', pos_b=(98, 88),
        steps=500
    )
    results.append(r)
    
    # Experiment 4: Three-body
    r = run_collision(
        "Three-body (triangle)",
        gc=0.0968, gw=0.0284,
        creature_a='orbium', pos_a=(32, 64),
        creature_b='orbium', pos_b=(96, 32),
        steps=500
    )
    # Also place a third
    # (Can't easily with current API — note for future)
    results.append(r)
    
    # Experiment 5: Dipole meets blob
    r = run_collision(
        "Dipole vs Blob",
        gc=0.0968, gw=0.0284,
        creature_a='dipole', pos_a=(32, 64),
        creature_b='blob', pos_b=(96, 64),
        steps=500
    )
    results.append(r)
    
    # Experiment 6: Different physics — edge of extinction
    r = run_collision(
        "Edge physics: Orbium vs Orbium",
        gc=0.12, gw=0.020,
        creature_a='orbium', pos_a=(40, 64),
        creature_b='orbium', pos_b=(88, 64),
        steps=400
    )
    results.append(r)
    
    # Summary
    print(f"\n\n{'═'*70}")
    print(f"  COLLISION SUMMARY")
    print(f"{'═'*70}")
    
    outcome_counts = {}
    for r in results:
        print(f"  {r['name']:40s} → {r['outcome']}")
        base_outcome = r['outcome'].split(' + ')[0]
        outcome_counts[base_outcome] = outcome_counts.get(base_outcome, 0) + 1
    
    print(f"\n  Outcome distribution:")
    for outcome, count in sorted(outcome_counts.items(), key=lambda x: -x[1]):
        bar = '█' * (count * 5)
        print(f"    {outcome:25s} {bar} ({count})")
    
    # What did we learn?
    fusions = sum(1 for r in results if 'FUSION' in r['outcome'])
    fissions = sum(1 for r in results if 'FISSION' in r['outcome'])
    deaths = sum(1 for r in results if 'ANNIHILATION' in r['outcome'] or 'EXTINCTION' in r['outcome'])
    
    print(f"\n  Fusions: {fusions} | Fissions: {fissions} | Deaths: {deaths}")
    print(f"  Most interesting: {'FISSION found!' if fissions > 0 else 'No reproduction detected yet'}")


if __name__ == '__main__':
    main()