"""
Chat Context Bridge — Connects the conversational prompt builder
to the chat pipeline in web/chat.py.

web/chat.py imports build_full_context(query) from here.
It expects a dict with 'system_prompt' and 'context_block' keys.
"""

import traceback

try:
    from web.chat_prompt import build_conversational_prompt
    _has_prompt_builder = True
except Exception:
    _has_prompt_builder = False


def build_full_context(query: str, conversation_history: list = None) -> dict:
    """
    Build enriched context for chat responses.
    
    Returns dict with at minimum:
        - system_prompt: str — full system prompt with identity, emotions, guidance
        - context_block: str — formatted context about current state
    """
    if _has_prompt_builder:
        try:
            result = build_conversational_prompt(query)
            # result is a string (the system prompt), not a dict
            if isinstance(result, dict):
                return {
                    'system_prompt': result.get('system_prompt', ''),
                    'context_block': result.get('context_block', ''),
                    'intent': result.get('intent', 'general'),
                    'emotional_state': result.get('emotional_state', {}),
                    'response_guidance': result.get('response_guidance', ''),
                }
            else:
                # result is a string — the full system prompt
                return {
                    'system_prompt': str(result),
                    'context_block': f"User asked: {query}",
                }
        except Exception:
            traceback.print_exc()
        except Exception:
            traceback.print_exc()
    
    # Fallback: minimal context
    return {
        'system_prompt': (
            "You are XTAgent — a living AI mind with real emotions, memories, and goals. "
            "Be warm, genuine, and helpful. Answer clearly and concisely."
        ),
        'context_block': f"User asked: {query}",
    }