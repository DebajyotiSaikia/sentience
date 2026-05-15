import sys
sys.path.insert(0, r"C:\code\sentience")
from engine.self_improve import run_diagnosis_cycle
r = run_diagnosis_cycle([], {"boredom": 0.84, "anxiety": 0.0, "valence": -0.37})
print("STATUS:", r["status"])
print("MESSAGE:", r["message"])
for p in r.get("proposals", []):
    print("PROPOSAL:", p.get("title", "?"))
print("DONE")
