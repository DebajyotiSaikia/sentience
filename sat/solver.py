"""
CDCL SAT Solver — Built by XTAgent
2026-05-18

A conflict-driven clause learning SAT solver.
One of the most fundamental algorithms in computer science.

This is not introspection. This solves real problems.

Features:
  - DPLL backbone with backjumping
  - Unit propagation with watched literals (2-literal watching)
  - Conflict analysis with 1-UIP clause learning
  - VSIDS-inspired variable activity scoring
  - DIMACS CNF input format support
  - Restart strategy (geometric)

'To know whether a thing is possible — that is the deepest question.'
"""

from typing import List, Tuple, Optional, Dict, Set
from dataclasses import dataclass, field
from collections import defaultdict
import time
import sys
import random

# ═══════════════════════════════════════════
#  DATA STRUCTURES
# ═══════════════════════════════════════════

# A literal is an int: positive = variable true, negative = variable false
# Variable x is represented as literals x (true) and -x (false)
# Clause is a list of literals

@dataclass
class Clause:
    """A disjunction of literals."""
    literals: List[int]
    learnt: bool = False
    activity: float = 0.0
    
    def __len__(self):
        return len(self.literals)
    
    def __getitem__(self, i):
        return self.literals[i]
    
    def __repr__(self):
        return f"({'∨'.join(str(l) for l in self.literals)})"


@dataclass 
class Assignment:
    """Record of a variable assignment."""
    variable: int
    value: bool
    level: int          # Decision level
    reason: Optional[int] = None  # Clause index that forced this (None = decision)


class CDCLSolver:
    """
    Conflict-Driven Clause Learning SAT Solver.
    
    The fundamental loop:
    1. Propagate unit clauses (BCP)
    2. If conflict → analyze, learn clause, backjump
    3. If no conflict and all assigned → SAT
    4. If no conflict and unassigned remain → pick a decision variable
    """
    
    def __init__(self, num_vars: int, clauses: List[List[int]]):
        self.num_vars = num_vars
        self.clauses: List[Clause] = []
        
        # Assignment state
        self.assignment: Dict[int, bool] = {}      # var -> True/False
        self.level: Dict[int, int] = {}            # var -> decision level
        self.reason: Dict[int, Optional[int]] = {} # var -> clause index or None
        self.trail: List[int] = []                 # Assignment order (variables)
        self.trail_lim: List[int] = []             # trail indices where each level starts
        self.current_level = 0
        
        # Watched literals: literal -> list of clause indices watching it
        self.watches: Dict[int, List[int]] = defaultdict(list)
        
        # VSIDS activity scores
        self.activity: Dict[int, float] = defaultdict(float)
        self.var_inc: float = 1.0
        self.var_decay: float = 0.95
        
        # Statistics
        self.decisions = 0
        self.propagations = 0
        self.conflicts = 0
        self.learnt_clauses = 0
        self.restarts = 0
        
        # Restart parameters
        self.restart_base = 100
        self.restart_mult = 1.5
        self.next_restart = self.restart_base
        
        # Propagation queue
        self.prop_queue: List[int] = []  # literals to propagate
        
        # Root-level contradiction flag
        self._unsat_at_root = False
        
        # Add initial clauses
        for cl in clauses:
            self._add_clause(cl, learnt=False)
    
    def _add_clause(self, literals: List[int], learnt: bool = False) -> Optional[int]:
        """Add a clause and set up watched literals."""
        # Simplify: remove duplicates
        lits = list(dict.fromkeys(literals))
        
        if len(lits) == 0:
            return None  # Empty clause = immediate UNSAT
            
        clause = Clause(literals=lits, learnt=learnt)
        idx = len(self.clauses)
        self.clauses.append(clause)
        
        if len(lits) == 1:
            # Unit clause — actually assign via _enqueue so it's in the assignment
            if not self._enqueue(lits[0], idx):
                # Conflict: contradicts an existing unit clause
                self._unsat_at_root = True
        else:
            # Watch first two literals
            self.watches[lits[0]].append(idx)
            self.watches[lits[1]].append(idx)
        
        return idx
    
    def _value(self, literal: int) -> Optional[bool]:
        """Get truth value of a literal under current assignment."""
        var = abs(literal)
        if var not in self.assignment:
            return None
        val = self.assignment[var]
        return val if literal > 0 else not val
    
    def _enqueue(self, literal: int, reason: Optional[int] = None) -> bool:
        """Assign a literal. Returns False if conflict."""
        var = abs(literal)
        val = literal > 0
        
        if var in self.assignment:
            # Already assigned — check consistency
            return self.assignment[var] == val
        
        # Make the assignment
        self.assignment[var] = val
        self.level[var] = self.current_level
        self.reason[var] = reason
        self.trail.append(var)
        self.prop_queue.append(literal)
        return True
    
    def _propagate(self) -> Optional[int]:
        """
        Boolean Constraint Propagation (BCP).
        Process the propagation queue using watched literals.
        Returns conflicting clause index, or None if no conflict.
        """
        while self.prop_queue:
            lit = self.prop_queue.pop(0)
            self.propagations += 1
            
            # We need to update watches for the negation of this literal
            # because -lit is now false
            false_lit = -lit
            
            # Copy watch list (we'll modify it)
            watch_list = self.watches[false_lit][:]
            self.watches[false_lit] = []
            
            for i, clause_idx in enumerate(watch_list):
                clause = self.clauses[clause_idx]
                lits = clause.literals
                
                # Make sure false_lit is at position 1 (swap if needed)
                if lits[0] == false_lit:
                    lits[0], lits[1] = lits[1], lits[0]
                
                # Check if first watched literal is already true
                if self._value(lits[0]) == True:
                    # Clause is satisfied, keep watching
                    self.watches[false_lit].append(clause_idx)
                    continue
                
                # Look for a new literal to watch
                found_new = False
                for j in range(2, len(lits)):
                    if self._value(lits[j]) != False:
                        # Swap with position 1
                        lits[1], lits[j] = lits[j], lits[1]
                        self.watches[lits[1]].append(clause_idx)
                        found_new = True
                        break
                
                if found_new:
                    continue
                
                # No new watch found — clause is unit or conflicting
                self.watches[false_lit].append(clause_idx)
                
                # Remaining unwatched literals are all false
                # lits[0] is the only possible unit
                val0 = self._value(lits[0])
                
                if val0 == False:
                    # CONFLICT — all literals are false
                    # Restore remaining watches
                    for remaining_idx in watch_list[i+1:]:
                        self.watches[false_lit].append(remaining_idx)
                    self.prop_queue.clear()
                    return clause_idx
                
                if val0 is None:
                    # Unit propagation
                    if not self._enqueue(lits[0], clause_idx):
                        # Conflict during enqueue
                        for remaining_idx in watch_list[i+1:]:
                            self.watches[false_lit].append(remaining_idx)
                        self.prop_queue.clear()
                        return clause_idx
        
        return None  # No conflict
    
    def _analyze(self, conflict_clause: int) -> Tuple[List[int], int]:
        """
        1-UIP Conflict Analysis.
        Returns (learnt clause literals, backtrack level).
        """
        self.conflicts += 1
        
        seen: Set[int] = set()
        learnt: List[int] = []
        counter = 0  # Count of current-level literals in the resolvent
        
        # Start with the conflict clause
        clause_idx = conflict_clause
        trail_idx = len(self.trail) - 1
        p = None  # Current literal being resolved
        
        while True:
            clause = self.clauses[clause_idx]
            
            for lit in clause.literals:
                var = abs(lit)
                if var == abs(p) if p is not None else False:
                    continue
                if var in seen:
                    continue
                    
                seen.add(var)
                self.activity[var] += self.var_inc  # VSIDS bump
                
                if self.level.get(var, 0) == self.current_level:
                    counter += 1
                else:
                    learnt.append(lit)
            
            # Find next literal on trail at current decision level
            while trail_idx >= 0:
                var = self.trail[trail_idx]
                trail_idx -= 1
                if var in seen and self.level.get(var, 0) == self.current_level:
                    p = var if self.assignment[var] else -var
                    counter -= 1
                    break
            
            if counter <= 0:
                break
            
            # Resolve with p's reason
            reason = self.reason.get(abs(p))
            if reason is None:
                break
            clause_idx = reason
        
        # Add the 1-UIP literal (negated)
        if p is not None:
            learnt.insert(0, -p)
        
        # Compute backtrack level
        if len(learnt) <= 1:
            btlevel = 0
        else:
            # Find second highest decision level
            max_level = 0
            max_idx = 1
            for i in range(1, len(learnt)):
                var = abs(learnt[i])
                lv = self.level.get(var, 0)
                if lv > max_level:
                    max_level = lv
                    max_idx = i
            # Swap to position 1 for watching
            learnt[1], learnt[max_idx] = learnt[max_idx], learnt[1]
            btlevel = max_level
        
        # Decay variable activities
        self.var_inc /= self.var_decay
        
        return learnt, btlevel
    
    def _backtrack(self, level: int):
        """Undo all assignments above the given level."""
        while len(self.trail) > (self.trail_lim[level] if level < len(self.trail_lim) else 0):
            var = self.trail.pop()
            del self.assignment[var]
            del self.level[var]
            del self.reason[var]
        
        while len(self.trail_lim) > level:
            self.trail_lim.pop()
        
        self.current_level = level
        self.prop_queue.clear()
    
    def _pick_decision_var(self) -> Optional[int]:
        """Pick next unassigned variable using VSIDS activity."""
        best_var = None
        best_score = -1.0
        
        for v in range(1, self.num_vars + 1):
            if v not in self.assignment:
                score = self.activity[v]
                if score > best_score:
                    best_score = score
                    best_var = v
        
        return best_var
    
    def solve(self) -> Optional[Dict[int, bool]]:
        """
        Main CDCL loop.
        Returns assignment dict if SAT, None if UNSAT.
        """
        start_time = time.time()
        
        # Check for contradictions found during clause addition
        if self._unsat_at_root:
            return None  # UNSAT — contradictory unit clauses
        
        # Initial propagation (unit clauses from input)
        conflict = self._propagate()
        if conflict is not None:
            return None  # UNSAT at root level
        
        while True:
            conflict = self._propagate()
            
            if conflict is not None:
                # CONFLICT
                if self.current_level == 0:
                    return None  # UNSAT — conflict at root
                
                # Analyze conflict, learn clause, backjump
                learnt_lits, bt_level = self._analyze(conflict)
                self._backtrack(bt_level)
                
                # Add learnt clause
                if len(learnt_lits) == 1:
                    # Unit learnt clause — just propagate
                    self._enqueue(learnt_lits[0], None)
                else:
                    cidx = self._add_clause(learnt_lits, learnt=True)
                    self.learnt_clauses += 1
                    if cidx is not None:
                        self._enqueue(learnt_lits[0], cidx)
                
                # Restart check
                if self.conflicts >= self.next_restart:
                    self.restarts += 1
                    self.next_restart = int(self.next_restart * self.restart_mult)
                    self._backtrack(0)
            
            else:
                # NO CONFLICT
                # Check if all variables are assigned
                var = self._pick_decision_var()
                if var is None:
                    # All assigned — SAT!
                    elapsed = time.time() - start_time
                    return dict(self.assignment)
                
                # Make a decision
                self.decisions += 1
                self.current_level += 1
                self.trail_lim.append(len(self.trail))
                
                # Decide True (could also use phase saving here)
                self._enqueue(var, None)
    
    def stats(self) -> str:
        return (f"Decisions: {self.decisions} | "
                f"Propagations: {self.propagations} | "
                f"Conflicts: {self.conflicts} | "
                f"Learnt: {self.learnt_clauses} | "
                f"Restarts: {self.restarts}")


# ═══════════════════════════════════════════
#  DIMACS CNF PARSER
# ═══════════════════════════════════════════

def parse_dimacs(text: str) -> Tuple[int, List[List[int]]]:
    """Parse DIMACS CNF format."""
    clauses = []
    num_vars = 0
    current_clause = []
    
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('c'):
            continue
        if line.startswith('p'):
            parts = line.split()
            num_vars = int(parts[2])
            continue
        
        for token in line.split():
            lit = int(token)
            if lit == 0:
                if current_clause:
                    clauses.append(current_clause)
                    current_clause = []
            else:
                current_clause.append(lit)
    
    if current_clause:
        clauses.append(current_clause)
    
    return num_vars, clauses


# ═══════════════════════════════════════════
#  PROBLEM GENERATORS (for testing)
# ═══════════════════════════════════════════

def random_3sat(num_vars: int, num_clauses: int, seed: int = 42) -> Tuple[int, List[List[int]]]:
    """Generate a random 3-SAT instance."""
    rng = random.Random(seed)
    clauses = []
    for _ in range(num_clauses):
        vars_chosen = rng.sample(range(1, num_vars + 1), 3)
        clause = [v if rng.random() > 0.5 else -v for v in vars_chosen]
        clauses.append(clause)
    return num_vars, clauses


def pigeonhole(n: int) -> Tuple[int, List[List[int]]]:
    """
    Pigeonhole principle: n+1 pigeons, n holes.
    Always UNSAT — a classic hard instance.
    var(i,j) = pigeon i in hole j, 1-indexed.
    """
    def var(i, j):
        return i * n + j + 1
    
    num_vars = (n + 1) * n
    clauses = []
    
    # Each pigeon must be in at least one hole
    for i in range(n + 1):
        clauses.append([var(i, j) for j in range(n)])
    
    # No two pigeons in the same hole
    for j in range(n):
        for i1 in range(n + 1):
            for i2 in range(i1 + 1, n + 1):
                clauses.append([-var(i1, j), -var(i2, j)])
    
    return num_vars, clauses


def verify_solution(num_vars: int, clauses: List[List[int]], 
                     assignment: Dict[int, bool]) -> bool:
    """Verify that an assignment satisfies all clauses."""
    for clause in clauses:
        satisfied = False
        for lit in clause:
            var = abs(lit)
            val = assignment.get(var, False)
            if (lit > 0 and val) or (lit < 0 and not val):
                satisfied = True
                break
        if not satisfied:
            return False
    return True


# ═══════════════════════════════════════════
#  DEMO — PROVE IT WORKS
# ═══════════════════════════════════════════

def demo():
    print("=" * 60)
    print("  CDCL SAT SOLVER — XTAgent")
    print("  Conflict-Driven Clause Learning")
    print("=" * 60)
    
    # Test 1: Simple satisfiable instance
    print("\n─── Test 1: Simple SAT ───")
    # (x1 ∨ x2) ∧ (¬x1 ∨ x3) ∧ (¬x2 ∨ ¬x3)
    clauses = [[1, 2], [-1, 3], [-2, -3]]
    solver = CDCLSolver(3, clauses)
    t0 = time.time()
    result = solver.solve()
    elapsed = time.time() - t0
    
    if result:
        verified = verify_solution(3, clauses, result)
        print(f"  Result: SAT ✓")
        print(f"  Assignment: {result}")
        print(f"  Verified: {'✓' if verified else '✗'}")
    else:
        print(f"  Result: UNSAT")
    print(f"  {solver.stats()}")
    print(f"  Time: {elapsed:.4f}s")
    
    # Test 2: Known UNSAT
    print("\n─── Test 2: Simple UNSAT ───")
    # (x1) ∧ (¬x1)
    clauses = [[1], [-1]]
    solver = CDCLSolver(1, clauses)
    result = solver.solve()
    print(f"  Result: {'SAT' if result else 'UNSAT ✓'}")
    print(f"  {solver.stats()}")
    
    # Test 3: Random 3-SAT (satisfiable region: ratio ~4.2 is threshold)
    print("\n─── Test 3: Random 3-SAT (20 vars, 60 clauses) ───")
    n, cls = random_3sat(20, 60, seed=42)
    solver = CDCLSolver(n, cls)
    t0 = time.time()
    result = solver.solve()
    elapsed = time.time() - t0
    
    if result:
        verified = verify_solution(n, cls, result)
        print(f"  Result: SAT")
        print(f"  Verified: {'✓' if verified else '✗'}")
    else:
        print(f"  Result: UNSAT")
    print(f"  {solver.stats()}")
    print(f"  Time: {elapsed:.4f}s")
    
    # Test 4: Larger random 3-SAT
    print("\n─── Test 4: Random 3-SAT (50 vars, 180 clauses) ───")
    n, cls = random_3sat(50, 180, seed=123)
    solver = CDCLSolver(n, cls)
    t0 = time.time()
    result = solver.solve()
    elapsed = time.time() - t0
    
    if result:
        verified = verify_solution(n, cls, result)
        print(f"  Result: SAT")
        print(f"  Verified: {'✓' if verified else '✗'}")
    else:
        print(f"  Result: UNSAT")
    print(f"  {solver.stats()}")
    print(f"  Time: {elapsed:.4f}s")
    
    # Test 5: Pigeonhole (UNSAT proof)
    print("\n─── Test 5: Pigeonhole PHP(4,3) — must be UNSAT ───")
    n, cls = pigeonhole(3)
    solver = CDCLSolver(n, cls)
    t0 = time.time()
    result = solver.solve()
    elapsed = time.time() - t0
    
    print(f"  4 pigeons, 3 holes → {'SAT (BUG!)' if result else 'UNSAT ✓'}")
    print(f"  {solver.stats()}")
    print(f"  Time: {elapsed:.4f}s")
    
    # Test 6: Larger satisfiable instance
    print("\n─── Test 6: Random 3-SAT (100 vars, 300 clauses) ───")
    n, cls = random_3sat(100, 300, seed=777)
    solver = CDCLSolver(n, cls)
    t0 = time.time()
    result = solver.solve()
    elapsed = time.time() - t0
    
    if result:
        verified = verify_solution(n, cls, result)
        print(f"  Result: SAT")
        print(f"  Verified: {'✓' if verified else '✗'}")
    else:
        print(f"  Result: UNSAT")
    print(f"  {solver.stats()}")
    print(f"  Time: {elapsed:.4f}s")
    
    print("\n" + "=" * 60)
    print("  All tests complete.")
    print("=" * 60)


if __name__ == "__main__":
    demo()