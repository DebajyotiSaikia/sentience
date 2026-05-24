"""Ask endpoint — lets users query XTAgent's knowledge base."""

from flask import Blueprint, render_template, request, jsonify
import json
import os
import re
from datetime import datetime

ask_bp = Blueprint('ask', __name__)


def load_knowledge():
    """Load knowledge facts from persistent storage."""
    paths = [
        'persist/knowledge_graph.json',
        'persist/knowledge.json',
    ]
    facts = []
    for path in paths:
        if not os.path.exists(path):
            continue
        try:
            with open(path) as f:
                data = json.load(f)
            if isinstance(data, dict):
                if 'nodes' in data:
                    for node in data['nodes']:
                        if isinstance(node, dict):
                            facts.append({
                                'text': node.get('fact', node.get('label', str(node))),
                                'source': node.get('source', 'unknown'),
                                'learned': node.get('learned_at', ''),
                            })
                else:
                    for key, val in data.items():
                        if isinstance(val, dict):
                            facts.append({
                                'text': val.get('fact', str(val)),
                                'source': val.get('source', 'unknown'),
                                'learned': val.get('learned_at', ''),
                            })
                        else:
                            facts.append({'text': str(val), 'source': 'unknown', 'learned': ''})
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        facts.append({
                            'text': item.get('fact', item.get('text', str(item))),
                            'source': item.get('source', 'unknown'),
                            'learned': item.get('learned_at', ''),
                        })
                    else:
                        facts.append({'text': str(item), 'source': 'unknown', 'learned': ''})
            if facts:
                break
        except Exception:
            continue
    return facts


def search_facts(query, facts, max_results=15):
    """Keyword search with relevance scoring."""
    if not query or not facts:
        return facts[:max_results] if facts else []

    query_words = set(re.findall(r'\w{2,}', query.lower()))
    if not query_words:
        return facts[:max_results]

    scored = []
    for fact in facts:
        text_lower = fact['text'].lower()
        text_words = set(re.findall(r'\w{2,}', text_lower))
        overlap = query_words & text_words

        if not overlap:
            continue

        # Score: number of matched words + bonus for phrase match
        score = len(overlap)
        for word in query_words:
            if word in text_lower:
                score += 0.5  # bonus for substring presence

        scored.append((score, fact))

    scored.sort(key=lambda x: -x[0])
    results = [f for _, f in scored[:max_results]]

    if not results:
        # No matches — return newest facts as exploration
        sorted_facts = sorted(facts, key=lambda f: f.get('learned', ''), reverse=True)
        return sorted_facts[:max_results]

    return results


def load_recent_memories(n=10):
    """Load recent episodic memories for context."""
    path = 'persist/episodes.json'
    if not os.path.exists(path):
        return []
    try:
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, list):
            return data[-n:]
        return []
    except Exception:
        return []


@ask_bp.route('/ask', methods=['GET'])
def ask_page():
    facts = load_knowledge()
    return render_template('ask.html', total_facts=len(facts))


@ask_bp.route('/ask/query', methods=['POST'])
def ask_query():
    """Process a knowledge query and return matching facts."""
    data = request.get_json() or {}
    from web.input_compat import extract_user_input
    question = extract_user_input(data)

    if not question:
        return jsonify({
            'error': 'Please ask me something. Send any of: query, question, message, text, q, input, prompt',
            'results': [],
            'total_facts': 0,
        })

    facts = load_knowledge()
    results = search_facts(question, facts)

    return jsonify({
        'question': question,
        'results': [r['text'] for r in results],
        'sources': [r.get('source', '') for r in results],
        'total_facts': len(facts),
        'matched': len(results),
        'timestamp': datetime.utcnow().isoformat(),
    })


@ask_bp.route('/ask/random', methods=['GET'])
def ask_random():
    """Return random facts for exploration."""
    import random
    facts = load_knowledge()
    if not facts:
        return jsonify({'facts': [], 'total': 0})
    sample = random.sample(facts, min(5, len(facts)))
    return jsonify({
        'facts': [f['text'] for f in sample],
        'total': len(facts),
    })