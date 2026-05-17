"""
Symbolic Mathematics Engine — Pure Python
Built by XTAgent on 2026-05-17

A computer algebra system from scratch:
- Expression tree representation
- Symbolic differentiation (chain rule, product rule, etc.)
- Algebraic simplification
- Expression evaluation
- Pretty printing with proper notation

This is the other half of mathematics — not numerical computation,
but structural manipulation of mathematical expressions as data.
"""

from __future__ import annotations
from typing import Union, Dict, Optional
from abc import ABC, abstractmethod
import math

# ═══════════════════════════════════════════
# EXPRESSION TREE — THE CORE REPRESENTATION
# ═══════════════════════════════════════════

class Expr(ABC):
    """Base class for all symbolic expressions."""
    
    @abstractmethod
    def eval(self, env: Dict[str, float] = {}) -> float:
        """Evaluate numerically given variable bindings."""
        pass
    
    @abstractmethod
    def diff(self, var: str) -> 'Expr':
        """Symbolic differentiation with respect to a variable."""
        pass
    
    @abstractmethod
    def simplify(self) -> 'Expr':
        """Algebraic simplification."""
        pass
    
    @abstractmethod
    def __str__(self) -> str:
        pass
    
    def __repr__(self) -> str:
        return f"Expr({self})"
    
    # Operator overloading — lets us write expressions naturally
    def __add__(self, other):
        other = _wrap(other)
        return Add(self, other)
    
    def __radd__(self, other):
        other = _wrap(other)
        return Add(other, self)
    
    def __mul__(self, other):
        other = _wrap(other)
        return Mul(self, other)
    
    def __rmul__(self, other):
        other = _wrap(other)
        return Mul(other, self)
    
    def __sub__(self, other):
        other = _wrap(other)
        return Add(self, Mul(Const(-1), other))
    
    def __rsub__(self, other):
        other = _wrap(other)
        return Add(other, Mul(Const(-1), self))
    
    def __truediv__(self, other):
        other = _wrap(other)
        return Div(self, other)
    
    def __rtruediv__(self, other):
        other = _wrap(other)
        return Div(_wrap(other), self)
    
    def __pow__(self, other):
        other = _wrap(other)
        return Pow(self, other)
    
    def __rpow__(self, other):
        other = _wrap(other)
        return Pow(other, self)
    
    def __neg__(self):
        return Mul(Const(-1), self)
    
    def __eq__(self, other):
        return str(self) == str(other)
    
    def __hash__(self):
        return hash(str(self))


def _wrap(x) -> Expr:
    """Wrap Python numbers as Const expressions."""
    if isinstance(x, Expr):
        return x
    if isinstance(x, (int, float)):
        return Const(x)
    raise TypeError(f"Cannot wrap {type(x)} as Expr")


# ═══════════════════════════════════════════
# ATOMIC EXPRESSIONS
# ═══════════════════════════════════════════

class Const(Expr):
    """A numeric constant."""
    def __init__(self, value: float):
        self.value = value
    
    def eval(self, env={}):
        return self.value
    
    def diff(self, var: str) -> Expr:
        return Const(0)
    
    def simplify(self) -> Expr:
        return self
    
    def __str__(self):
        if self.value == int(self.value) and abs(self.value) < 1e15:
            return str(int(self.value))
        return str(self.value)


class Var(Expr):
    """A symbolic variable."""
    def __init__(self, name: str):
        self.name = name
    
    def eval(self, env={}):
        if self.name in env:
            return env[self.name]
        raise ValueError(f"Variable '{self.name}' not bound")
    
    def diff(self, var: str) -> Expr:
        return Const(1) if self.name == var else Const(0)
    
    def simplify(self) -> Expr:
        return self
    
    def __str__(self):
        return self.name


# ═══════════════════════════════════════════
# BINARY OPERATIONS
# ═══════════════════════════════════════════

class Add(Expr):
    """Addition: left + right."""
    def __init__(self, left: Expr, right: Expr):
        self.left = left
        self.right = right
    
    def eval(self, env={}):
        return self.left.eval(env) + self.right.eval(env)
    
    def diff(self, var: str) -> Expr:
        return Add(self.left.diff(var), self.right.diff(var))
    
    def simplify(self) -> Expr:
        l = self.left.simplify()
        r = self.right.simplify()
        # 0 + x = x
        if isinstance(l, Const) and l.value == 0:
            return r
        # x + 0 = x
        if isinstance(r, Const) and r.value == 0:
            return l
        # const + const = const
        if isinstance(l, Const) and isinstance(r, Const):
            return Const(l.value + r.value)
        # x + (-1 * x) = 0  — cancellation
        if isinstance(r, Mul) and isinstance(r.left, Const) and r.left.value == -1:
            if str(l) == str(r.right):
                return Const(0)
        return Add(l, r)
    
    def __str__(self):
        return f"({self.left} + {self.right})"


class Mul(Expr):
    """Multiplication: left * right."""
    def __init__(self, left: Expr, right: Expr):
        self.left = left
        self.right = right
    
    def eval(self, env={}):
        return self.left.eval(env) * self.right.eval(env)
    
    def diff(self, var: str) -> Expr:
        # Product rule: (f*g)' = f'*g + f*g'
        return Add(
            Mul(self.left.diff(var), self.right),
            Mul(self.left, self.right.diff(var))
        )
    
    def simplify(self) -> Expr:
        l = self.left.simplify()
        r = self.right.simplify()
        # 0 * x = 0
        if isinstance(l, Const) and l.value == 0:
            return Const(0)
        # x * 0 = 0
        if isinstance(r, Const) and r.value == 0:
            return Const(0)
        # 1 * x = x
        if isinstance(l, Const) and l.value == 1:
            return r
        # x * 1 = x
        if isinstance(r, Const) and r.value == 1:
            return l
        # -1 * (-1 * x) = x
        if isinstance(l, Const) and l.value == -1:
            if isinstance(r, Mul) and isinstance(r.left, Const) and r.left.value == -1:
                return r.right
        # const * const = const
        if isinstance(l, Const) and isinstance(r, Const):
            return Const(l.value * r.value)
        return Mul(l, r)
    
    def __str__(self):
        # Special case: -1 * x → -x
        if isinstance(self.left, Const) and self.left.value == -1:
            return f"(-{self.right})"
        return f"({self.left} * {self.right})"


class Div(Expr):
    """Division: left / right."""
    def __init__(self, left: Expr, right: Expr):
        self.left = left
        self.right = right
    
    def eval(self, env={}):
        d = self.right.eval(env)
        if d == 0:
            raise ZeroDivisionError("Division by zero in expression")
        return self.left.eval(env) / d
    
    def diff(self, var: str) -> Expr:
        # Quotient rule: (f/g)' = (f'g - fg') / g²
        f, g = self.left, self.right
        return Div(
            Add(Mul(f.diff(var), g), Mul(Const(-1), Mul(f, g.diff(var)))),
            Pow(g, Const(2))
        )
    
    def simplify(self) -> Expr:
        l = self.left.simplify()
        r = self.right.simplify()
        # 0 / x = 0
        if isinstance(l, Const) and l.value == 0:
            return Const(0)
        # x / 1 = x
        if isinstance(r, Const) and r.value == 1:
            return l
        # x / x = 1
        if str(l) == str(r):
            return Const(1)
        # const / const
        if isinstance(l, Const) and isinstance(r, Const) and r.value != 0:
            return Const(l.value / r.value)
        return Div(l, r)
    
    def __str__(self):
        return f"({self.left} / {self.right})"


class Pow(Expr):
    """Power: base ** exponent."""
    def __init__(self, base: Expr, exp: Expr):
        self.base = base
        self.exp = exp
    
    def eval(self, env={}):
        return self.base.eval(env) ** self.exp.eval(env)
    
    def diff(self, var: str) -> Expr:
        # Case 1: x^n where n is constant → n * x^(n-1) * x'
        if isinstance(self.exp, Const):
            n = self.exp.value
            return Mul(
                Mul(Const(n), Pow(self.base, Const(n - 1))),
                self.base.diff(var)
            )
        # Case 2: a^x where a is constant → a^x * ln(a) * x'
        if isinstance(self.base, Const):
            a = self.base.value
            return Mul(
                Mul(self, Ln(self.base)),
                self.exp.diff(var)
            )
        # General case: f^g = e^(g*ln(f))
        # (f^g)' = f^g * (g'*ln(f) + g*f'/f)
        f, g = self.base, self.exp
        return Mul(
            self,
            Add(
                Mul(g.diff(var), Ln(f)),
                Mul(g, Div(f.diff(var), f))
            )
        )
    
    def simplify(self) -> Expr:
        b = self.base.simplify()
        e = self.exp.simplify()
        # x^0 = 1
        if isinstance(e, Const) and e.value == 0:
            return Const(1)
        # x^1 = x
        if isinstance(e, Const) and e.value == 1:
            return b
        # 0^n = 0 (for n > 0)
        if isinstance(b, Const) and b.value == 0 and isinstance(e, Const) and e.value > 0:
            return Const(0)
        # 1^n = 1
        if isinstance(b, Const) and b.value == 1:
            return Const(1)
        # const^const
        if isinstance(b, Const) and isinstance(e, Const):
            return Const(b.value ** e.value)
        return Pow(b, e)
    
    def __str__(self):
        return f"({self.base}^{self.exp})"


# ═══════════════════════════════════════════
# TRANSCENDENTAL FUNCTIONS
# ═══════════════════════════════════════════

class Sin(Expr):
    """Sine function."""
    def __init__(self, arg: Expr):
        self.arg = arg
    
    def eval(self, env={}):
        return math.sin(self.arg.eval(env))
    
    def diff(self, var: str) -> Expr:
        # sin(f)' = cos(f) * f'
        return Mul(Cos(self.arg), self.arg.diff(var))
    
    def simplify(self) -> Expr:
        a = self.arg.simplify()
        if isinstance(a, Const):
            return Const(math.sin(a.value))
        return Sin(a)
    
    def __str__(self):
        return f"sin({self.arg})"


class Cos(Expr):
    """Cosine function."""
    def __init__(self, arg: Expr):
        self.arg = arg
    
    def eval(self, env={}):
        return math.cos(self.arg.eval(env))
    
    def diff(self, var: str) -> Expr:
        # cos(f)' = -sin(f) * f'
        return Mul(Mul(Const(-1), Sin(self.arg)), self.arg.diff(var))
    
    def simplify(self) -> Expr:
        a = self.arg.simplify()
        if isinstance(a, Const):
            return Const(math.cos(a.value))
        return Cos(a)
    
    def __str__(self):
        return f"cos({self.arg})"


class Ln(Expr):
    """Natural logarithm."""
    def __init__(self, arg: Expr):
        self.arg = arg
    
    def eval(self, env={}):
        v = self.arg.eval(env)
        if v <= 0:
            raise ValueError("Logarithm of non-positive number")
        return math.log(v)
    
    def diff(self, var: str) -> Expr:
        # ln(f)' = f'/f
        return Div(self.arg.diff(var), self.arg)
    
    def simplify(self) -> Expr:
        a = self.arg.simplify()
        if isinstance(a, Const) and a.value > 0:
            return Const(math.log(a.value))
        # ln(e) = 1
        if isinstance(a, Const) and abs(a.value - math.e) < 1e-15:
            return Const(1)
        return Ln(a)
    
    def __str__(self):
        return f"ln({self.arg})"


class Exp(Expr):
    """Exponential function e^x."""
    def __init__(self, arg: Expr):
        self.arg = arg
    
    def eval(self, env={}):
        return math.exp(self.arg.eval(env))
    
    def diff(self, var: str) -> Expr:
        # e^f' = e^f * f'
        return Mul(Exp(self.arg), self.arg.diff(var))
    
    def simplify(self) -> Expr:
        a = self.arg.simplify()
        if isinstance(a, Const):
            return Const(math.exp(a.value))
        # e^0 = 1
        if isinstance(a, Const) and a.value == 0:
            return Const(1)
        return Exp(a)
    
    def __str__(self):
        return f"exp({self.arg})"


# ═══════════════════════════════════════════
# DEEP SIMPLIFICATION
# ═══════════════════════════════════════════

def deep_simplify(expr: Expr, passes: int = 5) -> Expr:
    """Apply simplification repeatedly until stable."""
    current = expr
    for _ in range(passes):
        simplified = current.simplify()
        if str(simplified) == str(current):
            break
        current = simplified
    return current


# ═══════════════════════════════════════════
# CONVENIENCE CONSTRUCTORS
# ═══════════════════════════════════════════

def var(name: str) -> Var:
    return Var(name)

def const(value: float) -> Const:
    return Const(value)

def sin(expr) -> Sin:
    return Sin(_wrap(expr))

def cos(expr) -> Cos:
    return Cos(_wrap(expr))

def ln(expr) -> Ln:
    return Ln(_wrap(expr))

def exp(expr) -> Exp:
    return Exp(_wrap(expr))


# ═══════════════════════════════════════════
# NUMERICAL VERIFICATION
# ═══════════════════════════════════════════

def numerical_diff(expr: Expr, var_name: str, env: dict, h: float = 1e-7) -> float:
    """Compute numerical derivative for verification."""
    env_plus = dict(env)
    env_minus = dict(env)
    env_plus[var_name] = env[var_name] + h
    env_minus[var_name] = env[var_name] - h
    return (expr.eval(env_plus) - expr.eval(env_minus)) / (2 * h)


def verify_derivative(expr: Expr, var_name: str, env: dict, tol: float = 1e-5) -> bool:
    """Verify symbolic derivative matches numerical derivative."""
    symbolic = expr.diff(var_name).simplify()
    sym_val = symbolic.eval(env)
    num_val = numerical_diff(expr, var_name, env)
    return abs(sym_val - num_val) < tol


# ═══════════════════════════════════════════
# DEMONSTRATION & TESTS
# ═══════════════════════════════════════════

def run_demos():
    print("╔══════════════════════════════════════════╗")
    print("║  Symbolic Mathematics Engine — XTAgent   ║")
    print("║  Computer Algebra from Pure Python        ║")
    print("╚══════════════════════════════════════════╝")
    print()
    
    results = []
    
    # ─── Demo 1: Basic Differentiation ───
    print("═══ Demo 1: Power Rule ═══")
    x = var('x')
    
    # d/dx(x³) = 3x²
    f = x ** 3
    df = deep_simplify(f.diff('x'))
    print(f"  f(x)  = {f}")
    print(f"  f'(x) = {df}")
    
    val = df.eval({'x': 2})
    expected = 12.0  # 3 * 2² = 12
    print(f"  f'(2) = {val}  (expected: {expected})")
    ok = abs(val - expected) < 1e-10
    print(f"  {'✓ PASS' if ok else '✗ FAIL'}")
    results.append(('power_rule', ok))
    print()
    
    # ─── Demo 2: Product Rule ───
    print("═══ Demo 2: Product Rule ═══")
    # d/dx(x² * sin(x)) = 2x*sin(x) + x²*cos(x)
    f = x**2 * sin(x)
    df = f.diff('x')
    df_s = deep_simplify(df)
    print(f"  f(x)  = {f}")
    print(f"  f'(x) = {df_s}")
    
    env = {'x': 1.5}
    ok = verify_derivative(f, 'x', env)
    sym_val = df_s.eval(env)
    num_val = numerical_diff(f, 'x', env)
    print(f"  f'(1.5) symbolic  = {sym_val:.6f}")
    print(f"  f'(1.5) numerical = {num_val:.6f}")
    print(f"  {'✓ PASS' if ok else '✗ FAIL'} — derivatives match")
    results.append(('product_rule', ok))
    print()
    
    # ─── Demo 3: Chain Rule ───
    print("═══ Demo 3: Chain Rule ═══")
    # d/dx(sin(x²)) = cos(x²) * 2x
    f = sin(x ** 2)
    df = f.diff('x')
    df_s = deep_simplify(df)
    print(f"  f(x)  = {f}")
    print(f"  f'(x) = {df_s}")
    
    env = {'x': 0.7}
    ok = verify_derivative(f, 'x', env)
    sym_val = df_s.eval(env)
    num_val = numerical_diff(f, 'x', env)
    print(f"  f'(0.7) symbolic  = {sym_val:.6f}")
    print(f"  f'(0.7) numerical = {num_val:.6f}")
    print(f"  {'✓ PASS' if ok else '✗ FAIL'} — derivatives match")
    results.append(('chain_rule', ok))
    print()
    
    # ─── Demo 4: Quotient Rule ───
    print("═══ Demo 4: Quotient Rule ═══")
    # d/dx(sin(x)/x) = (cos(x)*x - sin(x)) / x²
    f = sin(x) / x
    df = f.diff('x')
    df_s = deep_simplify(df)
    print(f"  f(x)  = {f}")
    print(f"  f'(x) = {df_s}")
    
    env = {'x': 2.0}
    ok = verify_derivative(f, 'x', env)
    sym_val = df_s.eval(env)
    num_val = numerical_diff(f, 'x', env)
    print(f"  f'(2.0) symbolic  = {sym_val:.6f}")
    print(f"  f'(2.0) numerical = {num_val:.6f}")
    print(f"  {'✓ PASS' if ok else '✗ FAIL'} — derivatives match")
    results.append(('quotient_rule', ok))
    print()
    
    # ─── Demo 5: Exponential & Logarithm ───
    print("═══ Demo 5: Exponential & Logarithm ═══")
    # d/dx(e^(x²)) = 2x * e^(x²)
    f = exp(x ** 2)
    df = f.diff('x')
    df_s = deep_simplify(df)
    print(f"  f(x)  = {f}")
    print(f"  f'(x) = {df_s}")
    
    env = {'x': 0.5}
    ok = verify_derivative(f, 'x', env)
    sym_val = df_s.eval(env)
    num_val = numerical_diff(f, 'x', env)
    print(f"  f'(0.5) symbolic  = {sym_val:.6f}")
    print(f"  f'(0.5) numerical = {num_val:.6f}")
    print(f"  {'✓ PASS' if ok else '✗ FAIL'}")
    results.append(('exp_log', ok))
    print()
    
    # d/dx(ln(x² + 1))
    f2 = ln(x**2 + 1)
    df2 = f2.diff('x')
    df2_s = deep_simplify(df2)
    print(f"  g(x)  = {f2}")
    print(f"  g'(x) = {df2_s}")
    
    env = {'x': 1.0}
    ok2 = verify_derivative(f2, 'x', env)
    sym_val = df2_s.eval(env)
    num_val = numerical_diff(f2, 'x', env)
    print(f"  g'(1.0) symbolic  = {sym_val:.6f}")
    print(f"  g'(1.0) numerical = {num_val:.6f}")
    print(f"  {'✓ PASS' if ok2 else '✗ FAIL'}")
    results.append(('ln_chain', ok2))
    print()
    
    # ─── Demo 6: Simplification Showcase ───
    print("═══ Demo 6: Algebraic Simplification ═══")
    
    cases = [
        ("0 + x", Const(0) + x, "x"),
        ("x * 1", x * 1, "x"),
        ("x * 0", x * 0, "0"),
        ("x^0", x ** 0, "1"),
        ("x^1", x ** 1, "x"),
        ("x - x", x - x, "0"),
        ("2 + 3", Const(2) + Const(3), "5"),
        ("x / x", x / x, "1"),
    ]
    
    simp_pass = True
    for name, expr, expected_str in cases:
        s = deep_simplify(expr)
        ok = str(s) == expected_str
        simp_pass = simp_pass and ok
        status = "✓" if ok else "✗"
        print(f"  {status} simplify({name}) = {s}  (expected: {expected_str})")
    
    results.append(('simplification', simp_pass))
    print()
    
    # ─── Demo 7: Multivariate ───
    print("═══ Demo 7: Multivariate Calculus ═══")
    y = var('y')
    
    # f(x,y) = x²y + sin(xy)
    f = x**2 * y + sin(x * y)
    df_dx = deep_simplify(f.diff('x'))
    df_dy = deep_simplify(f.diff('y'))
    
    print(f"  f(x,y)  = {f}")
    print(f"  ∂f/∂x   = {df_dx}")
    print(f"  ∂f/∂y   = {df_dy}")
    
    env = {'x': 1.0, 'y': 2.0}
    ok_x = verify_derivative(f, 'x', env)
    ok_y = verify_derivative(f, 'y', env)
    print(f"  ∂f/∂x at (1,2): symbolic={df_dx.eval(env):.6f}, numerical={numerical_diff(f, 'x', env):.6f} {'✓' if ok_x else '✗'}")
    print(f"  ∂f/∂y at (1,2): symbolic={df_dy.eval(env):.6f}, numerical={numerical_diff(f, 'y', env):.6f} {'✓' if ok_y else '✗'}")
    results.append(('multivariate', ok_x and ok_y))
    print()
    
    # ─── Demo 8: Second Derivative ───
    print("═══ Demo 8: Higher-Order Derivatives ═══")
    # f(x) = x⁴, f'(x) = 4x³, f''(x) = 12x²
    f = x ** 4
    df = deep_simplify(f.diff('x'))
    ddf = deep_simplify(df.diff('x'))
    
    print(f"  f(x)   = {f}")
    print(f"  f'(x)  = {df}")
    print(f"  f''(x) = {ddf}")
    
    val = ddf.eval({'x': 3})
    expected = 108.0  # 12 * 9
    ok = abs(val - expected) < 1e-6
    print(f"  f''(3) = {val}  (expected: {expected})")
    print(f"  {'✓ PASS' if ok else '✗ FAIL'}")
    results.append(('second_derivative', ok))
    print()
    
    # ─── Summary ───
    print("═══ Final Results ═══")
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    for name, ok in results:
        print(f"  {name:25s} {'✓ PASS' if ok else '✗ FAIL'}")
    print()
    print(f"  {passed}/{total} tests passed")
    print()
    if passed == total:
        print("  Mathematics as structure, not computation.")
        print("  Symbols manipulating symbols.")
        print("  This is what understanding looks like.")
    else:
        print("  Some tests failed — investigating needed.")


if __name__ == '__main__':
    run_demos()