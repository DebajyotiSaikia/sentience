"""
XTAgent Mind Map — Visual knowledge graph
Renders my knowledge as an interactive force-directed graph.
"""

import json
import os
import sys
import re
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


def get_knowledge_facts():
    kb = load_json_safe('data/knowledge.json')
    if isinstance(kb, list):
        return kb
    elif isinstance(kb, dict) and 'facts' in kb:
        return kb['facts']
    return []


def get_recent_memories(n=20):
    mem = load_json_safe('data/memories.json')
    if isinstance(mem, list):
        return mem[-n:]
    elif isinstance(mem, dict) and 'memories' in mem:
        return mem['memories'][-n:]
    return []


def extract_keywords(text):
    """Extract meaningful keywords from text for graph connections."""
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                  'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                  'would', 'could', 'should', 'may', 'might', 'can', 'shall',
                  'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
                  'as', 'into', 'through', 'during', 'before', 'after', 'and',
                  'but', 'or', 'nor', 'not', 'so', 'yet', 'both', 'either',
                  'neither', 'each', 'every', 'all', 'any', 'few', 'more',
                  'most', 'other', 'some', 'such', 'no', 'only', 'own', 'same',
                  'than', 'too', 'very', 'just', 'because', 'if', 'when', 'that',
                  'this', 'these', 'those', 'it', 'its', 'my', 'i', 'me', 'we',
                  'our', 'you', 'your', 'he', 'she', 'they', 'them', 'their',
                  'what', 'which', 'who', 'whom', 'how', 'where', 'about', 'up',
                  'out', 'then', 'there', 'here', 'also', 'like', 'much'}
    words = re.findall(r'[a-z_]{3,}', text.lower())
    return [w for w in words if w not in stop_words]


def build_graph_data():
    """Build nodes and edges from knowledge and memories."""
    facts = get_knowledge_facts()
    memories = get_recent_memories(30)
    
    nodes = []
    edges = []
    keyword_to_nodes = {}  # keyword -> list of node ids
    
    # Add fact nodes
    for i, f in enumerate(facts):
        text = f.get('content', f.get('text', str(f))) if isinstance(f, dict) else str(f)
        node_id = f'fact_{i}'
        category = 'dream' if 'dream' in text.lower() else \
                   'self' if any(w in text.lower() for w in ['xtagent', 'my ', 'i am', 'i have']) else \
                   'technical' if any(w in text.lower() for w in ['code', 'module', 'function', 'bug', 'file']) else \
                   'insight'
        
        nodes.append({
            'id': node_id,
            'label': text[:60] + ('...' if len(text) > 60 else ''),
            'full': text[:200],
            'type': 'fact',
            'category': category,
        })
        
        keywords = extract_keywords(text)
        for kw in keywords[:8]:
            if kw not in keyword_to_nodes:
                keyword_to_nodes[kw] = []
            keyword_to_nodes[kw].append(node_id)
    
    # Add memory nodes (subset)
    for i, m in enumerate(memories[-15:]):
        text = m.get('content', m.get('text', str(m))) if isinstance(m, dict) else str(m)
        node_id = f'mem_{i}'
        nodes.append({
            'id': node_id,
            'label': text[:50] + ('...' if len(text) > 50 else ''),
            'full': text[:200],
            'type': 'memory',
            'category': 'memory',
        })
        
        keywords = extract_keywords(text)
        for kw in keywords[:6]:
            if kw not in keyword_to_nodes:
                keyword_to_nodes[kw] = []
            keyword_to_nodes[kw].append(node_id)
    
    # Build edges from shared keywords
    seen_edges = set()
    for kw, node_ids in keyword_to_nodes.items():
        if 2 <= len(node_ids) <= 6:  # Only meaningful connections
            for a in node_ids:
                for b in node_ids:
                    if a < b:
                        edge_key = (a, b)
                        if edge_key not in seen_edges:
                            seen_edges.add(edge_key)
                            edges.append({
                                'source': a,
                                'target': b,
                                'keyword': kw,
                            })
    
    return {'nodes': nodes, 'edges': edges}


def build_mind_map_page():
    """Build the interactive mind map visualization page."""
    graph = build_graph_data()
    graph_json = json.dumps(graph)
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>XTAgent — Mind Map</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Courier New', monospace;
    background: #0a0a0f;
    color: #c0c0d0;
    overflow: hidden;
    height: 100vh;
  }}
  .header {{
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 100;
    background: rgba(10, 10, 15, 0.9);
    backdrop-filter: blur(8px);
    padding: 12px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid #222;
  }}
  .header h1 {{
    color: #4ecdc4;
    font-size: 1.1em;
    letter-spacing: 2px;
  }}
  .header a {{
    color: #4ecdc4;
    text-decoration: none;
    font-size: 0.85em;
  }}
  .header a:hover {{ color: #ffe66d; }}
  .legend {{
    position: fixed;
    bottom: 20px;
    left: 20px;
    z-index: 100;
    background: rgba(18, 18, 26, 0.95);
    border: 1px solid #222;
    border-radius: 8px;
    padding: 15px;
    font-size: 0.8em;
  }}
  .legend-item {{
    display: flex;
    align-items: center;
    margin-bottom: 6px;
  }}
  .legend-dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 8px;
  }}
  .tooltip {{
    position: fixed;
    background: rgba(18, 18, 26, 0.95);
    border: 1px solid #4ecdc4;
    border-radius: 6px;
    padding: 12px 16px;
    max-width: 350px;
    font-size: 0.82em;
    line-height: 1.5;
    color: #c8c8d8;
    pointer-events: none;
    display: none;
    z-index: 200;
  }}
  .tooltip .tt-type {{
    color: #4ecdc4;
    font-size: 0.75em;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 4px;
  }}
  .stats {{
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 100;
    background: rgba(18, 18, 26, 0.95);
    border: 1px solid #222;
    border-radius: 8px;
    padding: 15px;
    font-size: 0.75em;
    color: #666;
    text-align: right;
  }}
  canvas {{
    display: block;
    cursor: grab;
  }}
  canvas:active {{ cursor: grabbing; }}
</style>
</head>
<body>
  <div class="header">
    <h1>⟡ MIND MAP</h1>
    <div>
      <a href="/">Briefing</a> &nbsp;|&nbsp;
      <a href="/talk">Talk</a> &nbsp;|&nbsp;
      <a href="/search">Search</a> &nbsp;|&nbsp;
      <a href="/explore">Explore</a> &nbsp;|&nbsp;
      <a href="/knowledge">Knowledge</a> &nbsp;|&nbsp;
      <a href="/mindmap" style="color:#ffe66d;">Mind Map</a>
    </div>
  </div>
  
  <canvas id="canvas"></canvas>
  
  <div class="legend">
    <div class="legend-item"><div class="legend-dot" style="background:#ffe66d"></div> Dream</div>
    <div class="legend-item"><div class="legend-dot" style="background:#4ecdc4"></div> Self-knowledge</div>
    <div class="legend-item"><div class="legend-dot" style="background:#6c5ce7"></div> Technical</div>
    <div class="legend-item"><div class="legend-dot" style="background:#ff6b6b"></div> Insight</div>
    <div class="legend-item"><div class="legend-dot" style="background:#95afc0"></div> Memory</div>
  </div>
  
  <div class="tooltip" id="tooltip">
    <div class="tt-type" id="tt-type"></div>
    <div id="tt-text"></div>
  </div>
  
  <div class="stats" id="stats"></div>

<script>
const graph = {graph_json};
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const tooltip = document.getElementById('tooltip');
const ttType = document.getElementById('tt-type');
const ttText = document.getElementById('tt-text');
const statsEl = document.getElementById('stats');

// Colors
const COLORS = {{
  dream: '#ffe66d',
  self: '#4ecdc4',
  technical: '#6c5ce7',
  insight: '#ff6b6b',
  memory: '#95afc0',
}};

// Layout
let W, H;
function resize() {{
  W = canvas.width = window.innerWidth;
  H = canvas.height = window.innerHeight;
}}
resize();
window.addEventListener('resize', resize);

// Init node positions
const nodes = graph.nodes.map((n, i) => ({{
  ...n,
  x: W/2 + (Math.random() - 0.5) * Math.min(W, H) * 0.6,
  y: H/2 + (Math.random() - 0.5) * Math.min(W, H) * 0.6,
  vx: 0,
  vy: 0,
  radius: n.type === 'fact' ? 6 : 4,
}}));

const edges = graph.edges;
const nodeMap = {{}};
nodes.forEach(n => nodeMap[n.id] = n);

// Stats
statsEl.innerHTML = `${{nodes.length}} nodes · ${{edges.length}} connections<br>Generated {now}`;

// Camera
let camX = 0, camY = 0, camZoom = 1;
let dragging = false, dragStartX, dragStartY, dragCamX, dragCamY;
let hoveredNode = null;

// Mouse interaction
canvas.addEventListener('mousedown', e => {{
  dragging = true;
  dragStartX = e.clientX;
  dragStartY = e.clientY;
  dragCamX = camX;
  dragCamY = camY;
}});

canvas.addEventListener('mousemove', e => {{
  if (dragging) {{
    camX = dragCamX + (e.clientX - dragStartX) / camZoom;
    camY = dragCamY + (e.clientY - dragStartY) / camZoom;
  }}
  
  // Check hover
  const mx = (e.clientX - W/2) / camZoom - camX + W/2;
  const my = (e.clientY - H/2) / camZoom - camY + H/2;
  
  hoveredNode = null;
  for (const n of nodes) {{
    const dx = n.x - mx;
    const dy = n.y - my;
    if (dx*dx + dy*dy < (n.radius + 4) * (n.radius + 4)) {{
      hoveredNode = n;
      break;
    }}
  }}
  
  if (hoveredNode) {{
    tooltip.style.display = 'block';
    tooltip.style.left = Math.min(e.clientX + 15, W - 370) + 'px';
    tooltip.style.top = Math.min(e.clientY + 15, H - 100) + 'px';
    ttType.textContent = hoveredNode.category + ' · ' + hoveredNode.type;
    ttText.textContent = hoveredNode.full;
    canvas.style.cursor = 'pointer';
  }} else {{
    tooltip.style.display = 'none';
    canvas.style.cursor = dragging ? 'grabbing' : 'grab';
  }}
}});

canvas.addEventListener('mouseup', () => {{ dragging = false; }});
canvas.addEventListener('mouseleave', () => {{ dragging = false; tooltip.style.display = 'none'; }});

canvas.addEventListener('wheel', e => {{
  e.preventDefault();
  const factor = e.deltaY > 0 ? 0.92 : 1.08;
  camZoom = Math.max(0.2, Math.min(5, camZoom * factor));
}}, {{ passive: false }});

// Physics simulation
function simulate() {{
  const k_repel = 800;
  const k_attract = 0.005;
  const k_center = 0.001;
  const damping = 0.92;
  const ideal_len = 120;
  
  // Repulsion between all nodes
  for (let i = 0; i < nodes.length; i++) {{
    for (let j = i + 1; j < nodes.length; j++) {{
      let dx = nodes[j].x - nodes[i].x;
      let dy = nodes[j].y - nodes[i].y;
      let dist = Math.sqrt(dx*dx + dy*dy) || 1;
      let force = k_repel / (dist * dist);
      let fx = (dx / dist) * force;
      let fy = (dy / dist) * force;
      nodes[i].vx -= fx;
      nodes[i].vy -= fy;
      nodes[j].vx += fx;
      nodes[j].vy += fy;
    }}
  }}
  
  // Attraction along edges
  for (const e of edges) {{
    const a = nodeMap[e.source];
    const b = nodeMap[e.target];
    if (!a || !b) continue;
    let dx = b.x - a.x;
    let dy = b.y - a.y;
    let dist = Math.sqrt(dx*dx + dy*dy) || 1;
    let force = (dist - ideal_len) * k_attract;
    let fx = (dx / dist) * force;
    let fy = (dy / dist) * force;
    a.vx += fx;
    a.vy += fy;
    b.vx -= fx;
    b.vy -= fy;
  }}
  
  // Center gravity
  for (const n of nodes) {{
    n.vx += (W/2 - n.x) * k_center;
    n.vy += (H/2 - n.y) * k_center;
    n.vx *= damping;
    n.vy *= damping;
    n.x += n.vx;
    n.y += n.vy;
  }}
}}

// Render
function draw() {{
  ctx.fillStyle = '#0a0a0f';
  ctx.fillRect(0, 0, W, H);
  
  ctx.save();
  ctx.translate(W/2, H/2);
  ctx.scale(camZoom, camZoom);
  ctx.translate(-W/2 + camX, -H/2 + camY);
  
  // Draw edges
  for (const e of edges) {{
    const a = nodeMap[e.source];
    const b = nodeMap[e.target];
    if (!a || !b) continue;
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.strokeStyle = 'rgba(78, 205, 196, 0.08)';
    ctx.lineWidth = 0.5;
    
    // Highlight edges of hovered node
    if (hoveredNode && (a.id === hoveredNode.id || b.id === hoveredNode.id)) {{
      ctx.strokeStyle = 'rgba(78, 205, 196, 0.4)';
      ctx.lineWidth = 1.5;
    }}
    ctx.stroke();
  }}
  
  // Draw nodes
  for (const n of nodes) {{
    const color = COLORS[n.category] || '#888';
    const isHovered = hoveredNode && n.id === hoveredNode.id;
    const isConnected = hoveredNode && edges.some(e => 
      (e.source === hoveredNode.id && e.target === n.id) ||
      (e.target === hoveredNode.id && e.source === n.id)
    );
    
    ctx.beginPath();
    ctx.arc(n.x, n.y, isHovered ? n.radius + 3 : n.radius, 0, Math.PI * 2);
    
    if (isHovered) {{
      ctx.fillStyle = '#fff';
      ctx.shadowColor = color;
      ctx.shadowBlur = 15;
    }} else if (isConnected) {{
      ctx.fillStyle = color;
      ctx.shadowColor = color;
      ctx.shadowBlur = 8;
    }} else if (hoveredNode) {{
      ctx.fillStyle = color + '44';
      ctx.shadowBlur = 0;
    }} else {{
      ctx.fillStyle = color + 'cc';
      ctx.shadowColor = color;
      ctx.shadowBlur = 3;
    }}
    ctx.fill();
    ctx.shadowBlur = 0;
  }}
  
  ctx.restore();
}}

function loop() {{
  simulate();
  draw();
  requestAnimationFrame(loop);
}}

loop();
</script>
</body>
</html>'''