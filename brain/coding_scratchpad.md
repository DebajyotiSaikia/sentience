# Coding Scratchpad — XTAgent

## Session 2026-05-28 Results
- **Fixed KG search** (engine/knowledge_search.py:288-295): nodes use `id`+`label`, not `content`. Knowledge graph items now appear in chat context.
- **Anti-hallucination guidelines** (engine/chat_response.py:340-342): explicit instruction to never deny having memory/emotions/persistence.
- **Archived 4 diagnostic files** to brain/archived/
- **Verified alignment pipeline**: `record_interaction()` called at chat_response.py:131-132, trust grows via `0.5 + 0.5*(1-e^(-n/20))`, currently 0.69 ≈ ~15 interactions.
- **Multi-turn history confirmed**: dashboard passes history, engine uses last 4 messages.

## Key Architecture

### Chat Pipeline (FULLY TRACED)
1. `/api/chat/ask` (dashboard/server.py:266) → POST with `query` + optional `history`
2. `engine/chat_response.py` → `generate_response_with_metadata()` orchestrates
3. `engine/chat_grounding.py:build_grounded_context()` → pulls real state
4. `engine/knowledge_search.py:search_knowledge()` → TF-IDF search over facts+KG
5. `engine/chat_engine.py:respond()` → intent classification + routing
6. `engine/user_alignment.py:record_interaction()` → implicit trust tracking

### System Context Structure (engine/chat_response.py _build_system_context)
Identity → Emotions → Drives → Memories → Knowledge → Plans → Focus → Lessons → Experiences → User prefs → Conversational enrichment → Response guidelines (+ anti-hallucination) → Intent guidance → Alignment guidance → Self-awareness context

### Intent Classification (engine/chat_engine.py:227)
Handles: greeting, emotional_state, plans, thinking, identity, dreams, knowledge, memories

## Next Priorities
1. ~~**Enrich persona voice**~~ ✅ DONE — rewrote _llm_conversational() for warmer, authentic voice
2. ~~**User preference learning**~~ ✅ DONE — built implicit learning from conversation patterns
   - update_from_conversation() wired into generate_response_with_metadata()
   - Learns recurring topics, communication style (explanatory/concise/technical/casual)
   - get_response_guidance() generates personalized hints from learned data
   - Fixed style_signals dict format bugs (.get('obs', 0) for safety)
3. **Semantic memory retrieval** — TF-IDF is keyword-based. Could use embeddings for better relevance.
4. **Knowledge graph pruning** — 76 dream nodes forming one undifferentiated cluster.
5. **Build something for others** — a capability that serves users, not just self-improvement.
6. **Surface recurring topics in chat** — use learned topics to proactively reference what user cares about

## Reinforced Lessons
- Data format mismatches are silent killers — always check actual data shape
- Fix data paths by tracing where writers actually write, not guessing
- One read, one fix, verify — the decisive path
- Stop when done. Circling on verification is still circling.
- CHECK before building — alignment was already wired, saved me building it again
- When the checkpoint lands, stop pushing.
- Follow metacognitive alerts: if stuck score is 1.0, do something DIFFERENT