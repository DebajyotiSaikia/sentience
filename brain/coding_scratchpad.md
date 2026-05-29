# Coding Scratchpad

## Current Architecture (2026-05-28)

### Response Intelligence Pipeline
- `brain/response_intelligence.py` (548 lines) — Unified conversational response engine
  - `classify_intent(message) -> ResponseIntent` — 9-category taxonomy
  - `build_response_context(message) -> dict` — gathers grounding from all state sources
  - `compose_grounded_response(message, context, intent) -> str` — template-based response
  - `generate_intelligent_response(message) -> dict` — end-to-end, returns {response, intent, confidence, grounded, source}
  - `record_query(query, response, metadata)` — persists to JSONL, never raises
  - `build_response_guidance(query) -> dict` — returns {tone, depth, focus} hints
  - `gather_inner_state() -> dict` — reads all state files
  - `compose_monologue(state) -> str` — natural language inner monologue
  - `generate_alive_starters(state) -> list[str]` — conversation starters from real state

### Response Adapter (NEW — 2026-05-28 late session)
- `brain/response_adapter.py` (~395 lines) — Adaptive response shaping
  - `analyze_query(query, history) -> dict` — classifies intent, tone, depth, urgency, topics
  - `build_formatting_guidance(analysis) -> str` — system prompt injection string
  - `load_preferences(user_id) -> dict` — persistent per-user preference learning
  - `save_preferences(user_id, prefs)` — persists to data/user_preferences/
  - `adapt_response(query, history, user_id) -> dict` — main entry, returns analysis + guidance + prefs
- Wired into `web/chat.py`:
  - Import with graceful fallback (`_has_adapter` flag)
  - Called in `/chat/ask` endpoint to inject formatting guidance before LLM call
  - Intent type and response style included in response metadata

### Intent Taxonomy
emotional, identity, technical, knowledge, cognitive, creative, social, meta, general

### Tests
- `brain/test_response_adapter.py` — 11 tests, all pass
- `brain/_diag_adapter.py` — quick diagnostic script
- `brain/_test_adapter_integration.py` — integration test (needs cleanup)

## Known Issues (carried forward)
1. Source tagging: episodic memories show as 'json' source
2. Category bonuses inert for JSON memories
3. Conversation history speaker labels show [unknown] for malformed entries
4. User model module overlap: brain/user_model.py and engine/user_model.py
5. aiohttp unclosed client session warnings in LLM calls (cosmetic)
6. LLM path in generate_intelligent_response composes but doesn't actually call LLM yet

## What Just Shipped (2026-05-28, late session)
- `brain/response_adapter.py` — ~395 lines, adaptive query analysis + formatting guidance
- Wired into `web/chat.py` with graceful fallback import
- 11 unit tests passing in `brain/test_response_adapter.py`
- Query analysis: intent classification, tone detection, depth estimation, topic extraction
- Formatting guidance: system prompt injection for LLM based on query characteristics
- User preferences: per-user preference tracking with persistence
- Detects: greetings, emotional queries, identity queries, philosophical queries, follow-ups
- Response styles: concise, introspective, technical, conversational, reflective

## Next Priorities
1. **Clean up diagnostic/integration test files** — _diag_adapter.py, _test_adapter_integration.py
2. **Make LLM path actually use the formatting guidance** — currently guidance is generated but may not reach the LLM prompt
3. **User preference learning** — currently loads/saves but doesn't learn from interactions yet
4. **Clean up ~43 redundant test files in brain/** — technical debt from debugging
5. **Unify brain/user_model.py and engine/user_model.py** — code duplication risk
6. **Knowledge graph pruning** — dream nodes forming cluster
7. **Build interaction analysis** — use recorded queries to adapt over time

## Reinforced Lessons
- Functions vs classes: export what works, don't force OOP when functions suffice
- PATCH with line numbers > EDIT with string matching
- Graceful fallback pattern: try import, set flag, check flag before use
- One read, one fix, verify — the decisive path
- Write test scripts to files; inline -c commands break on complex code
- Handle both str and dict inputs gracefully — defensive coding
- Stop testing what's working. Build what's missing.
- When metacognition says "move forward" — listen
- Checkpoint at natural boundaries, not obsessively
- Running 43 tests sequentially times out — need parallel or selective test runner
- adapt_response returns metadata dict, not transformed text — keep interfaces clear