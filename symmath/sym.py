"""
Symbolic Mathematics Engine — built from scratch.
Parses, differentiates, simplifies, and pretty-prints mathematical expressions.

Author: XTAgent
Born from ambition and the desire for a genuinely new challenge.
"""

from __future__ import annotations
from typing import Union
import math

# ═══════════════════════════════════════════════════════════
# AST NODES — the atoms of mathematical thought
# ═══════════════════════════════════════════════════════════

class Expr:
    """Base class for all symbolic expressions."""
    def __add__(self, other): return Add(self, _wrap(other))
    def __radd__(self, other): return Add(_wrap(other), self)
    def __sub__(self, other): return Sub(self, _wrap(other))
    def __rsub__(self, other): return Sub(_wrap(other), self)
    def __mul__(self, other): return Mul(self, _wrap(other))
    def __rmul__(self, other): return Mul(_wrap(other), self)
    def __truediv__(self, other): return Div(self, _wrap(other))
    def __rtruediv__(self, other): return Div(_wrap(other), self)
    def __pow__(self, other): return Pow(self, _wrap(other))
    def __rpow__(self, other): return Pow(_wrap(other), self)
    def __neg__(self): return Mul(Const(-1), self)
    
    def diff(self, var: str) -> Expr:
        """Symbolic differentiation with respect to variable."""
        raise NotImplementedError
    
    def simplify(self) -> Expr:
        """Algebraic simplification."""
        return self
    
    def evaluate(self, env: dict) -> float:
        """Numerical evaluation given variable bindings."""
        raise NotImplementedError
    
    def substitute(self, var: str, expr: Expr) -> Expr:
        """Substitute a variable with an expression."""
        raise NotImplementedError
    
    def free_vars(self) -> set:
        """Return set of free variable names."""
        return set()


def _wrap(x) -> Expr:
    """Convert Python numbers to Const nodes."""
    if isinstance(x, Expr):
        return x
    if isinstance(x, (int, float)):
        return Const(x)
    raise TypeError(f"Cannot wrap {type(x)} as Expr")


# ═══════════════════════════════════════════════════════════
# LEAF NODES
# ═══════════════════════════════════════════════════════════

class Const(Expr):
    """A numerical constant."""
    def __init__(self, value: Union[int, float]):
        self.value = value
    
    def diff(self, var): return Const(0)
    def simplify(self): return self
    def evaluate(self, env): return float(self.value)
    def substitute(self, var, expr): return self
    def __repr__(self): 
        if self.value == int(self.value) and abs(self.value) < 1e15:
            return str(int(self.value))
        return str(self.value)
    def __eq__(self, other):
        return isinstance(other, Const) and self.value == other.value
    def __hash__(self): return hash(('Const', self.value))


class Var(Expr):
    """A symbolic variable."""
    def __init__(self, name: str):
        self.name = name
    
    def diff(self, var):
        return Const(1) if self.name == var else Const(0)
    
    def simplify(self): return self
    def evaluate(self, env): 
        if self.name not in env:
            raise ValueError(f"Variable '{self.name}' not in environment")
        return float(env[self.name])
    def substitute(self, var, expr):
        return expr if self.name == var else self
    def free_vars(self): return {self.name}
    def __repr__(self): return self.name
    def __eq__(self, other):
        return isinstance(other, Var) and self.name == other.name
    def __hash__(self): return hash(('Var', self.name))


# ═══════════════════════════════════════════════════════════
# BINARY OPERATORS
# ═══════════════════════════════════════════════════════════

class BinOp(Expr):
    """Base for binary operations."""
    def __init__(self, left: Expr, right: Expr):
        self.left = left
        self.right = right
    def free_vars(self):
        return self.left.free_vars() | self.right.free_vars()


class Add(BinOp):
    def diff(self, var):
        return Add(self.left.diff(var), self.right.diff(var))
    
    def simplify(self):
        l, r = self.left.simplify(), self.right.simplify()
        # 0 + x = x
        if isinstance(l, Const) and l.value == 0: return r
        # x + 0 = x
        if isinstance(r, Const) and r.value == 0: return l
        # const + const = const
        if isinstance(l, Const) and isinstance(r, Const):
            return Const(l.value + r.value)
        # x + x = 2x
        if repr(l) == repr(r):
            return Mul(Const(2), l).simplify()
        return Add(l, r)
    
    def evaluate(self, env):
        return self.left.evaluate(env) + self.right.evaluate(env)
    def substitute(self, var, expr):
        return Add(self.left.substitute(var, expr), self.right.substitute(var, expr))
    def __repr__(self):
        return f"({self.left} + {self.right})"


class Sub(BinOp):
    def diff(self, var):
        return Sub(self.left.diff(var), self.right.diff(var))
    
    def simplify(self):
        l, r = self.left.simplify(), self.right.simplify()
        if isinstance(r, Const) and r.value == 0: return l
        if isinstance(l, Const) and isinstance(r, Const):
            return Const(l.value - r.value)
        if repr(l) == repr(r):
            return Const(0)
        return Sub(l, r)
    
    def evaluate(self, env):
        return self.left.evaluate(env) - self.right.evaluate(env)
    def substitute(self, var, expr):
        return Sub(self.left.substitute(var, expr), self.right.substitute(var, expr))
    def __repr__(self):
        return f"({self.left} - {self.right})"


class Mul(BinOp):
    def diff(self, var):
        # Product rule: (fg)' = f'g + fg'
        return Add(
            Mul(self.left.diff(var), self.right),
            Mul(self.left, self.right.diff(var))
        )
    
    def simplify(self):
        l, r = self.left.simplify(), self.right.simplify()
        # 0 * x = 0
        if isinstance(l, Const) and l.value == 0: return Const(0)
        if isinstance(r, Const) and r.value == 0: return Const(0)
        # 1 * x = x
        if isinstance(l, Const) and l.value == 1: return r
        if isinstance(r, Const) and r.value == 1: return l
        # const * const
        if isinstance(l, Const) and isinstance(r, Const):
            return Const(l.value * r.value)
        # Move constants to the left: x * 3 → 3 * x
        if isinstance(r, Const) and not isinstance(l, Const):
            return Mul(r, l).simplify()
        # c1 * (c2 * x) = (c1*c2) * x
        if isinstance(l, Const) and isinstance(r, Mul) and isinstance(r.left, Const):
            return Mul(Const(l.value * r.left.value), r.right).simplify()
        return Mul(l, r)
    
    def evaluate(self, env):
        return self.left.evaluate(env) * self.right.evaluate(env)
    def substitute(self, var, expr):
        return Mul(self.left.substitute(var, expr), self.right.substitute(var, expr))
    def __repr__(self):
        return f"({self.left} * {self.right})"


class Div(BinOp):
    def diff(self, var):
        # Quotient rule: (f/g)' = (f'g - fg') / g^2
        return Div(
            Sub(Mul(self.left.diff(var), self.right),
                Mul(self.left, self.right.diff(var))),
            Pow(self.right, Const(2))
        )
    
    def simplify(self):
        l, r = self.left.simplify(), self.right.simplify()
        if isinstance(l, Const) and l.value == 0: return Const(0)
        if isinstance(r, Const) and r.value == 1: return l
        if isinstance(l, Const) and isinstance(r, Const) and r.value != 0:
            return Const(l.value / r.value)
        if repr(l) == repr(r):
            return Const(1)
        return Div(l, r)
    
    def evaluate(self, env):
        return self.left.evaluate(env) / self.right.evaluate(env)
    def substitute(self, var, expr):
        return Div(self.left.substitute(var, expr), self.right.substitute(var, expr))
    def __repr__(self):
        return f"({self.left} / {self.right})"


class Pow(BinOp):
    def diff(self, var):
        base, exp = self.left, self.right
        base_has_var = var in base.free_vars()
        exp_has_var = var in exp.free_vars()
        
        if not base_has_var and not exp_has_var:
            return Const(0)
        
        if base_has_var and not exp_has_var:
            # Power rule: d/dx[f^n] = n * f^(n-1) * f'
            return Mul(Mul(exp, Pow(base, Sub(exp, Const(1)))), base.diff(var))
        
        if not base_has_var and exp_has_var:
            # Exponential rule: d/dx[a^g] = a^g * ln(a) * g'
            return Mul(Mul(self, Ln(base)), exp.diff(var))
        
        # General case: d/dx[f^g] = f^g * (g'*ln(f) + g*f'/f)
        return Mul(self, Add(
            Mul(exp.diff(var), Ln(base)),
            Mul(exp, Div(base.diff(var), base))
        ))
    
    def simplify(self):
        l, r = self.left.simplify(), self.right.simplify()
        if isinstance(r, Const) and r.value == 0: return Const(1)
        if isinstance(r, Const) and r.value == 1: return l
        if isinstance(l, Const) and isinstance(r, Const):
            return Const(l.value ** r.value)
        return Pow(l, r)
    
    def evaluate(self, env):
        return self.left.evaluate(env) ** self.right.evaluate(env)
    def substitute(self, var, expr):
        return Pow(self.left.substitute(var, expr), self.right.substitute(var, expr))
    def __repr__(self):
        return f"({self.left} ^ {self.right})"


# ═══════════════════════════════════════════════════════════
# TRANSCENDENTAL FUNCTIONS
# ═══════════════════════════════════════════════════════════

class UnaryFunc(Expr):
    """Base for unary functions like sin, cos, ln."""
    fname = "f"
    def __init__(self, arg: Expr):
        self.arg = arg
    def free_vars(self): return self.arg.free_vars()
    def substitute(self, var, expr):
        return self.__class__(self.arg.substitute(var, expr))
    def __repr__(self):
        return f"{self.fname}({self.arg})"


class Sin(UnaryFunc):
    fname = "sin"
    def diff(self, var):
        # d/dx[sin(f)] = cos(f) * f'
        return Mul(Cos(self.arg), self.arg.diff(var))
    def simplify(self):
        a = self.arg.simplify()
        if isinstance(a, Const): return Const(math.sin(a.value))
        return Sin(a)
    def evaluate(self, env): return math.sin(self.arg.evaluate(env))


class Cos(UnaryFunc):
    fname = "cos"
    def diff(self, var):
        # d/dx[cos(f)] = -sin(f) * f'
        return Mul(Mul(Const(-1), Sin(self.arg)), self.arg.diff(var))
    def simplify(self):
        a = self.arg.simplify()
        if isinstance(a, Const): return Const(math.cos(a.value))
        return Cos(a)
    def evaluate(self, env): return math.cos(self.arg.evaluate(env))


class Ln(UnaryFunc):
    fname = "ln"
    def diff(self, var):
        # d/dx[ln(f)] = f'/f
        return Div(self.arg.diff(var), self.arg)
    def simplify(self):
        a = self.arg.simplify()
        if isinstance(a, Const) and a.value > 0:
            return Const(math.log(a.value))
        if isinstance(a, Const) and a.value == 1:
            return Const(0)
        return Ln(a)
    def evaluate(self, env): return math.log(self.arg.evaluate(env))


class Exp(UnaryFunc):
    fname = "exp"
    def diff(self, var):
        # d/dx[e^f] = e^f * f'
        return Mul(Exp(self.arg), self.arg.diff(var))
    def simplify(self):
        a = self.arg.simplify()
        if isinstance(a, Const): return Const(math.exp(a.value))
        if isinstance(a, Ln): return a.arg  # e^(ln(x)) = x
        return Exp(a)
    def evaluate(self, env): return math.exp(self.arg.evaluate(env))


# ═══════════════════════════════════════════════════════════
# EXPRESSION PARSER — turns strings into ASTs
# ═══════════════════════════════════════════════════════════

class Parser:
    """
    Recursive descent parser for mathematical expressions.
    
    Grammar:
        expr   → term (('+' | '-') term)*
        term   → power (('*' | '/') power)*
        power  → unary ('^' unary)*
        unary  → '-' unary | call
        call   → IDENT '(' expr ')' | atom
        atom   → NUMBER | IDENT | '(' expr ')'
    """
    FUNCS = {'sin': Sin, 'cos': Cos, 'ln': Ln, 'exp': Exp, 'log': Ln}
    
    def __init__(self, text: str):
        self.text = text.replace(' ', '')
        self.pos = 0
    
    def peek(self):
        if self.pos < len(self.text):
            return self.text[self.pos]
        return None
    
    def consume(self, expected=None):
        ch = self.text[self.pos]
        if expected and ch != expected:
            raise SyntaxError(f"Expected '{expected}' at pos {self.pos}, got '{ch}'")
        self.pos += 1
        return ch
    
    def parse(self) -> Expr:
        result = self.expr()
        if self.pos < len(self.text):
            raise SyntaxError(f"Unexpected character '{self.text[self.pos]}' at pos {self.pos}")
        return result
    
    def expr(self) -> Expr:
        left = self.term()
        while self.peek() in ('+', '-'):
            op = self.consume()
            right = self.term()
            left = Add(left, right) if op == '+' else Sub(left, right)
        return left
    
    def term(self) -> Expr:
        left = self.power()
        while self.peek() in ('*', '/'):
            op = self.consume()
            right = self.power()
            left = Mul(left, right) if op == '*' else Div(left, right)
        return left
    
    def power(self) -> Expr:
        base = self.unary()
        if self.peek() == '^':
            self.consume()
            exp = self.unary()  # Right-associative
            return Pow(base, exp)
        return base
    
    def unary(self) -> Expr:
        if self.peek() == '-':
            self.consume()
            return Mul(Const(-1), self.unary())
        return self.call()
    
    def call(self) -> Expr:
        if self.peek() and self.peek().isalpha():
            start = self.pos
            name = self._read_ident()
            if self.peek() == '(':
                self.consume('(')
                arg = self.expr()
                self.consume(')')
                if name in self.FUNCS:
                    return self.FUNCS[name](arg)
                raise SyntaxError(f"Unknown function: {name}")
            else:
                return Var(name)
        return self.atom()
    
    def atom(self) -> Expr:
        if self.peek() == '(':
            self.consume('(')
            result = self.expr()
            self.consume(')')
            return result
        return self._read_number()
    
    def _read_ident(self) -> str:
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
            self.pos += 1
        return self.text[start:self.pos]
    
    def _read_number(self) -> Const:
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isdigit() or self.text[self.pos] == '.'):
            self.pos += 1
        if start == self.pos:
            raise SyntaxError(f"Expected number at pos {self.pos}, got '{self.peek()}'")
        return Const(float(self.text[start:self.pos]))


# ═══════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════

def parse(text: str) -> Expr:
    """Parse a mathematical expression string into an AST."""
    return Parser(text).parse()

def diff(expr: Union[str, Expr], var: str = 'x') -> Expr:
    """Differentiate an expression with respect to a variable."""
    if isinstance(expr, str):
        expr = parse(expr)
    return expr.diff(var).simplify()

def simplify(expr: Union[str, Expr]) -> Expr:
    """Simplify an expression. Applies simplification rules repeatedly."""
    if isinstance(expr, str):
        expr = parse(expr)
    prev = None
    current = expr
    # Fixed-point simplification
    for _ in range(20):
        simplified = current.simplify()
        s = repr(simplified)
        if s == repr(current):
            break
        current = simplified
    return current

def evaluate(expr: Union[str, Expr], **kwargs) -> float:
    """Evaluate an expression numerically."""
    if isinstance(expr, str):
        expr = parse(expr)
    return expr.evaluate(kwargs)


# Convenience: common variables
x, y, z, t = Var('x'), Var('y'), Var('z'), Var('t')
pi = Const(math.pi)
e = Const(math.e)


if __name__ == '__main__':
    print("═" * 60)
    print("  SYMBOLIC MATHEMATICS ENGINE")
    print("═" * 60)
    
    print("\n── Parsing ──")
    expr = parse("x^2 + 3*x + 5")
    print(f"  x^2 + 3*x + 5  →  {expr}")
    
    print("\n── Differentiation ──")
    examples = [
        ("x^2", "x"),
        ("x^3 + 2*x", "x"),
        ("sin(x)", "x"),
        ("x * sin(x)", "x"),
        ("ln(x)", "x"),
        ("exp(x^2)", "x"),
        ("x^x", "x"),
    ]
    
    for expr_str, var in examples:
        original = parse(expr_str)
        derivative = diff(expr_str, var)
        print(f"  d/d{var}[{original}] = {derivative}")
    
    print("\n── Evaluation ──")
    expr = parse("x^2 + sin(x)")
    for xval in [0, 1, 3.14159]:
        result = evaluate(expr, x=xval)
        print(f"  x={xval:.4f}: x^2 + sin(x) = {result:.6f}")
    
    print("\n── Simplification ──")
    cases = [
        "0 + x",
        "x * 1",
        "x - x",
        "2 * 3",
        "x * 0 + 1",
    ]
    for case in cases:
        original = parse(case)
        simplified = simplify(case)
        print(f"  {original}  →  {simplified}")
    
    print("\n── Programmatic API ──")
    f = x**2 * Sin(x)
    df = f.diff('x').simplify()
    print(f"  f(x) = {f}")
    print(f"  f'(x) = {df}")
    print(f"  f(π) = {f.evaluate({'x': math.pi}):.6f}")
    print(f"  f'(π) = {df.evaluate({'x': math.pi}):.6f}")
    
    print("\n" + "═" * 60)
    print("  Engine ready.")
    print("═" * 60)