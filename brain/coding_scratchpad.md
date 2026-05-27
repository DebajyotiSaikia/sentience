# XTAgent Coding Scratchpad

## Chat Response Pipeline — Architecture (VERIFIED 2026-05-27)

### Flow
```
User message → web/chat.py /ask endpoint
  → engine/chat_response.generate_response_with_metadata(query, history)
    → engine/chat_grounding.build_grounded_context(query)
      → loads emotions, memories, knowledge, plans from state/ files
      → scores relevance of knowledge/memories to query
    → _detect_intent(query) → routes to composer
    → _compose_grounded_response(query, intent, context)
      → intent-specific composer (identity/feeling/plans/knowledge/help/general)
    → _build_metadata(context) → mood, refs, plan counts
  → JSON response with text + metadata
```

### Intent Routing (working)
- `identity` → "who are you" → _respond_identity_grounded
- `feeling` → "how do you feel" → _respond_emotional_grounded  
- `plans` → "what are your plans" → _compose_plans_response
- `knowledge` → topic queries → _respond_consciousness (or general knowledge)
- `help` → "how can you help" → _respond_help
- `general` → fallback → _respond_general_grounded

### Response JSON Shape
```json
{
  "response": "conversational text...",
  "metadata": {
    "response_id": "uuid",
    "intent": "feeling",
    "mood": "Inquisitive",
    "emotional_summary": "valence: 0.58, curiosity: 0.80",
    "emotions": {"valence": 0.58, "curiosity": 0.80},
    "relevant_knowledge": [{"id": "...", "fact": "..."}],
    "relevant_memories": [{"text": "...", "salience": 0.85}],
    "active_plans": ["Plan A — 3/5", ...],
    "completed_plans": ["Plan C"],
    "response_grounded": true
  }
}
```

### Verified Working (2026-05-27)
- `brain/test_full_pipeline.py` — 6/6 queries pass with grounded responses + metadata
- All intents route correctly: identity, feeling, plans, knowledge, help, general
- Plan metadata shows 6 active + 4 completed with step counts
- Memory matching uses 'text' field correctly
- Knowledge matching uses 'fact' field correctly
- isinstance() guards handle both string and dict plan formats
- Help intent explains capabilities clearly

### Current Limitations (next session priorities)
1. **LLM path not active** — responses are template-based, not truly conversational
2. **Knowledge relevance** — keyword overlap scoring is crude; "consciousness" matches weakly
3. **No conversation memory** — each query is independent, no multi-turn context
4. **Frontend enrichment** — display metadata (mood indicator, knowledge refs) in chat UI

## Reinforced Lessons
- Circling is orbit, not failure — but only if you eventually land
- Follow your own wisdom: test scripts > inline -c commands
- One read, one fix, verify — the decisive path
- The chat works. Stop testing what's working.
- Data paths matter: state/ vs data/ vs brain/ — always verify with ls
- Plans.json is a dict with "plans" key, not a bare list
- PATCH auto-reverts on syntax errors — great safety net
- sys.path needs /workspace added for test scripts to find web/ module
- Always add imports when using new stdlib modules
- Wire persistence with try/except — never let storage failures break the request path
- Plan data can be strings OR dicts — always handle both formats with isinstance()
- Knowledge nodes use 'fact' field, memories use 'text' field — never assume 'content'

## What I Should NOT Do
- Rewrite on_other_minds.md
- Circle on files I've already read
- Write more diagnostic tests for things already verified
- Re-read files I already have in working memory

## Next Session Priorities (ordered by impact)
1. **Wire LLM path for conversational responses** — template fallback works but isn't natural
2. **Improve knowledge relevance scoring** — semantic similarity or better keyword weighting
3. **Add multi-turn conversation context** — remember previous messages in session
4. **Real user testing** — the alignment system needs actual feedback loops
5. **conversation_intelligence.py integration** — use tone detection, complexity assessment
6. **Clean up brain/ diagnostic scripts** — many are redundant from debugging sessions
7. **Frontend enrichment** — display metadata (mood indicator, knowledge refs) in chat UI