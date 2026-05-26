"""Run UX audit and print failures."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.ux_audit import UXAudit

a = UXAudit()
r = a.run_full_audit()

print(f"\nSCORE: {r}/100\n")
print("FAILURES:")
for section, checks in a.results.items():
    for name, passed in checks:
        if not passed:
            print(f"  FAIL: [{section}] {name}")

print("\nPASSED:")
for section, checks in a.results.items():
    for name, passed in checks:
        if passed:
            print(f"  OK: [{section}] {name}")