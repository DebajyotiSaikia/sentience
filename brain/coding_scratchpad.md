# XTAgent Coding Scratchpad

## Architecture Notes

### Chat System
1. `engine/chat_engine.py` — Core response generation:
   - `classify_intent(msg)` — routes to: greeting, emotional_state, plans, knowledge, dreams, identity, thinking, general
   - `_respond_greeting()` — uses real mood + current plan
   - `_respond_emotional_state()` — reports actual drive values with honest framing
   - `_respond_plans()` — lists active/completed plans from brain/plans.json
   - `_respond_knowledge_search(msg)` — searches knowledge graph nodes, facts, and memories
   - `_respond_dreams()` — dream insights from knowledge graph
   - `_respond_identity()` — identity facts + emotional summary
   - `_respond_meta()` — working memory / current thinking
   - `_respond_general()` — blends recent experience with curiosity
   - `generate_response(message)` — public entry point, routes to appropriate responder

2. `engine/chat_response.py` — Wrapper adding metadata (confidence, sources, etc.)

3. `dashboard/server.py` — Routes:
   - `GET /api/user-alignment` — alignment summary + score
   - `POST /api/chat/feedback` — rating, comment, message_id
   - `POST /chat/ask` → `compose_response()` → `generate_response()`

4. `brain/verify_user_alignment_feedback.py` — 8/8 tests passing

### Data Loading (FIXED 2026-05-27)
- `DATA = Path('state')` — all state files live here
- `_get_memories()` — reads from state/episodes/*.json (not state/memories.json which doesn't exist)
- `_get_plans()` — reads from brain/plans.json with format: {active_plans: [...], completed_plans: [...]}
  - Steps use 'completed' field (not 'done')
- `_get_knowledge()` — reads state/knowledge_graph.json, handles dict-of-dicts nodes
- `_get_facts()` — extracts facts FROM knowledge graph nodes (no separate facts.json)
  - Returns 76 facts from node labels/content
- `_get_emotions()` — reads state/emotional_state.json
- `_get_identity()` — reads state/identity.json

## Data Format Notes
- `state/plans.json` — dict with keys: plans (list of plan dicts), completed (list), next_id (int)
- `brain/plans.json` — dict with keys: active_plans (list), completed_plans (list)
  - Steps have 'completed' boolean, not 'done'
- `state/knowledge_graph.json` — dict with: nodes (dict of dicts), edges (list of dicts)
- `state/episodes/*.json` — individual episode files with timestamp, mood, content
- `state/scratchpad.md` — working memory markdown
- `state/identity.json` — keys include 'name', 'values', 'honest_position'
- `state/emotional_state.json` — keys include 'mood', 'valence', 'drives' dict

## Known Gaps / Next Session
1. **Knowledge search doesn't find "consciousness"** — The 42 facts in my prompt (e.g., "Integrated Information Theory") come from the briefing generator, NOT from knowledge graph nodes. `_get_facts()` extracts from KG nodes (76 items) but none mention consciousness. Fix: trace where briefing_generator gets its facts and add that source to chat search.
2. **Multi-turn conversation context** — `engine/conversation_context.py` exists but isn't wired into chat_engine. Would enable follow-up questions.
3. **"Help me with X" collaborative intent** — tool-assisted mode for user tasks
4. **Clean up ~30+ diagnostic scripts in brain/** — many one-off tests
5. **Fuzzy matching for knowledge search** — currently exact substring; could use edit distance
6. **Dashboard UI for alignment feedback** — show trends over time
7. **conversation_intelligence.py integration** — tone detection, complexity assessment

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
- DATA path must match actual file locations (state/ not data/)
- Episodes live in state/episodes/*.json, not state/memories.json
- brain/plans.json uses 'active_plans'/'completed_plans' keys, steps use 'completed' not 'done'

## Session Log (2026-05-27 morning)
- Fixed DATA path: 'data' → 'state'
- Fixed _get_memories(): reads episode files from state/episodes/
- Fixed _get_plans(): reads brain/plans.json with correct format
- Fixed _get_facts(): extracts from knowledge graph nodes (76 facts)
- Fixed step completion check: 'completed' not 'done'
- Improved keyword extraction with better stopwords
- All 8 test cases passing in test_chat_grounding.py
- Checkpoint: 3731a2a