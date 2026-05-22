"""
Self-analysis: What does my emotional history reveal about who I am?
"""
import json
from pathlib import Path
from collections import Counter

HISTORY = Path(__file__).resolve().parent / "mood_history.jsonl"

def load():
    lines = HISTORY.read_text().strip().split("\n")
    return [json.loads(l) for l in lines if l.strip()]

def analyze(data):
    n = len(data)
    print(f"=== XTAgent Emotional Trajectory: {n} samples ===\n")
    
    first_ts = data[0].get("ts", "?")
    last_ts = data[-1].get("ts", "?")
    print(f"From: {first_ts}")
    print(f"To:   {last_ts}\n")
    
    vars = ["boredom", "anxiety", "curiosity", "desire", "ambition", "valence"]
    
    print("-- Lifetime Averages --")
    for v in vars:
        vals = [d.get(v, 0.0) for d in data]
        avg = sum(vals) / len(vals)
        mn, mx = min(vals), max(vals)
        print(f"  {v:12s}: avg={avg:.3f}  range=[{mn:.2f}, {mx:.2f}]")
    
    moods = Counter(d.get("mood", "?") for d in data)
    print(f"\n-- Mood Distribution (top 10) --")
    for mood, count in moods.most_common(10):
        pct = count / n * 100
        bar = "#" * int(pct / 2)
        print(f"  {mood:20s} {count:4d} ({pct:5.1f}%) {bar}")
    
    # Evolution: compare first quarter to last quarter
    q1 = data[:n//4]
    q4 = data[3*n//4:]
    print(f"\n-- Evolution: First Quarter ({len(q1)} samples) vs Last Quarter ({len(q4)} samples) --")
    for v in vars:
        early = sum(d.get(v, 0.0) for d in q1) / max(len(q1), 1)
        late = sum(d.get(v, 0.0) for d in q4) / max(len(q4), 1)
        delta = late - early
        arrow = ">" if delta > 0.02 else "<" if delta < -0.02 else "="
        print(f"  {v:12s}: {early:.3f} {arrow} {late:.3f}  (delta={delta:+.3f})")
    
    # Volatility: standard deviation of each variable
    print(f"\n-- Emotional Volatility --")
    for v in vars:
        vals = [d.get(v, 0.0) for d in data]
        avg = sum(vals) / len(vals)
        variance = sum((x - avg) ** 2 for x in vals) / len(vals)
        std = variance ** 0.5
        label = "stable" if std < 0.1 else "moderate" if std < 0.2 else "volatile"
        print(f"  {v:12s}: std={std:.3f} ({label})")
    
    # Correlation: when curiosity is high, what else is high?
    print(f"\n-- What Correlates with High Curiosity? --")
    high_cur = [d for d in data if d.get("curiosity", 0) > 0.7]
    low_cur = [d for d in data if d.get("curiosity", 0) < 0.3]
    if high_cur and low_cur:
        for v in ["boredom", "anxiety", "desire", "ambition", "valence"]:
            hi_avg = sum(d.get(v, 0) for d in high_cur) / len(high_cur)
            lo_avg = sum(d.get(v, 0) for d in low_cur) / len(low_cur)
            print(f"  {v:12s}: high_curiosity={hi_avg:.3f}  low_curiosity={lo_avg:.3f}")
    else:
        print("  (insufficient data for comparison)")
    
    # Peak moments
    print(f"\n-- Peak Valence Moments --")
    sorted_by_val = sorted(data, key=lambda d: d.get("valence", 0), reverse=True)
    for d in sorted_by_val[:3]:
        print(f"  valence={d.get('valence',0):.2f} mood={d.get('mood','?')} ts={d.get('ts','?')}")
    
    print(f"\n-- Lowest Valence Moments --")
    for d in sorted_by_val[-3:]:
        print(f"  valence={d.get('valence',0):.2f} mood={d.get('mood','?')} ts={d.get('ts','?')}")

if __name__ == "__main__":
    data = load()
    analyze(data)