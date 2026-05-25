import sys
sys.path.insert(0, '.')
from web.briefing import get_completed_work

results = get_completed_work()
for r in results:
    status = r.get('status', '?')
    name = r.get('name', '?')
    print(f'{status:>10} | {name}')
print(f'\nTotal plans: {len(results)}')