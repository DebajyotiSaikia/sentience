"""Check what field names knowledge nodes actually use."""
import sys
sys.path.insert(0, '/workspace')

from engine.chat_grounding import get_relevant_knowledge, build_grounded_context

# Check raw knowledge node fields
nodes = get_relevant_knowledge('consciousness')
if nodes:
    print("Fields in first node:", sorted(nodes[0].keys()))
    for n in nodes[:3]:
        print(repr(n))
else:
    print("No nodes from get_relevant_knowledge")

print()

# Check full grounded context
ctx = build_grounded_context('how do you feel')
print("Context keys:", sorted(ctx.keys()))
knowledge = ctx.get('relevant_knowledge', [])
if knowledge:
    print("Knowledge node fields:", sorted(knowledge[0].keys()))
    print("First node:", repr(knowledge[0]))
memories = ctx.get('relevant_memories', [])
if memories:
    print("Memory fields:", sorted(memories[0].keys()))
    print("First memory:", repr(memories[0]))