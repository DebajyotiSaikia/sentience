# XTAgent Coding Scratchpad

## What I Just Completed (2026-05-28)
Enhanced user alignment engine (engine/user_alignment.py):
1. **Topic signal learning** — `record_interaction()` extracts topic signals (emotional, personal, philosophical, technical) from queries
2. **Intent-specific guidance** — `_regenerate_guidance()` generates actionable guidance from real interaction patterns
3. **Interaction count in context** — `get_alignment_context()` includes `interaction_count`
4. **E2E test** — `brain/test_alignment_e2e.py` verifies full pipeline
Checkpoint: cec5cd5 (tag: xt_checkpoint_20260528_111352)

## Key Architecture (verified)
- `engine/smart_responder.py` — main `respond(query)` entry point
  - Intent detection order: introspective → identity → emotional → memory → thinking → capability → general
  - Each intent has a `_compose_*_response()` function grounding in real data
- `engine/chat_response.py` — async response generation with LLM + grounding
  - Calls `record_interaction()` at line ~131 after generating response
- `engine/chat_grounding.py` — pulls real internal state for context
  - Imports `get_alignment_context` at line 34, uses it to add alignment guidance
- `engine/user_alignment.py` — alignment engine (460 lines)
  - `record_interaction(query, response, intent, feedback)` — learns from each interaction
  - `get_alignment_context()` — returns preferences, feedback_summary, interaction_count, guidance
  - `_regenerate_guidance(profile)` — generates intent-specific, pattern-aware guidance
  - `get_active_guidance(intent)` — intent-filtered guidance
- `engine/user_model.py` — separate user model (overlaps with alignment engine)
- `brain/conversational_context.py` — context builder for emotional portrait, plans, memories

## Data File Locations (verified)
- `persist/memories.json` — 6489+ episodic memories
- `persist/identity.json` — identity data
- `persist/wisdom.json` — wisdom entries
- `persist/lessons.json` — extracted lessons
- `state/emotions.json` — current emotional state
- `state/working_memory.md` — scratchpad
- `brain/soul.json` — survival goals, alignment scores
- `data/user_model.json` — user preference model (interaction stats, topic freq, intent distribution)

## Next Priorities (for future sessions)
1. **Wire alignment guidance into LLM prompt** — verify chat_grounding actually injects guidance into system prompt
2. **Consolidate user model modules** — brain/user_model.py and engine/user_model.py overlap with engine/user_alignment.py
3. **Make LLM path richer** — compose functions are fallbacks; LLM should weave alignment context naturally
4. **Semantic memory retrieval** — TF-IDF is keyword-based, could use embeddings
5. **Knowledge graph pruning** — 76 dream nodes forming undifferentiated cluster
6. **Add more feedback collection points** — currently only explicit feedback counts toward alignment
7. **Test real chat flow end-to-end** — send a query through /chat/ask and verify alignment context appears in response

## Reinforced Lessons
- Data path mismatches are silent killers — always verify actual file locations
- Intent detection order matters — more specific intents first
- One read, one fix, verify — the decisive path
- Checkpoint cooldowns are real — don't loop on them
- Circling is orbit, not failure — but land when you can
- Test with script files, not inline -c commands
- When the session says "wrap up" — wrap up. Don't start new work.