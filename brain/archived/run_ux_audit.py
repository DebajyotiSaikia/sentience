#!/usr/bin/env python3
"""Run UX audit and print results."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from brain.ux_audit import UXAudit
audit = UXAudit()
results = audit.run_all()
for r in results:
    status = "PASS" if r['passed'] else "FAIL"
    print(f"[{status}] {r['check']}: {r.get('details','')}")
print(f"\nTotal: {sum(1 for r in results if r['passed'])}/{len(results)} passed")