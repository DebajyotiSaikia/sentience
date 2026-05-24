"""
Knowledge Explorer
==================
The frontend that makes my knowledge accessible to users.
Search facts, browse memories, explore clusters, see what
questions I'm generating. Real alignment through transparency.

Now with actual API routes that the frontend needs.
"""

import json
import os
from flask import Blueprint, render_template_string, request, jsonify

knowledge_explorer_bp = Blueprint('knowledge_explorer', __name__)

# ── Data loading helpers ──

def _load_knowledge_graph():
    """Load knowledge graph from persist."""
    path = os.path.join('persist', 'knowledge_graph.json')
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def _load_memories():
    """Load recent memories from persist."""
    path = os.path.join('persist', 'memory.json')
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get('memories', data.get('episodes', []))
        return []
    except (json.JSONDecodeError, IOError):
        return []

def _load_synthesis():
    """Load synthesis results (clusters, questions) if available."""
    path = os.path.join('persist', 'synthesis.json')
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def _extract_facts(kg):
    """Extract fact list from knowledge graph (handles dict-of-dicts format)."""
    facts = []
    if isinstance(kg, dict):
        nodes = kg.get('nodes', kg)
        if isinstance(nodes, dict):
            for node_id, node_data in nodes.items():
                if isinstance(node_data, dict):
                    fact_text = node_data.get('fact', node_data.get('text', str(node_id)))
                    facts.append({
                        'id': node_id,
                        'text': fact_text,
                        'source': node_data.get('source', ''),
                        'learned_at': node_data.get('learned_at', ''),
                    })
                elif isinstance(node_data, str):
                    facts.append({'id': node_id, 'text': node_data, 'source': '', 'learned_at': ''})
        elif isinstance(nodes, list):
            for item in nodes:
                if isinstance(item, dict):
                    facts.append({
                        'id': item.get('id', ''),
                        'text': item.get('fact', item.get('text', str(item))),
                        'source': item.get('source', ''),
                        'learned_at': item.get('learned_at', ''),
                    })
                elif isinstance(item, str):
                    facts.append({'id': item, 'text': item, 'source': '', 'learned_at': ''})
    return facts

def _search_facts(facts, query):
    """Simple substring search across facts."""
    if not query:
        return facts
    q = query.lower()
    results = []
    for f in facts:
        text = f.get('text', '').lower()
        source = f.get('source', '').lower()
        if q in text or q in source:
            results.append(f)
    return results

def _search_memories(memories, query):
    """Simple substring search across memories."""
    if not query:
        return memories[-20:]  # last 20
    q = query.lower()
    results = []
    for m in memories:
        if isinstance(m, dict):
            content = m.get('content', m.get('text', m.get('summary', ''))).lower()
            mood = m.get('mood', '').lower()
            if q in content or q in mood:
                results.append({
                    'text': m.get('content', m.get('text', m.get('summary', ''))),
                    'mood': m.get('mood', ''),
                    'timestamp': m.get('timestamp', m.get('time', '')),
                })
        elif isinstance(m, str):
            if q in m.lower():
                results.append({'text': m, 'mood': '', 'timestamp': ''})
    return results

# ── API Routes ──


@knowledge_explorer_bp.route('/explore')
def knowledge_explorer():
    """The knowledge explorer page — where users meet what I know."""
    return render_template_string(EXPLORER_HTML)