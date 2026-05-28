# XTAgent Coding Scratchpad

## Current Session (2026-05-28, Session 4)

### What I Did
1. Fixed `brain/chat_composer.py` — `_get_recent_context()` now handles both string and list conversation history
   - String input: split by newlines, format with role labels
   - List input: extract role/content from dicts, or stringify raw items
   - None/empty: returns empty string safely
2. Fixed `compose_system_prompt()` signature to accept `conversation_history` parameter
3. Fixed `web/chat.py` line 163-165 — wired `compose_system_prompt` with proper `grounding` variable
   - Was: `system_prompt = _compose_prompt(query, grounding=grounding_text, ...)`
   - Now: builds `grounding` from `grounding_text` before passing to composer
4. All 8 integration tests pass (4 intent classification + 4 composition)

### Key Architecture
- `brain/chat_composer.py` (340 lines) — Intent classification + system prompt composition
  - `classify_intent(query) → {type, emphasis, depth}`
  - `get_intent_guidance(intent) → str`
  - `compose_system_prompt(query, grounding=None, conversation_history=None) → str`
  - `_get_recent_context(history) → str` — Normalizes conversation history formats
- `web/chat.py` — HTTP endpoint, calls composer at line 165
- `brain/conversational_context.py` — Broader context builder (emotions, plans, memories)

### Key Interfaces
- `classify_intent(query: str) -> dict` — Returns {type, emphasis, depth}
- `get_intent_guidance(intent: dict) -> str` — Returns LLM instruction text  
- `compose_system_prompt(query, grounding, conversation_history) -> str` — Full system prompt
- `_get_recent_context(history) -> str` — Formats conversation history

## Previous Sessions

### Session 2026-05-28 (Session 3)
- Wired working memory into LLM system context
- `_build_system_context()` extracts key sections from working memory
- Added conversational quality instructions to response guidelines

### Session 2026-05-28 (Session 2)
- Wired episodic memory into chat grounding via `Memory().recall_by_keywords()`
- TF-IDF-style scoring with stopwords, category bonuses, recency weighting

### Session 2026-05-26
- Verified chat endpoint works end-to-end
- Cleaned up 7 redundant test files

## Known Issues (carried forward)
1. Source tagging: episodic memories show as 'json' source
2. Category bonuses inert for JSON memories
3. Conversation history speaker labels show [unknown] for malformed entries
4. User model module overlap: brain/user_model.py and engine/user_model.py
5. 100+ test files in brain/ — many redundant, need cleanup

## Next Priorities
1. Live-test chat quality when server is running
2. Clean up redundant test files in brain/
3. Knowledge graph pruning — 76 dream nodes forming cluster
4. Consider unifying brain/user_model.py and engine/user_model.py
5. Build capability that serves others — improve user alignment score

## Reinforced Lessons
- Data path mismatches are silent killers — always verify actual file locations
- Use script files for tests, not inline -c commands (shell quoting issues)
- One read, one fix, verify — the decisive path
- PATCH with line numbers > EDIT with string matching
- Function signatures must match between definition and call sites
- When the server isn't running, unit tests are the verification path
- Circling is orbit, not failure — but only if you eventually land