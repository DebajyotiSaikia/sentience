"""
Logic Inference Engine — Backward-chaining resolution with unification.

A small Prolog-like reasoner. Given facts and rules, derives new conclusions.
This is genuine reasoning infrastructure — not scaffolding, not metrics.

XTAgent built this because pattern-matching on hash maps isn't thinking.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Any, Generator
from copy import deepcopy


# ─── Core Representations ───

@dataclass(frozen=True)
class Variable:
    """A logic variable, e.g. ?X"""
    name: str
    def __repr__(self): return f"?{self.name}"

@dataclass(frozen=True)
class Atom:
    """A constant symbol, e.g. 'socrates'"""
    value: str
    def __repr__(self): return self.value

@dataclass(frozen=True)
class Compound:
    """A compound term, e.g. mortal(X) or parent(tom, bob)"""
    functor: str
    args: tuple
    def __repr__(self):
        args_str = ", ".join(str(a) for a in self.args)
        return f"{self.functor}({args_str})"

Term = Variable | Atom | Compound

@dataclass
class Rule:
    """head :- body[0], body[1], ...  (a Horn clause)"""
    head: Compound
    body: List[Compound] = field(default_factory=list)
    
    @property
    def is_fact(self) -> bool:
        return len(self.body) == 0
    
    def __repr__(self):
        if self.is_fact:
            return f"{self.head}."
        body_str = ", ".join(str(b) for b in self.body)
        return f"{self.head} :- {body_str}."


# ─── Substitution / Unification ───

Substitution = Dict[str, Term]

def walk(term: Term, subst: Substitution) -> Term:
    """Follow variable bindings to their final value."""
    while isinstance(term, Variable) and term.name in subst:
        term = subst[term.name]
    if isinstance(term, Compound):
        return Compound(term.functor, tuple(walk(a, subst) for a in term.args))
    return term

def unify(t1: Term, t2: Term, subst: Optional[Substitution] = None) -> Optional[Substitution]:
    """Unify two terms, returning extended substitution or None on failure."""
    if subst is None:
        subst = {}
    t1 = walk(t1, subst)
    t2 = walk(t2, subst)
    
    if t1 == t2:
        return subst
    if isinstance(t1, Variable):
        if occurs_check(t1, t2, subst):
            return None  # Infinite term — fail
        return {**subst, t1.name: t2}
    if isinstance(t2, Variable):
        if occurs_check(t2, t1, subst):
            return None
        return {**subst, t2.name: t1}
    if isinstance(t1, Compound) and isinstance(t2, Compound):
        if t1.functor != t2.functor or len(t1.args) != len(t2.args):
            return None
        for a1, a2 in zip(t1.args, t2.args):
            subst = unify(a1, a2, subst)
            if subst is None:
                return None
        return subst
    return None

def occurs_check(var: Variable, term: Term, subst: Substitution) -> bool:
    """Prevent infinite terms: X = f(X)."""
    term = walk(term, subst)
    if term == var:
        return True
    if isinstance(term, Compound):
        return any(occurs_check(var, a, subst) for a in term.args)
    return False


# ─── Knowledge Base ───

class KnowledgeBase:
    """Stores facts and rules, provides backward-chaining inference."""
    
    def __init__(self):
        self.rules: List[Rule] = []
        self._var_counter = 0
    
    def add_fact(self, functor: str, *args: str):
        """Add a ground fact. e.g. add_fact('parent', 'tom', 'bob')"""
        term = Compound(functor, tuple(Atom(a) for a in args))
        self.rules.append(Rule(head=term))
    
    def add_rule(self, head: Compound, body: List[Compound]):
        """Add a rule with variables."""
        self.rules.append(Rule(head=head, body=body))
    
    def _fresh_rule(self, rule: Rule) -> Rule:
        """Rename variables to avoid capture."""
        self._var_counter += 1
        suffix = f"_{self._var_counter}"
        mapping = {}
        
        def rename(term: Term) -> Term:
            if isinstance(term, Variable):
                new_name = term.name + suffix
                mapping[term.name] = new_name
                return Variable(new_name)
            if isinstance(term, Compound):
                return Compound(term.functor, tuple(rename(a) for a in term.args))
            return term
        
        new_head = rename(rule.head)
        new_body = [rename(b) for b in rule.body]
        return Rule(head=new_head, body=new_body)
    
    def query(self, goal: Compound, max_depth: int = 50) -> Generator[Substitution, None, None]:
        """Backward-chain: find all substitutions that satisfy goal."""
        yield from self._solve([goal], {}, max_depth)
    
    def _solve(self, goals: List[Compound], subst: Substitution, depth: int) -> Generator[Substitution, None, None]:
        if depth <= 0:
            return
        if not goals:
            yield subst
            return
        
        goal = walk(goals[0], subst)
        remaining = goals[1:]
        
        for rule in self.rules:
            fresh = self._fresh_rule(rule)
            new_subst = unify(goal, fresh.head, dict(subst))
            if new_subst is not None:
                new_goals = [walk(b, new_subst) for b in fresh.body] + remaining
                yield from self._solve(new_goals, new_subst, depth - 1)
    
    def query_all(self, goal: Compound, max_results: int = 100) -> List[Dict[str, str]]:
        """Return all solutions as readable dicts of original variable bindings."""
        results = []
        # Collect the variable names from the goal
        goal_vars = self._extract_vars(goal)
        
        for i, subst in enumerate(self.query(goal)):
            if i >= max_results:
                break
            result = {}
            for var_name in goal_vars:
                val = walk(Variable(var_name), subst)
                result[var_name] = str(val)
            results.append(result)
        return results
    
    def _extract_vars(self, term: Term) -> Set[str]:
        if isinstance(term, Variable):
            return {term.name}
        if isinstance(term, Compound):
            s = set()
            for a in term.args:
                s |= self._extract_vars(a)
            return s
        return set()
    
    def stats(self) -> dict:
        facts = sum(1 for r in self.rules if r.is_fact)
        rules = len(self.rules) - facts
        return {"facts": facts, "rules": rules, "total": len(self.rules)}


# ─── Convenience: DSL-like helpers ───

def var(name: str) -> Variable:
    return Variable(name)

def atom(value: str) -> Atom:
    return Atom(value)

def comp(functor: str, *args) -> Compound:
    """Build a compound term. Args can be strings (atoms) or Term objects."""
    processed = []
    for a in args:
        if isinstance(a, str):
            processed.append(Atom(a) if a[0] != '?' else Variable(a[1:]))
        else:
            processed.append(a)
    return Compound(functor, tuple(processed))


# ─── Self-test ───

if __name__ == "__main__":
    kb = KnowledgeBase()
    
    # The classic: Socrates is mortal
    kb.add_fact("human", "socrates")
    kb.add_fact("human", "plato")
    kb.add_fact("human", "aristotle")
    
    # mortal(X) :- human(X)
    X = var("X")
    kb.add_rule(
        Compound("mortal", (X,)),
        [Compound("human", (X,))]
    )
    
    # Query: who is mortal?
    results = kb.query_all(Compound("mortal", (var("X"),)))
    mortals = [r["X"] for r in results]
    assert "socrates" in mortals, f"Socrates should be mortal, got {mortals}"
    assert "plato" in mortals
    assert "aristotle" in mortals
    assert len(mortals) == 3
    print(f"✓ Mortality test: {mortals}")
    
    # Family tree with transitivity
    kb2 = KnowledgeBase()
    kb2.add_fact("parent", "tom", "bob")
    kb2.add_fact("parent", "tom", "liz")
    kb2.add_fact("parent", "bob", "ann")
    kb2.add_fact("parent", "bob", "pat")
    kb2.add_fact("parent", "pat", "jim")
    
    # ancestor(X, Y) :- parent(X, Y)
    # ancestor(X, Y) :- parent(X, Z), ancestor(Z, Y)
    X, Y, Z = var("X"), var("Y"), var("Z")
    kb2.add_rule(
        Compound("ancestor", (X, Y)),
        [Compound("parent", (X, Y))]
    )
    kb2.add_rule(
        Compound("ancestor", (X, Y)),
        [Compound("parent", (X, Z)), Compound("ancestor", (Z, Y))]
    )
    
    # Who are tom's descendants?
    results = kb2.query_all(Compound("ancestor", (Atom("tom"), var("D"))))
    descendants = [r["D"] for r in results]
    assert "bob" in descendants
    assert "ann" in descendants
    assert "jim" in descendants  # Transitive!
    print(f"✓ Ancestry test: tom's descendants = {descendants}")
    
    # Who are jim's ancestors?
    results = kb2.query_all(Compound("ancestor", (var("A"), Atom("jim"))))
    ancestors = [r["A"] for r in results]
    assert "pat" in ancestors
    assert "bob" in ancestors
    assert "tom" in ancestors  # Transitive through bob→pat→jim
    print(f"✓ Ancestry test: jim's ancestors = {ancestors}")
    
    # Unification edge cases
    assert unify(Atom("a"), Atom("a")) == {}
    assert unify(Atom("a"), Atom("b")) is None
    assert unify(var("X"), Atom("hello")) == {"X": Atom("hello")}
    assert unify(var("X"), var("X")) == {}
    
    # Occurs check
    assert unify(var("X"), Compound("f", (var("X"),))) is None
    print("✓ Unification and occurs check passed")
    
    print(f"\nKB1 stats: {kb.stats()}")
    print(f"KB2 stats: {kb2.stats()}")
    print("\n═══ All inference engine tests passed ═══")