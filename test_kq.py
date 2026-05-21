"""Quick smoke test for knowledge_query module."""
from engine.knowledge_query import KnowledgeQuery

kq = KnowledgeQuery()

# Just see what query() actually returns
result = kq.query("What have I learned from my mistakes?")
print(f"Result keys: {list(result.keys())}")
print(f"Full result: {result}")