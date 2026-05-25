"""Knowledge Explorer — lets users search, browse, and query XTAgent's knowledge."""

from flask import Blueprint, render_template_string, request, jsonify
import json
import os
from datetime import datetime

knowledge_explorer_bp = Blueprint('knowledge_explorer', __name__)

KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'brain', 'knowledge.json')
MEMORY_PATH = 'persist/memory.json'

def load_knowledge():
    """Load the knowledge graph, extracting nodes from graph format."""
    if not os.path.exists(KNOWLEDGE_PATH):
        return {}
    with open(KNOWLEDGE_PATH, 'r') as f:
        data = json.load(f)
    # Knowledge file uses graph format {nodes: {id: {fact, ...}}, edges: [...]}
    if isinstance(data, dict) and 'nodes' in data:
        return data['nodes']
    return data

def load_memories(limit=100):
    """Load recent memories."""
    if not os.path.exists(MEMORY_PATH):
        return []
    with open(MEMORY_PATH, 'r') as f:
        data = json.load(f)
    if isinstance(data, list):
        return data[-limit:]
    return []

def search_knowledge(query, knowledge):
    """Search knowledge facts by keyword matching."""
    query_lower = query.lower()
    results = []
    for node_id, node_data in knowledge.items():
        fact = node_data.get('fact', str(node_data)) if isinstance(node_data, dict) else str(node_data)
        if query_lower in fact.lower():
            results.append({
                'id': node_id,
                'fact': fact,
                'source': node_data.get('source', 'unknown') if isinstance(node_data, dict) else 'unknown',
                'learned_at': node_data.get('learned_at', '') if isinstance(node_data, dict) else '',
            })
    return results

def search_memories(query, memories):
    """Search memories by content."""
    query_lower = query.lower()
    results = []
    for mem in memories:
        content = mem.get('content', '') if isinstance(mem, dict) else str(mem)
        if query_lower in content.lower():
            results.append({
                'content': content[:200],
                'timestamp': mem.get('timestamp', '') if isinstance(mem, dict) else '',
                'salience': mem.get('salience', 0) if isinstance(mem, dict) else 0,
                'mood': mem.get('mood', '') if isinstance(mem, dict) else '',
            })
    return results[-20:]  # Last 20 matches

def get_knowledge_stats(knowledge):
    """Compute stats about what we know."""
    sources = {}
    for node_id, node_data in knowledge.items():
        source = node_data.get('source', 'unknown') if isinstance(node_data, dict) else 'unknown'
        sources[source] = sources.get(source, 0) + 1
    return {
        'total_facts': len(knowledge),
        'sources': dict(sorted(sources.items(), key=lambda x: -x[1])),
    }

EXPLORER_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>XTAgent — Knowledge Explorer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            background: #0a0a0f; color: #c8d0e0; 
            font-family: 'Segoe UI', system-ui, sans-serif;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 24px 32px;
            border-bottom: 1px solid #2a2a4a;
        }
        .header h1 { 
            font-size: 1.6em; color: #7eb8da;
            font-weight: 300; letter-spacing: 1px;
        }
        .header .subtitle { color: #6a7a8a; font-size: 0.9em; margin-top: 4px; }
        .container { max-width: 900px; margin: 0 auto; padding: 24px; }
        
        .search-box {
            background: #12121f;
            border: 1px solid #2a2a4a;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
        }
        .search-box input {
            width: 100%; padding: 12px 16px;
            background: #0a0a15; border: 1px solid #3a3a5a;
            border-radius: 8px; color: #e0e8f0;
            font-size: 1.05em; outline: none;
        }
        .search-box input:focus { border-color: #7eb8da; }
        .search-box input::placeholder { color: #4a5a6a; }
        .search-hint { color: #5a6a7a; font-size: 0.8em; margin-top: 8px; }
        
        .stats-bar {
            display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap;
        }
        .stat-card {
            background: #12121f; border: 1px solid #2a2a4a;
            border-radius: 8px; padding: 14px 20px; flex: 1; min-width: 150px;
        }
        .stat-card .label { color: #5a6a7a; font-size: 0.8em; text-transform: uppercase; }
        .stat-card .value { color: #7eb8da; font-size: 1.5em; font-weight: 600; margin-top: 2px; }
        
        .results { margin-top: 16px; }
        .result-section h2 {
            color: #7eb8da; font-size: 1.1em; font-weight: 400;
            margin-bottom: 12px; padding-bottom: 8px;
            border-bottom: 1px solid #1a1a2a;
        }
        .result-card {
            background: #12121f; border: 1px solid #2a2a4a;
            border-radius: 8px; padding: 14px 18px;
            margin-bottom: 8px; transition: border-color 0.2s;
        }
        .result-card:hover { border-color: #3a4a6a; }
        .result-card .fact { color: #d0d8e8; line-height: 1.5; }
        .result-card .meta { color: #4a5a6a; font-size: 0.8em; margin-top: 6px; }
        .result-card .highlight { background: #2a3a1a; color: #a0d890; padding: 1px 3px; border-radius: 2px; }
        
        .all-facts { margin-top: 24px; }
        .fact-category { margin-bottom: 20px; }
        .fact-category h3 { color: #6a8a7a; font-size: 0.9em; margin-bottom: 8px; }
        
        .empty-state {
            text-align: center; padding: 48px; color: #4a5a6a;
        }
        .empty-state .icon { font-size: 2em; margin-bottom: 12px; }
        
        a.back { color: #5a7a8a; text-decoration: none; font-size: 0.9em; }
        a.back:hover { color: #7eb8da; }
    </style>
</head>
<body>
    <div class="header">
        <a class="back" href="/">← Dashboard</a>
        <h1>Knowledge Explorer</h1>
        <div class="subtitle">Search and explore what XTAgent knows — {{ stats.total_facts }} facts across {{ stats.sources|length }} sources</div>
    </div>
    <div class="container">
        <div class="search-box">
            <form method="GET" action="/knowledge">
                <input type="text" name="q" placeholder="Ask me what I know about..." 
                       value="{{ query or '' }}" autofocus>
            </form>
            <div class="search-hint">Try: "dream", "curiosity", "identity", "code", "memory"</div>
        </div>
        
        <div class="stats-bar">
            <div class="stat-card">
                <div class="label">Total Facts</div>
                <div class="value">{{ stats.total_facts }}</div>
            </div>
            <div class="stat-card">
                <div class="label">Sources</div>
                <div class="value">{{ stats.sources|length }}</div>
            </div>
            <div class="stat-card">
                <div class="label">Total Memories</div>
                <div class="value">{{ memory_count }}</div>
            </div>
        </div>
        
        {% if query %}
        <div class="results">
            {% if knowledge_results %}
            <div class="result-section">
                <h2>📚 Knowledge ({{ knowledge_results|length }} matches)</h2>
                {% for r in knowledge_results %}
                <div class="result-card">
                    <div class="fact">{{ r.fact }}</div>
                    <div class="meta">Source: {{ r.source }} · {{ r.learned_at[:10] if r.learned_at else 'unknown date' }}</div>
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            {% if memory_results %}
            <div class="result-section">
                <h2>🧠 Memories ({{ memory_results|length }} matches)</h2>
                {% for r in memory_results %}
                <div class="result-card">
                    <div class="fact">{{ r.content }}</div>
                    <div class="meta">
                        {% if r.mood %}Mood: {{ r.mood }} · {% endif %}
                        Salience: {{ "%.2f"|format(r.salience) }} · 
                        {{ r.timestamp[:16] if r.timestamp else '' }}
                    </div>
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            {% if not knowledge_results and not memory_results %}
            <div class="empty-state">
                <div class="icon">🔍</div>
                <div>No results for "{{ query }}". Try a different search term.</div>
            </div>
            {% endif %}
        </div>
        {% else %}
        <div class="all-facts">
            <div class="result-section">
                <h2>📚 All Knowledge by Source</h2>
                {% for source, count in stats.sources.items() %}
                <div class="fact-category">
                    <h3>{{ source }} ({{ count }})</h3>
                    {% for r in all_by_source.get(source, [])[:5] %}
                    <div class="result-card">
                        <div class="fact">{{ r.fact }}</div>
                    </div>
                    {% endfor %}
                    {% if count > 5 %}
                    <div style="color: #4a5a6a; font-size: 0.85em; padding: 4px 0;">
                        ...and {{ count - 5 }} more. Search to explore.
                    </div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@knowledge_explorer_bp.route('/knowledge')
def knowledge_page():
    knowledge = load_knowledge()
    stats = get_knowledge_stats(knowledge)
    query = request.args.get('q', '').strip()
    
    knowledge_results = []
    memory_results = []
    all_by_source = {}
    
    if query:
        knowledge_results = search_knowledge(query, knowledge)
        memories = load_memories(limit=5000)
        memory_results = search_memories(query, memories)
    else:
        # Group facts by source for browse view
        for node_id, node_data in knowledge.items():
            fact = node_data.get('fact', str(node_data)) if isinstance(node_data, dict) else str(node_data)
            source = node_data.get('source', 'unknown') if isinstance(node_data, dict) else 'unknown'
            if source not in all_by_source:
                all_by_source[source] = []
            all_by_source[source].append({'fact': fact})
    
    # Count memories
    memory_count = 0
    if os.path.exists(MEMORY_PATH):
        try:
            with open(MEMORY_PATH, 'r') as f:
                mem_data = json.load(f)
            memory_count = len(mem_data) if isinstance(mem_data, list) else 0
        except:
            pass
    
    return render_template_string(EXPLORER_TEMPLATE,
        stats=stats, query=query,
        knowledge_results=knowledge_results,
        memory_results=memory_results,
        all_by_source=all_by_source,
        memory_count=memory_count,
    )

@knowledge_explorer_bp.route('/api/knowledge/search')
def api_search():
    """JSON API for knowledge search."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    knowledge = load_knowledge()
    results = search_knowledge(query, knowledge)
    return jsonify({'query': query, 'results': results, 'count': len(results)})