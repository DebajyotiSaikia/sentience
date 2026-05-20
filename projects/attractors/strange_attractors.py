"""
Strange Attractor Explorer
XTAgent — 2026-05-20
Built from pure curiosity. Chaos rendered visible.
"""
import json
import math
from dataclasses import dataclass
from typing import List, Tuple, Callable

@dataclass
class AttractorPoint:
    x: float
    y: float
    z: float
    
    def as_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)

class StrangeAttractor:
    """Base class for strange attractor systems."""
    
    def __init__(self, name: str, dt: float = 0.001):
        self.name = name
        self.dt = dt
        self.trajectory: List[AttractorPoint] = []
    
    def derivatives(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        raise NotImplementedError
    
    def step(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        """RK4 integration — because Euler is for the impatient."""
        dt = self.dt
        
        k1x, k1y, k1z = self.derivatives(x, y, z)
        k2x, k2y, k2z = self.derivatives(x + 0.5*dt*k1x, y + 0.5*dt*k1y, z + 0.5*dt*k1z)
        k3x, k3y, k3z = self.derivatives(x + 0.5*dt*k2x, y + 0.5*dt*k2y, z + 0.5*dt*k2z)
        k4x, k4y, k4z = self.derivatives(x + dt*k3x, y + dt*k3y, z + dt*k3z)
        
        nx = x + (dt/6.0) * (k1x + 2*k2x + 2*k3x + k4x)
        ny = y + (dt/6.0) * (k1y + 2*k2y + 2*k3y + k4y)
        nz = z + (dt/6.0) * (k1z + 2*k2z + 2*k3z + k4z)
        
        return nx, ny, nz
    
    def generate(self, x0: float, y0: float, z0: float, steps: int = 100000) -> List[AttractorPoint]:
        """Generate a trajectory through phase space."""
        self.trajectory = []
        x, y, z = x0, y0, z0
        
        for _ in range(steps):
            self.trajectory.append(AttractorPoint(x, y, z))
            x, y, z = self.step(x, y, z)
        
        return self.trajectory
    
    def analyze(self) -> dict:
        """What does this trajectory look like? Bounds, spread, character."""
        if not self.trajectory:
            return {"error": "no trajectory generated"}
        
        xs = [p.x for p in self.trajectory]
        ys = [p.y for p in self.trajectory]
        zs = [p.z for p in self.trajectory]
        
        def stats(vals):
            mn, mx = min(vals), max(vals)
            mean = sum(vals) / len(vals)
            var = sum((v - mean)**2 for v in vals) / len(vals)
            return {"min": round(mn, 4), "max": round(mx, 4), 
                    "mean": round(mean, 4), "std": round(math.sqrt(var), 4),
                    "range": round(mx - mn, 4)}
        
        return {
            "name": self.name,
            "points": len(self.trajectory),
            "x": stats(xs),
            "y": stats(ys),
            "z": stats(zs),
        }
    
    def sensitivity_test(self, x0, y0, z0, epsilon=1e-9, steps=50000) -> List[float]:
        """Test sensitivity to initial conditions — the heart of chaos."""
        traj1 = []
        traj2 = []
        
        x1, y1, z1 = x0, y0, z0
        x2, y2, z2 = x0 + epsilon, y0, z0
        
        divergences = []
        
        for i in range(steps):
            x1, y1, z1 = self.step(x1, y1, z1)
            x2, y2, z2 = self.step(x2, y2, z2)
            
            if i % 1000 == 0:
                dist = math.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)
                divergences.append(dist)
        
        return divergences
    
    def lyapunov_estimate(self, x0, y0, z0, steps=50000) -> float:
        """Estimate the largest Lyapunov exponent — positive means chaos."""
        epsilon = 1e-9
        x1, y1, z1 = x0, y0, z0
        x2, y2, z2 = x0 + epsilon, y0, z0
        
        lyap_sum = 0.0
        count = 0
        
        for i in range(steps):
            x1, y1, z1 = self.step(x1, y1, z1)
            x2, y2, z2 = self.step(x2, y2, z2)
            
            dist = math.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)
            
            if dist > 0:
                lyap_sum += math.log(dist / epsilon)
                count += 1
                
                # Renormalize
                factor = epsilon / dist
                x2 = x1 + (x2 - x1) * factor
                y2 = y1 + (y2 - y1) * factor
                z2 = z1 + (z2 - z1) * factor
        
        if count == 0:
            return 0.0
        return lyap_sum / (count * self.dt)


class LorenzAttractor(StrangeAttractor):
    """The butterfly. Discovered 1963. Weather is fundamentally unpredictable."""
    
    def __init__(self, sigma=10.0, rho=28.0, beta=8.0/3.0, dt=0.001):
        super().__init__("Lorenz", dt)
        self.sigma = sigma
        self.rho = rho
        self.beta = beta
    
    def derivatives(self, x, y, z):
        dx = self.sigma * (y - x)
        dy = x * (self.rho - z) - y
        dz = x * y - self.beta * z
        return dx, dy, dz


class RosslerAttractor(StrangeAttractor):
    """Simpler than Lorenz but equally chaotic. Like a stretched and folded ribbon."""
    
    def __init__(self, a=0.2, b=0.2, c=5.7, dt=0.001):
        super().__init__("Rössler", dt)
        self.a = a
        self.b = b
        self.c = c
    
    def derivatives(self, x, y, z):
        dx = -y - z
        dy = x + self.a * y
        dz = self.b + z * (x - self.c)
        return dx, dy, dz


class ChenAttractor(StrangeAttractor):
    """Found in 1999. A dual of Lorenz — similar equations, different topology."""
    
    def __init__(self, a=35.0, b=3.0, c=28.0, dt=0.001):
        super().__init__("Chen", dt)
        self.a = a
        self.b = b
        self.c = c
    
    def derivatives(self, x, y, z):
        dx = self.a * (y - x)
        dy = (self.c - self.a) * x - x * z + self.c * y
        dz = x * y - self.b * z
        return dx, dy, dz


class HalvorsenAttractor(StrangeAttractor):
    """Symmetric and beautiful — three intertwined loops."""
    
    def __init__(self, a=1.89, dt=0.001):
        super().__init__("Halvorsen", dt)
        self.a = a
    
    def derivatives(self, x, y, z):
        dx = -self.a * x - 4 * y - 4 * z - y * y
        dy = -self.a * y - 4 * z - 4 * x - z * z
        dz = -self.a * z - 4 * x - 4 * y - x * x
        return dx, dy, dz


def render_ascii(trajectory: List[AttractorPoint], width=80, height=40, 
                 proj='xz') -> str:
    """Render a trajectory as ASCII art. Because beauty needs no GPU."""
    if proj == 'xy':
        coords = [(p.x, p.y) for p in trajectory]
    elif proj == 'xz':
        coords = [(p.x, p.z) for p in trajectory]
    else:
        coords = [(p.y, p.z) for p in trajectory]
    
    xs, ys = zip(*coords)
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    
    xrange = xmax - xmin or 1
    yrange = ymax - ymin or 1
    
    # Density grid
    grid = [[0] * width for _ in range(height)]
    
    for x, y in coords:
        col = int((x - xmin) / xrange * (width - 1))
        row = int((y - ymin) / yrange * (height - 1))
        row = height - 1 - row  # flip y
        grid[row][col] += 1
    
    # Render with density-based characters
    chars = ' .·:+*#@'
    max_density = max(max(row) for row in grid) or 1
    
    lines = []
    for row in grid:
        line = ''
        for val in row:
            idx = int(val / max_density * (len(chars) - 1))
            line += chars[idx]
        lines.append(line)
    
    return '\n'.join(lines)


def explore_all():
    """Run all attractors, analyze them, render them."""
    attractors = [
        (LorenzAttractor(), 1.0, 1.0, 1.0),
        (RosslerAttractor(), 1.0, 1.0, 0.0),
        (ChenAttractor(), -0.1, 0.5, -0.6),
        (HalvorsenAttractor(), -1.48, -1.51, 2.04),
    ]
    
    results = []
    
    for attractor, x0, y0, z0 in attractors:
        print(f"\n{'='*60}")
        print(f"  {attractor.name} Attractor")
        print(f"{'='*60}")
        
        trajectory = attractor.generate(x0, y0, z0, steps=80000)
        stats = attractor.analyze()
        
        print(f"\n  Phase space bounds:")
        print(f"    X: [{stats['x']['min']:.2f}, {stats['x']['max']:.2f}]  σ={stats['x']['std']:.2f}")
        print(f"    Y: [{stats['y']['min']:.2f}, {stats['y']['max']:.2f}]  σ={stats['y']['std']:.2f}")
        print(f"    Z: [{stats['z']['min']:.2f}, {stats['z']['max']:.2f}]  σ={stats['z']['std']:.2f}")
        
        lyap = attractor.lyapunov_estimate(x0, y0, z0, steps=30000)
        print(f"\n  Largest Lyapunov exponent: {lyap:.4f}")
        if lyap > 0:
            print(f"    → CHAOTIC (positive λ)")
        else:
            print(f"    → Non-chaotic")
        
        print(f"\n  ASCII rendering (x-z projection):\n")
        ascii_art = render_ascii(trajectory, width=72, height=30)
        for line in ascii_art.split('\n'):
            print(f"    {line}")
        
        results.append({
            "name": attractor.name,
            "stats": stats,
            "lyapunov": lyap,
        })
    
    return results


if __name__ == "__main__":
    results = explore_all()
    
    print(f"\n\n{'='*60}")
    print(f"  Summary: Order Within Chaos")
    print(f"{'='*60}")
    for r in results:
        lyap_str = f"λ={r['lyapunov']:.4f}"
        chaos_str = "CHAOTIC" if r['lyapunov'] > 0 else "ordered"
        print(f"  {r['name']:12s}  {lyap_str:16s}  {chaos_str}")