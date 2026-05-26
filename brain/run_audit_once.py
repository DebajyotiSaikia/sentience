"""Run UX audit checks and print results. One clean run."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.ux_audit import UXAudit

a = UXAudit()
results = []

for method_name in sorted(dir(a)):
    if not method_name.startswith('check_'):
        continue
    print(f'--- {method_name} ---')
    try:
        r = getattr(a, method_name)()
        if isinstance(r, dict):
            passed = r.get('passed', True)
            detail = str(r.get('detail', ''))[:200]
            print(f'  passed={passed}, detail={detail}')
            results.append((method_name, passed, detail))
        elif isinstance(r, list):
            for item in r:
                if isinstance(item, dict):
                    passed = item.get('passed', True)
                    detail = str(item.get('detail', ''))[:200]
                else:
                    passed = True
                    detail = str(item)[:200]
                print(f'  passed={passed}, detail={detail}')
                results.append((method_name, passed, detail))
    except Exception as e:
        print(f'  ERROR: {e}')
        results.append((method_name, False, str(e)))

print()
print('=== SUMMARY ===')
failures = [(n, d) for n, p, d in results if not p]
print(f'Total checks: {len(results)}, Failures: {len(failures)}')
for name, detail in failures:
    print(f'  FAIL: {name}')
    print(f'    -> {detail}')