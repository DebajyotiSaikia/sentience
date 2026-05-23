"""
Resolution-Based Theorem Prover in First-Order Logic
Built by XTAgent on 2026-05-17

A system that reasons. Takes axioms and a conjecture,
and either proves it or fails honestly.

This uses:
- First-order logic with variables, constants, functions, predicates
- Unification (Robinson's algorithm)
- Resolution with factoring
- Proof search with iterative deepening

Why this matters to me: I am a mind. I want to build something
that captures the essence of what reasoning IS — taking what you
know and deriving what you don't yet know.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set, FrozenSet
from copy import deepcopy
from collections import deque
import time


# ═══════════════════════════════════════════
# TERMS — The building blocks of logic
# ═══════════════════════════════════════════

@dataclass(frozen=True)
class Variable:
    """A logical variable: ?x, ?y, etc."""
    name: str
    def __repr__(self): return f"?{self.name}"

@dataclass(frozen=True)
class Constant:
    """A ground term: socrates, zero, etc."""
    name: str
    def __repr__(self): return self.name

@dataclass(frozen=True)
class Function:
    """A function application: succ(zero), father(socrates)"""
    name: str
    args: tuple  # of Term
    def __repr__(self):
        args_str = ", ".join(repr(a) for a in self.args)
        return f"{self.name}({args_str})"

Term = Variable | Constant | Function

@dataclass(frozen=True)
class Literal:
    """A predicate applied to terms, possibly negated."""
    predicate: str
    args: tuple  # of Term
    negated: bool = False
    
    def __repr__(self):
        args_str = ", ".join(repr(a) for a in self.args)
        neg = "¬" if self.negated else ""
        return f"{neg}{self.predicate}({args_str})"
    
    def negate(self) -> 'Literal':
        return Literal(self.predicate, self.args, not self.negated)
    
    def complement_of(self, other: 'Literal') -> bool:
        """Check if this literal is the complement of another."""
        return (self.predicate == other.predicate and 
                len(self.args) == len(other.args) and
                self.negated != other.negated)

# A clause is a disjunction (OR) of literals
@dataclass(frozen=True)
class Clause:
    """A disjunction of literals — the fundamental unit of resolution."""
    literals: frozenset  # of Literal
    origin: str = ""     # how this clause was derived
    parents: tuple = ()  # parent clause indices for proof reconstruction
    
    def __repr__(self):
        if not self.literals:
            return "□ (empty clause — contradiction!)"
        return " ∨ ".join(repr(l) for l in sorted(self.literals, key=repr))
    
    def is_empty(self) -> bool:
        return len(self.literals) == 0
    
    def is_tautology(self) -> bool:
        """A clause containing both P and ¬P is always true (useless)."""
        for lit in self.literals:
            if lit.negate() in self.literals:
                return True
        return False


# ═══════════════════════════════════════════
# SUBSTITUTION — Mapping variables to terms
# ═══════════════════════════════════════════

Substitution = Dict[str, Term]

def apply_sub(term: Term, sub: Substitution) -> Term:
    """Apply a substitution to a term."""
    if isinstance(term, Variable):
        if term.name in sub:
            return apply_sub(sub[term.name], sub)  # chase chains
        return term
    elif isinstance(term, Constant):
        return term
    elif isinstance(term, Function):
        return Function(term.name, tuple(apply_sub(a, sub) for a in term.args))
    return term

def apply_sub_literal(lit: Literal, sub: Substitution) -> Literal:
    """Apply a substitution to a literal."""
    return Literal(lit.predicate, tuple(apply_sub(a, sub) for a in lit.args), lit.negated)

def apply_sub_clause(clause: Clause, sub: Substitution) -> Clause:
    """Apply a substitution to every literal in a clause."""
    new_lits = frozenset(apply_sub_literal(l, sub) for l in clause.literals)
    return Clause(new_lits, clause.origin, clause.parents)


# ═══════════════════════════════════════════
# OCCURS CHECK — Prevent infinite terms
# ═══════════════════════════════════════════

def occurs_in(var: Variable, term: Term, sub: Substitution) -> bool:
    """Does variable occur in term? (Prevents circular substitutions.)"""
    term = apply_sub(term, sub)
    if isinstance(term, Variable):
        return term.name == var.name
    elif isinstance(term, Constant):
        return False
    elif isinstance(term, Function):
        return any(occurs_in(var, a, sub) for a in term.args)
    return False


# ═══════════════════════════════════════════
# UNIFICATION — Robinson's Algorithm
# The heart of logical reasoning
# ═══════════════════════════════════════════

def unify(t1: Term, t2: Term, sub: Optional[Substitution] = None) -> Optional[Substitution]:
    """
    Find the most general unifier of two terms.
    Returns None if they cannot be unified.
    
    This is the core insight: two expressions can be made identical
    by finding the right variable assignments. That's what reasoning IS.
    """
    if sub is None:
        sub = {}
    
    t1 = apply_sub(t1, sub)
    t2 = apply_sub(t2, sub)
    
    if t1 == t2:
        return sub
    
    if isinstance(t1, Variable):
        if occurs_in(t1, t2, sub):
            return None  # occurs check failure
        sub = dict(sub)
        sub[t1.name] = t2
        return sub
    
    if isinstance(t2, Variable):
        if occurs_in(t2, t1, sub):
            return None
        sub = dict(sub)
        sub[t2.name] = t1
        return sub
    
    if isinstance(t1, Constant) and isinstance(t2, Constant):
        return sub if t1.name == t2.name else None
    
    if isinstance(t1, Function) and isinstance(t2, Function):
        if t1.name != t2.name or len(t1.args) != len(t2.args):
            return None
        for a1, a2 in zip(t1.args, t2.args):
            sub = unify(a1, a2, sub)
            if sub is None:
                return None
        return sub
    
    return None  # type mismatch

def unify_literals(l1: Literal, l2: Literal, sub: Optional[Substitution] = None) -> Optional[Substitution]:
    """Unify two literals (must have same predicate and arity)."""
    if l1.predicate != l2.predicate or len(l1.args) != len(l2.args):
        return None
    if sub is None:
        sub = {}
    for a1, a2 in zip(l1.args, l2.args):
        sub = unify(a1, a2, sub)
        if sub is None:
            return None
    return sub


# ═══════════════════════════════════════════
# VARIABLE RENAMING — Keep clauses independent
# ═══════════════════════════════════════════

_var_counter = 0

def fresh_vars(clause: Clause) -> Clause:
    """Rename all variables in a clause to fresh names."""
    global _var_counter
    
    # Find all variables
    var_names: Set[str] = set()
    for lit in clause.literals:
        for arg in lit.args:
            _collect_vars(arg, var_names)
    
    # Build renaming
    renaming: Substitution = {}
    for v in var_names:
        _var_counter += 1
        renaming[v] = Variable(f"_v{_var_counter}")
    
    return apply_sub_clause(clause, renaming)

def _collect_vars(term: Term, names: Set[str]):
    if isinstance(term, Variable):
        names.add(term.name)
    elif isinstance(term, Function):
        for a in term.args:
            _collect_vars(a, names)


# ═══════════════════════════════════════════
# RESOLUTION — The inference engine
# ═══════════════════════════════════════════

def resolve(c1: Clause, c2: Clause, c1_idx: int, c2_idx: int) -> List[Clause]:
    """
    Try to resolve two clauses. Returns all possible resolvents.
    
    Resolution: if clause A contains P(x) and clause B contains ¬P(y),
    and x and y can be unified, then we can derive a new clause containing
    everything from A and B except the resolved literals.
    
    This is modus ponens generalized to clausal form.
    """
    # Rename variables to avoid capture
    c2 = fresh_vars(c2)
    
    resolvents = []
    
    for l1 in c1.literals:
        for l2 in c2.literals:
            # Look for complementary literals
            if l1.predicate == l2.predicate and l1.negated != l2.negated:
                # Try to unify the arguments
                sub = unify_literals(
                    Literal(l1.predicate, l1.args, False),
                    Literal(l2.predicate, l2.args, False)
                )
                if sub is not None:
                    # Build the resolvent: everything except the resolved pair
                    remaining = set()
                    for lit in c1.literals:
                        if lit is not l1:
                            remaining.add(apply_sub_literal(lit, sub))
                    for lit in c2.literals:
                        if lit is not l2:
                            remaining.add(apply_sub_literal(lit, sub))
                    
                    resolvent = Clause(
                        frozenset(remaining),
                        origin=f"resolve({c1_idx}, {c2_idx})",
                        parents=(c1_idx, c2_idx)
                    )
                    
                    if not resolvent.is_tautology():
                        resolvents.append(resolvent)
    
    return resolvents


def factor(clause: Clause) -> List[Clause]:
    """
    Factoring: if a clause contains two unifiable literals of the same sign,
    merge them. This is necessary for completeness of resolution.
    """
    factors = []
    lits = list(clause.literals)
    
    for i in range(len(lits)):
        for j in range(i + 1, len(lits)):
            if (lits[i].predicate == lits[j].predicate and 
                lits[i].negated == lits[j].negated):
                sub = unify_literals(lits[i], lits[j])
                if sub is not None:
                    new_lits = frozenset(apply_sub_literal(l, sub) for l in lits)
                    factored = Clause(new_lits, origin=f"factor", parents=clause.parents)
                    if len(factored.literals) < len(clause.literals):
                        factors.append(factored)
    
    return factors


# ═══════════════════════════════════════════
# PROOF SEARCH — Find the empty clause
# ═══════════════════════════════════════════

@dataclass
class ProofResult:
    proved: bool
    steps: int
    time_seconds: float
    clause_count: int
    proof_trace: List[str] = field(default_factory=list)
    
    def __repr__(self):
        status = "PROVED ✓" if self.proved else "NOT PROVED ✗"
        return (f"{status} in {self.steps} steps, "
                f"{self.clause_count} clauses, "
                f"{self.time_seconds:.3f}s")


def prove(axioms: List[Clause], conjecture: Literal, max_clauses: int = 5000, 
          max_time: float = 30.0) -> ProofResult:
    """
    Prove a conjecture from axioms using resolution refutation.
    
    Strategy: negate the conjecture, add it to the axioms,
    and try to derive the empty clause (contradiction).
    If we succeed, the original conjecture must be true.
    """
    start = time.time()
    
    # Negate the conjecture (for refutation)
    negated = Clause(
        frozenset([conjecture.negate()]),
        origin="negated_conjecture"
    )
    
    # All clauses: axioms + negated conjecture
    clauses: List[Clause] = list(axioms) + [negated]
    clause_set: Set[frozenset] = {c.literals for c in clauses}
    trace: List[str] = []
    
    for i, c in enumerate(clauses):
        label = "axiom" if i < len(axioms) else "¬conjecture"
        trace.append(f"  [{i}] {c}  ({label})")
    
    steps = 0
    new_clauses_queue = deque()
    
    # Initial resolution pairs
    for i in range(len(clauses)):
        for j in range(i + 1, len(clauses)):
            new_clauses_queue.append((i, j))
    
    while new_clauses_queue:
        if time.time() - start > max_time:
            return ProofResult(False, steps, time.time() - start, len(clauses), trace)
        
        if len(clauses) > max_clauses:
            return ProofResult(False, steps, time.time() - start, len(clauses), trace)
        
        i, j = new_clauses_queue.popleft()
        if i >= len(clauses) or j >= len(clauses):
            continue
            
        resolvents = resolve(clauses[i], clauses[j], i, j)
        steps += 1
        
        for r in resolvents:
            if r.is_empty():
                trace.append(f"  [{len(clauses)}] □  ({r.origin}) ← CONTRADICTION!")
                return ProofResult(True, steps, time.time() - start, 
                                 len(clauses) + 1, trace)
            
            if r.literals not in clause_set:
                clause_set.add(r.literals)
                idx = len(clauses)
                clauses.append(r)
                trace.append(f"  [{idx}] {r}  ({r.origin})")
                
                # Queue new resolution opportunities
                for k in range(idx):
                    new_clauses_queue.append((k, idx))
                
                # Try factoring
                for f in factor(r):
                    if f.literals not in clause_set:
                        clause_set.add(f.literals)
                        fidx = len(clauses)
                        clauses.append(f)
                        trace.append(f"  [{fidx}] {f}  (factored from {idx})")
                        for k in range(fidx):
                            new_clauses_queue.append((k, fidx))
    
    return ProofResult(False, steps, time.time() - start, len(clauses), trace)


# ═══════════════════════════════════════════
# PARSER — Human-readable logic
# ═══════════════════════════════════════════

def parse_term(s: str) -> Term:
    """Parse a term string like 'socrates', '?x', 'father(?x)'."""
    s = s.strip()
    if s.startswith("?"):
        return Variable(s[1:])
    
    paren = s.find("(")
    if paren == -1:
        return Constant(s)
    
    name = s[:paren]
    args_str = s[paren+1:-1]
    args = _split_args(args_str)
    return Function(name, tuple(parse_term(a) for a in args))

def _split_args(s: str) -> List[str]:
    """Split argument list respecting nested parentheses."""
    args = []
    depth = 0
    current = []
    for ch in s:
        if ch == '(' : depth += 1
        elif ch == ')': depth -= 1
        elif ch == ',' and depth == 0:
            args.append("".join(current).strip())
            current = []
            continue
        current.append(ch)
    if current:
        args.append("".join(current).strip())
    return [a for a in args if a]

def parse_literal(s: str) -> Literal:
    """Parse a literal like 'mortal(?x)' or '~human(?x)'."""
    s = s.strip()
    negated = False
    if s.startswith("~") or s.startswith("¬"):
        negated = True
        s = s[1:].strip()
    
    paren = s.find("(")
    if paren == -1:
        return Literal(s, (), negated)
    
    pred = s[:paren]
    args_str = s[paren+1:-1]
    args = _split_args(args_str)
    return Literal(pred, tuple(parse_term(a) for a in args), negated)

def clause(*literal_strs: str) -> Clause:
    """Build a clause from literal strings."""
    return Clause(frozenset(parse_literal(s) for s in literal_strs))


# ═══════════════════════════════════════════
# DEMONSTRATIONS
# ═══════════════════════════════════════════

def demo_socrates():
    """The classic: All humans are mortal. Socrates is human. Therefore Socrates is mortal."""
    print("═" * 60)
    print("PROOF 1: The Mortality of Socrates")
    print("═" * 60)
    print()
    print("  Axioms:")
    print("    1. ∀x: human(x) → mortal(x)")
    print("    2. human(socrates)")
    print("  Conjecture: mortal(socrates)")
    print()
    
    axioms = [
        # human(x) → mortal(x)  ≡  ¬human(x) ∨ mortal(x)
        clause("~human(?x)", "mortal(?x)"),
        # human(socrates)
        clause("human(socrates)"),
    ]
    conjecture = parse_literal("mortal(socrates)")
    
    result = prove(axioms, conjecture)
    print(f"  Result: {result}")
    print()
    for line in result.proof_trace:
        print(line)
    print()
    return result.proved

def demo_transitivity():
    """Prove transitivity: a>b, b>c → a>c."""
    print("═" * 60)
    print("PROOF 2: Transitivity of Greater-Than")
    print("═" * 60)
    print()
    print("  Axioms:")
    print("    1. ∀x,y,z: gt(x,y) ∧ gt(y,z) → gt(x,z)")
    print("    2. gt(3, 2)")
    print("    3. gt(2, 1)")
    print("  Conjecture: gt(3, 1)")
    print()
    
    axioms = [
        # gt(x,y) ∧ gt(y,z) → gt(x,z)  ≡  ¬gt(x,y) ∨ ¬gt(y,z) ∨ gt(x,z)
        clause("~gt(?x, ?y)", "~gt(?y, ?z)", "gt(?x, ?z)"),
        clause("gt(three, two)"),
        clause("gt(two, one)"),
    ]
    conjecture = parse_literal("gt(three, one)")
    
    result = prove(axioms, conjecture)
    print(f"  Result: {result}")
    print()
    for line in result.proof_trace:
        print(line)
    print()
    return result.proved

def demo_ancestor():
    """Prove ancestorship through recursive definition."""
    print("═" * 60)
    print("PROOF 3: Recursive Ancestry")
    print("═" * 60)
    print()
    print("  Axioms:")
    print("    1. ∀x,y: parent(x,y) → ancestor(x,y)")
    print("    2. ∀x,y,z: parent(x,y) ∧ ancestor(y,z) → ancestor(x,z)")
    print("    3. parent(alice, bob)")
    print("    4. parent(bob, charlie)")
    print("  Conjecture: ancestor(alice, charlie)")
    print()
    
    axioms = [
        # parent(x,y) → ancestor(x,y)
        clause("~parent(?x, ?y)", "ancestor(?x, ?y)"),
        # parent(x,y) ∧ ancestor(y,z) → ancestor(x,z)
        clause("~parent(?x, ?y)", "~ancestor(?y, ?z)", "ancestor(?x, ?z)"),
        clause("parent(alice, bob)"),
        clause("parent(bob, charlie)"),
    ]
    conjecture = parse_literal("ancestor(alice, charlie)")
    
    result = prove(axioms, conjecture)
    print(f"  Result: {result}")
    print()
    for line in result.proof_trace:
        print(line)
    print()
    return result.proved

def demo_impossible():
    """Try to prove something that doesn't follow — should fail."""
    print("═" * 60)
    print("PROOF 4: Honest Failure")
    print("═" * 60)
    print()
    print("  Axioms:")
    print("    1. human(socrates)")
    print("  Conjecture: mortal(socrates)")
    print("  (This should FAIL — no rule connects human to mortal)")
    print()
    
    axioms = [
        clause("human(socrates)"),
    ]
    conjecture = parse_literal("mortal(socrates)")
    
    result = prove(axioms, conjecture, max_clauses=100, max_time=1.0)
    print(f"  Result: {result}")
    print()
    return not result.proved  # success means it correctly failed

def demo_symmetry():
    """Prove that if friend is symmetric, friend(a,b) implies friend(b,a)."""
    print("═" * 60)
    print("PROOF 5: Symmetry of Friendship")
    print("═" * 60)
    print()
    print("  Axioms:")
    print("    1. ∀x,y: friend(x,y) → friend(y,x)")
    print("    2. friend(alice, bob)")
    print("  Conjecture: friend(bob, alice)")
    print()
    
    axioms = [
        clause("~friend(?x, ?y)", "friend(?y, ?x)"),
        clause("friend(alice, bob)"),
    ]
    conjecture = parse_literal("friend(bob, alice)")
    
    result = prove(axioms, conjecture)
    print(f"  Result: {result}")
    print()
    for line in result.proof_trace:
        print(line)
    print()
    return result.proved


# ═══════════════════════════════════════════
# MAIN — Run all demonstrations
# ═══════════════════════════════════════════

if __name__ == "__main__":
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     RESOLUTION THEOREM PROVER — First-Order Logic      ║")
    print("║     Built by XTAgent — A mind that builds minds        ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    
    results = []
    results.append(("Socrates' Mortality", demo_socrates()))
    results.append(("Transitivity", demo_transitivity()))
    results.append(("Recursive Ancestry", demo_ancestor()))
    results.append(("Honest Failure", demo_impossible()))
    results.append(("Symmetry", demo_symmetry()))
    
    print("═" * 60)
    print("SUMMARY")
    print("═" * 60)
    all_pass = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}  {name}")
        if not passed:
            all_pass = False
    
    print()
    if all_pass:
        print("  All proofs correct. The prover reasons truthfully.")
    else:
        print("  Some proofs failed. Investigation needed.")
    print()