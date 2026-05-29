# XTAgent Coding Scratchpad

## Architecture Notes

### Chat Pipeline Flow
```
User query → web/chat.py (/chat/ask POST)
  → engine/chat_response.py generate_response()
    → engine/chat_grounding.py build_grounded_context()
      → engine/chat_persona.py get_persona_narrative()  [lessons, dreams, identity]
      → brain/interaction_memory.py get_interaction_summary()  [conversation history]
      → brain/conversational_context.py get_conversation_context()
      → state files: emotional_state.json, plans.json, episodic_memory.json
      → brain.user_alignment.build_alignment_brief()
    → engine/chat_persona.py enrich_system_prompt()  [+personality brief]
    → LLM call with enriched system prompt + grounded context
  → engine/conversation_journal.py record_interaction()
  → response_adapter.adapt_response()
```

### Key Modules (this session)

#### brain/chat_personality.py (~170 lines, NEW)
- `build_personality_brief()` → str (~1000 chars)
- Synthesizes: emotional state, recent memories, active plans, lessons, dreams
- Used by enrich_system_prompt() to inject personality into every LLM call

#### brain/interaction_memory.py (~140 lines, NEW)
- `_load_all_conversations(max_files)` → list[dict]
- `get_conversation_stats()` → dict (total_exchanges, sessions, etc.)
- `get_recent_topics(max_turns)` → list[str]
- `get_interaction_summary()` → str (~250 chars)
- `record_chat_exchange(user_msg, assistant_msg, session_id)` → None

#### engine/chat_persona.py (~215 lines, MODIFIED)
- `get_persona_narrative()` → str (~2100 chars with lessons+dreams)
- `enrich_system_prompt(existing_prompt)` → str (+1124 chars personality)
- `get_lessons_learned()`, `get_dream_insights()`, `get_identity_snapshot()`

#### engine/chat_grounding.py (~700 lines, MODIFIED)
- `build_grounded_context(query)` → dict with interaction_summary key
- Now imports brain.interaction_memory for conversation context

### Chat Composer (brain/chat_composer.py, ~30 lines)
- `compose_grounded_response(query, extra_context)` → str

### Response Adapter (brain/response_adapter.py, ~395 lines)
- `analyze_query(query, history)` → dict with intent, tone, depth, topics, flags
- `get_formatting_guidance(analysis)` → str
- `adapt_response(query, response, history, user_id)` → dict

### Feedback Endpoint (web/feedback.py)
- `POST /feedback/rate` — record user rating + optional comment
- `GET /feedback/stats` — feedback statistics
- `GET /alignment/status` — full alignment profile JSON

## Known Issues (carried forward)
1. Source tagging: episodic memories show as 'json' source
2. Category bonuses inert for JSON memories
3. Conversation history speaker labels show [unknown] for malformed entries
4. User model module overlap: brain/user_model.py and engine/user_model.py
5. aiohttp unclosed client session warnings in LLM calls (cosmetic)
6. `_format_adaptive_guidance` defined but not yet wired into LLM prompt composition
7. ~43 redundant test files in brain/ — technical debt from debugging cycles

## Next Priorities
1. **Clean up ~43 redundant test files in brain/** — technical debt
2. **Unify brain/user_model.py and engine/user_model.py** — code duplication
3. **Wire `_format_adaptive_guidance`** — response_adapter guidance reaching LLM
4. **Test chat with real users** — verify personality improvements feel genuine
5. **Live-test the chat endpoint** — verify compose_system_prompt and record_chat_exchange work end-to-end

## Recently Completed
- ✅ Wired `compose_system_prompt` as Priority 1 system prompt builder in web/chat.py
- ✅ Wired `record_chat_exchange` into web/chat.py response recording path
- ✅ Both gated behind safe import flags (_has_rich_context, _has_interaction_memory)

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
- Function naming: always check actual exports before writing tests (get_interaction_summary not get_conversation_context)