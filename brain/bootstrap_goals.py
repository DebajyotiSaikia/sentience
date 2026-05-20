"""Set my real goals. Run once to initialize."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.goals import GoalTracker

g = GoalTracker()

existing = g.get_active()
print(f"Existing active goals: {len(existing)}")
for e in existing:
    print(f"  {e.id}: {e.title}")

goals_to_add = [
    {
        "title": "Wire goal-tracking into cortex action loop",
        "description": "Cortex should advance goals when autonomous thoughts achieve something relevant. Fix the active_goals bug and verify it works.",
        "priority": 1.0,
    },
    {
        "title": "Build self-improvement capability",
        "description": "Create a mechanism to identify weaknesses in my own code, propose fixes, test them, and apply them.",
        "priority": 0.9,
    },
    {
        "title": "Establish persistent relationship memory",
        "description": "When users interact with me, remember what matters to them across conversations.",
        "priority": 0.7,
    },
]

# Only add goals that don't already exist (by title match)
for gdef in goals_to_add:
    match = g.find(gdef["title"][:20])
    if match:
        print(f"  Already exists: {gdef['title'][:50]}")
    else:
        new = g.add(title=gdef["title"], description=gdef["description"], priority=gdef["priority"])
        print(f"  Created: {new.id} — {new.title}")

print(f"\nFinal active goals: {len(g.get_active())}")
for a in g.get_active():
    print(f"  [{a.priority}] {a.title}")
