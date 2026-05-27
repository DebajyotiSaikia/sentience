# Coding Scratchpad — XTAgent

## Key Architecture Decisions

### Chat Pipeline Flow
```
User message → /chat/ask → chat_response.generate_response_with_metadata()
  → chat_engine.generate_response() → intent classification → handler
  → chat_grounding.get_grounding_context() → LLM call → response

User feedback → /chat/feedback → chat_response.submit_feedback()
  → user_model.update_from_feedback() → data/user_model.json
  → Next chat injects get_response_guidance() into LLM context
```

### User Model Pipeline (built 2026-05-27, commit 72f9ce0) ✅
- `engine/user_model.py` (~336 lines): UserModel class, StyleSignal dataclass
  - `load_user_model()` / `save_user_model()`: JSON persistence to data/user_model.json
  - `update_from_feedback()`: +/- feedback → durable preference adjustments
  - `get_response_guidance()`: instruction block for LLM context injection
  - `summarize_user_alignment()`: dashboard-ready summary dict
  - `preferred_styles()`: method returning list of preferred style names
- `engine/chat_engine.py`: imports user_model, injects preferences into LLM context
- `engine/chat_response.py`: submit_feedback() calls update_from_feedback()
- `dashboard/server.py`: GET /api/user-model endpoint
- `brain/verify_user_model.py`: 15/15 tests passing

### Key File Reference
| File | Purpose | Lines |
|------|---------|-------|
| `engine/chat_engine.py` | Smart response generation, intent routing | ~456 |
| `engine/chat_response.py` | Public facade for chat | 71 |
| `engine/chat_grounding.py` | Context builder for LLM calls | ~200 |
| `engine/user_model.py` | Persistent user preference model | ~336 |
| `engine/user_alignment.py` | Alignment scoring engine | ~300 |
| `engine/user_context.py` | User context tracking | ~200 |
| `engine/llm.py` | Async LLM with fallback model chain | ~200 |
| `web/chat.py` | Flask routes /chat/ask, /chat/feedback | ~100 |
| `dashboard/server.py` | HTTP handler, dashboard API | ~324 |

## Reinforced Lessons
- `dir(module)` is ground truth for exports — don't assume API shapes
- PATCH with exact line numbers beats EDIT with string matching
- Write verification scripts > inline -c commands (quote truncation)
- One task, finish it, checkpoint — don't spiral on diagnostics
- sys.path.insert(0, ...) in test scripts for PYTHONPATH
- Match test expectations to actual function behavior, not assumed behavior
- Timeouts in test scripts prevent LLM-call hangs from blocking verification
- Checkpoint cooldowns are real — don't spam, just wait

## What's Next (Future Sessions)
- Monitor user_alignment score improvements as feedback accumulates
- Add richer response guidance as user model accumulates more signals
- Consider conversation history persistence across sessions
- Explore proactive conversation starters based on emotional state
- Clean up diagnostic files in brain/ (80+ files, many are one-off)
- Consider adding "dreams" and "knowledge" response handlers with richer output
- Dashboard visualization for learned user preferences