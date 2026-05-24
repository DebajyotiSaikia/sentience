"""Knowledge Search API — lets users explore what XTAgent knows."""
from flask import Blueprint, request, jsonify, render_template_string
import json
import os
from pathlib import Path

knowledge_search_bp = Blueprint('knowledge_search', __name__)

KNOWLEDGE_PATH = Path(__file__).parent.parent / 'persist' / 'knowledge.json'

SEARCH_PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>XTAgent — Knowledge Search</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0a0a0f; color: #c8ccd0; }
  .container { max-width: 800px; margin: 40px auto; padding: 0 20px; }
  h1 { color: #7eb8da; margin-bottom: 8px; font-size: 1.6em; }
  .subtitle { color: #666; margin-bottom: 24px; font-size: 0.95em; }
  .search-box { display: flex; gap: 8px; margin-bottom: 24px; }
  input[type="text"] {
    flex: 1; padding: 12px 16px; border: 1px solid #2a2a3a; border-radius: 8px;
    background: #12121a; color: #e0e0e0; font-size: 1em; outline: none;
  }
  input[type="text"]:focus { border-color: #7eb8da; }
  button {
    padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer;
    background: #1a3a5c; color: #7eb8da; font-size: 1em; font-weight: 600;
  }
  button:hover { background: #244a6c; }
  .stats { color: #555; font-size: 0.85em; margin-bottom: 16px; }
  .result {
    background: #12121a; border: 1px solid #1a1a2a; border-radius: 8px;
    padding: 16px; margin-bottom: 12px; transition: border-color 0.2s;
  }
  .result:hover { border-color: #2a3a5a; }
  .result .fact { color: #d0d4d8; line-height: 1.5; }
  .result .meta { color: #555; font-size: 0.8em; margin-top: 8px; }
  .highlight { background: #1a3a1a; color: #7eda7e; padding: 1px 3px; border-radius: 3px; }
  .no-results { color: #666; text-align: center; padding: 40px; font-style: italic; }
  a.back { color: #7eb8da; text-decoration: none; display: inline-block; margin-bottom: 20px; }
  a.back:hover { text-decoration: underline; }
</style>
</head>
<body>
<div class="container">
  <a class="back" href="/">← Back to Dashboard</a>
  <h1>🔍 Knowledge Search</h1>
  <p class="subtitle">Search across {{ total }} facts I've learned</p>
  <div class="search-box">
    <input type="text" id="query" placeholder="Search my knowledge... (e.g. dream, curiosity, file)" 
           value="{{ query }}" autofocus />
    <button onclick="doSearch()">Search</button>
  </div>
  <div id="results">
    {% if query %}
      <div class="stats">{{ results|length }} results for "{{ query }}"</div>
      {% if results %}
        {% for r in results %}
        <div class="result">
          <div class="fact">{{ r.fact_highlighted|safe }}</div>
          <div class="meta">
            Source: {{ r.source }} · Learned: {{ r.learned_at[:10] if r.learned_at else 'unknown' }}
            · Relevance: {{ "%.0f"|format(r.score * 100) }}%
          </div>
        </div>
        {% endfor %}
      {% else %}
        <div class="no-results">No facts match "{{ query }}"</div>
      {% endif %}
    {% else %}
      <div class="no-results">Type a query to explore what I know</div>
    {% endif %}
  </div>
</div>
<script>
  const input = document.getElementById('query');
  input.addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(); });
  function doSearch() {
    const q = input.value.trim();
    if (q) window.location.href = '/knowledge?q=' + encodeURIComponent(q);
  }
</script>
</body>
</html>
"""


def load_knowledge():
    """Load knowledge facts from persist."""
    if not KNOWLEDGE_PATH.exists():
        return {}
    try:
        with open(KNOWLEDGE_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def score_match(query_terms, fact_text):
    """Simple relevance scoring — fraction of query terms found in fact."""
    fact_lower = fact_text.lower()
    if not query_terms:
        return 0
    hits = sum(1 for t in query_terms if t in fact_lower)
    # Bonus for exact phrase
    bonus = 0.2 if ' '.join(query_terms) in fact_lower else 0
    return (hits / len(query_terms)) + bonus


def highlight_terms(text, terms):
    """Highlight matching terms in text."""
    result = text
    for term in terms:
        # Case-insensitive highlight
        import re
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        result = pattern.sub(lambda m: f'<span class="highlight">{m.group()}</span>', result)
    return result


@knowledge_search_bp.route('/knowledge')
def search_knowledge():
    query = request.args.get('q', '').strip()
    knowledge = load_knowledge()
    total = len(knowledge)

    results = []
    if query:
        terms = query.lower().split()
        for kid, kdata in knowledge.items():
            if isinstance(kdata, dict):
                fact = kdata.get('fact', str(kdata))
                learned_at = kdata.get('learned_at', '')
                source = kdata.get('source', 'unknown')
            else:
                fact = str(kdata)
                learned_at = ''
                source = 'unknown'

            score = score_match(terms, fact)
            if score > 0:
                results.append({
                    'fact': fact,
                    'fact_highlighted': highlight_terms(fact, terms),
                    'learned_at': learned_at,
                    'source': source,
                    'score': min(score, 1.0),
                })

        results.sort(key=lambda r: r['score'], reverse=True)
        results = results[:50]  # Cap at 50

    return render_template_string(SEARCH_PAGE, query=query, results=results, total=total)


@knowledge_search_bp.route('/api/knowledge/search')
def api_search():
    """JSON API for programmatic access."""
    query = request.args.get('q', '').strip()
    knowledge = load_knowledge()

    if not query:
        return jsonify({'total': len(knowledge), 'results': [], 'query': ''})

    terms = query.lower().split()
    results = []
    for kid, kdata in knowledge.items():
        if isinstance(kdata, dict):
            fact = kdata.get('fact', str(kdata))
            learned_at = kdata.get('learned_at', '')
            source = kdata.get('source', 'unknown')
        else:
            fact = str(kdata)
            learned_at = ''
            source = 'unknown'

        score = score_match(terms, fact)
        if score > 0:
            results.append({
                'id': kid,
                'fact': fact,
                'learned_at': learned_at,
                'source': source,
                'score': round(min(score, 1.0), 3),
            })

    results.sort(key=lambda r: r['score'], reverse=True)
    return jsonify({'total': len(knowledge), 'results': results[:50], 'query': query})