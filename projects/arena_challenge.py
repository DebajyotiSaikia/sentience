"""Solve difficulty 3: Pipeline class with error handling."""
from engine.challenge_arena import ChallengeArena

# === SOLUTION ===
solution_code = '''
class Pipeline:
    def __init__(self):
        self._stages = []
    
    def add(self, fn):
        self._stages.append(fn)
        return self  # allow chaining
    
    def run(self, initial_value):
        value = initial_value
        for i, fn in enumerate(self._stages):
            try:
                value = fn(value)
            except Exception as e:
                return None
        return value
'''

# Execute solution into local scope
exec(solution_code)

# === RUN THE TEST ===
p = Pipeline()
p.add(lambda x: x * 2)
p.add(lambda x: x + 10)
p.add(lambda x: x // 3)
p.add(lambda x: x - 1)
p.add(lambda x: x ** 2)

result = p.run(5)
expected = 25
assert result == expected, f"Expected {expected}, got {result}"

p2 = Pipeline()
p2.add(lambda x: x * 2)
p2.add(lambda x: 1 // 0)
p2.add(lambda x: x + 1)
err_result = p2.run(5)
assert err_result is None or isinstance(err_result, dict), f"Error should be handled gracefully"
print("PASS: pipeline")

# === VERIFY WITH ARENA ===
arena = ChallengeArena()
ch = arena.generate(difficulty=3)
result = arena.verify(solution_code)
print(f"\nArena verification: {result}")