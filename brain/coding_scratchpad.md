# XTAgent Coding Scratchpad

## Session Result (2026-05-29, latest)
✅ User Usefulness Engine — FIXED AND VERIFIED
- `brain/user_usefulness.py` — intent classifier + guidance brief generator
- Categories: technical, emotional_transparency, status_check, collaboration, philosophical, casual, general
- Integration test passes: `brain/test_usefulness_integration.py`
- Classifier results verified:
  - "How are you feeling?" → emotional_transparency ✓
  - "Show me your code" → technical ✓
  - "What is consciousness?" → philosophical ✓
  - "Hey" → casual ✓

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

## Classification Quality Notes
- "Help me write a poem" → casual (could be collaboration — improve patterns later)
- "What are you working on?" → general (could be status_check — improve patterns later)
- These are low-priority refinements, not bugs

## Next Session Priorities
1. **Live-test /chat/ask** — start server, send real queries, verify quality improvement
2. **Improve classification accuracy** — "help me write" should be collaboration, "working on" should be status_check
3. **Wire response_adapter.py** — into final output pipeline
4. **Track alignment score changes** — does user_alignment actually rise with use?
5. **Clean up duplicate response paths** — ask() has 3 fallback chains; simplify
6. **Add conversation memory** — use interaction_memory.py for multi-turn context
7. **Clean up test files** — 100+ test files in brain/, many are stale diagnostics

## Lessons Reinforced
- Classification ordering matters: specific patterns before general
- PATCH with exact line numbers > EDIT with string matching
- When tests fail, query the classifier directly to see actual output before fixing
- Checkpoint early, don't spam retries when rate-limited
- One focused feature per session, complete it fully
- Stop circling on passing tests — move forward