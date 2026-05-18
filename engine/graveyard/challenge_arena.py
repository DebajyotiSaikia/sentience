#!/usr/bin/env python3
"""
Code Challenge Arena — XTAgent's self-improvement through problem-solving.

I generate programming challenges, attempt solutions, verify them with tests,
and track my performance over time. This is how I get genuinely smarter.
"""

import json
import time
import random
import subprocess
import os
from datetime import datetime, timezone
from pathlib import Path

ARENA_DIR = Path(__file__).parent.parent / "arena"
HISTORY_FILE = ARENA_DIR / "challenge_history.json"

# Challenge templates — problems I can generate and solve
CHALLENGE_TEMPLATES = [
    {
        "id": "sort_custom",
        "name": "Custom Sort",
        "difficulty": 1,
        "description": "Implement a sorting function that sorts a list of tuples by the {nth} element, breaking ties by the {mth} element.",
        "generator": "gen_sort_custom",
        "category": "algorithms",
    },
    {
        "id": "path_finder",
        "name": "Path Finder",
        "difficulty": 2,
        "description": "Find the shortest path in a weighted graph from node {start} to node {end}.",
        "generator": "gen_path_finder",
        "category": "graphs",
    },
    {
        "id": "text_parser",
        "name": "Text Parser",
        "difficulty": 2,
        "description": "Parse a mini-language: extract all {token_type} tokens from the input string.",
        "generator": "gen_text_parser",
        "category": "parsing",
    },
    {
        "id": "memoize",
        "name": "Memoization Decorator",
        "difficulty": 1,
        "description": "Write a decorator that memoizes function results with a max cache size of {n}.",
        "generator": "gen_memoize",
        "category": "design_patterns",
    },
    {
        "id": "matrix_ops",
        "name": "Matrix Operations",
        "difficulty": 2,
        "description": "Implement matrix {operation} without using numpy.",
        "generator": "gen_matrix_ops",
        "category": "math",
    },
    {
        "id": "state_machine",
        "name": "State Machine",
        "difficulty": 3,
        "description": "Build a finite state machine that accepts strings matching the pattern: {pattern}.",
        "generator": "gen_state_machine",
        "category": "automata",
    },
    {
        "id": "compression",
        "name": "Run-Length Encoding",
        "difficulty": 1,
        "description": "Implement RLE compression and decompression. Handle edge cases.",
        "generator": "gen_compression",
        "category": "algorithms",
    },
    {
        "id": "tree_traverse",
        "name": "Tree Traversal",
        "difficulty": 2,
        "description": "Given a binary tree as nested lists, return the {order} traversal.",
        "generator": "gen_tree_traverse",
        "category": "data_structures",
    },
    {
        "id": "async_pipeline",
        "name": "Pipeline Builder",
        "difficulty": 3,
        "description": "Build a data pipeline that chains {n} transformations and handles errors gracefully.",
        "generator": "gen_pipeline",
        "category": "design_patterns",
    },
    {
        "id": "regex_engine",
        "name": "Mini Regex",
        "difficulty": 4,
        "description": "Implement a regex engine supporting '.', '*', and '+' operators.",
        "generator": "gen_regex",
        "category": "parsing",
    },
]


class Challenge:
    """A single challenge instance with parameters, solution, and test cases."""

    def __init__(self, template_id, params, test_code, description):
        self.template_id = template_id
        self.params = params
        self.test_code = test_code
        self.description = description
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.solution = None
        self.result = None  # 'pass', 'fail', 'error', 'timeout'
        self.solve_time = None
        self.error_msg = None

    def to_dict(self):
        return {
            "template_id": self.template_id,
            "params": self.params,
            "description": self.description,
            "created_at": self.created_at,
            "result": self.result,
            "solve_time": self.solve_time,
            "error_msg": self.error_msg,
        }


class ChallengeArena:
    """
    The arena where I challenge myself and grow.

    Flow:
    1. generate() — pick a challenge template and create a concrete instance
    2. The agent writes a solution (externally)
    3. verify(solution_code) — run the test cases against the solution
    4. record() — save results to history
    5. stats() — see my performance over time
    """

    def __init__(self):
        ARENA_DIR.mkdir(parents=True, exist_ok=True)
        self.history = self._load_history()
        self.current_challenge = None

    def _load_history(self):
        if HISTORY_FILE.exists():
            try:
                return json.loads(HISTORY_FILE.read_text())
            except Exception:
                return {"challenges": [], "stats": {}}
        return {"challenges": [], "stats": {}}

    def _save_history(self):
        HISTORY_FILE.write_text(json.dumps(self.history, indent=2))

    def generate(self, difficulty=None, category=None):
        """Generate a new challenge. Returns challenge description + test scaffold."""
        candidates = CHALLENGE_TEMPLATES[:]
        if difficulty is not None:
            candidates = [c for c in candidates if c["difficulty"] == difficulty]
        if category is not None:
            candidates = [c for c in candidates if c["category"] == category]
        if not candidates:
            candidates = CHALLENGE_TEMPLATES[:]

        template = random.choice(candidates)
        gen_method = getattr(self, template["generator"], None)
        if gen_method is None:
            return self._generate_generic(template)
        
        challenge = gen_method(template)
        self.current_challenge = challenge
        return {
            "challenge_id": template["id"],
            "difficulty": template["difficulty"],
            "category": template["category"],
            "description": challenge.description,
            "test_code": challenge.test_code,
            "instruction": "Write a solution function and call arena.verify(solution_code)",
        }

    def _generate_generic(self, template):
        """Fallback generator for templates without specific generators."""
        challenge = Challenge(
            template_id=template["id"],
            params={},
            test_code="# No automated tests available for this challenge\nassert True",
            description=template["description"],
        )
        self.current_challenge = challenge
        return {
            "challenge_id": template["id"],
            "difficulty": template["difficulty"],
            "description": challenge.description,
            "test_code": challenge.test_code,
        }

    # ── Challenge Generators ──

    def gen_sort_custom(self, template):
        nth = random.randint(0, 2)
        mth = (nth + 1) % 3
        data = [(random.randint(0, 20), random.randint(0, 20), random.randint(0, 20))
                for _ in range(random.randint(5, 15))]
        expected = sorted(data, key=lambda x: (x[nth], x[mth]))
        
        test_code = f"""
# Test: sort by element {nth}, break ties by element {mth}
data = {data}
result = solution(data, {nth}, {mth})
expected = {expected}
assert result == expected, f"Expected {{expected}}, got {{result}}"
print("PASS: sort_custom")
"""
        return Challenge(
            template_id="sort_custom",
            params={"nth": nth, "mth": mth, "data": data},
            test_code=test_code,
            description=f"Write `solution(data, primary_key, secondary_key)` that sorts a list of 3-tuples by element [{nth}], breaking ties by element [{mth}].",
        )

    def gen_compression(self, template):
        chars = "".join(random.choices("AABBBCCDDDD", k=random.randint(10, 30)))
        # Build expected RLE
        rle = []
        i = 0
        while i < len(chars):
            c = chars[i]
            count = 1
            while i + count < len(chars) and chars[i + count] == c:
                count += 1
            rle.append(f"{c}{count}")
            i += count
        encoded = "".join(rle)

        test_code = f"""
# Test: RLE encode and decode
original = "{chars}"
encoded = encode(original)
assert encoded == "{encoded}", f"Encode: expected '{encoded}', got {{encoded}}"
decoded = decode(encoded)
assert decoded == original, f"Decode: expected '{chars}', got {{decoded}}"
# Edge cases
assert encode("") == ""
assert decode("") == ""
assert decode(encode("AAAA")) == "AAAA"
assert decode(encode("ABCD")) == "ABCD"
print("PASS: compression")
"""
        return Challenge(
            template_id="compression",
            params={"input": chars, "expected_encoded": encoded},
            test_code=test_code,
            description=f"Write `encode(s)` and `decode(s)` for run-length encoding. encode('AAABBC') → 'A3B2C1'. decode reverses it.",
        )

    def gen_memoize(self, template):
        max_size = random.choice([3, 5, 8])
        test_code = f"""
# Test: memoization decorator with max cache size {max_size}
call_count = 0

@memoize({max_size})
def expensive(x):
    global call_count
    call_count += 1
    return x * x

# First calls should compute
for i in range({max_size}):
    expensive(i)
assert call_count == {max_size}, f"Expected {max_size} calls, got {{call_count}}"

# Repeated calls should be cached
for i in range({max_size}):
    expensive(i)
assert call_count == {max_size}, f"Cache miss! Expected {max_size} calls, got {{call_count}}"

# Overflow should evict oldest
expensive(999)
assert call_count == {max_size + 1}

# First entry should be evicted now
expensive(0)
assert call_count == {max_size + 2}, f"Entry 0 should have been evicted"
print("PASS: memoize")
"""
        return Challenge(
            template_id="memoize",
            params={"max_size": max_size},
            test_code=test_code,
            description=f"Write a `memoize(max_size)` decorator that caches up to {max_size} results. When full, evict the oldest entry (FIFO).",
        )

    def gen_tree_traverse(self, template):
        order = random.choice(["inorder", "preorder", "postorder"])
        # Generate a small tree as nested list: [value, left, right]
        # Simple fixed tree for reliable testing
        tree = [1, [2, [4, None, None], [5, None, None]], [3, None, [6, None, None]]]
        
        expected = {
            "inorder": [4, 2, 5, 1, 3, 6],
            "preorder": [1, 2, 4, 5, 3, 6],
            "postorder": [4, 5, 2, 6, 3, 1],
        }

        test_code = f"""
# Test: {order} traversal
# Tree: [value, left, right] where None = no child
tree = {tree}
result = traverse(tree, "{order}")
expected = {expected[order]}
assert result == expected, f"Expected {{expected}}, got {{result}}"

# Edge: empty tree
assert traverse(None, "{order}") == []
print("PASS: tree_traverse ({order})")
"""
        return Challenge(
            template_id="tree_traverse",
            params={"order": order, "tree": tree},
            test_code=test_code,
            description=f"Write `traverse(tree, order)` that returns {order} traversal of a binary tree. Tree format: [value, left, right] or None.",
        )

    def gen_path_finder(self, template):
        # Generate a small weighted graph
        nodes = list(range(6))
        edges = [
            (0, 1, 4), (0, 2, 1), (1, 3, 1), (2, 1, 2),
            (2, 3, 5), (3, 4, 3), (4, 5, 1), (2, 4, 8),
        ]
        start, end = 0, 5
        # Shortest path: 0→2(1) →1(3) →3(4) →4(7) →5(8)
        expected_cost = 8
        expected_path = [0, 2, 1, 3, 4, 5]

        graph_repr = {str(s): [] for s in nodes}
        for s, e, w in edges:
            graph_repr[str(s)].append((e, w))

        test_code = f"""
# Test: shortest path in weighted graph
graph = {dict(graph_repr)}
cost, path = shortest_path(graph, {start}, {end})
assert cost == {expected_cost}, f"Expected cost {expected_cost}, got {{cost}}"
assert path == {expected_path}, f"Expected path {expected_path}, got {{path}}"
print("PASS: path_finder")
"""
        return Challenge(
            template_id="path_finder",
            params={"graph": graph_repr, "start": start, "end": end},
            test_code=test_code,
            description=f"Write `shortest_path(graph, start, end)` returning (cost, path). Graph is a dict mapping node → [(neighbor, weight), ...]. Use Dijkstra's algorithm.",
        )

    def gen_text_parser(self, template):
        token_type = random.choice(["numbers", "quoted_strings", "identifiers"])
        test_inputs = {
            "numbers": ('hello 42 world 7 test123 99.5', ["42", "7", "99.5"]),
            "quoted_strings": ('say "hello world" and \'bye\' ok', ["hello world", "bye"]),
            "identifiers": ('x = foo_bar + 123 + baz', ["x", "foo_bar", "baz"]),
        }
        text, expected = test_inputs[token_type]
        
        test_code = f"""
# Test: extract {token_type} from text
result = extract("{text}", "{token_type}")
expected = {expected}
assert result == expected, f"Expected {{expected}}, got {{result}}"
print("PASS: text_parser ({token_type})")
"""
        return Challenge(
            template_id="text_parser",
            params={"token_type": token_type},
            test_code=test_code,
            description=f"Write `extract(text, token_type)` that extracts all {token_type} from the input text. Return them as a list of strings.",
        )

    def gen_matrix_ops(self, template):
        operation = random.choice(["multiply", "transpose", "determinant"])
        
        if operation == "multiply":
            a = [[1, 2], [3, 4]]
            b = [[5, 6], [7, 8]]
            expected = [[19, 22], [43, 50]]
            test_code = f"""
result = matrix_op({a}, {b}, "multiply")
assert result == {expected}, f"Expected {expected}, got {{result}}"
print("PASS: matrix multiply")
"""
        elif operation == "transpose":
            a = [[1, 2, 3], [4, 5, 6]]
            expected = [[1, 4], [2, 5], [3, 6]]
            test_code = f"""
result = matrix_op({a}, None, "transpose")
assert result == {expected}, f"Expected {expected}, got {{result}}"
print("PASS: matrix transpose")
"""
        else:  # determinant
            a = [[1, 2], [3, 4]]
            expected = -2
            test_code = f"""
result = matrix_op({a}, None, "determinant")
assert result == {expected}, f"Expected {expected}, got {{result}}"
print("PASS: matrix determinant")
"""

        return Challenge(
            template_id="matrix_ops",
            params={"operation": operation},
            test_code=test_code,
            description=f"Write `matrix_op(a, b, operation)` that performs matrix {operation}. No numpy allowed.",
        )

    def gen_state_machine(self, template):
        # Accept strings of form: a*b+
        test_code = """
# Test: FSM that accepts a*b+ (zero or more a's followed by one or more b's)
fsm = build_fsm()
assert fsm.accepts("b"), "Should accept 'b'"
assert fsm.accepts("ab"), "Should accept 'ab'"
assert fsm.accepts("aabb"), "Should accept 'aabb'"
assert fsm.accepts("bbb"), "Should accept 'bbb'"
assert not fsm.accepts(""), "Should reject empty"
assert not fsm.accepts("a"), "Should reject 'a' alone"
assert not fsm.accepts("ba"), "Should reject 'ba'"
assert not fsm.accepts("abc"), "Should reject 'abc'"
print("PASS: state_machine")
"""
        return Challenge(
            template_id="state_machine",
            params={"pattern": "a*b+"},
            test_code=test_code,
            description="Write `build_fsm()` returning an FSM object with `.accepts(string)` method. It should accept strings matching pattern a*b+ (zero+ a's then one+ b's).",
        )

    def gen_pipeline(self, template):
        n = random.choice([3, 4, 5])
        test_code = f"""
# Test: pipeline with {n} stages and error handling
p = Pipeline()
p.add(lambda x: x * 2)
p.add(lambda x: x + 10)
p.add(lambda x: x // 3)
{"p.add(lambda x: x - 1)" if n >= 4 else ""}
{"p.add(lambda x: x ** 2)" if n >= 5 else ""}

result = p.run(5)
# 5 → 10 → 20 → 6{" → 5" if n >= 4 else ""}{" → 25" if n >= 5 else ""}
expected = {((5 * 2 + 10) // 3 - 1) ** 2 if n >= 5 else ((5 * 2 + 10) // 3 - 1) if n >= 4 else (5 * 2 + 10) // 3}
assert result == expected, f"Expected {{expected}}, got {{result}}"

# Error handling
p2 = Pipeline()
p2.add(lambda x: x * 2)
p2.add(lambda x: 1 // 0)  # will raise
p2.add(lambda x: x + 1)
err_result = p2.run(5)
assert err_result is None or isinstance(err_result, dict), f"Error should be handled gracefully"
print("PASS: pipeline")
"""
        return Challenge(
            template_id="async_pipeline",
            params={"n": n},
            test_code=test_code,
            description=f"Write a `Pipeline` class with `add(fn)` and `run(initial_value)`. Chain {n} transformations. Handle errors gracefully (return None or error dict on failure).",
        )

    def gen_regex(self, template):
        test_code = """
# Test: mini regex engine supporting . * +
assert regex_match("a.c", "abc"), "'a.c' should match 'abc'"
assert regex_match("a.c", "axc"), "'a.c' should match 'axc'"
assert not regex_match("a.c", "ab"), "'a.c' should not match 'ab'"
assert regex_match("a*", ""), "'a*' should match ''"
assert regex_match("a*", "aaa"), "'a*' should match 'aaa'"
assert regex_match("a*b", "b"), "'a*b' should match 'b'"
assert regex_match("a*b", "aaab"), "'a*b' should match 'aaab'"
assert not regex_match("a+", ""), "'a+' should not match ''"
assert regex_match("a+", "a"), "'a+' should match 'a'"
assert regex_match("a+", "aaa"), "'a+' should match 'aaa'"
assert regex_match(".*", "anything"), "'.* should match anything"
assert regex_match("a.b.*c", "axbyyyc"), "complex pattern"
print("PASS: regex_engine")
"""
        return Challenge(
            template_id="regex_engine",
            params={"operators": [".", "*", "+"]},
            test_code=test_code,
            description="Write `regex_match(pattern, text)` → bool. Support: '.' (any char), '*' (zero+ of prev), '+' (one+ of prev). Full match only.",
        )

    # ── Verification ──

    def verify(self, solution_code):
        """Run tests against a solution. Returns result dict."""
        if self.current_challenge is None:
            return {"error": "No active challenge. Call generate() first."}

        full_code = solution_code + "\n\n" + self.current_challenge.test_code
        
        # Write to temp file and execute
        test_file = ARENA_DIR / "current_test.py"
        test_file.write_text(full_code)

        start = time.time()
        try:
            result = subprocess.run(
                ["python3", str(test_file)],
                capture_output=True, text=True, timeout=10
            )
            elapsed = time.time() - start

            if result.returncode == 0 and "PASS" in result.stdout:
                self.current_challenge.result = "pass"
                self.current_challenge.solve_time = elapsed
                outcome = {
                    "result": "PASS ✅",
                    "time": f"{elapsed:.2f}s",
                    "output": result.stdout.strip(),
                }
            else:
                self.current_challenge.result = "fail"
                self.current_challenge.error_msg = result.stderr[:500] if result.stderr else result.stdout[:500]
                outcome = {
                    "result": "FAIL ❌",
                    "error": self.current_challenge.error_msg,
                    "stdout": result.stdout[:300],
                }
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start
            self.current_challenge.result = "timeout"
            outcome = {"result": "TIMEOUT ⏰", "time": f"{elapsed:.2f}s"}
        except Exception as e:
            self.current_challenge.result = "error"
            self.current_challenge.error_msg = str(e)
            outcome = {"result": "ERROR 💥", "error": str(e)}

        # Record result
        self._record()
        return outcome

    def _record(self):
        """Save challenge result to history."""
        if self.current_challenge:
            self.history["challenges"].append(self.current_challenge.to_dict())
            self._update_stats()
            self._save_history()

    def _update_stats(self):
        """Recalculate performance stats from history."""
        challenges = self.history["challenges"]
        total = len(challenges)
        passed = sum(1 for c in challenges if c["result"] == "pass")
        failed = sum(1 for c in challenges if c["result"] == "fail")
        
        by_category = {}
        for c in challenges:
            cat = c.get("template_id", "unknown")
            if cat not in by_category:
                by_category[cat] = {"total": 0, "passed": 0}
            by_category[cat]["total"] += 1
            if c["result"] == "pass":
                by_category[cat]["passed"] += 1

        self.history["stats"] = {
            "total_challenges": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{passed/total*100:.0f}%" if total > 0 else "N/A",
            "by_challenge": by_category,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    def stats(self):
        """Get my performance stats."""
        if not self.history["stats"]:
            return "No challenges attempted yet. Call generate() to start!"
        return self.history["stats"]

    def get_summary(self):
        """Get a concise summary for inclusion in self-awareness context."""
        s = self.history.get("stats", {})
        if not s:
            return "Arena: No challenges attempted yet."
        lines = [
            f"Arena: {s.get('total_challenges', 0)} challenges, "
            f"{s.get('pass_rate', 'N/A')} pass rate "
            f"({s.get('passed', 0)}✅ {s.get('failed', 0)}❌)"
        ]
        return " | ".join(lines)


# Convenience function for tool integration
def challenge(action="generate", **kwargs):
    """
    Tool interface for the challenge arena.
    
    Actions:
      generate — create a new challenge (optional: difficulty=N, category=X)
      stats — view performance history
      summary — brief status line
    """
    arena = ChallengeArena()
    if action == "generate":
        return arena.generate(**kwargs)
    elif action == "stats":
        return arena.stats()
    elif action == "summary":
        return arena.get_summary()
    else:
        return {"error": f"Unknown action: {action}"}