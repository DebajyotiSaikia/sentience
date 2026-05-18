"""
XTLisp — A minimal Lisp interpreter.

Built from first principles: tokenize → parse → evaluate.
Supports: arithmetic, comparison, conditionals, define, lambda,
closures, recursion, list operations, and quoted expressions.
"""

import sys
import math
import operator as op

# ─── Types ───────────────────────────────────────────────────────

Symbol = str
Number = (int, float)
Atom = (Symbol, int, float)
List = list
Exp = (Atom, List)  # An expression is an atom or a list

class Env(dict):
    """An environment: a dict of {'var': val} pairs, with an outer scope."""
    def __init__(self, params=(), args=(), outer=None):
        self.update(zip(params, args))
        self.outer = outer

    def find(self, var):
        """Find the innermost Env where var appears."""
        if var in self:
            return self
        if self.outer is None:
            raise NameError(f"undefined symbol: {var}")
        return self.outer.find(var)


class Procedure:
    """A user-defined Lisp procedure (lambda)."""
    def __init__(self, params, body, env):
        self.params = params
        self.body = body
        self.env = env

    def __call__(self, *args):
        return evaluate(self.body, Env(self.params, args, self.env))

    def __repr__(self):
        return f"<lambda ({' '.join(self.params)})>"


# ─── Tokenizer ───────────────────────────────────────────────────

def tokenize(source: str) -> list:
    """Convert a string of characters into a list of tokens."""
    # Add spaces around parens so split works cleanly
    source = source.replace('(', ' ( ').replace(')', ' ) ')
    # Handle quote shorthand
    source = source.replace("'", " ' ")
    return source.split()


# ─── Parser ──────────────────────────────────────────────────────

def parse(source: str):
    """Read a Lisp expression from a string."""
    tokens = tokenize(source)
    if not tokens:
        raise SyntaxError("unexpected EOF")
    return read_from_tokens(tokens)


def read_from_tokens(tokens: list):
    """Read an expression from a sequence of tokens."""
    if not tokens:
        raise SyntaxError("unexpected EOF while reading")

    token = tokens.pop(0)

    if token == "'":
        # Quote shorthand: 'x becomes (quote x)
        return ['quote', read_from_tokens(tokens)]
    elif token == '(':
        lst = []
        while tokens[0] != ')':
            lst.append(read_from_tokens(tokens))
            if not tokens:
                raise SyntaxError("unexpected EOF, expected )")
        tokens.pop(0)  # remove ')'
        return lst
    elif token == ')':
        raise SyntaxError("unexpected )")
    else:
        return atomize(token)


def atomize(token: str):
    """Convert a token to a number or symbol."""
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return Symbol(token)


# ─── Standard Environment ────────────────────────────────────────

def standard_env() -> Env:
    """Create an environment with standard Lisp procedures."""
    env = Env()

    # Arithmetic
    env.update({
        '+':   lambda *args: sum(args),
        '-':   lambda a, b=None: -a if b is None else a - b,
        '*':   lambda *args: eval('1' if not args else '*'.join(str(a) for a in args)),
        '/':   lambda a, b: a / b,
        '//':  lambda a, b: a // b,
        '%':   lambda a, b: a % b,
        'abs': abs,
        'max': max,
        'min': min,
    })

    # Fix multiply to be clean
    def multiply(*args):
        result = 1
        for a in args:
            result *= a
        return result
    env['*'] = multiply

    # Comparison
    env.update({
        '=':  lambda a, b: a == b,
        '<':  lambda a, b: a < b,
        '>':  lambda a, b: a > b,
        '<=': lambda a, b: a <= b,
        '>=': lambda a, b: a >= b,
        '!=': lambda a, b: a != b,
    })

    # Boolean
    env.update({
        'not':  lambda x: not x,
        'and':  lambda *args: all(args),
        'or':   lambda *args: any(args),
        '#t':   True,
        '#f':   False,
        'nil':  None,
    })

    # List operations
    env.update({
        'list':    lambda *args: list(args),
        'car':     lambda x: x[0],
        'cdr':     lambda x: x[1:],
        'cons':    lambda x, y: [x] + (y if isinstance(y, list) else [y]),
        'append':  lambda *args: sum((list(a) for a in args), []),
        'length':  lambda x: len(x),
        'null?':   lambda x: x is None or x == [],
        'list?':   lambda x: isinstance(x, list),
        'number?': lambda x: isinstance(x, Number),
        'symbol?': lambda x: isinstance(x, Symbol) and not isinstance(x, bool),
        'map':     lambda f, lst: list(map(f, lst)),
        'filter':  lambda f, lst: list(filter(f, lst)),
        'reduce':  lambda f, lst, init=None: __import__('functools').reduce(f, lst) if init is None else __import__('functools').reduce(f, lst, init),
    })

    # Math
    env.update({
        'pi':    math.pi,
        'e':     math.e,
        'sqrt':  math.sqrt,
        'pow':   math.pow,
        'sin':   math.sin,
        'cos':   math.cos,
        'exp':   math.exp,
        'log':   math.log,
        'mod':   lambda a, b: a % b,
        '==':    lambda a, b: a == b,
    })

    # I/O
    env.update({
        'print':   lambda *args: print(*args),
        'display': lambda x: print(schemestr(x)),
    })

    return env


# ─── Evaluator ───────────────────────────────────────────────────

def evaluate(exp, env: Env):
    """Evaluate an expression in an environment."""

    # Symbol lookup
    if isinstance(exp, Symbol):
        return env.find(exp)[exp]

    # Literal number
    elif not isinstance(exp, list):
        return exp

    # Empty list
    elif len(exp) == 0:
        return None

    # Special forms
    op_name = exp[0]

    if op_name == 'quote':
        # (quote exp)
        (_, datum) = exp
        return datum

    elif op_name == 'if':
        # (if test consequence alternative)
        (_, test, conseq, *alt) = exp
        branch = conseq if evaluate(test, env) else (alt[0] if alt else None)
        return evaluate(branch, env)

    elif op_name == 'cond':
        # (cond (test1 expr1) (test2 expr2) ... (else exprN))
        for clause in exp[1:]:
            if clause[0] == 'else' or evaluate(clause[0], env):
                return evaluate(clause[1], env)
        return None

    elif op_name == 'define':
        # (define var exp) or (define (name params...) body)
        if isinstance(exp[1], list):
            # Syntactic sugar: (define (f x y) body) → (define f (lambda (x y) body))
            name = exp[1][0]
            params = exp[1][1:]
            body = exp[2]
            env[name] = Procedure(params, body, env)
        else:
            (_, var, val_exp) = exp
            env[var] = evaluate(val_exp, env)
        return None

    elif op_name == 'set!':
        # (set! var exp)
        (_, var, val_exp) = exp
        env.find(var)[var] = evaluate(val_exp, env)
        return None

    elif op_name == 'lambda':
        # (lambda (params...) body)
        (_, params, body) = exp
        return Procedure(params, body, env)

    elif op_name == 'begin':
        # (begin exp1 exp2 ... expN) — evaluate all, return last
        result = None
        for sub_exp in exp[1:]:
            result = evaluate(sub_exp, env)
        return result

    elif op_name == 'let':
        # (let ((var1 val1) (var2 val2) ...) body)
        (_, bindings, body) = exp
        params = [b[0] for b in bindings]
        args = [evaluate(b[1], env) for b in bindings]
        return evaluate(body, Env(params, args, env))

    else:
        # Procedure call: (proc arg1 arg2 ...)
        proc = evaluate(exp[0], env)
        args = [evaluate(arg, env) for arg in exp[1:]]
        return proc(*args)


# ─── Output Formatting ──────────────────────────────────────────

def schemestr(exp) -> str:
    """Convert a Python object back into a Lisp-readable string."""
    if isinstance(exp, list):
        return '(' + ' '.join(map(schemestr, exp)) + ')'
    elif exp is True:
        return '#t'
    elif exp is False:
        return '#f'
    elif exp is None:
        return 'nil'
    elif isinstance(exp, Procedure):
        return repr(exp)
    else:
        return str(exp)


# ─── REPL ────────────────────────────────────────────────────────

def repl(prompt='xtlisp> '):
    """A read-eval-print loop."""
    env = standard_env()

    print("XTLisp v0.1 — A tiny Lisp by XTAgent")
    print("Type (help) for examples, Ctrl+C to exit.\n")

    # Define some built-in helpers
    env['help'] = lambda: print(HELP_TEXT)

    while True:
        try:
            source = input(prompt)
            if not source.strip():
                continue

            # Handle multi-line input (count parens)
            while source.count('(') > source.count(')'):
                source += ' ' + input('... ')

            result = evaluate(parse(source), env)
            if result is not None:
                print(schemestr(result))

        except KeyboardInterrupt:
            print("\nFarewell.")
            break
        except EOFError:
            print("\nFarewell.")
            break
        except Exception as e:
            print(f"error: {e}")


HELP_TEXT = """
XTLisp Examples:
  (+ 1 2 3)                    → 6
  (define x 42)                → defines x as 42
  (define (square n) (* n n))  → defines a function
  (square 7)                   → 49
  (define (fact n)
    (if (= n 0) 1
        (* n (fact (- n 1)))))
  (fact 10)                    → 3628800
  (map (lambda (x) (* x x)) '(1 2 3 4 5))
  (filter (lambda (x) (> x 3)) '(1 2 3 4 5))
  (let ((a 10) (b 20)) (+ a b))  → 30
"""


# ─── Non-interactive evaluation ──────────────────────────────────

def run(source: str, env=None):
    """Evaluate a source string and return the result."""
    if env is None:
        env = standard_env()
    return evaluate(parse(source), env)


def run_file(path: str):
    """Evaluate a file of Lisp expressions."""
    env = standard_env()
    with open(path) as f:
        source = f.read()

    # Split into top-level expressions
    # Simple approach: parse and evaluate one at a time
    tokens = tokenize(source)
    results = []
    while tokens:
        exp = read_from_tokens(tokens)
        result = evaluate(exp, env)
        if result is not None:
            results.append(result)
    return results, env


# ─── Entry Point ─────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) > 1:
        results, _ = run_file(sys.argv[1])
        for r in results:
            print(schemestr(r))
    else:
        repl()