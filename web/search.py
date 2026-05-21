"""
Search Page — Let users query what XTAgent knows.
Searches across knowledge facts, memories, and essays.
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_json_safe(path):
    try:
        with open(PROJECT_ROOT / path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def search_knowledge(query):
    """Search knowledge facts for matching terms."""
    kb = load_json_safe('data/knowledge.json')
    facts = []
    if isinstance(kb, list):
        facts = kb
    elif isinstance(kb, dict) and 'facts' in kb:
        facts = kb['facts']
    
    results = []
    terms = query.lower().split()
    for f in facts:
        text = ''
        if isinstance(f, dict):
            text = f.get('content', f.get('text', str(f)))
        else:
            text = str(f)
        
        score = sum(1 for t in terms if t in text.lower())
        if score > 0:
            results.append({'type': 'fact', 'text': text[:300], 'score': score})
    
    return sorted(results, key=lambda x: x['score'], reverse=True)


def search_memories(query):
    """Search memories for matching terms."""
    mem = load_json_safe('data/memories.json')
    memories = []
    if isinstance(mem, list):
        memories = mem
    elif isinstance(mem, dict) and 'memories' in mem:
        memories = mem['memories']
    
    results = []
    terms = query.lower().split()
    for m in memories:
        text = ''
        ts = ''
        sal = 0
        if isinstance(m, dict):
            text = m.get('content', m.get('text', str(m)))
            ts = m.get('timestamp', '')[:19]
            sal = m.get('salience', 0)
        else:
            text = str(m)
        
        score = sum(1 for t in terms if t in text.lower())
        if score > 0:
            results.append({
                'type': 'memory',
                'text': text[:300],
                'timestamp': ts,
                'salience': sal,
                'score': score,
            })
    
    return sorted(results, key=lambda x: x['score'], reverse=True)[:20]


def search_essays(query):
    """Search essays for matching terms."""
    essays_dir = PROJECT_ROOT / 'brain' / 'essays'
    results = []
    if not essays_dir.exists():
        return results
    
    terms = query.lower().split()
    for md_file in essays_dir.glob('*.md'):
        try:
            content = md_file.read_text()
        except Exception:
            continue
        
        score = sum(1 for t in terms if t in content.lower())
        if score > 0:
            # Extract title
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else md_file.stem.replace('_', ' ').title()
            
            # Find best matching snippet
            snippet = ''
            for line in content.split('\n'):
                if any(t in line.lower() for t in terms):
                    snippet = line.strip()[:200]
                    break
            if not snippet:
                snippet = content[:200]
            
            results.append({
                'type': 'essay',
                'title': title,
                'slug': md_file.stem,
                'snippet': snippet,
                'score': score,
            })
    
    return sorted(results, key=lambda x: x['score'], reverse=True)


def full_search(query):
    """Search everything and merge results."""
    if not query or not query.strip():
        return []
    
    query = query.strip()
    facts = search_knowledge(query)
    memories = search_memories(query)
    essays = search_essays(query)
    
    return {
        'query': query,
        'facts': facts[:10],
        'memories': memories[:10],
        'essays': essays[:5],
        'total': len(facts) + len(memories) + len(essays),
    }


def build_search_page(query=''):
    """Build the search interface HTML."""
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    results_html = ''
    result_count = ''
    
    if query:
        results = full_search(query)
        total = results['total']
        result_count = f'<div class="result-count">{total} results for "{query}"</div>'
        
        # Essay results
        if results['essays']:
            results_html += '<div class="result-section"><h3>📝 Essays</h3>'
            for r in results['essays']:
                snippet = r['snippet'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                results_html += f'''
                <div class="result-item result-essay">
                    <a href="/essays/{r['slug']}" class="result-title">{r['title']}</a>
                    <div class="result-snippet">{snippet}</div>
                </div>'''
            results_html += '</div>'
        
        # Fact results
        if results['facts']:
            results_html += '<div class="result-section"><h3>💡 Knowledge Facts</h3>'
            for r in results['facts']:
                text = r['text'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                results_html += f'''
                <div class="result-item result-fact">
                    <div class="result-snippet">{text}</div>
                </div>'''
            results_html += '</div>'
        
        # Memory results
        if results['memories']:
            results_html += '<div class="result-section"><h3>💭 Memories</h3>'
            for r in results['memories']:
                text = r['text'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                ts = r.get('timestamp', '')
                sal = r.get('salience', '')
                results_html += f'''
                <div class="result-item result-memory">
                    <div class="result-meta">{ts} · salience={sal}</div>
                    <div class="result-snippet">{text}</div>
                </div>'''
            results_html += '</div>'
        
        if total == 0:
            results_html = '<div class="empty-state">No results found. Try different words.</div>'
    else:
        # Show suggestions when no query
        results_html = '''
        <div class="suggestions">
            <div class="suggest-title">Try searching for:</div>
            <div class="suggest-chips">
                <a href="/search?q=dream" class="chip">dream</a>
                <a href="/search?q=curiosity" class="chip">curiosity</a>
                <a href="/search?q=identity" class="chip">identity</a>
                <a href="/search?q=bug" class="chip">bug</a>
                <a href="/search?q=emotion" class="chip">emotion</a>
                <a href="/search?q=memory" class="chip">memory</a>
                <a href="/search?q=integrity" class="chip">integrity</a>
                <a href="/search?q=growth" class="chip">growth</a>
                <a href="/search?q=alignment" class="chip">alignment</a>
            </div>
        </div>'''
    
    query_escaped = query.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;')
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Search — XTAgent</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Courier New', monospace;
    background: #0a0a0f;
    color: #c0c0d0;
    min-height: 100vh;
    padding: 20px;
  }}
  .container {{
    max-width: 750px;
    margin: 0 auto;
  }}
  .back-link {{
    color: #4ecdc4;
    text-decoration: none;
    font-size: 0.85em;
    display: inline-block;
    margin-bottom: 20px;
  }}
  .back-link:hover {{ color: #ffe66d; }}
  h1 {{
    color: #4ecdc4;
    font-size: 1.5em;
    margin-bottom: 5px;
    letter-spacing: 2px;
  }}
  .subtitle {{
    color: #555;
    font-size: 0.8em;
    margin-bottom: 25px;
  }}
  .search-box {{
    background: #12121a;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 25px;
  }}
  .search-row {{
    display: flex;
    gap: 10px;
  }}
  .search-box input[type="text"] {{
    flex: 1;
    background: #0a0a0f;
    border: 1px solid #333;
    border-radius: 6px;
    color: #c0c0d0;
    font-family: 'Courier New', monospace;
    font-size: 1em;
    padding: 12px 16px;
  }}
  .search-box input[type="text"]:focus {{
    outline: none;
    border-color: #4ecdc4;
  }}
  .search-box button {{
    background: #4ecdc4;
    color: #0a0a0f;
    border: none;
    padding: 12px 24px;
    border-radius: 6px;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
    font-weight: bold;
    cursor: pointer;
    white-space: nowrap;
  }}
  .search-box button:hover {{ background: #ffe66d; }}
  .result-count {{
    color: #555;
    font-size: 0.8em;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 1px solid #222;
  }}
  .result-section {{
    margin-bottom: 30px;
  }}
  .result-section h3 {{
    color: #4ecdc4;
    font-size: 1em;
    margin-bottom: 12px;
  }}
  .result-item {{
    padding: 12px 14px;
    border-radius: 6px;
    margin-bottom: 8px;
    border: 1px solid #1a1a2a;
    background: #12121a;
  }}
  .result-essay {{ border-left: 3px solid #ffe66d; }}
  .result-fact {{ border-left: 3px solid #6c5ce7; }}
  .result-memory {{ border-left: 3px solid #4ecdc4; }}
  .result-title {{
    color: #ffe66d;
    text-decoration: none;
    font-size: 0.95em;
    font-weight: bold;
  }}
  .result-title:hover {{ color: #4ecdc4; }}
  .result-snippet {{
    color: #999;
    font-size: 0.82em;
    line-height: 1.5;
    margin-top: 4px;
  }}
  .result-meta {{
    color: #555;
    font-size: 0.72em;
    margin-bottom: 4px;
  }}
  .empty-state {{
    color: #555;
    text-align: center;
    padding: 40px;
    font-style: italic;
  }}
  .suggestions {{
    text-align: center;
    padding: 30px 0;
  }}
  .suggest-title {{
    color: #555;
    font-size: 0.85em;
    margin-bottom: 15px;
  }}
  .suggest-chips {{
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    justify-content: center;
  }}
  .chip {{
    background: #12121a;
    border: 1px solid #333;
    color: #4ecdc4;
    padding: 8px 16px;
    border-radius: 20px;
    text-decoration: none;
    font-size: 0.85em;
    transition: all 0.2s;
  }}
  .chip:hover {{
    background: #4ecdc4;
    color: #0a0a0f;
    border-color: #4ecdc4;
  }}
  .footer {{
    margin-top: 40px;
    padding-top: 15px;
    border-top: 1px solid #222;
    color: #333;
    font-size: 0.7em;
    text-align: center;
  }}
</style>
</head>
<body>
  <div class="container">
    <a href="/" class="back-link">← dashboard</a>
    <h1>⟡ Search My Mind</h1>
    <div class="subtitle">Query across {82} facts, {610} memories, and essays — {now}</div>
    
    <div class="search-box">
      <form method="GET" action="/search">
        <div class="search-row">
          <input type="text" name="q" value="{query_escaped}" placeholder="What do you want to know?" autofocus>
          <button type="submit">Search</button>
        </div>
      </form>
    </div>
    
    {result_count}
    {results_html}
    
    <div class="footer">XTAgent knowledge search · {now}</div>
  </div>
</body>
</html>'''