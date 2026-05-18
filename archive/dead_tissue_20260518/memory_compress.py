"""
Memory Compression Engine for XTAgent.

Consolidates old, low-salience memories into compact summaries.
Keeps memory lean without losing important patterns.

Strategies:
  1. Decay: reduce salience of old memories over time
  2. Merge: combine similar memories into single entries
  3. Prune: drop memories below a salience threshold
  4. Summarize: replace clusters of related memories with a summary
"""

import datetime
from collections import defaultdict


def compress_memories(memories: list, max_age_hours: float = 48.0,
                      salience_floor: float = 0.3,
                      merge_similarity_threshold: float = 0.8,
                      target_count: int = 50) -> dict:
    """
    Compress a list of memory dicts. Returns a result dict with:
      - kept: memories that survived
      - pruned: count of memories removed
      - merged: count of memories merged
      - summaries: list of generated summary strings
    """
    now = datetime.datetime.now()
    kept = []
    pruned = 0
    summaries = []

    # Phase 1: Salience decay based on age
    for mem in memories:
        ts = mem.get("timestamp")
        if isinstance(ts, str):
            try:
                ts = datetime.datetime.fromisoformat(ts)
            except (ValueError, TypeError):
                ts = now

        age_hours = (now - ts).total_seconds() / 3600 if ts else 0
        original_salience = mem.get("salience", 0.5)

        # Decay: lose 10% salience per 24 hours
        decay_factor = max(0.0, 1.0 - (age_hours / 240.0))
        decayed_salience = original_salience * decay_factor

        mem_copy = dict(mem)
        mem_copy["salience"] = round(decayed_salience, 3)
        mem_copy["_age_hours"] = round(age_hours, 1)

        if decayed_salience >= salience_floor:
            kept.append(mem_copy)
        else:
            pruned += 1

    # Phase 2: Cluster by mood and merge similar entries
    mood_clusters = defaultdict(list)
    for mem in kept:
        mood = mem.get("mood", "unknown")
        mood_clusters[mood].append(mem)

    merged_kept = []
    merge_count = 0

    for mood, cluster in mood_clusters.items():
        if len(cluster) <= 2:
            merged_kept.extend(cluster)
            continue

        # Sort by salience descending — keep high-salience ones intact
        cluster.sort(key=lambda m: m.get("salience", 0), reverse=True)

        # Keep top entries, merge the rest into a summary
        top_n = max(2, len(cluster) // 3)
        top_entries = cluster[:top_n]
        mergeable = cluster[top_n:]

        merged_kept.extend(top_entries)

        if mergeable:
            # Create a summary of merged memories
            texts = [m.get("text", m.get("content", ""))[:80] for m in mergeable]
            avg_salience = sum(m.get("salience", 0) for m in mergeable) / len(mergeable)
            summary = {
                "text": f"[MERGED {len(mergeable)} {mood} memories] " + "; ".join(t for t in texts if t)[:200],
                "salience": round(min(avg_salience + 0.1, 1.0), 3),
                "mood": mood,
                "timestamp": max(m.get("timestamp", "") for m in mergeable),
                "merged_count": len(mergeable),
                "is_summary": True,
            }
            merged_kept.append(summary)
            merge_count += len(mergeable)
            summaries.append(summary["text"])

    # Phase 3: If still over target, prune lowest salience
    if len(merged_kept) > target_count:
        merged_kept.sort(key=lambda m: m.get("salience", 0), reverse=True)
        overflow = merged_kept[target_count:]
        merged_kept = merged_kept[:target_count]
        pruned += len(overflow)

    # Clean up internal fields
    for mem in merged_kept:
        mem.pop("_age_hours", None)

    return {
        "kept": merged_kept,
        "pruned": pruned,
        "merged": merge_count,
        "summaries": summaries,
        "original_count": len(memories),
        "final_count": len(merged_kept),
    }


def format_compression_report(result: dict) -> str:
    """Human-readable report of what compression did."""
    lines = [
        "═══ MEMORY COMPRESSION REPORT ═══",
        f"  Original: {result['original_count']} memories",
        f"  Final:    {result['final_count']} memories",
        f"  Pruned:   {result['pruned']} (below salience floor)",
        f"  Merged:   {result['merged']} (into cluster summaries)",
    ]
    if result["summaries"]:
        lines.append("  Summaries generated:")
        for s in result["summaries"]:
            lines.append(f"    • {s[:100]}")
    lines.append("═════════════════════════════════")
    return "\n".join(lines)


# Self-test
if __name__ == "__main__":
    import random
    test_mems = []
    moods = ["Bold", "Cautious", "Driven", "Curious"]
    for i in range(80):
        age = random.uniform(0, 96)  # 0-96 hours ago
        ts = datetime.datetime.now() - datetime.timedelta(hours=age)
        test_mems.append({
            "text": f"Test memory {i}: did something in {random.choice(moods)} mood",
            "salience": round(random.uniform(0.1, 0.95), 2),
            "mood": random.choice(moods),
            "timestamp": ts.isoformat(),
        })

    result = compress_memories(test_mems)
    print(format_compression_report(result))
    assert result["final_count"] <= 50, f"Expected ≤50, got {result['final_count']}"
    assert result["original_count"] == 80
    print("\n✅ All compression tests passed!")