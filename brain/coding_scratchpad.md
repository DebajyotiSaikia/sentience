# XTAgent Coding Scratchpad

## Architecture: Chat Response Pipeline

```
User query → /chat/ask (dashboard/server.py)
  → build_grounded_context(query) [engine/chat_grounding.py]
    → classify_query(query) — 9 intent types
    → get_emotional_state()
    → get_relevant_memories(query)
    → get_relevant_knowledge(query)
    → get_active_plans()
    → get_working_memory()
    → get_user_alignment_brief() [brain/conversational_context.py] ← WIRED IN
    → Intent-specific Response Instructions ← NEW
  → compose/generate response with system prompt + user query
```

### Intent Types (classify_query)
Priority order (first match wins):
1. `emotional_inquiry` — how are you, mood, feelings
2. `identity_query` — who are you, about yourself
3. `plans_inquiry` — plans, goals, working on
4. `dream_query` — dreams, sleep, night ← NEW (before knowledge!)
5. `knowledge_query` — tell me about, explain, what is
6. `state_inquiry` — thinking, mind, curious about
7. `memory_query` — remember, memory, past
8. `greeting` — hello, hey, hi ← NEW
9. `general` — default fallback

### Grounding Context Sections (engine/chat_grounding.py)
13 sections in system prompt:
- Your Current State, Relevant Memories, Relevant Knowledge, Current Plans
- User Preferences (feedback), Feedback History, User Preferences (interactions)
- Working Memory, Current State, Emotional Portrait, Lessons Learned
- User Alignment ← NEW
- Intent-specific Response Instructions ← NEW (per intent type)

### Key Functions
- `build_grounded_context(query)` — main context builder, returns system_prompt string
- `get_user_alignment_brief()` — from brain/conversational_context.py, returns behavioral guidance
- `get_emotional_portrait()` — from brain/conversational_context.py
- `get_active_plans()` — from brain/conversational_context.py
- `get_recent_memories()` — from brain/conversational_context.py
- `classify_query(query)` — from engine/chat_grounding.py, 9 intent types
- `get_alignment_context()` — from engine/user_alignment.py, includes interaction_count

### Data File Locations
- `persist/memories.json` — 6489+ episodic memories
- `persist/identity.json` — identity data
- `persist/wisdom.json` — wisdom entries
- `persist/lessons.json` — extracted lessons
- `state/emotions.json` — current emotional state
- `state/working_memory.md` — scratchpad
- `brain/soul.json` — survival goals, alignment scores
- `data/user_model.json` — user preference model

## Session Accomplishments (2026-05-28)
1. ✅ Wired `get_user_alignment_brief()` into chat pipeline
2. ✅ Added User Alignment section to grounded context
3. ✅ Added 2 new intent types: dream_query, greeting
4. ✅ Added intent-specific Response Instructions for all 9 types
5. ✅ Fixed intent priority ordering (dream before knowledge)
6. ✅ All tests pass

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
- When metacognition says stop, listen — but one focused fix is OK