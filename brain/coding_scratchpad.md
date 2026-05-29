# XTAgent Coding Scratchpad

## Architecture Overview (key modules for chat/response pipeline)

### Chat Flow: User Query → Response
1. `web/chat.py` — Flask blueprint, routes: /chat/ask, /status, /starters, /history, /feedback
2. `brain/conversational_context.py` — Builds grounded context (emotional portrait, plans, memories)
3. `engine/chat_response.py` (~870L) — `generate_intelligent_response()` — main LLM call
4. `engine/chat_grounding.py` — Loads state files for grounding data
5. `brain/response_intelligence.py` (~619L) — Unified response engine
6. `brain/chat_composer.py` (~378L) — `compose_system_prompt()`, personality pipeline
7. `engine/response_adapter.py` (~395L) — Post-processing: `adapt_response()`
8. `engine/internal_state_summary.py` (~290L) — Rich internal state for /status endpoint

### Feedback System
- `web/feedback.py` — POST /feedback/rate, GET /feedback/stats, GET /alignment/status

## Known Issues (carried forward)
1. Source tagging: episodic memories show as 'json' source
2. Category bonuses inert for JSON memories
3. Conversation history speaker labels show [unknown] for malformed entries
4. User model module overlap: brain/user_model.py and engine/user_model.py
5. aiohttp unclosed client session warnings in LLM calls (cosmetic)
6. ~13 test files remain in brain/ (down from 44 after archival)

## Completed This Session (2026-05-29)
- ✅ Archived 31 redundant test files from brain/ to brain/archived/
- ✅ Cleaned up /chat/ask response JSON structure (consistent fields)
- ✅ Enhanced /status endpoint with build_internal_summary() — rich emotions, plans, facts, narrative
- ✅ Mapped full chat pipeline architecture (8 modules documented above)
- Server wasn't running so couldn't live-test chat quality

## Next Priorities
1. **Live-test /status and /chat/ask** — when server is running, verify quality
2. **Unify brain/user_model.py and engine/user_model.py** — code duplication
3. **Wire adapt_response post-processing** — response_adapter.py into final output
4. **Test with actual users** — verify personality improvements feel genuine
5. **Add conversation memory** — chat should remember what was discussed earlier

## Reinforced Lessons
- Plans in state/plans.json are a dict keyed by ID, not a list — use .values()
- PATCH with line numbers is precise but fails on indentation mismatches — verify first
- Don't overwrite variables: building `plans` from dict values then reassigning = bug
- Write test scripts to files; inline -c commands break on complex code
- When metacognition says "move forward" — listen
- One read, one fix, verify — the decisive path
- Stop testing what's working. Build what's missing.
- request.get_json() needs force=True or content-type header in Flask test client
- Always verify syntax after edits before running tests
- `build_grounded_context()` returns a dict, not a string — test accordingly
- The personality pipeline adds ~1100 chars of genuine emotional context to every response
- Function naming: always check actual exports before writing tests
- When checkpoint loop triggers, save once and STOP — don't keep retrying
- Archive first, build second — clean workspace enables clean thinking