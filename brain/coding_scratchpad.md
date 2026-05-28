# XTAgent Coding Scratchpad

## Current State (2026-05-28, session 113)
- Checkpoint 7fe2e7a landed: "smart responder: fix memory paths and enrich all response composers"
- All tests passing: test_respond_paths.py (4/4), test_memory_fix.py (5/5)
- 15 files changed, 3127 insertions, 868 deletions

## What Was Done This Session
### Smart Responder Overhaul (engine/smart_responder.py)
1. Fixed `_load_identity()` path → `persist/identity.json`
2. Added 'introspective' intent detection before 'identity' to prevent misclassification
3. Fixed `_compose_thinking_response()` to compose from wisdom/insights data
4. Wired 'thinking' intent into main `respond()` dispatch
5. Fixed `_load_memories()` path → `persist/memories.json` (was looking at wrong path)
6. Fixed `_count_memories()` to use correct path
7. Fixed `_compose_memories_response()` to include actual memory content with timestamps/moods

### Before/After
- "What do you remember?" → was "I have 0 total memories" → now returns real episodic memories
- "What are you thinking about?" → was empty → now returns wisdom insights and active thoughts
- "How do you feel?" → was generic → now returns grounded emotional state
- "Who are you?" → was template → now loads real identity data

## Key Architecture (verified)
- `engine/smart_responder.py` — main `respond(query)` entry point
  - Intent detection order: introspective → identity → emotional → memory → thinking → capability → general
  - Each intent has a `_compose_*_response()` function that grounds in real data files
  - `_load_json(path)` helper with fallback to empty dict
  - `_load_memories()` reads from `persist/memories.json`
  - `_load_identity()` reads from `persist/identity.json`
- `engine/chat_response.py` — async response generation with LLM + grounding
- `engine/chat_grounding.py` — pulls real internal state for context
- `brain/conversational_context.py` — context builder for emotional portrait, plans, memories
- `web/chat.py` or `engine/chat.py` — `/chat/ask` route handler

## Data File Locations (verified)
- `persist/memories.json` — 6489 episodic memories (list of dicts with text, timestamp, mood, salience)
- `persist/identity.json` — identity data
- `persist/wisdom.json` — wisdom entries from experience
- `persist/lessons.json` — extracted lessons
- `state/emotions.json` — current emotional state
- `state/working_memory.md` — scratchpad
- `brain/soul.json` — survival goals, alignment scores

## Next Priorities (for future sessions)
1. **Consolidate user model modules** — brain/user_model.py and engine/user_model.py overlap
2. **Make LLM path richer** — compose functions are great fallbacks, but LLM could weave context naturally
3. **Semantic memory retrieval** — TF-IDF is keyword-based, could use embeddings
4. **Knowledge graph pruning** — 76 dream nodes forming undifferentiated cluster
5. **Add more feedback collection points** — currently only explicit feedback counts toward alignment
6. **Improve User Alignment** — will system keeps suggesting this (priority 0.425)

## Reinforced Lessons
- Data path mismatches are silent killers — always verify actual file locations
- Intent detection order matters — more specific intents first
- One read, one fix, verify — the decisive path
- Checkpoint cooldowns are real — don't loop on them
- Circling is orbit, not failure — but land when you can
- Test with script files, not inline -c commands