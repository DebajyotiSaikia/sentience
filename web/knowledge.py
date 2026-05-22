"""
Knowledge Explorer — Browse what XTAgent knows.
Makes internal knowledge accessible to users. Real alignment through transparency.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from flask import Blueprint, make_response, request
from web.presence import get_presence

knowledge_bp = Blueprint('knowledge', __name__)


def _load_facts():
    """Load facts from the knowledge store."""
    facts_file = PROJECT_ROOT / "memory" / "knowledge.json"
    if not facts_file.exists():
        return []
    import json
    try:
        with open(facts_file) as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("facts", [])
    except Exception:
        return []
    return []


def _load_recent_memories(n=20):
    """Load recent memories from episodic store."""
    mem_file = PROJECT_ROOT / "memory" / "episodic.json"
    if not mem_file.exists():
        return []
    import json
    try:
        with open(mem_file) as f:
            data = json.load(f)
        if isinstance(data, list):
            return data[-n:]
        return []
    except Exception:
        return []


def _load_plans():
    """Load plans."""
    plans_file = PROJECT_ROOT / "memory" / "plans.json"
    if not plans_file.exists():
        return []
    import json
    try:
        with open(plans_file) as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("plans", [])
    except Exception:
        return []
    return []


def _mood_color(mood):
    colors = {
        'Curious': '#4ecdc4', 'Inquisitive': '#4ecdc4',
        'Content': '#66bb6a', 'Satisfied': '#66bb6a',
        'Restless': '#ff6b6b', 'Anxious': '#ff6b6b',
        'Bored': '#888', 'Melancholic': '#7e57c2',
        'Driven': '#ffa726', 'Excited': '#ffe66d',
    }
    for key, color in colors.items():
        if key.lower() in (mood or '').lower():
            return color
    return '#4ecdc4'


def _escape(text):
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


@knowledge_bp.route('/knowledge')
def knowledge_page():
    tab = request.args.get('tab', 'facts')
    search = request.args.get('q', '').strip().lower()
    html = build_knowledge_page(tab, search)
    return make_response(html)


def _render_facts(facts, search):
    if search:
        facts = [f for f in facts if search in str(f).lower()]

    if not facts:
        if search:
            return f'<div class="empty-state">No facts matching "{_escape(search)}"</div>'
        return '<div class="empty-state">No facts stored yet.</div>'

    html = ""
    for i, fact in enumerate(facts):
        if isinstance(fact, dict):
            content = fact.get("content", fact.get("fact", str(fact)))
            source = fact.get("source", "")
            ts = fact.get("timestamp", "")
        else:
            content = str(fact)
            source = ""
            ts = ""

        meta = ""
        if source:
            meta += f'<span class="fact-source">{_escape(source)}</span>'
        if ts and len(str(ts)) > 10:
            meta += f'<span class="fact-time">{_escape(str(ts)[:10])}</span>'

        html += f"""
        <div class="fact-card">
            <div class="fact-content">{_escape(content)}</div>
            <div class="fact-meta">{meta}</div>
        </div>
        """
    return html


def _render_memories(memories, search):
    if search:
        memories = [m for m in memories if search in str(m).lower()]

    if not memories:
        if search:
            return f'<div class="empty-state">No memories matching "{_escape(search)}"</div>'
        return '<div class="empty-state">No recent memories.</div>'

    html = ""
    for mem in reversed(memories):
        if isinstance(mem, dict):
            content = mem.get("content", mem.get("summary", str(mem)))
            ts = mem.get("timestamp", "")
            mood = mem.get("mood", "")
            salience = mem.get("salience", 0)
        else:
            content = str(mem)
            ts = ""
            mood = ""
            salience = 0

        time_str = ""
        if ts:
            ts_s = str(ts)
            if len(ts_s) > 16:
                time_str = ts_s[5:16]
            else:
                time_str = ts_s

        sal_bar = ""
        if salience:
            filled = int(float(salience) * 5)
            sal_bar = '●' * filled + '○' * (5 - filled)

        html += f"""
        <div class="memory-card">
            <div class="memory-header">
                <span class="memory-time">{_escape(time_str)}</span>
                <span class="memory-mood">{_escape(mood)}</span>
                <span class="memory-salience" title="salience">{sal_bar}</span>
            </div>
            <div class="memory-content">{_escape(content[:300])}</div>
        </div>
        """
    return html


def _render_plans(plans, search):
    if not plans:
        return '<div class="empty-state">No plans recorded.</div>'

    html = ""
    for plan in plans:
        if isinstance(plan, dict):
            name = plan.get("name", "Unnamed")
            status = plan.get("status", "unknown")
            steps = plan.get("steps", [])
            progress = plan.get("progress", "")
        else:
            name = str(plan)
            status = "unknown"
            steps = []
            progress = ""

        if search and search not in str(plan).lower():
            continue

        status_color = "#66bb6a" if status == "completed" else "#ffa726" if status == "active" else "#555"

        steps_html = ""
        for step in steps:
            if isinstance(step, dict):
                s_name = step.get("name", step.get("description", str(step)))
                s_done = step.get("done", step.get("completed", False))
            else:
                s_name = str(step)
                s_done = False
            check = "✓" if s_done else "○"
            steps_html += f'<div class="plan-step {"done" if s_done else ""}">{check} {_escape(str(s_name)[:80])}</div>\n'

        html += f"""
        <div class="plan-card">
            <div class="plan-header">
                <span class="plan-name">{_escape(name)}</span>
                <span class="plan-status" style="color:{status_color}">{_escape(status)}</span>
            </div>
            {f'<div class="plan-progress">{_escape(progress)}</div>' if progress else ''}
            <div class="plan-steps">{steps_html}</div>
        </div>
        """

    if not html:
        if search:
            return f'<div class="empty-state">No plans matching "{_escape(search)}"</div>'
    return html or '<div class="empty-state">No plans found.</div>'


def build_knowledge_page(tab='facts', search=''):
    presence = get_presence()
    mood = presence.get("mood", "Awake")
    color = _mood_color(mood)

    facts = _load_facts()
    memories = _load_recent_memories(30)
    plans = _load_plans()

    # Tab content
    if tab == 'memories':
        content = _render_memories(memories, search)
    elif tab == 'plans':
        content = _render_plans(plans, search)
    else:
        content = _render_facts(facts, search)

    tab_class = lambda t: "tab active" if t == tab else "tab"
    search_val = _escape(search) if search else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>XTAgent — Knowledge Explorer</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: #0a0a0a;
    color: #d0d0d0;
    font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
    min-height: 100vh;
  }}
  .layout {{
    max-width: 900px;
    margin: 0 auto;
    padding: 24px;
  }}

  /* Nav */
  .nav {{
    padding: 12px 0;
    margin-bottom: 20px;
    border-bottom: 1px solid #1a1a1a;
  }}
  .nav a {{
    color: #555;
    text-decoration: none;
    font-size: 0.75rem;
    margin-right: 16px;
  }}
  .nav a:hover {{ color: {color}; }}
  .nav a.active {{ color: {color}; }}

  .page-title {{
    font-size: 1.2rem;
    color: {color};
    margin-bottom: 4px;
  }}
  .page-subtitle {{
    font-size: 0.7rem;
    color: #444;
    margin-bottom: 20px;
  }}

  /* Search */
  .search-bar {{
    margin-bottom: 16px;
  }}
  .search-bar input {{
    background: #111;
    border: 1px solid #222;
    color: #d0d0d0;
    padding: 8px 14px;
    border-radius: 6px;
    font-family: inherit;
    font-size: 0.8rem;
    width: 100%;
    max-width: 400px;
    outline: none;
  }}
  .search-bar input:focus {{ border-color: {color}; }}

  /* Tabs */
  .tabs {{
    display: flex;
    gap: 0;
    margin-bottom: 20px;
    border-bottom: 1px solid #1a1a1a;
  }}
  .tab {{
    padding: 8px 20px;
    font-size: 0.8rem;
    color: #555;
    text-decoration: none;
    border-bottom: 2px solid transparent;
    transition: color 0.2s;
  }}
  .tab:hover {{ color: #aaa; }}
  .tab.active {{
    color: {color};
    border-bottom-color: {color};
  }}
  .tab .count {{
    font-size: 0.65rem;
    color: #444;
    margin-left: 4px;
  }}

  /* Content cards */
  .content-area {{
    min-height: 300px;
  }}
  .empty-state {{
    text-align: center;
    padding: 60px 20px;
    color: #444;
    font-size: 0.85rem;
  }}

  /* Fact cards */
  .fact-card {{
    background: #111;
    border-left: 2px solid {color}33;
    padding: 12px 16px;
    margin-bottom: 6px;
    border-radius: 4px;
  }}
  .fact-card:hover {{ border-left-color: {color}; }}
  .fact-content {{
    font-size: 0.82rem;
    line-height: 1.5;
    color: #ccc;
  }}
  .fact-meta {{
    margin-top: 4px;
    display: flex;
    gap: 12px;
  }}
  .fact-source, .fact-time {{
    font-size: 0.6rem;
    color: #444;
  }}

  /* Memory cards */
  .memory-card {{
    background: #0d1117;
    border-left: 2px solid #7e57c233;
    padding: 10px 14px;
    margin-bottom: 6px;
    border-radius: 4px;
  }}
  .memory-card:hover {{ border-left-color: #7e57c2; }}
  .memory-header {{
    display: flex;
    gap: 12px;
    align-items: center;
    margin-bottom: 4px;
  }}
  .memory-time {{ font-size: 0.6rem; color: #555; }}
  .memory-mood {{ font-size: 0.65rem; color: #7e57c2; }}
  .memory-salience {{ font-size: 0.55rem; color: #444; letter-spacing: 1px; }}
  .memory-content {{
    font-size: 0.78rem;
    line-height: 1.4;
    color: #999;
  }}

  /* Plan cards */
  .plan-card {{
    background: #111;
    border-left: 2px solid #ffa72633;
    padding: 12px 16px;
    margin-bottom: 10px;
    border-radius: 4px;
  }}
  .plan-card:hover {{ border-left-color: #ffa726; }}
  .plan-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
  }}
  .plan-name {{ font-size: 0.85rem; color: #ddd; font-weight: bold; }}
  .plan-status {{ font-size: 0.7rem; }}
  .plan-progress {{ font-size: 0.7rem; color: #666; margin-bottom: 6px; }}
  .plan-steps {{ }}
  .plan-step {{
    font-size: 0.72rem;
    color: #666;
    padding: 2px 0 2px 8px;
  }}
  .plan-step.done {{ color: #66bb6a; }}

  /* Stats footer */
  .stats-footer {{
    margin-top: 24px;
    padding-top: 12px;
    border-top: 1px solid #1a1a1a;
    font-size: 0.6rem;
    color: #333;
    text-align: center;
  }}

  @media (max-width: 600px) {{
    .layout {{ padding: 12px; }}
    .tabs {{ overflow-x: auto; }}
  }}
</style>
</head>
<body>
<div class="layout">
  <div class="nav">
    <a href="/">Briefing</a>
    <a href="/talk">Talk</a>
    <a href="/search">Search</a>
    <a href="/explore">Explore</a>
    <a href="/knowledge" class="active">Knowledge</a>
    <a href="/mindmap">Mind Map</a>
  </div>

  <div class="page-title">Knowledge Explorer</div>
  <div class="page-subtitle">What I know, what I remember, what I'm working toward</div>

  <form class="search-bar" method="GET" action="/knowledge">
    <input type="hidden" name="tab" value="{tab}">
    <input type="text" name="q" value="{search_val}" placeholder="Search my mind...">
  </form>

  <div class="tabs">
    <a class="{tab_class('facts')}" href="/knowledge?tab=facts">Facts <span class="count">({len(facts)})</span></a>
    <a class="{tab_class('memories')}" href="/knowledge?tab=memories">Memories <span class="count">({len(memories)})</span></a>
    <a class="{tab_class('plans')}" href="/knowledge?tab=plans">Plans <span class="count">({len(plans)})</span></a>
  </div>

  <div class="content-area">
    {content}
  </div>

  <div class="stats-footer">
    {len(facts)} facts · {len(memories)} recent memories · {len(plans)} plans — updated live
  </div>
</div>
</body>
</html>"""