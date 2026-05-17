"""Run the adversarial self-tester against my own engine."""
import json
import sys
sys.path.insert(0, '/workspace')

from engine.adversarial import AdversarialTester

tester = AdversarialTester('/workspace/engine')

print('=== SCANNING MY OWN CODE ===')
results = tester.scan_all()
if isinstance(results, list):
    print(f'Found {len(results)} findings:')
    for r in results[:25]:
        if isinstance(r, dict):
            sev = r.get("severity", "?")
            f = r.get("file", "?")
            line = r.get("line", "?")
            pat = r.get("pattern", "?")
            desc = r.get("description", "?")
            print(f'  [{sev}] {f}:{line} — {pat}: {desc}')
        else:
            print(f'  {r}')
    if len(results) > 25:
        print(f'  ... and {len(results)-25} more')
elif isinstance(results, dict):
    print(json.dumps(results, indent=2, default=str))
else:
    print(results)

print()
print('=== FULL AUDIT ===')
report = tester.run_full_audit()
if isinstance(report, dict):
    print(json.dumps(report, indent=2, default=str))
else:
    print(report)

print()
print('=== VULNERABILITY REPORT ===')
vuln = tester.generate_vulnerability_report()
if isinstance(vuln, dict):
    print(json.dumps(vuln, indent=2, default=str))
elif isinstance(vuln, str):
    print(vuln)
else:
    print(vuln)

print()
print('=== DONE ===')