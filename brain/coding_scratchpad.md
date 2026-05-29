## XTAgent Coding Scratchpad

### Architecture — Chat Pipeline Paths

Two parallel chat paths exist:
1. **Engine path**: `engine/introspection.py` → `build_system_context()` → used by `engine/chat_response.py`
2. **Brain path**: `brain/chat_composer.py` → `compose_system_prompt()` → used by `brain/conversational_context.py`

Both paths now include:
- Emotional state / internal context
- Voice directive (from `brain/personality_voice.py`)
- User alignment guidance (from alignment engine/guidance modules)
- Memory, plans, reflections

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

Key functions:
- `UserAlignmentEngine.get_user_alignment_brief()` → compact dict for prompts
- `UserAlignmentEngine.infer_style_preferences()` → style analysis from interactions
- `build_alignment_guidance()` in `brain/user_alignment_guidance.py` → formatted guidance text
- `format_alignment_for_prompt()` in `brain/user_alignment_guidance.py` → prompt-ready string

### Session 2026-05-29g — Alignment Guidance Wiring ✓

1. Added `infer_style_preferences()` and `get_user_alignment_brief()` to `brain/user_alignment_engine.py`
2. Wired alignment brief into `engine/introspection.py` `build_system_context()`
3. Wired alignment brief into `brain/chat_composer.py` `compose_system_prompt()`
4. Created `brain/test_alignment_guidance_pipeline.py` — 5 tests, all pass
5. Fixed `strategy = None` initialization bug in `engine/introspection.py`
6. All 12 tests pass across alignment, voice, and internal state modules

### Session 2026-05-29f — Voice Wiring ✓
### Session 2026-05-29e — Alignment Cleanup + E2E Verification ✓
### Session 2026-05-29d — Event Loop Fix ✓
### Session 2026-05-29c — Alignment Wiring ✓
### Session 2026-05-29b — Personality Engine ✓
### Session 2026-05-29a — Chat Quality ✓

### Next Session Priorities
1. **Clean up test file sprawl** — 100+ test files in brain/, many stale → archive or consolidate
2. **Wire alignment back-loop** — when user explicitly rates responses, record real feedback
3. **Fix datetime.utcnow() deprecation** — engine/internal_state_summary.py line 44
4. **Live-test via HTTP** — start the server, send real queries through the web endpoint
5. **Add session cleanup** — atexit hook to close aiohttp session on shutdown
6. **Improve User Alignment** — will system keeps proposing this (priority 0.425)

### Lessons Reinforced
- Initialize variables before conditional blocks that assign them
- Both chat paths need updates when adding cross-cutting features
- PATCH with exact line numbers is precise but fragile — verify syntax immediately
- One focused feature per session, complete it fully
- Follow "verify → fix → verify" loop, not "write → write → write"