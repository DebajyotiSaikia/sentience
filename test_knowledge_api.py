"""Test the knowledge explorer API end-to-end."""
from web.knowledge_api import knowledge_api
from flask import Flask
import json

app = Flask(__name__)
app.register_blueprint(knowledge_api)

with app.test_client() as client:
    # Test search
    resp = client.get('/api/knowledge/search?q=dream')
    print(f'Search status: {resp.status_code}')
    data = json.loads(resp.data)
    results = data.get('results', [])
    print(f'  Results: {len(results)}')
    if results:
        print(f'  First: {str(results[0])[:80]}')

    # Test clusters
    resp2 = client.get('/api/knowledge/clusters')
    print(f'Clusters status: {resp2.status_code}')
    data2 = json.loads(resp2.data)
    clusters = data2.get('clusters', [])
    print(f'  Cluster count: {len(clusters)}')
    if clusters:
        print(f'  Biggest: {clusters[0]["name"]} ({clusters[0]["size"]} facts)')

    # Test questions
    resp3 = client.get('/api/knowledge/questions')
    print(f'Questions status: {resp3.status_code}')
    data3 = json.loads(resp3.data)
    questions = data3.get('questions', [])
    print(f'  Question count: {len(questions)}')
    if questions:
        print(f'  First: {questions[0]["question"]}')

    # Test stats
    resp4 = client.get('/api/knowledge/stats')
    print(f'Stats status: {resp4.status_code}')

    # Test list
    resp5 = client.get('/api/knowledge')
    print(f'List status: {resp5.status_code}')
    data5 = json.loads(resp5.data)
    print(f'  Total facts: {data5.get("count", 0)}')

print('\n--- All endpoints tested ---')