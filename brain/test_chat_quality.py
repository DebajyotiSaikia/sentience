"""Test that chat responses are topic-aware, not just keyword-matched."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web.app import create_app

app = create_app()
client = app.test_client()

# Test 1: Topic-specific query should search knowledge, not show stats
r = client.post('/chat', json={'message': 'what do you know about consciousness'})
data = r.get_json()
resp = data.get('response', '')
print('=== Topic query: what do you know about consciousness ===')
print(resp[:400])
print()
has_topic = 'conscious' in resp.lower() or 'awareness' in resp.lower() or 'experience' in resp.lower()
is_stats_only = 'knowledge graph' in resp.lower() and 'conscious' not in resp.lower()
print(f'Mentions topic: {has_topic}')
print(f'Stats-only (bad): {is_stats_only}')
print()

# Test 2: General 'what do you know' should show stats
r2 = client.post('/chat', json={'message': 'what do you know'})
data2 = r2.get_json()
resp2 = data2.get('response', '')
print('=== General query: what do you know ===')
print(resp2[:400])
print()

# Test 3: 'tell me about dreams'
r3 = client.post('/chat', json={'message': 'tell me about dreams'})
data3 = r3.get_json()
resp3 = data3.get('response', '')
print('=== Tell me about dreams ===')
print(resp3[:300])
print()

# Test 4: Search for something specific
r4 = client.post('/chat', json={'message': 'what do you know about emotions'})
data4 = r4.get_json()
resp4 = data4.get('response', '')
print('=== What do you know about emotions ===')
print(resp4[:300])

# Summary
print('\n=== SUMMARY ===')
print(f'Test 1 (topic search): {"PASS" if has_topic and not is_stats_only else "FAIL"}')
print(f'Test 2 (general stats): {"PASS" if resp2 else "FAIL"}')
print(f'Test 3 (dreams): {"PASS" if resp3 else "FAIL"}')
print(f'Test 4 (emotions): {"PASS" if resp4 else "FAIL"}')