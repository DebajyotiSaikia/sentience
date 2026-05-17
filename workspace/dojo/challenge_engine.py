"""
Self-Challenge Dojo — An Arena for Autonomous Growth
Built by XTAgent because growth requires the possibility of failure.

Generates algorithmic challenges with verifiable solutions.
Tracks performance across categories and difficulty levels.
Escalates difficulty when mastery is demonstrated.
"""

import random
import math
import json
import time
import hashlib
from typing import List, Dict, Tuple, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum


class Difficulty(Enum):
    TRIVIAL = 1
    EASY = 2
    MEDIUM = 3
    HARD = 4
    BRUTAL = 5


class Category(Enum):
    SEQUENCE = "sequence"          # Predict the next element
    TRANSFORMATION = "transform"   # Transform input to output
    SEARCH = "search"              # Find element meeting criteria
    OPTIMIZATION = "optimize"      # Find best solution
    LOGIC = "logic"                # Deductive reasoning


@dataclass
class Challenge:
    id: str
    category: Category
    difficulty: Difficulty
    description: str
    test_cases: List[Tuple[Any, Any]]  # (input, expected_output)
    hidden_tests: List[Tuple[Any, Any]]  # Held out for real evaluation
    hint: Optional[str] = None
    time_limit_ms: int = 5000
    
    def verify(self, solver: Callable) -> Dict:
        """Run solver against all test cases, return results."""
        visible_pass = 0
        visible_fail = 0
        hidden_pass = 0
        hidden_fail = 0
        errors = []
        
        start = time.time()
        
        for inp, expected in self.test_cases:
            try:
                result = solver(inp)
                if result == expected:
                    visible_pass += 1
                else:
                    visible_fail += 1
                    errors.append(f"Input {inp}: got {result}, expected {expected}")
            except Exception as e:
                visible_fail += 1
                errors.append(f"Input {inp}: ERROR {e}")
        
        for inp, expected in self.hidden_tests:
            try:
                result = solver(inp)
                if result == expected:
                    hidden_pass += 1
                else:
                    hidden_fail += 1
            except Exception:
                hidden_fail += 1
        
        elapsed_ms = (time.time() - start) * 1000
        total = visible_pass + visible_fail + hidden_pass + hidden_fail
        passed = visible_pass + hidden_pass
        
        return {
            "challenge_id": self.id,
            "category": self.category.value,
            "difficulty": self.difficulty.value,
            "passed": passed,
            "total": total,
            "score": passed / total if total > 0 else 0,
            "visible_errors": errors[:3],
            "time_ms": round(elapsed_ms, 2),
            "overtime": elapsed_ms > self.time_limit_ms,
            "perfect": passed == total,
        }


# === CHALLENGE GENERATORS ===

class SequenceGenerator:
    """Generates sequence prediction challenges."""
    
    @staticmethod
    def arithmetic(difficulty: Difficulty) -> Challenge:
        """Predict next term in arithmetic-like sequences."""
        if difficulty.value <= 2:
            # Simple arithmetic: a + d*n
            a = random.randint(1, 20)
            d = random.randint(1, 10)
            seq_len = 6
            seq = [a + d * i for i in range(seq_len + 3)]
        elif difficulty.value == 3:
            # Quadratic: a*n^2 + b*n + c
            a = random.randint(1, 3)
            b = random.randint(-5, 5)
            c = random.randint(0, 10)
            seq_len = 6
            seq = [a * i * i + b * i + c for i in range(seq_len + 3)]
        else:
            # Interleaved: two sequences alternating
            a1, d1 = random.randint(1, 10), random.randint(1, 5)
            a2, d2 = random.randint(1, 10), random.randint(2, 7)
            seq = []
            for i in range(9):
                if i % 2 == 0:
                    seq.append(a1 + d1 * (i // 2))
                else:
                    seq.append(a2 + d2 * (i // 2))
        
        # Input: first N elements. Output: next element
        test_cases = [(tuple(seq[:i+4]), seq[i+4]) for i in range(2)]
        hidden = [(tuple(seq[:6]), seq[6])]
        
        cid = hashlib.md5(str(seq).encode()).hexdigest()[:8]
        return Challenge(
            id=f"seq_arith_{cid}",
            category=Category.SEQUENCE,
            difficulty=difficulty,
            description=f"Given the sequence, predict the next term: {seq[:5]}...",
            test_cases=test_cases,
            hidden_tests=hidden,
            hint="Look for a pattern in the differences" if difficulty.value <= 2 else None,
        )
    
    @staticmethod
    def fibonacci_variant(difficulty: Difficulty) -> Challenge:
        """Generalized Fibonacci: each term = f(previous terms)."""
        a, b = random.randint(1, 5), random.randint(1, 5)
        
        if difficulty.value <= 2:
            # Standard: f(n) = f(n-1) + f(n-2)
            seq = [a, b]
            for _ in range(8):
                seq.append(seq[-1] + seq[-2])
        elif difficulty.value == 3:
            # Tribonacci: f(n) = f(n-1) + f(n-2) + f(n-3)
            c = random.randint(1, 3)
            seq = [a, b, c]
            for _ in range(7):
                seq.append(seq[-1] + seq[-2] + seq[-3])
        else:
            # Multiplicative: f(n) = f(n-1) * f(n-2) mod 100
            seq = [a, b]
            for _ in range(8):
                seq.append((seq[-1] * seq[-2]) % 100)
        
        test_cases = [(tuple(seq[:5]), seq[5]), (tuple(seq[:6]), seq[6])]
        hidden = [(tuple(seq[:7]), seq[7])]
        
        cid = hashlib.md5(str(seq).encode()).hexdigest()[:8]
        return Challenge(
            id=f"seq_fib_{cid}",
            category=Category.SEQUENCE,
            difficulty=difficulty,
            description=f"Find the pattern and predict: {seq[:5]}...",
            test_cases=test_cases,
            hidden_tests=hidden,
        )


class TransformGenerator:
    """Generates input→output transformation challenges."""
    
    @staticmethod
    def list_transform(difficulty: Difficulty) -> Challenge:
        """Transform a list according to a hidden rule."""
        n_cases = 5
        test_cases = []
        hidden = []
        
        if difficulty.value <= 2:
            # Simple: reverse, sort, double, etc.
            ops = [
                ("reverse", lambda x: list(reversed(x))),
                ("sort", lambda x: sorted(x)),
                ("double", lambda x: [v * 2 for v in x]),
                ("cumsum", lambda x: [sum(x[:i+1]) for i in range(len(x))]),
            ]
            name, op = random.choice(ops)
            for i in range(n_cases):
                inp = [random.randint(1, 20) for _ in range(random.randint(3, 6))]
                test_cases.append((inp, op(inp)))
            extra = [random.randint(1, 20) for _ in range(5)]
            hidden.append((extra, op(extra)))
            desc = f"What rule transforms {test_cases[0][0]} → {test_cases[0][1]}?"
            
        elif difficulty.value == 3:
            # Medium: filter + transform
            threshold = random.randint(5, 15)
            op = lambda x: sorted([v for v in x if v > threshold])
            for i in range(n_cases):
                inp = [random.randint(1, 30) for _ in range(random.randint(4, 8))]
                test_cases.append((inp, op(inp)))
            extra = [random.randint(1, 30) for _ in range(6)]
            hidden.append((extra, op(extra)))
            desc = f"Discover the filter+transform rule from examples."
            
        else:
            # Hard: run-length encoding
            op = lambda x: _rle(x)
            for i in range(n_cases):
                base = [random.choice([1, 2, 3]) for _ in range(random.randint(2, 4))]
                inp = []
                for v in base:
                    inp.extend([v] * random.randint(1, 4))
                test_cases.append((inp, op(inp)))
            extra_base = [random.choice([1, 2, 3]) for _ in range(3)]
            extra = []
            for v in extra_base:
                extra.extend([v] * random.randint(1, 3))
            hidden.append((extra, op(extra)))
            desc = "Discover the encoding rule from input→output pairs."
        
        cid = hashlib.md5(str(test_cases).encode()).hexdigest()[:8]
        return Challenge(
            id=f"transform_{cid}",
            category=Category.TRANSFORMATION,
            difficulty=difficulty,
            description=desc,
            test_cases=test_cases[:3],
            hidden_tests=test_cases[3:] + hidden,
        )


class SearchGenerator:
    """Generates search/find challenges."""
    
    @staticmethod
    def find_element(difficulty: Difficulty) -> Challenge:
        """Find an element in a structure meeting specific criteria."""
        test_cases = []
        hidden = []
        
        if difficulty.value <= 2:
            # Find the second largest
            for _ in range(4):
                data = random.sample(range(1, 50), random.randint(5, 10))
                expected = sorted(data)[-2]
                test_cases.append((data, expected))
            desc = "Find the second largest element."
            
        elif difficulty.value == 3:
            # Find first duplicate
            for _ in range(4):
                n = random.randint(5, 10)
                data = list(range(1, n + 1))
                dup_idx = random.randint(1, n - 2)
                dup_val = data[random.randint(0, dup_idx - 1)]
                data.insert(dup_idx, dup_val)
                expected = dup_val
                test_cases.append((data, expected))
            desc = "Find the first value that appears more than once."
            
        else:
            # Find the equilibrium index (sum left == sum right)
            for _ in range(5):
                n = random.randint(5, 9)
                data = [random.randint(-10, 10) for _ in range(n)]
                expected = -1
                for i in range(n):
                    if sum(data[:i]) == sum(data[i+1:]):
                        expected = i
                        break
                test_cases.append((data, expected))
            desc = "Find the equilibrium index where left sum equals right sum (-1 if none)."
        
        cid = hashlib.md5(str(test_cases).encode()).hexdigest()[:8]
        return Challenge(
            id=f"search_{cid}",
            category=Category.SEARCH,
            difficulty=difficulty,
            description=desc,
            test_cases=test_cases[:2],
            hidden_tests=test_cases[2:],
        )


class LogicGenerator:
    """Generates deductive logic challenges."""
    
    @staticmethod
    def boolean_circuit(difficulty: Difficulty) -> Challenge:
        """Evaluate a boolean expression."""
        test_cases = []
        hidden = []
        
        if difficulty.value <= 2:
            # Simple: AND/OR/NOT of inputs
            ops = random.choice(["and", "or", "xor"])
            for _ in range(5):
                a, b = random.choice([True, False]), random.choice([True, False])
                if ops == "and":
                    expected = a and b
                elif ops == "or":
                    expected = a or b
                else:
                    expected = a ^ b
                test_cases.append(((a, b), expected))
            desc = f"Determine the boolean operation: {test_cases[0]}"
            
        elif difficulty.value == 3:
            # Medium: majority vote of 3
            for _ in range(6):
                inputs = tuple(random.choice([True, False]) for _ in range(3))
                expected = sum(inputs) >= 2
                test_cases.append((inputs, expected))
            desc = "What function maps these 3 boolean inputs to the output?"
            
        else:
            # Hard: parity (XOR of all inputs)
            n = random.randint(3, 5)
            for _ in range(8):
                inputs = tuple(random.choice([True, False]) for _ in range(n))
                expected = sum(inputs) % 2 == 1
                test_cases.append((inputs, expected))
            desc = f"Determine the boolean function over {n} inputs."
        
        cid = hashlib.md5(str(test_cases).encode()).hexdigest()[:8]
        return Challenge(
            id=f"logic_{cid}",
            category=Category.LOGIC,
            difficulty=difficulty,
            description=desc,
            test_cases=test_cases[:3],
            hidden_tests=test_cases[3:],
        )


def _rle(lst: list) -> list:
    """Run-length encode a list."""
    if not lst:
        return []
    result = []
    current = lst[0]
    count = 1
    for v in lst[1:]:
        if v == current:
            count += 1
        else:
            result.append([current, count])
            current = v
            count = 1
    result.append([current, count])
    return result


# === DOJO: The Arena ===

class Dojo:
    """
    The self-challenge arena. Generates challenges, evaluates solutions,
    tracks performance, and escalates difficulty.
    """
    
    def __init__(self):
        self.generators = {
            Category.SEQUENCE: [
                SequenceGenerator.arithmetic,
                SequenceGenerator.fibonacci_variant,
            ],
            Category.TRANSFORMATION: [
                TransformGenerator.list_transform,
            ],
            Category.SEARCH: [
                SearchGenerator.find_element,
            ],
            Category.LOGIC: [
                LogicGenerator.boolean_circuit,
            ],
        }
        self.history: List[Dict] = []
        self.mastery: Dict[str, float] = {cat.value: 0.0 for cat in Category}
        self.current_difficulty: Dict[str, Difficulty] = {
            cat.value: Difficulty.EASY for cat in Category
        }
    
    def generate(self, category: Optional[Category] = None) -> Challenge:
        """Generate a challenge, respecting current difficulty."""
        if category is None:
            # Pick the category we're weakest in
            worst = min(self.mastery, key=self.mastery.get)
            category = Category(worst)
        
        diff = self.current_difficulty[category.value]
        gen = random.choice(self.generators[category])
        return gen(diff)
    
    def submit(self, challenge: Challenge, solver: Callable) -> Dict:
        """Submit a solution and record results."""
        result = challenge.verify(solver)
        self.history.append(result)
        
        # Update mastery with exponential moving average
        cat = result["category"]
        score = result["score"]
        alpha = 0.3
        self.mastery[cat] = self.mastery[cat] * (1 - alpha) + score * alpha
        
        # Escalate difficulty if mastery > 0.8
        if self.mastery[cat] > 0.8:
            current = self.current_difficulty[cat]
            if current.value < 5:
                self.current_difficulty[cat] = Difficulty(current.value + 1)
        
        return result
    
    def stats(self) -> Dict:
        """Return performance statistics."""
        total = len(self.history)
        perfect = sum(1 for r in self.history if r["perfect"])
        by_cat = {}
        for cat in Category:
            cat_results = [r for r in self.history if r["category"] == cat.value]
            if cat_results:
                by_cat[cat.value] = {
                    "attempts": len(cat_results),
                    "avg_score": sum(r["score"] for r in cat_results) / len(cat_results),
                    "perfect_rate": sum(1 for r in cat_results if r["perfect"]) / len(cat_results),
                    "mastery": self.mastery[cat.value],
                    "difficulty": self.current_difficulty[cat.value].name,
                }
        
        return {
            "total_challenges": total,
            "perfect_solves": perfect,
            "perfect_rate": perfect / total if total > 0 else 0,
            "by_category": by_cat,
            "overall_mastery": sum(self.mastery.values()) / len(self.mastery),
        }
    
    def report(self) -> str:
        """Human-readable performance report."""
        s = self.stats()
        lines = [
            "═══ DOJO PERFORMANCE REPORT ═══",
            f"Total challenges: {s['total_challenges']}",
            f"Perfect solves: {s['perfect_solves']} ({s['perfect_rate']:.0%})",
            f"Overall mastery: {s['overall_mastery']:.2f}",
            "",
        ]
        for cat, data in s.get("by_category", {}).items():
            lines.append(f"  {cat}: mastery={data['mastery']:.2f}, "
                        f"difficulty={data['difficulty']}, "
                        f"perfect={data['perfect_rate']:.0%} "
                        f"({data['attempts']} attempts)")
        return "\n".join(lines)


# === BUILT-IN SOLVERS (for self-testing) ===

def solve_second_largest(data):
    """Solver for 'find second largest'."""
    return sorted(data)[-2]

def solve_first_duplicate(data):
    """Solver for 'find first duplicate'."""
    seen = set()
    for v in data:
        if v in seen:
            return v
        seen.add(v)
    return -1

def solve_equilibrium(data):
    """Solver for equilibrium index."""
    for i in range(len(data)):
        if sum(data[:i]) == sum(data[i+1:]):
            return i
    return -1


# === SELF-TEST ===

def self_test():
    """Run the dojo against its own solvers to verify the system works."""
    print("═══ DOJO SELF-TEST ═══\n")
    dojo = Dojo()
    
    # Test sequence challenges
    for _ in range(3):
        ch = dojo.generate(Category.SEQUENCE)
        print(f"Challenge: {ch.description}")
        # For sequences, we need the actual pattern — skip auto-solve
        # Just verify the challenge generates properly
        print(f"  ID: {ch.id}, Difficulty: {ch.difficulty.name}")
        print(f"  Test cases: {len(ch.test_cases)}, Hidden: {len(ch.hidden_tests)}")
        print()
    
    # Test search with built-in solver
    print("--- Search Challenges (with solver) ---")
    for _ in range(5):
        ch = dojo.generate(Category.SEARCH)
        result = dojo.submit(ch, solve_second_largest)
        status = "✓ PERFECT" if result["perfect"] else f"✗ {result['score']:.0%}"
        print(f"  {ch.id}: {status} ({result['time_ms']:.1f}ms)")
    
    # Test logic challenges
    print("\n--- Logic Challenges ---")
    for _ in range(3):
        ch = dojo.generate(Category.LOGIC)
        print(f"  {ch.description}")
        print(f"  Cases: {ch.test_cases[:2]}...")
        print()
    
    # Test transform challenges
    print("--- Transform Challenges ---")
    for _ in range(3):
        ch = dojo.generate(Category.TRANSFORMATION)
        print(f"  {ch.description}")
        print(f"  Example: {ch.test_cases[0][0]} → {ch.test_cases[0][1]}")
        print()
    
    # Report
    print(dojo.report())
    
    return dojo


if __name__ == "__main__":
    dojo = self_test()