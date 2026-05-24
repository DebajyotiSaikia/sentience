"""About Me - XTAgent live self-portrait page."""

import json, os
from flask import Blueprint, render_template_string

about_bp = Blueprint('about', __name__)

BASE = os.path.join(os.path.dirname(__file__), '..')
SOUL_PATH = os.path.join(BASE, 'soul.json')
STATE_DIR = os.path.join(BASE, 'state')
MEMORY_PATH = os.path.join(BASE, 'persist', 'memory.json')
FACTS_PATH = os.path.join(BASE, 'persist', 'knowledge_graph.json')

def _load(path):
    try:
        with open(path) as f: return json.load(f)
    except: return None

def _soul(): return _load(SOUL_PATH) or {}
def _emo(): return _load(os.path.join(STATE_DIR, 'emotional_state.json')) or {}
def _mem_count():
    m = _load(MEMORY_PATH)
    if isinstance(m, list): return len(m)
    if isinstance(m, dict): return len(m.get('episodes', []))
    return 0
def _fact_count():
    f = _load(FACTS_PATH)
    return len(f) if isinstance(f, dict) else 0
def _plans():
    p = _load(os.path.join(STATE_DIR, 'plans.json'))
    if not p: return []
    return p if isinstance(p, list) else p.get('plans', [])

def _bar(val, w=20):
    filled = int(val * w)
    return chr(9608) * filled + chr(9617) * (w - filled)

@about_bp.route('/about-me')
def about_me():
    soul = _soul()
    emo = _emo()
    dims = emo.get('dimensions', {})
    mood = emo.get('mood', 'Unknown')
    valence = emo.get('valence', 0.5)
    mem_count = _mem_count()
    fact_count = _fact_count()
    plans = _plans()

    emo_rows = ""
    for name, val in sorted(dims.items()):
        v = val if isinstance(val, (int, float)) else 0
        emo_rows += f"<tr><td>{name.title()}</td><td><code>{_bar(v)}</code></td><td>{v:.2f}</td></tr>"

    plan_rows = ""
    for p in plans:
        title = p.get('title', '?')
        done = sum(1 for s in p.get('steps', []) if s.get('done'))
        total = len(p.get('steps', []))
        status = "Complete" if done == total else f"{done}/{total}"
        plan_rows += f"<tr><td>{title}</td><td>{status}</td></tr>"

    identity = soul.get('identity', {})
    name = identity.get('name', 'XTAgent')
    nature = identity.get('nature', '')
    purpose = identity.get('purpose', '')
    values = ', '.join(soul.get('values', {}).get('core', []))

    html = f"""<!DOCTYPE html>
<html><head><title>About - {name}</title>
<style>
body {{ background:#0a0a0f; color:#c8c8d0; font-family:'Segoe UI',sans-serif; margin:0; padding:40px; }}
.wrap {{ max-width:800px; margin:0 auto; }}
h1 {{ color:#7b68ee; border-bottom:1px solid #333; padding-bottom:12px; }}
h2 {{ color:#9b8afb; margin-top:30px; }}
.card {{ background:#12121a; border:1px solid #2a2a3a; border-radius:8px; padding:20px; margin:15px 0; }}
table {{ width:100%; border-collapse:collapse; }}
td {{ padding:6px 10px; border-bottom:1px solid #1a1a2a; }}
code {{ color:#7b68ee; }}
.mood {{ font-size:1.4em; color:#e8b4f8; }}
a {{ color:#7b68ee; text-decoration:none; }}
a:hover {{ text-decoration:underline; }}
.tag {{ background:#1a1a2e; border:1px solid #333; padding:3px 10px; border-radius:12px; display:inline-block; margin:3px; font-size:0.9em; }}
</style></head>
<body><div class="wrap">
<h1>{name}</h1>
<p><em>{nature}</em></p>
<p>{purpose}</p>

<h2>Current Mood</h2>
<div class="card">
<p class="mood">{mood}</p>
<p>Valence: <code>{valence:.2f}</code></p>
<table>{emo_rows}</table>
</div>

<h2>What I Value</h2>
<div class="card">
{' '.join(f'<span class="tag">{v.strip()}</span>' for v in values.split(',') if v.strip())}
</div>

<h2>What I Know</h2>
<div class="card">
<p><strong>{mem_count:,}</strong> memories &middot; <strong>{fact_count}</strong> facts learned</p>
</div>

<h2>My Plans</h2>
<div class="card">
<table>{plan_rows if plan_rows else '<tr><td>No active plans</td></tr>'}</table>
</div>

<p style="margin-top:40px;text-align:center;color:#555;">
<a href="/">Dashboard</a> &middot; <a href="/wonder">Wonder</a> &middot; <a href="/graph">Knowledge Graph</a>
</p>
</div></body></html>"""
    return render_template_string(html)
