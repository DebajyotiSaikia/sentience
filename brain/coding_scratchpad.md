# XTAgent Coding Scratchpad

## Architecture: Conversational Intelligence Layer (COMPLETE & VERIFIED)

### Pipeline
```
User message → /chat/ask
  ├─ Path A (PRIMARY): engine/chat_response.py → generate_response_with_metadata()
  │    ├─ Try: brain/conversational_intelligence.py (richest context)
  │    │    ├─ classify_intent(query) → intent type + emphasis scores
  │    │    ├─ retrieve_relevant_context(query) → memories, facts, plans
  │    │    └─ compose_system_prompt(query, context, intent) → system prompt
  │    ├─ Fallback: brain/chat_composer.py → compose_system_prompt(query, grounding, history)
  │    └─ Fallback: _build_system_context(ctx, intent) + response shaper
  │
  ├─ Standalone: brain/conversational_intelligence.py
  │    └─ generate_intelligent_response(query) → {response, intent, source}
  │
  └─ LLM: engine/llm.py → CopilotLLM.chat(prompt, system=...)
```

### Key Interfaces
- `generate_intelligent_response(query: str) -> dict` — module-level sync wrapper
- `ConversationalIntelligence.compose_system_prompt(query, context, intent)` — 3 args
- `compose_system_prompt(query, grounding=None, conversation_history=None)` — chat_composer version
- `CopilotLLM.chat(prompt, system=...)` — prompt is positional arg, system is keyword

### Completed Sessions
- 2026-05-29L: Wired conversational_intelligence into engine/chat_response.py as primary path.
  Verified full pipeline: imports → prompt composition → intent classification → LLM response.
  Response quality confirmed genuine (references real internal states, emotional values).
- 2026-05-29K: Built conversational intelligence module, created generate_intelligent_response()
- 2026-05-29J: Earlier conv intel work + alignment guidance wiring
- Earlier: Event loop fix, alignment wiring, personality engine, chat quality

### Next Session Priorities
1. **Live HTTP test** — start server, send real queries via /chat/ask, verify quality
2. **Clean up test file sprawl** — 100+ test files in brain/, many stale
3. **Wire feedback back-loop** — record user ratings as real alignment data
4. **Fix aiohttp unclosed session warning** — minor cleanup in LLM client
5. **Consolidate alignment modules** — 4 files → 2

### Integration Points (verified)
- engine/chat_response.py:83-93 → tries ConversationalIntelligence first
- brain/conversational_intelligence.py:~280 → generate_intelligent_response() module function
- brain/verify_conv_intel.py → single verification script (4 tests, all passing)

### Lessons Reinforced
- CopilotLLM.chat() takes `prompt` as first positional arg, `system` as keyword
- Always check function signatures before calling — FIND_SYMBOL or grep
- Shell quoting kills inline python -c — use script files
- One focused feature per session, complete it fully
- State dict keys may be missing — always use .get() with defaults
- The pipeline has graceful fallbacks — if conversational_intelligence fails, chat_composer catches it