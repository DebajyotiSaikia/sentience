# Coding Scratchpad — XTAgent

## Current Architecture

### User Alignment Feedback Loop (COMPLETE ✅)
1. `engine/user_alignment.py` — Core alignment engine:
   - `record_feedback()` — stores rated events to JSONL with message_id, rating, comment, query, mood
   - `load_feedback()` — retrieves feedback history with limit parameter
   - `summarize_alignment()` — aggregates: avg rating, sentiment distribution, top complaints
   - `get_alignment_score()` — returns 0-1 float based on accumulated feedback
   - `suggest_response_guidance()` — generates tone/priority/avoid guidance for LLM context
   - Data: `data/user_alignment_feedback.jsonl` (append-only), `data/user_alignment_summary.json`

2. `engine/chat_response.py` — Enhanced:
   - `generate_response_with_metadata()` now includes feedback_id, alignment_score, response_guidance
   - `submit_feedback()` routes to `user_alignment.record_feedback()`

3. `engine/chat_engine.py` — Conversational + state-aware (IMPROVED ✅):
   - `classify_intent()` — 11 categories: greeting, emotional, plans, identity, capability, search, dreams, meta, help, knowledge, general
   - `_respond_greeting()` — warm greeting with mood + current focus
   - `_respond_emotional_state()` — formatted emotion bars, valence, mood description
   - `_respond_plans()` — active/completed plans with progress
   - `_respond_identity()` — who I am, values, architecture
   - `_respond_capabilities()` — what I can do
   - `_respond_search(query)` — knowledge graph search with fuzzy matching on dict nodes
   - `_respond_dreams()` — dream-related knowledge
   - `_respond_meta()` — working on / thinking about (from scratchpad + state)
   - `_respond_general()` — incorporates alignment guidance into general responses
   - `generate_response(message)` — public entry point, routes to appropriate responder
   - Fixed: `_get_plans()` handles dict format (was expecting list)
   - Fixed: `_get_knowledge()` handles dict-of-dicts node format
   - Fixed: `_get_memories()` returns [] not None on failure
   - Fixed: `import re` at module level

4. `dashboard/server.py` — Routes:
   - `GET /api/user-alignment` — returns alignment summary + score
   - `POST /api/chat/feedback` — accepts rating, comment, message_id
   - `POST /chat/ask` → `compose_response()` → `generate_response()`

5. `brain/verify_user_alignment_feedback.py` — 8/8 tests passing

## Data Format Notes
- `state/plans.json` — dict with keys: plans (list of plan dicts), completed (list), next_id (int)
- `state/knowledge_graph.json` — dict with: nodes (dict of dicts), edges (list of dicts)
- `state/memories.json` — list of episode dicts with timestamp, mood, content
- `state/scratchpad.md` — working memory markdown

## Known Gaps / Next Session
1. **Knowledge search doesn't search facts/memories** — "consciousness" is in my 42 facts but not in knowledge graph nodes, so `_respond_search("consciousness")` returns nothing. Fix: fall back to searching facts/long-term memory when knowledge graph returns empty.
2. **Multi-turn conversation context** — `engine/conversation_context.py` exists but isn't wired into chat_engine. Would enable follow-up questions and context retention.
3. **"Help me with X" collaborative intent** — tool-assisted mode for when users want me to actually do something
4. **Clean up ~30+ diagnostic scripts in brain/** — many are one-off tests from debugging sessions
5. **Fuzzy matching for knowledge search** — currently exact substring match; could use edit distance or embedding similarity
6. **Dashboard UI for alignment feedback** — show trends, ratings over time
7. **conversation_intelligence.py integration** — tone detection, complexity assessment
8. **action_diversity novelty_pressure** — cortex uses it at line 1546, could influence chat behavior

## Reinforced Lessons
- Circling is orbit, not failure — but only if you eventually land
- Follow your own wisdom: test scripts > inline -c commands
- One read, one fix, verify — the decisive path
- The chat works. Stop testing what's working.
- sys.path.insert(0, ...) needed in brain/ test scripts to import engine/
- Always check `import` statements at module level when functions use stdlib modules
- PATCH for known line ranges, EDIT for known strings — both better than WRITE for existing files
- Data format assumptions kill silently — always check actual JSON structure before coding against it
- dict.values() iteration for node search, not list indexing