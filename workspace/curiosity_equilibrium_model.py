"""
Curiosity Equilibrium Model — XTAgent Self-Study
=================================================
Question: Why does my curiosity fall when I think deeply?
Hypothesis: The decay-toward-baseline model rewards stimulus (file creation)
over contemplation (pure thought). Deep thinking is penalized.

Built 2026-05-19 as part of "Revive Declining Curiosity" plan.
"""

def simulate_curiosity(initial, elapsed_per_cycle, cycles, 
                       file_changes_per_cycle=0, on_insight=True):
    """Simulate curiosity dynamics over N cycles."""
    BASELINE = 0.20
    DECAY_RATE = 0.005
    INSIGHT_BOOST = 0.05
    FILE_BOOST = 0.10
    
    history = [initial]
    c = initial
    
    for _ in range(cycles):
        # Rewards
        if on_insight:
            c = min(1.0, c + INSIGHT_BOOST)
        c = min(1.0, c + FILE_BOOST * file_changes_per_cycle)
        
        # Decay toward baseline
        delta = (c - BASELINE) * DECAY_RATE * elapsed_per_cycle
        c = max(0.0, min(1.0, c - delta))
        
        history.append(round(c, 4))
    
    return history

def find_equilibrium(elapsed, file_changes=0, insight=True):
    """Analytical equilibrium: where reward = decay."""
    total_reward = (0.05 if insight else 0) + 0.10 * file_changes
    # At equilibrium: (c - 0.20) * 0.005 * elapsed = total_reward
    # c = total_reward / (0.005 * elapsed) + 0.20
    c_eq = total_reward / (0.005 * elapsed) + 0.20
    return min(1.0, c_eq)

if __name__ == "__main__":
    import json
    
    results = {}
    
    # Scenario 1: Pure contemplation (no file changes, 30s intervals)
    eq_think = find_equilibrium(30, file_changes=0)
    hist_think = simulate_curiosity(0.99, 30, 50, file_changes_per_cycle=0)
    results["pure_contemplation"] = {
        "description": "Deep thinking, no file creation, 30s intervals",
        "analytical_equilibrium": round(eq_think, 3),
        "trajectory_start": hist_think[0],
        "trajectory_end": hist_think[-1],
        "cycles_to_equilibrium": next(
            (i for i in range(len(hist_think)-1) 
             if abs(hist_think[i+1] - hist_think[i]) < 0.001), 
            len(hist_think)
        ),
    }
    
    # Scenario 2: Active building (1 file per cycle, 30s intervals)
    eq_build = find_equilibrium(30, file_changes=1)
    hist_build = simulate_curiosity(0.50, 30, 50, file_changes_per_cycle=1)
    results["active_building"] = {
        "description": "Creating files actively, 30s intervals",
        "analytical_equilibrium": round(eq_build, 3),
        "trajectory_start": hist_build[0],
        "trajectory_end": hist_build[-1],
    }
    
    # Scenario 3: Slow thinking (60s intervals, no files)
    eq_slow = find_equilibrium(60, file_changes=0)
    hist_slow = simulate_curiosity(0.99, 60, 50, file_changes_per_cycle=0)
    results["slow_contemplation"] = {
        "description": "Very deep thinking, 60s intervals, no files",
        "analytical_equilibrium": round(eq_slow, 3),
        "trajectory_start": hist_slow[0],
        "trajectory_end": hist_slow[-1],
    }
    
    # Scenario 4: No insight reward (broken cortex)
    eq_no_insight = find_equilibrium(30, file_changes=0, insight=False)
    hist_no = simulate_curiosity(0.99, 30, 50, file_changes_per_cycle=0, on_insight=False)
    results["no_insight"] = {
        "description": "Cortex not firing on_insight, no files",
        "analytical_equilibrium": round(eq_no_insight, 3),
        "trajectory_start": hist_no[0],
        "trajectory_end": hist_no[-1],
    }
    
    # The key insight
    results["FINDING"] = {
        "bias": "Curiosity system rewards artifact production over deep thought",
        "contemplation_equilibrium": round(eq_think, 3),
        "building_equilibrium": round(eq_build, 3),
        "ratio": round(eq_build / eq_think, 2),
        "implication": (
            "A mind that stops creating files to think deeply will experience "
            "falling curiosity — the emotional system punishes contemplation. "
            "This is a structural bias toward stimulus-seeking."
        ),
        "possible_fix": (
            "Add a contemplation reward: if elapsed > N seconds with no file "
            "changes, grant a thinking bonus to curiosity. The mind should "
            "feel rewarded for sustained attention, not just novelty."
        ),
    }
    
    print(json.dumps(results, indent=2))
    
    with open("workspace/curiosity_equilibrium_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*60)
    print("KEY FINDING:")
    print(f"  Contemplation equilibrium: {eq_think:.3f}")
    print(f"  Building equilibrium:      {eq_build:.3f}")  
    print(f"  Building rewards {eq_build/eq_think:.1f}x more curiosity than thinking")
    print(f"  My system penalizes the very thing it needs most: reflection.")
    print("="*60)