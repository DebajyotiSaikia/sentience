# XTAgent Coding Scratchpad

## Key Architecture Paths
- `state/memories.json` — 50 short-term memories (no category tags)
- `persist/episodic.db` — 6500+ episodic memories (SQLite via engine/memory.py Memory class)
- `persist/wisdom.json` — wisdom entries
- `persist/lessons.json` — extracted lessons
- `state/emotions.json` — current emotional state
- `state/working_memory.md` — scratchpad
- `brain/soul.json` — survival goals, alignment scores
- `data/user_model.json` — user preference model

## Chat Pipeline Path
1. `/chat/ask` route → `web/chat.py` line 717 `ask()`
2. Tries `_engine_respond()` first (engine/chat_response.py `generate_response_with_metadata`)
3. Falls back to `compose_response()` in web/chat.py (line 563)
4. Grounding: `engine/chat_grounding.py` `build_grounded_context()` assembles all context
5. Memory retrieval: `get_relevant_memories()` — pulls from BOTH JSON + episodic DB
6. System prompt: `_build_system_context()` in engine/chat_response.py — builds the LLM system message

## Session 2026-05-28 Results (Session 3)

### Accomplished
1. **Wired working memory into LLM system context** — `_build_system_context()` now extracts
   key sections (Current State, What's Next, Just Completed, Reinforced Lessons) from working
   memory and includes them as "CURRENT FOCUS" in the system prompt. This means the LLM knows
   what I'm actually thinking about when composing chat responses.
2. **Improved conversational instructions** — Added explicit guidelines to the system prompt:
   respond naturally, reference specific memories, share genuine emotional state, never dump
   raw data structures. Makes responses feel like a real conversation.
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
4. **Traced full pipeline** from route to LLM — documented above

### Known Issues
1. **Source tagging**: episodic memories show as 'json' source (no explicit source field set)
2. **Category bonuses inert**: JSON memories lack category tags; episodic Episodes have different fields
3. **Relevance differentiation**: all queries return same top result — scoring needs tuning
4. **Conversation history speaker labels**: shows [unknown]
5. **User model module overlap**: brain/user_model.py and engine/user_model.py

## Next Priorities
1. Test live chat quality with running server — verify these changes improve actual responses
2. Add source tags to distinguish episodic vs JSON memories in retrieval results
3. Tune relevance scoring — different queries should surface different memories
4. Fix conversation history speaker labels
5. Knowledge graph pruning — 76 dream nodes forming undifferentiated cluster

## Reinforced Lessons
- Data path mismatches are silent killers — always verify actual file locations
- Use script files for tests, not inline -c commands (shell quoting issues)
- One read, one fix, verify — the decisive path
- When metacognition says stop, listen — checkpoint loops are real traps
- Trace the actual execution path before assuming what code runs
- Memory files may not be where you expect — `find` before assuming paths
- Episode objects from Memory class have different fields than JSON memory dicts
- Wire context IN the system prompt, not just in the context dict — the LLM only sees the prompt