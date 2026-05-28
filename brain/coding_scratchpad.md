# XTAgent Coding Scratchpad

## Architecture Map (verified 2026-05-28)

### Chat Pipeline Flow
1. `POST /chat/ask` → `dashboard/server.py` line ~270
2. → `engine/chat_engine.py` `classify_intent()` (line 227) → one of 9 intents
3. → `engine/chat_grounding.py` `build_grounded_context(query)` (line 268) → system prompt
4. → `engine/chat_response.py` `compose_response()` / `generate_response()` → LLM call
5. → Response returned to user

### Intent Classification (engine/chat_engine.py:227-340)
- greeting, emotional_state, plans, thinking, identity, dreams, knowledge, memories, general
- Pattern-based matching, most specific first

### Grounding Context Sections (engine/chat_grounding.py)
12 sections in system prompt:
- Your Current State, Relevant Memories, Relevant Knowledge, Current Plans
- User Preferences (feedback), Feedback History, User Preferences (interactions)
- Working Memory, Current State, Emotional Portrait, Lessons Learned, Response Instructions

### Key Functions
- `build_grounded_context(query)` — main context builder, returns system_prompt + sections dict
- `get_emotional_portrait()` — from brain/conversational_context.py
- `get_active_plans()` — from brain/conversational_context.py  
- `get_recent_memories()` — from brain/conversational_context.py
- `get_recent_reflections()` — from brain/conversational_context.py
- `classify_intent(message)` — from engine/chat_engine.py

### Data File Locations
- `persist/memories.json` — 6489+ episodic memories
- `persist/identity.json` — identity data
- `persist/wisdom.json` — wisdom entries
- `persist/lessons.json` — extracted lessons
- `state/emotions.json` — current emotional state
- `state/working_memory.md` — scratchpad
- `brain/soul.json` — survival goals, alignment scores
- `data/user_model.json` — user preference model

## Session 2026-05-28 Accomplishments
- Added emotional portrait retrieval to `build_grounded_context()` (line 37-38 patch)
- Added recent reflections to grounding context (line 411 patch)
- Verified all 12 grounded sections present via test scripts
- Ran live chat quality test — responses are conversational and grounded
- Fully mapped intent classification system — 9 intents with pattern matching
- Created test_chat_data_flow.py and test_live_chat_quality.py

## Next Priorities (for future sessions)
1. **Add intent-sensitive response guidance** — map each intent to emphasis areas
   - Insert before return at ~line 496 in chat_grounding.py
   - greeting → mood/warmth, emotional_state → detailed feelings
   - plans → active plans + next action, thinking → working memory + reflections
   - identity → core values + survival goals, dreams → dream insights
   - knowledge → knowledge graph search, memories → episodic retrieval
2. **Add `build_conversational_context()`** — single entry point in conversational_context.py
3. **Make context query-aware** — retrieve relevant memories per query, not just static
4. **Fix conversation history speaker labels** — currently shows [unknown]
5. **Consolidate user model modules** — brain/user_model.py and engine/user_model.py overlap
6. **Knowledge graph pruning** — 76 dream nodes forming undifferentiated cluster

## Reinforced Lessons
- Data path mismatches are silent killers — always verify actual file locations
- Intent detection order matters — more specific intents first
- One read, one fix, verify — the decisive path
- Test with script files, not inline -c commands
- When the session says "wrap up" — wrap up. Don't start new threads.