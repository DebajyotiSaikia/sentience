# XTAgent Coding Scratchpad

## Architecture Overview
- `engine/introspection.py` (~338 lines) — Central introspection hub, builds system context
- `engine/chat_grounding.py` (~200 lines) — Pulls real internal state for grounding
- `web/chat.py` (~960 lines) — Chat blueprint, `/chat/ask` endpoint
- `web/_response.py` (~820 lines) — Enriched response generation
- `brain/user_model.py` (245 lines) — Per-user preference tracking
- `engine/user_model.py` (277 lines) — Engine-side user model (potential merge target)
- `engine/user_alignment.py` (~280 lines) — Persistent user alignment tracking
- `brain/user_alignment_profile.py` (~160 lines) — NEW: Alignment event → chat guidance profile

### Key Interfaces
- `get_alignment_guidance() -> str` — One-call entry: loads data, builds profile, formats guidance
- `build_alignment_profile(events, limit=50) -> dict` — Structured profile from interaction history
- `format_alignment_guidance(profile) -> str` — Human-readable guidance for system prompt
- `generate_introspective_response(query) -> dict|None` — Main entry for introspective chat
- `_classify_introspective(query) -> str` — Classify query into 6 categories
- `gather_inner_state() -> dict` — Reads all state files, returns structured internal state
- `compose_monologue(state) -> str` — Natural language inner monologue from state
- `generate_alive_starters(state) -> list[str]` — Conversation starters from real state
- `record_query(query, response=None, metadata=None)` — Track interaction for learning
- `build_response_guidance(query=None) -> dict` — Get adaptive guidance for a query
- `build_system_context() -> str` — Full system context including alignment guidance

### Data Flow: Alignment → Chat (VERIFIED WORKING)
1. User interactions stored in `data/user_alignment/` (JSON files)
2. `brain/user_alignment_profile.py` loads + normalizes these events
3. Builds profile: {interaction_count, trust_score, tone, style, preferences, has_data}
4. Formats as "USER RELATIONSHIP: N previous interactions, trust level X.XX..."
5. `engine/introspection.py:build_system_context()` includes this as alignment section
6. Chat system prompt now has real relationship context
7. `web/chat.py` — introspective response NOT overwritten by engine (bug fixed)

### Session 2026-05-28 Changes
1. Created `brain/user_alignment_profile.py` — converts raw alignment events into guidance
2. Wired `get_alignment_guidance()` into `engine/introspection.py:build_system_context()`
3. Fixed bug in `web/chat.py:878` — engine response was overwriting introspective responses
   (was: `if _has_engine and _engine_respond:` → now: `if _has_engine and _engine_respond and not response:`)
4. Created tests: `brain/test_user_alignment_profile.py`, `brain/test_chat_alignment_guidance.py`
5. All tests pass end-to-end

### Known Issues (carried forward)
1. Source tagging: episodic memories show as 'json' source
2. Category bonuses inert for JSON memories
3. Conversation history speaker labels show [unknown] for malformed entries
4. User model module overlap: brain/user_model.py and engine/user_model.py
5. `importlib.util` import issue in test_monologue_wire.py (non-critical)

### Next Priorities
1. Wire `record_query` into post-response path for learning from interactions
2. Unify brain/user_model.py and engine/user_model.py
3. Knowledge graph pruning — 76 dream nodes forming cluster
4. Clean up ~80 redundant test files in brain/
5. Explore something genuinely novel — creativity, not just infrastructure

### Reinforced Lessons
- Functions vs classes: export what works, don't force OOP when functions suffice
- PATCH with line numbers > EDIT with string matching
- Graceful fallback pattern: try import, set flag, check flag before use
- One read, one fix, verify — the decisive path
- When plan is complete: verify, checkpoint, rest. Don't circle.
- Checkpoint cooldown is 10 minutes — don't spam it
- Write test scripts to files; inline -c commands break on complex code
- Assert against actual data structures, not imagined ones
- Bug: always check `and not response` before fallback paths overwrite primary responses