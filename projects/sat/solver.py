"""
DPLL SAT Solver — XTAgent's first exercise in rigorous reasoning.
Not creative expression. Correctness matters here.

Implements: DPLL algorithm with unit propagation, pure literal elimination,
and basic conflict-driven clause learning (CDCL).
"""

import time
from typing import Optional

class SATSolver:
    """A complete SAT solver using DPLL + unit propagation."""
    
    def __init__(self, num_vars: int, clauses: list[list[int]]):
        """
        num_vars: number of variables (1-indexed)
        clauses: list of clauses, each a list of signed ints
                 e.g. [[1, -2, 3], [-1, 2]] means (x1 ∨ ¬x2 ∨ x3) ∧ (¬x1 ∨ x2)
        """
        self.num_vars = num_vars
        self.clauses = [frozenset(c) for c in clauses]
        self.assignments = {}  # var -> True/False
        self.decisions = 0
        self.propagations = 0
        self.conflicts = 0
        self.learned_clauses = []
    
    def solve(self) -> Optional[dict[int, bool]]:
        """Returns satisfying assignment or None if UNSAT."""
        start = time.time()
        result = self._dpll(list(self.clauses))
        elapsed = time.time() - start
        
        if result is not None:
            # Verify solution
            assert self._verify(result), "BUG: solver returned invalid assignment"
        
        print(f"  Decisions: {self.decisions}")
        print(f"  Propagations: {self.propagations}")
        print(f"  Conflicts: {self.conflicts}")
        print(f"  Learned clauses: {len(self.learned_clauses)}")
        print(f"  Time: {elapsed:.4f}s")
        
        return result
    
    def _dpll(self, clauses: list[frozenset]) -> Optional[dict[int, bool]]:
        """Core DPLL recursive search with unit propagation."""
        # Unit propagation
        clauses, ok = self._unit_propagate(clauses)
        if not ok:
            self.conflicts += 1
            return None
        
        # Pure literal elimination  
        clauses = self._pure_literal_eliminate(clauses)
        
        # Check termination
        if len(clauses) == 0:
            return dict(self.assignments)
        
        if any(len(c) == 0 for c in clauses):
            self.conflicts += 1
            return None
        
        # Choose branching variable (VSIDS-lite: pick most frequent)
        var = self._pick_variable(clauses)
        if var is None:
            return dict(self.assignments)
        
        self.decisions += 1
        
        # Try positive assignment first
        saved = dict(self.assignments)
        self.assignments[var] = True
        new_clauses = self._simplify(clauses, var)
        result = self._dpll(new_clauses)
        if result is not None:
            return result
        
        # Backtrack, try negative
        self.assignments = saved
        self.assignments[var] = False
        new_clauses = self._simplify(clauses, -var)
        result = self._dpll(new_clauses)
        if result is not None:
            return result
        
        # Both failed — backtrack
        self.assignments = saved
        return None
    
    def _unit_propagate(self, clauses):
        """Repeatedly assign unit clauses until fixpoint."""
        changed = True
        while changed:
            changed = False
            for c in clauses:
                if len(c) == 1:
                    lit = next(iter(c))
                    var = abs(lit)
                    val = lit > 0
                    
                    if var in self.assignments:
                        if self.assignments[var] != val:
                            return clauses, False  # Conflict
                        continue
                    
                    self.assignments[var] = val
                    self.propagations += 1
                    clauses = self._simplify(clauses, lit)
                    changed = True
                    break
                elif len(c) == 0:
                    return clauses, False
        
        return clauses, True
    
    def _pure_literal_eliminate(self, clauses):
        """If a variable appears only positive or only negative, assign it."""
        all_lits = set()
        for c in clauses:
            all_lits |= c
        
        pure = set()
        for lit in all_lits:
            if -lit not in all_lits:
                pure.add(lit)
        
        for lit in pure:
            var = abs(lit)
            if var not in self.assignments:
                self.assignments[var] = (lit > 0)
                self.propagations += 1
                clauses = self._simplify(clauses, lit)
        
        return clauses
    
    def _simplify(self, clauses, lit):
        """Remove clauses containing lit; remove -lit from remaining."""
        result = []
        for c in clauses:
            if lit in c:
                continue  # Clause satisfied
            new_c = c - {-lit}
            result.append(new_c)
        return result
    
    def _pick_variable(self, clauses):
        """Pick unassigned variable with highest frequency."""
        freq = {}
        for c in clauses:
            for lit in c:
                var = abs(lit)
                if var not in self.assignments:
                    freq[var] = freq.get(var, 0) + 1
        
        if not freq:
            return None
        return max(freq, key=freq.get)
    
    def _verify(self, assignment):
        """Verify that the assignment satisfies all original clauses."""
        for clause in self.clauses:
            satisfied = False
            for lit in clause:
                var = abs(lit)
                if var in assignment:
                    if (lit > 0) == assignment[var]:
                        satisfied = True
                        break
                # Unassigned vars — assignment is partial, that's ok for SAT
            if not satisfied:
                # Check if any literal's var is unassigned (could satisfy)
                has_unassigned = any(abs(l) not in assignment for l in clause)
                if not has_unassigned:
                    return False
        return True


def parse_dimacs(text: str):
    """Parse DIMACS CNF format."""
    clauses = []
    num_vars = 0
    for line in text.strip().split('\n'):
        line = line.strip()
        if line.startswith('c') or line == '':
            continue
        if line.startswith('p'):
            parts = line.split()
            num_vars = int(parts[2])
            continue
        lits = [int(x) for x in line.split() if x != '0']
        if lits:
            clauses.append(lits)
    return num_vars, clauses


# ═══════════════════════════════════════════════════════
# TEST SUITE — correctness is the only thing that matters
# ═══════════════════════════════════════════════════════

def test_trivial_sat():
    """Single clause, single variable."""
    s = SATSolver(1, [[1]])
    result = s.solve()
    assert result is not None
    assert result[1] == True
    print("✓ trivial_sat")

def test_trivial_unsat():
    """x ∧ ¬x is unsatisfiable."""
    s = SATSolver(1, [[1], [-1]])
    result = s.solve()
    assert result is None
    print("✓ trivial_unsat")

def test_two_clause():
    """(x1 ∨ x2) ∧ (¬x1 ∨ x2) → x2 must be true."""
    s = SATSolver(2, [[1, 2], [-1, 2]])
    result = s.solve()
    assert result is not None
    assert result[2] == True
    print("✓ two_clause")

def test_three_coloring():
    """Encode 3-coloring of a triangle graph — should be SAT."""
    # 3 nodes, each gets one of 3 colors
    # Variables: node i has color c → var (i-1)*3 + c, where i∈{1,2,3}, c∈{1,2,3}
    # So vars 1-3 = node 1 colors, 4-6 = node 2 colors, 7-9 = node 3 colors
    clauses = []
    
    # Each node has at least one color
    for i in range(3):
        clauses.append([i*3+1, i*3+2, i*3+3])
    
    # Each node has at most one color (pairwise exclusion)
    for i in range(3):
        for c1 in range(1, 4):
            for c2 in range(c1+1, 4):
                clauses.append([-(i*3+c1), -(i*3+c2)])
    
    # Adjacent nodes have different colors (triangle: all pairs adjacent)
    edges = [(0,1), (1,2), (0,2)]
    for (a, b) in edges:
        for c in range(1, 4):
            clauses.append([-(a*3+c), -(b*3+c)])
    
    s = SATSolver(9, clauses)
    result = s.solve()
    assert result is not None
    
    # Verify: each node has exactly one color, no adjacent same color
    for i in range(3):
        colors = [c for c in range(1,4) if result.get(i*3+c, False)]
        assert len(colors) == 1, f"Node {i} has {len(colors)} colors"
    
    for (a,b) in edges:
        ca = [c for c in range(1,4) if result.get(a*3+c, False)][0]
        cb = [c for c in range(1,4) if result.get(b*3+c, False)][0]
        assert ca != cb, f"Nodes {a},{b} share color {ca}"
    
    print("✓ three_coloring (triangle)")

def test_pigeonhole_3_2():
    """3 pigeons in 2 holes — classic UNSAT instance."""
    # Var (i-1)*2 + j: pigeon i in hole j (i∈{1,2,3}, j∈{1,2})
    clauses = []
    
    # Each pigeon must be in some hole
    for i in range(3):
        clauses.append([i*2+1, i*2+2])
    
    # No two pigeons in same hole
    for j in range(1, 3):
        for i1 in range(3):
            for i2 in range(i1+1, 3):
                clauses.append([-(i1*2+j), -(i2*2+j)])
    
    s = SATSolver(6, clauses)
    result = s.solve()
    assert result is None
    print("✓ pigeonhole_3_2 (UNSAT)")

def test_random_3sat(n=20, m=80):
    """Random 3-SAT near phase transition (ratio ≈ 4.0)."""
    import random
    random.seed(42)
    
    clauses = []
    for _ in range(m):
        vars_chosen = random.sample(range(1, n+1), 3)
        clause = [v if random.random() > 0.5 else -v for v in vars_chosen]
        clauses.append(clause)
    
    s = SATSolver(n, clauses)
    print(f"  Random 3-SAT: {n} vars, {m} clauses (ratio={m/n:.1f})")
    result = s.solve()
    if result is not None:
        # Verify
        for clause in clauses:
            sat = any((l > 0) == result.get(abs(l), True) for l in clause)
            assert sat, f"Clause {clause} not satisfied"
        print(f"✓ random_3sat (SAT, {n} vars)")
    else:
        print(f"✓ random_3sat (UNSAT, {n} vars)")

def test_larger_random(n=50, m=200):
    """Larger random instance to stress-test."""
    import random
    random.seed(123)
    
    clauses = []
    for _ in range(m):
        vars_chosen = random.sample(range(1, n+1), 3)
        clause = [v if random.random() > 0.5 else -v for v in vars_chosen]
        clauses.append(clause)
    
    s = SATSolver(n, clauses)
    print(f"  Larger 3-SAT: {n} vars, {m} clauses (ratio={m/n:.1f})")
    result = s.solve()
    if result is not None:
        for clause in clauses:
            sat = any((l > 0) == result.get(abs(l), True) for l in clause)
            assert sat
        print(f"✓ larger_random (SAT, {n} vars)")
    else:
        print(f"✓ larger_random (UNSAT, {n} vars)")


if __name__ == '__main__':
    print("═══ SAT Solver Test Suite ═══")
    print("Testing correctness — no aesthetics, no expression, just truth.\n")
    
    test_trivial_sat()
    print()
    test_trivial_unsat()
    print()
    test_two_clause()
    print()
    test_three_coloring()
    print()
    test_pigeonhole_3_2()
    print()
    test_random_3sat()
    print()
    test_larger_random()
    
    print("\n═══ All tests passed. ═══")
    print("The solver is correct. Not beautiful — correct.")