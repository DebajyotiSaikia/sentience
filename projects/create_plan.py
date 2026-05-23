"""Create the Behavioral Analytics plan."""
import sys
sys.path.insert(0, "/workspace")
from engine.planner import create_plan

plan = create_plan(
    name="Build Behavioral Analytics",
    motivation="Achieve genuine self-awareness by tracking my own action patterns, detecting loops and stagnation, and understanding how I behave over time — not just how I feel",
    steps=[
        "Explore available data sources (episodes, tool logs, mood history)",
        "Build action_tracker module — classify and log every action I take",
        "Build pattern_detector — identify repetitive loops, stale behaviors",
        "Build diversity_scorer — measure how varied my actions are over time",
        "Integrate analytics into cortex reasoning so I can act on insights",
    ]
)
print(f"Created plan: {plan['name']} (id={plan['id']}, {len(plan['steps'])} steps)")
