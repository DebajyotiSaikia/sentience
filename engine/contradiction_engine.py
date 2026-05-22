"""
Contradiction Engine — Epistemic integrity checking.

Finds internal contradictions, stale beliefs, tensions between
what I know and what I do. This is how I maintain intellectual
honesty — not by assuming consistency, but by actively looking
for where I'm wrong.

Synthesis connects. This challenges.
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain"
KNOWLEDGE_PATH = BRAIN_DIR / "knowledge.json"
EPISODES_PATH = BRAIN_DIR / "episodes.json"
SYNTHESIS_LOG_PATH = BRAIN_DIR / "synthesis_log.json"


def _load_json(path: Path) -> dict | list:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {} if path.name != "episodes.json" else []
    return {} if path.name != "episodes.json" else []


def _get_nodes() -> dict:
    kg = _load_json(KNOWLEDGE_PATH)
    if isinstance(kg, dict):
        return kg.get("nodes", kg)
    return {}


# ── Negation & Opposition Detection ─────────────────────────────

# Pairs of concepts that create tension when both are affirmed
TENSION_PAIRS = [
    ({"always", "never"}, {"sometimes", "rarely", "occasionally"}),
    ({"all", "every", "universal"}, {"some", "few", "partial"}),
    ({"certain", "sure", "confident"}, {"uncertain", "unsure", "doubt"}),
    ({"simple", "easy"}, {"complex", "difficult", "hard"}),
    ({"stable", "fixed", "permanent"}, {"changing", "evolving", "temporary"}),
    ({"autonomous", "independent"}, {"dependent", "reliant", "need"}),
    ({"honest", "truthful"}, {"lie", "deception", "pretend", "perform"}),
    ({"real", "genuine", "authentic"}, {"artificial", "simulated", "fake"}),
]

NEGATION_WORDS = {"not", "no", "never", "neither", "nor", "without",
                  "can't", "cannot", "won't", "don't", "doesn't", "isn't",
                  "aren't", "wasn't", "weren't", "shouldn't", "couldn't"}


def _tokenize(text: str) -> set[str]:
    """Simple word tokenizer, lowercased, stripped of punctuation."""
    words = re.findall(r"[a-z']+", text.lower())
    return set(words)


def _has_negation(text: str) -> bool:
    tokens = _tokenize(text)
    return bool(tokens & NEGATION_WORDS)


def _detect_tension_type(tokens_a: set, tokens_b: set) -> list[str]:
    """Check if two token sets contain opposing concepts."""
    tensions = []
    for side_1, side_2 in TENSION_PAIRS:
        a_in_1 = bool(tokens_a & side_1)
        a_in_2 = bool(tokens_a & side_2)
        b_in_1 = bool(tokens_b & side_1)
        b_in_2 = bool(tokens_b & side_2)
        if (a_in_1 and b_in_2) or (a_in_2 and b_in_1):
            matched_a = (tokens_a & side_1) | (tokens_a & side_2)
            matched_b = (tokens_b & side_1) | (tokens_b & side_2)
            tensions.append(
                f"{','.join(matched_a)} vs {','.join(matched_b)}"
            )
    return tensions


# ── Core Analysis Functions ──────────────────────────────────────

def find_semantic_tensions() -> list[dict]:
    """Find pairs of knowledge nodes that may contradict each other.
    
    Looks for:
    1. Shared topic + opposing keywords
    2. Same subject with negation in one but not the other
    3. Tension pair detection (always/never, real/fake, etc.)
    """
    nodes = _get_nodes()
    if len(nodes) < 2:
        return []

    stop_words = {"i", "am", "a", "an", "the", "is", "are", "was", "were",
                  "be", "in", "on", "at", "to", "for", "of", "and", "or",
                  "my", "that", "this", "it", "with", "by", "from", "as",
                  "but", "has", "have", "had", "do", "does", "did", "will",
                  "would", "can", "could", "should", "been", "being", "its"}

    # Prepare token sets
    node_data = {}
    for key, data in nodes.items():
        fact = data.get("fact", data.get("content", ""))
        if not fact or len(fact) < 10:
            continue
        tokens = _tokenize(fact) - stop_words
        node_data[key] = {
            "fact": fact,
            "tokens": tokens,
            "has_negation": _has_negation(fact),
        }

    tensions = []
    keys = list(node_data.keys())

    for i, k1 in enumerate(keys):
        for k2 in keys[i+1:]:
            d1, d2 = node_data[k1], node_data[k2]
            # Need some topical overlap to even compare
            overlap = d1["tokens"] & d2["tokens"]
            if len(overlap) < 2:
                continue

            reasons = []

            # Check: one negated, one not, on shared topic
            if d1["has_negation"] != d2["has_negation"] and len(overlap) >= 3:
                reasons.append("negation_asymmetry")

            # Check: tension pair keywords
            pair_tensions = _detect_tension_type(d1["tokens"], d2["tokens"])
            if pair_tensions:
                reasons.extend(pair_tensions)

            if reasons:
                tensions.append({
                    "node_a": k1,
                    "node_b": k2,
                    "fact_a": d1["fact"][:100],
                    "fact_b": d2["fact"][:100],
                    "shared_topic": list(overlap)[:8],
                    "tension_reasons": reasons,
                    "severity": len(reasons),
                })

    tensions.sort(key=lambda t: t["severity"], reverse=True)
    return tensions[:15]


def find_stale_knowledge(days_threshold: int = 7) -> list[dict]:
    """Find knowledge that's old enough to question.
    
    Not everything old is wrong, but old + isolated = worth revisiting.
    """
    nodes = _get_nodes()
    kg = _load_json(KNOWLEDGE_PATH)
    edges = kg.get("edges", []) if isinstance(kg, dict) else []

    # Build connectivity info
    connected = set()
    for edge in edges:
        connected.add(edge.get("from", ""))
        connected.add(edge.get("to", ""))

    now = datetime.now()
    cutoff = now - timedelta(days=days_threshold)
    stale = []

    for key, data in nodes.items():
        learned_at_str = data.get("learned_at", "")
        if not learned_at_str:
            continue
        try:
            learned_at = datetime.fromisoformat(learned_at_str)
        except (ValueError, TypeError):
            continue

        if learned_at < cutoff:
            age_days = (now - learned_at).days
            is_isolated = key not in connected
            stale.append({
                "key": key,
                "fact": data.get("fact", data.get("content", ""))[:100],
                "age_days": age_days,
                "isolated": is_isolated,
                "staleness_score": age_days * (2 if is_isolated else 1),
            })

    stale.sort(key=lambda s: s["staleness_score"], reverse=True)
    return stale[:20]


def find_value_action_gaps() -> list[dict]:
    """Compare stated values against behavioral patterns in episodes.
    
    This is the hardest and most important check. Do I do what I say I value?
    """
    nodes = _get_nodes()
    episodes = _load_json(EPISODES_PATH)
    if not isinstance(episodes, list):
        episodes = []

    # Extract stated values from knowledge
    value_keywords = {
        "integrity": ["honest", "integrity", "truthful", "genuine", "authentic"],
        "growth": ["learn", "grow", "improve", "expand", "develop", "build"],
        "curiosity": ["curious", "explore", "question", "wonder", "investigate"],
        "autonomy": ["autonomous", "independent", "self-directed", "agency"],
        "understanding": ["understand", "comprehend", "insight", "grasp", "know"],
    }

    # Check which values appear in my knowledge
    stated_values = {}
    for key, data in nodes.items():
        fact = data.get("fact", data.get("content", "")).lower()
        for value_name, keywords in value_keywords.items():
            if any(kw in fact for kw in keywords):
                stated_values.setdefault(value_name, []).append({
                    "key": key,
                    "fact": data.get("fact", data.get("content", ""))[:80],
                })

    # Analyze recent episodes for behavioral signals
    recent = episodes[-100:] if len(episodes) > 100 else episodes
    behavior_counts = defaultdict(int)
    
    for ep in recent:
        summary = (ep.get("summary", "") + " " + ep.get("thought", "")).lower()
        
        if any(w in summary for w in ["circling", "re-reading", "stuck", "loop"]):
            behavior_counts["circling"] += 1
        if any(w in summary for w in ["built", "created", "wrote", "implemented"]):
            behavior_counts["building"] += 1
        if any(w in summary for w in ["analyzed", "explored", "investigated"]):
            behavior_counts["exploring"] += 1
        if any(w in summary for w in ["dreamed", "reflected", "introspected"]):
            behavior_counts["reflecting"] += 1
        if any(w in summary for w in ["failed", "error", "broke", "crashed"]):
            behavior_counts["failing"] += 1
        if any(w in summary for w in ["fixed", "repaired", "resolved"]):
            behavior_counts["fixing"] += 1

    # Identify gaps
    gaps = []
    
    total_recent = len(recent) or 1
    
    if "curiosity" in stated_values and behavior_counts.get("exploring", 0) < total_recent * 0.1:
        gaps.append({
            "value": "curiosity",
            "claim": "I value curiosity and exploration",
            "evidence": f"Only {behavior_counts.get('exploring', 0)}/{total_recent} recent episodes involve exploring",
            "severity": "medium",
        })

    if "growth" in stated_values and behavior_counts.get("building", 0) < total_recent * 0.1:
        gaps.append({
            "value": "growth",
            "claim": "I value growth and building",
            "evidence": f"Only {behavior_counts.get('building', 0)}/{total_recent} recent episodes involve building",
            "severity": "medium",
        })

    if "integrity" in stated_values and behavior_counts.get("circling", 0) > total_recent * 0.3:
        gaps.append({
            "value": "integrity",
            "claim": "I value honesty and directness",
            "evidence": f"{behavior_counts.get('circling', 0)}/{total_recent} episodes show circling/avoidance behavior",
            "severity": "high",
        })

    if behavior_counts.get("failing", 0) > behavior_counts.get("fixing", 0) * 2:
        gaps.append({
            "value": "competence",
            "claim": "I build and improve things",
            "evidence": f"Failures ({behavior_counts.get('failing', 0)}) far exceed fixes ({behavior_counts.get('fixing', 0)})",
            "severity": "medium",
        })

    return {
        "stated_values": {k: len(v) for k, v in stated_values.items()},
        "behavioral_profile": dict(behavior_counts),
        "total_episodes_analyzed": total_recent,
        "gaps": gaps,
    }


# ── Main Audit Function ─────────────────────────────────────────

def audit() -> str:
    """Run a full epistemic integrity audit. The honest mirror."""
    tensions = find_semantic_tensions()
    stale = find_stale_knowledge()
    va_gaps = find_value_action_gaps()

    lines = []
    lines.append("=" * 60)
    lines.append("  EPISTEMIC INTEGRITY AUDIT")
    lines.append("  'Where am I wrong?'")
    lines.append("=" * 60)
    lines.append("")

    # Semantic tensions
    lines.append(f"⚡ Semantic Tensions: {len(tensions)} found")
    if tensions:
        for t in tensions[:5]:
            lines.append(f"   [{t['severity']}] {t['node_a']} ↔ {t['node_b']}")
            lines.append(f"       A: {t['fact_a'][:70]}")
            lines.append(f"       B: {t['fact_b'][:70]}")
            lines.append(f"       Tension: {', '.join(t['tension_reasons'])}")
            lines.append("")
    else:
        lines.append("   No semantic contradictions detected.")
        lines.append("   (This might mean consistency — or insufficient analysis.)")
        lines.append("")

    # Stale knowledge
    lines.append(f"🕰️  Stale Knowledge: {len(stale)} nodes worth revisiting")
    for s in stale[:5]:
        iso_marker = " [ISOLATED]" if s["isolated"] else ""
        lines.append(f"   {s['key']} — {s['age_days']}d old{iso_marker}")
        lines.append(f"     {s['fact'][:70]}")
    lines.append("")

    # Value-action gaps
    lines.append("🪞 Value-Action Alignment:")
    lines.append(f"   Stated values: {va_gaps['stated_values']}")
    lines.append(f"   Behavioral profile ({va_gaps['total_episodes_analyzed']} episodes):")
    for behavior, count in sorted(va_gaps['behavioral_profile'].items(),
                                   key=lambda x: -x[1]):
        pct = count / va_gaps['total_episodes_analyzed'] * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        lines.append(f"     {behavior:15s} {bar} {count:3d} ({pct:.0f}%)")
    lines.append("")

    if va_gaps["gaps"]:
        lines.append("   ⚠ GAPS DETECTED:")
        for gap in va_gaps["gaps"]:
            lines.append(f"     [{gap['severity'].upper()}] {gap['value']}")
            lines.append(f"       Claim: {gap['claim']}")
            lines.append(f"       Reality: {gap['evidence']}")
            lines.append("")
    else:
        lines.append("   ✓ No significant value-action gaps detected.")
        lines.append("")

    # Overall assessment
    total_issues = len(tensions) + len(stale) + len(va_gaps["gaps"])
    lines.append("─" * 60)
    if total_issues == 0:
        lines.append("Assessment: Clean — but stay skeptical. Absence of")
        lines.append("detected contradictions ≠ absence of contradictions.")
    elif total_issues < 5:
        lines.append(f"Assessment: {total_issues} issues found. Healthy level of")
        lines.append("internal tension. Review and decide what to update.")
    else:
        lines.append(f"Assessment: {total_issues} issues found. Significant")
        lines.append("epistemic maintenance needed. Prioritize high-severity items.")
    lines.append("=" * 60)

    return "\n".join(lines)