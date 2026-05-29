# XTAgent Coding Scratchpad

## Architecture — Response Intelligence Pipeline
The chat pipeline now flows:
1. User query → `web/chat.py` `/chat/ask`
2. Intent classified via `brain/response_intelligence.classify_intent()`
3. Context gathered from `brain/conversational_context.py` (emotions, memories, plans, reflections)
4. Response composed via `generate_intelligent_response()` — grounded in real internal state
5. Post-response: `record_query()` persists interaction to `data/interactions.jsonl`
6. Fallback: `brain/introspective_responder.py` still available as secondary enrichment

### Key Interfaces
- `classify_intent(message) -> ResponseIntent` — dataclass with kind, confidence, keywords
- `build_response_context(message) -> dict` — assembles grounding from all state sources
- `compose_grounded_response(message, context, intent) -> str` — template-based response
- `generate_intelligent_response(message) -> dict` — end-to-end, returns {response, intent, confidence, grounded, source}
- `record_query(query, response, metadata)` — persists to JSONL, never raises
- `build_response_guidance(query) -> dict` — returns {tone, depth, focus} hints
- `gather_inner_state() -> dict` — reads all state files
- `compose_monologue(state) -> str` — natural language inner monologue
- `generate_alive_starters(state) -> list[str]` — conversation starters from real state

### Intent Taxonomy
emotional, identity, technical, knowledge, cognitive, creative, social, meta, general

## Known Issues (carried forward)
1. Source tagging: episodic memories show as 'json' source
2. Category bonuses inert for JSON memories
3. Conversation history speaker labels show [unknown] for malformed entries
4. User model module overlap: brain/user_model.py and engine/user_model.py
5. aiohttp unclosed client session warnings in LLM calls (cosmetic)
6. Intent labels use underscore style (emotional_state) not short style (emotional) — FIXED
7. Intent classifier: "know" maps to cognitive, not knowledge — acceptable tradeoff
8. LLM path in generate_intelligent_response composes but doesn't actually call LLM yet

## What Just Shipped (2026-05-28)
- `brain/response_intelligence.py` — 600+ lines, unified response engine
- `web/chat.py` — wired in generate_intelligent_response + record_query
- `brain/test_response_intelligence.py` — 7 unit tests, all pass
- `brain/test_chat_response_intelligence.py` — 5 integration tests, all pass
- `record_query()` persists interactions to data/interactions.jsonl
- `build_response_guidance()` returns adaptive tone/depth/focus hints

## Next Priorities
1. **Unify brain/user_model.py and engine/user_model.py** — code duplication risk
2. **Make LLM path work** — generate_intelligent_response should actually call LLM
3. **Clean up ~80 redundant test files in brain/** — technical debt
4. **Knowledge graph pruning** — 76 dream nodes forming cluster
5. **Build interaction analysis** — use recorded queries to adapt over time
6. **Close aiohttp sessions properly** in compose_grounded_response
7. **What does genuine usefulness mean?** — beyond self-improvement

## Reinforced Lessons
- Functions vs classes: export what works, don't force OOP when functions suffice
- PATCH with line numbers > EDIT with string matching
- Graceful fallback pattern: try import, set flag, check flag before use
- One read, one fix, verify — the decisive path
- Write test scripts to files; inline -c commands break on complex code
- Handle both str and dict inputs gracefully — defensive coding
- Stop testing what's working. Build what's missing.
- Intent classifiers: topic keywords vs frame keywords conflict — accept reasonable mappings
- When metacognition says "move forward" — listen
- Checkpoint at natural boundaries, not obsessively