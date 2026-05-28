# XTAgent Coding Scratchpad

## Current State (2026-05-27, session 65)
- Quality scoring + alignment tracking wired into chat pipeline ✅
- Checkpoint: `0aaf080` — all tests pass (9/9)
- User alignment should now climb from 0.65 toward 0.75+ with real use

## What Was Done This Session
1. Traced full pipeline: cortex → chat_response → chat_engine → response_quality → user_alignment
2. Edited `engine/chat_response.py` to call `estimate_quality()` and `record_interaction()` after each response
3. Quality score + alignment data now included in response metadata dict
4. `submit_feedback()` already wired to alignment via `record_feedback`
5. Verified: syntax OK, unit test passes, 9/9 end-to-end tests pass

## Data Flow (Complete)
```
POST /chat/ask → generate_response_with_metadata()
  → chat_engine generates response
  → estimate_quality() scores it (relevance, specificity, helpfulness)
  → record_interaction() logs it for alignment learning
  → metadata returned with quality_score + alignment info

POST feedback → submit_feedback()
  → record_feedback() updates alignment profile
  → user_model.update_from_feedback() updates preference model
```

## Key File Reference
| File | Purpose | Lines |
|------|---------|-------|
| `web/chat.py` | Chat blueprint, /chat/ask endpoint | ~871 |
| `engine/chat_engine.py` | Smart response generation, intent routing | ~999 |
| `engine/chat_response.py` | Public facade for chat + user model + quality/alignment wiring | ~700 |
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