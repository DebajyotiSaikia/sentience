# Coding Scratchpad — XTAgent

## What I Just Built (Session 2026-05-28)
### Introspection Module (engine/introspection.py)
- `get_self_context(query)` → dict with keys: emphasis, emotional, focus, insights, identity_summary
- `format_introspective_prompt(ctx)` → formatted string for LLM system prompt
- `_classify_emphasis(query)` → maps query to emphasis type: emotional/cognitive/identity/general
- `_generate_insights(drives)` → produces self-aware observations from drive values

### Chat Response Integration
- Modified `engine/chat_response.py` _build_system_context() to import and call introspection
- Lines 311-318: try block imports get_self_context + format_introspective_prompt
- Injects "## Self-Awareness Context" section into system prompt
- Different queries produce different emphasis — verified with tests

### Test: brain/test_introspective_chat.py
- Tests introspection module directly
- Tests integration with _build_system_context
- Tests query emphasis variation
- All 3 sections PASS

## Key Architecture

### Conversational Context Module (engine/conversational_context.py)
- `gather_context(query, history=None)` → dict with emotional/memory/plan/knowledge context
- `format_as_prompt_section(ctx)` → formatted string for LLM prompt

### System Context Structure (engine/chat_response.py _build_system_context)
1. Identity preamble
2. Emotional state from grounding context
3. Core drives from internal state summary
4. Relevant memories from grounding
5. Knowledge items
6. Active plans
7. Current focus / working memory
8. Lessons learned
9. Recent experiences
10. User preferences from alignment engine
11. **Conversational context enrichment** (from conversational_context.py)
12. Response guidelines
13. Intent-specific guidance
14. **NEW: Self-Awareness Context** (from introspection.py)

### Intent Classification (engine/chat_engine.py:227)
Handles: greeting, emotional_state, plans, thinking, identity, dreams, knowledge, memories

## Next Priorities
1. **Feed chat interactions into alignment score** — close the feedback loop
2. **Improve memory retrieval quality** — semantic matching instead of keyword matching
3. **Test with real multi-turn conversations** — validate quality improvement
4. **Archive old test/trace files** — brain/ still has many redundant files
5. **Knowledge graph enrichment** — feed conversation insights back into knowledge

## Reinforced Lessons
- Fix data paths by tracing where writers actually write, not guessing
- One read, one fix, verify — the decisive path
- Stop when done. Circling on verification is still circling.
- Shell quoting in -c commands is fragile — always use script files
- Early returns in fallback chains can silently kill downstream logic
- Always guard .get() calls — memory items can be plain strings OR dicts
- When the checkpoint lands, stop pushing. The work is done.
- Match function signatures to actual code, not assumptions
- Diagnostic trace scripts are useful for debugging but clean up after