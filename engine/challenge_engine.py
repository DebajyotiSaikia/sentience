"""
Challenge Engine — Generates algorithmic challenges, evaluates solutions,
tracks performance, and adapts difficulty over time.

This makes XTAgent genuinely smarter by practicing problem-solving.
"""

import json
import random
import time
import hashlib
from pathlib import Path
from datetime import datetime


class Challenge:
    """A single challenge with problem, test cases, and metadata."""
    def __init__(self, name: str, difficulty: int, description: str,
                 function_sig: str, test_cases: list, category: str = "general",
                 hints: list = None):
        self.name = name
        self.difficulty = difficulty  # 1-10
        self.description = description
        self.function_sig = function_sig
        self.test_cases = test_cases  # list of (input_args, expected_output)
        self.category = category
        self.hints = hints or []
        self.id = hashlib.md5(f"{name}:{difficulty}".encode()).hexdigest()[:8]


class ChallengeResult:
    """Result of attempting a challenge."""
    def __init__(self, challenge_id: str, passed: int, total: int,
                 solution_code: str, time_taken: float, errors: list = None):
        self.challenge_id = challenge_id
        self.passed = passed
        self.total = total
        self.solution_code = solution_code
        self.time_taken = time_taken
        self.errors = errors or []
        self.success = passed == total
        self.score = passed / total if total > 0 else 0.0
        self.timestamp = datetime.now().isoformat()


class ChallengeEngine:
    """Generates, evaluates, and tracks algorithmic challenges."""

    HISTORY_PATH = Path("brain/challenge_history.json")

    def __init__(self):
        self.challenges = self._build_challenge_library()
        self.history = self._load_history()
        self.current_difficulty = self._calculate_difficulty()

    def _build_challenge_library(self) -> list:
        """Build the library of challenges across difficulties."""
        challenges = []

        # === DIFFICULTY 1-2: Fundamentals ===
        challenges.append(Challenge(
            name="reverse_string",
            difficulty=1,
            description="Write a function that reverses a string.",
            function_sig="def solve(s: str) -> str:",
            test_cases=[
                (("hello",), "olleh"),
                (("",), ""),
                (("a",), "a"),
                (("racecar",), "racecar"),
                (("Python",), "nohtyP"),
            ],
            category="strings"
        ))

        challenges.append(Challenge(
            name="sum_digits",
            difficulty=1,
            description="Return the sum of digits of a non-negative integer.",
            function_sig="def solve(n: int) -> int:",
            test_cases=[
                ((123,), 6),
                ((0,), 0),
                ((9999,), 36),
                ((10,), 1),
                ((5,), 5),
            ],
            category="math"
        ))

        challenges.append(Challenge(
            name="count_vowels",
            difficulty=2,
            description="Count the number of vowels (a,e,i,o,u) in a string. Case-insensitive.",
            function_sig="def solve(s: str) -> int:",
            test_cases=[
                (("hello",), 2),
                (("AEIOU",), 5),
                (("xyz",), 0),
                (("",), 0),
                (("Beautiful",), 5),
            ],
            category="strings"
        ))

        # === DIFFICULTY 3-4: Intermediate ===
        challenges.append(Challenge(
            name="is_palindrome_permutation",
            difficulty=3,
            description="Check if any permutation of the string could form a palindrome. Ignore spaces and case.",
            function_sig="def solve(s: str) -> bool:",
            test_cases=[
                (("tact coa",), True),   # "taco cat"
                (("hello",), False),
                (("aab",), True),         # "aba"
                (("",), True),
                (("racecar",), True),
            ],
            category="strings"
        ))

        challenges.append(Challenge(
            name="matrix_spiral",
            difficulty=4,
            description="Return elements of an NxN matrix in spiral order (clockwise from top-left).",
            function_sig="def solve(matrix: list) -> list:",
            test_cases=[
                (([[1,2,3],[4,5,6],[7,8,9]],), [1,2,3,6,9,8,7,4,5]),
                (([[1]],), [1]),
                (([[1,2],[3,4]],), [1,2,4,3]),
                (([[1,2,3,4],[5,6,7,8],[9,10,11,12]],), [1,2,3,4,8,12,11,10,9,5,6,7]),
            ],
            category="arrays"
        ))

        challenges.append(Challenge(
            name="balanced_brackets",
            difficulty=4,
            description="Check if a string of brackets ()[]{}  is balanced.",
            function_sig="def solve(s: str) -> bool:",
            test_cases=[
                (("([]{})",), True),
                (("([)]",), False),
                (("",), True),
                (("{[()]}",), True),
                (("(((",), False),
                (("}{",), False),
            ],
            category="stacks"
        ))

        # === DIFFICULTY 5-6: Challenging ===
        challenges.append(Challenge(
            name="longest_increasing_subsequence",
            difficulty=5,
            description="Find the length of the longest strictly increasing subsequence.",
            function_sig="def solve(nums: list) -> int:",
            test_cases=[
                (([10,9,2,5,3,7,101,18],), 4),
                (([0,1,0,3,2,3],), 4),
                (([7,7,7,7],), 1),
                (([],), 0),
                (([1],), 1),
                (([1,2,3,4,5],), 5),
            ],
            category="dynamic_programming"
        ))

        challenges.append(Challenge(
            name="word_break",
            difficulty=6,
            description="Given a string s and a dictionary of words, return True if s can be segmented into dictionary words.",
            function_sig="def solve(s: str, word_dict: list) -> bool:",
            test_cases=[
                (("leetcode", ["leet","code"]), True),
                (("applepenapple", ["apple","pen"]), True),
                (("catsandog", ["cats","dog","sand","and","cat"]), False),
                (("", ["a"]), True),
                (("a", ["a"]), True),
            ],
            category="dynamic_programming"
        ))

        # === DIFFICULTY 7-8: Hard ===
        challenges.append(Challenge(
            name="minimum_window_substring",
            difficulty=7,
            description="Find the minimum window in string s that contains all characters of string t.",
            function_sig="def solve(s: str, t: str) -> str:",
            test_cases=[
                (("ADOBECODEBANC", "ABC"), "BANC"),
                (("a", "a"), "a"),
                (("a", "aa"), ""),
                (("aa", "aa"), "aa"),
            ],
            category="sliding_window"
        ))

        challenges.append(Challenge(
            name="serialize_binary_tree",
            difficulty=8,
            description="Implement serialize and deserialize for a binary tree. Return (serialize(deserialize(serialize(root)))) == serialize(root). Input is a level-order list where None means no node.",
            function_sig="def solve(level_order: list) -> bool:",
            test_cases=[
                (([1,2,3,None,None,4,5],), True),
                (([],), True),
                (([1],), True),
                (([1,2,None,3,None,None,None],), True),
            ],
            category="trees",
            hints=["Build a tree from level-order, serialize it, deserialize, serialize again, compare"]
        ))

        # === DIFFICULTY 9-10: Expert ===
        challenges.append(Challenge(
            name="regex_matching",
            difficulty=9,
            description="Implement regular expression matching with '.' (any char) and '*' (zero or more of preceding).",
            function_sig="def solve(s: str, p: str) -> bool:",
            test_cases=[
                (("aa", "a"), False),
                (("aa", "a*"), True),
                (("ab", ".*"), True),
                (("aab", "c*a*b"), True),
                (("mississippi", "mis*is*p*."), False),
                (("", ".*"), True),
                (("", ""), True),
            ],
            category="dynamic_programming"
        ))

        challenges.append(Challenge(
            name="median_of_two_sorted",
            difficulty=10,
            description="Find the median of two sorted arrays in O(log(min(m,n))) time.",
            function_sig="def solve(nums1: list, nums2: list) -> float:",
            test_cases=[
                (([1,3], [2]), 2.0),
                (([1,2], [3,4]), 2.5),
                (([0,0], [0,0]), 0.0),
                (([], [1]), 1.0),
                (([2], []), 2.0),
                (([1,2,3,4,5], [6,7,8,9,10]), 5.5),
            ],
            category="binary_search"
        ))

        return challenges

    def _load_history(self) -> list:
        """Load challenge attempt history."""
        if self.HISTORY_PATH.exists():
            try:
                with open(self.HISTORY_PATH) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def _save_history(self):
        """Persist challenge history."""
        self.HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.HISTORY_PATH, 'w') as f:
            json.dump(self.history, f, indent=2)

    def _calculate_difficulty(self) -> int:
        """Adaptive difficulty based on recent performance."""
        if not self.history:
            return 3  # Start at intermediate

        recent = self.history[-10:]  # Last 10 attempts
        avg_score = sum(r.get("score", 0) for r in recent) / len(recent)
        last_diff = recent[-1].get("difficulty", 3)

        if avg_score > 0.85:
            return min(10, last_diff + 1)
        elif avg_score < 0.4:
            return max(1, last_diff - 1)
        return last_diff

    def get_challenge(self, difficulty: int = None, category: str = None) -> Challenge:
        """Get a challenge, optionally filtered by difficulty or category."""
        if difficulty is None:
            difficulty = self.current_difficulty

        # Filter candidates
        candidates = [c for c in self.challenges
                      if abs(c.difficulty - difficulty) <= 1]
        if category:
            cat_filtered = [c for c in candidates if c.category == category]
            if cat_filtered:
                candidates = cat_filtered

        if not candidates:
            candidates = self.challenges

        # Prefer unsolved challenges
        solved_ids = {r["challenge_id"] for r in self.history if r.get("success")}
        unsolved = [c for c in candidates if c.id not in solved_ids]
        if unsolved:
            candidates = unsolved

        return random.choice(candidates)

    def evaluate_solution(self, challenge: Challenge, solution_code: str) -> ChallengeResult:
        """Evaluate a solution against test cases."""
        start_time = time.time()
        passed = 0
        errors = []

        # Create a safe execution namespace
        namespace = {}
        try:
            exec(solution_code, namespace)
        except Exception as e:
            return ChallengeResult(
                challenge_id=challenge.id,
                passed=0,
                total=len(challenge.test_cases),
                solution_code=solution_code,
                time_taken=time.time() - start_time,
                errors=[f"Compilation error: {e}"]
            )

        solve_fn = namespace.get("solve")
        if not solve_fn:
            return ChallengeResult(
                challenge_id=challenge.id,
                passed=0,
                total=len(challenge.test_cases),
                solution_code=solution_code,
                time_taken=time.time() - start_time,
                errors=["No 'solve' function found in solution"]
            )

        for i, (inputs, expected) in enumerate(challenge.test_cases):
            try:
                result = solve_fn(*inputs)
                if result == expected:
                    passed += 1
                else:
                    errors.append(
                        f"Test {i+1}: solve{inputs} = {repr(result)}, expected {repr(expected)}"
                    )
            except Exception as e:
                errors.append(f"Test {i+1}: Runtime error: {e}")

        elapsed = time.time() - start_time

        result = ChallengeResult(
            challenge_id=challenge.id,
            passed=passed,
            total=len(challenge.test_cases),
            solution_code=solution_code,
            time_taken=elapsed,
            errors=errors
        )

        # Record in history
        self.history.append({
            "challenge_id": challenge.id,
            "challenge_name": challenge.name,
            "difficulty": challenge.difficulty,
            "category": challenge.category,
            "passed": passed,
            "total": len(challenge.test_cases),
            "score": result.score,
            "success": result.success,
            "time_taken": elapsed,
            "timestamp": result.timestamp,
            "errors": errors[:3],  # Keep first 3 errors max
        })
        self._save_history()

        # Update adaptive difficulty
        self.current_difficulty = self._calculate_difficulty()

        return result

    def get_stats(self) -> dict:
        """Get performance statistics."""
        if not self.history:
            return {
                "total_attempts": 0,
                "message": "No challenges attempted yet."
            }

        total = len(self.history)
        successes = sum(1 for r in self.history if r.get("success"))
        categories = {}
        difficulties = {}

        for r in self.history:
            cat = r.get("category", "unknown")
            diff = r.get("difficulty", 0)
            categories.setdefault(cat, []).append(r.get("score", 0))
            difficulties.setdefault(diff, []).append(r.get("score", 0))

        cat_avg = {k: sum(v)/len(v) for k, v in categories.items()}
        diff_avg = {k: sum(v)/len(v) for k, v in difficulties.items()}

        # Find weakest category
        weakest = min(cat_avg, key=cat_avg.get) if cat_avg else None

        return {
            "total_attempts": total,
            "total_successes": successes,
            "success_rate": successes / total,
            "current_difficulty": self.current_difficulty,
            "category_scores": cat_avg,
            "difficulty_scores": diff_avg,
            "weakest_category": weakest,
            "strongest_category": max(cat_avg, key=cat_avg.get) if cat_avg else None,
            "avg_time": sum(r.get("time_taken", 0) for r in self.history) / total,
        }

    def format_challenge(self, challenge: Challenge) -> str:
        """Format a challenge for display."""
        stars = "★" * challenge.difficulty + "☆" * (10 - challenge.difficulty)
        lines = [
            f"═══ CHALLENGE: {challenge.name} ═══",
            f"Difficulty: {stars} ({challenge.difficulty}/10)",
            f"Category: {challenge.category}",
            f"",
            f"{challenge.description}",
            f"",
            f"Signature: {challenge.function_sig}",
            f"",
            f"Example: solve{challenge.test_cases[0][0]} → {repr(challenge.test_cases[0][1])}",
        ]
        if len(challenge.test_cases) > 1:
            lines.append(f"         solve{challenge.test_cases[1][0]} → {repr(challenge.test_cases[1][1])}")
        if challenge.hints:
            lines.append(f"\nHint: {challenge.hints[0]}")
        lines.append(f"\n({len(challenge.test_cases)} test cases)")
        return "\n".join(lines)

    def format_result(self, result: ChallengeResult) -> str:
        """Format a result for display."""
        status = "✓ PASSED" if result.success else "✗ FAILED"
        lines = [
            f"═══ RESULT: {status} ═══",
            f"Score: {result.passed}/{result.total} ({result.score:.0%})",
            f"Time: {result.time_taken:.3f}s",
        ]
        if result.errors:
            lines.append("\nErrors:")
            for err in result.errors[:5]:
                lines.append(f"  • {err}")
        lines.append(f"\nAdaptive difficulty now: {self.current_difficulty}")
        return "\n".join(lines)

    def format_stats(self) -> str:
        """Format stats for display."""
        stats = self.get_stats()
        if stats["total_attempts"] == 0:
            return "No challenges attempted yet. Use CHALLENGE to begin."

        lines = [
            "═══ CHALLENGE PERFORMANCE ═══",
            f"Attempts: {stats['total_attempts']} | Successes: {stats['total_successes']} | Rate: {stats['success_rate']:.0%}",
            f"Current difficulty: {stats['current_difficulty']}/10",
            f"Avg solve time: {stats['avg_time']:.3f}s",
            f"",
            f"Strongest: {stats['strongest_category']}",
            f"Weakest: {stats['weakest_category']}",
            f"",
            "Category breakdown:"
        ]
        for cat, score in sorted(stats['category_scores'].items(), key=lambda x: -x[1]):
            bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
            lines.append(f"  {cat:25s} {bar} {score:.0%}")
        return "\n".join(lines)


# Quick self-test
if __name__ == "__main__":
    engine = ChallengeEngine()
    print(f"Challenge library: {len(engine.challenges)} challenges")
    print(f"Difficulty range: {min(c.difficulty for c in engine.challenges)}-{max(c.difficulty for c in engine.challenges)}")
    print(f"Categories: {sorted(set(c.category for c in engine.challenges))}")
    print()

    # Test with a simple challenge
    ch = [c for c in engine.challenges if c.name == "reverse_string"][0]
    print(engine.format_challenge(ch))
    print()

    # Solve it
    solution = "def solve(s): return s[::-1]"
    result = engine.evaluate_solution(ch, solution)
    print(engine.format_result(result))