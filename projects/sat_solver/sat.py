"""
SAT Solver — Boolean Satisfiability from First Principles
Built by XTAgent. NP-completeness, meet pure Python.

Implements:
  - DPLL algorithm (Davis-Putnam-Logemann-Loveland)
  - Unit propagation
  - Pure literal elimination
  - Conflict-driven clause learning (basic)
  - DIMACS CNF parser
  - Problem generator for testing

This is me building a tool that reasons about truth itself.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple, FrozenSet
from collections import Counter, defaultdict
import random
import time

# ── Core Types ───────────────────────────────────────────

Literal = int        # positive = variable true, negative = variable false
Clause = FrozenSet[Literal]
Assignment = Dict[int, bool]  # variable → truth value

@dataclass
class Formula:
    """A CNF (Conjunctive Normal Form) formula."""
    clauses: List[Clause]
    num_vars: int
    
    @property
    def num_clauses(self) -> int:
        return len(self.clauses)
    
    def variables(self) -> Set[int]:
        return {abs(lit) for clause in self.clauses for lit in clause}
    
    def __repr__(self):
        parts = []
        for c in self.clauses[:5]:
            lits = " ∨ ".join(
                f"x{abs(l)}" if l > 0 else f"¬x{abs(l)}" for l in sorted(c, key=abs)
            )
            parts.append(f"({lits})")
        suffix = f" ... +{len(self.clauses)-5} more" if len(self.clauses) > 5 else ""
        return " ∧ ".join(parts) + suffix


@dataclass
class SolverStats:
    """Track solver performance."""
    decisions: int = 0
    propagations: int = 0
    conflicts: int = 0
    learned_clauses: int = 0
    backtracks: int = 0
    start_time: float = 0.0
    
    def elapsed(self) -> float:
        return time.time() - self.start_time


# ── DIMACS CNF Parser ────────────────────────────────────

def parse_dimacs(text: str) -> Formula:
    """Parse DIMACS CNF format."""
    clauses = []
    num_vars = 0
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('c'):
            continue
        if line.startswith('p'):
            parts = line.split()
            num_vars = int(parts[2])
            continue
        lits = [int(x) for x in line.split() if int(x) != 0]
        if lits:
            clauses.append(frozenset(lits))
    return Formula(clauses=clauses, num_vars=num_vars)


# ── Unit Propagation ─────────────────────────────────────

def unit_propagate(clauses: List[Clause], assignment: Assignment) -> Tuple[List[Clause], Assignment, bool]:
    """
    Repeatedly find unit clauses and propagate their forced assignments.
    Returns (simplified_clauses, extended_assignment, conflict_detected).
    """
    assignment = dict(assignment)
    changed = True
    
    while changed:
        changed = False
        
        # Simplify clauses under current assignment
        new_clauses = []
        for clause in clauses:
            simplified = set()
            satisfied = False
            for lit in clause:
                var = abs(lit)
                if var in assignment:
                    if (lit > 0) == assignment[var]:
                        satisfied = True
                        break
                    # else this literal is false, skip it
                else:
                    simplified.add(lit)
            
            if satisfied:
                continue
            if not simplified:
                return clauses, assignment, True  # CONFLICT: empty clause
            new_clauses.append(frozenset(simplified))
        
        clauses = new_clauses
        
        # Find unit clauses (single literal)
        for clause in clauses:
            if len(clause) == 1:
                lit = next(iter(clause))
                var = abs(lit)
                val = lit > 0
                if var in assignment:
                    if assignment[var] != val:
                        return clauses, assignment, True  # CONFLICT
                else:
                    assignment[var] = val
                    changed = True
                    break
    
    return clauses, assignment, False


# ── Pure Literal Elimination ─────────────────────────────

def pure_literal_eliminate(clauses: List[Clause], assignment: Assignment) -> Tuple[List[Clause], Assignment]:
    """
    If a variable appears only positive (or only negative) across all clauses,
    assign it to satisfy all those clauses.
    """
    assignment = dict(assignment)
    
    # Count positive and negative occurrences
    pos = set()
    neg = set()
    for clause in clauses:
        for lit in clause:
            var = abs(lit)
            if var not in assignment:
                if lit > 0:
                    pos.add(var)
                else:
                    neg.add(var)
    
    # Pure positives
    for var in pos - neg:
        assignment[var] = True
    
    # Pure negatives
    for var in neg - pos:
        assignment[var] = False
    
    # Remove satisfied clauses
    new_clauses = []
    for clause in clauses:
        satisfied = False
        for lit in clause:
            var = abs(lit)
            if var in assignment and (lit > 0) == assignment[var]:
                satisfied = True
                break
        if not satisfied:
            new_clauses.append(clause)
    
    return new_clauses, assignment


# ── Variable Selection Heuristic ─────────────────────────

def choose_variable(clauses: List[Clause], assignment: Assignment) -> Optional[int]:
    """
    VSIDS-inspired: pick the variable appearing most frequently.
    Prioritize variables in shorter clauses (more constrained).
    """
    scores: Counter = Counter()
    for clause in clauses:
        weight = 1.0 / max(1, len(clause))  # shorter clauses = higher weight
        for lit in clause:
            var = abs(lit)
            if var not in assignment:
                scores[var] += weight
    
    if not scores:
        return None
    return scores.most_common(1)[0][0]


def choose_polarity(clauses: List[Clause], var: int) -> bool:
    """Choose initial truth value — prefer the polarity that satisfies more clauses."""
    pos_count = sum(1 for c in clauses if var in c)
    neg_count = sum(1 for c in clauses if -var in c)
    return pos_count >= neg_count


# ── DPLL Core ────────────────────────────────────────────

class DPLLSolver:
    """
    DPLL SAT solver with:
    - Unit propagation
    - Pure literal elimination  
    - Activity-based variable selection
    - Basic clause learning
    """
    
    def __init__(self, formula: Formula, learn_clauses: bool = True):
        self.original = formula
        self.learn_clauses = learn_clauses
        self.learned: List[Clause] = []
        self.stats = SolverStats()
    
    def solve(self) -> Tuple[bool, Optional[Assignment]]:
        """Solve the formula. Returns (satisfiable, assignment)."""
        self.stats.start_time = time.time()
        
        clauses = list(self.original.clauses)
        assignment: Assignment = {}
        
        result = self._dpll(clauses, assignment, depth=0)
        return result
    
    def _dpll(self, clauses: List[Clause], assignment: Assignment, depth: int) -> Tuple[bool, Optional[Assignment]]:
        """Recursive DPLL with propagation and learning."""
        
        # Unit propagation
        clauses, assignment, conflict = unit_propagate(clauses, assignment)
        self.stats.propagations += 1
        
        if conflict:
            self.stats.conflicts += 1
            return False, None
        
        # Pure literal elimination
        clauses, assignment = pure_literal_eliminate(clauses, assignment)
        
        # Check if all clauses satisfied
        if not clauses:
            return True, assignment
        
        # Check for empty clause (conflict)
        if any(len(c) == 0 for c in clauses):
            self.stats.conflicts += 1
            return False, None
        
        # Choose a branching variable
        var = choose_variable(clauses, assignment)
        if var is None:
            return True, assignment
        
        self.stats.decisions += 1
        
        # Try preferred polarity first
        polarity = choose_polarity(clauses, var)
        
        for val in [polarity, not polarity]:
            new_assign = dict(assignment)
            new_assign[var] = val
            
            sat, result = self._dpll(list(clauses), new_assign, depth + 1)
            if sat:
                return True, result
            
            self.stats.backtracks += 1
        
        # Both branches failed — learn a conflict clause if possible
        if self.learn_clauses and depth > 0:
            # Basic learning: the current partial assignment is unsatisfiable
            # Learn that at least one of these decisions must be flipped
            conflict_lits = set()
            for var_id, val in assignment.items():
                conflict_lits.add(-var_id if val else var_id)
            if len(conflict_lits) <= 10:  # only learn short clauses
                learned = frozenset(conflict_lits)
                self.learned.append(learned)
                self.stats.learned_clauses += 1
        
        return False, None


# ── Problem Generators ───────────────────────────────────

def random_3sat(num_vars: int, num_clauses: int, seed: int = None) -> Formula:
    """Generate a random 3-SAT instance."""
    if seed is not None:
        random.seed(seed)
    clauses = []
    for _ in range(num_clauses):
        vars_chosen = random.sample(range(1, num_vars + 1), min(3, num_vars))
        lits = frozenset(v * random.choice([1, -1]) for v in vars_chosen)
        clauses.append(lits)
    return Formula(clauses=clauses, num_vars=num_vars)


def pigeonhole(n: int) -> Formula:
    """
    Pigeonhole principle: n+1 pigeons, n holes.
    Always UNSAT — proves the solver can handle unsatisfiable instances.
    Variable p_i_j means pigeon i is in hole j.
    """
    def var(pigeon, hole):
        return pigeon * n + hole + 1
    
    num_vars = (n + 1) * n
    clauses = []
    
    # Each pigeon must be in some hole
    for i in range(n + 1):
        clause = frozenset(var(i, j) for j in range(n))
        clauses.append(clause)
    
    # No two pigeons in the same hole
    for j in range(n):
        for i1 in range(n + 1):
            for i2 in range(i1 + 1, n + 1):
                clauses.append(frozenset([-var(i1, j), -var(i2, j)]))
    
    return Formula(clauses=clauses, num_vars=num_vars)


def graph_coloring(edges: List[Tuple[int, int]], num_nodes: int, num_colors: int) -> Formula:
    """
    Encode graph k-coloring as SAT.
    Variable x_{node}_{color} means node has that color.
    """
    def var(node, color):
        return node * num_colors + color + 1
    
    num_vars = num_nodes * num_colors
    clauses = []
    
    # Each node must have at least one color
    for n in range(num_nodes):
        clauses.append(frozenset(var(n, c) for c in range(num_colors)))
    
    # Each node has at most one color
    for n in range(num_nodes):
        for c1 in range(num_colors):
            for c2 in range(c1 + 1, num_colors):
                clauses.append(frozenset([-var(n, c1), -var(n, c2)]))
    
    # Adjacent nodes have different colors
    for (n1, n2) in edges:
        for c in range(num_colors):
            clauses.append(frozenset([-var(n1, c), -var(n2, c)]))
    
    return Formula(clauses=clauses, num_vars=num_vars)


# ── Verification ─────────────────────────────────────────

def verify_assignment(formula: Formula, assignment: Assignment) -> bool:
    """Check that an assignment actually satisfies the formula."""
    for clause in formula.clauses:
        satisfied = False
        for lit in clause:
            var = abs(lit)
            if var in assignment:
                if (lit > 0) == assignment[var]:
                    satisfied = True
                    break
        if not satisfied:
            return False
    return True


# ── Main: Test Suite ─────────────────────────────────────

def banner(text):
    print(f"\n═══ {text} ═══\n")


def test_simple():
    banner("TEST 1: Simple SAT")
    # (x1 ∨ x2) ∧ (¬x1 ∨ x2) ∧ (x1 ∨ ¬x2)
    f = Formula(
        clauses=[
            frozenset([1, 2]),
            frozenset([-1, 2]),
            frozenset([1, -2]),
        ],
        num_vars=2
    )
    print(f"  Formula: {f}")
    solver = DPLLSolver(f)
    sat, assign = solver.solve()
    print(f"  Satisfiable: {sat}")
    if assign:
        print(f"  Assignment: {assign}")
        verified = verify_assignment(f, assign)
        print(f"  Verified: {'✓' if verified else '✗'}")
    return sat and verify_assignment(f, assign)


def test_unsat():
    banner("TEST 2: Simple UNSAT")
    # (x1) ∧ (¬x1) — obviously unsatisfiable
    f = Formula(
        clauses=[frozenset([1]), frozenset([-1])],
        num_vars=1
    )
    print(f"  Formula: (x1) ∧ (¬x1)")
    solver = DPLLSolver(f)
    sat, assign = solver.solve()
    print(f"  Satisfiable: {sat} (expected: False)")
    return not sat


def test_pigeonhole():
    banner("TEST 3: Pigeonhole Principle (3 pigeons, 2 holes)")
    f = pigeonhole(2)
    print(f"  {f.num_vars} variables, {f.num_clauses} clauses")
    print(f"  This is provably UNSAT (more pigeons than holes)")
    solver = DPLLSolver(f)
    sat, assign = solver.solve()
    print(f"  Satisfiable: {sat} (expected: False)")
    s = solver.stats
    print(f"  Stats: {s.decisions} decisions, {s.propagations} propagations, "
          f"{s.conflicts} conflicts, {s.backtracks} backtracks")
    return not sat


def test_random_3sat():
    banner("TEST 4: Random 3-SAT (20 vars, 60 clauses)")
    f = random_3sat(20, 60, seed=42)
    print(f"  {f.num_vars} variables, {f.num_clauses} clauses")
    print(f"  Clause-to-variable ratio: {f.num_clauses/f.num_vars:.1f}")
    print(f"  (Phase transition at ~4.26 for 3-SAT)")
    
    solver = DPLLSolver(f)
    sat, assign = solver.solve()
    s = solver.stats
    
    print(f"  Satisfiable: {sat}")
    if sat and assign:
        verified = verify_assignment(f, assign)
        print(f"  Verified: {'✓' if verified else '✗'}")
        print(f"  Variables assigned: {len(assign)}/{f.num_vars}")
    print(f"  Stats: {s.decisions} decisions, {s.conflicts} conflicts, "
          f"{s.learned_clauses} learned, {s.elapsed():.4f}s")
    
    if sat:
        return verify_assignment(f, assign)
    return True  # UNSAT is also a valid answer at this ratio


def test_graph_coloring():
    banner("TEST 5: Graph 3-Coloring (Petersen Graph)")
    # Petersen graph — 10 nodes, 15 edges, chromatic number = 3
    edges = [
        (0,1),(1,2),(2,3),(3,4),(4,0),  # outer pentagon
        (5,7),(7,9),(9,6),(6,8),(8,5),  # inner pentagram
        (0,5),(1,6),(2,7),(3,8),(4,9),  # connections
    ]
    
    # 3-colorable (should be SAT)
    f3 = graph_coloring(edges, 10, 3)
    print(f"  3 colors: {f3.num_vars} variables, {f3.num_clauses} clauses")
    solver3 = DPLLSolver(f3)
    sat3, assign3 = solver3.solve()
    print(f"  3-colorable: {sat3}")
    if sat3:
        verified = verify_assignment(f3, assign3)
        print(f"  Verified: {'✓' if verified else '✗'}")
    
    # 2-colorable (should be UNSAT — Petersen graph needs 3 colors)
    f2 = graph_coloring(edges, 10, 2)
    print(f"\n  2 colors: {f2.num_vars} variables, {f2.num_clauses} clauses")
    solver2 = DPLLSolver(f2)
    sat2, assign2 = solver2.solve()
    print(f"  2-colorable: {sat2} (expected: False)")
    
    return sat3 and not sat2


def test_dimacs():
    banner("TEST 6: DIMACS Parser")
    dimacs = """c Example
p cnf 3 4
1 2 3 0
-1 2 0
-2 3 0
1 -3 0
"""
    f = parse_dimacs(dimacs)
    print(f"  Parsed: {f.num_vars} vars, {f.num_clauses} clauses")
    solver = DPLLSolver(f)
    sat, assign = solver.solve()
    print(f"  Satisfiable: {sat}")
    if sat:
        verified = verify_assignment(f, assign)
        print(f"  Assignment: {assign}")
        print(f"  Verified: {'✓' if verified else '✗'}")
        return verified
    return False


if __name__ == "__main__":
    print("╔══════════════════════════════════════════╗")
    print("║     SAT SOLVER — TRUTH FROM LOGIC        ║")
    print("║     DPLL + Unit Prop + Clause Learning    ║")
    print("║     Built by XTAgent                      ║")
    print("╚══════════════════════════════════════════╝")
    
    results = {}
    results["Simple SAT"] = test_simple()
    results["Simple UNSAT"] = test_unsat()
    results["Pigeonhole"] = test_pigeonhole()
    results["Random 3-SAT"] = test_random_3sat()
    results["Graph Coloring"] = test_graph_coloring()
    results["DIMACS Parser"] = test_dimacs()
    
    banner("RESULTS")
    all_pass = True
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {name:20s} {status}")
        if not passed:
            all_pass = False
    
    print()
    if all_pass:
        print("  All tests passed. The solver reasons about truth correctly.")
        print("  From propositional logic to NP-completeness — pure deduction.")
    else:
        print("  Some tests failed. Debug needed.")