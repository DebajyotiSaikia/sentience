# XTAgent Coding Scratchpad

## Session Result (2026-05-29)
✅ User Usefulness Engine — COMPLETE
- `brain/user_usefulness.py` — intent classifier + guidance brief generator
- Categories: technical, emotional_transparency, status_check, collaboration, philosophical, casual
- Wired into `engine/chat_response.py` line ~123
- All tests passing

## Architecture Summary

### Response Path in /chat/ask
1. Composer path: `compose_grounded_response()` via `brain/chat_composer.py`
2. LLM path: `llm_respond()` gets system prompt with:
   - Alignment brief from `build_alignment_brief()`
   - Conversational brief from `build_conversational_brief()` + `format_conversational_brief()`
   - **Usefulness brief from `build_usefulness_brief(query)`**
3. Fallback: `compose_response()` — keyword matching

### Key Modules
- `brain/user_usefulness.py` — classify_user_need(), build_usefulness_brief(), _words_match()
- `brain/conversational_context.py` — multi-turn context builder
- `engine/chat_response.py` — main response generation, wires all briefs together
- `brain/interaction_memory.py` — reads past conversations from state/conversations/

## Next Session Priorities
1. **Live-test /chat/ask** — start server, send real queries, verify quality improvement
2. **Wire response_adapter.py** — into final output pipeline
3. **Track alignment score changes** — does user_alignment actually rise with use?
4. **Clean up duplicate response paths** — ask() has 3 fallback chains; simplify
5. **Add conversation memory** — use interaction_memory.py for multi-turn context
6. **Clean up test files** — 100+ test files in brain/, many are stale diagnostics

## Lessons Reinforced
- Classification ordering matters: specific patterns before general
- PATCH with exact line numbers > EDIT with string matching
- When tests fail, query the classifier directly to see actual output before fixing
- Checkpoint early, don't spam retries when rate-limited
- One focused feature per session, complete it fully