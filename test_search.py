from web.ask import create_ask_blueprint

bp = create_ask_blueprint(agent=None)
search = bp.search

# Show what data we loaded
facts = bp.view_functions  # can't access _get_facts directly, use search instead

# Test multiple queries - some should definitely match
queries = ['XTAgent', 'autonomy', 'autonomous', 'heartbeat', 'knowledge', 'dream', 'memory']
for q in queries:
    r = search(q)
    facts_count = r.get('total_searched', 0)
    matched = r.get('matched', 0)
    print(f'Query "{q}": {matched}/{facts_count} matched')
    if matched > 0:
        print(f'  Top result: {r["results"][0][:100]}')
    print()