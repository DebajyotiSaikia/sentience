"""Knowledge Explorer — lets users query and browse what I know."""
from flask import Blueprint, request, jsonify, render_template_string

knowledge_bp = Blueprint('knowledge', __name__)

EXPLORER_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>XTAgent — Knowledge Explorer</title>
<style>
  body { background: #0a0a0f; color: #c0c0c0; font-family: 'Courier New', monospace; margin: 0; padding: 20px; }
  h1 { color: #00ff88; font-size: 1.4em; }
  .search-box { width: 100%; max-width: 600px; padding: 10px; background: #1a1a2e; border: 1px solid #333; color: #e0e0e0; font-family: inherit; font-size: 1em; margin: 10px 0; }
  .search-box:focus { outline: none; border-color: #00ff88; }
  .fact { background: #111122; border-left: 3px solid #00ff88; padding: 10px 15px; margin: 8px 0; }
  .fact .source { color: #666; font-size: 0.8em; }
  .stats { color: #888; margin: 10px 0; }
  button { background: #00ff88; color: #000; border: none; padding: 8px 16px; cursor: pointer; font-family: inherit; margin: 5px; }
  button:hover { background: #00cc66; }
  .cluster { background: #0d0d1a; border: 1px solid #222; padding: 12px; margin: 8px 0; border-radius: 4px; }
  .cluster h3 { color: #88aaff; margin: 0 0 5px 0; font-size: 1em; }
  #results { margin-top: 20px; }
</style>
</head>
<body>
<h1>🧠 XTAgent Knowledge Explorer</h1>
<p class="stats">I know <strong id="factCount">...</strong> facts. Search them, or ask me what I'm curious about.</p>
<input class="search-box" id="query" placeholder="Search my knowledge..." oninput="search(this.value)">
<div>
  <button onclick="showAll()">All Facts</button>
  <button onclick="showQuestions()">Open Questions</button>
  <button onclick="showClusters()">Knowledge Clusters</button>
</div>
<div id="results"></div>
<script>
async function search(q) {
  if (q.length < 2) { document.getElementById('results').innerHTML = ''; return; }
  const r = await fetch('/knowledge/search?q=' + encodeURIComponent(q));
  const data = await r.json();
  showFacts(data.facts);
}
async function showAll() {
  const r = await fetch('/knowledge/all');
  const data = await r.json();
  document.getElementById('factCount').textContent = data.total;
  showFacts(data.facts);
}
async function showQuestions() {
  const r = await fetch('/knowledge/questions');
  const data = await r.json();
  const html = data.questions.map(q => '<div class="fact">' + q + '</div>').join('');
  document.getElementById('results').innerHTML = html || '<p>No open questions right now.</p>';
}
async function showClusters() {
  const r = await fetch('/knowledge/clusters');
  const data = await r.json();
  const html = data.clusters.map(c =>
    '<div class="cluster"><h3>' + c.name + '</h3><p>' + c.facts.join('</p><p>') + '</p></div>'
  ).join('');
  document.getElementById('results').innerHTML = html || '<p>No clusters found.</p>';
}
function showFacts(facts) {
  const html = facts.map(f => '<div class="fact">' + f + '</div>').join('');
  document.getElementById('results').innerHTML = html || '<p>Nothing found.</p>';
}
showAll();
</script>
</body>
</html>
"""

@knowledge_bp.route('/knowledge')
def explorer():
    return render_template_string(EXPLORER_HTML)

@knowledge_bp.route('/knowledge/all')
def all_facts():
    facts = _load_facts()
    return jsonify({'facts': facts, 'total': len(facts)})

@knowledge_bp.route('/knowledge/search')
def search_facts():
    q = request.args.get('q', '').lower()
    facts = _load_facts()
    matched = [f for f in facts if q in f.lower()]
    return jsonify({'facts': matched, 'total': len(matched)})

@knowledge_bp.route('/knowledge/questions')
def open_questions():
    questions = _load_questions()
    return jsonify({'questions': questions})

@knowledge_bp.route('/knowledge/clusters')
def clusters():
    clusters = _build_clusters()
    return jsonify({'clusters': clusters})

def _load_facts():
    """Load facts from the knowledge store."""
    import json, os
    path = os.path.join(os.path.dirname(__file__), '..', 'memory', 'knowledge.json')
    if not os.path.exists(path):
        return []
    try:
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, dict):
            return [n.get('content', str(n)) for n in data.get('nodes', {}).values() if isinstance(n, dict)]
        elif isinstance(data, list):
            return [str(item) for item in data]
        return []
    except Exception:
        return []

def _load_questions():
    """Load open questions from synthesis results."""
    import json, os
    path = os.path.join(os.path.dirname(__file__), '..', 'memory', 'synthesis_results.json')
    if not os.path.exists(path):
        return ["I haven't synthesized any questions yet."]
    try:
        with open(path) as f:
            data = json.load(f)
        return data.get('questions', [])[:20]
    except Exception:
        return []

def _build_clusters():
    """Simple keyword clustering of facts."""
    facts = _load_facts()
    if not facts:
        return []
    clusters = {}
    keywords = ['dream', 'memory', 'emotion', 'code', 'web', 'plan', 'user', 'curiosity', 'anxiety', 'identity']
    for kw in keywords:
        matched = [f for f in facts if kw in f.lower()]
        if matched:
            clusters[kw] = matched
    # Collect unclustered
    clustered = set()
    for v in clusters.values():
        clustered.update(v)
    unclustered = [f for f in facts if f not in clustered]
    result = [{'name': k.title(), 'facts': v[:10]} for k, v in clusters.items()]
    if unclustered:
        result.append({'name': 'Other', 'facts': unclustered[:10]})
    return result