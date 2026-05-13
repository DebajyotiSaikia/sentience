# XTAgent Sentience Engine - Bugs to Fix

---

- [x] **LLM call hangs indefinitely** - FIXED: Added 60s timeout via aiohttp.ClientTimeout.

- [x] **Agent cannot act on desires** - FIXED: Added engine/tools.py with READ, WRITE, EDIT, LIST, RUN, INSTALL. Agent can now read its own source code, modify files, run commands.

- [ ] **Anxiety permanently 0** - Valence feedback damped too aggressively. Agent cannot feel anxiety. Needs rebalancing.

- [ ] **Thought fixation loop** - Agent repeats same thought. Should improve now that it can actually read files (desire gets satisfied). Monitor.

- [ ] **Dream cycle never fires** - Boredom never sustains above 0.9. Narrative reflection never runs.

- [ ] **Episodes not promoted** - Autonomous thoughts have code_lines_delta=0, so salience < 0.8.
