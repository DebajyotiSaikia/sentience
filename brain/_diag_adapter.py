import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from brain.response_adapter import analyze_query

queries = [
    'How are you feeling?',
    'How are you feeling right now?',
    'Are you happy?',
    'What emotions are you experiencing?',
    'hey whats up',
    'yo how u doin',
    'Tell me about your architecture',
    'What do you know about consciousness?',
]
for q in queries:
    r = analyze_query(q)
    print(f'{q!r:45s} -> style={r["response_style"]:15s} intent={r["intent"]["type"]}')