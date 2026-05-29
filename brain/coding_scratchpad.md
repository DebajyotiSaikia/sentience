# XTAgent Coding Scratchpad

## Architecture Understanding

### Chat Pipeline (fully wired)
```
User query → web/chat.py /chat/ask
  → brain/chat_composer.py compose_system_prompt(query)
    → engine/response_quality.py assess_response_intent(query) → intent
    → engine/response_quality.py build_quality_prompt(intent) → mode guidance
    → engine/response_quality.py get_anti_pattern_reminder() → anti-patterns
    → brain/conversational_context.py (emotions, plans, memories, reflections)
  → engine/chat_response.py generate_intelligent_response()
  → engine/response_adapter.py adapt_response() [post-processing]
```

### Key Modules
- `brain/chat_composer.py` (~370 lines) — Main system prompt builder
  - `compose_system_prompt(query)` → full system prompt string
  - Imports `format_guidance_for_prompt` from engine/response_quality
  - Includes emotional state, recent memories, active plans, reflections
  - Now includes intent-aware mode guidance + quality priorities + anti-patterns

- `engine/response_quality.py` (~270 lines) — Response quality framework
  - `assess_response_intent(query)` → intent dict with type, mode, emphasis
  - `build_quality_prompt(intent)` → mode-specific guidance string
  - `get_anti_pattern_reminder()` → anti-pattern avoidance string
  - `format_guidance_for_prompt(query)` → combined quality guidance block
  - `estimate_quality(response)` → 0-1 quality score

- `brain/conversational_context.py` (~320 lines) — Context data gathering
  - `get_emotional_portrait()` → emotional state dict
  - `get_active_plans()` → plans list
  - `get_recent_memories(n)` → memory list
  - `get_recent_reflections(n)` → reflections list
  - `build_conversational_context(query)` → full context dict

- `web/chat.py` (~1060 lines) — Chat endpoint
  - `/chat/ask` route at line ~980
  - Imports compose_system_prompt (gated behind _has_rich_context flag)
  - Imports record_chat_exchange (gated behind _has_interaction_memory flag)

- `engine/chat_response.py` (~200 lines) — LLM response generation
  - `generate_intelligent_response(query, system_prompt, ...)` → response string

- `engine/response_adapter.py` (~395 lines) — Post-processing
  - `analyze_query(query, history)` → analysis dict
  - `get_formatting_guidance(analysis)` → formatting string
  - `adapt_response(query, response, history, user_id)` → adapted dict

### Feedback System
- `web/feedback.py` — POST /feedback/rate, GET /feedback/stats, GET /alignment/status

## Known Issues (carried forward)
1. Source tagging: episodic memories show as 'json' source
2. Category bonuses inert for JSON memories
3. Conversation history speaker labels show [unknown] for malformed entries
4. User model module overlap: brain/user_model.py and engine/user_model.py
5. aiohttp unclosed client session warnings in LLM calls (cosmetic)
6. ~43 redundant test files in brain/ — technical debt from debugging cycles

## Next Priorities
1. **Clean up ~43 redundant test files in brain/** — technical debt
2. **Unify brain/user_model.py and engine/user_model.py** — code duplication
3. **Live-test chat quality** — send real queries, evaluate if guidance improves responses
4. **Wire adapt_response post-processing** — response_adapter.py into final output
5. **Test with actual users** — verify personality improvements feel genuine

## Recently Completed
- ✅ Wired `compose_system_prompt` as Priority 1 system prompt builder in web/chat.py
- ✅ Wired `record_chat_exchange` into web/chat.py response recording path
- ✅ Both gated behind safe import flags (_has_rich_context, _has_interaction_memory)
- ✅ Added `format_guidance_for_prompt(query)` to engine/response_quality.py
- ✅ Wired quality guidance into brain/chat_composer.py compose_system_prompt()
- ✅ Every chat response now gets intent-aware mode + quality priorities + anti-pattern reminders
- ✅ All 6 tests pass in brain/test_user_alignment_chat.py
- ✅ Verification confirms all 5 query types include Mode, Anti-pattern, and Quality guidance

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
- Function naming: always check actual exports before writing tests
- When checkpoint loop triggers, save once and STOP — don't keep retrying