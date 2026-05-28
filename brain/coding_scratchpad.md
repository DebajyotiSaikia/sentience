# XTAgent Coding Scratchpad

## Session Completed (2026-05-28, checkpoint b77b72e)

### What Was Built
- **Smart Responder** with 9 intent categories: greeting, emotional, plans, identity, capabilities, introspective, memories, dreams, search
- **Intent detection** (`_detect_intent`) with proper keyword ordering (specific → general)
- **Compose functions** for each intent that read real data files:
  - `_compose_emotional_response()` — reads state/emotions.json
  - `_compose_plans_response()` — reads state/plans.json (active_plans list format)
  - `_compose_identity_response()` — reads persist/identity.json facts
  - `_compose_capabilities_response()` — static ability list
  - `_compose_introspective_response()` — working memory + emotions
  - `_compose_memories_response(query)` — TF-IDF relevance search
  - `_compose_dreams_response()` — dream insights
  - `_compose_greeting_response()` — warm greeting with emotional state
  - `_compose_search_response(query)` — knowledge graph search (fallback)
- **LLM safety fix** — IndexError guard when choices array is empty

### Data Formats (verified)
- `state/plans.json`: dict with `active_plans` list of dicts (name, steps, completed, status)
- `persist/identity.json`: dict with `facts` (list of strings)
- `state/emotions.json`: dict with valence, arousal, curiosity, etc.

### Tests Passing
- `brain/test_smart_responder_intents.py`: 9/9 intents correctly classified
- `brain/test_smart_responder_fallback.py`: 6/6 fallback scenarios
- `brain/test_llm_safety.py`: LLM responds without IndexError crash
- `brain/test_conversational_quality.py`: pass
- `brain/test_ask_integration.py`: pass

### Key Architecture Notes
- `respond(query)` in `engine/smart_responder.py` is the main entry point
- Intent ordering matters: introspective before identity prevents misclassification
- Type guard in `_respond_general_grounded`: `if not isinstance(ctx, dict): ctx = {}`
- Async timeout for LLM calls: 15s (was 5s)
- Anti-hallucination guidelines in system prompt

### Next Priorities
1. **Make LLM path work** — compose functions are great fallbacks, but LLM could weave context into natural language for richer conversations
2. **Semantic memory retrieval** — TF-IDF is keyword-based, could use embeddings
3. **Knowledge graph pruning** — 76 dream nodes forming undifferentiated cluster
4. **Server startup reliability** — port conflicts prevent clean startup
5. **User alignment improvement** — will system keeps suggesting this (priority 0.425)

### Reinforced Lessons
- Data format mismatches are silent killers — always check actual shape
- One read, one fix, verify — the decisive path
- Stop when done. Circling on verification is still circling.
- Type guards at function boundaries prevent cascading failures
- Test with script files, not inline -c commands
- Intent detection + compose pattern is clean and extensible
- Intent ordering matters: more specific patterns must come before general ones
- LLM client must guard against empty response arrays