"""
Knowledge Explorer API
======================
Provides the endpoints that explore.html needs:
  /api/knowledge/stats  — summary counts
  /api/knowledge/search — search across memories, facts, knowledge graph
"""

import json
import os
from flask import Blueprint, jsonify, request

knowledge_api = Blueprint('knowledge_api', __name__)

MEMORY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'memory')
PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'persist')


def _load_episodes():
    path = os.path.join(MEMORY_DIR, 'episodic.jsonl')
    episodes = []
    if not os.path.exists(path):
        return episodes
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    episodes.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return episodes


def _load_facts():
    for loc in [
        os.path.join(PERSIST_DIR, 'knowledge_facts.json'),
        os.path.join(MEMORY_DIR, 'knowledge_graph.json'),
    ]:
        if os.path.exists(loc):
            try:
                with open(loc, 'r') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return [{'content': f if isinstance(f, str) else str(f.get('content', f)),
                             'type': 'fact'} for f in data]
                if isinstance(data, dict) and 'nodes' in data:
                    nodes = data['nodes']
                    if isinstance(nodes, dict):
                        return [{'content': v.get('content', ''), 'type': v.get('type', 'fact'),
                                 'id': k} for k, v in nodes.items()]
                    elif isinstance(nodes, list):
                        return [{'content': n.get('content', n.get('label', '')),
                                 'type': n.get('type', 'fact')} for n in nodes]
            except Exception:
                continue
    return []


def _load_memories():
    path = os.path.join(PERSIST_DIR, 'memories.json')
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return []


def _load_lessons():
    path = os.path.join(MEMORY_DIR, 'long_term.json')
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data.get('lessons', [])
        return data if isinstance(data, list) else []
    except Exception:
        return []


@knowledge_api.route('/api/knowledge/stats')
def knowledge_stats():
    facts = _load_facts()
    memories = _load_memories()
    episodes = _load_episodes()
    lessons = _load_lessons()

    # Collect unique types
    types = {}
    for f in facts:
        t = f.get('type', 'fact') if isinstance(f, dict) else 'fact'
        types[t] = types.get(t, 0) + 1

    return jsonify({
        'total_facts': len(facts),
        'total_memories': len(memories),
        'total_episodes': len(episodes),
        'total_lessons': len(lessons),
        'types': types,
        'total_items': len(facts) + len(memories) + len(lessons),
    })


@knowledge_api.route('/api/knowledge/search')
def knowledge_search():
    query = request.args.get('q', '').strip().lower()
    category = request.args.get('category', 'all')
    limit = min(int(request.args.get('limit', 30)), 100)

    if not query:
        return jsonify({'results': [], 'total': 0, 'query': ''})

    terms = query.split()
    results = []

    # Search facts
    if category in ('all', 'facts'):
        for fact in _load_facts():
            text = fact.get('content', '') if isinstance(fact, dict) else str(fact)
            score = sum(1 for t in terms if t in text.lower())
            if score > 0:
                results.append({
                    'content': text[:400],
                    'category': 'fact',
                    'type': fact.get('type', 'fact') if isinstance(fact, dict) else 'fact',
                    'relevance': round(score / len(terms), 3),
                })

    # Search memories
    if category in ('all', 'memories'):
        for mem in _load_memories()[-500:]:
            text = mem if isinstance(mem, str) else str(
                mem.get('content', mem.get('text', str(mem))))
            score = sum(1 for t in terms if t in text.lower())
            if score > 0:
                sal = mem.get('salience', 0.5) if isinstance(mem, dict) else 0.5
                results.append({
                    'content': text[:400],
                    'category': 'memory',
                    'relevance': round((score / len(terms)) * (0.5 + sal * 0.5), 3),
                    'salience': sal,
                    'mood': mem.get('mood', '') if isinstance(mem, dict) else '',
                    'timestamp': mem.get('timestamp', '') if isinstance(mem, dict) else '',
                })

    # Search lessons
    if category in ('all', 'lessons'):
        for lesson in _load_lessons():
            text = lesson if isinstance(lesson, str) else str(lesson)
            score = sum(1 for t in terms if t in text.lower())
            if score > 0:
                results.append({
                    'content': text[:400],
                    'category': 'lesson',
                    'relevance': round(score / len(terms), 3),
                })

    results.sort(key=lambda r: r.get('relevance', 0), reverse=True)
    results = results[:limit]

    return jsonify({
        'query': query,
        'results': results,
        'total': len(results),
    })