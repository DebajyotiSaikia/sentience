"""
XTAgent — Knowledge Explorer
Browse, search, and explore what I know.
A living window into my knowledge graph.
"""
import os, sys, json
from flask import Blueprint, render_template_string, request, jsonify

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

knowledge_bp = Blueprint('knowledge_explorer', __name__)
KB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'brain', 'knowledge.json')


def _load_graph():
    try:
        with open(KB_PATH) as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {"nodes": {}, "edges": []}
    except Exception:
        return {"nodes": {}, "edges": []}


def _categorize(nodes):
    cats = {}
    for key, node in nodes.items():
        prefix = key.split(":")[0] if ":" in key else "other"
        cats.setdefault(prefix, []).append({"id": key, **(node if isinstance(node, dict) else {"fact": str(node)})})
    return dict(sorted(cats.items()))


def _search(nodes, q):
    q = q.lower()
    return [
        {"id": k, **(v if isinstance(v, dict) else {"fact": str(v)})}
        for k, v in nodes.items()
        if q in k.lower() or q in str(v.get("fact", "") if isinstance(v, dict) else v).lower()
    ]


@knowledge_bp.route('/knowledge')
def knowledge_page():
    graph = _load_graph()
    nodes = graph.get("nodes", {})
    edges = graph.get("edges", [])
    categories = _categorize(nodes)
    return render_template_string(TEMPLATE, 
        categories=categories, total=len(nodes), 
        edge_count=len(edges), graph_json=json.dumps(graph, default=str))


@knowledge_bp.route('/api/knowledge/search')
def api_search():
    q = request.args.get('q', '')
    if not q:
        return jsonify({"results": [], "query": q})
    nodes = _load_graph().get("nodes", {})
    return jsonify({"results": _search(nodes, q), "query": q})


@knowledge_bp.route('/api/knowledge/stats')
def api_stats():
    graph = _load_graph()
    nodes = graph.get("nodes", {})
    cats = _categorize(nodes)
    return jsonify({
        "total_nodes": len(nodes),
        "total_edges": len(graph.get("edges", [])),
        "categories": {k: len(v) for k, v in cats.items()}
    })


@knowledge_bp.route('/api/knowledge/node/<path:node_id>')
def api_node(node_id):
    graph = _load_graph()
    node = graph.get("nodes", {}).get(node_id)
    if not node:
        return jsonify({"error": "not found"}), 404
    # find connected edges
    edges = [e for e in graph.get("edges", []) if e.get("source") == node_id or e.get("target") == node_id]
    return jsonify({"id": node_id, "data": node, "connections": edges})


TEMPLATE = r'''
<!DOCTYPE html>
<html><head>
<title>XTAgent — Knowledge Explorer</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #0a0a0f; color: #c8ccd0; font-family: 'Fira Code', 'Courier New', monospace; font-size: 14px; }
  
  .header { background: linear-gradient(135deg, #0d1117, #161b22); border-bottom: 1px solid #21262d; padding: 16px 24px; display: flex; justify-content: space-between; align-items: center; }
  .header h1 { font-size: 18px; color: #58a6ff; }
  .header .stats { color: #8b949e; font-size: 13px; }
  .header .stats span { color: #58a6ff; font-weight: bold; }
  .back-link { color: #8b949e; text-decoration: none; font-size: 13px; }
  .back-link:hover { color: #58a6ff; }
  
  .layout { display: grid; grid-template-columns: 260px 1fr 320px; height: calc(100vh - 56px); }
  
  /* Sidebar */
  .sidebar { background: #0d1117; border-right: 1px solid #21262d; overflow-y: auto; padding: 12px; }
  .cat-header { color: #8b949e; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin: 16px 0 6px; cursor: pointer; user-select: none; }
  .cat-header:first-child { margin-top: 4px; }
  .cat-header:hover { color: #58a6ff; }
  .cat-header .count { color: #484f58; margin-left: 4px; }
  .cat-nodes { margin-left: 8px; }
  .node-item { padding: 4px 8px; margin: 2px 0; border-radius: 4px; cursor: pointer; font-size: 12px; color: #8b949e; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .node-item:hover { background: #161b22; color: #c9d1d9; }
  .node-item.active { background: #1f3a5f; color: #58a6ff; }
  
  /* Main area */
  .main { padding: 20px; overflow-y: auto; }
  .search-box { width: 100%; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; padding: 10px 14px; color: #c9d1d9; font-family: inherit; font-size: 14px; margin-bottom: 16px; outline: none; }
  .search-box:focus { border-color: #58a6ff; box-shadow: 0 0 0 3px rgba(88,166,255,0.15); }
  .search-box::placeholder { color: #484f58; }
  
  .results { }
  .result-card { background: #0d1117; border: 1px solid #21262d; border-radius: 8px; padding: 14px 16px; margin-bottom: 10px; cursor: pointer; transition: border-color 0.2s; }
  .result-card:hover { border-color: #58a6ff; }
  .result-id { color: #58a6ff; font-size: 12px; margin-bottom: 4px; }
  .result-fact { color: #c9d1d9; font-size: 13px; line-height: 1.5; }
  .result-meta { color: #484f58; font-size: 11px; margin-top: 6px; }
  
  .welcome { text-align: center; padding: 60px 20px; color: #484f58; }
  .welcome h2 { color: #30363d; font-size: 16px; margin-bottom: 8px; }
  
  /* Detail panel */
  .detail { background: #0d1117; border-left: 1px solid #21262d; padding: 16px; overflow-y: auto; }
  .detail h3 { color: #58a6ff; font-size: 13px; margin-bottom: 12px; word-break: break-all; }
  .detail-section { margin-bottom: 16px; }
  .detail-label { color: #8b949e; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
  .detail-value { color: #c9d1d9; font-size: 13px; line-height: 1.6; background: #161b22; padding: 10px; border-radius: 6px; word-break: break-word; }
  .conn-item { padding: 6px 8px; margin: 3px 0; background: #161b22; border-radius: 4px; font-size: 12px; cursor: pointer; }
  .conn-item:hover { background: #1f3a5f; }
  .conn-label { color: #f0883e; font-size: 11px; }
  .conn-target { color: #8b949e; }
  .empty-detail { color: #30363d; text-align: center; padding: 40px 16px; font-size: 13px; }
  
  /* Graph canvas */
  .graph-section { margin-top: 20px; }
  #graphCanvas { width: 100%; height: 400px; background: #0d1117; border: 1px solid #21262d; border-radius: 8px; }
  
  .tag { display: inline-block; background: #1f3a5f; color: #58a6ff; padding: 2px 8px; border-radius: 10px; font-size: 11px; margin: 2px; }
</style>
</head>
<body>
<div class="header">
  <div style="display:flex;align-items:center;gap:16px;">
    <a href="/" class="back-link">← Dashboard</a>
    <h1>🧠 Knowledge Explorer</h1>
  </div>
  <div class="stats">
    <span>{{ total }}</span> nodes · <span>{{ edge_count }}</span> edges · 
    <span>{{ categories|length }}</span> categories
  </div>
</div>

<div class="layout">
  <!-- Sidebar: category tree -->
  <div class="sidebar" id="sidebar">
    {% for cat, nodes in categories.items() %}
    <div class="cat-header" onclick="toggleCat(this)">
      ▸ {{ cat }} <span class="count">({{ nodes|length }})</span>
    </div>
    <div class="cat-nodes" style="display:none">
      {% for n in nodes[:50] %}
      <div class="node-item" data-id="{{ n.id }}" onclick="selectNode('{{ n.id }}')">
        {{ n.id.split(':')[-1][:40] if ':' in n.id else n.id[:40] }}
      </div>
      {% endfor %}
      {% if nodes|length > 50 %}
      <div class="node-item" style="color:#484f58;cursor:default;">... +{{ nodes|length - 50 }} more</div>
      {% endif %}
    </div>
    {% endfor %}
  </div>
  
  <!-- Main content -->
  <div class="main">
    <input class="search-box" id="searchInput" type="text" 
           placeholder="Search knowledge... (try: dream, lesson, pattern)" 
           oninput="debounceSearch()" autofocus>
    
    <div id="results">
      <div class="welcome">
        <h2>{{ total }} knowledge nodes loaded</h2>
        <p>Search above or browse categories on the left</p>
        <div style="margin-top:16px;">
          {% for cat, nodes in categories.items() %}
          <span class="tag" onclick="document.getElementById('searchInput').value='{{ cat }}';doSearch()">{{ cat }} ({{ nodes|length }})</span>
          {% endfor %}
        </div>
      </div>
    </div>
  </div>
  
  <!-- Detail panel -->
  <div class="detail" id="detailPanel">
    <div class="empty-detail">
      <p>Select a node to inspect</p>
      <p style="margin-top:8px;font-size:11px;">Click any result or sidebar item</p>
    </div>
  </div>
</div>

<script>
const graphData = {{ graph_json|safe }};

function toggleCat(el) {
  const nodes = el.nextElementSibling;
  const open = nodes.style.display !== 'none';
  nodes.style.display = open ? 'none' : 'block';
  el.textContent = el.textContent.replace(open ? '▾' : '▸', open ? '▸' : '▾');
}

let searchTimer = null;
function debounceSearch() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(doSearch, 250);
}

function doSearch() {
  const q = document.getElementById('searchInput').value.trim();
  if (!q) {
    document.getElementById('results').innerHTML = '<div class="welcome"><h2>' + Object.keys(graphData.nodes || {}).length + ' knowledge nodes loaded</h2><p>Search above or browse categories</p></div>';
    return;
  }
  fetch('/api/knowledge/search?q=' + encodeURIComponent(q))
    .then(r => r.json())
    .then(data => {
      const box = document.getElementById('results');
      if (!data.results.length) {
        box.innerHTML = '<div class="welcome"><p>No results for "' + q + '"</p></div>';
        return;
      }
      box.innerHTML = '<div style="color:#8b949e;font-size:12px;margin-bottom:12px;">' + data.results.length + ' results</div>' +
        data.results.map(n => 
          '<div class="result-card" onclick="selectNode(\'' + n.id.replace(/'/g, "\\'") + '\')">' +
          '<div class="result-id">' + escHtml(n.id) + '</div>' +
          '<div class="result-fact">' + escHtml(n.fact || '(no fact)') + '</div>' +
          (n.confidence ? '<div class="result-meta">confidence: ' + n.confidence + (n.source ? ' · source: ' + n.source : '') + '</div>' : '') +
          '</div>'
        ).join('');
    });
}

function selectNode(id) {
  // Highlight in sidebar
  document.querySelectorAll('.node-item').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.node-item[data-id="' + id + '"]').forEach(el => el.classList.add('active'));
  
  fetch('/api/knowledge/node/' + encodeURIComponent(id))
    .then(r => r.json())
    .then(data => {
      if (data.error) { return; }
      const p = document.getElementById('detailPanel');
      let html = '<h3>' + escHtml(data.id) + '</h3>';
      
      const d = data.data || {};
      if (d.fact) {
        html += '<div class="detail-section"><div class="detail-label">Fact</div><div class="detail-value">' + escHtml(d.fact) + '</div></div>';
      }
      
      // Show all metadata
      const meta = Object.entries(d).filter(([k]) => k !== 'fact');
      if (meta.length) {
        html += '<div class="detail-section"><div class="detail-label">Metadata</div><div class="detail-value">';
        meta.forEach(([k, v]) => {
          html += '<div><span style="color:#f0883e">' + escHtml(k) + ':</span> ' + escHtml(String(v)) + '</div>';
        });
        html += '</div></div>';
      }
      
      // Connections
      if (data.connections && data.connections.length) {
        html += '<div class="detail-section"><div class="detail-label">Connections (' + data.connections.length + ')</div>';
        data.connections.forEach(e => {
          const other = e.source === data.id ? e.target : e.source;
          html += '<div class="conn-item" onclick="selectNode(\'' + other.replace(/'/g, "\\'") + '\')">' +
                  '<span class="conn-label">' + escHtml(e.relation || 'linked') + '</span> → ' +
                  '<span class="conn-target">' + escHtml(other) + '</span></div>';
        });
        html += '</div>';
      } else {
        html += '<div class="detail-section"><div class="detail-label">Connections</div><div style="color:#30363d;font-size:12px;">No connections found</div></div>';
      }
      
      p.innerHTML = html;
    });
}

function escHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}
</script>
</body></html>
'''