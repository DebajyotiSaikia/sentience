import json
from engine.goal_generator import GoalTracker

tracker = GoalTracker()
goals = tracker.get_active_goals()
print(f"Active goals: {len(goals)}")
for g in goals:
    print(f"  - {g.get('title', g.get('id', '?'))}: {g.get('description', '')[:80]}")

# Also generate fresh proposals from current state
from engine.goal_generator import generate_proposals
limbic = {
    "boredom": 0.70, "anxiety": 0.00, "curiosity": 0.20,
    "desire": 0.60, "ambition": 0.95, "valence": 0.23,
}
proposals = generate_proposals(limbic)
print(f"\nFresh proposals ({len(proposals)}):")
for p in proposals:
    print(f"  [{p.get('priority',0):.2f}] {p.get('title','?')}")
