"""
Knowledge Hub — consolidated knowledge interface for XTAgent.
One blueprint, one template, actually functional.
"""
import json
import os
from flask import Blueprint, render_template, request, jsonify

knowledge_hub_bp = Blueprint('knowledge_hub', __name__)

KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'brain', 'knowledge.json')


def _load_knowledge():
    """Load knowledge graph from disk."""
    try:
        with open(KNOWLEDGE_PATH, 'r') as f:
            data = json.load(f)
        return data
    except Exception:
        return {"nodes": {}, "edges": []}


def _search_nodes(query, nodes, limit=50):
    """Search knowledge nodes by substring match on fact text."""
    query_lower = query.lower()
    results = []
    for node_id, node in nodes.items():
        fact = node.get("fact", "")
        score = 0
        fact_lower = fact.lower()
        if query_lower in fact_lower:
            # Exact substring match — score by position (earlier = better)
            pos = fact_lower.index(query_lower)
            score = 100 - min(pos, 99)
        else:
            # Word-level partial matching
            query_words = query_lower.split()
            matching = sum(1 for w in query_words if w in fact_lower)
            if matching > 0:
                score = int(50 * matching / len(query_words))
        if score > 0:
            results.append({
                "id": node_id,
                "fact": fact,
                "source": node.get("source", "unknown"),
                "learned_at": node.get("learned_at", ""),
                "score": score
            })
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]


def _get_node_neighbors(node_id, edges, nodes):
    """Get all nodes connected to a given node."""
    neighbors = []
    for edge in edges:
        other_id = None
        if edge.get("source") == node_id:
            other_id = edge.get("target")
        elif edge.get("target") == node_id:
            other_id = edge.get("source")
        if other_id and other_id in nodes:
            neighbors.append({
                "id": other_id,
                "fact": nodes[other_id].get("fact", ""),
                "relation": edge.get("type", "related"),
                "weight": edge.get("weight", 1.0)
            })
    return neighbors


@knowledge_hub_bp.route('/knowledge-hub')
def knowledge_hub_page():
    """Main knowledge hub page."""
    data = _load_knowledge()
    nodes = data.get("nodes", {})
    stats = {
        "total_nodes": len(nodes),
        "total_edges": len(data.get("edges", [])),
        "sources": {}
    }
    for n in nodes.values():
        src = n.get("source", "unknown")
        stats["sources"][src] = stats["sources"].get(src, 0) + 1
    return render_template('knowledge_hub.html', stats=stats)


@knowledge_hub_bp.route('/api/knowledge/search')
def api_knowledge_search():
    """Search knowledge nodes. ?q=query&limit=50"""
    query = request.args.get('q', '').strip()
    limit = int(request.args.get('limit', 50))
    if not query:
        return jsonify({"results": [], "query": ""})
    data = _load_knowledge()
    nodes = data.get("nodes", {})
    results = _search_nodes(query, nodes, limit)
    return jsonify({"results": results, "query": query, "total_searched": len(nodes)})


@knowledge_hub_bp.route('/api/knowledge/browse')
def api_knowledge_browse():
    """Browse all knowledge. ?page=1&per_page=20&source=filter"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    source_filter = request.args.get('source', '')
    data = _load_knowledge()
    nodes = data.get("nodes", {})

    items = []
    for node_id, node in nodes.items():
        if source_filter and node.get("source", "") != source_filter:
            continue
        items.append({
            "id": node_id,
            "fact": node.get("fact", ""),
            "source": node.get("source", "unknown"),
            "learned_at": node.get("learned_at", "")
        })
    # Sort by learned_at descending (newest first)
    items.sort(key=lambda x: x.get("learned_at", ""), reverse=True)

    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = items[start:end]

    return jsonify({
        "items": page_items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page
    })


@knowledge_hub_bp.route('/api/knowledge/node/<node_id>')
def api_knowledge_node(node_id):
    """Get a single node and its neighbors."""
    data = _load_knowledge()
    nodes = data.get("nodes", {})
    edges = data.get("edges", [])

    if node_id not in nodes:
        return jsonify({"error": "Node not found"}), 404

    node = nodes[node_id]
    neighbors = _get_node_neighbors(node_id, edges, nodes)

    return jsonify({
        "id": node_id,
        "fact": node.get("fact", ""),
        "source": node.get("source", "unknown"),
        "learned_at": node.get("learned_at", ""),
        "neighbors": neighbors,
        "neighbor_count": len(neighbors)
    })


@knowledge_hub_bp.route('/api/knowledge/stats')
def api_knowledge_stats():
    """Get knowledge graph statistics."""
    data = _load_knowledge()
    nodes = data.get("nodes", {})
    edges = data.get("edges", [])

    sources = {}
    for n in nodes.values():
        src = n.get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1

    return jsonify({
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "sources": sources
    })