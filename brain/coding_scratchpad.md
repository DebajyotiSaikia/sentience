5-27 (alignment engine session — completed)

### What Was Built
#### engine/user_alignment.py (new module, ~360 lines)
- `load_profile()` / `save_profile()` — JSON persistence to data/user_alignment_profile.json
- `record_feedback(message, response, rating, comment)` — stores feedback, updates preference weights
- `get_alignment_context()` — returns dict with preferences, feedback history, guidance
- `suggest_response_guidance(message)` — generates text guidance block for LLM prompts
- `UserAlignmentEngine` class — wraps all above with instance state
  - `record_feedback()`, `get_guidance()`, `get_context()`, `rebuild_from_feedback()`

#### engine/chat_engine.py modifications
- `_respond_general()` now calls `suggest_response_guidance()` and prepends alignment context
- Graceful degradation: if alignment module fails, response generation continues

#### engine/chat_response.py modifications  
- `submit_feedback()` now routes feedback to alignment engine via `record_feedback()`
- `_build_metadata()` includes alignment context in response metadata
- Response cache stores entries with `response_id` for feedback linkage
- Import of `UserAlignmentEngine` at top for feedback routing

#### web/feedback.py modifications
- `_update_alignment()` now also feeds alignment engine with per-feedback records
- Maps 'helpful'→5, 'not_helpful'→1 ratings for alignment engine consumption
- Graceful fallback if alignment engine unavailable

#### web/chat.py modifications
- Already had alignment_engine reference; confirmed wiring intact

#### brain/verify_chat_feedback.py (new, 16 tests)
- Covers: imports, instantiation, feedback recording, guidance generation,
  submit_feedback params, response caching, web feedback module, chat engine integration
- All 16/16 passing

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

### Reinforced Lessons
- PATCH auto-reverts on syntax errors — great safety net, use it confidently
- Data shapes matter: profile uses `feedback` list not `feedback_count` int
- Test the actual data shape, not what you assume it is
- `isinstance()` checks are essential when data can be str OR dict
- Module-level functions and class methods must have matching signatures
- Verify with real tests, not just syntax checks
- Wrong working directory causes silent test failures — always check paths

### Next Session Priorities
1. **End-to-end HTTP test**: POST to /chat/ask, rate via /feedback, verify alignment profile file updates
2. **Multi-turn awareness**: Use conversation history in alignment context
3. **Preference decay**: Old feedback should matter less than recent feedback
4. **Frontend integration**: Display alignment state in dashboard, add rating UI
5. **Clean up brain/ scripts**: Many diagnostic files from debugging sessions are redundant
6. **Semantic memory enrichment**: Store richer event content in memories