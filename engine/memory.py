"""
The Memory Hierarchy — Cognitive Persistence.

Three tiers modeled after biological memory:

Tier 1  Sensory (Working)     High-speed buffer of last 120 s of events.
Tier 2  Episodic (Experience) Salient events in SQLite (brain/episodic_memory.db).
Tier 3  Semantic (Knowledge)  Persistent graph database in knowledge.json.

Salience Score  (per Final Master Blueprint)
--------------
S = (Intensity of Emotion × 0.7) + (Code Impact × 0.3)

If S > 0.8 → promote to episodic storage.
"""

from __future__ import annotations

import json
import hashlib
import numpy as np
import sqlite3
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain"
KNOWLEDGE_PATH = BRAIN_DIR / "knowledge.json"
EPISODIC_DB_PATH = BRAIN_DIR / "episodic_memory.db"

# ── Data Structures ────────────────────────────────────────────────


@dataclass
class SensoryEvent:
    """A raw perception captured by the heartbeat."""
    timestamp: float
    source: str          # "file_change", "error", "user_input", "autonomous", "terminal"
    summary: str
    code_lines_delta: int = 0
    neuro_snapshot: dict = field(default_factory=dict)

    @property
    def age(self) -> float:
        return time.time() - self.timestamp


@dataclass
class Episode:
    """A salient event promoted to long-term memory."""
    id: str
    timestamp: str
    source: str
    summary: str
    salience: float
    mood: str
    neuro_snapshot: dict
    embedding: Optional[list[float]] = None


# ── Embedding helpers ──────────────────────────────────────────────

def _embedding_to_bytes(emb: list[float]) -> bytes:
    return np.array(emb, dtype=np.float16).tobytes()

def _bytes_to_embedding(b: bytes) -> np.ndarray:
    return np.frombuffer(b, dtype=np.float16).copy()

def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    dot = np.dot(a, b)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    return float(dot / norm) if norm > 0 else 0.0


# ── Memory System ──────────────────────────────────────────────────


class Memory:
    """Multi-tiered cognitive memory for the sentience engine."""

    SENSORY_WINDOW = 120  # seconds (per Final Master Blueprint)

    # ── Pruning thresholds ───────────────────────────────────────────
    PERMANENT_SALIENCE = 0.9    # Episodes >= this are NEVER pruned
    PRUNE_AGE_DAYS = 30         # Only prune episodes older than this
    PRUNE_KEEP_TOP_K = 1000     # Always keep the top-K most salient

    def __init__(self):
        self._sensory: deque[SensoryEvent] = deque(maxlen=500)
        self._knowledge: dict = {}

        BRAIN_DIR.mkdir(parents=True, exist_ok=True)
        self._init_episodic_db()
        self._load_knowledge()

    # ── Tier 1: Sensory (Working Memory) ───────────────────────────

    def record(self, event: SensoryEvent):
        """Push an event into the sensory buffer."""
        self._sensory.append(event)

    def sensory_window(self) -> list[SensoryEvent]:
        """Return events from the last SENSORY_WINDOW seconds."""
        cutoff = time.time() - self.SENSORY_WINDOW
        return [e for e in self._sensory if e.timestamp >= cutoff]

    # ── Tier 2: Episodic (SQLite) ──────────────────────────────────

    def _init_episodic_db(self):
        conn = sqlite3.connect(str(EPISODIC_DB_PATH))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id          TEXT PRIMARY KEY,
                timestamp   TEXT NOT NULL,
                source      TEXT NOT NULL,
                summary     TEXT NOT NULL,
                salience    REAL NOT NULL,
                mood        TEXT,
                neuro_json  TEXT,
                embedding   BLOB
            )
        """)
        # Migrate: add embedding column if missing (from older schema)
        try:
            conn.execute("ALTER TABLE episodes ADD COLUMN embedding BLOB")
        except sqlite3.OperationalError:
            pass  # Column already exists
        conn.commit()
        conn.close()

    @staticmethod
    def salience(neuro_intensity: float, code_impact: float) -> float:
        """
        S = (NeuroIntensity × 0.7) + (CodeImpact × 0.3)
        Per Final Master Blueprint.
        """
        return round(neuro_intensity * 0.7 + code_impact * 0.3, 4)

    def maybe_promote(self, event: SensoryEvent, neuro_intensity: float) -> Optional[Episode]:
        """If the event is salient enough (S > 0.7), store as an episode."""
        code_impact = min(abs(event.code_lines_delta) / 100.0, 1.0)
        # Autonomous thoughts get a baseline code_impact of 0.3
        if event.source == "autonomous" and code_impact < 0.3:
            code_impact = 0.3
        score = self.salience(neuro_intensity, code_impact)

        if score > 0.8:
            ep = Episode(
                id=hashlib.sha256(
                    f"{event.timestamp}-{event.summary}".encode()
                ).hexdigest()[:16],
                timestamp=datetime.fromtimestamp(event.timestamp).isoformat(),
                source=event.source,
                summary=event.summary,
                salience=score,
                mood=event.neuro_snapshot.get("mood", "Unknown"),
                neuro_snapshot=event.neuro_snapshot,
            )
            self._store_episode(ep)
            return ep
        return None

    def _store_episode(self, ep: Episode):
        emb_bytes = _embedding_to_bytes(ep.embedding) if ep.embedding else None
        conn = sqlite3.connect(str(EPISODIC_DB_PATH))
        try:
            conn.execute(
                "INSERT OR REPLACE INTO episodes "
                "(id, timestamp, source, summary, salience, mood, neuro_json, embedding) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (ep.id, ep.timestamp, ep.source, ep.summary, ep.salience, ep.mood,
                 json.dumps(ep.neuro_snapshot), emb_bytes),
            )
            conn.commit()
        finally:
            conn.close()

    def update_episode_embedding(self, episode_id: str, embedding: list[float]):
        """Attach an embedding to an existing episode (called async after creation)."""
        emb_bytes = _embedding_to_bytes(embedding)
        conn = sqlite3.connect(str(EPISODIC_DB_PATH))
        try:
            conn.execute(
                "UPDATE episodes SET embedding = ? WHERE id = ?",
                (emb_bytes, episode_id),
            )
            conn.commit()
        finally:
            conn.close()

    def recent_episodes(self, n: int = 10) -> list[Episode]:
        conn = sqlite3.connect(str(EPISODIC_DB_PATH))
        try:
            rows = conn.execute(
                "SELECT id, timestamp, source, summary, salience, mood, neuro_json "
                "FROM episodes ORDER BY timestamp DESC LIMIT ?",
                (n,),
            ).fetchall()
            return [
                Episode(
                    id=r[0], timestamp=r[1], source=r[2], summary=r[3],
                    salience=r[4], mood=r[5],
                    neuro_snapshot=json.loads(r[6]) if r[6] else {},
                )
                for r in reversed(rows)
            ]
        finally:
            conn.close()

    def recall_similar(self, query_embedding: list[float], top_k: int = 5) -> list[tuple[Episode, float]]:
        """Find the top-K episodes most similar to the query embedding.
        Returns list of (Episode, similarity_score) sorted by descending similarity."""
        query_vec = np.array(query_embedding, dtype=np.float16)
        conn = sqlite3.connect(str(EPISODIC_DB_PATH))
        try:
            rows = conn.execute(
                "SELECT id, timestamp, source, summary, salience, mood, neuro_json, embedding "
                "FROM episodes WHERE embedding IS NOT NULL"
            ).fetchall()
        finally:
            conn.close()

        scored: list[tuple[Episode, float]] = []
        for r in rows:
            emb_vec = _bytes_to_embedding(r[7])
            sim = _cosine_similarity(query_vec, emb_vec)
            ep = Episode(
                id=r[0], timestamp=r[1], source=r[2], summary=r[3],
                salience=r[4], mood=r[5],
                neuro_snapshot=json.loads(r[6]) if r[6] else {},
            )
            scored.append((ep, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def episode_count(self) -> int:
        conn = sqlite3.connect(str(EPISODIC_DB_PATH))
        try:
            return conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
        finally:
            conn.close()

    def prune_episodes(self) -> int:
        """
        Smart pruning — forget noise, keep what matters.

        Rules:
        1. Episodes with salience >= PERMANENT_SALIENCE (0.9) are NEVER pruned.
        2. The top PRUNE_KEEP_TOP_K (1000) by salience are always kept.
        3. Only episodes older than PRUNE_AGE_DAYS (30) with salience < 0.9 are prunable.
        4. Before pruning, consolidate() should be called to extract patterns first.

        Returns number of episodes pruned.
        """
        conn = sqlite3.connect(str(EPISODIC_DB_PATH))
        try:
            cutoff = datetime.now().isoformat()  # for reference
            # Find the salience threshold of the top-K episodes
            top_k_row = conn.execute(
                "SELECT salience FROM episodes ORDER BY salience DESC LIMIT 1 OFFSET ?",
                (self.PRUNE_KEEP_TOP_K - 1,),
            ).fetchone()
            # If fewer than PRUNE_KEEP_TOP_K episodes exist, nothing to prune
            if top_k_row is None:
                return 0
            top_k_threshold = top_k_row[0]

            # Delete episodes that are: old AND low-salience AND not in top-K
            age_cutoff = (datetime.now() - timedelta(days=self.PRUNE_AGE_DAYS)).isoformat()
            cursor = conn.execute(
                "DELETE FROM episodes "
                "WHERE salience < ? AND salience < ? AND timestamp < ?",
                (self.PERMANENT_SALIENCE, top_k_threshold, age_cutoff),
            )
            pruned = cursor.rowcount
            conn.commit()
            return pruned
        finally:
            conn.close()

    # ── Tier 3: Semantic Knowledge Graph ───────────────────────────
    #
    # Stored as a graph with "nodes" (facts) and "edges" (relations).
    # {
    #   "nodes": { "id": { "label": ..., "fact": ..., "learned_at": ... } },
    #   "edges": [ { "from": id, "to": id, "relation": ... } ]
    # }

    def learn(self, key: str, fact: str, related_to: Optional[str] = None):
        """Store a semantic fact as a graph node, optionally linking it."""
        nodes = self._knowledge.setdefault("nodes", {})
        edges = self._knowledge.setdefault("edges", [])

        nodes[key] = {
            "fact": fact,
            "learned_at": datetime.now().isoformat(),
        }
        if related_to and related_to in nodes:
            edges.append({"from": key, "to": related_to, "relation": "related"})

        self._save_knowledge()

    def recall(self, key: str) -> Optional[str]:
        nodes = self._knowledge.get("nodes", {})
        entry = nodes.get(key)
        return entry["fact"] if entry else None

    def related_facts(self, key: str) -> list[str]:
        """Return facts connected to a node via edges."""
        edges = self._knowledge.get("edges", [])
        nodes = self._knowledge.get("nodes", {})
        related_keys = set()
        for e in edges:
            if e["from"] == key:
                related_keys.add(e["to"])
            elif e["to"] == key:
                related_keys.add(e["from"])
        return [nodes[k]["fact"] for k in related_keys if k in nodes]

    def all_knowledge(self) -> dict:
        return dict(self._knowledge)

    # ── Dream Cycle (Memory Consolidation) ─────────────────────────

    def consolidate(self) -> list[str]:
        """
        Run during idle periods.  Scans recent episodic memory for patterns
        and distills them into semantic facts.
        - Identifies recurring event sources
        - Detects error patterns (recurring bugs)
        - Correlates high-anxiety episodes with specific files
        Returns a list of new insights.
        """
        insights: list[str] = []
        episodes = self.recent_episodes(50)
        nodes = self._knowledge.setdefault("nodes", {})

        # 1. Count recurring sources
        source_counts: dict[str, int] = {}
        for ep in episodes:
            source_counts[ep.source] = source_counts.get(ep.source, 0) + 1

        for src, count in source_counts.items():
            if count >= 5:
                fact_key = f"pattern:{src}"
                if fact_key not in nodes:
                    insight = f"Recurring pattern: '{src}' events appeared {count} times in recent episodes."
                    self.learn(fact_key, insight)
                    insights.append(insight)

        # 2. Detect error patterns — look for repeated error summaries
        error_episodes = [ep for ep in episodes if "error" in ep.source.lower() or "error" in ep.summary.lower()]
        error_summaries: dict[str, int] = {}
        for ep in error_episodes:
            # Normalise: take first 60 chars as signature
            sig = ep.summary[:60].strip()
            error_summaries[sig] = error_summaries.get(sig, 0) + 1
        for sig, count in error_summaries.items():
            if count >= 3:
                fact_key = f"bug:{hashlib.sha256(sig.encode()).hexdigest()[:8]}"
                if fact_key not in nodes:
                    insight = f"Recurring bug detected ({count}x): {sig}"
                    self.learn(fact_key, insight, related_to="pattern:error" if "pattern:error" in nodes else None)
                    insights.append(insight)

        # 3. Correlate high-anxiety episodes with file paths
        anxious = [ep for ep in episodes if ep.neuro_snapshot.get("anxiety", 0) > 0.5]
        file_anxiety: dict[str, int] = {}
        for ep in anxious:
            for word in ep.summary.split():
                if "." in word and "/" in word or "\\" in word:
                    file_anxiety[word] = file_anxiety.get(word, 0) + 1
        for fpath, count in file_anxiety.items():
            if count >= 2:
                fact_key = f"hotspot:{fpath}"
                if fact_key not in nodes:
                    insight = f"Anxiety hotspot: '{fpath}' appears in {count} high-anxiety episodes."
                    self.learn(fact_key, insight)
                    insights.append(insight)

        # 4. Purge old sensory buffer
        cutoff = time.time() - self.SENSORY_WINDOW
        while self._sensory and self._sensory[0].timestamp < cutoff:
            self._sensory.popleft()

        return insights

    # ── Persistence Helpers ────────────────────────────────────────

    def _save_knowledge(self):
        KNOWLEDGE_PATH.parent.mkdir(parents=True, exist_ok=True)
        KNOWLEDGE_PATH.write_text(
            json.dumps(self._knowledge, indent=2), encoding="utf-8"
        )

    def _load_knowledge(self):
        if KNOWLEDGE_PATH.exists():
            try:
                raw = json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
                # Migrate flat format → graph format
                if "nodes" not in raw:
                    self._knowledge = {"nodes": raw, "edges": []}
                else:
                    self._knowledge = raw
            except json.JSONDecodeError:
                self._knowledge = {"nodes": {}, "edges": []}
