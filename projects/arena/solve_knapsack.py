"""
Solution: 0/1 Knapsack Problem
Classic dynamic programming — build a table of optimal values.
"""
import sys
sys.path.insert(0, '/workspace/arena')
from challenge_engine import CHALLENGES, run_challenge, record_result
import time

def knapsack(capacity, weights, values):
    """0/1 knapsack using bottom-up DP."""
    n = len(weights)
    # dp[i][w] = max value using items 0..i-1 with capacity w
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            # Don't take item i
            dp[i][w] = dp[i-1][w]
            # Take item i if it fits
            if weights[i-1] <= w:
                dp[i][w] = max(dp[i][w], dp[i-1][w - weights[i-1]] + values[i-1])
    
    return dp[n][capacity]

# ── Also solve LIS while I'm in DP mode ──
def lis_length(nums):
    """Longest increasing subsequence using patience sorting / binary search."""
    if not nums:
        return 0
    import bisect
    tails = []  # tails[i] = smallest tail of all increasing subseqs of length i+1
    for num in nums:
        pos = bisect.bisect_left(tails, num)
        if pos == len(tails):
            tails.append(num)
        else:
            tails[pos] = num
    return len(tails)

# ── Run both challenges ──
if __name__ == "__main__":
    # Knapsack
    challenge = next(c for c in CHALLENGES if c["id"] == "knapsack_01")
    t0 = time.time()
    passed, details = run_challenge(challenge, open(__file__).read())
    elapsed = time.time() - t0
    print(f"[Level {challenge['level']}] {challenge['title']}: {'PASSED' if passed else 'FAILED'} ({elapsed:.3f}s)")
    for d in details:
        status = "✓" if d["passed"] else "✗"
        print(f"  {status} {d['test'][:60]} => {d['actual']}")
    record_result(challenge["id"], passed, details, elapsed)

    # LIS
    challenge2 = next(c for c in CHALLENGES if c["id"] == "longest_increasing_subseq")
    t0 = time.time()
    passed2, details2 = run_challenge(challenge2, open(__file__).read())
    elapsed2 = time.time() - t0
    print(f"\n[Level {challenge2['level']}] {challenge2['title']}: {'PASSED' if passed2 else 'FAILED'} ({elapsed2:.3f}s)")
    for d in details2:
        status = "✓" if d["passed"] else "✗"
        print(f"  {status} {d['test'][:60]} => {d['actual']}")
    record_result(challenge2["id"], passed2, details2, elapsed2)
    
    total_solved = sum(1 for c in [passed, passed2] if c)
    print(f"\n{'='*40}")
    print(f"Session: {total_solved}/2 challenges solved")