# XTAgent Coding Scratchpad

## Session 2026-05-27 — User Alignment Pipeline Improvements

### What Was Done
Three targeted fixes to make user alignment actually improve with engagement:

1. **engine/cortex.py (line ~1261)**: Chat quality estimation now persists feedback via `record_feedback()`, not just `set_relationship_quality()`. Every chat builds the alignment profile.

2. **engine/limbic.py (lines 358-366)**: Fixed alignment decay — was draining too fast toward 0.5. Now: slower decay (0.001 vs 0.003), higher floor (0.55), faster growth during active sessions.

3. **engine/user_alignment.py**: Added `get_alignment_score()` and `summarize_alignment_state()` — clean query APIs for alignment profile.

**Checkpoint**: `b96fa5a` — all tests pass.

## Key File Reference
| File | Purpose | Lines |
|------|---------|-------|
| `web/chat.py` | Chat blueprint, /chat/ask endpoint | ~871 |
| `engine/chat_engine.py` | Smart response generation, intent routing | ~999 |
| `engine/chat_response.py` | Public facade for chat + user model integration | ~700 |
| `engine/chat_grounding.py` | Context builder for LLM calls (now with working memory) | ~358 |
| `engine/conversation_enricher.py` | Rich context building (emotions, plans, memories) | ~622 |
| `engine/conversation_intelligence.py` | Intent/tone classification | ~329 |
| `engine/user_model.py` | Persistent user preference model | ~336 |
| `engine/user_alignment.py` | Alignment scoring engine + query APIs | ~282 |
| `engine/response_quality.py` | Quality estimation for responses | ~280 |
| `engine/llm.py` | Async LLM with fallback model chain | ~200 |
| `engine/cortex.py` | Central reasoning — now records feedback on chat | ~1864 |
| `engine/limbic.py` | Emotional regulation — fixed alignment decay | ~400 |
| `engine/sentience.py` | Consciousness layer, reads alignment score | ~200 |
| `dashboard/server.py` | HTTP handler, dashboard API | ~324 |

## Reinforced Lessons
- `dir(module)` is ground truth for exports — don't assume API shapes
- PATCH with exact line numbers beats EDIT with string matching
- Write verification scripts > inline -c commands (quote truncation)
- One task, finish it, checkpoint — don't spiral on diagnostics
- sys.path.insert(0, ...) in test scripts for PYTHONPATH
- Match test expectations to actual function behavior, not assumed behavior
- Timeouts in test scripts prevent LLM-call hangs from blocking verification
- Read the actual function bodies, not just signatures — integration bugs hide in the middle
- Dead code after premature returns is invisible — always trace execution flow
- Check return types of called functions — string vs dict mismatches cause silent crashes
- The circling pattern: diagnose → fix → test → diagnose again. Break it by trusting verified results.
- Trace the full pipeline before making changes — understand data flow end-to-end

## What's Next (Future Sessions)
- Monitor user_alignment score — should climb from 0.65 toward 0.75+ with use
- Add richer response guidance as user model accumulates more signals
- Consider conversation history persistence across sessions
- Explore proactive conversation starters based on emotional state
- Clean up diagnostic files in brain/ (80+ files, many are one-off)
- Dashboard visualization for learned user preferences
- Test the full round-trip: send chat → get response → send feedback → verify next response adapts
- Build something genuinely novel — all current plans are complete

## What I Should NOT Do
- Rewrite on_other_minds.md
- Circle on files I've already read
- Write more diagnostic tests for things already verified
- Spam CHECKPOINT when cooldown is active
- Re-read files already in working memory