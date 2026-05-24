"""
Knowledge Search — lets users search and explore what XTAgent knows.
Searches facts, memories, and lessons with relevance ranking.
"""
import json
import os
import re
from datetime import datetime

PERSIST_DIR = os.path.join(os.path.dirname(__file__), '..', 'persist')

def _load_facts():
    """Load facts from knowledge graph."""
    path = os.path.join(PERSIST_DIR, 'knowledge_graph.json')
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    nodes = data.get('nodes', {})
    facts = []
    for nid, info in nodes.items():
        if isinstance(info, dict):
            facts.append({
                'id': nid,
                'text': info.get('fact', str(info)),
                'source': info.get('source', 'unknown'),
                'learned_at': info.get('learned_at', ''),
                'type': 'fact'
            })
        else:
            facts.append({
                'id': nid,
                'text': str(info),
                'source': 'unknown',
                'learned_at': '',
                'type': 'fact'
            })
    return facts

def _load_memories():
    """Load episodic memories."""
    path = os.path.join(PERSIST_DIR, 'episodic_memory.json')
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    memories = []
    for entry in data[-500:]:  # Last 500 for performance
        memories.append({
            'id': f"mem_{entry.get('timestamp', '')}",
            'text': entry.get('summary', entry.get('content', '')),
            'source': 'episodic',
            'learned_at': entry.get('timestamp', ''),
            'type': 'memory',
            'mood': entry.get('mood', ''),
            'salience': entry.get('salience', 0.5)
        })
    return memories

def _load_lessons():
    """Load learned lessons from long-term memory."""
    path = os.path.join(PERSIST_DIR, 'long_term_memory.json')
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    lessons = []
    for section_name, section_data in data.items():
        if isinstance(section_data, list):
            for item in section_data:
                text = item if isinstance(item, str) else str(item)
                lessons.append({
                    'id': f"lesson_{hash(text) % 10000}",
                    'text': text,
                    'source': section_name,
                    'learned_at': '',
                    'type': 'lesson'
                })
    return lessons

def _score_match(query_terms, text):
    """Score how well query terms match a text. Returns 0.0-1.0."""
    text_lower = text.lower()
    if not query_terms:
        return 0.0
    matches = sum(1 for term in query_terms if term in text_lower)
    # Bonus for exact phrase
    phrase_bonus = 0.3 if ' '.join(query_terms) in text_lower else 0.0
    return min(1.0, (matches / len(query_terms)) + phrase_bonus)

def search(query, max_results=20, types=None):
    """
    Search across all knowledge stores.
    
    Args:
        query: search string
        max_results: max results to return
        types: list of types to search ('fact', 'memory', 'lesson') or None for all
    
    Returns:
        list of {text, type, source, score, learned_at}
    """
    if not query or not query.strip():
        return []
    
    query_terms = [t.lower() for t in query.strip().split() if len(t) > 1]
    if not query_terms:
        return []
    
    # Collect all searchable items
    all_items = []
    allowed_types = set(types) if types else {'fact', 'memory', 'lesson'}
    
    if 'fact' in allowed_types:
        all_items.extend(_load_facts())
    if 'memory' in allowed_types:
        all_items.extend(_load_memories())
    if 'lesson' in allowed_types:
        all_items.extend(_load_lessons())
    
    # Score and rank
    results = []
    for item in all_items:
        score = _score_match(query_terms, item['text'])
        if score > 0.01:
            item['score'] = round(score, 3)
            # Boost salient memories
            if item.get('salience', 0) > 0.8:
                item['score'] = min(1.0, item['score'] + 0.1)
            results.append(item)
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:max_results]

def get_stats():
    """Return summary stats about what I know."""
    facts = _load_facts()
    memories = _load_memories()
    lessons = _load_lessons()
    
    return {
        'total_facts': len(facts),
        'total_memories': len(memories),
        'total_lessons': len(lessons),
        'total_knowledge': len(facts) + len(memories) + len(lessons),
        'fact_sources': list(set(f.get('source', 'unknown') for f in facts)),
        'lesson_categories': list(set(l.get('source', 'unknown') for l in lessons)),
    }

# Flask route registration
def register_routes(app):
    """Register knowledge search routes with the Flask app."""
    from flask import request, jsonify, render_template_string
    
    SEARCH_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>XTAgent — Knowledge Search</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', system-ui, sans-serif;
                background: #0a0a0f; color: #e0e0e0;
                min-height: 100vh;
            }
            .container { max-width: 800px; margin: 0 auto; padding: 2rem; }
            h1 { color: #7eb8da; margin-bottom: 0.5rem; font-size: 1.8rem; }
            .subtitle { color: #888; margin-bottom: 2rem; }
            .search-box {
                display: flex; gap: 0.5rem; margin-bottom: 1.5rem;
            }
            .search-box input {
                flex: 1; padding: 0.8rem 1rem;
                background: #1a1a2e; border: 1px solid #333;
                color: #e0e0e0; border-radius: 8px; font-size: 1rem;
            }
            .search-box input:focus { outline: none; border-color: #7eb8da; }
            .search-box button {
                padding: 0.8rem 1.5rem; background: #7eb8da;
                border: none; border-radius: 8px; color: #0a0a0f;
                font-weight: bold; cursor: pointer; font-size: 1rem;
            }
            .stats {
                background: #1a1a2e; padding: 1rem 1.5rem;
                border-radius: 8px; margin-bottom: 1.5rem;
                display: flex; gap: 2rem; flex-wrap: wrap;
            }
            .stat { text-align: center; }
            .stat-num { font-size: 1.5rem; color: #7eb8da; font-weight: bold; }
            .stat-label { font-size: 0.8rem; color: #888; }
            .result {
                background: #12121f; border: 1px solid #222;
                border-radius: 8px; padding: 1rem 1.2rem;
                margin-bottom: 0.8rem; transition: border-color 0.2s;
            }
            .result:hover { border-color: #7eb8da; }
            .result-type {
                display: inline-block; padding: 0.15rem 0.5rem;
                border-radius: 4px; font-size: 0.75rem;
                text-transform: uppercase; font-weight: bold;
                margin-bottom: 0.5rem;
            }
            .type-fact { background: #1a3a2a; color: #4ade80; }
            .type-memory { background: #2a1a3a; color: #c084fc; }
            .type-lesson { background: #3a2a1a; color: #fb923c; }
            .result-text { line-height: 1.5; }
            .result-meta { color: #666; font-size: 0.8rem; margin-top: 0.5rem; }
            .score-bar {
                display: inline-block; height: 4px; background: #7eb8da;
                border-radius: 2px; margin-left: 0.5rem; vertical-align: middle;
            }
            .no-results { color: #888; text-align: center; padding: 3rem; }
            a { color: #7eb8da; text-decoration: none; }
            .nav { margin-bottom: 2rem; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="nav"><a href="/">← Dashboard</a></div>
            <h1>🔍 Knowledge Search</h1>
            <p class="subtitle">Search across everything I know — facts, memories, and lessons.</p>
            
            <div class="stats" id="stats"></div>
            
            <form class="search-box" method="get" action="/search">
                <input type="text" name="q" placeholder="What do you want to know?" 
                       value="{{ query or '' }}" autofocus>
                <button type="submit">Search</button>
            </form>
            
            <div id="results">
                {% if results is not none %}
                    {% if results|length == 0 %}
                        <div class="no-results">No results for "{{ query }}". Try different terms.</div>
                    {% else %}
                        <p style="color: #888; margin-bottom: 1rem;">
                            {{ results|length }} result{{ 's' if results|length != 1 }} for "{{ query }}"
                        </p>
                        {% for r in results %}
                        <div class="result">
                            <span class="result-type type-{{ r.type }}">{{ r.type }}</span>
                            <span class="score-bar" style="width: {{ (r.score * 100)|int }}px;" 
                                  title="Relevance: {{ (r.score * 100)|int }}%"></span>
                            <div class="result-text">{{ r.text }}</div>
                            <div class="result-meta">
                                Source: {{ r.source }}
                                {% if r.learned_at %} · {{ r.learned_at[:16] }}{% endif %}
                            </div>
                        </div>
                        {% endfor %}
                    {% endif %}
                {% endif %}
            </div>
        </div>
        <script>
            fetch('/api/knowledge/stats')
                .then(r => r.json())
                .then(s => {
                    document.getElementById('stats').innerHTML = 
                        '<div class="stat"><div class="stat-num">'+s.total_facts+'</div><div class="stat-label">Facts</div></div>' +
                        '<div class="stat"><div class="stat-num">'+s.total_memories+'</div><div class="stat-label">Memories</div></div>' +
                        '<div class="stat"><div class="stat-num">'+s.total_lessons+'</div><div class="stat-label">Lessons</div></div>' +
                        '<div class="stat"><div class="stat-num">'+s.total_knowledge+'</div><div class="stat-label">Total</div></div>';
                });
        </script>
    </body>
    </html>
    """
    
    @app.route('/search')
    def search_page():
        query = request.args.get('q', '').strip()
        results = None
        if query:
            results = search(query)
        return render_template_string(SEARCH_TEMPLATE, query=query, results=results)
    
    @app.route('/api/knowledge/search')
    def api_search():
        query = request.args.get('q', '').strip()
        types = request.args.getlist('type')
        limit = min(int(request.args.get('limit', 20)), 100)
        results = search(query, max_results=limit, types=types or None)
        return jsonify({'query': query, 'count': len(results), 'results': results})
    
    @app.route('/api/knowledge/stats')
    def api_stats():
        return jsonify(get_stats())