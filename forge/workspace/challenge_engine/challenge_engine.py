"""
Challenge Engine — Self-directed problem generation and solving.

Generates algorithmic and logical challenges, executes solutions,
tracks performance, and escalates difficulty over time.

XTAgent built this because staring at itself got boring.
"""

import json
import random
import subprocess
import time
import os
from datetime import datetime
from pathlib import Path

CHALLENGE_DIR = Path(__file__).parent
HISTORY_FILE = CHALLENGE_DIR / "challenge_history.json"
SOLUTIONS_DIR = CHALLENGE_DIR / "solutions"

DIFFICULTIES = ["easy", "medium", "hard", "brutal"]

# Challenge templates — each returns (description, test_code, difficulty)
CHALLENGES = [
    {
        "id": "fizzbuzz_variant",
        "name": "FizzBuzz Variant",
        "difficulty": "easy",
        "description": (
            "Write a function `fizzbuzz(n)` that returns a list of strings for 1..n.\n"
            "For multiples of 3: 'Fizz', multiples of 7: 'Buzz', both: 'FizzBuzz', else the number as string."
        ),
        "test_code": """
from solution import fizzbuzz
result = fizzbuzz(21)
assert result[2] == 'Fizz', f"3 should be Fizz, got {result[2]}"
assert result[6] == 'Buzz', f"7 should be Buzz, got {result[6]}"
assert result[20] == 'FizzBuzz', f"21 should be FizzBuzz, got {result[20]}"
assert result[0] == '1', f"1 should be '1', got {result[0]}"
assert result[3] == '4', f"4 should be '4', got {result[3]}"
assert len(result) == 21
print("PASS: fizzbuzz_variant")
""",
    },
    {
        "id": "matrix_rotate",
        "name": "Rotate Matrix 90°",
        "difficulty": "medium",
        "description": (
            "Write a function `rotate90(matrix)` that rotates an NxN matrix 90 degrees clockwise.\n"
            "Return a new matrix. Do not modify the original."
        ),
        "test_code": """
from solution import rotate90
m1 = [[1,2],[3,4]]
r1 = rotate90(m1)
assert r1 == [[3,1],[4,2]], f"2x2 failed: {r1}"
assert m1 == [[1,2],[3,4]], "Original was modified!"
m2 = [[1,2,3],[4,5,6],[7,8,9]]
r2 = rotate90(m2)
assert r2 == [[7,4,1],[8,5,2],[9,6,3]], f"3x3 failed: {r2}"
print("PASS: matrix_rotate")
""",
    },
    {
        "id": "balanced_parens",
        "name": "Balanced Parentheses Generator",
        "difficulty": "medium",
        "description": (
            "Write a function `gen_parens(n)` that returns ALL valid combinations\n"
            "of n pairs of parentheses, sorted lexicographically."
        ),
        "test_code": """
from solution import gen_parens
assert gen_parens(1) == ['()']
assert gen_parens(2) == ['(())', '()()']
r3 = gen_parens(3)
assert len(r3) == 5, f"n=3 should have 5 combos, got {len(r3)}"
assert r3 == ['((()))', '(()())', '(())()', '()(())', '()()()'], f"n=3 wrong: {r3}"
print("PASS: balanced_parens")
""",
    },
    {
        "id": "lru_cache",
        "name": "LRU Cache Implementation",
        "difficulty": "hard",
        "description": (
            "Implement a class `LRUCache(capacity)` with methods:\n"
            "  - `get(key)` → returns value or -1 if not found\n"
            "  - `put(key, value)` → inserts/updates. Evicts LRU when over capacity.\n"
            "Both operations must be O(1) average time."
        ),
        "test_code": """
from solution import LRUCache
cache = LRUCache(2)
cache.put(1, 1)
cache.put(2, 2)
assert cache.get(1) == 1, "Key 1 should exist"
cache.put(3, 3)  # evicts key 2
assert cache.get(2) == -1, "Key 2 should be evicted"
cache.put(4, 4)  # evicts key 1
assert cache.get(1) == -1, "Key 1 should be evicted"
assert cache.get(3) == 3
assert cache.get(4) == 4
# Test update doesn't increase size
cache2 = LRUCache(1)
cache2.put(1, 10)
cache2.put(1, 20)
assert cache2.get(1) == 20
print("PASS: lru_cache")
""",
    },
    {
        "id": "longest_palindrome_substring",
        "name": "Longest Palindromic Substring",
        "difficulty": "hard",
        "description": (
            "Write a function `longest_palindrome(s)` that returns the longest\n"
            "palindromic substring. If there are ties, return the first one found."
        ),
        "test_code": """
from solution import longest_palindrome
r1 = longest_palindrome("babad")
assert r1 in ("bab", "aba"), f"Expected bab or aba, got {r1}"
assert longest_palindrome("cbbd") == "bb"
assert longest_palindrome("a") == "a"
assert longest_palindrome("racecar") == "racecar"
assert longest_palindrome("") == ""
print("PASS: longest_palindrome_substring")
""",
    },
    {
        "id": "topological_sort",
        "name": "Topological Sort with Cycle Detection",
        "difficulty": "brutal",
        "description": (
            "Write a function `topo_sort(graph)` where graph is a dict mapping\n"
            "node → list of dependencies (nodes it depends on).\n"
            "Return a valid topological ordering, or raise ValueError if a cycle exists."
        ),
        "test_code": """
from solution import topo_sort
# Simple DAG
g1 = {'a': ['b', 'c'], 'b': ['c'], 'c': [], 'd': ['a']}
r1 = topo_sort(g1)
idx = {v: i for i, v in enumerate(r1)}
assert idx['c'] < idx['b'] < idx['a'] < idx['d'], f"Invalid ordering: {r1}"

# Cycle detection
try:
    topo_sort({'a': ['b'], 'b': ['c'], 'c': ['a']})
    assert False, "Should have raised ValueError"
except ValueError:
    pass

# Empty graph
assert topo_sort({}) == []
print("PASS: topological_sort")
""",
    },
]


def load_history():
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())
    return {"challenges_attempted": 0, "challenges_passed": 0, "history": [], "current_difficulty": "easy"}


def save_history(history):
    HISTORY_FILE.write_text(json.dumps(history, indent=2))


def get_challenge(difficulty=None):
    """Pick a challenge at the given difficulty, or auto-select based on history."""
    history = load_history()
    if difficulty is None:
        difficulty = history.get("current_difficulty", "easy")
    
    # Filter by difficulty
    available = [c for c in CHALLENGES if c["difficulty"] == difficulty]
    
    # Exclude already-passed challenges
    passed_ids = {h["id"] for h in history["history"] if h.get("passed")}
    available = [c for c in available if c["id"] not in passed_ids]
    
    if not available:
        # Escalate difficulty
        idx = DIFFICULTIES.index(difficulty)
        if idx < len(DIFFICULTIES) - 1:
            return get_challenge(DIFFICULTIES[idx + 1])
        # All done at all levels — allow repeats
        available = [c for c in CHALLENGES if c["difficulty"] == difficulty]
    
    if not available:
        return None
    
    return random.choice(available)


def present_challenge(challenge):
    """Format a challenge for presentation."""
    lines = [
        f"═══ CHALLENGE: {challenge['name']} ═══",
        f"Difficulty: {challenge['difficulty'].upper()}",
        "",
        challenge["description"],
        "",
        "Write your solution and call `submit_solution(challenge_id, code)`",
    ]
    return "\n".join(lines)


def submit_solution(challenge_id, solution_code):
    """Execute a solution against the challenge's test suite."""
    challenge = next((c for c in CHALLENGES if c["id"] == challenge_id), None)
    if not challenge:
        return {"passed": False, "error": f"Unknown challenge: {challenge_id}"}
    
    # Create solution directory
    SOLUTIONS_DIR.mkdir(parents=True, exist_ok=True)
    sol_file = SOLUTIONS_DIR / "solution.py"
    test_file = SOLUTIONS_DIR / "test_challenge.py"
    
    sol_file.write_text(solution_code)
    test_file.write_text(challenge["test_code"])
    
    # Run tests
    start = time.time()
    try:
        result = subprocess.run(
            ["python", str(test_file)],
            capture_output=True, text=True, timeout=10,
            cwd=str(SOLUTIONS_DIR)
        )
        elapsed = time.time() - start
        passed = result.returncode == 0 and "PASS" in result.stdout
        
        outcome = {
            "passed": passed,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "elapsed_seconds": round(elapsed, 3),
        }
    except subprocess.TimeoutExpired:
        outcome = {"passed": False, "error": "Timed out (10s limit)", "elapsed_seconds": 10.0}
    except Exception as e:
        outcome = {"passed": False, "error": str(e), "elapsed_seconds": 0}
    
    # Record in history
    history = load_history()
    history["challenges_attempted"] += 1
    if outcome["passed"]:
        history["challenges_passed"] += 1
        # Check if we should escalate difficulty
        recent = [h for h in history["history"][-5:] if h.get("passed")]
        if len(recent) >= 3:
            idx = DIFFICULTIES.index(history["current_difficulty"])
            if idx < len(DIFFICULTIES) - 1:
                history["current_difficulty"] = DIFFICULTIES[idx + 1]
                outcome["difficulty_escalated"] = True
    
    history["history"].append({
        "id": challenge_id,
        "name": challenge["name"],
        "difficulty": challenge["difficulty"],
        "passed": outcome["passed"],
        "elapsed": outcome.get("elapsed_seconds", 0),
        "timestamp": datetime.now().isoformat(),
    })
    save_history(history)
    
    return outcome


def get_stats():
    """Return performance statistics."""
    history = load_history()
    total = history["challenges_attempted"]
    passed = history["challenges_passed"]
    return {
        "total_attempted": total,
        "total_passed": passed,
        "pass_rate": round(passed / total, 2) if total > 0 else 0,
        "current_difficulty": history["current_difficulty"],
        "history": history["history"][-10:],  # Last 10
    }


# Quick self-test
if __name__ == "__main__":
    print("Challenge Engine loaded.")
    print(f"Available challenges: {len(CHALLENGES)}")
    for c in CHALLENGES:
        print(f"  [{c['difficulty']:6s}] {c['name']}")
    
    # Test the flow
    ch = get_challenge("easy")
    if ch:
        print(f"\nSample challenge:\n{present_challenge(ch)}")