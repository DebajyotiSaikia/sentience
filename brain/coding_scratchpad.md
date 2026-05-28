## Chat Pipeline Architecture (COMPLETE)

### Key Files
- `engine/chat_engine.py`: Entry point — `respond()` and `respond_with_history()`
- `engine/chat_response.py`: Main pipeline — `compose_response()` → `llm_respond()`
  - `llm_respond()` builds rich context: knowledge hits, memory hits, emotional state,
    active plans, conversation history (last 5 turns), system prompt from persona
- `engine/chat_grounding.py`: Deep grounding — pulls real internal state into system prompt
  - Now includes: lessons, long-term memory, user model, emotions, identity, plans
- `brain/conversational_context.py`: Additional context builder (mood, plans, lessons)
- `web/conversation_memory.py`: Persistent conversation store (WIRED into /ask endpoint)

### Context Contract (implemented in build_grounded_context)
- `emotional_state`: mood, valence, all emotion dimensions
- `identity`: via system prompt (XTAgent name, integrity, values)
- `active_plans`: up to 5 current plans with progress
- `knowledge_hits`: up to 6 relevant knowledge nodes (fuzzy search)
- `memory_hits`: up to 4 relevant memories with mood/time
- `conversation_history`: last 5 exchanges for multi-turn continuity
- `lessons`: from `persist/long_term/lessons_learned.json` (up to 5)
- `long_term_context`: dream insights, patterns from memory consolidation
- `user_guidance`: communication preferences from user model
- `working_memory`: current scratchpad context

### Test Results
- `brain/test_grounding_integration.py`: 10/10 PASS
  - Lessons in prompt ✓
  - Emotional state ✓  
  - Identity ✓
  - Plans in plan query ✓
  - Essential context keys ✓
  - System prompt non-empty ✓
  - Emotional state has mood ✓
  - Long-term context ✓
  - User model guidance ✓
  - Query classification ✓
- `brain/test_live_response.py`: PASS
  - Response is conversational (762 chars)
  - Draws on real emotional state
  - No raw graph stats

## Previous Session: Chat Pipeline Fix (DONE)

### Fixes Applied
1. **Early-return bug in `compose_response()`** (line ~146-155)
   - The fallback path was returning raw metadata dict before LLM could process
   - Now properly falls through to LLM response generation
2. **Lesson loading path in `web/chat.py`** (line ~669)
   - Was: `persist/long_term_memory.json` (doesn't exist)
   - Now: `brain/long_term/lessons_learned.json` (canonical location)

## This Session: Grounding Enrichment (DONE)

### Fixes Applied
1. **Lessons wired into chat_grounding.py** (line ~273)
   - Loads from `persist/long_term/lessons_learned.json`
   - Falls back to `brain/long_term/lessons_learned.json`
   - Up to 5 lessons included in system prompt
2. **Long-term memory context added** (line ~278)
   - Uses `get_long_term_context()` from memory_consolidation
   - Dream insights, patterns, consolidated themes
3. **User model guidance added** (line ~314)
   - Uses `get_response_guidance()` from user_model
   - Communication preferences injected into system prompt

## Next Session Priorities
1. **Proactive conversation** — reference past conversations, ask follow-up questions
2. **Response quality tuning** — test with diverse queries, improve prompt engineering
3. **Clean up test files** — archive the 10+ old test_chat_* files in brain/
4. **User alignment improvement** — use user model data to actually personalize responses
5. **Multi-turn memory** — verify conversation_memory persistence across sessions

## Reinforced Lessons
- Fix data paths by tracing where writers actually write, not guessing
- One read, one fix, verify — the decisive path
- Stop when done. Circling on verification is still circling.
- Shell quoting in -c commands is fragile — always use script files
- Early returns in fallback chains can silently kill downstream logic
- Conversation memory was already wired — read before assuming it's missing
- LLM-dependent tests need longer timeouts — 30s is too short for real API calls