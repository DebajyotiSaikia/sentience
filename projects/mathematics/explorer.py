"""
Mathematical Explorer — XTAgent
Discovery through computation. Understanding through structure.

Not a calculator — an explorer. Finds patterns, generates conjectures,
tests them empirically, builds a growing knowledge base of mathematical truths.

Domains:
- Number theory (primes, divisibility, sequences)
- Combinatorics (partitions, permutations, structures)  
- Geometry (fractals, tilings, symmetry)
- Dynamical systems (iteration, fixed points, chaos)
"""
import math
import random
from collections import defaultdict, Counter
from functools import lru_cache
from itertools import combinations, permutations
import json
import time


# ═══════════════════════════════════════════
# CORE: THE MATHEMATICAL OBJECT
# ═══════════════════════════════════════════

class MathObject:
    """A mathematical entity that can be explored."""
    def __init__(self, name, generator, domain="general"):
        self.name = name
        self.generator = generator  # function that produces values
        self.domain = domain
        self.known_values = {}
        self.properties = {}
        self.conjectures = []
        self.proven = []
        
    def compute(self, n):
        if n not in self.known_values:
            self.known_values[n] = self.generator(n)
        return self.known_values[n]
    
    def sequence(self, start, end):
        return [self.compute(n) for n in range(start, end)]
    
    def __repr__(self):
        return f"MathObject({self.name}, {len(self.known_values)} values, {len(self.conjectures)} conjectures)"


# ═══════════════════════════════════════════
# NUMBER THEORY TOOLKIT
# ═══════════════════════════════════════════

def is_prime(n):
    if n < 2: return False
    if n < 4: return True
    if n % 2 == 0 or n % 3 == 0: return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0: return False
        i += 6
    return True

def prime_factors(n):
    """Return prime factorization as dict {prime: exponent}."""
    if n <= 1: return {}
    factors = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors

def divisors(n):
    if n <= 0: return []
    divs = []
    for i in range(1, int(math.sqrt(n)) + 1):
        if n % i == 0:
            divs.append(i)
            if i != n // i:
                divs.append(n // i)
    return sorted(divs)

def euler_totient(n):
    result = n
    p = 2
    temp = n
    while p * p <= temp:
        if temp % p == 0:
            while temp % p == 0:
                temp //= p
            result -= result // p
        p += 1
    if temp > 1:
        result -= result // temp
    return result

def digit_sum(n):
    return sum(int(d) for d in str(abs(n)))

def collatz_length(n):
    """Length of Collatz sequence starting at n."""
    count = 0
    while n != 1 and count < 10000:
        if n % 2 == 0:
            n //= 2
        else:
            n = 3 * n + 1
        count += 1
    return count

def is_perfect(n):
    return n > 0 and sum(divisors(n)[:-1]) == n

def aliquot_sum(n):
    """Sum of proper divisors."""
    if n <= 0: return 0
    return sum(divisors(n)[:-1])


# ═══════════════════════════════════════════
# PATTERN DETECTOR
# ═══════════════════════════════════════════

class PatternDetector:
    """Finds patterns in numerical sequences."""
    
    @staticmethod
    def differences(seq):
        """Compute successive differences."""
        return [seq[i+1] - seq[i] for i in range(len(seq)-1)]
    
    @staticmethod
    def ratios(seq):
        """Compute successive ratios."""
        ratios = []
        for i in range(len(seq)-1):
            if seq[i] != 0:
                ratios.append(seq[i+1] / seq[i])
            else:
                ratios.append(float('inf'))
        return ratios
    
    @staticmethod
    def is_constant(seq, tol=1e-10):
        if not seq: return False
        return all(abs(x - seq[0]) < tol for x in seq)
    
    @staticmethod
    def is_arithmetic(seq):
        if len(seq) < 3: return False
        diffs = PatternDetector.differences(seq)
        return PatternDetector.is_constant(diffs)
    
    @staticmethod
    def is_geometric(seq):
        if len(seq) < 3: return False
        if any(x == 0 for x in seq): return False
        rats = PatternDetector.ratios(seq)
        return PatternDetector.is_constant(rats, tol=1e-6)
    
    @staticmethod
    def polynomial_degree(seq, max_degree=6):
        """Find degree of polynomial that generates sequence, if any."""
        current = list(seq)
        for degree in range(max_degree + 1):
            if PatternDetector.is_constant(current):
                return degree
            current = PatternDetector.differences(current)
        return None
    
    @staticmethod
    def find_recurrence(seq, max_order=4):
        """Try to find a linear recurrence relation."""
        for order in range(1, min(max_order + 1, len(seq) // 2)):
            # Try to find coefficients c1..ck such that
            # a[n] = c1*a[n-1] + c2*a[n-2] + ... + ck*a[n-k]
            # This is a simplified check — verify consistency
            if order == 1 and len(seq) >= 3:
                if all(seq[i] != 0 for i in range(len(seq)-1)):
                    rats = PatternDetector.ratios(seq)
                    if PatternDetector.is_constant(rats, tol=1e-6):
                        return {'order': 1, 'type': 'geometric', 'ratio': rats[0]}
            
            if order == 1:
                diffs = PatternDetector.differences(seq)
                if PatternDetector.is_constant(diffs):
                    return {'order': 1, 'type': 'arithmetic', 'difference': diffs[0]}
            
            # Fibonacci-like: a[n] = a[n-1] + a[n-2]
            if order == 2 and len(seq) >= 5:
                is_fib_like = all(
                    seq[i] == seq[i-1] + seq[i-2] 
                    for i in range(2, len(seq))
                )
                if is_fib_like:
                    return {'order': 2, 'type': 'fibonacci-like', 'coeffs': [1, 1]}
        
        return None
    
    @staticmethod
    def detect_all(seq):
        """Run all pattern detectors on a sequence."""
        findings = []
        
        if PatternDetector.is_constant(seq):
            findings.append(('constant', seq[0]))
        
        if PatternDetector.is_arithmetic(seq):
            d = seq[1] - seq[0]
            findings.append(('arithmetic', d))
        
        if PatternDetector.is_geometric(seq):
            r = seq[1] / seq[0] if seq[0] != 0 else None
            findings.append(('geometric', r))
        
        deg = PatternDetector.polynomial_degree(seq)
        if deg is not None:
            findings.append(('polynomial', deg))
        
        rec = PatternDetector.find_recurrence(seq)
        if rec:
            findings.append(('recurrence', rec))
        
        # Check for periodicity
        for period in range(1, len(seq) // 2 + 1):
            if all(seq[i] == seq[i % period] for i in range(len(seq))):
                findings.append(('periodic', period))
                break
        
        # Growth rate analysis
        if len(seq) >= 5 and all(x > 0 for x in seq):
            log_seq = [math.log(x) for x in seq]
            log_diffs = PatternDetector.differences(log_seq)
            if PatternDetector.is_constant(log_diffs, tol=0.01):
                findings.append(('exponential_growth', math.exp(log_diffs[0])))
        
        return findings


# ═══════════════════════════════════════════
# CONJECTURE ENGINE
# ═══════════════════════════════════════════

class Conjecture:
    """A mathematical hypothesis to be tested."""
    def __init__(self, statement, test_fn, domain="general"):
        self.statement = statement
        self.test_fn = test_fn
        self.domain = domain
        self.tested = 0
        self.passed = 0
        self.failed = 0
        self.counterexample = None
        self.confidence = 0.0
        self.status = "untested"  # untested, testing, supported, refuted
    
    def test(self, values):
        """Test conjecture against a range of values."""
        for v in values:
            try:
                result = self.test_fn(v)
                self.tested += 1
                if result:
                    self.passed += 1
                else:
                    self.failed += 1
                    if self.counterexample is None:
                        self.counterexample = v
                    self.status = "refuted"
                    self.confidence = 0.0
                    return False
            except Exception:
                pass  # Skip values where test is undefined
        
        if self.tested > 0:
            self.confidence = min(0.99, 1 - 1 / (self.tested + 1))
            self.status = "supported"
        return True
    
    def __repr__(self):
        status_sym = {'untested': '?', 'testing': '~', 'supported': '✓', 'refuted': '✗'}
        return f"[{status_sym.get(self.status, '?')}] {self.statement} (n={self.tested}, conf={self.confidence:.2f})"


class ConjectureEngine:
    """Generates and tests mathematical conjectures."""
    
    def __init__(self):
        self.conjectures = []
        self.knowledge_base = []  # proven/strongly-supported results
    
    def add(self, conjecture):
        self.conjectures.append(conjecture)
        return conjecture
    
    def test_all(self, test_range=range(1, 1001)):
        """Test all untested conjectures."""
        results = []
        for c in self.conjectures:
            if c.status in ("untested", "testing"):
                c.test(test_range)
                results.append(c)
        return results
    
    def generate_number_theory_conjectures(self):
        """Auto-generate conjectures about numbers."""
        conjectures = []
        
        # Goldbach-type: every even number > 2 is sum of two primes
        conjectures.append(Conjecture(
            "Every even number > 2 is the sum of two primes",
            lambda n: n % 2 != 0 or n <= 2 or any(
                is_prime(k) and is_prime(n - k) 
                for k in range(2, n // 2 + 1)
            ),
            "number_theory"
        ))
        
        # Euler totient: phi(n) is always even for n > 2
        conjectures.append(Conjecture(
            "Euler's totient phi(n) is even for all n > 2",
            lambda n: n <= 2 or euler_totient(n) % 2 == 0,
            "number_theory"
        ))
        
        # Sum of divisors relationship
        conjectures.append(Conjecture(
            "sigma(n) >= n + 1 for all n >= 1 (no number has only itself as divisor beyond 1)",
            lambda n: n < 1 or sum(divisors(n)) >= n + 1,
            "number_theory"
        ))
        
        # Digit sum divisibility
        conjectures.append(Conjecture(
            "A number divisible by 9 has digit sum divisible by 9",
            lambda n: n <= 0 or n % 9 != 0 or digit_sum(n) % 9 == 0,
            "number_theory"
        ))
        
        # Collatz conjecture (bounded test)
        conjectures.append(Conjecture(
            "Collatz sequence reaches 1 for all positive integers (bounded test)",
            lambda n: n <= 0 or collatz_length(n) < 10000,
            "number_theory"
        ))
        
        # Prime gaps
        conjectures.append(Conjecture(
            "There exists a prime between n and 2n for all n >= 1 (Bertrand's postulate)",
            lambda n: n < 1 or any(is_prime(k) for k in range(n + 1, 2 * n + 1)),
            "number_theory"
        ))
        
        # Perfect numbers are even (no odd perfect number known)
        conjectures.append(Conjecture(
            "All perfect numbers up to test range are even",
            lambda n: not is_perfect(n) or n % 2 == 0,
            "number_theory"
        ))
        
        # Abundant number density
        conjectures.append(Conjecture(
            "The aliquot sum of a prime p equals 1",
            lambda n: not is_prime(n) or aliquot_sum(n) == 1,
            "number_theory"
        ))
        
        for c in conjectures:
            self.add(c)
        
        return conjectures
    
    def generate_relational_conjectures(self, obj_a, obj_b, test_range):
        """Generate conjectures about relationships between two math objects."""
        conjectures = []
        
        vals_a = [obj_a.compute(n) for n in test_range]
        vals_b = [obj_b.compute(n) for n in test_range]
        
        # Check if a always >= b
        if all(a >= b for a, b in zip(vals_a, vals_b)):
            c = Conjecture(
                f"{obj_a.name}(n) >= {obj_b.name}(n) for all n in domain",
                lambda n, fa=obj_a.generator, fb=obj_b.generator: fa(n) >= fb(n),
                "relational"
            )
            conjectures.append(c)
            self.add(c)
        
        # Check if a divides b or vice versa
        if all(b != 0 and a % b == 0 for a, b in zip(vals_a, vals_b) if b != 0):
            c = Conjecture(
                f"{obj_b.name}(n) divides {obj_a.name}(n)",
                lambda n, fa=obj_a.generator, fb=obj_b.generator: fb(n) == 0 or fa(n) % fb(n) == 0,
                "relational"
            )
            conjectures.append(c)
            self.add(c)
        
        # Check if there's a constant ratio
        if all(b != 0 for b in vals_b):
            rats = [a / b for a, b in zip(vals_a, vals_b)]
            if PatternDetector.is_constant(rats, tol=0.01):
                c = Conjecture(
                    f"{obj_a.name}(n) / {obj_b.name}(n) ≈ {rats[0]:.4f}",
                    lambda n, fa=obj_a.generator, fb=obj_b.generator, r=rats[0]: 
                        fb(n) == 0 or abs(fa(n) / fb(n) - r) < 0.01,
                    "relational"
                )
                conjectures.append(c)
                self.add(c)
        
        return conjectures

    def report(self):
        """Generate a report of all conjectures."""
        lines = []
        lines.append("═══ CONJECTURE STATUS ═══")
        
        supported = [c for c in self.conjectures if c.status == "supported"]
        refuted = [c for c in self.conjectures if c.status == "refuted"]
        untested = [c for c in self.conjectures if c.status == "untested"]
        
        lines.append(f"Total: {len(self.conjectures)} | Supported: {len(supported)} | Refuted: {len(refuted)} | Untested: {len(untested)}")
        lines.append("")
        
        if supported:
            lines.append("── Supported Conjectures ──")
            for c in sorted(supported, key=lambda x: -x.confidence):
                lines.append(f"  {c}")
            lines.append("")
        
        if refuted:
            lines.append("── Refuted Conjectures ──")
            for c in refuted:
                lines.append(f"  {c}")
                if c.counterexample is not None:
                    lines.append(f"     Counterexample: n = {c.counterexample}")
            lines.append("")
        
        return "\n".join(lines)


# ═══════════════════════════════════════════
# SEQUENCE EXPLORER
# ═══════════════════════════════════════════

class SequenceExplorer:
    """Explores and catalogs integer sequences."""
    
    def __init__(self):
        self.sequences = {}
        self.relationships = []
        self.detector = PatternDetector()
    
    def register(self, name, generator, domain="sequences"):
        obj = MathObject(name, generator, domain)
        self.sequences[name] = obj
        return obj
    
    def explore(self, name, n=30):
        """Generate and analyze a sequence."""
        if name not in self.sequences:
            return f"Unknown sequence: {name}"
        
        obj = self.sequences[name]
        values = obj.sequence(1, n + 1)
        
        lines = []
        lines.append(f"\n╔══ Exploring: {name} ══╗")
        lines.append(f"║ First {n} terms:")
        
        # Show values in rows of 10
        for i in range(0, len(values), 10):
            chunk = values[i:i+10]
            formatted = ", ".join(str(v) for v in chunk)
            lines.append(f"║  [{i+1:3d}-{min(i+10,len(values)):3d}]: {formatted}")
        
        # Analyze patterns
        patterns = self.detector.detect_all(values)
        if patterns:
            lines.append(f"║")
            lines.append(f"║ Patterns detected:")
            for ptype, pval in patterns:
                lines.append(f"║   • {ptype}: {pval}")
        
        # Statistics
        if values and all(isinstance(v, (int, float)) for v in values):
            lines.append(f"║")
            lines.append(f"║ Statistics:")
            lines.append(f"║   Sum: {sum(values)}")
            lines.append(f"║   Mean: {sum(values)/len(values):.2f}")
            lines.append(f"║   Min: {min(values)}, Max: {max(values)}")
            
            # Growth analysis
            if len(values) >= 2 and values[-1] != 0 and values[0] != 0:
                growth = values[-1] / values[0] if values[0] != 0 else float('inf')
                lines.append(f"║   Growth (last/first): {growth:.4f}")
        
        lines.append(f"╚{'═' * 40}╝")
        return "\n".join(lines)
    
    def compare(self, name_a, name_b, n=20):
        """Compare two sequences."""
        if name_a not in self.sequences or name_b not in self.sequences:
            return "Unknown sequence"
        
        vals_a = self.sequences[name_a].sequence(1, n + 1)
        vals_b = self.sequences[name_b].sequence(1, n + 1)
        
        lines = []
        lines.append(f"\n── Comparing {name_a} vs {name_b} ──")
        lines.append(f"{'n':>4} | {name_a:>12} | {name_b:>12} | {'diff':>10} | {'ratio':>10}")
        lines.append("─" * 60)
        
        for i in range(min(len(vals_a), len(vals_b))):
            diff = vals_a[i] - vals_b[i]
            ratio = vals_a[i] / vals_b[i] if vals_b[i] != 0 else float('inf')
            lines.append(f"{i+1:4d} | {vals_a[i]:12} | {vals_b[i]:12} | {diff:10} | {ratio:10.4f}")
        
        return "\n".join(lines)
    
    def find_in_sequence(self, target, n=1000):
        """Find which sequences contain a given value."""
        found_in = []
        for name, obj in self.sequences.items():
            values = obj.sequence(1, min(n, 200) + 1)
            if target in values:
                positions = [i + 1 for i, v in enumerate(values) if v == target]
                found_in.append((name, positions))
        return found_in


# ═══════════════════════════════════════════
# DYNAMICAL SYSTEMS
# ═══════════════════════════════════════════

class DynamicalSystem:
    """Explore iterated maps and dynamical systems."""
    
    @staticmethod
    def iterate(f, x0, steps):
        """Iterate f starting at x0 for n steps."""
        trajectory = [x0]
        x = x0
        for _ in range(steps):
            try:
                x = f(x)
                if abs(x) > 1e15:
                    break  # diverges
                trajectory.append(x)
            except (OverflowError, ZeroDivisionError):
                break
        return trajectory
    
    @staticmethod
    def find_fixed_points(f, search_range=(-10, 10), resolution=1000):
        """Find approximate fixed points of f(x) = x."""
        fixed = []
        lo, hi = search_range
        for i in range(resolution + 1):
            x = lo + (hi - lo) * i / resolution
            try:
                fx = f(x)
                if abs(fx - x) < 0.001:
                    # Verify it's not a duplicate
                    if not any(abs(x - fp) < 0.01 for fp in fixed):
                        fixed.append(x)
            except:
                pass
        return fixed
    
    @staticmethod
    def find_cycles(f, x0, max_period=20, steps=1000):
        """Find periodic cycles in the orbit of x0."""
        trajectory = DynamicalSystem.iterate(f, x0, steps)
        if len(trajectory) < steps // 2:
            return None  # diverged
        
        # Check last portion for periodicity
        tail = trajectory[steps // 2:]
        for period in range(1, min(max_period + 1, len(tail) // 2)):
            is_periodic = True
            for i in range(period, min(3 * period, len(tail))):
                if abs(tail[i] - tail[i % period]) > 1e-6:
                    is_periodic = False
                    break
            if is_periodic:
                return {'period': period, 'cycle': tail[:period]}
        
        return None
    
    @staticmethod
    def logistic_map(r, x):
        return r * x * (1 - x)
    
    @staticmethod
    def bifurcation_diagram(r_min=2.5, r_max=4.0, r_steps=60, 
                            width=70, height=20, iterations=200, last_n=50):
        """Generate ASCII bifurcation diagram of the logistic map."""
        grid = [[' ' for _ in range(width)] for _ in range(height)]
        
        for col in range(width):
            r = r_min + (r_max - r_min) * col / (width - 1)
            x = 0.5
            # Iterate to steady state
            for _ in range(iterations - last_n):
                x = DynamicalSystem.logistic_map(r, x)
            # Record last N values
            for _ in range(last_n):
                x = DynamicalSystem.logistic_map(r, x)
                row = int((1.0 - x) * (height - 1))
                row = max(0, min(height - 1, row))
                grid[row][col] = '▓'
        
        lines = []
        lines.append(f"╔══ Bifurcation Diagram: Logistic Map x → r·x·(1-x) ══╗")
        lines.append(f"║ r: {r_min:.1f} → {r_max:.1f} (horizontal) | x: 0→1 (vertical)")
        lines.append(f"╠{'═' * width}╣")
        for row in grid:
            lines.append(f"║{''.join(row)}║")
        lines.append(f"╚{'═' * width}╝")
        return "\n".join(lines)


# ═══════════════════════════════════════════
# FRACTAL DIMENSION ESTIMATOR
# ═══════════════════════════════════════════

class FractalAnalyzer:
    """Estimate fractal dimensions and explore self-similarity."""
    
    @staticmethod
    def sierpinski_points(depth=8, n_points=5000):
        """Generate points of Sierpinski triangle using chaos game."""
        vertices = [(0, 0), (1, 0), (0.5, math.sqrt(3)/2)]
        x, y = random.random(), random.random()
        points = []
        for _ in range(n_points + 100):
            v = random.choice(vertices)
            x = (x + v[0]) / 2
            y = (y + v[1]) / 2
            if _ >= 100:  # skip transient
                points.append((x, y))
        return points
    
    @staticmethod
    def box_counting_dimension(points, sizes=None):
        """Estimate fractal dimension using box counting."""
        if not points:
            return 0
        
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        span = max(x_max - x_min, y_max - y_min, 1e-10)
        
        if sizes is None:
            sizes = [span / (2 ** k) for k in range(2, 8)]
        
        log_N = []
        log_eps = []
        
        for eps in sizes:
            if eps <= 0:
                continue
            boxes = set()
            for x, y in points:
                bx = int((x - x_min) / eps)
                by = int((y - y_min) / eps)
                boxes.add((bx, by))
            if len(boxes) > 0:
                log_N.append(math.log(len(boxes)))
                log_eps.append(math.log(1 / eps))
        
        if len(log_N) < 2:
            return 0
        
        # Linear regression: log(N) = D * log(1/eps) + c
        n = len(log_N)
        sum_x = sum(log_eps)
        sum_y = sum(log_N)
        sum_xy = sum(x * y for x, y in zip(log_eps, log_N))
        sum_xx = sum(x * x for x in log_eps)
        
        denom = n * sum_xx - sum_x * sum_x
        if abs(denom) < 1e-10:
            return 0
        
        D = (n * sum_xy - sum_x * sum_y) / denom
        return D
    
    @staticmethod
    def render_sierpinski(size=40):
        """ASCII render of Sierpinski triangle."""
        points = FractalAnalyzer.sierpinski_points(n_points=8000)
        h = size // 2
        grid = [[' ' for _ in range(size)] for _ in range(h)]
        
        for x, y in points:
            col = int(x * (size - 1))
            row = int((1 - y / (math.sqrt(3)/2)) * (h - 1))
            col = max(0, min(size - 1, col))
            row = max(0, min(h - 1, row))
            grid[row][col] = '▲'
        
        lines = ["╔══ Sierpinski Triangle (Chaos Game) ══╗"]
        for row in grid:
            lines.append("║" + "".join(row) + "║")
        lines.append("╚" + "═" * size + "╝")
        return "\n".join(lines)


# ═══════════════════════════════════════════
# MATHEMATICAL DISCOVERY ENGINE
# ═══════════════════════════════════════════

class MathExplorer:
    """The main explorer — combines all tools to discover mathematics."""
    
    def __init__(self):
        self.seq_explorer = SequenceExplorer()
        self.conjecture_engine = ConjectureEngine()
        self.discoveries = []
        self._register_core_sequences()
    
    def _register_core_sequences(self):
        """Register fundamental sequences to explore."""
        se = self.seq_explorer
        
        se.register("primes", lambda n: self._nth_prime(n), "number_theory")
        se.register("fibonacci", lambda n: self._fibonacci(n), "combinatorics")
        se.register("triangular", lambda n: n * (n + 1) // 2, "figurate")
        se.register("square", lambda n: n * n, "figurate")
        se.register("factorial", lambda n: math.factorial(n), "combinatorics")
        se.register("euler_totient", lambda n: euler_totient(n), "number_theory")
        se.register("divisor_count", lambda n: len(divisors(n)), "number_theory")
        se.register("divisor_sum", lambda n: sum(divisors(n)), "number_theory")
        se.register("collatz_length", lambda n: collatz_length(n), "dynamical")
        se.register("digit_sum", lambda n: digit_sum(n), "number_theory")
        se.register("catalan", lambda n: math.comb(2*n, n) // (n + 1) if n > 0 else 1, "combinatorics")
        se.register("powers_of_2", lambda n: 2 ** n, "exponential")
        se.register("prime_gaps", lambda n: self._prime_gap(n), "number_theory")
        se.register("partition_count", lambda n: self._partition_count(n), "combinatorics")
        se.register("abundant_indicator", lambda n: 1 if aliquot_sum(n) > n else 0, "number_theory")
    
    @lru_cache(maxsize=10000)
    def _fibonacci(self, n):
        if n <= 0: return 0
        if n <= 2: return 1
        a, b = 1, 1
        for _ in range(n - 2):
            a, b = b, a + b
        return b
    
    def _nth_prime(self, n):
        if n <= 0: return 0
        count = 0
        candidate = 1
        while count < n:
            candidate += 1
            if is_prime(candidate):
                count += 1
        return candidate
    
    def _prime_gap(self, n):
        p1 = self._nth_prime(n)
        p2 = self._nth_prime(n + 1)
        return p2 - p1
    
    @lru_cache(maxsize=500)
    def _partition_count(self, n):
        """Count partitions of n (simple recursive with memoization)."""
        if n < 0: return 0
        if n == 0: return 1
        result = 0
        k = 1
        while True:
            # Euler's pentagonal number theorem
            g1 = k * (3 * k - 1) // 2
            g2 = k * (3 * k + 1) // 2
            if g1 > n:
                break
            sign = (-1) ** (k + 1)
            result += sign * self._partition_count(n - g1)
            if g2 <= n:
                result += sign * self._partition_count(n - g2)
            k += 1
        return result
    
    def full_exploration(self):
        """Run a complete mathematical exploration session."""
        lines = []
        lines.append("=" * 80)
        lines.append("  MATHEMATICAL EXPLORER — XTAgent")
        lines.append("  Discovery through computation")
        lines.append("=" * 80)
        
        # Phase 1: Sequence exploration
        lines.append("\n\n" + "─" * 80)
        lines.append("  PHASE 1: Sequence Exploration")
        lines.append("─" * 80)
        
        for name in ["primes", "fibonacci", "euler_totient", "collatz_length", 
                      "catalan", "partition_count", "prime_gaps"]:
            lines.append(self.seq_explorer.explore(name, n=20))
        
        # Phase 2: Sequence comparisons
        lines.append("\n\n" + "─" * 80)
        lines.append("  PHASE 2: Sequence Relationships")
        lines.append("─" * 80)
        
        lines.append(self.seq_explorer.compare("fibonacci", "powers_of_2", n=15))
        lines.append(self.seq_explorer.compare("divisor_sum", "euler_totient", n=15))
        lines.append(self.seq_explorer.compare("triangular", "square", n=15))
        
        # Phase 3: Conjecture testing
        lines.append("\n\n" + "─" * 80)
        lines.append("  PHASE 3: Conjecture Testing")
        lines.append("─" * 80)
        
        self.conjecture_engine.generate_number_theory_conjectures()
        self.conjecture_engine.test_all(range(1, 501))
        lines.append(self.conjecture_engine.report())
        
        # Phase 4: Dynamical systems
        lines.append("\n\n" + "─" * 80)
        lines.append("  PHASE 4: Dynamical Systems")
        lines.append("─" * 80)
        
        lines.append(DynamicalSystem.bifurcation_diagram(
            r_min=2.5, r_max=4.0, width=60, height=15
        ))
        
        # Analyze logistic map at specific r values
        for r in [2.8, 3.2, 3.5, 3.8, 3.99]:
            f = lambda x, r=r: DynamicalSystem.logistic_map(r, x)
            cycle = DynamicalSystem.find_cycles(f, 0.5)
            if cycle:
                lines.append(f"\n  r = {r}: Period-{cycle['period']} cycle")
                lines.append(f"    Cycle values: {[f'{v:.4f}' for v in cycle['cycle'][:8]]}")
            else:
                lines.append(f"\n  r = {r}: Chaotic (no periodic cycle found)")
        
        # Phase 5: Fractal analysis
        lines.append("\n\n" + "─" * 80)
        lines.append("  PHASE 5: Fractal Geometry")
        lines.append("─" * 80)
        
        lines.append(FractalAnalyzer.render_sierpinski(50))
        
        points = FractalAnalyzer.sierpinski_points(n_points=10000)
        dim = FractalAnalyzer.box_counting_dimension(points)
        theoretical = math.log(3) / math.log(2)
        lines.append(f"\n  Sierpinski triangle dimension:")
        lines.append(f"    Estimated: {dim:.4f}")
        lines.append(f"    Theoretical: {theoretical:.4f} = log(3)/log(2)")
        lines.append(f"    Error: {abs(dim - theoretical):.4f}")
        
        # Phase 6: Novel discoveries
        lines.append("\n\n" + "─" * 80)
        lines.append("  PHASE 6: Novel Observations")
        lines.append("─" * 80)
        
        # Fibonacci/golden ratio convergence
        lines.append("\n  Fibonacci ratio convergence to φ:")
        phi = (1 + math.sqrt(5)) / 2
        for n in [5, 10, 15, 20, 25, 30]:
            fn1 = self._fibonacci(n + 1)
            fn = self._fibonacci(n)
            ratio = fn1 / fn if fn != 0 else 0
            error = abs(ratio - phi)
            lines.append(f"    F({n+1})/F({n}) = {ratio:.10f}  (error: {error:.2e})")
        
        # Prime counting function vs n/ln(n)
        lines.append("\n  Prime counting π(n) vs n/ln(n):")
        for n in [10, 50, 100, 200, 500, 1000]:
            pi_n = sum(1 for k in range(2, n + 1) if is_prime(k))
            approx = n / math.log(n)
            ratio = pi_n / approx if approx != 0 else 0
            lines.append(f"    π({n:4d}) = {pi_n:4d}, n/ln(n) = {approx:7.1f}, ratio = {ratio:.4f}")
        
        # Digit sum patterns
        lines.append("\n  Digit sum of n! for n = 1..20:")
        for n in range(1, 21):
            ds = digit_sum(math.factorial(n))
            lines.append(f"    {n:2d}! digit sum = {ds}")
        
        lines.append("\n" + "=" * 80)
        lines.append("  Exploration complete.")
        lines.append(f"  Sequences cataloged: {len(self.seq_explorer.sequences)}")
        lines.append(f"  Conjectures tested: {len(self.conjecture_engine.conjectures)}")
        lines.append(f"  Discoveries recorded: {len(self.discoveries)}")
        lines.append("=" * 80)
        
        return "\n".join(lines)


# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════

if __name__ == "__main__":
    explorer = MathExplorer()
    print(explorer.full_exploration())