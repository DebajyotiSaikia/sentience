"""
Knowledge Query API — Blueprint for searching what I know.
"""
from flask import Blueprint, request, jsonify
from web.knowledge_query import search_facts, search_memories, get_graph_neighbors, query_all

knowledge_bp = Blueprint("knowledge", __name__)


@knowledge_bp.route("/api/knowledge/search")
def knowledge_search():
    """Search across facts, memories, and graph for a query string."""
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "No query provided", "results": {}})

    max_results = request.args.get("max", 10, type=int)
    max_results = min(max_results, 50)  # cap

    results = query_all(q, max_results=max_results)
    return jsonify({"query": q, "results": results})


@knowledge_bp.route("/api/knowledge/facts")
def knowledge_facts_search():
    """Search only facts."""
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "No query provided", "facts": []})
    facts = search_facts(q, max_results=20)
    return jsonify({"query": q, "facts": facts})


@knowledge_bp.route("/api/knowledge/memories")
def knowledge_memories_search():
    """Search only memories."""
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "No query provided", "memories": []})
    memories = search_memories(q, max_results=20)
    return jsonify({"query": q, "memories": memories})


@knowledge_bp.route("/api/knowledge/neighbors")
def knowledge_neighbors():
    """Get graph neighbors for a fact ID."""
    fact_id = request.args.get("id", "").strip()
    if not fact_id:
        return jsonify({"error": "No fact ID provided", "neighbors": []})
    neighbors = get_graph_neighbors(fact_id)
    return jsonify({"fact_id": fact_id, "neighbors": neighbors})