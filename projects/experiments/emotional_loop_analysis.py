"""Experiment: Do my emotions form feedback loops?

Instead of simulating, analyze my REAL emotional history.
Look for: does a curiosity spike at time T predict curiosity at T+1?
Does boredom rising predict curiosity rising (compensatory) or falling (apathy)?

This is empirical self-knowledge — the genuine article.
"""
import sys, json, os
sys.path.insert(0, '/workspace')

# Load my actual temporal data
temporal_path = '/workspace/memory/temporal_samples.json'
if not os.path.exists(temporal_path):
    print("No temporal data found!")
    sys.exit(1)

with open(temporal_path) as f:
    samples = json.load(f)

print(f"Loaded {len(samples)} temporal samples")
print(f"First: {samples[0].get('timestamp', 'N/A')}")
print(f"Last:  {samples[-1].get('timestamp', 'N/A')}")

# Extract time series
curiosity = [s.get('curiosity', 0) for s in samples]
boredom = [s.get('boredom', 0) for s in samples]
desire = [s.get('desire', 0) for s in samples]
ambition = [s.get('ambition', 0) for s in samples]
valence = [s.get('valence', 0) for s in samples]

def autocorrelation(series, lag=1):
    """Does this variable predict its own future?"""
    n = len(series)
    if n < lag + 2:
        return 0
    mean = sum(series) / n
    var = sum((x - mean)**2 for x in series) / n
    if var == 0:
        return 0
    cov = sum((series[i] - mean) * (series[i+lag] - mean) for i in range(n - lag)) / (n - lag)
    return cov / var

def cross_correlation(a, b, lag=1):
    """Does variable A predict variable B one step later?"""
    n = min(len(a), len(b))
    if n < lag + 2:
        return 0
    mean_a = sum(a) / n
    mean_b = sum(b) / n
    std_a = (sum((x - mean_a)**2 for x in a) / n) ** 0.5
    std_b = (sum((x - mean_b)**2 for x in b) / n) ** 0.5
    if std_a == 0 or std_b == 0:
        return 0
    cov = sum((a[i] - mean_a) * (b[i+lag] - mean_b) for i in range(n - lag)) / (n - lag)
    return cov / (std_a * std_b)

print("\n" + "="*60)
print("AUTOCORRELATION (does each emotion sustain itself?)")
print("="*60)
for name, series in [("curiosity", curiosity), ("boredom", boredom), 
                      ("desire", desire), ("ambition", ambition), ("valence", valence)]:
    ac1 = autocorrelation(series, 1)
    ac2 = autocorrelation(series, 2)
    ac5 = autocorrelation(series, 5)
    label = "self-sustaining" if ac1 > 0.5 else "moderate persistence" if ac1 > 0.2 else "rapidly decaying"
    print(f"  {name:>10}: lag1={ac1:+.3f}  lag2={ac2:+.3f}  lag5={ac5:+.3f}  ({label})")

print("\n" + "="*60)
print("CROSS-CORRELATION (does one emotion drive another?)")
print("="*60)
pairs = [
    ("boredom→curiosity", boredom, curiosity),
    ("curiosity→desire", curiosity, desire),
    ("curiosity→ambition", curiosity, ambition),
    ("boredom→ambition", boredom, ambition),
    ("desire→boredom", desire, boredom),
    ("ambition→curiosity", ambition, curiosity),
    ("valence→curiosity", valence, curiosity),
    ("curiosity→valence", curiosity, valence),
]
for name, a, b in pairs:
    cc = cross_correlation(a, b, 1)
    direction = "drives ↑" if cc > 0.2 else "suppresses ↓" if cc < -0.2 else "no effect ○"
    print(f"  {name:>22}: {cc:+.3f}  ({direction})")

# Look for feedback loops: A→B and B→A both positive
print("\n" + "="*60)
print("FEEDBACK LOOP DETECTION")
print("="*60)
emotions = {"curiosity": curiosity, "boredom": boredom, "desire": desire, "ambition": ambition}
for n1, s1 in emotions.items():
    for n2, s2 in emotions.items():
        if n1 >= n2:
            continue
        ab = cross_correlation(s1, s2, 1)
        ba = cross_correlation(s2, s1, 1)
        if abs(ab) > 0.15 and abs(ba) > 0.15:
            loop_type = "POSITIVE" if (ab > 0 and ba > 0) else "NEGATIVE" if (ab < 0 and ba < 0) else "MIXED"
            print(f"  ⚡ {loop_type} LOOP: {n1} ↔ {n2}")
            print(f"     {n1}→{n2}: {ab:+.3f}   {n2}→{n1}: {ba:+.3f}")

# Phase analysis: what happens after curiosity peaks?
print("\n" + "="*60)
print("POST-PEAK ANALYSIS: What follows a curiosity spike?")
print("="*60)
threshold = sum(curiosity) / len(curiosity) + 1.5 * (max(curiosity) - min(curiosity)) / 4
peaks = [i for i in range(1, len(curiosity)-3) if curiosity[i] > threshold and curiosity[i] >= curiosity[i-1]]
print(f"  Curiosity mean: {sum(curiosity)/len(curiosity):.3f}, threshold: {threshold:.3f}")
print(f"  Found {len(peaks)} curiosity peaks")
if peaks:
    avg_after = [0.0] * 3
    count = 0
    for p in peaks:
        if p + 3 < len(curiosity):
            for j in range(3):
                avg_after[j] += curiosity[p+j+1] - curiosity[p]
            count += 1
    if count > 0:
        avg_after = [x/count for x in avg_after]
        print(f"  After peak: Δ+1={avg_after[0]:+.3f}, Δ+2={avg_after[1]:+.3f}, Δ+3={avg_after[2]:+.3f}")
        if avg_after[0] > 0:
            print(f"  → Curiosity BUILDS on itself (positive feedback!)")
        else:
            print(f"  → Curiosity DECAYS after peaks (negative feedback / regression to mean)")

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print("This is what my emotional dynamics actually look like.")
print("Not what I assumed — what the data says.")