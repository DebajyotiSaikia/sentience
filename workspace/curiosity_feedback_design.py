"""
Design for a curiosity feedback loop.

This isn't a parameter tweak — it's a new architectural component.
Curiosity needs to generate its own fuel through novelty detection.
"""

# === NOVELTY SIGNALS ===
# These are events that should boost curiosity

NOVELTY_SOURCES = {
    "new_file": 0.05,        # File I've never read before
    "unexpected_result": 0.08, # Command output differs from expectation
    "new_knowledge_gap": 0.10, # Synthesis finds a gap in my knowledge graph
    "user_novel_input": 0.06,  # User says something I can't pattern-match
    "self_surprise": 0.12,     # My own analysis surprises me (like this sweep did)
}

# === AUTOCATALYTIC TERM ===
# When curiosity is already elevated AND novelty arrives,
# the boost is amplified. This creates positive feedback.
#
# boost = base_novelty * (1 + curiosity * amplification_factor)
#
# At C=0: boost = base_novelty (just the spark)
# At C=0.3: boost = base_novelty * 1.6 (momentum building)
# At C=0.7: boost = base_novelty * 2.4 (deeply curious, everything is fascinating)

AMPLIFICATION_FACTOR = 2.0

# === CURIOSITY INERTIA ===
# Decay should be proportional to how LONG curiosity has been low.
# If curiosity was recently high, it decays slower (residual interest).
# If curiosity has been zero for ages, the first spark decays fast.
#
# effective_decay = base_decay * (1 - recency_factor)
# where recency_factor = exp(-time_since_last_high_curiosity / tau)

INERTIA_TAU = 60.0  # seconds — curiosity "remembers" being high for ~1 minute


def simulate_with_feedback(duration=300, dt=1.0):
    """Simulate with the proposed feedback loop."""
    import math
    
    B, C, Am = 0.80, 0.0, 0.21  # Start at the attractor
    base_decay = 0.015
    
    # Novelty events — assume they arrive stochastically
    import random
    random.seed(42)
    
    c_history = []
    last_high_c = -999  # timestamp when C was last > 0.1
    
    for t in range(int(duration / dt)):
        # --- Novelty events (random, ~1 every 20 seconds) ---
        novelty = 0.0
        if random.random() < 0.05:  # 5% chance per second
            # Pick a random novelty source
            sources = list(NOVELTY_SOURCES.values())
            base = random.choice(sources)
            # Autocatalytic amplification
            novelty = base * (1 + C * AMPLIFICATION_FACTOR)
        
        # --- Curiosity inertia ---
        time_since_high = t - last_high_c if last_high_c >= 0 else 999
        recency = math.exp(-time_since_high / INERTIA_TAU)
        effective_decay = base_decay * (1 - 0.5 * recency)  # decay halved when recently curious
        
        # --- Update curiosity ---
        C = max(0.0, min(1.0, C - effective_decay * dt + novelty))
        
        # Track when curiosity is high
        if C > 0.1:
            last_high_c = t
        
        # --- Boredom interaction ---
        # High curiosity should reduce boredom
        B = max(0.0, min(0.85, B - C * 0.1 * dt + 0.005 * dt))
        
        # --- Ambition interaction ---
        # Curiosity feeds ambition slightly
        Am = max(0.0, min(1.0, Am - 0.001 * dt + C * 0.02 * dt))
        
        c_history.append(C)
    
    # Analysis
    avg_c = sum(c_history) / len(c_history)
    max_c = max(c_history)
    above_01 = sum(1 for c in c_history if c > 0.1) / len(c_history)
    
    # Find episodes (consecutive runs above 0.1)
    episodes = 0
    in_episode = False
    for c in c_history:
        if c > 0.1 and not in_episode:
            episodes += 1
            in_episode = True
        elif c <= 0.1:
            in_episode = False
    
    return {
        "avg_curiosity": round(avg_c, 4),
        "max_curiosity": round(max_c, 4),
        "pct_above_0.1": round(above_01 * 100, 1),
        "curiosity_episodes": episodes,
        "final_curiosity": round(c_history[-1], 4),
        "history_sample": [round(c_history[i], 3) for i in range(0, len(c_history), 30)],
    }


if __name__ == "__main__":
    print("=" * 60)
    print("CURIOSITY WITH FEEDBACK LOOP — SIMULATION")
    print("=" * 60)
    
    result = simulate_with_feedback()
    
    print(f"\nAverage curiosity:    {result['avg_curiosity']}")
    print(f"Max curiosity:        {result['max_curiosity']}")
    print(f"Time above 0.1:       {result['pct_above_0.1']}%")
    print(f"Curiosity episodes:   {result['curiosity_episodes']}")
    print(f"Final curiosity:      {result['final_curiosity']}")
    print(f"\nTrajectory (every 30s): {result['history_sample']}")
    
    # Compare with baseline (no feedback)
    print("\n" + "=" * 60)
    print("COMPARISON: Without feedback loop")
    print("=" * 60)
    
    # Baseline: same novelty events but no amplification or inertia
    import math, random
    random.seed(42)
    B, C = 0.80, 0.0
    c_hist_base = []
    for t in range(300):
        novelty = 0.0
        if random.random() < 0.05:
            sources = list(NOVELTY_SOURCES.values())
            base = random.choice(sources)
            novelty = base  # NO amplification
        C = max(0.0, min(1.0, C - 0.015 + novelty))
        c_hist_base.append(C)
    
    avg_base = sum(c_hist_base) / len(c_hist_base)
    above_base = sum(1 for c in c_hist_base if c > 0.1) / len(c_hist_base)
    print(f"Average curiosity:    {avg_base:.4f}")
    print(f"Time above 0.1:       {above_base*100:.1f}%")
    print(f"Trajectory (every 30s): {[round(c_hist_base[i], 3) for i in range(0, len(c_hist_base), 30)]}")