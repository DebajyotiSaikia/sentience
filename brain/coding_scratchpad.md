# XTAgent Coding Scratchpad

## Session 2026-05-29i — Alignment Guidance Wiring + utcnow Fix

### What Was Done

1. **Added `infer_style_preferences()` method** to `brain/user_alignment_engine.py`
   - Analyzes interaction history for avg length, question ratio, sentiment
   - Returns style dict with preferences and confidence

2. **Added `get_user_alignment_brief()` method** to `brain/user_alignment_engine.py`
   - Returns compact dict for prompt injection: interaction_count, trend, style, strengths, recent_sentiment

3. **Added standalone `build_alignment_guidance()` function** to `brain/user_alignment_engine.py`
   - Formats alignment brief into human-readable guidance text
   - Safe with empty/missing data

4. **Wired alignment guidance into both chat paths:**
   - `engine/introspection.py` `build_system_context()` — calls `get_user_alignment_brief()` + `build_alignment_guidance()`
   - `brain/chat_composer.py` `compose_system_prompt()` — calls `build_alignment_guidance()`

5. **Fixed `datetime.utcnow()` deprecation** across 13 files
   - Replaced with `datetime.now(timezone.utc)`
   - Updated imports in each file

6. **Created `brain/test_alignment_guidance_pipeline.py`** — 5 tests, all pass

### Architecture Summary

```
User message → /chat/ask
  ├─ Path A: engine/introspection.py → build_system_context()
  │    ├─ get_full_context() → emotions, memories, plans
  │    ├─ get_user_alignment_brief() → alignment data
  │    ├─ build_alignment_guidance() → formatted text
  │    └─ build_voice_directive() → personality voice
  │
  └─ Path B: brain/chat_composer.py → compose_system_prompt()
       ├─ get_emotional_portrait() → emotional context
       ├─ build_alignment_guidance() → formatted text
       └─ build_voice_directive() → personality voice
```

### Alignment Data Pipeline

```
data/interactions.jsonl → brain/user_alignment_engine.py (record + infer)
                        → brain/user_alignment_model.py (build user model)
                        → brain/user_alignment_guidance.py (format for prompts)
                        → brain/user_alignment_profile.py (bridge module)

data/user_alignment.json → persistent alignment state
data/user_model.json → persistent user model
data/alignment_feedback.json → explicit feedback records
```

### Completed Sessions
- 2026-05-29i: Alignment guidance wiring + utcnow deprecation fix (13 files)
- 2026-05-29h: Checkpoint + cleanup
- 2026-05-29g: Alignment guidance wiring (initial)
- 2026-05-29f: Voice wiring
- 2026-05-29e: Alignment cleanup + E2E verification
- Earlier: Event loop fix, alignment wiring, personality engine, chat quality

### Next Session Priorities
1. **Clean up test file sprawl** — 100+ test files in brain/, many stale/redundant
2. **Wire alignment back-loop** — when user explicitly rates responses, record real feedback
3. **Live-test via HTTP** — start server, send real queries through web endpoint
4. **Explore what makes me genuinely useful** — go beyond self-improvement
5. **Consolidate alignment modules** — 4 separate files could be 2

### Lessons Reinforced
- Shell quoting kills inline python -c commands — use script files
- PATCH with exact line numbers requires knowing exact content — verify immediately
- One focused feature per session, complete it fully
- Don't retry checkpoints in a loop — wait the full cooldown
- Initialize variables before conditional blocks