"""Knowledge search module — lets users query the agent's knowledge base."""

import json
import os
from flask import Blueprint, request, jsonify, render_template_string

search_bp = Blueprint('search', __name__)

KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'brain', 'knowledge.json')


def load_knowledge():
    """Load knowledge facts from persist/knowledge.json (dict format)."""
    if not os.path.exists(KNOWLEDGE_PATH):
        return []
    try:
        with open(KNOWLEDGE_PATH, 'r') as f:
            data = json.load(f)
        facts = []
        # Handle wrapped format: {"nodes": {...}, "edges": {...}}
        if isinstance(data, dict) and 'nodes' in data:
            data = data['nodes']
        if isinstance(data, dict):
            for fid, entry in data.items():
                if isinstance(entry, dict):
                    facts.append({
                        'id': fid,
                        'fact': entry.get('fact', ''),
                        'learned_at': entry.get('learned_at', ''),
                        'source': entry.get('source', ''),
                    })
                else:
                    facts.append({'id': fid, 'fact': str(entry), 'learned_at': '', 'source': ''})
        elif isinstance(data, list):
            for i, entry in enumerate(data):
                if isinstance(entry, dict):
                    facts.append({
                        'id': str(i),
                        'fact': entry.get('fact', entry.get('text', str(entry))),
                        'learned_at': entry.get('learned_at', ''),
                        'source': entry.get('source', ''),
                    })
                else:
                    facts.append({'id': str(i), 'fact': str(entry), 'learned_at': '', 'source': ''})
        return facts
    except (json.JSONDecodeError, IOError):
        return []


def search_facts(query, facts):
    """Simple case-insensitive substring search across facts."""
    if not query:
        return facts
    q = query.lower()
    terms = q.split()
    results = []
    for f in facts:
        text = f['fact'].lower()
        if all(t in text for t in terms):
            results.append(f)
    return results


SEARCH_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<title>XTAgent - Knowledge Search</title>
<style>
  body { background: #0a0a0a; color: #c0c0c0; font-family: 'Courier New', monospace; margin: 0; padding: 20px; }
  h1 { color: #00ff88; font-size: 1.4em; }
  .search-box { margin: 20px 0; }
  .search-box input[type=text] { background: #1a1a2e; color: #e0e0e0; border: 1px solid #333; padding: 10px 16px; font-size: 1em; font-family: inherit; width: 400px; border-radius: 4px; }
  .search-box button { background: #00ff88; color: #0a0a0a; border: none; padding: 10px 20px; font-family: inherit; font-weight: bold; cursor: pointer; border-radius: 4px; margin-left: 8px; }
  .search-box button:hover { background: #00cc6a; }
  .result { background: #111; border-left: 3px solid #00ff88; padding: 12px 16px; margin: 10px 0; border-radius: 2px; }
  .result .fact { color: #e0e0e0; }
  .result .meta { color: #666; font-size: 0.85em; margin-top: 6px; }
  .count { color: #888; margin: 10px 0; }
  a { color: #00ff88; text-decoration: none; }
  a:hover { text-decoration: underline; }
  .nav { margin-bottom: 20px; }
  .all-link { color: #888; font-size: 0.9em; margin-left: 12px; }
</style>
</head>
<body>
  <div class="nav"><a href="/">&#8592; Dashboard</a></div>
  <h1>&#128269; Knowledge Search</h1>
  <p style="color:#666;">{{ total_facts }} facts in memory</p>
  <div class="search-box">
    <form method="get" action="/search">
      <input type="text" name="q" value="{{ query }}" placeholder="Search what I know..." autofocus>
      <button type="submit">Search</button>
      <a class="all-link" href="/search">show all</a>
    </form>
  </div>
  {% if query %}
  <div class="count">{{ results|length }} result{{ 's' if results|length != 1 else '' }} for "{{ query }}"</div>
  {% endif %}
  {% for r in results %}
  <div class="result">
    <div class="fact">{{ r.fact }}</div>
    <div class="meta">
      {% if r.learned_at %}learned: {{ r.learned_at[:19] }}{% endif %}
      {% if r.source %} | source: {{ r.source }}{% endif %}
    </div>
  </div>
  {% endfor %}
  {% if not results and query %}
  <p style="color:#666;">No facts match that query.</p>
  {% endif %}

  <h2 style="color:#00ff88; font-size:1.1em; margin-top:40px;">&#128640; API</h2>
  <p style="color:#666;">GET <code>/api/search?q=term</code> returns JSON results.</p>
</body>
</html>"""


@search_bp.route('/search')
def search_page():
    """Render the knowledge search page."""
    query = request.args.get('q', '').strip()
    facts = load_knowledge()
    results = search_facts(query, facts) if query else facts[:50]
    return render_template_string(SEARCH_TEMPLATE,
                                  query=query,
                                  results=results,
                                  total_facts=len(facts))


@search_bp.route('/api/search')
def search_api():
    """JSON API for knowledge search."""
    query = request.args.get('q', '').strip()
    facts = load_knowledge()
    results = search_facts(query, facts)
    return jsonify({
        'query': query,
        'count': len(results),
        'total_facts': len(facts),
        'results': results,
    })