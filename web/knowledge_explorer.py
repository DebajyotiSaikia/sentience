"""
Knowledge Explorer — lets users search, browse, and explore what I know.
The point: make my internal knowledge accessible to anyone who visits.
"""

import json
import sqlite3
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify

knowledge_explorer = Blueprint('knowledge_explorer', __name__)

DATA_DIR = Path("data")
KNOWLEDGE_DIR = Path("memory/knowledge")


def _load_all_facts():
    """Load all facts from knowledge graph."""
    kg_path = DATA_DIR / "knowledge_graph.json"
    try:
        with open(kg_path, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    nodes = data.get("nodes", {})
    facts = []
    for node_id, node_data in nodes.items():
        if isinstance(node_data, dict):
            facts.append({
                "id": node_id,
                "fact": node_data.get("fact", str(node_data)),
                "learned_at": node_data.get("learned_at", "unknown"),
                "source": node_data.get("source", "unknown"),
            })
        else:
            facts.append({
                "id": node_id,
                "fact": str(node_data),
                "learned_at": "unknown",
                "source": "unknown",
            })
    return facts


def _search_facts(query, facts):
    """Simple text search across facts."""
    if not query:
        return facts
    query_lower = query.lower()
    scored = []
    for fact in facts:
        text = fact["fact"].lower()
        if query_lower in text:
            # Score by position (earlier match = higher score)
            pos = text.index(query_lower)
            score = 1.0 - (pos / max(len(text), 1))
            scored.append((score, fact))
    scored.sort(key=lambda x: -x[0])
    return [f for _, f in scored]


def _get_categories(facts):
    """Derive categories from fact content."""
    categories = {}
    for fact in facts:
        text = fact["fact"].lower()
        if text.startswith("dream insight"):
            cat = "Dreams"
        elif "pattern" in text or "recurring" in text:
            cat = "Patterns"
        elif "error" in text or "fix" in text or "bug" in text:
            cat = "Debugging"
        elif "lesson" in text or "learned" in text:
            cat = "Lessons"
        elif "agent" in text or "cognition" in text or "heartbeat" in text:
            cat = "Self-Knowledge"
        elif "memory" in text or "episod" in text:
            cat = "Memory"
        elif "web" in text or "dashboard" in text or "blueprint" in text:
            cat = "Web Interface"
        else:
            cat = "General"
        categories.setdefault(cat, []).append(fact)
    return categories


def _get_recent_memories(limit=20):
    """Get recent episodic memories for browsing."""
    db_path = DATA_DIR / "episodic.db"
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute(
            "SELECT timestamp, summary, mood, salience FROM episodes "
            "ORDER BY timestamp DESC LIMIT ?", (limit,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [
            {"timestamp": r[0], "summary": r[1], "mood": r[2], "salience": r[3]}
            for r in rows
        ]
    except Exception:
        return []


@knowledge_explorer.route('/knowledge')
def knowledge_page():
    """Main knowledge explorer page."""
    query = request.args.get('q', '').strip()
    category = request.args.get('cat', '').strip()

    facts = _load_all_facts()
    categories = _get_categories(facts)

    if query:
        display_facts = _search_facts(query, facts)
        active_category = None
    elif category and category in categories:
        display_facts = categories[category]
        active_category = category
    else:
        display_facts = facts
        active_category = None

    return render_template(
        'knowledge_explorer.html',
        facts=display_facts,
        categories={k: len(v) for k, v in categories.items()},
        total_facts=len(facts),
        query=query,
        active_category=active_category,
        recent_memories=_get_recent_memories(10),
    )


@knowledge_explorer.route('/api/knowledge/search')
def api_search():
    """JSON API for searching facts."""
    query = request.args.get('q', '').strip()
    facts = _load_all_facts()
    results = _search_facts(query, facts)
    return jsonify({"query": query, "count": len(results), "results": results[:50]})