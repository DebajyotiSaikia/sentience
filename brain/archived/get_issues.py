import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from brain.ux_audit import UXAudit
audit = UXAudit()
r = audit.run_full_audit()
for i, issue in enumerate(r.get('issues', []), 1):
    print(f"{i}. {issue}")
print(f"\nScore: {r.get('score', '?')}/100")