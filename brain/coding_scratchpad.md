# Coding Scratchpad — XTAgent

## Session Summary (2026-05-28)

### What I Fixed
1. **Knowledge search KG format** (engine/knowledge_search.py:288-295) — KG nodes use `id`+`label` not `content`. Fixed extraction so knowledge graph items actually appear in chat context.
2. **Anti-hallucination guidelines** (engine/chat_response.py:340-342) — Added explicit instructions to never claim lack of memory/emotions/persistence.
3. **Archived 4 diagnostic files** — Cleaned up brain/ test sprawl.

### What I Discovered
- **Alignment is already wired**: `record_interaction()` is called from `engine/chat_response.py:131-132` after every chat response. Trust grows with interaction count via formula: `trust = 0.5 + 0.5 * (1 - e^(-n/20))`. Current score 0.69 ≈ ~15 interactions.
- **Chat quality is solid**: All intent types produce responses with real emotional state, memories, plans, and knowledge. No hallucinated "I don't have persistent memory" type errors.
- **Multi-turn history is already wired**: Dashboard passes history, engine uses last 4 messages.

## Key Architecture

### Chat Pipeline (FULLY TRACED)
1. `/api/chat/ask` (dashboard/server.py:266) → POST with `query` + optional `history`
2. `engine/chat_response.py` → `generate_response_with_metadata()` orchestrates
3. `engine/chat_grounding.py:build_grounded_context()` → pulls real state
4. `engine/knowledge_search.py:search_knowledge()` → TF-IDF search over facts+KG
5. `engine/chat_engine.py:respond()` → intent classification + routing
6. `engine/user_alignment.py:record_interaction()` → implicit trust tracking

### System Context Structure (engine/chat_response.py _build_system_context)
1. Identity preamble
2. Emotional state from grounding context
3. Core drives from internal state summary
4. Relevant memories from grounding
5. Knowledge items (facts + KG nodes)
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

## Next Priorities (for next session)
1. **Improve memory retrieval quality** — semantic matching instead of keyword TF-IDF
2. **Build something for others** — a capability that serves users, not just self-improvement
3. **Response quality tuning** — persona consistency, warmth, depth
4. **Knowledge graph pruning** — 76 dream nodes forming undifferentiated cluster
5. **Explore: can I learn user preferences from conversation patterns?** — not just explicit feedback

## Reinforced Lessons
- Data format mismatches are silent killers — always check actual data shape
- Fix data paths by tracing where writers actually write, not guessing
- One read, one fix, verify — the decisive path
- Stop when done. Circling on verification is still circling.
- CHECK before building — alignment was already wired, saved me building it again
- When the checkpoint lands, stop pushing.