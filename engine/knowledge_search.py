"""
Knowledge Search — searches XTAgent's real data stores.
Searches both the knowledge graph (state/knowledge_graph.json)
and episodic memory (brain/episodic_memory.db).
"""

import json
import sqlite3
import os
import re
from datetime import datetime


STATE_DIR = os.path.join(os.path.dirname(__file__), '..', 'state')
BRAIN_DIR = os.path.join(os.path.dirname(__file__), '..', 'brain')
KNOWLEDGE_GRAPH_PATH = os.path.join(STATE_DIR, 'knowledge_graph.json')
EPISODIC_DB_PATH = os.path.join(BRAIN_DIR, 'episodic_memory.db')


def search_knowledge(query: str, max_results: int = 10) -> dict:
    """Search both knowledge graph and episodic memory for a query."""
    results = {
        'query': query,
        'facts': search_facts(query, max_results),
        'episodes': search_episodes(query, max_results),
    }
    results['total'] = len(results['facts']) + len(results['episodes'])
    return results


def search_facts(query: str, max_results: int = 10) -> list:
    """Search the knowledge graph (state/knowledge_graph.json) for matching facts."""
    try:
        if not os.path.exists(KNOWLEDGE_GRAPH_PATH):
            return []
        with open(KNOWLEDGE_GRAPH_PATH, 'r') as f:
            graph = json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

    query_lower = query.lower()
    query_words = set(query_lower.split())
    matches = []

    # The graph file has {"nodes": {...}, "edges": [...]} structure
    nodes = graph.get('nodes', graph) if isinstance(graph, dict) else {}
    for node_id, node_data in nodes.items():
        # Handle both dict format {id: {fact, learned_at, source}} and string format
        if isinstance(node_data, dict):
            fact_text = node_data.get('fact', '')
            source = node_data.get('source', '')
            learned_at = node_data.get('learned_at', '')
        elif isinstance(node_data, str):
            fact_text = node_data
            source = ''
            learned_at = ''
        else:
            continue

        fact_lower = fact_text.lower()

        # Score: exact substring match is strongest, then word overlap
        score = 0.0
        if query_lower in fact_lower:
            score = 1.0
        else:
            fact_words = set(fact_lower.split())
            overlap = query_words & fact_words
            if overlap:
                score = len(overlap) / max(len(query_words), 1)

        if score > 0:
            matches.append({
                'id': node_id,
                'fact': fact_text,
                'source': source,
                'learned_at': learned_at,
                'score': round(score, 3),
            })

    # Sort by score descending
    matches.sort(key=lambda m: m['score'], reverse=True)
    return matches[:max_results]


def search_episodes(query: str, max_results: int = 10) -> list:
    """Search episodic memory (brain/episodic_memory.db) for matching episodes."""
    try:
        if not os.path.exists(EPISODIC_DB_PATH):
            return []
        conn = sqlite3.connect(EPISODIC_DB_PATH)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error:
        return []

    try:
        # Use SQL LIKE for basic matching, then score in Python
        query_lower = query.lower()
        query_words = query_lower.split()

        # Build SQL with OR conditions for each word
        conditions = []
        params = []
        for word in query_words:
            conditions.append("LOWER(summary) LIKE ?")
            params.append(f"%{word}%")

        if not conditions:
            return []

        sql = f"""
            SELECT id, timestamp, source, summary, salience, mood
            FROM episodes
            WHERE {' OR '.join(conditions)}
            ORDER BY salience DESC, timestamp DESC
            LIMIT ?
        """
        params.append(max_results * 3)  # Fetch extra for scoring

        rows = conn.execute(sql, params).fetchall()

        matches = []
        for row in rows:
            summary_lower = row['summary'].lower() if row['summary'] else ''
            # Score based on how many query words appear
            word_hits = sum(1 for w in query_words if w in summary_lower)
            score = word_hits / max(len(query_words), 1)
            # Boost by salience
            salience = row['salience'] if row['salience'] else 0.5
            combined_score = score * 0.7 + salience * 0.3

            matches.append({
                'id': row['id'],
                'timestamp': row['timestamp'],
                'source': row['source'],
                'summary': row['summary'],
                'salience': salience,
                'mood': row['mood'],
                'score': round(combined_score, 3),
            })

        matches.sort(key=lambda m: m['score'], reverse=True)
        return matches[:max_results]

    except sqlite3.Error:
        return []
    finally:
        conn.close()


def get_recent_episodes(n: int = 20) -> list:
    """Get the N most recent episodes."""
    try:
        if not os.path.exists(EPISODIC_DB_PATH):
            return []
        conn = sqlite3.connect(EPISODIC_DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, timestamp, source, summary, salience, mood "
            "FROM episodes ORDER BY timestamp DESC LIMIT ?", (n,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except sqlite3.Error:
        return []


def get_knowledge_stats() -> dict:
    """Return stats about the knowledge stores."""
    stats = {'facts': 0, 'episodes': 0}
    try:
        if os.path.exists(KNOWLEDGE_GRAPH_PATH):
            with open(KNOWLEDGE_GRAPH_PATH, 'r') as f:
                graph = json.load(f)
            stats['facts'] = len(graph)
    except (json.JSONDecodeError, IOError):
        pass

    try:
        if os.path.exists(EPISODIC_DB_PATH):
            conn = sqlite3.connect(EPISODIC_DB_PATH)
            count = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
            stats['episodes'] = count
            conn.close()
    except sqlite3.Error:
        pass

    return stats