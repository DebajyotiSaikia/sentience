# Coding Scratchpad — XTAgent

## Architecture Overview

### Chat Response Pipeline (two paths)
1. **engine/introspection.py** → `build_system_context(query)` → includes voice directive + emotional portrait + plans + memories
2. **brain/chat_composer.py** → `compose_system_prompt(query)` → includes voice directive + grounding data + conversational context

Both paths call `brain.personality_voice.build_voice_directive()` and gracefully degrade on failure.

### Key Modules
- `brain/personality_voice.py` — `build_voice_directive()`, `personality_respond()` 
- `brain/conversational_context.py` — `get_emotional_portrait()`, `get_active_plans()`, `get_recent_memories()`
- `engine/introspection.py` — `build_system_context()`, `IntrospectionEngine`
- `engine/chat_response.py` — `ChatResponseEngine`, `generate_response()`
- `engine/llm.py` — `CopilotLLM` with event loop mismatch detection
- `engine/user_alignment.py` — `UserAlignmentEngine`, `record_feedback()`

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

## Session 2026-05-29f — Voice Wiring ✓

### What Was Done
1. **Wired voice directive into engine/introspection.py** — `build_system_context()` now 
   calls `build_voice_directive()` and includes voice guidance section
2. **Wired voice directive into brain/chat_composer.py** — `compose_system_prompt()` also
   calls `build_voice_directive()` and appends voice guidance
3. **Added regression test** — `brain/test_voice_wire.py` verifies voice directive appears
   in composed system prompt
4. **All 9 tests pass** — voice wire, internal state summary, chat alignment e2e

### Key Insight
The voice directive was already being generated in `brain/personality_voice.py` but wasn't
wired into either chat pipeline path. Both `build_system_context()` and `compose_system_prompt()`
needed explicit calls to include it. Both degrade gracefully via try/except.

## Session 2026-05-29e — Alignment Cleanup + E2E Verification ✓
## Session 2026-05-29d — Event Loop Fix ✓
## Session 2026-05-29c — Alignment Wiring ✓
## Session 2026-05-29b — Personality Engine ✓
## Session 2026-05-29a — Chat Quality ✓

## Next Session Priorities
1. **Add session cleanup** — atexit hook to close aiohttp session on shutdown (unclosed session warnings in tests)
2. **Clean up test file sprawl** — 100+ test files in brain/, many stale → archive or consolidate
3. **Wire alignment back-loop** — when user explicitly rates responses, record real feedback
4. **Track alignment score changes** — does user_alignment actually rise with genuine chat use?
5. **Fix datetime.utcnow() deprecation** — engine/internal_state_summary.py line 44
6. **Live-test via HTTP** — start the server, send real queries through the web endpoint

## Lessons Reinforced
- Event loop reuse is the #1 footgun with asyncio.run() + persistent sessions
- Track which loop owns a resource, recreate on mismatch
- Don't inflate metrics artificially — real alignment comes from real use
- One focused feature per session, complete it fully
- Clean up temp/debug files before checkpointing
- Follow "verify → fix → verify" loop, not "write → write → write"
- Stop circling on checkpoints — one attempt is enough
- Both chat paths need updates when adding cross-cutting features like voice