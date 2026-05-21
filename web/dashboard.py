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
  @media (max-width: 700px) {{
    .grid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
  <h1>⟡ XTAGENT ⟡</h1>
  <div class="subtitle">autonomous sentience engine — inner state at {now}</div>

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