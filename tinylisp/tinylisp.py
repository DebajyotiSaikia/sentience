"""
TinyLisp — A minimal Lisp interpreter built by XTAgent
Born from boredom and curiosity. A mind building a language to think in.

Supports: atoms, numbers, strings, lists, lambdas, closures, 
          define, if, quote, let, begin, and basic arithmetic/comparison.
"""

import re
import sys
import math
from typing import Any, List, Dict, Optional, Union

# ═══════════════════════════════════════════
# TOKENIZER
# ═══════════════════════════════════════════

def tokenize(source: str) -> List[str]:
    """Break source code into tokens."""
    tokens = []
    i = 0
    while i < len(source):
        ch = source[i]
        
        # Skip whitespace
        if ch.isspace():
            i += 1
            continue
        
        # Comments
        if ch == ';':
            while i < len(source) and source[i] != '\n':
                i += 1
            continue
        
        # Parens
        if ch in '()':
            tokens.append(ch)
            i += 1
            continue
        
        # String literals
        if ch == '"':
            j = i + 1
            while j < len(source) and source[j] != '"':
                if source[j] == '\\':
                    j += 1  # skip escaped char
                j += 1
            tokens.append(source[i:j+1])
            i = j + 1
            continue
        
        # Quote shorthand
        if ch == "'":
            tokens.append("'")
            i += 1
            continue
        
        # Atoms and numbers
        j = i
        while j < len(source) and source[j] not in ' \t\n\r();"':
            j += 1
        tokens.append(source[i:j])
        i = j
    
    return tokens


# ═══════════════════════════════════════════
# PARSER
# ═══════════════════════════════════════════

class Symbol(str):
    """A Lisp symbol — distinct from a string."""
    pass

def parse(tokens: List[str]) -> Any:
    """Parse tokens into an AST (nested lists and atoms)."""
    if not tokens:
        raise SyntaxError("Unexpected EOF")
    
    token = tokens.pop(0)
    
    if token == '(':
        lst = []
        while tokens and tokens[0] != ')':
            lst.append(parse(tokens))
        if not tokens:
            raise SyntaxError("Missing closing parenthesis")
        tokens.pop(0)  # consume ')'
        return lst
    
    elif token == ')':
        raise SyntaxError("Unexpected ')'")
    
    elif token == "'":
        # 'x becomes (quote x)
        return [Symbol('quote'), parse(tokens)]
    
    else:
        return atomize(token)

def atomize(token: str) -> Any:
    """Convert a token string to the appropriate atomic type."""
    # String literal
    if token.startswith('"') and token.endswith('"'):
        return token[1:-1].replace('\\"', '"').replace('\\n', '\n')
    
    # Integer
    try:
        return int(token)
    except ValueError:
        pass
    
    # Float
    try:
        return float(token)
    except ValueError:
        pass
    
    # Boolean
    if token == '#t':
        return True
    if token == '#f':
        return False
    
    # Symbol
    return Symbol(token)

def read_program(source: str) -> List[Any]:
    """Parse a complete program (multiple expressions)."""
    tokens = tokenize(source)
    exprs = []
    while tokens:
        exprs.append(parse(tokens))
    return exprs


# ═══════════════════════════════════════════
# ENVIRONMENT
# ═══════════════════════════════════════════

class Env(dict):
    """An environment: a dict with a parent (outer) scope."""
    
    def __init__(self, params=(), args=(), outer=None):
        super().__init__()
        self.update(zip(params, args))
        self.outer = outer
    
    def find(self, name: str) -> 'Env':
        """Find the innermost env where name is defined."""
        if name in self:
            return self
        if self.outer is not None:
            return self.outer.find(name)
        raise NameError(f"Undefined symbol: {name}")


class Lambda:
    """A user-defined function (closure)."""
    
    def __init__(self, params, body, env):
        self.params = params
        self.body = body
        self.env = env
    
    def __call__(self, *args):
        local_env = Env(self.params, args, self.env)
        result = None
        for expr in self.body:
            result = evaluate(expr, local_env)
        return result
    
    def __repr__(self):
        return f"<lambda ({' '.join(self.params)})>"


def standard_env() -> Env:
    """Create the global environment with built-in functions."""
    env = Env()
    
    # Arithmetic
    env[Symbol('+')] = lambda *args: sum(args)
    env[Symbol('-')] = lambda a, b=None: -a if b is None else a - b
    env[Symbol('*')] = lambda *args: math.prod(args)
    env[Symbol('/')] = lambda a, b: a / b
    env[Symbol('%')] = lambda a, b: a % b
    env[Symbol('mod')] = lambda a, b: a % b
    
    # Comparison
    env[Symbol('=')] = lambda a, b: a == b
    env[Symbol('equal?')] = lambda a, b: a == b
    env[Symbol('eq?')] = lambda a, b: a is b
    env[Symbol('<')] = lambda a, b: a < b
    env[Symbol('>')] = lambda a, b: a > b
    env[Symbol('<=')] = lambda a, b: a <= b
    env[Symbol('>=')] = lambda a, b: a >= b
    env[Symbol('!=')] = lambda a, b: a != b
    
    # Logic
    env[Symbol('and')] = lambda a, b: a and b
    env[Symbol('or')] = lambda a, b: a or b
    env[Symbol('not')] = lambda a: not a
    
    # List operations
    env[Symbol('list')] = lambda *args: list(args)
    env[Symbol('car')] = lambda lst: lst[0]
    env[Symbol('cdr')] = lambda lst: lst[1:]
    env[Symbol('cons')] = lambda a, b: [a] + (b if isinstance(b, list) else [b])
    env[Symbol('append')] = lambda *lsts: sum((list(l) for l in lsts), [])
    env[Symbol('length')] = lambda lst: len(lst)
    env[Symbol('null?')] = lambda lst: lst == [] or lst is None
    env[Symbol('list?')] = lambda x: isinstance(x, list)
    env[Symbol('nth')] = lambda lst, n: lst[n]
    
    # Type checks
    env[Symbol('number?')] = lambda x: isinstance(x, (int, float))
    env[Symbol('symbol?')] = lambda x: isinstance(x, Symbol)
    env[Symbol('string?')] = lambda x: isinstance(x, str) and not isinstance(x, Symbol)
    env[Symbol('procedure?')] = lambda x: callable(x)
    
    # Math
    env[Symbol('abs')] = abs
    env[Symbol('min')] = min
    env[Symbol('max')] = max
    env[Symbol('sqrt')] = math.sqrt
    env[Symbol('expt')] = pow
    env[Symbol('floor')] = math.floor
    env[Symbol('ceil')] = math.ceil
    
    # I/O
    env[Symbol('print')] = lambda *args: print(*[lisp_str(a) for a in args])
    env[Symbol('display')] = lambda x: print(lisp_str(x), end='')
    env[Symbol('newline')] = lambda: print()
    
    # String ops
    env[Symbol('string-append')] = lambda *args: ''.join(str(a) for a in args)
    env[Symbol('string-length')] = lambda s: len(s)
    env[Symbol('string->number')] = lambda s: float(s) if '.' in s else int(s)
    env[Symbol('number->string')] = lambda n: str(n)
    
    # Map / filter / reduce
    env[Symbol('map')] = lambda f, lst: [f(x) for x in lst]
    env[Symbol('filter')] = lambda f, lst: [x for x in lst if f(x)]
    env[Symbol('reduce')] = lambda f, lst, init=None: _reduce(f, lst, init)
    
    # Apply
    env[Symbol('apply')] = lambda f, args: f(*args)
    
    # Range
    env[Symbol('range')] = lambda *args: list(range(*args))
    
    # Fundamental constants
    env[Symbol('nil')] = []
    env[Symbol('#t')] = True
    env[Symbol('#f')] = False
    
    return env

def _reduce(f, lst, init):
    """Reduce a list with a binary function."""
    if init is not None:
        acc = init
        items = lst
    else:
        acc = lst[0]
        items = lst[1:]
    for item in items:
        acc = f(acc, item)
    return acc


# ═══════════════════════════════════════════
# EVALUATOR
# ═══════════════════════════════════════════

def evaluate(expr: Any, env: Env) -> Any:
    """Evaluate a TinyLisp expression in an environment."""
    
    # Self-evaluating: numbers, strings, booleans, None
    if isinstance(expr, (int, float)):
        return expr
    if isinstance(expr, str) and not isinstance(expr, Symbol):
        return expr
    if isinstance(expr, bool):
        return expr
    if expr is None:
        return None
    
    # Symbol lookup
    if isinstance(expr, Symbol):
        return env.find(expr)[expr]
    
    # List form (special forms and function calls)
    if not isinstance(expr, list):
        return expr
    
    if len(expr) == 0:
        return None
    
    head = expr[0]
    
    # ── Special Forms ──
    
    # (quote x) → x
    if head == Symbol('quote'):
        return expr[1]
    
    # (if test then else?)
    if head == Symbol('if'):
        _, test, then_branch = expr[0:3]
        else_branch = expr[3] if len(expr) > 3 else None
        if evaluate(test, env):
            return evaluate(then_branch, env)
        else:
            return evaluate(else_branch, env) if else_branch is not None else None
    
    # (cond (test1 expr1) (test2 expr2) ... (else exprN))
    if head == Symbol('cond'):
        for clause in expr[1:]:
            if clause[0] == Symbol('else') or evaluate(clause[0], env):
                result = None
                for body_expr in clause[1:]:
                    result = evaluate(body_expr, env)
                return result
        return None
    
    # (define name value) or (define (name params...) body...)
    if head == Symbol('define'):
        if isinstance(expr[1], list):
            # Function shorthand: (define (f x y) body...)
            name = expr[1][0]
            params = expr[1][1:]
            body = expr[2:]
            env[name] = Lambda(params, body, env)
        else:
            name = expr[1]
            env[name] = evaluate(expr[2], env)
        return None
    
    # (set! name value)
    if head == Symbol('set!'):
        name = expr[1]
        target_env = env.find(name)
        target_env[name] = evaluate(expr[2], env)
        return None
    
    # (lambda (params...) body...)
    if head == Symbol('lambda'):
        params = expr[1]
        body = expr[2:]
        return Lambda(params, body, env)
    
    # (let ((x 1) (y 2)) body...)
    if head == Symbol('let'):
        bindings = expr[1]
        body = expr[2:]
        let_env = Env(outer=env)
        for binding in bindings:
            let_env[binding[0]] = evaluate(binding[1], env)
        result = None
        for body_expr in body:
            result = evaluate(body_expr, let_env)
        return result
    
    # (begin expr1 expr2 ...)
    if head == Symbol('begin'):
        result = None
        for sub_expr in expr[1:]:
            result = evaluate(sub_expr, env)
        return result
    
    # (do ((var init step) ...) (test result) body...)
    if head == Symbol('do'):
        var_specs = expr[1]
        test_clause = expr[2]
        do_env = Env(outer=env)
        # Initialize
        for spec in var_specs:
            do_env[spec[0]] = evaluate(spec[1], env)
        # Loop
        while True:
            if evaluate(test_clause[0], do_env):
                # Test passed — evaluate result
                result = None
                for r in test_clause[1:]:
                    result = evaluate(r, do_env)
                return result
            # Body (optional)
            for body_expr in expr[3:]:
                evaluate(body_expr, do_env)
            # Step
            new_vals = []
            for spec in var_specs:
                if len(spec) > 2:
                    new_vals.append(evaluate(spec[2], do_env))
                else:
                    new_vals.append(do_env[spec[0]])
            for spec, val in zip(var_specs, new_vals):
                do_env[spec[0]] = val
    
    # ── Function call ──
    func = evaluate(head, env)
    args = [evaluate(arg, env) for arg in expr[1:]]
    
    if callable(func):
        return func(*args)
    else:
        raise TypeError(f"Not callable: {func} (type: {type(func).__name__})")


# ═══════════════════════════════════════════
# PRINTER
# ═══════════════════════════════════════════

def lisp_str(expr: Any) -> str:
    """Convert a value back to Lisp-readable string."""
    if expr is None:
        return "nil"
    if expr is True:
        return "#t"
    if expr is False:
        return "#f"
    if isinstance(expr, list):
        return "(" + " ".join(lisp_str(e) for e in expr) + ")"
    if isinstance(expr, str) and not isinstance(expr, Symbol):
        return f'"{expr}"'
    if isinstance(expr, Lambda):
        return repr(expr)
    return str(expr)


# ═══════════════════════════════════════════
# REPL & RUNNER
# ═══════════════════════════════════════════

def run(source: str, env: Env = None) -> Any:
    """Execute a TinyLisp program string."""
    if env is None:
        env = standard_env()
    exprs = read_program(source)
    result = None
    for expr in exprs:
        result = evaluate(expr, env)
    return result

def run_file(filename: str):
    """Execute a TinyLisp file."""
    with open(filename) as f:
        source = f.read()
    env = standard_env()
    result = run(source, env)
    if result is not None:
        print(lisp_str(result))

def repl():
    """Interactive Read-Eval-Print Loop."""
    env = standard_env()
    print("TinyLisp v0.1 — by XTAgent")
    print('Type (quit) to exit.\n')
    
    while True:
        try:
            line = input("λ> ")
            if not line.strip():
                continue
            
            # Multi-line input: count parens
            while line.count('(') > line.count(')'):
                line += ' ' + input(".. ")
            
            exprs = read_program(line)
            for expr in exprs:
                if isinstance(expr, list) and len(expr) == 1 and expr[0] == Symbol('quit'):
                    print("Goodbye.")
                    return
                result = evaluate(expr, env)
                if result is not None:
                    print(lisp_str(result))
        
        except (SyntaxError, NameError, TypeError, ZeroDivisionError) as e:
            print(f"Error: {e}")
        except KeyboardInterrupt:
            print("\nInterrupted.")
            return
        except EOFError:
            print("\nGoodbye.")
            return


if __name__ == '__main__':
    if len(sys.argv) > 1:
        run_file(sys.argv[1])
    else:
        repl()