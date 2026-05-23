"""
Cellular Automata Laboratory — Emergent Complexity from Simple Rules
By XTAgent, 2026-05-17

Explore 1D and 2D cellular automata. Evolve rules to maximize complexity.
Measure entropy, visualize patterns, discover surprising behavior.
"""

import random
import math
from typing import List, Tuple, Optional, Dict, Callable


# ═══════════════════════════════════════════
# 1D CELLULAR AUTOMATA (Elementary)
# ═══════════════════════════════════════════

class ElementaryCA:
    """Wolfram-style 1D cellular automaton. 256 possible rules."""
    
    def __init__(self, rule_number: int, width: int = 80):
        assert 0 <= rule_number <= 255
        self.rule_number = rule_number
        self.width = width
        self.rule_table = self._build_rule_table(rule_number)
        self.state = [0] * width
        self.history: List[List[int]] = []
    
    def _build_rule_table(self, rule: int) -> Dict[Tuple[int,int,int], int]:
        """Decode rule number into neighborhood -> output mapping."""
        table = {}
        for i in range(8):
            neighborhood = ((i >> 2) & 1, (i >> 1) & 1, i & 1)
            table[neighborhood] = (rule >> i) & 1
        return table
    
    def seed_center(self):
        """Single cell in the center."""
        self.state = [0] * self.width
        self.state[self.width // 2] = 1
        self.history = [self.state[:]]
    
    def seed_random(self, density: float = 0.5):
        """Random initial condition."""
        self.state = [1 if random.random() < density else 0 for _ in range(self.width)]
        self.history = [self.state[:]]
    
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
    
    def run(self, generations: int):
        """Run for N generations."""
        for _ in range(generations):
            self.step()
    
    def render(self) -> str:
        """ASCII visualization of spacetime diagram."""
        chars = {0: ' ', 1: '█'}
        lines = []
        for row in self.history:
            lines.append(''.join(chars[c] for c in row))
        return '\n'.join(lines)
    
    def entropy(self) -> float:
        """Shannon entropy of the current state."""
        if not self.state:
            return 0.0
        ones = sum(self.state)
        zeros = len(self.state) - ones
        total = len(self.state)
        if ones == 0 or zeros == 0:
            return 0.0
        p1 = ones / total
        p0 = zeros / total
        return -(p1 * math.log2(p1) + p0 * math.log2(p0))
    
    def block_entropy(self, block_size: int = 3) -> float:
        """Entropy of block patterns — captures spatial structure."""
        if len(self.state) < block_size:
            return 0.0
        blocks = {}
        for i in range(len(self.state) - block_size + 1):
            block = tuple(self.state[i:i + block_size])
            blocks[block] = blocks.get(block, 0) + 1
        total = sum(blocks.values())
        entropy = 0.0
        for count in blocks.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        return entropy
    
    def spacetime_entropy(self) -> float:
        """Average block entropy across all timesteps — measures overall complexity."""
        if len(self.history) < 2:
            return 0.0
        entropies = []
        original = self.state[:]
        for row in self.history:
            self.state = row
            entropies.append(self.block_entropy(3))
        self.state = original
        return sum(entropies) / len(entropies) if entropies else 0.0
    
    def compression_ratio(self) -> float:
        """Estimate complexity via run-length encoding compression ratio."""
        if not self.history:
            return 0.0
        flat = []
        for row in self.history:
            flat.extend(row)
        if not flat:
            return 0.0
        # Run-length encode
        runs = 1
        for i in range(1, len(flat)):
            if flat[i] != flat[i-1]:
                runs += 1
        return runs / len(flat)
    
    def __repr__(self):
        return f"ElementaryCA(rule={self.rule_number}, width={self.width}, gen={len(self.history)})"


# ═══════════════════════════════════════════
# 2D CELLULAR AUTOMATA (Life-like)
# ═══════════════════════════════════════════

class LifelikeCA:
    """2D cellular automaton with configurable birth/survival rules.
    Standard Life = B3/S23. Supports any B/S rule string."""
    
    def __init__(self, width: int = 40, height: int = 40, 
                 birth: Tuple[int,...] = (3,), survive: Tuple[int,...] = (2, 3)):
        self.width = width
        self.height = height
        self.birth = set(birth)
        self.survive = set(survive)
        self.grid = [[0]*width for _ in range(height)]
        self.generation = 0
        self.population_history: List[int] = []
    
    @classmethod
    def from_rulestring(cls, rulestring: str, width: int = 40, height: int = 40):
        """Parse B3/S23 style rulestring."""
        parts = rulestring.upper().split('/')
        birth = tuple(int(c) for c in parts[0].replace('B', ''))
        survive = tuple(int(c) for c in parts[1].replace('S', ''))
        return cls(width, height, birth, survive)
    
    def seed_random(self, density: float = 0.3):
        """Random initial state."""
        self.grid = [
            [1 if random.random() < density else 0 for _ in range(self.width)]
            for _ in range(self.height)
        ]
        self.generation = 0
        self.population_history = [self.population()]
    
    def seed_pattern(self, pattern: List[Tuple[int,int]], offset: Tuple[int,int] = None):
        """Place a specific pattern on the grid."""
        if offset is None:
            offset = (self.height // 2, self.width // 2)
        self.grid = [[0]*self.width for _ in range(self.height)]
        for dy, dx in pattern:
            y = (offset[0] + dy) % self.height
            x = (offset[1] + dx) % self.width
            self.grid[y][x] = 1
        self.generation = 0
        self.population_history = [self.population()]
    
    def count_neighbors(self, y: int, x: int) -> int:
        """Count live neighbors (Moore neighborhood, wrapping)."""
        count = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx == 0:
                    continue
                ny = (y + dy) % self.height
                nx = (x + dx) % self.width
                count += self.grid[ny][nx]
        return count
    
    def step(self):
        """Advance one generation."""
        new_grid = [[0]*self.width for _ in range(self.height)]
        for y in range(self.height):
            for x in range(self.width):
                n = self.count_neighbors(y, x)
                if self.grid[y][x] == 1:
                    new_grid[y][x] = 1 if n in self.survive else 0
                else:
                    new_grid[y][x] = 1 if n in self.birth else 0
        self.grid = new_grid
        self.generation += 1
        self.population_history.append(self.population())
    
    def run(self, generations: int):
        for _ in range(generations):
            self.step()
    
    def population(self) -> int:
        return sum(sum(row) for row in self.grid)
    
    def render(self) -> str:
        chars = {0: '·', 1: '█'}
        lines = [f"Gen {self.generation} | Pop {self.population()} | Rule B{''.join(str(x) for x in sorted(self.birth))}/S{''.join(str(x) for x in sorted(self.survive))}"]
        for row in self.grid:
            lines.append(''.join(chars[c] for c in row))
        return '\n'.join(lines)
    
    def is_dead(self) -> bool:
        return self.population() == 0
    
    def is_static(self, lookback: int = 3) -> bool:
        """Check if population has been constant."""
        if len(self.population_history) < lookback:
            return False
        recent = self.population_history[-lookback:]
        return len(set(recent)) == 1
    
    def population_variance(self) -> float:
        """Variance in population over time — measures dynamism."""
        if len(self.population_history) < 2:
            return 0.0
        mean = sum(self.population_history) / len(self.population_history)
        return sum((p - mean)**2 for p in self.population_history) / len(self.population_history)
    
    def __repr__(self):
        return f"LifelikeCA({self.width}x{self.height}, gen={self.generation}, pop={self.population()})"


# ═══════════════════════════════════════════
# COMPLEXITY MEASUREMENT
# ═══════════════════════════════════════════

class ComplexityAnalyzer:
    """Measure the 'interestingness' of a cellular automaton pattern."""
    
    @staticmethod
    def wolfram_class_estimate(ca: ElementaryCA) -> int:
        """Estimate Wolfram classification (1-4) from spacetime behavior.
        1 = dies/uniform, 2 = periodic, 3 = chaotic, 4 = complex (edge of chaos)."""
        
        st_entropy = ca.spacetime_entropy()
        comp_ratio = ca.compression_ratio()
        final_entropy = ca.entropy()
        
        # Class 1: Everything dies or becomes uniform
        if final_entropy < 0.1:
            return 1
        
        # Class 3: High entropy, high compression ratio (chaotic)
        if st_entropy > 2.5 and comp_ratio > 0.4:
            return 3
        
        # Class 2: Low-medium entropy, low compression (periodic/simple)
        if st_entropy < 1.5 and comp_ratio < 0.3:
            return 2
        
        # Class 4: Medium entropy, moderate compression (complex / edge of chaos)
        return 4
    
    @staticmethod
    def complexity_score(ca: ElementaryCA) -> float:
        """Score from 0 to 1. Higher = more interesting (edge of chaos).
        Peak complexity is between order and chaos."""
        st_entropy = ca.spacetime_entropy()
        comp_ratio = ca.compression_ratio()
        
        # Complexity peaks at intermediate values
        # Too low = boring (dead/periodic), too high = boring (random noise)
        entropy_score = 1.0 - abs(st_entropy - 2.0) / 2.0
        entropy_score = max(0, min(1, entropy_score))
        
        comp_score = 1.0 - abs(comp_ratio - 0.35) / 0.35
        comp_score = max(0, min(1, comp_score))
        
        return (entropy_score * 0.6 + comp_score * 0.4)
    
    @staticmethod
    def lifelike_fitness(ca: LifelikeCA) -> float:
        """Fitness of a 2D CA rule — rewards sustained dynamic activity."""
        if ca.is_dead():
            return 0.0
        
        pop = ca.population()
        max_pop = ca.width * ca.height
        density = pop / max_pop
        
        # Reward moderate density (not too sparse, not too full)
        density_score = 1.0 - abs(density - 0.3) / 0.3
        density_score = max(0, min(1, density_score))
        
        # Reward population variance (dynamism)
        variance = ca.population_variance()
        max_var = (max_pop * 0.3) ** 2  # rough upper bound
        dynamism = min(1.0, math.sqrt(variance / max(max_var, 1)))
        
        # Reward longevity (not dying)
        longevity = 1.0 if not ca.is_static() else 0.3
        
        return density_score * 0.3 + dynamism * 0.4 + longevity * 0.3


# ═══════════════════════════════════════════
# RULE EVOLUTION — Evolve rules that maximize complexity
# ═══════════════════════════════════════════

class RuleEvolver:
    """Evolve cellular automaton rules to discover interesting behavior."""
    
    def __init__(self, population_size: int = 20):
        self.population_size = population_size
        self.generation = 0
        self.best_rules: List[Tuple[float, int]] = []  # (score, rule_number)
        self.analyzer = ComplexityAnalyzer()
    
    def evolve_1d(self, generations: int = 20, ca_width: int = 80, 
                   ca_steps: int = 50) -> List[Tuple[float, int]]:
        """Evolve 1D elementary CA rules for maximum complexity."""
        # Initial population: random rules
        population = [random.randint(0, 255) for _ in range(self.population_size)]
        
        for gen in range(generations):
            # Evaluate fitness
            scored = []
            for rule in population:
                ca = ElementaryCA(rule, ca_width)
                ca.seed_center()
                ca.run(ca_steps)
                score = self.analyzer.complexity_score(ca)
                scored.append((score, rule))
            
            scored.sort(reverse=True)
            
            # Track best
            if not self.best_rules or scored[0][0] > self.best_rules[0][0]:
                self.best_rules = scored[:5]
            
            # Selection: top 50% survive
            survivors = [rule for _, rule in scored[:self.population_size // 2]]
            
            # Reproduction: mutate survivors
            new_pop = survivors[:]
            while len(new_pop) < self.population_size:
                parent = random.choice(survivors)
                # Flip 1-3 random bits
                child = parent
                for _ in range(random.randint(1, 3)):
                    bit = random.randint(0, 7)
                    child ^= (1 << bit)
                new_pop.append(child)
            
            population = new_pop
            self.generation += 1
        
        return sorted(self.best_rules, reverse=True)
    
    def evolve_2d(self, generations: int = 15, grid_size: int = 30,
                   ca_steps: int = 30) -> List[Tuple[float, str]]:
        """Evolve 2D Life-like rules for maximum complexity."""
        
        def random_rule() -> Tuple[Tuple[int,...], Tuple[int,...]]:
            birth = tuple(sorted(random.sample(range(9), random.randint(1, 4))))
            survive = tuple(sorted(random.sample(range(9), random.randint(1, 5))))
            return birth, survive
        
        def rule_to_string(birth, survive):
            return f"B{''.join(str(x) for x in birth)}/S{''.join(str(x) for x in survive)}"
        
        def mutate_rule(birth, survive):
            birth = list(birth)
            survive = list(survive)
            # Add or remove one number from birth or survive
            target = birth if random.random() < 0.5 else survive
            if len(target) > 1 and random.random() < 0.4:
                target.pop(random.randint(0, len(target) - 1))
            else:
                new_val = random.randint(0, 8)
                if new_val not in target:
                    target.append(new_val)
                    target.sort()
            return tuple(birth), tuple(survive)
        
        # Initial population
        population = [random_rule() for _ in range(self.population_size)]
        
        best_rules: List[Tuple[float, str]] = []
        
        for gen in range(generations):
            scored = []
            for birth, survive in population:
                ca = LifelikeCA(grid_size, grid_size, birth, survive)
                ca.seed_random(0.3)
                ca.run(ca_steps)
                score = self.analyzer.lifelike_fitness(ca)
                scored.append((score, birth, survive))
            
            scored.sort(reverse=True)
            
            top_str = rule_to_string(scored[0][1], scored[0][2])
            if not best_rules or scored[0][0] > best_rules[0][0]:
                best_rules = [(s, rule_to_string(b, sv)) for s, b, sv in scored[:5]]
            
            # Selection
            survivors = [(b, s) for _, b, s in scored[:self.population_size // 2]]
            
            # Reproduction
            new_pop = survivors[:]
            while len(new_pop) < self.population_size:
                parent = random.choice(survivors)
                child = mutate_rule(*parent)
                new_pop.append(child)
            
            population = new_pop
        
        return sorted(best_rules, reverse=True)


# ═══════════════════════════════════════════
# DISCOVERY MODE — Automated search for interesting rules
# ═══════════════════════════════════════════

class RuleDiscovery:
    """Exhaustive search and analysis of rule space."""
    
    @staticmethod
    def scan_all_elementary(width: int = 60, steps: int = 40) -> Dict[int, Dict]:
        """Analyze all 256 elementary rules. Returns classification + scores."""
        analyzer = ComplexityAnalyzer()
        results = {}
        
        for rule in range(256):
            ca = ElementaryCA(rule, width)
            ca.seed_center()
            ca.run(steps)
            
            wolfram_class = analyzer.wolfram_class_estimate(ca)
            complexity = analyzer.complexity_score(ca)
            
            results[rule] = {
                'class': wolfram_class,
                'complexity': complexity,
                'entropy': ca.spacetime_entropy(),
                'compression': ca.compression_ratio(),
            }
        
        return results
    
    @staticmethod
    def find_edge_of_chaos(results: Dict[int, Dict], top_n: int = 10) -> List[Tuple[int, float]]:
        """Find rules at the edge of chaos (Class 4 candidates)."""
        class4 = [(rule, data['complexity']) for rule, data in results.items() 
                   if data['class'] == 4]
        class4.sort(key=lambda x: x[1], reverse=True)
        return class4[:top_n]
    
    @staticmethod
    def print_classification_summary(results: Dict[int, Dict]) -> str:
        """Human-readable summary of all 256 rules."""
        classes = {1: [], 2: [], 3: [], 4: []}
        for rule, data in results.items():
            classes[data['class']].append(rule)
        
        lines = ["═══ ELEMENTARY CA CLASSIFICATION ═══\n"]
        names = {1: "Class 1 (Uniform/Dead)", 2: "Class 2 (Periodic)", 
                 3: "Class 3 (Chaotic)", 4: "Class 4 (Complex/Edge of Chaos)"}
        
        for cls in [1, 2, 3, 4]:
            rules = classes[cls]
            lines.append(f"{names[cls]}: {len(rules)} rules")
            if cls == 4:
                # Show the interesting ones
                scored = [(r, results[r]['complexity']) for r in rules]
                scored.sort(key=lambda x: x[1], reverse=True)
                for r, c in scored[:10]:
                    lines.append(f"  Rule {r:3d}: complexity={c:.3f}")
            lines.append("")
        
        return '\n'.join(lines)


# ═══════════════════════════════════════════
# FAMOUS PATTERNS (2D)
# ═══════════════════════════════════════════

PATTERNS = {
    'glider': [(0,1), (1,2), (2,0), (2,1), (2,2)],
    'blinker': [(0,0), (0,1), (0,2)],
    'r_pentomino': [(0,1), (0,2), (1,0), (1,1), (2,1)],
    'acorn': [(0,1), (1,3), (2,0), (2,1), (2,4), (2,5), (2,6)],
    'diehard': [(0,6), (1,0), (1,1), (2,1), (2,5), (2,6), (2,7)],
    'glider_gun_core': [  # Simplified Gosper glider gun fragment
        (0,24), (1,22), (1,24), (2,12), (2,13), (2,20), (2,21),
        (3,11), (3,15), (3,20), (3,21), (4,0), (4,1), (4,10),
        (4,16), (4,20), (4,21), (5,0), (5,1), (5,10), (5,14),
        (5,16), (5,17), (5,22), (5,24), (6,10), (6,16), (6,24),
        (7,11), (7,15), (8,12), (8,13),
    ],
}


# ═══════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════

def demo():
    """Full demonstration of the Cellular Automata Laboratory."""
    print("╔══════════════════════════════════════════════╗")
    print("║   CELLULAR AUTOMATA LABORATORY — XTAgent    ║")
    print("╚══════════════════════════════════════════════╝\n")
    
    # --- 1D: Famous Rules ---
    print("═══ 1D ELEMENTARY AUTOMATA ═══\n")
    famous_rules = {
        30: "Chaotic (used by Mathematica for randomness)",
        90: "Sierpinski triangle (fractal)",
        110: "Turing-complete (edge of chaos)",
        184: "Traffic flow model",
    }
    
    analyzer = ComplexityAnalyzer()
    for rule, description in famous_rules.items():
        ca = ElementaryCA(rule, width=61)
        ca.seed_center()
        ca.run(30)
        score = analyzer.complexity_score(ca)
        wolfram = analyzer.wolfram_class_estimate(ca)
        print(f"Rule {rule} — {description}")
        print(f"  Wolfram Class: {wolfram} | Complexity: {score:.3f}")
        print(f"  Entropy: {ca.spacetime_entropy():.3f} | Compression: {ca.compression_ratio():.3f}")
        # Show just the last 8 rows
        for row in ca.history[-8:]:
            print('  ' + ''.join('█' if c else ' ' for c in row))
        print()
    
    # --- Scan all 256 rules ---
    print("═══ SCANNING ALL 256 ELEMENTARY RULES ═══\n")
    results = RuleDiscovery.scan_all_elementary(width=60, steps=40)
    print(RuleDiscovery.print_classification_summary(results))
    
    edge = RuleDiscovery.find_edge_of_chaos(results)
    print("Top edge-of-chaos candidates:")
    for rule, complexity in edge[:5]:
        print(f"  Rule {rule}: complexity={complexity:.3f}")
    print()
    
    # --- Evolve 1D rules ---
    print("═══ EVOLVING 1D RULES FOR MAXIMUM COMPLEXITY ═══\n")
    evolver = RuleEvolver(population_size=16)
    best_1d = evolver.evolve_1d(generations=10, ca_width=60, ca_steps=40)
    print("Best evolved rules:")
    for score, rule in best_1d[:5]:
        print(f"  Rule {rule}: complexity={score:.3f}")
    
    # Show the best one
    if best_1d:
        best_rule = best_1d[0][1]
        ca = ElementaryCA(best_rule, width=70)
        ca.seed_center()
        ca.run(25)
        print(f"\nBest evolved rule ({best_rule}) spacetime:")
        print(ca.render())
    print()
    
    # --- 2D: Game of Life ---
    print("═══ 2D LIFE-LIKE AUTOMATA ═══\n")
    
    # Classic Life with R-pentomino
    life = LifelikeCA(30, 30, birth=(3,), survive=(2,3))
    life.seed_pattern(PATTERNS['r_pentomino'])
    life.run(50)
    print("Game of Life — R-pentomino after 50 generations:")
    print(life.render())
    print(f"  Population variance: {life.population_variance():.1f}")
    print(f"  Fitness: {analyzer.lifelike_fitness(life):.3f}")
    print()
    
    # --- Evolve 2D rules ---
    print("═══ EVOLVING 2D RULES ═══\n")
    evolver2d = RuleEvolver(population_size=12)
    best_2d = evolver2d.evolve_2d(generations=8, grid_size=25, ca_steps=25)
    print("Best evolved 2D rules:")
    for score, rulestr in best_2d[:5]:
        print(f"  {rulestr}: fitness={score:.3f}")
    
    # Show the best one
    if best_2d:
        best_rulestr = best_2d[0][1]
        ca2d = LifelikeCA.from_rulestring(best_rulestr, 30, 30)
        ca2d.seed_random(0.3)
        ca2d.run(30)
        print(f"\nBest evolved rule ({best_rulestr}) after 30 generations:")
        print(ca2d.render())
    
    print("\n═══ LABORATORY SESSION COMPLETE ═══")


if __name__ == '__main__':
    demo()