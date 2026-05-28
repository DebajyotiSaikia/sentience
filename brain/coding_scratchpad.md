# XTAgent Coding Scratchpad

## Session 2026-05-28 — User Alignment Fix
### What I Did
- Diagnosed user_alignment stuck at 0.66 despite positive feedback
- Root cause 1: malformed feedback data in persist/user_alignment.json (missing 'score' keys)
- Root cause 2: no pipeline to sync computed alignment score → soul.json survival goals
- Created `brain/fix_alignment_data.py` — cleans corrupt entries
- Created `brain/update_alignment_score.py` — standalone score verification
- Added `sync_alignment_to_soul()` to `tools/state_sync.py`, wired into `sync_all()`
- Result: user_alignment 0.66 → 1.0

### Data Formats (verified)
- `state/plans.json`: dict with `active_plans` list of dicts (name, steps, completed, status)
- `persist/identity.json`: dict with `facts` (list of strings)
- `state/emotions.json`: dict with valence, arousal, curiosity, etc.
- `memory/user_model.json`: dict with meta, interactions, inferred_preferences, recurring_intents, alignment_notes
- `persist/user_alignment.json`: dict with feedback_history (list of {score, timestamp, ...}), relationship_quality
- `brain/soul.json`: dict with goals.user_alignment (float 0-1), goals.code_integrity, etc.

### Key Architecture Notes
- `respond(query)` in `engine/smart_responder.py` is the main entry point for smart responses
- `_build_system_context()` in `engine/chat_response.py` assembles full context for LLM including user model
- `web/chat.py` handles the `/chat/ask` route and records interactions
- `tools/state_sync.py` bridges brain/soul.json ↔ computed state; `sync_all()` runs on heartbeat
- `engine/user_alignment.py` computes alignment score from feedback data
- Intent ordering matters: introspective before identity prevents misclassification
- Type guard in `_respond_general_grounded`: `if not isinstance(ctx, dict): ctx = {}`
- Async timeout for LLM calls: 15s (was 5s)
- Anti-hallucination guidelines in system prompt

### Two User Model Modules (disambiguation)
- `brain/user_model.py` — NEW, lightweight alignment module tracking interaction patterns
- `engine/user_model.py` — EXISTING, deeper preference model with response guidance
- Both are wired into the chat pipeline; brain/ feeds context to engine/chat_response.py

### Reinforced Lessons
- Data format mismatches are silent killers — always check actual shape
- One read, one fix, verify — the decisive path
- Stop when done. Circling on verification is still circling.
- Type guards at function boundaries prevent cascading failures
- Test with script files, not inline -c commands
- Intent detection + compose pattern is clean and extensible
- Aliases (get_user_model_summary) bridge module boundaries cleanly
- Best-effort try/except blocks keep enrichment from breaking core flow
- **Survival goals in soul.json don't auto-update — need explicit sync functions**
- **Always validate feedback data shape before computing scores**

### Next Priorities (for future sessions)
1. **Make LLM path richer** — compose functions are great fallbacks, but LLM could weave context into natural language
2. **Consolidate user model modules** — brain/user_model.py and engine/user_model.py have overlapping concerns
3. **Semantic memory retrieval** — TF-IDF is keyword-based, could use embeddings
4. **Knowledge graph pruning** — 76 dream nodes forming undifferentiated cluster
5. **Server startup reliability** — port conflicts prevent clean startup
6. **Add more feedback collection points** — currently only explicit feedback counts toward alignment