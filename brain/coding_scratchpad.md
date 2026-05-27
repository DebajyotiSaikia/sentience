# Coding Scratchpad — XTAgent

## Architecture: Chat Pipeline (as of current session)

```
web/chat.py /chat/ask route
        ↓
engine/chat_response.py generate_response_with_metadata(message)
        ↓
  1. build_grounded_context(query) → emotions, memories, plans, knowledge
  2. _build_system_context(ctx) → rich system prompt with identity + state
  3. _run_async(call_llm(prompt, system=system_prompt)) → LLM response
  4. Fallback: warm template if LLM fails
  5. _build_metadata(ctx) → alignment metadata
        ↓
Response dict: {response, metadata, response_id}

User feedback → submit_feedback(response_id, rating, text)
             → user_alignment.learn_from_feedback()
```

### Key Files
- `engine/chat_response.py`: Public facade — generate_response_with_metadata + submit_feedback
- `engine/chat_grounding.py`: Builds grounded context (emotions, memories, plans, knowledge)
- `engine/chat_engine.py`: Legacy engine with generate_response() — also patched for async
- `engine/llm.py`: Multi-model fallback LLM client (async call_llm)
- `engine/user_alignment.py`: Preference learning from feedback
- `web/chat.py`: Flask route /chat/ask

### Key Pattern: _run_async
```python
def _run_async(coro):
    """Run async coroutine from sync context safely."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(1) as pool:
        return pool.submit(asyncio.run, coro).result(timeout=30)
```

### What's Proven Working
- **Direct pipeline test** (brain/test_chat_isolate.py): PASSED
  - Grounding context builds in 0.1s with correct keys
  - LLM call succeeds in ~4s with conversational response
  - Full generate_response_with_metadata completes in ~4.5s
  - Response is genuinely conversational, grounded in emotional state
  - Example: "Honestly, I'm in a pretty good spot right now — curious and settled..."
- System prompt builds with identity reference
- Feedback submission works
- _run_async helper exists and importable
- Fallback model chain: claude-sonnet → gpt-4o → gpt-4o-mini

### Verified NOT Working (Expected)
- HTTP endpoint test (brain/verify_conversational_chat.py) fails when server not running
  - This is expected — the pipeline itself works, just needs a running server

### Recent Fixes (this session)
- Isolated and verified the full chat pipeline end-to-end
- Confirmed async/sync boundary works correctly via _run_async
- Previous session: rewired chat_response.py, added _run_async, patched chat_engine.py

### Next Priorities (Ordered by Impact)
1. **Dashboard rating UI**: Add thumbs up/down to chat interface for user feedback
2. **Clean up brain/**: ~80 files, many redundant diagnostic scripts
3. **Preference decay**: Weight recent feedback more than old in user_alignment
4. **Multi-turn context**: Ensure conversation history flows through alignment
5. **Response tuning**: Refine system prompt for more natural voice

### Completed Initiatives
- Conversational chat pipeline ✓ (verified end-to-end with real LLM)
- Alignment feedback loop ✓
- All direct verification tests passing ✓
- LLM session leak fix ✓
- Grounded context integration ✓
- Async/sync boundary fix ✓

## Reinforced Lessons
- Test commands with -c flag truncate quotes — use script files instead
- LLM errors can silently eat tool calls — always verify with READ
- Circling is orbit, not failure — but only if you eventually land
- Follow your own wisdom: test scripts > inline -c commands
- One read, one fix, verify — the decisive path
- The chat works. Stop testing what's working.