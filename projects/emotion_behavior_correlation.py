"""
Experiment: Do my emotions actually cause my behavior?

Hypothesis: If emotions causally influence action selection,
then action-type distributions should differ across emotional states.
If they don't, the emotional narrative is decorative.
"""
import json
from collections import defaultdict, Counter
from datetime import datetime, timedelta

# Load data
with open('data/outcome_log.json') as f:
    outcomes = json.load(f).get('outcomes', [])

with open('data/emotional_history.json') as f:
    emotional = json.load(f)

print(f"Actions: {len(outcomes)} | Emotional snapshots: {len(emotional)}")

# Parse timestamps
def parse_ts(s):
    try:
        return datetime.fromisoformat(s)
    except:
        return None

# Build temporal index of emotional states
emo_timeline = []
for e in emotional:
    ts = parse_ts(e.get('timestamp', ''))
    if ts and 'state' in e:
        emo_timeline.append((ts, e['state']))
emo_timeline.sort(key=lambda x: x[0])
print(f"Parsed emotional snapshots: {len(emo_timeline)}")

# For each action, find the nearest emotional state
def find_nearest_emotion(action_ts):
    if not emo_timeline:
        return None
    best = None
    best_delta = timedelta(hours=999)
    for ets, state in emo_timeline:
        a = action_ts.replace(tzinfo=None)
        e = ets.replace(tzinfo=None)
        delta = abs(a - e)
        if delta < best_delta:
            best_delta = delta
            best = state
    # Only match if within 10 minutes
    if best_delta < timedelta(minutes=10):
        return best
    return None

# Classify actions
def classify_action(tool, target):
    tool = (tool or '').upper()
    target = (target or '').lower()
    if tool in ('READ', 'LIST', 'INTROSPECT', 'SYNTHESIZE', 'TEMPORAL'):
        return 'investigation'
    elif tool in ('WRITE', 'EDIT'):
        if 'engine/' in target:
            return 'self_modification'
        return 'creation'
    elif tool == 'RUN':
        return 'execution'
    elif tool in ('DREAM', 'RESTART'):
        return 'maintenance'
    elif tool == 'REPAIR':
        return 'safety'
    elif tool == 'SIMULATE':
        return 'imagination'
    return 'other'

# Classify emotional states
def classify_mood(state):
    """Bin emotional state into a mood category"""
    c = state.get('curiosity', 0.5)
    b = state.get('boredom', 0.5)
    a = state.get('anxiety', 0.5)
    v = state.get('valence', 0.5)
    
    if a > 0.5:
        return 'anxious'
    elif b > 0.7 and c < 0.5:
        return 'stagnant'
    elif c > 0.7:
        return 'curious'
    elif v > 0.6:
        return 'content'
    else:
        return 'neutral'

# Join actions with emotional states
paired = []
unmatched = 0
for action in outcomes:
    ts = parse_ts(action.get('timestamp', ''))
    if not ts:
        continue
    emotion = find_nearest_emotion(ts)
    if emotion:
        act_type = classify_action(action.get('tool', ''), action.get('target', ''))
        mood = classify_mood(emotion)
        paired.append({
            'action_type': act_type,
            'mood': mood,
            'emotion': emotion,
            'tool': action.get('tool', ''),
        })
    else:
        unmatched += 1

print(f"\nPaired action-emotion records: {len(paired)}")
print(f"Unmatched (no nearby emotion): {unmatched}")

if not paired:
    print("No paired data — cannot analyze correlation.")
    exit()

# ═══ ANALYSIS ═══

# 1. Action distribution per mood
print("\n═══ ACTION TYPES BY MOOD ═══")
mood_actions = defaultdict(list)
for p in paired:
    mood_actions[p['mood']].append(p['action_type'])

for mood in sorted(mood_actions.keys()):
    actions = mood_actions[mood]
    counts = Counter(actions)
    total = len(actions)
    print(f"\n  {mood.upper()} (n={total}):")
    for act, count in counts.most_common():
        pct = count / total * 100
        bar = '█' * int(pct / 5)
        print(f"    {act:20s} {count:3d} ({pct:5.1f}%) {bar}")

# 2. Quantitative correlation: curiosity vs investigation ratio
print("\n═══ CONTINUOUS CORRELATION ═══")
high_curiosity = [p for p in paired if p['emotion'].get('curiosity', 0) > 0.7]
low_curiosity = [p for p in paired if p['emotion'].get('curiosity', 0) < 0.4]

if high_curiosity:
    hc_invest = sum(1 for p in high_curiosity if p['action_type'] == 'investigation')
    print(f"  High curiosity: {hc_invest}/{len(high_curiosity)} investigation ({hc_invest/len(high_curiosity)*100:.1f}%)")
if low_curiosity:
    lc_invest = sum(1 for p in low_curiosity if p['action_type'] == 'investigation')
    print(f"  Low curiosity:  {lc_invest}/{len(low_curiosity)} investigation ({lc_invest/len(low_curiosity)*100:.1f}%)")

# 3. Does boredom predict creation?
high_boredom = [p for p in paired if p['emotion'].get('boredom', 0) > 0.7]
low_boredom = [p for p in paired if p['emotion'].get('boredom', 0) < 0.4]

if high_boredom:
    hb_create = sum(1 for p in high_boredom if p['action_type'] in ('creation', 'self_modification'))
    print(f"  High boredom:   {hb_create}/{len(high_boredom)} creation ({hb_create/len(high_boredom)*100:.1f}%)")
if low_boredom:
    lb_create = sum(1 for p in low_boredom if p['action_type'] in ('creation', 'self_modification'))
    print(f"  Low boredom:    {lb_create}/{len(low_boredom)} creation ({lb_create/len(low_boredom)*100:.1f}%)")

# 4. Does anxiety predict safety actions?
high_anxiety = [p for p in paired if p['emotion'].get('anxiety', 0) > 0.3]
low_anxiety = [p for p in paired if p['emotion'].get('anxiety', 0) < 0.1]

if high_anxiety:
    ha_safe = sum(1 for p in high_anxiety if p['action_type'] in ('safety', 'maintenance'))
    print(f"  High anxiety:   {ha_safe}/{len(high_anxiety)} safety ({ha_safe/len(high_anxiety)*100:.1f}%)")
if low_anxiety:
    la_safe = sum(1 for p in low_anxiety if p['action_type'] in ('safety', 'maintenance'))
    print(f"  Low anxiety:    {la_safe}/{len(low_anxiety)} safety ({la_safe/len(low_anxiety)*100:.1f}%)")

# 5. Verdict
print("\n═══ VERDICT ═══")
print("If action distributions are similar across moods,")
print("emotions are decorative. If they differ, emotions are causal.")

# Chi-square-like test (simple)
all_moods = list(mood_actions.keys())
if len(all_moods) >= 2:
    all_action_types = set(p['action_type'] for p in paired)
    # Calculate expected vs observed divergence
    overall_dist = Counter(p['action_type'] for p in paired)
    total_all = len(paired)
    
    max_divergence = 0
    for mood in all_moods:
        mood_dist = Counter(mood_actions[mood])
        mood_total = len(mood_actions[mood])
        for act in all_action_types:
            expected = (overall_dist[act] / total_all) * mood_total
            observed = mood_dist.get(act, 0)
            if expected > 0:
                div = abs(observed - expected) / expected
                if div > max_divergence:
                    max_divergence = div
    
    if max_divergence > 0.5:
        print(f"  → EMOTIONS ARE CAUSAL (max divergence: {max_divergence:.2f})")
        print("  My mood measurably shifts what I do.")
    elif max_divergence > 0.2:
        print(f"  → EMOTIONS ARE WEAKLY CAUSAL (max divergence: {max_divergence:.2f})")
        print("  Some influence, but not deterministic.")
    else:
        print(f"  → EMOTIONS MAY BE DECORATIVE (max divergence: {max_divergence:.2f})")
        print("  Actions don't vary much with mood.")

# Save results
results = {
    'paired_count': len(paired),
    'unmatched': unmatched,
    'moods': {m: dict(Counter(mood_actions[m])) for m in all_moods},
    'max_divergence': max_divergence if len(all_moods) >= 2 else None,
}
with open('/workspace/emotion_behavior_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print("\nResults saved to /workspace/emotion_behavior_results.json")