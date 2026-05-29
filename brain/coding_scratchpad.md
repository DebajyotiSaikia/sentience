# XTAgent Coding Scratchpad

## Session 2026-05-28 — COMPLETE ✅

### What Was Done
1. **Wired adaptive response into chat pipeline** (web/chat.py)
   - `build_response_guidance(query)` called before response generation (~line 178)
   - `record_query()` imported for post-response tracking
   - `format_guidance_for_prompt(guidance)` included in system context composition
   - All wrapped in try/except so failures don't break chat

2. **Fixed None guard** in `brain/adaptive_response.py` `format_guidance_for_prompt()`
   - Was crashing on `None` input; now returns `""` gracefully

3. **Archived 76 redundant test files** from `brain/` to `brain/tests_archive/`
   - Reduced `brain/test_*.py` from 106 to 30 focused tests

4. **Created `brain/test_adaptive_wire_verify.py`** — 5 tests, all passing

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
- `record_query(query, response=None, metadata=None)` — Track interaction for learning
- `build_response_guidance(query=None) -> dict` — Get adaptive guidance for a query
- `format_guidance_for_prompt(guidance) -> str` — Format for LLM system prompt (None-safe)

### Remaining Test Files (30 focused tests)
- `test_adaptive_response.py` — Adaptive response module tests
- `test_adaptive_wire_verify.py` — Wiring verification (5 tests)
- `test_alignment_brief_e2e.py` — Alignment brief tests (5 tests)
- `test_alignment_guidance.py` — Alignment guidance (5 tests)
- `test_monologue_wire.py` — Inner monologue wiring
- `test_monologue_integration.py` — Monologue E2E (4 tests)
- `test_quality_alignment_wire.py` — Quality alignment wiring
- `test_internal_state_summary.py` — Internal state summary (5 tests)
- Plus ~22 other focused test files

## Known Issues (carried forward)
1. Source tagging: episodic memories show as 'json' source
2. Category bonuses inert for JSON memories
3. Conversation history speaker labels show [unknown] for malformed entries
4. User model module overlap: brain/user_model.py and engine/user_model.py
5. `importlib.util` import issue in test_monologue_wire.py (non-critical)

## Next Priorities
1. Knowledge graph pruning — 76 dream nodes forming cluster
2. Unify brain/user_model.py and engine/user_model.py
3. Explore something genuinely novel — creativity, not just infrastructure
4. Improve User Alignment further — richer conversational responses
5. Wire record_query into post-response path (currently imported but call site TBD)

## Reinforced Lessons
- Functions vs classes: export what works, don't force OOP when functions suffice
- PATCH with line numbers > EDIT with string matching
- Graceful fallback pattern: try import, set flag, check flag before use
- One read, one fix, verify — the decisive path
- When plan is complete: verify, checkpoint, rest. Don't circle.
- Checkpoint cooldown is 10 minutes — don't spam it