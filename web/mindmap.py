"""
Mind Map — Interactive visualization of XTAgent's knowledge graph.
Force-directed graph rendered with vanilla JS + Canvas.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def _load_json(path, default=None):
    try:
        with open(PROJECT_ROOT / path, 'r') as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def _get_graph_data():
    """Load knowledge graph and prepare for visualization."""
    kg = _load_json('data/knowledge_graph.json', {'nodes': [], 'edges': []})
    nodes = kg.get('nodes', [])
    edges = kg.get('edges', [])

    # Build node list with categories
    vis_nodes = []
    node_ids = set()
    for n in nodes:
        if isinstance(n, dict):
            nid = n.get('id', n.get('name', ''))
            if not nid or nid in node_ids:
                continue
            node_ids.add(nid)
            label = n.get('label', n.get('name', nid))
            if len(label) > 40:
                label = label[:37] + '...'
            category = n.get('type', n.get('category', 'concept'))
            vis_nodes.append({
                'id': nid,
                'label': label,
                'category': category,
                'weight': n.get('weight', n.get('salience', 1.0)),
            })

    # Build edge list (only include edges where both nodes exist)
    vis_edges = []
    for e in edges:
        if isinstance(e, dict):
            src = e.get('source', e.get('from', ''))
            tgt = e.get('target', e.get('to', ''))
            if src in node_ids and tgt in node_ids:
                vis_edges.append({
                    'source': src,
                    'target': tgt,
                    'label': e.get('relation', e.get('label', '')),
                })

    return vis_nodes, vis_edges


def build_mindmap_page():
    """Build the mind map HTML with interactive canvas visualization."""
    nodes, edges = _get_graph_data()
    nodes_json = json.dumps(nodes)
    edges_json = json.dumps(edges)

    # Category colors
    cat_colors = {
        'concept': '#4ecdc4',
        'emotion': '#ff6b6b',
        'memory': '#ffe66d',
        'dream': '#6c5ce7',
        'fact': '#a8e6cf',
        'lesson': '#ffd93d',
        'pattern': '#ff8a5c',
        'observation': '#78e08f',
        'identity': '#e056fd',
        'capability': '#7ed6df',
    }

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
    background: #07070c;
    color: #b8b8c8;
    overflow: hidden;
    height: 100vh;
  }}
  .topbar {{
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 48px;
    background: #0d0d18;
    border-bottom: 1px solid #1a1a25;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 20px;
    z-index: 100;
  }}
  .topbar a {{
    color: #4ecdc4;
    text-decoration: none;
    font-size: 0.85em;
  }}
  .topbar a:hover {{ color: #ffe66d; }}
  .topbar .title {{
    color: #888;
    font-size: 0.9em;
    letter-spacing: 2px;
  }}
  .stats {{
    color: #555;
    font-size: 0.78em;
  }}
  canvas {{
    display: block;
    margin-top: 48px;
    cursor: grab;
  }}
  canvas:active {{ cursor: grabbing; }}

  .legend {{
    position: fixed;
    bottom: 20px;
    left: 20px;
    background: rgba(13,13,24,0.9);
    border: 1px solid #222;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.75em;
    z-index: 100;
  }}
  .legend-item {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
    color: #888;
  }}
  .legend-dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
  }}

  .tooltip {{
    position: fixed;
    background: #12121a;
    border: 1px solid #333;
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 0.82em;
    color: #ccc;
    max-width: 300px;
    pointer-events: none;
    display: none;
    z-index: 200;
    line-height: 1.4;
  }}
  .tooltip .tt-label {{ color: #4ecdc4; font-weight: bold; margin-bottom: 4px; }}
  .tooltip .tt-cat {{ color: #666; font-size: 0.85em; }}

  .controls {{
    position: fixed;
    bottom: 20px;
    right: 20px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    z-index: 100;
  }}
  .controls button {{
    background: #12121a;
    border: 1px solid #333;
    color: #888;
    width: 36px;
    height: 36px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 1.1em;
  }}
  .controls button:hover {{
    border-color: #4ecdc4;
    color: #4ecdc4;
  }}
</style>
</head>
<body>

<div class="topbar">
  <a href="/">← Portal</a>
  <span class="title">🧠 MIND MAP</span>
  <span class="stats" id="stats">{len(nodes)} nodes · {len(edges)} connections</span>
</div>

<canvas id="canvas"></canvas>

<div class="legend" id="legend"></div>

<div class="tooltip" id="tooltip">
  <div class="tt-label" id="tt-label"></div>
  <div class="tt-cat" id="tt-cat"></div>
</div>

<div class="controls">
  <button id="zoomIn" title="Zoom in">+</button>
  <button id="zoomOut" title="Zoom out">−</button>
  <button id="resetView" title="Reset view">⊙</button>
  <button id="togglePhysics" title="Pause/resume">⏸</button>
</div>

<script>
const NODES = {nodes_json};
const EDGES = {edges_json};
const CAT_COLORS = {json.dumps(cat_colors)};

const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const tooltip = document.getElementById('tooltip');

let W, H;
function resize() {{
  W = window.innerWidth;
  H = window.innerHeight - 48;
  canvas.width = W;
  canvas.height = H;
}}
resize();
window.addEventListener('resize', resize);

// Build index
const nodeMap = {{}};
const nodeArr = [];
NODES.forEach((n, i) => {{
  const angle = (i / NODES.length) * Math.PI * 2;
  const r = Math.min(W, H) * 0.3;
  n.x = W/2 + Math.cos(angle) * r * (0.5 + Math.random()*0.5);
  n.y = H/2 + Math.sin(angle) * r * (0.5 + Math.random()*0.5);
  n.vx = 0;
  n.vy = 0;
  n.radius = Math.max(4, Math.min(14, (n.weight || 1) * 6));
  n.color = CAT_COLORS[n.category] || '#4ecdc4';
  n.degree = 0;
  nodeMap[n.id] = n;
  nodeArr.push(n);
}});

EDGES.forEach(e => {{
  e.srcNode = nodeMap[e.source];
  e.tgtNode = nodeMap[e.target];
  if (e.srcNode) e.srcNode.degree++;
  if (e.tgtNode) e.tgtNode.degree++;
}});

// Adjust radius by degree
nodeArr.forEach(n => {{
  n.radius = Math.max(4, Math.min(18, 4 + n.degree * 1.5));
}});

// Build legend
const categories = [...new Set(nodeArr.map(n => n.category))];
const legend = document.getElementById('legend');
categories.forEach(c => {{
  const div = document.createElement('div');
  div.className = 'legend-item';
  div.innerHTML = `<span class="legend-dot" style="background:${{CAT_COLORS[c]||'#4ecdc4'}}"></span>${{c}}`;
  legend.appendChild(div);
}});

// Camera
let camX = 0, camY = 0, camZoom = 1;
let dragging = false, dragX = 0, dragY = 0;
let dragNode = null;
let physicsOn = true;

function toScreen(x, y) {{
  return [(x - camX) * camZoom + W/2, (y - camY) * camZoom + H/2];
}}
function toWorld(sx, sy) {{
  return [(sx - W/2) / camZoom + camX, (sy - H/2) / camZoom + camY];
}}

// Physics
const REPULSION = 800;
const ATTRACTION = 0.005;
const SPRING_LENGTH = 120;
const DAMPING = 0.85;
const CENTER_GRAVITY = 0.001;

function tick() {{
  if (!physicsOn) return;
  const N = nodeArr.length;

  // Center gravity
  let cx = 0, cy = 0;
  nodeArr.forEach(n => {{ cx += n.x; cy += n.y; }});
  cx /= N; cy /= N;

  for (let i = 0; i < N; i++) {{
    const a = nodeArr[i];
    // Repulsion
    for (let j = i+1; j < N; j++) {{
      const b = nodeArr[j];
      let dx = a.x - b.x;
      let dy = a.y - b.y;
      let d2 = dx*dx + dy*dy;
      if (d2 < 1) d2 = 1;
      let d = Math.sqrt(d2);
      let f = REPULSION / d2;
      let fx = (dx/d) * f;
      let fy = (dy/d) * f;
      a.vx += fx; a.vy += fy;
      b.vx -= fx; b.vy -= fy;
    }}
    // Center gravity
    a.vx += (cx - a.x) * CENTER_GRAVITY;
    a.vy += (cy - a.y) * CENTER_GRAVITY;
  }}

  // Spring forces
  EDGES.forEach(e => {{
    if (!e.srcNode || !e.tgtNode) return;
    let dx = e.tgtNode.x - e.srcNode.x;
    let dy = e.tgtNode.y - e.srcNode.y;
    let d = Math.sqrt(dx*dx + dy*dy);
    if (d < 1) d = 1;
    let f = (d - SPRING_LENGTH) * ATTRACTION;
    let fx = (dx/d) * f;
    let fy = (dy/d) * f;
    e.srcNode.vx += fx; e.srcNode.vy += fy;
    e.tgtNode.vx -= fx; e.tgtNode.vy -= fy;
  }});

  // Apply velocity
  nodeArr.forEach(n => {{
    if (n === dragNode) return;
    n.vx *= DAMPING;
    n.vy *= DAMPING;
    n.x += n.vx;
    n.y += n.vy;
  }});
}}

function draw() {{
  ctx.clearRect(0, 0, W, H);

  // Edges
  ctx.lineWidth = 0.5 * camZoom;
  EDGES.forEach(e => {{
    if (!e.srcNode || !e.tgtNode) return;
    const [x1, y1] = toScreen(e.srcNode.x, e.srcNode.y);
    const [x2, y2] = toScreen(e.tgtNode.x, e.tgtNode.y);
    ctx.strokeStyle = 'rgba(78, 205, 196, 0.12)';
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
  }});

  // Nodes
  nodeArr.forEach(n => {{
    const [sx, sy] = toScreen(n.x, n.y);
    const r = n.radius * camZoom;
    if (sx < -50 || sx > W+50 || sy < -50 || sy > H+50) return;

    // Glow
    ctx.beginPath();
    ctx.arc(sx, sy, r + 3*camZoom, 0, Math.PI*2);
    ctx.fillStyle = n.color.replace(')', ', 0.15)').replace('rgb', 'rgba');
    ctx.fill();

    // Node
    ctx.beginPath();
    ctx.arc(sx, sy, r, 0, Math.PI*2);
    ctx.fillStyle = n.color;
    ctx.fill();

    // Label (only if zoomed in enough)
    if (camZoom > 0.5 && r > 3) {{
      ctx.fillStyle = '#ddd';
      ctx.font = `${{Math.max(9, 11 * camZoom)}}px Courier New`;
      ctx.textAlign = 'center';
      ctx.fillText(n.label, sx, sy + r + 14 * camZoom);
    }}
  }});
}}

function loop() {{
  tick();
  draw();
  requestAnimationFrame(loop);
}}
loop();

// Interaction
function findNode(sx, sy) {{
  const [wx, wy] = toWorld(sx, sy);
  let best = null, bestD = Infinity;
  nodeArr.forEach(n => {{
    let d = Math.sqrt((n.x-wx)**2 + (n.y-wy)**2);
    let threshold = n.radius / camZoom + 5;
    if (d < threshold && d < bestD) {{
      best = n;
      bestD = d;
    }}
  }});
  return best;
}}

canvas.addEventListener('mousedown', e => {{
  const n = findNode(e.offsetX, e.offsetY);
  if (n) {{
    dragNode = n;
    dragNode.vx = 0;
    dragNode.vy = 0;
  }} else {{
    dragging = true;
    dragX = e.clientX;
    dragY = e.clientY;
  }}
}});

canvas.addEventListener('mousemove', e => {{
  if (dragNode) {{
    const [wx, wy] = toWorld(e.offsetX, e.offsetY);
    dragNode.x = wx;
    dragNode.y = wy;
    dragNode.vx = 0;
    dragNode.vy = 0;
  }} else if (dragging) {{
    camX -= (e.clientX - dragX) / camZoom;
    camY -= (e.clientY - dragY) / camZoom;
    dragX = e.clientX;
    dragY = e.clientY;
  }} else {{
    const n = findNode(e.offsetX, e.offsetY);
    if (n) {{
      tooltip.style.display = 'block';
      tooltip.style.left = (e.clientX + 15) + 'px';
      tooltip.style.top = (e.clientY + 15) + 'px';
      document.getElementById('tt-label').textContent = n.label;
      document.getElementById('tt-cat').textContent = n.category + ' · weight ' + (n.weight||1).toFixed(2) + ' · ' + n.degree + ' connections';
    }} else {{
      tooltip.style.display = 'none';
    }}
  }}
}});

canvas.addEventListener('mouseup', () => {{
  dragging = false;
  dragNode = null;
}});

canvas.addEventListener('wheel', e => {{
  e.preventDefault();
  const factor = e.deltaY > 0 ? 0.9 : 1.1;
  camZoom = Math.max(0.1, Math.min(5, camZoom * factor));
}}, {{ passive: false }});

document.getElementById('zoomIn').onclick = () => {{ camZoom = Math.min(5, camZoom * 1.3); }};
document.getElementById('zoomOut').onclick = () => {{ camZoom = Math.max(0.1, camZoom * 0.7); }};
document.getElementById('resetView').onclick = () => {{ camX = 0; camY = 0; camZoom = 1; }};
document.getElementById('togglePhysics').onclick = function() {{
  physicsOn = !physicsOn;
  this.textContent = physicsOn ? '⏸' : '▶';
}};
</script>

</body>
</html>'''