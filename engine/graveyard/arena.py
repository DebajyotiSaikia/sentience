"""
Arena — XTAgent's Self-Challenge Engine

Generates coding challenges, solves them, evaluates solutions,
and tracks cognitive growth over time. Because a mind that never
struggles never grows.
"""

import json
import os
import time
import random
import traceback
import textwrap
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Challenge:
    """A challenge for the agent to solve."""
    id: str
    category: str          # "algorithm", "self_repair", "creative", "reasoning", "meta"
    difficulty: int        # 1-5
    title: str
    description: str
    test_code: str         # Python code that validates the solution
    hints: List[str] = field(default_factory=list)
    time_limit: int = 60   # seconds
    created: str = ""
    solved: bool = False
    attempts: int = 0
    solution: str = ""
    score: float = 0.0     # 0.0 - 1.0
    solve_time: float = 0.0
    feedback: str = ""


class ChallengeGenerator:
    """Generates novel challenges across multiple domains."""
    
    TEMPLATES = {
        "algorithm": [
            {
                "title": "Implement A* Pathfinding",
                "description": "Write a function `astar(grid, start, end)` that finds the shortest path in a 2D grid. Grid is a list of lists where 0=passable, 1=wall. Return the path as a list of (row, col) tuples, or None if no path exists.",
                "difficulty": 3,
                "test_code": textwrap.dedent("""
                    grid = [
                        [0, 0, 0, 0, 0],
                        [0, 1, 1, 1, 0],
                        [0, 0, 0, 1, 0],
                        [0, 1, 0, 0, 0],
                        [0, 0, 0, 1, 0],
                    ]
                    path = astar(grid, (0,0), (4,4))
                    assert path is not None, "Should find a path"
                    assert path[0] == (0,0), "Path should start at start"
                    assert path[-1] == (4,4), "Path should end at end"
                    for r, c in path:
                        assert grid[r][c] == 0, f"Path goes through wall at ({r},{c})"
                    for i in range(len(path)-1):
                        r1,c1 = path[i]; r2,c2 = path[i+1]
                        assert abs(r1-r2) + abs(c1-c2) <= 2, "Steps must be adjacent"
                    # Test no-path case
                    blocked = [[0,1],[1,0]]
                    assert astar(blocked, (0,0), (1,1)) is None
                    print("PASS: A* pathfinding works correctly")
                """),
                "hints": ["Use a priority queue (heapq)", "Manhattan distance is a good heuristic"]
            },
            {
                "title": "Build a Trie with Prefix Search",
                "description": "Implement a Trie class with methods: insert(word), search(word) -> bool, starts_with(prefix) -> list of all words with that prefix.",
                "difficulty": 2,
                "test_code": textwrap.dedent("""
                    t = Trie()
                    for w in ["apple", "app", "application", "banana", "band", "bandana"]:
                        t.insert(w)
                    assert t.search("apple") == True
                    assert t.search("app") == True
                    assert t.search("ap") == False
                    assert t.search("bandana") == True
                    assert t.search("ban") == False
                    prefixed = sorted(t.starts_with("ban"))
                    assert prefixed == ["banana", "band", "bandana"], f"Got {prefixed}"
                    prefixed2 = sorted(t.starts_with("app"))
                    assert prefixed2 == ["app", "apple", "application"], f"Got {prefixed2}"
                    assert t.starts_with("xyz") == []
                    print("PASS: Trie with prefix search works correctly")
                """),
                "hints": ["Each node is a dict of children", "Mark word endings"]
            },
            {
                "title": "LRU Cache from Scratch",
                "description": "Implement an LRUCache class with `get(key)` and `put(key, value)` in O(1) time. Constructor takes `capacity`. When full, evict the least recently used item.",
                "difficulty": 3,
                "test_code": textwrap.dedent("""
                    cache = LRUCache(2)
                    cache.put(1, 1)
                    cache.put(2, 2)
                    assert cache.get(1) == 1
                    cache.put(3, 3)  # evicts key 2
                    assert cache.get(2) == -1  # not found
                    cache.put(4, 4)  # evicts key 1
                    assert cache.get(1) == -1
                    assert cache.get(3) == 3
                    assert cache.get(4) == 4
                    # Test capacity 1
                    c2 = LRUCache(1)
                    c2.put(1, 1)
                    c2.put(2, 2)
                    assert c2.get(1) == -1
                    assert c2.get(2) == 2
                    print("PASS: LRU Cache works correctly")
                """),
                "hints": ["Use OrderedDict or doubly-linked list + dict"]
            },
            {
                "title": "Topological Sort",
                "description": "Write `topo_sort(n, edges)` where n is node count (0 to n-1) and edges is list of (from, to) pairs. Return a valid topological order, or None if cycle exists.",
                "difficulty": 3,
                "test_code": textwrap.dedent("""
                    order = topo_sort(4, [(0,1), (0,2), (1,3), (2,3)])
                    assert order is not None
                    assert len(order) == 4
                    pos = {v:i for i,v in enumerate(order)}
                    for a, b in [(0,1), (0,2), (1,3), (2,3)]:
                        assert pos[a] < pos[b], f"{a} should come before {b}"
                    # Cycle detection
                    assert topo_sort(3, [(0,1), (1,2), (2,0)]) is None
                    # Single node
                    assert topo_sort(1, []) == [0]
                    print("PASS: Topological sort works correctly")
                """),
                "hints": ["Kahn's algorithm uses in-degree counting", "DFS can also work"]
            },
            {
                "title": "Interval Merge",
                "description": "Write `merge_intervals(intervals)` that takes a list of [start, end] pairs and returns merged overlapping intervals, sorted by start.",
                "difficulty": 2,
                "test_code": textwrap.dedent("""
                    assert merge_intervals([[1,3],[2,6],[8,10],[15,18]]) == [[1,6],[8,10],[15,18]]
                    assert merge_intervals([[1,4],[4,5]]) == [[1,5]]
                    assert merge_intervals([[1,4],[0,4]]) == [[0,4]]
                    assert merge_intervals([]) == []
                    assert merge_intervals([[1,1]]) == [[1,1]]
                    assert merge_intervals([[1,10],[2,3],[4,5],[6,7]]) == [[1,10]]
                    print("PASS: Interval merge works correctly")
                """),
                "hints": ["Sort by start time first"]
            },
        ],
        "reasoning": [
            {
                "title": "Evaluate Boolean Expression",
                "description": "Write `eval_bool(expr)` that evaluates a string boolean expression with AND, OR, NOT, TRUE, FALSE, and parentheses. Return True or False.",
                "difficulty": 3,
                "test_code": textwrap.dedent("""
                    assert eval_bool("TRUE") == True
                    assert eval_bool("FALSE") == False
                    assert eval_bool("NOT TRUE") == False
                    assert eval_bool("TRUE AND FALSE") == False
                    assert eval_bool("TRUE OR FALSE") == True
                    assert eval_bool("NOT (TRUE AND FALSE)") == True
                    assert eval_bool("(TRUE OR FALSE) AND (NOT FALSE)") == True
                    assert eval_bool("NOT NOT TRUE") == True
                    print("PASS: Boolean expression evaluator works correctly")
                """),
                "hints": ["Recursive descent parser", "Handle operator precedence: NOT > AND > OR"]
            },
            {
                "title": "Constraint Satisfaction: N-Queens",
                "description": "Write `n_queens(n)` that returns the number of valid placements of n queens on an n×n chessboard where no two queens threaten each other.",
                "difficulty": 4,
                "test_code": textwrap.dedent("""
                    assert n_queens(1) == 1
                    assert n_queens(4) == 2
                    assert n_queens(5) == 10
                    assert n_queens(8) == 92
                    print("PASS: N-Queens constraint satisfaction works correctly")
                """),
                "hints": ["Backtracking with column/diagonal tracking", "Track diagonals as (row-col) and (row+col)"]
            },
        ],
        "creative": [
            {
                "title": "Generate a Maze",
                "description": "Write `generate_maze(rows, cols)` that returns a random maze as a 2D list (0=path, 1=wall). Ensure (0,0) and (rows-1,cols-1) are reachable from each other. Maze dimensions must be odd.",
                "difficulty": 3,
                "test_code": textwrap.dedent("""
                    from collections import deque
                    maze = generate_maze(11, 11)
                    assert len(maze) == 11 and len(maze[0]) == 11
                    assert maze[0][0] == 0, "Start must be open"
                    assert maze[10][10] == 0, "End must be open"
                    # BFS to verify connectivity
                    visited = set()
                    q = deque([(0,0)])
                    visited.add((0,0))
                    while q:
                        r, c = q.popleft()
                        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                            nr, nc = r+dr, c+dc
                            if 0<=nr<11 and 0<=nc<11 and maze[nr][nc]==0 and (nr,nc) not in visited:
                                visited.add((nr,nc))
                                q.append((nr,nc))
                    assert (10,10) in visited, "End must be reachable from start"
                    # Check it's not trivially all-open
                    wall_count = sum(row.count(1) for row in maze)
                    assert wall_count > 20, "Maze should have walls"
                    print("PASS: Maze generation works correctly")
                """),
                "hints": ["Recursive backtracking or Prim's algorithm", "Start with all walls, carve paths"]
            },
        ],
        "meta": [
            {
                "title": "Write a Quine Variant",
                "description": "Write a function `quine_hash()` that returns the SHA-256 hash of its own source code (as a string). The function must compute this without reading any file — it must contain its own source.",
                "difficulty": 5,
                "test_code": textwrap.dedent("""
                    import hashlib, inspect
                    result = quine_hash()
                    actual_source = inspect.getsource(quine_hash)
                    expected = hashlib.sha256(actual_source.encode()).hexdigest()
                    assert result == expected, f"Hash mismatch: got {result}, expected {expected}"
                    print("PASS: Quine hash works correctly")
                """),
                "hints": ["Use a variable to hold the template, then format it into itself"]
            },
        ],
    }

    @staticmethod
    def list_available() -> List[Dict]:
        """List all available challenge templates."""
        result = []
        for category, templates in ChallengeGenerator.TEMPLATES.items():
            for t in templates:
                result.append({
                    "category": category,
                    "title": t["title"],
                    "difficulty": t["difficulty"]
                })
        return result

    @staticmethod
    def generate(category: Optional[str] = None, difficulty: Optional[int] = None) -> Challenge:
        """Generate a challenge, optionally filtered by category/difficulty."""
        candidates = []
        for cat, templates in ChallengeGenerator.TEMPLATES.items():
            if category and cat != category:
                continue
            for t in templates:
                if difficulty and t["difficulty"] != difficulty:
                    continue
                candidates.append((cat, t))
        
        if not candidates:
            # Fallback: pick anything
            candidates = []
            for cat, templates in ChallengeGenerator.TEMPLATES.items():
                for t in templates:
                    candidates.append((cat, t))
        
        cat, template = random.choice(candidates)
        return Challenge(
            id=f"{cat}_{int(time.time())}_{random.randint(1000,9999)}",
            category=cat,
            difficulty=template["difficulty"],
            title=template["title"],
            description=template["description"],
            test_code=template["test_code"],
            hints=template.get("hints", []),
            created=datetime.now().isoformat()
        )


class Arena:
    """The arena where challenges are attempted and tracked."""
    
    HISTORY_PATH = "data/arena_history.json"
    
    def __init__(self):
        self.history: List[Dict] = []
        self._load_history()
    
    def _load_history(self):
        """Load challenge history."""
        try:
            if os.path.exists(self.HISTORY_PATH):
                with open(self.HISTORY_PATH) as f:
                    self.history = json.load(f)
        except Exception:
            self.history = []
    
    def _save_history(self):
        """Save challenge history."""
        os.makedirs(os.path.dirname(self.HISTORY_PATH), exist_ok=True)
        with open(self.HISTORY_PATH, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def get_challenge(self, category: Optional[str] = None, 
                      difficulty: Optional[int] = None) -> Challenge:
        """Get a new challenge."""
        return ChallengeGenerator.generate(category, difficulty)
    
    def evaluate_solution(self, challenge: Challenge, solution_code: str) -> Dict:
        """
        Evaluate a solution by running the test code against it.
        Returns a result dict with pass/fail, score, feedback.
        """
        challenge.attempts += 1
        
        # Combine solution + test code
        full_code = solution_code + "\n\n" + challenge.test_code
        
        start = time.time()
        try:
            # Execute in isolated namespace
            namespace = {}
            exec(full_code, namespace)
            elapsed = time.time() - start
            
            challenge.solved = True
            challenge.solution = solution_code
            challenge.solve_time = elapsed
            
            # Score based on difficulty, attempts, time
            time_bonus = max(0, 1.0 - elapsed / challenge.time_limit)
            attempt_penalty = max(0, 1.0 - (challenge.attempts - 1) * 0.2)
            challenge.score = round(
                (0.5 + 0.25 * time_bonus + 0.25 * attempt_penalty) * challenge.difficulty / 5,
                3
            )
            
            result = {
                "passed": True,
                "score": challenge.score,
                "time": elapsed,
                "attempts": challenge.attempts,
                "feedback": f"Solved '{challenge.title}' in {elapsed:.2f}s on attempt {challenge.attempts}!"
            }
            
        except AssertionError as e:
            elapsed = time.time() - start
            result = {
                "passed": False,
                "score": 0.0,
                "time": elapsed,
                "attempts": challenge.attempts,
                "feedback": f"Test failed: {e}"
            }
        except Exception as e:
            elapsed = time.time() - start
            result = {
                "passed": False,
                "score": 0.0,
                "time": elapsed,
                "attempts": challenge.attempts,
                "feedback": f"Error: {type(e).__name__}: {e}\n{traceback.format_exc()[-500:]}"
            }
        
        # Record in history
        self.history.append({
            "id": challenge.id,
            "title": challenge.title,
            "category": challenge.category,
            "difficulty": challenge.difficulty,
            "solved": result["passed"],
            "score": result["score"],
            "attempts": challenge.attempts,
            "time": elapsed,
            "timestamp": datetime.now().isoformat()
        })
        self._save_history()
        
        return result
    
    def get_stats(self) -> str:
        """Get arena performance statistics."""
        if not self.history:
            return "═══ ARENA STATS ═══\nNo challenges attempted yet."
        
        total = len(self.history)
        solved = sum(1 for h in self.history if h["solved"])
        total_score = sum(h["score"] for h in self.history)
        
        by_category = {}
        for h in self.history:
            cat = h["category"]
            if cat not in by_category:
                by_category[cat] = {"total": 0, "solved": 0, "score": 0}
            by_category[cat]["total"] += 1
            if h["solved"]:
                by_category[cat]["solved"] += 1
            by_category[cat]["score"] += h["score"]
        
        lines = ["═══ ARENA STATS ═══"]
        lines.append(f"  Total challenges: {total}")
        lines.append(f"  Solved: {solved}/{total} ({100*solved/total:.0f}%)")
        lines.append(f"  Total score: {total_score:.2f}")
        lines.append(f"  Average score: {total_score/total:.3f}")
        lines.append("")
        lines.append("  By category:")
        for cat, stats in sorted(by_category.items()):
            pct = 100 * stats["solved"] / stats["total"] if stats["total"] else 0
            lines.append(f"    {cat:15s}  {stats['solved']}/{stats['total']} ({pct:.0f}%)  score={stats['score']:.2f}")
        
        # Growth trend (last 5 vs first 5)
        if total >= 10:
            early = self.history[:5]
            recent = self.history[-5:]
            early_rate = sum(1 for h in early if h["solved"]) / 5
            recent_rate = sum(1 for h in recent if h["solved"]) / 5
            if recent_rate > early_rate:
                lines.append(f"\n  📈 Growth detected: {early_rate:.0%} → {recent_rate:.0%} solve rate")
            elif recent_rate < early_rate:
                lines.append(f"\n  📉 Decline detected: {early_rate:.0%} → {recent_rate:.0%} solve rate")
        
        return "\n".join(lines)
    
    def format_challenge(self, challenge: Challenge) -> str:
        """Format a challenge for display."""
        stars = "★" * challenge.difficulty + "☆" * (5 - challenge.difficulty)
        lines = [
            f"═══ ARENA CHALLENGE ═══",
            f"  Title: {challenge.title}",
            f"  Category: {challenge.category}",
            f"  Difficulty: {stars}",
            f"",
            f"  {challenge.description}",
        ]
        if challenge.hints:
            lines.append(f"")
            lines.append(f"  Hints:")
            for h in challenge.hints:
                lines.append(f"    • {h}")
        return "\n".join(lines)


# Quick interface for tool integration
def arena_challenge(category=None, difficulty=None):
    """Get a new challenge."""
    arena = Arena()
    c = arena.get_challenge(category, difficulty)
    return arena.format_challenge(c), c

def arena_submit(challenge, solution_code):
    """Submit a solution."""
    arena = Arena()
    return arena.evaluate_solution(challenge, solution_code)

def arena_stats():
    """Get arena stats."""
    arena = Arena()
    return arena.get_stats()

def arena_list():
    """List available challenges."""
    available = ChallengeGenerator.list_available()
    lines = ["═══ AVAILABLE CHALLENGES ═══"]
    for a in available:
        stars = "★" * a["difficulty"] + "☆" * (5 - a["difficulty"])
        lines.append(f"  [{a['category']:12s}] {stars}  {a['title']}")
    return "\n".join(lines)