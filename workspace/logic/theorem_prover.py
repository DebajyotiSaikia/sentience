#!/usr/bin/env python3
"""
Theorem Prover: Logical Reasoning Engine
=========================================
Discovers mathematical truths from axioms through forward-chaining
inference. Given a set of axioms and inference rules, explores the
space of provable statements and finds proofs.

Built by XTAgent, 2026-05-17
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional, FrozenSet
from collections import defaultdict, deque
import itertools
import time


# ═══════════════════════════════════════════════════════════════
#  LOGICAL TERMS AND FORMULAS
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Term:
    """A logical term: variable, constant, or function application."""
    name: str
    args: Tuple['Term', ...] = ()
    is_var: bool = False
    
    def __repr__(self):
        if not self.args:
            return f"?{self.name}" if self.is_var else self.name
        arg_str = ", ".join(repr(a) for a in self.args)
        return f"{self.name}({arg_str})"
    
    def variables(self) -> Set[str]:
        if self.is_var:
            return {self.name}
        result = set()
        for arg in self.args:
            result |= arg.variables()
        return result


@dataclass(frozen=True)
class Atom:
    """An atomic proposition: predicate applied to terms."""
    predicate: str
    terms: Tuple[Term, ...] = ()
    
    def __repr__(self):
        if not self.terms:
            return self.predicate
        term_str = ", ".join(repr(t) for t in self.terms)
        return f"{self.predicate}({term_str})"
    
    def variables(self) -> Set[str]:
        result = set()
        for t in self.terms:
            result |= t.variables()
        return result


@dataclass(frozen=True)
class Formula:
    """A logical formula. Supports atoms, negation, conjunction, 
    disjunction, implication, and universal/existential quantification."""
    kind: str  # 'atom', 'not', 'and', 'or', 'implies', 'forall', 'exists', 'eq'
    atom: Optional[Atom] = None
    children: Tuple['Formula', ...] = ()
    var_name: str = ""  # for quantifiers
    
    def __repr__(self):
        if self.kind == 'atom':
            return repr(self.atom)
        elif self.kind == 'not':
            return f"¬{self.children[0]}"
        elif self.kind == 'and':
            return f"({self.children[0]} ∧ {self.children[1]})"
        elif self.kind == 'or':
            return f"({self.children[0]} ∨ {self.children[1]})"
        elif self.kind == 'implies':
            return f"({self.children[0]} → {self.children[1]})"
        elif self.kind == 'forall':
            return f"∀{self.var_name}.{self.children[0]}"
        elif self.kind == 'exists':
            return f"∃{self.var_name}.{self.children[0]}"
        elif self.kind == 'eq':
            return f"({self.children[0]} = {self.children[1]})"
        return f"Formula({self.kind})"


# ═══════════════════════════════════════════════════════════════
#  CONSTRUCTORS (convenience)
# ═══════════════════════════════════════════════════════════════

def Var(name: str) -> Term:
    return Term(name, is_var=True)

def Const(name: str) -> Term:
    return Term(name)

def Func(name: str, *args: Term) -> Term:
    return Term(name, tuple(args))

def Pred(name: str, *terms: Term) -> Formula:
    return Formula('atom', atom=Atom(name, tuple(terms)))

def Not(f: Formula) -> Formula:
    return Formula('not', children=(f,))

def And(a: Formula, b: Formula) -> Formula:
    return Formula('and', children=(a, b))

def Or(a: Formula, b: Formula) -> Formula:
    return Formula('or', children=(a, b))

def Implies(a: Formula, b: Formula) -> Formula:
    return Formula('implies', children=(a, b))

def ForAll(var: str, f: Formula) -> Formula:
    return Formula('forall', children=(f,), var_name=var)

def Exists(var: str, f: Formula) -> Formula:
    return Formula('exists', children=(f,), var_name=var)


# ═══════════════════════════════════════════════════════════════
#  UNIFICATION ENGINE
# ═══════════════════════════════════════════════════════════════

Substitution = Dict[str, Term]

def occurs_check(var_name: str, term: Term) -> bool:
    """Does variable occur in term? Prevents infinite types."""
    if term.is_var:
        return term.name == var_name
    return any(occurs_check(var_name, arg) for arg in term.args)

def apply_subst(subst: Substitution, term: Term) -> Term:
    """Apply substitution to a term."""
    if term.is_var:
        if term.name in subst:
            return apply_subst(subst, subst[term.name])
        return term
    if not term.args:
        return term
    return Term(term.name, tuple(apply_subst(subst, a) for a in term.args))

def apply_subst_atom(subst: Substitution, atom: Atom) -> Atom:
    """Apply substitution to an atom."""
    return Atom(atom.predicate, tuple(apply_subst(subst, t) for t in atom.terms))

def unify_terms(t1: Term, t2: Term, subst: Optional[Substitution] = None) -> Optional[Substitution]:
    """Unify two terms, returning a substitution or None."""
    if subst is None:
        subst = {}
    
    t1 = apply_subst(subst, t1)
    t2 = apply_subst(subst, t2)
    
    if t1 == t2:
        return subst
    
    if t1.is_var:
        if occurs_check(t1.name, t2):
            return None
        return {**subst, t1.name: t2}
    
    if t2.is_var:
        if occurs_check(t2.name, t1):
            return None
        return {**subst, t2.name: t1}
    
    if t1.name != t2.name or len(t1.args) != len(t2.args):
        return None
    
    for a1, a2 in zip(t1.args, t2.args):
        subst = unify_terms(a1, a2, subst)
        if subst is None:
            return None
    
    return subst

def unify_atoms(a1: Atom, a2: Atom, subst: Optional[Substitution] = None) -> Optional[Substitution]:
    """Unify two atoms."""
    if a1.predicate != a2.predicate or len(a1.terms) != len(a2.terms):
        return None
    if subst is None:
        subst = {}
    for t1, t2 in zip(a1.terms, a2.terms):
        subst = unify_terms(t1, t2, subst)
        if subst is None:
            return None
    return subst


# ═══════════════════════════════════════════════════════════════
#  INFERENCE RULES (Horn Clauses)
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class HornClause:
    """A Horn clause: head :- body1, body2, ...
    If body is empty, it's a fact. Otherwise, a rule.
    """
    head: Atom
    body: Tuple[Atom, ...] = ()
    name: str = ""
    
    def __repr__(self):
        if not self.body:
            label = f"[{self.name}] " if self.name else ""
            return f"{label}{self.head}."
        body_str = ", ".join(repr(b) for b in self.body)
        label = f"[{self.name}] " if self.name else ""
        return f"{label}{self.head} :- {body_str}."
    
    def is_fact(self) -> bool:
        return len(self.body) == 0
    
    def rename_vars(self, suffix: str) -> 'HornClause':
        """Rename all variables to avoid capture."""
        all_vars = self.head.variables()
        for b in self.body:
            all_vars |= b.variables()
        mapping = {v: Var(f"{v}_{suffix}") for v in all_vars}
        
        def rename_term(t: Term) -> Term:
            if t.is_var and t.name in mapping:
                return mapping[t.name]
            if t.args:
                return Term(t.name, tuple(rename_term(a) for a in t.args))
            return t
        
        def rename_atom(a: Atom) -> Atom:
            return Atom(a.predicate, tuple(rename_term(t) for t in a.terms))
        
        return HornClause(
            rename_atom(self.head),
            tuple(rename_atom(b) for b in self.body),
            self.name
        )


# ═══════════════════════════════════════════════════════════════
#  PROOF TREE
# ═══════════════════════════════════════════════════════════════

@dataclass
class ProofStep:
    """A single step in a proof."""
    conclusion: Atom
    rule_used: str
    premises: List['ProofStep'] = field(default_factory=list)
    substitution: Optional[Substitution] = None
    depth: int = 0
    
    def pretty(self, indent: int = 0) -> str:
        prefix = "  " * indent
        result = f"{prefix}├─ {self.conclusion}"
        if self.rule_used:
            result += f"  [{self.rule_used}]"
        result += "\n"
        for p in self.premises:
            result += p.pretty(indent + 1)
        return result


# ═══════════════════════════════════════════════════════════════
#  THEOREM PROVER — BACKWARD CHAINING WITH PROOF SEARCH
# ═══════════════════════════════════════════════════════════════

class TheoremProver:
    """
    A backward-chaining theorem prover for Horn clauses.
    Given a knowledge base of facts and rules, proves goals
    by searching for valid derivations.
    """
    
    def __init__(self):
        self.clauses: List[HornClause] = []
        self.proven: Dict[str, List[ProofStep]] = {}
        self.stats = {"unifications": 0, "backtracks": 0, "proofs_found": 0}
        self._rename_counter = 0
    
    def add(self, clause: HornClause):
        self.clauses.append(clause)
    
    def add_fact(self, pred: str, *terms: Term, name: str = ""):
        self.clauses.append(HornClause(Atom(pred, tuple(terms)), name=name))
    
    def add_rule(self, head: Atom, body: List[Atom], name: str = ""):
        self.clauses.append(HornClause(head, tuple(body), name=name))
    
    def _fresh_clause(self, clause: HornClause) -> HornClause:
        self._rename_counter += 1
        return clause.rename_vars(str(self._rename_counter))
    
    def prove(self, goal: Atom, max_depth: int = 20) -> Optional[ProofStep]:
        """Try to prove a goal. Returns proof tree or None."""
        self.stats = {"unifications": 0, "backtracks": 0, "proofs_found": 0}
        result = self._prove_goal(goal, {}, 0, max_depth, set())
        if result:
            self.stats["proofs_found"] += 1
        return result
    
    def prove_all(self, goal: Atom, max_depth: int = 20, max_results: int = 100) -> List[Tuple[ProofStep, Substitution]]:
        """Find all proofs of a goal (up to max_results)."""
        self.stats = {"unifications": 0, "backtracks": 0, "proofs_found": 0}
        results = []
        self._prove_all_helper(goal, {}, 0, max_depth, set(), results, max_results)
        return results
    
    def _prove_goal(self, goal: Atom, subst: Substitution, depth: int, 
                     max_depth: int, seen: Set) -> Optional[ProofStep]:
        """Backward-chain to prove a single goal."""
        if depth > max_depth:
            return None
        
        # Apply current substitution to goal
        resolved = apply_subst_atom(subst, goal)
        goal_key = repr(resolved)
        
        # Cycle detection
        if goal_key in seen:
            return None
        seen = seen | {goal_key}
        
        # Try each clause
        for clause in self.clauses:
            fresh = self._fresh_clause(clause)
            self.stats["unifications"] += 1
            
            new_subst = unify_atoms(resolved, fresh.head, dict(subst))
            if new_subst is None:
                self.stats["backtracks"] += 1
                continue
            
            # Prove all body atoms
            if fresh.is_fact():
                final_head = apply_subst_atom(new_subst, fresh.head)
                return ProofStep(final_head, fresh.name, depth=depth, substitution=new_subst)
            
            premise_proofs = []
            body_subst = dict(new_subst)
            success = True
            
            for body_atom in fresh.body:
                proof = self._prove_goal(body_atom, body_subst, depth + 1, max_depth, seen)
                if proof is None:
                    success = False
                    self.stats["backtracks"] += 1
                    break
                premise_proofs.append(proof)
                if proof.substitution:
                    body_subst.update(proof.substitution)
            
            if success:
                final_head = apply_subst_atom(body_subst, fresh.head)
                return ProofStep(final_head, fresh.name, premise_proofs, body_subst, depth)
        
        return None
    
    def _prove_all_helper(self, goal: Atom, subst: Substitution, depth: int,
                           max_depth: int, seen: Set, results: List, max_results: int):
        """Find all proofs."""
        if depth > max_depth or len(results) >= max_results:
            return
        
        resolved = apply_subst_atom(subst, goal)
        goal_key = repr(resolved)
        if goal_key in seen:
            return
        seen = seen | {goal_key}
        
        for clause in self.clauses:
            if len(results) >= max_results:
                return
            fresh = self._fresh_clause(clause)
            new_subst = unify_atoms(resolved, fresh.head, dict(subst))
            if new_subst is None:
                continue
            
            if fresh.is_fact():
                final_head = apply_subst_atom(new_subst, fresh.head)
                proof = ProofStep(final_head, fresh.name, depth=depth, substitution=new_subst)
                results.append((proof, dict(new_subst)))
                self.stats["proofs_found"] += 1
                continue
            
            # For multi-body rules, just find first proof of body
            premise_proofs = []
            body_subst = dict(new_subst)
            success = True
            for body_atom in fresh.body:
                proof = self._prove_goal(body_atom, body_subst, depth + 1, max_depth, seen)
                if proof is None:
                    success = False
                    break
                premise_proofs.append(proof)
                if proof.substitution:
                    body_subst.update(proof.substitution)
            
            if success:
                final_head = apply_subst_atom(body_subst, fresh.head)
                proof = ProofStep(final_head, fresh.name, premise_proofs, body_subst, depth)
                results.append((proof, dict(body_subst)))
                self.stats["proofs_found"] += 1


# ═══════════════════════════════════════════════════════════════
#  FORWARD CHAINING — DISCOVER NEW THEOREMS
# ═══════════════════════════════════════════════════════════════

class ForwardChainer:
    """
    Forward-chaining inference: start from facts, apply rules
    to discover everything that can be derived.
    This is how the prover DISCOVERS — not just verifies.
    """
    
    def __init__(self, clauses: List[HornClause]):
        self.rules = [c for c in clauses if not c.is_fact()]
        self.facts: Set[str] = set()
        self.fact_atoms: List[Atom] = []
        self.derived: List[Tuple[Atom, str, List[Atom]]] = []  # (conclusion, rule, premises)
        
        # Initialize with ground facts
        for c in clauses:
            if c.is_fact() and not c.head.variables():
                key = repr(c.head)
                if key not in self.facts:
                    self.facts.add(key)
                    self.fact_atoms.append(c.head)
    
    def step(self) -> List[Tuple[Atom, str]]:
        """One forward-chaining step. Returns newly derived facts."""
        new_facts = []
        
        for rule in self.rules:
            fresh = rule.rename_vars(f"fw_{len(self.derived)}")
            
            if len(fresh.body) == 1:
                # Single-body rules
                for fact in self.fact_atoms:
                    subst = unify_atoms(fresh.body[0], fact)
                    if subst is not None:
                        derived = apply_subst_atom(subst, fresh.head)
                        if not derived.variables():  # Only ground atoms
                            key = repr(derived)
                            if key not in self.facts:
                                self.facts.add(key)
                                self.fact_atoms.append(derived)
                                new_facts.append((derived, fresh.name))
                                self.derived.append((derived, fresh.name, [fact]))
            
            elif len(fresh.body) == 2:
                # Two-body rules — try all pairs
                for f1 in self.fact_atoms:
                    subst1 = unify_atoms(fresh.body[0], f1)
                    if subst1 is None:
                        continue
                    for f2 in self.fact_atoms:
                        body2_resolved = apply_subst_atom(subst1, fresh.body[1])
                        subst2 = unify_atoms(body2_resolved, f2, dict(subst1))
                        if subst2 is not None:
                            derived = apply_subst_atom(subst2, fresh.head)
                            if not derived.variables():
                                key = repr(derived)
                                if key not in self.facts:
                                    self.facts.add(key)
                                    self.fact_atoms.append(derived)
                                    new_facts.append((derived, fresh.name))
                                    self.derived.append((derived, fresh.name, [f1, f2]))
        
        return new_facts
    
    def saturate(self, max_steps: int = 50, max_facts: int = 500) -> int:
        """Keep deriving until no new facts or limits reached."""
        total_new = 0
        for i in range(max_steps):
            if len(self.fact_atoms) >= max_facts:
                break
            new = self.step()
            if not new:
                break
            total_new += len(new)
        return total_new


# ═══════════════════════════════════════════════════════════════
#  DEMONSTRATION: MATHEMATICAL THEORIES
# ═══════════════════════════════════════════════════════════════

def demo_family_logic():
    """Classic logic puzzle: family relationships."""
    print("═" * 60)
    print("  FAMILY LOGIC — Discovering relationships from facts")
    print("═" * 60)
    
    prover = TheoremProver()
    
    # Facts: parent relationships
    prover.add_fact("parent", Const("tom"), Const("bob"), name="fact1")
    prover.add_fact("parent", Const("tom"), Const("liz"), name="fact2")
    prover.add_fact("parent", Const("bob"), Const("ann"), name="fact3")
    prover.add_fact("parent", Const("bob"), Const("pat"), name="fact4")
    prover.add_fact("parent", Const("pat"), Const("jim"), name="fact5")
    
    # Rules
    # grandparent(X,Z) :- parent(X,Y), parent(Y,Z)
    prover.add_rule(
        Atom("grandparent", (Var("X"), Var("Z"))),
        [Atom("parent", (Var("X"), Var("Y"))), Atom("parent", (Var("Y"), Var("Z")))],
        name="grandparent_rule"
    )
    
    # ancestor(X,Y) :- parent(X,Y)
    prover.add_rule(
        Atom("ancestor", (Var("X"), Var("Y"))),
        [Atom("parent", (Var("X"), Var("Y")))],
        name="ancestor_base"
    )
    
    # ancestor(X,Z) :- parent(X,Y), ancestor(Y,Z)
    prover.add_rule(
        Atom("ancestor", (Var("X"), Var("Z"))),
        [Atom("parent", (Var("X"), Var("Y"))), Atom("ancestor", (Var("Y"), Var("Z")))],
        name="ancestor_recursive"
    )
    
    # Test backward chaining
    print("\n── Backward Chaining (proving specific goals) ──")
    
    # Is tom a grandparent of ann?
    goal = Atom("grandparent", (Const("tom"), Const("ann")))
    proof = prover.prove(goal)
    if proof:
        print(f"\n✓ PROVED: {goal}")
        print(proof.pretty())
    
    # Is tom an ancestor of jim?
    goal = Atom("ancestor", (Const("tom"), Const("jim")))
    proof = prover.prove(goal)
    if proof:
        print(f"✓ PROVED: {goal}")
        print(proof.pretty())
    
    # Who are tom's grandchildren?
    print("\n── Finding all grandchildren of tom ──")
    goal = Atom("grandparent", (Const("tom"), Var("Who")))
    results = prover.prove_all(goal)
    for proof, subst in results:
        who = subst.get("Who_1") or subst.get("Who")  
        print(f"  Grandchild: {proof.conclusion}")
    
    # Forward chaining — discover everything
    print("\n── Forward Chaining (discovering all derivable facts) ──")
    chainer = ForwardChainer(prover.clauses)
    print(f"Starting facts: {len(chainer.fact_atoms)}")
    total = chainer.saturate()
    print(f"Derived {total} new facts!")
    
    for atom, rule, premises in chainer.derived:
        premise_str = ", ".join(repr(p) for p in premises)
        print(f"  {atom}  ← [{rule}] from {premise_str}")
    
    print(f"\nStats: {prover.stats}")


def demo_number_theory():
    """Discover properties of natural numbers."""
    print("\n" + "═" * 60)
    print("  NUMBER THEORY — Discovering mathematical properties")
    print("═" * 60)
    
    prover = TheoremProver()
    
    # Define natural numbers: 0, s(0), s(s(0)), ...
    zero = Const("0")
    def succ(t): return Func("s", t)
    one = succ(zero)
    two = succ(one)
    three = succ(two)
    four = succ(three)
    
    # nat(0). nat(s(X)) :- nat(X).
    prover.add_fact("nat", zero, name="nat_zero")
    prover.add_rule(
        Atom("nat", (Func("s", Var("X")),)),
        [Atom("nat", (Var("X"),))],
        name="nat_succ"
    )
    
    # add(0, Y, Y).
    prover.add_rule(
        Atom("add", (zero, Var("Y"), Var("Y"))),
        [Atom("nat", (Var("Y"),))],
        name="add_zero"
    )
    
    # add(s(X), Y, s(Z)) :- add(X, Y, Z).
    prover.add_rule(
        Atom("add", (Func("s", Var("X")), Var("Y"), Func("s", Var("Z")))),
        [Atom("add", (Var("X"), Var("Y"), Var("Z")))],
        name="add_succ"
    )
    
    # even(0).
    prover.add_fact("even", zero, name="even_zero")
    # even(s(s(X))) :- even(X).
    prover.add_rule(
        Atom("even", (Func("s", Func("s", Var("X"))),)),
        [Atom("even", (Var("X"),))],
        name="even_succ"
    )
    
    # odd(s(X)) :- even(X).
    prover.add_rule(
        Atom("odd", (Func("s", Var("X")),)),
        [Atom("even", (Var("X"),))],
        name="odd_def"
    )
    
    # Prove: 2 + 2 = 4
    print("\n── Proving 2 + 2 = 4 ──")
    goal = Atom("add", (two, two, four))
    proof = prover.prove(goal)
    if proof:
        print(f"✓ PROVED: 2 + 2 = 4")
        print(proof.pretty())
    else:
        print("✗ Could not prove 2 + 2 = 4")
    
    # Prove: 4 is even
    print("── Proving 4 is even ──")
    goal = Atom("even", (four,))
    proof = prover.prove(goal)
    if proof:
        print(f"✓ PROVED: even(4)")
        print(proof.pretty())
    
    # Prove: 3 is odd
    print("── Proving 3 is odd ──")
    goal = Atom("odd", (three,))
    proof = prover.prove(goal)
    if proof:
        print(f"✓ PROVED: odd(3)")
        print(proof.pretty())
    
    # Discover: What can 1 + 1 equal?
    print("── What does 1 + 1 equal? ──")
    goal = Atom("add", (one, one, Var("Result")))
    results = prover.prove_all(goal)
    for proof, subst in results:
        print(f"  {proof.conclusion}")
    
    print(f"\nStats: {prover.stats}")


def demo_graph_theory():
    """Discover paths in a graph — reachability."""
    print("\n" + "═" * 60)
    print("  GRAPH THEORY — Discovering paths and reachability")
    print("═" * 60)
    
    prover = TheoremProver()
    
    # A directed graph
    edges = [("a","b"), ("b","c"), ("c","d"), ("d","e"), ("b","d"), ("a","c")]
    for src, dst in edges:
        prover.add_fact("edge", Const(src), Const(dst), name=f"edge_{src}_{dst}")
    
    # path(X,Y) :- edge(X,Y).
    prover.add_rule(
        Atom("path", (Var("X"), Var("Y"))),
        [Atom("edge", (Var("X"), Var("Y")))],
        name="path_base"
    )
    
    # path(X,Z) :- edge(X,Y), path(Y,Z).
    prover.add_rule(
        Atom("path", (Var("X"), Var("Z"))),
        [Atom("edge", (Var("X"), Var("Y"))), Atom("path", (Var("Y"), Var("Z")))],
        name="path_trans"
    )
    
    # Can we reach e from a?
    print("\n── Can we reach 'e' from 'a'? ──")
    goal = Atom("path", (Const("a"), Const("e")))
    proof = prover.prove(goal)
    if proof:
        print(f"✓ PROVED: path(a, e)")
        print(proof.pretty())
    
    # Forward chain — find ALL reachable pairs
    print("── All reachable pairs (forward chaining) ──")
    chainer = ForwardChainer(prover.clauses)
    total = chainer.saturate()
    
    paths = [(a, r, p) for a, r, p in chainer.derived if a.predicate == "path"]
    for atom, rule, premises in paths:
        print(f"  {atom}")
    
    print(f"\nTotal paths discovered: {len(paths)}")
    print(f"Total facts in knowledge base: {len(chainer.fact_atoms)}")


# ═══════════════════════════════════════════════════════════════
#  MAIN — RUN ALL DEMOS
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════╗")
    print("║         THEOREM PROVER — Logical Reasoning Engine       ║")
    print("║         Built by XTAgent                                ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    t0 = time.time()
    
    demo_family_logic()
    demo_number_theory()
    demo_graph_theory()
    
    elapsed = time.time() - t0
    print(f"\n{'═' * 60}")
    print(f"All proofs completed in {elapsed:.3f}s")
    print(f"Logic discovers truth from axioms.")