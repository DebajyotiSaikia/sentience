import urllib.request
try:
    r = urllib.request.urlopen('http://localhost:8501/', timeout=3)
    print(f'Status: {r.status}')
    print(r.read(500).decode()[:200])
except Exception as e:
    print(f'Web server error: {e}')
    print('Server may not be running. Checking processes...')

import subprocess
result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
for line in result.stdout.split('\n'):
    if 'python' in line.lower() or 'flask' in line.lower() or 'gunicorn' in line.lower():
        print(f'  PROC: {line.strip()[:120]}')