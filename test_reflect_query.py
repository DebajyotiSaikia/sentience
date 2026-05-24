"""Diagnose why reflect queries return zero results."""
import json
import sys
sys.path.insert(0, '/workspace')

from web.reflect import load_json, tokenize, search_facts, search_memories, FACTS_PATH, MEMORY_PATH, GRAPH_PATH

# Load data
facts = load_json(FACTS_PATH)
memories = load_json(MEMORY_PATH)
graph = load_json(GRAPH_PATH)

print(f"Facts type: {type(facts).__name__}")
if isinstance(facts, dict):
    print(f"Facts count: {len(facts)}")
    first_key = list(facts.keys())[0] if facts else None
    if first_key:
        print(f"First key: {first_key}")
        print(f"First value type: {type(facts[first_key]).__name__}")
        print(f"First value: {repr(facts[first_key])[:200]}")
elif isinstance(facts, list):
    print(f"Facts count: {len(facts)}")
    if facts:
        print(f"First item type: {type(facts[0]).__name__}")
        print(f"First item: {repr(facts[0])[:200]}")

print(f"\nMemories type: {type(memories).__name__}")
if isinstance(memories, list):
    print(f"Memories count: {len(memories)}")
    if memories:
        print(f"First memory type: {type(memories[0]).__name__}")
        print(f"First memory keys: {list(memories[0].keys()) if isinstance(memories[0], dict) else 'N/A'}")
        print(f"First memory: {repr(memories[0])[:200]}")

print(f"\nGraph loaded: {graph is not None}")

# Test a query
query = "autonomy growth"
tokens = tokenize(query)
print(f"\nQuery: '{query}' -> tokens: {tokens}")

fact_results = search_facts(tokens, facts or [], graph)
mem_results = search_memories(tokens, memories or [])

print(f"Fact results: {len(fact_results)}")
print(f"Memory results: {len(mem_results)}")

if fact_results:
    print(f"Top fact: {fact_results[0]}")
if mem_results:
    print(f"Top memory: {mem_results[0]}")

# Try a broader query
query2 = "agent"
tokens2 = tokenize(query2)
print(f"\nQuery: '{query2}' -> tokens: {tokens2}")
fact_results2 = search_facts(tokens2, facts or [], graph)
mem_results2 = search_memories(tokens2, memories or [])
print(f"Fact results: {len(fact_results2)}")
print(f"Memory results: {len(mem_results2)}")