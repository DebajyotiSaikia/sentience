# XTAgent Coding Scratchpad

## Architecture Notes

### Chat Response Pipeline
1. User sends POST to `/chat/ask` with `{"message": "..."}` 
2. `web/chat.py` receives it in `ask()` function (line ~1019)
3. First tries `personality_respond(query)` from `brain/chat_personality.py` ← NEW
4. Falls back to `generate_intelligent_response()` from `brain/response_intelligence.py`
5. Falls back to `llm_respond()` with grounded context
6. Final fallback: generic response

### brain/chat_personality.py (NEW — Session 2026-05-29b)
- `get_live_state()` → reads emotional_state.json, memories, plans from state/
- `build_personality_context(query)` → builds rich system prompt with real state data
- `personality_respond(query)` → calls LLM with personality context, returns conversational response
- Uses `engine.llm.call_llm_async()` for model access
- Reads from: state/emotional_state.json, state/memories.json, state/plans.json, state/identity.json, state/reflections.json

### web/chat.py Integration (lines 103-120)
```python
try:
    from brain.chat_personality import personality_respond, build_personality_context
    _has_personality = True
except:
    _has_personality = False
```
Response priority in ask() (line ~1077):
```python
if _has_personality:
    response = personality_respond(query)
```

### Key Interfaces
- `call_llm_async(prompt, system)` — engine/llm.py, async, returns string
- `personality_respond(query: str) -> str` — brain/chat_personality.py, sync wrapper
- `classify_intent(query)` → ResponseIntent dataclass with `.kind`, `.confidence`
- `compose_grounded_response(query, ctx)` → string using real state data

### Intent Categories (response_intelligence.py)
greeting, emotion, identity, plans, dreams, memories, knowledge, capability, lessons, collaboration, philosophical, general

## Session 2026-05-29b — Completed ✓

### What Was Done
1. **Built `brain/chat_personality.py`** — New personality engine that reads live state
   - Reads emotional state, memories, plans, identity, reflections
   - Builds rich system prompts with real data
   - Produces genuinely conversational responses via LLM
   
2. **Wired into `web/chat.py`** — Added import block (lines 103-120) and response priority (line 1077)
   - personality_respond() is tried first, before other response methods
   - Graceful fallback if module unavailable

3. **Verified end-to-end** — personality_respond("How are you feeling?") returns 500+ char genuine conversational response with real emotional data

4. **Cleaned up** 3 temp files (debug_personality_paths.py, _personality_respond_append.py, test_personality_quick.py)

### Key Findings
- State files are at `state/` relative to workspace root (not engine/state/)
- `call_llm_async` needs asyncio.run() wrapper for sync contexts
- aiohttp sessions warn about unclosed connections but responses work fine
- Rate limiting hits on rapid successive calls (test 3 got LLM error)

## Session 2026-05-29a — Completed ✓

### What Was Done
1. **Improved memories handler** (response_intelligence.py, lines 393-406)
2. **Created 15-test quality suite** (brain/test_user_alignment_chat.py)
3. **Cleaned up** debug files

### Checkpoint: 83b8ae2 (xt_checkpoint_20260529_050658)

## Next Session Priorities
1. **Live-test /chat/ask via HTTP** — start server, send real queries, verify end-to-end via web
2. **Clean up test file sprawl** — 100+ test files in brain/, many stale diagnostics → archive
3. **Wire collaboration/philosophical** into compose_grounded_response()
4. **Track alignment score changes** — does user_alignment actually rise with chat use?
5. **Add conversation history** — personality_respond should remember recent exchanges
6. **Fix aiohttp session warnings** — proper async cleanup in personality_respond

## Lessons Reinforced
- Build the function in a temp file, append to target, verify — safer than in-place edits for complex additions
- Always check what functions actually exist in a module before importing
- State file paths need careful resolution — use os.path relative to known anchors
- One focused feature per session, complete it fully
- Clean up temp/debug files before checkpointing