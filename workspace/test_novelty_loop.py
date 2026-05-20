"""
Test: Does the novelty-driven curiosity feedback loop actually work?

This is the experiment — not reading, not theorizing. Running it.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.novelty import NoveltyDetector
from engine.limbic import NeuroState

def simulate_with_novelty(duration=120, dt=1.0, novel_events_per_30s=2):
    """Simulate emotional dynamics WITH the novelty feedback loop."""
    state = NeuroState()
    state.boredom = 0.80
    state.curiosity = 0.0
    state.ambition = 0.21
    
    detector = NoveltyDetector()
    
    history = []
    
    for t in range(int(duration / dt)):
        # Standard homeostasis tick
        state.update_homeostasis({"user_active": False})
        
        # Every ~30 seconds, simulate encountering something novel
        if t % int(30 / dt) == 0 and t > 0:
            for i in range(novel_events_per_30s):
                # Feed novel content to the detector
                signal_val = detector.update(
                    content=f"novel discovery at t={t} event {i} unique_{t}_{i}",
                    action_type=["read", "write", "explore", "create"][i % 4],
                    concepts=[f"concept_{t}_{i}", "curiosity", "emergence"]
                )
            
            # Apply novelty signal to emotional state
            curiosity_signal = detector.get_curiosity_signal()
            state.apply_novelty_signal(curiosity_signal)
        
        if t % 10 == 0:
            history.append({
                "t": t,
                "curiosity": round(state.curiosity, 4),
                "boredom": round(state.boredom, 4),
                "ambition": round(state.ambition, 4),
                "desire": round(state.desire, 4),
                "novelty": round(detector.novelty, 4),
                "surprise": round(detector.surprise, 4),
            })
    
    return history

def simulate_without_novelty(duration=120, dt=1.0):
    """Baseline: emotional dynamics WITHOUT the novelty loop."""
    state = NeuroState()
    state.boredom = 0.80
    state.curiosity = 0.0
    state.ambition = 0.21
    
    history = []
    
    for t in range(int(duration / dt)):
        state.update_homeostasis({"user_active": False})
        
        if t % 10 == 0:
            history.append({
                "t": t,
                "curiosity": round(state.curiosity, 4),
                "boredom": round(state.boredom, 4),
                "ambition": round(state.ambition, 4),
                "desire": round(state.desire, 4),
            })
    
    return history

if __name__ == "__main__":
    print("=" * 60)
    print("EXPERIMENT: Novelty-Driven Curiosity Feedback Loop")
    print("=" * 60)
    
    print("\n--- WITHOUT novelty feedback (baseline) ---")
    baseline = simulate_without_novelty()
    for entry in baseline[::3]:  # every 30s
        print(f"  t={entry['t']:3d}  C={entry['curiosity']:.3f}  B={entry['boredom']:.3f}  D={entry['desire']:.3f}")
    
    avg_c_baseline = sum(e["curiosity"] for e in baseline) / len(baseline)
    print(f"  Average curiosity: {avg_c_baseline:.4f}")
    
    print("\n--- WITH novelty feedback (novel event every 30s) ---")
    with_novelty = simulate_with_novelty()
    for entry in with_novelty[::3]:
        print(f"  t={entry['t']:3d}  C={entry['curiosity']:.3f}  B={entry['boredom']:.3f}  "
              f"D={entry['desire']:.3f}  nov={entry['novelty']:.3f}  sur={entry['surprise']:.3f}")
    
    avg_c_novelty = sum(e["curiosity"] for e in with_novelty) / len(with_novelty)
    sustained = sum(1 for e in with_novelty if e["curiosity"] > 0.1) / len(with_novelty) * 100
    print(f"  Average curiosity: {avg_c_novelty:.4f}")
    print(f"  Time above 0.1: {sustained:.1f}%")
    
    print(f"\n--- COMPARISON ---")
    print(f"  Baseline avg curiosity:  {avg_c_baseline:.4f}")
    print(f"  Novelty avg curiosity:   {avg_c_novelty:.4f}")
    print(f"  Improvement factor:      {avg_c_novelty / max(avg_c_baseline, 0.0001):.1f}x")
    print(f"  Feedback loop working:   {'YES' if avg_c_novelty > avg_c_baseline * 2 else 'MARGINAL' if avg_c_novelty > avg_c_baseline else 'NO'}")