"""Diagnose the exact mismatch between knowledge stats API and UX audit expectations."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
c = app.test_client()

# Get exact stats response
r = c.get('/api/knowledge/stats')
print(f"Status: {r.status_code}")
raw = r.get_data(as_text=True)
print(f"Raw response:\n{raw}\n")

try:
    data = json.loads(raw)
    print("Fields and values:")
    for k, v in data.items():
        val_preview = str(v)[:100] if not isinstance(v, (int, float, bool)) else v
        print(f"  {k}: {val_preview}")
    
    # Check common field names the audit might use
    for key in ['facts', 'total_facts', 'total', 'count', 'num_facts', 'fact_count']:
        val = data.get(key, 'MISSING')
        print(f"  data['{key}'] = {val}")
except json.JSONDecodeError:
    print("Response is not valid JSON!")

# Now check what the audit actually checks
print("\n--- Checking UX audit source for 'facts' checks ---")
audit_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'brain', 'ux_audit.py')
with open(audit_path) as f:
    for i, line in enumerate(f, 1):
        if 'facts' in line.lower() and ('stats' in line.lower() or 'has_facts' in line.lower() or 'total' in line.lower() or 'check' in line.lower()):
            print(f"  L{i}: {line.rstrip()}")