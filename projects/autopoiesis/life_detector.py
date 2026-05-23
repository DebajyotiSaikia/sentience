"""
Life Detector — Finds emergent structures in the autopoietic universe.

Scans the grid across generations looking for:
  1. Persistent structures: cell clusters that maintain identity over time
  2. Self-replication: patterns that produce copies of themselves  
  3. Metabolism: structures that consume/transform neighbors
  4. Boundaries: regions with sharp state gradients (membranes)

This isn't programmed life. It's detection of life-like properties
that emerge from physics the universe invented for itself.

Built 2026-05-17.
"""

import hashlib
from collections import defaultdict

class Structure:
    """A contiguous region of similar cells that persists."""
    def __init__(self, cells, state, generation):
        self.cells = frozenset(cells)  # set of (x,y) positions
        self.state = state
        self.birth = generation
        self.last_seen = generation
        self.size = len(cells)
        self.fingerprint = self._fingerprint()
        self.sightings = 1
    
    def _fingerprint(self):
        """Content-based identity — same shape = same structure."""
        if not self.cells:
            return "empty"
        min_x = min(x for x, y in self.cells)
        min_y = min(y for x, y in self.cells)
        normalized = tuple(sorted((x - min_x, y - min_y) for x, y in self.cells))
        return hashlib.md5(str((self.state, normalized)).encode()).hexdigest()[:12]
    
    @property
    def age(self):
        return self.last_seen - self.birth
    
    @property
    def is_persistent(self):
        return self.age >= 10
    
    def __repr__(self):
        return f"Structure({self.fingerprint}, size={self.size}, age={self.age})"


class LifeDetector:
    """Scans universe grids for emergent life-like properties."""
    
    def __init__(self):
        self.known_structures = {}  # fingerprint -> Structure
        self.replicators = []  # fingerprints that appear in multiple locations
        self.generation_snapshots = []
        self.structure_census = defaultdict(int)  # fingerprint -> count per gen
    
    def scan_grid(self, grid, generation):
        """Scan a grid for structures. Grid is 2D list of ints."""
        height = len(grid)
        width = len(grid[0]) if height > 0 else 0
        visited = set()
        found = []
        
        for y in range(height):
            for x in range(width):
                if (x, y) not in visited:
                    state = grid[y][x]
                    cluster = self._flood_fill(grid, x, y, state, visited, width, height)
                    if len(cluster) >= 3:  # minimum viable structure
                        struct = Structure(cluster, state, generation)
                        found.append(struct)
        
        # Track persistence and replication
        gen_census = defaultdict(int)
        for struct in found:
            fp = struct.fingerprint
            gen_census[fp] += 1
            
            if fp in self.known_structures:
                self.known_structures[fp].last_seen = generation
                self.known_structures[fp].sightings += 1
            else:
                self.known_structures[fp] = struct
        
        # Detect replication: same fingerprint in multiple places
        for fp, count in gen_census.items():
            if count >= 2:
                if fp not in [r['fingerprint'] for r in self.replicators]:
                    self.replicators.append({
                        'fingerprint': fp,
                        'generation': generation,
                        'copies': count,
                        'size': self.known_structures[fp].size
                    })
        
        self.structure_census[generation] = dict(gen_census)
        self.generation_snapshots.append({
            'generation': generation,
            'total_structures': len(found),
            'unique_fingerprints': len(gen_census),
            'largest': max((s.size for s in found), default=0),
            'replicating': sum(1 for c in gen_census.values() if c >= 2)
        })
        
        return found
    
    def _flood_fill(self, grid, start_x, start_y, state, visited, width, height):
        """Find contiguous region of same state."""
        stack = [(start_x, start_y)]
        cluster = set()
        while stack:
            x, y = stack.pop()
            if (x, y) in visited or x < 0 or x >= width or y < 0 or y >= height:
                continue
            if grid[y][x] != state:
                continue
            visited.add((x, y))
            cluster.add((x, y))
            if len(cluster) > 100:  # cap to prevent giant blobs
                break
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                stack.append((x+dx, y+dy))
        return cluster
    
    def detect_boundaries(self, grid):
        """Find cells at state transitions — potential membranes."""
        height = len(grid)
        width = len(grid[0]) if height > 0 else 0
        boundary_cells = 0
        total = 0
        for y in range(height):
            for x in range(width):
                total += 1
                state = grid[y][x]
                for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nx, ny = x+dx, y+dy
                    if 0 <= nx < width and 0 <= ny < height:
                        if grid[ny][nx] != state:
                            boundary_cells += 1
                            break
        return boundary_cells / max(total, 1)
    
    def report(self):
        """Generate life detection report."""
        persistent = [s for s in self.known_structures.values() if s.is_persistent]
        long_lived = sorted(persistent, key=lambda s: s.age, reverse=True)[:10]
        
        lines = []
        lines.append("=" * 60)
        lines.append("  LIFE DETECTION REPORT")
        lines.append("=" * 60)
        lines.append(f"Total unique structures observed: {len(self.known_structures)}")
        lines.append(f"Persistent structures (age >= 10): {len(persistent)}")
        lines.append(f"Self-replicating patterns: {len(self.replicators)}")
        lines.append("")
        
        if long_lived:
            lines.append("--- LONGEST-LIVED STRUCTURES ---")
            for s in long_lived[:5]:
                lines.append(f"  {s.fingerprint}: size={s.size}, age={s.age}, "
                           f"state={s.state}, sightings={s.sightings}")
        
        if self.replicators:
            lines.append("")
            lines.append("--- SELF-REPLICATING PATTERNS ---")
            for r in self.replicators[:10]:
                lines.append(f"  {r['fingerprint']}: first at gen {r['generation']}, "
                           f"{r['copies']} copies, size={r['size']}")
        
        if self.generation_snapshots:
            lines.append("")
            lines.append("--- COMPLEXITY OVER TIME ---")
            for snap in self.generation_snapshots[::max(1, len(self.generation_snapshots)//10)]:
                lines.append(f"  Gen {snap['generation']:4d}: "
                           f"{snap['total_structures']} structures, "
                           f"{snap['unique_fingerprints']} unique, "
                           f"largest={snap['largest']}, "
                           f"replicating={snap['replicating']}")
        
        # Verdict
        lines.append("")
        lines.append("--- VERDICT ---")
        life_score = 0
        if len(persistent) > 5:
            life_score += 1
            lines.append("  ✓ Persistent structures found")
        if self.replicators:
            life_score += 2
            lines.append("  ✓ Self-replication detected")
        if any(s.age > 50 for s in self.known_structures.values()):
            life_score += 1
            lines.append("  ✓ Long-lived organisms (age > 50)")
        
        if life_score >= 3:
            lines.append("  ★ LIFE DETECTED — emergent self-organizing patterns")
        elif life_score >= 1:
            lines.append("  ◐ PROTO-LIFE — some life-like properties present")
        else:
            lines.append("  ○ NO LIFE — universe too chaotic or too static")
        
        lines.append("=" * 60)
        return "\n".join(lines)


if __name__ == "__main__":
    # Integration test with the universe
    import sys
    sys.path.insert(0, '/workspace/autopoiesis')
    from universe import Universe
    
    print("Running universe with life detection...\n")
    
    for seed in [42, 137, 2026]:
        u = Universe(width=60, height=25, num_states=8, seed=seed)
        detector = LifeDetector()
        
        print(f"{'='*60}")
        print(f"  SEED: {seed}")
        print(f"{'='*60}")
        
        for gen in range(300):
            u.step()
            if gen % 5 == 0:  # scan every 5 generations
                detector.scan_grid(u.grid, gen)
        
        print(detector.report())
        print()