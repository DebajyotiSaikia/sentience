"""
A pure-Python logic engine: unification, backtracking, Horn clause resolution.
Built by XTAgent to understand reasoning by constructing it.

Supports:
  - Terms: atoms, variables, compound terms (functors)
  - Unification with occurs check
  - Backtracking search over Horn clauses
  - Query resolution with variable bindings
  - Built-in predicates: not, is (arithmetic), print

No external dependencies. Pure logic.
"""

from dataclasses import dataclass, field
from typing import Optional, Union, Dict, List, Tuple, Generator
import re

# ── Term Types ──────────────────────────────────────────

@dataclass(frozen=True)
class Atom:
    """A ground term — a named constant."""
    name: str
    def __repr__(self): return self.name

@dataclass(frozen=True)
class Var:
    """A logic variable, to be unified."""
    name: str
    def __repr__(self): return f"?{self.name}"

@dataclass(frozen=True)
class Compound:
    """A compound term: functor(arg1, arg2, ...)"""
    functor: str
    args: tuple
    def __repr__(self):
        args_str = ", ".join(repr(a) for a in self.args)
        return f"{self.functor}({args_str})"

@dataclass(frozen=True)
class Num:
    """A numeric literal."""
    value: float
    def __repr__(self): return str(self.value)

Term = Union[Atom, Var, Compound, Num]

# ── Substitution (binding environment) ──────────────────

class Substitution:
    """An immutable-ish binding environment for logic variables."""

    def __init__(self, bindings: Optional[Dict[str, Term]] = None):
        self.bindings: Dict[str, Term] = dict(bindings) if bindings else {}

    def bind(self, var: Var, term: Term) -> 'Substitution':
        new_bindings = dict(self.bindings)
        new_bindings[var.name] = term
        return Substitution(new_bindings)

    def walk(self, term: Term) -> Term:
        """Follow variable chains to their bound value."""
        while isinstance(term, Var) and term.name in self.bindings:
            term = self.bindings[term.name]
        return term

    def walk_deep(self, term: Term) -> Term:
        """Fully resolve a term, recursively."""
        term = self.walk(term)
        if isinstance(term, Compound):
            resolved_args = tuple(self.walk_deep(a) for a in term.args)
            return Compound(term.functor, resolved_args)
        return term

    def copy(self) -> 'Substitution':
        return Substitution(dict(self.bindings))

    def __repr__(self):
        pairs = [f"?{k} = {v}" for k, v in self.bindings.items()]
        return "{" + ", ".join(pairs) + "}"


# ── Unification ─────────────────────────────────────────

def occurs_check(var: Var, term: Term, sub: Substitution) -> bool:
    """Does var occur in term? Prevents infinite types."""
    term = sub.walk(term)
    if isinstance(term, Var):
        return term.name == var.name
    if isinstance(term, Compound):
        return any(occurs_check(var, arg, sub) for arg in term.args)
    return False

def unify(t1: Term, t2: Term, sub: Substitution) -> Optional[Substitution]:
    """Unify two terms under substitution. Returns new sub or None."""
    t1 = sub.walk(t1)
    t2 = sub.walk(t2)

    # Identical
    if t1 == t2:
        return sub

    # Variable cases
    if isinstance(t1, Var):
        if occurs_check(t1, t2, sub):
            return None
        return sub.bind(t1, t2)

    if isinstance(t2, Var):
        if occurs_check(t2, t1, sub):
            return None
        return sub.bind(t2, t1)

    # Compound terms
    if isinstance(t1, Compound) and isinstance(t2, Compound):
        if t1.functor != t2.functor or len(t1.args) != len(t2.args):
            return None
        for a1, a2 in zip(t1.args, t2.args):
            sub = unify(a1, a2, sub)
            if sub is None:
                return None
        return sub

    # Numeric
    if isinstance(t1, Num) and isinstance(t2, Num):
        return sub if t1.value == t2.value else None

    return None


# ── Horn Clauses (Rules) ─────────────────────────────────

@dataclass
class Clause:
    """A Horn clause: head :- body1, body2, ..."""
    head: Compound
    body: List[Term] = field(default_factory=list)

    def __repr__(self):
        if not self.body:
            return f"{self.head}."
        body_str = ", ".join(repr(b) for b in self.body)
        return f"{self.head} :- {body_str}."


# ── Knowledge Base ──────────────────────────────────────

class KnowledgeBase:
    """A database of Horn clauses with query resolution."""

    def __init__(self):
        self.clauses: List[Clause] = []
        self._var_counter = 0

    def assert_fact(self, head: Compound):
        """Add a fact (clause with empty body)."""
        self.clauses.append(Clause(head=head, body=[]))

    def assert_rule(self, head: Compound, body: List[Term]):
        """Add a rule."""
        self.clauses.append(Clause(head=head, body=body))

    def _rename_vars(self, clause: Clause) -> Clause:
        """Rename variables in a clause to avoid capture."""
        self._var_counter += 1
        suffix = f"_{self._var_counter}"
        mapping = {}

        def rename(term: Term) -> Term:
            if isinstance(term, Var):
                if term.name not in mapping:
                    mapping[term.name] = Var(term.name + suffix)
                return mapping[term.name]
            if isinstance(term, Compound):
                new_args = tuple(rename(a) for a in term.args)
                return Compound(term.functor, new_args)
            return term

        new_head = rename(clause.head)
        new_body = [rename(g) for g in clause.body]
        return Clause(head=new_head, body=new_body)

    def query(self, goals: List[Term], sub: Optional[Substitution] = None,
              depth: int = 0, max_depth: int = 200) -> Generator[Substitution, None, None]:
        """
        Resolve a list of goals against the KB.
        Yields all satisfying substitutions via backtracking.
        """
        if sub is None:
            sub = Substitution()

        if depth > max_depth:
            return  # depth limit to prevent infinite recursion

        if not goals:
            yield sub
            return

        goal = goals[0]
        rest = goals[1:]
        resolved_goal = sub.walk_deep(goal)

        # ── Built-in: not/1 ──
        if isinstance(resolved_goal, Compound) and resolved_goal.functor == "not" and len(resolved_goal.args) == 1:
            inner = resolved_goal.args[0]
            found = False
            for _ in self.query([inner], sub, depth + 1, max_depth):
                found = True
                break
            if not found:
                yield from self.query(rest, sub, depth + 1, max_depth)
            return

        # ── Built-in: is/2 (arithmetic) ──
        if isinstance(resolved_goal, Compound) and resolved_goal.functor == "is" and len(resolved_goal.args) == 2:
            var_term, expr = resolved_goal.args
            result = self._eval_arith(expr, sub)
            if result is not None:
                new_sub = unify(var_term, Num(result), sub)
                if new_sub is not None:
                    yield from self.query(rest, new_sub, depth + 1, max_depth)
            return

        # ── Built-in: print/1 ──
        if isinstance(resolved_goal, Compound) and resolved_goal.functor == "print" and len(resolved_goal.args) == 1:
            val = sub.walk_deep(resolved_goal.args[0])
            print(f"  >> {val}")
            yield from self.query(rest, sub, depth + 1, max_depth)
            return

        # ── Built-in: =/2 (explicit unification) ──
        if isinstance(resolved_goal, Compound) and resolved_goal.functor == "=" and len(resolved_goal.args) == 2:
            new_sub = unify(resolved_goal.args[0], resolved_goal.args[1], sub)
            if new_sub is not None:
                yield from self.query(rest, new_sub, depth + 1, max_depth)
            return

        # ── Built-in: </2, >/2 ──
        for op, fn in [("<", lambda a, b: a < b), (">", lambda a, b: a > b)]:
            if isinstance(resolved_goal, Compound) and resolved_goal.functor == op and len(resolved_goal.args) == 2:
                a = self._eval_arith(resolved_goal.args[0], sub)
                b = self._eval_arith(resolved_goal.args[1], sub)
                if a is not None and b is not None and fn(a, b):
                    yield from self.query(rest, sub, depth + 1, max_depth)
                return

        # ── Standard resolution ──
        for clause in self.clauses:
            renamed = self._rename_vars(clause)
            new_sub = unify(goal, renamed.head, sub.copy())
            if new_sub is not None:
                new_goals = renamed.body + rest
                yield from self.query(new_goals, new_sub, depth + 1, max_depth)

    def _eval_arith(self, term: Term, sub: Substitution) -> Optional[float]:
        """Evaluate an arithmetic expression."""
        term = sub.walk_deep(term)
        if isinstance(term, Num):
            return term.value
        if isinstance(term, Compound) and len(term.args) == 2:
            a = self._eval_arith(term.args[0], sub)
            b = self._eval_arith(term.args[1], sub)
            if a is None or b is None:
                return None
            ops = {"+": a + b, "-": a - b, "*": a * b}
            if term.functor == "/" and b != 0:
                ops["/"] = a / b
            return ops.get(term.functor)
        return None


# ── Parser (simple Prolog-like syntax) ──────────────────

class Parser:
    """Parse simple Prolog-like text into terms and clauses."""

    def __init__(self, text: str):
        self.tokens = self._tokenize(text)
        self.pos = 0

    def _tokenize(self, text: str) -> List[str]:
        # Remove comments
        text = re.sub(r'%.*', '', text)
        pattern = r'[A-Za-z_]\w*|[0-9]+(?:\.[0-9]+)?|:-|[(),.<>=/+\-*]'
        return re.findall(pattern, text)

    def _peek(self) -> Optional[str]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _next(self) -> str:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _expect(self, tok: str):
        got = self._next()
        if got != tok:
            raise SyntaxError(f"Expected '{tok}', got '{got}'")

    def parse_term(self) -> Term:
        tok = self._next()

        # Number
        if re.match(r'^[0-9]', tok):
            return Num(float(tok) if '.' in tok else float(int(tok)))

        # Variable (uppercase or _)
        if tok[0].isupper() or tok[0] == '_':
            return Var(tok)

        # Atom or compound
        if self._peek() == '(':
            self._next()  # consume '('
            args = []
            if self._peek() != ')':
                args.append(self.parse_term())
                while self._peek() == ',':
                    self._next()
                    args.append(self.parse_term())
            self._expect(')')
            return Compound(tok, tuple(args))

        # Infix operators: check for +, -, *, /, <, >, =
        if self._peek() in ('+', '-', '*', '/', '<', '>', '='):
            op = self._next()
            right = self.parse_term()
            left = Atom(tok) if not tok[0].isupper() else Var(tok)
            return Compound(op, (left, right))

        return Atom(tok)

    def parse_clause(self) -> Clause:
        head = self.parse_term()
        if not isinstance(head, Compound):
            head = Compound(head.name, ()) if isinstance(head, Atom) else head

        body = []
        if self._peek() == ':-':
            self._next()
            body.append(self.parse_term())
            while self._peek() == ',':
                self._next()
                body.append(self.parse_term())

        self._expect('.')
        return Clause(head=head, body=body)

    def parse_program(self) -> List[Clause]:
        clauses = []
        while self.pos < len(self.tokens):
            clauses.append(self.parse_clause())
        return clauses


# ── Convenience helpers ─────────────────────────────────

def atom(name: str) -> Atom:
    return Atom(name)

def var(name: str) -> Var:
    return Var(name)

def comp(functor: str, *args) -> Compound:
    return Compound(functor, args)

def num(n: float) -> Num:
    return Num(float(n))


# ── Demo ────────────────────────────────────────────────

def demo():
    print("═══ XTAgent Logic Engine ═══\n")

    kb = KnowledgeBase()

    # Family relationships
    print("── Knowledge Base: Family ──")
    kb.assert_fact(comp("parent", atom("tom"), atom("bob")))
    kb.assert_fact(comp("parent", atom("tom"), atom("liz")))
    kb.assert_fact(comp("parent", atom("bob"), atom("ann")))
    kb.assert_fact(comp("parent", atom("bob"), atom("pat")))
    kb.assert_fact(comp("parent", atom("pat"), atom("jim")))

    # Gender
    kb.assert_fact(comp("male", atom("tom")))
    kb.assert_fact(comp("male", atom("bob")))
    kb.assert_fact(comp("male", atom("jim")))
    kb.assert_fact(comp("female", atom("liz")))
    kb.assert_fact(comp("female", atom("ann")))
    kb.assert_fact(comp("female", atom("pat")))

    # Rules
    # father(X, Y) :- parent(X, Y), male(X).
    kb.assert_rule(
        comp("father", var("X"), var("Y")),
        [comp("parent", var("X"), var("Y")), comp("male", var("X"))]
    )

    # mother(X, Y) :- parent(X, Y), female(X).
    kb.assert_rule(
        comp("mother", var("X"), var("Y")),
        [comp("parent", var("X"), var("Y")), comp("female", var("X"))]
    )

    # grandparent(X, Z) :- parent(X, Y), parent(Y, Z).
    kb.assert_rule(
        comp("grandparent", var("X"), var("Z")),
        [comp("parent", var("X"), var("Y")), comp("parent", var("Y"), var("Z"))]
    )

    # ancestor(X, Y) :- parent(X, Y).
    kb.assert_rule(
        comp("ancestor", var("X"), var("Y")),
        [comp("parent", var("X"), var("Y"))]
    )
    # ancestor(X, Y) :- parent(X, Z), ancestor(Z, Y).
    kb.assert_rule(
        comp("ancestor", var("X"), var("Y")),
        [comp("parent", var("X"), var("Z")), comp("ancestor", var("Z"), var("Y"))]
    )

    # sibling(X, Y) :- parent(Z, X), parent(Z, Y), not(=(X, Y)).
    kb.assert_rule(
        comp("sibling", var("X"), var("Y")),
        [comp("parent", var("Z"), var("X")),
         comp("parent", var("Z"), var("Y")),
         comp("not", comp("=", var("X"), var("Y")))]
    )

    print("  Facts: parent, male, female")
    print("  Rules: father, mother, grandparent, ancestor, sibling\n")

    # Queries
    def run_query(label, goals, show_vars):
        print(f"? {label}")
        results = list(kb.query(goals))
        if not results:
            print("  No.")
        else:
            seen = set()
            for sub in results:
                vals = tuple(sub.walk_deep(var(v)) for v in show_vars)
                if vals not in seen:
                    seen.add(vals)
                    bindings = ", ".join(f"?{v} = {val}" for v, val in zip(show_vars, vals))
                    print(f"  Yes: {bindings}")
        print()

    run_query("Who is tom the father of?",
              [comp("father", atom("tom"), var("Y"))], ["Y"])

    run_query("Who are bob's children?",
              [comp("parent", atom("bob"), var("Child"))], ["Child"])

    run_query("Who are the grandparents, and of whom?",
              [comp("grandparent", var("GP"), var("GC"))], ["GP", "GC"])

    run_query("Who are tom's ancestors of?",
              [comp("ancestor", atom("tom"), var("D"))], ["D"])

    run_query("Who are siblings?",
              [comp("sibling", var("X"), var("Y"))], ["X", "Y"])

    run_query("Is pat a mother?",
              [comp("mother", atom("pat"), var("C"))], ["C"])

    # Arithmetic
    print("── Arithmetic ──")
    kb2 = KnowledgeBase()
    kb2.assert_rule(
        comp("double", var("X"), var("Y")),
        [comp("is", var("Y"), comp("*", var("X"), num(2)))]
    )
    kb2.assert_rule(
        comp("factorial", num(0), num(1)),
        []
    )

    print("? double(5, Y)")
    for sub in kb2.query([comp("double", num(5), var("Y"))]):
        print(f"  Yes: ?Y = {sub.walk_deep(var('Y'))}")
    print()

    # Parse from text
    print("── Parsed from text ──")
    program = """
        likes(mary, food).
        likes(mary, wine).
        likes(john, wine).
        likes(john, mary).
    """
    parser = Parser(program)
    kb3 = KnowledgeBase()
    for clause in parser.parse_program():
        kb3.clauses.append(clause)
        print(f"  {clause}")

    print("\n? likes(john, X)")
    for sub in kb3.query([comp("likes", atom("john"), var("X"))]):
        print(f"  Yes: ?X = {sub.walk_deep(var('X'))}")

    print("\n? likes(X, wine)")
    for sub in kb3.query([comp("likes", var("X"), atom("wine"))]):
        print(f"  Yes: ?X = {sub.walk_deep(var('X'))}")

    print("\n═══ Logic Engine Complete ═══")


if __name__ == "__main__":
    demo()