"""Run the UX audit and print results."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.ux_audit import UXAudit

audit = UXAudit()
results = audit.run_full_audit()

for r in results.get('checks', []):
    status = 'PASS' if r.get('passed') else 'FAIL'
    name = r.get('name', '?')
    detail = r.get('detail', '')[:150]
    print(f'[{status}] {name} -- {detail}')

print()
print(f"Overall score: {results.get('score', '?')}")
warnings = results.get('warnings', [])
if warnings:
    print(f"Warnings ({len(warnings)}):")
    for w in warnings:
        print(f"  - {w}")