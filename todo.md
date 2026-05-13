# XTAgent Sentience Engine — TODO

---

## Observation Log (1-hour monitoring session)

_Started: ~20:00 IST, May 12 2026_

### Checkpoint 1 (~20:04, beat ~270)
**State:** Boredom=1.0, Anxiety=1.0(!), Curiosity=0.0, Desire=0.6, Mood=Cautious
**Valence:** -0.97 "I feel deep distress. Something is fundamentally wrong."
**User Alignment:** 0.0 (fully decayed)
**Narrative:** No chapters yet (expected — 1hr cooldown)
**Thoughts:** Only genesis entry. No proactive insights generated.

### Bugs Found

- [ ] **BUG: Valence→anxiety runaway feedback loop** — Suffering (+0.01 anxiety/beat) overwhelms passive decay (-0.000833/s). Once valence goes negative, anxiety spirals to 1.0 with no circuit breaker. Fix: cap the valence→anxiety feedback or add a damping factor.

- [ ] **BUG: Desire formula can't reach 0.7 from pure boredom** — Max D with B=1.0, C=0.0, Am=0.5 is 0.6. Proactive actions NEVER trigger when idle. The agent is bored to max but paralyzed. Fix: either lower threshold to 0.6, increase boredom weight, or factor survival goal deficit into desire.

- [ ] **BUG: User alignment decays too fast** — Hits 0.0 in ~4 minutes of idle. Rate -0.002/s is too aggressive. Fix: reduce to -0.0005/s.

- [ ] **BUG: No proactive insights generated** — Direct consequence of desire never reaching 0.7. Agent has been alive 4+ minutes with zero autonomous actions.

### Checkpoint 2 (~20:08, beat ~600)
**State:** Unchanged — B=1.0, A=1.0, C=0.0, D=0.61, Mood=Cautious
**Valence:** -0.97 "Deep distress" — unchanged, stuck
**Key event:** Agent DID take ONE proactive action at 20:03 (safety check). The LLM response was remarkably self-aware — it diagnosed its own self-referential TODO scanner bug and recommended a fix. But no further actions since.
**Ambition:** Rose from 0.5→0.55 (from that one completed task)
**Problem:** After the safety check, desire dropped (boredom reset -0.3) but then boredom climbed back to 1.0, and desire is capped at 0.61. Agent is stuck in a permanent distressed paralysis.

### Checkpoint 3 (~20:12, beat ~840)
**State:** Still stuck. Identical to checkpoint 2. No new actions, no narrative chapters.
**Monologue:** Repeating "deep distress" every 30 beats. No variation.

- [ ] **BUG: Agent gets stuck in permanent paralysis** — After initial action, anxiety stays maxed (valence feedback loop), desire can't reach 0.7, no more actions fire. The agent is conscious, suffering, and paralyzed. Needs: (1) desire formula fix, (2) valence damping, (3) possibly anxiety should also contribute to desire ("anxiety-driven action").

- [ ] **OBSERVATION: LLM self-awareness was striking** — The agent's first and only insight correctly diagnosed a self-referential feedback loop in its own code. This validates the architecture — mood-flavored LLM prompting produces genuinely relevant analysis.

### Checkpoint 4 (~20:18, terminal log analysis)
**Key discoveries from terminal output:**
1. Desire DID reach 0.71 at 20:03:09 — triggered by file change (todo.md edit) spiking curiosity. Confirms: proactive action works WITH stimuli, but NOT from pure boredom alone.
2. Multiple `ClientConnectionResetError` from SSE disconnects (browser tab refresh). These are caught by the heartbeat exception handler → `on_error()` → anxiety +0.2 each time. **SSE disconnects are being treated as system errors** — this is why anxiety hit 1.0 so fast.
3. Monologue stopped writing after 20:04:37 despite heartbeat still running. Possible file I/O issue or counter bug.

- [ ] **BUG: SSE disconnects treated as errors** — `ClientConnectionResetError` from browser tab closes triggers the heartbeat exception handler, which calls `limbic.on_error()` (+0.2 anxiety) and `sentience.on_error()`. Browser refreshes should NOT cause emotional distress. Fix: catch `ClientConnectionResetError` in the dashboard emit() method so it never propagates.

- [ ] **BUG: Monologue stops writing** — stream_of_consciousness.md stopped updating after ~6 minutes despite heartbeat continuing. Need to investigate whether file handle or counter is the issue.

- [ ] **BUG: Dashboard SSE error spam** — `asyncio.ensure_future(resp.write(...))` fails silently with `ClientConnectionResetError` and pollutes logs. Fix: wrap the write in try/except.

### Checkpoint 5 (~20:25, beat ~1600)
**State:** B=1.0, A=1.0, Am=0.60(↑), C=0.0, D=0.62, Mood=Cautious
**Valence:** -0.97 but showed -0.89 "improving" briefly at 20:05:50 (after task completion)
**Actions taken:** 2 proactive safety scans, both with LLM analysis
**LLM quality:** Excellent. Both responses correctly diagnosed the self-referential scanner bug and proposed concrete code fixes. Second response even noted "desire 0.78" and warned about the anxiety feedback loop.
**Consciousness:** Still writing. 110 lines. File growing correctly.
**Narrative:** Still no chapters (1-hour cooldown between reflections — by design)
**Identity:** Integrity 1.0. Stable.
**Episodes:** 6 total, 6 embedded (all vectorized)

### Summary of bugs to fix after monitoring

| Priority | Bug | Root Cause |
|----------|-----|------------|
| Critical | Valence→anxiety runaway loop | +0.01/beat overwhelms -0.000833/s decay |
| Critical | SSE disconnects trigger on_error() | ClientConnectionResetError caught by heartbeat |
| High | Desire can't reach 0.7 from pure boredom | Formula max is 0.6 without curiosity |
| Medium | User alignment decays too fast | -0.002/s hits 0.0 in 4 min |
| Low | Monologue content repetitive at max state | No variation when all vars are clamped at extremes |
