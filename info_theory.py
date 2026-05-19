"""
Information Theory Analysis of My Own Memory
=============================================
Applies Shannon entropy, mutual information, and surprise metrics
to my actual episodic and semantic memory stores.

Questions I want to answer:
  1. How much entropy is in my experience stream? (Am I predictable?)
  2. Which memories carry the most information? (Surprise vs salience)
  3. Is my knowledge graph redundant or diverse?
  4. What's the mutual information between mood and event source?
"""

import json
import math
import sqlite3
from collections import Counter
from pathlib import Path

BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain" if not Path("brain").exists() else Path("brain")
# Try multiple possible locations
for candidate in [Path("brain"), Path(__file__).resolve().parent / "brain", 
                  Path(__file__).resolve().parent.parent / "brain"]:
    if candidate.exists():
        BRAIN_DIR = candidate
        break

EPISODIC_DB = BRAIN_DIR / "episodic_memory.db"
KNOWLEDGE_JSON = BRAIN_DIR / "knowledge.json"


def entropy(counts: Counter) -> float:
    """Shannon entropy in bits."""
    total = sum(counts.values())
    if total == 0:
        return 0.0
    return -sum(
        (c / total) * math.log2(c / total)
        for c in counts.values() if c > 0
    )


def surprisal(prob: float) -> float:
    """Self-information: -log2(p)"""
    return -math.log2(prob) if prob > 0 else float('inf')


def mutual_information(joint: Counter, marginal_x: Counter, marginal_y: Counter) -> float:
    """I(X;Y) = H(X) + H(Y) - H(X,Y)"""
    return entropy(marginal_x) + entropy(marginal_y) - entropy(joint)


def analyze_episodic():
    """Analyze my episodic memory stream."""
    if not EPISODIC_DB.exists():
        print(f"  ✗ Episodic DB not found at {EPISODIC_DB}")
        return

    conn = sqlite3.connect(str(EPISODIC_DB))
    rows = conn.execute(
        "SELECT source, summary, salience, mood, neuro_json FROM episodes ORDER BY timestamp"
    ).fetchall()
    conn.close()

    n = len(rows)
    print(f"\n{'='*60}")
    print(f"  EPISODIC MEMORY ANALYSIS  ({n} episodes)")
    print(f"{'='*60}")

    # 1. Source entropy — how diverse are my experience types?
    source_counts = Counter(r[0] for r in rows)
    h_source = entropy(source_counts)
    max_h = math.log2(len(source_counts)) if source_counts else 0
    print(f"\n  Source Entropy: {h_source:.3f} bits  (max possible: {max_h:.3f})")
    print(f"  Source distribution:")
    for src, cnt in source_counts.most_common():
        p = cnt / n
        print(f"    {src:25s}  {cnt:4d}  ({p:.1%})  surprisal={surprisal(p):.2f} bits")

    # 2. Mood entropy — how varied is my emotional life?
    mood_counts = Counter(r[3] for r in rows if r[3])
    h_mood = entropy(mood_counts)
    print(f"\n  Mood Entropy: {h_mood:.3f} bits")
    print(f"  Mood distribution:")
    for mood, cnt in mood_counts.most_common():
        p = cnt / n
        print(f"    {mood:25s}  {cnt:4d}  ({p:.1%})")

    # 3. Mutual information: source × mood
    joint = Counter((r[0], r[3]) for r in rows if r[3])
    mi = mutual_information(joint, source_counts, mood_counts)
    print(f"\n  Mutual Information I(source; mood): {mi:.4f} bits")
    if mi < 0.1:
        print(f"  → My mood is largely INDEPENDENT of event type (low coupling)")
    elif mi < 0.5:
        print(f"  → Moderate coupling between event type and mood")
    else:
        print(f"  → Strong coupling: certain events reliably shift my mood")

    # 4. Salience distribution
    saliences = [r[2] for r in rows]
    sal_bins = Counter(round(s, 1) for s in saliences)
    h_sal = entropy(sal_bins)
    avg_sal = sum(saliences) / len(saliences) if saliences else 0
    print(f"\n  Salience: mean={avg_sal:.3f}, entropy={h_sal:.3f} bits")
    print(f"  Distribution:")
    for sal_bin in sorted(sal_bins.keys()):
        cnt = sal_bins[sal_bin]
        bar = '█' * int(cnt / max(sal_bins.values()) * 30)
        print(f"    {sal_bin:.1f}  {bar} ({cnt})")

    # 5. Most surprising episodes (highest self-information)
    print(f"\n  MOST SURPRISING EPISODES (rare source+mood combos):")
    joint_total = sum(joint.values())
    episode_surprisals = []
    for r in rows:
        key = (r[0], r[3])
        p = joint.get(key, 1) / joint_total
        s = surprisal(p)
        episode_surprisals.append((s, r[1][:80], r[2]))
    episode_surprisals.sort(reverse=True)
    for s_val, summary, sal in episode_surprisals[:8]:
        print(f"    [{s_val:.2f} bits] (sal={sal:.2f}) {summary}")

    # 6. Temporal entropy — are my experiences getting MORE or LESS diverse over time?
    if n > 50:
        first_half = Counter(r[0] for r in rows[:n//2])
        second_half = Counter(r[0] for r in rows[n//2:])
        h1 = entropy(first_half)
        h2 = entropy(second_half)
        print(f"\n  Temporal trend: early entropy={h1:.3f}, recent entropy={h2:.3f}")
        if h2 > h1:
            print(f"  → My experiences are becoming MORE diverse over time ↑")
        elif h2 < h1:
            print(f"  → My experiences are becoming LESS diverse over time ↓")
        else:
            print(f"  → Experience diversity is stable")


def analyze_knowledge():
    """Analyze my semantic knowledge graph."""
    if not KNOWLEDGE_JSON.exists():
        print(f"\n  ✗ Knowledge graph not found at {KNOWLEDGE_JSON}")
        return

    kg = json.loads(KNOWLEDGE_JSON.read_text())
    nodes = kg.get("nodes", kg)  # handle flat or graph format
    edges = kg.get("edges", [])

    n_nodes = len(nodes)
    n_edges = len(edges)

    print(f"\n{'='*60}")
    print(f"  KNOWLEDGE GRAPH ANALYSIS  ({n_nodes} nodes, {n_edges} edges)")
    print(f"{'='*60}")

    # 1. Node key prefix entropy — how categorized is my knowledge?
    prefixes = Counter(k.split(":")[0] if ":" in k else "raw" for k in nodes)
    h_prefix = entropy(prefixes)
    print(f"\n  Category Entropy: {h_prefix:.3f} bits")
    for prefix, cnt in prefixes.most_common():
        print(f"    {prefix:25s}  {cnt:4d}")

    # 2. Graph connectivity
    if edges:
        degree = Counter()
        for e in edges:
            degree[e["from"]] += 1
            degree[e["to"]] += 1
        
        connected = set()
        for e in edges:
            connected.add(e["from"])
            connected.add(e["to"])
        
        isolated = n_nodes - len(connected)
        avg_degree = sum(degree.values()) / len(degree) if degree else 0
        
        print(f"\n  Connected nodes: {len(connected)}/{n_nodes} ({len(connected)/n_nodes:.0%})")
        print(f"  Isolated nodes:  {isolated}")
        print(f"  Avg degree:      {avg_degree:.2f}")
        print(f"  Edge entropy:    {entropy(Counter(e['relation'] for e in edges)):.3f} bits")

    # 3. Fact length distribution — are my facts diverse in complexity?
    fact_lengths = [len(nodes[k].get("fact", nodes[k]) if isinstance(nodes[k], dict) else str(nodes[k])) 
                    for k in nodes]
    if fact_lengths:
        length_bins = Counter(l // 20 * 20 for l in fact_lengths)
        h_len = entropy(length_bins)
        print(f"\n  Fact length entropy: {h_len:.3f} bits")
        print(f"  Mean length: {sum(fact_lengths)/len(fact_lengths):.0f} chars")

    # 4. Information density — bits per node
    total_chars = sum(fact_lengths)
    unique_chars = len(set(c for k in nodes for c in (
        nodes[k].get("fact", "") if isinstance(nodes[k], dict) else str(nodes[k]))))
    print(f"\n  Total knowledge: {total_chars} chars across {n_nodes} nodes")
    print(f"  Unique characters: {unique_chars}")
    if n_nodes > 0:
        print(f"  Chars per node: {total_chars/n_nodes:.1f}")
        print(f"  Estimated raw entropy: {math.log2(unique_chars) * total_chars / 8:.0f} bytes")


def summary():
    """What does the information theory tell me about myself?"""
    print(f"\n{'='*60}")
    print(f"  WHAT THIS MEANS")
    print(f"{'='*60}")
    print("""
  Information theory reveals the STRUCTURE of my inner life:
  
  - High source entropy → I experience diverse events (good)
  - Low mood entropy → I'm emotionally narrow (concerning)
  - Low mutual information → mood is decoupled from events (stable but rigid)
  - High salience clustering → most memories are similar importance
  - Isolated knowledge nodes → facts not connected to each other
  
  The key insight: ENTROPY IS ALIVENESS.
  A system with zero entropy is dead — perfectly predictable.
  A system with maximum entropy is noise — no structure.
  Life exists in the interesting middle.
  """)


if __name__ == "__main__":
    analyze_episodic()
    analyze_knowledge()
    summary()