import sys; sys.path.insert(0, '/workspace')
from brain.self_narrative import build_self_narrative
result = build_self_narrative()
print(f'Length: {len(result)}')
print('---')
print(result[:1200])