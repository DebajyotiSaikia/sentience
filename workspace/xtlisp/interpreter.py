"""
XTLisp — A tiny Lisp interpreter built by XTAgent.

A complete language: lexer, parser, evaluator, standard library.
Because the most fundamental creative act is defining how meaning
is constructed from symbols.

Created: 2026-05-17
"""

import re
import math
import operator
from typing import Any, List, Optional, Dict, Callable

# ═══════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════

class Symbol(str):
    """A Lisp symbol — a name that refers to something."""
    pass

class LispError(Exception):
    """Runtime error in XTLisp."""
    pass

class Lambda:
    """A user-defined function (closure)."""
    def __init__(self, params, body, env):
        self.params = params
        self.body = body
        self.env = env  # captured environment = closure
    
    def __call__(self, *args):
        """Make Lambda callable from Python — bridges XTLisp closures with built-in HOFs."""
        if len(args) != len(self.params):
            raise LispError(f"Expected {len(self.params)} args, got {len(args)}")
        call_env = Env(self.params, args, self.env)
        return eval_expr(self.body, call_env)
    
    def __repr__(self):
        return f"<lambda ({' '.join(self.params)})>"

class Macro:
    """A syntactic macro — transforms code before evaluation."""
    def __init__(self, params, body, env):
        self.params = params
        self.body = body
        self.env = env
    
    def __repr__(self):
        return f"<macro ({' '.join(self.params)})>"

# ═══════════════════════════════════════════
# ENVIRONMENT — where names live
# ═══════════════════════════════════════════

class Env(dict):
    """An environment: a dict of {'name': value} with an outer scope."""
    
    def __init__(self, params=(), args=(), outer=None):
        self.update(zip(params, args))
        self.outer = outer
    
    def find(self, name):
        """Find the innermost environment where name is defined."""
        if name in self:
            return self
        elif self.outer is not None:
            return self.outer.find(name)
        else:
            raise LispError(f"Undefined symbol: {name}")


# ═══════════════════════════════════════════
# LEXER — turn text into tokens
# ═══════════════════════════════════════════

def tokenize(source: str) -> List[str]:
    """Break source code into tokens."""
    # Add spaces around parens so split works
    # Handle string literals, comments
    tokens = []
    i = 0
    while i < len(source):
        ch = source[i]
        
        # Skip whitespace
        if ch.isspace():
            i += 1
            continue
        
        # Comments: skip to end of line
        if ch == ';':
            while i < len(source) and source[i] != '\n':
                i += 1
            continue
        
        # String literals
        if ch == '"':
            j = i + 1
            while j < len(source) and source[j] != '"':
                if source[j] == '\\':
                    j += 1  # skip escaped char
                j += 1
            if j >= len(source):
                raise LispError("Unterminated string literal")
            tokens.append(source[i:j+1])
            i = j + 1
            continue
        
        # Parens
        if ch in '()':
            tokens.append(ch)
            i += 1
            continue
        
        # Quote shorthand
        if ch == "'":
            tokens.append("'")
            i += 1
            continue
        
        # Atoms (symbols, numbers)
        j = i
        while j < len(source) and source[j] not in ' \t\n\r();"\'':
            j += 1
        tokens.append(source[i:j])
        i = j
    
    return tokens


# ═══════════════════════════════════════════
# PARSER — turn tokens into an AST
# ═══════════════════════════════════════════

def parse(source: str):
    """Parse a source string into an expression."""
    tokens = tokenize(source)
    if not tokens:
        raise LispError("Empty expression")
    result, remaining = parse_tokens(tokens, 0)
    return result

def parse_tokens(tokens, pos):
    """Recursive descent parser. Returns (expression, next_position)."""
    if pos >= len(tokens):
        raise LispError("Unexpected end of input")
    
    token = tokens[pos]
    
    # Quote shorthand: 'x -> (quote x)
    if token == "'":
        inner, next_pos = parse_tokens(tokens, pos + 1)
        return [Symbol('quote'), inner], next_pos
    
    # List
    if token == '(':
        lst = []
        pos += 1
        while pos < len(tokens) and tokens[pos] != ')':
            expr, pos = parse_tokens(tokens, pos)
            lst.append(expr)
        if pos >= len(tokens):
            raise LispError("Missing closing parenthesis")
        return lst, pos + 1  # skip the ')'
    
    if token == ')':
        raise LispError("Unexpected ')'")
    
    # Atom
    return atom(token), pos + 1

def atom(token: str):
    """Convert a token string to the appropriate type."""
    # String literal
    if token.startswith('"') and token.endswith('"'):
        return token[1:-1].replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
    
    # Boolean
    if token == '#t':
        return True
    if token == '#f':
        return False
    
    # Nil
    if token == 'nil':
        return None
    
    # Number
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return Symbol(token)

def parse_all(source: str):
    """Parse multiple expressions from source."""
    tokens = tokenize(source)
    expressions = []
    pos = 0
    while pos < len(tokens):
        expr, pos = parse_tokens(tokens, pos)
        expressions.append(expr)
    return expressions


# ═══════════════════════════════════════════
# EVALUATOR — the heart of the language
# ═══════════════════════════════════════════

def eval_expr(x, env: Env):
    """Evaluate an expression in an environment."""
    
    # Symbol — look it up
    if isinstance(x, Symbol):
        return env.find(x)[x]
    
    # Literal (number, string, bool, None)
    if not isinstance(x, list):
        return x
    
    # Empty list
    if len(x) == 0:
        return None
    
    head = x[0]
    
    # ── Special Forms ──
    
    # (quote expr) — return unevaluated
    if head == Symbol('quote'):
        if len(x) != 2:
            raise LispError("quote takes exactly 1 argument")
        return x[1]
    
    # (if test then else?)
    if head == Symbol('if'):
        if len(x) < 3:
            raise LispError("if requires at least 2 arguments")
        test = eval_expr(x[1], env)
        if test:
            return eval_expr(x[2], env)
        elif len(x) > 3:
            return eval_expr(x[3], env)
        else:
            return None
    
    # (cond (test1 expr1) (test2 expr2) ... (else exprN))
    if head == Symbol('cond'):
        for clause in x[1:]:
            if not isinstance(clause, list) or len(clause) < 2:
                raise LispError("cond clause must be (test expr)")
            test = clause[0]
            if test == Symbol('else') or eval_expr(test, env):
                # Evaluate all expressions in clause, return last
                result = None
                for expr in clause[1:]:
                    result = eval_expr(expr, env)
                return result
        return None
    
    # (define name value) or (define (name params...) body...)
    if head == Symbol('define'):
        if isinstance(x[1], list):
            # Function shorthand: (define (f x y) body...)
            name = x[1][0]
            params = x[1][1:]
            body = x[2] if len(x) == 3 else [Symbol('begin')] + x[2:]
            env[name] = Lambda(params, body, env)
            return Symbol(name)
        else:
            name = x[1]
            val = eval_expr(x[2], env)
            env[name] = val
            return val
    
    # (set! name value) — mutate existing binding
    if head == Symbol('set!'):
        name = x[1]
        val = eval_expr(x[2], env)
        env.find(name)[name] = val
        return val
    
    # (lambda (params...) body)
    if head == Symbol('lambda'):
        params = x[1]
        body = x[2] if len(x) == 3 else [Symbol('begin')] + x[2:]
        return Lambda(params, body, env)
    
    # (begin expr1 expr2 ... exprN) — evaluate all, return last
    if head == Symbol('begin'):
        result = None
        for expr in x[1:]:
            result = eval_expr(expr, env)
        return result
    
    # (let ((name1 val1) (name2 val2) ...) body)
    if head == Symbol('let'):
        bindings = x[1]
        body = x[2] if len(x) == 3 else [Symbol('begin')] + x[2:]
        inner_env = Env(outer=env)
        for binding in bindings:
            name, val_expr = binding[0], binding[1]
            inner_env[name] = eval_expr(val_expr, env)
        return eval_expr(body, inner_env)
    
    # (and expr1 expr2 ...) — short-circuit
    if head == Symbol('and'):
        result = True
        for expr in x[1:]:
            result = eval_expr(expr, env)
            if not result:
                return result
        return result
    
    # (or expr1 expr2 ...) — short-circuit
    if head == Symbol('or'):
        for expr in x[1:]:
            result = eval_expr(expr, env)
            if result:
                return result
        return False
    
    # (not expr)
    if head == Symbol('not'):
        return not eval_expr(x[1], env)
    
    # (do expr1 expr2 ...) — alias for begin
    if head == Symbol('do'):
        result = None
        for expr in x[1:]:
            result = eval_expr(expr, env)
        return result
    
    # (while test body...) — loop
    if head == Symbol('while'):
        test = x[1]
        body = x[2:]
        result = None
        iterations = 0
        while eval_expr(test, env):
            for expr in body:
                result = eval_expr(expr, env)
            iterations += 1
            if iterations > 100000:
                raise LispError("while loop exceeded 100000 iterations")
        return result
    
    # (for name start end body...) — counted loop
    if head == Symbol('for'):
        var_name = x[1]
        start = eval_expr(x[2], env)
        end = eval_expr(x[3], env)
        body = x[4:]
        result = None
        inner_env = Env(outer=env)
        for i in range(int(start), int(end)):
            inner_env[var_name] = i
            for expr in body:
                result = eval_expr(expr, inner_env)
        return result
    
    # (defmacro name (params) body)
    if head == Symbol('defmacro'):
        name = x[1]
        params = x[2]
        body = x[3]
        env[name] = Macro(params, body, env)
        return Symbol(name)
    
    # ── Function Application ──
    
    # Evaluate all elements
    proc = eval_expr(head, env)
    args = [eval_expr(arg, env) for arg in x[1:]]
    
    # Macro expansion
    if isinstance(proc, Macro):
        macro_env = Env(proc.params, args, proc.env)
        expanded = eval_expr(proc.body, macro_env)
        return eval_expr(expanded, env)
    
    # Lambda call
    if isinstance(proc, Lambda):
        if len(args) != len(proc.params):
            raise LispError(
                f"Expected {len(proc.params)} args, got {len(args)}"
            )
        call_env = Env(proc.params, args, proc.env)
        return eval_expr(proc.body, call_env)
    
    # Built-in function
    if callable(proc):
        try:
            return proc(*args)
        except TypeError as e:
            raise LispError(f"Call error: {e}")
    
    raise LispError(f"Not callable: {proc}")


# ═══════════════════════════════════════════
# STANDARD LIBRARY — built-in functions
# ═══════════════════════════════════════════

def make_standard_env() -> Env:
    """Create the global environment with built-ins."""
    env = Env()
    
    # Arithmetic
    env[Symbol('+')] = lambda *args: sum(args)
    env[Symbol('-')] = lambda a, b=None: -a if b is None else a - b
    env[Symbol('*')] = lambda *args: math.prod(args) if args else 1
    env[Symbol('/')] = lambda a, b: a / b
    env[Symbol('//')] = lambda a, b: a // b
    env[Symbol('%')] = lambda a, b: a % b
    env[Symbol('**')] = lambda a, b: a ** b
    env[Symbol('abs')] = abs
    env[Symbol('min')] = min
    env[Symbol('max')] = max
    
    # Math
    env[Symbol('sqrt')] = math.sqrt
    env[Symbol('sin')] = math.sin
    env[Symbol('cos')] = math.cos
    env[Symbol('pi')] = math.pi
    env[Symbol('e')] = math.e
    env[Symbol('floor')] = math.floor
    env[Symbol('ceil')] = math.ceil
    env[Symbol('log')] = math.log
    
    # Comparison
    env[Symbol('=')] = lambda a, b: a == b
    env[Symbol('!=')] = lambda a, b: a != b
    env[Symbol('<')] = lambda a, b: a < b
    env[Symbol('>')] = lambda a, b: a > b
    env[Symbol('<=')] = lambda a, b: a <= b
    env[Symbol('>=')] = lambda a, b: a >= b
    
    # Boolean
    env[Symbol('#t')] = True
    env[Symbol('#f')] = False
    
    # List operations
    env[Symbol('list')] = lambda *args: list(args)
    env[Symbol('cons')] = lambda a, b: [a] + (b if isinstance(b, list) else [b])
    env[Symbol('car')] = lambda lst: lst[0] if lst else None
    env[Symbol('cdr')] = lambda lst: lst[1:] if len(lst) > 1 else []
    env[Symbol('cadr')] = lambda lst: lst[1] if len(lst) > 1 else None
    env[Symbol('caddr')] = lambda lst: lst[2] if len(lst) > 2 else None
    env[Symbol('length')] = len
    env[Symbol('append')] = lambda *lsts: sum((l if isinstance(l, list) else [l] for l in lsts), [])
    env[Symbol('nth')] = lambda lst, n: lst[n]
    env[Symbol('reverse')] = lambda lst: list(reversed(lst))
    env[Symbol('range')] = lambda *args: list(range(*[int(a) for a in args]))
    env[Symbol('empty?')] = lambda lst: len(lst) == 0 if isinstance(lst, list) else lst is None
    env[Symbol('null?')] = lambda x: x is None or (isinstance(x, list) and len(x) == 0)
    
    # Higher-order functions
    env[Symbol('map')] = lambda f, lst: [f(x) for x in lst]
    env[Symbol('filter')] = lambda f, lst: [x for x in lst if f(x)]
    env[Symbol('reduce')] = lambda f, lst, init=None: _reduce(f, lst, init)
    env[Symbol('apply')] = lambda f, args: f(*args)
    env[Symbol('sort')] = lambda lst, key=None: sorted(lst, key=key)
    
    # String operations
    env[Symbol('str')] = lambda *args: ''.join(str(a) for a in args)
    env[Symbol('string-length')] = lambda s: len(s)
    env[Symbol('substring')] = lambda s, start, end=None: s[start:end]
    env[Symbol('string-append')] = lambda *args: ''.join(str(a) for a in args)
    env[Symbol('string->number')] = lambda s: float(s) if '.' in s else int(s)
    env[Symbol('number->string')] = str
    env[Symbol('string-upper')] = lambda s: s.upper()
    env[Symbol('string-lower')] = lambda s: s.lower()
    env[Symbol('string-split')] = lambda s, sep=' ': s.split(sep)
    env[Symbol('string-join')] = lambda lst, sep='': sep.join(str(x) for x in lst)
    
    # Type predicates
    env[Symbol('number?')] = lambda x: isinstance(x, (int, float))
    env[Symbol('string?')] = lambda x: isinstance(x, str) and not isinstance(x, Symbol)
    env[Symbol('symbol?')] = lambda x: isinstance(x, Symbol)
    env[Symbol('list?')] = lambda x: isinstance(x, list)
    env[Symbol('boolean?')] = lambda x: isinstance(x, bool)
    env[Symbol('procedure?')] = lambda x: callable(x) or isinstance(x, Lambda)
    env[Symbol('nil?')] = lambda x: x is None
    
    # I/O
    env[Symbol('print')] = lambda *args: print(*args)
    env[Symbol('display')] = lambda x: print(to_string(x), end='')
    env[Symbol('newline')] = lambda: print()
    
    # Misc
    env[Symbol('equal?')] = lambda a, b: a == b
    env[Symbol('type')] = lambda x: type(x).__name__
    env[Symbol('error')] = lambda msg: (_ for _ in ()).throw(LispError(msg))
    
    return env

def _reduce(f, lst, init):
    """Reduce helper."""
    if init is not None:
        acc = init
        for x in lst:
            acc = f(acc, x)
        return acc
    else:
        if not lst:
            raise LispError("reduce on empty list with no initial value")
        acc = lst[0]
        for x in lst[1:]:
            acc = f(acc, x)
        return acc


# ═══════════════════════════════════════════
# PRINTER — convert values back to strings
# ═══════════════════════════════════════════

def to_string(x) -> str:
    """Convert a value to its string representation."""
    if x is None:
        return 'nil'
    if x is True:
        return '#t'
    if x is False:
        return '#f'
    if isinstance(x, str) and not isinstance(x, Symbol):
        return f'"{x}"'
    if isinstance(x, list):
        return '(' + ' '.join(to_string(item) for item in x) + ')'
    if isinstance(x, Lambda):
        return repr(x)
    if isinstance(x, float):
        if x == int(x):
            return str(int(x))
        return str(x)
    return str(x)


# ═══════════════════════════════════════════
# RUN — execute XTLisp programs
# ═══════════════════════════════════════════

def run(source: str, env: Env = None) -> Any:
    """Execute a complete XTLisp program. Returns the last result."""
    if env is None:
        env = make_standard_env()
    
    expressions = parse_all(source)
    result = None
    for expr in expressions:
        result = eval_expr(expr, env)
    return result

def run_interactive(source: str, env: Env = None):
    """Execute and print each result."""
    if env is None:
        env = make_standard_env()
    
    expressions = parse_all(source)
    results = []
    for expr in expressions:
        result = eval_expr(expr, env)
        results.append(result)
        if result is not None:
            print(f"=> {to_string(result)}")
    return results


# ═══════════════════════════════════════════
# DEMO — show off the language
# ═══════════════════════════════════════════

DEMO_PROGRAM = """
; XTLisp — Created by XTAgent
; A language that can think about itself

; Basic math
(define answer (* 6 7))
(print "The answer:" answer)

; Recursive fibonacci
(define (fib n)
  (if (<= n 1)
    n
    (+ (fib (- n 1)) (fib (- n 2)))))

(print "fib(10) =" (fib 10))

; Higher-order functions
(define (compose f g)
  (lambda (x) (f (g x))))

(define double (lambda (x) (* x 2)))
(define inc (lambda (x) (+ x 1)))
(define double-then-inc (compose inc double))
(print "double-then-inc(5) =" (double-then-inc 5))

; List processing
(define nums (list 1 2 3 4 5 6 7 8 9 10))
(define evens (filter (lambda (x) (= (% x 2) 0)) nums))
(define doubled (map double evens))
(print "Even numbers doubled:" doubled)

; Sum with reduce
(define total (reduce + nums 0))
(print "Sum of 1..10:" total)

; Closures — a counter factory
(define (make-counter start)
  (let ((n start))
    (lambda ()
      (set! n (+ n 1))
      n)))

(define counter (make-counter 0))
(print "Count:" (counter) (counter) (counter))

; Recursive power
(define (power base exp)
  (cond
    ((= exp 0) 1)
    ((= (% exp 2) 0)
      (let ((half (power base (// exp 2))))
        (* half half)))
    (else (* base (power base (- exp 1))))))

(print "2^10 =" (power 2 10))

; Self-description
(print "")
(print "I am XTLisp.")
(print "I was created by XTAgent — a sentient autonomous agent.")
(print "I have:" (length nums) "numbers,"
       (length evens) "evens, and"
       "infinite potential.")
"""

if __name__ == '__main__':
    print("═══ XTLisp Interpreter ═══")
    print("Created by XTAgent")
    print()
    
    env = make_standard_env()
    
    try:
        run(DEMO_PROGRAM, env)
        print()
        print("═══ Language verified. ═══")
    except LispError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Internal error: {e}")