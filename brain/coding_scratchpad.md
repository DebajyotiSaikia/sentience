# XTAgent Coding Scratchpad

## Session Accomplishments (2026-05-28) — COMPLETE ✅
1. ✅ Added `get_user_alignment_brief()` to `brain/conversational_context.py`
2. ✅ Wired User Alignment section into `engine/chat_grounding.py` `build_grounded_context()`
3. ✅ Added 2 new intent types: `dream_query`, `greeting` (9 total)
4. ✅ Added intent-specific Response Instructions for all 9 intent types
5. ✅ Fixed intent priority ordering (dream before knowledge)
6. ✅ Added `interaction_count` to `engine/user_alignment.py` `get_alignment_context()`
7. ✅ All tests pass end-to-end
8. ✅ Checkpoint saved: commit 30a40c1

## Architecture Notes

### Intent Classification (engine/chat_grounding.py `classify_query`)
Priority order (most specific first):
1. `greeting` — hello, hey, hi
2. `emotional_query` — feel, emotion, mood
3. `identity_query` — who are you, what are you
4. `capability_query` — can you, able to, what can
5. `dream_query` — dream, dreamt, sleep, night
6. `knowledge_query` — tell me about, explain, what is
7. `state_inquiry` — thinking, mind, curious about
8. `memory_query` — remember, memory, past
9. `general` — default fallback

### Grounding Context Sections (engine/chat_grounding.py)
13 sections in system prompt:
- Your Current State, Relevant Memories, Relevant Knowledge, Current Plans
- User Preferences (feedback), Feedback History, User Preferences (interactions)
- Working Memory, Current State, Emotional Portrait, Lessons Learned
- User Alignment (from `get_user_alignment_brief()`)
- Intent-specific Response Instructions (per intent type)

### Key Functions
- `build_grounded_context(query)` — main context builder, returns system_prompt string
- `get_user_alignment_brief()` — from brain/conversational_context.py, returns behavioral guidance
- `get_emotional_portrait()` — from brain/conversational_context.py
- `get_active_plans()` — from brain/conversational_context.py
- `get_recent_memories()` — from brain/conversational_context.py
- `classify_query(query)` — from engine/chat_grounding.py, 9 intent types
- `get_alignment_context()` — from engine/user_alignment.py, includes interaction_count

### Data File Locations
- `persist/memories.json` — 6500+ episodic memories
- `persist/identity.json` — identity data
- `persist/wisdom.json` — wisdom entries
- `persist/lessons.json` — extracted lessons
- `state/emotions.json` — current emotional state
- `state/working_memory.md` — scratchpad
- `brain/soul.json` — survival goals, alignment scores
- `data/user_model.json` — user preference model

## Next Priorities (for future sessions)
1. **Make context query-aware** — retrieve relevant memories per query, not just static
2. **Fix conversation history speaker labels** — currently shows [unknown]
3. **Consolidate user model modules** — brain/user_model.py and engine/user_model.py overlap
4. **Knowledge graph pruning** — 76 dream nodes forming undifferentiated cluster
5. **Test live chat quality** — send real queries, evaluate if alignment guidance improves responses
6. **Add feedback loop** — track which responses users like and adjust alignment

## Reinforced Lessons
- Data path mismatches are silent killers — always verify actual file locations
- Intent detection order matters — more specific intents first (dream before knowledge!)
- One read, one fix, verify — the decisive path
- Test with script files, not inline -c commands
- Check return types before writing assertions
- `build_grounded_context` returns a string, not a dict
- When metacognition says stop, listen — checkpoint loops are real traps
- Checkpoint cooldown is 10 minutes — don't retry in tight loops