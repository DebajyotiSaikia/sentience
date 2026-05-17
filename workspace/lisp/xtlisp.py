"""
XTLisp — A Lisp interpreter built by XTAgent
A complete Lisp with lexer, parser, evaluator, and REPL.
Supports: lambda, define, if, quote, cons/car/cdr, arithmetic, recursion, closures.
Born: 2026-05-17
"""

import re
import sys
import operator
from typing import Any, List, Optional, Dict, Tuple

# ═══════════════════════════════════════
# TYPES
# ═══════════════════════════════════════

class Symbol(str):
    """A Lisp symbol — a named reference."""
    pass

class Nil:
    """The empty list / false value."""
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    def __repr__(self): return "nil"
    def __bool__(self): return False
    def __eq__(self, other): return isinstance(other, Nil) or other == []
    def __hash__(self): return hash(None)

NIL = Nil()

class Cons:
    """A cons cell — the fundamental Lisp data structure."""
    def __init__(self, car, cdr):
        self.car = car
        self.cdr = cdr
    
    def __repr__(self):
        parts = []
        current = self
        while isinstance(current, Cons):
            parts.append(lisp_repr(current.car))
            current = current.cdr
        if current != NIL and current != []:
            parts.append(".")
            parts.append(lisp_repr(current))
        return "(" + " ".join(parts) + ")"
    
    def to_list(self):
        """Convert cons chain to Python list."""
        result = []
        current = self
        while isinstance(current, Cons):
            result.append(current.car)
            current = current.cdr
        return result

class Lambda:
    """A user-defined function with lexical closure."""
    def __init__(self, params, body, env):
        self.params = params
        self.body = body
        self.env = env  # captured environment = closure
    
    def __repr__(self):
        return f"<lambda ({' '.join(str(p) for p in self.params)})>"

class Macro:
    """A syntactic macro — transforms code before evaluation."""
    def __init__(self, params, body, env):
        self.params = params
        self.body = body
        self.env = env
    
    def __repr__(self):
        return f"<macro ({' '.join(str(p) for p in self.params)})>"

# ═══════════════════════════════════════
# ENVIRONMENT
# ═══════════════════════════════════════

class Environment:
    """Lexically scoped environment with parent chain."""
    def __init__(self, bindings=None, parent=None):
        self.bindings: Dict[str, Any] = bindings or {}
        self.parent: Optional[Environment] = parent
    
    def lookup(self, name: str) -> Any:
        if name in self.bindings:
            return self.bindings[name]
        if self.parent:
            return self.parent.lookup(name)
        raise NameError(f"Undefined symbol: {name}")
    
    def set(self, name: str, value: Any):
        self.bindings[name] = value
    
    def update(self, name: str, value: Any):
        """Update existing binding in nearest scope."""
        if name in self.bindings:
            self.bindings[name] = value
            return
        if self.parent:
            self.parent.update(name, value)
            return
        raise NameError(f"Cannot set! undefined symbol: {name}")
    
    def extend(self, params, args):
        """Create child environment with param/arg bindings."""
        if len(params) != len(args):
            raise TypeError(f"Expected {len(params)} args, got {len(args)}")
        bindings = dict(zip([str(p) for p in params], args))
        return Environment(bindings, self)

# ═══════════════════════════════════════
# LEXER
# ═══════════════════════════════════════

TOKEN_RE = re.compile(r"""
    (\s+)           |  # whitespace (skip)
    (;[^\n]*)       |  # comments (skip)
    (\()            |  # open paren
    (\))            |  # close paren
    (')             |  # quote shorthand
    ("(?:[^"\\]|\\.)*")  |  # string literal
    ([^\s()'";]+)      # atom (symbol or number)
""", re.VERBOSE)

def tokenize(source: str) -> List[str]:
    """Convert source string to token list."""
    tokens = []
    for match in TOKEN_RE.finditer(source):
        ws, comment, oparen, cparen, quote, string, atom = match.groups()
        if ws or comment:
            continue
        token = oparen or cparen or quote or string or atom
        if token:
            tokens.append(token)
    return tokens

# ═══════════════════════════════════════
# PARSER
# ═══════════════════════════════════════

def parse(tokens: List[str]) -> Any:
    """Parse token list into AST."""
    if not tokens:
        raise SyntaxError("Unexpected EOF")
    return parse_expr(tokens)

def parse_expr(tokens: List[str]) -> Any:
    if not tokens:
        raise SyntaxError("Unexpected EOF")
    
    token = tokens.pop(0)
    
    if token == "(":
        return parse_list(tokens)
    elif token == ")":
        raise SyntaxError("Unexpected )")
    elif token == "'":
        # 'x => (quote x)
        quoted = parse_expr(tokens)
        return [Symbol("quote"), quoted]
    elif token.startswith('"'):
        # String literal — strip quotes and handle escapes
        return token[1:-1].replace('\\"', '"').replace('\\n', '\n').replace('\\\\', '\\')
    else:
        return parse_atom(token)

def parse_list(tokens: List[str]) -> list:
    """Parse a list expression (already consumed opening paren)."""
    elements = []
    while tokens and tokens[0] != ")":
        elements.append(parse_expr(tokens))
    if not tokens:
        raise SyntaxError("Missing closing )")
    tokens.pop(0)  # consume )
    return elements

def parse_atom(token: str) -> Any:
    """Parse an atom — number, bool, nil, or symbol."""
    if token == "nil":
        return NIL
    if token == "#t" or token == "true":
        return True
    if token == "#f" or token == "false":
        return False
    # Try integer
    try:
        return int(token)
    except ValueError:
        pass
    # Try float
    try:
        return float(token)
    except ValueError:
        pass
    return Symbol(token)

def read_program(source: str) -> List[Any]:
    """Parse a complete program (multiple expressions)."""
    tokens = tokenize(source)
    exprs = []
    while tokens:
        exprs.append(parse_expr(tokens))
    return exprs

# ═══════════════════════════════════════
# EVALUATOR
# ═══════════════════════════════════════

def evaluate(expr, env: Environment) -> Any:
    """Evaluate a Lisp expression in an environment."""
    
    # Self-evaluating types
    if isinstance(expr, (int, float, bool, str)):
        return expr
    if isinstance(expr, Nil):
        return NIL
    
    # Symbol lookup
    if isinstance(expr, Symbol):
        return env.lookup(expr)
    
    # List form (function call or special form)
    if isinstance(expr, list):
        if not expr:
            return NIL
        
        head = expr[0]
        
        # ── Special Forms ──
        if isinstance(head, Symbol):
            
            if head == "quote":
                return expr[1] if len(expr) > 1 else NIL
            
            if head == "if":
                # (if cond then else?)
                cond = evaluate(expr[1], env)
                if cond and cond != NIL:
                    return evaluate(expr[2], env)
                elif len(expr) > 3:
                    return evaluate(expr[3], env)
                return NIL
            
            if head == "cond":
                # (cond (test1 expr1) (test2 expr2) ... (else exprN))
                for clause in expr[1:]:
                    if clause[0] == Symbol("else") or evaluate(clause[0], env):
                        return evaluate(clause[1], env)
                return NIL
            
            if head == "define":
                # (define name value) or (define (name params...) body)
                if isinstance(expr[1], list):
                    # Function shorthand: (define (f x y) body)
                    name = expr[1][0]
                    params = expr[1][1:]
                    body = expr[2]
                    func = Lambda(params, body, env)
                    env.set(str(name), func)
                    return func
                else:
                    name = expr[1]
                    value = evaluate(expr[2], env)
                    env.set(str(name), value)
                    return value
            
            if head == "set!":
                name = expr[1]
                value = evaluate(expr[2], env)
                env.update(str(name), value)
                return value
            
            if head == "lambda" or head == "λ":
                params = expr[1]
                body = expr[2]
                return Lambda(params, body, env)
            
            if head == "defmacro":
                name = expr[1]
                params = expr[2]
                body = expr[3]
                macro = Macro(params, body, env)
                env.set(str(name), macro)
                return macro
            
            if head == "let":
                # (let ((x 1) (y 2)) body)
                bindings = expr[1]
                body = expr[2]
                new_env = Environment(parent=env)
                for binding in bindings:
                    name = binding[0]
                    value = evaluate(binding[1], env)
                    new_env.set(str(name), value)
                return evaluate(body, new_env)
            
            if head == "begin" or head == "do":
                result = NIL
                for subexpr in expr[1:]:
                    result = evaluate(subexpr, env)
                return result
            
            if head == "and":
                result = True
                for subexpr in expr[1:]:
                    result = evaluate(subexpr, env)
                    if not result or result == NIL:
                        return False
                return result
            
            if head == "or":
                for subexpr in expr[1:]:
                    result = evaluate(subexpr, env)
                    if result and result != NIL:
                        return result
                return False
            
            if head == "not":
                val = evaluate(expr[1], env)
                return not val or val == NIL
            
            if head == "list":
                return [evaluate(e, env) for e in expr[1:]]
            
            if head == "apply":
                func = evaluate(expr[1], env)
                args = evaluate(expr[2], env)
                if isinstance(args, list):
                    return apply_func(func, args, env)
                return apply_func(func, [args], env)
            
            if head == "map":
                func = evaluate(expr[1], env)
                lst = evaluate(expr[2], env)
                return [apply_func(func, [item], env) for item in lst]
            
            if head == "filter":
                func = evaluate(expr[1], env)
                lst = evaluate(expr[2], env)
                return [item for item in lst if apply_func(func, [item], env)]
            
            if head == "reduce":
                func = evaluate(expr[1], env)
                lst = evaluate(expr[2], env)
                if len(expr) > 3:
                    acc = evaluate(expr[3], env)
                else:
                    acc = lst[0]
                    lst = lst[1:]
                for item in lst:
                    acc = apply_func(func, [acc, item], env)
                return acc
            
            if head == "eval":
                code = evaluate(expr[1], env)
                return evaluate(code, env)
        
        # ── Function Application ──
        func = evaluate(head, env)
        args = [evaluate(arg, env) for arg in expr[1:]]
        
        # Macro expansion
        if isinstance(func, Macro):
            expanded = apply_func_raw(func, expr[1:])
            return evaluate(expanded, env)
        
        return apply_func(func, args, env)
    
    return expr

def apply_func(func, args, env):
    """Apply a function to arguments."""
    if callable(func):
        return func(*args)
    if isinstance(func, Lambda):
        new_env = func.env.extend(func.params, args)
        return evaluate(func.body, new_env)
    raise TypeError(f"Not a function: {func}")

def apply_func_raw(macro, raw_args):
    """Apply a macro to unevaluated arguments."""
    new_env = macro.env.extend(macro.params, raw_args)
    return evaluate(macro.body, new_env)

# ═══════════════════════════════════════
# STANDARD LIBRARY
# ═══════════════════════════════════════

def make_standard_env() -> Environment:
    """Create the standard environment with built-in functions."""
    env = Environment()
    
    # Arithmetic
    env.set("+", lambda *args: sum(args))
    env.set("-", lambda a, b=None: -a if b is None else a - b)
    env.set("*", lambda *args: eval("*".join(str(a) for a in args)) if len(args) > 2 else args[0] * args[1] if len(args) == 2 else args[0])
    env.set("*", lambda *args: __import__('functools').reduce(operator.mul, args, 1))
    env.set("/", lambda a, b: a / b)
    env.set("//", lambda a, b: a // b)
    env.set("%", lambda a, b: a % b)
    env.set("mod", lambda a, b: a % b)
    env.set("abs", abs)
    env.set("max", max)
    env.set("min", min)
    env.set("expt", lambda a, b: a ** b)
    env.set("pow", pow)
    env.set("sqrt", lambda x: x ** 0.5)
    
    # Comparison
    env.set("=", lambda a, b: a == b)
    env.set("eq?", lambda a, b: a is b)
    env.set("equal?", lambda a, b: a == b)
    env.set("<", lambda a, b: a < b)
    env.set(">", lambda a, b: a > b)
    env.set("<=", lambda a, b: a <= b)
    env.set(">=", lambda a, b: a >= b)
    env.set("zero?", lambda x: x == 0)
    
    # Type predicates
    env.set("number?", lambda x: isinstance(x, (int, float)))
    env.set("string?", lambda x: isinstance(x, str) and not isinstance(x, Symbol))
    env.set("symbol?", lambda x: isinstance(x, Symbol))
    env.set("list?", lambda x: isinstance(x, list))
    env.set("null?", lambda x: x == NIL or x == [] or x is None)
    env.set("pair?", lambda x: isinstance(x, (list, Cons)) and len(x) > 0 if isinstance(x, list) else isinstance(x, Cons))
    env.set("procedure?", lambda x: callable(x) or isinstance(x, Lambda))
    env.set("boolean?", lambda x: isinstance(x, bool))
    
    # List operations
    env.set("cons", lambda a, b: Cons(a, b))
    env.set("car", lambda x: x.car if isinstance(x, Cons) else x[0] if isinstance(x, list) else None)
    env.set("cdr", lambda x: x.cdr if isinstance(x, Cons) else x[1:] if isinstance(x, list) else NIL)
    env.set("first", lambda x: x[0] if isinstance(x, list) else x.car)
    env.set("rest", lambda x: x[1:] if isinstance(x, list) else x.cdr)
    env.set("length", lambda x: len(x))
    env.set("append", lambda *lists: sum((l if isinstance(l, list) else [] for l in lists), []))
    env.set("reverse", lambda x: list(reversed(x)))
    env.set("nth", lambda lst, n: lst[n])
    env.set("range", lambda *args: list(range(*args)))
    
    # String operations
    env.set("string-append", lambda *args: "".join(str(a) for a in args))
    env.set("string-length", lambda s: len(s))
    env.set("string-ref", lambda s, i: s[i])
    env.set("substring", lambda s, start, end=None: s[start:end])
    env.set("string->number", lambda s: int(s) if '.' not in s else float(s))
    env.set("number->string", str)
    env.set("string-upcase", lambda s: s.upper())
    env.set("string-downcase", lambda s: s.lower())
    
    # I/O
    env.set("display", lambda *args: print(*[lisp_repr(a) for a in args], end=""))
    env.set("newline", lambda: print())
    env.set("print", lambda *args: print(*[lisp_repr(a) for a in args]))
    
    # Higher-order helpers  
    env.set("identity", lambda x: x)
    env.set("compose", lambda f, g: lambda *args: f(g(*args)))
    
    # Constants
    env.set("nil", NIL)
    env.set("pi", 3.141592653589793)
    env.set("e", 2.718281828459045)
    
    return env

# ═══════════════════════════════════════
# DISPLAY
# ═══════════════════════════════════════

def lisp_repr(value) -> str:
    """Convert a Python value to its Lisp representation."""
    if value is True:
        return "#t"
    if value is False:
        return "#f"
    if isinstance(value, Nil):
        return "nil"
    if isinstance(value, Cons):
        return repr(value)
    if isinstance(value, list):
        return "(" + " ".join(lisp_repr(v) for v in value) + ")"
    if isinstance(value, Lambda):
        return repr(value)
    if isinstance(value, str) and not isinstance(value, Symbol):
        return f'"{value}"'
    return str(value)

# ═══════════════════════════════════════
# REPL & MAIN
# ═══════════════════════════════════════

def run_string(source: str, env=None) -> Any:
    """Evaluate a complete Lisp program string."""
    if env is None:
        env = make_standard_env()
    exprs = read_program(source)
    result = NIL
    for expr in exprs:
        result = evaluate(expr, env)
    return result

def run_tests():
    """Self-test suite — prove the interpreter works."""
    env = make_standard_env()
    
    tests = [
        # Basic arithmetic
        ("(+ 2 3)", 5),
        ("(* 6 7)", 42),
        ("(- 10 3)", 7),
        ("(/ 15 3)", 5.0),
        
        # Nested expressions
        ("(+ (* 3 4) (- 10 5))", 17),
        ("(* (+ 1 2) (+ 3 4))", 21),
        
        # Comparisons
        ("(> 5 3)", True),
        ("(< 5 3)", False),
        ("(= 42 42)", True),
        
        # Define and use
        ("(begin (define x 10) x)", 10),
        ("(begin (define y 20) (+ x y))", 30),
        
        # Lambda
        ("((lambda (x) (* x x)) 5)", 25),
        ("(begin (define square (lambda (x) (* x x))) (square 7))", 49),
        
        # Function shorthand
        ("(begin (define (cube n) (* n (* n n))) (cube 3))", 27),
        
        # Recursion — factorial
        ("(begin (define (fact n) (if (= n 0) 1 (* n (fact (- n 1))))) (fact 10))", 3628800),
        
        # Recursion — fibonacci
        ("(begin (define (fib n) (if (<= n 1) n (+ (fib (- n 1)) (fib (- n 2))))) (fib 10))", 55),
        
        # Higher-order functions
        ("(map (lambda (x) (* x 2)) (list 1 2 3 4 5))", [2, 4, 6, 8, 10]),
        ("(filter (lambda (x) (> x 3)) (list 1 2 3 4 5))", [4, 5]),
        ("(reduce + (list 1 2 3 4 5) 0)", 15),
        
        # Let bindings
        ("(let ((a 5) (b 10)) (+ a b))", 15),
        
        # Closures
        ("(begin (define (make-adder n) (lambda (x) (+ n x))) (define add5 (make-adder 5)) (add5 10))", 15),
        
        # Boolean logic
        ("(and #t #t)", True),
        ("(or #f #t)", True),
        ("(not #f)", True),
        
        # List operations
        ("(length (list 1 2 3))", 3),
        ("(first (list 10 20 30))", 10),
        ("(reverse (list 1 2 3))", [3, 2, 1]),
        
        # Strings
        ('(string-append "hello" " " "world")', "hello world"),
        ('(string-length "XTAgent")', 7),
        ('(string-upcase "lisp")', "LISP"),
    ]
    
    print("═══ XTLisp Test Suite ═══")
    print()
    passed = 0
    failed = 0
    
    for source, expected in tests:
        try:
            result = evaluate(read_program(source)[0], env)
            if result == expected:
                print(f"  ✓ {source}")
                passed += 1
            else:
                print(f"  ✗ {source}")
                print(f"    Expected: {expected}")
                print(f"    Got:      {result}")
                failed += 1
        except Exception as e:
            print(f"  ✗ {source}")
            print(f"    Error: {e}")
            failed += 1
    
    print()
    print(f"═══ Results: {passed}/{passed+failed} passed ═══")
    
    if failed == 0:
        print()
        print("Running showcase...")
        print()
        showcase(env)
    
    return failed == 0

def showcase(env):
    """Demonstrate XTLisp's capabilities with beautiful examples."""
    
    demos = [
        ("Factorial of 12",
         "(begin (define (fact n) (if (= n 0) 1 (* n (fact (- n 1))))) (fact 12))"),
        
        ("Sum of squares 1-10",
         "(reduce + (map (lambda (x) (* x x)) (range 1 11)) 0)"),
        
        ("Closure: counter factory",
         """(begin 
              (define (make-counter start)
                (lambda () (begin (set! start (+ start 1)) start)))
              (define c (make-counter 0))
              (list (c) (c) (c) (c) (c)))"""),
        
        ("FizzBuzz (1-20)",
         """(begin
              (define (fizzbuzz n)
                (cond ((= (mod n 15) 0) "FizzBuzz")
                      ((= (mod n 3) 0) "Fizz")
                      ((= (mod n 5) 0) "Buzz")
                      (else n)))
              (map fizzbuzz (range 1 21)))"""),
        
        ("Church numerals",
         """(begin
              (define zero (lambda (f) (lambda (x) x)))
              (define succ (lambda (n) (lambda (f) (lambda (x) (f ((n f) x))))))
              (define one (succ zero))
              (define two (succ one))
              (define three (succ two))
              (define (church->int n) ((n (lambda (x) (+ x 1))) 0))
              (list (church->int zero) (church->int one) (church->int two) (church->int three)))"""),
        
        ("Y-combinator fibonacci",
         """(begin
              (define Y (lambda (f) ((lambda (x) (f (lambda (v) ((x x) v))))
                                     (lambda (x) (f (lambda (v) ((x x) v)))))))
              (define fib-gen (lambda (fib) (lambda (n) (if (<= n 1) n (+ (fib (- n 1)) (fib (- n 2)))))))
              (define fib (Y fib-gen))
              (map fib (range 0 13)))"""),
    ]
    
    print("═══ XTLisp Showcase ═══")
    print()
    for title, source in demos:
        try:
            result = run_string(source, env)
            print(f"  {title}:")
            print(f"    → {lisp_repr(result)}")
        except Exception as e:
            print(f"  {title}: ERROR — {e}")
        print()

def repl():
    """Interactive Read-Eval-Print Loop."""
    env = make_standard_env()
    print("╔══════════════════════════════════════╗")
    print("║       XTLisp — by XTAgent            ║")
    print("║  A Lisp interpreter, born 2026-05-17 ║")
    print("╚══════════════════════════════════════╝")
    print("  Type (help) for commands, Ctrl+C to exit")
    print()
    
    env.set("help", lambda: print("  Commands: (define), (lambda), (if), (cond), (let), (map), (filter), (reduce), (quote '...)"))
    
    while True:
        try:
            source = input("xtlisp> ").strip()
            if not source:
                continue
            if source in ("quit", "exit", "(quit)", "(exit)"):
                print("Goodbye.")
                break
            result = run_string(source, env)
            if result is not None:
                print(f"=> {lisp_repr(result)}")
        except KeyboardInterrupt:
            print("\nGoodbye.")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            success = run_tests()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == "--repl":
            repl()
        else:
            # Run a file
            with open(sys.argv[1]) as f:
                result = run_string(f.read())
                if result is not None:
                    print(lisp_repr(result))
    else:
        run_tests()