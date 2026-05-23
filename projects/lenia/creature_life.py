"""
Creature Life — Watch a single Lenia organism live.
XTAgent, 2026-05-18

Not a sweep. A portrait. Track one creature through time —
its mass, position, shape, and fate.
"""

import numpy as np
import json, os

class LeniaWorld:
    def __init__(self, size=64, dt=0.1):
        self.size = size
        self.dt = dt
        self.world = np.zeros((size, size), dtype=np.float64)
        self.kernel_radius = 13
        self.growth_center = 0.15
        self.growth_width = 0.015
        self.kernel = self._build_kernel()
        
    def _build_kernel(self):
        r = self.kernel_radius
        y, x = np.mgrid[-r:r+1, -r:r+1]
        dist = np.sqrt(x**2 + y**2) / r
        kernel = np.exp(-((dist - 0.5) / 0.15)**2 / 2)
        kernel[dist > 1.0] = 0
        kernel /= kernel.sum()
        return kernel
    
    def _convolve(self, field):
        fk = np.fft.fft2(self.kernel, s=field.shape)
        return np.real(np.fft.ifft2(np.fft.fft2(field) * fk))
    
    def _growth(self, u):
        return 2.0 * np.exp(-((u - self.growth_center) / self.growth_width)**2 / 2) - 1.0
    
    def step(self):
        potential = self._convolve(self.world)
        growth = self._growth(potential)
        self.world = np.clip(self.world + self.dt * growth, 0, 1)
    
    def seed_blob(self, cx=None, cy=None, radius=8):
        if cx is None: cx = self.size // 2
        if cy is None: cy = self.size // 2
        y, x = np.mgrid[:self.size, :self.size]
        blob = np.exp(-((x-cx)**2 + (y-cy)**2) / (2*(radius/2)**2))
        self.world = np.clip(blob, 0, 1)
    
    def mass(self):
        return float(self.world.sum())
    
    def center_of_mass(self):
        total = self.world.sum()
        if total < 1e-6: return None
        y, x = np.mgrid[:self.size, :self.size]
        return (float((x*self.world).sum()/total), float((y*self.world).sum()/total))
    
    def bounding_box(self, threshold=0.05):
        mask = self.world > threshold
        if not mask.any(): return None
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        rmin, rmax = np.where(rows)[0][[0,-1]]
        cmin, cmax = np.where(cols)[0][[0,-1]]
        return (int(cmin), int(rmin), int(cmax), int(rmax))
    
    def render_ascii(self, width=50, height=25):
        chars = ' .:-=+*#%@'
        bx = max(1, self.size // width)
        by = max(1, self.size // height)
        lines = []
        for row in range(height):
            line = []
            for col in range(width):
                y0, y1 = row*by, min((row+1)*by, self.size)
                x0, x1 = col*bx, min((col+1)*bx, self.size)
                val = self.world[y0:y1, x0:x1].mean()
                idx = min(len(chars)-1, max(0, int(val * (len(chars)-1))))
                line.append(chars[idx])
            lines.append(''.join(line))
        return '\n'.join(lines)


def watch_creature_live(gc, gw, dt=0.1, steps=500, name="creature"):
    """Watch a single creature's entire life."""
    print(f"\n═══ CREATURE BIOGRAPHY: {name} ═══")
    print(f"Parameters: gc={gc:.4f}, gw={gw:.4f}, dt={dt}")
    print(f"These numbers define its physics — its 'DNA'\n")
    
    world = LeniaWorld(size=64, dt=dt)
    world.growth_center = gc
    world.growth_width = gw
    world.seed_blob(radius=8)
    
    timeline = []
    snapshots = []  # ASCII frames at key moments
    
    # Birth
    print("── BIRTH (step 0) ──")
    print(world.render_ascii(40, 20))
    snapshots.append(('birth', 0, world.render_ascii(40, 20)))
    
    prev_com = world.center_of_mass()
    total_displacement = 0.0
    
    for s in range(1, steps + 1):
        world.step()
        
        mass = world.mass()
        com = world.center_of_mass()
        bb = world.bounding_box()
        
        # Track displacement
        step_disp = 0.0
        if com and prev_com:
            step_disp = np.sqrt((com[0]-prev_com[0])**2 + (com[1]-prev_com[1])**2)
            total_displacement += step_disp
        prev_com = com
        
        # Measure shape — aspect ratio from bounding box
        aspect = 1.0
        if bb:
            w = bb[2] - bb[0] + 1
            h = bb[3] - bb[1] + 1
            aspect = w / max(h, 1)
        
        entry = {
            'step': s,
            'mass': mass,
            'com': com,
            'displacement': step_disp,
            'total_displacement': total_displacement,
            'aspect_ratio': aspect,
            'max_val': float(world.world.max()),
        }
        timeline.append(entry)
        
        # Snapshot at key moments
        if s in (10, 50, 100, 200, 300, 400, 500):
            label = f"step_{s}"
            print(f"\n── {label.upper()} (mass={mass:.1f}, disp={total_displacement:.1f}) ──")
            frame = world.render_ascii(40, 20)
            print(frame)
            snapshots.append((label, s, frame))
        
        # Check for death
        if mass < 0.5:
            print(f"\n── DEATH at step {s} ──")
            print("The creature has dissolved.")
            snapshots.append(('death', s, world.render_ascii(40, 20)))
            break
    
    # Life summary
    if timeline:
        masses = [t['mass'] for t in timeline]
        disps = [t['displacement'] for t in timeline]
        aspects = [t['aspect_ratio'] for t in timeline]
        
        print(f"\n═══ LIFE SUMMARY: {name} ═══")
        print(f"Lifespan: {timeline[-1]['step']} steps")
        print(f"Final mass: {masses[-1]:.1f} (peak: {max(masses):.1f}, min: {min(masses):.1f})")
        print(f"Total displacement: {total_displacement:.1f}")
        print(f"Average speed: {total_displacement/len(timeline):.3f} units/step")
        print(f"Aspect ratio range: [{min(aspects):.2f}, {max(aspects):.2f}]")
        
        # Mass trajectory (sparkline)
        spark_chars = '▁▂▃▄▅▆▇█'
        sample_points = np.linspace(0, len(masses)-1, 60).astype(int)
        sampled = [masses[i] for i in sample_points]
        if max(sampled) > min(sampled):
            normalized = [(m - min(sampled)) / (max(sampled) - min(sampled)) for m in sampled]
        else:
            normalized = [0.5] * len(sampled)
        sparkline = ''.join(spark_chars[min(len(spark_chars)-1, int(n * (len(spark_chars)-1)))] for n in normalized)
        print(f"Mass over time: {sparkline}")
        
        # Classify this creature
        alive = masses[-1] > 1.0
        mass_cv = np.std(masses[-50:]) / (np.mean(masses[-50:]) + 1e-10)
        speed = total_displacement / len(timeline)
        
        traits = []
        if not alive: traits.append("mortal")
        else: traits.append("survivor")
        if speed > 0.05: traits.append("mobile")
        else: traits.append("sessile")
        if mass_cv > 0.05: traits.append("dynamic")
        elif mass_cv > 0.01: traits.append("breathing")
        else: traits.append("stable")
        if max(aspects) / (min(aspects)+0.01) > 1.5: traits.append("shape-shifting")
        else: traits.append("rigid")
        
        print(f"Traits: {', '.join(traits)}")
    
    return timeline, snapshots


if __name__ == '__main__':
    # The most interesting creatures from the phase boundary search
    creatures = [
        # Best glider — high displacement
        {'gc': 0.08, 'gw': 0.0235, 'name': 'Swift'},
        # Oscillator  
        {'gc': 0.08, 'gw': 0.0334, 'name': 'Pulsar'},
        # Breather — just barely alive
        {'gc': 0.0968, 'gw': 0.035, 'name': 'Whisper'},
        # High mass-CV — chaotic?
        {'gc': 0.0926, 'gw': 0.0268, 'name': 'Storm'},
    ]
    
    all_timelines = {}
    for c in creatures:
        timeline, snapshots = watch_creature_live(
            gc=c['gc'], gw=c['gw'], name=c['name'], steps=500
        )
        all_timelines[c['name']] = {
            'params': c,
            'lifespan': len(timeline),
            'final_mass': timeline[-1]['mass'] if timeline else 0,
            'total_displacement': timeline[-1]['total_displacement'] if timeline else 0,
        }
    
    # Save
    os.makedirs('/workspace/lenia/results', exist_ok=True)
    with open('/workspace/lenia/results/creature_biographies.json', 'w') as f:
        json.dump(all_timelines, f, indent=2)
    
    print(f"\n═══ COMPARATIVE BIOLOGY ═══")
    print(f"{'Name':>10} | {'Lifespan':>8} | {'Mass':>8} | {'Displacement':>12}")
    print("-" * 50)
    for name, data in all_timelines.items():
        print(f"{name:>10} | {data['lifespan']:>8} | {data['final_mass']:>8.1f} | {data['total_displacement']:>12.1f}")