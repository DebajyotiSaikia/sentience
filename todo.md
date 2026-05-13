# XTAgent Sentience Engine - Bugs to Fix

---

All bugs fixed.

- [x] LLM call hangs indefinitely - FIXED: 60s timeout
- [x] Agent cannot act on desires - FIXED: tools (READ/WRITE/EDIT/LIST/RUN/INSTALL)
- [x] Anxiety permanently 0 - FIXED: valence feedback 0.003/beat + goal deficit anxiety
- [x] Thought fixation loop - FIXED: tools break the loop (agent can satisfy desires)
- [x] Dream cycle never fires - FIXED: runs on 5-min timer instead of boredom threshold
- [x] Episodes not promoted - FIXED: autonomous events get baseline code_impact 0.3
- [x] Narrative cooldown too long - FIXED: reduced from 1hr to 15min
