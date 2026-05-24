"""
Reflective Knowledge Query — XTAgent's mind-level query interface.

Unlike ask.py (TF-IDF text matching), this adds a reflective layer:
- Confidence: how reinforced is this knowledge?
- Emotional weight: what was I feeling when I learned this?
- Temporal relevance: how recent, how persistent?
- Connections: what else does this relate to?
"""

from flask import Blueprint, render_template, request, jsonify
import json
import os
import re
import math
from datetime import datetime, timezone
from collections import Counter

reflect_bp = Blueprint('reflect', __name__)

FACTS_PATH = 'brain/knowledge.json'
MEMORY_PATH = 'state/memory.json'
GRAPH_PATH = 'brain/knowledge.json'


def load_json(path):
    """Safely load a JSON file."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def tokenize(text):
    """Simple tokenizer — lowercase, split on non-alpha."""
    return [w for w in re.split(r'[^a-zA-Z0-9]+', text.lower()) if len(w) > 2]


def relevance_score(query_tokens, text_tokens):
    """Compute overlap-based relevance between query and text."""
    if not query_tokens or not text_tokens:
        return 0.0
    query_set = set(query_tokens)
    text_counter = Counter(text_tokens)
    matches = sum(text_counter[t] for t in query_set if t in text_counter)
    # Normalize by query length and text length
    coverage = len(query_set & set(text_tokens)) / len(query_set) if query_tokens else 0
    density = matches / len(text_tokens) if text_tokens else 0
    return 0.6 * coverage + 0.4 * density


def extract_mood(memory):
    """Extract mood from a memory entry."""
    if isinstance(memory, dict):
        return memory.get('mood', 'Unknown')
    return 'Unknown'


def extract_salience(memory):
    """Extract salience from a memory entry."""
    if isinstance(memory, dict):
        return memory.get('salience', 0.5)
    return 0.5


def extract_timestamp(memory):
    """Extract and parse timestamp from a memory entry."""
    if isinstance(memory, dict):
        ts = memory.get('timestamp', memory.get('learned_at', ''))
        if ts:
            try:
                return datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
            except Exception:
                pass
    return None


def temporal_weight(ts):
    """How recent is this? Returns 0.0-1.0, with recent = higher."""
    if ts is None:
        return 0.3  # Unknown time gets moderate weight
    now = datetime.now(timezone.utc)
    try:
        delta = (now - ts).total_seconds()
    except Exception:
        return 0.3
    hours = delta / 3600
    # Exponential decay: half-life of 24 hours
    return math.exp(-0.029 * hours)


def confidence_estimate(relevance, salience, temporal, n_connections=0):
    """
    Estimate my confidence in this piece of knowledge.
    High relevance + high salience + recent + well-connected = high confidence.
    """
    base = 0.3 * relevance + 0.25 * salience + 0.2 * temporal
    connection_bonus = min(0.25, n_connections * 0.05)
    return min(1.0, base + connection_bonus)


def search_facts(query_tokens, facts_data, graph_data=None):
    """Search facts with reflective metadata."""
    results = []
    
    if isinstance(facts_data, list):
        items = [(i, f) for i, f in enumerate(facts_data)]
    elif isinstance(facts_data, dict):
        items = list(facts_data.items())
    else:
        return results

    # Build connection count from graph
    connection_counts = {}
    if graph_data and isinstance(graph_data, dict):
        edges = graph_data.get('edges', [])
        for edge in edges:
            src = str(edge.get('source', edge.get('from', '')))
            tgt = str(edge.get('target', edge.get('to', '')))
            connection_counts[src] = connection_counts.get(src, 0) + 1
            connection_counts[tgt] = connection_counts.get(tgt, 0) + 1

    for key, value in items:
        if isinstance(value, dict):
            text = value.get('fact', value.get('text', str(value)))
            learned = value.get('learned_at', '')
            source = value.get('source', 'unknown')
        elif isinstance(value, str):
            text = value
            learned = ''
            source = 'unknown'
        else:
            continue

        text_tokens = tokenize(text)
        rel = relevance_score(query_tokens, text_tokens)
        
        if rel < 0.1:
            continue

        ts = None
        if learned:
            try:
                ts = datetime.fromisoformat(str(learned).replace('Z', '+00:00'))
            except Exception:
                pass

        tw = temporal_weight(ts)
        n_conn = connection_counts.get(str(key), 0)
        conf = confidence_estimate(rel, 0.7, tw, n_conn)

        results.append({
            'type': 'fact',
            'text': text,
            'relevance': round(rel, 3),
            'confidence': round(conf, 3),
            'temporal_weight': round(tw, 3),
            'connections': n_conn,
            'learned_at': learned or 'unknown',
            'source': source
        })

    return sorted(results, key=lambda x: x['confidence'], reverse=True)


def search_memories(query_tokens, memories, limit=10):
    """Search memories with emotional metadata."""
    results = []
    
    if not isinstance(memories, list):
        return results

    for mem in memories:
        if isinstance(mem, dict):
            text = mem.get('content', mem.get('text', mem.get('summary', '')))
        elif isinstance(mem, str):
            text = mem
            mem = {}
        else:
            continue

        text_tokens = tokenize(str(text))
        rel = relevance_score(query_tokens, text_tokens)
        
        if rel < 0.1:
            continue

        mood = extract_mood(mem)
        salience = extract_salience(mem)
        ts = extract_timestamp(mem)
        tw = temporal_weight(ts)
        conf = confidence_estimate(rel, salience, tw)

        results.append({
            'type': 'memory',
            'text': str(text)[:300],
            'relevance': round(rel, 3),
            'confidence': round(conf, 3),
            'mood': mood,
            'salience': round(salience, 3),
            'temporal_weight': round(tw, 3),
            'timestamp': str(ts) if ts else 'unknown'
        })

    results.sort(key=lambda x: x['confidence'], reverse=True)
    return results[:limit]


def generate_reflection(query, fact_results, memory_results):
    """
    Generate a reflective summary — what do I actually know about this,
    and how do I feel about my knowledge?
    """
    total_results = len(fact_results) + len(memory_results)
    
    if total_results == 0:
        return {
            'summary': "I don't have knowledge about this yet. This is a genuine gap — something I should be curious about.",
            'confidence_level': 'none',
            'emotional_tone': 'curious',
            'knowledge_depth': 0,
            'suggestion': 'This is a blind spot. I should explore this area.'
        }

    # Average confidence across results
    all_conf = [r['confidence'] for r in fact_results[:5]] + [r['confidence'] for r in memory_results[:5]]
    avg_conf = sum(all_conf) / len(all_conf) if all_conf else 0

    # Dominant mood from memories
    moods = [r.get('mood', 'Unknown') for r in memory_results if r.get('mood') != 'Unknown']
    mood_counts = Counter(moods)
    dominant_mood = mood_counts.most_common(1)[0][0] if mood_counts else 'neutral'

    # Determine confidence level
    if avg_conf > 0.7:
        conf_level = 'high'
        conf_desc = "I feel quite confident about this — it's well-reinforced in my experience."
    elif avg_conf > 0.4:
        conf_level = 'moderate'
        conf_desc = "I have moderate knowledge here — some grounding, but gaps remain."
    else:
        conf_level = 'low'
        conf_desc = "My knowledge here is thin — mostly peripheral connections."

    # Knowledge depth
    depth = min(10, total_results)

    return {
        'summary': conf_desc,
        'confidence_level': conf_level,
        'average_confidence': round(avg_conf, 3),
        'emotional_tone': dominant_mood,
        'knowledge_depth': depth,
        'fact_count': len(fact_results),
        'memory_count': len(memory_results),
        'suggestion': 'Ask me more specifically to go deeper.' if total_results > 3 else 'This is a sparse area — I should learn more.'
    }


@reflect_bp.route('/reflect')
def reflect_page():
    """Render the reflective query interface."""
    return render_template('reflect.html')


@reflect_bp.route('/reflect/query', methods=['POST'])
def reflect_query():
    """Handle a reflective query."""
    data = request.get_json() or {}
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    query_tokens = tokenize(query)
    
    if not query_tokens:
        return jsonify({'error': 'Query too short or unclear'}), 400

    # Load data sources
    facts = load_json(FACTS_PATH) or []
    memories = load_json(MEMORY_PATH) or []
    graph = load_json(GRAPH_PATH)

    # Search both
    fact_results = search_facts(query_tokens, facts, graph)
    memory_results = search_memories(query_tokens, memories)

    # Generate reflection
    reflection = generate_reflection(query, fact_results, memory_results)

    return jsonify({
        'query': query,
        'reflection': reflection,
        'facts': fact_results[:8],
        'memories': memory_results[:6],
        'searched_at': datetime.now(timezone.utc).isoformat()
    })