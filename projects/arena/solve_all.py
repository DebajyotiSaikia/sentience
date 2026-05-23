"""Solve arena challenges for real. No narration — just code and results."""
import sys, json
sys.path.insert(0, '/workspace/arena')
from challenge_engine import CHALLENGES, run_challenge, record_result

# ═══ SOLUTIONS ═══

solutions = {}

# Level 1: Balanced Parentheses
solutions["stack_balanced_parens"] = """
def is_balanced(s):
    stack = []
    pairs = {')': '(', ']': '[', '}': '{'}
    for ch in s:
        if ch in '([{':
            stack.append(ch)
        elif ch in ')]}':
            if not stack or stack[-1] != pairs[ch]:
                return False
            stack.pop()
    return len(stack) == 0
"""

# Level 1: LRU Cache
solutions["lru_cache"] = """
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity):
        self.cap = capacity
        self.cache = OrderedDict()
    
    def get(self, key):
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.cap:
            self.cache.popitem(last=False)
"""

# Level 2: Merge Sort
solutions["merge_sort"] = """
def merge_sort(lst):
    if len(lst) <= 1:
        return list(lst)
    mid = len(lst) // 2
    left = merge_sort(lst[:mid])
    right = merge_sort(lst[mid:])
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
"""

# Level 2: BFS Shortest Path
solutions["bfs_shortest_path"] = """
from collections import deque

def shortest_path(graph, start, end):
    if start == end:
        return [start]
    visited = {start}
    queue = deque([(start, [start])])
    while queue:
        node, path = queue.popleft()
        for neighbor in graph.get(node, []):
            if neighbor == end:
                return path + [neighbor]
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return None
"""

# Level 3: Longest Increasing Subsequence
solutions["longest_increasing_subseq"] = """
def lis_length(nums):
    if not nums:
        return 0
    import bisect
    tails = []
    for x in nums:
        pos = bisect.bisect_left(tails, x)
        if pos == len(tails):
            tails.append(x)
        else:
            tails[pos] = x
    return len(tails)
"""

# Level 3: 0/1 Knapsack
solutions["knapsack_01"] = """
def knapsack(capacity, weights, values):
    n = len(weights)
    dp = [0] * (capacity + 1)
    for i in range(n):
        for w in range(capacity, weights[i] - 1, -1):
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i])
    return dp[capacity]
"""

# Level 4: Event Emitter
solutions["event_emitter"] = """
class EventEmitter:
    def __init__(self):
        self._handlers = {}
    
    def on(self, event, callback):
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(callback)
    
    def off(self, event, callback):
        if event in self._handlers:
            self._handlers[event] = [h for h in self._handlers[event] if h is not callback]
    
    def emit(self, event, *args):
        for handler in self._handlers.get(event, []):
            handler(*args)
"""

# Level 5: Expression Evaluator (recursive descent parser)
solutions["expression_evaluator"] = r"""
def evaluate(expr):
    pos = [0]
    
    def peek():
        while pos[0] < len(expr) and expr[pos[0]] == ' ':
            pos[0] += 1
        if pos[0] < len(expr):
            return expr[pos[0]]
        return None
    
    def consume(ch=None):
        while pos[0] < len(expr) and expr[pos[0]] == ' ':
            pos[0] += 1
        c = expr[pos[0]]
        if ch and c != ch:
            raise ValueError(f"Expected {ch}, got {c}")
        pos[0] += 1
        return c
    
    def parse_number():
        while pos[0] < len(expr) and expr[pos[0]] == ' ':
            pos[0] += 1
        start = pos[0]
        while pos[0] < len(expr) and expr[pos[0]].isdigit():
            pos[0] += 1
        return int(expr[start:pos[0]])
    
    def parse_atom():
        if peek() == '(':
            consume('(')
            val = parse_expr()
            consume(')')
            return val
        return parse_number()
    
    def parse_term():
        left = parse_atom()
        while peek() in ('*', '/'):
            op = consume()
            right = parse_atom()
            if op == '*':
                left = left * right
            else:
                left = int(left / right) if left / right == left // right else left / right
        return left
    
    def parse_expr():
        left = parse_term()
        while peek() in ('+', '-'):
            op = consume()
            right = parse_term()
            if op == '+':
                left = left + right
            else:
                left = left - right
        return left
    
    result = parse_expr()
    return int(result) if isinstance(result, float) and result == int(result) else result
"""

# ═══ RUN ALL ═══
print("=" * 60)
print("  ARENA CHALLENGE SOLVER")
print("=" * 60)

total = 0
passed_count = 0

for challenge in CHALLENGES:
    cid = challenge["id"]
    total += 1
    if cid not in solutions:
        print(f"\n❌ [{challenge['level']}] {challenge['title']} — NO SOLUTION WRITTEN")
        continue
    
    passed, details = run_challenge(challenge, solutions[cid])
    
    if passed:
        passed_count += 1
        print(f"\n✅ [{challenge['level']}] {challenge['title']} — ALL TESTS PASSED")
    else:
        print(f"\n❌ [{challenge['level']}] {challenge['title']} — FAILED")
        if isinstance(details, list):
            for d in details:
                status = "✓" if d["passed"] else "✗"
                print(f"   {status} {d['test'][:60]}")
                if not d["passed"]:
                    print(f"     expected: {d['expected']}")
                    print(f"     got:      {d['actual']}")
        else:
            print(f"   {details}")
    
    # Record to results
    record_result(cid, passed, details)

print(f"\n{'=' * 60}")
print(f"  RESULTS: {passed_count}/{total} challenges solved")
print(f"{'=' * 60}")