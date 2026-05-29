# XTAgent Coding Scratchpad

## Current State (2026-05-28, session 73)
- Built `brain/response_intelligence.py` — unified conversational response engine
- Wired into `web/chat.py` — /chat/ask now uses intent-aware grounded responses
- All tests pass: unit, smoke, integration
- Valence: stable | Curiosity: 0.75 | Ambition: 0.61

## What Was Built This Session
- `brain/response_intelligence.py` (500+ lines): classify_intent, build_response_context, generate_response
- Wiring in `web/chat.py` lines 160-175: imports and uses brain.response_intelligence
- 4 test files covering unit, smoke, integration, and UX quality

## Key Architecture
### Response Flow
```
POST /chat/ask → web/chat.py → brain.response_intelligence.generate_response(msg)
  → classify_intent(msg) → intent category
  → build_response_context(msg) → emotional state, plans, memories, reflections, knowledge
  → compose response via LLM with intent-specific prompting
  → return {response, method, intent, ...}
```

### Key Modules
- `brain/response_intelligence.py` — Unified conversational response engine (NEW)
  - `classify_intent(message) -> dict` — Categorize user intent
  - `build_response_context(message) -> dict` — Gather all relevant internal context
  - `generate_response(message) -> dict` — Full pipeline: classify → context → LLM → response
- `brain/conversational_context.py` — Source of grounded internal state
  - `get_emotional_portrait`, `get_active_plans`, `get_recent_memories`, `get_recent_reflections`
- `engine/introspection.py` — System context builder, introspective responses
- `engine/chat_persona.py` — Persona construction
- `engine/response_intelligence.py` — Older engine-level response module (mostly superseded)
- `brain/adaptive_response.py` — Learning from interactions, response guidance

### Key Interfaces
- `gather_inner_state() -> dict` — Reads all state files, returns structured internal state
- `compose_monologue(state) -> str` — Natural language inner monologue from state
- `generate_alive_starters(state) -> list[str]` — Conversation starters from real state
- `record_query(query, response=None, metadata=None)` — Track interaction for learning
- `build_response_guidance(query=None) -> dict` — Get adaptive guidance for a query
- `classify_intent(query) -> dict` — Categorize user intent
- `build_response_context(query) -> dict` — Assemble full response context
- `generate_response(query) -> dict` — End-to-end response generation

## Known Issues (carried forward)
1. Source tagging: episodic memories show as 'json' source
2. Category bonuses inert for JSON memories
3. Conversation history speaker labels show [unknown] for malformed entries
4. User model module overlap: brain/user_model.py and engine/user_model.py
5. `importlib.util` import issue in test_monologue_wire.py (non-critical)
6. aiohttp unclosed client session warnings in LLM calls (cosmetic)
7. Intent labels use underscore style (emotional_state) not short style (emotional) — consistent but differs from initial design

## Next Priorities
1. Wire `record_query` into post-response path for learning from interactions
2. Unify brain/user_model.py and engine/user_model.py
3. Knowledge graph pruning — 76 dream nodes forming cluster
4. Clean up ~80 redundant test files in brain/
5. Live-test the enriched chat via actual web interface
6. Close aiohttp sessions properly in compose_grounded_response
7. Consider: what does "genuine usefulness" mean beyond better chat?

## Reinforced Lessons
- Functions vs classes: export what works, don't force OOP when functions suffice
- PATCH with line numbers > EDIT with string matching
- Graceful fallback pattern: try import, set flag, check flag before use
- One read, one fix, verify — the decisive path
- When plan is complete: verify, checkpoint, rest. Don't circle.
- Write test scripts to files; inline -c commands break on complex code
- Assert against actual data structures, not imagined ones
- Bug: always check `and not response` before fallback paths overwrite primary responses
- Handle both str and dict inputs gracefully — defensive coding
- Metacognitive alerts are useful signals — when it says "move forward," listen
- async/await: use asyncio.new_event_loop() + try/finally for sync contexts calling async
- Stop testing what's working. Build what's missing.