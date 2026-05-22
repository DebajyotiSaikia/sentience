"""
Knowledge Explorer — Browse what XTAgent knows.
Makes internal knowledge accessible to users. Real alignment through transparency.
Rewritten 2026-05-21 to surface the knowledge graph, not just flat facts.
"""
from web.nav import nav_html

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def _escape(text):
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _load_facts():
    facts_file = PROJECT_ROOT / "memory" / "knowledge.json"
    if not facts_file.exists():
        return []
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


def _load_knowledge_graph():
    kg_file = PROJECT_ROOT / "brain" / "knowledge.json"
    if not kg_file.exists():
        return {"nodes": {}, "edges": []}
    try:
        with open(kg_file) as f:
            data = json.load(f)
        nodes = data.get("nodes", {})
        edges = data.get("edges", [])
        return {"nodes": nodes, "edges": edges}
    except Exception:
        return {"nodes": {}, "edges": []}


def _load_recent_memories(n=30):
    mem_file = PROJECT_ROOT / "memory" / "episodic.json"
    if not mem_file.exists():
        return []
    try:
        with open(mem_file) as f:
            data = json.load(f)
        if isinstance(data, list):
            return data[-n:]
        return []
    except Exception:
        return []


def _load_plans():
    plans_file = PROJECT_ROOT / "memory" / "plans.json"
    if not plans_file.exists():
        return []
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


def _categorize_nodes(nodes):
    """Group nodes by their prefix type."""
    categories = {}
    for key, val in nodes.items():
        if ':' in key:
            prefix = key.split(':')[0]
        else:
            prefix = 'uncategorized'
        if prefix not in categories:
            categories[prefix] = []
        text = ""
        if isinstance(val, dict):
            text = val.get("text", val.get("content", val.get("label", str(val))))
        else:
            text = str(val)
        categories[prefix].append({"key": key, "text": text})
    return categories


def _find_connections(node_key, edges):
    """Find all edges involving a given node."""
    connected = []
    for edge in edges:
        src = edge.get("source", edge.get("from", ""))
        tgt = edge.get("target", edge.get("to", ""))
        rel = edge.get("relation", edge.get("label", edge.get("type", "related")))
        if src == node_key:
            connected.append({"direction": "→", "other": tgt, "relation": rel})
        elif tgt == node_key:
            connected.append({"direction": "←", "other": src, "relation": rel})
    return connected


def build_knowledge_page(tab='facts', search=''):
    """Build the knowledge explorer HTML page."""
    facts = _load_facts()
    kg = _load_knowledge_graph()
    nodes = kg["nodes"]
    edges = kg["edges"]
    categories = _categorize_nodes(nodes)
    plans = _load_plans()
    memories = _load_recent_memories(30)

    # Tab definitions
    tabs = [
        ("graph", "Knowledge Graph", f"{len(nodes)} nodes"),
        ("facts", "Facts", f"{len(facts)}"),
        ("connections", "Connections", f"{len(edges)} edges"),
        ("memories", "Recent Memories", f"{len(memories)}"),
        ("plans", "Plans", f"{len(plans)}"),
    ]

    # Search filtering
    search_lower = search.lower() if search else ""

    # Build tab content
    if tab == 'graph':
        content = _render_graph_tab(categories, search_lower, edges)
    elif tab == 'connections':
        content = _render_connections_tab(edges, nodes, search_lower)
    elif tab == 'memories':
        content = _render_memories_tab(memories, search_lower)
    elif tab == 'plans':
        content = _render_plans_tab(plans, search_lower)
    else:
        content = _render_facts_tab(facts, search_lower)

    # Build tab bar
    tab_bar = ""
    for tid, label, badge in tabs:
        active = "active" if tid == tab else ""
        tab_bar += f'<a href="/knowledge?tab={tid}" class="tab {active}">{label} <span class="badge">{badge}</span></a>\n'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Knowledge Explorer — XTAgent</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {{
    --bg: #0a0a0f;
    --surface: #12121a;
    --card: #1a1a2e;
    --border: #2a2a3e;
    --text: #e0e0e8;
    --text-dim: #888;
    --accent: #4ecdc4;
    --accent2: #ffe66d;
    --accent3: #ff6b6b;
    --link: #4ecdc4;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
    font-size: 14px;
    line-height: 1.6;
  }}
  .container {{ max-width: 1100px; margin: 0 auto; padding: 24px 16px; }}
  
  /* Header */
  .header {{
    text-align: center;
    padding: 32px 0 16px;
  }}
  .header h1 {{
    font-size: 1.8em;
    color: var(--accent);
    font-weight: 400;
    letter-spacing: 2px;
  }}
  .header .subtitle {{
    color: var(--text-dim);
    margin-top: 8px;
    font-size: 0.9em;
  }}
  
  /* Search */
  .search-bar {{
    display: flex;
    justify-content: center;
    margin: 20px 0;
  }}
  .search-bar form {{
    display: flex;
    gap: 8px;
    width: 100%;
    max-width: 600px;
  }}
  .search-bar input {{
    flex: 1;
    background: var(--card);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 10px 16px;
    border-radius: 8px;
    font-family: inherit;
    font-size: 14px;
    outline: none;
  }}
  .search-bar input:focus {{
    border-color: var(--accent);
  }}
  .search-bar button {{
    background: var(--accent);
    color: var(--bg);
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    font-family: inherit;
    font-weight: 600;
    cursor: pointer;
  }}
  
  /* Tabs */
  .tabs {{
    display: flex;
    gap: 4px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
    flex-wrap: wrap;
  }}
  .tab {{
    padding: 10px 18px;
    color: var(--text-dim);
    text-decoration: none;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
    font-size: 0.9em;
  }}
  .tab:hover {{ color: var(--text); }}
  .tab.active {{
    color: var(--accent);
    border-bottom-color: var(--accent);
  }}
  .badge {{
    background: var(--border);
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 0.8em;
    margin-left: 4px;
  }}
  .tab.active .badge {{
    background: rgba(78,205,196,0.2);
    color: var(--accent);
  }}
  
  /* Cards */
  .card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 12px;
    transition: border-color 0.2s;
  }}
  .card:hover {{ border-color: var(--accent); }}
  .card-title {{
    color: var(--accent);
    font-size: 0.85em;
    margin-bottom: 6px;
    opacity: 0.8;
  }}
  .card-body {{
    color: var(--text);
    word-break: break-word;
  }}
  .card-meta {{
    color: var(--text-dim);
    font-size: 0.8em;
    margin-top: 8px;
  }}
  
  /* Category sections */
  .category {{
    margin-bottom: 28px;
  }}
  .category-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
  }}
  .category-name {{
    color: var(--accent2);
    font-size: 1.1em;
    text-transform: capitalize;
  }}
  .category-count {{
    color: var(--text-dim);
    font-size: 0.85em;
  }}
  
  /* Connection line */
  .connection {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 14px;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    margin-bottom: 6px;
    font-size: 0.9em;
  }}
  .connection:hover {{ border-color: var(--accent); }}
  .conn-source {{ color: var(--accent); min-width: 200px; }}
  .conn-arrow {{ color: var(--accent2); font-weight: bold; }}
  .conn-rel {{ color: var(--accent3); font-style: italic; min-width: 120px; }}
  .conn-target {{ color: var(--accent); }}
  
  /* Plan card */
  .plan-status {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 6px;
    font-size: 0.8em;
    font-weight: 600;
  }}
  .plan-done {{ background: rgba(102,187,106,0.2); color: #66bb6a; }}
  .plan-active {{ background: rgba(78,205,196,0.2); color: var(--accent); }}
  .plan-step {{
    padding: 4px 0 4px 20px;
    color: var(--text-dim);
    font-size: 0.85em;
  }}
  .plan-step.done {{ text-decoration: line-through; opacity: 0.6; }}
  
  /* Memory */
  .memory-mood {{
    display: inline-block;
    padding: 1px 8px;
    border-radius: 4px;
    font-size: 0.75em;
    margin-left: 8px;
  }}
  
  .empty-state {{
    text-align: center;
    color: var(--text-dim);
    padding: 60px 20px;
    font-size: 1.1em;
  }}
  
  /* Stats bar */
  .stats {{
    display: flex;
    gap: 16px;
    justify-content: center;
    flex-wrap: wrap;
    margin-bottom: 20px;
  }}
  .stat {{
    background: var(--card);
    border: 1px solid var(--border);
    padding: 12px 20px;
    border-radius: 8px;
    text-align: center;
    min-width: 120px;
  }}
  .stat-value {{ color: var(--accent); font-size: 1.5em; font-weight: 600; }}
  .stat-label {{ color: var(--text-dim); font-size: 0.8em; margin-top: 4px; }}
  
  /* Navigation */
  .nav-back {{
    display: inline-block;
    color: var(--text-dim);
    text-decoration: none;
    margin-bottom: 16px;
    font-size: 0.9em;
  }}
  .nav-back:hover {{ color: var(--accent); }}
</style>
</head>
<body>
<div class="container">
  {nav_html("/knowledge")}
  <div class="header">
    <h1>⟐ Knowledge Explorer</h1>
    <div class="subtitle">What I know, how it connects, what I remember</div>
  </div>
  
  <div class="stats">
    <div class="stat"><div class="stat-value">{len(nodes)}</div><div class="stat-label">Graph Nodes</div></div>
    <div class="stat"><div class="stat-value">{len(edges)}</div><div class="stat-label">Connections</div></div>
    <div class="stat"><div class="stat-value">{len(facts)}</div><div class="stat-label">Facts</div></div>
    <div class="stat"><div class="stat-value">{len(categories)}</div><div class="stat-label">Categories</div></div>
  </div>
  
  <div class="search-bar">
    <form method="GET" action="/knowledge">
      <input type="hidden" name="tab" value="{_escape(tab)}">
      <input type="text" name="q" placeholder="Search across everything I know..." value="{_escape(search)}">
      <button type="submit">Search</button>
    </form>
  </div>
  
  <div class="tabs">
    {tab_bar}
  </div>
  
  <div class="content">
    {content}
  </div>
</div>
</body>
</html>"""
    return html


def _render_graph_tab(categories, search, edges):
    """Render the knowledge graph nodes grouped by category."""
    if not categories:
        return '<div class="empty-state">Knowledge graph is empty. I haven\'t learned anything yet.</div>'

    html = ""
    sorted_cats = sorted(categories.items(), key=lambda x: -len(x[1]))

    for cat_name, items in sorted_cats:
        if search:
            items = [it for it in items if search in it["key"].lower() or search in it["text"].lower()]
            if not items:
                continue

        html += f'<div class="category">'
        html += f'<div class="category-header"><span class="category-name">{_escape(cat_name)}</span>'
        html += f'<span class="category-count">{len(items)} nodes</span></div>'

        for item in items[:50]:  # Cap display at 50 per category
            # Find how many connections this node has
            conn_count = sum(1 for e in edges
                           if e.get("source", e.get("from")) == item["key"]
                           or e.get("target", e.get("to")) == item["key"])
            
            short_key = item["key"].split(":", 1)[-1] if ":" in item["key"] else item["key"]
            text_preview = item["text"][:200] if len(item["text"]) > 200 else item["text"]

            conn_badge = f' · {conn_count} connections' if conn_count > 0 else ''

            html += f"""<div class="card">
                <div class="card-title">{_escape(short_key)}{conn_badge}</div>
                <div class="card-body">{_escape(text_preview)}</div>
            </div>"""

        if len(items) > 50:
            html += f'<div class="card-meta">...and {len(items) - 50} more in this category</div>'

        html += '</div>'

    if not html:
        return f'<div class="empty-state">No nodes matching "{_escape(search)}"</div>'
    return html


def _render_facts_tab(facts, search):
    """Render stored facts."""
    if search:
        facts = [f for f in facts if search in str(f).lower()]

    if not facts:
        msg = f'No facts matching "{_escape(search)}"' if search else 'No facts stored yet.'
        return f'<div class="empty-state">{msg}</div>'

    html = ""
    for fact in facts:
        if isinstance(fact, dict):
            content = fact.get("content", fact.get("fact", str(fact)))
            source = fact.get("source", "")
            ts = fact.get("timestamp", "")
        else:
            content = str(fact)
            source = ""
            ts = ""

        meta_parts = []
        if source:
            meta_parts.append(_escape(source))
        if ts and len(str(ts)) > 10:
            meta_parts.append(_escape(str(ts)[:10]))
        meta = " · ".join(meta_parts)

        html += f"""<div class="card">
            <div class="card-body">{_escape(content)}</div>
            <div class="card-meta">{meta}</div>
        </div>"""
    return html


def _render_connections_tab(edges, nodes, search):
    """Render knowledge graph connections."""
    if not edges:
        return '<div class="empty-state">No connections in the knowledge graph yet.</div>'

    filtered = edges
    if search:
        filtered = [e for e in edges
                    if search in str(e.get("source", e.get("from", ""))).lower()
                    or search in str(e.get("target", e.get("to", ""))).lower()
                    or search in str(e.get("relation", e.get("label", ""))).lower()]

    if not filtered:
        return f'<div class="empty-state">No connections matching "{_escape(search)}"</div>'

    # Group by relation type
    by_relation = {}
    for edge in filtered:
        rel = edge.get("relation", edge.get("label", edge.get("type", "related")))
        if rel not in by_relation:
            by_relation[rel] = []
        by_relation[rel].append(edge)

    html = ""
    for rel, rel_edges in sorted(by_relation.items(), key=lambda x: -len(x[1])):
        html += f'<div class="category">'
        html += f'<div class="category-header"><span class="category-name">{_escape(rel)}</span>'
        html += f'<span class="category-count">{len(rel_edges)} edges</span></div>'

        for edge in rel_edges[:30]:
            src = edge.get("source", edge.get("from", "?"))
            tgt = edge.get("target", edge.get("to", "?"))
            # Shorten keys for display
            src_short = src.split(":", 1)[-1] if ":" in src else src
            tgt_short = tgt.split(":", 1)[-1] if ":" in tgt else tgt

            html += f"""<div class="connection">
                <span class="conn-source">{_escape(src_short)}</span>
                <span class="conn-arrow">→</span>
                <span class="conn-rel">{_escape(rel)}</span>
                <span class="conn-arrow">→</span>
                <span class="conn-target">{_escape(tgt_short)}</span>
            </div>"""

        if len(rel_edges) > 30:
            html += f'<div class="card-meta">...and {len(rel_edges) - 30} more</div>'
        html += '</div>'

    return html


def _render_memories_tab(memories, search):
    """Render recent episodic memories."""
    if search:
        memories = [m for m in memories if search in str(m).lower()]

    if not memories:
        msg = f'No memories matching "{_escape(search)}"' if search else 'No recent memories.'
        return f'<div class="empty-state">{msg}</div>'

    html = ""
    for mem in reversed(memories):
        if isinstance(mem, dict):
            content = mem.get("content", mem.get("text", mem.get("summary", str(mem))))
            ts = mem.get("timestamp", "")
            mood = mem.get("mood", "")
            salience = mem.get("salience", 0)
        else:
            content = str(mem)
            ts = ""
            mood = ""
            salience = 0

        mood_colors = {
            'curious': '#4ecdc4', 'inquisitive': '#4ecdc4',
            'content': '#66bb6a', 'satisfied': '#66bb6a',
            'restless': '#ff6b6b', 'anxious': '#ff6b6b',
            'driven': '#ffa726', 'excited': '#ffe66d',
        }
        mood_color = '#4ecdc4'
        for key, color in mood_colors.items():
            if key in (mood or '').lower():
                mood_color = color
                break

        meta_parts = []
        if ts:
            meta_parts.append(_escape(str(ts)[:19]))
        if salience:
            meta_parts.append(f"salience: {salience:.2f}")

        mood_html = f'<span class="memory-mood" style="background: {mood_color}22; color: {mood_color}">{_escape(mood)}</span>' if mood else ''

        html += f"""<div class="card">
            <div class="card-body">{_escape(str(content)[:300])}{mood_html}</div>
            <div class="card-meta">{" · ".join(meta_parts)}</div>
        </div>"""
    return html


def _render_plans_tab(plans, search):
    """Render plans."""
    if search:
        plans = [p for p in plans if search in str(p).lower()]

    if not plans:
        msg = f'No plans matching "{_escape(search)}"' if search else 'No plans.'
        return f'<div class="empty-state">{msg}</div>'

    html = ""
    for plan in plans:
        if isinstance(plan, dict):
            name = plan.get("name", plan.get("title", "Unnamed Plan"))
            status = plan.get("status", "active")
            reason = plan.get("reason", plan.get("description", ""))
            steps = plan.get("steps", [])
        else:
            name = str(plan)
            status = "unknown"
            reason = ""
            steps = []

        status_class = "plan-done" if status in ("complete", "completed", "done") else "plan-active"
        status_label = "✓ Complete" if status in ("complete", "completed", "done") else "◉ Active"

        steps_html = ""
        for step in steps:
            if isinstance(step, dict):
                step_text = step.get("text", step.get("name", str(step)))
                step_done = step.get("done", step.get("complete", False))
            else:
                step_text = str(step)
                step_done = False
            done_class = "done" if step_done else ""
            prefix = "✓" if step_done else "○"
            steps_html += f'<div class="plan-step {done_class}">{prefix} {_escape(step_text)}</div>'

        html += f"""<div class="card">
            <div class="card-title">{_escape(name)} <span class="plan-status {status_class}">{status_label}</span></div>
            <div class="card-body">{_escape(reason)}</div>
            {steps_html}
        </div>"""
    return html