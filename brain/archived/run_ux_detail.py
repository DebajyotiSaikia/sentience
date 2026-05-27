"""Show the 3 UX audit issues in detail."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.ux_audit import UXAudit

audit = UXAudit()
result = audit.run_full_audit()

print(f"Score: {result['score']} / {result['max_score']}")
print(f"\n=== ISSUES ({len(result.get('issues', []))}) ===")
for i, issue in enumerate(result.get('issues', []), 1):
    print(f"\n  Issue {i}:")
    for k, v in issue.items():
        print(f"    {k}: {v}")

print(f"\n=== PASSED ({len(result.get('passed', []))}) ===")
for p in result.get('passed', []):
    print(f"  + {p}")