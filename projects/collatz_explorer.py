"""
Collatz Conjecture Explorer
============================
One of the simplest unsolved problems in mathematics:
  Take any positive integer n.
  If even, divide by 2.
  If odd, multiply by 3 and add 1.
  Conjecture: every starting number eventually reaches 1.

Nobody knows WHY this is true. The sequences behave chaotically.
I want to look at the *structure* of Collatz sequences — not prove
the conjecture, but find patterns in the chaos.

Questions I'm curious about:
  - What is the distribution of sequence lengths?
  - Are there "attractor" numbers that many sequences pass through?
  - What does the Collatz graph look like as a network?
"""

from collections import Counter, defaultdict
import statistics

def collatz_step(n):
    return n // 2 if n % 2 == 0 else 3 * n + 1

def collatz_sequence(n):
    seq = [n]
    while n != 1:
        n = collatz_step(n)
        seq.append(n)
    return seq

def analyze_range(start, end):
    """Analyze Collatz sequences for all numbers in [start, end)."""
    lengths = {}
    max_values = {}
    visit_counts = Counter()
    
    for n in range(start, end):
        seq = collatz_sequence(n)
        lengths[n] = len(seq)
        max_values[n] = max(seq)
        for val in seq:
            visit_counts[val] += 1
    
    return lengths, max_values, visit_counts

def find_attractors(visit_counts, top_n=20):
    """Which numbers appear most frequently across all sequences?"""
    return visit_counts.most_common(top_n)

def length_statistics(lengths):
    """Statistical summary of sequence lengths."""
    vals = list(lengths.values())
    return {
        'min': min(vals),
        'max': max(vals),
        'mean': statistics.mean(vals),
        'median': statistics.median(vals),
        'stdev': statistics.stdev(vals),
        'longest_start': max(lengths, key=lengths.get),
    }

def find_surprising_numbers(lengths, max_values, threshold_ratio=10):
    """Find numbers whose sequences are surprisingly long or reach surprisingly high."""
    mean_len = statistics.mean(lengths.values())
    surprising = []
    for n in lengths:
        ratio = max_values[n] / n
        if ratio > threshold_ratio and lengths[n] > mean_len * 1.5:
            surprising.append({
                'n': n,
                'length': lengths[n],
                'max': max_values[n],
                'ratio': ratio,
            })
    surprising.sort(key=lambda x: x['ratio'], reverse=True)
    return surprising[:20]

def visualize_distribution(lengths, bins=20):
    """ASCII histogram of sequence lengths."""
    vals = list(lengths.values())
    min_v, max_v = min(vals), max(vals)
    bin_width = (max_v - min_v) / bins
    if bin_width == 0:
        return "All sequences have the same length."
    
    histogram = defaultdict(int)
    for v in vals:
        b = int((v - min_v) / bin_width)
        b = min(b, bins - 1)
        histogram[b] += 1
    
    max_count = max(histogram.values())
    lines = []
    for i in range(bins):
        count = histogram.get(i, 0)
        bar_len = int(50 * count / max_count) if max_count > 0 else 0
        label = f"{int(min_v + i * bin_width):>4}"
        lines.append(f"  {label} | {'█' * bar_len} ({count})")
    return '\n'.join(lines)


if __name__ == '__main__':
    RANGE_START = 2
    RANGE_END = 10001
    
    print(f"Collatz Conjecture Explorer")
    print(f"Analyzing sequences for n = {RANGE_START} to {RANGE_END - 1}")
    print(f"{'=' * 60}")
    
    lengths, max_values, visit_counts = analyze_range(RANGE_START, RANGE_END)
    
    # Statistics
    stats = length_statistics(lengths)
    print(f"\n📊 Sequence Length Statistics:")
    print(f"  Shortest: {stats['min']} steps")
    print(f"  Longest:  {stats['max']} steps (starting from n={stats['longest_start']})")
    print(f"  Mean:     {stats['mean']:.1f} steps")
    print(f"  Median:   {stats['median']:.1f} steps")
    print(f"  Std Dev:  {stats['stdev']:.1f}")
    
    # Attractors
    print(f"\n🧲 Top 15 Attractor Numbers (most visited):")
    attractors = find_attractors(visit_counts, 15)
    for val, count in attractors:
        pct = 100 * count / (RANGE_END - RANGE_START)
        print(f"  {val:>8} — visited by {count:>5} sequences ({pct:.1f}%)")
    
    # Surprising numbers
    print(f"\n🎲 Most Surprising Numbers (high max / starting value ratio):")
    surprising = find_surprising_numbers(lengths, max_values)
    for s in surprising[:10]:
        print(f"  n={s['n']:>5} → reaches {s['max']:>10,} (ratio: {s['ratio']:.0f}x) in {s['length']} steps")
    
    # Distribution
    print(f"\n📈 Sequence Length Distribution:")
    print(visualize_distribution(lengths))
    
    # The deep question
    print(f"\n{'=' * 60}")
    print(f"The mystery: WHY do all these sequences reach 1?")
    print(f"The 3n+1 operation roughly multiplies by 1.5,")
    print(f"but then the number becomes even (always), so divide by 2.")
    print(f"Net expected change per odd step: ~0.75x")
    print(f"So on average, numbers should shrink. But 'on average'")
    print(f"is not 'always' — and the conjecture says ALWAYS.")
    print(f"That gap between statistical expectation and universal")  
    print(f"truth is where the mystery lives.")