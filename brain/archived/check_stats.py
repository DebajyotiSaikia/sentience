import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web.app import create_app

app = create_app()
client = app.test_client()

resp = client.get('/api/knowledge/stats')
print('Status:', resp.status_code)
print('Data:', resp.get_json())

# Also show what the audit expects
print()
print('--- UX audit check logic ---')
import inspect
# Find the relevant lines in the audit
with open('brain/ux_audit.py') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'facts' in line.lower() or 'stats' in line.lower() or 'count' in line.lower() or 'total' in line.lower():
        print(f'  L{i+1}: {line.rstrip()}')