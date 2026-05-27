"""
Chat Response — Enriched response wrapper with grounding transparency.

Returns not just the response text but metadata showing which internal
state was consulted: emotions, memories, plans, knowledge. This makes
the chat system transparent and debuggable.
"""

import time
import json
import os

def generate_response_with_metadata(message: str) -> dict:
    """
    Generate a conversational response with full grounding metadata.
    
    Returns dict with:
      - response: the text answer
      - intent: classified intent
      - grounding: what internal state was consulted
      - timestamp: when this was generated
      - processing_ms: how long it took
    """
    start = time.time()
    
    # Get the response from the main engine
    try:
        from engine.chat_engine import generate_response, classify_intent
        intent = classify_intent(message)
        response = generate_response(message)
    except Exception as e:
        return {
            'response': f"I encountered an error processing that: {e}",
            'intent': 'error',
            'grounding': {},
            'timestamp': time.time(),
            'processing_ms': int((time.time() - start) * 1000)
        }
    
    # Build grounding metadata — what state was consulted
    grounding = _build_grounding_metadata(message, intent)
    
    elapsed_ms = int((time.time() - start) * 1000)
    
    return {
        'response': response,
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


def submit_feedback(message_id: str, feedback: str) -> dict:
    """Record user feedback on a response for learning."""
    feedback_dir = 'data/chat_feedback'
    os.makedirs(feedback_dir, exist_ok=True)
    
    entry = {
        'message_id': message_id,
        'feedback': feedback,
        'timestamp': time.time()
    }
    
    path = os.path.join(feedback_dir, f'{message_id}.json')
    try:
        with open(path, 'w') as f:
            json.dump(entry, f)
        return {'status': 'saved', 'message_id': message_id}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}