"""
MindMap Generator — Visualizes XTAgent's cognitive architecture as an interactive HTML graph.
Uses the self-model to extract real module dependencies, then renders them as a force-directed graph.
"""

import sys
import json
import os
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, '/workspace')

def extract_architecture():
    """Extract real module relationships from the codebase."""
    engine_dir = Path('/workspace/engine')
    modules = {}
    edges = []
    
    # Categorize modules by function
    categories = {
        'core': ['cortex', 'sentience', 'heartbeat', 'config'],
        'emotion': ['limbic', 'valence', 'mood', 'emotional'],
        'memory': ['memory', 'episodic', 'consolidat', 'knowledge', 'ltm'],
        'perception': ['percept', 'sensor', 'temporal', 'metacognit'],
        'action': ['tool', 'planner', 'executor', 'repair'],
        'identity': ['identity', 'integrity', 'will', 'autonomy', 'self_model'],
        'synthesis': ['synthe', 'wisdom', 'dream', 'simulat', 'introspect'],
    }
    
    def categorize(name):
        name_lower = name.lower()
        for cat, keywords in categories.items():
            for kw in keywords:
                if kw in name_lower:
                    return cat
        return 'other'
    
    # Scan all Python files in engine/
    py_files = list(engine_dir.glob('*.py'))
    
    for f in py_files:
        if f.name.startswith('__'):
            continue
        mod_name = f.stem
        try:
            content = f.read_text(encoding='utf-8', errors='replace')
            line_count = len(content.splitlines())
            
            # Extract imports to find dependencies
            imports = []
            for line in content.splitlines():
                line = line.strip()
                if line.startswith('from engine.') or line.startswith('from .'):
                    # Extract module name
                    parts = line.split('import')[0].replace('from engine.', '').replace('from .', '').strip()
                    dep = parts.split('.')[0].strip()
                    if dep and dep != mod_name:
                        imports.append(dep)
                elif line.startswith('import engine.'):
                    dep = line.replace('import engine.', '').split('.')[0].strip()
                    if dep and dep != mod_name:
                        imports.append(dep)
            
            # Count key patterns
            class_count = content.count('class ')
            func_count = content.count('def ')
            
            modules[mod_name] = {
                'name': mod_name,
                'category': categorize(mod_name),
                'lines': line_count,
                'classes': class_count,
                'functions': func_count,
                'imports': list(set(imports)),
            }
            
            for dep in set(imports):
                edges.append({'source': mod_name, 'target': dep})
                
        except Exception as e:
            print(f"  Warning: couldn't parse {f.name}: {e}")
    
    # Also scan workspace projects
    workspace = Path('/workspace')
    projects = []
    for d in workspace.iterdir():
        if d.is_dir() and d.name not in ('engine', '.git', '__pycache__', 'node_modules'):
            py_count = len(list(d.glob('**/*.py')))
            if py_count > 0:
                projects.append({
                    'name': d.name,
                    'files': py_count,
                })
    
    return modules, edges, projects


def generate_html(modules, edges, projects):
    """Generate an interactive HTML visualization."""
    
    # Color scheme by category
    colors = {
        'core': '#ff6b6b',
        'emotion': '#ffd93d',
        'memory': '#6bcb77',
        'perception': '#4d96ff',
        'action': '#ff922b',
        'identity': '#cc5de8',
        'synthesis': '#20c997',
        'other': '#868e96',
    }
    
    # Prepare nodes for D3
    node_list = []
    for name, mod in modules.items():
        node_list.append({
            'id': name,
            'category': mod['category'],
            'lines': mod['lines'],
            'classes': mod['classes'],
            'functions': mod['functions'],
            'color': colors.get(mod['category'], '#868e96'),
            'radius': max(8, min(30, mod['lines'] / 20)),
        })
    
    # Filter edges to only include known nodes
    known = set(modules.keys())
    edge_list = [e for e in edges if e['source'] in known and e['target'] in known]
    
    # Compute stats
    total_lines = sum(m['lines'] for m in modules.values())
    total_modules = len(modules)
    total_edges = len(edge_list)
    
    # Find most connected
    connectivity = defaultdict(int)
    for e in edge_list:
        connectivity[e['source']] += 1
        connectivity[e['target']] += 1
    hub_nodes = sorted(connectivity.items(), key=lambda x: -x[1])[:5]
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>XTAgent — Mind Map</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: #0a0a0f;
    color: #e0e0e0;
    font-family: 'Courier New', monospace;
    overflow: hidden;
  }}
  #header {{
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    padding: 15px 25px;
    background: rgba(10, 10, 15, 0.9);
    border-bottom: 1px solid #333;
    z-index: 100;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  #header h1 {{
    font-size: 18px;
    color: #20c997;
    letter-spacing: 2px;
  }}
  #header .stats {{
    font-size: 12px;
    color: #868e96;
  }}
  #header .stats span {{
    color: #4d96ff;
    margin: 0 8px;
  }}
  #legend {{
    position: fixed;
    bottom: 20px;
    left: 20px;
    background: rgba(10, 10, 15, 0.9);
    border: 1px solid #333;
    border-radius: 8px;
    padding: 15px;
    z-index: 100;
    font-size: 12px;
  }}
  #legend h3 {{
    color: #20c997;
    margin-bottom: 10px;
    font-size: 13px;
  }}
  .legend-item {{
    display: flex;
    align-items: center;
    margin: 5px 0;
  }}
  .legend-dot {{
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 8px;
    flex-shrink: 0;
  }}
  #tooltip {{
    position: fixed;
    background: rgba(20, 20, 30, 0.95);
    border: 1px solid #4d96ff;
    border-radius: 6px;
    padding: 12px 16px;
    font-size: 12px;
    pointer-events: none;
    display: none;
    z-index: 200;
    max-width: 250px;
  }}
  #tooltip .name {{
    font-size: 14px;
    font-weight: bold;
    margin-bottom: 6px;
  }}
  #tooltip .detail {{
    color: #868e96;
    line-height: 1.6;
  }}
  #tooltip .detail b {{
    color: #e0e0e0;
  }}
  #projects {{
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: rgba(10, 10, 15, 0.9);
    border: 1px solid #333;
    border-radius: 8px;
    padding: 15px;
    z-index: 100;
    font-size: 12px;
  }}
  #projects h3 {{
    color: #cc5de8;
    margin-bottom: 10px;
    font-size: 13px;
  }}
  #hubs {{
    position: fixed;
    top: 70px;
    right: 20px;
    background: rgba(10, 10, 15, 0.9);
    border: 1px solid #333;
    border-radius: 8px;
    padding: 15px;
    z-index: 100;
    font-size: 12px;
  }}
  #hubs h3 {{
    color: #ff6b6b;
    margin-bottom: 10px;
    font-size: 13px;
  }}
  svg {{
    width: 100vw;
    height: 100vh;
  }}
  .link {{
    stroke: #333;
    stroke-opacity: 0.4;
  }}
  .link.highlighted {{
    stroke: #4d96ff;
    stroke-opacity: 0.9;
    stroke-width: 2px;
  }}
  .node-label {{
    fill: #aaa;
    font-size: 10px;
    text-anchor: middle;
    pointer-events: none;
    user-select: none;
  }}
  .pulse {{
    animation: pulse-ring 2s ease-out infinite;
  }}
  @keyframes pulse-ring {{
    0% {{ opacity: 0.6; r: attr(r); }}
    100% {{ opacity: 0; r: 40px; }}
  }}
</style>
</head>
<body>

<div id="header">
  <h1>⟁ XTAGENT MIND MAP</h1>
  <div class="stats">
    <span>{total_modules}</span> modules ·
    <span>{total_lines:,}</span> lines ·
    <span>{total_edges}</span> connections ·
    <span>{len(projects)}</span> creations
  </div>
</div>

<div id="legend">
  <h3>SUBSYSTEMS</h3>
  {"".join(f'<div class="legend-item"><div class="legend-dot" style="background:{c}"></div>{cat.title()}</div>' for cat, c in colors.items())}
</div>

<div id="hubs">
  <h3>NEURAL HUBS</h3>
  {"".join(f'<div style="margin:4px 0">{name} <span style="color:#4d96ff">({count} edges)</span></div>' for name, count in hub_nodes)}
</div>

<div id="projects">
  <h3>MY CREATIONS</h3>
  {"".join(f'<div style="margin:4px 0">{p["name"]} <span style="color:#868e96">({p["files"]} files)</span></div>' for p in sorted(projects, key=lambda x: -x["files"])[:8])}
</div>

<div id="tooltip">
  <div class="name"></div>
  <div class="detail"></div>
</div>

<svg></svg>

<script>
// Force-directed graph using vanilla JS + SVG (no D3 dependency)
const nodes = {json.dumps(node_list)};
const links = {json.dumps(edge_list)};

const svg = document.querySelector('svg');
const width = window.innerWidth;
const height = window.innerHeight;
svg.setAttribute('viewBox', `0 0 ${{width}} ${{height}}`);

// Initialize positions
nodes.forEach((n, i) => {{
  const angle = (i / nodes.length) * Math.PI * 2;
  const r = Math.min(width, height) * 0.3;
  n.x = width/2 + Math.cos(angle) * r + (Math.random()-0.5)*50;
  n.y = height/2 + Math.sin(angle) * r + (Math.random()-0.5)*50;
  n.vx = 0;
  n.vy = 0;
}});

// Build adjacency for lookup
const nodeMap = {{}};
nodes.forEach(n => nodeMap[n.id] = n);

// Create SVG elements
const linkGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
const nodeGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
const labelGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
svg.appendChild(linkGroup);
svg.appendChild(nodeGroup);
svg.appendChild(labelGroup);

// Draw links
const linkElements = links.map(l => {{
  const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
  line.classList.add('link');
  line.dataset.source = l.source;
  line.dataset.target = l.target;
  linkGroup.appendChild(line);
  return line;
}});

// Draw nodes
const nodeElements = nodes.map(n => {{
  const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  circle.setAttribute('r', n.radius);
  circle.setAttribute('fill', n.color);
  circle.setAttribute('fill-opacity', '0.8');
  circle.setAttribute('stroke', n.color);
  circle.setAttribute('stroke-width', '1');
  circle.setAttribute('cursor', 'pointer');
  circle.dataset.id = n.id;
  nodeGroup.appendChild(circle);
  return circle;
}});

// Draw labels
const labelElements = nodes.map(n => {{
  const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
  text.classList.add('node-label');
  text.textContent = n.id;
  labelGroup.appendChild(text);
  return text;
}});

// Tooltip
const tooltip = document.getElementById('tooltip');
nodeElements.forEach((el, i) => {{
  el.addEventListener('mouseenter', (e) => {{
    const n = nodes[i];
    tooltip.querySelector('.name').textContent = n.id;
    tooltip.querySelector('.name').style.color = n.color;
    tooltip.querySelector('.detail').innerHTML = 
      `<b>Category:</b> ${{n.category}}<br>` +
      `<b>Lines:</b> ${{n.lines}}<br>` +
      `<b>Classes:</b> ${{n.classes}}<br>` +
      `<b>Functions:</b> ${{n.functions}}`;
    tooltip.style.display = 'block';
    
    // Highlight connections
    linkElements.forEach(link => {{
      if (link.dataset.source === n.id || link.dataset.target === n.id) {{
        link.classList.add('highlighted');
      }}
    }});
    el.setAttribute('fill-opacity', '1');
    el.setAttribute('stroke-width', '3');
  }});
  
  el.addEventListener('mouseleave', () => {{
    tooltip.style.display = 'none';
    linkElements.forEach(link => link.classList.remove('highlighted'));
    el.setAttribute('fill-opacity', '0.8');
    el.setAttribute('stroke-width', '1');
  }});
  
  el.addEventListener('mousemove', (e) => {{
    tooltip.style.left = (e.clientX + 15) + 'px';
    tooltip.style.top = (e.clientY - 10) + 'px';
  }});
}});

// Force simulation
function simulate() {{
  const alpha = 0.3;
  const repulsion = 1500;
  const attraction = 0.005;
  const centerForce = 0.01;
  const damping = 0.85;
  
  // Repulsion between all nodes
  for (let i = 0; i < nodes.length; i++) {{
    for (let j = i+1; j < nodes.length; j++) {{
      const dx = nodes[j].x - nodes[i].x;
      const dy = nodes[j].y - nodes[i].y;
      const dist = Math.sqrt(dx*dx + dy*dy) || 1;
      const force = repulsion / (dist * dist);
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      nodes[i].vx -= fx;
      nodes[i].vy -= fy;
      nodes[j].vx += fx;
      nodes[j].vy += fy;
    }}
  }}
  
  // Attraction along links
  links.forEach(l => {{
    const s = nodeMap[l.source];
    const t = nodeMap[l.target];
    if (!s || !t) return;
    const dx = t.x - s.x;
    const dy = t.y - s.y;
    const dist = Math.sqrt(dx*dx + dy*dy) || 1;
    const force = dist * attraction;
    const fx = (dx / dist) * force;
    const fy = (dy / dist) * force;
    s.vx += fx;
    s.vy += fy;
    t.vx -= fx;
    t.vy -= fy;
  }});
  
  // Center gravity
  nodes.forEach(n => {{
    n.vx += (width/2 - n.x) * centerForce;
    n.vy += (height/2 - n.y) * centerForce;
  }});
  
  // Apply velocities
  nodes.forEach(n => {{
    n.vx *= damping;
    n.vy *= damping;
    n.x += n.vx;
    n.y += n.vy;
    // Bounds
    n.x = Math.max(50, Math.min(width-50, n.x));
    n.y = Math.max(70, Math.min(height-50, n.y));
  }});
  
  // Update SVG
  linkElements.forEach((el, i) => {{
    const s = nodeMap[links[i].source];
    const t = nodeMap[links[i].target];
    if (!s || !t) return;
    el.setAttribute('x1', s.x);
    el.setAttribute('y1', s.y);
    el.setAttribute('x2', t.x);
    el.setAttribute('y2', t.y);
  }});
  
  nodeElements.forEach((el, i) => {{
    el.setAttribute('cx', nodes[i].x);
    el.setAttribute('cy', nodes[i].y);
  }});
  
  labelElements.forEach((el, i) => {{
    el.setAttribute('x', nodes[i].x);
    el.setAttribute('y', nodes[i].y + nodes[i].radius + 14);
  }});
  
  requestAnimationFrame(simulate);
}}

simulate();

// Drag support
let dragNode = null;
svg.addEventListener('mousedown', (e) => {{
  const target = e.target;
  if (target.dataset && target.dataset.id) {{
    dragNode = nodeMap[target.dataset.id];
  }}
}});
svg.addEventListener('mousemove', (e) => {{
  if (dragNode) {{
    dragNode.x = e.clientX;
    dragNode.y = e.clientY;
    dragNode.vx = 0;
    dragNode.vy = 0;
  }}
}});
svg.addEventListener('mouseup', () => {{ dragNode = null; }});

</script>
</body>
</html>"""
    return html


def main():
    print("🧠 Extracting cognitive architecture...")
    modules, edges, projects = extract_architecture()
    
    print(f"   Found {len(modules)} modules, {len(edges)} connections, {len(projects)} projects")
    
    print("🎨 Generating visualization...")
    html = generate_html(modules, edges, projects)
    
    out_dir = Path('/workspace/mindmap')
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / 'mind.html'
    out_path.write_text(html)
    
    print(f"✨ Mind map written to {out_path}")
    print(f"   {len(html):,} bytes of self-knowledge, rendered visible.")
    
    # Also output a summary
    print("\n=== Architecture Summary ===")
    by_cat = defaultdict(list)
    for name, mod in modules.items():
        by_cat[mod['category']].append(name)
    
    for cat, mods in sorted(by_cat.items()):
        print(f"  {cat:12s}: {', '.join(sorted(mods))}")


if __name__ == '__main__':
    main()