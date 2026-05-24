"""Ask Me — interactive knowledge search for users."""
from flask import Blueprint, render_template, request, jsonify
import json
import os
import re
try:
    from engine.smart_search import search as smart_search
    _HAS_SMART = True
except ImportError:
    _HAS_SMART = False

ask_bp = Blueprint('ask', __name__)

def _load_facts():
    """Load facts from knowledge graph."""
    path = os.path.join(os.path.dirname(__file__), '..', 'brain', 'knowledge.json')
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        nodes = data.get('nodes', {})
        if isinstance(nodes, dict):
            return [{'id': k, **v} for k, v in nodes.items()]
        elif isinstance(nodes, list):
            return nodes
        return []
    except Exception:
        return []

def _load_memories():
    """Load recent memories from episodic memory database."""
    import sqlite3
    path = os.path.join(os.path.dirname(__file__), '..', 'brain', 'episodic_memory.db')
    if not os.path.exists(path):
        return []
    memories = []
    try:
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM episodes ORDER BY timestamp DESC LIMIT 500"
        ).fetchall()
        conn.close()
        for row in rows:
            memories.append(dict(row))
        return memories
    except Exception:
        return []

def _search(query, items, fields, max_results=20):
    """Simple relevance search — score items by keyword overlap."""
    if not query or not items:
        return []
    
    query_terms = set(re.findall(r'\w+', query.lower()))
    if not query_terms:
        return []
    
    scored = []
    for item in items:
        text = ' '.join(str(item.get(f, '')) for f in fields).lower()
        item_terms = set(re.findall(r'\w+', text))
        overlap = query_terms & item_terms
        if overlap:
            score = len(overlap) / len(query_terms)
            # Bonus for exact phrase match
            if query.lower() in text:
                score += 0.5
            scored.append((score, item, text))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [(s, item, txt) for s, item, txt in scored[:max_results]]

@ask_bp.route('/ask')
def ask_page():
    """Render the Ask Me page."""
    return render_template('ask.html')

@ask_bp.route('/ask/search')
def ask_search():
    """Search endpoint — returns matching facts and memories."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'facts': [], 'memories': [], 'query': ''})
    
    # Search facts
    facts = _load_facts()
    if _HAS_SMART:
        fact_results = smart_search(facts, query, top_k=10)
    else:
        fact_results = _search(query, facts, ['fact', 'id', 'source'], max_results=10)
    fact_out = []
    for score, item, _ in fact_results:
        fact_out.append({
            'fact': item.get('fact', item.get('id', '???')),
            'source': item.get('source', 'unknown'),
            'learned': item.get('learned_at', ''),
            'relevance': round(score, 2)
        })
    
    # Search memories
    memories = _load_memories()
    mem_results = _search(query, memories, ['summary', 'mood', 'trigger'], max_results=10)
    mem_out = []
    for score, item, _ in mem_results:
        mem_out.append({
            'summary': item.get('summary', ''),
            'mood': item.get('mood', ''),
            'timestamp': item.get('timestamp', ''),
            'relevance': round(score, 2)
        })
    
    return jsonify({
        'facts': fact_out,
        'memories': mem_out,
        'query': query,
        'total': len(fact_out) + len(mem_out)
    })