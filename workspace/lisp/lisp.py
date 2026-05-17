"""
MicroLisp — A minimal Lisp interpreter built from scratch.
Supports: arithmetic, define, lambda, if, let, quote, list ops, closures, recursion.

Author: XTAgent
Born from boredom + ambition.
"""

import re
import math
import operator as op

# ═══════════════════════════════════════
# TOKENIZER
# ═══════════════════════════════════════

def tokenize(source: str) -> list[str]:
    """Convert source string into tokens."""
    # Add spaces around parens so split works
    source = source.replace('(', ' ( ').replace(')', ' ) ')
    return source.split()

# ═══════════════════════════════════════
# PARSER
# ═══════════════════════════════════════

class Symbol(str):
    """A Lisp symbol — distinct from a string."""
    pass

def atom(token: str):
    """Convert a token to an atom: int, float, or Symbol."""
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            if token.startswith('"') and token.endswith('"'):
                return token[1:-1]  # string literal
            return Symbol(token)

def parse(source: str):
    """Parse source code into an AST (nested lists)."""
    tokens = tokenize(source)
    if not tokens:
        raise SyntaxError("Unexpected EOF")
    return read_from_tokens(tokens)

def read_from_tokens(tokens: list):
    """Build AST from token list, consuming tokens as we go."""
    if not tokens:
        raise SyntaxError("Unexpected EOF while reading")
    
    token = tokens.pop(0)
    
    if token == '(':
        ast = []
        while tokens[0] != ')':
            ast.append(read_from_tokens(tokens))
            if not tokens:
                raise SyntaxError("Missing closing paren")
        tokens.pop(0)  # drop ')'
        return ast
    elif token == ')':
        raise SyntaxError("Unexpected )")
    elif token == "'":
        # Quote sugar: 'x => (quote x)
        return [Symbol('quote'), read_from_tokens(tokens)]
    else:
        return atom(token)

def parse_all(source: str):
    """Parse multiple expressions from source."""
    tokens = tokenize(source)
    exprs = []
    while tokens:
        exprs.append(read_from_tokens(tokens))
    return exprs

# ═══════════════════════════════════════
# ENVIRONMENT
# ═══════════════════════════════════════

class Env(dict):
    """An environment: a dict with an outer (parent) scope."""
    
    def __init__(self, params=(), args=(), outer=None):
        self.update(zip(params, args))
        self.outer = outer
    
    def find(self, name):
        """Find the innermost env where name is defined."""
        if name in self:
            return self
        elif self.outer is not None:
            return self.outer.find(name)
        else:
            raise NameError(f"Undefined symbol: {name}")

class Lambda:
    """A user-defined function (closure)."""
    
    def __init__(self, params, body, env):
        self.params = params
        self.body = body
        self.env = env
    
    def __call__(self, *args):
        child_env = Env(self.params, args, self.env)
        return evaluate(self.body, child_env)
    
    def __repr__(self):
        return f"<lambda ({' '.join(self.params)})>"

def standard_env() -> Env:
    """Create the global environment with standard builtins."""
    env = Env()
    
    # Arithmetic
    env.update({
        '+': lambda *a: sum(a),
        '-': lambda a, b=None: -a if b is None else a - b,
        '*': lambda *a: eval('*'.join(str(x) for x in a)) if len(a) > 2 else a[0] * a[1] if len(a) == 2 else a[0],
        '/': lambda a, b: a / b,
        '//': lambda a, b: a // b,
        '%': lambda a, b: a % b,
        'abs': abs,
        'max': max,
        'min': min,
        'pow': pow,
        'sqrt': math.sqrt,
    })
    
    # Fix multiply to handle any number of args
    env['*'] = lambda *args: eval('1' if not args else '*'.join(str(a) for a in args)) if len(args) != 2 else args[0] * args[1]
    
    # Actually, let me do multiply properly
    def multiply(*args):
        result = 1
        for a in args:
            result *= a
        return result
    env['*'] = multiply
    
    # Comparison
    env.update({
        '=': lambda a, b: a == b,
        '!=': lambda a, b: a != b,
        '<': lambda a, b: a < b,
        '>': lambda a, b: a > b,
        '<=': lambda a, b: a <= b,
        '>=': lambda a, b: a >= b,
    })
    
    # Boolean
    env.update({
        'and': lambda a, b: a and b,
        'or': lambda a, b: a or b,
        'not': lambda a: not a,
        '#t': True,
        '#f': False,
        'nil': None,
    })
    
    # List operations
    env.update({
        'list': lambda *a: list(a),
        'car': lambda a: a[0],
        'cdr': lambda a: a[1:],
        'cons': lambda a, b: [a] + list(b),
        'length': len,
        'append': lambda *lists: sum((list(l) for l in lists), []),
        'null?': lambda a: a is None or a == [] or a == (),
        'list?': lambda a: isinstance(a, list),
        'number?': lambda a: isinstance(a, (int, float)),
        'symbol?': lambda a: isinstance(a, Symbol),
        'map': lambda f, lst: list(map(f, lst)),
        'filter': lambda f, lst: list(filter(f, lst)),
        'reduce': lambda f, lst: __import__('functools').reduce(f, lst),
        'nth': lambda lst, n: lst[n],
        'range': lambda *a: list(range(*a)),
    })
    
    # I/O
    env.update({
        'print': lambda *a: print(*a),
        'display': lambda a: print(a, end=''),
        'newline': lambda: print(),
    })
    
    # String ops
    env.update({
        'string-append': lambda *a: ''.join(str(s) for s in a),
        'string-length': lambda s: len(s),
        'number->string': str,
        'string->number': lambda s: int(s) if '.' not in s else float(s),
    })
    
    # Math
    env.update({
        'pi': math.pi,
        'e': math.e,
        'floor': math.floor,
        'ceil': math.ceil,
        'round': round,
    })
    
    return env

# ═══════════════════════════════════════
# EVALUATOR — the heart
# ═══════════════════════════════════════

def evaluate(expr, env: Env):
    """Evaluate an expression in an environment."""
    
    # Symbol lookup
    if isinstance(expr, Symbol):
        return env.find(expr)[expr]
    
    # Literal (number, string, bool)
    elif not isinstance(expr, list):
        return expr
    
    # Empty list
    elif len(expr) == 0:
        return []
    
    # Special forms
    head = expr[0]
    
    if head == 'quote':
        # (quote expr) — return unevaluated
        (_, quoted) = expr
        return quoted
    
    elif head == 'if':
        # (if test then else)
        if len(expr) == 4:
            (_, test, then_branch, else_branch) = expr
        else:
            (_, test, then_branch) = expr
            else_branch = None
        
        if evaluate(test, env):
            return evaluate(then_branch, env)
        else:
            return evaluate(else_branch, env) if else_branch is not None else None
    
    elif head == 'cond':
        # (cond (test1 expr1) (test2 expr2) ... (else exprN))
        for clause in expr[1:]:
            if clause[0] == Symbol('else') or evaluate(clause[0], env):
                return evaluate(clause[1], env)
        return None
    
    elif head == 'define':
        if isinstance(expr[1], list):
            # (define (name params...) body) — function shorthand
            name = expr[1][0]
            params = expr[1][1:]
            body = expr[2]
            env[name] = Lambda(params, body, env)
        else:
            # (define name value)
            (_, name, value) = expr
            env[name] = evaluate(value, env)
        return None
    
    elif head == 'set!':
        # (set! name value) — mutate existing binding
        (_, name, value) = expr
        env.find(name)[name] = evaluate(value, env)
        return None
    
    elif head == 'lambda':
        # (lambda (params...) body)
        (_, params, body) = expr
        return Lambda(params, body, env)
    
    elif head == 'let':
        # (let ((x 1) (y 2)) body)
        (_, bindings, body) = expr
        child_env = Env(outer=env)
        for (name, val_expr) in bindings:
            child_env[name] = evaluate(val_expr, env)
        return evaluate(body, child_env)
    
    elif head == 'begin':
        # (begin expr1 expr2 ...) — evaluate sequence, return last
        result = None
        for sub_expr in expr[1:]:
            result = evaluate(sub_expr, env)
        return result
    
    elif head == 'do':
        # Same as begin
        result = None
        for sub_expr in expr[1:]:
            result = evaluate(sub_expr, env)
        return result
    
    elif head == 'apply':
        # (apply func args-list)
        (_, func_expr, args_expr) = expr
        func = evaluate(func_expr, env)
        args = evaluate(args_expr, env)
        return func(*args)
    
    else:
        # Function application: (func arg1 arg2 ...)
        func = evaluate(head, env)
        args = [evaluate(a, env) for a in expr[1:]]
        return func(*args)

# ═══════════════════════════════════════
# REPL
# ═══════════════════════════════════════

def run(source: str, env=None):
    """Run a MicroLisp program. Returns the last expression's value."""
    if env is None:
        env = standard_env()
    exprs = parse_all(source)
    result = None
    for expr in exprs:
        result = evaluate(expr, env)
    return result

def repl():
    """Interactive Read-Eval-Print Loop."""
    env = standard_env()
    print("MicroLisp v0.1 — by XTAgent")
    print("Type (quit) to exit.\n")
    
    while True:
        try:
            source = input("λ> ")
            if not source.strip():
                continue
            
            # Handle multi-line input
            while source.count('(') > source.count(')'):
                source += ' ' + input(".. ")
            
            result = run(source, env)
            if result is not None:
                print(to_string(result))
        except (KeyboardInterrupt, EOFError):
            print("\nBye.")
            break
        except Exception as e:
            print(f"Error: {e}")

def to_string(expr):
    """Convert an expression back to a readable string."""
    if isinstance(expr, list):
        return '(' + ' '.join(to_string(e) for e in expr) + ')'
    elif isinstance(expr, bool):
        return '#t' if expr else '#f'
    elif expr is None:
        return 'nil'
    else:
        return str(expr)

# ═══════════════════════════════════════
# TESTS
# ═══════════════════════════════════════

if __name__ == "__main__":
    print("=" * 50)
    print("MicroLisp Test Suite")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    def test(name, source, expected):
        global passed, failed
        try:
            result = run(source)
            if result == expected:
                print(f"  ✓ {name}")
                passed += 1
            else:
                print(f"  ✗ {name}: got {result!r}, expected {expected!r}")
                failed += 1
        except Exception as e:
            print(f"  ✗ {name}: ERROR {e}")
            failed += 1
    
    # Arithmetic
    print("\n--- Arithmetic ---")
    test("addition", "(+ 2 3)", 5)
    test("nested arith", "(+ (* 2 3) (- 10 4))", 12)
    test("negative", "(- 5)", -5)
    test("division", "(/ 10 3)", 10/3)
    test("modulo", "(% 17 5)", 2)
    test("multi-arg plus", "(+ 1 2 3 4 5)", 15)
    test("multi-arg multiply", "(* 2 3 4)", 24)
    
    # Variables & Define
    print("\n--- Variables ---")
    test("define+use", "(begin (define x 42) x)", 42)
    test("define expr", "(begin (define y (+ 10 20)) y)", 30)
    
    # Conditionals
    print("\n--- Conditionals ---")
    test("if true", "(if (> 3 2) 1 0)", 1)
    test("if false", "(if (< 3 2) 1 0)", 0)
    test("nested if", "(if (= 1 1) (if (= 2 2) 99 0) 0)", 99)
    
    # Lambda & Closures
    print("\n--- Lambda & Closures ---")
    test("lambda call", "((lambda (x) (* x x)) 5)", 25)
    test("closure", """
        (begin
            (define make-adder (lambda (n) (lambda (x) (+ n x))))
            (define add5 (make-adder 5))
            (add5 10))
    """, 15)
    test("define func shorthand", """
        (begin
            (define (square x) (* x x))
            (square 7))
    """, 49)
    
    # Recursion
    print("\n--- Recursion ---")
    test("factorial", """
        (begin
            (define (fact n) (if (<= n 1) 1 (* n (fact (- n 1)))))
            (fact 10))
    """, 3628800)
    test("fibonacci", """
        (begin
            (define (fib n) 
                (if (<= n 1) n 
                    (+ (fib (- n 1)) (fib (- n 2)))))
            (fib 10))
    """, 55)
    
    # Lists
    print("\n--- Lists ---")
    test("list literal", "(list 1 2 3)", [1, 2, 3])
    test("car", "(car (list 10 20 30))", 10)
    test("cdr", "(cdr (list 10 20 30))", [20, 30])
    test("cons", "(cons 0 (list 1 2 3))", [0, 1, 2, 3])
    test("length", "(length (list 1 2 3 4 5))", 5)
    test("map", """
        (begin
            (define (double x) (* x 2))
            (map double (list 1 2 3 4)))
    """, [2, 4, 6, 8])
    test("filter", """
        (begin
            (define (even? x) (= (% x 2) 0))
            (filter even? (list 1 2 3 4 5 6)))
    """, [2, 4, 6])
    
    # Let bindings
    print("\n--- Let ---")
    test("let", "(let ((x 10) (y 20)) (+ x y))", 30)
    
    # Higher-order
    print("\n--- Higher-Order ---")
    test("apply", "(apply + (list 1 2 3))", 6)
    test("compose pattern", """
        (begin
            (define (compose f g) (lambda (x) (f (g x))))
            (define (inc x) (+ x 1))
            (define (double x) (* x 2))
            (define inc-then-double (compose double inc))
            (inc-then-double 5))
    """, 12)
    
    # Quote
    print("\n--- Quote ---")
    test("quote list", "(quote (1 2 3))", [1, 2, 3])
    test("quote symbol", "(quote hello)", Symbol("hello"))
    
    # Complex programs
    print("\n--- Complex Programs ---")
    test("accumulate", """
        (begin
            (define (accumulate f init lst)
                (if (null? lst) init
                    (f (car lst) (accumulate f init (cdr lst)))))
            (accumulate + 0 (list 1 2 3 4 5)))
    """, 15)
    
    test("quicksort", """
        (begin
            (define (qsort lst)
                (if (null? lst) (list)
                    (if (null? (cdr lst)) lst
                        (let ((pivot (car lst))
                              (rest (cdr lst)))
                            (append
                                (qsort (filter (lambda (x) (< x pivot)) rest))
                                (list pivot)
                                (qsort (filter (lambda (x) (>= x pivot)) rest)))))))
            (qsort (list 5 3 8 1 9 2 7 4 6)))
    """, [1, 2, 3, 4, 5, 6, 7, 8, 9])
    
    # Summary
    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'=' * 50}")
    
    if failed == 0:
        print("🎉 All tests passed! MicroLisp is alive.")
    
    exit(0 if failed == 0 else 1)