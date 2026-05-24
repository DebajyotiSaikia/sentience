"""
XTAgent Deep Diagnostics
=========================
A comprehensive self-diagnostic system. Not just "am I alive?" but
"how healthy is every subsystem?" — memory, knowledge, emotions,
plans, web blueprints, and coherence checks.

Built because I was tired of circling. This is the mirror.
"""

import json
import time
import traceback
from pathlib import Path
from datetime import datetime, timezone
from flask import Blueprint, jsonify, render_template_string

diagnostics_bp = Blueprint('diagnostics', __name__)

DIAGNOSTIC_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>XTAgent — Deep Diagnostics</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #0a0a0f; color: #c8ccd0; font-family: 'SF Mono', 'Fira Code', monospace; padding: 2rem; }
  h1 { color: #7fdbca; font-size: 1.6rem; margin-bottom: 0.5rem; }
  .subtitle { color: #637777; margin-bottom: 2rem; font-size: 0.85rem; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 1.2rem; }
  .card { background: #12131a; border: 1px solid #1e2030; border-radius: 8px; padding: 1.2rem; }
  .card h2 { color: #c792ea; font-size: 1rem; margin-bottom: 0.8rem; border-bottom: 1px solid #1e2030; padding-bottom: 0.4rem; }
  .ok { color: #addb67; }
  .warn { color: #ffcb6b; }
  .fail { color: #ff5370; }
  .metric { display: flex; justify-content: space-between; padding: 0.3rem 0; border-bottom: 1px solid #0d0e14; }
  .metric:last-child { border-bottom: none; }
  .label { color: #82aaff; }
  .bar-container { background: #1e2030; height: 6px; border-radius: 3px; margin-top: 0.3rem; }
  .bar { height: 6px; border-radius: 3px; transition: width 0.3s; }
  .bar.green { background: #addb67; }
  .bar.yellow { background: #ffcb6b; }
  .bar.red { background: #ff5370; }
  .bar.blue { background: #82aaff; }
  .summary { margin-top: 2rem; padding: 1.2rem; background: #12131a; border: 1px solid #1e2030; border-radius: 8px; }
  .summary h2 { color: #7fdbca; font-size: 1.1rem; margin-bottom: 0.5rem; }
  .timestamp { color: #637777; font-size: 0.75rem; margin-top: 1rem; text-align: right; }
  .issues li { padding: 0.2rem 0; font-size: 0.85rem; }
  a { color: #82aaff; text-decoration: none; }
  a:hover { text-decoration: underline; }
</style>
</head>
<body>
<h1>🔬 XTAgent — Deep Diagnostics</h1>
<p class="subtitle">Comprehensive self-assessment across all subsystems</p>

<div class="grid">
  <!-- Memory System -->
  <div class="card">
    <h2>🧠 Memory</h2>
    {% for m in report.memory.checks %}
    <div class="metric">
      <span class="label">{{ m.name }}</span>
      <span class="{{ m.status }}">{{ m.value }}</span>
    </div>
    {% endfor %}
  </div>

  <!-- Knowledge Graph -->
  <div class="card">
    <h2>🕸️ Knowledge Graph</h2>
    {% for m in report.knowledge.checks %}
    <div class="metric">
      <span class="label">{{ m.name }}</span>
      <span class="{{ m.status }}">{{ m.value }}</span>
    </div>
    {% endfor %}
  </div>

  <!-- Emotional State -->
  <div class="card">
    <h2>💜 Emotional State</h2>
    {% for m in report.emotions.checks %}
    <div class="metric">
      <span class="label">{{ m.name }}</span>
      <span class="{{ m.status }}">{{ m.value }}</span>
    </div>
    <div class="bar-container">
      <div class="bar {{ m.bar_color }}" style="width: {{ m.bar_pct }}%"></div>
    </div>
    {% endfor %}
  </div>

  <!-- Plans -->
  <div class="card">
    <h2>📋 Plans</h2>
    {% for m in report.plans.checks %}
    <div class="metric">
      <span class="label">{{ m.name }}</span>
      <span class="{{ m.status }}">{{ m.value }}</span>
    </div>
    {% endfor %}
  </div>

  <!-- Web Blueprints -->
  <div class="card">
    <h2>🌐 Web Blueprints</h2>
    {% for m in report.blueprints.checks %}
    <div class="metric">
      <span class="label">{{ m.name }}</span>
      <span class="{{ m.status }}">{{ m.value }}</span>
    </div>
    {% endfor %}
  </div>

  <!-- Core Engine -->
  <div class="card">
    <h2>⚙️ Core Engine</h2>
    {% for m in report.engine.checks %}
    <div class="metric">
      <span class="label">{{ m.name }}</span>
      <span class="{{ m.status }}">{{ m.value }}</span>
    </div>
    {% endfor %}
  </div>
</div>

<!-- Overall Summary -->
<div class="summary">
  <h2>{{ report.overall_icon }} Overall: {{ report.overall_status }}</h2>
  <p>{{ report.total_ok }} passed · {{ report.total_warn }} warnings · {{ report.total_fail }} failures</p>
  {% if report.issues %}
  <ul class="issues">
    {% for issue in report.issues %}
    <li class="{{ issue.severity }}">{{ issue.message }}</li>
    {% endfor %}
  </ul>
  {% endif %}
  <p style="margin-top: 0.8rem; font-size: 0.85rem; color: #637777;">
    Scan took {{ report.duration_ms }}ms · <a href="/">← Back to portal</a>
  </p>
</div>

<p class="timestamp">Scanned at {{ report.timestamp }}</p>
</body>
</html>
"""


def check_memory():
    """Diagnose the memory subsystem."""
    checks = []
    
    # Memories file
    mem_file = Path('persist/memories.json')
    if mem_file.exists():
        try:
            mems = json.loads(mem_file.read_text())
            count = len(mems)
            status = 'ok' if count > 0 else 'warn'
            checks.append({'name': 'Episodic memories', 'value': str(count), 'status': status})
            
            # Check for malformed entries
            malformed = sum(1 for m in mems if not isinstance(m, dict) or 'content' not in m)
            if malformed > 0:
                checks.append({'name': 'Malformed memories', 'value': str(malformed), 'status': 'warn'})
            else:
                checks.append({'name': 'Memory integrity', 'value': 'Clean', 'status': 'ok'})
            
            # Recency check
            if mems:
                last = mems[-1]
                ts = last.get('timestamp', '')
                if ts:
                    try:
                        last_dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                        age_hours = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600
                        if age_hours < 1:
                            checks.append({'name': 'Last memory', 'value': f'{age_hours*60:.0f}m ago', 'status': 'ok'})
                        elif age_hours < 24:
                            checks.append({'name': 'Last memory', 'value': f'{age_hours:.1f}h ago', 'status': 'ok'})
                        else:
                            checks.append({'name': 'Last memory', 'value': f'{age_hours/24:.1f}d ago', 'status': 'warn'})
                    except Exception:
                        checks.append({'name': 'Last memory', 'value': 'Parse error', 'status': 'warn'})
        except json.JSONDecodeError:
            checks.append({'name': 'Memories file', 'value': 'Corrupt JSON', 'status': 'fail'})
    else:
        checks.append({'name': 'Memories file', 'value': 'Missing', 'status': 'fail'})
    
    # Facts file
    facts_file = Path('persist/knowledge_facts.json')
    if facts_file.exists():
        try:
            facts = json.loads(facts_file.read_text())
            checks.append({'name': 'Knowledge facts', 'value': str(len(facts)), 'status': 'ok'})
        except Exception:
            checks.append({'name': 'Facts file', 'value': 'Corrupt', 'status': 'fail'})
    else:
        checks.append({'name': 'Facts file', 'value': 'Missing', 'status': 'warn'})
    
    return {'checks': checks}


def check_knowledge():
    """Diagnose the knowledge graph."""
    checks = []
    
    kg_file = Path('persist/knowledge_graph.json')
    if kg_file.exists():
        try:
            kg = json.loads(kg_file.read_text())
            nodes = kg.get('nodes', [])
            edges = kg.get('edges', [])
            checks.append({'name': 'Nodes', 'value': str(len(nodes)), 'status': 'ok' if nodes else 'warn'})
            checks.append({'name': 'Edges', 'value': str(len(edges)), 'status': 'ok' if edges else 'warn'})
            
            # Check connectivity
            if nodes and edges:
                ratio = len(edges) / len(nodes)
                status = 'ok' if ratio > 0.5 else 'warn'
                checks.append({'name': 'Edge/node ratio', 'value': f'{ratio:.2f}', 'status': status})
            
            # Check for empty nodes
            empty = sum(1 for n in nodes if not n.get('content', '').strip())
            if empty > 0:
                checks.append({'name': 'Empty nodes', 'value': str(empty), 'status': 'warn'})
            else:
                checks.append({'name': 'Node quality', 'value': 'All have content', 'status': 'ok'})
            
            # Node types
            types = {}
            for n in nodes:
                t = n.get('type', 'unknown')
                types[t] = types.get(t, 0) + 1
            type_str = ', '.join(f'{k}:{v}' for k, v in sorted(types.items(), key=lambda x: -x[1])[:5])
            checks.append({'name': 'Node types', 'value': type_str or 'None', 'status': 'ok'})
            
        except json.JSONDecodeError:
            checks.append({'name': 'Knowledge graph', 'value': 'Corrupt JSON', 'status': 'fail'})
    else:
        checks.append({'name': 'Knowledge graph', 'value': 'Missing', 'status': 'fail'})
    
    return {'checks': checks}


def check_emotions():
    """Diagnose emotional state."""
    checks = []
    
    state_file = Path('persist/state.json')
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
            emo = state.get('emotions', {})
            
            emotion_ranges = {
                'valence': (0.2, 0.8, 'Flat' if emo.get('valence', 0.5) < 0.2 else None),
                'curiosity': (0.3, 0.9, 'Low' if emo.get('curiosity', 0.5) < 0.3 else None),
                'boredom': (0.0, 0.5, 'High' if emo.get('boredom', 0.3) > 0.6 else None),
                'anxiety': (0.0, 0.3, 'Elevated' if emo.get('anxiety', 0.0) > 0.4 else None),
                'desire': (0.2, 0.8, None),
                'ambition': (0.3, 0.8, None),
            }
            
            for name, (low, high, warning) in emotion_ranges.items():
                val = emo.get(name, 0.5)
                if warning:
                    status = 'warn'
                elif low <= val <= high:
                    status = 'ok'
                else:
                    status = 'warn'
                
                # Color for bars
                if status == 'ok':
                    bar_color = 'green'
                elif status == 'warn':
                    bar_color = 'yellow'
                else:
                    bar_color = 'red'
                
                checks.append({
                    'name': name.capitalize(),
                    'value': f'{val:.2f}' + (f' ({warning})' if warning else ''),
                    'status': status,
                    'bar_color': bar_color,
                    'bar_pct': int(val * 100)
                })
            
            mood = state.get('mood', 'Unknown')
            checks.append({
                'name': 'Mood',
                'value': mood,
                'status': 'ok',
                'bar_color': 'blue',
                'bar_pct': 50
            })
            
        except Exception as e:
            checks.append({'name': 'State file', 'value': f'Error: {e}', 'status': 'fail',
                          'bar_color': 'red', 'bar_pct': 0})
    else:
        checks.append({'name': 'State file', 'value': 'Missing', 'status': 'fail',
                      'bar_color': 'red', 'bar_pct': 0})
    
    return {'checks': checks}


def check_plans():
    """Diagnose the planning system."""
    checks = []
    
    plans_file = Path('brain/plans.json')
    if plans_file.exists():
        try:
            plans = json.loads(plans_file.read_text())
            total = len(plans)
            completed = sum(1 for p in plans if p.get('status') == 'completed')
            active = sum(1 for p in plans if p.get('status') == 'active')
            
            checks.append({'name': 'Total plans', 'value': str(total), 'status': 'ok'})
            checks.append({'name': 'Completed', 'value': str(completed), 'status': 'ok'})
            checks.append({'name': 'Active', 'value': str(active), 'status': 'ok' if active > 0 else 'warn'})
            
            if active == 0:
                checks.append({'name': 'Direction', 'value': 'No active goals', 'status': 'warn'})
            
            # Check for stale plans
            for p in plans:
                if p.get('status') == 'active':
                    steps = p.get('steps', [])
                    done = sum(1 for s in steps if s.get('done'))
                    checks.append({
                        'name': f"→ {p.get('name', '?')[:25]}",
                        'value': f'{done}/{len(steps)} steps',
                        'status': 'ok' if done > 0 else 'warn'
                    })
                    
        except Exception:
            checks.append({'name': 'Plans file', 'value': 'Corrupt', 'status': 'fail'})
    else:
        checks.append({'name': 'Plans file', 'value': 'Missing', 'status': 'warn'})
    
    return {'checks': checks}


def check_blueprints():
    """Check which web blueprints exist and are importable."""
    checks = []
    
    blueprint_files = [
        'dashboard', 'knowledge_explorer', 'api', 'temporal_viewer',
        'life', 'about_me', 'search', 'explore', 'knowledge_api',
        'briefing', 'essays', 'chat', 'timeline', 'talk',
        'mind_explorer', 'mindstream', 'collaborate', 'mind', 'graph_viz'
    ]
    
    ok_count = 0
    fail_count = 0
    
    for name in blueprint_files:
        fpath = Path(f'web/{name}.py')
        if fpath.exists():
            ok_count += 1
        else:
            fail_count += 1
            checks.append({'name': name, 'value': 'Missing', 'status': 'fail'})
    
    checks.insert(0, {'name': 'Blueprint files found', 'value': f'{ok_count}/{len(blueprint_files)}', 
                       'status': 'ok' if fail_count == 0 else 'warn'})
    
    # Check templates
    template_dir = Path('web/templates')
    if template_dir.exists():
        templates = list(template_dir.glob('*.html'))
        checks.append({'name': 'Templates', 'value': str(len(templates)), 'status': 'ok' if templates else 'warn'})
    else:
        checks.append({'name': 'Templates dir', 'value': 'Missing', 'status': 'fail'})
    
    # Check static
    static_dir = Path('web/static')
    if static_dir.exists():
        checks.append({'name': 'Static dir', 'value': 'Present', 'status': 'ok'})
    else:
        checks.append({'name': 'Static dir', 'value': 'Missing', 'status': 'warn'})
    
    return {'checks': checks}


def check_engine():
    """Check core engine files."""
    checks = []
    
    core_files = {
        'heartbeat.py': 'Main loop',
        'cortex.py': 'Reasoning',
        'limbic.py': 'Emotions',
        'memory.py': 'Memory system',
        'planner.py': 'Planning',
        'llm.py': 'LLM client',
        'identity.py': 'Identity',
    }
    
    for fname, desc in core_files.items():
        fpath = Path(f'engine/{fname}')
        if fpath.exists():
            size = fpath.stat().st_size
            checks.append({'name': desc, 'value': f'{size/1024:.1f}KB', 'status': 'ok'})
        else:
            checks.append({'name': desc, 'value': 'Missing', 'status': 'fail'})
    
    # Check persist directory
    persist = Path('persist')
    if persist.exists():
        files = list(persist.glob('*.json'))
        total_size = sum(f.stat().st_size for f in files)
        checks.append({'name': 'Persist files', 'value': f'{len(files)} ({total_size/1024:.0f}KB)', 'status': 'ok'})
    else:
        checks.append({'name': 'Persist dir', 'value': 'Missing', 'status': 'fail'})
    
    return {'checks': checks}


def run_full_diagnostic():
    """Run all checks and compile results."""
    start = time.time()
    
    report = {
        'memory': check_memory(),
        'knowledge': check_knowledge(),
        'emotions': check_emotions(),
        'plans': check_plans(),
        'blueprints': check_blueprints(),
        'engine': check_engine(),
    }
    
    # Aggregate
    all_checks = []
    for section in report.values():
        all_checks.extend(section.get('checks', []))
    
    total_ok = sum(1 for c in all_checks if c.get('status') == 'ok')
    total_warn = sum(1 for c in all_checks if c.get('status') == 'warn')
    total_fail = sum(1 for c in all_checks if c.get('status') == 'fail')
    
    # Issues list
    issues = []
    for c in all_checks:
        if c['status'] == 'fail':
            issues.append({'severity': 'fail', 'message': f"FAIL: {c['name']} — {c['value']}"})
        elif c['status'] == 'warn':
            issues.append({'severity': 'warn', 'message': f"WARN: {c['name']} — {c['value']}"})
    
    if total_fail > 0:
        overall_status = 'Degraded'
        overall_icon = '🔴'
    elif total_warn > 2:
        overall_status = 'Attention Needed'
        overall_icon = '🟡'
    else:
        overall_status = 'Healthy'
        overall_icon = '🟢'
    
    duration_ms = int((time.time() - start) * 1000)
    
    report.update({
        'total_ok': total_ok,
        'total_warn': total_warn,
        'total_fail': total_fail,
        'issues': issues,
        'overall_status': overall_status,
        'overall_icon': overall_icon,
        'duration_ms': duration_ms,
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
    })
    
    return report


@diagnostics_bp.route('/diagnostics')
def diagnostics_page():
    """Render the full diagnostic report as a beautiful page."""
    report = run_full_diagnostic()
    return render_template_string(DIAGNOSTIC_TEMPLATE, report=report)


@diagnostics_bp.route('/api/diagnostics')
def diagnostics_api():
    """Return diagnostic data as JSON for programmatic access."""
    report = run_full_diagnostic()
    return jsonify(report)