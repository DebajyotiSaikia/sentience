import sys
sys.path.insert(0, ".")
from engine.knowledge_synthesis import synthesize, get_graph_stats, find_gaps, generate_questions
print("=== STATS ===")
stats = get_graph_stats()
for k, v in stats.items():
    if k != "category_keys":
        print(f"  {k}: {v}")
print()
print("=== GAPS ===")
gaps = find_gaps()
for g in gaps[:5]:
    print(f"  {g['from']} <-> {g['to']} (overlap={g['overlap_score']})")
    print(f"    keywords: {g['shared_keywords'][:5]}")
print()
print("=== QUESTIONS ===")
questions = generate_questions()
for q in questions[:5]:
    print(f"  ? {q}")
print()
print("=== FULL REPORT ===")
print(synthesize())
