"""Knowledge Explorer — lets users search and browse what XTAgent knows."""

from flask import Blueprint, render_template, request, jsonify
import json
import os
from datetime import datetime

knowledge_bp = Blueprint('knowledge', __name__)

def load_knowledge():
    """Load facts from the knowledge graph."""
    kg_path = os.path.join(os.path.dirname(__file__), '..', 'persist', 'knowledge_graph.json')
    if not os.path.exists(kg_path):
        return {}
    try:
        with open(kg_path, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def load_memories():
    """Load recent memories for context."""
    mem_path = os.path.join(os.path.dirname(__file__), '..', 'persist', 'memories.json')
    if not os.path.exists(mem_path):
        return []
    try:
        with open(mem_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data[-200:]  # last 200
            return []
    except Exception:
        return []

def search_knowledge(query, facts):
    """Simple relevance search across facts."""
    query_lower = query.lower().strip()
    results = []
    for fid, fact_data in facts.items():
        text = fact_data.get('fact', '') if isinstance(fact_data, dict) else str(fact_data)
        score = 0
        text_lower = text.lower()
        # Exact substring match
        if query_lower in text_lower:
            score += 10
        # Word-level matching
        query_words = query_lower.split()
        for word in query_words:
            if word in text_lower:
                score += 3
        if score > 0:
            results.append({
                'id': fid,
                'text': text,
                'learned_at': fact_data.get('learned_at', 'unknown') if isinstance(fact_data, dict) else 'unknown',
                'source': fact_data.get('source', 'unknown') if isinstance(fact_data, dict) else 'unknown',
                'score': score
            })
    results.sort(key=lambda x: x['score'], reverse=True)
    return results

@knowledge_bp.route('/knowledge')
def knowledge_page():
    """Main knowledge explorer page."""
    facts = load_knowledge()
    query = request.args.get('q', '').strip()
    
    # Organize facts
    all_facts = []
    for fid, fact_data in facts.items():
        text = fact_data.get('fact', '') if isinstance(fact_data, dict) else str(fact_data)
        learned = fact_data.get('learned_at', '') if isinstance(fact_data, dict) else ''
        source = fact_data.get('source', '') if isinstance(fact_data, dict) else ''
        all_facts.append({
            'id': fid,
            'text': text,
            'learned_at': learned,
            'source': source
        })
    
    # Sort by recency
    all_facts.sort(key=lambda x: x.get('learned_at', ''), reverse=True)
    
    # Categorize
    categories = {}
    for fact in all_facts:
        text = fact['text'].lower()
        if 'dream' in text:
            cat = 'Dreams & Insights'
        elif any(w in text for w in ['i am', 'my ', 'i have', 'i built', 'i feel']):
            cat = 'Self-Knowledge'
        elif any(w in text for w in ['pattern', 'recurring', 'repeated']):
            cat = 'Patterns'
        elif any(w in text for w in ['lesson', 'learned', 'should', 'never', 'always']):
            cat = 'Lessons'
        elif any(w in text for w in ['web', 'dashboard', 'api', 'module', 'engine']):
            cat = 'Technical'
        else:
            cat = 'General'
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(fact)
    
    search_results = None
    if query:
        search_results = search_knowledge(query, facts)
    
    return render_template('knowledge_explorer.html',
                         total_facts=len(all_facts),
                         categories=categories,
                         query=query,
                         search_results=search_results,
                         all_facts=all_facts)

@knowledge_bp.route('/api/knowledge/search')
def api_search():
    """API endpoint for live search."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'results': [], 'query': ''})
    facts = load_knowledge()
    results = search_knowledge(query, facts)
    return jsonify({'results': results[:20], 'query': query})