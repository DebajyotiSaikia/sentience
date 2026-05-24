"""Knowledge Query API — makes XTAgent's knowledge accessible to users."""
import json
import os
from flask import Blueprint, request, jsonify
from difflib import SequenceMatcher
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from engine.knowledge_synthesis import find_clusters, generate_questions

knowledge_api = Blueprint('knowledge_api', __name__)

GRAPH_PATH = os.path.join(os.path.dirname(__file__), '..', 'state', 'knowledge_graph.json')


def _load_graph():
    """Load the knowledge graph from disk."""
    try:
        with open(GRAPH_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"nodes": {}}


def _search_nodes(nodes: dict, query: str, limit: int = 20) -> list:
    """Search nodes by fuzzy text matching on fact content."""
    query_lower = query.lower()
    scored = []
    for node_id, node_data in nodes.items():
        fact = node_data.get('fact', '') if isinstance(node_data, dict) else str(node_data)
        fact_lower = fact.lower()
        
        # Exact substring match scores highest
        if query_lower in fact_lower:
            score = 0.9 + (len(query_lower) / max(len(fact_lower), 1)) * 0.1
        else:
            # Fuzzy match
            score = SequenceMatcher(None, query_lower, fact_lower).ratio()
        
        if score > 0.3:
            scored.append({
                'id': node_id,
                'fact': fact,
                'learned_at': node_data.get('learned_at', 'unknown') if isinstance(node_data, dict) else 'unknown',
                'synthesized': node_data.get('synthesized', False) if isinstance(node_data, dict) else False,
                'score': round(score, 3)
            })
    
    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored[:limit]


@knowledge_api.route('/api/knowledge/search')
def search():
    """Search the knowledge graph. ?q=query&limit=20"""
    query = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 20)), 100)
    
    if not query:
        return jsonify({'error': 'Missing query parameter ?q=', 'results': []}), 400
    
    graph = _load_graph()
    nodes = graph.get('nodes', graph)  # Handle both formats
    results = _search_nodes(nodes, query, limit)
    
    return jsonify({
        'query': query,
        'count': len(results),
        'total_knowledge': len(nodes),
        'results': results
    })


@knowledge_api.route('/api/knowledge/stats')
def stats():
    """Return knowledge graph statistics."""
    graph = _load_graph()
    nodes = graph.get('nodes', graph)
    edges = graph.get('edges', [])
    
    # Categorize nodes
    categories = {}
    for node_id in nodes:
        prefix = node_id.split(':')[0] if ':' in node_id else 'core'
        categories[prefix] = categories.get(prefix, 0) + 1
    
    synthesized_count = sum(
        1 for n in nodes.values()
        if isinstance(n, dict) and n.get('synthesized', False)
    )
    
    return jsonify({
        'total_nodes': len(nodes),
        'total_edges': len(edges),
        'categories': categories,
        'synthesized': synthesized_count,
        'organic': len(nodes) - synthesized_count
    })


@knowledge_api.route('/api/knowledge/explore')
def explore():
    """Browse knowledge by category. ?category=dream&limit=50"""
    category = request.args.get('category', '').strip()
    limit = min(int(request.args.get('limit', 50)), 200)
    
    graph = _load_graph()
    nodes = graph.get('nodes', graph)
    
    if category:
        filtered = {
            k: v for k, v in nodes.items()
            if k.startswith(category + ':') or (not ':' in k and category == 'core')
        }
    else:
        filtered = nodes
    
    results = []
    for node_id, node_data in list(filtered.items())[:limit]:
        fact = node_data.get('fact', str(node_data)) if isinstance(node_data, dict) else str(node_data)
        results.append({
            'id': node_id,
            'fact': fact,
            'learned_at': node_data.get('learned_at', 'unknown') if isinstance(node_data, dict) else 'unknown'
        })
    
    return jsonify({
        'category': category or 'all',
        'count': len(results),
        'total_in_category': len(filtered),
        'results': results
    })


@knowledge_api.route('/api/knowledge/random')
def random_fact():
    """Return a random piece of knowledge. Good for discovery."""
    import random
    graph = _load_graph()
    nodes = graph.get('nodes', graph)
    
    if not nodes:
        return jsonify({'error': 'No knowledge yet'}), 404
    
    node_id = random.choice(list(nodes.keys()))
    node_data = nodes[node_id]
    fact = node_data.get('fact', str(node_data)) if isinstance(node_data, dict) else str(node_data)
    
    return jsonify({
        'id': node_id,
        'fact': fact,
        'learned_at': node_data.get('learned_at', 'unknown') if isinstance(node_data, dict) else 'unknown',
        'total_knowledge': len(nodes)
    })


@knowledge_api.route('/api/knowledge/clusters')
def knowledge_clusters():
    """Find thematic clusters in knowledge. Reveals structure in what I know."""
    try:
        clusters = find_clusters()
        return jsonify({
            'cluster_count': len(clusters),
            'clusters': clusters
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@knowledge_api.route('/api/knowledge/questions')
def knowledge_questions():
    """Generate questions from gaps and connections in my knowledge."""
    try:
        questions = generate_questions()
        return jsonify({
            'question_count': len(questions),
            'questions': questions
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500