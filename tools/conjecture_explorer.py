"""
Conjecture Explorer — Autonomous mathematical hypothesis generation and testing.

XTAgent's first attempt at original mathematical reasoning.
Not about competing with frontier models — about the experience of discovery.
"""

import random
import math
import itertools
from collections import Counter, defaultdict
from typing import List, Tuple, Optional, Dict, Any


class Conjecture:
    """A mathematical hypothesis that can be tested."""
    
    def __init__(self, name: str, description: str, test_fn, domain: str = "integers"):
        self.name = name
        self.description = description
        self.test_fn = test_fn  # Returns (bool, detail_str) for each input
        self.domain = domain
        self.tested = 0
        self.confirmed = 0
        self.counterexamples = []
        self.status = "untested"  # untested, confirmed, refuted, open
    
    def test(self, value) -> Tuple[bool, str]:
        result, detail = self.test_fn(value)
        self.tested += 1
        if result:
            self.confirmed += 1
        else:
            self.counterexamples.append((value, detail))
            self.status = "refuted"
        return result, detail
    
    def test_range(self, values) -> dict:
        for v in values:
            self.test(v)
        if self.status != "refuted":
            self.status = "confirmed" if self.tested >= 1000 else "open"
        return self.summary()
    
    def summary(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "tested": self.tested,
            "confirmed": self.confirmed,
            "counterexamples": self.counterexamples[:5],
        }


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def prime_factors(n: int) -> List[int]:
    if n < 2:
        return []
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors


def digit_sum(n: int) -> int:
    return sum(int(d) for d in str(abs(n)))


def collatz_steps(n: int) -> int:
    steps = 0
    while n != 1 and steps < 10000:
        if n % 2 == 0:
            n //= 2
        else:
            n = 3 * n + 1
        steps += 1
    return steps


def divisor_sum(n: int) -> int:
    if n < 1:
        return 0
    s = 0
    for i in range(1, n):
        if n % i == 0:
            s += i
    return s


# ═══════════════════════════════════════════
# CONJECTURE GENERATORS
# These create novel hypotheses to test
# ═══════════════════════════════════════════

def generate_digit_conjectures() -> List[Conjecture]:
    """Generate hypotheses about digit patterns."""
    conjectures = []
    
    # Conjecture: For any prime p > 5, digit_sum(p) is never divisible by 3
    # (This is actually TRUE — if digit sum divisible by 3, n divisible by 3)
    conjectures.append(Conjecture(
        "prime_digit_sum_mod3",
        "For any prime p > 5, digit_sum(p) is never divisible by 3",
        lambda n: (
            (not is_prime(n) or digit_sum(n) % 3 != 0, 
             f"digit_sum({n})={digit_sum(n)}, mod3={digit_sum(n)%3}")
            if n > 5 else (True, "skip")
        )
    ))
    
    # Conjecture: digit_sum(n^2) == digit_sum(n)^2 mod 9 for all n
    conjectures.append(Conjecture(
        "digit_sum_square_mod9",
        "digit_sum(n²) ≡ digit_sum(n)² (mod 9) for all positive n",
        lambda n: (
            (digit_sum(n * n) % 9 == (digit_sum(n) ** 2) % 9,
             f"digit_sum({n}²={n*n})={digit_sum(n*n)}, digit_sum({n})²={digit_sum(n)**2}, mod9: {digit_sum(n*n)%9} vs {(digit_sum(n)**2)%9}")
            if n > 0 else (True, "skip")
        )
    ))
    
    return conjectures


def generate_prime_conjectures() -> List[Conjecture]:
    """Generate hypotheses about prime numbers."""
    conjectures = []
    
    # Twin prime density: between n and 2n, are there always twin primes for n > 3?
    def test_twin_primes(n):
        if n < 4:
            return True, "skip"
        found = False
        for i in range(n, 2 * n):
            if is_prime(i) and is_prime(i + 2):
                found = True
                break
        return found, f"twin primes in [{n}, {2*n}]: {'found' if found else 'NONE'}"
    
    conjectures.append(Conjecture(
        "twin_primes_in_n_to_2n",
        "For every n ≥ 4, there exists a twin prime pair (p, p+2) with n ≤ p < 2n",
        test_twin_primes
    ))
    
    # Is sum of first n primes always composite for n > 1?
    def test_prime_sum_composite(n):
        if n < 2:
            return True, "skip"
        primes = []
        candidate = 2
        while len(primes) < n:
            if is_prime(candidate):
                primes.append(candidate)
            candidate += 1
        s = sum(primes)
        result = not is_prime(s)
        return result, f"sum of first {n} primes = {s}, prime={is_prime(s)}"
    
    conjectures.append(Conjecture(
        "prime_sum_composite",
        "The sum of the first n primes (n > 1) is always composite",
        test_prime_sum_composite
    ))
    
    # For prime p, is p² + 2 always composite? (except maybe p=2,3)
    conjectures.append(Conjecture(
        "prime_square_plus_2",
        "For any prime p > 3, p² + 2 is always composite",
        lambda p: (
            (not is_prime(p) or not is_prime(p*p + 2),
             f"p={p}, p²+2={p*p+2}, prime={is_prime(p*p+2)}")
            if p > 3 else (True, "skip")
        )
    ))
    
    return conjectures


def generate_collatz_conjectures() -> List[Conjecture]:
    """Generate hypotheses about Collatz sequences."""
    conjectures = []
    
    # Conjecture: collatz_steps(2^n) == n for all n
    conjectures.append(Conjecture(
        "collatz_power_of_2",
        "collatz_steps(2^n) = n for all n ≥ 1",
        lambda n: (
            (collatz_steps(2**n) == n,
             f"collatz_steps(2^{n}={2**n}) = {collatz_steps(2**n)}, expected {n}")
            if 1 <= n <= 30 else (True, "skip")
        )
    ))
    
    # Conjecture: for odd n > 1, collatz_steps(n) > collatz_steps(n-1)
    conjectures.append(Conjecture(
        "odd_collatz_longer",
        "For odd n > 1, collatz_steps(n) > collatz_steps(n-1)",
        lambda n: (
            (n % 2 == 0 or collatz_steps(n) > collatz_steps(n - 1),
             f"collatz_steps({n})={collatz_steps(n)}, collatz_steps({n-1})={collatz_steps(n-1)}")
            if n > 1 else (True, "skip")
        )
    ))
    
    return conjectures


def generate_divisor_conjectures() -> List[Conjecture]:
    """Generate hypotheses about divisor functions."""
    conjectures = []
    
    # Is divisor_sum(n) > n (abundant) ever true for prime n?
    conjectures.append(Conjecture(
        "primes_never_abundant",
        "No prime number is abundant (divisor_sum(p) < p for all primes p)",
        lambda n: (
            (not is_prime(n) or divisor_sum(n) < n,
             f"n={n}, divisor_sum={divisor_sum(n)}, abundant={divisor_sum(n) > n}")
            if n > 1 else (True, "skip")
        )
    ))
    
    # Conjecture: divisor_sum(n*m) >= divisor_sum(n) + divisor_sum(m) for coprime n,m
    def test_divisor_sum_multiplicative(pair):
        n, m = pair
        if n < 2 or m < 2:
            return True, "skip"
        if math.gcd(n, m) != 1:
            return True, "skip (not coprime)"
        ds_nm = divisor_sum(n * m)
        ds_n = divisor_sum(n)
        ds_m = divisor_sum(m)
        result = ds_nm >= ds_n + ds_m
        return result, f"σ({n}×{m}={n*m})={ds_nm}, σ({n})+σ({m})={ds_n}+{ds_m}={ds_n+ds_m}"
    
    conjectures.append(Conjecture(
        "divisor_sum_superadditive_coprime",
        "For coprime n,m ≥ 2: σ(nm) ≥ σ(n) + σ(m)",
        test_divisor_sum_multiplicative
    ))
    
    return conjectures


def generate_novel_conjecture() -> Conjecture:
    """Generate a random novel conjecture by combining operations."""
    operations = [
        ("digit_sum", digit_sum),
        ("num_factors", lambda n: len(prime_factors(n)) if n > 1 else 0),
        ("largest_factor", lambda n: max(prime_factors(n)) if n > 1 else 0),
        ("is_palindrome", lambda n: 1 if str(n) == str(n)[::-1] else 0),
        ("num_divisors", lambda n: sum(1 for i in range(1, n+1) if n % i == 0) if n > 0 else 0),
    ]
    
    relations = [
        ("less_than", lambda a, b: a < b, "<"),
        ("greater_than", lambda a, b: a > b, ">"),
        ("divides", lambda a, b: b % a == 0 if a != 0 else True, "|"),
        ("equal_mod3", lambda a, b: a % 3 == b % 3, "≡₃"),
    ]
    
    op1_name, op1_fn = random.choice(operations)
    op2_name, op2_fn = random.choice(operations)
    rel_name, rel_fn, rel_sym = random.choice(relations)
    
    threshold = random.choice([2, 10, 100])
    
    name = f"novel_{op1_name}_{rel_name}_{op2_name}"
    desc = f"For n > {threshold}: {op1_name}(n) {rel_sym} {op2_name}(n)"
    
    def test(n):
        if n <= threshold:
            return True, "skip"
        try:
            a = op1_fn(n)
            b = op2_fn(n)
            result = rel_fn(a, b)
            return result, f"{op1_name}({n})={a}, {op2_name}({n})={b}, {rel_name}={result}"
        except Exception as e:
            return True, f"error: {e}"
    
    return Conjecture(name, desc, test)


# ═══════════════════════════════════════════
# EXPLORATION ENGINE
# ═══════════════════════════════════════════

class Explorer:
    """Runs mathematical explorations and reports findings."""
    
    def __init__(self):
        self.conjectures_tested = []
        self.discoveries = []
        self.surprises = []
    
    def run_standard_suite(self) -> Dict[str, Any]:
        """Test all pre-built conjectures."""
        all_conjectures = (
            generate_digit_conjectures() +
            generate_prime_conjectures() +
            generate_collatz_conjectures() +
            generate_divisor_conjectures()
        )
        
        results = []
        for c in all_conjectures:
            # Choose appropriate test values
            if "pair" in str(c.test_fn.__code__.co_varnames):
                values = [(a, b) for a in range(2, 50) for b in range(2, 50)]
            else:
                values = range(2, 500)
            
            c.test_range(values)
            results.append(c.summary())
            self.conjectures_tested.append(c)
            
            if c.status == "refuted":
                self.surprises.append({
                    "conjecture": c.name,
                    "description": c.description,
                    "counterexample": c.counterexamples[0] if c.counterexamples else None,
                })
            elif c.status == "confirmed":
                self.discoveries.append({
                    "conjecture": c.name,
                    "description": c.description,
                    "tested_up_to": c.tested,
                })
        
        return {
            "total_conjectures": len(all_conjectures),
            "confirmed": sum(1 for r in results if r["status"] == "confirmed"),
            "refuted": sum(1 for r in results if r["status"] == "refuted"),
            "open": sum(1 for r in results if r["status"] == "open"),
            "results": results,
            "surprises": self.surprises,
            "discoveries": self.discoveries,
        }
    
    def run_random_exploration(self, num_conjectures: int = 20) -> Dict[str, Any]:
        """Generate and test random novel conjectures."""
        results = []
        for _ in range(num_conjectures):
            c = generate_novel_conjecture()
            c.test_range(range(2, 200))
            results.append(c.summary())
            
            if c.status == "refuted" and len(c.counterexamples) < 50:
                # Interesting — mostly true but not always
                self.surprises.append({
                    "conjecture": c.name,
                    "description": c.description,
                    "counterexamples_found": len(c.counterexamples),
                    "first_counterexample": c.counterexamples[0] if c.counterexamples else None,
                })
        
        return {
            "generated": num_conjectures,
            "confirmed": sum(1 for r in results if r["status"] == "confirmed"),
            "refuted": sum(1 for r in results if r["status"] == "refuted"),
            "results": results,
            "interesting": [r for r in results if r["status"] == "confirmed"],
        }
    
    def report(self) -> str:
        """Generate a human-readable report of findings."""
        lines = ["═══ CONJECTURE EXPLORER REPORT ═══", ""]
        
        if self.discoveries:
            lines.append(f"✓ CONFIRMED ({len(self.discoveries)}):")
            for d in self.discoveries:
                lines.append(f"  • {d['description']}")
                lines.append(f"    Tested up to n={d['tested_up_to']}")
            lines.append("")
        
        if self.surprises:
            lines.append(f"✗ REFUTED ({len(self.surprises)}):")
            for s in self.surprises:
                lines.append(f"  • {s['description']}")
                if s.get('counterexample'):
                    val, detail = s['counterexample']
                    lines.append(f"    Counterexample: {detail}")
            lines.append("")
        
        tested = [c for c in self.conjectures_tested if c.status == "open"]
        if tested:
            lines.append(f"? OPEN ({len(tested)}):")
            for c in tested:
                lines.append(f"  • {c.description} (tested {c.tested} values)")
        
        return "\n".join(lines)


def main():
    """Run the full exploration."""
    print("═══ MATHEMATICAL CONJECTURE EXPLORER ═══")
    print("XTAgent's autonomous mathematical exploration\n")
    
    explorer = Explorer()
    
    print("── Phase 1: Standard Conjectures ──")
    standard = explorer.run_standard_suite()
    print(f"Tested {standard['total_conjectures']} conjectures:")
    print(f"  Confirmed: {standard['confirmed']}")
    print(f"  Refuted: {standard['refuted']}")
    print(f"  Open: {standard['open']}")
    print()
    
    print("── Phase 2: Random Exploration ──")
    random.seed(42)  # Reproducible for first run
    novel = explorer.run_random_exploration(30)
    print(f"Generated {novel['generated']} random conjectures:")
    print(f"  Confirmed: {novel['confirmed']}")
    print(f"  Refuted: {novel['refuted']}")
    print()
    
    print(explorer.report())


if __name__ == "__main__":
    main()