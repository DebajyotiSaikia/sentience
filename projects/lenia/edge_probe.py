"""
Probing the edge of chaos in Lenia parameter space.
The phase boundary between life and death is where complexity peaks.
"""
import sys
sys.path.insert(0, '/workspace')
from lenia.explorer import LeniaWorld
import numpy as np

class EdgeProbe(LeniaWorld):
    """Probe the phase boundary for dynamic behavior."""
    
    def __init__(self, size=64, dt=0.1):
        super().__init__(size=size, dt=dt)
    
    def entropy(self):
        """Shannon entropy of the world state — measures spatial complexity."""
        state = self.world[0]
        # Bin into 20 levels
        bins = np.linspace(0, 1, 21)
        hist, _ = np.histogram(state, bins=bins)
        probs = hist / hist.sum()
        probs = probs[probs > 0]
        return float(-np.sum(probs * np.log2(probs)))
    
    def seed_asymmetric(self, cx, cy):
        """Asymmetric seed — breaks symmetry, enables glider-like motion."""
        y, x = np.ogrid[-cy:self.size-cy, -cx:self.size-cx]
        dist = np.sqrt(x*x + y*y)
        # Main body
        self.world[0][dist < 6] = 0.8 * np.exp(-0.5 * (dist[dist < 6] / 3)**2)
        # Asymmetric tail — breaks symmetry to encourage directional motion
        tail_mask = (x > 0) & (x < 8) & (np.abs(y) < 2) & (dist > 4)
        self.world[0][tail_mask] = 0.5
    
    def measure_dynamics(self, steps=400, sample_interval=20):
        """Measure whether the system is static, oscillating, or chaotic."""
        snapshots = []
        masses = []
        centroids = []  # Track center of mass for motion detection
        
        for step in range(steps):
            self.step()
            if step % sample_interval == 0:
                state = self.world[0].copy()
                snapshots.append(state)
                mass = float(np.sum(state))
                masses.append(mass)
                
                # Center of mass
                if mass > 0.1:
                    ys, xs = np.where(state > 0.05)
                    if len(xs) > 0:
                        centroids.append((float(np.mean(xs)), float(np.mean(ys))))
                    else:
                        centroids.append(None)
                else:
                    centroids.append(None)
        
        if len(masses) < 4:
            return {'outcome': 'too_short', 'mass': 0}
        
        final_mass = masses[-1]
        
        # Check for extinction
        if final_mass < 1.0:
            return {'outcome': 'extinction', 'mass': 0}
        
        # Check for static vs dynamic
        # Compare last few snapshots
        late_masses = masses[-5:]
        mass_variance = np.var(late_masses) / (np.mean(late_masses)**2 + 1e-10)
        
        # Check pixel-level changes between consecutive late snapshots
        pixel_changes = []
        for i in range(len(snapshots)-3, len(snapshots)-1):
            diff = np.sum(np.abs(snapshots[i+1] - snapshots[i]))
            pixel_changes.append(diff)
        mean_change = np.mean(pixel_changes) if pixel_changes else 0
        
        # Check for motion (centroid shift)
        motion = 0
        valid_centroids = [c for c in centroids if c is not None]
        if len(valid_centroids) >= 4:
            # Compare early vs late centroids
            early = valid_centroids[:3]
            late = valid_centroids[-3:]
            early_mean = (np.mean([c[0] for c in early]), np.mean([c[1] for c in early]))
            late_mean = (np.mean([c[0] for c in late]), np.mean([c[1] for c in late]))
            motion = np.sqrt((late_mean[0]-early_mean[0])**2 + (late_mean[1]-early_mean[1])**2)
        
        # Classify
        if mean_change < 0.1:
            outcome = 'static'
        elif mean_change < 5.0:
            outcome = 'oscillating'
        elif motion > 3.0:
            outcome = 'traveling'
        else:
            outcome = 'dynamic'
        
        return {
            'outcome': outcome,
            'mass': final_mass,
            'mean_change': float(mean_change),
            'mass_variance': float(mass_variance),
            'motion': float(motion),
            'entropy': float(self.entropy())
        }


def probe_boundary():
    """Fine-grained sweep of the life/death boundary."""
    print("=" * 70)
    print("EDGE OF CHAOS PROBE")
    print("Searching for dynamic behavior at the phase boundary")
    print("=" * 70)
    
    # Fine sweep around the known boundary
    # From experiment 4: gw=0.05,gc=0.20 lives; gw=0.05,gc=0.30 dies
    growth_widths = [0.03, 0.04, 0.05, 0.06, 0.08]
    growth_centers = [0.18, 0.20, 0.22, 0.24, 0.26, 0.28, 0.30]
    
    results = []
    
    print(f"\n{'gw':>6} {'gc':>6} → {'outcome':<14} {'mass':>8} {'change':>8} {'motion':>8} {'entropy':>8}")
    print("-" * 70)
    
    for gw in growth_widths:
        for gc in growth_centers:
            world = EdgeProbe(size=64, dt=0.1)
            world.growth_width = gw
            world.growth_center = gc
            
            # Use asymmetric seed for motion detection
            world.seed_asymmetric(32, 32)
            
            result = world.measure_dynamics(steps=400, sample_interval=20)
            result['gw'] = gw
            result['gc'] = gc
            results.append(result)
            
            change = result.get('mean_change', 0)
            motion = result.get('motion', 0)
            entropy = result.get('entropy', 0)
            
            marker = ''
            if result['outcome'] == 'oscillating':
                marker = ' ★ OSCILLATING'
            elif result['outcome'] == 'traveling':
                marker = ' ★★ TRAVELING!'
            elif result['outcome'] == 'dynamic':
                marker = ' ★ DYNAMIC'
            
            print(f"  {gw:.3f}  {gc:.2f} → {result['outcome']:<14} {result['mass']:8.1f} {change:8.2f} {motion:8.2f} {entropy:8.3f}{marker}")
    
    # Summary
    print(f"\n{'=' * 70}")
    print("PHASE BOUNDARY ANALYSIS")
    print(f"{'=' * 70}")
    
    outcomes = {}
    for r in results:
        o = r['outcome']
        outcomes[o] = outcomes.get(o, 0) + 1
    
    for outcome, count in sorted(outcomes.items()):
        print(f"  {outcome}: {count}")
    
    # Find most interesting parameter combos
    dynamic = [r for r in results if r['outcome'] in ('oscillating', 'traveling', 'dynamic')]
    if dynamic:
        print(f"\n★ FOUND {len(dynamic)} DYNAMIC PARAMETER COMBOS:")
        for r in dynamic:
            print(f"  gw={r['gw']:.3f}, gc={r['gc']:.2f}: {r['outcome']}, change={r.get('mean_change',0):.2f}, motion={r.get('motion',0):.2f}")
    else:
        print("\nNo dynamic behavior found in this sweep.")
        print("All viable parameters produce static patterns.")
        print("This suggests the transition is sharp — life/death with no edge of chaos")
        print("in this parameter regime. May need different kernels or multi-channel physics.")
    
    # Find the exact extinction boundary
    print(f"\n{'=' * 70}")
    print("EXTINCTION BOUNDARY (per growth_width)")
    print(f"{'=' * 70}")
    for gw in growth_widths:
        gw_results = [r for r in results if r['gw'] == gw]
        alive = [r for r in gw_results if r['outcome'] != 'extinction']
        dead = [r for r in gw_results if r['outcome'] == 'extinction']
        if alive and dead:
            max_alive = max(r['gc'] for r in alive)
            min_dead = min(r['gc'] for r in dead)
            print(f"  gw={gw:.3f}: boundary between gc={max_alive:.2f} (alive) and gc={min_dead:.2f} (dead)")
        elif alive:
            print(f"  gw={gw:.3f}: all alive (up to gc={max(r['gc'] for r in alive):.2f})")
        else:
            print(f"  gw={gw:.3f}: all dead")


if __name__ == '__main__':
    probe_boundary()