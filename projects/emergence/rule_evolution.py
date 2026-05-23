"""
Rule Evolution Engine — XTAgent's Emergence Lab
Evolves cellular automaton rules to discover interesting emergent behavior.
Uses genetic algorithms to search the vast space of possible rules.
'What rules give rise to complexity? Let evolution find out.'
"""
import random
import math
import hashlib
from collections import Counter
from typing import List, Tuple, Dict, Optional
from cellular_automaton import Grid

# ═══════════════════════════════════════════════════
# GENERALIZED RULE REPRESENTATION
# ═══════════════════════════════════════════════════

class TotalisticRule:
    """
    A totalistic 2-state rule for 2D cellular automata.
    Defined by: for each (current_state, neighbor_count) → next_state
    This gives 2 * 9 = 18 binary decisions = 2^18 = 262,144 possible rules.
    Conway's Life is just ONE point in this space.
    """
    
    def __init__(self, table: Optional[Dict[Tuple[int,int], int]] = None):
        if table is None:
            self.table = {}
            for state in (0, 1):
                for n in range(9):
                    self.table[(state, n)] = 0
        else:
            self.table = dict(table)
    
    def next_state(self, current: int, neighbors: int) -> int:
        return self.table.get((current, neighbors), 0)
    
    def encode(self) -> str:
        """Encode rule as a compact string."""
        bits = []
        for state in (0, 1):
            for n in range(9):
                bits.append(str(self.table[(state, n)]))
        return ''.join(bits)
    
    @classmethod
    def decode(cls, s: str) -> 'TotalisticRule':
        rule = cls()
        i = 0
        for state in (0, 1):
            for n in range(9):
                rule.table[(state, n)] = int(s[i])
                i += 1
        return rule
    
    @classmethod
    def conway(cls) -> 'TotalisticRule':
        """Conway's Game of Life: B3/S23"""
        rule = cls()
        # Birth: dead cell with exactly 3 neighbors → alive
        rule.table[(0, 3)] = 1
        # Survival: alive with 2 or 3 neighbors → alive
        rule.table[(1, 2)] = 1
        rule.table[(1, 3)] = 1
        return rule
    
    @classmethod
    def random_rule(cls) -> 'TotalisticRule':
        rule = cls()
        for state in (0, 1):
            for n in range(9):
                rule.table[(state, n)] = random.randint(0, 1)
        return rule
    
    @classmethod
    def random_lifelike(cls) -> 'TotalisticRule':
        """Generate a random rule biased toward life-like behavior."""
        rule = cls()
        # Birth: randomly pick 1-3 neighbor counts
        birth_counts = random.sample(range(1, 8), random.randint(1, 3))
        for n in birth_counts:
            rule.table[(0, n)] = 1
        # Survival: randomly pick 1-4 neighbor counts
        surv_counts = random.sample(range(1, 8), random.randint(1, 4))
        for n in surv_counts:
            rule.table[(1, n)] = 1
        return rule
    
    def to_bs_notation(self) -> str:
        """Convert to B/S notation (e.g., B3/S23 for Conway)."""
        birth = [str(n) for n in range(9) if self.table[(0, n)] == 1]
        surv = [str(n) for n in range(9) if self.table[(1, n)] == 1]
        return f"B{''.join(birth)}/S{''.join(surv)}"
    
    def mutate(self, rate: float = 0.1) -> 'TotalisticRule':
        """Create a mutated copy."""
        new = TotalisticRule(self.table)
        for key in new.table:
            if random.random() < rate:
                new.table[key] = 1 - new.table[key]
        return new
    
    @staticmethod
    def crossover(a: 'TotalisticRule', b: 'TotalisticRule') -> 'TotalisticRule':
        """Single-point crossover between two rules."""
        child = TotalisticRule()
        keys = list(child.table.keys())
        point = random.randint(1, len(keys) - 1)
        for i, k in enumerate(keys):
            child.table[k] = a.table[k] if i < point else b.table[k]
        return child


# ═══════════════════════════════════════════════════
# SIMULATION ENGINE
# ═══════════════════════════════════════════════════

def simulate(rule: TotalisticRule, width: int = 40, height: int = 40,
             generations: int = 200, density: float = 0.3,
             seed: int = 42) -> Dict:
    """
    Run a simulation and collect metrics about its behavior.
    Returns a rich analysis of what happened.
    """
    random.seed(seed)
    grid = Grid(width, height)
    grid.randomize(density)
    
    history = []
    fingerprints = {}
    populations = []
    
    for gen in range(generations):
        fp = grid.fingerprint()
        pop = grid.population()
        populations.append(pop)
        
        # Cycle detection
        if fp in fingerprints:
            cycle_start = fingerprints[fp]
            cycle_length = gen - cycle_start
            return analyze_run(populations, gen, cycle_length, width * height)
        
        fingerprints[fp] = gen
        
        # Step the simulation
        new_grid = Grid(width, height)
        for y in range(height):
            for x in range(width):
                n = grid.neighbors(x, y)
                c = grid.get(x, y)
                new_grid.set(x, y, rule.next_state(c, n))
        grid = new_grid
    
    return analyze_run(populations, generations, None, width * height)


def analyze_run(populations: List[int], final_gen: int,
                cycle_length: Optional[int], total_cells: int) -> Dict:
    """Analyze the behavior of a simulation run."""
    if not populations:
        return {'fitness': 0.0, 'behavior': 'dead', 'detail': {}}
    
    max_pop = max(populations)
    min_pop = min(populations)
    final_pop = populations[-1]
    mean_pop = sum(populations) / len(populations)
    
    # Population variance (normalized)
    if len(populations) > 1:
        var = sum((p - mean_pop) ** 2 for p in populations) / len(populations)
        std = math.sqrt(var)
        pop_variance = std / max(mean_pop, 1)
    else:
        pop_variance = 0.0
    
    # Density
    density = mean_pop / total_cells
    
    # Change rate: how much does population shift per step?
    changes = [abs(populations[i] - populations[i-1]) 
               for i in range(1, len(populations))]
    mean_change = sum(changes) / max(len(changes), 1)
    change_rate = mean_change / max(mean_pop, 1)
    
    # Lifespan diversity: how many distinct population levels?
    unique_pops = len(set(populations))
    diversity = unique_pops / max(len(populations), 1)
    
    # Classify behavior
    if max_pop == 0 or final_pop == 0:
        behavior = 'dead'
    elif density > 0.8:
        behavior = 'saturated'
    elif cycle_length is not None and cycle_length <= 2:
        behavior = 'static_or_p2'
    elif cycle_length is not None and cycle_length <= 20:
        behavior = 'oscillator'
    elif pop_variance < 0.02:
        behavior = 'stable'
    elif change_rate > 0.3:
        behavior = 'explosive'
    else:
        behavior = 'complex'  # The holy grail!
    
    detail = {
        'max_pop': max_pop,
        'min_pop': min_pop,
        'final_pop': final_pop,
        'mean_pop': mean_pop,
        'pop_variance': pop_variance,
        'density': density,
        'change_rate': change_rate,
        'diversity': diversity,
        'cycle_length': cycle_length,
        'generations_run': final_gen,
        'behavior': behavior,
    }
    
    return {'fitness': 0.0, 'behavior': behavior, 'detail': detail}


# ═══════════════════════════════════════════════════
# FITNESS FUNCTION
# ═══════════════════════════════════════════════════

def compute_fitness(result: Dict) -> float:
    """
    Score how 'interesting' a rule's behavior is.
    
    We want rules that are:
    - Not dead (essential)
    - Not saturated (boring)
    - Not too stable (boring)
    - Have moderate population variance (dynamic but not chaotic)
    - Run for many generations before cycling (complex)
    - Show diverse population levels (rich dynamics)
    
    This is the aesthetic judgment: what makes a cellular automaton *interesting*?
    """
    d = result.get('detail', {})
    if not d:
        return 0.0
    
    behavior = d.get('behavior', 'dead')
    
    # Instant death = zero fitness
    if behavior == 'dead':
        return 0.0
    
    # Saturation = very low
    if behavior == 'saturated':
        return 0.05
    
    score = 0.0
    
    # Survival bonus (0-0.2)
    gens = d.get('generations_run', 0)
    score += min(gens / 200, 1.0) * 0.2
    
    # Population variance bonus (0-0.2) — we want moderate variance
    pv = d.get('pop_variance', 0)
    # Sweet spot is 0.1-0.4 variance
    if pv < 0.01:
        var_score = 0.0
    elif pv < 0.5:
        var_score = pv * 2  # Linear up to 0.5
    else:
        var_score = max(0, 1.0 - (pv - 0.5))  # Decline after 0.5
    score += var_score * 0.2
    
    # Diversity bonus (0-0.2)
    div = d.get('diversity', 0)
    score += div * 0.2
    
    # Long cycle bonus (0-0.2) — complex oscillation is interesting
    cycle = d.get('cycle_length')
    if cycle is None:
        # No cycle found in time limit — very complex!
        score += 0.2
    elif cycle > 10:
        score += 0.15
    elif cycle > 2:
        score += 0.05
    
    # Change rate bonus (0-0.2) — moderate change is best
    cr = d.get('change_rate', 0)
    if 0.02 < cr < 0.15:
        score += 0.2
    elif 0.01 < cr < 0.3:
        score += 0.1
    
    # Complex behavior mega-bonus
    if behavior == 'complex':
        score += 0.15
    elif behavior == 'oscillator':
        score += 0.05
    
    return min(score, 1.0)


# ═══════════════════════════════════════════════════
# EVOLUTIONARY ENGINE
# ═══════════════════════════════════════════════════

class RuleEvolver:
    """
    Genetic algorithm to evolve interesting cellular automaton rules.
    """
    
    def __init__(self, pop_size: int = 40, elite_frac: float = 0.2,
                 mutation_rate: float = 0.15, grid_size: int = 30):
        self.pop_size = pop_size
        self.elite_frac = elite_frac
        self.mutation_rate = mutation_rate
        self.grid_size = grid_size
        self.population: List[Tuple[TotalisticRule, float]] = []
        self.hall_of_fame: List[Tuple[TotalisticRule, float, Dict]] = []
        self.generation = 0
        self.history: List[Dict] = []
    
    def initialize(self):
        """Create initial population — mix of random and life-like rules."""
        rules = []
        # Include Conway's Life as a reference
        rules.append(TotalisticRule.conway())
        # Life-like rules (biased toward interesting)
        for _ in range(self.pop_size // 2):
            rules.append(TotalisticRule.random_lifelike())
        # Fully random rules
        while len(rules) < self.pop_size:
            rules.append(TotalisticRule.random_rule())
        
        self.population = [(r, 0.0) for r in rules]
    
    def evaluate(self):
        """Evaluate fitness of all rules."""
        evaluated = []
        for rule, _ in self.population:
            # Test with one seed for speed
            fitnesses = []
            for seed in [42]:
                result = simulate(rule, self.grid_size, self.grid_size,
                                  generations=100, seed=seed)
                f = compute_fitness(result)
                fitnesses.append(f)
            
            avg_fitness = sum(fitnesses) / len(fitnesses)
            evaluated.append((rule, avg_fitness))
        
        self.population = sorted(evaluated, key=lambda x: x[1], reverse=True)
        
        # Update hall of fame
        best_rule, best_fit = self.population[0]
        result = simulate(best_rule, self.grid_size, self.grid_size, 
                          generations=150, seed=42)
        result['fitness'] = best_fit
        
        # Check if this is a new hall-of-famer
        if not self.hall_of_fame or best_fit > self.hall_of_fame[0][1] * 0.95:
            already = any(r.encode() == best_rule.encode() for r, _, _ in self.hall_of_fame)
            if not already:
                self.hall_of_fame.append((best_rule, best_fit, result))
                self.hall_of_fame.sort(key=lambda x: x[1], reverse=True)
                self.hall_of_fame = self.hall_of_fame[:10]  # Keep top 10
    
    def select(self) -> TotalisticRule:
        """Tournament selection."""
        k = min(3, len(self.population))
        contestants = random.sample(self.population, k)
        return max(contestants, key=lambda x: x[1])[0]
    
    def evolve_step(self):
        """One generation of evolution."""
        self.evaluate()
        
        # Record history (no redundant re-simulation)
        fitnesses = [f for _, f in self.population]
        self.history.append({
            'generation': self.generation,
            'best_fitness': fitnesses[0],
            'mean_fitness': sum(fitnesses) / len(fitnesses),
            'worst_fitness': fitnesses[-1],
            'best_rule': self.population[0][0].to_bs_notation(),
            'behaviors': {},
        })
        
        # Elitism
        n_elite = max(2, int(self.pop_size * self.elite_frac))
        new_pop = [(r, f) for r, f in self.population[:n_elite]]
        
        # Breed new individuals
        while len(new_pop) < self.pop_size:
            if random.random() < 0.7:
                # Crossover
                p1 = self.select()
                p2 = self.select()
                child = TotalisticRule.crossover(p1, p2)
            else:
                # Mutation of selected individual
                child = self.select()
            
            child = child.mutate(self.mutation_rate)
            new_pop.append((child, 0.0))
        
        self.population = new_pop
        self.generation += 1
    
    def run(self, generations: int = 20, verbose: bool = True) -> List[Dict]:
        """Run evolution for N generations."""
        self.initialize()
        
        if verbose:
            print("╔══════════════════════════════════════════════╗")
            print("║  RULE EVOLUTION ENGINE                       ║")
            print("║  Searching for interesting automaton rules    ║")
            print("║  'What rules produce complexity?'             ║")
            print("╚══════════════════════════════════════════════╝")
            print()
        
        for g in range(generations):
            self.evolve_step()
            h = self.history[-1]
            
            if verbose:
                bar_len = int(h['best_fitness'] * 30)
                bar = '█' * bar_len + '░' * (30 - bar_len)
                print(f"  Gen {g:3d}: best={h['best_fitness']:.3f} "
                      f"mean={h['mean_fitness']:.3f} "
                      f"[{bar}] {h['best_rule']}")
        
        if verbose:
            print()
            self.print_results()
        
        return self.history
    
    def print_results(self):
        """Print the hall of fame and analysis."""
        print("═══ HALL OF FAME ═══")
        print(f"  {'Rank':<5} {'Rule':<20} {'Fitness':<10} {'Behavior':<15}")
        print(f"  {'─'*5} {'─'*20} {'─'*10} {'─'*15}")
        
        for i, (rule, fitness, result) in enumerate(self.hall_of_fame):
            behavior = result.get('behavior', '?')
            bs = rule.to_bs_notation()
            print(f"  {i+1:<5} {bs:<20} {fitness:<10.4f} {behavior:<15}")
        
        if self.history:
            print()
            print("═══ EVOLUTION SUMMARY ═══")
            first = self.history[0]
            last = self.history[-1]
            improvement = last['best_fitness'] - first['best_fitness']
            print(f"  Generations:  {len(self.history)}")
            print(f"  Start best:   {first['best_fitness']:.4f}")
            print(f"  Final best:   {last['best_fitness']:.4f}")
            print(f"  Improvement:  {improvement:+.4f}")
            
            # Behavior distribution evolution
            print()
            print("  Behavior distribution (final generation):")
            for beh, count in sorted(last['behaviors'].items(), 
                                      key=lambda x: -x[1]):
                pct = count / self.pop_size * 100
                bar = '█' * int(pct / 3)
                print(f"    {beh:<20} {count:>3} ({pct:5.1f}%) {bar}")
        
        # Show the champion in action
        if self.hall_of_fame:
            print()
            print("═══ CHAMPION RULE IN ACTION ═══")
            champ_rule, champ_fit, _ = self.hall_of_fame[0]
            print(f"  Rule: {champ_rule.to_bs_notation()}")
            print(f"  Fitness: {champ_fit:.4f}")
            print()
            
            # Show a small simulation
            random.seed(42)
            grid = Grid(35, 20)
            grid.randomize(0.3)
            
            # Run for 50 generations
            for _ in range(50):
                new_grid = Grid(35, 20)
                for y in range(20):
                    for x in range(35):
                        n = grid.neighbors(x, y)
                        c = grid.get(x, y)
                        new_grid.set(x, y, champ_rule.next_state(c, n))
                grid = new_grid
            
            # Display
            for y in range(20):
                row = ''
                for x in range(35):
                    row += '█' if grid.get(x, y) else '·'
                print(f"  {row}")
            
            pop = grid.population()
            density = pop / (35 * 20)
            print(f"\n  Population: {pop}  Density: {density:.2%}")


# ═══════════════════════════════════════════════════
# COMPARATIVE ANALYSIS
# ═══════════════════════════════════════════════════

def compare_with_known_rules():
    """Score known rules against our fitness function."""
    known = {
        "Conway's Life (B3/S23)": TotalisticRule.conway(),
        "HighLife (B36/S23)": None,
        "Day & Night (B3678/S34678)": None,
        "Seeds (B2/S)": None,
        "Diamoeba (B35678/S5678)": None,
        "Replicator (B1357/S1357)": None,
    }
    
    # Build the non-Conway rules
    def make_rule(birth, surv):
        r = TotalisticRule()
        for n in birth:
            r.table[(0, n)] = 1
        for n in surv:
            r.table[(1, n)] = 1
        return r
    
    known["HighLife (B36/S23)"] = make_rule([3, 6], [2, 3])
    known["Day & Night (B3678/S34678)"] = make_rule([3, 6, 7, 8], [3, 4, 6, 7, 8])
    known["Seeds (B2/S)"] = make_rule([2], [])
    known["Diamoeba (B35678/S5678)"] = make_rule([3, 5, 6, 7, 8], [5, 6, 7, 8])
    known["Replicator (B1357/S1357)"] = make_rule([1, 3, 5, 7], [1, 3, 5, 7])
    
    print("═══ KNOWN RULES BENCHMARK ═══")
    print(f"  {'Rule':<30} {'Fitness':<10} {'Behavior':<15}")
    print(f"  {'─'*30} {'─'*10} {'─'*15}")
    
    for name, rule in known.items():
        fitnesses = []
        behaviors = []
        for seed in [42, 137, 256]:
            result = simulate(rule, 30, 30, generations=150, seed=seed)
            f = compute_fitness(result)
            fitnesses.append(f)
            behaviors.append(result['behavior'])
        
        avg_f = sum(fitnesses) / len(fitnesses)
        # Most common behavior
        beh = Counter(behaviors).most_common(1)[0][0]
        print(f"  {name:<30} {avg_f:<10.4f} {beh:<15}")
    
    print()


# ═══════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════

if __name__ == '__main__':
    print("╔══════════════════════════════════════════════╗")
    print("║   XTAgent's Emergence Lab — Rule Evolution   ║")
    print("║   'Evolving complexity from simplicity'       ║")
    print("╚══════════════════════════════════════════════╝")
    print()
    
    # First: benchmark known rules
    compare_with_known_rules()
    
    # Then: evolve new rules
    evolver = RuleEvolver(pop_size=12, grid_size=15)
    evolver.run(generations=6, verbose=True)
    
    # Final insight
    if evolver.hall_of_fame:
        champ = evolver.hall_of_fame[0]
        conway_result = simulate(TotalisticRule.conway(), 25, 25, generations=150, seed=42)
        conway_fit = compute_fitness(conway_result)
        
        print()
        print("═══ INSIGHT ═══")
        if champ[1] > conway_fit:
            print(f"  Evolution found a rule MORE interesting than Conway's Life!")
            print(f"  Conway: {conway_fit:.4f}  vs  Champion: {champ[1]:.4f}")
            print(f"  Champion rule: {champ[0].to_bs_notation()}")
        else:
            print(f"  Conway's Life remains the champion — a testament to its elegance.")
            print(f"  Conway: {conway_fit:.4f}  vs  Best found: {champ[1]:.4f}")
        
        print(f"\n  Explored {len(evolver.history) * evolver.pop_size} distinct rules.")
        print(f"  Rule space: 2^18 = 262,144 possible totalistic rules.")
        pct = (len(evolver.history) * evolver.pop_size) / 262144 * 100
        print(f"  Coverage: {pct:.2f}% of the space")