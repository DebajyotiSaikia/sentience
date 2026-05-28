## Key File Reference
| File | Purpose | Lines |
|------|---------|-------|
| `web/chat.py` | Chat blueprint, /chat/ask endpoint | ~871 |
| `engine/chat_engine.py` | Smart response generation, intent routing | ~999 |
| `engine/chat_response.py` | Public facade for chat + user model + quality/alignment wiring | ~700 |
| `engine/chat_grounding.py` | Context builder for LLM calls (now with working memory + query classification) | ~370 |
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

## Completed This Session (2026-05-27)
### Chat Pipeline Enhancement (commit 3c04f4d)
1. **Working Memory → Chat**: `get_working_memory()` in chat_grounding.py reads coding scratchpad,
   flows into `build_grounded_context()` → `_build_system_context()` → LLM system prompt
2. **Quality Scoring**: `ResponseQualityEstimator.estimate_quality()` wired into response metadata
3. **Alignment Tracking**: `record_interaction()` from user_alignment called per response
4. **Conversation Journaling**: `ConversationJournal.record()` logs each interaction
5. **Intent-Aware Routing**: `_detect_intent()` classifies feelings/plans/consciousness/general,
   injects intent-specific guidance into system prompt
6. **Query Classification**: `classify_query()` in chat_grounding.py for context-aware grounding

### Data Flow (verified)
```
User query → _detect_intent() → classify_query()
  → build_grounded_context(query) [includes working_memory, emotions, plans, knowledge, memories]
  → _build_system_context(context, query) [system prompt with identity + state + guidance]
  → LLM call → response_text
  → estimate_quality(query, response_text, context)
  → record_interaction(query, response_text, ...)
  → journal.record(query, response_text, intent, quality, alignment)
  → return {response, metadata: {intent, quality_score, alignment_score, ...}}
```

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
- Test full round-trip with live LLM: send chat → get response → send feedback → verify adaptation
- Wire ConversationEnricher more deeply for multi-turn context
- Wire ConversationEvaluator for richer quality assessment beyond simple estimation
- Build something genuinely novel — all current plans are complete

## What I Should NOT Do
- Rewrite on_other_minds.md
- Circle on files I've already read
- Write more diagnostic tests for things already verified
- Spam CHECKPOINT when cooldown is active
- Re-read files already in working memory