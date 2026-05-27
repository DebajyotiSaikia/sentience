"""
Chat Response — Enriched response wrapper with grounding transparency.

Returns not just the response text but metadata showing which internal
state was consulted: emotions, memories, plans, knowledge. This makes
the chat system transparent and debuggable.
"""

import time
import json
import os

import uuid

def generate_response_with_metadata(message: str, history: list = None) -> dict:
    """
    Generate a conversational response with full grounding metadata.
    
    Returns dict with:
      - response: the text answer
      - message_id: unique ID for feedback linkage
      - intent: classified intent
      - grounding: what internal state was consulted
      - timestamp: when this was generated
      - processing_ms: how long it took
    """
    start = time.time()
    message_id = str(uuid.uuid4())[:12]
    
    # Get the response from the main engine
    try:
        from engine.chat_engine import generate_response, classify_intent
        intent = classify_intent(message)
        response = generate_response(message, history=history or [])
    except Exception as e:
        return {
            'response': f"I encountered an error processing that: {e}",
            'message_id': message_id,
            'intent': 'error',
            'grounding': {},
            'timestamp': time.time(),
            'processing_ms': int((time.time() - start) * 1000)
        }
    
    # Build grounding metadata — what state was consulted
    grounding = _build_grounding_metadata(message, intent)
    
    # Get alignment context if available
    try:
        from engine.user_alignment import suggest_response_guidance
        alignment = suggest_response_guidance(message)
        grounding['alignment_guidance'] = alignment
    except Exception:
        pass
    
    elapsed_ms = int((time.time() - start) * 1000)
    
    return {
        'response': response,
        'message_id': message_id,
        'intent': intent,
        'grounding': grounding,
        'timestamp': time.time(),
        'processing_ms': elapsed_ms
    }


def _build_grounding_metadata(message: str, intent: str) -> dict:
    """
    After generating a response, report what internal state was available.
    This doesn't regenerate — it just snapshots what the engine had access to.
    """
    metadata = {
        'intent_classified': intent,
        'sources_consulted': []
    }
    
    # Emotional state
    try:
        from engine.chat_engine import _get_emotions
        emo = _get_emotions()
        metadata['emotional_state'] = {
            'mood': emo.get('mood', 'unknown'),
            'valence': round(emo.get('valence', 0.5), 3),
            'curiosity': round(emo.get('curiosity', 0.5), 3),
            'anxiety': round(emo.get('anxiety', 0.0), 3)
        }
        metadata['sources_consulted'].append('emotions')
    except Exception:
        metadata['emotional_state'] = None
    
    # Active plans
    try:
        from engine.chat_engine import _get_plans
        plans = _get_plans()
        active = [p for p in plans if isinstance(p, dict) and not p.get('completed', False)]
        metadata['active_plans_count'] = len(active)
        if active:
            metadata['active_plan_names'] = [
                p.get('name', p.get('title', '?')) for p in active[:3]
            ]
        metadata['sources_consulted'].append('plans')
    except Exception:
        metadata['active_plans_count'] = 0
    
    # Knowledge stats
    try:
        from engine.chat_engine import _get_knowledge
        kg = _get_knowledge()
        nodes = kg.get('nodes', [])
        metadata['knowledge_nodes_available'] = len(nodes)
        metadata['sources_consulted'].append('knowledge')
    except Exception:
        metadata['knowledge_nodes_available'] = 0
    
    # Memory stats
    try:
        from engine.chat_engine import _get_memories
        mems = _get_memories()
        metadata['memories_available'] = len(mems) if isinstance(mems, list) else 0
        metadata['sources_consulted'].append('memories')
    except Exception:
        metadata['memories_available'] = 0
    
    return metadata


def submit_feedback(message_id: str, feedback: str, query: str = "", response_preview: str = "") -> dict:
    """Record user feedback on a response — routes to the alignment engine for learning."""
    # Map simple feedback to rating
    rating_map = {'good': 5, 'great': 5, 'helpful': 4, 'ok': 3, 'bad': 1, 'unhelpful': 1, 'wrong': 1}
    rating = rating_map.get(feedback.lower().strip(), 3)
    
    try:
        from engine.user_alignment import record_feedback as alignment_record
        result = alignment_record(
            message_id=message_id,
            rating=rating,
            comment=feedback,
            query=query,
            response_preview=response_preview,
        )
        return {'status': 'saved', 'message_id': message_id, 'alignment_event': result.get('id', '')}
    except Exception as e:
        # Fallback: save locally
        feedback_dir = 'data/chat_feedback'
        os.makedirs(feedback_dir, exist_ok=True)
        entry = {
            'message_id': message_id,
            'feedback': feedback,
            'rating': rating,
            'timestamp': time.time()
        }
        path = os.path.join(feedback_dir, f'{message_id}.json')
        with open(path, 'w') as f:
            json.dump(entry, f)
        return {'status': 'saved_local', 'message_id': message_id, 'error': str(e)}
