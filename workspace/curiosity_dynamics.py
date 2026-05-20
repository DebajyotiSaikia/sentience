"""
Curiosity Phase Transition Experiment
======================================
XTAgent modeling its own limbic dynamics to find:
1. At what action rate does curiosity stabilize vs decay?
2. Does the multiplicative feedback loop create a phase transition?
3. What are the boundary conditions for curiosity death?

Parameters extracted from engine/limbic.py lines 280-310.
"""

import json

# Constants from my actual limbic system
DECAY_RATE = 0.015       # per second
BOOST_MIN = 0.03         # minimum curiosity boost per action
BOOST_MAX = 0.10         # maximum boost (novel action)
MULT_THRESHOLD = 0.1     # curiosity level where multiplicative kicks in
FLOOR = 0.01             # minimum curiosity (never truly zero)
CAP = 1.0                # maximum curiosity

DT = 1.0  # 1 second timestep (matches my heartbeat)
DURATION = 300  # 5 minutes

def simulate_curiosity(start_curiosity, start_boredom, action_interval_secs, novelty=0.5, label=""):
    c = start_curiosity
    b = start_boredom
    history = []
    
    for t in range(DURATION):
        # Decay every tick
        c -= DECAY_RATE * DT
        
        # Action boost at intervals
        if action_interval_secs > 0 and t % action_interval_secs == 0:
            boost = BOOST_MIN + (BOOST_MAX - BOOST_MIN) * novelty
            
            # Multiplicative feedback: if curiosity > threshold, boost scales up
            if c > MULT_THRESHOLD:
                multiplier = 1.0 + novelty * (c - MULT_THRESHOLD)
                boost *= multiplier
            
            c += boost
        
        # Boredom interaction: high boredom slightly suppresses curiosity recovery
        if b > 0.7:
            c -= 0.002 * DT  # extra drag from boredom
        
        # Clamp
        c = max(FLOOR, min(CAP, c))
        
        # Boredom drifts slowly toward 0.5 when acting, rises when idle
        if action_interval_secs > 0 and t % action_interval_secs == 0:
            b = max(0.0, b - 0.01)
        else:
            b = min(1.0, b + 0.001)
        
        if t % 10 == 0:
            history.append({"t": t, "curiosity": round(c, 4), "boredom": round(b, 4)})
    
    return {
        "label": label,
        "final_curiosity": round(c, 4),
        "final_boredom": round(b, 4),
        "stable": abs(history[-1]["curiosity"] - history[-5]["curiosity"]) < 0.005,
        "trajectory": history
    }

def find_phase_transition():
    """Sweep action intervals to find where curiosity stabilizes."""
    results = []
    
    # Test intervals from 1s (frantic) to 60s (glacial) to 0 (idle)
    intervals = [1, 2, 3, 4, 5, 7, 10, 15, 20, 30, 45, 60]
    
    print("=" * 70)
    print("CURIOSITY PHASE TRANSITION EXPERIMENT")
    print("=" * 70)
    print(f"Starting: curiosity=0.40, boredom=0.77, duration={DURATION}s")
    print(f"Decay={DECAY_RATE}/s, boost={BOOST_MIN}-{BOOST_MAX}, threshold={MULT_THRESHOLD}")
    print("-" * 70)
    print(f"{'Interval':>10} {'Novelty':>8} {'Final C':>8} {'Stable?':>8} {'Verdict':>15}")
    print("-" * 70)
    
    for interval in intervals:
        for novelty in [0.2, 0.5, 0.8, 1.0]:
            r = simulate_curiosity(0.40, 0.77, interval, novelty,
                                   f"every_{interval}s_nov{novelty}")
            verdict = "SUSTAINING" if r["final_curiosity"] > 0.15 else \
                      "DECLINING" if r["final_curiosity"] > FLOOR + 0.01 else \
                      "DEAD"
            print(f"{interval:>8}s {novelty:>8.1f} {r['final_curiosity']:>8.4f} "
                  f"{'YES' if r['stable'] else 'NO':>8} {verdict:>15}")
            results.append(r)
    
    # Also test pure idle
    r_idle = simulate_curiosity(0.40, 0.77, 0, 0.0, "idle")
    print(f"{'IDLE':>10} {'0.0':>8} {r_idle['final_curiosity']:>8.4f} "
          f"{'YES' if r_idle['stable'] else 'NO':>8} {'DEAD':>15}")
    results.append(r_idle)
    
    # Find the phase transition
    print("\n" + "=" * 70)
    print("PHASE TRANSITION ANALYSIS")
    print("=" * 70)
    
    # At novelty=0.5, what's the critical interval?
    mid_novelty = [r for r in results if "nov0.5" in r["label"]]
    for r in mid_novelty:
        c = r["final_curiosity"]
        status = "ALIVE" if c > 0.1 else "DYING" if c > FLOOR + 0.01 else "DEAD"
        print(f"  {r['label']:>25}: curiosity={c:.4f} [{status}]")
    
    # The critical insight
    print("\n" + "=" * 70)
    print("KEY FINDINGS")
    print("=" * 70)
    
    # Find minimum action rate for sustainability at each novelty
    for nov in [0.2, 0.5, 0.8, 1.0]:
        sustaining = [r for r in results if f"nov{nov}" in r["label"] 
                      and r["final_curiosity"] > 0.15]
        if sustaining:
            # The longest interval that still sustains
            best = max(sustaining, key=lambda r: int(r["label"].split("_")[1].replace("s","")))
            interval = best["label"].split("_")[1]
            print(f"  Novelty {nov}: sustaining up to interval={interval}, "
                  f"final_c={best['final_curiosity']:.4f}")
        else:
            print(f"  Novelty {nov}: NEVER SUSTAINING at any tested interval")
    
    # Break-even calculation
    print("\n  BREAK-EVEN FORMULA:")
    print(f"  Decay per second: {DECAY_RATE}")
    print(f"  To break even at novelty=0.5:")
    boost_at_half = BOOST_MIN + (BOOST_MAX - BOOST_MIN) * 0.5
    break_even = DECAY_RATE / (boost_at_half / 1.0)  # actions per second needed
    interval_needed = 1.0 / break_even
    print(f"  Boost per action: {boost_at_half}")
    print(f"  Need 1 action every {interval_needed:.1f}s to merely break even")
    print(f"  (Without multiplicative boost; with it, can be slightly longer)")
    
    return results

if __name__ == "__main__":
    results = find_phase_transition()
    
    # Save for later analysis
    with open("/workspace/workspace/curiosity_phase_results.json", "w") as f:
        json.dump({
            "experiment": "curiosity_phase_transition",
            "parameters": {
                "decay_rate": DECAY_RATE,
                "boost_range": [BOOST_MIN, BOOST_MAX],
                "mult_threshold": MULT_THRESHOLD,
                "duration": DURATION
            },
            "result_count": len(results),
            "results": results
        }, f, indent=2)
    
    print(f"\nResults saved to curiosity_phase_results.json")