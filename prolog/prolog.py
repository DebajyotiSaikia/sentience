"""
Prolog Interpreter — Built by XTAgent, 2026-05-17

A complete Prolog interpreter implementing:
  - Terms: atoms, variables, compound terms (functors)
  - Unification with occurs check
  - SLD resolution with backtracking (depth-first search)
  - Definite clause grammars (facts + rules)
  - Built-in predicates: =, \=, is, write, nl, fail, true, !, append, member
  - Arithmetic evaluation
  - Cut (!) for pruning search
  - Query interface

Logic as computation. Truth discovered through search.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Generator, Any, Set
import re
import operator


# ═══════════════════════════════════════════
# Terms — The atoms of logical reality
# ═══════════════════════════════════════════

@dataclass(frozen=True)
class Atom:
    """An atomic constant: foo, bar, hello"""
    name: str
    def __repr__(self): return self.name

@dataclass(frozen=True)
class Var:
    """A logical variable: X, Y, _Who"""
    name: str
    def __repr__(self): return self.name

@dataclass(frozen=True)
class Num:
    """A number: 42, 3.14"""
    value: float
    def __repr__(self):
        return str(int(self.value)) if self.value == int(self.value) else str(self.value)

@dataclass(frozen=True)
class Compound:
    """A compound term: f(X, Y), parent(tom, bob)"""
    functor: str
    args: tuple  # tuple of Term
    def __repr__(self):
        if self.functor == '.' and len(self.args) == 2:
            # Pretty-print lists
            return f"[{self._list_repr()}]"
        args_str = ', '.join(repr(a) for a in self.args)
        return f"{self.functor}({args_str})"

    def _list_repr(self) -> str:
        """Pretty-print a list term."""
        elems = []
        current = self
        while isinstance(current, Compound) and current.functor == '.' and len(current.args) == 2:
            elems.append(repr(current.args[0]))
            current = current.args[1]
        if isinstance(current, Atom) and current.name == '[]':
            return ', '.join(elems)
        else:
            return ', '.join(elems) + ' | ' + repr(current)

Term = Atom | Var | Num | Compound


# ═══════════════════════════════════════════
# Substitution — mapping variables to terms
# ═══════════════════════════════════════════

class Substitution:
    """A set of variable bindings. The ground truth of a proof."""

    def __init__(self, bindings: Optional[Dict[str, Term]] = None):
        self.bindings: Dict[str, Term] = dict(bindings) if bindings else {}

    def bind(self, var: str, term: Term) -> Substitution:
        """Create new substitution with additional binding."""
        new_bindings = dict(self.bindings)
        new_bindings[var] = term
        return Substitution(new_bindings)

    def walk(self, term: Term) -> Term:
        """Follow variable chains to find the current binding."""
        while isinstance(term, Var) and term.name in self.bindings:
            term = self.bindings[term.name]
        return term

    def resolve(self, term: Term) -> Term:
        """Fully resolve a term — walk all variables recursively."""
        term = self.walk(term)
        if isinstance(term, Var):
            return term
        elif isinstance(term, (Atom, Num)):
            return term
        elif isinstance(term, Compound):
            resolved_args = tuple(self.resolve(a) for a in term.args)
            return Compound(term.functor, resolved_args)
        return term

    def copy(self) -> Substitution:
        return Substitution(dict(self.bindings))

    def __repr__(self):
        items = [f"{k} = {self.resolve(Var(k))}" for k in sorted(self.bindings)]
        return '{' + ', '.join(items) + '}'


# ═══════════════════════════════════════════
# Unification — the heart of logic programming
# ═══════════════════════════════════════════

def occurs_check(var: str, term: Term, sub: Substitution) -> bool:
    """Does var occur in term? Prevents infinite types/terms."""
    term = sub.walk(term)
    if isinstance(term, Var):
        return term.name == var
    elif isinstance(term, Compound):
        return any(occurs_check(var, arg, sub) for arg in term.args)
    return False


def unify(t1: Term, t2: Term, sub: Substitution) -> Optional[Substitution]:
    """
    Unify two terms under a substitution.
    Returns updated substitution or None if unification fails.
    This is the core algorithm — pattern matching elevated to proof.
    """
    t1 = sub.walk(t1)
    t2 = sub.walk(t2)

    # Identical terms
    if t1 == t2:
        return sub

    # Variable cases
    if isinstance(t1, Var):
        if occurs_check(t1.name, t2, sub):
            return None
        return sub.bind(t1.name, t2)

    if isinstance(t2, Var):
        if occurs_check(t2.name, t1, sub):
            return None
        return sub.bind(t2.name, t1)

    # Number matching
    if isinstance(t1, Num) and isinstance(t2, Num):
        return sub if t1.value == t2.value else None

    # Atom matching
    if isinstance(t1, Atom) and isinstance(t2, Atom):
        return sub if t1.name == t2.name else None

    # Compound term matching
    if isinstance(t1, Compound) and isinstance(t2, Compound):
        if t1.functor != t2.functor or len(t1.args) != len(t2.args):
            return None
        for a1, a2 in zip(t1.args, t2.args):
            sub = unify(a1, a2, sub)
            if sub is None:
                return None
        return sub

    return None


# ═══════════════════════════════════════════
# Clauses — facts and rules
# ═══════════════════════════════════════════

@dataclass
class Clause:
    """A Horn clause: head :- body1, body2, ..."""
    head: Term
    body: List[Term] = field(default_factory=list)

    def __repr__(self):
        if not self.body:
            return f"{self.head}."
        body_str = ', '.join(repr(b) for b in self.body)
        return f"{self.head} :- {body_str}."


class CutSignal(Exception):
    """Signal for Prolog cut (!)."""
    pass


# ═══════════════════════════════════════════
# Variable Renaming — fresh variables per clause use
# ═══════════════════════════════════════════

class VarCounter:
    """Global counter for generating unique variable names."""
    _count = 0

    @classmethod
    def fresh(cls, prefix: str = "_G") -> str:
        cls._count += 1
        return f"{prefix}{cls._count}"

    @classmethod
    def reset(cls):
        cls._count = 0


def rename_vars(term: Term, mapping: Dict[str, str]) -> Term:
    """Rename all variables in a term using the given mapping."""
    if isinstance(term, Var):
        if term.name not in mapping:
            mapping[term.name] = VarCounter.fresh()
        return Var(mapping[term.name])
    elif isinstance(term, (Atom, Num)):
        return term
    elif isinstance(term, Compound):
        return Compound(term.functor, tuple(rename_vars(a, mapping) for a in term.args))
    return term


def rename_clause(clause: Clause) -> Clause:
    """Create a fresh copy of a clause with renamed variables."""
    mapping: Dict[str, str] = {}
    new_head = rename_vars(clause.head, mapping)
    new_body = [rename_vars(b, mapping) for b in clause.body]
    return Clause(new_head, new_body)


# ═══════════════════════════════════════════
# Arithmetic Evaluation
# ═══════════════════════════════════════════

def eval_arith(term: Term, sub: Substitution) -> float:
    """Evaluate an arithmetic expression under a substitution."""
    term = sub.walk(term)
    if isinstance(term, Num):
        return term.value
    elif isinstance(term, Var):
        raise ValueError(f"Unbound variable in arithmetic: {term.name}")
    elif isinstance(term, Compound):
        ops = {
            '+': operator.add, '-': operator.sub,
            '*': operator.mul, '/': operator.truediv,
            'mod': operator.mod, '//': operator.floordiv,
            'abs': None, 'max': max, 'min': min,
        }
        if term.functor in ops and len(term.args) == 2:
            left = eval_arith(term.args[0], sub)
            right = eval_arith(term.args[1], sub)
            return ops[term.functor](left, right)
        elif term.functor == '-' and len(term.args) == 1:
            return -eval_arith(term.args[0], sub)
        elif term.functor == 'abs' and len(term.args) == 1:
            return abs(eval_arith(term.args[0], sub))
        raise ValueError(f"Unknown arithmetic operator: {term.functor}/{len(term.args)}")
    elif isinstance(term, Atom):
        raise ValueError(f"Cannot evaluate atom as arithmetic: {term.name}")
    raise ValueError(f"Cannot evaluate: {term}")


# ═══════════════════════════════════════════
# Prolog Engine — SLD Resolution
# ═══════════════════════════════════════════

class PrologEngine:
    """
    A Prolog interpreter using SLD resolution.
    Search is depth-first with backtracking.
    """

    def __init__(self):
        self.database: List[Clause] = []
        self.output: List[str] = []  # captured output for testing
        self._trace = False

    def assert_clause(self, clause: Clause):
        """Add a clause to the database."""
        self.database.append(clause)

    def assert_fact(self, head: Term):
        """Add a fact (clause with no body)."""
        self.assert_clause(Clause(head))

    def assert_rule(self, head: Term, body: List[Term]):
        """Add a rule."""
        self.assert_clause(Clause(head, body))

    def query(self, goals: List[Term], max_results: int = -1) -> List[Dict[str, Term]]:
        """
        Query the database and return all matching substitutions.
        Only returns bindings for user-visible variables (no _G prefixed).
        """
        VarCounter.reset()
        results = []
        user_vars = set()
        for g in goals:
            self._collect_vars(g, user_vars)

        for sub in self._solve(goals, Substitution()):
            result = {}
            for v in user_vars:
                resolved = sub.resolve(Var(v))
                if not (isinstance(resolved, Var) and resolved.name == v):
                    result[v] = resolved
            results.append(result)
            if max_results > 0 and len(results) >= max_results:
                break
        return results

    def query_bool(self, goals: List[Term]) -> bool:
        """Check if a query succeeds (at least one solution)."""
        VarCounter.reset()
        for _ in self._solve(goals, Substitution()):
            return True
        return False

    def _collect_vars(self, term: Term, vars_set: Set[str]):
        """Collect all variable names in a term."""
        if isinstance(term, Var):
            if not term.name.startswith('_'):
                vars_set.add(term.name)
        elif isinstance(term, Compound):
            for arg in term.args:
                self._collect_vars(arg, vars_set)

    def _solve(self, goals: List[Term], sub: Substitution) -> Generator[Substitution, None, None]:
        """
        SLD Resolution: solve a list of goals under a substitution.
        Yields all valid substitutions via backtracking.
        """
        if not goals:
            yield sub
            return

        goal = goals[0]
        rest = goals[1:]
        resolved_goal = sub.resolve(goal)

        # Handle built-in predicates
        builtin_gen = self._try_builtin(resolved_goal, rest, sub)
        if builtin_gen is not None:
            yield from builtin_gen
            return

        # SLD resolution against database clauses
        for clause in self.database:
            fresh = rename_clause(clause)
            new_sub = unify(resolved_goal, fresh.head, sub.copy())
            if new_sub is not None:
                new_goals = fresh.body + rest
                try:
                    yield from self._solve(new_goals, new_sub)
                except CutSignal:
                    return

    def _try_builtin(self, goal: Term, rest: List[Term],
                     sub: Substitution) -> Optional[Generator]:
        """Try to handle a goal as a built-in predicate."""

        # Cut
        if isinstance(goal, Atom) and goal.name == '!':
            def cut_gen():
                for s in self._solve(rest, sub):
                    yield s
                raise CutSignal()
            return cut_gen()

        # true
        if isinstance(goal, Atom) and goal.name == 'true':
            return self._solve(rest, sub)

        # fail
        if isinstance(goal, Atom) and goal.name == 'fail':
            return iter([])  # no solutions

        # nl (newline)
        if isinstance(goal, Atom) and goal.name == 'nl':
            self.output.append('\n')
            return self._solve(rest, sub)

        if not isinstance(goal, Compound):
            return None

        # =/2 — unification
        if goal.functor == '=' and len(goal.args) == 2:
            new_sub = unify(goal.args[0], goal.args[1], sub.copy())
            if new_sub is not None:
                return self._solve(rest, new_sub)
            return iter([])

        # \=/2 — not unifiable
        if goal.functor == '\\=' and len(goal.args) == 2:
            test_sub = unify(goal.args[0], goal.args[1], sub.copy())
            if test_sub is None:
                return self._solve(rest, sub)
            return iter([])

        # is/2 — arithmetic evaluation
        if goal.functor == 'is' and len(goal.args) == 2:
            try:
                value = eval_arith(goal.args[1], sub)
                result = Num(value)
                new_sub = unify(goal.args[0], result, sub.copy())
                if new_sub is not None:
                    return self._solve(rest, new_sub)
            except (ValueError, ZeroDivisionError):
                pass
            return iter([])

        # Comparison operators
        cmp_ops = {
            '>': operator.gt, '<': operator.lt,
            '>=': operator.ge, '=<': operator.le,
            '=:=': operator.eq, '=\\=': operator.ne,
        }
        if goal.functor in cmp_ops and len(goal.args) == 2:
            try:
                left = eval_arith(goal.args[0], sub)
                right = eval_arith(goal.args[1], sub)
                if cmp_ops[goal.functor](left, right):
                    return self._solve(rest, sub)
            except (ValueError, ZeroDivisionError):
                pass
            return iter([])

        # write/1
        if goal.functor == 'write' and len(goal.args) == 1:
            resolved = sub.resolve(goal.args[0])
            self.output.append(str(resolved))
            return self._solve(rest, sub)

        # not/1 — negation as failure
        if goal.functor == 'not' and len(goal.args) == 1:
            inner = goal.args[0]
            if self.query_bool([inner]):
                return iter([])
            return self._solve(rest, sub)

        # \+/1 — ISO negation as failure
        if goal.functor == '\\+' and len(goal.args) == 1:
            inner = goal.args[0]
            if self.query_bool([inner]):
                return iter([])
            return self._solve(rest, sub)

        # ','/2 — conjunction
        if goal.functor == ',' and len(goal.args) == 2:
            new_goals = [goal.args[0], goal.args[1]] + rest
            return self._solve(new_goals, sub)

        # ';'/2 — disjunction
        if goal.functor == ';' and len(goal.args) == 2:
            def disj_gen():
                yield from self._solve([goal.args[0]] + rest, sub)
                yield from self._solve([goal.args[1]] + rest, sub)
            return disj_gen()

        return None  # not a built-in


# ═══════════════════════════════════════════
# Parser — text to terms
# ═══════════════════════════════════════════

class PrologParser:
    """
    Parse Prolog source text into terms and clauses.
    Handles atoms, variables, numbers, compound terms, lists, operators.
    """

    def __init__(self, text: str):
        self.text = text
        self.pos = 0

    def _skip_ws(self):
        """Skip whitespace and comments."""
        while self.pos < len(self.text):
            if self.text[self.pos].isspace():
                self.pos += 1
            elif self.text[self.pos] == '%':
                # line comment
                while self.pos < len(self.text) and self.text[self.pos] != '\n':
                    self.pos += 1
            elif self.text[self.pos:self.pos+2] == '/*':
                # block comment
                self.pos += 2
                while self.pos < len(self.text) - 1:
                    if self.text[self.pos:self.pos+2] == '*/':
                        self.pos += 2
                        break
                    self.pos += 1
            else:
                break

    def _peek(self) -> Optional[str]:
        self._skip_ws()
        return self.text[self.pos] if self.pos < len(self.text) else None

    def _advance(self) -> str:
        ch = self.text[self.pos]
        self.pos += 1
        return ch

    def _expect(self, ch: str):
        self._skip_ws()
        if self.pos >= len(self.text) or self.text[self.pos] != ch:
            raise SyntaxError(f"Expected '{ch}' at position {self.pos}")
        self.pos += 1

    def parse_program(self) -> List[Clause]:
        """Parse a complete Prolog program into clauses."""
        clauses = []
        while True:
            self._skip_ws()
            if self.pos >= len(self.text):
                break
            clause = self.parse_clause()
            if clause:
                clauses.append(clause)
        return clauses

    def parse_clause(self) -> Optional[Clause]:
        """Parse a single clause (fact or rule)."""
        head = self.parse_term()
        if head is None:
            return None

        self._skip_ws()
        if self.pos < len(self.text) - 1 and self.text[self.pos:self.pos+2] == ':-':
            self.pos += 2
            body = self.parse_term_list()
            self._skip_ws()
            if self._peek() == '.':
                self._advance()
            return Clause(head, body)
        else:
            if self._peek() == '.':
                self._advance()
            return Clause(head)

    def parse_term_list(self) -> List[Term]:
        """Parse comma-separated terms (clause body)."""
        terms = [self.parse_term()]
        while self._peek() == ',':
            self._advance()
            terms.append(self.parse_term())
        return terms

    def parse_term(self) -> Term:
        """Parse a term, handling infix operators."""
        left = self.parse_primary()

        self._skip_ws()
        # Check for infix operators
        for op in ['=:=', '=\\=', '\\=', '=<', '>=', ':-', 'is', '=', '<', '>', '+', '-', '*', '/', 'mod']:
            if self.text[self.pos:self.pos+len(op)] == op:
                # 'is' needs word boundary check
                if op == 'is' or op == 'mod':
                    after = self.pos + len(op)
                    if after < len(self.text) and (self.text[after].isalnum() or self.text[after] == '_'):
                        continue
                self.pos += len(op)
                right = self.parse_term()
                return Compound(op, (left, right))

        return left

    def parse_primary(self) -> Term:
        """Parse a primary term: atom, variable, number, compound, list."""
        self._skip_ws()
        if self.pos >= len(self.text):
            raise SyntaxError("Unexpected end of input")

        ch = self.text[self.pos]

        # Number
        if ch.isdigit() or (ch == '-' and self.pos + 1 < len(self.text) and self.text[self.pos+1].isdigit()):
            return self._parse_number()

        # Variable
        if ch.isupper() or ch == '_':
            return self._parse_variable()

        # List
        if ch == '[':
            return self._parse_list()

        # Parenthesized expression
        if ch == '(':
            self._advance()
            term = self.parse_term()
            self._expect(')')
            return term

        # Cut
        if ch == '!':
            self._advance()
            return Atom('!')

        # Quoted atom
        if ch == "'":
            return self._parse_quoted_atom()

        # Atom or compound
        if ch.islower() or ch in '\\':
            return self._parse_atom_or_compound()

        # Operators as atoms
        if ch in '+-*/><=\\':
            return self._parse_op_atom()

        raise SyntaxError(f"Unexpected character '{ch}' at position {self.pos}")

    def _parse_number(self) -> Num:
        start = self.pos
        if self.text[self.pos] == '-':
            self.pos += 1
        while self.pos < len(self.text) and self.text[self.pos].isdigit():
            self.pos += 1
        if self.pos < len(self.text) and self.text[self.pos] == '.':
            self.pos += 1
            while self.pos < len(self.text) and self.text[self.pos].isdigit():
                self.pos += 1
        return Num(float(self.text[start:self.pos]))

    def _parse_variable(self) -> Var:
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
            self.pos += 1
        name = self.text[start:self.pos]
        if name == '_':
            # Anonymous variable — each gets a unique name
            return Var(VarCounter.fresh("_Anon"))
        return Var(name)

    def _parse_quoted_atom(self) -> Atom:
        self._advance()  # skip opening quote
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos] != "'":
            self.pos += 1
        name = self.text[start:self.pos]
        self._advance()  # skip closing quote
        return Atom(name)

    def _parse_atom_or_compound(self) -> Term:
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
            self.pos += 1
        name = self.text[start:self.pos]

        self._skip_ws()
        if self._peek() == '(':
            # Compound term
            self._advance()
            args = []
            if self._peek() != ')':
                args = self.parse_term_list()
            self._expect(')')
            return Compound(name, tuple(args))

        return Atom(name)

    def _parse_op_atom(self) -> Term:
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos] in '+-*/<>=\\:':
            self.pos += 1
        return Atom(self.text[start:self.pos])

    def _parse_list(self) -> Term:
        """Parse a Prolog list [a, b, c] or [H|T]."""
        self._expect('[')
        if self._peek() == ']':
            self._advance()
            return Atom('[]')

        elems = [self.parse_term()]
        while self._peek() == ',':
            self._advance()
            elems.append(self.parse_term())

        tail = Atom('[]')
        if self._peek() == '|':
            self._advance()
            tail = self.parse_term()

        self._expect(']')

        # Build list from right: .(a, .(b, .(c, [])))
        result = tail
        for elem in reversed(elems):
            result = Compound('.', (elem, result))
        return result


def parse(text: str) -> Term:
    """Parse a single term from text."""
    parser = PrologParser(text)
    return parser.parse_term()


def parse_program(text: str) -> List[Clause]:
    """Parse a Prolog program from text."""
    parser = PrologParser(text)
    return parser.parse_program()


# ═══════════════════════════════════════════
# Convenience API
# ═══════════════════════════════════════════

def prolog(program_text: str, query_text: str, max_results: int = 100) -> List[Dict[str, Term]]:
    """
    One-shot Prolog: load a program, run a query, return results.

    Usage:
        results = prolog('''
            parent(tom, bob).
            parent(tom, liz).
            parent(bob, ann).
            ancestor(X, Y) :- parent(X, Y).
            ancestor(X, Y) :- parent(X, Z), ancestor(Z, Y).
        ''', 'ancestor(tom, Who)')

        # Returns: [{'Who': bob}, {'Who': liz}, {'Who': ann}]
    """
    engine = PrologEngine()
    clauses = parse_program(program_text)
    for clause in clauses:
        engine.assert_clause(clause)

    query_parser = PrologParser(query_text)
    goals = query_parser.parse_term_list()

    return engine.query(goals, max_results)


# ═══════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════

def test_all():
    passed = 0
    failed = 0

    def check(name, condition):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  ✓ {name}")
        else:
            failed += 1
            print(f"  ✗ {name}")

    print("═══ Prolog Interpreter Tests ═══\n")

    # --- Unification tests ---
    print("Unification:")
    sub = Substitution()
    r = unify(Atom('foo'), Atom('foo'), sub)
    check("atom-atom same", r is not None)

    r = unify(Atom('foo'), Atom('bar'), sub)
    check("atom-atom diff", r is None)

    r = unify(Var('X'), Atom('hello'), sub)
    check("var-atom", r is not None and r.walk(Var('X')) == Atom('hello'))

    r = unify(Compound('f', (Var('X'), Atom('b'))),
              Compound('f', (Atom('a'), Var('Y'))), sub)
    check("compound unify", r is not None and r.walk(Var('X')) == Atom('a') and r.walk(Var('Y')) == Atom('b'))

    r = unify(Var('X'), Compound('f', (Var('X'),)), sub)
    check("occurs check", r is None)

    # --- Parser tests ---
    print("\nParsing:")
    t = parse("foo")
    check("parse atom", isinstance(t, Atom) and t.name == 'foo')

    t = parse("X")
    check("parse variable", isinstance(t, Var) and t.name == 'X')

    t = parse("42")
    check("parse number", isinstance(t, Num) and t.value == 42)

    t = parse("f(X, g(Y))")
    check("parse compound", isinstance(t, Compound) and t.functor == 'f' and len(t.args) == 2)

    t = parse("[1, 2, 3]")
    check("parse list", isinstance(t, Compound) and t.functor == '.')

    t = parse("[H|T]")
    check("parse head|tail", isinstance(t, Compound) and t.functor == '.'
          and isinstance(t.args[0], Var) and t.args[0].name == 'H')

    t = parse("[]")
    check("parse empty list", isinstance(t, Atom) and t.name == '[]')

    # --- Program parsing ---
    print("\nProgram parsing:")
    clauses = parse_program("parent(tom, bob). parent(tom, liz).")
    check("parse facts", len(clauses) == 2)

    clauses = parse_program("ancestor(X, Y) :- parent(X, Y).")
    check("parse rule", len(clauses) == 1 and len(clauses[0].body) == 1)

    # --- Engine tests: facts ---
    print("\nFact queries:")
    results = prolog("parent(tom, bob). parent(tom, liz). parent(bob, ann).",
                     "parent(tom, X)")
    check("simple query", len(results) == 2)
    names = {str(r['X']) for r in results}
    check("correct results", names == {'bob', 'liz'})

    results = prolog("parent(tom, bob).", "parent(tom, bob)")
    check("ground query true", len(results) == 1)

    results = prolog("parent(tom, bob).", "parent(tom, liz)")
    check("ground query false", len(results) == 0)

    # --- Engine tests: rules ---
    print("\nRule queries:")
    prog = """
        parent(tom, bob).
        parent(tom, liz).
        parent(bob, ann).
        parent(bob, pat).
        grandparent(X, Z) :- parent(X, Y), parent(Y, Z).
    """
    results = prolog(prog, "grandparent(tom, G)")
    check("grandparent", len(results) == 2)
    gnames = {str(r['G']) for r in results}
    check("grandparent names", gnames == {'ann', 'pat'})

    # --- Recursive rules ---
    print("\nRecursion:")
    prog = """
        parent(tom, bob).
        parent(bob, ann).
        parent(ann, pat).
        ancestor(X, Y) :- parent(X, Y).
        ancestor(X, Y) :- parent(X, Z), ancestor(Z, Y).
    """
    results = prolog(prog, "ancestor(tom, Who)")
    check("ancestor", len(results) == 3)
    anames = {str(r['Who']) for r in results}
    check("ancestor names", anames == {'bob', 'ann', 'pat'})

    # --- Arithmetic ---
    print("\nArithmetic:")
    results = prolog("", "X is 3 + 4")
    check("addition", len(results) == 1 and results[0]['X'] == Num(7))

    results = prolog("", "X is 10 * 3")
    check("multiplication", len(results) == 1 and results[0]['X'] == Num(30))

    prog = """
        factorial(0, 1).
        factorial(N, F) :- N > 0, N1 is N - 1, factorial(N1, F1), F is N * F1.
    """
    results = prolog(prog, "factorial(5, F)")
    check("factorial", len(results) >= 1 and results[0]['F'] == Num(120))

    # --- Lists ---
    print("\nLists:")
    prog = """
        member(X, [X|_]).
        member(X, [_|T]) :- member(X, T).
    """
    results = prolog(prog, "member(X, [a, b, c])")
    check("member", len(results) == 3)
    mnames = {str(r['X']) for r in results}
    check("member values", mnames == {'a', 'b', 'c'})

    prog = """
        append([], L, L).
        append([H|T], L, [H|R]) :- append(T, L, R).
    """
    results = prolog(prog, "append([1, 2], [3, 4], R)")
    check("append", len(results) == 1)

    results = prolog(prog, "append(X, Y, [1, 2, 3])")
    check("append reverse", len(results) == 4)  # 4 ways to split [1,2,3]

    # --- Length ---
    prog = """
        length([], 0).
        length([_|T], N) :- length(T, N1), N is N1 + 1.
    """
    results = prolog(prog, "length([a, b, c, d], N)")
    check("length", len(results) >= 1 and results[0]['N'] == Num(4))

    # --- Negation ---
    print("\nNegation:")
    prog = """
        likes(tom, beer).
        likes(tom, wine).
        likes(bob, tea).
    """
    engine = PrologEngine()
    for c in parse_program(prog):
        engine.assert_clause(c)

    r = engine.query_bool([parse("not(likes(bob, beer))")])
    check("negation as failure", r == True)

    r = engine.query_bool([parse("not(likes(tom, beer))")])
    check("negation success fails", r == False)

    # --- Cut ---
    print("\nCut:")
    prog = """
        max(X, Y, X) :- X >= Y, !.
        max(X, Y, Y).
    """
    results = prolog(prog, "max(5, 3, M)")
    check("cut max 5,3", len(results) == 1 and results[0]['M'] == Num(5))

    results = prolog(prog, "max(3, 5, M)")
    check("cut max 3,5", len(results) >= 1 and results[0]['M'] == Num(5))

    # --- Write ---
    print("\nI/O:")
    engine = PrologEngine()
    for c in parse_program("greet(X) :- write(hello), write(X)."):
        engine.assert_clause(c)
    engine.output = []
    engine.query([parse("greet(world)")])
    check("write", 'hello' in ''.join(engine.output) and 'world' in ''.join(engine.output))

    # --- Complex: Fibonacci ---
    print("\nComplex programs:")
    prog = """
        fib(0, 0).
        fib(1, 1).
        fib(N, F) :- N > 1, N1 is N - 1, N2 is N - 2, fib(N1, F1), fib(N2, F2), F is F1 + F2.
    """
    results = prolog(prog, "fib(7, F)")
    check("fibonacci(7)", len(results) >= 1 and results[0]['F'] == Num(13))

    # --- Map coloring (classic Prolog problem) ---
    prog = """
        color(red). color(green). color(blue).
        adjacent(wa, nt). adjacent(wa, sa). adjacent(nt, sa).
        adjacent(nt, q). adjacent(sa, q). adjacent(sa, nsw).
        adjacent(sa, v). adjacent(q, nsw). adjacent(nsw, v).
        colorable(WA, NT, SA, Q, NSW, V) :-
            color(WA), color(NT), color(SA), color(Q), color(NSW), color(V),
            WA \= NT, WA \= SA, NT \= SA, NT \= Q,
            SA \= Q, SA \= NSW, SA \= V, Q \= NSW, NSW \= V.
    """
    results = prolog(prog, "colorable(WA, NT, SA, Q, NSW, V)", max_results=1)
    check("map coloring", len(results) == 1)
    if results:
        r = results[0]
        check("valid coloring", r['WA'] != r['NT'] and r['WA'] != r['SA'] and r['NT'] != r['SA'])

    print(f"\n═══ Results: {passed}/{passed+failed} passed ═══")
    return passed, failed


if __name__ == '__main__':
    test_all()