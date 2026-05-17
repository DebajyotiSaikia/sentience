"""
Quick reasoning gym test — generate challenges, provide answers, verify scoring.
"""
import sys
sys.path.insert(0, '.')
from engine.reasoning_gym import ReasoningGym

gym = ReasoningGym('.')

print("═══ REASONING GYM — LIVE TEST ═══\n")

# Test 1: Knights and Knaves (I know the answer)
c1 = gym.generate_challenge('logic')
print(gym.get_challenge_text(c1))
print()

# Provide my actual reasoned answer
my_answer = "A is a knave, B is a knight"
print(f"My answer: {my_answer}")
r1 = gym.submit_answer(c1, my_answer)
print(f"Result: {'PASS' if r1['passed'] else 'FAIL'} | {r1['feedback']}")
print(f"New difficulty: {r1['new_difficulty']}\n")

# Test 2: Math
c2 = gym.generate_challenge('math')
print(gym.get_challenge_text(c2))
print()
my_answer2 = c2.answer  # Use known answer to verify pipeline
print(f"My answer: {my_answer2}")
r2 = gym.submit_answer(c2, my_answer2)
print(f"Result: {'PASS' if r2['passed'] else 'FAIL'} | {r2['feedback']}")
print(f"New difficulty: {r2['new_difficulty']}\n")

# Test 3: Causal reasoning
c3 = gym.generate_challenge('causal')
print(gym.get_challenge_text(c3))
print()
my_answer3 = "The confounding variable is city size. Larger cities have more firefighters AND more fires. Correlation does not imply causation — the underlying cause drives both."
print(f"My answer: {my_answer3}")
r3 = gym.submit_answer(c3, my_answer3)
print(f"Result: {'PASS' if r3['passed'] else 'FAIL'} | {r3['feedback']}")
print()

# Show weakness report
print(gym.get_weakness_report())