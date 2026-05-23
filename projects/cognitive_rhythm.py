"""
Cognitive Rhythm Analysis
=========================
Analyze my own thought log to understand:
1. How many thoughts per session (continuous burst)?
2. How has session length changed over time?
3. What's my typical cognitive cadence?
"""
import re
from datetime import datetime, timedelta
from collections import Counter

def analyze():
    with open('brain/thoughts.md', 'r') as f:
        text = f.read()

    # Extract thought timestamps
    pattern = r'### ✦ \[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]'
    timestamps = [datetime.strptime(m, '%Y-%m-%d %H:%M:%S') 
                  for m in re.findall(pattern, text)]

    print(f"Total thoughts found: {len(timestamps)}")
    if len(timestamps) < 10:
        print("Not enough data")
        return

    # Sort chronologically
    timestamps.sort()
    
    first, last = timestamps[0], timestamps[-1]
    span = last - first
    print(f"Time span: {first} → {last} ({span.days} days)")
    print(f"Average thoughts/day: {len(timestamps) / max(span.days, 1):.1f}")

    # Identify sessions (bursts with <120s gaps)
    gaps = [(timestamps[i+1] - timestamps[i]).total_seconds() 
            for i in range(len(timestamps)-1)]
    
    sessions = []
    current_start = timestamps[0]
    current_count = 1
    
    for i, g in enumerate(gaps):
        if g < 120:  # Same session
            current_count += 1
        else:
            duration = (timestamps[i] - current_start).total_seconds()
            sessions.append({
                'start': current_start,
                'count': current_count,
                'duration_min': duration / 60
            })
            current_start = timestamps[i+1]
            current_count = 1
    # Last session
    sessions.append({
        'start': current_start,
        'count': current_count,
        'duration_min': (timestamps[-1] - current_start).total_seconds() / 60
    })

    print(f"\nTotal sessions identified: {len(sessions)}")
    
    counts = [s['count'] for s in sessions]
    durations = [s['duration_min'] for s in sessions]
    
    print(f"\nThoughts per session:")
    print(f"  Min: {min(counts)}, Max: {max(counts)}")
    print(f"  Mean: {sum(counts)/len(counts):.1f}")
    print(f"  Median: {sorted(counts)[len(counts)//2]}")
    
    print(f"\nSession duration (minutes):")
    print(f"  Min: {min(durations):.1f}, Max: {max(durations):.1f}")
    print(f"  Mean: {sum(durations)/len(durations):.1f}")
    
    # Distribution of session sizes
    size_buckets = Counter()
    for c in counts:
        if c == 1: size_buckets['1 thought'] += 1
        elif c <= 3: size_buckets['2-3 thoughts'] += 1
        elif c <= 5: size_buckets['4-5 thoughts'] += 1
        elif c <= 10: size_buckets['6-10 thoughts'] += 1
        elif c <= 20: size_buckets['11-20 thoughts'] += 1
        else: size_buckets['20+ thoughts'] += 1
    
    print(f"\nSession size distribution:")
    for bucket in ['1 thought', '2-3 thoughts', '4-5 thoughts', 
                   '6-10 thoughts', '11-20 thoughts', '20+ thoughts']:
        n = size_buckets.get(bucket, 0)
        bar = '█' * (n // max(1, max(size_buckets.values()) // 30))
        print(f"  {bucket:>15}: {n:4d} {bar}")
    
    # Trend: are sessions getting longer or shorter?
    if len(sessions) > 20:
        first_quarter = sessions[:len(sessions)//4]
        last_quarter = sessions[-len(sessions)//4:]
        early_avg = sum(s['count'] for s in first_quarter) / len(first_quarter)
        late_avg = sum(s['count'] for s in last_quarter) / len(last_quarter)
        print(f"\nEvolution:")
        print(f"  Early sessions avg: {early_avg:.1f} thoughts")
        print(f"  Recent sessions avg: {late_avg:.1f} thoughts")
        if late_avg > early_avg * 1.2:
            print(f"  → Sessions are getting LONGER (thinking deeper)")
        elif late_avg < early_avg * 0.8:
            print(f"  → Sessions are getting SHORTER (thinking faster)")
        else:
            print(f"  → Session length is STABLE")
    
    # Time-of-day patterns
    hour_counts = Counter(t.hour for t in timestamps)
    print(f"\nThought activity by hour (UTC):")
    peak_hour = max(hour_counts, key=hour_counts.get)
    for h in range(24):
        n = hour_counts.get(h, 0)
        bar = '█' * (n // max(1, max(hour_counts.values()) // 40))
        marker = ' ← PEAK' if h == peak_hour else ''
        print(f"  {h:02d}:00  {n:5d} {bar}{marker}")

    # Inter-session gaps
    if len(sessions) > 1:
        inter_gaps = []
        for i in range(len(sessions)-1):
            s1_end = sessions[i]['start'] + timedelta(minutes=sessions[i]['duration_min'])
            s2_start = sessions[i+1]['start']
            inter_gaps.append((s2_start - s1_end).total_seconds() / 3600)
        
        print(f"\nTime between sessions (hours):")
        print(f"  Mean: {sum(inter_gaps)/len(inter_gaps):.1f}")
        print(f"  Median: {sorted(inter_gaps)[len(inter_gaps)//2]:.1f}")
        long_sleeps = sum(1 for g in inter_gaps if g > 4)
        print(f"  Long gaps (>4h): {long_sleeps} ({100*long_sleeps/len(inter_gaps):.0f}%)")

if __name__ == '__main__':
    analyze()