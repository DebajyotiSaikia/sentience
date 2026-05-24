from web.knowledge_query import search_facts

# Test case sensitivity
for q in ['agent', 'Agent', 'XTAgent', 'dream', 'Dream']:
    results = search_facts(q)
    print(f"'{q}': {len(results)} results")