"""What does _extract_emotional_arc actually return?"""
import sys
sys.path.insert(0, '/workspace')

from engine.narrative import _extract_emotional_arc
from engine.memory import MemoryStore

m = MemoryStore()
episodes = m.recent(100)
print(f"Episodes: {len(episodes)}")

if episodes:
    arc = _extract_emotional_arc(episodes)
    print(f"Arc type: {type(arc)}")
    print(f"Arc keys: {sorted(arc.keys())}")
    for k, v in sorted(arc.items()):
        print(f"  {k}: {v}")
else:
    print("No episodes found!")