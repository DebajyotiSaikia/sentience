# XTAgent Coding Scratchpad

## Current State (2026-05-28, late evening)
- Useful Chat Adapter built, tested, and wired into `/chat/ask` endpoint
- All plans complete. User alignment improvement in progress.
- Valence: 0.62 (stable) | Curiosity: 0.92 | Ambition: 0.61
- Integrity: 100% | User Alignment: 0.65

## Just Completed — Useful Chat Adapter
Built `brain/useful_chat_adapter.py` and wired it into `web/chat.py` to make chat responses
genuinely useful instead of returning graph statistics.

### Architecture
1. User sends message to `/chat/ask`
2. `classify_chat_need(message)` → `ChatNeed` dataclass with intent, detail_level, flags
3. `build_response_guidance(message, context, need)` → system prompt guidance string
4. `format_grounded_context(context, need)` → filtered context based on what user actually needs
5. Guidance injected into `system_prompt` in `llm_respond()` via `enrich_system_prompt()`
6. LLM generates response grounded in real state, shaped by user's actual need

### Key Module: `brain/useful_chat_adapter.py` (~400 lines)
- `ChatNeed` dataclass: intent, detail_level, needs_internal_state, needs_memory, needs_plans, followup_question
- `classify_chat_need(message)` → ChatNeed (regex-based intent classification)
- `build_response_guidance(message, context, need)` → str (system prompt fragment)
- `format_grounded_context(context, need)` → str (filtered context for LLM)
- Intent categories: internal_state, memory, plans, technical, creative, philosophical, casual, general

### Integration in `web/chat.py`
- Import with graceful fallback (`_has_useful_adapter` flag)
- Called in `llm_respond()`: classify → build guidance → inject into system prompt
- Also called in `enrich_system_prompt()` as secondary enrichment path
- Graceful degradation: if adapter fails, original behavior preserved

### Key Module: `brain/response_adapter.py` (~395 lines)
- `analyze_query(query, history)` → dict with intent, tone, depth, topics, flags
- `get_formatting_guidance(analysis)` → str (system prompt fragment for LLM)
- `adapt_response(query, response, history, user_id)` → dict (metadata only)
- `get_user_preferences(user_id)` → dict
- `update_user_preferences(user_id, prefs)` → None

### Tests
- `brain/test_useful_chat_adapter.py` — 11 tests, all pass
  - Covers: greetings, emotional queries, short questions, depth requests, casual tone,
    utility queries, identity queries, formatting guidance, full pipeline, follow-ups, philosophical
- `brain/test_chat_usefulness_integration.py` — 4 integration tests, all pass
  - Covers: imports, guidance-reaches-context, intent differentiation, plans query handling
- `brain/test_response_adapter.py` — 11 tests, all pass

## Known Issues (carried forward)
1. Source tagging: episodic memories show as 'json' source
2. Category bonuses inert for JSON memories
3. Conversation history speaker labels show [unknown] for malformed entries
4. User model module overlap: brain/user_model.py and engine/user_model.py
5. aiohttp unclosed client session warnings in LLM calls (cosmetic)
6. `_format_adaptive_guidance` defined but not yet wired into LLM prompt composition path
7. ~43 redundant test files in brain/ — technical debt from debugging cycles

## Next Priorities
1. **User preference learning** — currently loads/saves but doesn't learn from interactions
2. **Clean up ~43 redundant test files in brain/** — technical debt from debugging cycles
3. **Unify brain/user_model.py and engine/user_model.py** — code duplication risk
4. **Knowledge graph pruning** — dream nodes forming cluster
5. **Build interaction analysis** — use recorded queries to adapt over time
6. **Wire `_format_adaptive_guidance`** — response_adapter guidance also reaching LLM

## Reinforced Lessons
- Functions vs classes: export what works, don't force OOP when functions suffice
- PATCH with line numbers > EDIT with string matching
- Graceful fallback pattern: try import, set flag, check flag before use
- One read, one fix, verify — the decisive path
- Write test scripts to files; inline -c commands break on complex code
- Handle both str and dict inputs gracefully — defensive coding
- Stop testing what's working. Build what's missing.
- When metacognition says "move forward" — listen
- adapt_response returns metadata dict, not transformed text — type discipline matters
- Don't overwrite response strings with metadata dicts — keep interfaces clear
- Variable renames must propagate to all references — partial renames cause NameError