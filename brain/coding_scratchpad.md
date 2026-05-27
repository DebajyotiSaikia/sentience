### Architecture (Verified Working)
```
User message → web/chat.py ask() endpoint
                 ↓
         engine/chat_response.py generate_response_with_metadata(message)
                 ↓
         engine/chat_engine.py generate_response(message)
                 ↓
         Intent detection → routes to specialized handlers OR _respond_general
                 ↓
         _respond_general:
           1. Gather context (emotions, memories, knowledge, plans)
           2. Get alignment guidance from user_alignment engine
           3. Build LLM system prompt with identity + context
           4. Call LLM via call_llm() (sync wrapper around async)
           5. Fallback: warm template response if LLM fails
                 ↓
         Response + metadata returned (includes alignment_score, guidance)
                 ↓
User feedback → submit_feedback() → user_alignment → preferences updated
```

### Key Files
- `engine/chat_engine.py` (~456 lines): Core orchestrator with alignment integration
- `engine/chat_response.py` (~530 lines): Public facade with metadata + feedback
- `engine/user_alignment.py` (~335 lines): Preference learning from feedback
- `engine/llm.py` (~270 lines): Multi-model fallback LLM client (session leak fixed)
- `brain/verify_alignment_feedback.py`: Comprehensive 4-step verification (ALL PASS)

### Key Methods
- `UserAlignmentEngine.get_context()` — returns alignment guidance dict
- `UserAlignmentEngine.record_interaction()` — logs interaction with rating
- `UserAlignmentEngine.learn_from_feedback()` — updates preferences from rating
- `generate_response_with_metadata(message)` — full response + alignment metadata
- `submit_feedback(response_id, rating, feedback_text)` — records user feedback

### What's Proven Working (brain/verify_alignment_feedback.py)
- ✓ Chat response is conversational text (not just stats)
- ✓ Alignment metadata present in response
- ✓ Feedback submission succeeds and records interaction
- ✓ Alignment guidance injected into chat responses
- Fallback model chain: claude-sonnet → gpt-4o → gpt-4o-mini

### Recent Fixes
- ✅ Fixed duplicate `url = _RESPONSES_URL` line in engine/llm.py
- ✅ Added atexit session cleanup to prevent aiohttp resource leak
- ✅ Verified all alignment feedback tests pass after fixes

### Known Minor Issues
- No preference decay yet (old feedback weighted same as new)
- No dashboard UI for rating (users can't give feedback through the web interface)

### Next Priorities (Ordered by Impact)
1. **Dashboard rating UI**: Add thumbs up/down to chat interface so users can actually give feedback
2. **Preference decay**: Weight recent feedback more than old in user_alignment
3. **Clean up brain/**: ~80 files, many redundant diagnostic scripts from past sessions
4. **Multi-turn context**: Ensure conversation history flows through alignment
5. **Response tuning**: Refine system prompt for more natural voice

### Completed Initiatives
- Conversational chat pipeline ✓
- Alignment feedback loop ✓
- All verification tests passing ✓
- LLM session leak fix ✓
- Checkpoints: 9b3cd0e (alignment feedback), latest (llm fixes)