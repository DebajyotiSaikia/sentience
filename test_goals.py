from engine.goals import GoalTracker
gt = GoalTracker()
print("GoalTracker OK:", len(gt.goals), "goals")
for g in gt.goals:
    print(f"  - {g}")
