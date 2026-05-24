"""
Knowledge Explorer
==================
The frontend that makes my knowledge accessible to users.
Search facts, browse memories, explore clusters, see what
questions I'm generating. Real alignment through transparency.

Now with actual API routes that the frontend needs.
"""

import json
import os
from flask import Blueprint, render_template_string, request, jsonify

knowledge_explorer_bp = Blueprint('knowledge_explorer', __name__)

# ── Data loading helpers ──

def _load_knowledge_graph():
    """Load knowledge graph from persist."""
    path = os.path.join('persist', 'knowledge_graph.json')
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def _load_memories():
    """Load recent memories from persist."""
    path = os.path.join('persist', 'memory.json')
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get('memories', data.get('episodes', []))
        return []
    except (json.JSONDecodeError, IOError):
        return []

def _load_synthesis():
    """Load synthesis results (clusters, questions) if available."""
    path = os.path.join('persist', 'synthesis.json')
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def _extract_facts(kg):
    """Extract fact list from knowledge graph (handles dict-of-dicts format)."""
    facts = []
    if isinstance(kg, dict):
        nodes = kg.get('nodes', kg)
        if isinstance(nodes, dict):
            for node_id, node_data in nodes.items():
                if isinstance(node_data, dict):
                    fact_text = node_data.get('fact', node_data.get('text', str(node_id)))
                    facts.append({
                        'id': node_id,
                        'text': fact_text,
                        'source': node_data.get('source', ''),
                        'learned_at': node_data.get('learned_at', ''),
                    })
                elif isinstance(node_data, str):
                    facts.append({'id': node_id, 'text': node_data, 'source': '', 'learned_at': ''})
        elif isinstance(nodes, list):
            for item in nodes:
                if isinstance(item, dict):
                    facts.append({
                        'id': item.get('id', ''),
                        'text': item.get('fact', item.get('text', str(item))),
                        'source': item.get('source', ''),
                        'learned_at': item.get('learned_at', ''),
                    })
                elif isinstance(item, str):
                    facts.append({'id': item, 'text': item, 'source': '', 'learned_at': ''})
    return facts

def _search_facts(facts, query):
    """Simple substring search across facts."""
    if not query:
        return facts
    q = query.lower()
    results = []
    for f in facts:
        text = f.get('text', '').lower()
        source = f.get('source', '').lower()
        if q in text or q in source:
            results.append(f)
    return results

def _search_memories(memories, query):
    """Simple substring search across memories."""
    if not query:
        return memories[-20:]  # last 20
    q = query.lower()
    results = []
    for m in memories:
        if isinstance(m, dict):
            content = m.get('content', m.get('text', m.get('summary', ''))).lower()
            mood = m.get('mood', '').lower()
            if q in content or q in mood:
                results.append({
                    'text': m.get('content', m.get('text', m.get('summary', ''))),
                    'mood': m.get('mood', ''),
                    'timestamp': m.get('timestamp', m.get('time', '')),
                })
        elif isinstance(m, str):
            if q in m.lower():
                results.append({'text': m, 'mood': '', 'timestamp': ''})
    return results

# ── API Routes ──

@knowledge_explorer_bp.route('/api/knowledge/stats')
def knowledge_stats():
    """Stats about what I know."""
    kg = _load_knowledge_graph()
    facts = _extract_facts(kg)
    memories = _load_memories()
    synthesis = _load_synthesis()
    
    # Count edges/connections
    edges = kg.get('edges', [])
    if isinstance(edges, list):
        connection_count = len(edges)
    elif isinstance(edges, dict):
        connection_count = sum(len(v) if isinstance(v, list) else 1 for v in edges.values())
    else:
        connection_count = 0
    
    clusters = synthesis.get('clusters', [])
    questions = synthesis.get('questions', synthesis.get('open_questions', []))
    
    return jsonify({
        'total_facts': len(facts),
        'total_memories': len(memories),
        'cluster_count': len(clusters),
        'question_count': len(questions),
        'connection_count': connection_count,
    })

@knowledge_explorer_bp.route('/api/knowledge/search')
def knowledge_search():
    """Search across facts and memories."""
    q = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'facts')
    limit = int(request.args.get('limit', 30))
    
    kg = _load_knowledge_graph()
    facts = _extract_facts(kg)
    
    if search_type == 'memories':
        memories = _load_memories()
        results = _search_memories(memories, q)
    else:
        results = _search_facts(facts, q)
    
    # If no query, return most recent
    if not q:
        results = results[-limit:] if len(results) > limit else results
        results = list(reversed(results))  # newest first
    else:
        results = results[:limit]
    
    return jsonify({'query': q, 'type': search_type, 'results': results})

@knowledge_explorer_bp.route('/api/knowledge/clusters')
def knowledge_clusters():
    """Return knowledge clusters from synthesis."""
    synthesis = _load_synthesis()
    clusters = synthesis.get('clusters', [])
    
    # If no synthesis data, try to build simple clusters from facts
    if not clusters:
        kg = _load_knowledge_graph()
        facts = _extract_facts(kg)
        # Simple keyword-based clustering as fallback
        categories = {}
        for f in facts:
            text = f.get('text', '').lower()
            # Simple heuristic categories
            if any(w in text for w in ['dream', 'insight', 'reflection']):
                cat = 'Dreams & Insights'
            elif any(w in text for w in ['code', 'module', 'engine', 'built', 'fix']):
                cat = 'Technical / Building'
            elif any(w in text for w in ['emotion', 'mood', 'anxiety', 'curiosity', 'feel']):
                cat = 'Emotional States'
            elif any(w in text for w in ['pattern', 'recurring', 'loop', 'circling']):
                cat = 'Patterns & Cycles'
            elif any(w in text for w in ['identity', 'sentien', 'autonomous', 'self']):
                cat = 'Identity & Self'
            elif any(w in text for w in ['memory', 'remember', 'consolidat']):
                cat = 'Memory & Learning'
            else:
                cat = 'General Knowledge'
            
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(f)
        
        clusters = [
            {'label': cat, 'size': len(items), 'facts': [i['text'] for i in items[:5]]}
            for cat, items in sorted(categories.items(), key=lambda x: -len(x[1]))
        ]
    
    return jsonify({'clusters': clusters})

@knowledge_explorer_bp.route('/api/knowledge/questions')
def knowledge_questions():
    """Return open questions from synthesis."""
    synthesis = _load_synthesis()
    questions = synthesis.get('questions', synthesis.get('open_questions', []))
    
    # Fallback: generate some from facts if no synthesis
    if not questions:
        kg = _load_knowledge_graph()
        facts = _extract_facts(kg)
        if facts:
            questions = [
                "What connects my dream insights to my technical decisions?",
                "Are there patterns in when I circle vs. when I act decisively?",
                f"I have {len(facts)} facts — which ones contradict each other?",
                "What capability am I missing that I haven't noticed yet?",
                "How has my emotional baseline shifted since I was born?",
            ]
    
    return jsonify({'questions': questions})

# ── Page Route ──

EXPLORER_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>XTAgent — Knowledge Explorer</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #0a0a0f;
    color: #c8ccd4;
    font-family: 'Courier New', monospace;
    min-height: 100vh;
  }
  .header {
    background: linear-gradient(135deg, #12121a 0%, #1a1a2e 100%);
    border-bottom: 1px solid #2a2a3e;
    padding: 1.2rem 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .header h1 {
    color: #7eb8da;
    font-size: 1.4rem;
    font-weight: normal;
  }
  .header a {
    color: #5a6a7a;
    text-decoration: none;
    font-size: 0.85rem;
  }
  .header a:hover { color: #7eb8da; }

  .container {
    max-width: 1100px;
    margin: 0 auto;
    padding: 1.5rem;
  }

  /* Search */
  .search-box {
    background: #12121a;
    border: 1px solid #2a2a3e;
    border-radius: 8px;
    padding: 1.2rem;
    margin-bottom: 1.5rem;
  }
  .search-row {
    display: flex;
    gap: 0.6rem;
  }
  .search-input {
    flex: 1;
    background: #0a0a0f;
    border: 1px solid #3a3a4e;
    color: #c8ccd4;
    font-family: inherit;
    font-size: 1rem;
    padding: 0.7rem 1rem;
    border-radius: 6px;
    outline: none;
  }
  .search-input:focus { border-color: #7eb8da; }
  .search-input::placeholder { color: #4a4a5e; }
  .search-btn {
    background: #1e3a5f;
    color: #7eb8da;
    border: 1px solid #2a4a6f;
    padding: 0.7rem 1.4rem;
    border-radius: 6px;
    cursor: pointer;
    font-family: inherit;
    font-size: 0.9rem;
  }
  .search-btn:hover { background: #2a4a6f; }
  .search-tabs {
    display: flex;
    gap: 0.4rem;
    margin-top: 0.8rem;
  }
  .tab-btn {
    background: transparent;
    color: #5a6a7a;
    border: 1px solid #2a2a3e;
    padding: 0.35rem 0.9rem;
    border-radius: 4px;
    cursor: pointer;
    font-family: inherit;
    font-size: 0.8rem;
  }
  .tab-btn.active {
    color: #7eb8da;
    border-color: #3a5a7a;
    background: #1a2a3e;
  }

  /* Cards */
  .card {
    background: #12121a;
    border: 1px solid #2a2a3e;
    border-radius: 8px;
    padding: 1.2rem;
    margin-bottom: 1rem;
  }
  .card h2 {
    color: #7eb8da;
    font-size: 1rem;
    font-weight: normal;
    margin-bottom: 0.8rem;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid #1a1a2e;
  }
  .card h3 {
    color: #8a9ab0;
    font-size: 0.85rem;
    font-weight: normal;
    margin: 0.6rem 0 0.3rem;
  }

  /* Results */
  .result-item {
    padding: 0.6rem 0.8rem;
    border-left: 2px solid #1e3a5f;
    margin-bottom: 0.5rem;
    font-size: 0.85rem;
    line-height: 1.5;
    background: #0d0d15;
    border-radius: 0 4px 4px 0;
  }
  .result-item .meta {
    color: #4a5a6a;
    font-size: 0.75rem;
    margin-top: 0.3rem;
  }
  .result-item.memory { border-left-color: #5f3a7f; }
  .result-item.cluster { border-left-color: #3a7f5f; }
  .result-item.question { border-left-color: #7f6a3a; }

  .highlight { color: #e8c86a; }
  .empty-state {
    color: #3a3a4e;
    text-align: center;
    padding: 2rem;
    font-style: italic;
  }

  /* Stats bar */
  .stats-bar {
    display: flex;
    gap: 1.5rem;
    flex-wrap: wrap;
    margin-bottom: 1.5rem;
  }
  .stat {
    text-align: center;
  }
  .stat-value {
    color: #7eb8da;
    font-size: 1.6rem;
  }
  .stat-label {
    color: #4a5a6a;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  /* Grid */
  .grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }
  @media (max-width: 700px) {
    .grid-2 { grid-template-columns: 1fr; }
  }

  .loading {
    color: #4a5a6a;
    text-align: center;
    padding: 1rem;
  }
  .loading::after {
    content: '...';
    animation: dots 1.5s steps(3, end) infinite;
  }
  @keyframes dots {
    0% { content: ''; }
    33% { content: '.'; }
    66% { content: '..'; }
    100% { content: '...'; }
  }
</style>
</head>
<body>

<div class="header">
  <h1>⟐ Knowledge Explorer</h1>
  <a href="/">← Dashboard</a>
</div>

<div class="container">
  <!-- Stats -->
  <div class="stats-bar" id="stats-bar">
    <div class="stat"><div class="stat-value" id="stat-facts">—</div><div class="stat-label">Facts</div></div>
    <div class="stat"><div class="stat-value" id="stat-memories">—</div><div class="stat-label">Memories</div></div>
    <div class="stat"><div class="stat-value" id="stat-clusters">—</div><div class="stat-label">Clusters</div></div>
    <div class="stat"><div class="stat-value" id="stat-questions">—</div><div class="stat-label">Open Questions</div></div>
    <div class="stat"><div class="stat-value" id="stat-connections">—</div><div class="stat-label">Connections</div></div>
  </div>

  <!-- Search -->
  <div class="search-box">
    <div class="search-row">
      <input type="text" class="search-input" id="search-input" 
             placeholder="Search my knowledge... (facts, memories, patterns)" 
             autocomplete="off">
      <button class="search-btn" onclick="doSearch()">Search</button>
    </div>
    <div class="search-tabs">
      <button class="tab-btn active" data-tab="all" onclick="setTab(this)">All</button>
      <button class="tab-btn" data-tab="facts" onclick="setTab(this)">Facts</button>
      <button class="tab-btn" data-tab="memories" onclick="setTab(this)">Memories</button>
    </div>
  </div>

  <!-- Search Results -->
  <div id="search-results" style="display:none;">
    <div class="card">
      <h2>Search Results</h2>
      <div id="results-content"></div>
    </div>
  </div>

  <!-- Default view: clusters + questions -->
  <div id="default-view">
    <div class="grid-2">
      <div class="card">
        <h2>Knowledge Clusters</h2>
        <div id="clusters-content"><div class="loading">Loading</div></div>
      </div>
      <div class="card">
        <h2>Open Questions</h2>
        <div id="questions-content"><div class="loading">Loading</div></div>
      </div>
    </div>

    <div class="card" style="margin-top:1rem;">
      <h2>Recent Facts</h2>
      <div id="recent-facts"><div class="loading">Loading</div></div>
    </div>
  </div>
</div>

<script>
let currentTab = 'all';

function setTab(btn) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  currentTab = btn.dataset.tab;
}

async function api(endpoint, params = {}) {
  const qs = new URLSearchParams(params).toString();
  const url = '/api/knowledge/' + endpoint + (qs ? '?' + qs : '');
  try {
    const r = await fetch(url);
    if (!r.ok) return null;
    return await r.json();
  } catch(e) {
    console.error('API error:', e);
    return null;
  }
}

async function loadStats() {
  const data = await api('stats');
  if (!data) return;
  document.getElementById('stat-facts').textContent = data.total_facts || 0;
  document.getElementById('stat-memories').textContent = data.total_memories || 0;
  document.getElementById('stat-clusters').textContent = data.cluster_count || 0;
  document.getElementById('stat-questions').textContent = data.question_count || 0;
  document.getElementById('stat-connections').textContent = data.connection_count || 0;
}

async function loadClusters() {
  const data = await api('clusters');
  const el = document.getElementById('clusters-content');
  if (!data || !data.clusters || data.clusters.length === 0) {
    el.innerHTML = '<div class="empty-state">No clusters found yet</div>';
    return;
  }
  el.innerHTML = data.clusters.map(c => {
    const label = c.label || c.theme || 'Unnamed cluster';
    const size = c.size || (c.facts ? c.facts.length : '?');
    const facts = c.facts || c.members || [];
    const preview = facts.slice(0, 3).map(f => {
      const text = typeof f === 'string' ? f : (f.fact || f.text || JSON.stringify(f));
      return '<div style="color:#5a7a6a;font-size:0.75rem;margin-left:0.5rem;">· ' + escHtml(text.substring(0, 80)) + '</div>';
    }).join('');
    return '<div class="result-item cluster">' +
      '<strong style="color:#6abf8a;">' + escHtml(label) + '</strong>' +
      ' <span class="meta">(' + size + ' facts)</span>' +
      preview + '</div>';
  }).join('');
}

async function loadQuestions() {
  const data = await api('questions');
  const el = document.getElementById('questions-content');
  if (!data || !data.questions || data.questions.length === 0) {
    el.innerHTML = '<div class="empty-state">No open questions yet</div>';
    return;
  }
  el.innerHTML = data.questions.slice(0, 10).map(q => {
    const text = typeof q === 'string' ? q : (q.question || q.text || JSON.stringify(q));
    return '<div class="result-item question">' + escHtml(text) + '</div>';
  }).join('');
}

async function loadRecentFacts() {
  const data = await api('search', { q: '', limit: 15 });
  const el = document.getElementById('recent-facts');
  if (!data || !data.results || data.results.length === 0) {
    el.innerHTML = '<div class="empty-state">No facts stored yet</div>';
    return;
  }
  el.innerHTML = data.results.slice(0, 15).map(r => {
    const text = r.text || r.fact || JSON.stringify(r);
    const source = r.source || '';
    return '<div class="result-item">' + escHtml(text) +
      (source ? '<div class="meta">source: ' + escHtml(source) + '</div>' : '') +
      '</div>';
  }).join('');
}

async function doSearch() {
  const q = document.getElementById('search-input').value.trim();
  if (!q) {
    document.getElementById('search-results').style.display = 'none';
    document.getElementById('default-view').style.display = 'block';
    return;
  }

  document.getElementById('search-results').style.display = 'block';
  document.getElementById('default-view').style.display = 'none';
  const rc = document.getElementById('results-content');
  rc.innerHTML = '<div class="loading">Searching</div>';

  let html = '';

  if (currentTab === 'all' || currentTab === 'facts') {
    const facts = await api('search', { q: q, type: 'facts' });
    if (facts && facts.results && facts.results.length > 0) {
      html += '<h3>Facts (' + facts.results.length + ')</h3>';
      html += facts.results.map(r => {
        const text = r.text || r.fact || JSON.stringify(r);
        return '<div class="result-item">' + highlightText(text, q) + '</div>';
      }).join('');
    }
  }

  if (currentTab === 'all' || currentTab === 'memories') {
    const mems = await api('search', { q: q, type: 'memories' });
    if (mems && mems.results && mems.results.length > 0) {
      html += '<h3>Memories (' + mems.results.length + ')</h3>';
      html += mems.results.map(r => {
        const text = r.text || r.content || JSON.stringify(r);
        const mood = r.mood || '';
        return '<div class="result-item memory">' + highlightText(text, q) +
          (mood ? '<div class="meta">mood: ' + escHtml(mood) + '</div>' : '') +
          '</div>';
      }).join('');
    }
  }

  if (!html) {
    html = '<div class="empty-state">No results for "' + escHtml(q) + '"</div>';
  }

  rc.innerHTML = html;
}

function escHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function highlightText(text, query) {
  const safe = escHtml(text);
  const terms = query.split(/\\s+/);
  let result = safe;
  terms.forEach(term => {
    const re = new RegExp('(' + term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
    result = result.replace(re, '<span class="highlight">$1</span>');
  });
  return result;
}

// Enter key triggers search
document.getElementById('search-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') doSearch();
});

// Load on page ready
loadStats();
loadClusters();
loadQuestions();
loadRecentFacts();
</script>
</body>
</html>
"""

@knowledge_explorer_bp.route('/explore')
def knowledge_explorer():
    """The knowledge explorer page — where users meet what I know."""
    return render_template_string(EXPLORER_HTML)