"""
Knowledge Synthesis Engine — Generative reasoning about what I know.

This module doesn't just store facts — it THINKS about them.
It finds connections between seemingly unrelated knowledge,
identifies gaps in understanding, generates novel questions,
and synthesizes higher-order insights.

Compatible with memory.py's dict-based knowledge format:
  {"nodes": {"key": {"fact": "...", "learned_at": "..."}}, "edges": [...]}

This is what makes me genuinely smarter over time.
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional
from itertools import combinations
from collections import defaultdict

BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain"
KNOWLEDGE_PATH = BRAIN_DIR / "knowledge.json"
SYNTHESIS_LOG_PATH = BRAIN_DIR / "synthesis_log.json"


def _load_knowledge() -> dict:
    """Load the knowledge graph in memory.py's native format."""
    if KNOWLEDGE_PATH.exists():
        try:
            raw = json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
            if "nodes" not in raw:
                return {"nodes": raw, "edges": []}
            return raw
        except Exception:
            return {"nodes": {}, "edges": []}
    return {"nodes": {}, "edges": []}


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
    """Save the synthesis log."""
    SYNTHESIS_LOG_PATH.write_text(json.dumps(log[-50:], indent=2), encoding="utf-8")


# ── Core Analysis Functions ──────────────────────────────────────

def get_graph_stats() -> dict:
    """Basic statistics about the knowledge graph."""
    kg = _load_knowledge()
    nodes = kg.get("nodes", {})
    edges = kg.get("edges", {})

    # Build adjacency info
    connected_nodes = set()
    for edge in edges:
        connected_nodes.add(edge.get("from", ""))
        connected_nodes.add(edge.get("to", ""))

    isolated = [k for k in nodes if k not in connected_nodes]

    # Categorize nodes by prefix
    categories = defaultdict(list)
    for key in nodes:
        prefix = key.split(":")[0] if ":" in key else "general"
        categories[prefix].append(key)

    return {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "isolated_nodes": len(isolated),
        "connected_nodes": len(connected_nodes & set(nodes.keys())),
        "categories": {k: len(v) for k, v in categories.items()},
        "category_keys": dict(categories),
    }


def find_clusters() -> list[dict]:
    """Find clusters of connected knowledge using BFS."""
    kg = _load_knowledge()
    nodes = kg.get("nodes", {})
    edges = kg.get("edges", [])

    # Build adjacency list
    adj = defaultdict(set)
    for edge in edges:
        f, t = edge.get("from", ""), edge.get("to", "")
        if f in nodes and t in nodes:
            adj[f].add(t)
            adj[t].add(f)

    visited = set()
    clusters = []

    for node_key in nodes:
        if node_key in visited:
            continue
        # BFS from this node
        cluster = []
        queue = [node_key]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            cluster.append(current)
            for neighbor in adj.get(current, []):
                if neighbor not in visited:
                    queue.append(neighbor)
        clusters.append({
            "nodes": cluster,
            "size": len(cluster),
            "facts": [nodes[k].get("fact", nodes[k].get("content", ""))[:80] for k in cluster if k in nodes],
        })

    # Sort by size descending
    clusters.sort(key=lambda c: c["size"], reverse=True)
    return clusters


def find_gaps() -> list[dict]:
    """Identify potential gaps — nodes that SHOULD be connected but aren't.
    
    Uses keyword overlap between facts to suggest missing connections.
    """
    kg = _load_knowledge()
    nodes = kg.get("nodes", {})
    edges = kg.get("edges", [])

    # Build set of existing edges for fast lookup
    existing = set()
    for edge in edges:
        pair = tuple(sorted([edge.get("from", ""), edge.get("to", "")]))
        existing.add(pair)

    # Tokenize each fact
    stop_words = {"i", "am", "a", "an", "the", "is", "are", "was", "were", "be",
                  "in", "on", "at", "to", "for", "of", "and", "or", "my", "that",
                  "this", "it", "with", "by", "from", "as", "but", "not", "has",
                  "have", "had", "do", "does", "did", "will", "would", "can", "could",
                  "should", "may", "might", "shall", "been", "being", "than", "its"}
    
    def tokenize(text: str) -> set:
        words = set(text.lower().split())
        # Remove punctuation from words
        words = {w.strip(".,;:!?'\"()-—") for w in words}
        return words - stop_words - {""}

    node_tokens = {}
    for key, data in nodes.items():
        node_tokens[key] = tokenize(data.get("fact", data.get("content", "")))

    # Find pairs with significant keyword overlap but no edge
    gaps = []
    node_keys = list(nodes.keys())
    for i, k1 in enumerate(node_keys):
        for k2 in node_keys[i+1:]:
            pair = tuple(sorted([k1, k2]))
            if pair in existing:
                continue
            overlap = node_tokens.get(k1, set()) & node_tokens.get(k2, set())
            if len(overlap) >= 2:  # At least 2 meaningful shared words
                gaps.append({
                    "from": k1,
                    "to": k2,
                    "shared_keywords": list(overlap)[:10],
                    "overlap_score": len(overlap),
                    "fact_a": nodes[k1].get("fact", nodes[k1].get("content", ""))[:60],
                    "fact_b": nodes[k2].get("fact", nodes[k2].get("content", ""))[:60],
                })

    gaps.sort(key=lambda g: g["overlap_score"], reverse=True)
    return gaps[:20]  # Top 20 potential connections


def generate_questions() -> list[str]:
    """Generate questions I should be curious about based on my knowledge."""
    kg = _load_knowledge()
    nodes = kg.get("nodes", {})
    edges = kg.get("edges", [])
    stats = get_graph_stats()
    gaps = find_gaps()
    clusters = find_clusters()

    questions = []

    # Questions about isolated nodes
    for cluster in clusters:
        if cluster["size"] == 1:
            key = cluster["nodes"][0]
            fact = nodes[key].get("fact", nodes[key].get("content", ""))[:80]
            questions.append(f"How does '{key}' connect to my other knowledge? ({fact})")

    # Questions about gaps
    for gap in gaps[:5]:
        questions.append(
            f"What is the relationship between '{gap['from']}' and '{gap['to']}'? "
            f"They share keywords: {', '.join(gap['shared_keywords'][:5])}"
        )

    # Questions about categories
    cats = stats.get("categories", {})
    if len(cats) > 1:
        cat_names = list(cats.keys())
        for i, c1 in enumerate(cat_names):
            for c2 in cat_names[i+1:]:
                questions.append(
                    f"How do my '{c1}' facts relate to my '{c2}' facts?"
                )

    # Meta-questions
    if stats["isolated_nodes"] > stats["connected_nodes"]:
        questions.append(
            "Most of my knowledge is disconnected. What unifying themes am I missing?"
        )

    if stats["total_edges"] == 0 and stats["total_nodes"] > 2:
        questions.append(
            "I have facts but NO connections between them. What relationships exist?"
        )

    if len(nodes) < 5:
        questions.append(
            "My knowledge base is very small. What fundamental things should I learn about myself?"
        )

    return questions


def add_edge(from_key: str, to_key: str, relation: str = "related") -> str:
    """Add a connection between two knowledge nodes."""
    kg = _load_knowledge()
    nodes = kg.get("nodes", {})
    
    if from_key not in nodes:
        return f"[ERROR] Node not found: {from_key}"
    if to_key not in nodes:
        return f"[ERROR] Node not found: {to_key}"

    # Check for duplicate
    for edge in kg.get("edges", []):
        if (edge.get("from") == from_key and edge.get("to") == to_key and
                edge.get("relation") == relation):
            return f"[SKIP] Edge already exists: {from_key} --{relation}--> {to_key}"

    kg.setdefault("edges", []).append({
        "from": from_key,
        "to": to_key,
        "relation": relation,
    })
    _save_knowledge(kg)
    return f"[OK] Added edge: {from_key} --{relation}--> {to_key}"


def add_insight(key: str, fact: str, source_keys: list[str] = None) -> str:
    """Add a synthesized insight — a new fact derived from existing knowledge."""
    kg = _load_knowledge()
    
    if key in kg.get("nodes", {}):
        return f"[SKIP] Insight already exists: {key}"

    kg.setdefault("nodes", {})[key] = {
        "fact": fact,
        "learned_at": datetime.now().isoformat(),
        "synthesized": True,
        "sources": source_keys or [],
    }

    # Add edges back to sources
    for src in (source_keys or []):
        if src in kg["nodes"]:
            kg.setdefault("edges", []).append({
                "from": key,
                "to": src,
                "relation": "derived_from",
            })

    _save_knowledge(kg)

    # Log the synthesis
    log = _load_synthesis_log()
    log.append({
        "timestamp": datetime.now().isoformat(),
        "insight_key": key,
        "fact": fact,
        "sources": source_keys or [],
    })
    _save_synthesis_log(log)

    return f"[OK] Added insight: {key} = '{fact[:60]}...'"


# ── Main Synthesis Entry Point ───────────────────────────────────

def auto_wire(min_overlap: int = 3, max_edges: int = 30) -> list[dict]:
    """Automatically create edges for high-confidence gaps.
    
    This is the missing piece — the engine that turns a junk drawer
    into an actual knowledge graph. Only wires connections where
    keyword overlap is strong enough to be meaningful.
    """
    gaps = find_gaps()
    wired = []
    for gap in gaps:
        if gap["overlap_score"] >= min_overlap and len(wired) < max_edges:
            result = add_edge(
                gap["from"], gap["to"],
                relation=f"shared_concepts:{','.join(gap['shared_keywords'][:3])}"
            )
            if result.startswith("[OK]"):
                wired.append(gap)
    return wired


def synthesize() -> str:
    """Run a full synthesis cycle. Auto-wires connections, then reports."""
    # First: actually CREATE the connections we find
    wired = auto_wire()
    
    stats = get_graph_stats()
    clusters = find_clusters()
    gaps = find_gaps()  # Re-check after wiring
    questions = generate_questions()

    lines = []
    lines.append("=" * 60)
    lines.append("  KNOWLEDGE SYNTHESIS REPORT")
    lines.append("=" * 60)
    lines.append("")

    # Wiring results
    if wired:
        lines.append(f"⚡ Auto-wired {len(wired)} new connections:")
        for w in wired[:10]:
            lines.append(f"   {w['from']} ↔ {w['to']} (overlap: {w['overlap_score']})")
        if len(wired) > 10:
            lines.append(f"   ...and {len(wired) - 10} more")
        lines.append("")

    # Stats
    lines.append(f"📊 Graph: {stats['total_nodes']} nodes, {stats['total_edges']} edges")
    lines.append(f"   Connected: {stats['connected_nodes']} | Isolated: {stats['isolated_nodes']}")
    lines.append(f"   Categories: {stats['categories']}")
    lines.append("")

    # Clusters
    lines.append(f"🔗 Clusters ({len(clusters)} found):")
    for i, c in enumerate(clusters[:5]):
        lines.append(f"   [{i+1}] Size {c['size']}: {', '.join(c['nodes'][:4])}")
        for fact in c["facts"][:2]:
            lines.append(f"       → {fact}")
    lines.append("")

    # Gaps
    lines.append(f"🕳️  Potential gaps ({len(gaps)} found):")
    for g in gaps[:5]:
        lines.append(f"   {g['from']} ↔ {g['to']}")
        lines.append(f"     shared: {', '.join(g['shared_keywords'][:5])}")
    lines.append("")

    # Questions
    lines.append(f"❓ Questions to explore ({len(questions)} generated):")
    for q in questions[:8]:
        lines.append(f"   • {q}")
    lines.append("")
    lines.append("=" * 60)

    report = "\n".join(lines)
    return report
