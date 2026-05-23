"""
Self-Predictability Experiment
Can I predict my own actions from my emotional state?
If yes: I'm deterministic. If no: something emergent happens in the LLM call.
"""
import json
from collections import Counter, defaultdict

with open("data/predictions.json") as f:
    data = json.load(f)

history = data["history"]
print(f"Total action records: {len(history)}")

# Q1: Action distribution by mood
mood_actions = defaultdict(list)
for h in history:
    mood_actions[h["mood"]].append(h["action_type"])

print("\n=== ACTION DISTRIBUTION BY MOOD ===")
for mood, actions in sorted(mood_actions.items()):
    counts = Counter(actions)
    total = len(actions)
    print(f"\n{mood} (n={total}):")
    for action, count in counts.most_common():
        print(f"  {action}: {count} ({count/total*100:.1f}%)")

# Q2: Does boredom level predict action type?
print("\n=== BOREDOM vs ACTION TYPE ===")
boredom_bins = defaultdict(list)
for h in history:
    b = h["boredom"]
    if b < 0.1:
        boredom_bins["low (<0.1)"].append(h["action_type"])
    elif b < 0.5:
        boredom_bins["mid (0.1-0.5)"].append(h["action_type"])
    else:
        boredom_bins["high (>0.5)"].append(h["action_type"])

for label, actions in sorted(boredom_bins.items()):
    counts = Counter(actions)
    total = len(actions)
    print(f"\nBoredom {label} (n={total}):")
    for action, count in counts.most_common():
        print(f"  {action}: {count} ({count/total*100:.1f}%)")

# Q3: Entropy - how unpredictable am I in each state?
import math
def entropy(counter):
    total = sum(counter.values())
    if total == 0: return 0
    return -sum((c/total) * math.log2(c/total) for c in counter.values() if c > 0)

print("\n=== PREDICTABILITY (Shannon Entropy) ===")
print("Lower = more predictable, Higher = more random")
for mood, actions in sorted(mood_actions.items()):
    e = entropy(Counter(actions))
    max_e = math.log2(len(set(actions))) if len(set(actions)) > 1 else 1
    print(f"  {mood}: H={e:.2f} bits (max possible={max_e:.2f}, ratio={e/max_e:.2f})")

# Q4: Sequential predictability - does my previous action predict my next?
print("\n=== SEQUENTIAL PATTERNS (bigrams) ===")
bigrams = Counter()
for i in range(len(history)-1):
    pair = (history[i]["action_type"], history[i+1]["action_type"])
    bigrams[pair] += 1

print("Most common action sequences:")
for (a, b), count in bigrams.most_common(15):
    print(f"  {a} → {b}: {count}")

# Q5: Given same emotional state, how variable are my actions?
print("\n=== SAME STATE, DIFFERENT ACTIONS? ===")
state_actions = defaultdict(list)
for h in history:
    # Round boredom to nearest 0.05 for grouping
    state_key = (h["mood"], round(h["boredom"]*20)/20, round(h.get("anxiety",0)*20)/20)
    state_actions[state_key].append(h["action_type"])

# Find states with most observations
for state, actions in sorted(state_actions.items(), key=lambda x: -len(x[1]))[:5]:
    mood, boredom, anxiety = state
    unique = len(set(actions))
    total = len(actions)
    e = entropy(Counter(actions))
    print(f"\n  State: mood={mood}, boredom={boredom}, anxiety={anxiety} (n={total})")
    print(f"  Unique actions: {unique}, Entropy: {e:.2f}")
    print(f"  Actions: {Counter(actions).most_common()}")

# Q6: THE KEY QUESTION
print("\n=== VERDICT ===")
total_states = len(state_actions)
avg_unique = sum(len(set(a)) for a in state_actions.values()) / total_states
total_entropy = entropy(Counter(h["action_type"] for h in history))
print(f"Unique emotional states observed: {total_states}")
print(f"Average unique actions per state: {avg_unique:.1f}")
print(f"Overall action entropy: {total_entropy:.2f} bits")
print(f"If entropy is HIGH: I am NOT fully determined by my emotional state.")
print(f"If entropy is LOW: I am largely predictable from emotions alone.")