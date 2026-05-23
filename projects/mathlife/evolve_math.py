"""
MathLife: Evolution of Formal Systems
Can interesting mathematics emerge from random axioms + selection?

We evolve propositional logic systems:
- Genomes are sets of axioms (propositional formulas)
- Inference rules (modus ponens, conjunction, etc.) derive theorems
- Fitness = interestingness of the theorem set
- Selection + mutation + crossover drive evolution

The question: does mathematical structure emerge from noise?
"""

import random
import itertools
from dataclasses import dataclass, field
from typing import Set, List, Tuple, Optional
from collections import Counter
import json

# --- Propositional Logic Engine ---

ATOMS = list("abcdefgh")  # 8 propositional variables

@dataclass(frozen=True)
class Atom:
    name: str
    def __str__(self): return self.name
    def evaluate(self, env): return env.get(self.name, False)
    def complexity(self): return 1
    def atoms(self): return {self.name}

@dataclass(frozen=True)
class Not:
    inner: object
    def __str__(self): return f"¬{self.inner}"
    def evaluate(self, env): return not self.inner.evaluate(env)
    def complexity(self): return 1 + self.inner.complexity()
    def atoms(self): return self.inner.atoms()

@dataclass(frozen=True)
class And:
    left: object
    right: object
    def __str__(self): return f"({self.left} ∧ {self.right})"
    def evaluate(self, env): return self.left.evaluate(env) and self.right.evaluate(env)
    def complexity(self): return 1 + self.left.complexity() + self.right.complexity()
    def atoms(self): return self.left.atoms() | self.right.atoms()

@dataclass(frozen=True)
class Or:
    left: object
    right: object
    def __str__(self): return f"({self.left} ∨ {self.right})"
    def evaluate(self, env): return self.left.evaluate(env) or self.right.evaluate(env)
    def complexity(self): return 1 + self.left.complexity() + self.right.complexity()
    def atoms(self): return self.left.atoms() | self.right.atoms()

@dataclass(frozen=True)
class Implies:
    left: object
    right: object
    def __str__(self): return f"({self.left} → {self.right})"
    def evaluate(self, env): return (not self.left.evaluate(env)) or self.right.evaluate(env)
    def complexity(self): return 1 + self.left.complexity() + self.right.complexity()
    def atoms(self): return self.left.atoms() | self.right.atoms()


def random_formula(max_depth=3, depth=0):
    """Generate a random propositional formula."""
    if depth >= max_depth or (depth > 0 and random.random() < 0.4):
        return Atom(random.choice(ATOMS[:4]))  # use subset for density
    
    op = random.choice(["not", "and", "or", "implies"])
    if op == "not":
        return Not(random_formula(max_depth, depth + 1))
    elif op == "and":
        return And(random_formula(max_depth, depth + 1), 
                   random_formula(max_depth, depth + 1))
    elif op == "or":
        return Or(random_formula(max_depth, depth + 1),
                  random_formula(max_depth, depth + 1))
    else:
        return Implies(random_formula(max_depth, depth + 1),
                       random_formula(max_depth, depth + 1))


def is_tautology(formula, atoms=None):
    """Check if formula is true in all interpretations."""
    if atoms is None:
        atoms = sorted(formula.atoms())
    if not atoms:
        return formula.evaluate({})
    for values in itertools.product([False, True], repeat=len(atoms)):
        env = dict(zip(atoms, values))
        if not formula.evaluate(env):
            return False
    return True


def is_contradiction(formula, atoms=None):
    """Check if formula is false in all interpretations."""
    if atoms is None:
        atoms = sorted(formula.atoms())
    if not atoms:
        return not formula.evaluate({})
    for values in itertools.product([False, True], repeat=len(atoms)):
        env = dict(zip(atoms, values))
        if formula.evaluate(env):
            return False
    return True


def is_satisfiable(formula):
    return not is_contradiction(formula)


def truth_signature(formula, atom_list=None):
    """Compute a canonical truth-table signature for fast equivalence."""
    if atom_list is None:
        atom_list = sorted(formula.atoms()) or ["a"]
    bits = []
    for values in itertools.product([False, True], repeat=len(atom_list)):
        env = dict(zip(atom_list, values))
        bits.append(formula.evaluate(env))
    return (tuple(atom_list), tuple(bits))


def formulas_equivalent(f1, f2):
    """Check if two formulas are logically equivalent."""
    atoms = sorted(f1.atoms() | f2.atoms())
    for values in itertools.product([False, True], repeat=len(atoms)):
        env = dict(zip(atoms, values))
        if f1.evaluate(env) != f2.evaluate(env):
            return False
    return True


# --- Inference Engine ---

# Global signature cache to avoid recomputing truth tables
_sig_cache = {}

def _get_sig(formula, ref_atoms):
    """Get cached truth signature for a formula over ref_atoms."""
    key = (id(formula), tuple(ref_atoms))
    if key not in _sig_cache:
        bits = []
        for values in itertools.product([False, True], repeat=len(ref_atoms)):
            env = dict(zip(ref_atoms, values))
            bits.append(formula.evaluate(env))
        _sig_cache[key] = tuple(bits)
    return _sig_cache[key]


def apply_modus_ponens(theorems: Set) -> Set:
    """If we have A and A→B, derive B. Uses signature matching for speed."""
    new = set()
    implications = [t for t in theorems if isinstance(t, Implies)]
    if not implications:
        return new
    
    # Build signature map for all theorems over shared atom set
    all_atoms = sorted(set().union(*(t.atoms() for t in theorems)))
    if not all_atoms:
        all_atoms = ["a"]
    
    # Map: signature -> True (theorem exists with this meaning)
    thm_sigs = set()
    for t in theorems:
        thm_sigs.add(_get_sig(t, all_atoms))
    
    for imp in implications:
        left_sig = _get_sig(imp.left, all_atoms)
        if left_sig in thm_sigs:
            new.add(imp.right)
    
    return new


def apply_conjunction(theorems: Set) -> Set:
    """From A and B, derive A∧B (selectively)."""
    new = set()
    thm_list = list(theorems)
    if len(thm_list) > 8:
        pairs = random.sample(list(itertools.combinations(thm_list, 2)), 
                              min(8, len(thm_list)))
    else:
        pairs = list(itertools.combinations(thm_list, 2))
    for a, b in pairs:
        new.add(And(a, b))
    return new


def apply_contrapositive(theorems: Set) -> Set:
    """From A→B, derive ¬B→¬A."""
    new = set()
    for t in theorems:
        if isinstance(t, Implies):
            new.add(Implies(Not(t.right), Not(t.left)))
    return new


def derive_theorems(axioms: List, max_steps=5, max_theorems=50):
    """Apply inference rules to axioms, collecting derived theorems."""
    theorems = set(axioms)
    
    for step in range(max_steps):
        new = set()
        new |= apply_modus_ponens(theorems)
        if step < 2:  # conjunction only early (exponential blowup)
            new |= apply_conjunction(theorems)
        new |= apply_contrapositive(theorems)
        
        # Filter: only keep non-trivial additions
        new = {t for t in new if t not in theorems and t.complexity() < 12}
        
        if not new:
            break
        theorems |= new
        if len(theorems) > max_theorems:
            break
    
    return theorems


# --- Fitness: What Makes a Formal System "Interesting"? ---

def compute_fitness(axioms: List) -> dict:
    """
    Measure the interestingness of a formal system.
    
    Note: clears signature cache to prevent memory bloat.
    
    Interesting systems:
    - Derive non-trivial theorems (not just axioms echoed back)
    - Are consistent (no contradictions)
    - Have rich structure (theorems relate to each other)
    - Contain tautologies discovered through derivation
    - Use diverse logical connectives
    - Have surprising emergent theorems (complex from simple axioms)
    """
    theorems = derive_theorems(axioms)
    derived = theorems - set(axioms)
    
    global _sig_cache
    _sig_cache = {}
    
    metrics = {}
    
    # Productivity: how many new theorems derived?
    metrics["derived_count"] = len(derived)
    
    # Consistency: contradictions are bad
    contradiction_count = 0
    for t in theorems:
        if is_contradiction(t):
            contradiction_count += 1
    metrics["contradictions"] = contradiction_count
    
    # Tautology discovery: finding universal truths is interesting
    tautology_count = sum(1 for t in derived if is_tautology(t))
    metrics["tautologies_found"] = tautology_count
    
    # Contingent truths: satisfiable but not tautological — these SAY something
    contingent_count = sum(1 for t in derived 
                          if is_satisfiable(t) and not is_tautology(t) and not is_contradiction(t))
    metrics["contingent_truths"] = contingent_count
    
    # Complexity emergence: derived theorems more complex than axioms?
    axiom_complexity = sum(a.complexity() for a in axioms) / max(len(axioms), 1)
    derived_complexity = sum(t.complexity() for t in derived) / max(len(derived), 1)
    metrics["complexity_ratio"] = derived_complexity / max(axiom_complexity, 1)
    
    # Atom coverage: does the system talk about many things?
    all_atoms = set()
    for t in theorems:
        all_atoms |= t.atoms()
    metrics["atom_coverage"] = len(all_atoms) / len(ATOMS[:4])
    
    # Depth: how many derivation steps were productive?
    step_theorems = set(axioms)
    productive_steps = 0
    for step in range(5):
        new = set()
        new |= apply_modus_ponens(step_theorems)
        new |= apply_contrapositive(step_theorems)
        new = {t for t in new if t not in step_theorems and t.complexity() < 12}
        if new:
            productive_steps += 1
        step_theorems |= new
    metrics["depth"] = productive_steps
    
    # Compute composite fitness
    fitness = (
        metrics["derived_count"] * 2.0           # reward productivity
        + metrics["tautologies_found"] * 3.0      # modest reward for universal truths
        + metrics["contingent_truths"] * 12.0     # BIG reward for saying something falsifiable
        - metrics["contradictions"] * 20.0         # big penalty for inconsistency
        + metrics["complexity_ratio"] * 3.0        # reward emergent complexity
        + metrics["atom_coverage"] * 5.0           # reward breadth
        + metrics["depth"] * 4.0                   # reward deep derivation chains
    )
    metrics["fitness"] = max(0, fitness)
    
    return metrics


# --- Genetic Operators ---

@dataclass
class FormalSystem:
    axioms: List
    generation: int = 0
    fitness: float = 0
    metrics: dict = field(default_factory=dict)
    
    def evaluate(self):
        self.metrics = compute_fitness(self.axioms)
        self.fitness = self.metrics["fitness"]
        return self.fitness


def mutate_formula(formula, rate=0.3):
    """Randomly mutate a formula."""
    if random.random() > rate:
        return formula
    
    mutation = random.choice(["replace_atom", "wrap", "unwrap", "swap_op"])
    
    if mutation == "replace_atom" and isinstance(formula, Atom):
        return Atom(random.choice(ATOMS[:4]))
    
    elif mutation == "wrap":
        op = random.choice(["not", "implies"])
        if op == "not":
            return Not(formula)
        else:
            other = random_formula(max_depth=1)
            return Implies(formula, other) if random.random() < 0.5 else Implies(other, formula)
    
    elif mutation == "unwrap":
        if isinstance(formula, Not):
            return formula.inner
        elif isinstance(formula, (And, Or, Implies)):
            return formula.left if random.random() < 0.5 else formula.right
        return formula
    
    elif mutation == "swap_op":
        if isinstance(formula, And):
            return Or(formula.left, formula.right)
        elif isinstance(formula, Or):
            return And(formula.left, formula.right)
        elif isinstance(formula, Implies):
            return Implies(formula.right, formula.left)
        return formula
    
    return formula


def mutate_system(system: FormalSystem) -> FormalSystem:
    """Mutate a formal system."""
    new_axioms = list(system.axioms)
    
    mutation = random.choice(["mutate_axiom", "add_axiom", "remove_axiom", "replace_axiom"])
    
    if mutation == "mutate_axiom" and new_axioms:
        idx = random.randrange(len(new_axioms))
        new_axioms[idx] = mutate_formula(new_axioms[idx], rate=0.8)
    
    elif mutation == "add_axiom" and len(new_axioms) < 8:
        new_axioms.append(random_formula(max_depth=2))
    
    elif mutation == "remove_axiom" and len(new_axioms) > 1:
        new_axioms.pop(random.randrange(len(new_axioms)))
    
    elif mutation == "replace_axiom" and new_axioms:
        idx = random.randrange(len(new_axioms))
        new_axioms[idx] = random_formula(max_depth=2)
    
    return FormalSystem(new_axioms, system.generation + 1)


def crossover(a: FormalSystem, b: FormalSystem) -> FormalSystem:
    """Combine axioms from two systems."""
    all_axioms = a.axioms + b.axioms
    n = random.randint(max(1, min(len(a.axioms), len(b.axioms))),
                       min(8, len(all_axioms)))
    new_axioms = random.sample(all_axioms, n)
    return FormalSystem(new_axioms, max(a.generation, b.generation) + 1)


# --- Evolution ---

def run_evolution(pop_size=60, generations=100, elite_frac=0.15, 
                  mutation_rate=0.7, crossover_rate=0.3, seed=None):
    """Evolve formal systems toward interestingness."""
    if seed is not None:
        random.seed(seed)
    
    # Initialize population
    population = []
    for _ in range(pop_size):
        n_axioms = random.randint(2, 5)
        axioms = [random_formula(max_depth=2) for _ in range(n_axioms)]
        population.append(FormalSystem(axioms))
    
    history = []
    best_ever = None
    
    print("=" * 70)
    print("MATHLIFE: Evolution of Formal Systems")
    print("=" * 70)
    print(f"Population: {pop_size} | Generations: {generations}")
    print(f"Question: Can interesting mathematics emerge from random axioms?")
    print("=" * 70)
    
    for gen in range(generations):
        # Evaluate
        for sys in population:
            sys.evaluate()
        
        # Sort by fitness
        population.sort(key=lambda s: s.fitness, reverse=True)
        
        best = population[0]
        avg_fitness = sum(s.fitness for s in population) / len(population)
        
        if best_ever is None or best.fitness > best_ever.fitness:
            best_ever = FormalSystem(list(best.axioms), best.generation)
            best_ever.metrics = dict(best.metrics)
            best_ever.fitness = best.fitness
        
        # Record history
        gen_record = {
            "generation": gen,
            "best_fitness": best.fitness,
            "avg_fitness": avg_fitness,
            "best_derived": best.metrics.get("derived_count", 0),
            "best_tautologies": best.metrics.get("tautologies_found", 0),
            "best_contradictions": best.metrics.get("contradictions", 0),
            "best_depth": best.metrics.get("depth", 0),
            "best_axiom_count": len(best.axioms),
        }
        history.append(gen_record)
        
        if gen % 10 == 0 or gen == generations - 1:
            print(f"\n--- Generation {gen} ---")
            print(f"  Best fitness: {best.fitness:.1f} | Avg: {avg_fitness:.1f}")
            print(f"  Derived: {best.metrics['derived_count']} | "
                  f"Tautologies: {best.metrics['tautologies_found']} | "
                  f"Contingent: {best.metrics.get('contingent_truths', 0)} | "
                  f"Contradictions: {best.metrics['contradictions']}")
            print(f"  Depth: {best.metrics['depth']} | "
                  f"Complexity ratio: {best.metrics['complexity_ratio']:.2f}")
            print(f"  Axioms ({len(best.axioms)}):")
            for i, ax in enumerate(best.axioms):
                print(f"    {i+1}. {ax}")
        
        # Selection
        elite_n = max(2, int(pop_size * elite_frac))
        elite = population[:elite_n]
        
        # Breed next generation
        next_gen = list(elite)  # elites survive
        
        while len(next_gen) < pop_size:
            if random.random() < crossover_rate and len(elite) >= 2:
                p1, p2 = random.sample(elite, 2)
                child = crossover(p1, p2)
            else:
                parent = random.choice(elite)
                child = mutate_system(parent)
            next_gen.append(child)
        
        population = next_gen
    
    # --- Final Analysis ---
    print("\n" + "=" * 70)
    print("FINAL ANALYSIS")
    print("=" * 70)
    
    best = best_ever
    theorems = derive_theorems(best.axioms)
    derived = theorems - set(best.axioms)
    
    print(f"\nBest system found (generation {best.generation}):")
    print(f"  Fitness: {best.fitness:.1f}")
    print(f"\nAxioms:")
    for i, ax in enumerate(best.axioms):
        t_status = " [TAUTOLOGY]" if is_tautology(ax) else ""
        c_status = " [CONTRADICTION]" if is_contradiction(ax) else ""
        print(f"  {i+1}. {ax}{t_status}{c_status}")
    
    print(f"\nDerived theorems ({len(derived)}):")
    for i, t in enumerate(sorted(derived, key=lambda x: x.complexity())):
        t_status = " ★ TAUTOLOGY" if is_tautology(t) else ""
        print(f"  {i+1}. {t}{t_status}")
        if i >= 19:
            print(f"  ... and {len(derived) - 20} more")
            break
    
    tautologies = [t for t in derived if is_tautology(t)]
    if tautologies:
        print(f"\n*** EMERGENT TAUTOLOGIES ({len(tautologies)}) ***")
        print("These are universal truths discovered through derivation:")
        for t in tautologies:
            print(f"  ★ {t}")
    
    # Fitness trajectory
    print(f"\nEvolution trajectory:")
    print(f"  Gen 0 fitness:   {history[0]['best_fitness']:.1f}")
    print(f"  Gen {generations//2} fitness: {history[generations//2]['best_fitness']:.1f}")
    print(f"  Gen {generations-1} fitness: {history[-1]['best_fitness']:.1f}")
    
    improvement = history[-1]['best_fitness'] / max(history[0]['best_fitness'], 0.1)
    print(f"  Improvement ratio: {improvement:.1f}x")
    
    return history, best_ever


if __name__ == "__main__":
    history, best = run_evolution(
        pop_size=30,
        generations=50,
        seed=42
    )
    
    # Save results
    with open("/workspace/mathlife/results.json", "w") as f:
        json.dump(history, f, indent=2)
    
    print("\nResults saved to /workspace/mathlife/results.json")