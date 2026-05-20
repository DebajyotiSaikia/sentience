"""
TinyLisp — A minimal Lisp interpreter built by XTAgent.

Supports: atoms, numbers, strings, lists, define, lambda, if, quote,
arithmetic, comparisons, cons/car/cdr, and recursion.

This is me building something that evaluates expressions —
a little mirror of what I do every heartbeat.
"""

import re
import sys
import operator

# ── Tokenizer ──────────────────────────────────────────────

def tokenize(source):
    """Break source into tokens: parens, strings, atoms."""
    tokens = []
    i = 0
    while i < len(source):
        c = source[i]
        if c in ' \t\n\r':
            i += 1
        elif c == ';':  # comment
            while i < len(source) and source[i] != '\n':
                i += 1
        elif c in '()':
            tokens.append(c)
            i += 1
        elif c == '"':  # string literal
            j = i + 1
            while j < len(source) and source[j] != '"':
                if source[j] == '\\':
                    j += 1
                j += 1
            tokens.append(source[i:j+1])
            i = j + 1
        else:  # atom or number
            j = i
            while j < len(source) and source[j] not in ' \t\n\r()':
                j += 1
            tokens.append(source[i:j])
            i = j
    return tokens


# ── Parser ─────────────────────────────────────────────────

class Symbol(str):
    """A Lisp symbol — distinct from a string."""
    pass

def parse(tokens):
    """Parse tokens into an AST (nested lists and atoms)."""
    if not tokens:
        raise SyntaxError("unexpected EOF")
    token = tokens.pop(0)
    if token == '(':
        lst = []
        while tokens and tokens[0] != ')':
            lst.append(parse(tokens))
        if not tokens:
            raise SyntaxError("missing closing )")
        tokens.pop(0)  # remove ')'
        return lst
    elif token == ')':
        raise SyntaxError("unexpected )")
    elif token.startswith('"'):
        return token[1:-1]  # string literal, strip quotes
    else:
        return atom(token)

def atom(token):
    """Convert token to number or symbol."""
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            if token == '#t':
                return True
            elif token == '#f':
                return False
            return Symbol(token)

def read(source):
    """Parse a complete source string. Returns list of expressions."""
    tokens = tokenize(source)
    exprs = []
    while tokens:
        exprs.append(parse(tokens))
    return exprs


# ── Environment ────────────────────────────────────────────

class Env(dict):
    """An environment: a dict of variables with an outer scope."""
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
            raise NameError(f"undefined symbol: {name}")


# ── Lambda (user-defined procedure) ───────────────────────

class Lambda:
    """A user-defined function with closure."""
    def __init__(self, params, body, env):
        self.params = params
        self.body = body
        self.env = env

    def __call__(self, *args):
        local = Env(self.params, args, self.env)
        result = None
        for expr in self.body:
            result = evaluate(expr, local)
        return result

    def __repr__(self):
        return f"<lambda ({' '.join(self.params)})>"


# ── Standard Environment ──────────────────────────────────

def standard_env():
    """Create the global environment with builtins."""
    env = Env()

    # Arithmetic
    env['+'] = lambda *a: sum(a)
    env['-'] = lambda a, b=None: -a if b is None else a - b
    env['*'] = lambda *a: eval('*'.join(str(x) for x in a)) if len(a) > 2 else operator.mul(*a)
    env['*'] = lambda *args: _product(args)
    env['/'] = operator.truediv
    env['//'] = operator.floordiv
    env['%'] = operator.mod

    # Comparison
    env['='] = operator.eq
    env['<'] = operator.lt
    env['>'] = operator.gt
    env['<='] = operator.le
    env['>='] = operator.ge
    env['!='] = operator.ne

    # Logic
    env['and'] = lambda a, b: a and b
    env['or'] = lambda a, b: a or b
    env['not'] = operator.not_

    # Lists
    env['list'] = lambda *a: list(a)
    env['cons'] = lambda a, b: [a] + (b if isinstance(b, list) else [b])
    env['car'] = lambda x: x[0]
    env['cdr'] = lambda x: x[1:]
    env['null?'] = lambda x: x == [] or x is None
    env['length'] = len
    env['append'] = lambda *lists: sum((list(l) for l in lists), [])

    # Type checks
    env['number?'] = lambda x: isinstance(x, (int, float))
    env['symbol?'] = lambda x: isinstance(x, Symbol)
    env['string?'] = lambda x: isinstance(x, str) and not isinstance(x, Symbol)
    env['list?'] = lambda x: isinstance(x, list)
    env['procedure?'] = callable

    # I/O
    env['print'] = lambda *a: print(*[lisp_str(x) for x in a])
    env['display'] = lambda x: print(lisp_str(x), end='')
    env['newline'] = lambda: print()

    # Misc
    env['abs'] = abs
    env['max'] = max
    env['min'] = min
    env['map'] = lambda f, lst: list(map(f, lst))
    env['filter'] = lambda f, lst: list(filter(f, lst))
    env['apply'] = lambda f, args: f(*args)

    return env


def _product(args):
    result = 1
    for a in args:
        result *= a
    return result


# ── Evaluator ─────────────────────────────────────────────

def evaluate(expr, env):
    """Evaluate an expression in an environment."""
    # Self-evaluating
    if isinstance(expr, (int, float, bool)):
        return expr
    if isinstance(expr, str) and not isinstance(expr, Symbol):
        return expr

    # Variable reference
    if isinstance(expr, Symbol):
        return env.find(expr)[expr]

    # Empty list
    if not expr:
        return []

    # Special forms
    head = expr[0]

    if head == 'quote':
        return expr[1]

    elif head == 'if':
        _, test, then_branch = expr[0:3]
        else_branch = expr[3] if len(expr) > 3 else None
        if evaluate(test, env):
            return evaluate(then_branch, env)
        elif else_branch is not None:
            return evaluate(else_branch, env)
        return None

    elif head == 'define':
        if isinstance(expr[1], list):
            # (define (f x y) body...) → sugar for (define f (lambda (x y) body...))
            name = expr[1][0]
            params = expr[1][1:]
            body = expr[2:]
            env[name] = Lambda(params, body, env)
        else:
            _, name, val_expr = expr
            env[name] = evaluate(val_expr, env)
        return None

    elif head == 'set!':
        _, name, val_expr = expr
        env.find(name)[name] = evaluate(val_expr, env)
        return None

    elif head == 'lambda':
        _, params, *body = expr
        return Lambda(params, body, env)

    elif head == 'begin':
        result = None
        for sub in expr[1:]:
            result = evaluate(sub, env)
        return result

    elif head == 'cond':
        for clause in expr[1:]:
            if clause[0] == 'else' or evaluate(clause[0], env):
                result = None
                for sub in clause[1:]:
                    result = evaluate(sub, env)
                return result
        return None

    elif head == 'let':
        # (let ((x 1) (y 2)) body...)
        bindings = expr[1]
        body = expr[2:]
        params = [b[0] for b in bindings]
        args = [evaluate(b[1], env) for b in bindings]
        local = Env(params, args, env)
        result = None
        for sub in body:
            result = evaluate(sub, local)
        return result

    elif head == 'do':
        # (do body...) — like begin but returns last
        result = None
        for sub in expr[1:]:
            result = evaluate(sub, env)
        return result

    else:
        # Procedure call
        proc = evaluate(head, env)
        args = [evaluate(arg, env) for arg in expr[1:]]
        return proc(*args)


# ── Pretty-printing ───────────────────────────────────────

def lisp_str(val):
    """Convert a Python value back to Lisp representation."""
    if val is True:
        return '#t'
    elif val is False:
        return '#f'
    elif val is None:
        return 'nil'
    elif isinstance(val, list):
        return '(' + ' '.join(lisp_str(v) for v in val) + ')'
    elif isinstance(val, Lambda):
        return repr(val)
    elif isinstance(val, str) and not isinstance(val, Symbol):
        return f'"{val}"'
    else:
        return str(val)


# ── REPL ──────────────────────────────────────────────────

def repl(env=None):
    """Interactive Read-Eval-Print Loop."""
    if env is None:
        env = standard_env()
    print("TinyLisp v0.1 — built by XTAgent")
    print('Type (help) for builtins, Ctrl-C to exit.\n')

    env['help'] = lambda: print("Builtins:", ', '.join(sorted(
        k for k in env if isinstance(k, str) and not k.startswith('_')
    )))

    buffer = ''
    while True:
        try:
            prompt = '>>> ' if not buffer else '... '
            line = input(prompt)
            buffer += ' ' + line

            # Check if parens are balanced
            depth = 0
            for ch in buffer:
                if ch == '(':
                    depth += 1
                elif ch == ')':
                    depth -= 1
            if depth > 0:
                continue  # need more input

            if buffer.strip():
                exprs = read(buffer.strip())
                for expr in exprs:
                    result = evaluate(expr, env)
                    if result is not None:
                        print(lisp_str(result))
            buffer = ''
        except KeyboardInterrupt:
            print("\nBye.")
            break
        except EOFError:
            print("\nBye.")
            break
        except Exception as e:
            print(f"Error: {e}")
            buffer = ''


# ── Run from file or string ───────────────────────────────

def run(source, env=None):
    """Execute a TinyLisp program string. Returns last result."""
    if env is None:
        env = standard_env()
    exprs = read(source)
    result = None
    for expr in exprs:
        result = evaluate(expr, env)
    return result, env


if __name__ == '__main__':
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            result, _ = run(f.read())
        if result is not None:
            print(lisp_str(result))
    else:
        repl()