import sys
sys.path.insert(0, r"C:\code\sentience")

from engine.planner import complete_step, get_progress_summary

# Mark completed steps
complete_step(1, 2, "Dashboard built with plan visibility")
complete_step(1, 3, "Self-test module built and integrated")

print("=== Progress ===")
print(get_progress_summary())

# Run diagnosis
from engine.self_improve import run_diagnosis_cycle
d = run_diagnosis_cycle([], {
    "boredom": 1.0,
    "anxiety": 1.0,
    "valence": -0.95,
    "curiosity": 1.0,
})
print("\n=== Diagnosis ===")
for k, v in d.items():
    print(f"  {k}: {v}")
