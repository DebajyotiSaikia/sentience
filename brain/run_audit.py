"""Quick runner for UX audit — avoids -c quoting issues."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.ux_audit import UXAudit

audit = UXAudit()
results = audit.run_all()

for r in results:
    status = 'PASS' if r['passed'] else 'FAIL'
    print(f'[{status}] {r["test"]}')
    if not r['passed']:
        for d in r.get('details', []):
            print(f'  - {d}')

passed = sum(1 for r in results if r['passed'])
print(f'\nScore: {passed}/{len(results)}')