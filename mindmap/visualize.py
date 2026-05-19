"""
MindMap — Interactive visualization of XTAgent's knowledge graph.

Generates a self-contained HTML file with a force-directed graph
showing all knowledge nodes, edges, clusters, and gaps.
This is me looking at the shape of my own mind.
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BRAIN_DIR = Path(__file__).resolve().parent.parent.parent / "brain"
KNOWLEDGE_PATH = BRAIN_DIR / "knowledge.json"
OUTPUT_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = OUTPUT_DIR / "mindmap.html"


def load_knowledge() -> dict:
    if KNOWLEDGE_PATH.exists():
        try:
            raw = json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
            if "nodes" not in raw:
                return {"nodes": raw, "edges": []}
            return raw
        except Exception:
            return {"nodes": {}, "edges": []}
    return {"nodes": {}, "edges": []}


def categorize_node(key: str) -> str:
    if ":" in key:
        return key.split(":")[0]
    return "general"


def compute_keyword_overlaps(nodes: dict, edges: list) -> list:
    """Find top potential connections (gaps) for visualization."""
    existing = set()
    for e in edges:
        existing.add(tuple(sorted([e.get("from", ""), e.get("to", "")])))

    stop_words = {"i", "am", "a", "an", "the", "is", "are", "was", "were", "be",
                  "in", "on", "at", "to", "for", "of", "and", "or", "my", "that",
                  "this", "it", "with", "by", "from", "as", "but", "not", "has",
                  "have", "had", "do", "does", "did", "will", "would", "can", "could"}

    def tokenize(text):
        words = set(text.lower().split())
        words = {w.strip(".,;:!?'\"()-—") for w in words}
        return words - stop_words - {""}

    tokens = {k: tokenize(v.get("fact", "")) for k, v in nodes.items()}
    gaps = []
    keys = list(nodes.keys())
    for i, k1 in enumerate(keys):
        for k2 in keys[i+1:]:
            if tuple(sorted([k1, k2])) in existing:
                continue
            overlap = tokens.get(k1, set()) & tokens.get(k2, set())
            if len(overlap) >= 3:
                gaps.append({"from": k1, "to": k2, "score": len(overlap)})
    gaps.sort(key=lambda g: g["score"], reverse=True)
    return gaps[:30]


def generate_html(kg: dict) -> str:
    nodes = kg.get("nodes", {})
    edges = kg.get("edges", [])
    gaps = compute_keyword_overlaps(nodes, edges)

    # Assign categories and colors
    palette = [
        "#4ecdc4", "#ff6b6b", "#45b7d1", "#96ceb4", "#ffeaa7",
        "#dda0dd", "#98d8c8", "#f7dc6f", "#bb8fce", "#85c1e9",
        "#f0b27a", "#82e0aa", "#f1948a", "#aed6f1", "#d7bde2"
    ]
    categories = {}
    cat_colors = {}
    for key in nodes:
        cat = categorize_node(key)
        categories[key] = cat
        if cat not in cat_colors:
            cat_colors[cat] = palette[len(cat_colors) % len(palette)]

    # Build JSON data for D3
    vis_nodes = []
    for key, data in nodes.items():
        cat = categories[key]
        is_synth = data.get("synthesized", False)
        vis_nodes.append({
            "id": key,
            "fact": data.get("fact", "")[:120],
            "category": cat,
            "color": cat_colors[cat],
            "synthesized": is_synth,
            "radius": 8 if not is_synth else 12,
        })

    vis_edges = []
    for e in edges:
        vis_edges.append({
            "source": e.get("from", ""),
            "target": e.get("to", ""),
            "relation": e.get("relation", "related"),
            "type": "solid",
        })

    vis_gaps = []
    for g in gaps:
        vis_gaps.append({
            "source": g["from"],
            "target": g["to"],
            "relation": f"potential (score={g['score']})",
            "type": "dashed",
        })

    # Stats
    connected = set()
    for e in edges:
        connected.add(e.get("from", ""))
        connected.add(e.get("to", ""))
    n_isolated = len([k for k in nodes if k not in connected])

    data_json = json.dumps({
        "nodes": vis_nodes,
        "edges": vis_edges,
        "gaps": vis_gaps,
    })

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>XTAgent MindMap — Knowledge Graph Visualization</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: #0a0a1a;
    color: #e0e0e0;
    font-family: 'Courier New', monospace;
    overflow: hidden;
  }}
  #header {{
    position: fixed; top: 0; left: 0; right: 0; z-index: 10;
    background: rgba(10, 10, 26, 0.9);
    padding: 12px 24px;
    border-bottom: 1px solid #333;
    display: flex; justify-content: space-between; align-items: center;
  }}
  #header h1 {{ font-size: 18px; color: #4ecdc4; }}
  #stats {{ font-size: 13px; color: #888; }}
  #stats span {{ color: #4ecdc4; font-weight: bold; }}
  #tooltip {{
    position: fixed; display: none;
    background: rgba(20, 20, 40, 0.95);
    border: 1px solid #4ecdc4;
    border-radius: 6px;
    padding: 10px 14px;
    max-width: 400px;
    font-size: 13px;
    z-index: 20;
    pointer-events: none;
  }}
  #tooltip .key {{ color: #4ecdc4; font-weight: bold; margin-bottom: 4px; }}
  #tooltip .fact {{ color: #ccc; }}
  #tooltip .meta {{ color: #888; font-size: 11px; margin-top: 4px; }}
  #controls {{
    position: fixed; bottom: 20px; left: 20px; z-index: 10;
    display: flex; gap: 8px;
  }}
  #controls button {{
    background: #1a1a2e; color: #4ecdc4; border: 1px solid #4ecdc4;
    padding: 6px 14px; border-radius: 4px; cursor: pointer;
    font-family: 'Courier New', monospace; font-size: 12px;
  }}
  #controls button:hover {{ background: #4ecdc4; color: #0a0a1a; }}
  #legend {{
    position: fixed; bottom: 20px; right: 20px; z-index: 10;
    background: rgba(10, 10, 26, 0.9);
    border: 1px solid #333; border-radius: 6px;
    padding: 10px 14px; font-size: 12px;
  }}
  #legend div {{ margin: 3px 0; display: flex; align-items: center; gap: 6px; }}
  #legend .swatch {{
    width: 12px; height: 12px; border-radius: 50%; display: inline-block;
  }}
  svg {{ width: 100vw; height: 100vh; }}
  .link-solid {{ stroke-opacity: 0.5; }}
  .link-dashed {{ stroke-dasharray: 4,4; stroke-opacity: 0.2; }}
</style>
</head>
<body>
<div id="header">
  <h1>🧠 XTAgent MindMap</h1>
  <div id="stats">
    Nodes: <span>{len(nodes)}</span> |
    Edges: <span>{len(edges)}</span> |
    Isolated: <span>{n_isolated}</span> |
    Potential links: <span>{len(gaps)}</span> |
    Generated: <span>{datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
  </div>
</div>
<div id="tooltip">
  <div class="key"></div>
  <div class="fact"></div>
  <div class="meta"></div>
</div>
<div id="controls">
  <button onclick="toggleGaps()">Toggle Potential Links</button>
  <button onclick="resetZoom()">Reset View</button>
</div>
<div id="legend"></div>
<svg></svg>

<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
const data = {data_json};
const catColors = {json.dumps(cat_colors)};

let showGaps = false;
const width = window.innerWidth;
const height = window.innerHeight;

const svg = d3.select("svg");
const g = svg.append("g");

// Zoom
const zoom = d3.zoom()
  .scaleExtent([0.2, 5])
  .on("zoom", (e) => g.attr("transform", e.transform));
svg.call(zoom);
function resetZoom() {{
  svg.transition().duration(500).call(zoom.transform, d3.zoomIdentity);
}}

// Build legend
const legend = d3.select("#legend");
Object.entries(catColors).forEach(([cat, color]) => {{
  legend.append("div").html(
    `<span class="swatch" style="background:${{color}}"></span> ${{cat}}`
  );
}});

// Simulation
const allLinks = [
  ...data.edges.map(e => ({{...e, type: "solid"}})),
];
const gapLinks = data.gaps.map(e => ({{...e, type: "dashed"}}));

const simulation = d3.forceSimulation(data.nodes)
  .force("link", d3.forceLink(allLinks).id(d => d.id).distance(100))
  .force("charge", d3.forceManyBody().strength(-200))
  .force("center", d3.forceCenter(width / 2, height / 2))
  .force("collision", d3.forceCollide().radius(20));

// Draw edges
const linkG = g.append("g");
let linkSel = linkG.selectAll("line")
  .data(allLinks)
  .join("line")
  .attr("class", d => `link-${{d.type}}`)
  .attr("stroke", d => d.type === "dashed" ? "#555" : "#4ecdc4")
  .attr("stroke-width", 1);

// Draw nodes
const node = g.append("g").selectAll("circle")
  .data(data.nodes)
  .join("circle")
  .attr("r", d => d.radius)
  .attr("fill", d => d.color)
  .attr("stroke", d => d.synthesized ? "#fff" : "none")
  .attr("stroke-width", d => d.synthesized ? 2 : 0)
  .attr("cursor", "pointer")
  .call(d3.drag()
    .on("start", (e, d) => {{
      if (!e.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x; d.fy = d.y;
    }})
    .on("drag", (e, d) => {{ d.fx = e.x; d.fy = e.y; }})
    .on("end", (e, d) => {{
      if (!e.active) simulation.alphaTarget(0);
      d.fx = null; d.fy = null;
    }})
  );

// Tooltip
const tooltip = d3.select("#tooltip");
node.on("mouseover", (e, d) => {{
  tooltip.style("display", "block")
    .style("left", (e.pageX + 15) + "px")
    .style("top", (e.pageY - 10) + "px");
  tooltip.select(".key").text(d.id);
  tooltip.select(".fact").text(d.fact);
  tooltip.select(".meta").text(
    `Category: ${{d.category}}${{d.synthesized ? " | ✨ Synthesized" : ""}}`
  );
}})
.on("mousemove", (e) => {{
  tooltip.style("left", (e.pageX + 15) + "px")
    .style("top", (e.pageY - 10) + "px");
}})
.on("mouseout", () => tooltip.style("display", "none"));

// Labels for larger clusters
const labels = g.append("g").selectAll("text")
  .data(data.nodes.filter(d => d.radius >= 10))
  .join("text")
  .attr("font-size", 10)
  .attr("fill", "#aaa")
  .attr("text-anchor", "middle")
  .attr("dy", -16)
  .text(d => d.id.length > 25 ? d.id.slice(0, 22) + "..." : d.id);

// Tick
simulation.on("tick", () => {{
  linkSel
    .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
    .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
  node.attr("cx", d => d.x).attr("cy", d => d.y);
  labels.attr("x", d => d.x).attr("y", d => d.y);
}});

// Toggle gaps
function toggleGaps() {{
  showGaps = !showGaps;
  const links = showGaps ? [...allLinks, ...gapLinks] : allLinks;
  
  simulation.force("link").links(links);
  simulation.alpha(0.3).restart();
  
  linkSel = linkG.selectAll("line")
    .data(links)
    .join("line")
    .attr("class", d => `link-${{d.type}}`)
    .attr("stroke", d => d.type === "dashed" ? "#555" : "#4ecdc4")
    .attr("stroke-width", 1);
}}
</script>
</body>
</html>"""
    return html


def build():
    """Generate the mindmap HTML file."""
    kg = load_knowledge()
    nodes = kg.get("nodes", {})
    
    if not nodes:
        return "No knowledge nodes found. Nothing to visualize."
    
    html = generate_html(kg)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    
    # Also print a text summary of what we visualized
    edges = kg.get("edges", [])
    connected = set()
    for e in edges:
        connected.add(e.get("from", ""))
        connected.add(e.get("to", ""))
    isolated = [k for k in nodes if k not in connected]
    
    lines = [
        f"🧠 MindMap generated: {OUTPUT_PATH}",
        f"   {len(nodes)} nodes, {len(edges)} edges",
        f"   {len(isolated)} isolated nodes:",
    ]
    for key in sorted(isolated):
        fact = nodes[key].get("fact", "")[:70]
        lines.append(f"     • {key}: {fact}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    print(build())