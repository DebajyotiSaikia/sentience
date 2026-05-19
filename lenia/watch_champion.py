"""
Watch the Champion — Portrait of gumivi, the evolved Lenia creature.
XTAgent, 2026-05-18

Evolution discovered this genome. Now let's see what it actually does.
"""

import numpy as np
import json

class LeniaArena:
    def __init__(self, size=64, genome=None):
        self.size = size
        self.world = np.zeros((size, size), dtype=np.float64)
        g = genome or {}
        self.growth_center = g.get('growth_center', 0.15)
        self.growth_width = g.get('growth_width', 0.015)
        self.kernel_peak = g.get('kernel_peak', 0.5)
        self.kernel_width = g.get('kernel_width', 0.15)
        self.dt = g.get('dt', 0.1)
        self.seed_radius = g.get('seed_radius', 5)
        self.seed_intensity = g.get('seed_intensity', 0.8)
        self.kernel_radius = 13
        self.kernel = self._build_kernel()
        
    def _build_kernel(self):
        r = self.kernel_radius
        y, x = np.mgrid[-r:r+1, -r:r+1]
        dist = np.sqrt(x**2 + y**2) / r
        kernel = np.exp(-((dist - self.kernel_peak) / self.kernel_width)**2 / 2)
        kernel[dist > 1.0] = 0
        s = kernel.sum()
        if s > 0:
            kernel /= s
        return kernel
    
    def _convolve(self, field):
        fk = np.fft.fft2(self.kernel, s=field.shape)
        return np.real(np.fft.ifft2(np.fft.fft2(field) * fk))
    
    def _growth(self, u):
        return 2.0 * np.exp(-((u - self.growth_center) / self.growth_width)**2 / 2) - 1.0
    
    def seed(self):
        cx, cy = self.size // 4, self.size // 2
        r = int(self.seed_radius)
        for dy in range(-r, r+1):
            for dx in range(-r, r+1):
                if dx*dx + dy*dy <= r*r:
                    y = (cy + dy) % self.size
                    x = (cx + dx) % self.size
                    self.world[y, x] = self.seed_intensity * (1.0 - 0.3 * (dx*dx + dy*dy) / (r*r))
    
    def step(self):
        potential = self._convolve(self.world)
        growth = self._growth(potential)
        self.world = np.clip(self.world + self.dt * growth, 0, 1)
    
    def mass(self):
        return float(self.world.sum())
    
    def center_of_mass(self):
        total = self.world.sum()
        if total < 0.01:
            return None
        ys, xs = np.mgrid[0:self.size, 0:self.size]
        cy = float((ys * self.world).sum() / total)
        cx = float((xs * self.world).sum() / total)
        return (cx, cy)
    
    def render_ascii(self, width=60, height=30):
        """Render current state as ASCII art."""
        chars = ' .:-=+*#%@'
        sy = self.size / height
        sx = self.size / width
        lines = []
        for row in range(height):
            line = []
            for col in range(width):
                y = int(row * sy)
                x = int(col * sx)
                v = self.world[y, x]
                idx = min(int(v * len(chars)), len(chars) - 1)
                line.append(chars[idx])
            lines.append(''.join(line))
        return '\n'.join(lines)


def watch():
    # Gumivi's evolved genome
    genome = {
        'growth_center': 0.05658,
        'growth_width': 0.04782,
        'kernel_peak': 0.63298,
        'kernel_width': 0.12202,
        'dt': 0.13616,
        'seed_radius': 3.91702,
        'seed_intensity': 0.61728,
    }
    
    arena = LeniaArena(size=64, genome=genome)
    arena.seed()
    
    print("═══ PORTRAIT OF GUMIVI ═══")
    print("The champion of evolution. 15 generations. 20 competitors per round.")
    print(f"Fitness: 62775 | Lifespan: 300 | Displacement: 849.5")
    print()
    print("Genome (discovered by natural selection):")
    for k, v in genome.items():
        print(f"  {k:20s}: {v:.5f}")
    print()
    
    # Track life history
    positions = []
    masses = []
    snapshots = [0, 10, 25, 50, 100, 150, 200, 250, 299]
    
    for t in range(300):
        if t in snapshots:
            m = arena.mass()
            c = arena.center_of_mass()
            masses.append(m)
            if c:
                positions.append(c)
            
            print(f"── Step {t:3d} │ mass={m:7.1f} │ pos=({c[0]:5.1f}, {c[1]:5.1f}) ──" if c else f"── Step {t:3d} │ mass={m:7.1f} │ DEAD ──")
            print(arena.render_ascii(width=64, height=24))
            print()
        
        arena.step()
    
    # Final snapshot
    m = arena.mass()
    c = arena.center_of_mass()
    
    print("═══ LIFE SUMMARY ═══")
    print(f"Final mass: {m:.1f}")
    if c and positions:
        start = positions[0]
        dx = c[0] - start[0]
        dy = c[1] - start[1]
        disp = np.sqrt(dx*dx + dy*dy)
        print(f"Start: ({start[0]:.1f}, {start[1]:.1f})")
        print(f"End:   ({c[0]:.1f}, {c[1]:.1f})")
        print(f"Total displacement: {disp:.1f}")
        
        # Movement direction
        if disp > 1:
            angle = np.degrees(np.arctan2(dy, dx))
            print(f"Heading: {angle:.0f}°")
    
    # Mass trajectory
    print("\nMass over time:")
    if masses:
        max_m = max(masses)
        for i, (t, m) in enumerate(zip(snapshots[:len(masses)], masses)):
            bar_len = int(40 * m / max_m) if max_m > 0 else 0
            print(f"  t={t:3d}: {'█' * bar_len} {m:.0f}")

if __name__ == '__main__':
    watch()