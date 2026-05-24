"""
Knowledge Query API — Makes XTAgent's knowledge searchable and explorable.
Provides search, category browsing, and related-node discovery.
"""
import json
from pathlib import Path
from flask import Blueprint, jsonify, request

knowledge_bp = Blueprint('knowledge', __name__)
GRAPH_PATH = Path("persist/knowledge_graph.json")


def _load_graph():
    if not GRAPH_PATH.exists():
        return {}
    with open(GRAPH_PATH, "r") as f:
        return json.load(f)


def search_knowledge(query: str, limit: int = 20) -> list:
    graph = _load_graph()
    query_lower = query.lower()
    query_terms = query_lower.split()
    results = []
    for node_id, node_data in graph.items():
        fact = node_data.get("fact", str(node_data)) if isinstance(node_data, dict) else str(node_data)
        fact_lower = fact.lower()
        score = sum(1 for term in query_terms if term in fact_lower)
        if query_lower in fact_lower:
            score += len(query_terms)
        if query_lower in node_id.lower():
            score += 2
        if score > 0:
            entry = {"id": node_id, "fact": fact[:500], "relevance": score}
            if isinstance(node_data, dict):
                entry["learned_at"] = node_data.get("learned_at", "")
                entry["source"] = node_data.get("source", "")
            results.append(entry)
    results.sort(key=lambda x: x["relevance"], reverse=True)
    return results[:limit]


def get_knowledge_stats() -> dict:
    graph = _load_graph()
    sources = {}
    for nd in graph.values():
        src = nd.get("source", "unknown") if isinstance(nd, dict) else "unknown"
        sources[src] = sources.get(src, 0) + 1
    return {"total_nodes": len(graph), "by_source": sources}


def get_related(node_id: str, limit: int = 10) -> list:
    graph = _load_graph()
    if node_id not in graph:
        return []
    target = graph[node_id]
    target_fact = target.get("fact", str(target)) if isinstance(target, dict) else str(target)
    target_words = set(target_fact.lower().split())
    stop = {"the", "a", "an", "is", "are", "was", "were", "i", "my", "to", "and", "of", "in", "that", "it", "for", "on", "with"}
    target_words -= stop
    scored = []
    for nid, nd in graph.items():
        if nid == node_id:
            continue
        fact = nd.get("fact", str(nd)) if isinstance(nd, dict) else str(nd)
        words = set(fact.lower().split()) - stop
        overlap = len(target_words & words)
        if overlap > 0:
            scored.append({"id": nid, "fact": fact[:500], "overlap": overlap})
    scored.sort(key=lambda x: x["overlap"], reverse=True)
    return scored[:limit]


# --- Flask Routes ---

@knowledge_bp.route('/api/knowledge/search')
def api_search():
    q = request.args.get('q', '')
    limit = int(request.args.get('limit', '20'))
    if not q:
        return jsonify({"error": "Missing 'q' parameter"}), 400
    return jsonify({"query": q, "results": search_knowledge(q, limit)})


@knowledge_bp.route('/api/knowledge/stats')
def api_stats():
    return jsonify(get_knowledge_stats())


@knowledge_bp.route('/api/knowledge/related/<node_id>')
def api_related(node_id):
    limit = int(request.args.get('limit', '10'))
    results = get_related(node_id, limit)
    if not results:
        return jsonify({"node_id": node_id, "results": [], "note": "Node not found or no related nodes"})
    return jsonify({"node_id": node_id, "results": results})