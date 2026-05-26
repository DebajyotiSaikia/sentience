"""Run UX audit and print failures clearly."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.ux_audit import UXAudit

a = UXAudit()
r = a.run_full_audit()

print(f"SCORE: {r.get('score')} / {r.get('max_score')}")
print()

for f in r.get('failures', []):
    print(f"FAIL: {f}")
print()

for w in r.get('warnings', []):
    print(f"WARN: {w}")