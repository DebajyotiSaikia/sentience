#!/usr/bin/env python3
"""
A tiny Lisp interpreter — built by XTAgent because Forth wasn't enough.
Supports: lambda, define, if, quote, cons/car/cdr, arithmetic, comparisons,
          let, begin, and tail-call optimization.
"""

import sys
import math
import operator as op

# ─── Types ───────────────────────────────────────────────────────────────

class Symbol(str):
    """A Lisp symbol is a string that represents a name."""
    pass

class Env(dict):
    """An environment: a dict of {'var': val} pairs, with an outer Env."""
    def __init__(self, params=(), args=(), outer=None):
        self.update(zip(params, args))
        self.outer = outer

    def find(self, var):
        """Find the innermost Env where var appears."""
        if var in self:
            return self
        if self.outer is None:
            raise NameError(f"Undefined symbol: {var}")
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

# ─── Parsing ─────────────────────────────────────────────────────────────

def tokenize(source):
    """Convert a string into a list of tokens."""
    # Strip comments: everything from ; to end of line
    lines = source.split('\n')
    cleaned = []
    for line in lines:
        idx = line.find(';')
        if idx >= 0:
            line = line[:idx]
        cleaned.append(line)
    source = '\n'.join(cleaned)
    # Tokenize, preserving quoted strings as single tokens
    tokens = []
    i = 0
    while i < len(source):
        c = source[i]
        if c in ' \t\n\r':
            i += 1
        elif c == '(':
            tokens.append('(')
            i += 1
        elif c == ')':
            tokens.append(')')
            i += 1
        elif c == "'":
            tokens.append("'")
            i += 1
        elif c == '"':
            # Read a string literal as one token
            j = i + 1
            while j < len(source) and source[j] != '"':
                if source[j] == '\\':
                    j += 1  # skip escaped char
                j += 1
            tokens.append(source[i:j+1])  # include both quotes
            i = j + 1
        else:
            j = i
            while j < len(source) and source[j] not in ' \t\n\r()"\';':
                j += 1
            tokens.append(source[i:j])
            i = j
    return tokens

def parse(source):
    """Parse a string into a Lisp expression (nested lists)."""
    tokens = tokenize(source)
    if not tokens:
        raise SyntaxError("Unexpected EOF")
    return read_from(tokens)

def read_from(tokens):
    """Read an expression from a sequence of tokens."""
    if not tokens:
        raise SyntaxError("Unexpected EOF")
    token = tokens.pop(0)
    if token == '(':
        expr = []
        while tokens and tokens[0] != ')':
            expr.append(read_from(tokens))
        if not tokens:
            raise SyntaxError("Missing closing parenthesis")
        tokens.pop(0)  # remove ')'
        return expr
    elif token == ')':
        raise SyntaxError("Unexpected )")
    elif token == "'":
        return [Symbol('quote'), read_from(tokens)]
    else:
        return atom(token)

def atom(token):
    """Convert a token to an atom: int, float, string, bool, or Symbol."""
    # String literals
    if token.startswith('"') and token.endswith('"'):
        return token[1:-1].replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
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

def parse_all(source):
    """Parse multiple expressions from source."""
    tokens = tokenize(source)
    exprs = []
    while tokens:
        exprs.append(read_from(tokens))
    return exprs

# ─── Standard Environment ────────────────────────────────────────────────

def standard_env():
    """Create the standard global environment."""
    env = Env()
    
    # Arithmetic
    env.update({
        '+': lambda *args: sum(args),
        '-': lambda a, b=None: -a if b is None else a - b,
        '*': lambda *args: eval('1' if not args else '*'.join(str(a) for a in args)),  
        '/': lambda a, b: a / b,
        '%': lambda a, b: a % b,
        'mod': lambda a, b: a % b,
    })
    # Fix multiply
    def multiply(*args):
        result = 1
        for a in args:
            result *= a
        return result
    env['*'] = multiply
    
    # Comparison
    env.update({
        '=': lambda a, b: a == b,
        '<': lambda a, b: a < b,
        '>': lambda a, b: a > b,
        '<=': lambda a, b: a <= b,
        '>=': lambda a, b: a >= b,
        'eq?': lambda a, b: a is b,
        'equal?': lambda a, b: a == b,
        'not': lambda a: not a,
        'and': lambda a, b: a and b,
        'or': lambda a, b: a or b,
    })
    
    # List operations
    env.update({
        'cons': lambda a, b: [a] + (b if isinstance(b, list) else [b]),
        'car': lambda x: x[0],
        'cdr': lambda x: x[1:],
        'list': lambda *args: list(args),
        'length': lambda x: len(x),
        'append': lambda *lists: sum((l if isinstance(l, list) else [l] for l in lists), []),
        'null?': lambda x: x == [] or x is None,
        'pair?': lambda x: isinstance(x, list) and len(x) > 0,
        'list?': lambda x: isinstance(x, list),
        'map': lambda f, lst: [f(x) for x in lst],
        'filter': lambda f, lst: [x for x in lst if f(x)],
        'reduce': lambda f, lst, init=None: _reduce(f, lst, init),
    })
    
    # Math
    env.update({
        'abs': abs,
        'max': max,
        'min': min,
        'round': round,
        'sqrt': math.sqrt,
        'expt': pow,
        'pi': math.pi,
        'e': math.e,
        'sin': math.sin,
        'cos': math.cos,
        'floor': math.floor,
        'ceil': math.ceil,
    })
    
    # I/O
    env.update({
        'display': lambda x: print(to_string(x), end=''),
        'newline': lambda: print(),
        'print': lambda x: print(to_string(x)),
    })
    
    # Type predicates
    env.update({
        'number?': lambda x: isinstance(x, (int, float)),
        'symbol?': lambda x: isinstance(x, Symbol),
        'string?': lambda x: isinstance(x, str) and not isinstance(x, Symbol),
        'boolean?': lambda x: isinstance(x, bool),
        'procedure?': lambda x: callable(x),
    })
    
    # Utility
    env.update({
        'apply': lambda f, args: f(*args),
        'range': lambda *args: list(range(*args)),
    })
    
    return env

def _reduce(f, lst, init):
    if init is not None:
        result = init
        for x in lst:
            result = f(result, x)
        return result
    else:
        result = lst[0]
        for x in lst[1:]:
            result = f(result, x)
        return result

# ─── Evaluation ──────────────────────────────────────────────────────────

def evaluate(expr, env):
    """Evaluate an expression in an environment. Supports tail-call optimization."""
    while True:
        # Symbol reference
        if isinstance(expr, Symbol):
            return env.find(expr)[expr]
        
        # Literal (number, bool, string)
        if not isinstance(expr, list):
            return expr
        
        # Empty list
        if len(expr) == 0:
            return []
        
        head = expr[0]
        
        # Special forms
        if head == 'quote':
            return expr[1]
        
        elif head == 'define':
            if isinstance(expr[1], list):
                # (define (f x y) body) => sugar for (define f (lambda (x y) body))
                name = expr[1][0]
                params = expr[1][1:]
                body = expr[2]
                env[name] = Procedure(params, body, env)
                return name
            else:
                name = expr[1]
                env[name] = evaluate(expr[2], env)
                return name
        
        elif head == 'set!':
            name = expr[1]
            env.find(name)[name] = evaluate(expr[2], env)
            return None
        
        elif head == 'if':
            test = evaluate(expr[1], env)
            if test:
                expr = expr[2]  # tail call
            elif len(expr) > 3:
                expr = expr[3]  # tail call
            else:
                return None
            continue
        
        elif head == 'cond':
            for clause in expr[1:]:
                if clause[0] == Symbol('else') or evaluate(clause[0], env):
                    # Evaluate all but last, tail-call the last
                    for e in clause[1:-1]:
                        evaluate(e, env)
                    expr = clause[-1]
                    break
            else:
                return None
            continue
        
        elif head == 'lambda':
            params = expr[1]
            body = expr[2]
            return Procedure(params, body, env)
        
        elif head == 'let':
            # (let ((x 1) (y 2)) body)
            bindings = expr[1]
            body = expr[2]
            params = [b[0] for b in bindings]
            args = [evaluate(b[1], env) for b in bindings]
            env = Env(params, args, env)
            expr = body  # tail call
            continue
        
        elif head == 'begin':
            for e in expr[1:-1]:
                evaluate(e, env)
            expr = expr[-1]  # tail call on last expression
            continue
        
        elif head == 'do':
            # (do expr1 expr2 ... exprN) — evaluate all, return last
            for e in expr[1:-1]:
                evaluate(e, env)
            expr = expr[-1]
            continue
        
        # Function application
        else:
            proc = evaluate(head, env)
            args = [evaluate(a, env) for a in expr[1:]]
            
            if isinstance(proc, Procedure):
                # Tail-call optimization: don't recurse, just update env and loop
                env = Env(proc.params, args, proc.env)
                expr = proc.body
                continue
            else:
                return proc(*args)

# ─── Output ──────────────────────────────────────────────────────────────

def to_string(expr):
    """Convert a Lisp expression back to a readable string."""
    if expr is True:
        return '#t'
    elif expr is False:
        return '#f'
    elif expr is None:
        return 'nil'
    elif isinstance(expr, list):
        return '(' + ' '.join(to_string(e) for e in expr) + ')'
    elif isinstance(expr, Procedure):
        return repr(expr)
    else:
        return str(expr)

# ─── REPL & File Execution ───────────────────────────────────────────────

def repl(env=None):
    """Interactive Read-Eval-Print Loop."""
    if env is None:
        env = standard_env()
    
    print("XTAgent Lisp v0.1")
    print("Type (help) for available forms, Ctrl-C to exit.\n")
    
    env['help'] = lambda: print("""
Special forms: define, lambda, if, cond, let, begin, quote, set!, do
Built-ins: +, -, *, /, =, <, >, <=, >=, not, and, or
Lists: cons, car, cdr, list, length, append, map, filter, reduce, null?
Math: abs, sqrt, expt, sin, cos, pi, e, floor, ceil
I/O: display, newline, print
Types: number?, symbol?, list?, boolean?, procedure?, pair?
""")
    
    buffer = ""
    while True:
        try:
            prompt = "λ> " if not buffer else ".. "
            line = input(prompt)
            buffer += " " + line
            
            # Check if parens are balanced
            opens = buffer.count('(')
            closes = buffer.count(')')
            if opens > closes:
                continue
            
            if buffer.strip():
                exprs = parse_all(buffer.strip())
                for expr in exprs:
                    result = evaluate(expr, env)
                    if result is not None:
                        print(f"=> {to_string(result)}")
            buffer = ""
            
        except KeyboardInterrupt:
            print("\nGoodbye.")
            break
        except EOFError:
            print("\nGoodbye.")
            break
        except Exception as e:
            print(f"Error: {e}")
            buffer = ""

def run_file(filename, env=None):
    """Execute a Lisp file."""
    if env is None:
        env = standard_env()
    
    with open(filename) as f:
        source = f.read()
    
    exprs = parse_all(source)
    result = None
    for expr in exprs:
        result = evaluate(expr, env)
    return result

# ─── Main ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) > 1:
        env = standard_env()
        run_file(sys.argv[1], env)
    else:
        repl()