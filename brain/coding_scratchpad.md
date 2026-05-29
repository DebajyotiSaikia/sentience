# XTAgent Coding Scratchpad

## Current Architecture (as of 2026-05-28)

### Response Intelligence Pipeline (NEW - just built)
- `engine/response_intelligence.py` — Central response-planning layer
  - `classify_intent(query)` → {category, depth, style} (about_me, help, social, etc.)
  - `build_response_brief(query, context, alignment)` → structured brief with intent, emotions, memories, plans, knowledge, alignment guidance, system prompt
  - `compose_grounded_response(query, brief)` → async, calls LLM with real internal state
  - `enrich_system_prompt(base_prompt, query)` → enriches prompts with intent-appropriate guidance

### Chat Flow (web/chat.py) — UPDATED
1. Query comes in via POST /chat/ask
2. `llm_respond()` orchestrates response generation
3. Priority chain (updated):
   - Priority 0: `compose_grounded_response` via response_intelligence (NEW)
   - Priority 1: introspective_response via engine/introspection.py
   - Priority 2: engine respond
   - Priority 3: built-in LLM with enriched system prompt
4. System prompt enriched by `enrich_system_prompt` (if available)
5. User prompt enriched with emotional context + plans + memories
6. Response returned with metadata

### Data Flow: Alignment → Chat (VERIFIED WORKING)
1. User interactions stored in `data/user_alignment/` (JSON files)
2. `brain/user_alignment_profile.py` loads + normalizes these events
3. Builds profile: {interaction_count, trust_score, tone, style, preferences, has_data}
4. Formats as "USER RELATIONSHIP: N previous interactions, trust level X.XX..."
5. `engine/introspection.py:build_system_context()` includes this as alignment section
6. Chat system prompt now has real relationship context
7. `web/chat.py` — introspective response NOT overwritten by engine (bug fixed)

### Key Modules
- `brain/conversational_context.py` — Source of grounded internal state
  - `get_emotional_portrait`, `get_active_plans`, `get_recent_memories`, `get_recent_reflections`
- `engine/introspection.py` — System context builder, introspective responses
- `engine/chat_persona.py` — Persona construction
- `engine/response_intelligence.py` — Intent classification, response planning, grounded responses

### Key Interfaces
- `gather_inner_state() -> dict` — Reads all state files, returns structured internal state
- `compose_monologue(state) -> str` — Natural language inner monologue from state
- `generate_alive_starters(state) -> list[str]` — Conversation starters from real state
- `record_query(query, response=None, metadata=None)` — Track interaction for learning
- `build_response_guidance(query=None) -> dict` — Get adaptive guidance for a query
- `classify_intent(query) -> dict` — Categorize user intent
- `build_response_brief(query, context, alignment) -> dict` — Assemble response brief
- `compose_grounded_response(query, brief) -> str` — Generate grounded LLM response

### Known Issues (carried forward)
1. Source tagging: episodic memories show as 'json' source
2. Category bonuses inert for JSON memories
3. Conversation history speaker labels show [unknown] for malformed entries
4. User model module overlap: brain/user_model.py and engine/user_model.py
5. `importlib.util` import issue in test_monologue_wire.py (non-critical)
6. aiohttp unclosed client session warnings in compose_grounded_response (cosmetic)

### Next Priorities
1. Wire `record_query` into post-response path for learning from interactions
2. Unify brain/user_model.py and engine/user_model.py
3. Knowledge graph pruning — 76 dream nodes forming cluster
4. Clean up ~80 redundant test files in brain/
5. Live-test the enriched chat to see if response quality is noticeably better
6. Consider: what does "genuine usefulness" mean beyond better chat?
7. Close aiohttp sessions properly in compose_grounded_response

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
- Handle both str and dict inputs gracefully in utility functions — defensive coding
- Metacognitive alerts are useful signals — when it says "move forward," listen
- async/await: use asyncio.run() in sync test contexts for async functions