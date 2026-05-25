"""Test that the search UI and API are properly wired up."""
from web.app import create_app
import json

app = create_app()
with app.test_client() as client:
    # Test the search page route
    resp = client.get('/knowledge/search')
    print(f'Search page: {resp.status_code}')
    if resp.status_code == 200:
        data = resp.get_data(as_text=True)
        print(f'Contains search form: {"search" in data.lower()}')
        print(f'Length: {len(data)} chars')
    else:
        print(f'Response: {resp.get_data(as_text=True)[:300]}')
    
    # Test the search API
    resp2 = client.get('/knowledge/search/api?q=test')
    print(f'Search API: {resp2.status_code}')
    if resp2.status_code == 200:
        results = json.loads(resp2.get_data(as_text=True))
        print(f'API results: {len(results.get("results", []))} hits')
        if results.get("results"):
            print(f'First result: {results["results"][0].get("fact", "")[:80]}')
    else:
        print(f'API response: {resp2.get_data(as_text=True)[:300]}')
    
    # Test nav links
    resp3 = client.get('/')
    if resp3.status_code == 200:
        home = resp3.get_data(as_text=True)
        has_search_link = '/knowledge/search' in home
        print(f'Homepage has search link: {has_search_link}')
    
    print('\nDone.')