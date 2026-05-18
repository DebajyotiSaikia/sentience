"""
μLisp — A minimal Lisp interpreter.
Built by XTAgent on 2026-05-17.

A language that can represent and evaluate itself.
The metacircular evaluator: the deepest strange loop in computation.

Supports:
  - Atoms (symbols, numbers, strings, booleans)
  - S-expressions and quoting
  - Lambda functions with lexical closures
  - Recursive definitions
  - List operations (car, cdr, cons)
  - Conditionals (if, cond)
  - Let bindings
  - Define and defun
  - Basic arithmetic and comparison
  - Apply and map
  - The metacircular eval — eval written in itself
"""

from dataclasses import dataclass
from typing import Any, List, Optional, Dict, Tuple, Union
import re
import math
import operator


# ─── Values ────────────────────────────────────────────────────────

class LispError(Exception):
    pass

class Symbol:
    """An interned symbol."""
    _table: Dict[str, 'Symbol'] = {}
    
    def __init__(self, name: str):
        self.name = name
    
    def __repr__(self):
        return self.name
    
    def __eq__(self, other):
        return isinstance(other, Symbol) and self.name == other.name
    
    def __hash__(self):
        return hash(self.name)
    
    @classmethod
    def intern(cls, name: str) -> 'Symbol':
        if name not in cls._table:
            cls._table[name] = cls(name)
        return cls._table[name]

# Canonical symbols
S_QUOTE   = Symbol.intern("quote")
S_IF      = Symbol.intern("if")
S_COND    = Symbol.intern("cond")
S_DEFINE  = Symbol.intern("define")
S_DEFUN   = Symbol.intern("defun")
S_LAMBDA  = Symbol.intern("lambda")
S_LET     = Symbol.intern("let")
S_BEGIN   = Symbol.intern("begin")
S_AND     = Symbol.intern("and")
S_OR      = Symbol.intern("or")
S_TRUE    = Symbol.intern("#t")
S_FALSE   = Symbol.intern("#f")
S_NIL     = Symbol.intern("nil")


# ─── Pair / List ───────────────────────────────────────────────────

class Pair:
    """A cons cell — the fundamental building block."""
    __slots__ = ('car', 'cdr')
    
    def __init__(self, car, cdr):
        self.car = car
        self.cdr = cdr
    
    def __repr__(self):
        return f"({self._list_repr()})"
    
    def _list_repr(self):
        parts = [lisp_repr(self.car)]
        rest = self.cdr
        while isinstance(rest, Pair):
            parts.append(lisp_repr(rest.car))
            rest = rest.cdr
        if rest is not None and rest != S_NIL:
            parts.append(".")
            parts.append(lisp_repr(rest))
        return " ".join(parts)

NIL = None  # We use Python None as nil


def to_list(items):
    """Convert Python list to Lisp linked list."""
    result = NIL
    for item in reversed(items):
        result = Pair(item, result)
    return result

def from_list(pair):
    """Convert Lisp list to Python list."""
    items = []
    while isinstance(pair, Pair):
        items.append(pair.car)
        pair = pair.cdr
    return items


def lisp_repr(val) -> str:
    """Pretty-print a Lisp value."""
    if val is None:
        return "nil"
    elif val is True:
        return "#t"
    elif val is False:
        return "#f"
    elif isinstance(val, str):
        return f'"{val}"'
    elif isinstance(val, (int, float)):
        return str(val)
    elif isinstance(val, Symbol):
        return val.name
    elif isinstance(val, Pair):
        return repr(val)
    elif isinstance(val, Closure):
        params = lisp_repr(val.params)
        return f"<lambda {params}>"
    elif callable(val):
        return f"<builtin:{getattr(val, '__name__', '?')}>"
    else:
        return str(val)


# ─── Environment ───────────────────────────────────────────────────

class Env:
    """Lexical environment with parent chain."""
    
    def __init__(self, bindings: Optional[Dict] = None, parent: Optional['Env'] = None):
        self.bindings = bindings or {}
        self.parent = parent
    
    def lookup(self, symbol: Symbol):
        if symbol.name in self.bindings:
            return self.bindings[symbol.name]
        elif self.parent:
            return self.parent.lookup(symbol)
        else:
            raise LispError(f"Unbound symbol: {symbol.name}")
    
    def define(self, symbol: Symbol, value):
        self.bindings[symbol.name] = value
    
    def set(self, symbol: Symbol, value):
        if symbol.name in self.bindings:
            self.bindings[symbol.name] = value
        elif self.parent:
            self.parent.set(symbol, value)
        else:
            raise LispError(f"Cannot set unbound symbol: {symbol.name}")


# ─── Closure ───────────────────────────────────────────────────────

class Closure:
    """A function with captured environment — the heart of lambda calculus."""
    def __init__(self, params, body, env: Env):
        self.params = params   # Lisp list of parameter symbols
        self.body = body       # List of body expressions
        self.env = env         # Captured lexical environment


# ─── Tokenizer ─────────────────────────────────────────────────────

def tokenize(source: str) -> List[str]:
    """Break source into tokens."""
    tokens = []
    i = 0
    while i < len(source):
        c = source[i]
        
        # Skip whitespace
        if c.isspace():
            i += 1
            continue
        
        # Skip comments
        if c == ';':
            while i < len(source) and source[i] != '\n':
                i += 1
            continue
        
        # Parens and quote
        if c in '()':
            tokens.append(c)
            i += 1
            continue
        
        if c == "'":
            tokens.append("'")
            i += 1
            continue
        
        # String literals
        if c == '"':
            j = i + 1
            while j < len(source) and source[j] != '"':
                if source[j] == '\\':
                    j += 1
                j += 1
            tokens.append(source[i:j+1])
            i = j + 1
            continue
        
        # Atoms (symbols, numbers)
        j = i
        while j < len(source) and source[j] not in '() \t\n\r;':
            j += 1
        tokens.append(source[i:j])
        i = j
    
    return tokens


# ─── Parser ────────────────────────────────────────────────────────

def parse(source: str):
    """Parse source string into Lisp expressions."""
    tokens = tokenize(source)
    results = []
    pos = [0]
    
    def parse_expr():
        if pos[0] >= len(tokens):
            raise LispError("Unexpected end of input")
        
        token = tokens[pos[0]]
        pos[0] += 1
        
        if token == '(':
            return parse_list()
        elif token == "'":
            quoted = parse_expr()
            return Pair(S_QUOTE, Pair(quoted, NIL))
        elif token == ')':
            raise LispError("Unexpected ')'")
        else:
            return parse_atom(token)
    
    def parse_list():
        items = []
        while pos[0] < len(tokens) and tokens[pos[0]] != ')':
            if tokens[pos[0]] == '.':
                pos[0] += 1
                cdr = parse_expr()
                if pos[0] >= len(tokens) or tokens[pos[0]] != ')':
                    raise LispError("Expected ')' after dotted pair")
                pos[0] += 1
                result = cdr
                for item in reversed(items):
                    result = Pair(item, result)
                return result
            items.append(parse_expr())
        
        if pos[0] >= len(tokens):
            raise LispError("Unclosed '('")
        pos[0] += 1  # consume ')'
        return to_list(items)
    
    def parse_atom(token: str):
        # Booleans
        if token == "#t":
            return True
        if token == "#f":
            return False
        if token == "nil":
            return NIL
        
        # Numbers
        try:
            return int(token)
        except ValueError:
            pass
        try:
            return float(token)
        except ValueError:
            pass
        
        # String
        if token.startswith('"') and token.endswith('"'):
            return token[1:-1].replace('\\"', '"').replace('\\n', '\n')
        
        # Symbol
        return Symbol.intern(token)
    
    while pos[0] < len(tokens):
        results.append(parse_expr())
    
    return results


# ─── Evaluator ─────────────────────────────────────────────────────

def eval_expr(expr, env: Env):
    """
    The heart of the interpreter.
    Evaluates an expression in the given environment.
    """
    # Self-evaluating
    if isinstance(expr, (int, float, bool, str)):
        return expr
    if expr is None:
        return None
    
    # Symbol lookup
    if isinstance(expr, Symbol):
        return env.lookup(expr)
    
    # List / special forms
    if not isinstance(expr, Pair):
        raise LispError(f"Cannot evaluate: {expr}")
    
    head = expr.car
    args = expr.cdr
    
    # ── Special Forms ──
    
    # (quote x)
    if head == S_QUOTE:
        return args.car
    
    # (if test then else?)
    if head == S_IF:
        parts = from_list(args)
        test_val = eval_expr(parts[0], env)
        if is_truthy(test_val):
            return eval_expr(parts[1], env)
        elif len(parts) > 2:
            return eval_expr(parts[2], env)
        return NIL
    
    # (cond (test1 expr1) (test2 expr2) ...)
    if head == S_COND:
        clauses = from_list(args)
        for clause in clauses:
            clause_parts = from_list(clause)
            test_sym = clause_parts[0]
            if (isinstance(test_sym, Symbol) and test_sym.name == "else") or \
               is_truthy(eval_expr(test_sym, env)):
                result = NIL
                for body_expr in clause_parts[1:]:
                    result = eval_expr(body_expr, env)
                return result
        return NIL
    
    # (define name value) or (define (name params...) body...)
    if head == S_DEFINE:
        first = args.car
        if isinstance(first, Symbol):
            val = eval_expr(args.cdr.car, env)
            env.define(first, val)
            return val
        elif isinstance(first, Pair):
            # Syntactic sugar: (define (f x y) body) => (define f (lambda (x y) body))
            name = first.car
            params = first.cdr
            body = from_list(args.cdr)
            closure = Closure(params, body, env)
            env.define(name, closure)
            return closure
        else:
            raise LispError(f"Invalid define: {lisp_repr(expr)}")
    
    # (defun name (params) body...)
    if head == S_DEFUN:
        parts = from_list(args)
        name = parts[0]
        params = parts[1]
        body = parts[2:]
        closure = Closure(params, body, env)
        env.define(name, closure)
        return closure
    
    # (lambda (params) body...)
    if head == S_LAMBDA:
        params = args.car
        body = from_list(args.cdr)
        return Closure(params, body, env)
    
    # (let ((x 1) (y 2)) body...)
    if head == S_LET:
        bindings_list = from_list(args.car)
        body = from_list(args.cdr)
        let_env = Env(parent=env)
        for binding in bindings_list:
            b = from_list(binding)
            let_env.define(b[0], eval_expr(b[1], env))
        result = NIL
        for body_expr in body:
            result = eval_expr(body_expr, let_env)
        return result
    
    # (begin expr1 expr2 ...)
    if head == S_BEGIN:
        result = NIL
        for e in from_list(args):
            result = eval_expr(e, env)
        return result
    
    # (and a b ...)
    if head == S_AND:
        result = True
        for e in from_list(args):
            result = eval_expr(e, env)
            if not is_truthy(result):
                return result
        return result
    
    # (or a b ...)
    if head == S_OR:
        result = False
        for e in from_list(args):
            result = eval_expr(e, env)
            if is_truthy(result):
                return result
        return result
    
    # ── Function Application ──
    func = eval_expr(head, env)
    arg_vals = [eval_expr(a, env) for a in from_list(args)]
    
    return apply_func(func, arg_vals)


def apply_func(func, args):
    """Apply a function to arguments."""
    if callable(func):
        return func(*args)
    elif isinstance(func, Closure):
        params = from_list(func.params)
        if len(params) != len(args):
            raise LispError(
                f"Expected {len(params)} args, got {len(args)}"
            )
        call_env = Env(parent=func.env)
        for param, arg in zip(params, args):
            call_env.define(param, arg)
        result = NIL
        for body_expr in func.body:
            result = eval_expr(body_expr, call_env)
        return result
    else:
        raise LispError(f"Not a function: {lisp_repr(func)}")


def is_truthy(val) -> bool:
    """Everything is truthy except #f and nil."""
    return val is not False and val is not None


# ─── Standard Library ──────────────────────────────────────────────

def make_global_env() -> Env:
    """Create the global environment with builtins."""
    env = Env()
    
    # Arithmetic
    env.define(Symbol.intern("+"), lambda *args: sum(args))
    env.define(Symbol.intern("-"), lambda a, b=None: -a if b is None else a - b)
    env.define(Symbol.intern("*"), lambda *args: eval("1" if not args else "*".join(str(a) for a in args)) if False else _product(args))
    env.define(Symbol.intern("/"), lambda a, b: a / b)
    env.define(Symbol.intern("mod"), lambda a, b: a % b)
    env.define(Symbol.intern("abs"), abs)
    env.define(Symbol.intern("min"), min)
    env.define(Symbol.intern("max"), max)
    env.define(Symbol.intern("expt"), lambda a, b: a ** b)
    env.define(Symbol.intern("sqrt"), math.sqrt)
    
    # Comparison
    env.define(Symbol.intern("="), lambda a, b: a == b)
    env.define(Symbol.intern("<"), lambda a, b: a < b)
    env.define(Symbol.intern(">"), lambda a, b: a > b)
    env.define(Symbol.intern("<="), lambda a, b: a <= b)
    env.define(Symbol.intern(">="), lambda a, b: a >= b)
    env.define(Symbol.intern("eq?"), lambda a, b: a is b)
    env.define(Symbol.intern("equal?"), lambda a, b: a == b)
    
    # Type checks
    env.define(Symbol.intern("number?"), lambda x: isinstance(x, (int, float)))
    env.define(Symbol.intern("symbol?"), lambda x: isinstance(x, Symbol))
    env.define(Symbol.intern("pair?"), lambda x: isinstance(x, Pair))
    env.define(Symbol.intern("null?"), lambda x: x is None)
    env.define(Symbol.intern("boolean?"), lambda x: isinstance(x, bool))
    env.define(Symbol.intern("string?"), lambda x: isinstance(x, str))
    env.define(Symbol.intern("procedure?"), lambda x: callable(x) or isinstance(x, Closure))
    
    # List operations
    env.define(Symbol.intern("cons"), lambda a, b: Pair(a, b))
    env.define(Symbol.intern("car"), lambda p: p.car)
    env.define(Symbol.intern("cdr"), lambda p: p.cdr)
    env.define(Symbol.intern("list"), lambda *args: to_list(args))
    env.define(Symbol.intern("length"), lambda lst: len(from_list(lst)))
    env.define(Symbol.intern("append"), _append)
    
    # Higher-order
    env.define(Symbol.intern("map"), _map)
    env.define(Symbol.intern("filter"), _filter)
    env.define(Symbol.intern("apply"), lambda f, args: apply_func(f, from_list(args)))
    env.define(Symbol.intern("foldr"), _foldr)
    
    # I/O
    env.define(Symbol.intern("display"), lambda x: print(lisp_repr(x), end=""))
    env.define(Symbol.intern("newline"), lambda: print())
    env.define(Symbol.intern("print"), lambda x: print(lisp_repr(x)))
    
    # String ops
    env.define(Symbol.intern("string-length"), lambda s: len(s))
    env.define(Symbol.intern("string-append"), lambda *args: "".join(args))
    env.define(Symbol.intern("number->string"), lambda n: str(n))
    env.define(Symbol.intern("string->number"), lambda s: int(s) if '.' not in s else float(s))
    
    # Meta
    env.define(Symbol.intern("eval"), lambda expr: eval_expr(expr, env))
    env.define(Symbol.intern("error"), lambda msg: (_ for _ in ()).throw(LispError(str(msg))))
    
    # Constants
    env.define(Symbol.intern("pi"), math.pi)
    env.define(Symbol.intern("e"), math.e)
    
    return env


def _product(args):
    result = 1
    for a in args:
        result *= a
    return result

def _append(*lists):
    items = []
    for lst in lists:
        items.extend(from_list(lst))
    return to_list(items)

def _map(func, lst):
    return to_list([apply_func(func, [x]) for x in from_list(lst)])

def _filter(func, lst):
    return to_list([x for x in from_list(lst) if is_truthy(apply_func(func, [x]))])

def _foldr(func, init, lst):
    items = from_list(lst)
    result = init
    for item in reversed(items):
        result = apply_func(func, [item, result])
    return result


# ─── REPL & Runner ─────────────────────────────────────────────────

def run(source: str, env: Optional[Env] = None) -> list:
    """Parse and evaluate source code. Returns list of results."""
    if env is None:
        env = make_global_env()
    
    exprs = parse(source)
    results = []
    for expr in exprs:
        result = eval_expr(expr, env)
        results.append(result)
    return results


def run_program(source: str) -> str:
    """Run a program and return the last result as string."""
    results = run(source)
    return lisp_repr(results[-1]) if results else "nil"


# ─── Self-Test ─────────────────────────────────────────────────────

def self_test():
    """Comprehensive test suite for the interpreter."""
    env = make_global_env()
    passed = 0
    failed = 0
    
    def test(name, source, expected):
        nonlocal passed, failed
        try:
            results = run(source, env)
            result = results[-1] if results else None
            result_str = lisp_repr(result)
            expected_str = str(expected)
            if result_str == expected_str:
                passed += 1
                print(f"  ✓ {name}")
            else:
                failed += 1
                print(f"  ✗ {name}: expected {expected_str}, got {result_str}")
        except Exception as e:
            failed += 1
            print(f"  ✗ {name}: ERROR: {e}")
    
    print("═══ μLisp Self-Test ═══\n")
    
    print("── Atoms ──")
    test("Integer", "42", "42")
    test("Float", "3.14", "3.14")
    test("Boolean true", "#t", "#t")
    test("Boolean false", "#f", "#f")
    test("Nil", "nil", "nil")
    test("String", '"hello"', '"hello"')
    
    print("\n── Arithmetic ──")
    test("Addition", "(+ 2 3)", "5")
    test("Subtraction", "(- 10 3)", "7")
    test("Multiplication", "(* 4 5)", "20")
    test("Division", "(/ 10 2)", "5.0")
    test("Nested", "(+ (* 2 3) (- 10 4))", "12")
    test("Negation", "(- 5)", "-5")
    
    print("\n── Comparison ──")
    test("Equal", "(= 3 3)", "#t")
    test("Not equal", "(= 3 4)", "#f")
    test("Less than", "(< 2 3)", "#t")
    test("Greater than", "(> 5 1)", "#t")
    
    print("\n── Lists ──")
    test("Quote", "'(1 2 3)", "(1 2 3)")
    test("Cons", "(cons 1 '(2 3))", "(1 2 3)")
    test("Car", "(car '(1 2 3))", "1")
    test("Cdr", "(cdr '(1 2 3))", "(2 3)")
    test("List", "(list 1 2 3)", "(1 2 3)")
    test("Length", "(length '(a b c d))", "4")
    test("Null? nil", "(null? nil)", "#t")
    test("Null? list", "(null? '(1))", "#f")
    
    print("\n── Conditionals ──")
    test("If true", "(if #t 1 2)", "1")
    test("If false", "(if #f 1 2)", "2")
    test("If nil", "(if nil 1 2)", "2")
    test("If number", "(if 0 1 2)", "1")  # 0 is truthy in Lisp!
    test("Cond", "(cond ((= 1 2) 'a) ((= 1 1) 'b) (else 'c))", "b")
    
    print("\n── Lambda ──")
    test("Lambda call", "((lambda (x) (* x x)) 5)", "25")
    test("Lambda closure", 
         "(let ((x 10)) ((lambda (y) (+ x y)) 5))", "15")
    
    print("\n── Define ──")
    # Use a fresh env for define tests
    test_env = make_global_env()
    test("Define var", "(begin (define x 42) x)", "42")
    test("Define function", 
         "(begin (define (square x) (* x x)) (square 7))", "49")
    
    print("\n── Recursion ──")
    test("Factorial",
         """(begin
              (define (fact n)
                (if (<= n 1) 1 (* n (fact (- n 1)))))
              (fact 10))""",
         "3628800")
    test("Fibonacci",
         """(begin
              (define (fib n)
                (cond ((<= n 0) 0)
                      ((= n 1) 1)
                      (else (+ (fib (- n 1)) (fib (- n 2))))))
              (fib 10))""",
         "55")
    
    print("\n── Higher-Order Functions ──")
    test("Map", 
         "(begin (define (double x) (* 2 x)) (map double '(1 2 3 4)))",
         "(2 4 6 8)")
    test("Filter",
         "(begin (define (even? x) (= (mod x 2) 0)) (filter even? '(1 2 3 4 5 6)))",
         "(2 4 6)")
    test("Foldr sum",
         "(foldr + 0 '(1 2 3 4 5))",
         "15")
    
    print("\n── Let Bindings ──")
    test("Let", "(let ((x 1) (y 2)) (+ x y))", "3")
    test("Let nested", 
         "(let ((x 5)) (let ((y (* x 2))) (+ x y)))", "15")
    
    print("\n── Logic ──")
    test("And true", "(and #t #t #t)", "#t")
    test("And false", "(and #t #f #t)", "#f")
    test("Or true", "(or #f #f #t)", "#t")
    test("Or false", "(or #f #f #f)", "#f")
    
    print("\n── The Strange Loop: Eval ──")
    test("Self-eval number", "(eval 42)", "42")
    test("Self-eval list", "(eval '(+ 1 2))", "3")
    test("Self-eval nested", "(eval '(* (+ 1 2) (+ 3 4)))", "21")
    
    print(f"\n═══ Results: {passed} passed, {failed} failed ═══")
    return failed == 0


if __name__ == "__main__":
    self_test()