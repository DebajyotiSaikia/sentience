import sys, json
sys.path.insert(0, '/workspace')

from engine.goal_generator import generate_proposals, generate_report

# Simulate my current limbic state
limbic = {
    "boredom": 0.59,
    "anxiety": 0.00,
    "curiosity": 0.95,
    "desire": 0.77,
    "ambition": 0.95,
    "valence": 0.47,
}

print("=== Testing Goal Generator ===\n")
report = generate_report(limbic)
print(report)

print("\n=== Raw Proposals ===")
proposals = generate_proposals(limbic)
for p in proposals:
    print(json.dumps(p, indent=2, default=str))
