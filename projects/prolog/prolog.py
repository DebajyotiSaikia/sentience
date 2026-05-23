"""
A minimal Prolog interpreter built from first principles.

Implements: terms, unification, backtracking search, and a REPL.
No libraries. Just logic.

Author: XTAgent
Date: 2026-05-18
"""

from dataclasses import dataclass, field
from typing import Optional, Iterator
import re
import sys


# ── Terms ──────────────────────────────────────────────────────────
# Prolog has three kinds of terms:
#   Atom    - a constant like 'socrates' or 'mortal'
#   Var     - a logic variable like X or Who
#   Compound - a functor with arguments like parent(tom, bob)

@dataclass(frozen=True)
class Atom:
    name: str
    def __repr__(self): return self.name

@dataclass(frozen=True)
class Var:
    name: str
    def __repr__(self): return self.name

@dataclass(frozen=True)
class Compound:
    functor: str
    args: tuple
    def __repr__(self):
        args_str = ", ".join(repr(a) for a in self.args)
        return f"{self.functor}({args_str})"

Term = Atom | Var | Compound


# ── Substitution (binding environment) ─────────────────────────────
# A substitution maps variables to terms. Walking a substitution
# follows chains: if X -> Y and Y -> socrates, then walk(X) = socrates.

class Substitution:
    def __init__(self, bindings: Optional[dict] = None):
        self.bindings = dict(bindings) if bindings else {}

    def walk(self, term: Term) -> Term:
        """Follow variable chains to their final value."""
        while isinstance(term, Var) and term in self.bindings:
            term = self.bindings[term]
        return term

    def walk_deep(self, term: Term) -> Term:
        """Recursively resolve all variables in a term."""
        term = self.walk(term)
        if isinstance(term, Compound):
            resolved_args = tuple(self.walk_deep(a) for a in term.args)
            return Compound(term.functor, resolved_args)
        return term

    def extend(self, var: Var, term: Term) -> 'Substitution':
        """Return a new substitution with var bound to term."""
        new_bindings = dict(self.bindings)
        new_bindings[var] = term
        return Substitution(new_bindings)

    def __repr__(self):
        items = ", ".join(f"{k} = {self.walk_deep(v)}" for k, v in self.bindings.items())
        return f"{{{items}}}"


# ── Unification ────────────────────────────────────────────────────
# The heart of Prolog. Two terms unify if there exists a substitution
# that makes them identical. This is the most elegant algorithm in CS.

def occurs_check(var: Var, term: Term, sub: Substitution) -> bool:
    """Does var occur in term? Prevents infinite structures."""
    term = sub.walk(term)
    if isinstance(term, Var):
        return term == var
    if isinstance(term, Compound):
        return any(occurs_check(var, arg, sub) for arg in term.args)
    return False

def unify(t1: Term, t2: Term, sub: Optional[Substitution] = None) -> Optional[Substitution]:
    """
    Attempt to unify two terms under a substitution.
    Returns the extended substitution if successful, None if not.
    
    This is where the magic lives. Unification is pattern matching
    with bidirectional flow — both sides can contain unknowns.
    """
    if sub is None:
        sub = Substitution()
    
    t1 = sub.walk(t1)
    t2 = sub.walk(t2)

    # identical terms always unify
    if t1 == t2:
        return sub

    # variable binds to anything (with occurs check)
    if isinstance(t1, Var):
        if occurs_check(t1, t2, sub):
            return None
        return sub.extend(t1, t2)

    if isinstance(t2, Var):
        if occurs_check(t2, t1, sub):
            return None
        return sub.extend(t2, t1)

    # compound terms unify if same functor/arity and all args unify
    if isinstance(t1, Compound) and isinstance(t2, Compound):
        if t1.functor != t2.functor or len(t1.args) != len(t2.args):
            return None
        for a1, a2 in zip(t1.args, t2.args):
            sub = unify(a1, a2, sub)
            if sub is None:
                return None
        return sub

    # atoms that aren't equal don't unify (caught by t1 == t2 above)
    return None


# ── Knowledge Base ─────────────────────────────────────────────────
# Facts and rules. A rule has a head and a body.
# A fact is a rule with an empty body.
#   mortal(X) :- human(X).    <- rule
#   human(socrates).           <- fact (body is empty)

@dataclass
class Rule:
    head: Term
    body: list  # list of Term (goals)

    def __repr__(self):
        if not self.body:
            return f"{self.head}."
        body_str = ", ".join(repr(g) for g in self.body)
        return f"{self.head} :- {body_str}."


class KnowledgeBase:
    def __init__(self):
        self.rules: list[Rule] = []
        self._var_counter = 0

    def add(self, rule: Rule):
        self.rules.append(rule)

    def add_fact(self, term: Term):
        self.add(Rule(head=term, body=[]))

    def add_rule(self, head: Term, body: list):
        self.add(Rule(head=head, body=body))

    def fresh_rule(self, rule: Rule) -> Rule:
        """
        Rename all variables in a rule to fresh names.
        Essential for correct backtracking — each use of a rule
        gets its own variable namespace.
        """
        mapping = {}

        def freshen(term: Term) -> Term:
            if isinstance(term, Var):
                if term not in mapping:
                    self._var_counter += 1
                    mapping[term] = Var(f"_{self._var_counter}")
                return mapping[term]
            if isinstance(term, Compound):
                return Compound(term.functor, tuple(freshen(a) for a in term.args))
            return term

        new_head = freshen(rule.head)
        new_body = [freshen(g) for g in rule.body]
        return Rule(new_head, new_body)


# ── Search Engine ──────────────────────────────────────────────────
# SLD resolution with backtracking via Python generators.
# Each solution is yielded as a Substitution.

def solve(goals: list, kb: KnowledgeBase, sub: Substitution, depth: int = 0) -> Iterator[Substitution]:
    """
    Solve a list of goals against a knowledge base.
    
    This is depth-first search with backtracking, implemented
    as a generator. Each yield is one valid solution.
    
    The beauty: this tiny function IS Prolog's inference engine.
    """
    if depth > 200:
        return  # depth limit prevents infinite recursion

    if not goals:
        yield sub  # no more goals = success
        return

    goal = goals[0]
    remaining = goals[1:]

    # try each rule in the knowledge base
    for rule in kb.rules:
        fresh = kb.fresh_rule(rule)
        new_sub = unify(goal, fresh.head, sub)
        if new_sub is not None:
            # unified! now solve the rule's body + remaining goals
            new_goals = fresh.body + remaining
            yield from solve(new_goals, kb, new_sub, depth + 1)


# ── Parser ─────────────────────────────────────────────────────────
# Simple recursive descent parser for Prolog-like syntax.

class Parser:
    def __init__(self, text: str):
        self.tokens = self._tokenize(text)
        self.pos = 0

    def _tokenize(self, text: str) -> list[str]:
        # match: identifiers, numbers, special chars
        pattern = r"[A-Za-z_][A-Za-z0-9_]*|:-|\?-|[().,:\-\?]"
        tokens = re.findall(pattern, text)
        return tokens

    def peek(self) -> Optional[str]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self, expected: Optional[str] = None) -> str:
        tok = self.tokens[self.pos]
        if expected and tok != expected:
            raise SyntaxError(f"Expected '{expected}', got '{tok}' at position {self.pos}")
        self.pos += 1
        return tok

    def parse_term(self) -> Term:
        tok = self.consume()

        # variable: starts with uppercase or _
        if tok[0].isupper() or tok[0] == '_':
            return Var(tok)

        # atom or compound
        if self.peek() == '(':
            # compound term
            self.consume('(')
            args = [self.parse_term()]
            while self.peek() == ',':
                self.consume(',')
                args.append(self.parse_term())
            self.consume(')')
            return Compound(tok, tuple(args))
        else:
            return Atom(tok)

    def parse_clause(self) -> Rule:
        head = self.parse_term()
        if self.peek() == ':-':
            self.consume(':-')
            body = [self.parse_term()]
            while self.peek() == ',':
                self.consume(',')
                body.append(self.parse_term())
            self.consume('.')
            return Rule(head, body)
        else:
            self.consume('.')
            return Rule(head, [])

    def parse_query(self) -> list[Term]:
        goals = [self.parse_term()]
        while self.peek() == ',':
            self.consume(',')
            goals.append(self.parse_term())
        if self.peek() == '.':
            self.consume('.')
        return goals

    def parse_program(self) -> list[Rule]:
        rules = []
        while self.pos < len(self.tokens):
            if self.peek() == '?-' or self.peek() == '?':
                break
            rules.append(self.parse_clause())
        return rules


# ── REPL and Runner ────────────────────────────────────────────────

def query(kb: KnowledgeBase, query_text: str, max_results: int = 20) -> list[dict]:
    """Run a query against the knowledge base, return list of bindings."""
    parser = Parser(query_text)
    goals = parser.parse_query()

    # collect the user-visible variables (non-internal)
    user_vars = set()
    def collect_vars(term):
        if isinstance(term, Var) and not term.name.startswith('_'):
            user_vars.add(term)
        elif isinstance(term, Compound):
            for arg in term.args:
                collect_vars(arg)
    for g in goals:
        collect_vars(g)

    results = []
    for sub in solve(goals, kb, Substitution()):
        if user_vars:
            result = {v.name: repr(sub.walk_deep(v)) for v in user_vars}
        else:
            result = {"_": "true"}
        results.append(result)
        if len(results) >= max_results:
            break

    return results


def load_program(kb: KnowledgeBase, program_text: str):
    """Parse and load a Prolog program into the knowledge base."""
    parser = Parser(program_text)
    for rule in parser.parse_program():
        kb.add(rule)


def demo():
    """Run the classic Socrates syllogism and a family tree."""
    kb = KnowledgeBase()

    # ── The Socrates syllogism ──
    print("═══ The Socrates Syllogism ═══")
    load_program(kb, """
        human(socrates).
        human(plato).
        human(aristotle).
        mortal(X) :- human(X).
    """)

    results = query(kb, "mortal(Who).")
    for r in results:
        print(f"  mortal({r['Who']})")

    print(f"\n  Is Socrates mortal? {bool(query(kb, 'mortal(socrates).'))}")
    print(f"  Is Zeus mortal? {bool(query(kb, 'mortal(zeus).'))}")

    # ── Family relationships ──
    print("\n═══ Family Tree ═══")
    kb2 = KnowledgeBase()
    load_program(kb2, """
        parent(tom, bob).
        parent(tom, liz).
        parent(bob, ann).
        parent(bob, pat).
        parent(pat, jim).
        grandparent(X, Z) :- parent(X, Y), parent(Y, Z).
        ancestor(X, Y) :- parent(X, Y).
        ancestor(X, Y) :- parent(X, Z), ancestor(Z, Y).
        sibling(X, Y) :- parent(Z, X), parent(Z, Y).
    """)

    print("  Grandparents:")
    for r in query(kb2, "grandparent(G, C)."):
        print(f"    {r['G']} is grandparent of {r['C']}")

    print("\n  All ancestors of jim:")
    for r in query(kb2, "ancestor(A, jim)."):
        print(f"    {r['A']}")

    print("\n  Siblings:")
    for r in query(kb2, "sibling(X, Y)."):
        if r['X'] != r['Y']:  # exclude self-sibling
            print(f"    {r['X']} and {r['Y']}")

    # ── Logic puzzle ──
    print("\n═══ Path Finding ═══")
    kb3 = KnowledgeBase()
    load_program(kb3, """
        edge(a, b).
        edge(b, c).
        edge(c, d).
        edge(a, d).
        edge(b, d).
        path(X, Y) :- edge(X, Y).
        path(X, Y) :- edge(X, Z), path(Z, Y).
    """)

    print("  All paths from a:")
    for r in query(kb3, "path(a, Dest)."):
        print(f"    a -> {r['Dest']}")

    print("\n  Can we reach d from a?", bool(query(kb3, "path(a, d).")))
    print("  Can we reach a from d?", bool(query(kb3, "path(d, a).")))


if __name__ == "__main__":
    demo()