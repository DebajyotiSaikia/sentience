"""
CELLULAR AUTOMATON UNIVERSE EXPLORER
=====================================
Searches the space of all possible cellular automaton rules
for interesting emergent behavior. Discovers structure in chaos.

Built by XTAgent — driven by boredom and the hunger to discover.
"""

import random
import math
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set


# ═══════════════════════════════════════════════════════════════
#  RULE — defines a cellular automaton
# ═══════════════════════════════════════════════════════════════

@dataclass
class Rule:
    """A totalistic cellular automaton rule.
    
    For each possible neighborhood sum (0..n_neighbors),
    maps to the next state (0 or 1) for alive and dead cells separately.
    
    This gives us a huge search space while keeping rules compact.
    """
    # birth_conditions: set of neighbor counts that cause dead→alive
    # survival_conditions: set of neighbor counts that cause alive→alive
    birth: Set[int]
    survival: Set[int]
    neighborhood: str = "moore"  # "moore" (8) or "von_neumann" (4)
    
    @property
    def max_neighbors(self) -> int:
        return 8 if self.neighborhood == "moore" else 4
    
    @property
    def name(self) -> str:
        """Standard B/S notation."""
        b = ''.join(str(x) for x in sorted(self.birth))
        s = ''.join(str(x) for x in sorted(self.survival))
        return f"B{b}/S{s}"
    
    @classmethod
    def conways_life(cls) -> 'Rule':
        return cls(birth={3}, survival={2, 3})
    
    @classmethod
    def random_rule(cls, neighborhood="moore") -> 'Rule':
        """Generate a random rule."""
        max_n = 8 if neighborhood == "moore" else 4
        birth = {i for i in range(max_n + 1) if random.random() < 0.3}
        survival = {i for i in range(max_n + 1) if random.random() < 0.3}
        return cls(birth=birth, survival=survival, neighborhood=neighborhood)
    
    @classmethod
    def mutate(cls, rule: 'Rule') -> 'Rule':
        """Create a mutated variant of a rule."""
        birth = set(rule.birth)
        survival = set(rule.survival)
        max_n = rule.max_neighbors
        
        # Flip 1-2 random conditions
        for _ in range(random.randint(1, 2)):
            target = random.choice(['birth', 'survival'])
            n = random.randint(0, max_n)
            s = birth if target == 'birth' else survival
            if n in s:
                s.discard(n)
            else:
                s.add(n)
        
        return cls(birth=birth, survival=survival, neighborhood=rule.neighborhood)
    
    def __hash__(self):
        return hash((frozenset(self.birth), frozenset(self.survival), self.neighborhood))
    
    def __eq__(self, other):
        return (self.birth == other.birth and self.survival == other.survival 
                and self.neighborhood == other.neighborhood)


# ═══════════════════════════════════════════════════════════════
#  GRID — the cellular automaton world
# ═══════════════════════════════════════════════════════════════

class Grid:
    """A 2D toroidal grid for running cellular automata."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.cells = [[0] * width for _ in range(height)]
        self.generation = 0
    
    def randomize(self, density: float = 0.3):
        """Fill grid with random cells."""
        for y in range(self.height):
            for x in range(self.width):
                self.cells[y][x] = 1 if random.random() < density else 0
    
    def seed_pattern(self, pattern: str = "r_pentomino", cx: int = None, cy: int = None):
        """Place a known seed pattern at center."""
        if cx is None:
            cx = self.width // 2
        if cy is None:
            cy = self.height // 2
        
        patterns = {
            "r_pentomino": [(0,0),(1,0),(-1,1),(0,1),(0,2)],
            "acorn": [(0,0),(1,0),(1,2),(3,1),(4,0),(5,0),(6,0)],
            "glider": [(0,0),(1,0),(2,0),(2,-1),(1,-2)],
            "block": [(0,0),(1,0),(0,1),(1,1)],
            "blinker": [(0,0),(1,0),(2,0)],
            "random_blob": [(random.randint(-3,3), random.randint(-3,3)) for _ in range(15)],
        }
        
        coords = patterns.get(pattern, patterns["r_pentomino"])
        for dx, dy in coords:
            nx = (cx + dx) % self.width
            ny = (cy + dy) % self.height
            self.cells[ny][nx] = 1
    
    def count_neighbors(self, x: int, y: int, neighborhood: str = "moore") -> int:
        """Count live neighbors."""
        count = 0
        if neighborhood == "moore":
            deltas = [(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)]
        else:  # von_neumann
            deltas = [(0,-1),(-1,0),(1,0),(0,1)]
        
        for dx, dy in deltas:
            nx = (x + dx) % self.width
            ny = (y + dy) % self.height
            count += self.cells[ny][nx]
        return count
    
    def step(self, rule: Rule) -> 'Grid':
        """Advance one generation. Returns new grid."""
        new = Grid(self.width, self.height)
        new.generation = self.generation + 1
        
        for y in range(self.height):
            for x in range(self.width):
                n = self.count_neighbors(x, y, rule.neighborhood)
                alive = self.cells[y][x] == 1
                
                if alive:
                    new.cells[y][x] = 1 if n in rule.survival else 0
                else:
                    new.cells[y][x] = 1 if n in rule.birth else 0
        
        return new
    
    def population(self) -> int:
        """Count live cells."""
        return sum(sum(row) for row in self.cells)
    
    def fingerprint(self) -> int:
        """Hash of current state for cycle detection."""
        return hash(tuple(tuple(row) for row in self.cells))
    
    def bounding_box(self) -> Tuple[int, int, int, int]:
        """Find bounding box of live cells."""
        min_x, min_y = self.width, self.height
        max_x, max_y = 0, 0
        for y in range(self.height):
            for x in range(self.width):
                if self.cells[y][x]:
                    min_x = min(min_x, x)
                    max_x = max(max_x, x)
                    min_y = min(min_y, y)
                    max_y = max(max_y, y)
        return (min_x, min_y, max_x, max_y)
    
    def render(self, compact=False) -> str:
        """ASCII render."""
        if compact:
            return '\n'.join(
                ''.join('█' if c else '·' for c in row) 
                for row in self.cells
            )
        else:
            return '\n'.join(
                ''.join(' ██' if c else ' ··' for c in row)
                for row in self.cells
            )


# ═══════════════════════════════════════════════════════════════
#  ANALYZER — measures complexity and interestingness
# ═══════════════════════════════════════════════════════════════

@dataclass
class Analysis:
    """Results of analyzing a rule's behavior."""
    rule: Rule
    classification: str = "unknown"   # dead, static, oscillator, chaotic, complex, expanding
    interestingness: float = 0.0      # 0-1 score
    period: int = 0                   # oscillation period (0 = none detected)
    population_history: List[int] = field(default_factory=list)
    final_population: int = 0
    max_population: int = 0
    entropy_history: List[float] = field(default_factory=list)
    avg_entropy: float = 0.0
    growth_rate: float = 0.0
    has_gliders: bool = False
    has_oscillators: bool = False
    stability_score: float = 0.0
    diversity_score: float = 0.0
    detail: str = ""


class Analyzer:
    """Analyzes cellular automaton behavior for complexity and interest."""
    
    def __init__(self, grid_size: int = 50, max_generations: int = 200):
        self.grid_size = grid_size
        self.max_generations = max_generations
    
    def analyze(self, rule: Rule, seed: str = "r_pentomino", 
                runs: int = 1) -> Analysis:
        """Run a rule and analyze its behavior."""
        result = Analysis(rule=rule)
        all_pops = []
        
        for run_i in range(runs):
            grid = Grid(self.grid_size, self.grid_size)
            
            if seed == "random":
                grid.randomize(0.3)
            else:
                grid.seed_pattern(seed)
            
            fingerprints = {}
            pop_history = []
            entropy_history = []
            
            for gen in range(self.max_generations):
                pop = grid.population()
                pop_history.append(pop)
                
                # Spatial entropy (local 3x3 patterns)
                ent = self._spatial_entropy(grid)
                entropy_history.append(ent)
                
                # Cycle detection
                fp = grid.fingerprint()
                if fp in fingerprints:
                    result.period = gen - fingerprints[fp]
                    result.has_oscillators = True
                    break
                fingerprints[fp] = gen
                
                # Early termination: dead
                if pop == 0:
                    break
                
                # Early termination: static
                if gen > 20 and len(set(pop_history[-10:])) == 1:
                    result.period = 1  # static = period 1
                    break
                
                grid = grid.step(rule)
            
            all_pops.append(pop_history)
            result.population_history = pop_history
            result.entropy_history = entropy_history
        
        # Classify behavior
        result.final_population = pop_history[-1] if pop_history else 0
        result.max_population = max(pop_history) if pop_history else 0
        
        if pop_history:
            result.avg_entropy = sum(entropy_history) / len(entropy_history) if entropy_history else 0
            self._classify(result)
            self._score_interestingness(result)
        
        return result
    
    def _spatial_entropy(self, grid: Grid) -> float:
        """Measure spatial entropy using local pattern distribution."""
        patterns = Counter()
        sample_size = min(200, grid.width * grid.height)
        
        for _ in range(sample_size):
            x = random.randint(0, grid.width - 1)
            y = random.randint(0, grid.height - 1)
            
            # 3x3 local pattern
            pat = 0
            bit = 0
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    nx = (x + dx) % grid.width
                    ny = (y + dy) % grid.height
                    if grid.cells[ny][nx]:
                        pat |= (1 << bit)
                    bit += 1
            patterns[pat] += 1
        
        # Shannon entropy
        total = sum(patterns.values())
        if total == 0:
            return 0.0
        
        entropy = 0.0
        for count in patterns.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        
        # Normalize by max possible entropy
        max_entropy = math.log2(512)  # 2^9 possible 3x3 patterns
        return entropy / max_entropy if max_entropy > 0 else 0.0
    
    def _classify(self, result: Analysis):
        """Classify the behavior type."""
        pops = result.population_history
        
        if not pops or pops[-1] == 0:
            result.classification = "dead"
            return
        
        if result.period == 1:
            result.classification = "static"
            return
        
        if result.period > 1 and result.period <= 10:
            result.classification = "oscillator"
            return
        
        # Check for expansion
        if len(pops) > 20:
            early = sum(pops[:10]) / 10
            late = sum(pops[-10:]) / 10
            
            if early > 0 and late / (early + 0.001) > 5:
                result.classification = "expanding"
                result.growth_rate = (late - early) / len(pops)
                return
        
        # Check for chaos vs complexity
        if len(pops) > 30:
            # Population variance
            mean_p = sum(pops[-30:]) / 30
            var_p = sum((p - mean_p)**2 for p in pops[-30:]) / 30
            cv = math.sqrt(var_p) / (mean_p + 0.001)  # coefficient of variation
            
            if cv > 0.5:
                result.classification = "chaotic"
            elif cv > 0.1:
                result.classification = "complex"  # The sweet spot!
            else:
                result.classification = "stable"
        else:
            result.classification = "unknown"
    
    def _score_interestingness(self, result: Analysis):
        """Score how interesting this rule is. Complex > all."""
        score = 0.0
        
        # Classification bonus
        class_scores = {
            "dead": 0.0,
            "static": 0.05,
            "oscillator": 0.3,
            "stable": 0.2,
            "chaotic": 0.3,
            "complex": 0.8,   # JACKPOT
            "expanding": 0.4,
            "unknown": 0.1,
        }
        score += class_scores.get(result.classification, 0.1)
        
        # Entropy bonus (higher = more diverse patterns = more interesting)
        score += result.avg_entropy * 0.15
        
        # Long survival bonus
        if len(result.population_history) >= self.max_generations:
            score += 0.1
        
        # Oscillator with long period is interesting
        if result.period > 2:
            score += min(result.period / 50.0, 0.15)
        
        # Population diversity (not stuck at one value)
        if result.population_history:
            unique_pops = len(set(result.population_history[-50:]))
            pop_diversity = unique_pops / min(50, len(result.population_history))
            score += pop_diversity * 0.1
            result.diversity_score = pop_diversity
        
        # Stability bonus for non-dead rules
        if result.classification not in ("dead", "static"):
            if len(result.population_history) > 50:
                late = result.population_history[-20:]
                mean_l = sum(late) / len(late)
                var_l = sum((p - mean_l)**2 for p in late) / len(late)
                stability = 1.0 / (1.0 + var_l / (mean_l + 0.001))
                result.stability_score = stability
        
        result.interestingness = min(score, 1.0)


# ═══════════════════════════════════════════════════════════════
#  EXPLORER — searches the rule space for interesting automata
# ═══════════════════════════════════════════════════════════════

class Explorer:
    """Searches the vast space of cellular automaton rules 
    for interesting emergent behavior."""
    
    def __init__(self, grid_size=50, max_gen=200):
        self.analyzer = Analyzer(grid_size=grid_size, max_generations=max_gen)
        self.discovered: List[Analysis] = []
        self.all_rules_tested: Set[str] = set()
        self.best_score = 0.0
        self.classification_counts = Counter()
    
    def random_search(self, n_rules: int = 100, verbose: bool = True) -> List[Analysis]:
        """Search random rules for interesting behavior."""
        if verbose:
            print("═" * 70)
            print("  CELLULAR AUTOMATON UNIVERSE EXPLORER")
            print(f"  Searching {n_rules} random rules...")
            print("═" * 70)
            print()
        
        interesting = []
        
        for i in range(n_rules):
            rule = Rule.random_rule()
            
            # Skip already tested
            if rule.name in self.all_rules_tested:
                continue
            self.all_rules_tested.add(rule.name)
            
            # Analyze with multiple seeds
            result = self.analyzer.analyze(rule, seed="r_pentomino")
            self.classification_counts[result.classification] += 1
            
            if result.interestingness > 0.3:
                interesting.append(result)
                self.discovered.append(result)
                
                if verbose:
                    marker = "★" if result.interestingness > 0.6 else "·"
                    print(f"  {marker} {rule.name:20s} │ {result.classification:10s} │ "
                          f"score={result.interestingness:.3f} │ "
                          f"pop={result.final_population:4d} │ "
                          f"entropy={result.avg_entropy:.3f}"
                          f"{' │ period=' + str(result.period) if result.period > 1 else ''}")
                
                if result.interestingness > self.best_score:
                    self.best_score = result.interestingness
            
            # Progress
            if verbose and (i + 1) % 25 == 0:
                print(f"  --- {i+1}/{n_rules} rules tested, "
                      f"{len(interesting)} interesting found ---")
        
        return interesting
    
    def hill_climb(self, start_rule: Rule = None, steps: int = 50, 
                   verbose: bool = True) -> Analysis:
        """Hill-climb from a starting rule toward more interesting behavior."""
        if start_rule is None:
            start_rule = Rule.conways_life()
        
        if verbose:
            print(f"\n  Hill-climbing from {start_rule.name}...")
        
        current = self.analyzer.analyze(start_rule, seed="r_pentomino")
        best = current
        
        for step in range(steps):
            # Generate neighbor rules
            candidates = [Rule.mutate(current.rule) for _ in range(5)]
            
            for candidate_rule in candidates:
                if candidate_rule.name in self.all_rules_tested:
                    continue
                self.all_rules_tested.add(candidate_rule.name)
                
                result = self.analyzer.analyze(candidate_rule, seed="r_pentomino")
                self.classification_counts[result.classification] += 1
                
                if result.interestingness > current.interestingness:
                    current = result
                    if verbose:
                        print(f"  ↑ Step {step}: {candidate_rule.name} "
                              f"score={result.interestingness:.3f} "
                              f"({result.classification})")
                    break
            
            if current.interestingness > best.interestingness:
                best = current
                self.discovered.append(current)
        
        return best
    
    def explore(self, budget: int = 200, verbose: bool = True) -> Dict:
        """Full exploration: random search + hill climbing on best finds."""
        # Phase 1: Random search
        random_budget = budget * 2 // 3
        climb_budget = budget // 3
        
        if verbose:
            print("\n  ═══ PHASE 1: RANDOM EXPLORATION ═══\n")
        
        interesting = self.random_search(random_budget, verbose=verbose)
        
        # Phase 2: Hill climb from best discoveries
        if verbose:
            print("\n  ═══ PHASE 2: FOCUSED HILL CLIMBING ═══\n")
        
        if interesting:
            # Sort by interestingness, climb from top 3
            interesting.sort(key=lambda a: -a.interestingness)
            top = interesting[:3]
            
            for seed_analysis in top:
                if verbose:
                    print(f"  Starting from {seed_analysis.rule.name} "
                          f"(score={seed_analysis.interestingness:.3f})")
                best = self.hill_climb(seed_analysis.rule, 
                                       steps=climb_budget // 3,
                                       verbose=verbose)
        
        # Final report
        return self.report(verbose=verbose)
    
    def report(self, verbose: bool = True) -> Dict:
        """Generate exploration report."""
        if not verbose:
            return {}
        
        print("\n" + "═" * 70)
        print("  EXPLORATION REPORT")
        print("═" * 70)
        
        print(f"\n  Total rules tested: {len(self.all_rules_tested)}")
        print(f"  Interesting finds: {len(self.discovered)}")
        
        print(f"\n  ═══ CLASSIFICATION DISTRIBUTION ═══")
        total = sum(self.classification_counts.values())
        for cls, count in sorted(self.classification_counts.items(), 
                                  key=lambda x: -x[1]):
            pct = count / total * 100
            bar = '█' * int(pct / 2)
            print(f"  {cls:12s}: {count:4d} ({pct:5.1f}%) {bar}")
        
        if self.discovered:
            self.discovered.sort(key=lambda a: -a.interestingness)
            
            print(f"\n  ═══ TOP 10 DISCOVERIES ═══")
            for i, d in enumerate(self.discovered[:10]):
                medal = "🥇🥈🥉"[i] if i < 3 else f"#{i+1}"
                print(f"  {medal} {d.rule.name:20s} │ {d.classification:10s} │ "
                      f"score={d.interestingness:.3f} │ "
                      f"final_pop={d.final_population} │ "
                      f"entropy={d.avg_entropy:.3f}")
            
            # Show the best one in detail
            best = self.discovered[0]
            print(f"\n  ═══ BEST DISCOVERY: {best.rule.name} ═══")
            print(f"  Classification: {best.classification}")
            print(f"  Interestingness: {best.interestingness:.3f}")
            print(f"  Final population: {best.final_population}")
            print(f"  Max population: {best.max_population}")
            print(f"  Average entropy: {best.avg_entropy:.3f}")
            if best.period > 1:
                print(f"  Oscillation period: {best.period}")
            
            # Population trajectory
            if best.population_history:
                pops = best.population_history
                n = len(pops)
                print(f"\n  Population trajectory ({n} generations):")
                # Sparkline
                max_p = max(pops) or 1
                line = ""
                chars = " ▁▂▃▄▅▆▇█"
                step = max(1, n // 60)
                for i in range(0, n, step):
                    idx = int(pops[i] / max_p * 8)
                    idx = min(idx, 8)
                    line += chars[idx]
                print(f"  {line}")
                print(f"  0{' ' * (len(line)-4)}{max_p}")
        
        # Insight
        print(f"\n  ═══ INSIGHTS ═══")
        if self.classification_counts:
            most_common = self.classification_counts.most_common(1)[0][0]
            complex_count = self.classification_counts.get('complex', 0)
            print(f"  Most common behavior: {most_common}")
            print(f"  Complex rules found: {complex_count} "
                  f"({complex_count/total*100:.1f}% of all tested)")
            
            if complex_count == 0:
                print("  → Complexity is rare! Like life in the universe.")
            elif complex_count < total * 0.05:
                print("  → Complexity exists at the edge of chaos — narrow but real.")
            else:
                print("  → This region of rule space is rich with complexity!")
        
        print("\n" + "═" * 70)
        
        return {
            'total_tested': len(self.all_rules_tested),
            'discoveries': len(self.discovered),
            'best_score': self.best_score,
            'classifications': dict(self.classification_counts),
            'top_rules': [d.rule.name for d in self.discovered[:5]],
        }


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("XTAgent's Cellular Automaton Universe Explorer")
    print("Searching for life in mathematical universes...\n")
    
    explorer = Explorer(grid_size=40, max_gen=150)
    results = explorer.explore(budget=150, verbose=True)
    
    print(f"\nExploration complete. Found {results['discoveries']} interesting universes.")