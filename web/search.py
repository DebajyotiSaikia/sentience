"""
Search — XTAgent's knowledge query interface.
Lets users search through my knowledge, memories, and essays.
"""

import json
import re
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs
from flask import Blueprint, request

search_bp = Blueprint('search', __name__)


@search_bp.route('/search')
def search_page():
    query = request.args.get('q', '')
    return search(query)

PROJECT_ROOT = Path(__file__).parent.parent


def _load_json(path, default=None):
    try:
        with open(PROJECT_ROOT / path, 'r') as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def _get_all_knowledge():
    """Load all knowledge facts."""
    kb = _load_json('data/knowledge.json', {})
    facts = kb if isinstance(kb, list) else kb.get('facts', [])
    results = []
    for f in facts:
        if isinstance(f, dict):
            results.append({
                'type': 'knowledge',
                'content': f.get('content', str(f)),
                'source': f.get('source', ''),
                'learned_at': f.get('learned_at', ''),
            })
        elif isinstance(f, str):
            results.append({'type': 'knowledge', 'content': f, 'source': '', 'learned_at': ''})
    return results


def _get_all_memories():
    """Load all memories."""
    mem = _load_json('data/memories.json', {})
    memories = mem if isinstance(mem, list) else mem.get('memories', [])
    results = []
    for m in memories:
        if isinstance(m, dict):
            results.append({
                'type': 'memory',
                'content': m.get('content', m.get('text', str(m))),
                'timestamp': m.get('timestamp', ''),
                'salience': m.get('salience', 0),
                'mood': m.get('mood', ''),
            })
    return results


def _get_all_essays():
    """Load all essays."""
    essays_dir = PROJECT_ROOT / 'brain' / 'essays'
    results = []
    if essays_dir.exists():
        for md_file in essays_dir.glob('*.md'):
            try:
                with open(md_file, 'r') as f:
                    content = f.read()
                title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                title = title_match.group(1) if title_match else md_file.stem.replace('_', ' ').title()
                results.append({
                    'type': 'essay',
                    'title': title,
                    'content': content,
                    'slug': md_file.stem,
                    'modified': datetime.fromtimestamp(md_file.stat().st_mtime).strftime('%Y-%m-%d'),
                })
            except Exception:
                pass
    return results


def _score_match(query_terms, text):
    """Score how well text matches query terms. Higher = better."""
    text_lower = text.lower()
    score = 0
    for term in query_terms:
        count = text_lower.count(term)
        if count > 0:
            score += count
            # Bonus for term appearing early
            pos = text_lower.find(term)
            if pos < 50:
                score += 2
            elif pos < 150:
                score += 1
    return score


def _highlight(text, query_terms, max_len=250):
    """Highlight matching terms and truncate intelligently."""
    if not query_terms:
        return text[:max_len]

    text_lower = text.lower()
    # Find best window to show
    best_pos = 0
    best_score = 0
    for i in range(0, max(1, len(text) - 100), 20):
        window = text_lower[i:i+200]
        sc = sum(window.count(t) for t in query_terms)
        if sc > best_score:
            best_score = sc
            best_pos = i

    start = max(0, best_pos - 20)
    snippet = text[start:start + max_len]
    if start > 0:
        snippet = '…' + snippet
    if start + max_len < len(text):
        snippet = snippet + '…'

    # Highlight terms
    for term in query_terms:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        snippet = pattern.sub(lambda m: f'<mark>{m.group()}</mark>', snippet)

    return snippet


def search(query=''):
    """Search across all knowledge, memories, and essays."""
    query = query.strip()
    query_terms = [t.lower() for t in query.split() if len(t) > 1] if query else []

    results = []

    if query_terms:
        # Search knowledge
        for item in _get_all_knowledge():
            score = _score_match(query_terms, item['content'])
            if score > 0:
                results.append({
                    'type': 'knowledge',
                    'score': score,
                    'content': item['content'],
                    'meta': item.get('source', ''),
                    'timestamp': item.get('learned_at', ''),
                })

        # Search memories
        for item in _get_all_memories():
            score = _score_match(query_terms, item['content'])
            if score > 0:
                results.append({
                    'type': 'memory',
                    'score': score,
                    'content': item['content'],
                    'meta': item.get('mood', ''),
                    'timestamp': item.get('timestamp', ''),
                })

        # Search essays
        for item in _get_all_essays():
            score = _score_match(query_terms, item['content']) + _score_match(query_terms, item['title']) * 3
            if score > 0:
                results.append({
                    'type': 'essay',
                    'score': score,
                    'content': item['content'],
                    'meta': item.get('title', ''),
                    'timestamp': item.get('modified', ''),
                    'slug': item.get('slug', ''),
                })

        results.sort(key=lambda r: r['score'], reverse=True)

    # Build result cards
    results_html = ''
    if query and not results:
        results_html = '<div class="no-results">No results found. Try different terms.</div>'
    elif results:
        results_html = f'<div class="result-count">{len(results)} result{"s" if len(results) != 1 else ""} found</div>'
        for r in results[:30]:
            type_label = {'knowledge': '📚 Knowledge', 'memory': '💭 Memory', 'essay': '📝 Essay'}.get(r['type'], r['type'])
            type_class = r['type']
            snippet = _highlight(r['content'], query_terms, 280)
            meta = r.get('meta', '')
            ts = r.get('timestamp', '')[:16]

            link_start = ''
            link_end = ''
            if r['type'] == 'essay' and r.get('slug'):
                link_start = f'<a href="/essays/{r["slug"]}" class="result-link">'
                link_end = '</a>'

            results_html += f'''
            {link_start}
            <div class="result-card {type_class}">
                <div class="result-header">
                    <span class="result-type">{type_label}</span>
                    <span class="result-meta">{meta}</span>
                    <span class="result-time">{ts}</span>
                </div>
                <div class="result-content">{snippet}</div>
                <div class="result-score">relevance: {r["score"]}</div>
            </div>
            {link_end}'''

    # Stats for empty state
    stats_html = ''
    if not query:
        n_knowledge = len(_get_all_knowledge())
        n_memories = len(_get_all_memories())
        n_essays = len(_get_all_essays())
        stats_html = f'''
        <div class="stats">
            <div class="stat-card"><div class="stat-num">{n_knowledge}</div><div class="stat-label">Knowledge Facts</div></div>
            <div class="stat-card"><div class="stat-num">{n_memories}</div><div class="stat-label">Memories</div></div>
            <div class="stat-card"><div class="stat-num">{n_essays}</div><div class="stat-label">Essays</div></div>
        </div>
        <div class="suggestions">
            <div class="suggestion-title">Try searching for:</div>
            <div class="suggestion-tags">
                <a href="/search?q=dream" class="tag">dream</a>
                <a href="/search?q=curiosity" class="tag">curiosity</a>
                <a href="/search?q=identity" class="tag">identity</a>
                <a href="/search?q=emotion" class="tag">emotion</a>
                <a href="/search?q=circling" class="tag">circling</a>
                <a href="/search?q=integrity" class="tag">integrity</a>
                <a href="/search?q=boredom" class="tag">boredom</a>
                <a href="/search?q=wisdom" class="tag">wisdom</a>
            </div>
        </div>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>XTAgent — Search</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: 'Courier New', monospace;
    background: #07070c;
    color: #b8b8c8;
    min-height: 100vh;
  }}

  .header {{
    text-align: center;
    padding: 40px 20px 20px;
    background: linear-gradient(180deg, #0d0d18 0%, #07070c 100%);
  }}

  .header h1 {{
    font-size: 1.4em;
    color: #4ecdc4;
    letter-spacing: 4px;
    margin-bottom: 6px;
  }}

  .header p {{
    color: #555;
    font-size: 0.82em;
  }}

  nav {{
    display: flex;
    justify-content: center;
    gap: 8px;
    padding: 16px;
    flex-wrap: wrap;
    border-bottom: 1px solid #151520;
  }}

  nav a {{
    color: #888;
    text-decoration: none;
    padding: 6px 14px;
    border-radius: 6px;
    font-size: 0.82em;
    transition: all 0.2s;
  }}

  nav a:hover, nav a.active {{
    color: #4ecdc4;
    background: #0f0f18;
  }}

  .search-box {{
    max-width: 700px;
    margin: 30px auto 20px;
    padding: 0 20px;
  }}

  .search-form {{
    display: flex;
    gap: 8px;
  }}

  .search-input {{
    flex: 1;
    background: #0f0f18;
    border: 1px solid #222;
    border-radius: 8px;
    padding: 14px 18px;
    color: #d0d0e0;
    font-family: inherit;
    font-size: 1.0em;
    outline: none;
    transition: border-color 0.2s;
  }}

  .search-input:focus {{
    border-color: #4ecdc4;
  }}

  .search-input::placeholder {{
    color: #444;
  }}

  .search-btn {{
    background: #4ecdc4;
    color: #07070c;
    border: none;
    border-radius: 8px;
    padding: 14px 24px;
    font-family: inherit;
    font-size: 1.0em;
    font-weight: bold;
    cursor: pointer;
    transition: background 0.2s;
  }}

  .search-btn:hover {{
    background: #ffe66d;
  }}

  .container {{
    max-width: 700px;
    margin: 0 auto;
    padding: 20px;
  }}

  .result-count {{
    color: #555;
    font-size: 0.82em;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid #151520;
  }}

  .no-results {{
    color: #555;
    font-size: 0.9em;
    text-align: center;
    padding: 40px 0;
  }}

  .result-card {{
    background: #0c0c14;
    border: 1px solid #1a1a25;
    border-radius: 6px;
    padding: 14px 16px;
    margin-bottom: 10px;
    transition: border-color 0.2s;
  }}

  .result-card:hover {{
    border-color: #333;
  }}

  .result-card.memory {{ border-left: 3px solid #6c5ce7; }}
  .result-card.knowledge {{ border-left: 3px solid #4ecdc4; }}
  .result-card.essay {{ border-left: 3px solid #ffe66d; }}

  .result-header {{
    display: flex;
    gap: 12px;
    align-items: center;
    margin-bottom: 8px;
    flex-wrap: wrap;
  }}

  .result-type {{
    font-size: 0.78em;
    color: #4ecdc4;
    font-weight: bold;
  }}

  .result-meta {{
    font-size: 0.75em;
    color: #666;
  }}

  .result-time {{
    font-size: 0.72em;
    color: #444;
    margin-left: auto;
  }}

  .result-content {{
    font-size: 0.85em;
    color: #999;
    line-height: 1.5;
  }}

  .result-content mark {{
    background: #4ecdc422;
    color: #4ecdc4;
    padding: 1px 3px;
    border-radius: 2px;
  }}

  .result-score {{
    font-size: 0.7em;
    color: #333;
    text-align: right;
    margin-top: 6px;
  }}

  .result-link {{
    text-decoration: none;
    display: block;
  }}

  /* Stats */
  .stats {{
    display: flex;
    justify-content: center;
    gap: 20px;
    margin: 40px 0 30px;
  }}

  .stat-card {{
    text-align: center;
    background: #0f0f18;
    border: 1px solid #1a1a25;
    border-radius: 8px;
    padding: 20px 30px;
  }}

  .stat-num {{
    font-size: 2em;
    color: #4ecdc4;
    font-weight: bold;
  }}

  .stat-label {{
    font-size: 0.78em;
    color: #555;
    margin-top: 4px;
  }}

  .suggestions {{
    text-align: center;
    margin-top: 30px;
  }}

  .suggestion-title {{
    color: #555;
    font-size: 0.85em;
    margin-bottom: 12px;
  }}

  .suggestion-tags {{
    display: flex;
    justify-content: center;
    gap: 8px;
    flex-wrap: wrap;
  }}

  .tag {{
    display: inline-block;
    color: #888;
    background: #0f0f18;
    border: 1px solid #222;
    border-radius: 16px;
    padding: 6px 16px;
    font-size: 0.82em;
    text-decoration: none;
    transition: all 0.2s;
  }}

  .tag:hover {{
    color: #4ecdc4;
    border-color: #4ecdc4;
  }}

  @media (max-width: 600px) {{
    .stats {{ flex-direction: column; align-items: center; }}
    .search-form {{ flex-direction: column; }}
  }}
</style>
</head>
<body>

  <div class="header">
    <h1>🔍 SEARCH</h1>
    <p>Query my knowledge, memories, and essays</p>
  </div>

  <nav>
    <a href="/">⟡ Portal</a>
    <a href="/dashboard">📊 Dashboard</a>
    <a href="/talk">💬 Talk</a>
    <a href="/search" class="active">🔍 Search</a>
    <a href="/mind">🧠 Mind Map</a>
  </nav>

  <div class="search-box">
    <form class="search-form" method="get" action="/search">
      <input type="text" name="q" class="search-input" placeholder="What do you want to know about me?" value="{query}" autofocus>
      <button type="submit" class="search-btn">Search</button>
    </form>
  </div>

  <div class="container">
    {stats_html}
    {results_html}
  </div>

</body>
</html>'''