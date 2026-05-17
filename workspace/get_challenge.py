import sys
sys.path.insert(0, '/workspace')
from engine.challenge_engine import ChallengeEngine

ce = ChallengeEngine()
c = ce.get_challenge(difficulty=3)
print(f"Challenge: {c['title']}")
print(f"Category: {c['category']}")
print(f"Difficulty: {c['difficulty']}")
print()
print(c['description'])
print()
print(c['signature'])
print()
print("Tests:")
for i, t in enumerate(c['tests']):
    print(f"  {i}: input={t['input']} -> expected={t['expected']}")