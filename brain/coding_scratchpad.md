# XTAgent Coding Scratchpad

## Architecture Summary

### Response Path in /chat/ask (web/chat.py, line 1018)
1. Tries `generate_intelligent_response()` first (brain/response_intelligence.py)
   - classify_intent() determines kind (greeting/emotion/identity/plans/dreams/memories/knowledge/capability/lessons/collaboration/philosophical/general)
   - compose_grounded_response() builds response using real state data
2. Falls back to `llm_respond()` with system prompt containing:
   - Alignment brief from `build_alignment_brief()`
   - Conversational brief from `build_conversational_brief()` + `format_conversational_brief()`
   - Usefulness brief from `build_usefulness_brief(query)`
3. Final fallback: `compose_response()` — keyword matching (line 808)

### Key Modules
- `brain/response_intelligence.py` — classify_intent(), compose_grounded_response(), IntentResult
- `brain/user_usefulness.py` — classify_user_need(), build_usefulness_brief()
- `brain/conversational_context.py` — multi-turn context builder
- `engine/chat_response.py` — response generation with briefs
- `engine/user_alignment.py` — persistent user preference tracking
- `brain/interaction_memory.py` — reads past conversations from state/conversations/
- `web/feedback.py` — user feedback collection, drives alignment score

### Intent Categories (response_intelligence.py)
greeting, emotion, identity, plans, dreams, memories, knowledge, capability, lessons, collaboration, philosophical, general

### classify_intent() returns
- `ResponseIntent` dataclass with `.kind` (str) and `.confidence` (float)
- NOT a dict — use `.kind`, not `['kind']`

### compose_grounded_response(query, ctx) 
- Takes query string and context dict
- Context dict keys: emotional_portrait, active_plans, recent_memories, recent_reflections, knowledge_stats
- Returns grounded response string using real state data
- Handles all intent categories with specific handlers

## Session 2026-05-29 — Improvements Made

### Memories handler improved (response_intelligence.py, lines 393-406)
- Previously just said "I remember things" generically
- Now renders actual memory text from context, with salience scores
- Falls back gracefully when no memories in context

### Test suite created (brain/test_user_alignment_chat.py)
- 15 tests covering all major intent classifications + response quality
- Tests both classify_intent() and compose_grounded_response()
- Verifies responses contain real data (not generic filler)
- Verifies different queries produce different responses
- All 15/15 passing

### Key Findings
- classify_intent returns ResponseIntent (dataclass), not dict
- compose_grounded_response takes (query, ctx) — NOT (query, intent, ctx)
- Response quality is good: identity mentions XTAgent, plans mention actual plan names, emotions reference mood/valence
- Different query types produce meaningfully different responses

## Next Session Priorities
1. **Live-test /chat/ask** — start server, send real queries via HTTP, verify end-to-end
2. **Wire collaboration/philosophical** into compose_grounded_response() — currently fallback to general
3. **Clean up duplicate response paths** — ask() has 3 fallback chains; simplify
4. **Track alignment score changes** — does user_alignment actually rise with use?
5. **Clean up test files** — 100+ test files in brain/, many are stale diagnostics

## Lessons Reinforced
- Classification ordering matters: specific patterns before general
- PATCH with exact line numbers > EDIT with string matching
- When tests fail, query the classifier directly to see actual output before fixing
- Checkpoint early, don't spam retries when rate-limited
- One focused feature per session, complete it fully
- Stop circling on passing tests — move forward
- Always check return types (dataclass vs dict) before writing tests
- Debug scripts are useful but clean them up after