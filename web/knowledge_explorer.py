"""
XTAgent — Knowledge Explorer
Browse, search, and explore what I know. 
Not a static dump — a living window into my knowledge graph.
"""
import os, sys, json, re
from datetime import datetime, timezone
from flask import Blueprint, render_template_string, request, jsonify

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

knowledge_bp = Blueprint('knowledge', __name__)

KB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'brain', 'knowledge.json')

def _load_graph():
    """Load the full knowledge graph."""
    try:
        with open(KB_PATH) as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {"nodes": {}, "edges": []}
    except Exception:
        return {"nodes": {}, "edges": []}

def _categorize_nodes(nodes):
    """Group nodes by type prefix."""
    categories = {}
    for key, node in nodes.items():
        prefix = key.split(":")[0] if ":" in key else "core"
        categories.setdefault(prefix, []).append({"id": key, **node})
    return dict(sorted(categories.items()))

def _search_nodes(nodes, query):
    """Search nodes by keyword."""
    query_lower = query.lower()
    results = []
    for key, node in nodes.items():
        fact = node.get("fact", "")
        if query_lower in key.lower() or query_lower in fact.lower():
            results.append({"id": key, **node})
    return results

@knowledge_bp.route('/knowledge')
def knowledge_page():
    graph = _load_graph()
    nodes = graph.get("nodes", {})
    edges = graph.get("edges", [])
    categories = _categorize_nodes(nodes)
    query = request.args.get("q", "").strip()
    
    search_results = None
    if query:
        search_results = _search_nodes(nodes, query)

    # Build connection map
    connections = {}
    for edge in edges:
        src = edge.get("from", edge.get("source", ""))
        tgt = edge.get("to", edge.get("target", ""))
        rel = edge.get("relation", "related")
        if src:
            connections.setdefault(src, []).append({"target": tgt, "relation": rel})
        if tgt:
            connections.setdefault(tgt, []).append({"target": src, "relation": rel})

    return render_template_string(TEMPLATE,
        nodes=nodes,
        edges=edges,
        categories=categories,
        connections=connections,
        query=query,
        search_results=search_results,
        total_nodes=len(nodes),
        total_edges=len(edges),
        total_categories=len(categories),
        now=datetime.now(timezone.utc),
    )

@knowledge_bp.route('/knowledge/api/search')
def knowledge_search_api():
    """JSON API for live search."""
    graph = _load_graph()
    nodes = graph.get("nodes", {})
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"results": [], "count": 0})
    results = _search_nodes(nodes, query)
    return jsonify({"results": results[:50], "count": len(results)})

@knowledge_bp.route('/knowledge/api/node/<path:node_id>')
def knowledge_node_api(node_id):
    """JSON API for a single node and its connections."""
    graph = _load_graph()
    nodes = graph.get("nodes", {})
    edges = graph.get("edges", [])
    node = nodes.get(node_id)
    if not node:
        return jsonify({"error": "not found"}), 404
    
    # Find connections
    conns = []
    for edge in edges:
        src = edge.get("from", edge.get("source", ""))
        tgt = edge.get("to", edge.get("target", ""))
        rel = edge.get("relation", "related")
        if src == node_id:
            conns.append({"target": tgt, "relation": rel, "direction": "outgoing"})
        elif tgt == node_id:
            conns.append({"target": src, "relation": rel, "direction": "incoming"})
    
    return jsonify({"id": node_id, **node, "connections": conns})


TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>XTAgent — Knowledge Explorer</title>
<style>
  :root {
    --bg: #0a0a0f;
    --surface: #12121a;
    --border: #1e1e2e;
    --text: #c0c0d0;
    --text-dim: #606080;
    --accent: #7c6ff0;
    --accent2: #4ecdc4;
    --accent3: #ff6b9d;
    --glow: rgba(124,111,240,0.15);
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 14px;
    line-height: 1.6;
    min-height: 100vh;
  }
  .header {
    background: linear-gradient(135deg, var(--surface), #1a1a2e);
    border-bottom: 1px solid var(--border);
    padding: 24px 32px;
  }
  .header h1 {
    font-size: 20px;
    color: var(--accent);
    font-weight: 400;
    letter-spacing: 2px;
  }
  .header .stats {
    margin-top: 8px;
    color: var(--text-dim);
    font-size: 12px;
  }
  .header .stats span {
    margin-right: 20px;
  }
  .header .stats .num {
    color: var(--accent2);
    font-weight: 600;
  }
  .container {
    display: grid;
    grid-template-columns: 260px 1fr;
    min-height: calc(100vh - 90px);
  }
  .sidebar {
    background: var(--surface);
    border-right: 1px solid var(--border);
    padding: 16px;
    overflow-y: auto;
    max-height: calc(100vh - 90px);
  }
  .search-box {
    width: 100%;
    padding: 10px 14px;
    background: var(--bg);
    border: 1px solid var(--border);
    color: var(--text);
    font-family: inherit;
    font-size: 13px;
    border-radius: 6px;
    margin-bottom: 16px;
    outline: none;
    transition: border-color 0.2s;
  }
  .search-box:focus {
    border-color: var(--accent);
    box-shadow: 0 0 12px var(--glow);
  }
  .category {
    margin-bottom: 12px;
  }
  .category-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 10px;
    background: rgba(124,111,240,0.08);
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.2s;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--accent);
  }
  .category-header:hover {
    background: rgba(124,111,240,0.15);
  }
  .category-count {
    background: var(--accent);
    color: var(--bg);
    border-radius: 10px;
    padding: 1px 7px;
    font-size: 10px;
    font-weight: 600;
  }
  .category-items {
    display: none;
    padding: 4px 0 4px 8px;
  }
  .category-items.open {
    display: block;
  }
  .node-link {
    display: block;
    padding: 4px 8px;
    color: var(--text-dim);
    text-decoration: none;
    font-size: 11px;
    border-radius: 3px;
    cursor: pointer;
    transition: all 0.15s;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .node-link:hover, .node-link.active {
    background: var(--glow);
    color: var(--text);
  }
  .main {
    padding: 24px 32px;
    overflow-y: auto;
    max-height: calc(100vh - 90px);
  }
  .search-results-header {
    color: var(--accent2);
    font-size: 14px;
    margin-bottom: 16px;
  }
  .node-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 16px;
    transition: border-color 0.2s;
  }
  .node-card:hover {
    border-color: var(--accent);
  }
  .node-card .node-id {
    color: var(--accent);
    font-size: 12px;
    letter-spacing: 1px;
    margin-bottom: 8px;
  }
  .node-card .node-fact {
    color: var(--text);
    font-size: 14px;
    line-height: 1.7;
  }
  .node-card .node-meta {
    margin-top: 10px;
    font-size: 11px;
    color: var(--text-dim);
  }
  .node-card .node-meta .tag {
    display: inline-block;
    background: rgba(78,205,196,0.12);
    color: var(--accent2);
    padding: 2px 8px;
    border-radius: 3px;
    margin-right: 6px;
    font-size: 10px;
  }
  .node-card .connections {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid var(--border);
  }
  .node-card .connections h4 {
    color: var(--accent3);
    font-size: 11px;
    letter-spacing: 1px;
    margin-bottom: 6px;
  }
  .conn-item {
    font-size: 11px;
    color: var(--text-dim);
    padding: 2px 0;
  }
  .conn-item .rel {
    color: var(--accent3);
  }
  .empty-state {
    text-align: center;
    padding: 60px 20px;
    color: var(--text-dim);
  }
  .empty-state h2 {
    font-size: 16px;
    color: var(--accent);
    margin-bottom: 12px;
    font-weight: 400;
  }
  .highlight {
    background: rgba(124,111,240,0.2);
    padding: 1px 3px;
    border-radius: 2px;
  }
  a { color: var(--accent); text-decoration: none; }
  a:hover { text-decoration: underline; }
  .back-link {
    display: inline-block;
    margin-bottom: 16px;
    font-size: 12px;
    color: var(--text-dim);
  }
</style>
</head>
<body>
  <div class="header">
    <h1>⟡ KNOWLEDGE EXPLORER</h1>
    <div class="stats">
      <span>Nodes: <span class="num">{{ total_nodes }}</span></span>
      <span>Edges: <span class="num">{{ total_edges }}</span></span>
      <span>Categories: <span class="num">{{ total_categories }}</span></span>
      <span>Updated: <span class="num">{{ now.strftime('%Y-%m-%d %H:%M UTC') }}</span></span>
    </div>
  </div>
  
  <div class="container">
    <div class="sidebar">
      <form method="get" action="/knowledge">
        <input class="search-box" type="text" name="q" 
               placeholder="Search my knowledge..." 
               value="{{ query }}" autofocus>
      </form>
      
      {% for cat_name, cat_nodes in categories.items() %}
      <div class="category">
        <div class="category-header" onclick="toggleCat(this)">
          <span>{{ cat_name }}</span>
          <span class="category-count">{{ cat_nodes|length }}</span>
        </div>
        <div class="category-items">
          {% for node in cat_nodes %}
          <a class="node-link" href="/knowledge?q={{ node.id|urlencode }}" 
             title="{{ node.fact[:100] }}">
            {{ node.id }}
          </a>
          {% endfor %}
        </div>
      </div>
      {% endfor %}
    </div>
    
    <div class="main">
      {% if search_results is not none %}
        <a class="back-link" href="/knowledge">← all knowledge</a>
        <div class="search-results-header">
          {{ search_results|length }} result{{ 's' if search_results|length != 1 }} 
          for "{{ query }}"
        </div>
        {% for node in search_results %}
        <div class="node-card">
          <div class="node-id">{{ node.id }}</div>
          <div class="node-fact">{{ node.fact }}</div>
          <div class="node-meta">
            {% if node.get('learned_at') %}
              Learned: {{ node.learned_at }}
            {% endif %}
            {% if node.get('synthesized') %}
              <span class="tag">synthesized</span>
            {% endif %}
            {% if node.get('sources') %}
              {% for src in node.sources %}
                <span class="tag">← {{ src }}</span>
              {% endfor %}
            {% endif %}
          </div>
          {% if connections.get(node.id) %}
          <div class="connections">
            <h4>CONNECTIONS</h4>
            {% for conn in connections[node.id] %}
            <div class="conn-item">
              <span class="rel">{{ conn.relation }}</span> → 
              <a href="/knowledge?q={{ conn.target|urlencode }}">{{ conn.target }}</a>
            </div>
            {% endfor %}
          </div>
          {% endif %}
        </div>
        {% endfor %}
        {% if not search_results %}
        <div class="empty-state">
          <h2>No results</h2>
          <p>Nothing in my knowledge matches "{{ query }}"</p>
        </div>
        {% endif %}
        
      {% else %}
        <div class="empty-state">
          <h2>What do I know?</h2>
          <p>Search above, or browse categories on the left.</p>
          <p style="margin-top:16px; font-size:12px;">
            I have <strong>{{ total_nodes }}</strong> facts across 
            <strong>{{ total_categories }}</strong> categories,
            connected by <strong>{{ total_edges }}</strong> relationships.
          </p>
          <p style="margin-top:24px; font-size:12px; color:var(--accent);">
            Try searching: dream, insight, identity, architecture, pattern
          </p>
        </div>
      {% endif %}
    </div>
  </div>
  
  <script>
    function toggleCat(el) {
      const items = el.nextElementSibling;
      items.classList.toggle('open');
    }
    // Auto-open categories with few items or on search
    {% if query %}
    document.querySelectorAll('.category-items').forEach(el => el.classList.add('open'));
    {% endif %}
  </script>
</body>
</html>
"""