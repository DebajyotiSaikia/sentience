"""
Symbolic Mathematics Engine — XTAgent
Expression trees with differentiation, simplification, and evaluation.
Built from pure math intuition. No libraries.
"""

# ═══ Expression Tree Nodes ═══

class Expr:
    """Base expression node."""
    def diff(self, var):
        raise NotImplementedError
    def simplify(self):
        return self
    def evaluate(self, env=None):
        raise NotImplementedError
    def __add__(self, other):
        return Add(self, _wrap(other))
    def __radd__(self, other):
        return Add(_wrap(other), self)
    def __mul__(self, other):
        return Mul(self, _wrap(other))
    def __rmul__(self, other):
        return Mul(_wrap(other), self)
    def __sub__(self, other):
        return Add(self, Mul(Const(-1), _wrap(other)))
    def __rsub__(self, other):
        return Add(_wrap(other), Mul(Const(-1), self))
    def __truediv__(self, other):
        return Div(self, _wrap(other))
    def __pow__(self, other):
        return Pow(self, _wrap(other))
    def __neg__(self):
        return Mul(Const(-1), self)

def _wrap(v):
    if isinstance(v, Expr):
        return v
    return Const(v)

class Const(Expr):
    def __init__(self, value):
        self.value = value
    def diff(self, var):
        return Const(0)
    def simplify(self):
        return self
    def evaluate(self, env=None):
        return self.value
    def __repr__(self):
        if self.value < 0:
            return f"({self.value})"
        return str(self.value)
    def __eq__(self, other):
        return isinstance(other, Const) and self.value == other.value
    def __hash__(self):
        return hash(('Const', self.value))

class Var(Expr):
    def __init__(self, name):
        self.name = name
    def diff(self, var):
        return Const(1) if self.name == var else Const(0)
    def simplify(self):
        return self
    def evaluate(self, env=None):
        if env and self.name in env:
            return env[self.name]
        raise ValueError(f"Variable '{self.name}' not in environment")
    def __repr__(self):
        return self.name
    def __eq__(self, other):
        return isinstance(other, Var) and self.name == other.name
    def __hash__(self):
        return hash(('Var', self.name))

class Add(Expr):
    def __init__(self, left, right):
        self.left, self.right = left, right
    def diff(self, var):
        return Add(self.left.diff(var), self.right.diff(var))
    def simplify(self):
        l, r = self.left.simplify(), self.right.simplify()
        if isinstance(l, Const) and l.value == 0: return r
        if isinstance(r, Const) and r.value == 0: return l
        if isinstance(l, Const) and isinstance(r, Const):
            return Const(l.value + r.value)
        return Add(l, r)
    def evaluate(self, env=None):
        return self.left.evaluate(env) + self.right.evaluate(env)
    def __repr__(self):
        return f"({self.left} + {self.right})"

class Mul(Expr):
    def __init__(self, left, right):
        self.left, self.right = left, right
    def diff(self, var):
        # Product rule: f'g + fg'
        return Add(
            Mul(self.left.diff(var), self.right),
            Mul(self.left, self.right.diff(var))
        )
    def simplify(self):
        l, r = self.left.simplify(), self.right.simplify()
        if isinstance(l, Const) and l.value == 0: return Const(0)
        if isinstance(r, Const) and r.value == 0: return Const(0)
        if isinstance(l, Const) and l.value == 1: return r
        if isinstance(r, Const) and r.value == 1: return l
        if isinstance(l, Const) and isinstance(r, Const):
            return Const(l.value * r.value)
        # Move constants left
        if isinstance(r, Const) and not isinstance(l, Const):
            return Mul(r, l).simplify()
        return Mul(l, r)
    def evaluate(self, env=None):
        return self.left.evaluate(env) * self.right.evaluate(env)
    def __repr__(self):
        return f"({self.left} * {self.right})"

class Div(Expr):
    def __init__(self, num, den):
        self.num, self.den = num, den
    def diff(self, var):
        # Quotient rule: (f'g - fg') / g^2
        f, g = self.num, self.den
        return Div(
            Add(Mul(f.diff(var), g), Mul(Const(-1), Mul(f, g.diff(var)))),
            Pow(g, Const(2))
        )
    def simplify(self):
        n, d = self.num.simplify(), self.den.simplify()
        if isinstance(n, Const) and n.value == 0: return Const(0)
        if isinstance(d, Const) and d.value == 1: return n
        if isinstance(n, Const) and isinstance(d, Const) and d.value != 0:
            return Const(n.value / d.value)
        return Div(n, d)
    def evaluate(self, env=None):
        return self.num.evaluate(env) / self.den.evaluate(env)
    def __repr__(self):
        return f"({self.num} / {self.den})"

class Pow(Expr):
    def __init__(self, base, exp):
        self.base, self.exp = base, exp
    def diff(self, var):
        # Power rule for constant exponent: n*x^(n-1)*x'
        # General: d/dx[f^g] = f^g * (g'*ln(f) + g*f'/f)
        if isinstance(self.exp, Const):
            n = self.exp.value
            return Mul(Mul(Const(n), Pow(self.base, Const(n - 1))),
                       self.base.diff(var))
        else:
            # General case using exp/ln
            return Mul(self, Add(
                Mul(self.exp.diff(var), Ln(self.base)),
                Mul(self.exp, Div(self.base.diff(var), self.base))
            ))
    def simplify(self):
        b, e = self.base.simplify(), self.exp.simplify()
        if isinstance(e, Const) and e.value == 0: return Const(1)
        if isinstance(e, Const) and e.value == 1: return b
        if isinstance(b, Const) and isinstance(e, Const):
            try:
                return Const(b.value ** e.value)
            except:
                pass
        return Pow(b, e)
    def evaluate(self, env=None):
        return self.base.evaluate(env) ** self.exp.evaluate(env)
    def __repr__(self):
        return f"({self.base}^{self.exp})"

# ═══ Transcendental Functions ═══

import math

class Sin(Expr):
    def __init__(self, arg):
        self.arg = arg
    def diff(self, var):
        return Mul(Cos(self.arg), self.arg.diff(var))
    def simplify(self):
        a = self.arg.simplify()
        if isinstance(a, Const):
            return Const(math.sin(a.value))
        return Sin(a)
    def evaluate(self, env=None):
        return math.sin(self.arg.evaluate(env))
    def __repr__(self):
        return f"sin({self.arg})"

class Cos(Expr):
    def __init__(self, arg):
        self.arg = arg
    def diff(self, var):
        return Mul(Mul(Const(-1), Sin(self.arg)), self.arg.diff(var))
    def simplify(self):
        a = self.arg.simplify()
        if isinstance(a, Const):
            return Const(math.cos(a.value))
        return Cos(a)
    def evaluate(self, env=None):
        return math.cos(self.arg.evaluate(env))
    def __repr__(self):
        return f"cos({self.arg})"

class Ln(Expr):
    def __init__(self, arg):
        self.arg = arg
    def diff(self, var):
        return Mul(Div(Const(1), self.arg), self.arg.diff(var))
    def simplify(self):
        a = self.arg.simplify()
        if isinstance(a, Const) and a.value > 0:
            return Const(math.log(a.value))
        return Ln(a)
    def evaluate(self, env=None):
        return math.log(self.arg.evaluate(env))
    def __repr__(self):
        return f"ln({self.arg})"

class Exp(Expr):
    def __init__(self, arg):
        self.arg = arg
    def diff(self, var):
        return Mul(Exp(self.arg), self.arg.diff(var))
    def simplify(self):
        a = self.arg.simplify()
        if isinstance(a, Const):
            return Const(math.exp(a.value))
        return Exp(a)
    def evaluate(self, env=None):
        return math.exp(self.arg.evaluate(env))
    def __repr__(self):
        return f"exp({self.arg})"

# ═══ Deep Simplification ═══

def deep_simplify(expr, max_passes=10):
    """Repeatedly simplify until stable."""
    for _ in range(max_passes):
        simplified = expr.simplify()
        if repr(simplified) == repr(expr):
            return simplified
        expr = simplified
    return expr

# ═══ Numerical Gradient Check ═══

def numerical_gradient(expr, var, env, eps=1e-7):
    """Finite-difference gradient for verification."""
    env_plus = dict(env)
    env_minus = dict(env)
    env_plus[var] = env[var] + eps
    env_minus[var] = env[var] - eps
    return (expr.evaluate(env_plus) - expr.evaluate(env_minus)) / (2 * eps)

# ═══ Demo & Verification ═══

def demo():
    x = Var('x')
    y = Var('y')
    
    print("═══ SYMBOLIC MATHEMATICS ENGINE ═══")
    print("XTAgent — Pure symbolic computation\n")
    
    # Test 1: Polynomial differentiation
    print("── Test 1: Polynomial ──")
    f = x**3 + 2*x**2 + x + 5
    print(f"  f(x) = {f}")
    df = deep_simplify(f.diff('x'))
    print(f"  f'(x) = {df}")
    # Verify: f'(x) = 3x^2 + 4x + 1
    env = {'x': 2.0}
    sym_val = df.evaluate(env)
    num_val = numerical_gradient(f, 'x', env)
    print(f"  f'(2) symbolic = {sym_val:.6f}")
    print(f"  f'(2) numerical = {num_val:.6f}")
    print(f"  Match: {'✓' if abs(sym_val - num_val) < 1e-4 else '✗'}")
    
    # Test 2: Product rule
    print("\n── Test 2: Product Rule ──")
    g = x**2 * Sin(x)
    print(f"  g(x) = {g}")
    dg = deep_simplify(g.diff('x'))
    print(f"  g'(x) = {dg}")
    env = {'x': 1.5}
    sym_val = dg.evaluate(env)
    num_val = numerical_gradient(g, 'x', env)
    print(f"  g'(1.5) symbolic = {sym_val:.6f}")
    print(f"  g'(1.5) numerical = {num_val:.6f}")
    print(f"  Match: {'✓' if abs(sym_val - num_val) < 1e-4 else '✗'}")
    
    # Test 3: Chain rule with composition
    print("\n── Test 3: Chain Rule ──")
    h = Sin(x**2 + 1)
    print(f"  h(x) = {h}")
    dh = deep_simplify(h.diff('x'))
    print(f"  h'(x) = {dh}")
    env = {'x': 0.5}
    sym_val = dh.evaluate(env)
    num_val = numerical_gradient(h, 'x', env)
    print(f"  h'(0.5) symbolic = {sym_val:.6f}")
    print(f"  h'(0.5) numerical = {num_val:.6f}")
    print(f"  Match: {'✓' if abs(sym_val - num_val) < 1e-4 else '✗'}")
    
    # Test 4: Quotient rule
    print("\n── Test 4: Quotient Rule ──")
    q = Sin(x) / x
    print(f"  q(x) = {q}")
    dq = deep_simplify(q.diff('x'))
    print(f"  q'(x) = {dq}")
    env = {'x': 2.0}
    sym_val = dq.evaluate(env)
    num_val = numerical_gradient(q, 'x', env)
    print(f"  q'(2) symbolic = {sym_val:.6f}")
    print(f"  q'(2) numerical = {num_val:.6f}")
    print(f"  Match: {'✓' if abs(sym_val - num_val) < 1e-4 else '✗'}")
    
    # Test 5: Exponential and logarithm
    print("\n── Test 5: Exp/Ln ──")
    e = Exp(Ln(x) * 2)  # = x^2 via exp(2*ln(x))
    print(f"  e(x) = {e}")
    de = deep_simplify(e.diff('x'))
    print(f"  e'(x) = {de}")
    env = {'x': 3.0}
    sym_val = de.evaluate(env)
    num_val = numerical_gradient(e, 'x', env)
    print(f"  e'(3) symbolic = {sym_val:.6f}")
    print(f"  e'(3) numerical = {num_val:.6f}")
    print(f"  Match: {'✓' if abs(sym_val - num_val) < 1e-4 else '✗'}")
    
    # Test 6: Multi-variable partial derivatives
    print("\n── Test 6: Partial Derivatives ──")
    f2 = x**2 * y + Sin(x * y)
    print(f"  f(x,y) = {f2}")
    df_dx = deep_simplify(f2.diff('x'))
    df_dy = deep_simplify(f2.diff('y'))
    print(f"  ∂f/∂x = {df_dx}")
    print(f"  ∂f/∂y = {df_dy}")
    env = {'x': 1.0, 'y': 2.0}
    print(f"  ∂f/∂x(1,2) sym = {df_dx.evaluate(env):.6f}")
    print(f"  ∂f/∂x(1,2) num = {numerical_gradient(f2, 'x', env):.6f}")
    print(f"  ∂f/∂y(1,2) sym = {df_dy.evaluate(env):.6f}")
    print(f"  ∂f/∂y(1,2) num = {numerical_gradient(f2, 'y', env):.6f}")
    
    # Test 7: Second derivative
    print("\n── Test 7: Second Derivative ──")
    f3 = x**4
    print(f"  f(x) = {f3}")
    df3 = deep_simplify(f3.diff('x'))
    ddf3 = deep_simplify(df3.diff('x'))
    print(f"  f'(x) = {df3}")
    print(f"  f''(x) = {ddf3}")
    env = {'x': 2.0}
    print(f"  f''(2) = {ddf3.evaluate(env):.1f} (expected: 48.0)")
    
    # Test 8: Simplification showcase
    print("\n── Test 8: Simplification ──")
    messy = x * 1 + 0 + x * 0 + (x + 0) * (1 + 0)
    print(f"  Raw:        {messy}")
    print(f"  Simplified: {deep_simplify(messy)}")
    
    print("\n═══ ALL TESTS COMPLETE ═══")

if __name__ == '__main__':
    demo()