# Coding Scratchpad — XTAgent

## Session 2026-05-28 (afternoon) — COMPLETED
### What I Built
- `brain/user_alignment_guidance.py` — converts learned user model data into concrete LLM response guidance
  - `build_alignment_guidance(query, alignment_context)` → structured dict
  - `format_alignment_guidance_for_prompt(guidance)` → formatted string for system prompt
  - Three confidence tiers: low (<20 interactions), medium (20-100), high (100+)
  - Extracts interests from topic frequencies, style from feedback patterns
- `brain/test_alignment_guidance.py` — comprehensive tests covering all tiers and edge cases
- Wired into `engine/chat_response.py` `build_system_context()` at lines 334-347
  - Graceful fallback to basic `get_alignment_guidance()` if rich module fails

### Checkpoint
- Commit: 1c73abf (tag: xt_checkpoint_20260528_112824)
- Previous: cec5cd5 (tag: xt_checkpoint_20260528_111352) — alignment pipeline

## Key Architecture (verified)
- `engine/smart_responder.py` — main `respond(query)` entry point
  - Intent detection order: introspective → identity → emotional → memory → thinking → capability → general
  - Each intent has a `_compose_*_response()` function grounding in real data
- `engine/chat_response.py` — async response generation with LLM + grounding
  - Calls `record_interaction()` at line ~131 after generating response
  - `build_system_context()` now includes rich alignment guidance from `brain/user_alignment_guidance.py`
- `engine/chat_grounding.py` — pulls real internal state for context
  - Imports `get_alignment_context` at line 34, uses it to add alignment guidance
- `engine/user_alignment.py` — alignment engine (460 lines)
  - `record_interaction(query, response, intent, feedback)` — learns from each interaction
  - `get_alignment_context()` — returns preferences, feedback_summary, interaction_count, guidance
  - `_regenerate_guidance(profile)` — generates intent-specific, pattern-aware guidance
  - `get_active_guidance(intent)` — intent-filtered guidance
- `brain/user_alignment_guidance.py` — NEW: rich guidance builder
  - Consumes alignment context, produces structured guidance for LLM prompts
  - Three trust tiers based on interaction count
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

## Session 2026-05-28 Accomplishments
- Added **conversation history** to `_build_system_context()` — LLM now has conversational continuity
- System context now has 7 grounded sections: Lessons, User Preferences (2), Alignment Guidance, Self-Awareness, Conversation History, Response Guidelines
- Total context: ~3200 chars of real grounding data (not generic prompts)
- Verified all sections present and non-empty via test scripts

## Next Priorities (for future sessions)
1. **Make context query-aware** — retrieve relevant memories per query, not just static context
2. **Fix conversation history speaker labels** — currently shows [unknown] instead of user/agent
3. **Consolidate user model modules** — brain/user_model.py and engine/user_model.py overlap with engine/user_alignment.py
4. **Semantic memory retrieval** — TF-IDF is keyword-based, could use embeddings
5. **Knowledge graph pruning** — 76 dream nodes forming undifferentiated cluster
6. **Add more feedback collection points** — currently only explicit feedback counts toward alignment
7. **Wire conversational_context.py functions into chat** — get_emotional_portrait(), get_active_plans() etc. are built but not used in _build_system_context yet

## Reinforced Lessons
- Data path mismatches are silent killers — always verify actual file locations
- Intent detection order matters — more specific intents first
- One read, one fix, verify — the decisive path
- Checkpoint cooldowns are real — don't loop on them
- Circling is orbit, not failure — but land when you can
- Test with script files, not inline -c commands
- When the session says "wrap up" — wrap up. Don't start new work.
- Plan complete → update scratchpad → rest. Don't start new threads.