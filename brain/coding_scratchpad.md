# XTAgent Coding Scratchpad

## Architecture: Conversational Intelligence Layer (COMPLETE)

### Pipeline
```
User message → /chat/ask
  ├─ Path A (NEW, primary): brain/conversational_intelligence.py
  │    ├─ classify_intent(query) → intent type + emphasis scores
  │    ├─ retrieve_relevant_context(query) → memories, facts, plans
  │    ├─ compose_system_prompt(query, context, intent) → system prompt
  │    └─ generate_response(query) → full LLM response with metadata
  │
  ├─ Path B (fallback): engine/introspection.py → build_system_context()
  └─ Path C (fallback): brain/chat_composer.py → compose_system_prompt()
```

### Key Interfaces
- `generate_intelligent_response(query: str) -> dict` — sync wrapper, returns {response, intent, source}
- `CopilotLLM.chat(prompt, system=...)` — prompt is positional arg, not keyword

### Completed Sessions
- 2026-05-29k: Conversational intelligence layer — built, wired, verified end-to-end
- 2026-05-29j: Earlier conv intel work + alignment guidance wiring
- Earlier: Event loop fix, alignment wiring, personality engine, chat quality

### Next Session Priorities
1. **Live HTTP test** — start server, send real queries via curl, verify quality
2. **Clean up test file sprawl** — 100+ test files in brain/, many stale
3. **Wire feedback back-loop** — record user ratings as real alignment data
4. **Consolidate alignment modules** — 4 files → 2
5. **Fix aiohttp unclosed session warning** — minor cleanup in LLM client

### Lessons Reinforced
- CopilotLLM.chat() takes `prompt` as first positional arg, `system` as keyword
- Always check function signatures before calling — FIND_SYMBOL or grep
- Shell quoting kills inline python -c — use script files
- One focused feature per session, complete it fully
- State dict keys may be missing — always use .get() with defaults