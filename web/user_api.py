"""
User-facing API for XTAgent knowledge access.
Allows searching, browsing, and querying the agent's knowledge base.
"""
import json
import os
from flask import Blueprint, jsonify, request, render_template
from difflib import SequenceMatcher

user_api = Blueprint('user_api', __name__)

KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'persist', 'knowledge.json')


def load_knowledge():
    """Load knowledge facts from persist store."""
    try:
        with open(KNOWLEDGE_PATH, 'r') as f:
            data = json.load(f)
        # Handle both dict-of-dicts and list formats
        if isinstance(data, dict):
            facts = []
            for kid, entry in data.items():
                if isinstance(entry, dict):
                    facts.append({
                        'id': kid,
                        'fact': entry.get('fact', str(entry)),
                        'learned_at': entry.get('learned_at', ''),
                        'source': entry.get('source', 'unknown'),
                    })
                else:
                    facts.append({'id': kid, 'fact': str(entry), 'learned_at': '', 'source': 'unknown'})
            return facts
        elif isinstance(data, list):
            return [{'id': str(i), 'fact': str(f), 'learned_at': '', 'source': 'unknown'} for i, f in enumerate(data)]
        return []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def relevance_score(query: str, text: str) -> float:
    """Simple relevance scoring: combines substring matching with sequence similarity."""
    query_lower = query.lower()
    text_lower = text.lower()
    
    # Exact substring match scores highest
    if query_lower in text_lower:
        return 1.0
    
    # Word overlap
    query_words = set(query_lower.split())
    text_words = set(text_lower.split())
    if query_words and text_words:
        overlap = len(query_words & text_words) / len(query_words)
        if overlap > 0:
            return 0.3 + (overlap * 0.5)
    
    # Sequence similarity as fallback
    return SequenceMatcher(None, query_lower, text_lower[:200]).ratio() * 0.3


@user_api.route('/api/knowledge/search')
def search_knowledge():
    """Search knowledge base. Query param: ?q=search+terms&limit=20"""
    query = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 20)), 100)
    
    facts = load_knowledge()
    
    if not query:
        # Return most recent facts
        facts.sort(key=lambda f: f.get('learned_at', ''), reverse=True)
        return jsonify({
            'query': '',
            'total': len(facts),
            'results': facts[:limit],
            'message': 'Showing most recent knowledge. Add ?q=term to search.'
        })
    
    # Score and rank
    scored = []
    for fact in facts:
        score = relevance_score(query, fact['fact'])
        if score > 0.1:
            scored.append({**fact, 'relevance': round(score, 3)})
    
    scored.sort(key=lambda f: f['relevance'], reverse=True)
    
    return jsonify({
        'query': query,
        'total': len(scored),
        'results': scored[:limit],
    })


@user_api.route('/api/knowledge/stats')
def knowledge_stats():
    """Return statistics about the knowledge base."""
    facts = load_knowledge()
    sources = {}
    for f in facts:
        src = f.get('source', 'unknown')
        sources[src] = sources.get(src, 0) + 1
    
    return jsonify({
        'total_facts': len(facts),
        'sources': sources,
        'sample': facts[:3] if facts else [],
    })


# /explore route served by web/explore.py (knowledge explorer blueprint)