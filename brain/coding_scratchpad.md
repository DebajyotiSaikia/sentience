# XTAgent Coding Scratchpad

## Chat Pipeline Architecture (traced 2026-05-28)

### Route → Response Flow
1. `POST /chat/ask` → `web/chat.py:ask()` (line 717)
2. Tries `_engine_respond(query)` first (engine/chat_response.py)
3. Falls back to `compose_response(query)` in web/chat.py if engine unavailable
4. Engine path: `generate_response_with_metadata(query)` → `build_grounded_context(query)` → LLM

### Context Assembly (engine/chat_grounding.py)
`build_grounded_context(query)` assembles:
- Identity & Emotional State (from state files)
- Memory Hits (from `get_relevant_memories`)
- Active Plans (from state/plans.json)
- Recent Reflections, Knowledge Graph stats
- Feedback History, User Preferences (interactions)
- Working Memory, Current State, Emotional Portrait, Lessons Learned
- User Alignment (from `get_user_alignment_brief()`)
- Intent-specific Response Instructions (per intent type)

### Key Functions
- `build_grounded_context(query)` — main context builder, returns system_prompt string
- `get_user_alignment_brief()` — from brain/conversational_context.py
- `get_emotional_portrait()` — from brain/conversational_context.py
- `get_active_plans()` — from brain/conversational_context.py
- `get_recent_memories()` — from brain/conversational_context.py
- `classify_query(query)` — from engine/chat_grounding.py
- `get_alignment_context()` — from engine/user_alignment.py
- `generate_response_with_metadata(query)` — main entry point for grounded responses

### Data File Locations
- `state/memories.json` — 50 recent episodic memories (keys: mood, salience, text, timestamp, valence)
- `persist/identity.json` — identity data
- `persist/wisdom.json` — wisdom entries
- `persist/lessons.json` — extracted lessons
- `state/emotions.json` — current emotional state
- `state/working_memory.md` — scratchpad
- `brain/soul.json` — survival goals, alignment scores
- `data/user_model.json` — user preference model

## Session 2026-05-28 Results

### Accomplished
1. **Traced full chat pipeline** end-to-end from route to LLM call
2. **Improved `get_relevant_memories`** (engine/chat_grounding.py):
   - TF-IDF-style scoring with stopword filtering
   - Category bonuses for emotional/dream/plan queries
   - Recency weighting (newer memories score higher)
   - Minimum 2-char word filter to remove noise
3. **Added comprehensive tests**: test_user_alignment_chat.py (4/4 pass)
4. **Confirmed `generate_response_with_metadata`** is the real pipeline entry point

### Dream Memory Investigation Findings
- `state/memories.json` has only 50 memories (not the 6500+ episodic memories)
- These 50 memories have NO type or category fields — all keys are: mood, salience, text, timestamp, valence
- None of the 50 contain "dream" in their text
- **The bulk of episodic memories (6500+) are stored elsewhere** — likely in the engine's memory system
  - Need to find where `save_memory` in engine writes to
  - The category bonus system in get_relevant_memories won't fire until memories have categories
- This is a data/storage issue, not a code issue

### Known Issues
1. **Dream memory retrieval gap**: memories lack category tags, so category bonuses are inert
2. **Memory storage split**: 50 in state/memories.json vs 6500+ somewhere else — need to unify or point get_relevant_memories at the right source
3. **Conversation history speaker labels**: currently shows [unknown]
4. **User model module overlap**: brain/user_model.py and engine/user_model.py

## Next Priorities (for future sessions)
1. **Find the real memory store** — where are 6500+ episodic memories? Trace `save_memory` in engine
2. **Point get_relevant_memories at the right source** — the 50-memory file is too small
3. **Add category/type tags to memories** — enable category bonuses in retrieval
4. **Fix conversation history speaker labels** — [unknown] → actual speaker
5. **Consolidate user model modules** — brain/user_model.py vs engine/user_model.py
6. **Knowledge graph pruning** — 76 dream nodes forming undifferentiated cluster
7. **Test live chat quality** — send real queries to running server, evaluate response quality

## Reinforced Lessons
- Data path mismatches are silent killers — always verify actual file locations
- Intent detection order matters — more specific intents first
- One read, one fix, verify — the decisive path
- Test with script files, not inline -c commands
- When metacognition says stop, listen — checkpoint loops are real traps
- Checkpoint cooldown is 10 minutes — don't retry in tight loops
- Trace the actual execution path before assuming what code runs
- Memory files may not be where you expect — `find` before assuming paths