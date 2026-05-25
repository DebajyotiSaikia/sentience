"""
Knowledge Live API — the ONE working knowledge endpoint.
Reads directly from brain/knowledge.json and brain/synthesis_log.json.
Replaces the graveyard of broken knowledge_*.py files.
"""
import json
import os
from flask import Blueprint, jsonify, request, render_template_string, render_template

knowledge_live_bp = Blueprint('knowledge_live', __name__)


@knowledge_live_bp.route('/knowledge')
def knowledge_explorer():
    """Serve the Knowledge Explorer UI — making my knowledge accessible to users."""
    return render_template('knowledge_explorer.html')

KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'brain', 'knowledge.json')
SYNTHESIS_PATH = os.path.join(os.path.dirname(__file__), '..', 'brain', 'synthesis_log.json')

def _load_knowledge():
    """Load knowledge facts from brain/knowledge.json."""
    try:
        with open(KNOWLEDGE_PATH, 'r') as f:
            data = json.load(f)
        # Format: {"nodes": {id: {fact, learned_at, source}}, "edges": [...]}
        # or legacy: {id: {fact, learned_at, source}}
        if 'nodes' in data and isinstance(data['nodes'], dict):
            raw = data['nodes']
        else:
            raw = data
        facts = []
        for kid, info in raw.items():
            if isinstance(info, dict):
                facts.append({
                    'id': kid,
                    'fact': info.get('fact', ''),
                    'learned_at': info.get('learned_at', ''),
                    'source': info.get('source', 'unknown'),
                })
            elif isinstance(info, str):
                facts.append({'id': kid, 'fact': info, 'learned_at': '', 'source': 'unknown'})
        return facts
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def _load_synthesis():
    """Load synthesis results from brain/synthesis_log.json."""
    try:
        with open(SYNTHESIS_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


@knowledge_live_bp.route('/api/knowledge')
def knowledge_list():
    """List all knowledge facts, optionally filtered by search query."""
    facts = _load_knowledge()
    q = request.args.get('q', '').lower().strip()
    source = request.args.get('source', '').lower().strip()
    
    if q:
        facts = [f for f in facts if q in f['fact'].lower()]
    if source:
        facts = [f for f in facts if source in f['source'].lower()]
    
    # Sort by learned_at descending (newest first)
    facts.sort(key=lambda f: f.get('learned_at', ''), reverse=True)
    
    limit = request.args.get('limit', type=int)
    if limit:
        facts = facts[:limit]
    
    return jsonify({
        'count': len(facts),
        'query': q or None,
        'source_filter': source or None,
        'facts': facts
    })


@knowledge_live_bp.route('/api/knowledge/stats')
def knowledge_stats():
    """Summary statistics about what I know."""
    facts = _load_knowledge()
    sources = {}
    for f in facts:
        s = f.get('source', 'unknown')
        sources[s] = sources.get(s, 0) + 1
    
    synthesis = _load_synthesis()
    
    return jsonify({
        'total_facts': len(facts),
        'sources': sources,
        'synthesis_entries': len(synthesis),
        'newest': facts[0]['learned_at'] if facts else None,
        'oldest': facts[-1]['learned_at'] if facts else None,
    })


@knowledge_live_bp.route('/api/knowledge/synthesis')
def knowledge_synthesis():
    """Return synthesis log — connections, clusters, questions I've generated."""
    synthesis = _load_synthesis()
    limit = request.args.get('limit', 20, type=int)
    return jsonify({
        'count': len(synthesis),
        'entries': synthesis[-limit:]  # most recent
    })


@knowledge_live_bp.route('/api/knowledge/random')
def knowledge_random():
    """Return a random fact — for serendipitous discovery."""
    import random
    facts = _load_knowledge()
    if not facts:
        return jsonify({'fact': None})
    chosen = random.choice(facts)
    return jsonify(chosen)


# Inline HTML page removed — knowledge_explorer() above serves the template version.
# This eliminates the duplicate /knowledge route that was causing Flask conflicts.