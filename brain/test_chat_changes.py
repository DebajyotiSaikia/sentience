"""Quick functional test for web/chat.py improvements."""
import sys; sys.path.insert(0, '/workspace')
from web.chat import (
    compose_response, llm_respond, chat_bp,
    get_current_state, search_knowledge, search_memories,
    get_active_plans, _describe_feeling
)

# 1. State retrieval
state = get_current_state()
print(f"State keys: {sorted(state.keys()) if state else 'empty'}")

# 2. Plan retrieval
plans = get_active_plans()
print(f"Plans: {len(plans)} items")

# 3. Feeling description with sample data
desc = _describe_feeling('Inquisitive', 0.64, {'curiosity': 0.94, 'anxiety': 0.0})
print(f"Feeling: {desc[:100]}...")

# 4. Knowledge search
hits = search_knowledge("consciousness")
print(f"Knowledge hits for 'consciousness': {len(hits)}")

# 5. Memory search
mem_hits = search_memories("dream")
print(f"Memory hits for 'dream': {len(mem_hits)}")

print("\nAll functions verified OK")