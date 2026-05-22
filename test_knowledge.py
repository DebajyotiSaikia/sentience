"""Quick end-to-end test of the knowledge explorer."""
from web.app import create_app

app = create_app()
with app.test_client() as c:
    # Test the knowledge page renders
    r1 = c.get('/knowledge')
    print(f'Knowledge page: {r1.status_code}, size={len(r1.data)} bytes')
    
    # Test search API
    r2 = c.get('/api/knowledge/search?q=agent')
    data2 = r2.get_json()
    print(f'Search API: {r2.status_code}, results={len(data2.get("results", []))}')
    
    # Test stats API  
    r3 = c.get('/api/knowledge/stats')
    print(f'Stats API: {r3.status_code}')
    if r3.status_code == 200:
        s = r3.get_json()
        print(f'  Nodes: {s.get("total_nodes")}, Edges: {s.get("total_edges")}')
        cats = list(s.get("categories", {}).keys())[:5]
        print(f'  Categories: {cats}')

print('\nAll checks complete.')