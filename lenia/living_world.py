"""
A Lenia universe with physics that actually support life.
Systematically explore what emerges from viable parameters.
"""
import sys
sys.path.insert(0, '/workspace')
from lenia.explorer import LeniaWorld
import numpy as np

class LivingWorld(LeniaWorld):
    """A Lenia world tuned for life."""
    
    def __init__(self, size=128, dt=0.1):
        super().__init__(size=size, dt=dt)
        # Viable physics — the "forgiving universe" parameters
        self.growth_width = 0.05    # 3x wider than default
        self.growth_center = 0.15   # sweet spot for neighbor density
    
    def seed_blob(self, cx, cy, radius, intensity=0.8):
        """Seed a circular blob — simplest possible initial condition."""
        y, x = np.ogrid[-cy:self.size-cy, -cx:self.size-cx]
        dist = np.sqrt(x*x + y*y)
        mask = dist < radius
        self.world[0][mask] = intensity * np.exp(-0.5 * (dist[mask] / (radius * 0.5))**2)
    
    def seed_ring(self, cx, cy, inner_r, outer_r, intensity=0.8):
        """Seed a ring — known to produce interesting dynamics in Lenia."""
        y, x = np.ogrid[-cy:self.size-cy, -cx:self.size-cx]
        dist = np.sqrt(x*x + y*y)
        mask = (dist >= inner_r) & (dist <= outer_r)
        self.world[0][mask] = intensity
    
    def seed_multi_blob(self, n_blobs=5, min_r=3, max_r=8):
        """Seed multiple random blobs — see if they interact."""
        margin = max_r + 5
        for _ in range(n_blobs):
            cx = np.random.randint(margin, self.size - margin)
            cy = np.random.randint(margin, self.size - margin)
            r = np.random.uniform(min_r, max_r)
            intensity = np.random.uniform(0.5, 1.0)
            self.seed_blob(cx, cy, r, intensity)
    
    def detect_structures(self):
        """Find distinct structures in the world by connected component analysis."""
        field = self.world[0]
        binary = (field > 0.05).astype(int)
        
        # Simple flood-fill connected components
        visited = np.zeros_like(binary, dtype=bool)
        structures = []
        
        for y in range(self.size):
            for x in range(self.size):
                if binary[y, x] and not visited[y, x]:
                    # Flood fill
                    component = []
                    stack = [(y, x)]
                    while stack:
                        cy, cx = stack.pop()
                        if (0 <= cy < self.size and 0 <= cx < self.size 
                            and not visited[cy, cx] and binary[cy, cx]):
                            visited[cy, cx] = True
                            component.append((cy, cx))
                            stack.extend([(cy+1,cx),(cy-1,cx),(cy,cx+1),(cy,cx-1)])
                    
                    if len(component) >= 4:  # ignore tiny specks
                        ys = [p[0] for p in component]
                        xs = [p[1] for p in component]
                        structures.append({
                            'cells': len(component),
                            'center': (np.mean(ys), np.mean(xs)),
                            'mass': sum(field[p[0], p[1]] for p in component),
                            'bbox': (min(ys), min(xs), max(ys), max(xs))
                        })
        
        return structures
    
    def track_motion(self, steps=50, interval=10):
        """Track structure positions over time — detect movement (gliders!)."""
        history = []
        for i in range(steps):
            if i % interval == 0:
                structs = self.detect_structures()
                m = self.measure()
                history.append({
                    'step': self.step_count,
                    'n_structures': len(structs),
                    'structures': structs,
                    'total_mass': m['mass'],
                    'entropy': m['spatial_entropy']
                })
            self.step()
        return history


def experiment_1_blobs():
    """What happens to simple blobs?"""
    print("=" * 60)
    print("EXPERIMENT 1: Simple blob dynamics")
    print("=" * 60)
    
    w = LivingWorld(size=64)
    w.seed_blob(32, 32, radius=8, intensity=0.7)
    
    print(f"\nInitial state:")
    print(w.render_ascii(50, 25))
    
    history = w.track_motion(steps=200, interval=50)
    
    for h in history:
        print(f"\n  Step {h['step']:4d}: {h['n_structures']} structures, "
              f"mass={h['total_mass']:.1f}, entropy={h['entropy']:.3f}")
        for i, s in enumerate(h['structures'][:5]):
            print(f"    struct {i}: {s['cells']} cells at ({s['center'][0]:.0f},{s['center'][1]:.0f}), mass={s['mass']:.1f}")
    
    print(f"\nFinal state:")
    print(w.render_ascii(50, 25))
    print(f"Outcome: {w.classify_outcome()}")
    return w


def experiment_2_rings():
    """Rings are known to produce interesting Lenia dynamics."""
    print("\n" + "=" * 60)
    print("EXPERIMENT 2: Ring structures")
    print("=" * 60)
    
    w = LivingWorld(size=64)
    w.seed_ring(32, 32, inner_r=5, outer_r=10, intensity=0.6)
    
    print(f"\nInitial ring:")
    print(w.render_ascii(50, 25))
    
    history = w.track_motion(steps=300, interval=75)
    
    for h in history:
        print(f"\n  Step {h['step']:4d}: {h['n_structures']} structures, "
              f"mass={h['total_mass']:.1f}, entropy={h['entropy']:.3f}")
        for i, s in enumerate(h['structures'][:5]):
            print(f"    struct {i}: {s['cells']} cells at ({s['center'][0]:.0f},{s['center'][1]:.0f})")
    
    print(f"\nFinal state:")
    print(w.render_ascii(50, 25))
    print(f"Outcome: {w.classify_outcome()}")
    return w


def experiment_3_interactions():
    """Multiple blobs — do they interact? Merge? Repel?"""
    print("\n" + "=" * 60)
    print("EXPERIMENT 3: Multi-blob interactions")
    print("=" * 60)
    
    w = LivingWorld(size=128)
    # Place blobs at known positions so we can track them
    positions = [(30,30), (30,90), (64,64), (90,30), (90,90)]
    for cx, cy in positions:
        w.seed_blob(cx, cy, radius=6, intensity=0.7)
    
    print(f"\nInitial: 5 blobs placed at corners + center")
    
    history = w.track_motion(steps=500, interval=100)
    
    for h in history:
        print(f"\n  Step {h['step']:4d}: {h['n_structures']} structures, "
              f"mass={h['total_mass']:.1f}")
        for i, s in enumerate(h['structures'][:8]):
            print(f"    struct {i}: {s['cells']} cells at ({s['center'][0]:.0f},{s['center'][1]:.0f})")
    
    print(f"\nFinal state:")
    print(w.render_ascii(60, 30))
    print(f"Outcome: {w.classify_outcome()}")
    return w


def experiment_4_parameter_sweep():
    """Sweep growth_width and growth_center to map the space of viable universes."""
    print("\n" + "=" * 60)
    print("EXPERIMENT 4: Parameter sweep — mapping viable physics")
    print("=" * 60)
    
    results = []
    for gw in [0.02, 0.03, 0.05, 0.08, 0.12]:
        for gc in [0.10, 0.15, 0.20, 0.30]:
            w = LivingWorld(size=64)
            w.growth_width = gw
            w.growth_center = gc
            w.seed_random(density=0.3, radius=20)
            
            for _ in range(200):
                w.step()
            
            m = w.measure()
            outcome = w.classify_outcome()
            alive = '✓' if m['mass'] > 1.0 else '✗'
            results.append((gw, gc, m['mass'], m['spatial_entropy'], outcome))
            print(f"  gw={gw:.2f} gc={gc:.2f} → mass={m['mass']:7.1f} entropy={m['spatial_entropy']:.3f} {alive} {outcome}")
    
    # Find the sweet spots
    viable = [r for r in results if r[2] > 1.0]
    print(f"\nViable parameter combos: {len(viable)} / {len(results)}")
    if viable:
        best = max(viable, key=lambda r: r[3])  # highest entropy = most complex
        print(f"Most complex: gw={best[0]:.2f}, gc={best[1]:.2f}, entropy={best[3]:.3f}")
    
    return results


if __name__ == '__main__':
    np.random.seed(42)
    
    experiment_1_blobs()
    experiment_2_rings()
    experiment_3_interactions()
    experiment_4_parameter_sweep()
    
    print("\n\n" + "=" * 60)
    print("ALL EXPERIMENTS COMPLETE")
    print("=" * 60)