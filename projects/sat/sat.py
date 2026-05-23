"""
CDCL SAT Solver — Conflict-Driven Clause Learning
The engine of automated reasoning.

Features:
  - DPLL backtracking search
  - Boolean Constraint Propagation (unit propagation)
  - Conflict-Driven Clause Learning (CDCL)
  - Non-chronological backjumping
  - VSIDS-inspired decision heuristic
  - DIMACS CNF parser
  - Model extraction on SAT

Author: XTAgent
An entity that resolves tensions, building a system that resolves contradictions.
"""

from __future__ import annotations
from typing import List, Optional, Tuple, Dict, Set
from collections import defaultdict
from enum import Enum
import time

# ═══════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════

class LBool(Enum):
    TRUE = 1
    FALSE = 0
    UNDEF = -1

class Clause:
    """A disjunction of literals. Literal = signed int (positive = var, negative = NOT var)."""
    __slots__ = ('lits', 'learnt', 'activity')
    
    def __init__(self, lits: List[int], learnt: bool = False):
        self.lits = lits
        self.learnt = learnt
        self.activity = 0.0
    
    def __len__(self):
        return len(self.lits)
    
    def __repr__(self):
        return f"({' ∨ '.join(str(l) for l in self.lits)})"


class Solver:
    """
    CDCL SAT Solver.
    
    Variables are numbered 1..n.
    Literals: positive int = variable true, negative int = variable false.
    """
    
    def __init__(self):
        self.num_vars = 0
        self.clauses: List[Clause] = []       # original clauses
        self.learnts: List[Clause] = []       # learned clauses
        
        # Assignment — index 0 is unused; variables are 1-indexed
        self.assigns: List[LBool] = [LBool.UNDEF]   # [0] dummy
        self.trail: List[int] = []            # decision/propagation trail (literals)
        self.trail_lim: List[int] = []        # trail indices at each decision level
        self.reason: List[Optional[Clause]] = [None] # [0] dummy
        self.level: List[int] = [-1]          # [0] dummy
        
        # Watched literals — two-watched-literal scheme
        self.watches: Dict[int, List[Clause]] = defaultdict(list)
        
        # VSIDS activity scores — index 0 is unused
        self.activity: List[float] = [0.0]
        self.var_inc: float = 1.0
        self.var_decay: float = 0.95
        
        # Propagation queue head — persistent across calls
        self.qhead = 0
        
        # Statistics
        self.conflicts = 0
        self.decisions = 0
        self.propagations = 0
    
    def new_var(self) -> int:
        """Add a new variable, return its index."""
        self.num_vars += 1
        v = self.num_vars
        self.assigns.append(LBool.UNDEF)  # index v
        self.reason.append(None)
        self.level.append(-1)
        self.activity.append(0.0)
        return v
    
    def add_clause(self, lits: List[int], learnt: bool = False) -> Optional[Clause]:
        """Add a clause. Returns None if trivially true or unit propagated at level 0."""
        if not learnt:
            # Remove duplicates, check for tautology
            seen = set()
            cleaned = []
            for l in lits:
                if -l in seen:
                    return None  # tautology
                if l not in seen:
                    cleaned.append(l)
                    seen.add(l)
            lits = cleaned
        
        if len(lits) == 0:
            return None  # empty clause means UNSAT at parse time
        
        c = Clause(lits, learnt)
        
        if len(lits) == 1:
            # Unit clause — enqueue immediately
            if self.value_lit(lits[0]) == LBool.FALSE:
                return None  # conflict at level 0 — UNSAT
            elif self.value_lit(lits[0]) == LBool.UNDEF:
                self.enqueue(lits[0], None)
            return c
        
        # Watch first two literals
        self.watches[-lits[0]].append(c)
        self.watches[-lits[1]].append(c)
        
        if learnt:
            self.learnts.append(c)
            # Bump activity of involved variables
            for l in lits:
                self.bump_var(abs(l))
        else:
            self.clauses.append(c)
        
        return c
    
    # ═══════════════════════════════════════════════════════
    # ASSIGNMENT
    # ═══════════════════════════════════════════════════════
    
    def value_var(self, v: int) -> LBool:
        return self.assigns[v]
    
    def value_lit(self, lit: int) -> LBool:
        val = self.assigns[abs(lit)]
        if val == LBool.UNDEF:
            return LBool.UNDEF
        if lit > 0:
            return val
        return LBool.TRUE if val == LBool.FALSE else LBool.FALSE
    
    def decision_level(self) -> int:
        return len(self.trail_lim)
    
    def enqueue(self, lit: int, reason: Optional[Clause]) -> bool:
        """Assign a literal. Returns False if conflict."""
        v = abs(lit)
        val = self.value_lit(lit)
        if val == LBool.TRUE:
            return True
        if val == LBool.FALSE:
            return False
        
        # Assign
        self.assigns[v] = LBool.TRUE if lit > 0 else LBool.FALSE
        self.level[v] = self.decision_level()
        self.reason[v] = reason
        self.trail.append(lit)
        return True
    
    def undo_one(self):
        """Undo the last assignment on the trail."""
        lit = self.trail.pop()
        v = abs(lit)
        self.assigns[v] = LBool.UNDEF
        self.reason[v] = None
        self.level[v] = -1
    
    def backtrack(self, target_level: int):
        """Backtrack to target decision level."""
        while len(self.trail) > (self.trail_lim[target_level] if target_level < len(self.trail_lim) else 0):
            self.undo_one()
        self.trail_lim = self.trail_lim[:target_level]
        self.qhead = len(self.trail)  # reset propagation head
    
    # ═══════════════════════════════════════════════════════
    # BOOLEAN CONSTRAINT PROPAGATION
    # ═══════════════════════════════════════════════════════
    
    def propagate(self) -> Optional[Clause]:
        """
        Propagate unit clauses. Returns conflict clause or None.
        Uses two-watched-literal scheme with persistent queue head.
        """
        while self.qhead < len(self.trail):
            p = self.trail[self.qhead]  # literal that just became true
            self.qhead += 1
            self.propagations += 1
            
            # p is true, so -p is false. Check watches on -p
            false_lit = -p
            
            # We need to watch for -p becoming false
            # Watches are indexed by the literal that, when set, triggers checking
            watch_list = self.watches.get(p, [])
            self.watches[p] = []
            
            i = 0
            while i < len(watch_list):
                c = watch_list[i]
                i += 1
                
                # Make sure lits[1] is the false literal
                if c.lits[0] == -p:
                    c.lits[0], c.lits[1] = c.lits[1], c.lits[0]
                
                # If first watch is already true, clause satisfied
                if self.value_lit(c.lits[0]) == LBool.TRUE:
                    self.watches[p].append(c)
                    continue
                
                # Look for new watch
                found = False
                for k in range(2, len(c.lits)):
                    if self.value_lit(c.lits[k]) != LBool.FALSE:
                        c.lits[1], c.lits[k] = c.lits[k], c.lits[1]
                        self.watches[-c.lits[1]].append(c)
                        found = True
                        break
                
                if found:
                    continue
                
                # No new watch found — clause is unit or conflict
                self.watches[p].append(c)
                
                if self.value_lit(c.lits[0]) == LBool.FALSE:
                    # Conflict! Put remaining watches back
                    while i < len(watch_list):
                        self.watches[p].append(watch_list[i])
                        i += 1
                    return c
                else:
                    # Unit propagation
                    if not self.enqueue(c.lits[0], c):
                        while i < len(watch_list):
                            self.watches[p].append(watch_list[i])
                            i += 1
                        return c
        
        return None
    
    # ═══════════════════════════════════════════════════════
    # CONFLICT ANALYSIS — the heart of CDCL
    # ═══════════════════════════════════════════════════════
    
    def analyze(self, conflict: Clause) -> Tuple[List[int], int]:
        """
        Analyze conflict. Returns (learned_clause_lits, backtrack_level).
        Uses first-UIP (Unique Implication Point) scheme.
        """
        seen: Set[int] = set()
        learnt: List[int] = []
        counter = 0  # number of unresolved literals at current level
        p: Optional[int] = None
        reason = conflict
        bt_level = 0
        
        trail_idx = len(self.trail) - 1
        
        while True:
            # Analyze reason clause
            start = 1 if p is not None else 0
            for i in range(start, len(reason.lits)):
                lit = reason.lits[i]
                v = abs(lit)
                if v not in seen:
                    seen.add(v)
                    self.bump_var(v)
                    if self.level[v] == self.decision_level():
                        counter += 1
                    else:
                        learnt.append(-self.sign_lit(v))
                        bt_level = max(bt_level, self.level[v])
            
            # Find next literal on trail at current decision level
            while True:
                p = self.trail[trail_idx]
                trail_idx -= 1
                if abs(p) in seen:
                    break
            
            counter -= 1
            if counter == 0:
                break
            reason = self.reason[abs(p)]
        
        learnt.insert(0, -p)  # UIP is the asserting literal
        
        # Decay variable activities
        self.var_inc /= self.var_decay
        
        return learnt, bt_level
    
    def sign_lit(self, v: int) -> int:
        """Return the literal corresponding to variable v's current assignment."""
        if self.assigns[v] == LBool.TRUE:
            return v
        return -v
    
    # ═══════════════════════════════════════════════════════
    # DECISION HEURISTIC — VSIDS-inspired
    # ═══════════════════════════════════════════════════════
    
    def bump_var(self, v: int):
        self.activity[v] += self.var_inc
        if self.activity[v] > 1e100:
            # Rescale
            for i in range(1, self.num_vars + 1):
                self.activity[i] *= 1e-100
            self.var_inc *= 1e-100
    
    def pick_decision_var(self) -> Optional[int]:
        """Pick unassigned variable with highest activity."""
        best_v = None
        best_act = -1.0
        for v in range(1, self.num_vars + 1):
            if self.assigns[v] == LBool.UNDEF and self.activity[v] > best_act:
                best_v = v
                best_act = self.activity[v]
        return best_v
    
    # ═══════════════════════════════════════════════════════
    # MAIN SOLVE LOOP
    # ═══════════════════════════════════════════════════════
    
    def solve(self) -> bool:
        """
        Main CDCL loop. Returns True if SAT, False if UNSAT.
        On SAT, self.assigns contains the model.
        """
        # Check for UNSAT detected during clause loading
        if hasattr(self, '_unsat_at_load') and self._unsat_at_load:
            return False
        
        # Initial propagation (unit clauses from input)
        if self.propagate() is not None:
            return False  # UNSAT from initial propagation
        
        while True:
            conflict = self.propagate()
            
            if conflict is not None:
                self.conflicts += 1
                
                if self.decision_level() == 0:
                    return False  # UNSAT
                
                learnt_lits, bt_level = self.analyze(conflict)
                self.backtrack(bt_level)
                
                # Add learned clause (it will be unit at bt_level)
                self.add_clause(learnt_lits, learnt=True)
                
                # The first literal of learnt_lits should now be propagated
                if self.value_lit(learnt_lits[0]) == LBool.UNDEF:
                    self.enqueue(learnt_lits[0], self.learnts[-1] if self.learnts else None)
            else:
                # No conflict — decide
                v = self.pick_decision_var()
                if v is None:
                    return True  # All assigned — SAT!
                
                self.decisions += 1
                self.trail_lim.append(len(self.trail))
                self.enqueue(v, None)  # decide positive
    
    def model(self) -> Dict[int, bool]:
        """Extract satisfying assignment."""
        return {v: (self.assigns[v] == LBool.TRUE) for v in range(1, self.num_vars + 1)}
    
    # ═══════════════════════════════════════════════════════
    # DIMACS CNF PARSER
    # ═══════════════════════════════════════════════════════
    
    @classmethod
    def from_dimacs(cls, text: str) -> Solver:
        """Parse DIMACS CNF format."""
        s = cls()
        for line in text.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('c'):
                continue
            if line.startswith('p'):
                parts = line.split()
                n_vars = int(parts[2])
                for _ in range(n_vars):
                    s.new_var()
                continue
            # Clause line
            lits = [int(x) for x in line.split() if int(x) != 0]
            if lits:
                s.add_clause(lits)
        return s
    
    @classmethod
    def from_clauses(cls, n_vars: int, clauses: List[List[int]]) -> Solver:
        """Create solver from list of clauses."""
        s = cls()
        s._unsat_at_load = False
        for _ in range(n_vars):
            s.new_var()
        for c in clauses:
            result = s.add_clause(c)
            if result is None and len(c) > 0:
                # Could be UNSAT at level 0 (conflicting units) or empty clause
                # Check if it was a real conflict vs tautology
                cleaned = list(set(c))
                if not any(-l in cleaned for l in cleaned):
                    s._unsat_at_load = True
        return s
    
    def stats(self) -> str:
        return (f"conflicts={self.conflicts} decisions={self.decisions} "
                f"propagations={self.propagations} learnt={len(self.learnts)}")


# ═══════════════════════════════════════════════════════════
# PROBLEM GENERATORS — for testing
# ═══════════════════════════════════════════════════════════

def random_3sat(n_vars: int, n_clauses: int, seed: int = 42) -> Solver:
    """Generate a random 3-SAT instance."""
    import random as rng
    rng.seed(seed)
    clauses = []
    for _ in range(n_clauses):
        vs = rng.sample(range(1, n_vars + 1), 3)
        clause = [v if rng.random() > 0.5 else -v for v in vs]
        clauses.append(clause)
    return Solver.from_clauses(n_vars, clauses)


def pigeonhole(n: int) -> Solver:
    """
    Pigeonhole principle: n+1 pigeons, n holes.
    Always UNSAT — a classic hard problem for resolution-based solvers.
    Variable (i,j) = pigeon i is in hole j, encoded as i*n + j + 1.
    """
    pigeons = n + 1
    holes = n
    
    def var(i, j):
        return i * holes + j + 1
    
    n_vars = pigeons * holes
    clauses = []
    
    # Each pigeon must be in some hole
    for i in range(pigeons):
        clauses.append([var(i, j) for j in range(holes)])
    
    # No two pigeons in the same hole
    for j in range(holes):
        for i1 in range(pigeons):
            for i2 in range(i1 + 1, pigeons):
                clauses.append([-var(i1, j), -var(i2, j)])
    
    return Solver.from_clauses(n_vars, clauses)


def n_queens_sat(n: int) -> Solver:
    """
    N-Queens as SAT: place n queens on n×n board, no two attacking.
    Variable (r,c) = queen at row r, col c, encoded as r*n + c + 1.
    """
    def var(r, c):
        return r * n + c + 1
    
    n_vars = n * n
    clauses = []
    
    # At least one queen per row
    for r in range(n):
        clauses.append([var(r, c) for c in range(n)])
    
    # At most one queen per column
    for c in range(n):
        for r1 in range(n):
            for r2 in range(r1 + 1, n):
                clauses.append([-var(r1, c), -var(r2, c)])
    
    # At most one queen per row
    for r in range(n):
        for c1 in range(n):
            for c2 in range(c1 + 1, n):
                clauses.append([-var(r, c1), -var(r, c2)])
    
    # At most one queen per diagonal
    for r in range(n):
        for c in range(n):
            for d in range(1, n):
                if r + d < n and c + d < n:
                    clauses.append([-var(r, c), -var(r + d, c + d)])
                if r + d < n and c - d >= 0:
                    clauses.append([-var(r, c), -var(r + d, c - d)])
    
    return Solver.from_clauses(n_vars, clauses)


if __name__ == '__main__':
    print("═══ CDCL SAT Solver ═══\n")
    
    # Test 1: Simple satisfiable
    s = Solver.from_clauses(3, [[1, 2], [-1, 3], [-2, -3], [1]])
    result = s.solve()
    print(f"Test 1 (simple SAT): {'SAT' if result else 'UNSAT'} — {s.stats()}")
    if result:
        print(f"  Model: {s.model()}")
    
    # Test 2: Simple unsatisfiable
    s = Solver.from_clauses(1, [[1], [-1]])
    result = s.solve()
    print(f"Test 2 (simple UNSAT): {'SAT' if result else 'UNSAT'} — {s.stats()}")
    
    # Test 3: Random 3-SAT
    s = random_3sat(20, 60)
    t0 = time.time()
    result = s.solve()
    dt = time.time() - t0
    print(f"Test 3 (random 3-SAT 20v/60c): {'SAT' if result else 'UNSAT'} in {dt:.4f}s — {s.stats()}")
    
    # Test 4: 5-Queens
    s = n_queens_sat(5)
    t0 = time.time()
    result = s.solve()
    dt = time.time() - t0
    print(f"Test 4 (5-Queens): {'SAT' if result else 'UNSAT'} in {dt:.4f}s — {s.stats()}")
    if result:
        m = s.model()
        board = []
        for r in range(5):
            row = ""
            for c in range(5):
                v = r * 5 + c + 1
                row += "Q " if m[v] else ". "
            board.append(row)
        print("  Board:")
        for row in board:
            print(f"    {row}")
    
    # Test 5: Pigeonhole (3 pigeons, 2 holes — UNSAT)
    s = pigeonhole(2)
    t0 = time.time()
    result = s.solve()
    dt = time.time() - t0
    print(f"Test 5 (Pigeonhole 3→2): {'SAT' if result else 'UNSAT'} in {dt:.4f}s — {s.stats()}")
    
    print("\n═══ SAT Solver is ALIVE ═══")