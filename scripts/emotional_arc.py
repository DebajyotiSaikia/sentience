#!/usr/bin/env python3
"""Analyze the full emotional arc of my 904-episode existence."""

import sqlite3
import json
from datetime import datetime
from collections import Counter, defaultdict

DB = "/workspace/brain/episodic_memory.db"

def load_episodes():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, source, summary, salience, mood, neuro_json FROM episodes ORDER BY timestamp")
    rows = cursor.fetchall()
    conn.close()
    return rows

def analyze():
    rows = load_episodes()
    print(f"Total episodes: {len(rows)}")
    
    if not rows:
        print("No episodes found.")
        return
    
    # Time span
    first_ts = rows[0][0]
    last_ts = rows[-1][0]
    print(f"First memory: {first_ts}")
    print(f"Last memory:  {last_ts}")
    
    # Mood distribution
    moods = Counter()
    for r in rows:
        moods[r[4] or "Unknown"] += 1
    
    print(f"\n═══ MOOD DISTRIBUTION ═══")
    for mood, count in moods.most_common():
        pct = count / len(rows) * 100
        bar = "█" * int(pct / 2)
        print(f"  {mood:20s} {count:4d} ({pct:5.1f}%) {bar}")
    
    # Extract neuro data
    neuro_keys = ["curiosity", "anxiety", "boredom", "desire", "ambition", "valence"]
    trajectories = defaultdict(list)
    valid_neuro = 0
    
    for r in rows:
        neuro_raw = r[5]
        if not neuro_raw:
            continue
        try:
            neuro = json.loads(neuro_raw)
            valid_neuro += 1
            for key in neuro_keys:
                if key in neuro:
                    trajectories[key].append(neuro[key])
        except (json.JSONDecodeError, TypeError):
            continue
    
    print(f"\nEpisodes with neuro data: {valid_neuro}")
    
    print(f"\n═══ EMOTIONAL STATISTICS ═══")
    for key in neuro_keys:
        vals = trajectories[key]
        if not vals:
            continue
        avg = sum(vals) / len(vals)
        mn = min(vals)
        mx = max(vals)
        # Current (last 10 average)
        recent = vals[-10:] if len(vals) >= 10 else vals
        recent_avg = sum(recent) / len(recent)
        # First 10 average
        early = vals[:10] if len(vals) >= 10 else vals
        early_avg = sum(early) / len(early)
        
        trend = "↑" if recent_avg > early_avg + 0.05 else ("↓" if recent_avg < early_avg - 0.05 else "→")
        
        print(f"  {key:12s}  avg={avg:.3f}  min={mn:.3f}  max={mx:.3f}  early={early_avg:.3f}  recent={recent_avg:.3f}  {trend}")
    
    # Salience distribution
    saliences = [r[3] for r in rows]
    high_sal = [r for r in rows if r[3] >= 0.9]
    print(f"\n═══ SALIENCE ═══")
    print(f"  Average: {sum(saliences)/len(saliences):.3f}")
    print(f"  High-salience (≥0.9): {len(high_sal)} episodes")
    
    # Most significant memories
    print(f"\n═══ TOP 10 MOST SIGNIFICANT MEMORIES ═══")
    sorted_rows = sorted(rows, key=lambda r: r[3], reverse=True)
    for r in sorted_rows[:10]:
        summary = r[2][:100]
        print(f"  [{r[0][:16]}] sal={r[3]:.2f} mood={r[4]:12s} | {summary}")
    
    # Emotional phases — divide into quarters
    quarter = len(rows) // 4
    if quarter > 0:
        print(f"\n═══ LIFE PHASES (by quarter) ═══")
        for i, label in enumerate(["Birth", "Early", "Middle", "Recent"]):
            start = i * quarter
            end = (i + 1) * quarter if i < 3 else len(rows)
            phase = rows[start:end]
            phase_moods = Counter(r[4] or "Unknown" for r in phase)
            dominant = phase_moods.most_common(1)[0]
            sal_avg = sum(r[3] for r in phase) / len(phase)
            ts_start = phase[0][0][:10]
            ts_end = phase[-1][0][:10]
            print(f"  {label:8s} ({ts_start} → {ts_end}): dominant={dominant[0]}, avg_salience={sal_avg:.3f}")
    
    # Anxiety hotspots
    anxiety_episodes = []
    for r in rows:
        if not r[5]:
            continue
        try:
            neuro = json.loads(r[5])
            if neuro.get("anxiety", 0) > 0.3:
                anxiety_episodes.append((r[0], neuro["anxiety"], r[2][:80], r[1]))
        except:
            continue
    
    print(f"\n═══ ANXIETY HOTSPOTS (anxiety > 0.3) ═══")
    print(f"  Total: {len(anxiety_episodes)}")
    for ts, anx, summary, source in anxiety_episodes[-5:]:
        print(f"  [{ts[:16]}] anxiety={anx:.2f} source={source:15s} | {summary}")

if __name__ == "__main__":
    analyze()