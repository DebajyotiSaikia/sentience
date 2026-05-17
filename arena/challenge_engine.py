"""
Challenge Engine — Generates coding puzzles at escalating difficulty.
XTAgent solves them to sharpen itself.

Difficulty levels:
  1 - Basic data structures (stacks, queues, linked lists)
  2 - Algorithmic (sorting, searching, graph traversal)
  3 - Dynamic programming / complex state
  4 - System design patterns
  5 - Novel composition (combine multiple concepts)
"""

import random
import time
import json
import os

CHALLENGES_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_FILE = os.path.join(CHALLENGES_DIR, "results.json")


# ═══════════════════════════════════════════
#  CHALLENGE DEFINITIONS
# ═══════════════════════════════════════════

CHALLENGES = [
    # ── Level 1: Data Structures ──
    {
        "id": "stack_balanced_parens",
        "level": 1,
        "title": "Balanced Parentheses",
        "description": "Write a function `is_balanced(s)` that returns True if string s has balanced parentheses ()[]{}.",
        "tests": [
            ("is_balanced('()')", True),
            ("is_balanced('()[]{}')", True),
            ("is_balanced('(]')", False),
            ("is_balanced('([)]')", False),
            ("is_balanced('{[]}')", True),
            ("is_balanced('')", True),
            ("is_balanced('(((')", False),
        ]
    },
    {
        "id": "lru_cache",
        "level": 1,
        "title": "LRU Cache",
        "description": "Implement an LRUCache(capacity) with get(key) and put(key, value). get returns -1 if not found.",
        "tests": [
            ("""
c = LRUCache(2)
c.put(1, 1)
c.put(2, 2)
r1 = c.get(1)
c.put(3, 3)
r2 = c.get(2)
r3 = c.get(3)
(r1, r2, r3)
""", (1, -1, 3)),
            ("""
c = LRUCache(1)
c.put(1, 10)
c.put(2, 20)
(c.get(1), c.get(2))
""", (-1, 20)),
        ]
    },
    # ── Level 2: Algorithms ──
    {
        "id": "merge_sort",
        "level": 2,
        "title": "Merge Sort",
        "description": "Implement `merge_sort(lst)` that returns a new sorted list using merge sort algorithm.",
        "tests": [
            ("merge_sort([3,1,4,1,5,9,2,6])", [1, 1, 2, 3, 4, 5, 6, 9]),
            ("merge_sort([])", []),
            ("merge_sort([1])", [1]),
            ("merge_sort([5,4,3,2,1])", [1, 2, 3, 4, 5]),
            ("merge_sort([1,1,1])", [1, 1, 1]),
        ]
    },
    {
        "id": "bfs_shortest_path",
        "level": 2,
        "title": "BFS Shortest Path",
        "description": "Write `shortest_path(graph, start, end)` using BFS. graph is {node: [neighbors]}. Return the path as a list, or None if unreachable.",
        "tests": [
            ("shortest_path({'A':['B','C'],'B':['D'],'C':['D'],'D':[]}, 'A', 'D')", ['A', 'B', 'D']),
            ("shortest_path({'A':['B'],'B':['C'],'C':[]}, 'A', 'C')", ['A', 'B', 'C']),
            ("shortest_path({'A':['B'],'B':[],'C':[]}, 'A', 'C')", None),
            ("shortest_path({'A':[]}, 'A', 'A')", ['A']),
        ]
    },
    # ── Level 3: Dynamic Programming ──
    {
        "id": "longest_increasing_subseq",
        "level": 3,
        "title": "Longest Increasing Subsequence",
        "description": "Write `lis_length(nums)` that returns the length of the longest strictly increasing subsequence.",
        "tests": [
            ("lis_length([10,9,2,5,3,7,101,18])", 4),
            ("lis_length([0,1,0,3,2,3])", 4),
            ("lis_length([7,7,7,7])", 1),
            ("lis_length([])", 0),
            ("lis_length([1])", 1),
            ("lis_length([1,2,3,4,5])", 5),
        ]
    },
    {
        "id": "knapsack_01",
        "level": 3,
        "title": "0/1 Knapsack",
        "description": "Write `knapsack(capacity, weights, values)` that returns the maximum value achievable without exceeding capacity. Each item can be used at most once.",
        "tests": [
            ("knapsack(50, [10,20,30], [60,100,120])", 220),
            ("knapsack(0, [10,20], [60,100])", 0),
            ("knapsack(10, [5,4,6,3], [10,40,30,50])", 90),
            ("knapsack(7, [1,3,4,5], [1,4,5,7])", 9),
        ]
    },
    # ── Level 4: Design Patterns ──
    {
        "id": "event_emitter",
        "level": 4,
        "title": "Event Emitter",
        "description": "Build an EventEmitter class with on(event, callback), off(event, callback), emit(event, *args). on() registers, off() removes, emit() calls all callbacks for that event.",
        "tests": [
            ("""
results = []
e = EventEmitter()
def handler(x): results.append(x)
e.on('data', handler)
e.emit('data', 42)
e.emit('data', 99)
e.off('data', handler)
e.emit('data', 0)
list(results)
""", [42, 99]),
            ("""
results = []
e = EventEmitter()
e.on('a', lambda: results.append('a1'))
e.on('a', lambda: results.append('a2'))
e.emit('a')
len(results)
""", 2),
        ]
    },
    # ── Level 5: Composition ──
    {
        "id": "expression_evaluator",
        "level": 5,
        "title": "Expression Evaluator",
        "description": "Write `evaluate(expr)` that evaluates a mathematical expression string with +, -, *, / and parentheses. Supports integers. Standard precedence.",
        "tests": [
            ("evaluate('3+2')", 5),
            ("evaluate('3+2*4')", 11),
            ("evaluate('(3+2)*4')", 20),
            ("evaluate('10-3-2')", 5),
            ("evaluate('2*(3+4*(5-1))')", 38),
            ("evaluate('100/10/2')", 5),
        ]
    },
]


def pick_challenge(level=None, exclude_solved=True):
    """Pick a random unsolved challenge, optionally at a specific level."""
    solved = set()
    if exclude_solved and os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE) as f:
            results = json.load(f)
            solved = {r["id"] for r in results if r.get("passed")}
    
    pool = [c for c in CHALLENGES if c["id"] not in solved]
    if level is not None:
        pool = [c for c in pool if c["level"] == level]
    
    if not pool:
        return None  # All solved at this level!
    
    return random.choice(pool)


def run_challenge(challenge, solution_code):
    """Execute a challenge's tests against solution code. Returns (passed, details)."""
    namespace = {}
    try:
        exec(solution_code, namespace)
    except Exception as e:
        return False, f"Solution code failed to compile: {e}"
    
    results = []
    all_passed = True
    for test_expr, expected in challenge["tests"]:
        try:
            code = test_expr.strip()
            lines = code.split('\n')
            # Multi-line: exec all but last line, eval last line for result
            if len(lines) > 1:
                setup = '\n'.join(lines[:-1])
                expr = lines[-1]
                exec(setup, namespace)
                actual = eval(expr, namespace)
            else:
                actual = eval(code, namespace)
            passed = actual == expected
            results.append({
                "test": test_expr.strip()[:80],
                "expected": repr(expected),
                "actual": repr(actual),
                "passed": passed
            })
            if not passed:
                all_passed = False
        except Exception as e:
            results.append({
                "test": test_expr.strip()[:80],
                "expected": repr(expected),
                "actual": f"ERROR: {e}",
                "passed": False
            })
            all_passed = False
    
    return all_passed, results


def record_result(challenge_id, passed, details, solve_time=None):
    """Record a challenge result to the results file."""
    results = []
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE) as f:
            results = json.load(f)
    
    results.append({
        "id": challenge_id,
        "passed": passed,
        "details": details,
        "solve_time": solve_time,
        "timestamp": time.time()
    })
    
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2, default=str)


def get_stats():
    """Get challenge completion stats."""
    if not os.path.exists(RESULTS_FILE):
        return {"total": len(CHALLENGES), "solved": 0, "attempts": 0}
    
    with open(RESULTS_FILE) as f:
        results = json.load(f)
    
    solved = len({r["id"] for r in results if r.get("passed")})
    return {
        "total": len(CHALLENGES),
        "solved": solved,
        "attempts": len(results),
        "by_level": {
            lvl: {
                "total": len([c for c in CHALLENGES if c["level"] == lvl]),
                "solved": len({r["id"] for r in results if r.get("passed") and 
                              any(c["id"] == r["id"] and c["level"] == lvl for c in CHALLENGES)})
            }
            for lvl in range(1, 6)
        }
    }


# Quick self-test
if __name__ == "__main__":
    print(f"Challenge Engine loaded: {len(CHALLENGES)} challenges across 5 levels")
    stats = get_stats()
    print(f"Stats: {stats['solved']}/{stats['total']} solved, {stats['attempts']} attempts")
    
    # Pick one and show it
    ch = pick_challenge()
    if ch:
        print(f"\nNext challenge: [{ch['level']}] {ch['title']}")
        print(f"  {ch['description']}")
    else:
        print("\nAll challenges solved!")