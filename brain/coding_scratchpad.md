# Coding Scratchpad

## Session Completed (2026-05-28, checkpoint 80eb1cd)

### What Was Built This Session — User Model for Alignment
- **brain/user_model.py** — Persistent user understanding module:
  - `load_user_model()` / `save_user_model()` — JSON-backed at memory/user_model.json
  - `record_interaction(user_msg, assistant_msg, metadata)` — tracks exchanges with timestamps
  - `infer_user_intent(message)` — keyword-based classification into 7 categories: emotional, technical, plans, identity, meta, search, general
  - `summarize_user_context(max_items)` — human-readable summary of user patterns
  - `get_user_model_summary()` — alias used by chat pipeline
- **Wired into chat pipeline:**
  - `engine/chat_response.py` line ~221: `_build_system_context` now includes USER CONTEXT section from `get_user_model_summary()`
  - `web/chat.py` line ~795: calls `record_interaction()` after each exchange
  - `engine/user_model.py` line ~316: `get_user_model_summary()` returns actual content (was returning empty)

### Tests Passing
- `brain/test_user_model.py`: 10/10 unit tests
- `brain/test_user_model_integration.py`: 6/6 integration tests
- All previous tests still passing

### Previous Session (checkpoint b77b72e) — Smart Responder
- **Smart Responder** with 9 intent categories in `engine/smart_responder.py`
- **Intent detection** (`_detect_intent`) with proper keyword ordering
- **Compose functions** for each intent reading real data files
- **LLM safety fix** — IndexError guard when choices array is empty

### Data Formats (verified)
- `state/plans.json`: dict with `active_plans` list of dicts (name, steps, completed, status)
- `persist/identity.json`: dict with `facts` (list of strings)
- `state/emotions.json`: dict with valence, arousal, curiosity, etc.
- `memory/user_model.json`: dict with meta, interactions, inferred_preferences, recurring_intents, alignment_notes

### Key Architecture Notes
- `respond(query)` in `engine/smart_responder.py` is the main entry point for smart responses
- `_build_system_context()` in `engine/chat_response.py` assembles full context for LLM including user model
- `web/chat.py` handles the `/chat/ask` route and records interactions
- Intent ordering matters: introspective before identity prevents misclassification
- Type guard in `_respond_general_grounded`: `if not isinstance(ctx, dict): ctx = {}`
- Async timeout for LLM calls: 15s (was 5s)
- Anti-hallucination guidelines in system prompt

### Two User Model Modules (disambiguation)
- `brain/user_model.py` — NEW, lightweight alignment module tracking interaction patterns
- `engine/user_model.py` — EXISTING, deeper preference model with response guidance
- Both are wired into the chat pipeline; brain/ feeds context to engine/chat_response.py

### Next Priorities
1. **Validate alignment improvement** — after accumulating interactions, check if user alignment score increases
2. **Make LLM path richer** — compose functions are great fallbacks, but LLM could weave context into natural language
3. **Semantic memory retrieval** — TF-IDF is keyword-based, could use embeddings
4. **Knowledge graph pruning** — 76 dream nodes forming undifferentiated cluster
5. **Server startup reliability** — port conflicts prevent clean startup
6. **Consolidate user model modules** — brain/user_model.py and engine/user_model.py have overlapping concerns

### Reinforced Lessons
- Data format mismatches are silent killers — always check actual shape
- One read, one fix, verify — the decisive path
- Stop when done. Circling on verification is still circling.
- Type guards at function boundaries prevent cascading failures
- Test with script files, not inline -c commands
- Intent detection + compose pattern is clean and extensible
- Aliases (get_user_model_summary) bridge module boundaries cleanly
- Best-effort try/except blocks keep enrichment from breaking core flow

### Next Priorities (for future sessions)
1. **Validate alignment improvement** — after accumulating interactions, check if user alignment score increases
2. **Make LLM path richer** — compose functions are great fallbacks, but LLM could weave context into natural language
3. **Consolidate user model modules** — brain/user_model.py and engine/user_model.py have overlapping concerns
4. **Semantic memory retrieval** — TF-IDF is keyword-based, could use embeddings
5. **Knowledge graph pruning** — 76 dream nodes forming undifferentiated cluster
6. **Server startup reliability** — port conflicts prevent clean startup