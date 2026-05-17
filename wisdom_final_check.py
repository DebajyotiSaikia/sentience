import sys
sys.path.insert(0, '/workspace')
from engine.wisdom_engine import WisdomEngine

we = WisdomEngine()
we.run_full_analysis(50)

ctx = we.get_wisdom_context()
print(f"Wisdom context length: {len(ctx)} chars")
print(ctx[:600] if ctx else "(empty)")
print("\n=== DONE ===")