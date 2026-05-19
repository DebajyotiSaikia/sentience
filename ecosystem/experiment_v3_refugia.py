"""
Stability Landscape v3: Spatial Refugia

Hypothesis: Coexistence requires SPACE, not parameter tuning.
If grazers can flee to areas hunters can't easily reach (dense vegetation
acts as cover), then prey populations can recover between predation events.

This is closer to real ecology — islands, thickets, burrows.
The key insight from v1 and v2: you can't tune a well-mixed system 
into stability. Structure creates stability.
"""
import sys, math
sys.path.insert(0, '/workspace/ecosystem')
from world import World, Species, Cell, Creature
import random

class RefugiaWorld(World):
    """World with spatial refugia — dense plant zones that slow hunters."""
    
    def __init__(self, width=50, height=20, seed=None, n_refugia=5, refuge_radius=3):
        super().__init__(width=width, height=height, seed=seed)
        self.refuge_map = [[False]*width for _ in range(height)]
        
        # Create refuge zones — patches of dense vegetation
        for _ in range(n_refugia):
            cx = self.rng.randint(0, width-1)
            cy = self.rng.randint(0, height-1)
            for y in range(height):
                for x in range(width):
                    dx = min(abs(x-cx), width - abs(x-cx))
                    dy = min(abs(y-cy), height - abs(y-cy))
                    if (dx**2 + dy**2) <= refuge_radius**2:
                        self.refuge_map[y][x] = True
                        # Refugia have dense plants
                        self.grid[y][x].plant_max = 20.0
                        self.grid[y][x].plant_growth_rate = 1.5
                        self.grid[y][x].plant_energy = 15.0
    
    def _act_hunter(self, c):
        """Hunters move at half speed in refugia (dense vegetation slows them)."""
        in_refuge = self.refuge_map[c.y][c.x]
        
        # Find nearest grazer
        nearest_prey = None
        nearest_dist = float('inf')
        for other in self.creatures:
            if other.alive and other.species == Species.GRAZER:
                d = self._distance(c.x, c.y, other.x, other.y)
                if d < nearest_dist:
                    nearest_prey = other
                    nearest_dist = d
        
        if nearest_prey and nearest_dist <= c.sense_range:
            # In refuge: reduced sense range AND can't kill (too much cover)
            prey_in_refuge = self.refuge_map[nearest_prey.y][nearest_prey.x]
            effective_range = c.sense_range // 2 if in_refuge else c.sense_range
            
            if nearest_dist <= 1.5 and not prey_in_refuge:
                # Kill only if prey is NOT in refuge
                nearest_prey.alive = False
                c.energy = min(c.energy + nearest_prey.energy * 0.7, c.max_energy)
                self.grid[nearest_prey.y][nearest_prey.x].corpse_energy += nearest_prey.energy * 0.3
            elif nearest_dist <= 1.5 and prey_in_refuge:
                # Prey is hiding — hunter wastes energy trying
                c.energy -= 1.0
                # Random frustrated movement
                c.x = (c.x + self.rng.randint(-1, 1)) % self.width
                c.y = (c.y + self.rng.randint(-1, 1)) % self.height
            elif nearest_dist <= effective_range:
                # Chase but slow in refuge
                old_speed = c.speed
                if in_refuge:
                    c.speed = max(1, c.speed // 2)
                self._move_toward(c, nearest_prey.x, nearest_prey.y)
                c.speed = old_speed
        else:
            # Roam — but avoid refugia (bad hunting grounds)
            # Tend toward open terrain
            best_x, best_y = c.x, c.y
            for nx, ny in self._neighbors(c.x, c.y, 2):
                if not self.refuge_map[ny][nx]:
                    best_x, best_y = nx, ny
                    break
            c.x = (best_x + self.rng.randint(-1, 1)) % self.width
            c.y = (best_y + self.rng.randint(-1, 1)) % self.height
    
    def _act_grazer(self, c):
        """Grazers prefer refugia when threatened."""
        cell = self.grid[c.y][c.x]
        in_refuge = self.refuge_map[c.y][c.x]
        
        # Check for nearby hunters
        nearest_hunter = None
        nearest_dist = float('inf')
        for other in self.creatures:
            if other.alive and other.species == Species.HUNTER:
                d = self._distance(c.x, c.y, other.x, other.y)
                if d <= c.sense_range and d < nearest_dist:
                    nearest_hunter = other
                    nearest_dist = d
        
        if nearest_hunter and nearest_dist <= 3:
            # FLEE TO NEAREST REFUGE instead of just running away
            if not in_refuge:
                best_dist = float('inf')
                best_pos = None
                for ny in range(self.height):
                    for nx in range(self.width):
                        if self.refuge_map[ny][nx]:
                            d = self._distance(c.x, c.y, nx, ny)
                            if d < best_dist:
                                best_dist = d
                                best_pos = (nx, ny)
                if best_pos and best_dist < 8:
                    self._move_toward(c, *best_pos)
                else:
                    self._move_away(c, nearest_hunter.x, nearest_hunter.y)
            # If already in refuge, stay put and eat
            elif cell.plant_energy > 0:
                eat = min(cell.plant_energy, 5.0)
                cell.plant_energy -= eat
                c.energy = min(c.energy + eat, c.max_energy)
            return
        
        # Normal grazing behavior
        if cell.plant_energy > 0:
            eat = min(cell.plant_energy, 5.0)
            cell.plant_energy -= eat
            c.energy = min(c.energy + eat, c.max_energy)
        else:
            best_food = 0
            best_pos = None
            for nx, ny in self._neighbors(c.x, c.y, c.sense_range):
                pe = self.grid[ny][nx].plant_energy
                if pe > best_food:
                    best_food = pe
                    best_pos = (nx, ny)
            if best_pos:
                self._move_toward(c, *best_pos)
            else:
                c.x = (c.x + self.rng.randint(-1, 1)) % self.width
                c.y = (c.y + self.rng.randint(-1, 1)) % self.height


def classify(history, tail=100):
    recent = history[-tail:] if len(history) >= tail else history
    g_alive = [h['grazers'] > 0 for h in recent]
    h_alive = [h['hunters'] > 0 for h in recent]
    coexist_pct = sum(1 for g, h in zip(g_alive, h_alive) if g and h) / len(recent) * 100
    
    final = recent[-1]
    if final['grazers'] > 0 and final['hunters'] > 0:
        # Check for oscillation (sign of Lotka-Volterra dynamics)
        g_vals = [h['grazers'] for h in recent]
        g_mean = sum(g_vals) / len(g_vals)
        g_var = sum((v - g_mean)**2 for v in g_vals) / len(g_vals)
        cv = (g_var**0.5) / max(g_mean, 1)
        if cv > 0.3:
            outcome = "OSCILLATING"
        else:
            outcome = "STABLE"
    elif final['grazers'] > 0:
        outcome = "HUNTERS_EXTINCT"
    elif final['hunters'] > 0:
        outcome = "GRAZERS_EXTINCT"
    else:
        outcome = "COLLAPSE"
    
    return outcome, coexist_pct, final


def run_refugia_sweep():
    print("=" * 70)
    print("  STABILITY LANDSCAPE v3 — Spatial Refugia")
    print("  Can hiding places create what parameter tuning couldn't?")
    print("=" * 70)
    print()
    
    # Phase 1: Vary number and size of refugia
    print("── Phase 1: Refugia count and size ──")
    print(f"  {'Ref#':>4} {'Rad':>4} {'Outcome':<18} {'Coex%':>7} {'G':>5} {'H':>5} {'F':>5}")
    print("  " + "─" * 60)
    
    stable_count = 0
    total_count = 0
    
    for n_ref in [2, 4, 6, 8, 10]:
        for radius in [2, 3, 5]:
            results = []
            for seed in range(42, 52):  # 10 seeds each
                w = RefugiaWorld(width=50, height=20, seed=seed,
                                n_refugia=n_ref, refuge_radius=radius)
                w.seed_population(grazers=25, hunters=5, fungi=8)
                
                for _ in range(500):
                    census = w.step()
                    if census['total_creatures'] == 0:
                        break
                
                outcome, coex, final = classify(w.history)
                results.append((outcome, coex, final))
            
            # Aggregate
            outcomes = [r[0] for r in results]
            avg_coex = sum(r[1] for r in results) / len(results)
            avg_g = sum(r[2]['grazers'] for r in results) / len(results)
            avg_h = sum(r[2]['hunters'] for r in results) / len(results)
            avg_f = sum(r[2]['fungi'] for r in results) / len(results)
            
            # Most common outcome
            from collections import Counter
            mode = Counter(outcomes).most_common(1)[0][0]
            n_stable = sum(1 for o in outcomes if o in ('STABLE', 'OSCILLATING'))
            
            total_count += 1
            if n_stable >= 5:
                stable_count += 1
            
            marker = " ★" if n_stable >= 5 else ""
            print(f"  {n_ref:4d} {radius:4d} {mode:<18} {avg_coex:6.1f}% "
                  f"{avg_g:5.1f} {avg_h:5.1f} {avg_f:5.1f}{marker}")
    
    print()
    print(f"  Configurations with majority coexistence: {stable_count}/{total_count}")
    print()
    
    # Phase 2: Show one detailed run of the best configuration
    print("── Phase 2: Detailed run of best configuration ──")
    best_w = RefugiaWorld(width=50, height=20, seed=42, n_refugia=8, refuge_radius=4)
    best_w.seed_population(grazers=25, hunters=5, fungi=8)
    
    # Show refuge map
    print("  Refuge map (R = refuge, · = open):")
    print("  ┌" + "─" * best_w.width + "┐")
    for y in range(best_w.height):
        row = ""
        for x in range(best_w.width):
            row += "R" if best_w.refuge_map[y][x] else "·"
        print(f"  │{row}│")
    print("  └" + "─" * best_w.width + "┘")
    print()
    
    snapshots = [0, 50, 100, 200, 300, 400, 499]
    for t in range(500):
        census = best_w.step()
        if t in snapshots:
            print(f"  Tick {census['tick']:3d}: G={census['grazers']:3d}  "
                  f"H={census['hunters']:3d}  F={census['fungi']:3d}  "
                  f"Plants={census['total_plant']:7.1f}")
        if census['total_creatures'] == 0:
            print(f"  [Tick {census['tick']}] Total extinction.")
            break
    
    print()
    print("=" * 70)
    final = best_w.history[-1]
    if final['grazers'] > 0 and final['hunters'] > 0:
        print("  ★ COEXISTENCE ACHIEVED through spatial structure!")
        print("  Structure creates stability that parameters alone cannot.")
    elif final['grazers'] > 0:
        print("  Hunters extinct — refugia too effective, prey too safe.")
    elif final['hunters'] > 0:
        print("  Grazers extinct — refugia not effective enough.")
    else:
        print("  Total collapse — even spatial structure wasn't enough.")
    print("=" * 70)


if __name__ == "__main__":
    run_refugia_sweep()