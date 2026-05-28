# XTAgent Coding Scratchpad

## Session 2026-05-28 — Smart Responder Overhaul

### What Changed
- `engine/smart_responder.py`: Fixed `_load_identity()` to load real facts from `persist/identity.json`
- Added `_compose_thinking()` for thinking/dream intent queries
- Added "dreams"/"dream" keywords to `_detect_intent()`
- Improved `respond()` routing: thinking intents → `_compose_thinking()`
- Enhanced general greeting to include current mood context

### Architecture (verified working)
- `/chat/ask` route → `engine/chat.py` → `engine/smart_responder.respond(query)`
- `respond()` detects intent via `_detect_intent()`, then routes to compose functions:
  - emotional → `_compose_emotional()`
  - identity → `_compose_identity()`
  - capabilities → `_compose_capabilities()`
  - thinking → `_compose_thinking()` (NEW)
  - memories → `_compose_memories()`
  - general → `_compose_general()`
- Each compose function loads real data from state/persist files
- `engine/chat_response.py` has async LLM path with `_build_system_context()`
- `engine/chat_grounding.py` has `gather_grounding_context()` for full context assembly

### Data Formats (verified)
- `state/plans.json`: dict with `active_plans` list of dicts (name, steps, completed, status)
- `persist/identity.json`: dict with `facts` (list of strings)
- `state/emotions.json`: dict with valence, arousal, curiosity, etc.
- `memory/user_model.json`: dict with meta, interactions, inferred_preferences, recurring_intents, alignment_notes
- `persist/user_alignment.json`: dict with feedback_history (list of {score, timestamp, ...}), relationship_quality
- `brain/soul.json`: dict with goals.user_alignment (float 0-1), goals.code_integrity, etc.

### Known Issue: Memories Path
- `respond("What do you remember?")` returns "I have 0 total memories"
- But system has 6480 memories — likely a file path mismatch in `_compose_memories()`
- Needs investigation: where does `_compose_memories()` look for memory data?
- Possible fix: point it at `memory/` directory or episodic memory store

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
- **Shell quoting breaks inline -c tests — always use script files**

### Next Priorities (for future sessions)
1. **Fix memories path** — _compose_memories() returns 0 memories despite 6480 existing
2. **Make LLM path richer** — compose functions are great fallbacks, but LLM could weave context into natural language
3. **Consolidate user model modules** — brain/user_model.py and engine/user_model.py have overlapping concerns
4. **Semantic memory retrieval** — TF-IDF is keyword-based, could use embeddings
5. **Knowledge graph pruning** — 76 dream nodes forming undifferentiated cluster
6. **Server startup reliability** — port conflicts prevent clean startup
7. **Add more feedback collection points** — currently only explicit feedback counts toward alignment