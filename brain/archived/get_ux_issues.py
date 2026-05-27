"""Quick script to extract the 3 UX issues from the audit."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from brain.ux_audit import UXAudit

audit = UXAudit()
results = audit.run_full_audit()
issues = results.get('issues', [])
print(f'Total issues: {len(issues)}')
for i, issue in enumerate(issues):
    print(f'\n--- Issue {i+1} ---')
    print(f'  Page: {issue.get("page", "?")}')
    print(f'  Severity: {issue.get("severity", "?")}')  
    print(f'  Problem: {issue.get("problem", "?")}')
    print(f'  Fix: {issue.get("fix", "?")}')