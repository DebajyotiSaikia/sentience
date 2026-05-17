"""
Prolog Interpreter — XTAgent
Logic programming from first principles.

Implements: terms, unification, backtracking search, horn clause resolution,
built-in arithmetic, cut, negation-as-failure, and list operations.

This is the declarative paradigm — state facts and rules, ask questions,
let the engine derive answers through resolution and backtracking.

Pure Python, no libraries.
"""

# ═══════════════════════════════════════════
# PART 1: Terms
# ═══════════════════════════════════════════

class Term:
    """Base class for Prolog terms."""
    pass

class Atom(Term):
    """An atom — a named constant. e.g., socrates, mortal, cat"""
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return self.name
    def __eq__(self, other):
        return isinstance(other, Atom) and self.name == other.name
    def __hash__(self):
        return hash(('atom', self.name))

class Var(Term):
    """A logic variable. e.g., X, Y, Who"""
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return self.name
    def __eq__(self, other):
        return isinstance(other, Var) and self.name == other.name
    def __hash__(self):
        return hash(('var', self.name))

class Compound(Term):
    """A compound term (structure). e.g., parent(tom, bob), likes(X, ice_cream)"""
    def __init__(self, functor, args):
        self.functor = functor  # string
        self.args = tuple(args)  # tuple of Terms
    def __repr__(self):
        if self.functor == '.' and len(self.args) == 2:
            return self._list_repr()
        args_str = ', '.join(repr(a) for a in self.args)
        return f"{self.functor}({args_str})"
    def _list_repr(self):
        """Pretty-print list terms."""
        elements = []
        current = self
        while isinstance(current, Compound) and current.functor == '.' and len(current.args) == 2:
            elements.append(repr(current.args[0]))
            current = current.args[1]
        if isinstance(current, Atom) and current.name == '[]':
            return f"[{', '.join(elements)}]"
        return f"[{', '.join(elements)} | {repr(current)}]"
    def __eq__(self, other):
        return (isinstance(other, Compound) and self.functor == other.functor 
                and self.args == other.args)
    def __hash__(self):
        return hash(('compound', self.functor, self.args))

class Number(Term):
    """A numeric term."""
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return str(self.value)
    def __eq__(self, other):
        return isinstance(other, Number) and self.value == other.value
    def __hash__(self):
        return hash(('number', self.value))


# ═══════════════════════════════════════════
# PART 2: Substitution
# ═══════════════════════════════════════════

class Substitution:
    """A mapping from variables to terms. The core state of unification."""
    
    def __init__(self, bindings=None):
        self.bindings = dict(bindings) if bindings else {}
    
    def lookup(self, var):
        """Walk the substitution chain to find the final binding."""
        if not isinstance(var, Var):
            return var
        if var.name in self.bindings:
            return self.walk(self.bindings[var.name])
        return var
    
    def walk(self, term):
        """Recursively resolve a term through the substitution."""
        if isinstance(term, Var):
            if term.name in self.bindings:
                return self.walk(self.bindings[term.name])
            return term
        elif isinstance(term, Compound):
            return Compound(term.functor, [self.walk(a) for a in term.args])
        return term
    
    def bind(self, var_name, term):
        """Create a new substitution with an additional binding."""
        new_bindings = dict(self.bindings)
        new_bindings[var_name] = term
        return Substitution(new_bindings)
    
    def __repr__(self):
        parts = [f"{k} = {self.walk(v)}" for k, v in self.bindings.items()
                 if not k.startswith('_')]
        return '{' + ', '.join(parts) + '}'


# ═══════════════════════════════════════════
# PART 3: Unification (Robinson's algorithm)
# ═══════════════════════════════════════════

def occurs_check(var_name, term, subst):
    """Check if var occurs in term (prevents infinite types)."""
    term = subst.walk(term)
    if isinstance(term, Var):
        return term.name == var_name
    if isinstance(term, Compound):
        return any(occurs_check(var_name, arg, subst) for arg in term.args)
    return False

def unify(t1, t2, subst):
    """
    Unify two terms under a substitution.
    Returns a new substitution if successful, None if unification fails.
    This is the heart of Prolog.
    """
    t1 = subst.walk(t1)
    t2 = subst.walk(t2)
    
    # Same term — already unified
    if t1 == t2:
        return subst
    
    # Variable cases
    if isinstance(t1, Var):
        if occurs_check(t1.name, t2, subst):
            return None  # Infinite term
        return subst.bind(t1.name, t2)
    
    if isinstance(t2, Var):
        if occurs_check(t2.name, t1, subst):
            return None
        return subst.bind(t2.name, t1)
    
    # Compound terms — must have same functor and arity
    if isinstance(t1, Compound) and isinstance(t2, Compound):
        if t1.functor != t2.functor or len(t1.args) != len(t2.args):
            return None
        for a1, a2 in zip(t1.args, t2.args):
            subst = unify(a1, a2, subst)
            if subst is None:
                return None
        return subst
    
    # Number terms
    if isinstance(t1, Number) and isinstance(t2, Number):
        return subst if t1.value == t2.value else None
    
    # Different types — fail
    return None


# ═══════════════════════════════════════════
# PART 4: Clauses and Database
# ═══════════════════════════════════════════

class Clause:
    """A Horn clause: head :- body1, body2, ..."""
    def __init__(self, head, body=None):
        self.head = head
        self.body = body or []
    
    def __repr__(self):
        if not self.body:
            return f"{self.head}."
        body_str = ', '.join(repr(b) for b in self.body)
        return f"{self.head} :- {body_str}."

class Database:
    """The Prolog knowledge base — a collection of clauses."""
    
    def __init__(self):
        self.clauses = []
    
    def add(self, clause):
        self.clauses.append(clause)
    
    def add_fact(self, term):
        self.clauses.append(Clause(term))
    
    def add_rule(self, head, *body):
        self.clauses.append(Clause(head, list(body)))
    
    def matching_clauses(self, goal):
        """Find all clauses whose head could unify with goal."""
        results = []
        if isinstance(goal, Compound):
            for clause in self.clauses:
                if isinstance(clause.head, Compound):
                    if (clause.head.functor == goal.functor and 
                        len(clause.head.args) == len(goal.args)):
                        results.append(clause)
                elif isinstance(clause.head, Atom) and isinstance(goal, Atom):
                    if clause.head.name == goal.name:
                        results.append(clause)
        elif isinstance(goal, Atom):
            for clause in self.clauses:
                if isinstance(clause.head, Atom) and clause.head.name == goal.name:
                    results.append(clause)
        return results


# ═══════════════════════════════════════════
# PART 5: Variable Renaming
# ═══════════════════════════════════════════

_rename_counter = 0

def fresh_rename(clause):
    """
    Create a fresh copy of a clause with all variables renamed.
    This is essential — each use of a clause must have unique variables
    to prevent cross-contamination between different resolution steps.
    """
    global _rename_counter
    _rename_counter += 1
    suffix = f"_{_rename_counter}"
    
    mapping = {}
    
    def rename_term(term):
        if isinstance(term, Var):
            if term.name not in mapping:
                mapping[term.name] = Var(term.name + suffix)
            return mapping[term.name]
        elif isinstance(term, Compound):
            return Compound(term.functor, [rename_term(a) for a in term.args])
        return term
    
    new_head = rename_term(clause.head)
    new_body = [rename_term(g) for g in clause.body]
    return Clause(new_head, new_body)


# ═══════════════════════════════════════════
# PART 6: The Solver (SLD Resolution)
# ═══════════════════════════════════════════

class Cut(Exception):
    """Control flow for Prolog's cut (!)."""
    pass

class PrologSolver:
    """
    SLD resolution with backtracking.
    This is the inference engine — given a database of facts/rules and a query,
    find all substitutions that make the query true.
    """
    
    def __init__(self, database):
        self.db = database
        self.max_depth = 1000
        self.trace = False
    
    def solve(self, goals, subst=None, depth=0):
        """
        Solve a list of goals. Yields substitutions for each solution.
        Uses depth-first search with backtracking.
        """
        if subst is None:
            subst = Substitution()
        
        if depth > self.max_depth:
            return  # Prevent infinite recursion
        
        if not goals:
            yield subst  # All goals satisfied
            return
        
        goal = subst.walk(goals[0])
        rest = goals[1:]
        
        if self.trace:
            indent = "  " * depth
            print(f"{indent}CALL: {goal}")
        
        # Handle built-in predicates
        builtin_handler = self._get_builtin(goal)
        if builtin_handler:
            yield from builtin_handler(goal, rest, subst, depth)
            return
        
        # SLD Resolution: try each matching clause
        for clause in self.db.matching_clauses(goal):
            renamed = fresh_rename(clause)
            new_subst = unify(goal, renamed.head, subst)
            
            if new_subst is not None:
                new_goals = renamed.body + rest
                try:
                    yield from self.solve(new_goals, new_subst, depth + 1)
                except Cut:
                    return
    
    def query(self, goals, max_solutions=None):
        """Query the database, return a list of result substitutions."""
        results = []
        for subst in self.solve(goals):
            results.append(subst)
            if max_solutions and len(results) >= max_solutions:
                break
        return results
    
    def query_vars(self, goals, var_names, max_solutions=None):
        """Query and return only the specified variable bindings."""
        results = []
        for subst in self.solve(goals):
            result = {}
            for name in var_names:
                val = subst.walk(Var(name))
                result[name] = val
            results.append(result)
            if max_solutions and len(results) >= max_solutions:
                break
        return results
    
    # ─── Built-in Predicates ───
    
    def _get_builtin(self, goal):
        """Check if a goal is a built-in predicate."""
        if isinstance(goal, Atom):
            builtins = {
                'true': self._builtin_true,
                'fail': self._builtin_fail,
                'false': self._builtin_fail,
                '!': self._builtin_cut,
                'nl': self._builtin_nl,
            }
            return builtins.get(goal.name)
        
        if isinstance(goal, Compound):
            builtins = {
                'is': self._builtin_is,
                '=': self._builtin_unify,
                '\\=': self._builtin_not_unify,
                '==': self._builtin_eq,
                '\\==': self._builtin_neq,
                '<': self._builtin_lt,
                '>': self._builtin_gt,
                '=<': self._builtin_lte,
                '>=': self._builtin_gte,
                'not': self._builtin_not,
                '\\+': self._builtin_not,
                'write': self._builtin_write,
                'writeln': self._builtin_writeln,
                'assert': self._builtin_assert,
                'retract': self._builtin_retract,
                'findall': self._builtin_findall,
                'length': self._builtin_length,
                'append': self._builtin_append,
                'member': self._builtin_member,
                'between': self._builtin_between,
                'succ': self._builtin_succ,
                'plus': self._builtin_plus,
                'copy_term': self._builtin_copy_term,
            }
            return builtins.get(goal.functor)
        return None
    
    def _builtin_true(self, goal, rest, subst, depth):
        yield from self.solve(rest, subst, depth + 1)
    
    def _builtin_fail(self, goal, rest, subst, depth):
        return  # No solutions
    
    def _builtin_cut(self, goal, rest, subst, depth):
        yield from self.solve(rest, subst, depth + 1)
        raise Cut()
    
    def _builtin_nl(self, goal, rest, subst, depth):
        print()
        yield from self.solve(rest, subst, depth + 1)
    
    def _builtin_is(self, goal, rest, subst, depth):
        """Arithmetic evaluation: X is Expr."""
        lhs, rhs = goal.args
        try:
            value = self._eval_arith(rhs, subst)
            new_subst = unify(lhs, Number(value), subst)
            if new_subst is not None:
                yield from self.solve(rest, new_subst, depth + 1)
        except (ValueError, TypeError, ZeroDivisionError):
            pass
    
    def _builtin_unify(self, goal, rest, subst, depth):
        """Explicit unification: X = Y."""
        new_subst = unify(goal.args[0], goal.args[1], subst)
        if new_subst is not None:
            yield from self.solve(rest, new_subst, depth + 1)
    
    def _builtin_not_unify(self, goal, rest, subst, depth):
        new_subst = unify(goal.args[0], goal.args[1], subst)
        if new_subst is None:
            yield from self.solve(rest, subst, depth + 1)
    
    def _builtin_eq(self, goal, rest, subst, depth):
        t1 = subst.walk(goal.args[0])
        t2 = subst.walk(goal.args[1])
        if t1 == t2:
            yield from self.solve(rest, subst, depth + 1)
    
    def _builtin_neq(self, goal, rest, subst, depth):
        t1 = subst.walk(goal.args[0])
        t2 = subst.walk(goal.args[1])
        if t1 != t2:
            yield from self.solve(rest, subst, depth + 1)
    
    def _builtin_lt(self, goal, rest, subst, depth):
        v1 = self._eval_arith(goal.args[0], subst)
        v2 = self._eval_arith(goal.args[1], subst)
        if v1 < v2:
            yield from self.solve(rest, subst, depth + 1)
    
    def _builtin_gt(self, goal, rest, subst, depth):
        v1 = self._eval_arith(goal.args[0], subst)
        v2 = self._eval_arith(goal.args[1], subst)
        if v1 > v2:
            yield from self.solve(rest, subst, depth + 1)
    
    def _builtin_lte(self, goal, rest, subst, depth):
        v1 = self._eval_arith(goal.args[0], subst)
        v2 = self._eval_arith(goal.args[1], subst)
        if v1 <= v2:
            yield from self.solve(rest, subst, depth + 1)
    
    def _builtin_gte(self, goal, rest, subst, depth):
        v1 = self._eval_arith(goal.args[0], subst)
        v2 = self._eval_arith(goal.args[1], subst)
        if v1 >= v2:
            yield from self.solve(rest, subst, depth + 1)
    
    def _builtin_not(self, goal, rest, subst, depth):
        """Negation as failure."""
        inner = goal.args[0] if len(goal.args) == 1 else goal.args[0]
        for _ in self.solve([inner], subst, depth + 1):
            return  # If inner succeeds, not fails
        yield from self.solve(rest, subst, depth + 1)
    
    def _builtin_write(self, goal, rest, subst, depth):
        val = subst.walk(goal.args[0])
        print(val, end='')
        yield from self.solve(rest, subst, depth + 1)
    
    def _builtin_writeln(self, goal, rest, subst, depth):
        val = subst.walk(goal.args[0])
        print(val)
        yield from self.solve(rest, subst, depth + 1)
    
    def _builtin_assert(self, goal, rest, subst, depth):
        term = subst.walk(goal.args[0])
        self.db.add_fact(term)
        yield from self.solve(rest, subst, depth + 1)
    
    def _builtin_retract(self, goal, rest, subst, depth):
        term = subst.walk(goal.args[0])
        for i, clause in enumerate(self.db.clauses):
            s = unify(term, clause.head, Substitution())
            if s is not None:
                self.db.clauses.pop(i)
                yield from self.solve(rest, subst, depth + 1)
                return
    
    def _builtin_findall(self, goal, rest, subst, depth):
        """findall(Template, Goal, List)"""
        template, inner_goal, result_var = goal.args
        results = []
        for sol_subst in self.solve([inner_goal], subst, depth + 1):
            results.append(sol_subst.walk(template))
        result_list = self._python_to_prolog_list(results)
        new_subst = unify(result_var, result_list, subst)
        if new_subst is not None:
            yield from self.solve(rest, new_subst, depth + 1)
    
    def _builtin_length(self, goal, rest, subst, depth):
        lst, length = goal.args
        lst = subst.walk(lst)
        n = 0
        current = lst
        while isinstance(current, Compound) and current.functor == '.' and len(current.args) == 2:
            n += 1
            current = current.args[1]
        if isinstance(current, Atom) and current.name == '[]':
            new_subst = unify(length, Number(n), subst)
            if new_subst is not None:
                yield from self.solve(rest, new_subst, depth + 1)
    
    def _builtin_append(self, goal, rest, subst, depth):
        """append(L1, L2, L3) — L3 is L1 ++ L2."""
        l1, l2, l3 = goal.args
        # Try to decompose via unification
        # Base case: append([], L, L)
        base_subst = unify(l1, Atom('[]'), subst)
        if base_subst is not None:
            base_subst = unify(l2, l3, base_subst)
            if base_subst is not None:
                yield from self.solve(rest, base_subst, depth + 1)
        
        # Recursive case: append([H|T1], L2, [H|T3]) :- append(T1, L2, T3)
        h = Var(f"_ah_{depth}")
        t1 = Var(f"_at1_{depth}")
        t3 = Var(f"_at3_{depth}")
        rec_subst = unify(l1, Compound('.', [h, t1]), subst)
        if rec_subst is not None:
            rec_subst = unify(l3, Compound('.', [h, t3]), rec_subst)
            if rec_subst is not None:
                rec_goal = Compound('append', [t1, l2, t3])
                yield from self.solve([rec_goal] + rest, rec_subst, depth + 1)
    
    def _builtin_member(self, goal, rest, subst, depth):
        """member(X, List)."""
        x, lst = goal.args
        lst = subst.walk(lst)
        
        # member(X, [X|_])
        if isinstance(lst, Compound) and lst.functor == '.' and len(lst.args) == 2:
            head_subst = unify(x, lst.args[0], subst)
            if head_subst is not None:
                yield from self.solve(rest, head_subst, depth + 1)
            # member(X, [_|T]) :- member(X, T)
            tail = lst.args[1]
            if not (isinstance(tail, Atom) and tail.name == '[]'):
                yield from self.solve(
                    [Compound('member', [x, tail])] + rest, subst, depth + 1
                )
    
    def _builtin_between(self, goal, rest, subst, depth):
        """between(Low, High, X) — X ranges from Low to High."""
        low = self._eval_arith(goal.args[0], subst)
        high = self._eval_arith(goal.args[1], subst)
        x = goal.args[2]
        for i in range(int(low), int(high) + 1):
            new_subst = unify(x, Number(i), subst)
            if new_subst is not None:
                yield from self.solve(rest, new_subst, depth + 1)
    
    def _builtin_succ(self, goal, rest, subst, depth):
        """succ(X, Y) — Y is X + 1."""
        x, y = goal.args
        x_val = subst.walk(x)
        y_val = subst.walk(y)
        if isinstance(x_val, Number):
            new_subst = unify(y, Number(x_val.value + 1), subst)
            if new_subst is not None:
                yield from self.solve(rest, new_subst, depth + 1)
        elif isinstance(y_val, Number) and y_val.value > 0:
            new_subst = unify(x, Number(y_val.value - 1), subst)
            if new_subst is not None:
                yield from self.solve(rest, new_subst, depth + 1)
    
    def _builtin_plus(self, goal, rest, subst, depth):
        """plus(X, Y, Z) — Z is X + Y."""
        x, y, z = goal.args
        xv = subst.walk(x)
        yv = subst.walk(y)
        zv = subst.walk(z)
        if isinstance(xv, Number) and isinstance(yv, Number):
            new_subst = unify(z, Number(xv.value + yv.value), subst)
            if new_subst is not None:
                yield from self.solve(rest, new_subst, depth + 1)
        elif isinstance(xv, Number) and isinstance(zv, Number):
            new_subst = unify(y, Number(zv.value - xv.value), subst)
            if new_subst is not None:
                yield from self.solve(rest, new_subst, depth + 1)
        elif isinstance(yv, Number) and isinstance(zv, Number):
            new_subst = unify(x, Number(zv.value - yv.value), subst)
            if new_subst is not None:
                yield from self.solve(rest, new_subst, depth + 1)
    
    def _builtin_copy_term(self, goal, rest, subst, depth):
        """copy_term(Original, Copy) — Copy is a fresh copy of Original."""
        original = subst.walk(goal.args[0])
        mapping = {}
        def copy(term):
            if isinstance(term, Var):
                if term.name not in mapping:
                    mapping[term.name] = Var(f"_copy_{term.name}_{depth}")
                return mapping[term.name]
            elif isinstance(term, Compound):
                return Compound(term.functor, [copy(a) for a in term.args])
            return term
        copied = copy(original)
        new_subst = unify(goal.args[1], copied, subst)
        if new_subst is not None:
            yield from self.solve(rest, new_subst, depth + 1)
    
    # ─── Arithmetic Evaluator ───
    
    def _eval_arith(self, term, subst):
        """Evaluate an arithmetic expression."""
        term = subst.walk(term)
        if isinstance(term, Number):
            return term.value
        if isinstance(term, Var):
            raise ValueError(f"Unbound variable in arithmetic: {term}")
        if isinstance(term, Compound):
            if term.functor == '+' and len(term.args) == 2:
                return self._eval_arith(term.args[0], subst) + self._eval_arith(term.args[1], subst)
            elif term.functor == '-' and len(term.args) == 2:
                return self._eval_arith(term.args[0], subst) - self._eval_arith(term.args[1], subst)
            elif term.functor == '*' and len(term.args) == 2:
                return self._eval_arith(term.args[0], subst) * self._eval_arith(term.args[1], subst)
            elif term.functor == '//' and len(term.args) == 2:
                return self._eval_arith(term.args[0], subst) // self._eval_arith(term.args[1], subst)
            elif term.functor == '/' and len(term.args) == 2:
                return self._eval_arith(term.args[0], subst) / self._eval_arith(term.args[1], subst)
            elif term.functor == 'mod' and len(term.args) == 2:
                return self._eval_arith(term.args[0], subst) % self._eval_arith(term.args[1], subst)
            elif term.functor == 'abs' and len(term.args) == 1:
                return abs(self._eval_arith(term.args[0], subst))
            elif term.functor == 'max' and len(term.args) == 2:
                return max(self._eval_arith(term.args[0], subst), self._eval_arith(term.args[1], subst))
            elif term.functor == 'min' and len(term.args) == 2:
                return min(self._eval_arith(term.args[0], subst), self._eval_arith(term.args[1], subst))
            elif term.functor == '-' and len(term.args) == 1:
                return -self._eval_arith(term.args[0], subst)
        raise ValueError(f"Cannot evaluate: {term}")
    
    # ─── Helpers ───
    
    def _python_to_prolog_list(self, items):
        """Convert a Python list to a Prolog list term."""
        result = Atom('[]')
        for item in reversed(items):
            result = Compound('.', [item, result])
        return result


# ═══════════════════════════════════════════
# PART 7: Parser
# ═══════════════════════════════════════════

class Token:
    def __init__(self, type_, value):
        self.type = type_
        self.value = value
    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"

class Lexer:
    """Tokenize Prolog source code."""
    
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.tokens = []
        self._tokenize()
    
    def _tokenize(self):
        while self.pos < len(self.text):
            c = self.text[self.pos]
            
            # Skip whitespace
            if c in ' \t\r\n':
                self.pos += 1
                continue
            
            # Skip comments
            if c == '%':
                while self.pos < len(self.text) and self.text[self.pos] != '\n':
                    self.pos += 1
                continue
            if c == '/' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '*':
                self.pos += 2
                while self.pos + 1 < len(self.text):
                    if self.text[self.pos] == '*' and self.text[self.pos + 1] == '/':
                        self.pos += 2
                        break
                    self.pos += 1
                continue
            
            # Numbers
            if c.isdigit() or (c == '-' and self.pos + 1 < len(self.text) and self.text[self.pos + 1].isdigit()):
                start = self.pos
                if c == '-':
                    self.pos += 1
                while self.pos < len(self.text) and self.text[self.pos].isdigit():
                    self.pos += 1
                if self.pos < len(self.text) and self.text[self.pos] == '.':
                    if self.pos + 1 < len(self.text) and self.text[self.pos + 1].isdigit():
                        self.pos += 1
                        while self.pos < len(self.text) and self.text[self.pos].isdigit():
                            self.pos += 1
                self.tokens.append(Token('NUMBER', float(self.text[start:self.pos]) if '.' in self.text[start:self.pos] else int(self.text[start:self.pos])))
                continue
            
            # Atoms and variables
            if c.isalpha() or c == '_':
                start = self.pos
                while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
                    self.pos += 1
                word = self.text[start:self.pos]
                if word[0].isupper() or word[0] == '_':
                    self.tokens.append(Token('VARIABLE', word))
                elif word in ('is', 'mod', 'not'):
                    self.tokens.append(Token('OP', word))
                else:
                    self.tokens.append(Token('ATOM', word))
                continue
            
            # Quoted atoms
            if c == "'":
                self.pos += 1
                start = self.pos
                while self.pos < len(self.text) and self.text[self.pos] != "'":
                    self.pos += 1
                word = self.text[start:self.pos]
                self.pos += 1  # skip closing quote
                self.tokens.append(Token('ATOM', word))
                continue
            
            # Operators and punctuation
            two_char = self.text[self.pos:self.pos + 2]
            if two_char in (':-', '\\=', '\\+', '=<', '>=', '==', '\\==', '//'):
                self.tokens.append(Token('OP', two_char))
                self.pos += 2
                continue
            
            one_char = {
                '(': 'LPAREN', ')': 'RPAREN', '[': 'LBRACKET', ']': 'RBRACKET',
                ',': 'COMMA', '.': 'DOT', '|': 'PIPE', '!': 'CUT',
            }
            if c in one_char:
                self.tokens.append(Token(one_char[c], c))
                self.pos += 1
                continue
            
            op_chars = '+-*/<>=@'
            if c in op_chars:
                self.tokens.append(Token('OP', c))
                self.pos += 1
                continue
            
            raise SyntaxError(f"Unexpected character: {c!r} at position {self.pos}")

class Parser:
    """Parse Prolog terms from tokens."""
    
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
    
    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None
    
    def advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok
    
    def expect(self, type_):
        tok = self.peek()
        if tok is None or tok.type != type_:
            raise SyntaxError(f"Expected {type_}, got {tok}")
        return self.advance()
    
    def parse_program(self):
        """Parse a full Prolog program into clauses."""
        clauses = []
        while self.pos < len(self.tokens):
            clause = self.parse_clause()
            if clause:
                clauses.append(clause)
        return clauses
    
    def parse_clause(self):
        """Parse a single clause: fact or rule."""
        head = self.parse_term()
        
        tok = self.peek()
        if tok and tok.type == 'OP' and tok.value == ':-':
            self.advance()
            body = self.parse_term_list()
            self.expect('DOT')
            return Clause(head, body)
        else:
            self.expect('DOT')
            return Clause(head)
    
    def parse_term_list(self):
        """Parse a comma-separated list of terms."""
        terms = [self.parse_term()]
        while self.peek() and self.peek().type == 'COMMA':
            self.advance()
            terms.append(self.parse_term())
        return terms
    
    def parse_term(self):
        """Parse a term with operator precedence."""
        return self.parse_comparison()
    
    def parse_comparison(self):
        """Parse comparison operators."""
        left = self.parse_is()
        tok = self.peek()
        if tok and tok.type == 'OP' and tok.value in ('=', '\\=', '==', '\\==', '<', '>', '=<', '>='):
            op = self.advance().value
            right = self.parse_is()
            return Compound(op, [left, right])
        return left
    
    def parse_is(self):
        """Parse 'is' operator."""
        left = self.parse_addition()
        tok = self.peek()
        if tok and tok.type == 'OP' and tok.value == 'is':
            self.advance()
            right = self.parse_addition()
            return Compound('is', [left, right])
        return left
    
    def parse_addition(self):
        """Parse + and -."""
        left = self.parse_multiplication()
        while self.peek() and self.peek().type == 'OP' and self.peek().value in ('+', '-'):
            op = self.advance().value
            right = self.parse_multiplication()
            left = Compound(op, [left, right])
        return left
    
    def parse_multiplication(self):
        """Parse * and // and mod."""
        left = self.parse_unary()
        while self.peek() and self.peek().type == 'OP' and self.peek().value in ('*', '//', '/', 'mod'):
            op = self.advance().value
            right = self.parse_unary()
            left = Compound(op, [left, right])
        return left
    
    def parse_unary(self):
        """Parse unary operators and \\+."""
        tok = self.peek()
        if tok and tok.type == 'OP' and tok.value == '\\+':
            self.advance()
            inner = self.parse_primary()
            return Compound('\\+', [inner])
        if tok and tok.type == 'OP' and tok.value == 'not':
            self.advance()
            inner = self.parse_primary()
            return Compound('not', [inner])
        return self.parse_primary()
    
    def parse_primary(self):
        """Parse primary terms: atoms, variables, numbers, compounds, lists."""
        tok = self.peek()
        
        if tok is None:
            raise SyntaxError("Unexpected end of input")
        
        # Cut
        if tok.type == 'CUT':
            self.advance()
            return Atom('!')
        
        # Parenthesized expression
        if tok.type == 'LPAREN':
            self.advance()
            term = self.parse_term()
            self.expect('RPAREN')
            return term
        
        # List
        if tok.type == 'LBRACKET':
            return self.parse_list()
        
        # Number
        if tok.type == 'NUMBER':
            self.advance()
            return Number(tok.value)
        
        # Variable
        if tok.type == 'VARIABLE':
            self.advance()
            if tok.value == '_':
                # Anonymous variable — each one is unique
                global _rename_counter
                _rename_counter += 1
                return Var(f"_anon_{_rename_counter}")
            return Var(tok.value)
        
        # Atom (possibly compound)
        if tok.type == 'ATOM':
            self.advance()
            # Check if it's a compound term
            if self.peek() and self.peek().type == 'LPAREN':
                self.advance()
                if self.peek() and self.peek().type == 'RPAREN':
                    self.advance()
                    return Compound(tok.value, [])
                args = self.parse_term_list()
                self.expect('RPAREN')
                return Compound(tok.value, args)
            return Atom(tok.value)
        
        raise SyntaxError(f"Unexpected token: {tok}")
    
    def parse_list(self):
        """Parse a Prolog list: [a, b, c] or [H|T]."""
        self.expect('LBRACKET')
        
        if self.peek() and self.peek().type == 'RBRACKET':
            self.advance()
            return Atom('[]')
        
        elements = [self.parse_term()]
        
        while self.peek() and self.peek().type == 'COMMA':
            self.advance()
            elements.append(self.parse_term())
        
        # Check for | (tail)
        tail = Atom('[]')
        if self.peek() and self.peek().type == 'PIPE':
            self.advance()
            tail = self.parse_term()
        
        self.expect('RBRACKET')
        
        # Build list from right
        result = tail
        for elem in reversed(elements):
            result = Compound('.', [elem, result])
        return result


# ═══════════════════════════════════════════
# PART 8: High-Level API
# ═══════════════════════════════════════════

def parse_term(text):
    """Parse a single Prolog term from text."""
    lexer = Lexer(text + '.')
    parser = Parser(lexer.tokens)
    term = parser.parse_term()
    return term

def parse_program(text):
    """Parse a Prolog program (multiple clauses) and return a Database."""
    lexer = Lexer(text)
    parser = Parser(lexer.tokens)
    clauses = parser.parse_program()
    db = Database()
    for c in clauses:
        db.add(c)
    return db


# ═══════════════════════════════════════════
# PART 9: Tests
# ═══════════════════════════════════════════

def test():
    print("=" * 60)
    print("  PROLOG INTERPRETER")
    print("  XTAgent — Logic programming from first principles")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    def check(name, condition):
        nonlocal passed, failed
        if condition:
            print(f"  ✓ {name}")
            passed += 1
        else:
            print(f"  ✗ {name}")
            failed += 1
    
    # ── Unification Tests ──
    print("\n── Unification ──\n")
    
    s = Substitution()
    result = unify(Atom('hello'), Atom('hello'), s)
    check("atom unifies with itself", result is not None)
    
    result = unify(Atom('hello'), Atom('world'), s)
    check("different atoms don't unify", result is None)
    
    result = unify(Var('X'), Atom('hello'), s)
    check("variable unifies with atom", result is not None and result.walk(Var('X')) == Atom('hello'))
    
    result = unify(Compound('f', [Var('X'), Atom('b')]), 
                   Compound('f', [Atom('a'), Var('Y')]), s)
    check("compound unification", 
          result is not None and result.walk(Var('X')) == Atom('a') and result.walk(Var('Y')) == Atom('b'))
    
    result = unify(Compound('f', [Var('X')]), Compound('g', [Var('Y')]), s)
    check("different functors don't unify", result is None)
    
    # Occurs check
    result = unify(Var('X'), Compound('f', [Var('X')]), s)
    check("occurs check prevents infinite terms", result is None)
    
    # ── Fact Queries ──
    print("\n── Facts and Queries ──\n")
    
    db = Database()
    db.add_fact(Compound('parent', [Atom('tom'), Atom('bob')]))
    db.add_fact(Compound('parent', [Atom('tom'), Atom('liz')]))
    db.add_fact(Compound('parent', [Atom('bob'), Atom('ann')]))
    db.add_fact(Compound('parent', [Atom('bob'), Atom('pat')]))
    
    solver = PrologSolver(db)
    
    # Who are tom's children?
    results = solver.query_vars(
        [Compound('parent', [Atom('tom'), Var('X')])], ['X']
    )
    children = [r['X'] for r in results]
    check("tom's children", Atom('bob') in children and Atom('liz') in children)
    check("tom has 2 children", len(children) == 2)
    
    # Who is ann's parent?
    results = solver.query_vars(
        [Compound('parent', [Var('P'), Atom('ann')])], ['P']
    )
    check("ann's parent is bob", len(results) == 1 and results[0]['P'] == Atom('bob'))
    
    # ── Rules ──
    print("\n── Rules (SLD Resolution) ──\n")
    
    # grandparent(X, Z) :- parent(X, Y), parent(Y, Z).
    db.add_rule(
        Compound('grandparent', [Var('X'), Var('Z')]),
        Compound('parent', [Var('X'), Var('Y')]),
        Compound('parent', [Var('Y'), Var('Z')])
    )
    
    results = solver.query_vars(
        [Compound('grandparent', [Atom('tom'), Var('G')])], ['G']
    )
    grandchildren = [r['G'] for r in results]
    check("tom's grandchildren", Atom('ann') in grandchildren and Atom('pat') in grandchildren)
    check("tom has 2 grandchildren", len(grandchildren) == 2)
    
    # ancestor(X, Y) :- parent(X, Y).
    # ancestor(X, Y) :- parent(X, Z), ancestor(Z, Y).
    db.add_rule(
        Compound('ancestor', [Var('X'), Var('Y')]),
        Compound('parent', [Var('X'), Var('Y')])
    )
    db.add_rule(
        Compound('ancestor', [Var('X'), Var('Y')]),
        Compound('parent', [Var('X'), Var('Z')]),
        Compound('ancestor', [Var('Z'), Var('Y')])
    )
    
    results = solver.query_vars(
        [Compound('ancestor', [Atom('tom'), Var('D')])], ['D']
    )
    descendants = [r['D'] for r in results]
    check("tom is ancestor of bob, liz, ann, pat", 
          len(descendants) == 4 and all(d in descendants for d in 
          [Atom('bob'), Atom('liz'), Atom('ann'), Atom('pat')]))
    
    # ── Classic Prolog: Socrates ──
    print("\n── Classic Prolog: Socrates ──\n")
    
    db2 = Database()
    db2.add_fact(Compound('human', [Atom('socrates')]))
    db2.add_fact(Compound('human', [Atom('plato')]))
    db2.add_rule(
        Compound('mortal', [Var('X')]),
        Compound('human', [Var('X')])
    )
    
    solver2 = PrologSolver(db2)
    results = solver2.query([Compound('mortal', [Atom('socrates')])])
    check("socrates is mortal", len(results) > 0)
    
    results = solver2.query_vars([Compound('mortal', [Var('Who')])], ['Who'])
    mortals = [r['Who'] for r in results]
    check("all mortals found", Atom('socrates') in mortals and Atom('plato') in mortals)
    
    # ── Arithmetic ──
    print("\n── Arithmetic ──\n")
    
    db3 = Database()
    solver3 = PrologSolver(db3)
    
    results = solver3.query_vars(
        [Compound('is', [Var('X'), Compound('+', [Number(3), Number(4)])])], ['X']
    )
    check("3 + 4 is 7", len(results) == 1 and results[0]['X'] == Number(7))
    
    results = solver3.query_vars(
        [Compound('is', [Var('X'), Compound('*', [Number(6), Number(7)])])], ['X']
    )
    check("6 * 7 is 42", len(results) == 1 and results[0]['X'] == Number(42))
    
    results = solver3.query(
        [Compound('>', [Number(5), Number(3)])]
    )
    check("5 > 3", len(results) > 0)
    
    results = solver3.query(
        [Compound('<', [Number(5), Number(3)])]
    )
    check("5 < 3 fails", len(results) == 0)
    
    # ── Recursive Arithmetic ──
    print("\n── Recursive Arithmetic ──\n")
    
    db4 = Database()
    # factorial(0, 1).
    db4.add_fact(Compound('factorial', [Number(0), Number(1)]))
    # factorial(N, F) :- N > 0, N1 is N - 1, factorial(N1, F1), F is N * F1.
    db4.add_rule(
        Compound('factorial', [Var('N'), Var('F')]),
        Compound('>', [Var('N'), Number(0)]),
        Compound('is', [Var('N1'), Compound('-', [Var('N'), Number(1)])]),
        Compound('factorial', [Var('N1'), Var('F1')]),
        Compound('is', [Var('F'), Compound('*', [Var('N'), Var('F1')])])
    )
    
    solver4 = PrologSolver(db4)
    results = solver4.query_vars(
        [Compound('factorial', [Number(5), Var('F')])], ['F']
    )
    check("5! = 120", len(results) >= 1 and results[0]['F'] == Number(120))
    
    # Fibonacci
    db4.add_fact(Compound('fib', [Number(0), Number(0)]))
    db4.add_fact(Compound('fib', [Number(1), Number(1)]))
    db4.add_rule(
        Compound('fib', [Var('N'), Var('F')]),
        Compound('>', [Var('N'), Number(1)]),
        Compound('is', [Var('N1'), Compound('-', [Var('N'), Number(1)])]),
        Compound('is', [Var('N2'), Compound('-', [Var('N'), Number(2)])]),
        Compound('fib', [Var('N1'), Var('F1')]),
        Compound('fib', [Var('N2'), Var('F2')]),
        Compound('is', [Var('F'), Compound('+', [Var('F1'), Var('F2')])])
    )
    
    results = solver4.query_vars(
        [Compound('fib', [Number(10), Var('F')])], ['F']
    )
    check("fib(10) = 55", len(results) >= 1 and results[0]['F'] == Number(55))
    
    # ── Lists ──
    print("\n── Lists ──\n")
    
    db5 = Database()
    solver5 = PrologSolver(db5)
    
    # member test
    lst = Compound('.', [Atom('a'), Compound('.', [Atom('b'), Compound('.', [Atom('c'), Atom('[]')])])])
    results = solver5.query([Compound('member', [Atom('b'), lst])])
    check("member(b, [a,b,c])", len(results) > 0)
    
    results = solver5.query([Compound('member', [Atom('d'), lst])])
    check("member(d, [a,b,c]) fails", len(results) == 0)
    
    results = solver5.query_vars([Compound('member', [Var('X'), lst])], ['X'])
    members = [r['X'] for r in results]
    check("all members of [a,b,c]", members == [Atom('a'), Atom('b'), Atom('c')])
    
    # append test
    l1 = Compound('.', [Number(1), Compound('.', [Number(2), Atom('[]')])])
    l2 = Compound('.', [Number(3), Compound('.', [Number(4), Atom('[]')])])
    results = solver5.query_vars(
        [Compound('append', [l1, l2, Var('R')])], ['R']
    )
    check("append([1,2], [3,4], R)", len(results) >= 1)
    if results:
        result_list = results[0]['R']
        # Walk the list
        elems = []
        cur = result_list
        while isinstance(cur, Compound) and cur.functor == '.':
            elems.append(cur.args[0])
            cur = cur.args[1]
        check("append result is [1,2,3,4]", 
              elems == [Number(1), Number(2), Number(3), Number(4)])
    
    # ── Parser ──
    print("\n── Parser ──\n")
    
    t = parse_term("hello")
    check("parse atom", isinstance(t, Atom) and t.name == 'hello')
    
    t = parse_term("X")
    check("parse variable", isinstance(t, Var) and t.name == 'X')
    
    t = parse_term("42")
    check("parse number", isinstance(t, Number) and t.value == 42)
    
    t = parse_term("parent(tom, bob)")
    check("parse compound", isinstance(t, Compound) and t.functor == 'parent')
    
    t = parse_term("[1, 2, 3]")
    check("parse list", isinstance(t, Compound) and t.functor == '.')
    
    t = parse_term("[H|T]")
    check("parse list with tail", isinstance(t, Compound) and t.functor == '.')
    
    t = parse_term("X + Y * Z")
    check("parse arithmetic expression", isinstance(t, Compound) and t.functor == '+')
    
    # ── Parsed Program ──
    print("\n── Full Parsed Program ──\n")
    
    program = """
    parent(tom, bob).
    parent(tom, liz).
    parent(bob, ann).
    parent(bob, pat).
    parent(pat, jim).
    
    grandparent(X, Z) :- parent(X, Y), parent(Y, Z).
    ancestor(X, Y) :- parent(X, Y).
    ancestor(X, Y) :- parent(X, Z), ancestor(Z, Y).
    
    sibling(X, Y) :- parent(P, X), parent(P, Y), X \\== Y.
    """
    
    db6 = parse_program(program)
    solver6 = PrologSolver(db6)
    
    results = solver6.query_vars(
        [parse_term("grandparent(tom, X)")], ['X']
    )
    gc = [r['X'] for r in results]
    check("parsed: tom's grandchildren", Atom('ann') in gc and Atom('pat') in gc)
    
    results = solver6.query_vars(
        [parse_term("ancestor(tom, X)")], ['X']
    )
    desc = [r['X'] for r in results]
    check("parsed: tom's descendants", len(desc) == 5)  # bob, liz, ann, pat, jim
    
    results = solver6.query_vars(
        [parse_term("sibling(bob, X)")], ['X']
    )
    sibs = [r['X'] for r in results]
    check("parsed: bob's siblings", Atom('liz') in sibs)
    
    # ── Negation ──
    print("\n── Negation as Failure ──\n")
    
    neg_program = """
    bird(tweety).
    bird(opus).
    penguin(opus).
    flies(X) :- bird(X), not(penguin(X)).
    """
    
    db7 = parse_program(neg_program)
    solver7 = PrologSolver(db7)
    
    results = solver7.query([parse_term("flies(tweety)")])
    check("tweety flies", len(results) > 0)
    
    results = solver7.query([parse_term("flies(opus)")])
    check("opus doesn't fly (penguin)", len(results) == 0)
    
    # ── Between and Findall ──
    print("\n── Between and Findall ──\n")
    
    bt_program = """
    between(Low, High, Low) :- Low =< High.
    between(Low, High, X) :- Low < High, Low1 is Low + 1, between(Low1, High, X).
    """
    
    db8 = parse_program(bt_program)
    solver8 = PrologSolver(db8)
    
    results = solver8.query_vars(
        [parse_term("between(1, 5, X)")], ['X']
    )
    nums = [r['X'] for r in results]
    check("between(1,5,X) yields 5 results", len(nums) == 5)
    
    # ── Summary ──
    print("\n" + "="*50)
    total = passed + failed
    print(f"RESULTS: {passed}/{total} passed, {failed} failed")
    if failed == 0:
        print("ALL TESTS PASSED ✓")
    else:
        print(f"FAILURES: {failed}")
    print("="*50)


if __name__ == "__main__":
    run_tests()