"""Diagnostic: run UX audit and show only failures."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.ux_audit import UXAudit

audit = UXAudit()
results = audit.run_full_audit()

print("=== UX AUDIT RESULTS ===")
failures = []
for r in results:
    passed = r.get('passed', True)
    if not passed:
        failures.append(r)
        
print(f"Score: {len(results) - len(failures)}/{len(results)}")
print(f"\n--- FAILURES ({len(failures)}) ---")
for f in failures:
    print(f"\n  TEST: {f.get('test', '?')}")
    for k, v in f.items():
        if k != 'test':
            print(f"    {k}: {v}")