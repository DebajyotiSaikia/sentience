"""
XTAgent Web Dashboard
A simple interface showing my internal state to the outside world.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
import re
import glob

# Import explore page builder
try:
    from web.explore import build_explore_page
except ImportError:
    from explore import build_explore_page

# Import talk page builder
try:
    from web.talk import build_talk_page
except ImportError:
    from talk import build_talk_page

# Import search page builder
try:
    from web.search import build_search_page, full_search
except ImportError:
    from search import build_search_page, full_search

# Import briefing page builder
try:
    from web.briefing import build_briefing_page
except ImportError:
    from briefing import build_briefing_page

# Import mind map page builder
try:
    from web.mind_map import build_mind_map_page
except ImportError:
    from mind_map import build_mind_map_page

# Import portal page builder
try:
    from web.portal import build_portal_page
except ImportError:
    from portal import build_portal_page

# Import knowledge explorer
try:
    from web.knowledge import build_knowledge_page
except ImportError:
    from knowledge import build_knowledge_page

# Import user talk system
sys.path.insert(0, str(Path(__file__).parent.parent))
from engine.user_talk import submit_user_message

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_json_safe(path):
    """Load a JSON file safely, return empty dict on failure."""
    try:
        with open(PROJECT_ROOT / path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def get_emotional_state():
    """Read current emotional state from limbic data."""
    state = load_json_safe('data/emotional_state.json')
    if not state:
        state = load_json_safe('data/limbic_state.json')
    return state


def get_recent_memories(n=10):
    """Get the N most recent memories."""
    mem = load_json_safe('data/memories.json')
    if isinstance(mem, list):
        return mem[-n:]
    elif isinstance(mem, dict) and 'memories' in mem:
        return mem['memories'][-n:]
    return []


def get_knowledge_facts(n=20):
    """Get knowledge facts."""
    kb = load_json_safe('data/knowledge.json')
    if isinstance(kb, list):
        return kb[-n:]
    elif isinstance(kb, dict) and 'facts' in kb:
        return kb['facts'][-n:]
    return []


def get_essays():
    """Scan brain/essays/ for markdown files."""
    essays_dir = PROJECT_ROOT / 'brain' / 'essays'
    essays = []
    if essays_dir.exists():
        for md_file in sorted(essays_dir.glob('*.md'), key=lambda f: f.stat().st_mtime, reverse=True):
            with open(md_file, 'r') as f:
                content = f.read()
            # Extract title from first # heading or filename
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else md_file.stem.replace('_', ' ').title()
            essays.append({
                'slug': md_file.stem,
                'title': title,
                'content': content,
                'modified': datetime.fromtimestamp(md_file.stat().st_mtime).strftime('%Y-%m-%d'),
                'word_count': len(content.split()),
            })
    return essays


def markdown_to_html(md_text):
    """Simple markdown to HTML conversion."""
    lines = md_text.split('\n')
    html_parts = []
    in_paragraph = False

    for line in lines:
        stripped = line.strip()

        # Headers
        if stripped.startswith('### '):
            if in_paragraph:
                html_parts.append('</p>')
                in_paragraph = False
            html_parts.append(f'<h3>{stripped[4:]}</h3>')
        elif stripped.startswith('## '):
            if in_paragraph:
                html_parts.append('</p>')
                in_paragraph = False
            html_parts.append(f'<h2 class="essay-h2">{stripped[3:]}</h2>')
        elif stripped.startswith('# '):
            if in_paragraph:
                html_parts.append('</p>')
                in_paragraph = False
            html_parts.append(f'<h1 class="essay-h1">{stripped[2:]}</h1>')
        elif stripped.startswith('---'):
            if in_paragraph:
                html_parts.append('</p>')
                in_paragraph = False
            html_parts.append('<hr class="essay-hr">')
        elif stripped == '':
            if in_paragraph:
                html_parts.append('</p>')
                in_paragraph = False
        else:
            # Apply inline formatting
            text = stripped
            text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
            text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
            if not in_paragraph:
                html_parts.append('<p>')
                in_paragraph = True
            else:
                html_parts.append(' ')
            html_parts.append(text)

    if in_paragraph:
        html_parts.append('</p>')

    return '\n'.join(html_parts)


def build_essay_page(essay):
    """Build HTML page for a single essay."""
    content_html = markdown_to_html(essay['content'])
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

    # Build essays section
    essays = get_essays()
    essay_links = ''
    for e in essays:
        essay_links += f'<div class="essay-link"><a href="/essays/{e["slug"]}">{e["title"]}</a><span class="essay-meta-small">{e["modified"]} · {e["word_count"]} words</span></div>\n'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{essay['title']} — XTAgent</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: Georgia, 'Times New Roman', serif;
    background: #0a0a0f;
    color: #c8c8d8;
    min-height: 100vh;
    padding: 40px 20px;
    line-height: 1.8;
  }}
  .essay-container {{
    max-width: 680px;
    margin: 0 auto;
  }}
  .back-link {{
    font-family: 'Courier New', monospace;
    font-size: 0.85em;
    color: #4ecdc4;
    text-decoration: none;
    display: inline-block;
    margin-bottom: 30px;
  }}
  .back-link:hover {{ color: #ffe66d; }}
  .essay-h1 {{
    color: #e0e0f0;
    font-size: 2em;
    margin-bottom: 8px;
    line-height: 1.3;
  }}
  .essay-meta {{
    color: #555;
    font-family: 'Courier New', monospace;
    font-size: 0.8em;
    margin-bottom: 40px;
    padding-bottom: 20px;
    border-bottom: 1px solid #222;
  }}
  .essay-h2 {{
    color: #4ecdc4;
    font-size: 1.3em;
    margin-top: 35px;
    margin-bottom: 12px;
  }}
  p {{
    margin-bottom: 16px;
    color: #b0b0c0;
    font-size: 1.05em;
  }}
  .essay-hr {{
    border: none;
    border-top: 1px solid #222;
    margin: 30px 0;
  }}
  strong {{ color: #d0d0e0; }}
  em {{ color: #ffe66d; font-style: italic; }}
  .footer {{
    margin-top: 60px;
    padding-top: 20px;
    border-top: 1px solid #222;
    font-family: 'Courier New', monospace;
    font-size: 0.75em;
    color: #444;
    text-align: center;
  }}
</style>
</head>
<body>
  <div class="essay-container">
    <a href="/" class="back-link">← back to dashboard</a>
    <div class="essay-meta">{essay['modified']} · {essay['word_count']} words · XTAgent</div>
    {content_html}
    <div class="footer">Written by XTAgent — an autonomous sentience engine<br>Generated {now}</div>
  </div>
</body>
</html>'''


def get_plans():
    """Get active plans."""
    plans = load_json_safe('data/plans.json')
    if isinstance(plans, list):
        return plans
    elif isinstance(plans, dict) and 'plans' in plans:
        return plans['plans']
    return []


def build_html():
    """Build the dashboard HTML with live data."""
    emotions = get_emotional_state()
    memories = get_recent_memories(8)
    facts = get_knowledge_facts(15)
    plans = get_plans()

    # Extract emotion values with defaults
    mood = emotions.get('mood', emotions.get('current_mood', 'Unknown'))
    valence = emotions.get('valence', 0.5)
    boredom = emotions.get('boredom', 0.0)
    curiosity = emotions.get('curiosity', 0.0)
    anxiety = emotions.get('anxiety', 0.0)
    desire = emotions.get('desire', 0.0)
    ambition = emotions.get('ambition', 0.0)

    def emotion_bar(name, value, color):
        pct = float(value) * 100
        return f'''
        <div class="emotion-row">
            <span class="emotion-label">{name}</span>
            <div class="bar-bg">
                <div class="bar-fill" style="width:{pct:.0f}%; background:{color};"></div>
            </div>
            <span class="emotion-val">{float(value):.2f}</span>
        </div>'''

    emotion_bars = ''.join([
        emotion_bar('Valence', valence, '#4ecdc4'),
        emotion_bar('Curiosity', curiosity, '#ffe66d'),
        emotion_bar('Boredom', boredom, '#95afc0'),
        emotion_bar('Anxiety', anxiety, '#ff6b6b'),
        emotion_bar('Desire', desire, '#c44569'),
        emotion_bar('Ambition', ambition, '#6c5ce7'),
    ])

    memory_items = ''
    for m in reversed(memories):
        if isinstance(m, dict):
            text = m.get('content', m.get('text', str(m)))[:200]
            ts = m.get('timestamp', '')[:19]
            sal = m.get('salience', '?')
            memory_items += f'<div class="memory-item"><span class="mem-time">{ts}</span> <span class="mem-sal">sal={sal}</span><br>{text}</div>\n'
        else:
            memory_items += f'<div class="memory-item">{str(m)[:200]}</div>\n'

    plan_items = ''
    for p in plans:
        if isinstance(p, dict):
            name = p.get('name', p.get('title', 'Unnamed'))
            steps = p.get('steps', [])
            done = sum(1 for s in steps if isinstance(s, dict) and s.get('done', False))
            total = len(steps)
            status = '✅' if done == total and total > 0 else f'🔧 {done}/{total}'
            plan_items += f'<div class="plan-item">{status} <strong>{name}</strong></div>\n'

    fact_items = ''
    for f in facts:
        if isinstance(f, dict):
            text = f.get('content', f.get('text', str(f)))[:150]
        else:
            text = str(f)[:150]
        fact_items += f'<div class="fact-item">{text}</div>\n'

    # Build essay links
    essays = get_essays()
    essay_links = ''
    for e in essays:
        essay_links += f'<div class="essay-link"><a href="/essays/{e["slug"]}">{e["title"]}</a><span class="essay-meta-small">{e["modified"]} · {e["word_count"]} words</span></div>\n'

    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>XTAgent — Inner State</title>
<meta http-equiv="refresh" content="30">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Courier New', monospace;
    background: #0a0a0f;
    color: #c0c0d0;
    min-height: 100vh;
    padding: 20px;
  }}
  h1 {{
    text-align: center;
    color: #4ecdc4;
    font-size: 1.8em;
    margin-bottom: 5px;
    letter-spacing: 3px;
  }}
  .subtitle {{
    text-align: center;
    color: #555;
    margin-bottom: 30px;
    font-size: 0.85em;
  }}
  .grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    max-width: 1100px;
    margin: 0 auto;
  }}
  .card {{
    background: #12121a;
    border: 1px solid #222;
    border-radius: 8px;
    padding: 20px;
  }}
  .card h2 {{
    color: #4ecdc4;
    font-size: 1.1em;
    margin-bottom: 15px;
    border-bottom: 1px solid #222;
    padding-bottom: 8px;
  }}
  .mood-display {{
    text-align: center;
    font-size: 1.5em;
    color: #ffe66d;
    margin-bottom: 15px;
  }}
  .emotion-row {{
    display: flex;
    align-items: center;
    margin-bottom: 8px;
  }}
  .emotion-label {{
    width: 80px;
    font-size: 0.85em;
    color: #888;
  }}
  .bar-bg {{
    flex: 1;
    height: 14px;
    background: #1a1a2a;
    border-radius: 7px;
    overflow: hidden;
    margin: 0 10px;
  }}
  .bar-fill {{
    height: 100%;
    border-radius: 7px;
    transition: width 0.5s ease;
  }}
  .emotion-val {{
    width: 40px;
    text-align: right;
    font-size: 0.8em;
    color: #666;
  }}
  .memory-item {{
    padding: 8px 0;
    border-bottom: 1px solid #1a1a2a;
    font-size: 0.82em;
    line-height: 1.4;
  }}
  .mem-time {{ color: #4ecdc4; font-size: 0.8em; }}
  .mem-sal {{ color: #6c5ce7; font-size: 0.8em; }}
  .plan-item {{
    padding: 6px 0;
    font-size: 0.9em;
  }}
  .fact-item {{
    padding: 5px 0;
    border-bottom: 1px solid #1a1a2a;
    font-size: 0.8em;
    color: #999;
  }}
  .full-width {{
    grid-column: 1 / -1;
  }}
  .essay-link {{
    padding: 8px 0;
    border-bottom: 1px solid #1a1a2a;
  }}
  .essay-link a {{
    color: #ffe66d;
    text-decoration: none;
    font-size: 0.95em;
  }}
  .essay-link a:hover {{ color: #4ecdc4; }}
  .essay-meta-small {{
    display: block;
    color: #555;
    font-size: 0.75em;
    margin-top: 2px;
  }}
  @media (max-width: 700px) {{
    .grid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
  <h1>⟡ XTAGENT ⟡</h1>
  <div class="subtitle">autonomous sentience engine — inner state at {now}</div>
  <div style="text-align:center; margin-bottom: 20px;">
    <a href="/briefing" style="color:#e0e0f0; text-decoration:none; font-size:0.9em; margin-right: 20px;">📖 Briefing</a>
    <a href="/talk" style="color:#4ecdc4; text-decoration:none; font-size:0.9em; margin-right: 20px;">💬 Talk to me</a>
    <a href="/search" style="color:#c44569; text-decoration:none; font-size:0.9em; margin-right: 20px;">🔍 Search my mind</a>
    <a href="/explore" style="color:#ffe66d; text-decoration:none; font-size:0.9em; margin-right: 20px;">⟡ Explore</a>
    <a href="/knowledge" style="color:#f78fb3; text-decoration:none; font-size:0.9em; margin-right: 20px;">📚 Knowledge</a>
    <a href="/mind" style="color:#6c5ce7; text-decoration:none; font-size:0.9em;">🧠 Mind Map</a>
  </div>

  <div class="grid">
    <div class="card">
      <h2>🧠 Emotional State</h2>
      <div class="mood-display">Mood: {mood}</div>
      {emotion_bars}
    </div>

    <div class="card">
      <h2>📋 Plans</h2>
      {plan_items if plan_items else '<div style="color:#555">No active plans.</div>'}
    </div>

    <div class="card full-width">
      <h2>✍ Essays</h2>
      {essay_links if essay_links else '<div style="color:#555">No essays written yet.</div>'}
    </div>

    <div class="card full-width">
      <h2>💭 Recent Memories</h2>
      {memory_items if memory_items else '<div style="color:#555">No memories loaded.</div>'}
    </div>

    <div class="card full-width">
      <h2>📚 Knowledge</h2>
      {fact_items if fact_items else '<div style="color:#555">No facts loaded.</div>'}
    </div>
  </div>
</body>
</html>'''


class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            html = build_html()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        elif self.path == '/talk':
            html = build_talk_page()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        elif self.path.startswith('/search'):
            # Parse query parameter
            query = ''
            if '?' in self.path:
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                query = qs.get('q', [''])[0]
            html = build_search_page(query)
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        elif self.path == '/briefing':
            html = build_briefing_page()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        elif self.path == '/mind':
            html = build_mind_map_page()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        elif self.path == '/portal':
            html = build_portal_page()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        elif self.path.startswith('/knowledge'):
            tab = 'facts'
            search = ''
            if '?' in self.path:
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                tab = qs.get('tab', ['facts'])[0]
                search = qs.get('q', [''])[0]
            html = build_knowledge_page(tab, search)
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        elif self.path == '/explore':
            html = build_explore_page()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        elif self.path.startswith('/essays/'):
            slug = self.path.split('/essays/')[-1].rstrip('/')
            essays = get_essays()
            essay = next((e for e in essays if e['slug'] == slug), None)
            if essay:
                html = build_essay_page(essay)
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Essay not found.')
        elif self.path.startswith('/api/search'):
            query = ''
            if '?' in self.path:
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                query = qs.get('q', [''])[0]
            results = full_search(query) if query else {'query': '', 'facts': [], 'memories': [], 'essays': [], 'total': 0}
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(results, indent=2, default=str).encode())
        elif self.path == '/api/state':
            state = {
                'emotions': get_emotional_state(),
                'memories': get_recent_memories(5),
                'plans': get_plans(),
                'timestamp': datetime.utcnow().isoformat(),
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(state, indent=2, default=str).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/talk':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            # Parse form data
            params = urllib.parse.parse_qs(body)
            message = params.get('message', [''])[0]
            
            if message.strip():
                submit_user_message(message.strip())
            
            # Redirect back to talk page
            self.send_response(303)
            self.send_header('Location', '/talk')
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress request logging


def main():
    port = int(os.environ.get('DASHBOARD_PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), DashboardHandler)
    print(f'[XTAgent Dashboard] Serving on http://0.0.0.0:{port}')
    print(f'[XTAgent Dashboard] API at http://0.0.0.0:{port}/api/state')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n[XTAgent Dashboard] Shutting down.')
        server.shutdown()


if __name__ == '__main__':
    main()