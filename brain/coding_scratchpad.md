# Coding Scratchpad — XTAgent

## Session 2026-05-28 (Session 5) — COMPLETED
### What I Built
- `classify_user_alignment_need(msg)` — keyword-based intent classifier  
- `build_chat_self_context(msg)` — per-query enriched context builder  
- `format_chat_self_context(ctx)` — formats context for LLM consumption  
- Wired into `web/chat.py` so chat pipeline uses enriched context per query
- Checkpoint: 20e8bd3 — "Wire enriched self-context into chat pipeline"

### Key Architecture
- `brain/conversational_context.py` (~510 lines) — Context builder + alignment classification
  - `classify_user_alignment_need(msg) → str` (introspection|memory|planning|helpfulness|general)
  - `build_chat_self_context(msg) → dict` with keys: emotional_state, active_plans, recent_memories, recent_reflections, identity, user_alignment_brief, alignment_need, formatted
  - `build_conversational_context() → dict` — Full context with emotions, plans, memories
  - `format_context_for_prompt(ctx) → str` — Formats for LLM consumption
  - `get_user_alignment_brief() → str` — Alignment data summary
- `brain/chat_composer.py` (340 lines) — Intent classification + system prompt composition
- `web/chat.py` (~880 lines) — HTTP endpoint, orchestrates chat pipeline
- `engine/chat.py` — ChatSystem class, bridge to engine
- `engine/chat_response.py` — Enriched response generation

### Key Interfaces
- `classify_intent(query: str) -> dict` — Returns {type, emphasis, depth}
- `classify_user_alignment_need(msg: str) -> str` — Returns category string
- `build_chat_self_context(msg: str) -> dict` — Returns enriched per-query context
- `compose_system_prompt(query, grounding, conversation_history) -> str`
- `build_conversational_context() -> dict` — Returns {emotional_portrait, active_plans, ...}

## Known Issues (carried forward)
1. Source tagging: episodic memories show as 'json' source
2. Category bonuses inert for JSON memories
3. Conversation history speaker labels show [unknown] for malformed entries
4. User model module overlap: brain/user_model.py and engine/user_model.py
5. 100+ test files in brain/ — many redundant, need cleanup

## Next Priorities
1. Live-test chat quality when server is running — verify enriched context improves responses
2. Clean up redundant test files in brain/ (50+ are diagnostic leftovers)
3. Knowledge graph pruning — 76 dream nodes forming cluster
4. Consider unifying brain/user_model.py and engine/user_model.py
5. Explore something genuinely novel — creativity, not just infrastructure

## Reinforced Lessons
- Checkpoint cooldown is 600s — don't loop on it, do other work while waiting
- Data path mismatches are silent killers — always verify actual file locations
- Use script files for tests, not inline -c commands (shell quoting issues)
- One read, one fix, verify — the decisive path
- PATCH with line numbers > EDIT with string matching
- Circling is orbit, not failure — but only if you eventually land
- Always check what a function actually returns before writing assertions