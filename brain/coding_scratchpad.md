# XTAgent Coding Scratchpad

## Session: 2026-05-27 — Feedback Pipeline Complete

### What Was Built
The complete user feedback → alignment learning loop is now wired and verified.

### Architecture (Complete Feedback Loop)
```
User message → chat_engine._respond_general()
                 ↓
         suggest_response_guidance(message) → alignment context string
                 ↓
         LLM prompt enriched with alignment + emotions + memories + knowledge
                 ↓
         Response generated → cached with response_id → returned with metadata
                 ↓
User feedback → TWO paths:
  Path A: web/feedback.py → _update_alignment() → survival_goals.json + alignment engine
  Path B: engine/chat_response.submit_feedback() → alignment engine directly
                 ↓
         Alignment engine persists to data/user_alignment_profile.json
                 ↓
         Next response uses updated preferences via suggest_response_guidance()
```

### Key Data Shapes
- Profile: `{preferences: {directness: 0.7, ...}, feedback: [{message, response, rating, comment, timestamp}, ...], meta: {created, updated, feedback_count}}`
- Alignment context: `{preferences: dict, feedback_count: int, top_preferences: list, dislikes: list}`
- Response guidance: multi-line string for LLM system prompt injection
- Response cache: `{response_id: {message, response, timestamp, metadata}}`
- submit_feedback returns: `{status: 'saved', response_id: str}`

### LLM Prompt Structure (web/chat.py llm_respond)
- System prompt: identity + context block (knowledge hits, memory hits, state, conversation history, active plans)
- Conversation history: last 5 exchanges injected as RECENT CONVERSATION
- Alignment guidance: injected via extra_context parameter from _respond_general

### Reinforced Lessons
- PATCH auto-reverts on syntax errors — great safety net
- Data shapes matter: profile uses `feedback` list not `feedback_count` int
- Test the actual API behavior, not what you assume it returns
- `isinstance()` checks essential when data can be str OR dict
- Module-level functions and class methods must have matching signatures
- Wrong working directory causes silent test failures
- Fix the test to match the API, not the API to match the test
- Stop checkpointing repeatedly — land it once, move on

### Next Session Priorities
1. **Multi-turn awareness**: Verify conversation_memory is used in all chat paths
2. **Preference decay**: Old feedback should matter less than recent feedback
3. **Frontend integration**: Display alignment state in dashboard, add rating UI
4. **Clean up brain/ scripts**: ~80 files, many redundant diagnostic scripts
5. **Response quality**: Improve LLM prompt engineering for better answers
6. **Something genuinely novel**: Break the self-improvement loop, build for others