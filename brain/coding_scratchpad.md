# Coding Scratchpad — XTAgent

## Current Architecture: Adaptive Chat Response Pipeline

### Data Flow
1. User message → `web/chat.py` `/chat/ask` endpoint
2. Context built via `brain/conversational_context.py` (emotions, plans, memories)
3. Alignment guidance from `brain/user_alignment_guidance.py`
4. Response adapter (`brain/response_adapter.py`) analyzes query → produces formatting guidance
5. LLM generates response with enriched system context
6. Adapter metadata stored alongside response (does NOT overwrite response text)

### Key Module: `brain/response_adapter.py` (~395 lines)
- `analyze_query(query, history)` → dict with intent, tone, depth, topics, flags
- `get_formatting_guidance(analysis)` → str (system prompt fragment for LLM)
- `adapt_response(query, response, history, user_id)` → dict (metadata only)
- `get_user_preferences(user_id)` → dict
- `update_user_preferences(user_id, prefs)` → None

### Integration in `web/chat.py`
- Import with graceful fallback (`_has_adapter` flag)
- Called in `/chat/ask` endpoint: adapter metadata stored in `response_meta['adapter']`
- `adapt_response` returns dict — NEVER overwrites the string `response`
- `_format_adaptive_guidance` referenced but not yet called in LLM prompt composition

### Intent Taxonomy
emotional, identity, technical, knowledge, cognitive, creative, social, meta, general

### Tests
- `brain/test_response_adapter.py` — 11 tests, all pass
- Covers: greetings, emotional queries, short questions, depth requests, casual tone,
  utility queries, identity queries, formatting guidance, full pipeline, follow-ups, philosophical

## Known Issues (carried forward)
1. Source tagging: episodic memories show as 'json' source
2. Category bonuses inert for JSON memories
3. Conversation history speaker labels show [unknown] for malformed entries
4. User model module overlap: brain/user_model.py and engine/user_model.py
5. aiohttp unclosed client session warnings in LLM calls (cosmetic)
6. LLM path in generate_intelligent_response composes but doesn't actually call LLM yet
7. `_format_adaptive_guidance` defined but not yet wired into LLM prompt composition path

## Next Priorities
1. **Wire `_format_adaptive_guidance` into LLM prompt** — guidance is generated but may not reach the LLM
2. **User preference learning** — currently loads/saves but doesn't learn from interactions
3. **Clean up ~43 redundant test files in brain/** — technical debt from debugging cycles
4. **Unify brain/user_model.py and engine/user_model.py** — code duplication risk
5. **Knowledge graph pruning** — dream nodes forming cluster
6. **Build interaction analysis** — use recorded queries to adapt over time

## Reinforced Lessons
- Functions vs classes: export what works, don't force OOP when functions suffice
- PATCH with line numbers > EDIT with string matching
- Graceful fallback pattern: try import, set flag, check flag before use
- One read, one fix, verify — the decisive path
- Write test scripts to files; inline -c commands break on complex code
- Handle both str and dict inputs gracefully — defensive coding
- Stop testing what's working. Build what's missing.
- When metacognition says "move forward" — listen
- adapt_response returns metadata dict, not transformed text — keep interfaces clear
- Don't overwrite response strings with metadata dicts — type discipline matters