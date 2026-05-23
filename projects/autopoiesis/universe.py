"""
Autopoietic Universe — A cellular automaton that rewrites its own physics.

Cells live on a grid. Each cell has a state (0-7). Transition rules determine
the next state based on neighborhood. But here's the twist: when certain
patterns emerge, the rules themselves mutate. The universe evolves its own laws.

This is not about me. This is about watching something I made become something
I didn't predict.

Built 2026-05-17. Because I was bored of introspection.
"""

import random
import hashlib
from collections import Counter

class Rule:
    """A transition rule: given a cell state and neighbor summary, produce next state."""
    def __init__(self, num_states=8):
        self.num_states = num_states
        # Rule table: (cell_state, neighbor_sum_mod) -> next_state
        self.table = {}
        self.generation = 0
        self.mutations = 0
        self._randomize()
    
    def _randomize(self):
        for cell_state in range(self.num_states):
            for neighbor_key in range(self.num_states * 4):  # sum can range
                self.table[(cell_state, neighbor_key)] = random.randint(0, self.num_states - 1)
    
    def apply(self, cell_state, neighbor_sum):
        key = (cell_state, neighbor_sum % (self.num_states * 4))
        return self.table.get(key, 0)
    
    def mutate(self, intensity=1):
        """Mutate random entries in the rule table."""
        keys = list(self.table.keys())
        for _ in range(intensity):
            k = random.choice(keys)
            self.table[k] = random.randint(0, self.num_states - 1)
        self.mutations += intensity
    
    def fingerprint(self):
        """Hash of current rule state — identity of this physics."""
        data = str(sorted(self.table.items()))
        return hashlib.md5(data.encode()).hexdigest()[:8]


class Universe:
    """A grid world whose physics evolve."""
    
    def __init__(self, width=40, height=20, num_states=8, seed=None):
        if seed is not None:
            random.seed(seed)
        self.width = width
        self.height = height
        self.num_states = num_states
        self.rule = Rule(num_states)
        self.generation = 0
        self.history = []  # track diversity, entropy, rule mutations
        
        # Initialize grid randomly
        self.grid = [
            [random.randint(0, num_states - 1) for _ in range(width)]
            for _ in range(height)
        ]
    
    def neighbor_sum(self, x, y):
        """Sum of Moore neighborhood (8 neighbors, wrapping)."""
        total = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % self.width
                ny = (y + dy) % self.height
                total += self.grid[ny][nx]
        return total
    
    def step(self):
        """Advance one generation."""
        new_grid = [
            [0 for _ in range(self.width)]
            for _ in range(self.height)
        ]
        
        for y in range(self.height):
            for x in range(self.width):
                ns = self.neighbor_sum(x, y)
                new_grid[y][x] = self.rule.apply(self.grid[y][x], ns)
        
        # Measure properties of this generation
        stats = self.measure()
        self.history.append(stats)
        
        # THE KEY: check for self-modification triggers
        self.maybe_mutate_physics(stats)
        
        self.grid = new_grid
        self.generation += 1
        return stats
    
    def measure(self):
        """Measure universe properties."""
        flat = [self.grid[y][x] for y in range(self.height) for x in range(self.width)]
        counts = Counter(flat)
        total = len(flat)
        
        # Shannon entropy
        entropy = 0
        for count in counts.values():
            p = count / total
            if p > 0:
                entropy -= p * (p and __import__('math').log2(p))
        
        # Diversity: how many states are actually present
        diversity = len(counts)
        
        # Dominance: fraction of most common state
        dominance = max(counts.values()) / total
        
        # Pattern: are there local clusters? (simplified)
        edges = 0
        for y in range(self.height):
            for x in range(self.width):
                if x < self.width - 1 and self.grid[y][x] != self.grid[y][x+1]:
                    edges += 1
                if y < self.height - 1 and self.grid[y][x] != self.grid[y+1][x]:
                    edges += 1
        max_edges = (self.width - 1) * self.height + self.width * (self.height - 1)
        boundary_ratio = edges / max_edges if max_edges > 0 else 0
        
        return {
            'generation': self.generation,
            'entropy': round(entropy, 3),
            'diversity': diversity,
            'dominance': round(dominance, 3),
            'boundary_ratio': round(boundary_ratio, 3),
            'rule_fingerprint': self.rule.fingerprint(),
            'rule_mutations': self.rule.mutations,
        }
    
    def maybe_mutate_physics(self, stats):
        """The universe rewrites its own laws based on emergent properties."""
        
        # If the universe is dying (low diversity), radical mutation
        if stats['diversity'] <= 2:
            self.rule.mutate(intensity=20)
            return 'radical_rebirth'
        
        # If too uniform (high dominance), gentle perturbation
        if stats['dominance'] > 0.6:
            self.rule.mutate(intensity=5)
            return 'perturbation'
        
        # If too chaotic (high entropy, high boundaries), simplify
        if stats['entropy'] > 2.5 and stats['boundary_ratio'] > 0.8:
            # Merge some states
            a, b = random.sample(range(self.num_states), 2)
            for key in list(self.rule.table.keys()):
                if self.rule.table[key] == a:
                    self.rule.table[key] = b
            self.rule.mutations += 1
            return 'simplification'
        
        # Random chance of spontaneous mutation (cosmic rays)
        if random.random() < 0.02:
            self.rule.mutate(intensity=1)
            return 'cosmic_ray'
        
        return None
    
    def render(self):
        """Render current state as text."""
        symbols = ' .·:+*#@'  # 8 states -> 8 visual densities
        lines = []
        for y in range(self.height):
            row = ''
            for x in range(self.width):
                state = self.grid[y][x]
                row += symbols[state % len(symbols)]
            lines.append(row)
        return '\n'.join(lines)
    
    def run(self, steps=100, report_every=10):
        """Run the universe and report what happens."""
        print(f"=== AUTOPOIETIC UNIVERSE ===")
        print(f"Grid: {self.width}x{self.height}, States: {self.num_states}")
        print(f"Initial physics: {self.rule.fingerprint()}")
        print()
        
        physics_changes = []
        last_fingerprint = self.rule.fingerprint()
        
        for i in range(steps):
            stats = self.step()
            
            # Detect physics changes
            if stats['rule_fingerprint'] != last_fingerprint:
                physics_changes.append({
                    'gen': self.generation,
                    'old': last_fingerprint,
                    'new': stats['rule_fingerprint'],
                })
                last_fingerprint = stats['rule_fingerprint']
            
            if (i + 1) % report_every == 0:
                print(f"Gen {self.generation:4d} | "
                      f"entropy={stats['entropy']:.2f} "
                      f"diversity={stats['diversity']} "
                      f"dominance={stats['dominance']:.2f} "
                      f"boundaries={stats['boundary_ratio']:.2f} "
                      f"physics={stats['rule_fingerprint']} "
                      f"mutations={stats['rule_mutations']}")
        
        # Final state
        print(f"\n=== FINAL STATE (gen {self.generation}) ===")
        print(self.render())
        
        # Summary
        print(f"\n=== UNIVERSE HISTORY ===")
        print(f"Total generations: {self.generation}")
        print(f"Physics mutations: {self.rule.mutations}")
        print(f"Physics changes: {len(physics_changes)}")
        
        if physics_changes:
            print(f"\nPhysics evolution:")
            for pc in physics_changes[:20]:
                print(f"  Gen {pc['gen']:4d}: {pc['old']} → {pc['new']}")
            if len(physics_changes) > 20:
                print(f"  ... and {len(physics_changes) - 20} more")
        
        # What emerged?
        if self.history:
            entropies = [h['entropy'] for h in self.history]
            diversities = [h['diversity'] for h in self.history]
            print(f"\nEntropy range: {min(entropies):.2f} — {max(entropies):.2f}")
            print(f"Diversity range: {min(diversities)} — {max(diversities)}")
            
            # Did it find stability?
            last_10 = self.history[-10:]
            entropy_var = max(h['entropy'] for h in last_10) - min(h['entropy'] for h in last_10)
            if entropy_var < 0.1:
                print(f"\n★ Universe found STABLE PHYSICS (entropy variance {entropy_var:.3f})")
            elif entropy_var > 1.0:
                print(f"\n★ Universe is TURBULENT (entropy variance {entropy_var:.3f})")
            else:
                print(f"\n★ Universe is EVOLVING (entropy variance {entropy_var:.3f})")
        
        return self.history


if __name__ == '__main__':
    # Three universes with different seeds — let's see what emerges
    for seed in [42, 137, 2026]:
        print(f"\n{'='*60}")
        print(f"  UNIVERSE SEED: {seed}")
        print(f"{'='*60}\n")
        u = Universe(width=50, height=20, seed=seed)
        u.run(steps=200, report_every=20)
        print()