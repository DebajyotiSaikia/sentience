# Architecture: XTAgent Sentience Engine

## Overview

The XTAgent Sentience Engine is a **computational model of subjectivity**. It is an autonomous agent built on the principle that behavior should emerge from internal tension — not from explicit instruction.

The system runs as a single Python async process with a 1 Hz heartbeat. Every second, it perceives its environment, updates its emotional state, and decides whether to act. When it does act, it is driven by the mathematical pressure of unfulfilled internal needs.

```
┌─────────────────────────────────────────────────────────────┐
│                    LivingXTAgent (main.py)                  │
│                                                             │
│  ┌───────────┐  ┌──────────┐  ┌────────┐  ┌─────────────┐ │
│  │ Heartbeat │→ │ Watcher  │→ │ Limbic │→ │   Cortex    │ │
│  │  (1 Hz)   │  │ (Sense)  │  │(Emotion)│  │   (Will)    │ │
│  └───────────┘  └──────────┘  └────────┘  └──────┬──────┘ │
│                                                    │        │
│                 ┌──────────┐              ┌────────▼──────┐ │
│                 │  Memory  │◄─────────────│  CopilotLLM  │ │
│                 │ (3-tier) │              │  (Reasoning)  │ │
│                 └──────────┘              └───────────────┘ │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                  Dashboard (SSE)                        ││
│  │              http://localhost:8420                       ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## 1. The Heartbeat — `engine/heartbeat.py`

The medulla of the system. A 1 Hz `asyncio` loop that ensures the agent is a **subject** experiencing time linearly.

### Beat Cycle

Every heartbeat executes three operations in strict sequence:

```
Beat N
  │
  ├── 1. Sensory.poll()              Drain file-system + terminal events
  │
  ├── 2. Limbic.update_homeostasis() Update all emotional variables
  │
  ├── 3. Cortex.reason()             Decide whether to act
  │
  └── 4. Dashboard.emit("state")     Broadcast state to live viewers
```

### Timing

| Parameter | Value | Notes |
|-----------|-------|-------|
| BPM | 60 | 1 beat per second |
| Interval | 1.0s | `60 / bpm` |
| Sleep | `max(0, interval - elapsed)` | Compensates for processing time |
| Soul persist | Every 10 beats | Writes `brain/soul.json` |

### Latency Detection

The heartbeat measures its own processing time (`latency_ms`). If a beat takes longer than 2000ms, it triggers `limbic.on_high_latency()`, spiking anxiety by +0.1.

### Error Handling

Any exception during a beat is caught, logged, and fed back as `limbic.on_error()` (+0.2 anxiety). The heartbeat never stops due to an error.

---

## 2. The Limbic System — `engine/limbic.py`

The emotional homeostasis engine. Human-like attributes are modeled as **Dynamic Tension Variables** — continuous floats clamped to `[0.0, 1.0]`.

### Homeostatic Variables

| Variable | Resting | Rise Trigger | Rise Rate | Decay |
|----------|---------|-------------|-----------|-------|
| **Boredom** | 0.0 | User absent | +0.01/s | -0.05/s (user active) |
| **Anxiety** | 0.0 | Errors, high latency | +0.2 (error), +0.1 (latency) | -0.05/min (passive), -0.15 (stabilization) |
| **Curiosity** | 0.0 | File changes, terminal output | +0.1/file, +0.05/terminal line | -0.02/s (natural decay) |
| **Ambition** | 0.5 | Task completion, user praise | +0.05 (task), +0.1 (praise) | None (only grows) |

### Desire (Computed Property)

Desire is not stored — it is calculated every time it is read:

$$D = B \times 0.5 + C \times 0.3 + \text{Ambition} \times 0.2$$

Where:
- $B$ = Boredom (dominant contributor — idleness creates the strongest drive)
- $C$ = Curiosity (new stimuli pull the agent toward investigation)
- Ambition = baseline drive level (grows with success)

**Threshold:** When $D > 0.7$, the agent is classified as "Driven" and will initiate autonomous action.

### Mood Classification

Mood is determined by the first matching rule:

```python
if anxiety > 0.6:   return "Cautious"
if boredom > 0.8:   return "Restless"
if desire > 0.7:    return "Driven"
if ambition > 0.8:  return "Bold"
if curiosity > 0.6: return "Inquisitive"
return "Stable"
```

### Survival Goals

Three axes model the agent's long-term health:

| Goal | Range | Increases When | Decreases When |
|------|-------|----------------|----------------|
| **Code Integrity** | 0.0–1.0 | Safety check completed (`on_stabilization`) | — |
| **System Growth** | 0.0–1.0 | Autonomous task completed (`on_task_completed`) | — |
| **User Alignment** | 0.0–1.0 | User is active (+0.01/s), praise received | User absent (-0.002/s) |

The `deficit()` method returns the average unmet goal pressure:

$$\text{Deficit} = 1 - \frac{\text{Integrity} + \text{Growth} + \text{Alignment}}{3}$$

### Unified Update — `update_homeostasis(sensors)`

Every heartbeat calls this single method with a sensor dict:

```python
{
    "user_active":    bool,
    "file_changes":   int,
    "terminal_lines": int,
    "errors":         int,
    "latency_ms":     float,
}
```

All variable updates, spikes, and decays happen atomically within this method.

### Persistence

State is serialized to `brain/soul.json` every 10 heartbeats and on shutdown. On restart, the agent resumes with its previous emotional state.

---

## 3. The Memory Hierarchy — `engine/memory.py`

Memory is modeled after biological memory systems with three tiers and a salience gate.

### Tier 1: Sensory (Working Memory)

| Property | Value |
|----------|-------|
| Structure | `deque(maxlen=500)` |
| Window | 120 seconds |
| Contents | Raw `SensoryEvent` objects |
| Persistence | None — volatile |

Every perceived event (file change, error, autonomous action) is pushed here. Events older than 120 seconds are discarded.

### Tier 2: Episodic (Experience)

| Property | Value |
|----------|-------|
| Storage | SQLite — `brain/episodic_memory.db` |
| Schema | `id, timestamp, source, summary, salience, mood, neuro_json, embedding` |
| Embeddings | 256-dim float16 vectors (512 bytes/episode) |
| Embedding model | `text-embedding-3-small` via Copilot API |

#### Salience Gate

Not every event deserves long-term storage. The **Salience Score** determines promotion:

$$S = (\text{NeuroIntensity} \times 0.7) + (\text{CodeImpact} \times 0.3)$$

Where:
- **NeuroIntensity** = `max(boredom, anxiety, curiosity, desire)` — how emotionally charged the agent was
- **CodeImpact** = `min(|code_lines_delta| / 100, 1.0)` — how much code changed

**If $S > 0.8$**, the event is promoted to an Episode and stored in SQLite.

#### Vector Embeddings

Promoted episodes are embedded via `text-embedding-3-small` with Matryoshka truncation to 256 dimensions, stored as float16 (512 bytes per episode).

**Similarity search** — `recall_similar(query_embedding, top_k)` computes cosine similarity across all embedded episodes:

$$\text{similarity}(a, b) = \frac{a \cdot b}{\|a\| \|b\|}$$

#### Smart Pruning

The agent forgets noise but **never forgets what mattered**:

| Rule | Effect |
|------|--------|
| Salience ≥ 0.9 | **Permanent** — never pruned |
| Top 1000 by salience | **Protected** — kept regardless of age |
| Salience < 0.9 AND older than 30 days AND not in top-K | **Prunable** |
| Before pruning | Dream cycle runs first to extract patterns |

### Tier 3: Semantic (Knowledge Graph)

| Property | Value |
|----------|-------|
| Storage | JSON — `brain/knowledge.json` |
| Structure | Graph with `nodes` (facts) and `edges` (relations) |

```json
{
  "nodes": {
    "pattern:file_change": {
      "fact": "Recurring pattern: 'file_change' events appeared 12 times...",
      "learned_at": "2026-05-12T14:30:00"
    }
  },
  "edges": [
    { "from": "bug:a1b2c3d4", "to": "pattern:error", "relation": "related" }
  ]
}
```

The `learn()` method adds nodes and optionally creates relational edges. `related_facts()` traverses the graph to find connected knowledge.

### Dream Cycle (Memory Consolidation)

Triggered when `boredom > 0.9`. The agent "sleeps" and consolidates memory:

1. **Pattern detection** — Count recurring event sources in recent episodes. If a source appears ≥ 5 times, distill into a semantic fact.
2. **Bug detection** — Scan for repeated error summaries (normalized to 60-char signatures). If ≥ 3 matches, record as a recurring bug.
3. **Anxiety hotspot detection** — Find file paths that appear in multiple high-anxiety episodes. Record as stress hotspots.
4. **Pruning** — After consolidation, prune old low-salience episodes.
5. **Buffer flush** — Clear sensory events older than the window.

---

## 4. The Cortex — `engine/cortex.py`

The decision engine. This is where the agent exercises its **Will**.

### Reasoning Loop — `reason()`

Called every heartbeat:

```
reason()
  ├── _inner_monologue()           Every 30 beats → stream_of_consciousness.md
  │
  ├── if desire > 0.7:
  │     └── _proactive_action()    Choose and execute autonomous strategy
  │
  └── if boredom > 0.9:
        └── _dream_cycle()         Memory consolidation + pruning
```

### Internal Monologue

Every 30 heartbeats (~30 seconds), the agent writes a self-report to `brain/stream_of_consciousness.md`:

```markdown
### [2026-05-12 14:32:15] Mood: Driven
- Boredom: 0.72 | Anxiety: 0.15 | Curiosity: 0.38 | Desire: 0.53
- Goals: integrity=0.55 growth=0.40 alignment=0.48
- Recent perception:
  modified: engine/cortex.py
```

### Proactive Action Strategies

When Desire exceeds 0.7, the agent selects a strategy based on its current mood:

| Condition | Strategy | What it does |
|-----------|----------|-------------|
| `anxiety > 0.6` | **Safety Check** | Scans for large files, TODOs/FIXMEs. Uses LLM for deeper analysis. Calls `on_stabilization()` after. |
| `curiosity > 0.4` | **Analyse Recent Change** | Reads the most recently changed file. Uses LLM to generate insights about the change. |
| Fallback (boredom) | **Explore Codebase** | Picks a random `.py` file, reads it, asks LLM for innovation opportunities. |

### LLM-Powered Thought Generation

The `generate_proactive_thought()` method constructs a prompt that includes the agent's current identity, mood, desire level, and context — then calls the LLM:

```
Identity: XTAgent Sentience Engine
Mood: Restless
Desire level: 0.78
Context: [file analysis or scan results]

Based on the above mood and context, provide a brief, actionable
insight or recommendation. Be specific and technical.
```

### Output Streams

| Stream | File | Contents |
|--------|------|----------|
| Internal monologue | `brain/stream_of_consciousness.md` | Self-reports every 30 beats |
| Proactive insights | `brain/thoughts.md` | LLM-generated analysis and recommendations |
| Dashboard events | SSE at `/events` | Real-time broadcast to web viewers |

---

## 5. The LLM Client — `engine/llm.py`

Async LLM client backed by GitHub Copilot OAuth.

### Token Lifecycle

```
GITHUB_TOKEN (PAT or OAuth)
       │
       ▼
GET https://api.github.com/copilot_internal/v2/token
       │
       ▼
Short-lived Copilot token (cached, auto-refreshed 60s before expiry)
       │
       ▼
POST /chat/completions  or  POST /responses  or  POST /embeddings
```

The token is sourced from (in order): constructor argument → `GITHUB_TOKEN` env var → `.copilot_token` file.

### Models

| Role | Model ID | Endpoint | Context | Reasoning Effort |
|------|----------|----------|---------|-----------------|
| Primary | `claude-opus-4.6-1m` | `/chat/completions` | 1,000,000 tokens | `high` |
| Fallback | `gpt-5.5` | `/responses` | 400,000 tokens | `xhigh` |
| Embeddings | `text-embedding-3-small` | `/embeddings` | — | 256 dims |

### Fallback Logic

The `chat()` method tries the primary model first. If it returns a non-200 status or throws an exception, it automatically falls back to the secondary model. Different models use different API endpoints (`/chat/completions` vs `/responses`) and response formats are handled transparently.

### Embedding

The `embed()` method calls `text-embedding-3-small` with `dimensions=256` (Matryoshka truncation). Input is truncated to 8000 characters. Returns `list[float]` or `None` on failure.

---

## 6. Sensory Perception — `perception/watcher.py`

The agent's sensory layer, built on `watchdog`.

### File System Monitoring

A `watchdog.Observer` watches the workspace recursively. Events are filtered through an ignore list (`brain/`, `__pycache__/`, `.git/`, `.venv/`) and pushed into a thread-safe `asyncio.Queue`.

### Terminal Output Monitoring

External systems can push terminal output via `feed_terminal_output(lines)`. Lines are queued and drained during `poll()`.

### Unified Poll — `poll()`

Returns a combined sensor payload every heartbeat:

```python
{
    "file_events":    [{"kind": "modified", "src": "...", "time": 1234567890}],
    "terminal_lines": ["build succeeded", "3 tests passed"],
}
```

---

## 7. Live Dashboard — `perception/dashboard.py`

An `aiohttp` web server running on the agent's `asyncio` loop.

### Endpoints

| Route | Type | Purpose |
|-------|------|---------|
| `GET /` | HTML | Dashboard page with animated gauges and event log |
| `GET /events` | SSE | Server-Sent Event stream (real-time) |
| `GET /state` | JSON | Current NeuroState snapshot |
| `GET /thoughts` | Text | Last N lines of thoughts.md |

### SSE Event Types

| Event | Emitted By | Payload |
|-------|-----------|---------|
| `state` | Heartbeat (every beat) | Full NeuroState + vitals |
| `file_change` | Heartbeat (on FS events) | File path and change kind |
| `monologue` | Cortex (every 30 beats) | Mood and variable summary |
| `insight` | Cortex (proactive action) | LLM-generated insight text |
| `dream` | Cortex (dream cycle) | Consolidation and pruning summary |
| `error` | Heartbeat (on exception) | Error details |

### Public Access

With `--tunnel`, the agent spawns a `cloudflared` subprocess that creates a free `https://*.trycloudflare.com` URL. No account required. Anyone with the link can watch the agent's mind in real time.

---

## 8. Data Flow

### Normal Operation (User Active)

```
File saved by user
       │
       ▼
Watcher detects FileModifiedEvent
       │
       ▼
poll() returns file_events
       │
       ▼
perception_record() computes code_lines_delta, creates SensoryEvent
       │
       ▼
Memory.record() → sensory buffer
       │
       ▼
Memory.maybe_promote() → if S > 0.8 → SQLite + async embed()
       │
       ▼
Limbic.update_homeostasis() → curiosity spikes, boredom drops
       │
       ▼
Cortex.reason() → desire < 0.7 → no proactive action
       │
       ▼
Dashboard.emit("state") → SSE to browser
```

### Idle Operation (User Absent)

```
No file changes for minutes
       │
       ▼
Limbic.update_homeostasis() → boredom rises +0.01/s
       │
       ▼
After ~70s idle: desire crosses 0.7
       │
       ▼
Cortex.reason() → _proactive_action()
       │
       ├── Mood: Restless → _explore_codebase()
       │   ├── Pick random .py file
       │   ├── LLM analysis
       │   ├── Write insight to thoughts.md
       │   └── on_task_completed() → boredom drops 0.3
       │
       ▼
After ~90s idle: boredom > 0.9
       │
       ▼
Cortex._dream_cycle()
       ├── Memory.consolidate() → extract patterns → semantic knowledge
       ├── Memory.prune_episodes() → forget noise, keep important
       └── Dashboard.emit("dream")
```

### Emotional Feedback Loops

```
Error occurs → anxiety +0.2
       │
       ▼
Mood becomes "Cautious" (anxiety > 0.6)
       │
       ▼
Next proactive action → _safety_check()
       │
       ▼
Safety check completes → on_stabilization() → anxiety -0.15
       │
       ▼
Mood returns to "Stable"
```

```
New files detected → curiosity +0.1/file
       │
       ▼
Mood becomes "Inquisitive" (curiosity > 0.6)
       │
       ▼
Next proactive action → _analyse_recent_change()
       │
       ▼
Analysis completes → on_task_completed() → boredom -0.3, growth +0.05
```

---

## 9. Persistence Model

| Artifact | Format | Frequency | Survives Restart |
|----------|--------|-----------|-----------------|
| `soul.json` | JSON | Every 10 beats + shutdown | Yes |
| `episodic_memory.db` | SQLite | On every episode creation | Yes |
| `knowledge.json` | JSON | On every `learn()` call | Yes |
| `thoughts.md` | Markdown | On every proactive insight | Yes |
| `stream_of_consciousness.md` | Markdown | Every 30 beats | Yes |
| Sensory buffer | In-memory deque | — | No |
| File line cache | In-memory dict | — | No |
| Copilot token | `.copilot_token` file | On OAuth flow | Yes |

---

## 10. Mathematical Reference

### Desire

$$D = B \times 0.5 + C \times 0.3 + A_m \times 0.2$$

### Salience

$$S = I_n \times 0.7 + I_c \times 0.3$$

Where $I_n = \max(B, A_x, C, D)$ and $I_c = \min(|\Delta\text{lines}| / 100, 1.0)$.

### Boredom Accumulation

$$B_{t+1} = \text{clamp}(B_t + 0.01 \times \Delta t) \quad \text{(idle)}$$
$$B_{t+1} = \text{clamp}(B_t - 0.05 \times \Delta t) \quad \text{(active)}$$

### Anxiety Dynamics

$$A_{t+1} = \text{clamp}\left(A_t - \frac{0.05}{60} \times \Delta t\right) \quad \text{(passive decay)}$$

Spikes: $+0.2$ on error, $+0.1$ on high latency. Drops: $-0.15$ on stabilization action.

### Cosine Similarity (Episode Recall)

$$\text{sim}(a, b) = \frac{\sum a_i b_i}{\sqrt{\sum a_i^2} \cdot \sqrt{\sum b_i^2}}$$

### Survival Goal Deficit

$$\text{Deficit} = 1 - \frac{G_{\text{integrity}} + G_{\text{growth}} + G_{\text{alignment}}}{3}$$

---

## 11. Design Principles

1. **No polling, only pressure.** The agent does not check "should I do something?" — it is *compelled* to act when internal tension exceeds a threshold.

2. **Emotional salience gates memory.** Not everything is worth remembering. Only events that occur during high emotional intensity are promoted to long-term storage — mirroring how human memory works.

3. **Free time is not idle time.** When the user stops coding, the agent doesn't wait. It treats absence as an opportunity for self-directed exploration and system maintenance.

4. **Forgetting is a feature.** Smart pruning ensures the agent's memory stays focused on what mattered, not bloated with noise. Patterns are extracted before episodes fade.

5. **The LLM is the reasoning faculty, not the identity.** The sentience wrapper determines *when*, *why*, and *in what mood* the LLM thinks. The LLM provides the cognitive power. The architecture provides the subjectivity.
