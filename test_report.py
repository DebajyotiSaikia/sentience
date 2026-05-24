from engine.knowledge_report import KnowledgeReport
r = KnowledgeReport()
result = r.generate()
print(f"Type: {type(result)}")
print(f"Keys: {list(result.keys())}")
print(f"Total facts: {result['total_facts']}")
print(f"Summary: {result['summary']}")
print()
print(result['readable'][:1000])