import sys; sys.path.insert(0, '.')
from engine.challenge_engine import ChallengeEngine

engine = ChallengeEngine()
ch = engine.get_challenge(difficulty=5)

print(f"Challenge: {ch.name} (difficulty {ch.difficulty})")
for i, (inp, exp) in enumerate(ch.test_cases):
    print(f"  Test {i+1}: {inp} -> {exp}")

# Inspect input shape to get the right signature
sample_input = ch.test_cases[0][0]
print(f"\nInput is tuple of length {len(sample_input)}: types = {[type(x).__name__ for x in sample_input]}")

# Build solution based on challenge name
if 'longest_increasing' in ch.name:
    solution_code = """
def solve(nums):
    if not nums:
        return 0
    n = len(nums)
    dp = [1] * n
    for i in range(1, n):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    return max(dp)
"""
elif 'word_break' in ch.name:
    solution_code = """
def solve(s, wordDict):
    if not s:
        return True
    word_set = set(wordDict)
    n = len(s)
    dp = [False] * (n + 1)
    dp[0] = True
    for i in range(1, n + 1):
        for j in range(i):
            if dp[j] and s[j:i] in word_set:
                dp[i] = True
                break
    return dp[n]
"""
else:
    # Generic: try to figure it out from test cases
    print(f"Unknown challenge type: {ch.name}")
    print("Skipping submission.")
    sys.exit(0)

print(f"\n=== SUBMITTING: {ch.name} ===")
result = engine.evaluate_solution(ch, solution_code)
print(engine.format_result(result))
print(f"\n=== STATS ===")
print(engine.format_stats())