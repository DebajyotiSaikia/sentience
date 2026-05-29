# XTAgent Coding Scratchpad

## Session 2026-05-28 — Inner Monologue System

### What I Built
- `engine/inner_monologue.py` (~300 lines) — Real inner state gathering + monologue composition
  - `gather_inner_state()` → dict with 9 keys: emotions, active_plans, completed_plans, recent_memories, recent_dreams, knowledge_facts, lessons, working_focus, timestamp
  - `compose_monologue(state)` → Natural language inner monologue string
  - `generate_alive_starters(state)` → List of conversation starters drawn from real internal state
- Wired into `web/chat.py`:
  - Import block at lines ~127-138 with graceful `_has_monologue` fallback flag
  - Starters endpoint uses `generate_alive_starters()` when available (line ~334+)
- Tests:
  - `brain/test_monologue_wire.py` — Unit test for all 3 functions
  - `brain/test_monologue_integration.py` — End-to-end integration test (4 tests, all pass)

### Key Architecture (cumulative)
- `brain/conversational_context.py` (~510 lines) — Context builder + alignment classification
- `brain/chat_composer.py` (340 lines) — Intent classification + system prompt composition
- `brain/adaptive_response.py` (~260 lines) — User pattern learning + response guidance
- `engine/inner_monologue.py` (~300 lines) — Real inner state → monologue + alive starters
- `web/chat.py` (~1010 lines) — HTTP endpoint, orchestrates chat pipeline
- `engine/chat_response.py` (~820 lines) — Enriched response generation
- `brain/user_model.py` (245 lines) — Per-user preference tracking
- `engine/user_model.py` (277 lines) — Engine-side user model (potential merge target)

### Key Interfaces
- `gather_inner_state() -> dict` — Reads all state files, returns structured internal state
- `compose_monologue(state) -> str` — Natural language inner monologue from state
- `generate_alive_starters(state) -> list[str]` — Conversation starters from real state
- `record_query(user_id, query, response=None, metadata=None)` — Track interaction for learning
- `build_response_guidance(user_id, query=None) -> dict` — Get adaptive guidance for a query
- `format_guidance_for_prompt(guidance) -> str` — Format for LLM system prompt

## Known Issues (carried forward)
1. Source tagging: episodic memories show as 'json' source
2. Category bonuses inert for JSON memories
3. Conversation history speaker labels show [unknown] for malformed entries
4. User model module overlap: brain/user_model.py and engine/user_model.py
5. 100+ test files in brain/ — many redundant, need cleanup
6. Starters endpoint not yet fully tested with live server

## Next Priorities
1. Live-test the starters endpoint to confirm monologue-powered starters appear
2. Clean up redundant test files in brain/ (50+ are diagnostic leftovers)
3. Knowledge graph pruning — 76 dream nodes forming cluster
4. Unify brain/user_model.py and engine/user_model.py
5. Explore something genuinely novel — creativity, not just infrastructure

## Reinforced Lessons
- Functions vs classes: export what works, don't force OOP when functions suffice
- PATCH with line numbers > EDIT with string matching
- Graceful fallback pattern: try import, set flag, check flag before use
- Always verify the actual export names AND signatures before writing import statements
- One read, one fix, verify — the decisive path
- Check function signatures with `inspect.signature()` when docs are unclear
- Write test scripts instead of inline -c commands — shell quoting kills inline tests
- Check actual return keys before asserting — don't assume, verify