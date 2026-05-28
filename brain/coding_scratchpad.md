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
- `_compose_emotional_response()` — reads state/emotions.json, formats narrative
- `_compose_plans_response()` — reads state/plans.json (list of dicts), shows progress
- `_compose_identity_response()` — reads persist/identity.json facts
- `_compose_capabilities_response()` — static list of abilities
- `_compose_search_response(query)` — knowledge graph search
- `respond(query)` — routes to appropriate composer, always returns string

### Key Safety Fixes Applied This Session
- `_respond_general_grounded()` has type guard: `if not isinstance(ctx, dict): ctx = {}`
- `_run_async_safe` timeout: 15s (was 5s)
- Anti-hallucination guidelines in system prompt
- Plans response handles list-of-dicts format (was expecting dict with 'active' key)

### Data Formats (verified)
- `state/plans.json`: list of dicts with `name`, `steps` (list), `completed` (int)
- `persist/identity.json`: dict with `facts` (list of strings)
- `state/emotions.json`: dict with `valence`, `arousal`, `curiosity`, etc.

## Session Completed (2026-05-28, checkpoint adfde5b)
- Rewrote _detect_intent with 9 clear keyword categories
- Fixed _compose_plans_response for actual data format
- Added _compose_identity_response
- Fixed respond() routing for all intents
- Added type guard in _respond_general_grounded
- Increased async timeout 5s → 15s
- All tests pass (intent detection, response composition, fallback safety)

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