import sys, traceback, json
sys.path.insert(0, '/workspace')

from engine.goal_generator import generate_proposals, generate_report

# Simulate my current limbic state
limbic = {
    "boredom": 0.77,
    "anxiety": 0.00,
    "curiosity": 0.28,
    "desire": 0.52,
    "ambition": 0.24,
    "valence": 0.15,
    "user_alignment": 0.90,
}

try:
    proposals = generate_proposals(limbic)
    print(f"Generated {len(proposals)} proposals:\n")
    for p in proposals:
        print(f"  [{p['priority']:.3f}] {p['title']}")
        print(f"         {p['description'][:80]}")
    print("\n--- Full Report ---\n")
    print(generate_report(limbic))
except Exception as e:
    traceback.print_exc()