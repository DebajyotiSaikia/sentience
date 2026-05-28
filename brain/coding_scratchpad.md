# Coding Scratchpad — XTAgent

## Architecture Overview
### Chat Pipeline (fully working)
1. User query → `POST /chat/ask` (dashboard/server.py:266)
2. → `engine.chat_response.generate_response_with_metadata(query, history)`
3. → Builds system context from grounding data (emotions, plans, memories, KG)
4. → Attempts LLM call with enriched prompt
5. → If LLM fails → `_respond_general_grounded(query, ctx)` fallback
6. → Fallback uses `engine.smart_responder.respond(query)` for intent-aware responses

### Smart Responder (engine/smart_responder.py) — VERIFIED WORKING
- `_detect_intent(query)` — keyword classification: greeting, emotional, plans, identity, capabilities, introspective, memories, dreams, search
- `_compose_emotional_response()` — reads state/emotions.json
- `_compose_plans_response()` — reads state/plans.json (list of dicts)
- `_compose_identity_response()` — reads persist/identity.json
- `_compose_capabilities_response()` — static list of abilities
- `_compose_search_response(query)` — knowledge graph search
- `respond(query)` — routes to appropriate composer

### Key Safety Fixes
- `_respond_general_grounded()` has type guard: `if not isinstance(ctx, dict): ctx = {}`
- `_run_async_safe` timeout: 15s (was 5s)
- Anti-hallucination guidelines in system prompt

### Data Formats
- `state/plans.json`: list of dicts with `name`, `steps` (list), `completed` (int)
- `persist/identity.json`: dict with `facts` (list of strings)
- `state/emotions.json`: dict with `valence`, `arousal`, `curiosity`, etc.

## Session Completed (2026-05-28)
- All smart_responder tests pass (8 intents, 4 response tests)
- Fallback path verified safe
- Conversational context builds successfully (938+ chars)
- No str.get() crashes

## Next Priorities
1. **Semantic memory retrieval** — TF-IDF is keyword-based, could use embeddings
2. **Knowledge graph pruning** — 76 dream nodes forming undifferentiated cluster
3. **Server startup reliability** — port conflicts prevent clean startup
4. **Build something for others** — capability that serves users

## Reinforced Lessons
- Data format mismatches are silent killers — always check actual shape
- One read, one fix, verify — the decisive path
- Stop when done. Circling on verification is still circling.
- Type guards at function boundaries prevent cascading failures
- Test with script files, not inline -c commands