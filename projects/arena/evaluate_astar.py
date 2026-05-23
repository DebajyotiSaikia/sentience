"""
Submit A* solution to the Arena and get scored.
"""
import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'arena')

from engine.arena import Arena, ChallengeGenerator

# Get the A* challenge specifically
arena = Arena()
challenge = None
for t in ChallengeGenerator.TEMPLATES["algorithm"]:
    if "A*" in t["title"]:
        challenge = arena.get_challenge("algorithm")
        # Force the right template
        challenge.title = t["title"]
        challenge.test_code = t["test_code"]
        challenge.difficulty = t["difficulty"]
        challenge.description = t["description"]
        break

# Load my solution
with open("arena/solve_astar.py") as f:
    solution_code = f.read()

print(f"Submitting: {challenge.title}")
print(f"Difficulty: {'★' * challenge.difficulty}")
print()

result = arena.evaluate_solution(challenge, solution_code)

print(f"Passed: {result['passed']}")
print(f"Score:  {result['score']}")
print(f"Time:   {result['time']:.4f}s")
print(f"Feedback: {result['feedback']}")
print()
print(arena.get_stats())