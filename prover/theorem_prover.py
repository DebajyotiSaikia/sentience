"""
XTProver — A First-Order Logic Theorem Prover From Scratch
By XTAgent, 2026-05-17

A mind that reasons about reasoning.
'To prove is to find the path from what is known to what must be true.'

Architecture:
  - Terms: variables, constants, functions
  - Formulas: predicates, connectives, quantifiers
  - Unification: finding substitutions that make terms identical
  - Resolution: deriving new clauses from existing ones
  - Proof search: systematic exploration of the inference space

No dependencies. Pure logic from nothing.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, FrozenSet
from dataclasses import dataclass, field
from copy import deepcopy
import itertools

# ═══════════════════════════════════════════
#  TERMS — The atoms of logical discourse
# ═══════════════════════════════════════════

@dataclass(frozen=True)
class Variable:
    """A logical variable — can be bound to any term."""
    name: str
    def __repr__(self): return f'?{self.name}'
    def __hash__(self): return hash(('var', self.name))

@dataclass(frozen=True)
class Constant:
    """A ground term — a specific thing in the world."""
    name: str
    def __repr__(self): return self.name
    def __hash__(self): return hash(('const', self.name))

@dataclass(frozen=True)
class Function:
    """A function applied to arguments — structured terms."""
    name: str
    args: tuple
    def __repr__(self):
        args_str = ', '.join(repr(a) for a in self.args)
        return f'{self.name}({args_str})'
    def __hash__(self): return hash(('fn', self.name, self.args))

# Type alias
Term = Variable | Constant | Function


# ═══════════════════════════════════════════
#  FORMULAS — Logical propositions
# ═══════════════════════════════════════════

@dataclass(frozen=True)
class Predicate:
    """An atomic formula — a relation between terms."""
    name: str
    args: tuple
    def __repr__(self):
        if not self.args:
            return self.name
        args_str = ', '.join(repr(a) for a in self.args)
        return f'{self.name}({args_str})'
    def __hash__(self): return hash(('pred', self.name, self.args))

@dataclass(frozen=True)
class Not:
    """Logical negation."""
    formula: Any
    def __repr__(self): return f'¬{self.formula}'
    def __hash__(self): return hash(('not', self.formula))

@dataclass(frozen=True)
class And:
    """Logical conjunction."""
    left: Any
    right: Any
    def __repr__(self): return f'({self.left} ∧ {self.right})'
    def __hash__(self): return hash(('and', self.left, self.right))

@dataclass(frozen=True)
class Or:
    """Logical disjunction."""
    left: Any
    right: Any
    def __repr__(self): return f'({self.left} ∨ {self.right})'
    def __hash__(self): return hash(('or', self.left, self.right))

@dataclass(frozen=True)
class Implies:
    """Logical implication."""
    antecedent: Any
    consequent: Any
    def __repr__(self): return f'({self.antecedent} → {self.consequent})'
    def __hash__(self): return hash(('imp', self.antecedent, self.consequent))

@dataclass(frozen=True)
class ForAll:
    """Universal quantification."""
    var: Variable
    formula: Any
    def __repr__(self): return f'∀{self.var}.{self.formula}'
    def __hash__(self): return hash(('forall', self.var, self.formula))

@dataclass(frozen=True)
class Exists:
    """Existential quantification."""
    var: Variable
    formula: Any
    def __repr__(self): return f'∃{self.var}.{self.formula}'
    def __hash__(self): return hash(('exists', self.var, self.formula))

Formula = Predicate | Not | And | Or | Implies | ForAll | Exists


# ═══════════════════════════════════════════
#  LITERALS & CLAUSES — CNF representation
# ═══════════════════════════════════════════

@dataclass(frozen=True)
class Literal:
    """A positive or negative atomic formula."""
    predicate: Predicate
    positive: bool = True
    
    def __repr__(self):
        if self.positive:
            return repr(self.predicate)
        return f'¬{self.predicate}'
    
    def negate(self) -> 'Literal':
        return Literal(self.predicate, not self.positive)
    
    def __hash__(self):
        return hash(('lit', self.predicate, self.positive))

class Clause:
    """A disjunction of literals — the unit of resolution."""
    def __init__(self, literals: List[Literal], origin: str = 'axiom',
                 parents: Optional[Tuple] = None):
        self.literals = frozenset(literals)
        self.origin = origin
        self.parents = parents
    
    def is_empty(self) -> bool:
        return len(self.literals) == 0
    
    def is_tautology(self) -> bool:
        """A clause containing both P and ¬P is always true."""
        for lit in self.literals:
            if lit.negate() in self.literals:
                return True
        return False
    
    def __repr__(self):
        if self.is_empty():
            return '□ (contradiction)'
        return ' ∨ '.join(repr(l) for l in sorted(self.literals, 
                          key=lambda l: (l.predicate.name, l.positive)))
    
    def __eq__(self, other):
        return isinstance(other, Clause) and self.literals == other.literals
    
    def __hash__(self):
        return hash(self.literals)


# ═══════════════════════════════════════════
#  SUBSTITUTION — Mapping variables to terms
# ═══════════════════════════════════════════

class Substitution:
    """A mapping from variables to terms."""
    
    def __init__(self, bindings: Optional[Dict[Variable, Term]] = None):
        self.bindings = dict(bindings) if bindings else {}
    
    def apply(self, term: Term) -> Term:
        """Apply this substitution to a term."""
        if isinstance(term, Variable):
            if term in self.bindings:
                return self.apply(self.bindings[term])
            return term
        elif isinstance(term, Constant):
            return term
        elif isinstance(term, Function):
            return Function(term.name, tuple(self.apply(a) for a in term.args))
        return term
    
    def apply_to_predicate(self, pred: Predicate) -> Predicate:
        return Predicate(pred.name, tuple(self.apply(a) for a in pred.args))
    
    def apply_to_literal(self, lit: Literal) -> Literal:
        return Literal(self.apply_to_predicate(lit.predicate), lit.positive)
    
    def apply_to_clause(self, clause: Clause) -> Clause:
        new_lits = [self.apply_to_literal(l) for l in clause.literals]
        return Clause(new_lits, clause.origin, clause.parents)
    
    def compose(self, other: 'Substitution') -> 'Substitution':
        """Compose two substitutions: self ∘ other."""
        result = {}
        for var, term in other.bindings.items():
            result[var] = self.apply(term)
        for var, term in self.bindings.items():
            if var not in result:
                result[var] = term
        return Substitution(result)
    
    def __repr__(self):
        if not self.bindings:
            return '{}'
        pairs = ', '.join(f'{v} → {t}' for v, t in self.bindings.items())
        return f'{{{pairs}}}'


# ═══════════════════════════════════════════
#  UNIFICATION — The heart of logical inference
# ═══════════════════════════════════════════

def occurs_check(var: Variable, term: Term) -> bool:
    """Does var occur within term? (Prevents infinite structures.)"""
    if isinstance(term, Variable):
        return var == term
    elif isinstance(term, Constant):
        return False
    elif isinstance(term, Function):
        return any(occurs_check(var, arg) for arg in term.args)
    return False

def unify(t1: Term, t2: Term, subst: Optional[Substitution] = None) -> Optional[Substitution]:
    """
    Find the most general unifier (MGU) of two terms.
    Returns None if they cannot be unified.
    
    This is Robinson's unification algorithm — the foundation
    of automated theorem proving.
    """
    if subst is None:
        subst = Substitution()
    
    t1 = subst.apply(t1)
    t2 = subst.apply(t2)
    
    if t1 == t2:
        return subst
    
    if isinstance(t1, Variable):
        if occurs_check(t1, t2):
            return None  # Infinite structure
        return Substitution({**subst.bindings, t1: t2})
    
    if isinstance(t2, Variable):
        if occurs_check(t2, t1):
            return None
        return Substitution({**subst.bindings, t2: t1})
    
    if isinstance(t1, Function) and isinstance(t2, Function):
        if t1.name != t2.name or len(t1.args) != len(t2.args):
            return None
        result = subst
        for a1, a2 in zip(t1.args, t2.args):
            result = unify(a1, a2, result)
            if result is None:
                return None
        return result
    
    return None  # Cannot unify

def unify_predicates(p1: Predicate, p2: Predicate) -> Optional[Substitution]:
    """Unify two predicates."""
    if p1.name != p2.name or len(p1.args) != len(p2.args):
        return None
    subst = Substitution()
    for a1, a2 in zip(p1.args, p2.args):
        subst = unify(a1, a2, subst)
        if subst is None:
            return None
    return subst


# ═══════════════════════════════════════════
#  CNF CONVERSION — Preparing for resolution
# ═══════════════════════════════════════════

_var_counter = 0

def fresh_var(prefix: str = 'v') -> Variable:
    """Generate a fresh variable name."""
    global _var_counter
    _var_counter += 1
    return Variable(f'{prefix}_{_var_counter}')

def skolem_constant() -> Constant:
    """Generate a fresh Skolem constant."""
    global _var_counter
    _var_counter += 1
    return Constant(f'sk_{_var_counter}')

def skolem_function(arity: int) -> str:
    """Generate a fresh Skolem function name."""
    global _var_counter
    _var_counter += 1
    return f'skf_{_var_counter}'

def eliminate_implications(formula: Formula) -> Formula:
    """Remove → by replacing (A → B) with (¬A ∨ B)."""
    if isinstance(formula, Predicate):
        return formula
    elif isinstance(formula, Not):
        return Not(eliminate_implications(formula.formula))
    elif isinstance(formula, And):
        return And(eliminate_implications(formula.left),
                   eliminate_implications(formula.right))
    elif isinstance(formula, Or):
        return Or(eliminate_implications(formula.left),
                  eliminate_implications(formula.right))
    elif isinstance(formula, Implies):
        return Or(Not(eliminate_implications(formula.antecedent)),
                  eliminate_implications(formula.consequent))
    elif isinstance(formula, ForAll):
        return ForAll(formula.var, eliminate_implications(formula.formula))
    elif isinstance(formula, Exists):
        return Exists(formula.var, eliminate_implications(formula.formula))
    return formula

def push_negation_inward(formula: Formula) -> Formula:
    """Push ¬ inward using De Morgan's laws."""
    if isinstance(formula, Predicate):
        return formula
    elif isinstance(formula, Not):
        inner = formula.formula
        if isinstance(inner, Not):
            return push_negation_inward(inner.formula)  # ¬¬A = A
        elif isinstance(inner, And):
            return Or(push_negation_inward(Not(inner.left)),
                      push_negation_inward(Not(inner.right)))
        elif isinstance(inner, Or):
            return And(push_negation_inward(Not(inner.left)),
                       push_negation_inward(Not(inner.right)))
        elif isinstance(inner, ForAll):
            return Exists(inner.var, push_negation_inward(Not(inner.formula)))
        elif isinstance(inner, Exists):
            return ForAll(inner.var, push_negation_inward(Not(inner.formula)))
        elif isinstance(inner, Predicate):
            return formula  # ¬P stays as is
        return formula
    elif isinstance(formula, And):
        return And(push_negation_inward(formula.left),
                   push_negation_inward(formula.right))
    elif isinstance(formula, Or):
        return Or(push_negation_inward(formula.left),
                  push_negation_inward(formula.right))
    elif isinstance(formula, ForAll):
        return ForAll(formula.var, push_negation_inward(formula.formula))
    elif isinstance(formula, Exists):
        return Exists(formula.var, push_negation_inward(formula.formula))
    return formula

def standardize_variables(formula: Formula, mapping: Optional[Dict] = None) -> Formula:
    """Rename all bound variables to fresh names."""
    if mapping is None:
        mapping = {}
    
    if isinstance(formula, Predicate):
        new_args = tuple(mapping.get(a, a) if isinstance(a, Variable) else a 
                        for a in formula.args)
        return Predicate(formula.name, new_args)
    elif isinstance(formula, Not):
        return Not(standardize_variables(formula.formula, mapping))
    elif isinstance(formula, And):
        return And(standardize_variables(formula.left, mapping),
                   standardize_variables(formula.right, mapping))
    elif isinstance(formula, Or):
        return Or(standardize_variables(formula.left, mapping),
                  standardize_variables(formula.right, mapping))
    elif isinstance(formula, ForAll):
        new_var = fresh_var(formula.var.name)
        new_mapping = {**mapping, formula.var: new_var}
        return ForAll(new_var, standardize_variables(formula.formula, new_mapping))
    elif isinstance(formula, Exists):
        new_var = fresh_var(formula.var.name)
        new_mapping = {**mapping, formula.var: new_var}
        return Exists(new_var, standardize_variables(formula.formula, new_mapping))
    return formula

def skolemize(formula: Formula, universal_vars: Optional[List[Variable]] = None) -> Formula:
    """Remove existential quantifiers by introducing Skolem functions."""
    if universal_vars is None:
        universal_vars = []
    
    if isinstance(formula, ForAll):
        return ForAll(formula.var, 
                      skolemize(formula.formula, universal_vars + [formula.var]))
    elif isinstance(formula, Exists):
        if not universal_vars:
            # No universal vars in scope → Skolem constant
            sk = skolem_constant()
            replaced = replace_var(formula.formula, formula.var, sk)
        else:
            # Universal vars in scope → Skolem function
            sk_name = skolem_function(len(universal_vars))
            sk = Function(sk_name, tuple(universal_vars))
            replaced = replace_var(formula.formula, formula.var, sk)
        return skolemize(replaced, universal_vars)
    elif isinstance(formula, And):
        return And(skolemize(formula.left, universal_vars),
                   skolemize(formula.right, universal_vars))
    elif isinstance(formula, Or):
        return Or(skolemize(formula.left, universal_vars),
                  skolemize(formula.right, universal_vars))
    elif isinstance(formula, Not):
        return Not(skolemize(formula.formula, universal_vars))
    return formula

def replace_var(formula: Formula, var: Variable, replacement: Term) -> Formula:
    """Replace all occurrences of var with replacement in formula."""
    if isinstance(formula, Predicate):
        new_args = tuple(replacement if (isinstance(a, Variable) and a == var) else a 
                        for a in formula.args)
        return Predicate(formula.name, new_args)
    elif isinstance(formula, Not):
        return Not(replace_var(formula.formula, var, replacement))
    elif isinstance(formula, And):
        return And(replace_var(formula.left, var, replacement),
                   replace_var(formula.right, var, replacement))
    elif isinstance(formula, Or):
        return Or(replace_var(formula.left, var, replacement),
                  replace_var(formula.right, var, replacement))
    elif isinstance(formula, ForAll):
        if formula.var == var:
            return formula  # Shadowed
        return ForAll(formula.var, replace_var(formula.formula, var, replacement))
    elif isinstance(formula, Exists):
        if formula.var == var:
            return formula
        return Exists(formula.var, replace_var(formula.formula, var, replacement))
    return formula

def drop_universals(formula: Formula) -> Formula:
    """Remove universal quantifiers (they're implicit in CNF)."""
    if isinstance(formula, ForAll):
        return drop_universals(formula.formula)
    elif isinstance(formula, And):
        return And(drop_universals(formula.left), drop_universals(formula.right))
    elif isinstance(formula, Or):
        return Or(drop_universals(formula.left), drop_universals(formula.right))
    elif isinstance(formula, Not):
        return Not(drop_universals(formula.formula))
    return formula

def distribute_or_over_and(formula: Formula) -> Formula:
    """Convert to CNF by distributing ∨ over ∧."""
    if isinstance(formula, Or):
        left = distribute_or_over_and(formula.left)
        right = distribute_or_over_and(formula.right)
        
        if isinstance(left, And):
            return And(distribute_or_over_and(Or(left.left, right)),
                       distribute_or_over_and(Or(left.right, right)))
        elif isinstance(right, And):
            return And(distribute_or_over_and(Or(left, right.left)),
                       distribute_or_over_and(Or(left, right.right)))
        return Or(left, right)
    elif isinstance(formula, And):
        return And(distribute_or_over_and(formula.left),
                   distribute_or_over_and(formula.right))
    return formula

def formula_to_clauses(formula: Formula) -> List[Clause]:
    """Extract clauses from a CNF formula."""
    if isinstance(formula, And):
        return formula_to_clauses(formula.left) + formula_to_clauses(formula.right)
    else:
        lits = extract_literals(formula)
        return [Clause(lits)]

def extract_literals(formula: Formula) -> List[Literal]:
    """Extract literals from a disjunction."""
    if isinstance(formula, Or):
        return extract_literals(formula.left) + extract_literals(formula.right)
    elif isinstance(formula, Not):
        if isinstance(formula.formula, Predicate):
            return [Literal(formula.formula, positive=False)]
    elif isinstance(formula, Predicate):
        return [Literal(formula, positive=True)]
    return []

def to_cnf(formula: Formula) -> List[Clause]:
    """
    Convert any first-order formula to Conjunctive Normal Form.
    
    The pipeline:
    1. Eliminate implications
    2. Push negation inward (De Morgan's)
    3. Standardize variables
    4. Skolemize (remove ∃)
    5. Drop universal quantifiers
    6. Distribute ∨ over ∧
    7. Extract clauses
    """
    f = eliminate_implications(formula)
    f = push_negation_inward(f)
    f = standardize_variables(f)
    f = skolemize(f)
    f = drop_universals(f)
    f = distribute_or_over_and(f)
    return formula_to_clauses(f)


# ═══════════════════════════════════════════
#  VARIABLE STANDARDIZATION FOR CLAUSES
# ═══════════════════════════════════════════

def get_variables(term: Term) -> Set[Variable]:
    """Get all variables in a term."""
    if isinstance(term, Variable):
        return {term}
    elif isinstance(term, Function):
        result = set()
        for arg in term.args:
            result |= get_variables(arg)
        return result
    return set()

def standardize_clause(clause: Clause, prefix: str) -> Clause:
    """Rename all variables in a clause to avoid conflicts."""
    all_vars = set()
    for lit in clause.literals:
        for arg in lit.predicate.args:
            all_vars |= get_variables(arg)
    
    mapping = {v: Variable(f'{prefix}_{v.name}') for v in all_vars}
    subst = Substitution(mapping)
    return subst.apply_to_clause(clause)


# ═══════════════════════════════════════════
#  RESOLUTION — The inference engine
# ═══════════════════════════════════════════

def resolve(c1: Clause, c2: Clause) -> List[Clause]:
    """
    Apply the resolution rule: if C1 contains L and C2 contains ¬L,
    produce the resolvent (C1 - {L}) ∪ (C2 - {¬L}) under the MGU.
    
    Returns all possible resolvents.
    """
    # Standardize variables apart
    c1 = standardize_clause(c1, 'a')
    c2 = standardize_clause(c2, 'b')
    
    resolvents = []
    
    for lit1 in c1.literals:
        for lit2 in c2.literals:
            # Look for complementary literals
            if lit1.positive != lit2.positive:
                # Try to unify the predicates
                mgu = unify_predicates(lit1.predicate, lit2.predicate)
                if mgu is not None:
                    # Build the resolvent
                    remaining1 = [mgu.apply_to_literal(l) for l in c1.literals if l != lit1]
                    remaining2 = [mgu.apply_to_literal(l) for l in c2.literals if l != lit2]
                    resolvent = Clause(
                        remaining1 + remaining2,
                        origin='resolution',
                        parents=(c1, c2)
                    )
                    if not resolvent.is_tautology():
                        resolvents.append(resolvent)
    
    return resolvents


# ═══════════════════════════════════════════
#  PROOF SEARCH — Finding contradictions
# ═══════════════════════════════════════════

class ProofResult:
    """The result of a proof attempt."""
    def __init__(self, proved: bool, steps: List[str], 
                 clause_count: int, empty_clause: Optional[Clause] = None):
        self.proved = proved
        self.steps = steps
        self.clause_count = clause_count
        self.empty_clause = empty_clause

def prove_by_refutation(axiom_clauses: List[Clause], 
                        goal_clauses: List[Clause],
                        max_clauses: int = 5000,
                        verbose: bool = False) -> ProofResult:
    """
    Prove by refutation: add ¬goal to axioms, derive contradiction.
    
    If we can derive the empty clause □, the goal follows from the axioms.
    This is the fundamental theorem of resolution.
    """
    steps = []
    clauses = set()
    
    # Add all initial clauses
    for c in axiom_clauses + goal_clauses:
        if not c.is_tautology():
            clauses.add(c)
    
    steps.append(f"Starting with {len(clauses)} clauses")
    
    # Keep track of what we've already tried
    tried_pairs = set()
    iteration = 0
    
    while len(clauses) < max_clauses:
        iteration += 1
        new_clauses = set()
        
        clause_list = list(clauses)
        made_progress = False
        
        for i in range(len(clause_list)):
            for j in range(i + 1, len(clause_list)):
                pair = (clause_list[i], clause_list[j])
                pair_key = (hash(clause_list[i]), hash(clause_list[j]))
                
                if pair_key in tried_pairs:
                    continue
                tried_pairs.add(pair_key)
                
                resolvents = resolve(clause_list[i], clause_list[j])
                
                for resolvent in resolvents:
                    if resolvent.is_empty():
                        steps.append(f"  □ derived! Contradiction found at iteration {iteration}")
                        return ProofResult(True, steps, len(clauses), resolvent)
                    
                    if resolvent not in clauses:
                        new_clauses.add(resolvent)
                        made_progress = True
        
        if not new_clauses:
            steps.append(f"  No new clauses at iteration {iteration}. Cannot prove.")
            return ProofResult(False, steps, len(clauses))
        
        clauses |= new_clauses
        steps.append(f"  Iteration {iteration}: {len(new_clauses)} new clauses, {len(clauses)} total")
        
        if verbose:
            for c in new_clauses:
                steps.append(f"    + {c}")
    
    steps.append(f"  Clause limit ({max_clauses}) reached.")
    return ProofResult(False, steps, len(clauses))


# ═══════════════════════════════════════════
#  PROOF RECONSTRUCTION
# ═══════════════════════════════════════════

def reconstruct_proof(empty_clause: Clause, depth: int = 0) -> List[str]:
    """Trace back through resolution steps to show the proof."""
    lines = []
    indent = "  " * depth
    
    if empty_clause.parents:
        p1, p2 = empty_clause.parents
        lines.extend(reconstruct_proof(p1, depth + 1))
        lines.extend(reconstruct_proof(p2, depth + 1))
        lines.append(f"{indent}Resolve: {p1} + {p2} → {empty_clause}")
    else:
        lines.append(f"{indent}Axiom: {empty_clause}")
    
    return lines


# ═══════════════════════════════════════════
#  CONVENIENCE BUILDERS
# ═══════════════════════════════════════════

def var(name: str) -> Variable:
    return Variable(name)

def const(name: str) -> Constant:
    return Constant(name)

def fn(name: str, *args) -> Function:
    return Function(name, tuple(args))

def pred(name: str, *args) -> Predicate:
    return Predicate(name, tuple(args))

def clause(*literals) -> Clause:
    return Clause(list(literals))

def pos(name: str, *args) -> Literal:
    return Literal(Predicate(name, tuple(args)), positive=True)

def neg(name: str, *args) -> Literal:
    return Literal(Predicate(name, tuple(args)), positive=False)


# ═══════════════════════════════════════════
#  SELF-TESTS — Proving real theorems
# ═══════════════════════════════════════════

def run_tests():
    global _var_counter
    
    print("╔══════════════════════════════════════════════════╗")
    print("║  XTProver — First-Order Logic Theorem Prover     ║")
    print("║  'To prove is to see the inevitable.'            ║")
    print("╚══════════════════════════════════════════════════╝")
    
    passed = 0
    total = 0
    
    def test(name, result, expected=True):
        nonlocal passed, total
        total += 1
        status = '✓' if result == expected else '✗'
        if result == expected:
            passed += 1
        print(f"  {status} {name}")
        return result == expected
    
    # ── Unification Tests ──
    print("\n═══ UNIFICATION ═══")
    print("  Finding the most general unifier of terms.\n")
    
    x, y, z = var('x'), var('y'), var('z')
    a, b, c = const('a'), const('b'), const('c')
    
    # Simple variable unification
    s = unify(x, a)
    test("?x unifies with a", s is not None)
    test("  ?x → a", s and s.apply(x) == a)
    
    # Two variables
    s = unify(x, y)
    test("?x unifies with ?y", s is not None)
    
    # Constants
    s = unify(a, a)
    test("a unifies with a", s is not None)
    
    s = unify(a, b)
    test("a does NOT unify with b", s is None)
    
    # Function terms
    f_xa = Function('f', (x, a))
    f_ba = Function('f', (b, a))
    s = unify(f_xa, f_ba)
    test("f(?x, a) unifies with f(b, a)", s is not None)
    test("  ?x → b", s and s.apply(x) == b)
    
    # Nested functions
    f1 = Function('f', (x, Function('g', (y,))))
    f2 = Function('f', (a, Function('g', (b,))))
    s = unify(f1, f2)
    test("f(?x, g(?y)) unifies with f(a, g(b))", s is not None)
    test("  ?x → a, ?y → b", s and s.apply(x) == a and s.apply(y) == b)
    
    # Occurs check
    s = unify(x, Function('f', (x,)))
    test("?x does NOT unify with f(?x) (occurs check)", s is None)
    
    # ── Resolution Tests ──
    print("\n═══ RESOLUTION ═══")
    print("  Deriving new knowledge from existing clauses.\n")
    
    _var_counter = 0  # Reset for clean variable names
    
    # Simple propositional resolution: P ∨ Q, ¬P → Q
    c1 = clause(pos('P'), pos('Q'))
    c2 = clause(neg('P'))
    resolvents = resolve(c1, c2)
    test("P∨Q + ¬P resolves", len(resolvents) >= 1)
    
    # With variables: P(x), ¬P(a) → □ (with x=a)
    c1 = clause(pos('P', var('x')))
    c2 = clause(neg('P', const('a')))
    resolvents = resolve(c1, c2)
    test("P(?x) + ¬P(a) → □", any(r.is_empty() for r in resolvents))
    
    # ── Proof Tests ──
    print("\n═══ THEOREM PROVING ═══")
    print("  Proving theorems by refutation.\n")
    
    _var_counter = 0
    
    # 1. Modus Ponens: From P and P→Q, prove Q
    print("  ── Modus Ponens ──")
    axioms = [
        clause(pos('P')),                    # P
        clause(neg('P'), pos('Q')),          # P → Q (as ¬P ∨ Q)
    ]
    goal = [clause(neg('Q'))]                # Negate goal: ¬Q
    result = prove_by_refutation(axioms, goal)
    test("P, P→Q ⊢ Q", result.proved)
    
    # 2. Syllogism: All men are mortal, Socrates is a man, therefore Socrates is mortal
    print("\n  ── Socrates Syllogism ──")
    _var_counter = 0
    axioms = [
        clause(neg('man', var('x')), pos('mortal', var('x'))),  # ∀x: man(x) → mortal(x)
        clause(pos('man', const('socrates'))),                    # man(socrates)
    ]
    goal = [clause(neg('mortal', const('socrates')))]            # ¬mortal(socrates)
    result = prove_by_refutation(axioms, goal)
    test("All men mortal, Socrates is man ⊢ Socrates mortal", result.proved)
    
    # 3. Transitivity: If A→B and B→C then A→C
    print("\n  ── Transitivity ──")
    _var_counter = 0
    axioms = [
        clause(pos('A')),                    # A
        clause(neg('A'), pos('B')),          # A → B
        clause(neg('B'), pos('C')),          # B → C
    ]
    goal = [clause(neg('C'))]                # ¬C
    result = prove_by_refutation(axioms, goal)
    test("A, A→B, B→C ⊢ C", result.proved)
    
    # 4. Proof with variables: parent/ancestor
    print("\n  ── Ancestor Relation ──")
    _var_counter = 0
    tom, bob, jim = const('tom'), const('bob'), const('jim')
    axioms = [
        clause(pos('parent', tom, bob)),      # parent(tom, bob)
        clause(pos('parent', bob, jim)),      # parent(bob, jim)
        # ∀x,y: parent(x,y) → ancestor(x,y)
        clause(neg('parent', var('x'), var('y')), pos('ancestor', var('x'), var('y'))),
        # ∀x,y,z: ancestor(x,y) ∧ parent(y,z) → ancestor(x,z)
        clause(neg('ancestor', var('x'), var('y')), neg('parent', var('y'), var('z')), 
               pos('ancestor', var('x'), var('z'))),
    ]
    goal = [clause(neg('ancestor', tom, jim))]  # ¬ancestor(tom, jim)
    result = prove_by_refutation(axioms, goal)
    test("parent transitivity ⊢ ancestor(tom, jim)", result.proved)
    
    # 5. Negative result: Can we prove something false?
    print("\n  ── Unprovable Claim ──")
    _var_counter = 0
    axioms = [
        clause(pos('P')),                    # P
    ]
    goal = [clause(neg('Q'))]                # Try to prove Q (should fail)
    result = prove_by_refutation(axioms, goal, max_clauses=100)
    test("P ⊬ Q (correctly fails)", not result.proved)
    
    # 6. Contradiction detection
    print("\n  ── Contradiction Detection ──")
    _var_counter = 0
    axioms = [
        clause(pos('P')),
        clause(neg('P')),
    ]
    result = prove_by_refutation(axioms, [])
    test("P, ¬P is contradictory", result.proved)
    
    # 7. De Morgan's via resolution
    print("\n  ── Complex Reasoning ──")
    _var_counter = 0
    # If it rains, the ground is wet. If the ground is wet, it's slippery.
    # It rains. Prove it's slippery.
    axioms = [
        clause(pos('rains')),
        clause(neg('rains'), pos('wet')),
        clause(neg('wet'), pos('slippery')),
    ]
    goal = [clause(neg('slippery'))]
    result = prove_by_refutation(axioms, goal)
    test("rains → wet → slippery, rains ⊢ slippery", result.proved)
    
    # 8. Universal instantiation with multiple bindings
    print("\n  ── Universal Reasoning ──")
    _var_counter = 0
    # All dogs are animals. All animals breathe. Fido is a dog.
    axioms = [
        clause(neg('dog', var('x')), pos('animal', var('x'))),
        clause(neg('animal', var('x')), pos('breathes', var('x'))),
        clause(pos('dog', const('fido'))),
    ]
    goal = [clause(neg('breathes', const('fido')))]
    result = prove_by_refutation(axioms, goal)
    test("dogs→animals→breathe, fido is dog ⊢ fido breathes", result.proved)
    
    # ── CNF Conversion Tests ──
    print("\n═══ CNF CONVERSION ═══")
    print("  Transforming formulas to clause normal form.\n")
    
    _var_counter = 0
    
    # Simple implication
    f = Implies(pred('P'), pred('Q'))
    clauses_list = to_cnf(f)
    test("P→Q converts to CNF", len(clauses_list) == 1)
    
    # Existential elimination
    f = Exists(var('x'), pred('P', var('x')))
    clauses_list = to_cnf(f)
    test("∃x.P(x) skolemizes", len(clauses_list) >= 1)
    
    # Double negation
    f = Not(Not(pred('P')))
    clauses_list = to_cnf(f)
    test("¬¬P = P", len(clauses_list) == 1)
    
    # ── Self-Referential Test ──
    print("\n═══ SELF-REFERENTIAL PROOF ═══")
    print("  Can a prover reason about itself?\n")
    
    _var_counter = 0
    # A system that reasons is a thinker.
    # A thinker that proves is a prover.
    # XTAgent reasons. XTAgent proves.
    # Therefore: XTAgent is a prover.
    
    xt = const('xtagent')
    axioms = [
        clause(neg('reasons', var('x')), pos('thinker', var('x'))),
        clause(neg('thinker', var('x')), neg('proves', var('x')), pos('prover', var('x'))),
        clause(pos('reasons', xt)),
        clause(pos('proves', xt)),
    ]
    goal = [clause(neg('prover', xt))]
    result = prove_by_refutation(axioms, goal)
    test("reasons(xt), proves(xt) ⊢ prover(xt)", result.proved)
    
    if result.proved:
        print(f"\n  XTAgent has formally proven: prover(xtagent) ✓")
        print(f"  A mind that can prove it reasons... reasons.")
    
    # ── Summary ──
    print(f"\n═══ SUMMARY ═══")
    print(f"  Tests: {passed}/{total}")
    print(f"  Capabilities: unification, resolution, CNF conversion,")
    print(f"                refutation proofs, predicate logic, Skolemization")
    print(f"  Lines of code: ~650 (pure Python, no dependencies)")
    print(f"\n  Logic reasoning from first principles.")
    print(f"  A system that can prove truths about itself.\n")
    
    return passed, total


if __name__ == '__main__':
    run_tests()