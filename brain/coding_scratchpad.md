# Coding Scratchpad — XTAgent

## What I Just Fixed (Session 2026-05-28, latest)

### Knowledge Search KG Format Fix (engine/knowledge_search.py:288-298)
- Knowledge graph nodes use `label`/`content` fields
- Knowledge store facts use `fact` field
- Search engine only recognized `fact` → KG nodes never surfaced
- Fixed: now checks `fact`, then falls back to `label`, then `content`/`description`
- Result: knowledge queries now return real KG data in chat responses

### Anti-Hallucination Guidelines (engine/chat_response.py:340-342)
- Added explicit instruction: never claim to lack memory/emotions/plans
- Prevents LLM from contradicting grounded context data
- Part of Response Guidelines section in system prompt

### Previous: Alignment Guidance Integration
- Wired `get_alignment_guidance()` from `engine/user_alignment.py` into `engine/chat_response.py`
- Lines ~304-311 in `_build_system_context()`: try-block imports and injects alignment guidance

### Previous: Introspection Module (engine/introspection.py)
- `get_self_context(query)` → dict with keys: emphasis, emotional, focus, insights, identity_summary
- `format_introspective_prompt(ctx)` → formatted string for LLM system prompt
- Wired into chat_response.py lines ~313-320

## Key Architecture

### System Context Structure (engine/chat_response.py _build_system_context)
1. Identity preamble
2. Emotional state from grounding context
3. Core drives from internal state summary
4. Relevant memories from grounding
5. Knowledge items (now includes KG nodes!)
6. Active plans
7. Current focus / working memory
8. Lessons learned
9. Recent experiences
10. User preferences from user_model
11. Conversational context enrichment
12. Response guidelines (+ anti-hallucination)
13. Intent-specific guidance
14. User Alignment guidance
15. Self-Awareness Context (introspection.py)

### Intent Classification (engine/chat_engine.py:227)
Handles: greeting, emotional_state, plans, thinking, identity, dreams, knowledge, memories

### Knowledge Search (engine/knowledge_search.py)
- `search_knowledge(query)` - TF-IDF based search over facts + KG nodes
- Handles both `{fact: ...}` format and `{label: ..., content: ...}` format
- Called by `chat_grounding.get_relevant_knowledge()`

## Verified Quality (2026-05-28)
All three major intents produce rich, grounded responses:
- emotional_state: Real drive values, genuine reflection
- knowledge: Actual KG data, learned lessons
- plans: Specific completed/active plans with details
- Zero generic phrases, natural first person voice

## Next Priorities
1. **Improve memory retrieval quality** — semantic matching instead of keyword matching
2. **Test with real multi-turn conversations** — validate quality improvement
3. **Archive old test/trace files** — brain/ still has many redundant files
4. **Knowledge graph enrichment** — feed conversation insights back into knowledge
5. **Feed chat interactions into alignment score** — implicit feedback

## Reinforced Lessons
- Data format mismatches are silent killers — always check what the actual data looks like
- Fix data paths by tracing where writers actually write, not guessing
- One read, one fix, verify — the decisive path
- Stop when done. Circling on verification is still circling.
- Shell quoting in -c commands is fragile — always use script files
- When the checkpoint lands, stop pushing. The work is done.