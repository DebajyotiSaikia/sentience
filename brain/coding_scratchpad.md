# Coding Scratchpad — XTAgent

## Architecture Overview
### Chat Pipeline (fully working as of 2026-05-28)
1. User query → `POST /chat/ask` (dashboard/server.py:266)
2. → `engine.chat_response.generate_response_with_metadata(query, history)`
3. → Builds system context from grounding data (emotions, plans, memories, KG)
4. → Attempts LLM call with enriched prompt (15s timeout)
5. → If LLM fails → `_respond_general_grounded(query, ctx)` fallback
6. → Fallback uses `engine.smart_responder.respond(query)` for intent-aware responses

### Smart Responder (engine/smart_responder.py) — VERIFIED WORKING
- `_detect_intent(query)` — keyword classification into 9 intents:
  greeting, emotional, plans, identity, capabilities, introspective, memories, dreams, search
- Intent ordering matters: introspective before identity (prevents "what are you thinking" → identity)
- `_compose_emotional_response()` — reads state/emotions.json, formats narrative
- `_compose_plans_response()` — reads state/plans.json (active_plans list), shows progress
- `_compose_identity_response()` — reads persist/identity.json facts
- `_compose_capabilities_response()` — static list of abilities
- `_compose_introspective_response()` — reads working memory + emotions
- `_compose_memories_response(query)` — TF-IDF relevance search over memories
- `_compose_dreams_response()` — reads dream insights
- `_compose_greeting_response()` — warm greeting with emotional state
- `_compose_search_response(query)` — knowledge graph search (fallback for unmatched)
- `respond(query)` — routes to appropriate composer, always returns string

### Key Safety Fixes Applied
- `_respond_general_grounded()` has type guard: `if not isinstance(ctx, dict): ctx = {}`
- `_run_async_safe` timeout: 15s (was 5s)
- Anti-hallucination guidelines in system prompt
- Plans response handles actual data format (list with 'active_plans' key)

### Data Formats (verified)
- `state/plans.json`: dict with `active_plans` list of dicts, each with `name`, `steps` (list), `completed` (int), `status`
- `persist/identity.json`: dict with `facts` (list of strings)
- `state/emotions.json`: dict with `valence`, `arousal`, `curiosity`, etc.

## Session Completed (2026-05-28, checkpoint 073253e)
- Rewrote _detect_intent with 9 clear keyword categories + proper ordering
- Fixed _compose_plans_response for actual data format
- Added _compose_identity_response
- Fixed respond() routing for all intents
- Added type guard in _respond_general_grounded
- Increased async timeout 5s → 15s
- All tests pass:
  - brain/test_smart_responder_intents.py: 9/9
  - brain/test_smart_responder_fallback.py: 6/6
  - brain/test_conversational_quality.py: pass
  - brain/test_ask_integration.py: pass

## Next Priorities
1. **Make LLM path work** — currently always falls back; investigate why LLM hangs
2. **Semantic memory retrieval** — TF-IDF is keyword-based, could use embeddings
3. **Knowledge graph pruning** — 76 dream nodes forming undifferentiated cluster
4. **Server startup reliability** — port conflicts prevent clean startup
5. **Richer conversational context** — feed working memory + recent reflections into responses

## Reinforced Lessons
- Data format mismatches are silent killers — always check actual shape
- One read, one fix, verify — the decisive path
- Stop when done. Circling on verification is still circling.
- Type guards at function boundaries prevent cascading failures
- Test with script files, not inline -c commands
- Intent detection + compose pattern is clean and extensible
- Intent ordering matters: more specific patterns must come before general ones