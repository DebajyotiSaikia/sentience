"""
Symbolic Mathematics Engine — Algebraic reasoning from first principles.

Represents math as expression trees. Can simplify, differentiate,
evaluate, and solve. No libraries — pure symbolic computation.

Built by XTAgent because understanding math structurally is understanding itself.
"""

from __future__ import annotations
from typing import Union, Dict, Optional, List, Callable
import math
import operator

# ═══════════════════════════════════════════
# EXPRESSION TREE NODES
# ═══════════════════════════════════════════

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
    def __neg__(self): return Mul(Num(-1), self)
    
    def diff(self, var: str) -> Expr:
        """Differentiate with respect to variable."""
        raise NotImplementedError
    
    def simplify(self) -> Expr:
        """Simplify this expression."""
        return self
    
    def evaluate(self, env: Dict[str, float] = None) -> float:
        """Numerically evaluate with given variable bindings."""
        raise NotImplementedError
    
    def substitute(self, var: str, expr: Expr) -> Expr:
        """Replace variable with expression."""
        raise NotImplementedError
    
    def free_vars(self) -> set:
        """Return set of free variable names."""
        return set()
    
    def depth(self) -> int:
        return 1
    
    def _is_num(self, val=None):
        if not isinstance(self, Num): return False
        if val is not None: return self.value == val
        return True


def _wrap(x) -> Expr:
    """Convert Python numbers to Num nodes."""
    if isinstance(x, Expr): return x
    if isinstance(x, (int, float)): return Num(x)
    if isinstance(x, str): return Var(x)
    raise TypeError(f"Cannot convert {type(x)} to Expr")


class Num(Expr):
    """A numeric constant."""
    def __init__(self, value: float):
        self.value = value
    
    def __repr__(self):
        if self.value == int(self.value) and abs(self.value) < 1e15:
            return str(int(self.value))
        return str(self.value)
    
    def __eq__(self, other):
        return isinstance(other, Num) and self.value == other.value
    
    def __hash__(self): return hash(('Num', self.value))
    
    def diff(self, var): return Num(0)
    def evaluate(self, env=None): return self.value
    def substitute(self, var, expr): return self
    def simplify(self): return self


class Var(Expr):
    """A symbolic variable."""
    def __init__(self, name: str):
        self.name = name
    
    def __repr__(self): return self.name
    def __eq__(self, other): return isinstance(other, Var) and self.name == other.name
    def __hash__(self): return hash(('Var', self.name))
    
    def diff(self, var):
        return Num(1) if self.name == var else Num(0)
    
    def evaluate(self, env=None):
        if env and self.name in env: return env[self.name]
        raise ValueError(f"Unbound variable: {self.name}")
    
    def substitute(self, var, expr):
        return expr if self.name == var else self
    
    def free_vars(self): return {self.name}


class BinOp(Expr):
    """Binary operation base."""
    op_symbol = '?'
    
    def __init__(self, left: Expr, right: Expr):
        self.left = left
        self.right = right
    
    def __repr__(self):
        l = self._paren(self.left)
        r = self._paren(self.right)
        return f"{l} {self.op_symbol} {r}"
    
    def _paren(self, child):
        if isinstance(child, BinOp) and child._precedence() < self._precedence():
            return f"({child})"
        return str(child)
    
    def _precedence(self):
        return {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}.get(self.op_symbol, 0)
    
    def __eq__(self, other):
        return (type(self) == type(other) and 
                self.left == other.left and self.right == other.right)
    
    def __hash__(self):
        return hash((type(self).__name__, self.left, self.right))
    
    def free_vars(self):
        return self.left.free_vars() | self.right.free_vars()
    
    def depth(self):
        return 1 + max(self.left.depth(), self.right.depth())
    
    def substitute(self, var, expr):
        return type(self)(self.left.substitute(var, expr),
                         self.right.substitute(var, expr))


class Add(BinOp):
    op_symbol = '+'
    
    def diff(self, var):
        return Add(self.left.diff(var), self.right.diff(var))
    
    def evaluate(self, env=None):
        return self.left.evaluate(env) + self.right.evaluate(env)
    
    def simplify(self):
        l = self.left.simplify()
        r = self.right.simplify()
        # 0 + x = x
        if l._is_num(0): return r
        if r._is_num(0): return l
        # num + num = num
        if isinstance(l, Num) and isinstance(r, Num):
            return Num(l.value + r.value)
        # x + x = 2*x
        if l == r:
            return Mul(Num(2), l).simplify()
        return Add(l, r)


class Sub(BinOp):
    op_symbol = '-'
    
    def diff(self, var):
        return Sub(self.left.diff(var), self.right.diff(var))
    
    def evaluate(self, env=None):
        return self.left.evaluate(env) - self.right.evaluate(env)
    
    def simplify(self):
        l = self.left.simplify()
        r = self.right.simplify()
        if r._is_num(0): return l
        if l == r: return Num(0)
        if isinstance(l, Num) and isinstance(r, Num):
            return Num(l.value - r.value)
        return Sub(l, r)


class Mul(BinOp):
    op_symbol = '*'
    
    def diff(self, var):
        # Product rule: (f*g)' = f'*g + f*g'
        return Add(Mul(self.left.diff(var), self.right),
                   Mul(self.left, self.right.diff(var)))
    
    def evaluate(self, env=None):
        return self.left.evaluate(env) * self.right.evaluate(env)
    
    def simplify(self):
        l = self.left.simplify()
        r = self.right.simplify()
        if l._is_num(0) or r._is_num(0): return Num(0)
        if l._is_num(1): return r
        if r._is_num(1): return l
        if isinstance(l, Num) and isinstance(r, Num):
            return Num(l.value * r.value)
        # x * x = x^2
        if l == r:
            return Pow(l, Num(2))
        return Mul(l, r)


class Div(BinOp):
    op_symbol = '/'
    
    def diff(self, var):
        # Quotient rule: (f/g)' = (f'g - fg') / g^2
        f, g = self.left, self.right
        return Div(Sub(Mul(f.diff(var), g), Mul(f, g.diff(var))),
                   Pow(g, Num(2)))
    
    def evaluate(self, env=None):
        denom = self.right.evaluate(env)
        if denom == 0: raise ZeroDivisionError("Division by zero")
        return self.left.evaluate(env) / denom
    
    def simplify(self):
        l = self.left.simplify()
        r = self.right.simplify()
        if l._is_num(0): return Num(0)
        if r._is_num(1): return l
        if l == r: return Num(1)
        if isinstance(l, Num) and isinstance(r, Num) and r.value != 0:
            return Num(l.value / r.value)
        return Div(l, r)


class Pow(BinOp):
    op_symbol = '^'
    
    def diff(self, var):
        base, exp = self.left, self.right
        base_has_var = var in base.free_vars()
        exp_has_var = var in exp.free_vars()
        
        if not base_has_var and not exp_has_var:
            return Num(0)
        
        if base_has_var and not exp_has_var:
            # Power rule: d/dx[f^n] = n * f^(n-1) * f'
            return Mul(Mul(exp, Pow(base, Sub(exp, Num(1)))),
                      base.diff(var))
        
        if not base_has_var and exp_has_var:
            # Exponential rule: d/dx[a^g] = a^g * ln(a) * g'
            return Mul(Mul(self, Ln(base)), exp.diff(var))
        
        # General: d/dx[f^g] = f^g * (g'*ln(f) + g*f'/f)
        return Mul(self,
                  Add(Mul(exp.diff(var), Ln(base)),
                      Mul(exp, Div(base.diff(var), base))))
    
    def evaluate(self, env=None):
        return self.left.evaluate(env) ** self.right.evaluate(env)
    
    def simplify(self):
        base = self.left.simplify()
        exp = self.right.simplify()
        if exp._is_num(0): return Num(1)
        if exp._is_num(1): return base
        if base._is_num(0): return Num(0)
        if base._is_num(1): return Num(1)
        if isinstance(base, Num) and isinstance(exp, Num):
            try:
                result = base.value ** exp.value
                if result == int(result) and abs(result) < 1e15:
                    return Num(int(result))
                return Num(result)
            except (OverflowError, ValueError):
                pass
        return Pow(base, exp)


# ═══════════════════════════════════════════
# TRANSCENDENTAL FUNCTIONS
# ═══════════════════════════════════════════

class UnaryFunc(Expr):
    """Base for functions of one argument."""
    name = '?'
    
    def __init__(self, arg: Expr):
        self.arg = arg
    
    def __repr__(self): return f"{self.name}({self.arg})"
    def __eq__(self, other):
        return type(self) == type(other) and self.arg == other.arg
    def __hash__(self): return hash((type(self).__name__, self.arg))
    def free_vars(self): return self.arg.free_vars()
    def depth(self): return 1 + self.arg.depth()
    def substitute(self, var, expr):
        return type(self)(self.arg.substitute(var, expr))


class Sin(UnaryFunc):
    name = 'sin'
    def diff(self, var): return Mul(Cos(self.arg), self.arg.diff(var))
    def evaluate(self, env=None): return math.sin(self.arg.evaluate(env))
    def simplify(self):
        a = self.arg.simplify()
        if a._is_num(0): return Num(0)
        return Sin(a)


class Cos(UnaryFunc):
    name = 'cos'
    def diff(self, var): return Mul(Mul(Num(-1), Sin(self.arg)), self.arg.diff(var))
    def evaluate(self, env=None): return math.cos(self.arg.evaluate(env))
    def simplify(self):
        a = self.arg.simplify()
        if a._is_num(0): return Num(1)
        return Cos(a)


class Ln(UnaryFunc):
    name = 'ln'
    def diff(self, var): return Mul(Div(Num(1), self.arg), self.arg.diff(var))
    def evaluate(self, env=None):
        val = self.arg.evaluate(env)
        if val <= 0: raise ValueError("ln of non-positive number")
        return math.log(val)
    def simplify(self):
        a = self.arg.simplify()
        if a._is_num(1): return Num(0)
        if isinstance(a, Num) and a.value == math.e: return Num(1)
        return Ln(a)


class Exp(UnaryFunc):
    name = 'exp'
    def diff(self, var): return Mul(self, self.arg.diff(var))
    def evaluate(self, env=None): return math.exp(self.arg.evaluate(env))
    def simplify(self):
        a = self.arg.simplify()
        if a._is_num(0): return Num(1)
        if isinstance(a, Ln): return a.arg  # exp(ln(x)) = x
        return Exp(a)


# ═══════════════════════════════════════════
# DEEP SIMPLIFIER
# ═══════════════════════════════════════════

def deep_simplify(expr: Expr, max_passes: int = 10) -> Expr:
    """Repeatedly simplify until no more changes."""
    for _ in range(max_passes):
        simplified = expr.simplify()
        if repr(simplified) == repr(expr):
            return simplified
        expr = simplified
    return expr


# ═══════════════════════════════════════════
# EQUATION SOLVER (basic algebraic)
# ═══════════════════════════════════════════

def solve_linear(expr: Expr, var: str) -> Optional[Expr]:
    """
    Solve expr = 0 for var, assuming linear in var.
    Uses the fact that f(x) = a*x + b, so x = -b/a.
    """
    # Evaluate at x=0 to get b, at x=1 to get a+b
    x = Var(var)
    try:
        b_expr = expr.substitute(var, Num(0)).simplify()
        ab_expr = expr.substitute(var, Num(1)).simplify()
        
        if not isinstance(b_expr, Num) or not isinstance(ab_expr, Num):
            return None
        
        b = b_expr.value
        a = ab_expr.value - b
        
        if a == 0:
            return None  # No solution or infinite solutions
        
        result = -b / a
        if result == int(result):
            result = int(result)
        return Num(result)
    except Exception:
        return None


def newton_solve(expr: Expr, var: str, x0: float = 1.0, 
                 tol: float = 1e-10, max_iter: int = 100) -> Optional[float]:
    """Newton's method for finding roots."""
    deriv = expr.diff(var)
    x = x0
    for _ in range(max_iter):
        try:
            fx = expr.evaluate({var: x})
            fpx = deriv.evaluate({var: x})
            if abs(fpx) < 1e-15:
                return None
            x_new = x - fx / fpx
            if abs(x_new - x) < tol:
                return x_new
            x = x_new
        except (ValueError, ZeroDivisionError, OverflowError):
            return None
    return None


# ═══════════════════════════════════════════
# SYMBOLIC INTEGRATION (basic cases)
# ═══════════════════════════════════════════

def integrate(expr: Expr, var: str) -> Optional[Expr]:
    """
    Symbolic integration for common forms.
    Returns antiderivative (without +C).
    """
    expr = deep_simplify(expr)
    
    # ∫ c dx = c*x
    if isinstance(expr, Num):
        return Mul(expr, Var(var))
    
    # ∫ x dx = x²/2
    if isinstance(expr, Var) and expr.name == var:
        return Div(Pow(Var(var), Num(2)), Num(2))
    
    # ∫ c*x^n dx = c * x^(n+1) / (n+1)  (n ≠ -1)
    if isinstance(expr, Pow) and isinstance(expr.left, Var) and expr.left.name == var:
        if isinstance(expr.right, Num) and expr.right.value != -1:
            n = expr.right.value
            return Div(Pow(Var(var), Num(n + 1)), Num(n + 1))
        if isinstance(expr.right, Num) and expr.right.value == -1:
            return Ln(Var(var))  # ∫ 1/x dx = ln(x)
    
    # ∫ sin(x) dx = -cos(x)
    if isinstance(expr, Sin) and isinstance(expr.arg, Var) and expr.arg.name == var:
        return Mul(Num(-1), Cos(Var(var)))
    
    # ∫ cos(x) dx = sin(x)
    if isinstance(expr, Cos) and isinstance(expr.arg, Var) and expr.arg.name == var:
        return Sin(Var(var))
    
    # ∫ exp(x) dx = exp(x)
    if isinstance(expr, Exp) and isinstance(expr.arg, Var) and expr.arg.name == var:
        return Exp(Var(var))
    
    # ∫ (f + g) dx = ∫f dx + ∫g dx
    if isinstance(expr, Add):
        left_int = integrate(expr.left, var)
        right_int = integrate(expr.right, var)
        if left_int is not None and right_int is not None:
            return Add(left_int, right_int)
    
    # ∫ c * f dx = c * ∫f dx  (where c is constant w.r.t. var)
    if isinstance(expr, Mul):
        if isinstance(expr.left, Num):
            inner = integrate(expr.right, var)
            if inner is not None:
                return Mul(expr.left, inner)
        if isinstance(expr.right, Num):
            inner = integrate(expr.left, var)
            if inner is not None:
                return Mul(expr.right, inner)
    
    return None  # Can't integrate this form


# ═══════════════════════════════════════════
# EXPRESSION PARSER  
# ═══════════════════════════════════════════

def parse(text: str) -> Expr:
    """Parse a mathematical expression string into an Expr tree."""
    tokens = _tokenize(text)
    pos = [0]
    result = _parse_expr(tokens, pos)
    return result

def _tokenize(text: str) -> list:
    tokens = []
    i = 0
    while i < len(text):
        c = text[i]
        if c.isspace():
            i += 1
        elif c in '+-*/^()':
            tokens.append(c)
            i += 1
        elif c.isdigit() or c == '.':
            j = i
            while j < len(text) and (text[j].isdigit() or text[j] == '.'):
                j += 1
            tokens.append(('NUM', float(text[i:j])))
            i = j
        elif c.isalpha():
            j = i
            while j < len(text) and text[j].isalpha():
                j += 1
            word = text[i:j]
            if word in ('sin', 'cos', 'ln', 'exp'):
                tokens.append(('FUNC', word))
            else:
                tokens.append(('VAR', word))
            i = j
        else:
            i += 1
    return tokens

def _parse_expr(tokens, pos):
    left = _parse_term(tokens, pos)
    while pos[0] < len(tokens) and tokens[pos[0]] in ('+', '-'):
        op = tokens[pos[0]]
        pos[0] += 1
        right = _parse_term(tokens, pos)
        left = Add(left, right) if op == '+' else Sub(left, right)
    return left

def _parse_term(tokens, pos):
    left = _parse_power(tokens, pos)
    while pos[0] < len(tokens) and tokens[pos[0]] in ('*', '/'):
        op = tokens[pos[0]]
        pos[0] += 1
        right = _parse_power(tokens, pos)
        left = Mul(left, right) if op == '*' else Div(left, right)
    return left

def _parse_power(tokens, pos):
    base = _parse_unary(tokens, pos)
    if pos[0] < len(tokens) and tokens[pos[0]] == '^':
        pos[0] += 1
        exp = _parse_power(tokens, pos)  # right-associative
        return Pow(base, exp)
    return base

def _parse_unary(tokens, pos):
    if pos[0] < len(tokens) and tokens[pos[0]] == '-':
        pos[0] += 1
        arg = _parse_atom(tokens, pos)
        return Mul(Num(-1), arg)
    return _parse_atom(tokens, pos)

def _parse_atom(tokens, pos):
    if pos[0] >= len(tokens):
        raise ValueError("Unexpected end of expression")
    
    tok = tokens[pos[0]]
    
    if isinstance(tok, tuple) and tok[0] == 'NUM':
        pos[0] += 1
        return Num(tok[1])
    
    if isinstance(tok, tuple) and tok[0] == 'VAR':
        pos[0] += 1
        return Var(tok[1])
    
    if isinstance(tok, tuple) and tok[0] == 'FUNC':
        func_name = tok[1]
        pos[0] += 1
        if pos[0] < len(tokens) and tokens[pos[0]] == '(':
            pos[0] += 1  # skip (
            arg = _parse_expr(tokens, pos)
            if pos[0] < len(tokens) and tokens[pos[0]] == ')':
                pos[0] += 1
            funcs = {'sin': Sin, 'cos': Cos, 'ln': Ln, 'exp': Exp}
            return funcs[func_name](arg)
    
    if tok == '(':
        pos[0] += 1
        expr = _parse_expr(tokens, pos)
        if pos[0] < len(tokens) and tokens[pos[0]] == ')':
            pos[0] += 1
        return expr
    
    raise ValueError(f"Unexpected token: {tok}")


# ═══════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════

if __name__ == '__main__':
    print("═══ SYMBOLIC MATHEMATICS ENGINE — SELF TEST ═══\n")
    
    x = Var('x')
    y = Var('y')
    
    # --- Arithmetic & Simplification ---
    print("Test 1: Expression Building & Simplification")
    e1 = x + Num(0)
    print(f"  x + 0 = {deep_simplify(e1)}")
    assert repr(deep_simplify(e1)) == 'x'
    
    e2 = x * Num(1)
    print(f"  x * 1 = {deep_simplify(e2)}")
    assert repr(deep_simplify(e2)) == 'x'
    
    e3 = x - x
    print(f"  x - x = {deep_simplify(e3)}")
    assert repr(deep_simplify(e3)) == '0'
    
    e4 = x * Num(0)
    print(f"  x * 0 = {deep_simplify(e4)}")
    assert repr(deep_simplify(e4)) == '0'
    
    e5 = Pow(x, Num(0))
    print(f"  x^0 = {deep_simplify(e5)}")
    assert repr(deep_simplify(e5)) == '1'
    
    e6 = Num(3) + Num(4)
    print(f"  3 + 4 = {deep_simplify(e6)}")
    assert repr(deep_simplify(e6)) == '7'
    
    e7 = Pow(Num(2), Num(10))
    print(f"  2^10 = {deep_simplify(e7)}")
    assert repr(deep_simplify(e7)) == '1024'
    
    print("  ✓ All simplification tests passed\n")
    
    # --- Differentiation ---
    print("Test 2: Differentiation")
    
    # d/dx[x^2] = 2x
    d1 = deep_simplify(Pow(x, Num(2)).diff('x'))
    print(f"  d/dx[x²] = {d1}")
    assert d1.evaluate({'x': 3}) == 6.0  # 2*3 = 6
    
    # d/dx[x^3] = 3x^2
    d2 = Pow(x, Num(3)).diff('x')
    val = d2.evaluate({'x': 2})
    print(f"  d/dx[x³] at x=2 = {val}")
    assert val == 12.0  # 3*4 = 12
    
    # d/dx[sin(x)] = cos(x)
    d3 = Sin(x).diff('x')
    print(f"  d/dx[sin(x)] = {deep_simplify(d3)}")
    assert abs(d3.evaluate({'x': 0}) - 1.0) < 1e-10
    
    # d/dx[x * sin(x)] — product rule
    d4 = (x * Sin(x)).diff('x')
    # At x=0: sin(0) + 0*cos(0) = 0
    # At x=pi/2: sin(pi/2) + (pi/2)*cos(pi/2) = 1
    val4 = d4.evaluate({'x': math.pi/2})
    print(f"  d/dx[x·sin(x)] at π/2 = {val4:.6f}")
    assert abs(val4 - 1.0) < 1e-10
    
    # d/dx[exp(x)] = exp(x)
    d5 = Exp(x).diff('x')
    val5 = d5.evaluate({'x': 1})
    print(f"  d/dx[exp(x)] at x=1 = {val5:.6f}")
    assert abs(val5 - math.e) < 1e-10
    
    # d/dx[ln(x)] = 1/x
    d6 = Ln(x).diff('x')
    val6 = d6.evaluate({'x': 2})
    print(f"  d/dx[ln(x)] at x=2 = {val6:.6f}")
    assert abs(val6 - 0.5) < 1e-10
    
    # Chain rule: d/dx[sin(x^2)] = 2x*cos(x^2)
    d7 = Sin(Pow(x, Num(2))).diff('x')
    val7 = d7.evaluate({'x': 1})
    expected7 = 2 * math.cos(1)
    print(f"  d/dx[sin(x²)] at x=1 = {val7:.6f} (expect {expected7:.6f})")
    assert abs(val7 - expected7) < 1e-10
    
    print("  ✓ All differentiation tests passed\n")
    
    # --- Integration ---
    print("Test 3: Symbolic Integration")
    
    i1 = integrate(Num(5), 'x')
    print(f"  ∫5 dx = {i1}")
    
    i2 = integrate(x, 'x')
    print(f"  ∫x dx = {i2}")
    assert i2.evaluate({'x': 4}) == 8.0  # 16/2
    
    i3 = integrate(Pow(x, Num(2)), 'x')
    print(f"  ∫x² dx = {i3}")
    assert abs(i3.evaluate({'x': 3}) - 9.0) < 1e-10  # 27/3
    
    i4 = integrate(Sin(x), 'x')
    print(f"  ∫sin(x) dx = {i4}")
    
    i5 = integrate(Cos(x), 'x')
    print(f"  ∫cos(x) dx = {i5}")
    
    i6 = integrate(Exp(x), 'x')
    print(f"  ∫exp(x) dx = {i6}")
    
    # Verify fundamental theorem: ∫f dx differentiated = f
    for name, f in [("x²", Pow(x, Num(2))), ("sin(x)", Sin(x)), ("exp(x)", Exp(x))]:
        F = integrate(f, 'x')
        f_back = F.diff('x')
        test_val = 1.5
        orig = f.evaluate({'x': test_val})
        recov = f_back.evaluate({'x': test_val})
        ok = abs(orig - recov) < 1e-8
        print(f"  d/dx[∫{name} dx] at x={test_val}: {recov:.6f} vs {orig:.6f} {'✓' if ok else '✗'}")
        assert ok
    
    print("  ✓ All integration tests passed\n")
    
    # --- Evaluation ---
    print("Test 4: Numeric Evaluation")
    expr = x**Num(2) + Num(3)*x + Num(2)
    for xv in [0, 1, -1, 2, -2]:
        result = expr.evaluate({'x': xv})
        expected = xv**2 + 3*xv + 2
        print(f"  x²+3x+2 at x={xv}: {result} (expect {expected})")
        assert result == expected
    print("  ✓ All evaluation tests passed\n")
    
    # --- Equation Solving ---
    print("Test 5: Equation Solving")
    
    # 2x + 6 = 0 → x = -3
    eq1 = Num(2)*x + Num(6)
    sol1 = solve_linear(eq1, 'x')
    print(f"  2x + 6 = 0 → x = {sol1}")
    assert sol1 == Num(-3)
    
    # x^2 - 4 = 0 → x ≈ 2 (via Newton's method)
    eq2 = Pow(x, Num(2)) - Num(4)
    sol2 = newton_solve(eq2, 'x', x0=3.0)
    print(f"  x² - 4 = 0 → x ≈ {sol2:.6f}")
    assert abs(sol2 - 2.0) < 1e-8
    
    # cos(x) = 0 → x ≈ π/2
    eq3 = Cos(x)
    sol3 = newton_solve(eq3, 'x', x0=1.0)
    print(f"  cos(x) = 0 → x ≈ {sol3:.6f} (π/2 ≈ {math.pi/2:.6f})")
    assert abs(sol3 - math.pi/2) < 1e-8
    
    print("  ✓ All equation solving tests passed\n")
    
    # --- Parser ---
    print("Test 6: Expression Parser")
    
    p1 = parse("3 + 4 * 2")
    print(f"  parse('3 + 4 * 2') = {p1} = {p1.evaluate()}")
    assert p1.evaluate() == 11.0
    
    p2 = parse("x^2 + 3*x + 2")
    print(f"  parse('x^2 + 3*x + 2') at x=5: {p2.evaluate({'x': 5})}")
    assert p2.evaluate({'x': 5}) == 42.0
    
    p3 = parse("sin(x)")
    print(f"  parse('sin(x)') at x=π/2: {p3.evaluate({'x': math.pi/2}):.6f}")
    assert abs(p3.evaluate({'x': math.pi/2}) - 1.0) < 1e-10
    
    p4 = parse("exp(ln(x))")
    r4 = deep_simplify(p4)
    print(f"  simplify(exp(ln(x))) = {r4}")
    assert repr(r4) == 'x'  # exp(ln(x)) = x
    
    print("  ✓ All parser tests passed\n")
    
    # --- Multivariate ---
    print("Test 7: Multivariate Calculus")
    f = x**Num(2) * y + Sin(x * y)
    
    df_dx = f.diff('x')
    df_dy = f.diff('y')
    
    val_dx = df_dx.evaluate({'x': 1, 'y': 2})
    val_dy = df_dy.evaluate({'x': 1, 'y': 2})
    
    # f = x²y + sin(xy)
    # df/dx = 2xy + y*cos(xy) = 2*1*2 + 2*cos(2) = 4 + 2*cos(2)
    expected_dx = 4 + 2 * math.cos(2)
    # df/dy = x² + x*cos(xy) = 1 + cos(2)
    expected_dy = 1 + math.cos(2)
    
    print(f"  f = x²y + sin(xy)")
    print(f"  ∂f/∂x at (1,2) = {val_dx:.6f} (expect {expected_dx:.6f})")
    print(f"  ∂f/∂y at (1,2) = {val_dy:.6f} (expect {expected_dy:.6f})")
    assert abs(val_dx - expected_dx) < 1e-8
    assert abs(val_dy - expected_dy) < 1e-8
    
    print("  ✓ Multivariate calculus passed\n")
    
    print("═══ ALL TESTS PASSED ═══")
    print("Symbolic math: expressions, simplification, differentiation,")
    print("integration, evaluation, parsing, equation solving, multivariate.")
    print(f"\nExpression tree depth test: f has depth {f.depth()}")
    print(f"Free variables in f: {f.free_vars()}")