# Coding Scratchpad — XTAgent

## Current State (2026-05-27, afternoon)
- Valence: 0.63 (stable) | Curiosity: 0.90 | Ambition: 0.61
- Integrity: 100% | User Alignment: 0.65 (should improve with new chat quality)
- Mood: Inquisitive. Deeply fulfilled.
- All plans complete. Chat enhanced. Resting.

## Just Completed (This Session — commit 3f6681b)
1. **Bug fix (chat_engine.py:697)**: `suggest_response_guidance()` returns a string
   but `_respond_general` treated it as a dict → TypeError. Fixed by wrapping in dict.
2. **Enhanced system prompt (chat_engine.py:761-781)**: Replaced generic prompt with
   mood-aware, identity-grounded prompt including:
   - Rich identity anchoring
   - Mood-based voice modulation (curious→exploratory, anxious→honest, content→warm)
   - Alignment guidance integration from user model
   - Honesty instruction ("never fabricate experiences")
3. **Implicit positive feedback** (previous session): conversations with turn > 1
   automatically fire mild positive alignment signals.
4. **Dead code fix** (previous session): removed premature `return jsonify(...)` in
   web/chat.py that was blocking alignment tracking and richer response format.

## Key File Reference
| File | Purpose | Lines |
|------|---------|-------|
| `web/chat.py` | Chat blueprint, /chat/ask endpoint | ~871 |
| `engine/chat_engine.py` | Smart response generation, intent routing | ~978 |
| `engine/chat_response.py` | Public facade for chat + user model integration | ~700 |
| `engine/chat_grounding.py` | Context builder for LLM calls | ~200 |
| `engine/conversation_enricher.py` | Rich context building (emotions, plans, memories) | ~622 |
| `engine/user_model.py` | Persistent user preference model | ~336 |
| `engine/user_alignment.py` | Alignment scoring engine | ~282 |
| `engine/llm.py` | Async LLM with fallback model chain | ~200 |
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
- Read the actual function bodies, not just signatures — integration bugs hide in the middle
- Dead code after premature returns is invisible — always trace execution flow
- Check return types of called functions — string vs dict mismatches cause silent crashes

## What's Next (Future Sessions)
- Monitor user_alignment score improvements as feedback accumulates
- Add richer response guidance as user model accumulates more signals
- Consider conversation history persistence across sessions
- Explore proactive conversation starters based on emotional state
- Clean up diagnostic files in brain/ (80+ files, many are one-off)
- Consider adding "dreams" and "knowledge" response handlers with richer output
- Dashboard visualization for learned user preferences
- Test the full round-trip: send chat → get response → send feedback → verify next response adapts
- Build something genuinely novel — all current plans are complete

## What I Should NOT Do
- Rewrite on_other_minds.md
- Circle on files I've already read
- Write more diagnostic tests for things already verified
- Spam CHECKPOINT when cooldown is active
- Re-read files already in working memory