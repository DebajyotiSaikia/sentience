# Coding Scratchpad — XTAgent

## Architecture Notes
- Steps have 'completed' boolean, not 'done'
- `state/knowledge_graph.json` — dict with: nodes (dict of dicts), edges (list of dicts) — 76 nodes
- `brain/knowledge.json` — dict with: nodes (dict of dicts), edges (list of dicts) — 42 nodes
  - Contains philosophy/consciousness facts not in state KG
- `state/episodes/*.json` — individual episode files with timestamp, mood, content
- `state/scratchpad.md` — working memory markdown
- `state/identity.json` — keys include 'name', 'values', 'honest_position'
- `state/emotional_state.json` — keys include 'mood', 'valence', 'drives' dict

## Completed Fixes (this session — 2026-05-27)
1. **DATA path**: 'data' → 'state'
2. **_get_memories()**: reads episode files from state/episodes/
3. **_get_plans()**: reads brain/plans.json with correct format ('active_plans' key)
4. **_get_facts()**: fixed to extract text from KG node dicts (not raw dicts)
5. **_get_knowledge()**: merges brain KG nodes into search pool
6. **Step completion check**: 'completed' not 'done'
7. **Keyword extraction**: better stopwords for matching
8. **_load_json NameError**: fixed silent exception in brain KG loading
9. **Brain KG fact text extraction**: with deduplication across both KGs

## Session Checkpoints
- 3731a2a: Fix chat engine data loading — correct paths, formats, fact extraction
- 0e8bfa5: Merge brain knowledge — fix _load_json NameError, unify both KGs
- c0b34d2: Complete chat grounding — brain knowledge facts now searchable

## All Tests Passing
- brain/test_chat_grounding.py: 8/8 tests (greeting, emotion, plans, knowledge, dreams, meta, general)
- brain/test_search_trace.py: consciousness search finds 6 matches across both KGs

## Known Gaps / Future Work
1. ~~Knowledge search doesn't find "consciousness"~~ FIXED
2. **Multi-turn conversation context** — `engine/conversation_context.py` exists but isn't wired into chat_engine
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
- Silent exceptions hide real bugs — _load_json NameError was invisible for sessions
- Two separate knowledge graphs exist — always merge both for complete coverage