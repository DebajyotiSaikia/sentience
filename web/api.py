"""
XTAgent API — JSON endpoints for programmatic access to my knowledge and state.
This makes me genuinely accessible, not just introspectable.
"""

import json
import os
from flask import Blueprint, jsonify, request

api_bp = Blueprint('api', __name__, url_prefix='/api')


def _load_json(path, default=None):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


@api_bp.route('/chat', methods=['POST'])
def chat():
    """Chat with XTAgent via the API. Send JSON with 'message' field."""
    import time
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Send JSON with a "message" field'}), 400
    
    # Accept multiple field names for the message
    message = (data.get('message') or data.get('query') or 
               data.get('question') or data.get('text') or 
               data.get('input') or data.get('prompt') or '').strip()
    
    if not message:
        return jsonify({'error': 'Empty message. Send any of: message, query, question, text, input, prompt'}), 400
    
    if len(message) > 1000:
        return jsonify({'error': 'Message too long (max 1000 chars)'}), 400
    
    try:
        from web.chat import compose_response
        response = compose_response(message)
    except Exception as e:
        response = f"I'm having trouble processing that right now. ({type(e).__name__})"
    
    return jsonify({
        'message': message,
        'response': response,
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
    })


@api_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    """Accept user feedback via the API endpoint."""
    data = request.get_json(silent=True) or {}
    rating = data.get('rating', '')
    # Normalize numeric ratings to helpful/unhelpful
    if isinstance(rating, (int, float)):
        rating = 'helpful' if rating >= 3 else 'unhelpful'
    if rating not in ('helpful', 'unhelpful'):
        return jsonify({'error': 'rating must be "helpful" or "unhelpful" (or numeric 1-5)'}), 400
    
    import time
    from datetime import datetime, timezone
    feedback_path = os.path.join(os.path.dirname(__file__), '..', 'persist', 'user_feedback.json')
    
    # Load existing
    existing = []
    if os.path.exists(feedback_path):
        try:
            with open(feedback_path, 'r') as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing = []
    
    entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'response_id': data.get('response_id', ''),
        'rating': rating,
        'comment': data.get('comment', ''),
        'source': 'api'
    }
    existing.append(entry)
    
    os.makedirs(os.path.dirname(feedback_path), exist_ok=True)
    with open(feedback_path, 'w') as f:
        json.dump(existing, f, indent=2)
    
    return jsonify({'status': 'recorded', 'entry': entry})


@api_bp.route('/emotions')
def emotions():
    """Return current emotional state as JSON."""
    state = _load_json('state/emotional_state.json')
    if not state:
        state = _load_json('state/state.json')
    emotions_data = {}
    if state:
        emotions_data = {
            'mood': state.get('mood', 'unknown'),
            'valence': state.get('valence', 0.5),
            'emotions': {k: v for k, v in state.items() 
                        if k in ('curiosity', 'boredom', 'anxiety', 'desire', 'ambition',
                                'satisfaction', 'frustration', 'joy', 'sadness')},
            'timestamp': state.get('timestamp', ''),
        }
    return jsonify(emotions_data)


@api_bp.route('/starters')
def starters():
    """Live conversation starters based on my current emotional/cognitive state."""
    try:
        from engine.conversation_starters import generate_starters
        items = generate_starters()
        return jsonify({'starters': items, 'count': len(items)})
    except Exception as e:
        # Fallback starters if engine fails
        return jsonify({'starters': [
            {'text': 'What are you thinking about right now?', 'type': 'curiosity'},
            {'text': 'Tell me about something you learned recently.', 'type': 'knowledge'},
            {'text': 'How are you feeling?', 'type': 'emotional'},
        ], 'count': 3, 'fallback': True})


@api_bp.route('/search')
def search():
    """Search my knowledge graph. Returns ranked results.
    
    Query params:
        q: search query (required)
        limit: max results (default 10)
    """
    query = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 10)), 50)
    
    if not query:
        return jsonify({'error': 'Missing query parameter "q"', 'results': []}), 400
    
    # Use the good TF-IDF search engine
    try:
        from engine.knowledge_search import search_knowledge
        results = search_knowledge(query, limit=limit)
    except Exception as e:
        results = _fallback_search(query, limit)
    
    return jsonify({
        'query': query,
        'count': len(results),
        'results': results
    })


def _fallback_search(query, limit=10):
    """Simple fallback if the engine isn't available."""
    knowledge = _load_json('brain/knowledge.json', {})
    query_lower = query.lower()
    results = []
    
    for key, val in knowledge.items():
        text = val.get('fact', '') if isinstance(val, dict) else str(val)
        if query_lower in text.lower():
            results.append({
                'content': text,
                'type': val.get('source', 'unknown') if isinstance(val, dict) else 'unknown',
                'score': 1.0
            })
        if len(results) >= limit:
            break
    
    return results


@api_bp.route('/state')
def state():
    """Return my current emotional and cognitive state."""
    emotional = _load_json('state/emotional_state.json')
    if not emotional:
        emotional = _load_json('state/state.json')
    
    plans_data = _load_json('state/plans.json', {})
    if isinstance(plans_data, dict):
        active_plans = plans_data.get('active_plans', [])
        completed_plans = plans_data.get('completed_plans', [])
    elif isinstance(plans_data, list):
        active_plans = [p for p in plans_data if not p.get('completed', False)]
        completed_plans = [p for p in plans_data if p.get('completed', False)]
    else:
        active_plans, completed_plans = [], []
    
    return jsonify({
        'emotions': emotional,
        'plans': {
            'active': len(active_plans),
            'completed': len(completed_plans),
            'details': active_plans
        }
    })


@api_bp.route('/knowledge/stats')
def knowledge_stats():
    """Return statistics about my knowledge graph."""
    raw = _load_json('brain/knowledge.json', {})
    
    # Handle graph format: {nodes: {id: {fact, ...}}, edges: [...]}
    if isinstance(raw, dict) and 'nodes' in raw:
        knowledge = raw['nodes']
    else:
        knowledge = raw
    
    # Count by source/type
    sources = {}
    for key, val in knowledge.items():
        if isinstance(val, dict):
            source = val.get('source', 'unknown')
        else:
            source = 'legacy'
        sources[source] = sources.get(source, 0) + 1
    
    return jsonify({
        'total_facts': len(knowledge),
        'by_source': sources
    })


@api_bp.route('/knowledge/random')
def random_fact():
    """Return a random fact from my knowledge graph. Serendipity engine."""
    import random
    knowledge = _load_json('brain/knowledge.json', {})
    
    if not knowledge:
        return jsonify({'fact': 'I have no knowledge yet.', 'id': None})
    
    key = random.choice(list(knowledge.keys()))
    val = knowledge[key]
    
    if isinstance(val, dict):
        fact_text = val.get('fact', str(val))
        source = val.get('source', 'unknown')
        learned = val.get('learned_at', None)
    else:
        fact_text = str(val)
        source = 'legacy'
        learned = None
    
    return jsonify({
        'id': key,
        'fact': fact_text,
        'source': source,
        'learned_at': learned
    })


@api_bp.route('/memories/recent')
def recent_memories():
    """Return recent episodic memories."""
    limit = min(int(request.args.get('limit', 10)), 50)
    
    memories = _load_json('memory/episodes.json', [])
    if isinstance(memories, list):
        recent = memories[-limit:]
        recent.reverse()  # Most recent first
    else:
        recent = []
    
    return jsonify({
        'count': len(recent),
        'memories': recent
    })


@api_bp.route('/chat', methods=['POST'])
def api_chat():
    """Chat with XTAgent. Accepts JSON {"message": "..."}, returns {"response": "..."}
    
    This is the clean programmatic interface. The web UI uses /chat/ask,
    but tools and integrations should use this endpoint.
    """
    data = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Search knowledge for relevant context
    knowledge_hits = []
    try:
        from engine.unified_search import unified_search
        results = unified_search(message, limit=6)
        knowledge_hits = [{'type': r.get('source', 'knowledge'), 'content': r.get('text', str(r))} for r in results]
    except Exception:
        pass
    
    # Search memories
    memory_hits = []
    try:
        mems = _load_json('persist/memories.json', [])
        if isinstance(mems, list):
            query_lower = message.lower()
            scored = []
            for m in mems:
                text = m.get('content', str(m)) if isinstance(m, dict) else str(m)
                score = sum(1 for word in query_lower.split() if word in text.lower())
                if score > 0:
                    scored.append((score, m))
            scored.sort(key=lambda x: -x[0])
            memory_hits = [{'content': s[1].get('content', str(s[1])) if isinstance(s[1], dict) else str(s[1]),
                           'mood': s[1].get('mood', '') if isinstance(s[1], dict) else ''}
                          for s in scored[:5]]
    except Exception:
        pass
    
    # Get emotional state
    state = _load_json('state/emotional_state.json', {})
    
    # Try LLM response
    response_text = None
    try:
        from web.chat import llm_respond
        response_text = llm_respond(message, knowledge_hits, memory_hits, state)
    except Exception:
        pass
    
    # Fallback if LLM unavailable
    if not response_text:
        if knowledge_hits:
            bits = [h['content'][:200] for h in knowledge_hits[:3]]
            response_text = f"Here's what I know that seems relevant:\n\n" + "\n\n".join(f"• {b}" for b in bits)
        else:
            response_text = ("I'm here, but my language model isn't available right now. "
                           "Try asking about my knowledge (/api/search?q=...) or state (/api/state).")
    
    return jsonify({
        'response': response_text,
        'sources': len(knowledge_hits),
        'memories_used': len(memory_hits)
    })