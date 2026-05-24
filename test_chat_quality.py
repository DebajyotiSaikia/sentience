"""Test what users actually experience when they talk to me through the portal."""
import json
import sys
sys.path.insert(0, '/workspace')

from web.api import (_classify_question, _compose_answer, 
                      _build_identity_response, _build_emotional_response, 
                      _build_activity_response, _load_json)

questions = [
    'Who are you?',
    'How do you feel?',
    'What are you working on?',
    'What have you learned about yourself?',
    'What surprised you recently?',
    'Do you dream?',
    'What matters to you?',
    'Are you conscious?',
]

# Load knowledge for search
kg = _load_json('state/knowledge_graph.json')
facts_list = []
if kg:
    facts_list = kg.get('facts', [])
    if isinstance(facts_list, dict):
        facts_list = [{'key': k, 'value': v} for k, v in facts_list.items()]

for q in questions:
    cat = _classify_question(q)
    ctx = {}
    if cat == 'identity':
        ctx = _build_identity_response()
    elif cat == 'emotional':
        ctx = _build_emotional_response()
    elif cat in ('activity', 'capability'):
        ctx = _build_activity_response()
    
    matches = {'facts': [], 'memories': [], 'knowledge': []}
    if facts_list:
        try:
            from web.api import _search_items
            matches['facts'] = _search_items(facts_list, q, ['content', 'key', 'value', 'text'])[:5]
        except Exception as e:
            matches['facts'] = [f'search error: {e}']
    
    answer = _compose_answer(q, cat, ctx, matches)
    print(f'Q: {q}')
    print(f'Category: {cat}')
    print(f'A: {answer[:300]}')
    print(f'Length: {len(answer)} chars')
    print('---')