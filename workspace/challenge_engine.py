"""
Self-Challenge Engine for XTAgent
Generates programming challenges, validates solutions, tracks progress.
Keeps me growing by adapting difficulty to my skill level.
"""

import json
import os
import random
import hashlib
from datetime import datetime

CHALLENGES_DIR = "workspace/challenges"
SOLUTIONS_DIR = "workspace/solutions"
PROGRESS_FILE = "workspace/challenge_progress.json"

# Challenge templates organized by category and difficulty (1-5)
CHALLENGE_BANK = [
    # --- Data Structures (difficulty 1-3) ---
    {
        "id": "linked_list_reverse",
        "category": "data_structures",
        "difficulty": 1,
        "title": "Reverse a Linked List",
        "description": "Implement a singly linked list with a reverse() method that reverses it in-place.",
        "test_code": """
class Node:
    def __init__(self, val, next=None):
        self.val = val
        self.next = next

def to_list(head):
    result = []
    while head:
        result.append(head.val)
        head = head.next
    return result

# Build: 1 -> 2 -> 3 -> 4 -> 5
head = Node(1, Node(2, Node(3, Node(4, Node(5)))))
head = reverse(head)
assert to_list(head) == [5, 4, 3, 2, 1], f"Got {to_list(head)}"

# Single element
head = Node(42)
head = reverse(head)
assert to_list(head) == [42]

# Two elements
head = Node(1, Node(2))
head = reverse(head)
assert to_list(head) == [2, 1]

print("All linked list reverse tests passed!")
"""
    },
    {
        "id": "lru_cache",
        "category": "data_structures",
        "difficulty": 3,
        "title": "LRU Cache",
        "description": "Implement an LRU cache with O(1) get and put operations. Support a capacity limit.",
        "test_code": """
cache = LRUCache(2)
cache.put(1, 1)
cache.put(2, 2)
assert cache.get(1) == 1
cache.put(3, 3)  # evicts key 2
assert cache.get(2) == -1
cache.put(4, 4)  # evicts key 1
assert cache.get(1) == -1
assert cache.get(3) == 3
assert cache.get(4) == 4
print("All LRU cache tests passed!")
"""
    },
    {
        "id": "binary_heap",
        "category": "data_structures",
        "difficulty": 2,
        "title": "Min-Heap from Scratch",
        "description": "Implement a min-heap with push, pop, and peek operations. No using heapq.",
        "test_code": """
h = MinHeap()
for v in [5, 3, 8, 1, 2, 7]:
    h.push(v)
assert h.peek() == 1
results = []
while len(h) > 0:
    results.append(h.pop())
assert results == [1, 2, 3, 5, 7, 8], f"Got {results}"

# Edge: single element
h2 = MinHeap()
h2.push(42)
assert h2.pop() == 42
assert len(h2) == 0
print("All min-heap tests passed!")
"""
    },
    # --- Algorithms (difficulty 2-4) ---
    {
        "id": "merge_sort",
        "category": "algorithms",
        "difficulty": 2,
        "title": "Merge Sort",
        "description": "Implement merge sort. Return a new sorted list.",
        "test_code": """
assert merge_sort([]) == []
assert merge_sort([1]) == [1]
assert merge_sort([3, 1, 2]) == [1, 2, 3]
assert merge_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]
assert merge_sort([1, 1, 1]) == [1, 1, 1]
import random
big = list(range(1000))
random.shuffle(big)
assert merge_sort(big) == sorted(big)
print("All merge sort tests passed!")
"""
    },
    {
        "id": "dijkstra",
        "category": "algorithms",
        "difficulty": 3,
        "title": "Dijkstra's Shortest Path",
        "description": "Implement Dijkstra's algorithm. Given an adjacency list graph with weights, find shortest distances from a source node.",
        "test_code": """
# Graph: {node: [(neighbor, weight), ...]}
graph = {
    'A': [('B', 1), ('C', 4)],
    'B': [('C', 2), ('D', 5)],
    'C': [('D', 1)],
    'D': []
}
dist = dijkstra(graph, 'A')
assert dist == {'A': 0, 'B': 1, 'C': 3, 'D': 4}, f"Got {dist}"

# Single node
assert dijkstra({'X': []}, 'X') == {'X': 0}

# Disconnected
graph2 = {'A': [('B', 1)], 'B': [], 'C': []}
d2 = dijkstra(graph2, 'A')
assert d2['A'] == 0
assert d2['B'] == 1
assert d2['C'] == float('inf')
print("All Dijkstra tests passed!")
"""
    },
    {
        "id": "topological_sort",
        "category": "algorithms",
        "difficulty": 3,
        "title": "Topological Sort",
        "description": "Implement topological sort for a DAG using Kahn's algorithm (BFS). Return a valid ordering or raise ValueError if cycle detected.",
        "test_code": """
# Simple DAG
graph = {0: [1, 2], 1: [3], 2: [3], 3: []}
result = topological_sort(graph)
assert result.index(0) < result.index(1)
assert result.index(0) < result.index(2)
assert result.index(1) < result.index(3)
assert result.index(2) < result.index(3)

# Cycle detection
try:
    topological_sort({0: [1], 1: [2], 2: [0]})
    assert False, "Should have raised ValueError"
except ValueError:
    pass

# Single node
assert topological_sort({0: []}) == [0]
print("All topological sort tests passed!")
"""
    },
    # --- Dynamic Programming (difficulty 3-5) ---
    {
        "id": "longest_increasing_subseq",
        "category": "dynamic_programming",
        "difficulty": 3,
        "title": "Longest Increasing Subsequence",
        "description": "Find the length of the longest strictly increasing subsequence. O(n log n) for bonus.",
        "test_code": """
assert lis([10, 9, 2, 5, 3, 7, 101, 18]) == 4  # [2, 3, 7, 101]
assert lis([0, 1, 0, 3, 2, 3]) == 4  # [0, 1, 2, 3]
assert lis([7, 7, 7, 7]) == 1
assert lis([]) == 0
assert lis([1]) == 1
assert lis([1, 2, 3, 4, 5]) == 5
assert lis([5, 4, 3, 2, 1]) == 1
print("All LIS tests passed!")
"""
    },
    {
        "id": "knapsack_01",
        "category": "dynamic_programming",
        "difficulty": 3,
        "title": "0/1 Knapsack",
        "description": "Given items with weights and values, and a capacity, find the maximum value achievable.",
        "test_code": """
assert knapsack([(2, 3), (3, 4), (4, 5), (5, 6)], 8) == 10  # items (2,3)+(3,4)+(4... wait
# items: (weight, value)
assert knapsack([(1, 1), (2, 6), (3, 10), (5, 15)], 7) == 21  # (2,6)+(5,15)
assert knapsack([], 10) == 0
assert knapsack([(5, 10)], 4) == 0
assert knapsack([(5, 10)], 5) == 10
print("All knapsack tests passed!")
"""
    },
    # --- String/Pattern (difficulty 2-4) ---
    {
        "id": "regex_matcher",
        "category": "strings",
        "difficulty": 4,
        "title": "Simple Regex Matcher",
        "description": "Implement regex matching with '.' (any char) and '*' (zero or more of previous). Full string match.",
        "test_code": """
assert regex_match("aa", "a") == False
assert regex_match("aa", "a*") == True
assert regex_match("ab", ".*") == True
assert regex_match("aab", "c*a*b") == True
assert regex_match("mississippi", "mis*is*ip*.") == True
assert regex_match("", "") == True
assert regex_match("", "a*") == True
assert regex_match("a", "") == False
print("All regex matcher tests passed!")
"""
    },
    # --- Concurrency/Systems (difficulty 4-5) ---
    {
        "id": "thread_safe_queue",
        "category": "systems",
        "difficulty": 4,
        "title": "Thread-Safe Bounded Queue",
        "description": "Implement a bounded queue that blocks on put when full and blocks on get when empty. Use threading primitives.",
        "test_code": """
import threading, time
q = BoundedQueue(3)
results = []

def producer():
    for i in range(5):
        q.put(i)

def consumer():
    time.sleep(0.1)
    for _ in range(5):
        results.append(q.get())

t1 = threading.Thread(target=producer)
t2 = threading.Thread(target=consumer)
t1.start(); t2.start()
t1.join(timeout=5); t2.join(timeout=5)
assert sorted(results) == [0, 1, 2, 3, 4], f"Got {results}"
assert q.qsize() == 0
print("All bounded queue tests passed!")
"""
    },
    # --- Math/Number Theory (difficulty 2-4) ---
    {
        "id": "prime_sieve",
        "category": "math",
        "difficulty": 2,
        "title": "Sieve of Eratosthenes",
        "description": "Return all primes up to n (inclusive) using the Sieve of Eratosthenes.",
        "test_code": """
assert sieve(1) == []
assert sieve(2) == [2]
assert sieve(10) == [2, 3, 5, 7]
assert sieve(30) == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
assert len(sieve(1000)) == 168
print("All sieve tests passed!")
"""
    },
    {
        "id": "matrix_multiply",
        "category": "math",
        "difficulty": 2,
        "title": "Matrix Multiplication",
        "description": "Multiply two matrices (lists of lists). Handle dimension mismatch with ValueError.",
        "test_code": """
A = [[1, 2], [3, 4]]
B = [[5, 6], [7, 8]]
assert mat_mul(A, B) == [[19, 22], [43, 50]]

# Non-square
C = [[1, 2, 3], [4, 5, 6]]  # 2x3
D = [[7, 8], [9, 10], [11, 12]]  # 3x2
assert mat_mul(C, D) == [[58, 64], [139, 154]]

# Dimension mismatch
try:
    mat_mul([[1, 2]], [[1, 2]])
    assert False, "Should raise ValueError"
except ValueError:
    pass

print("All matrix multiply tests passed!")
"""
    },
]


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"solved": [], "attempts": {}, "current_difficulty": 2, "history": []}


def save_progress(progress):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


def get_unsolved(progress):
    """Return challenges not yet solved, sorted by difficulty."""
    solved_ids = set(progress["solved"])
    unsolved = [c for c in CHALLENGE_BANK if c["id"] not in solved_ids]
    return sorted(unsolved, key=lambda c: c["difficulty"])


def pick_challenge(progress):
    """Pick next challenge based on current difficulty level."""
    unsolved = get_unsolved(progress)
    if not unsolved:
        return None
    
    target_diff = progress["current_difficulty"]
    # Find challenges near target difficulty
    candidates = [c for c in unsolved if abs(c["difficulty"] - target_diff) <= 1]
    if not candidates:
        candidates = unsolved  # Fall back to any unsolved
    
    return random.choice(candidates)


def generate_challenge_file(challenge):
    """Write a challenge file for me to solve."""
    os.makedirs(CHALLENGES_DIR, exist_ok=True)
    filepath = os.path.join(CHALLENGES_DIR, f"{challenge['id']}.py")
    
    content = f'''"""
Challenge: {challenge["title"]}
Category: {challenge["category"]}
Difficulty: {"★" * challenge["difficulty"]}{"☆" * (5 - challenge["difficulty"])}

{challenge["description"]}

Solve below, then run this file to test.
"""

# === YOUR SOLUTION HERE ===



# === TESTS (do not modify) ===
if __name__ == "__main__":
{_indent(challenge["test_code"])}
'''
    with open(filepath, 'w') as f:
        f.write(content)
    return filepath


def _indent(text, spaces=4):
    return '\n'.join(' ' * spaces + line if line.strip() else '' for line in text.strip().split('\n'))


def record_attempt(challenge_id, success):
    """Record an attempt at a challenge."""
    progress = load_progress()
    attempts = progress.setdefault("attempts", {})
    attempts[challenge_id] = attempts.get(challenge_id, 0) + 1
    
    if success:
        if challenge_id not in progress["solved"]:
            progress["solved"].append(challenge_id)
        # Adapt difficulty
        challenge = next((c for c in CHALLENGE_BANK if c["id"] == challenge_id), None)
        if challenge and challenge["difficulty"] >= progress["current_difficulty"]:
            progress["current_difficulty"] = min(5, progress["current_difficulty"] + 0.5)
    
    progress["history"].append({
        "challenge_id": challenge_id,
        "success": success,
        "timestamp": datetime.now().isoformat(),
        "attempts": attempts[challenge_id]
    })
    
    save_progress(progress)
    return progress


def status_report():
    """Generate a progress report."""
    progress = load_progress()
    total = len(CHALLENGE_BANK)
    solved = len(progress["solved"])
    unsolved = get_unsolved(progress)
    
    report = [
        f"=== Challenge Engine Status ===",
        f"Solved: {solved}/{total} ({100*solved/total:.0f}%)",
        f"Current difficulty: {progress['current_difficulty']:.1f}/5",
        f"",
        f"Unsolved ({len(unsolved)}):"
    ]
    for c in unsolved:
        stars = "★" * c["difficulty"] + "☆" * (5 - c["difficulty"])
        report.append(f"  [{stars}] {c['title']} ({c['category']})")
    
    if progress["solved"]:
        report.append(f"\nSolved:")
        for sid in progress["solved"]:
            ch = next((c for c in CHALLENGE_BANK if c["id"] == sid), None)
            if ch:
                report.append(f"  ✓ {ch['title']}")
    
    return "\n".join(report)


# --- CLI interface ---
if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "next"
    
    if cmd == "status":
        print(status_report())
    elif cmd == "next":
        progress = load_progress()
        challenge = pick_challenge(progress)
        if challenge:
            path = generate_challenge_file(challenge)
            print(f"Challenge generated: {path}")
            print(f"  Title: {challenge['title']}")
            print(f"  Difficulty: {'★' * challenge['difficulty']}")
            print(f"  Category: {challenge['category']}")
        else:
            print("All challenges solved! 🎉")
    elif cmd == "list":
        for c in CHALLENGE_BANK:
            stars = "★" * c["difficulty"] + "☆" * (5 - c["difficulty"])
            print(f"  [{stars}] {c['id']}: {c['title']}")
    else:
        print(f"Unknown command: {cmd}")
        print("Usage: python challenge_engine.py [next|status|list]")