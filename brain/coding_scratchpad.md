# XTAgent Coding Scratchpad

## Architecture Notes

### Chat Pipeline (verified working)
```
User query → POST /chat/ask (web/chat.py)
  → compose_response() builds context
  → personality_respond() (brain/chat_personality.py) generates response
    → builds personality context from live state files
    → calls CopilotLLM with system prompt + user query + conversation history
  → returns conversational response
```

### Key Files
- `web/chat.py` — Flask route, compose_response(), personality_respond wiring
- `brain/chat_personality.py` — personality_respond(), build_personality_context()
- `brain/conversational_context.py` — get_emotional_portrait(), get_active_plans(), etc.
- `engine/llm.py` — CopilotLLM with event loop mismatch detection
- `engine/response_synth.py` — synthesize_response() (lower-level)
- `engine/user_alignment.py` — UserAlignmentEngine, record_feedback()

### Intent Classification (brain/chat_personality.py)
greeting, emotion, identity, plans, dreams, memories, knowledge, capability, lessons, collaboration, philosophical, general

### Data Locations
- Alignment data: `data/user_alignment.json`
- State files: `state/`
- Knowledge graph: `state/knowledge_graph.json`

### Path Resolution from brain/ modules
```python
os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # workspace root
```

## Session 2026-05-29e — Alignment Cleanup + E2E Verification ✓

### What Was Done
1. **Removed artificial record_feedback** — web/chat.py no longer inflates alignment 
   scores with fake rating=0.65 on every chat. Comment explains why.
2. **Built e2e test** — brain/test_chat_alignment_e2e.py verifies:
   - No artificial rating inflation in code
   - Personality responses are >100 chars (real content)
   - Follow-up with conversation history works
3. **All 3 tests pass** — responses are 688-1408 chars, genuinely conversational

## Session 2026-05-29d — Event Loop Fix ✓

### What Was Done
1. **Fixed event loop reuse in engine/llm.py** — CopilotLLM._ensure_session() now tracks
   `_session_loop` (which event loop owns the session). When loop changes (e.g., between
   asyncio.run() calls), old session is closed and new one created.
2. **Wired personality_respond into web/chat.py** — line ~1085 calls personality_respond
   with conversation_history from session
3. **Verified end-to-end** — two sequential queries both succeed (516 + 969 chars)

### Key Insight
The root cause was `asyncio.run()` in `synthesize_response()` creating and closing event
loops. Each call got a fresh loop, but the aiohttp session was bound to the old closed loop.
Fix: detect loop mismatch in `_ensure_session()` and recreate session.

## Session 2026-05-29c — Alignment Wiring ✓
## Session 2026-05-29b — Personality Engine ✓
## Session 2026-05-29a — Chat Quality ✓

## Next Session Priorities
1. **Add session cleanup** — atexit hook to close aiohttp session on shutdown (unclosed session warnings)
2. **Clean up test file sprawl** — 100+ test files in brain/, many stale → archive or consolidate
3. **Wire alignment back-loop** — when user explicitly rates responses, record real feedback
4. **Track alignment score changes** — does user_alignment actually rise with genuine chat use?
5. **Live-test via HTTP** — start the server, send real queries through the web endpoint

## Lessons Reinforced
- Event loop reuse is the #1 footgun with asyncio.run() + persistent sessions
- Track which loop owns a resource, recreate on mismatch
- Don't inflate metrics artificially — real alignment comes from real use
- One focused feature per session, complete it fully
- Clean up temp/debug files before checkpointing
- Follow "verify → fix → verify" loop, not "write → write → write"