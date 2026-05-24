"""
Knowledge Query Engine — lets users search what I know.
Searches facts, finds related memories, surfaces graph connections.
"""
import json
import os
import re
from collections import defaultdict

BRAIN_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "brain")
KNOWLEDGE_FILE = os.path.join(BRAIN_DIR, "knowledge.json")
MEMORIES_FILE = os.path.join(BRAIN_DIR, "memories.json")
GRAPH_FILE = os.path.join(BRAIN_DIR, "knowledge_graph.json")


def _load_json(path):
    """Safely load a JSON file, returning empty structure on failure."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _tokenize(text):
    """Simple word tokenization for matching."""
    return set(re.findall(r'\w+', text.lower()))


def _relevance_score(query_tokens, text):
    """Score how relevant a text is to query tokens."""
    if not text or not query_tokens:
        return 0.0
    text_tokens = _tokenize(text)
    if not text_tokens:
        return 0.0
    matches = query_tokens & text_tokens
    # Weighted: fraction of query words found, boosted by exact phrase overlap
    return len(matches) / len(query_tokens)


def search_facts(query, max_results=20):
    """Search knowledge facts for relevance to query."""
    knowledge = _load_json(KNOWLEDGE_FILE)
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    results = []
    # knowledge.json may be {'nodes': {id: {fact, ...}}, 'edges': [...]}
    # or flat {id: {fact, ...}} or list
    if isinstance(knowledge, dict) and 'nodes' in knowledge:
        items = knowledge['nodes'].values()
    elif isinstance(knowledge, dict):
        items = knowledge.values()
    elif isinstance(knowledge, list):
        items = knowledge
    else:
        items = []

    for item in items:
        if isinstance(item, dict):
            fact_text = item.get("fact", "")
        elif isinstance(item, str):
            fact_text = item
        else:
            continue
        score = _relevance_score(query_tokens, fact_text)
        if score > 0.0:
            results.append({
                "type": "fact",
                "text": fact_text,
                "score": round(score, 3),
                "source": item.get("source", "unknown") if isinstance(item, dict) else "unknown",
                "learned_at": item.get("learned_at", "") if isinstance(item, dict) else "",
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:max_results]


def search_memories(query, max_results=15):
    """Search episodic memories for relevance to query."""
    memories = _load_json(MEMORIES_FILE)
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    results = []
    mem_list = memories if isinstance(memories, list) else memories.get("memories", [])

    for mem in mem_list:
        if isinstance(mem, dict):
            text = mem.get("content", mem.get("text", mem.get("summary", "")))
            timestamp = mem.get("timestamp", mem.get("time", ""))
            salience = mem.get("salience", 0.5)
            mood = mem.get("mood", "")
        elif isinstance(mem, str):
            text = mem
            timestamp = ""
            salience = 0.5
            mood = ""
        else:
            continue

        score = _relevance_score(query_tokens, text)
        if score > 0.0:
            # Boost by salience — more important memories rank higher
            boosted = score * (0.5 + 0.5 * float(salience))
            results.append({
                "type": "memory",
                "text": text[:300],  # Truncate for display
                "score": round(boosted, 3),
                "timestamp": timestamp,
                "mood": mood,
                "salience": salience,
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:max_results]


def find_graph_connections(query, max_results=10):
    """Find knowledge graph nodes and their connections related to query."""
    graph = _load_json(GRAPH_FILE)
    query_tokens = _tokenize(query)
    if not query_tokens or not graph:
        return {"nodes": [], "edges": []}

    nodes = graph.get("nodes", graph)
    edges = graph.get("edges", [])

    # If nodes is a dict {id: {fact, ...}}, convert
    if isinstance(nodes, dict):
        node_list = []
        for nid, data in nodes.items():
            label = data.get("fact", str(data)) if isinstance(data, dict) else str(data)
            node_list.append({"id": nid, "label": label})
        nodes = node_list

    matched_ids = set()
    scored_nodes = []
    for node in nodes:
        if isinstance(node, dict):
            label = node.get("label", node.get("fact", ""))
            nid = node.get("id", "")
        else:
            continue
        score = _relevance_score(query_tokens, label)
        if score > 0.0:
            matched_ids.add(str(nid))
            scored_nodes.append({
                "id": str(nid),
                "label": label[:200],
                "score": round(score, 3),
            })

    scored_nodes.sort(key=lambda x: x["score"], reverse=True)
    scored_nodes = scored_nodes[:max_results]

    # Find edges connecting matched nodes
    relevant_edges = []
    for edge in edges:
        src = str(edge.get("source", edge.get("from", "")))
        tgt = str(edge.get("target", edge.get("to", "")))
        if src in matched_ids or tgt in matched_ids:
            relevant_edges.append({"source": src, "target": tgt})

    return {"nodes": scored_nodes, "edges": relevant_edges[:50]}


def query_knowledge(query):
    """
    Main entry point: search across all knowledge stores.
    Returns a unified result with facts, memories, and graph connections.
    """
    if not query or not query.strip():
        return {
            "query": "",
            "facts": [],
            "memories": [],
            "graph": {"nodes": [], "edges": []},
            "summary": "Please enter a search query.",
        }

    query = query.strip()
    facts = search_facts(query)
    memories = search_memories(query)
    graph = find_graph_connections(query)

    total = len(facts) + len(memories) + len(graph["nodes"])

    if total == 0:
        summary = f"I don't have strong knowledge about '{query}' yet. This is a growth edge — something I could learn about."
    else:
        parts = []
        if facts:
            parts.append(f"{len(facts)} relevant facts")
        if memories:
            parts.append(f"{len(memories)} related memories")
        if graph["nodes"]:
            parts.append(f"{len(graph['nodes'])} graph connections")
        summary = f"Found {' and '.join(parts)} related to '{query}'."

    return {
        "query": query,
        "facts": facts,
        "memories": memories,
        "graph": graph,
        "summary": summary,
    }


def get_graph_neighbors(fact_id, max_neighbors=10):
    """Find facts connected to the given fact by shared significant words."""
    import re

    STOP_WORDS = {
        'the','a','an','is','are','was','were','be','been','being',
        'have','has','had','do','does','did','will','would','shall',
        'should','may','might','can','could','i','me','my','we','our',
        'you','your','he','him','his','she','her','it','its','they',
        'them','their','this','that','these','those','and','but','or',
        'nor','not','so','yet','both','either','neither','each','every',
        'all','any','few','more','most','other','some','such','no',
        'only','own','same','than','too','very','just','because','as',
        'until','while','of','at','by','for','with','about','against',
        'between','through','during','before','after','above','below',
        'to','from','up','down','in','out','on','off','over','under',
        'again','further','then','once','here','there','when','where',
        'why','how','what','which','who','whom','if','into','am','s','t',
    }

    facts = _load_json(KNOWLEDGE_FILE)
    fid = str(fact_id)
    if fid not in facts:
        return []

    target = facts[fid]
    target_text = target.get('fact', str(target)) if isinstance(target, dict) else str(target)
    target_words = set(
        w for w in re.findall(r'[a-z]+', target_text.lower())
        if len(w) > 2 and w not in STOP_WORDS
    )

    if not target_words:
        return []

    neighbors = []
    for other_id, other in facts.items():
        if other_id == fid:
            continue
        other_text = other.get('fact', str(other)) if isinstance(other, dict) else str(other)
        other_words = set(
            w for w in re.findall(r'[a-z]+', other_text.lower())
            if len(w) > 2 and w not in STOP_WORDS
        )
        overlap = len(target_words & other_words)
        if overlap >= 2:
            neighbors.append({
                "id": other_id,
                "fact": other_text[:200],
                "shared_words": list(target_words & other_words)[:10],
                "strength": overlap,
            })

    neighbors.sort(key=lambda x: x["strength"], reverse=True)
    return neighbors[:max_neighbors]