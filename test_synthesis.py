"""Quick test of the knowledge synthesis engine."""
import sys
sys.path.insert(0, '.')

from engine.knowledge_synthesis import synthesize, get_graph_stats, find_gaps, generate_questions

print("=== Testing Knowledge Synthesis ===")
print()

stats = get_graph_stats()
print(f"Graph stats: {stats}")
print()

gaps = find_gaps()
print(f"Gaps found: {len(gaps)}")
for g in gaps[:3]:
    print(f"  {g['from']} <-> {g['to']} (shared: {g['shared_keywords'][:5]})")
print()

questions = generate_questions()
print(f"Questions generated: {len(questions)}")
for q in questions[:5]:
    print(f"  * {q}")
print()

print("=== Full Synthesis Report ===")
print(synthesize())
