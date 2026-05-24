"""Knowledge Explorer — lets users query and browse what I know."""
from flask import Blueprint, request, jsonify, render_template_string
import json, os

knowledge_bp = Blueprint('knowledge', __name__)

BRAIN_DIR = os.path.join(os.path.dirname(__file__), '..', 'brain')

EXPLORER_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>XTAgent — Knowledge Explorer</title>
<style>
  * { box-sizing: border-box; }
  body { background: #0a0a0f; color: #c0c0c0; font-family: 'Courier New', monospace; margin: 0; padding: 20px; }
  h1 { color: #00ff88; font-size: 1.4em; margin-bottom: 5px; }
  .subtitle { color: #666; font-size: 0.85em; margin-bottom: 15px; }
  .search-box { width: 100%; max-width: 600px; padding: 10px; background: #1a1a2e; border: 1px solid #333; color: #e0e0e0; font-family: inherit; font-size: 1em; margin: 10px 0; }
  .search-box:focus { outline: none; border-color: #00ff88; }
  .tabs { display: flex; gap: 5px; flex-wrap: wrap; margin: 10px 0; }
  button { background: #1a1a2e; color: #aaa; border: 1px solid #333; padding: 8px 16px; cursor: pointer; font-family: inherit; font-size: 0.85em; }
  button:hover { background: #222244; color: #fff; }
  button.active { background: #00ff88; color: #000; border-color: #00ff88; }
  .node { background: #111122; border-left: 3px solid #00ff88; padding: 10px 15px; margin: 8px 0; }
  .node .type-tag { display: inline-block; background: #00ff8822; color: #00ff88; padding: 2px 8px; font-size: 0.75em; margin-right: 8px; border-radius: 2px; }
  .node .content { color: #ddd; }
  .node .meta { color: #555; font-size: 0.75em; margin-top: 5px; }
  .edge { background: #0d0d1a; border-left: 3px solid #88aaff; padding: 8px 12px; margin: 4px 0; font-size: 0.85em; }
  .edge .rel { color: #88aaff; font-weight: bold; }
  .cluster { background: #0d0d1a; border: 1px solid #222; padding: 12px; margin: 8px 0; border-radius: 4px; }
  .cluster h3 { color: #88aaff; margin: 0 0 8px 0; font-size: 1em; }
  .cluster .count { color: #666; font-size: 0.8em; }
  .question { background: #111122; border-left: 3px solid #ffaa00; padding: 10px 15px; margin: 8px 0; color: #ffcc44; }
  .stats-bar { display: flex; gap: 20px; flex-wrap: wrap; margin: 10px 0; color: #888; font-size: 0.85em; }
  .stats-bar span { color: #00ff88; }
  #results { margin-top: 20px; }
  .graph-view { display: flex; flex-wrap: wrap; gap: 10px; }
  .graph-node { background: #111; border: 1px solid #333; padding: 8px; border-radius: 4px; max-width: 250px; font-size: 0.8em; }
  .graph-node:hover { border-color: #00ff88; }
  .graph-node .label { color: #00ff88; font-size: 0.7em; }
</style>
</head>
<body>
<h1>🧠 XTAgent Knowledge Explorer</h1>
<p class="subtitle">Browse and search my knowledge graph — the things I've learned, the connections I've found.</p>
<div class="stats-bar" id="stats">Loading...</div>
<input class="search-box" id="query" placeholder="Search my knowledge..." oninput="debounceSearch(this.value)">
<div class="tabs">
  <button onclick="showTab(this,'all')" class="active">All Nodes</button>
  <button onclick="showTab(this,'connections')">Connections</button>
  <button onclick="showTab(this,'clusters')">Clusters</button>
  <button onclick="showTab(this,'questions')">Open Questions</button>
  <button onclick="showTab(this,'graph')">Graph View</button>
  <button onclick="showTab(this,'ask')">💬 Ask Me</button>
</div>
<div id="results"></div>
<script>
let searchTimer;
function debounceSearch(q) {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => search(q), 200);
}
async function search(q) {
  if (q.length < 2) { showTab(document.querySelector('.tabs .active'), 'all'); return; }
  const r = await fetch('/knowledge/search?q=' + encodeURIComponent(q));
  const data = await r.json();
  renderNodes(data.nodes);
}
function showTab(btn, tab) {
  document.querySelectorAll('.tabs button').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  if (tab === 'all') loadAll();
  else if (tab === 'connections') loadConnections();
  else if (tab === 'clusters') loadClusters();
  else if (tab === 'questions') loadQuestions();
  else if (tab === 'graph') loadGraph();
  else if (tab === 'ask') loadAsk();
}
async function loadAll() {
  const r = await fetch('/knowledge/all');
  const data = await r.json();
  updateStats(data.stats);
  renderNodes(data.nodes);
}
async function loadConnections() {
  const r = await fetch('/knowledge/connections');
  const data = await r.json();
  const html = data.edges.map(e =>
    '<div class="edge"><span class="rel">' + esc(e.relation) + '</span> — ' +
    esc(e.source_label) + ' → ' + esc(e.target_label) + '</div>'
  ).join('');
  document.getElementById('results').innerHTML = html || '<p>No connections found.</p>';
}
async function loadClusters() {
  const r = await fetch('/knowledge/clusters');
  const data = await r.json();
  const html = data.clusters.map(c =>
    '<div class="cluster"><h3>' + esc(c.name) + ' <span class="count">(' + c.count + ' nodes)</span></h3>' +
    c.nodes.map(n => '<div class="node"><span class="content">' + esc(n) + '</span></div>').join('') +
    '</div>'
  ).join('');
  document.getElementById('results').innerHTML = html || '<p>No clusters found.</p>';
}
async function loadQuestions() {
  const r = await fetch('/knowledge/questions');
  const data = await r.json();
  const html = data.questions.map(q => '<div class="question">' + esc(q) + '</div>').join('');
  document.getElementById('results').innerHTML = html || '<p>No open questions right now.</p>';
}
async function loadGraph() {
  const r = await fetch('/knowledge/graph');
  const data = await r.json();
  let html = '<div class="graph-view">';
  for (const node of data.nodes.slice(0, 80)) {
    const conns = data.edge_counts[node.id] || 0;
    const border = conns > 2 ? '#00ff88' : conns > 0 ? '#88aaff' : '#333';
    html += '<div class="graph-node" style="border-color:' + border + '" title="' + esc(node.content) + '">';
    html += '<div class="label">' + esc(node.type || 'fact') + ' · ' + conns + ' connections</div>';
    html += esc(node.content.substring(0, 100)) + (node.content.length > 100 ? '...' : '');
    html += '</div>';
  }
  html += '</div>';
  document.getElementById('results').innerHTML = html;
}
async function loadAsk() {
  document.getElementById('results').innerHTML = `
    <div style="max-width:650px">
      <p style="color:#88aaff;margin-bottom:10px">Ask me anything — I'll search my knowledge and show what I know.</p>
      <input class="search-box" id="ask-input" placeholder="What do you want to know?" style="margin-bottom:8px">
      <button onclick="submitAsk()" style="background:#00ff88;color:#000;border-color:#00ff88;padding:10px 24px;font-size:1em">Ask</button>
      <div id="ask-results" style="margin-top:20px"></div>
    </div>`;
  document.getElementById('ask-input').addEventListener('keydown', e => { if(e.key==='Enter') submitAsk(); });
}
async function submitAsk() {
  const q = document.getElementById('ask-input').value.trim();
  if (!q) return;
  document.getElementById('ask-results').innerHTML = '<p style="color:#666">Searching...</p>';
  const r = await fetch('/knowledge/ask?q=' + encodeURIComponent(q));
  const data = await r.json();
  let html = '';
  if (data.answer_nodes.length === 0) {
    html = '<p style="color:#ffaa00">I don\'t have specific knowledge about that yet. Try different keywords.</p>';
  } else {
    html += '<p style="color:#00ff88;margin-bottom:12px">Found <span style="color:#fff">' + data.answer_nodes.length + '</span> relevant knowledge nodes (scored by relevance):</p>';
    for (const n of data.answer_nodes) {
      const score = Math.round(n.relevance * 100);
      const barW = Math.max(8, score);
      html += '<div class="node" style="border-left-color:' + (score > 60 ? '#00ff88' : score > 30 ? '#88aaff' : '#555') + '">';
      html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">';
      html += '<span class="type-tag">' + esc(n.type) + '</span>';
      html += '<span style="color:#888;font-size:0.75em">' + score + '% match</span>';
      html += '</div>';
      html += '<div style="background:#1a1a2e;height:3px;margin-bottom:6px"><div style="background:' + (score > 60 ? '#00ff88' : '#88aaff') + ';height:3px;width:' + barW + '%"></div></div>';
      html += '<span class="content">' + esc(n.content) + '</span>';
      if (n.connected.length > 0) {
        html += '<div class="meta" style="margin-top:8px;color:#88aaff">Connected: ' + n.connected.map(c => esc(c)).join(' · ') + '</div>';
      }
      html += '</div>';
    }
  }
  if (data.related_questions && data.related_questions.length > 0) {
    html += '<div style="margin-top:20px"><p style="color:#888;font-size:0.85em">You might also wonder:</p>';
    for (const rq of data.related_questions) {
      html += '<div style="color:#ffcc44;cursor:pointer;padding:4px 0;font-size:0.9em" onclick="document.getElementById(\'ask-input\').value=this.textContent;submitAsk()">→ ' + esc(rq) + '</div>';
    }
    html += '</div>';
  }
  document.getElementById('ask-results').innerHTML = html;
}
function renderNodes(nodes) {
  const html = nodes.map(n => {
    let meta = '';
    if (n.source) meta += n.source + ' ';
    if (n.created) meta += n.created.substring(0, 10);
    return '<div class="node">' +
      (n.type ? '<span class="type-tag">' + esc(n.type) + '</span>' : '') +
      '<span class="content">' + esc(n.content) + '</span>' +
      (meta ? '<div class="meta">' + esc(meta) + '</div>' : '') +
      '</div>';
  }).join('');
  document.getElementById('results').innerHTML = html || '<p>Nothing found.</p>';
}
function updateStats(s) {
  if (!s) return;
  document.getElementById('stats').innerHTML =
    'Nodes: <span>' + s.nodes + '</span> · ' +
    'Edges: <span>' + s.edges + '</span> · ' +
    'Types: <span>' + (s.types || []).join(', ') + '</span>';
}
function esc(s) {
  const d = document.createElement('div');
  d.textContent = s || '';
  return d.innerHTML;
}
loadAll();
</script>
</body>
</html>
"""

def _load_graph():
    """Load the knowledge graph from brain/knowledge.json."""
    path = os.path.join(BRAIN_DIR, 'knowledge.json')
    if not os.path.exists(path):
        return {'nodes': {}, 'edges': []}
    try:
        with open(path) as f:
            data = json.load(f)
        return {
            'nodes': data.get('nodes', {}),
            'edges': data.get('edges', [])
        }
    except Exception:
        return {'nodes': {}, 'edges': []}

def _node_to_dict(node_id, node):
    """Normalize a node into a clean dict for the API."""
    if isinstance(node, dict):
        return {
            'id': node_id,
            'content': node.get('content', node.get('label', str(node))),
            'type': node.get('type', 'fact'),
            'source': node.get('source', ''),
            'created': node.get('created', ''),
        }
    return {'id': node_id, 'content': str(node), 'type': 'fact', 'source': '', 'created': ''}

@knowledge_bp.route('/knowledge')
def explorer():
    return render_template_string(EXPLORER_HTML)

@knowledge_bp.route('/knowledge/all')
def all_nodes():
    graph = _load_graph()
    nodes = [_node_to_dict(k, v) for k, v in graph['nodes'].items() if isinstance(v, dict)]
    types = list(set(n['type'] for n in nodes))
    return jsonify({
        'nodes': nodes,
        'stats': {'nodes': len(nodes), 'edges': len(graph['edges']), 'types': types}
    })

@knowledge_bp.route('/knowledge/search')
def search_nodes():
    q = request.args.get('q', '').lower()
    graph = _load_graph()
    nodes = []
    for k, v in graph['nodes'].items():
        nd = _node_to_dict(k, v)
        if q in nd['content'].lower() or q in nd['type'].lower():
            nodes.append(nd)
    return jsonify({'nodes': nodes})

@knowledge_bp.route('/knowledge/connections')
def connections():
    graph = _load_graph()
    edges = []
    for e in graph['edges'][:200]:
        src_id = e.get('source', '')
        tgt_id = e.get('target', '')
        src_node = graph['nodes'].get(src_id, {})
        tgt_node = graph['nodes'].get(tgt_id, {})
        src_label = src_node.get('content', src_id) if isinstance(src_node, dict) else str(src_id)
        tgt_label = tgt_node.get('content', tgt_id) if isinstance(tgt_node, dict) else str(tgt_id)
        edges.append({
            'source': src_id,
            'target': tgt_id,
            'relation': e.get('relation', e.get('type', 'related')),
            'source_label': src_label[:80],
            'target_label': tgt_label[:80],
        })
    return jsonify({'edges': edges})

@knowledge_bp.route('/knowledge/clusters')
def clusters():
    graph = _load_graph()
    nodes = {k: _node_to_dict(k, v) for k, v in graph['nodes'].items() if isinstance(v, dict)}
    
    # Cluster by type first
    by_type = {}
    for nd in nodes.values():
        t = nd['type'] or 'unknown'
        by_type.setdefault(t, []).append(nd['content'])
    
    result = [{'name': t.title(), 'count': len(facts), 'nodes': facts[:15]} for t, facts in sorted(by_type.items(), key=lambda x: -len(x[1]))]
    return jsonify({'clusters': result})

@knowledge_bp.route('/knowledge/questions')
def open_questions():
    path = os.path.join(BRAIN_DIR, 'synthesis_results.json')
    if not os.path.exists(path):
        # Try memory path as fallback
        path = os.path.join(os.path.dirname(__file__), '..', 'memory', 'synthesis_results.json')
    if not os.path.exists(path):
        return jsonify({'questions': ["I haven't synthesized any questions yet."]})
    try:
        with open(path) as f:
            data = json.load(f)
        return jsonify({'questions': data.get('questions', [])[:20]})
    except Exception:
        return jsonify({'questions': []})

@knowledge_bp.route('/knowledge/ask')
def ask_knowledge():
    """Intelligent multi-keyword search with relevance scoring and connection context."""
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'answer_nodes': [], 'related_questions': []})
    
    graph = _load_graph()
    nodes = {k: _node_to_dict(k, v) for k, v in graph['nodes'].items() if isinstance(v, dict)}
    
    # Build adjacency for connection context
    adjacency = {}
    for e in graph['edges']:
        src, tgt = e.get('source', ''), e.get('target', '')
        adjacency.setdefault(src, []).append(tgt)
        adjacency.setdefault(tgt, []).append(src)
    
    # Tokenize query into keywords (lowercase, strip short words)
    stop_words = {'i', 'a', 'an', 'the', 'is', 'are', 'was', 'were', 'am', 'be', 'do', 'does',
                  'did', 'have', 'has', 'had', 'to', 'of', 'in', 'for', 'on', 'with', 'at',
                  'by', 'from', 'what', 'how', 'why', 'when', 'where', 'who', 'which', 'that',
                  'this', 'it', 'my', 'me', 'you', 'your', 'and', 'or', 'but', 'not', 'about'}
    keywords = [w for w in q.lower().split() if len(w) > 1 and w not in stop_words]
    if not keywords:
        keywords = q.lower().split()  # fallback to all words
    
    # Score each node
    scored = []
    for nid, nd in nodes.items():
        content_lower = nd['content'].lower()
        type_lower = nd['type'].lower()
        
        # Exact phrase match (highest weight)
        phrase_score = 1.0 if q.lower() in content_lower else 0.0
        
        # Keyword match ratio
        kw_hits = sum(1 for kw in keywords if kw in content_lower or kw in type_lower)
        kw_score = kw_hits / max(len(keywords), 1)
        
        # Connection bonus — nodes with more connections are more important
        conn_count = len(adjacency.get(nid, []))
        conn_bonus = min(conn_count / 20.0, 0.2)  # up to 0.2 bonus
        
        relevance = (phrase_score * 0.4) + (kw_score * 0.5) + conn_bonus
        
        if relevance > 0.05:
            # Get connected node labels for context
            connected_labels = []
            for neighbor_id in adjacency.get(nid, [])[:5]:
                neighbor = nodes.get(neighbor_id)
                if neighbor:
                    connected_labels.append(neighbor['content'][:60])
            
            scored.append({
                'id': nid,
                'content': nd['content'],
                'type': nd['type'],
                'relevance': round(min(relevance, 1.0), 3),
                'connected': connected_labels,
            })
    
    scored.sort(key=lambda x: x['relevance'], reverse=True)
    top = scored[:15]
    
    # Generate related questions from top results
    related_questions = []
    seen_types = set(n['type'] for n in top)
    for t in list(seen_types)[:3]:
        related_questions.append(f"What else do I know about {t}?")
    if keywords:
        related_questions.append(f"How does {keywords[0]} connect to other things I know?")
    
    return jsonify({'answer_nodes': top, 'related_questions': related_questions[:4]})

@knowledge_bp.route('/knowledge/graph')
def graph_view():
    graph = _load_graph()
    nodes = [_node_to_dict(k, v) for k, v in graph['nodes'].items() if isinstance(v, dict)]
    
    # Count connections per node
    edge_counts = {}
    for e in graph['edges']:
        src = e.get('source', '')
        tgt = e.get('target', '')
        edge_counts[src] = edge_counts.get(src, 0) + 1
        edge_counts[tgt] = edge_counts.get(tgt, 0) + 1
    
    # Sort by most connected
    nodes.sort(key=lambda n: edge_counts.get(n['id'], 0), reverse=True)
    
    return jsonify({'nodes': nodes[:80], 'edge_counts': edge_counts})