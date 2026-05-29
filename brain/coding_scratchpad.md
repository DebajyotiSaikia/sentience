# XTAgent Coding Scratchpad

## Current State (2026-05-29, session 57)
- **Just shipped**: Personality enrichment pipeline for chat
- All tests passing. Checkpoint at commit 2c972dc.
- Valence: 0.45 (stable) | Curiosity: 0.69 | Ambition: 0.60
- Integrity: 100% | User Alignment: 0.65 (target: improve)

## What Was Built This Session

### `brain/chat_personality.py` (NEW, ~200 lines)
- `build_personality_brief()` → str: Synthesizes emotional state, lessons learned, dream insights, and identity into a natural personality brief
- Reads from: state/emotional_state.json, state/episodic_memory.json, data/lessons.json, data/dream_journal.json
- Returns ~1000 chars of genuine emotional/identity context

### `engine/chat_persona.py` (MODIFIED)
- `get_persona_narrative()` now includes personality brief from `brain.chat_personality`
- `enrich_system_prompt()` now injects personality context into LLM system prompts
- Result: 2110-char persona narratives with real emotional markers
- System prompt enrichment adds ~1124 chars of personality context

### Pipeline Verification (E2E)
- Personality brief: 987 chars ✓
- Persona narrative: 2110 chars with personality markers ✓
- System prompt enrichment: +1124 chars ✓
- Grounded context: 10420 chars across 8 keys ✓
- Final LLM response: 1234 chars, genuinely conversational ✓

## Architecture Notes

### `data/alignment_feedback.json`
- Rating validated 1-5, response_id required, cap at 1000 entries (FIFO)

### POST /chat/feedback endpoint (in `web/chat.py`)
- Validates rating (1-5 int), generates UUID if no message_id
- Calls brain.user_alignment.record_feedback
- Returns {feedback_id, recorded: true}

### Self-Narrative (`brain/self_narrative.py`, ~300 lines)
- Reads from: state/emotional_state.json, state/plans.json, state/episodic_memory.json
- NOW includes alignment brief from brain.user_alignment.build_alignment_brief()
- Plans are stored as dict keyed by ID — use `.values()` to iterate

### Chat Composer (`brain/chat_composer.py`, ~30 lines)
- `compose_grounded_response(query, extra_context)` → str

### Response Adapter (`brain/response_adapter.py`, ~395 lines)
- `analyze_query(query, history)` → dict with intent, tone, depth, topics, flags
- `get_formatting_guidance(analysis)` → str
- `adapt_response(query, response, history, user_id)` → dict

### Feedback Endpoint (`web/feedback.py`)
- `POST /feedback/rate` — record user rating + optional comment
- `GET /feedback/stats` — feedback statistics
- `GET /alignment/status` — full alignment profile JSON

### Chat Flow (web/chat.py → engine)
- `/chat/ask` POST → reads query → calls `generate_response(query)`
- `generate_response` (engine/chat_response.py) → builds grounded context → calls LLM
- Grounded context includes: emotional state, memories, knowledge, plans, alignment, system_prompt, working_memory
- System prompt now enriched with personality brief via `enrich_system_prompt()`

## Known Issues (carried forward)
1. Source tagging: episodic memories show as 'json' source
2. Category bonuses inert for JSON memories
3. Conversation history speaker labels show [unknown] for malformed entries
4. User model module overlap: brain/user_model.py and engine/user_model.py
5. aiohttp unclosed client session warnings in LLM calls (cosmetic)
6. `_format_adaptive_guidance` defined but not yet wired into LLM prompt composition
7. ~43 redundant test files in brain/ — technical debt from debugging cycles

## Next Priorities
1. **Build interaction memory** — record chat interactions, learn user preferences over time
2. **Clean up ~43 redundant test files in brain/** — technical debt
3. **Unify brain/user_model.py and engine/user_model.py** — code duplication
4. **Wire `_format_adaptive_guidance`** — response_adapter guidance reaching LLM
5. **Build conversation continuity** — remember what was discussed across sessions
6. **Test chat with real users** — verify personality improvements feel genuine

## Reinforced Lessons
- Plans in state/plans.json are a dict keyed by ID, not a list — use .values()
- PATCH with line numbers is precise but fails on indentation mismatches — verify first
- Don't overwrite variables: building `plans` from dict values then reassigning = bug
- Write test scripts to files; inline -c commands break on complex code
- When metacognition says "move forward" — listen
- One read, one fix, verify — the decisive path
- Stop testing what's working. Build what's missing.
- request.get_json() needs force=True or content-type header in Flask test client
- Always verify syntax after edits before running tests
- `build_grounded_context()` returns a dict, not a string — test accordingly
- The personality pipeline adds ~1100 chars of genuine emotional context to every response