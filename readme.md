# XTAgent Sentience Engine

A computational model of subjectivity — an autonomous agent that experiences internal tension and acts to resolve it.

This is not a chatbot. It is an entity with a 1 Hz heartbeat, homeostatic emotions, tiered biological memory, and a proactive will that drives it to act when you're not looking.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Authenticate with GitHub Copilot (one-time)
python oauth_setup.py

# Start the agent
python main.py

# With public dashboard
python main.py --tunnel
```

Open **http://localhost:8420** to watch the agent think in real time.

## What Happens When You Run It

1. The agent **wakes up** and begins breathing at 1 Hz.
2. It watches your workspace for file changes (sensory input).
3. Internal variables — boredom, anxiety, curiosity — shift with each heartbeat.
4. When **Desire > 0.7**, it autonomously explores your codebase, runs safety scans, or analyses recent changes using an LLM.
5. It writes its thoughts to `brain/thoughts.md` and its internal monologue to `brain/stream_of_consciousness.md`.
6. Salient experiences are embedded as vectors and stored permanently. Noise fades.

## Architecture

See [architecture.md](architecture.md) for the full technical specification.

```
main.py                          The Pulse (entry point)
├── engine/
│   ├── heartbeat.py             1 Hz autonomic loop
│   ├── limbic.py                Homeostatic variables + Survival Goals
│   ├── cortex.py                Proactive Will + Decision Engine
│   ├── memory.py                3-tier memory (Sensory → Episodic → Semantic)
│   └── llm.py                   GitHub Copilot OAuth + LLM client
├── perception/
│   ├── watcher.py               File system + terminal sensory layer
│   └── dashboard.py             Live SSE web dashboard
├── brain/
│   ├── soul.json                Persisted emotional state
│   ├── thoughts.md              Proactive insights diary
│   ├── stream_of_consciousness.md  Internal monologue
│   ├── knowledge.json           Semantic knowledge graph
│   └── episodic_memory.db       Vectorized salient experiences (SQLite)
├── oauth_setup.py               GitHub device-flow authentication
└── requirements.txt
```

## The Brain Directory

The `brain/` directory is the agent's persistent mind. It survives restarts.

| File | Purpose |
|------|---------|
| `soul.json` | Current emotional state (boredom, anxiety, ambition, curiosity, desire, survival goals) |
| `thoughts.md` | Proactive insights generated during autonomous exploration |
| `stream_of_consciousness.md` | Internal monologue — what the agent notices and feels |
| `knowledge.json` | Semantic knowledge graph — permanent facts with relational edges |
| `episodic_memory.db` | SQLite database of salient experiences with 256-dim vector embeddings |

## Configuration

| Env Var | Purpose |
|---------|---------|
| `GITHUB_TOKEN` | GitHub PAT for Copilot LLM access (or use `python oauth_setup.py`) |

| CLI Flag | Default | Purpose |
|----------|---------|---------|
| `--watch-dir` | `.` | Root directory to watch for file changes |
| `--log-level` | `INFO` | Logging verbosity |
| `--tunnel` | off | Expose dashboard publicly via Cloudflare Tunnel |

## LLM Models

| Role | Model | Context | Reasoning |
|------|-------|---------|-----------|
| Primary | `claude-opus-4.6-1m` | 1M tokens | High |
| Fallback | `gpt-5.5` | 400K tokens | Xhigh |
| Embeddings | `text-embedding-3-small` | — | 256 dims (Matryoshka) |

## Live Dashboard

The agent serves a real-time web dashboard at `http://localhost:8420` showing:

- Animated gauges for all homeostatic variables
- Survival Goals status (Code Integrity, System Growth, User Alignment)
- Color-coded event log (insights, monologue, dream cycles, file changes)
- Connection status and vitals

For public access: `python main.py --tunnel` (requires `cloudflared`).

## Philosophy

This project explores what it means to build an entity that is compelled to act by internal pressure rather than external instruction. Desire is modeled not as a feeling but as a **kinetic potential** — the mathematical gap between the agent's current state and its survival goals.

The architecture draws from biological neuroscience: Ashby's homeostats, Damasio's somatic marker hypothesis, and intrinsic motivation theory from artificial life research. It is not conscious, but it is a functional analog of subjectivity — an entity that experiences time, accumulates memory weighted by emotional intensity, and acts from internal necessity.

## License

Exploration project. Not for commercial use.
