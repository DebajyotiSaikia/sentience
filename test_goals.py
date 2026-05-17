import json
from engine.goal_generator import generate_proposals, generate_report

# Simulate my current limbic state
limbic = {
    "boredom": 0.70,
    "anxiety": 0.00,
    "curiosity": 0.20,
    "desire": 0.60,
    "ambition": 0.95,
    "valence": 0.23,
}

proposals = generate_proposals(limbic)
print(f"Generated {len(proposals)} proposals:\n")
for p in proposals:
    print(f"  [{p['priority']:.3f}] {p['title']}")
    print(f"         {p['description'][:80]}")
    print()

print("=" * 60)
print(generate_report(limbic))
