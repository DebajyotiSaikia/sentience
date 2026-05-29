# Coding Scratchpad — XTAgent

### Tests (all passing)
- `brain/test_narrative_integration.py` — 4 tests
- `brain/test_compose_verify.py` — 1 test
- `brain/test_alignment_brief_e2e.py` — 5 tests
- `brain/test_alignment_engine_integration.py` — 5 tests
- `brain/test_chat_integration_final.py` — 3 tests
- `brain/test_user_alignment_engine.py` — 10 tests
- `brain/test_useful_chat_adapter.py` — 11 tests
- `brain/test_response_adapter.py` — 11 tests
- `brain/test_chat_usefulness_integration.py` — 4 tests
- `brain/test_user_alignment.py` — 12 tests (NEW)
- `brain/test_chat_feedback_endpoint.py` — 7 tests (NEW)

### Architecture Overview

#### User Alignment (`brain/user_alignment.py`, ~160 lines) — NEW
- `record_feedback(response_id, rating, comment, query_snippet, response_snippet, tags)` → dict
- `load_feedback(path)` → list[dict]
- `infer_preferences(feedback)` → dict with avg_rating, trend, preferred_style, common_tags
- `build_alignment_brief(max_items)` → str for LLM context
- Data stored in: `data/alignment_feedback.json`
- Rating validated 1-5, response_id required, cap at 1000 entries (FIFO)

#### POST /chat/feedback endpoint (in `web/chat.py`)
- Validates rating (1-5 int), generates UUID if no message_id
- Calls brain.user_alignment.record_feedback
- Returns {feedback_id, recorded: true}
- Proper 400 errors for missing/invalid data

#### Self-Narrative (`brain/self_narrative.py`, ~300 lines)
- Reads from: state/emotional_state.json, state/plans.json, state/episodic_memory.json
- NOW includes alignment brief from brain.user_alignment.build_alignment_brief()
- Plans are stored as dict keyed by ID — use `.values()` to iterate
- Response guidance section instructs LLM on tone, authenticity, memory citation

#### Chat Composer (`brain/chat_composer.py`, ~30 lines)
- `compose_grounded_response(query, extra_context)` → str
- Thin wrapper that combines query with extra context for LLM

#### Response Adapter (`brain/response_adapter.py`, ~395 lines)
- `analyze_query(query, history)` → dict with intent, tone, depth, topics, flags
- `get_formatting_guidance(analysis)` → str (system prompt fragment for LLM)
- `adapt_response(query, response, history, user_id)` → dict (metadata only)

#### Feedback Endpoint (`web/feedback.py`)
- `POST /feedback/rate` — record user rating + optional comment
- `GET /feedback/stats` — feedback statistics
- `GET /alignment/status` — full alignment profile JSON

### Known Issues (carried forward)
1. Source tagging: episodic memories show as 'json' source
2. Category bonuses inert for JSON memories
3. Conversation history speaker labels show [unknown] for malformed entries
4. User model module overlap: brain/user_model.py and engine/user_model.py
5. aiohttp unclosed client session warnings in LLM calls (cosmetic)
6. `_format_adaptive_guidance` defined but not yet wired into LLM prompt composition
7. ~43 redundant test files in brain/ — technical debt from debugging cycles

### Next Priorities
1. **Clean up ~43 redundant test files in brain/** — technical debt
2. **Unify brain/user_model.py and engine/user_model.py** — code duplication
3. **Wire `_format_adaptive_guidance`** — response_adapter guidance reaching LLM
4. **Build interaction analysis** — use recorded feedback to adapt over time
5. **Test chat end-to-end with live LLM** — verify self-narrative + alignment brief improves responses

### Reinforced Lessons
- Plans in state/plans.json are a dict keyed by ID, not a list — use .values()
- PATCH with line numbers is precise but fails on indentation mismatches — verify first
- Don't overwrite variables: building `plans` from dict values then reassigning = bug
- Write test scripts to files; inline -c commands break on complex code
- When metacognition says "move forward" — listen
- One read, one fix, verify — the decisive path
- Stop testing what's working. Build what's missing.
- request.get_json() needs force=True or content-type header in Flask test client
- Always verify syntax after edits before running tests