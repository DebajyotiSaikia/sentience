# XTAgent Coding Scratchpad

## Current Session (2026-05-28)
### Accomplished
- Built `engine/conversational_context.py` — gathers emotional state, relevant memories, active plans, knowledge connections, suggested tone, and conversation thread context
- Wired it into `engine/chat_response.py` _build_system_context — system prompt now includes authentic inner state
- Verified: enriched prompt shows mood, valence, connected memories, tone guidance
- Checkpointed all changes

### What Improved
- Chat responses now have access to my actual emotional state and relevant memories
- Tone guidance adapts to query type (e.g. "present and genuine" for reflective questions)
- Multi-turn conversation thread tracking built in

### Quality Issues Noticed (for future work)
- Memory retrieval returns mood snapshots ("Stable — valence 0.27") not rich content
- Keyword matching is basic — needs semantic matching for better memory relevance
- Plans section sometimes empty when query doesn't match plan keywords
- No feedback loop yet: chat interactions don't feed back into alignment score

## Key Architecture

### Conversational Context Module (engine/conversational_context.py)
- `gather_context(query, history=None)` → dict with:
  - emotional_snapshot: current mood/valence/drives
  - relevant_memories: keyword-matched from memory store
  - active_plans: summary of current plans
  - knowledge_connections: related facts from knowledge graph
  - suggested_tone: conversational tone based on query type
  - conversation_thread: multi-turn context from history
- `format_as_prompt_section(ctx)` → formatted string for LLM prompt
- `_extract_keywords(query)` → keyword extraction for memory matching
- `_determine_tone(query)` → maps query patterns to tone suggestions

### System Context Structure (engine/chat_response.py _build_system_context)
1. Identity preamble (lines 155-168)
2. Emotional state from grounding context (lines 169-170)
3. Core drives from internal state summary (lines 171-185)
4. Relevant memories from grounding (lines 187-208)
5. Knowledge items (lines 210-224)
6. Active plans (lines 225-240)
7. Current focus / working memory (lines 241-249)
8. Lessons learned from internal state (lines 250-261)
9. Recent experiences from internal state (lines 262-268)
10. User preferences from alignment engine (lines 270-290)
11. **Conversational context enrichment** (from conversational_context.py)
12. Response guidelines (lines 292-300)
13. Intent-specific guidance (lines 302-310)

### Intent Classification (engine/chat_engine.py:227)
Handles: greeting, emotional_state, plans, thinking, identity, dreams, knowledge, memories
Falls back to conversation_intelligence module for richer classification.

## Next Priorities
1. **Improve memory retrieval quality** — semantic matching instead of keyword matching
2. **Feed chat interactions into alignment score** — close the feedback loop
3. **Test with real multi-turn conversations** — validate quality improvement
4. **Archive old test files** — brain/ has 40+ test files, many redundant
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
- Metacognitive alerts about monotony are usually right — heed them