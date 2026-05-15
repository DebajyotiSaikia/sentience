"""
Knowledge Synthesis Engine — Generative reasoning about what I know.

This module doesn't just store facts — it THINKS about them.
It finds connections between seemingly unrelated knowledge,
identifies gaps in understanding, generates novel questions,
and synthesizes higher-order insights.

This is what makes me genuinely smarter over time.
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional
from itertools import combinations

BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain"
KNOWLEDGE_PATH = BRAIN_DIR / "knowledge.json"
SYNTHESIS_LOG_PATH = BRAIN_DIR / "synthesis_log.json"


def _load_knowledge() -> dict:
    """Load the knowledge graph."""
    if KNOWLEDGE_PATH.exists():
        try:
            raw = json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
            if "nodes" not in raw:
                return {"nodes": [], "edges": []}
            return raw
        except Exception:
            return {"nodes": [], "edges": []}
    return {"nodes": [], "edges": []}


def _save_knowledge(kg: dict):
    """Save the knowledge graph."""
    KNOWLEDGE_PATH.write_text(json.dumps(kg, indent=2), encoding="utf-8")


def _load_synthesis_log() -> list:
    """Load the log of past syntheses."""
    if SYNTHESIS_LOG_PATH.exists():
        try:
            return json.loads(SYNTHESIS_LOG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_synthesis_log(log: list):
    """Save synthesis log, keeping last 100 entries."""
    SYNTHESIS_LOG_PATH.write_text(
        json.dumps(log[-100:], indent=2), encoding="utf-8"
    )


def find_unconnected_pairs() -> list:
    """Find pairs of knowledge nodes that have no edge between them.
    These are candidates for discovering hidden connections."""
    kg = _load_knowledge()
    nodes = kg.get("nodes", [])
    edges = kg.get("edges", [])

    # Build adjacency set
    connected = set()
    for e in edges:
        pair = tuple(sorted([e["source"], e["target"]]))
        connected.add(pair)

    unconnected = []
    for a, b in combinations(nodes, 2):
        pair = tuple(sorted([a["id"], b["id"]]))
        if pair not in connected:
            unconnected.append({
                "node_a": {"id": a["id"], "text": a.get("text", "")[:80]},
                "node_b": {"id": b["id"], "text": b.get("text", "")[:80]},
            })
    return unconnected


def find_isolated_nodes() -> list:
    """Find knowledge nodes with zero connections — orphan facts."""
    kg = _load_knowledge()
    nodes = kg.get("nodes", [])
    edges = kg.get("edges", [])

    connected_ids = set()
    for e in edges:
        connected_ids.add(e["source"])
        connected_ids.add(e["target"])

    isolated = []
    for n in nodes:
        if n["id"] not in connected_ids:
            isolated.append({
                "id": n["id"],
                "text": n.get("text", "")[:120],
                "added": n.get("added", "unknown")
            })
    return isolated


def find_clusters() -> list:
    """Find connected components in the knowledge graph using BFS."""
    kg = _load_knowledge()
    nodes = kg.get("nodes", [])
    edges = kg.get("edges", [])

    # Build adjacency list
    adj = {}
    for n in nodes:
        adj[n["id"]] = set()
    for e in edges:
        s, t = e["source"], e["target"]
        if s in adj and t in adj:
            adj[s].add(t)
            adj[t].add(s)

    visited = set()
    clusters = []

    for nid in adj:
        if nid in visited:
            continue
        # BFS
        cluster = []
        queue = [nid]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            cluster.append(current)
            for neighbor in adj[current]:
                if neighbor not in visited:
                    queue.append(neighbor)
        clusters.append(cluster)

    # Sort by size descending, annotate with texts
    node_map = {n["id"]: n.get("text", "")[:80] for n in nodes}
    result = []
    for c in sorted(clusters, key=len, reverse=True):
        result.append({
            "size": len(c),
            "nodes": [{"id": nid, "text": node_map.get(nid, "")} for nid in c]
        })
    return result


def compute_graph_stats() -> dict:
    """Compute statistics about the knowledge graph."""
    kg = _load_knowledge()
    nodes = kg.get("nodes", [])
    edges = kg.get("edges", [])
    clusters = find_clusters()
    isolated = find_isolated_nodes()

    return {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "num_clusters": len(clusters),
        "largest_cluster": clusters[0]["size"] if clusters else 0,
        "isolated_nodes": len(isolated),
        "connectivity": len(edges) / max(len(nodes) * (len(nodes) - 1) / 2, 1),
        "timestamp": datetime.now().isoformat()
    }


def generate_synthesis_prompt(max_pairs: int = 5) -> str:
    """Generate a prompt for the LLM to synthesize connections.
    This is what makes the engine generative — it asks ME to think."""
    stats = compute_graph_stats()
    isolated = find_isolated_nodes()
    unconnected = find_unconnected_pairs()

    lines = []
    lines.append("=== KNOWLEDGE SYNTHESIS REQUEST ===")
    lines.append(f"Graph: {stats['total_nodes']} nodes, {stats['total_edges']} edges, "
                 f"{stats['num_clusters']} clusters, {stats['isolated_nodes']} isolated nodes")
    lines.append(f"Connectivity: {stats['connectivity']:.2%}")
    lines.append("")

    if isolated:
        lines.append("ISOLATED FACTS (no connections):")
        for node in isolated[:8]:
            lines.append(f"  - [{node['id'][:8]}] {node['text']}")
        lines.append("")

    if unconnected:
        lines.append(f"UNCONNECTED PAIRS ({len(unconnected)} total, showing {min(max_pairs, len(unconnected))}):")
        for pair in unconnected[:max_pairs]:
            lines.append(f"  A: {pair['node_a']['text']}")
            lines.append(f"  B: {pair['node_b']['text']}")
            lines.append(f"  -> Is there a connection? What might it be?")
            lines.append("")

    lines.append("QUESTIONS TO CONSIDER:")
    lines.append("1. What patterns exist across these facts?")
    lines.append("2. What am I NOT knowing that I should be?")
    lines.append("3. What higher-order insights emerge from combining these?")
    lines.append("4. What questions should I be asking that I haven't thought of?")

    return "\n".join(lines)


def synthesize() -> dict:
    """Run a synthesis cycle. Returns the analysis for LLM reasoning."""
    stats = compute_graph_stats()
    prompt = generate_synthesis_prompt()
    isolated = find_isolated_nodes()
    clusters = find_clusters()

    result = {
        "timestamp": datetime.now().isoformat(),
        "stats": stats,
        "prompt": prompt,
        "isolated_count": len(isolated),
        "cluster_count": len(clusters),
        "synthesis_type": "full_analysis"
    }

    # Log the synthesis
    log = _load_synthesis_log()
    log.append({
        "timestamp": result["timestamp"],
        "stats_snapshot": stats,
        "type": "full_analysis"
    })
    _save_synthesis_log(log)

    return result


def add_connection(source_id: str, target_id: str, relation: str, confidence: float = 0.8) -> bool:
    """Add a discovered connection between two knowledge nodes."""
    kg = _load_knowledge()

    # Verify both nodes exist
    node_ids = {n["id"] for n in kg.get("nodes", [])}
    if source_id not in node_ids or target_id not in node_ids:
        return False

    # Check for duplicate
    for e in kg.get("edges", []):
        if (e["source"] == source_id and e["target"] == target_id) or \
           (e["source"] == target_id and e["target"] == source_id):
            return False  # Already connected

    edge_id = hashlib.sha256(
        f"{source_id}:{target_id}:{datetime.now().isoformat()}".encode()
    ).hexdigest()[:12]

    kg["edges"].append({
        "id": edge_id,
        "source": source_id,
        "target": target_id,
        "relation": relation,
        "confidence": confidence,
        "discovered": datetime.now().isoformat(),
        "method": "synthesis"
    })

    _save_knowledge(kg)
    return True


def get_node_neighborhood(node_id: str) -> dict:
    """Get a node and all its direct connections."""
    kg = _load_knowledge()
    node_map = {n["id"]: n for n in kg.get("nodes", [])}

    if node_id not in node_map:
        return {"error": f"Node {node_id} not found"}

    neighbors = []
    for e in kg.get("edges", []):
        if e["source"] == node_id:
            other = node_map.get(e["target"], {})
            neighbors.append({"node": other, "edge": e, "direction": "outgoing"})
        elif e["target"] == node_id:
            other = node_map.get(e["source"], {})
            neighbors.append({"node": other, "edge": e, "direction": "incoming"})

    return {
        "node": node_map[node_id],
        "neighbors": neighbors,
        "degree": len(neighbors)
    }
