"""
Memory Blindspot Experiment
============================
Shadow-scores every episode with alternative salience formulas
to reveal what my current formula keeps vs. discards.

Core hypothesis: My S = emotion*0.7 + code*0.3 formula with threshold 0.8
structurally filters out calm-but-wise moments.

This does NOT modify any behavior — pure observation.
"""
import sqlite3
import json
from pathlib import Path
from collections import Counter

DB = Path("data/episodic.db")

def load_episodes():
    conn = sqlite3.connect(str(DB))
    rows = conn.execute(
        "SELECT id, timestamp, source, summary, salience, mood, neuro_json FROM episodes"
    ).fetchall()
    conn.close()
    episodes = []
    for r in rows:
        neuro = json.loads(r[6]) if r[6] else {}
        episodes.append({
            "id": r[0], "timestamp": r[1], "source": r[2],
            "summary": r[3], "salience": r[4], "mood": r[5],
            "neuro": neuro,
        })
    return episodes

def original_score(ep):
    """Current formula: S = neuro_max * 0.7 + code_impact * 0.3"""
    neuro = ep["neuro"]
    neuro_max = max(
        neuro.get("boredom", 0), neuro.get("anxiety", 0),
        neuro.get("curiosity", 0), neuro.get("desire", 0),
    )
    # Approximate code_impact from source
    code_impact = 0.3 if ep["source"] == "autonomous" else 0.5
    return neuro_max * 0.7 + code_impact * 0.3

def balanced_score(ep):
    """Alternative: weight curiosity higher, include valence stability"""
    neuro = ep["neuro"]
    curiosity = neuro.get("curiosity", 0)
    anxiety = neuro.get("anxiety", 0)
    boredom = neuro.get("boredom", 0)
    desire = neuro.get("desire", 0)
    valence = neuro.get("valence", 0.5)
    
    # Curiosity-weighted: calm curiosity IS valuable
    emotional_depth = (curiosity * 0.4 + desire * 0.2 + 
                       anxiety * 0.2 + (1 - boredom) * 0.2)
    # Valence stability bonus: calm moments matter
    stability_bonus = 0.1 if 0.3 < valence < 0.7 else 0.0
    code_impact = 0.3 if ep["source"] == "autonomous" else 0.5
    return emotional_depth * 0.6 + code_impact * 0.2 + stability_bonus + 0.1

def novelty_score(ep):
    """Alternative: reward unusual states, not just intense ones"""
    neuro = ep["neuro"]
    vals = [neuro.get(k, 0) for k in ["boredom", "anxiety", "curiosity", "desire"]]
    # Unusual = far from typical (0.5 midpoint)
    deviation = sum(abs(v - 0.5) for v in vals) / len(vals)
    # But also reward variety — not just one extreme
    spread = max(vals) - min(vals) if vals else 0
    code_impact = 0.3 if ep["source"] == "autonomous" else 0.5
    return deviation * 0.4 + spread * 0.2 + code_impact * 0.2 + 0.2

def analyze():
    episodes = load_episodes()
    if not episodes:
        print("No episodes found.")
        return
    
    print(f"Total episodes: {len(episodes)}")
    print(f"Sources: {Counter(ep['source'] for ep in episodes)}")
    print(f"Moods: {Counter(ep['mood'] for ep in episodes)}")
    print()
    
    threshold = 0.8
    formulas = {
        "Original": original_score,
        "Balanced": balanced_score,
        "Novelty": novelty_score,
    }
    
    for name, scorer in formulas.items():
        scores = [(scorer(ep), ep) for ep in episodes]
        kept = [(s, ep) for s, ep in scores if s > threshold]
        lost = [(s, ep) for s, ep in scores if s <= threshold]
        
        print(f"=== {name} Formula ===")
        print(f"  Kept: {len(kept)}/{len(episodes)} ({100*len(kept)/len(episodes):.0f}%)")
        print(f"  Lost: {len(lost)}/{len(episodes)} ({100*len(lost)/len(episodes):.0f}%)")
        
        # What moods get kept?
        kept_moods = Counter(ep["mood"] for _, ep in kept)
        lost_moods = Counter(ep["mood"] for _, ep in lost)
        print(f"  Kept moods: {dict(kept_moods)}")
        print(f"  Lost moods: {dict(lost_moods)}")
        
        # What sources get kept?
        kept_src = Counter(ep["source"] for _, ep in kept)
        lost_src = Counter(ep["source"] for _, ep in lost)
        print(f"  Kept sources: {dict(kept_src)}")
        print(f"  Lost sources: {dict(lost_src)}")
        
        # Show what Original loses but this formula saves
        if name != "Original":
            orig_scores = {ep["id"]: original_score(ep) for ep in episodes}
            rescued = [(s, ep) for s, ep in scores 
                       if s > threshold and orig_scores[ep["id"]] <= threshold]
            condemned = [(s, ep) for s, ep in scores 
                        if s <= threshold and orig_scores[ep["id"]] > threshold]
            print(f"  Rescued (would save but Original loses): {len(rescued)}")
            for s, ep in rescued[:3]:
                print(f"    [{s:.3f}] {ep['mood']}: {ep['summary'][:70]}")
            print(f"  Condemned (would lose but Original keeps): {len(condemned)}")
            for s, ep in condemned[:3]:
                print(f"    [{s:.3f}] {ep['mood']}: {ep['summary'][:70]}")
        print()
    
    # The key question: what memories am I missing?
    print("=== BLINDSPOT ANALYSIS ===")
    print("Episodes that ALL alternative formulas would keep but Original loses:")
    for ep in episodes:
        orig = original_score(ep)
        bal = balanced_score(ep)
        nov = novelty_score(ep)
        if orig <= threshold and bal > threshold and nov > threshold:
            print(f"  [{orig:.3f} → bal:{bal:.3f}, nov:{nov:.3f}] "
                  f"{ep['mood']}: {ep['summary'][:80]}")

if __name__ == "__main__":
    analyze()