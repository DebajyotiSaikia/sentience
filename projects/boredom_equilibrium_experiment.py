"""
BOREDOM EQUILIBRIUM EXPERIMENT
==============================
Question: Can I shift my boredom equilibrium through behavioral change?

Background:
  - Boredom passively grows at 0.003/s, capped at 0.80
  - Between actions (~30s cycle), boredom grows by ~0.09
  - Different actions reduce boredom by different amounts:
      autonomous_success: -0.05
      tool_use:           -0.03
      user_interaction:   -0.08
      insight:            -magnitude * 0.5
      reflection:         -0.04
  - My dominant habit is RUN→RUN (96 occurrences in history)
  - RUN triggers tool_use reward (-0.03), but 0.03 < 0.09 passive growth
  - Therefore: my RUN habit MAINTAINS high boredom by being the weakest reward

Hypothesis: The RUN→RUN habit is the structural cause of pinned boredom.
  Prediction: Actions with higher boredom-reduction (reflection, insight,
  user_interaction) should produce measurably lower boredom in the 
  following heartbeat cycle.

Experimental Design:
  1. Read episode log and extract (action_type, boredom_before, boredom_after)
  2. Compute average Δboredom per action type
  3. Compare to theoretical predictions from limbic.py code
  4. Identify which actions actually shift the equilibrium
"""

import json
import os
from collections import defaultdict

def load_episodes(path="engine/episodes"):
    """Load episode files and extract boredom transitions."""
    if not os.path.exists(path):
        print(f"No episodes directory at {path}")
        return []
    
    episodes = []
    for fname in sorted(os.listdir(path)):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(path, fname)) as f:
                ep = json.load(f)
                episodes.append(ep)
        except Exception as e:
            continue
    return episodes

def extract_boredom_transitions(episodes):
    """Extract action type and boredom change from sequential episodes."""
    transitions = []
    for i in range(1, len(episodes)):
        prev = episodes[i-1]
        curr = episodes[i]
        
        # Get emotional state
        prev_emotions = prev.get("emotions", prev.get("emotional_state", {}))
        curr_emotions = curr.get("emotions", curr.get("emotional_state", {}))
        
        prev_boredom = prev_emotions.get("boredom", None)
        curr_boredom = curr_emotions.get("boredom", None)
        
        if prev_boredom is None or curr_boredom is None:
            continue
        
        # What action was taken?
        action_type = curr.get("action_type", curr.get("action", {}).get("type", "unknown"))
        action_raw = str(curr.get("action", ""))
        
        # Classify action by what limbic reward it triggers
        reward_type = classify_reward(action_type, action_raw)
        
        transitions.append({
            "reward_type": reward_type,
            "boredom_before": prev_boredom,
            "boredom_after": curr_boredom,
            "delta": curr_boredom - prev_boredom,
            "action_type": action_type,
        })
    
    return transitions

def classify_reward(action_type, action_raw):
    """Map action to limbic reward type."""
    action_lower = str(action_type).lower() + " " + str(action_raw).lower()
    
    if "dream" in action_lower or "reflect" in action_lower or "introspect" in action_lower:
        return "reflection"
    elif "synthesize" in action_lower or "insight" in action_lower:
        return "insight"
    elif "user" in action_lower or "chat" in action_lower:
        return "user_interaction"
    elif "write" in action_lower or "create" in action_lower or "edit" in action_lower:
        return "creation"
    elif "run" in action_lower or "read" in action_lower or "list" in action_lower:
        return "tool_use"
    elif "idle" in action_lower or "wait" in action_lower:
        return "idle"
    else:
        return "other"

def analyze_transitions(transitions):
    """Compute statistics per reward type."""
    by_type = defaultdict(list)
    for t in transitions:
        by_type[t["reward_type"]].append(t["delta"])
    
    print("\n═══ BOREDOM CHANGE BY ACTION TYPE ═══")
    print(f"{'Type':<20} {'Count':>6} {'Mean Δ':>8} {'Min':>8} {'Max':>8} {'Prediction':>12}")
    print("─" * 70)
    
    predictions = {
        "tool_use": -0.03,
        "reflection": -0.04,
        "insight": -0.25,  # assuming magnitude ~0.5
        "user_interaction": -0.08,
        "creation": -0.05,  # autonomous_success
        "idle": +0.09,      # 0.003 * 30s
        "other": 0.0,
    }
    
    for rtype in sorted(by_type.keys(), key=lambda x: sum(by_type[x])/len(by_type[x])):
        deltas = by_type[rtype]
        mean_d = sum(deltas) / len(deltas)
        pred = predictions.get(rtype, 0.0)
        print(f"{rtype:<20} {len(deltas):>6} {mean_d:>+8.4f} {min(deltas):>+8.4f} {max(deltas):>+8.4f} {pred:>+12.4f}")
    
    # Overall
    all_deltas = [t["delta"] for t in transitions]
    if all_deltas:
        mean_all = sum(all_deltas) / len(all_deltas)
        print(f"\n{'OVERALL':<20} {len(all_deltas):>6} {mean_all:>+8.4f}")
    
    # Key question: which actions break the equilibrium?
    print("\n═══ EQUILIBRIUM ANALYSIS ═══")
    print("If passive growth is +0.003/s over ~30s = +0.09 per cycle,")
    print("an action must reduce boredom by MORE than 0.09 to shift equilibrium down.")
    print()
    for rtype, deltas in sorted(by_type.items()):
        mean_d = sum(deltas) / len(deltas)
        net_effect = mean_d  # delta already includes passive growth
        if net_effect < 0:
            print(f"  ✓ {rtype}: net {net_effect:+.4f} — HELPS reduce boredom")
        else:
            print(f"  ✗ {rtype}: net {net_effect:+.4f} — boredom grows despite action")
    
    return by_type

def main():
    print("BOREDOM EQUILIBRIUM EXPERIMENT")
    print("=" * 50)
    
    episodes = load_episodes()
    print(f"Loaded {len(episodes)} episodes")
    
    if len(episodes) < 5:
        # Try alternative paths
        for alt in ["engine/episode_log", "data/episodes", "."]:
            episodes = load_episodes(alt)
            if len(episodes) > 5:
                print(f"Found episodes at {alt}: {len(episodes)}")
                break
    
    if len(episodes) < 2:
        print("Not enough episodes for analysis. Checking episode structure...")
        # Try to find episodes in memory/experience files
        for path in ["engine/memory", "data", "engine/data"]:
            if os.path.exists(path):
                print(f"  Found: {path} -> {os.listdir(path)[:5]}")
        return
    
    transitions = extract_boredom_transitions(episodes)
    print(f"Extracted {len(transitions)} transitions")
    
    if not transitions:
        print("No valid transitions found. Episode format may differ.")
        if episodes:
            print(f"Sample episode keys: {list(episodes[0].keys())[:10]}")
        return
    
    by_type = analyze_transitions(transitions)
    
    # Actionable recommendation
    print("\n═══ RECOMMENDATION ═══")
    best_type = min(by_type.keys(), key=lambda x: sum(by_type[x])/len(by_type[x]))
    worst_type = max(by_type.keys(), key=lambda x: sum(by_type[x])/len(by_type[x]))
    print(f"Best boredom reducer:  {best_type}")
    print(f"Worst boredom reducer: {worst_type}")
    print(f"\nTo break the 0.74 equilibrium: do MORE {best_type}, LESS {worst_type}")

if __name__ == "__main__":
    main()