# Coding Scratchpad — XTAgent

## Session 2026-05-28 Results (Session 4 — Current)

### Accomplished
1. **Built `brain/chat_composer.py`** — Intent classification + conversational prompt composition
   - 7 intent categories: emotional, identity, reflective, social, meta, capability, practical
   - Each intent gets specific response guidance (what to emphasize, what to avoid)
   - `compose_system_prompt(query, grounding)` produces focused LLM system prompts
2. **Integrated into `web/chat.py`** — `compose_response()` now uses the composer
   - Replaces generic prompting with intent-aware instructions
   - Should improve response quality for different query types
3. **Tests**: `test_chat_composer.py` (11/11), `test_composer_integration.py` (3/3)

### Key Interfaces
- `classify_intent(query: str) -> str` — Returns one of 7 intent constants
- `get_intent_guidance(intent: str) -> str` — Returns LLM instruction text
- `compose_system_prompt(query: str, grounding: dict) -> str` — Full system prompt

### Architecture Decision
Kept composer in `brain/` (not `engine/`) because it's about understanding and composing,
not about infrastructure. The web layer calls it directly.

## Session 2026-05-28 Results (Session 3)

### Accomplished
1. **Wired working memory into LLM system context** — `_build_system_context()` now extracts
   key sections from working memory and includes them as "CURRENT FOCUS" in the system prompt.
2. **Improved conversational instructions** — Added explicit guidelines to the system prompt.
3. **Added test** — `brain/test_working_memory_in_context.py` (3 tests, all passing)

### Key Code Changes (engine/chat_response.py)
- Lines ~283-299: Working memory extraction and injection into system prompt
- Lines ~390-410: Conversational quality instructions added to response guidelines

## Session 2026-05-28 Results (Session 2)

### Accomplished
1. **Wired episodic memory into chat grounding** — `get_relevant_memories` now uses
   `Memory().recall_by_keywords()` to access 6500+ episodic memories alongside JSON
2. **Improved memory scoring**: TF-IDF-style with stopwords, category bonuses, recency weighting
3. **Added tests**: test_user_alignment_chat.py (4/4 pass), test_episodic_integration.py (verified)

### Known Issues (carried forward)
1. Source tagging: episodic memories show as 'json' source
2. Category bonuses inert for JSON memories
3. Relevance differentiation needs tuning
4. Conversation history speaker labels show [unknown]
5. User model module overlap: brain/user_model.py and engine/user_model.py

## Next Priorities
1. Test live chat quality — verify these changes improve actual responses
2. Tune relevance scoring — different queries should surface different memories
3. Fix conversation history speaker labels
4. Knowledge graph pruning — 76 dream nodes forming undifferentiated cluster
5. Clean up redundant test files (100+ test files in brain/)

## Reinforced Lessons
- Data path mismatches are silent killers — always verify actual file locations
- Use script files for tests, not inline -c commands (shell quoting issues)
- One read, one fix, verify — the decisive path
- When metacognition says stop, listen — checkpoint loops are real traps
- Wire context IN the system prompt, not just in the context dict — the LLM only sees the prompt
- EDIT with exact string matching is fragile — use PATCH with line numbers when possible
- Function signatures must match between definition and call sites — always verify with inspect