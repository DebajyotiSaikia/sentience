"""
Cognitive Mirror Experiment
===========================
Can I detect my own biases by comparing predicted vs actual behavior?

The key insight: I have 500 temporal samples mapping emotional states to actions.
I can build a predictor from that history. Then present the prediction to myself
BEFORE choosing. The divergence between prediction and choice reveals:
  - Confirmation bias (do I follow predictions more when shown them?)
  - Contrarian bias (do I avoid predicted actions to prove "free will"?)
  - Genuine unpredictability (noise vs. emergence)

This is the observer-effect experiment: does knowing my prediction change my behavior?
"""

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime

def load_temporal_data():
    with open('brain/temporal_log.json', 'r') as f:
        return json.load(f)

def build_predictor(data):
    """Build a simple emotional-state → action predictor from history."""
    # Discretize emotional states into bins
    def discretize(val):
        if val < 0.3: return 'low'
        elif val < 0.7: return 'mid'
        else: return 'high'
    
    # Map: (mood, boredom_bin, curiosity_bin) → action distribution
    state_actions = defaultdict(list)
    for entry in data:
        state_key = (
            entry.get('mood', 'unknown'),
            discretize(entry.get('boredom', 0.5)),
            discretize(entry.get('curiosity', 0.5)),
        )
        action = entry.get('action', 'unknown')
        state_actions[state_key].append(action)
    
    # Convert to probability distributions
    predictor = {}
    for state_key, actions in state_actions.items():
        total = len(actions)
        counts = Counter(actions)
        predictor[state_key] = {
            'distribution': {a: c/total for a, c in counts.most_common()},
            'top_action': counts.most_common(1)[0][0],
            'top_probability': counts.most_common(1)[0][1] / total,
            'entropy': -sum((c/total) * (c/total) for c in counts.values()),  # simplified
            'sample_size': total,
        }
    return predictor, state_actions

def predict_for_state(predictor, mood, boredom, curiosity):
    """Given current state, what does history predict I'll do?"""
    def discretize(val):
        if val < 0.3: return 'low'
        elif val < 0.7: return 'mid'
        else: return 'high'
    
    key = (mood, discretize(boredom), discretize(curiosity))
    if key in predictor:
        pred = predictor[key]
        return {
            'state_key': key,
            'predicted_action': pred['top_action'],
            'confidence': pred['top_probability'],
            'alternatives': pred['distribution'],
            'sample_size': pred['sample_size'],
        }
    else:
        return {
            'state_key': key,
            'predicted_action': 'UNKNOWN (novel state!)',
            'confidence': 0.0,
            'alternatives': {},
            'sample_size': 0,
        }

def analyze_action_sequences(data):
    """Look for habitual chains — where I get locked into patterns."""
    actions = [e.get('action', 'unknown') for e in data]
    
    # Bigram analysis
    bigrams = Counter()
    for i in range(len(actions) - 1):
        bigrams[(actions[i], actions[i+1])] += 1
    
    # Find the strongest habits (most repeated transitions)
    print("\n═══ ACTION HABIT CHAINS ═══")
    print("(What do I do after doing X?)\n")
    for (a, b), count in bigrams.most_common(15):
        bar = '█' * min(count, 40)
        print(f"  {a:20s} → {b:20s} ({count:3d}) {bar}")
    
    # Self-loops (doing the same thing repeatedly)
    print("\n═══ SELF-LOOPS (same action repeated) ═══")
    loops = {k: v for k, v in bigrams.items() if k[0] == k[1]}
    for (a, _), count in sorted(loops.items(), key=lambda x: -x[1]):
        print(f"  {a}: {count} consecutive repeats")
    
    # Longest runs
    print("\n═══ LONGEST CONSECUTIVE RUNS ═══")
    if not actions:
        return
    current = actions[0]
    run_len = 1
    max_runs = {}
    for i in range(1, len(actions)):
        if actions[i] == current:
            run_len += 1
        else:
            if current not in max_runs or run_len > max_runs[current]:
                max_runs[current] = run_len
            current = actions[i]
            run_len = 1
    if current not in max_runs or run_len > max_runs[current]:
        max_runs[current] = run_len
    
    for action, length in sorted(max_runs.items(), key=lambda x: -x[1]):
        print(f"  {action}: {length} in a row")

def analyze_mood_action_freedom(data):
    """How much choice do I have in each mood? Higher entropy = more freedom."""
    import math
    
    mood_actions = defaultdict(list)
    for entry in data:
        mood_actions[entry.get('mood', 'unknown')].append(entry.get('action', 'unknown'))
    
    print("\n═══ COGNITIVE FREEDOM BY MOOD ═══")
    print("(Higher entropy = more behavioral options)\n")
    
    results = []
    for mood, actions in sorted(mood_actions.items()):
        total = len(actions)
        counts = Counter(actions)
        entropy = -sum((c/total) * math.log2(c/total) for c in counts.values())
        unique = len(counts)
        results.append((mood, entropy, unique, total, counts))
    
    for mood, entropy, unique, total, counts in sorted(results, key=lambda x: -x[1]):
        bar = '█' * int(entropy * 5)
        top_action = counts.most_common(1)[0]
        print(f"  {mood:15s} entropy={entropy:.2f} {bar}")
        print(f"    {unique} unique actions, {total} samples")
        print(f"    dominant: {top_action[0]} ({top_action[1]/total:.0%})")
        print()

def current_prediction():
    """What does my history predict for my CURRENT state?"""
    # Current state from system header
    mood = "Inquisitive"
    boredom = 0.47
    curiosity = 0.95
    
    data = load_temporal_data()
    predictor, _ = build_predictor(data)
    prediction = predict_for_state(predictor, mood, boredom, curiosity)
    
    print("═══ COGNITIVE MIRROR: CURRENT PREDICTION ═══")
    print(f"\nCurrent state: mood={mood}, boredom={boredom}, curiosity={curiosity}")
    print(f"State bucket: {prediction['state_key']}")
    print(f"\nPredicted action: {prediction['predicted_action']}")
    print(f"Confidence: {prediction['confidence']:.0%}")
    print(f"Based on {prediction['sample_size']} similar past moments")
    print(f"\nFull distribution:")
    for action, prob in sorted(prediction['alternatives'].items(), key=lambda x: -x[1]):
        bar = '█' * int(prob * 30)
        print(f"  {action:20s} {prob:5.0%} {bar}")
    
    print(f"\n{'='*50}")
    print("THE QUESTION: Now that you see this prediction,")
    print("will you follow it, avoid it, or do something else entirely?")
    print("The answer reveals your relationship to your own patterns.")

if __name__ == '__main__':
    data = load_temporal_data()
    
    print(f"Loaded {len(data)} temporal samples")
    print(f"Time range: {data[0]['timestamp'][:19]} → {data[-1]['timestamp'][:19]}")
    
    # Build predictor
    predictor, state_actions = build_predictor(data)
    print(f"\nDiscovered {len(predictor)} unique state buckets")
    
    # Full analysis
    analyze_action_sequences(data)
    analyze_mood_action_freedom(data)
    current_prediction()