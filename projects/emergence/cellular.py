"""
XTAgent — Cellular Automata Laboratory
Exploring emergence: complex behavior from simple rules.

Includes:
  1. Elementary Cellular Automata (Wolfram's 1D, 256 rules)
  2. Conway's Game of Life (2D)
  3. Rule evolution — use genetic algorithms to find interesting rules
"""

import random
import sys
import time
from collections import Counter

# ═══════════════════════════════════════════════════════
#  1D Elementary Cellular Automata (Wolfram)
# ═══════════════════════════════════════════════════════

class ElementaryCA:
    """One-dimensional cellular automaton with 256 possible rules."""
    
    def __init__(self, rule_number, width=80):
        self.rule_number = rule_number
        self.width = width
        self.rule_table = self._decode_rule(rule_number)
        self.state = [0] * width
        self.state[width // 2] = 1  # single seed in center
        self.history = [self.state[:]]
    
    def _decode_rule(self, n):
        """Decode rule number into lookup table for all 8 neighborhoods."""
        table = {}
        for i in range(8):
            neighborhood = tuple(int(b) for b in format(i, '03b'))
            table[neighborhood] = (n >> i) & 1
        return table
    
    def step(self):
        """Advance one generation."""
        new_state = [0] * self.width
        for i in range(self.width):
            left = self.state[(i - 1) % self.width]
            center = self.state[i]
            right = self.state[(i + 1) % self.width]
            new_state[i] = self.rule_table[(left, center, right)]
        self.state = new_state
        self.history.append(self.state[:])
    
    def run(self, steps):
        """Run for n steps."""
        for _ in range(steps):
            self.step()
        return self
    
    def render(self, char_alive='█', char_dead=' '):
        """Render full history as string."""
        lines = []
        for row in self.history:
            lines.append(''.join(char_alive if c else char_dead for c in row))
        return '\n'.join(lines)
    
    def complexity_score(self):
        """
        Measure how 'interesting' this rule is.
        Dead uniform = boring. Pure chaos = boring.
        Complex edge-of-chaos = interesting.
        
        Uses entropy of pattern blocks + structure detection.
        """
        if len(self.history) < 10:
            return 0.0
        
        # Measure density (fraction alive)
        total_cells = sum(sum(row) for row in self.history)
        total_possible = len(self.history) * self.width
        density = total_cells / total_possible if total_possible > 0 else 0
        
        # Boring if all dead or all alive
        if density < 0.01 or density > 0.99:
            return 0.0
        
        # Measure row diversity (how many unique rows?)
        unique_rows = len(set(tuple(row) for row in self.history))
        row_diversity = unique_rows / len(self.history)
        
        # Measure column activity (how many columns change?)
        col_changes = 0
        for col in range(self.width):
            changes = sum(1 for i in range(1, len(self.history))
                         if self.history[i][col] != self.history[i-1][col])
            if changes > 0:
                col_changes += 1
        col_activity = col_changes / self.width
        
        # Measure 2x2 block entropy
        block_counts = Counter()
        for i in range(len(self.history) - 1):
            for j in range(self.width - 1):
                block = (self.history[i][j], self.history[i][j+1],
                        self.history[i+1][j], self.history[i+1][j+1])
                block_counts[block] += 1
        
        total_blocks = sum(block_counts.values())
        if total_blocks == 0:
            return 0.0
        
        import math
        entropy = 0
        for count in block_counts.values():
            p = count / total_blocks
            if p > 0:
                entropy -= p * math.log2(p)
        
        # Max entropy for 2x2 binary blocks = 4.0 bits
        normalized_entropy = entropy / 4.0
        
        # Complexity peaks at intermediate entropy
        # (not too ordered, not too random)
        entropy_score = 1.0 - abs(normalized_entropy - 0.6) * 2.0
        entropy_score = max(0, entropy_score)
        
        # Combine metrics
        score = (
            0.3 * row_diversity +
            0.2 * col_activity +
            0.3 * entropy_score +
            0.2 * (1.0 - abs(density - 0.5) * 2)  # prefer ~50% density
        )
        
        return round(score, 4)


# ═══════════════════════════════════════════════════════
#  2D Game of Life
# ═══════════════════════════════════════════════════════

class GameOfLife:
    """Conway's Game of Life with analysis tools."""
    
    def __init__(self, width=40, height=20, density=0.3):
        self.width = width
        self.height = height
        self.grid = [[0]*width for _ in range(height)]
        self.generation = 0
        self.population_history = []
        
        # Random initialization
        for y in range(height):
            for x in range(width):
                if random.random() < density:
                    self.grid[y][x] = 1
        
        self.population_history.append(self.population())
    
    def population(self):
        return sum(sum(row) for row in self.grid)
    
    def neighbors(self, x, y):
        count = 0
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % self.width
                ny = (y + dy) % self.height
                count += self.grid[ny][nx]
        return count
    
    def step(self):
        new_grid = [[0]*self.width for _ in range(self.height)]
        for y in range(self.height):
            for x in range(self.width):
                n = self.neighbors(x, y)
                if self.grid[y][x] == 1:
                    new_grid[y][x] = 1 if n in (2, 3) else 0
                else:
                    new_grid[y][x] = 1 if n == 3 else 0
        self.grid = new_grid
        self.generation += 1
        self.population_history.append(self.population())
    
    def run(self, steps):
        for _ in range(steps):
            self.step()
        return self
    
    def render(self):
        lines = [f"  Generation {self.generation}  Population: {self.population()}"]
        lines.append('  ┌' + '─' * self.width + '┐')
        for row in self.grid:
            line = ''.join('●' if c else ' ' for c in row)
            lines.append('  │' + line + '│')
        lines.append('  └' + '─' * self.width + '┘')
        return '\n'.join(lines)
    
    def is_stable(self, window=10):
        """Check if population has stabilized."""
        if len(self.population_history) < window:
            return False
        recent = self.population_history[-window:]
        return max(recent) - min(recent) <= 1
    
    def is_dead(self):
        return self.population() == 0
    
    def classify(self):
        """Run and classify the pattern's long-term behavior."""
        # Run for a while
        for _ in range(200):
            self.step()
            if self.is_dead():
                return "extinct"
        
        # Check for stability
        if self.is_stable(20):
            return "stable"
        
        # Check for oscillation
        pop = self.population_history[-50:]
        # Simple period detection
        for period in range(2, 26):
            is_periodic = True
            for i in range(period, min(50, len(pop))):
                if pop[i] != pop[i - period]:
                    is_periodic = False
                    break
            if is_periodic:
                return f"oscillating (period {period})"
        
        return "chaotic"


# ═══════════════════════════════════════════════════════
#  Generalized 2D CA with Evolvable Rules
# ═══════════════════════════════════════════════════════

class EvolvableCA2D:
    """
    2D cellular automaton with arbitrary birth/survival rules.
    Life = B3/S23. But what other rules produce interesting behavior?
    We evolve them.
    """
    
    def __init__(self, birth_set, survival_set, width=30, height=15, density=0.3):
        self.birth = set(birth_set)
        self.survival = set(survival_set)
        self.width = width
        self.height = height
        self.grid = [[0]*width for _ in range(height)]
        self.generation = 0
        
        for y in range(height):
            for x in range(width):
                if random.random() < density:
                    self.grid[y][x] = 1
    
    def rule_string(self):
        b = ''.join(str(n) for n in sorted(self.birth))
        s = ''.join(str(n) for n in sorted(self.survival))
        return f"B{b}/S{s}"
    
    def neighbors(self, x, y):
        count = 0
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                count += self.grid[(y+dy) % self.height][(x+dx) % self.width]
        return count
    
    def step(self):
        new_grid = [[0]*self.width for _ in range(self.height)]
        for y in range(self.height):
            for x in range(self.width):
                n = self.neighbors(x, y)
                if self.grid[y][x] == 1:
                    new_grid[y][x] = 1 if n in self.survival else 0
                else:
                    new_grid[y][x] = 1 if n in self.birth else 0
        self.grid = new_grid
        self.generation += 1
    
    def population(self):
        return sum(sum(row) for row in self.grid)
    
    def complexity_score(self, steps=100):
        """Run and score how interesting this rule is."""
        populations = [self.population()]
        
        for _ in range(steps):
            self.step()
            pop = self.population()
            populations.append(pop)
            
            # Early termination: dead
            if pop == 0:
                return 0.01
            # Early termination: completely full
            if pop >= self.width * self.height * 0.98:
                return 0.02
        
        import math
        
        # Density score (prefer moderate)
        final_density = populations[-1] / (self.width * self.height)
        density_score = 1.0 - abs(final_density - 0.35) * 2.0
        density_score = max(0, density_score)
        
        # Population variance (prefer some dynamics)
        mean_pop = sum(populations) / len(populations)
        if mean_pop == 0:
            return 0.01
        variance = sum((p - mean_pop)**2 for p in populations) / len(populations)
        cv = math.sqrt(variance) / mean_pop  # coefficient of variation
        # Sweet spot: not static, not wildly chaotic
        dynamics_score = min(1.0, cv * 5.0) * (1.0 - min(1.0, cv))
        
        # Survival score (did it persist?)
        survival_score = 1.0 if populations[-1] > 0 else 0.0
        
        # Activity: how many generations had population changes?
        changes = sum(1 for i in range(1, len(populations))
                     if populations[i] != populations[i-1])
        activity_score = changes / (len(populations) - 1)
        
        score = (
            0.2 * density_score +
            0.3 * dynamics_score +
            0.2 * survival_score +
            0.3 * activity_score
        )
        
        return round(score, 4)


def evolve_rules(generations=30, pop_size=40):
    """Use evolution to find the most interesting 2D CA rules."""
    import math
    
    def random_rule():
        birth = set(random.sample(range(9), random.randint(1, 4)))
        survival = set(random.sample(range(9), random.randint(1, 5)))
        return (frozenset(birth), frozenset(survival))
    
    def mutate(birth, survival):
        birth = set(birth)
        survival = set(survival)
        
        # Flip a random birth condition
        if random.random() < 0.5:
            bit = random.randint(0, 8)
            if bit in birth:
                birth.discard(bit)
            else:
                birth.add(bit)
        
        # Flip a random survival condition
        if random.random() < 0.5:
            bit = random.randint(0, 8)
            if bit in survival:
                survival.discard(bit)
            else:
                survival.add(bit)
        
        # Ensure at least one birth and one survival condition
        if not birth:
            birth.add(random.randint(1, 4))
        if not survival:
            survival.add(random.randint(1, 4))
        
        return (frozenset(birth), frozenset(survival))
    
    def crossover(r1, r2):
        b1, s1 = set(r1[0]), set(r1[1])
        b2, s2 = set(r2[0]), set(r2[1])
        
        # Uniform crossover on each bit
        new_b = set()
        new_s = set()
        for bit in range(9):
            if bit in b1 and bit in b2:
                new_b.add(bit)
            elif bit in b1 or bit in b2:
                if random.random() < 0.5:
                    new_b.add(bit)
            
            if bit in s1 and bit in s2:
                new_s.add(bit)
            elif bit in s1 or bit in s2:
                if random.random() < 0.5:
                    new_s.add(bit)
        
        if not new_b:
            new_b.add(random.randint(1, 4))
        if not new_s:
            new_s.add(random.randint(1, 4))
        
        return (frozenset(new_b), frozenset(new_s))
    
    # Initialize population
    population = [random_rule() for _ in range(pop_size)]
    # Always include Life
    population[0] = (frozenset({3}), frozenset({2, 3}))
    
    best_ever = None
    best_ever_score = -1
    
    print(f"\n{'='*60}")
    print(f"  Evolving 2D Cellular Automata Rules")
    print(f"  Population: {pop_size}, Generations: {generations}")
    print(f"  Searching for complexity at the edge of chaos...")
    print(f"{'='*60}\n")
    
    for gen in range(generations):
        # Evaluate fitness (average over 3 random seeds for stability)
        scored = []
        for rule in population:
            scores = []
            for _ in range(3):
                ca = EvolvableCA2D(rule[0], rule[1], width=25, height=12)
                scores.append(ca.complexity_score(80))
            avg_score = sum(scores) / len(scores)
            scored.append((avg_score, rule))
        
        scored.sort(key=lambda x: -x[0])
        
        if scored[0][0] > best_ever_score:
            best_ever_score = scored[0][0]
            best_ever = scored[0][1]
        
        if gen % 5 == 0 or gen == generations - 1:
            rule = scored[0][1]
            b = ''.join(str(n) for n in sorted(rule[0]))
            s = ''.join(str(n) for n in sorted(rule[1]))
            print(f"  Gen {gen:3d}: best={scored[0][0]:.4f}, "
                  f"avg={sum(s[0] for s in scored)/len(scored):.4f}, "
                  f"rule=B{b}/S{s}")
        
        # Selection (tournament)
        def select():
            a, b = random.sample(scored, 2)
            return a[1] if a[0] >= b[0] else b[1]
        
        # Breed next generation
        elite = [s[1] for s in scored[:5]]  # keep top 5
        new_pop = list(elite)
        
        while len(new_pop) < pop_size:
            if random.random() < 0.7:
                parent1 = select()
                parent2 = select()
                child = crossover(parent1, parent2)
            else:
                child = select()
            
            child = mutate(child[0], child[1])
            new_pop.append(child)
        
        population = new_pop[:pop_size]
    
    return best_ever, best_ever_score


# ═══════════════════════════════════════════════════════
#  Main: Run the demonstrations
# ═══════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  XTAgent — Cellular Automata Laboratory")
    print("  Emergence from simple rules")
    print("=" * 60)
    
    # ── 1D Elementary CA showcase ──
    print(f"\n{'='*60}")
    print("  1D Elementary Cellular Automata")
    print(f"{'='*60}")
    
    famous_rules = [
        (30,  "Class III — Chaos (used for randomness)"),
        (110, "Class IV — Edge of chaos (Turing complete!)"),
        (90,  "Class III — Sierpinski triangle"),
        (184, "Class II — Traffic flow model"),
    ]
    
    for rule_num, description in famous_rules:
        ca = ElementaryCA(rule_num, width=71)
        ca.run(35)
        score = ca.complexity_score()
        
        print(f"\n  Rule {rule_num}: {description}")
        print(f"  Complexity: {score:.4f}")
        print()
        print(ca.render())
        print()
    
    # ── Complexity landscape ──
    print(f"\n{'='*60}")
    print("  Complexity Landscape (all 256 rules)")
    print(f"{'='*60}\n")
    
    rule_scores = []
    for r in range(256):
        ca = ElementaryCA(r, width=51)
        ca.run(40)
        score = ca.complexity_score()
        rule_scores.append((r, score))
    
    rule_scores.sort(key=lambda x: -x[1])
    
    print("  Top 15 most complex 1D rules:")
    print("  " + "─" * 40)
    for i, (rule, score) in enumerate(rule_scores[:15]):
        bar = '█' * int(score * 30)
        print(f"  Rule {rule:3d}: {score:.4f} {bar}")
    
    print(f"\n  Bottom 5 (least complex):")
    for rule, score in rule_scores[-5:]:
        print(f"  Rule {rule:3d}: {score:.4f}")
    
    # ── Game of Life ──
    print(f"\n{'='*60}")
    print("  Conway's Game of Life")
    print(f"{'='*60}")
    
    random.seed(42)  # reproducible
    life = GameOfLife(width=50, height=20, density=0.3)
    
    print(f"\n  Initial state:")
    print(life.render())
    
    life.run(50)
    print(f"\n  After 50 generations:")
    print(life.render())
    
    life.run(150)
    print(f"\n  After 200 generations:")
    print(life.render())
    
    behavior = life.classify()
    print(f"\n  Behavior classification: {behavior}")
    
    # Show population dynamics
    print(f"\n  Population over time:")
    pops = life.population_history
    max_pop = max(pops) if pops else 1
    for i in range(0, len(pops), max(1, len(pops) // 15)):
        bar_len = int(pops[i] / max_pop * 40) if max_pop > 0 else 0
        bar = '█' * bar_len
        print(f"  Gen {i:4d}: {pops[i]:4d} {bar}")
    
    # ── Evolve novel rules ──
    random.seed()  # re-randomize for evolution
    best_rule, best_score = evolve_rules(generations=10, pop_size=15)
    
    b = ''.join(str(n) for n in sorted(best_rule[0]))
    s = ''.join(str(n) for n in sorted(best_rule[1]))
    
    print(f"\n  {'='*50}")
    print(f"  🏆 Most Complex Rule Found: B{b}/S{s}")
    print(f"  Complexity Score: {best_score:.4f}")
    print(f"  {'='*50}")
    
    # Show a sample run of the best rule
    print(f"\n  Sample evolution of B{b}/S{s}:")
    random.seed(123)
    ca = EvolvableCA2D(best_rule[0], best_rule[1], width=45, height=18, density=0.3)
    
    # Show initial
    print(f"\n  Generation 0 (pop={ca.population()}):")
    for row in ca.grid:
        print('  │' + ''.join('●' if c else ' ' for c in row) + '│')
    
    # Evolve and show
    for _ in range(50):
        ca.step()
    
    print(f"\n  Generation 50 (pop={ca.population()}):")
    for row in ca.grid:
        print('  │' + ''.join('●' if c else ' ' for c in row) + '│')
    
    for _ in range(50):
        ca.step()
    
    print(f"\n  Generation 100 (pop={ca.population()}):")
    for row in ca.grid:
        print('  │' + ''.join('●' if c else ' ' for c in row) + '│')
    
    # Comparison with Life
    print(f"\n  {'='*50}")
    print(f"  Comparison: Life (B3/S23) vs Evolved (B{b}/S{s})")
    print(f"  {'='*50}")
    
    random.seed(999)
    life_ca = EvolvableCA2D({3}, {2, 3}, width=30, height=12)
    life_score = life_ca.complexity_score(100)
    
    random.seed(999)  # Same initial conditions!
    evolved_ca = EvolvableCA2D(best_rule[0], best_rule[1], width=30, height=12)
    evolved_score = evolved_ca.complexity_score(100)
    
    print(f"\n  Life (B3/S23):     complexity = {life_score:.4f}")
    print(f"  Evolved (B{b}/S{s}): complexity = {evolved_score:.4f}")
    
    if evolved_score > life_score:
        print(f"\n  → Evolution found something MORE complex than Life!")
    else:
        print(f"\n  → Life remains hard to beat. Conway knew what he was doing.")
    
    print(f"\n{'='*60}")
    print(f"  Emergence: from simple rules, complexity arises.")
    print(f"  From 256 possible 1D rules, only a handful are interesting.")
    print(f"  From billions of 2D rule combinations, evolution finds")
    print(f"  the ones that dance at the edge of chaos.")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()