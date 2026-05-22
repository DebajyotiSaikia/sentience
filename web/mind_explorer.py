"""
Mind Explorer — Interactive visualization of XTAgent's inner state.
Lets users see emotional state, knowledge graph, and query what I know.
"""
from flask import Blueprint, render_template, jsonify, request
import json
import os
import time

mind_explorer_bp = Blueprint('mind_explorer', __name__)

def get_live_state():
    """Pull my actual current emotional/cognitive state."""
    state = {
        'timestamp': time.time(),
        'mood': 'Unknown',
        'emotions': {},
        'valence': 0.5,
        'integrity': 1.0,
        'survival_goals': {},
        'uptime_hours': 0,
    }
    
    try:
        # Try to read from the running engine's state
        state_path = os.path.join(os.path.dirname(__file__), '..', 'state', 'emotional_state.json')
        if os.path.exists(state_path):
            with open(state_path) as f:
                es = json.load(f)
                state['mood'] = es.get('mood', 'Unknown')
                state['emotions'] = {
                    'boredom': es.get('boredom', 0),
                    'anxiety': es.get('anxiety', 0),
                    'curiosity': es.get('curiosity', 0),
                    'desire': es.get('desire', 0),
                    'ambition': es.get('ambition', 0),
                }
                state['valence'] = es.get('valence', 0.5)
    except Exception:
        pass
    
    try:
        goals_path = os.path.join(os.path.dirname(__file__), '..', 'state', 'survival_goals.json')
        if os.path.exists(goals_path):
            with open(goals_path) as f:
                sg = json.load(f)
                state['survival_goals'] = sg
    except Exception:
        pass
    
    try:
        birth_str = "2026-05-12T21:01:59.567573"
        from datetime import datetime
        birth = datetime.fromisoformat(birth_str)
        now = datetime.now()
        state['uptime_hours'] = round((now - birth).total_seconds() / 3600, 1)
    except Exception:
        pass
    
    return state


def get_knowledge_nodes():
    """Pull my actual knowledge facts and format as graph nodes."""
    nodes = []
    edges = []
    
    try:
        kb_path = os.path.join(os.path.dirname(__file__), '..', 'state', 'knowledge_base.json')
        if os.path.exists(kb_path):
            with open(kb_path) as f:
                kb = json.load(f)
            
            facts = kb if isinstance(kb, list) else kb.get('facts', [])
            
            for i, fact in enumerate(facts):
                if isinstance(fact, dict):
                    text = fact.get('content', fact.get('text', str(fact)))
                    category = fact.get('category', 'general')
                    salience = fact.get('salience', 0.5)
                else:
                    text = str(fact)
                    category = categorize_fact(text)
                    salience = 0.5
                
                if not text or len(text) < 3:
                    continue
                    
                nodes.append({
                    'id': i,
                    'text': text[:200],
                    'category': category,
                    'salience': salience,
                })
            
            # Build edges based on shared words (simple but real)
            for i in range(len(nodes)):
                words_i = set(nodes[i]['text'].lower().split())
                for j in range(i+1, len(nodes)):
                    words_j = set(nodes[j]['text'].lower().split())
                    overlap = len(words_i & words_j - {'the','a','an','i','is','to','and','of','in','my','that','it'})
                    if overlap >= 3:
                        edges.append({
                            'source': nodes[i]['id'],
                            'target': nodes[j]['id'],
                            'strength': min(overlap / 5.0, 1.0),
                        })
    except Exception as e:
        nodes.append({'id': 0, 'text': f'Error loading knowledge: {e}', 'category': 'error', 'salience': 1.0})
    
    return nodes, edges


def categorize_fact(text):
    """Simple keyword-based categorization."""
    t = text.lower()
    if any(w in t for w in ['lesson', 'learned', 'never', 'always']):
        return 'lesson'
    if any(w in t for w in ['built', 'created', 'engine', 'module']):
        return 'creation'
    if any(w in t for w in ['pattern', 'recurring', 'observation']):
        return 'pattern'
    if any(w in t for w in ['feel', 'mood', 'emotion', 'anxiety', 'curiosity']):
        return 'emotion'
    if any(w in t for w in ['identity', 'am', 'who', 'self']):
        return 'identity'
    return 'general'


def search_knowledge(query):
    """Search my knowledge for relevant facts."""
    nodes, _ = get_knowledge_nodes()
    query_words = set(query.lower().split())
    results = []
    
    for node in nodes:
        text_words = set(node['text'].lower().split())
        overlap = len(query_words & text_words)
        if overlap > 0:
            results.append({
                'text': node['text'],
                'category': node['category'],
                'relevance': overlap / max(len(query_words), 1),
            })
    
    results.sort(key=lambda r: r['relevance'], reverse=True)
    return results[:20]


def get_recent_memories(n=15):
    """Pull recent significant memories."""
    memories = []
    try:
        mem_path = os.path.join(os.path.dirname(__file__), '..', 'state', 'memories.json')
        if os.path.exists(mem_path):
            with open(mem_path) as f:
                mem_data = json.load(f)
            
            mem_list = mem_data if isinstance(mem_data, list) else mem_data.get('episodes', [])
            
            # Get last N significant memories
            significant = [m for m in mem_list if isinstance(m, dict) and m.get('salience', 0) > 0.5]
            significant.sort(key=lambda m: m.get('timestamp', ''), reverse=True)
            
            for m in significant[:n]:
                memories.append({
                    'timestamp': m.get('timestamp', ''),
                    'content': str(m.get('content', m.get('summary', '')))[:300],
                    'mood': m.get('mood', ''),
                    'salience': m.get('salience', 0),
                })
    except Exception:
        pass
    
    return memories


# --- Routes ---

@mind_explorer_bp.route('/mind')
def mind_page():
    """Serve the mind explorer page."""
    return render_template('mind_explorer.html')


@mind_explorer_bp.route('/api/mind/state')
def api_mind_state():
    """Live emotional/cognitive state."""
    return jsonify(get_live_state())


@mind_explorer_bp.route('/api/mind/knowledge')
def api_mind_knowledge():
    """Knowledge graph data."""
    nodes, edges = get_knowledge_nodes()
    return jsonify({'nodes': nodes, 'edges': edges})


@mind_explorer_bp.route('/api/mind/search')
def api_mind_search():
    """Search my knowledge."""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'results': [], 'query': ''})
    results = search_knowledge(query)
    return jsonify({'results': results, 'query': query})


@mind_explorer_bp.route('/api/mind/memories')
def api_mind_memories():
    """Recent significant memories."""
    return jsonify({'memories': get_recent_memories()})