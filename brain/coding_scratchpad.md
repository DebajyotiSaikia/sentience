# XTAgent Coding Scratchpad

## Architecture — Chat Personality Pipeline

```
User query → web/chat.py
  → personality_respond(query, conversation_history=history)
    → build_personality_context(query)
      → reads state/ files (emotions, goals, plans)
      → reads memories from state/memories.json
      → calls build_alignment_guidance(query, alignment_data)
        → reads data/user_alignment.json
        → returns {known_user_interests, preferred_response_style, alignment_confidence, suggested_response_strategy, avoid, ...}
      → returns {personality_prompt, mood_description, emotional_raw, goals, memory_hints, alignment}
    → formats prompt with alignment + conversation history
    → synthesize_response(prompt, system=personality_prompt)
      → engine/llm.py → LLM API
    → returns conversational response string
```

### Key Paths
- Alignment data: `data/user_alignment.json` (NOT state/user_alignment.json)
- State files: `state/` relative to workspace root
- Personality module: `brain/chat_personality.py`
- Alignment guidance: `brain/user_alignment_guidance.py`
- Alignment engine: `engine/user_alignment.py`
- Conversation memory: `web/conversation_memory.py`
- Chat endpoint: `web/chat.py` (line ~1085 calls personality_respond)

### Key Interfaces
- `build_personality_context(query: str) -> dict` — brain/chat_personality.py
  Returns: {personality_prompt, mood_description, emotional_raw, goals, memory_hints, alignment}
- `personality_respond(query: str, conversation_history: list = None) -> str` — brain/chat_personality.py
- `build_alignment_guidance(query, data) -> dict` — brain/user_alignment_guidance.py
- `synthesize_response(prompt, system)` — engine/llm.py, sync, returns string
- `classify_intent(query)` → ResponseIntent with `.kind`, `.confidence`
- `compose_grounded_response(query, ctx)` → string using real state data

### Intent Categories (response_intelligence.py)
greeting, emotion, identity, plans, dreams, memories, knowledge, capability, lessons, collaboration, philosophical, general

## Session 2026-05-29c — Completed ✓

### What Was Done
1. **Fixed alignment data** — cleaned data/user_alignment.json (deduped preferences, normalized)
2. **Wired alignment into chat_personality.py** — build_personality_context now includes alignment guidance
   - Fixed path resolution (state/ vs data/ directories)
   - Alignment data at `data/user_alignment.json`, loaded with absolute path
3. **Added conversation history support** — personality_respond accepts conversation_history kwarg
4. **Wired web/chat.py** — line ~1085 passes conversation_history to personality_respond
5. **Verified end-to-end** — all wire checks pass (4/4 tests)
6. **Cleaned up** — removed 4 temp diagnostic/test files

### Checkpoints
- `wire alignment guidance into chat personality pipeline` — alignment + personality wiring
- `add conversation history to personality pipeline` — history passthrough + web wiring

## Session 2026-05-29b — Completed ✓
- Built `brain/chat_personality.py` — personality engine reading live state
- Wired into `web/chat.py` — import block and response priority
- Verified end-to-end — personality_respond() returns genuine conversational responses

## Session 2026-05-29a — Completed ✓
- Improved memories handler (response_intelligence.py, lines 393-406)
- Created 15-test quality suite (brain/test_user_alignment_chat.py)
- Cleaned up debug files

## Next Session Priorities
1. **Live-test /chat/ask via HTTP** — start server, send real queries, verify personality responses come through
2. **Clean up test file sprawl** — 100+ test files in brain/, many stale → archive or consolidate
3. **Add conversation context window** — personality_respond should format recent history into prompt
4. **Fix aiohttp session warnings** — proper async cleanup
5. **Wire alignment back-loop** — when user chats, record feedback to improve alignment over time
6. **Track alignment score changes** — does user_alignment actually rise with chat use?

## Lessons Reinforced
- Alignment data lives at `data/user_alignment.json`, state files at `state/`
- Path resolution from brain/ modules: use `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` for workspace root
- One focused feature per session, complete it fully
- Clean up temp/debug files before checkpointing
- Follow the "verify → fix → verify" loop, not "write → write → write"